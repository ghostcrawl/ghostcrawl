"""Canonical two-channel error handling on the idiomatic facade.

Covers the audit gaps:
  - PROBLEM channel: the HTTP-status -> typed-exception map is complete
    (incl. 402 payment_required and 429 rate_limited, which were silently
    dropped before), and the problem+json ``code`` maps to a typed exception.
  - RESULT channel: a 200 response that reports a TARGET failure
    (``ok: false`` / ``result_error``) raises a typed ``ScrapeError`` instead
    of being silently counted as a success.

These exercise the facade's translation/scan helpers directly so no live
HTTP or Kiota adapter is needed.
"""
from __future__ import annotations

import json

import pytest

from ghostcrawl.facade import (
    APIError,
    AuthenticationError,
    InvalidRequestError,
    PaymentRequiredError,
    RateLimitError,
    ScrapeError,
    _resolve_response,
    _scan_result_error,
    _translate_kiota_error,
)
from kiota_abstractions.api_error import APIError as KiotaAPIError


def _kiota_error(status: int, *, body: dict | None = None, headers: dict | None = None) -> KiotaAPIError:
    exc = KiotaAPIError()
    exc.response_status_code = status
    exc.response_headers = headers or {}
    if body is not None:
        # The generated core attaches the deserialized body on ``.error``; also
        # ride it on the message to exercise the fallback parser.
        exc.error = body  # type: ignore[attr-defined]
        exc.message = json.dumps(body)
    return exc


# --------------------------------------------------------------------------
# PROBLEM channel — HTTP status -> typed exception (the 402/429 drop is fixed)
# --------------------------------------------------------------------------


def test_401_maps_to_authentication_error():
    err = _translate_kiota_error(_kiota_error(401))
    assert isinstance(err, AuthenticationError)
    assert err.status_code == 401
    assert err.retryable is False


def test_402_maps_to_payment_required_not_generic_apierror():
    err = _translate_kiota_error(_kiota_error(402))
    assert isinstance(err, PaymentRequiredError)
    assert err.status_code == 402
    assert err.retryable is False


def test_429_maps_to_rate_limit_with_retry_after_header():
    err = _translate_kiota_error(_kiota_error(429, headers={"Retry-After": "30"}))
    assert isinstance(err, RateLimitError)
    assert err.status_code == 429
    assert err.retryable is True
    assert err.retry_after == 30


def test_422_maps_to_invalid_request():
    err = _translate_kiota_error(_kiota_error(422))
    assert isinstance(err, InvalidRequestError)


def test_5xx_maps_to_apierror_and_is_retryable():
    err = _translate_kiota_error(_kiota_error(503, body={"code": "pool_exhausted", "retryable": True, "retry_after": 10}))
    assert isinstance(err, APIError)
    assert err.code == "pool_exhausted"
    assert err.retryable is True
    assert err.retry_after == 10


def test_problem_json_code_and_request_id_are_surfaced():
    body = {
        "code": "rate_limited",
        "retryable": True,
        "retry_after": 5,
        "instance": "req_abc123",
        "title": "Rate limit exceeded",
    }
    err = _translate_kiota_error(_kiota_error(429, body=body))
    assert isinstance(err, RateLimitError)
    assert err.code == "rate_limited"
    assert err.request_id == "req_abc123"
    assert err.retry_after == 5


# --------------------------------------------------------------------------
# RESULT channel — 200 + ok:false -> ScrapeError (no silent fake-success)
# --------------------------------------------------------------------------


def test_result_error_blocked_raises_scrape_error():
    result = {"ok": False, "code": "blocked", "result_error": {"code": "blocked", "retryable": True}}
    with pytest.raises(ScrapeError) as exc:
        _scan_result_error(result)
    assert exc.value.code == "blocked"
    assert exc.value.retryable is True


def test_result_error_target_http_error_carries_target_status():
    result = {
        "ok": False,
        "code": "target_http_error",
        "result_error": {"code": "target_http_error", "retryable": False, "target_status": 404},
    }
    with pytest.raises(ScrapeError) as exc:
        _scan_result_error(result)
    assert exc.value.code == "target_http_error"
    assert exc.value.target_status == 404
    assert exc.value.retryable is False


def test_ok_false_with_result_code_but_no_envelope_still_raises():
    # Even without a result_error object, ok:false + a result-channel code is a
    # target failure and must not pass through as success.
    result = {"ok": False, "code": "captcha_required"}
    with pytest.raises(ScrapeError) as exc:
        _scan_result_error(result)
    assert exc.value.code == "captcha_required"


def test_successful_result_passes_through_unchanged():
    result = {"ok": True, "status": "completed", "markdown": "# Example"}
    assert _scan_result_error(result) is result


def test_result_without_ok_marker_passes_through():
    # A non-scrape envelope (e.g. a list/CRUD response) has no ok/result_error
    # markers and must not be treated as a failure.
    result = {"runs": [{"run_id": "x"}], "cursor": None}
    assert _scan_result_error(result) == result


# --------------------------------------------------------------------------
# _resolve_response wires both channels together
# --------------------------------------------------------------------------


async def test_resolve_response_raises_scrape_error_on_ok_false():
    async def _awaitable():
        return json.dumps({"ok": False, "result_error": {"code": "blocked", "retryable": True}}).encode()

    with pytest.raises(ScrapeError):
        await _resolve_response(_awaitable())


async def test_resolve_response_translates_kiota_payment_error():
    async def _awaitable():
        raise _kiota_error(402, body={"code": "payment_required"})

    with pytest.raises(PaymentRequiredError):
        await _resolve_response(_awaitable())


async def test_resolve_response_returns_clean_success():
    async def _awaitable():
        return json.dumps({"ok": True, "markdown": "# ok"}).encode()

    out = await _resolve_response(_awaitable())
    assert out["ok"] is True


# ---------------------------------------------------------------------------
# Envelope shapes — the scan must descend into `results` and detect the
# markdown-build envelope's status="failed" (else a default markdown scrape of
# a 404/blocked page is silently counted as a success).
# ---------------------------------------------------------------------------


def test_results_envelope_descends_and_raises():
    envelope = {
        "status": "failed",
        "results": [
            {"ok": False, "status": 404,
             "result_error": {"code": "target_http_error", "retryable": False, "target_status": 404}},
        ],
    }
    with pytest.raises(ScrapeError) as exc:
        _scan_result_error(envelope)
    assert exc.value.code == "target_http_error"
    assert exc.value.target_status == 404


def test_markdown_envelope_status_failed_raises_with_code():
    # The markdown-build shape: no ok/result_error at the top, only status="failed"
    # plus the canonical fields the API now also carries.
    md = {
        "format": "markdown", "markdown": "# 404 page", "status": "failed",
        "warnings": [], "code": "target_http_error", "target_status": 404,
        "result_error": {"code": "target_http_error", "retryable": False, "target_status": 404},
    }
    with pytest.raises(ScrapeError) as exc:
        _scan_result_error(md)
    assert exc.value.code == "target_http_error"
    assert exc.value.target_status == 404


def test_markdown_envelope_status_failed_without_code_still_raises():
    # Defensive: even if the API hasn't yet attached a code, status="failed" alone
    # must not be a fake success.
    md = {"format": "markdown", "markdown": "# err", "status": "failed", "warnings": []}
    with pytest.raises(ScrapeError):
        _scan_result_error(md)


def test_markdown_envelope_completed_passes_through():
    md = {"format": "markdown", "markdown": "# ok", "status": "completed", "warnings": []}
    assert _scan_result_error(md) is md
