"""Canonical GhostCrawl error codes.

This module is the SDK-side mirror of the server's single source of truth
(``ghostcrawl/errors/codes.json``, generated from the server error catalog).
The values here are copied verbatim from that catalog so the SDK never invents
its own vocabulary — keep them in lockstep when the catalog changes.

Two channels (see :data:`CHANNELS`):

* ``problem`` — OUR failure. The API returns a non-2xx
  ``application/problem+json`` body. The facade raises a typed exception keyed
  on the ``code`` (e.g. ``payment_required`` → ``PaymentRequiredError``,
  ``rate_limited`` → ``RateLimitError``).
* ``result`` — TARGET failure. The API returns HTTP 200 with a result envelope
  carrying ``ok: false`` + ``result_error: {code, retryable, target_status?}``.
  The facade raises :class:`ghostcrawl.ScrapeError` so a blocked / timed-out /
  errored scrape is never silently a success.
"""

from __future__ import annotations

from typing import Dict, NamedTuple

CHANNELS: Dict[str, str] = {
    "problem": "OUR failure -> non-2xx application/problem+json",
    "result": "TARGET failure -> HTTP 200 + result_error{code,retryable}",
}


class ErrorCode(NamedTuple):
    """One canonical error code and its catalog metadata."""

    code: str
    http: int
    retryable: bool
    channel: str
    title: str
    retry_after: int | None


# --- Generated from ghostcrawl/errors/codes.json (do not hand-diverge) -------
ERROR_CODES: Dict[str, ErrorCode] = {
    "bad_request": ErrorCode("bad_request", 400, False, "problem", "Malformed request", None),
    "unauthorized": ErrorCode("unauthorized", 401, False, "problem", "Authentication required", None),
    "forbidden": ErrorCode("forbidden", 403, False, "problem", "Insufficient permissions", None),
    "payment_required": ErrorCode("payment_required", 402, False, "problem", "Payment required", None),
    "not_found": ErrorCode("not_found", 404, False, "problem", "Resource not found", None),
    "conflict": ErrorCode("conflict", 409, False, "problem", "Resource conflict", None),
    "byo_proxy_invalid": ErrorCode("byo_proxy_invalid", 422, False, "problem", "BYO proxy URL invalid", None),
    "tier_unavailable": ErrorCode("tier_unavailable", 400, False, "problem", "Requested proxy tier unavailable", None),
    "rate_limited": ErrorCode("rate_limited", 429, True, "problem", "Rate limit exceeded", 5),
    "quota_backend_unavailable": ErrorCode("quota_backend_unavailable", 503, True, "problem", "Rate-limit service unavailable", 5),
    "pool_exhausted": ErrorCode("pool_exhausted", 503, True, "problem", "Proxy pool exhausted", 10),
    "egress_integrity_failed": ErrorCode("egress_integrity_failed", 503, True, "problem", "Egress integrity check failed", 5),
    "render_hung": ErrorCode("render_hung", 503, True, "problem", "Render did not progress (page wedged)", 5),
    "engine_crashed": ErrorCode("engine_crashed", 503, True, "problem", "Rendering engine crashed", 5),
    "render_timeout": ErrorCode("render_timeout", 504, True, "problem", "Render exceeded its time budget", 5),
    "engine_timeout": ErrorCode("engine_timeout", 504, True, "problem", "Request was not completed in time", 5),
    "service_unavailable": ErrorCode("service_unavailable", 503, True, "problem", "Service temporarily unavailable", 5),
    "internal_error": ErrorCode("internal_error", 500, True, "problem", "Internal server error", None),
    "target_http_error": ErrorCode("target_http_error", 200, False, "result", "Target returned an HTTP error", None),
    "navigation_failed": ErrorCode("navigation_failed", 200, False, "result", "Could not reach the target", None),
    "blocked": ErrorCode("blocked", 200, True, "result", "Blocked by the target's anti-bot protection", None),
    "captcha_required": ErrorCode("captcha_required", 200, True, "result", "The target presented a CAPTCHA", None),
    "empty_content": ErrorCode("empty_content", 200, False, "result", "No extractable content", None),
}

#: Frozen tuple of every canonical code string.
ALL_CODES = tuple(ERROR_CODES.keys())

#: Codes whose ``channel`` is ``"result"`` (TARGET failures returned on HTTP 200).
RESULT_CODES = frozenset(c for c, e in ERROR_CODES.items() if e.channel == "result")

#: Codes whose ``channel`` is ``"problem"`` (OUR failures returned as non-2xx).
PROBLEM_CODES = frozenset(c for c, e in ERROR_CODES.items() if e.channel == "problem")


def is_retryable(code: str | None) -> bool:
    """Return the catalog ``retryable`` flag for ``code`` (False if unknown)."""
    entry = ERROR_CODES.get(code or "")
    return bool(entry.retryable) if entry is not None else False


__all__ = [
    "CHANNELS",
    "ErrorCode",
    "ERROR_CODES",
    "ALL_CODES",
    "RESULT_CODES",
    "PROBLEM_CODES",
    "is_retryable",
]
