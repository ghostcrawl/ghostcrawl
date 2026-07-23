"""GhostCrawl idiomatic facade — delegates to the Kiota-generated canonical core.

Architecture:
  _generated/ Kiota core  — spec-faithful 98-op request-builder, models, auth/transport
  This FACADE              — thin async ergonomic layer that calls the generated builders

All HTTP transport, auth, serialization, and model types come from the generated core.
The facade maps idiomatic calls (client.scrape(url=...)) to generated builders
(self._core.v1.scrape.post(body)) and returns plain dicts for JSON-serializable responses.

Async convention:
  Every method is ``async``. For one-off scripts, use ``asyncio.run()``:

      import asyncio
      from ghostcrawl import GhostCrawlClient
      client = GhostCrawlClient(token="gck_live_YOUR_KEY")
      result = asyncio.run(client.scrape(url="https://example.com"))

Usage::

    import asyncio
    from ghostcrawl import GhostCrawlClient

    async def main():
        async with GhostCrawlClient(token="gck_live_YOUR_KEY") as client:
            result = await client.scrape(url="https://example.com")
            run = await client.crawl_runs.start(url="https://example.com")
            results = await client.search(query="latest AI news")
    asyncio.run(main())
"""

from __future__ import annotations

import json
import os
import time
import typing

from kiota_abstractions.authentication import (
    AccessTokenProvider,
    AllowedHostsValidator,
    BaseBearerTokenAuthenticationProvider,
)
from kiota_abstractions.api_error import APIError as _KiotaAPIError
from kiota_http.httpx_request_adapter import HttpxRequestAdapter

# _generated/ lives at sdks/python/_generated/ (sibling to ghostcrawl/).
# Include _generated* in pyproject.toml packages.find so it ships with the SDK.
from _generated.ghostcrawl_client import GhostCrawlClient as _KiotaClient  # type: ignore[import]

# Public ghostcrawl error classes (the ones re-exported from the package root).
# Aliased so transport errors from the generated core can be re-raised as the
# documented types without colliding with the facade-local classes below.
from .errors.identity_errors import (
    APIError as _PublicAPIError,
    AuthenticationError as _PublicAuthenticationError,
    InvalidRequestError as _PublicInvalidRequestError,
)

# Canonical error catalog (mirror of ghostcrawl/errors/codes.json). Used to map
# the problem+json ``code`` and the result-envelope ``result_error.code`` onto
# typed exceptions and the ``retryable`` flag.
from .errors.codes import ALL_CODES, RESULT_CODES, is_retryable as _is_retryable

_DEFAULT_BASE_URL = "https://api.ghostcrawl.io"


# ---------------------------------------------------------------------------
# Error types (kept on the facade — these are the user-facing error classes)
# ---------------------------------------------------------------------------


class GhostCrawlError(Exception):
    """Base error from the GhostCrawl API.

    Carries the canonical, machine-readable fields from the two-channel error
    model so callers can branch on ``code`` / ``retryable`` without parsing the
    message:

    Attributes
    ----------
    status_code : int
        HTTP status of the response (0 for transport errors with no response).
    code : str or None
        The canonical error code from the catalog (e.g. ``"rate_limited"``,
        ``"blocked"``). ``None`` if the server did not supply one.
    retryable : bool
        Whether the catalog marks this failure as retryable.
    retry_after : int or None
        Seconds to wait before retrying, when the server advertised one.
    request_id : str or None
        The ``instance`` field of the problem+json body (the request id) — quote
        this to support when reporting an OUR-side failure.
    body : Any
        The parsed response body, when available.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 0,
        body: typing.Optional[typing.Any] = None,
        *,
        code: typing.Optional[str] = None,
        retryable: bool = False,
        retry_after: typing.Optional[int] = None,
        request_id: typing.Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body
        self.code = code
        self.retryable = retryable
        self.retry_after = retry_after
        self.request_id = request_id


class AuthenticationError(GhostCrawlError):
    """Raised on 401 — missing or invalid API key."""


class RateLimitError(GhostCrawlError):
    """Raised on 429 — rate limit reached (retryable; honour ``retry_after``)."""


class PaymentRequiredError(GhostCrawlError):
    """Raised on 402 — usage or spend limit reached."""


class InvalidRequestError(GhostCrawlError):
    """Raised on 400/422 — bad request parameters."""


class APIError(GhostCrawlError):
    """Raised on 5xx server errors (and other OUR-side problem responses)."""


class ScrapeError(GhostCrawlError):
    """Raised when a 200 response reports a TARGET-side failure.

    The scrape reached the API fine, but the *target* failed in a way that
    means the result is not usable — the site blocked us (``blocked``),
    presented a CAPTCHA (``captcha_required``), returned an HTTP error
    (``target_http_error`` with ``target_status``), could not be reached
    (``navigation_failed``), or yielded no extractable content
    (``empty_content``). This prevents a blocked / errored scrape from being
    silently counted as a success.

    Attributes
    ----------
    target_status : int or None
        The target's HTTP status code, when the failure was ``target_http_error``.
    reason : str or None
        An optional finer-grained sub-reason (e.g. ``"dns_error"``).
    """

    def __init__(
        self,
        message: str,
        *,
        code: typing.Optional[str] = None,
        retryable: bool = False,
        target_status: typing.Optional[int] = None,
        reason: typing.Optional[str] = None,
        request_id: typing.Optional[str] = None,
        body: typing.Optional[typing.Any] = None,
    ) -> None:
        super().__init__(
            message,
            status_code=200,
            body=body,
            code=code,
            retryable=retryable,
            request_id=request_id,
        )
        self.target_status = target_status
        self.reason = reason


# ---------------------------------------------------------------------------
# Kiota auth wiring: static-token access-token provider
# ---------------------------------------------------------------------------


class _BodyCapturingHttpxRequestAdapter(HttpxRequestAdapter):
    """HttpxRequestAdapter that preserves the problem+json body on error responses.

    Kiota's adapter raises a bare ``APIError`` (with only headers, no body) when
    the response status is not in a route's ``error_map`` — which is the case for
    401 / 402 / 429 (the generated builders map only 422). The human-readable
    server ``detail`` / ``title`` was therefore lost, leaving the typed error's
    message as the kiota repr ("no error class is registered for code N").

    This override reads the response body (available at this point) and attaches
    the parsed problem+json dict onto the raised exception as ``error`` so
    :func:`_problem_body` can recover ``detail`` / ``code`` / ``instance``. It is
    transparent on the success path and never swallows the exception.
    """

    async def throw_failed_responses(
        self, response, error_map, parent_span, attribute_span
    ):  # type: ignore[override]
        if response.is_success or response.status_code == 304:
            return await super().throw_failed_responses(
                response, error_map, parent_span, attribute_span
            )
        # Capture the body BEFORE delegating (super() raises). content-type is the
        # problem+json the API emits for OUR-side failures.
        captured: typing.Optional[dict] = None
        try:
            ctype = response.headers.get("content-type", "")
            if "json" in ctype:
                captured = response.json()
        except Exception:  # pragma: no cover - defensive; never block the raise
            captured = None
        try:
            await super().throw_failed_responses(
                response, error_map, parent_span, attribute_span
            )
        except _KiotaAPIError as exc:
            # Only fill in when Kiota didn't already attach a deserialized body.
            if isinstance(captured, dict) and getattr(exc, "error", None) is None:
                try:
                    exc.error = captured  # type: ignore[attr-defined]
                except Exception:  # pragma: no cover - defensive
                    pass
            raise


class _StaticTokenProvider(AccessTokenProvider):
    """Wraps a static bearer token as a Kiota AccessTokenProvider."""

    def __init__(self, token: str) -> None:
        self._token = token

    async def get_authorization_token(
        self,
        uri: str,
        additional_authentication_context: typing.Optional[
            dict[str, typing.Any]
        ] = None,
    ) -> str:
        return self._token

    def get_allowed_hosts_validator(self) -> AllowedHostsValidator:
        # Allow all hosts (the validator accepts an empty set = no restriction)
        return AllowedHostsValidator()


# ---------------------------------------------------------------------------
# Response helper: Kiota returns bytes for most endpoints; decode to dict
# ---------------------------------------------------------------------------


def _bytes_to_dict(raw: typing.Optional[bytes]) -> dict:
    """Decode bytes JSON response from the Kiota adapter to a plain dict."""
    if raw is None:
        return {}
    if isinstance(raw, (bytes, bytearray)):
        return json.loads(raw.decode("utf-8"))
    # Already deserialized (Parsable objects from typed endpoints)
    if hasattr(raw, "__dict__"):
        return _parsable_to_dict(raw)
    return raw  # type: ignore[return-value]


def _parsable_to_dict(obj: typing.Any, _seen: typing.Optional[set] = None) -> typing.Any:
    """Recursively convert a Kiota Parsable dataclass to a plain dict."""
    if _seen is None:
        _seen = set()
    obj_id = id(obj)
    if obj_id in _seen:
        return None
    _seen.add(obj_id)

    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, (list, tuple)):
        return [_parsable_to_dict(item, _seen) for item in obj]
    if isinstance(obj, dict):
        return {k: _parsable_to_dict(v, _seen) for k, v in obj.items()}
    # Enum-like objects (Kiota generates enum wrappers with a .value attribute)
    if hasattr(obj, "value") and type(obj).__name__.endswith(
        ("_engine", "_format", "_mode", "_vertical", "_freshness", "_country")
    ):
        return obj.value
    # Kiota Parsable dataclasses have additional_data and typed fields
    if hasattr(obj, "__dataclass_fields__"):
        result = {}
        for field_name in obj.__dataclass_fields__:  # type: ignore[attr-defined]
            val = getattr(obj, field_name, None)
            if field_name == "additional_data" and isinstance(val, dict):
                for k, v in val.items():
                    result[k] = _parsable_to_dict(v, _seen)
            elif val is not None:
                result[field_name] = _parsable_to_dict(val, _seen)
        return result
    return str(obj)


# Fallback HTTP-status -> canonical-code map for problem responses that arrive
# without a problem+json ``code`` (so ``retryable`` is still inferred correctly).
_STATUS_TO_CODE: typing.Dict[int, str] = {
    400: "bad_request",
    401: "unauthorized",
    402: "payment_required",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    422: "byo_proxy_invalid",
    429: "rate_limited",
    500: "internal_error",
    503: "service_unavailable",
    504: "engine_timeout",
}


def _problem_body(exc: Exception) -> typing.Optional[dict]:
    """Best-effort extraction of an ``application/problem+json`` body from a
    Kiota ``APIError``.

    The generated core attaches the deserialized error response to ``.error``
    when an error mapping exists; otherwise the JSON often rides on the
    exception message. We try both so the canonical ``code`` / ``retryable`` /
    ``retry_after`` / ``instance`` fields can be recovered either way.
    """
    err = getattr(exc, "error", None)
    if isinstance(err, dict):
        return err
    if err is not None and hasattr(err, "__dataclass_fields__"):
        try:
            return _parsable_to_dict(err)  # type: ignore[return-value]
        except Exception:  # pragma: no cover - defensive
            pass
    # Some adapters serialize the body into the message; try to recover JSON.
    msg = getattr(exc, "message", None) or str(exc)
    if isinstance(msg, str) and "{" in msg:
        try:
            return json.loads(msg[msg.index("{") : msg.rindex("}") + 1])
        except Exception:
            return None
    return None


def _retry_after_from_headers(exc: Exception) -> typing.Optional[int]:
    """Read the ``Retry-After`` header (seconds) from a Kiota error, if present."""
    headers = getattr(exc, "response_headers", None)
    if not isinstance(headers, dict):
        return None
    raw = headers.get("Retry-After") or headers.get("retry-after")
    if isinstance(raw, (list, tuple)):
        raw = raw[0] if raw else None
    try:
        return int(raw) if raw is not None else None
    except (TypeError, ValueError):
        return None


def _translate_kiota_error(exc: Exception) -> Exception:
    """Map a Kiota transport ``APIError`` onto the public ghostcrawl error types.

    The generated core raises ``kiota_abstractions.api_error.APIError`` with a
    ``response_status_code`` attribute and (when an error mapping exists) the
    deserialized problem+json body. This maps the canonical ``code`` (preferred)
    and the HTTP status onto the typed ``ghostcrawl`` error classes, carrying the
    ``retryable`` / ``retry_after`` / ``request_id`` fields so callers can route
    retries without re-parsing the body.

    Previously this only handled 401 / 422 and silently flattened 402 and 429
    into a generic ``APIError`` — that drop is fixed here.
    """
    status = getattr(exc, "response_status_code", None)
    if status is None:
        return exc

    body = _problem_body(exc)
    code = body.get("code") if isinstance(body, dict) else None
    if code not in ALL_CODES:
        code = None
    # When the server didn't deliver a code, infer the canonical one from the
    # HTTP status so ``retryable`` is still correct (e.g. a bare 429 is
    # retryable even with no problem+json body).
    if code is None:
        code = _STATUS_TO_CODE.get(status)
    # request_id rides on the problem+json ``instance`` field.
    request_id = None
    if isinstance(body, dict):
        request_id = body.get("instance") or body.get("request_id")
    retry_after = None
    if isinstance(body, dict) and isinstance(body.get("retry_after"), int):
        retry_after = body["retry_after"]
    if retry_after is None:
        retry_after = _retry_after_from_headers(exc)
    retryable = bool(body.get("retryable")) if isinstance(body, dict) and "retryable" in body else _is_retryable(code)

    # Prefer the server's problem+json human message (``detail``, then ``title``)
    # over the kiota repr ("no error class is registered for code N"), which is
    # what ``str(exc)`` returns when the status was not in the route error map.
    message = (
        (body.get("detail") or body.get("title"))
        if isinstance(body, dict)
        else None
    ) or str(exc) or f"HTTP {status}"

    common = dict(
        status_code=status,
        body=body if body is not None else getattr(exc, "error", None),
        code=code,
        retryable=retryable,
        retry_after=retry_after,
        request_id=request_id,
    )

    # Prefer the canonical code; fall back to the HTTP status. Both 401/402/429
    # below now resolve regardless of whether a code was delivered.
    if code == "unauthorized" or status == 401:
        return AuthenticationError(message, **common)
    if code == "payment_required" or status == 402:
        return PaymentRequiredError(message, **common)
    if code == "rate_limited" or status == 429:
        return RateLimitError(message, **common)
    if code in ("bad_request", "byo_proxy_invalid", "tier_unavailable") or status in (400, 422):
        return InvalidRequestError(message, **common)
    return APIError(message, **common)


def _normalize_scrape_content(result: typing.Any) -> None:
    """Surface the rendered output under the documented ``content`` key.

    The API returns the rendered page under a format-specific field
    (``markdown`` / ``html`` / ``text``); the SDK contract (and every quickstart)
    exposes it as ``result["content"]``. Mirror it in-place so the quickstart
    works regardless of ``format``, without dropping the format-specific key.
    """
    if not isinstance(result, dict) or "content" in result:
        return
    fmt = result.get("format")
    value = result.get(fmt) if isinstance(fmt, str) else None
    if not isinstance(value, str):
        for key in ("markdown", "html", "text"):
            candidate = result.get(key)
            if isinstance(candidate, str):
                value = candidate
                break
    if isinstance(value, str):
        result["content"] = value


def _scan_result_error(result: dict) -> dict:
    """Raise :class:`ScrapeError` when a 200 result reports a TARGET failure.

    The two-channel model returns target failures on HTTP 200 with
    ``ok: false`` plus a ``result_error`` envelope (and a top-level ``code``).
    Left unchecked, a blocked / timed-out / errored scrape looks like a success.
    This scans the decoded body and raises a typed error so it never is.

    A result is treated as a target failure when EITHER it carries a
    ``result_error`` object OR it has ``ok: false`` with a canonical
    result-channel ``code``. Results without those markers pass through
    unchanged.
    """
    if not isinstance(result, dict):
        return result

    # The scrape/extract APIs wrap per-URL results in a `results` envelope
    # ({"status": ..., "results": [{ok, result_error, ...}]}); the target failure
    # lives on the INNER result, not the envelope top level. Descend so a single
    # scrape of a 404/blocked/captcha page raises instead of looking like a success.
    inner = result.get("results")
    if isinstance(inner, list):
        for item in inner:
            _scan_result_error(item)  # raises ScrapeError on the first target failure
        return result

    result_error = result.get("result_error")
    top_code = result.get("code")
    ok = result.get("ok")
    status = result.get("status")

    code: typing.Optional[str] = None
    retryable = False
    target_status: typing.Optional[int] = None
    reason: typing.Optional[str] = None

    if isinstance(result_error, dict):
        code = result_error.get("code") or (top_code if isinstance(top_code, str) else None)
        retryable = bool(result_error.get("retryable"))
        ts = result_error.get("target_status")
        target_status = ts if isinstance(ts, int) else None
        reason = result_error.get("reason")
    elif ok is False and isinstance(top_code, str) and top_code in RESULT_CODES:
        code = top_code
        retryable = _is_retryable(code)
        ts = result.get("target_status")
        target_status = ts if isinstance(ts, int) else None
    elif status == "failed":
        # The markdown-build envelope ({markdown, status, warnings}) reports a target
        # failure ONLY via status="failed" — no ok/result_error/code. Without this branch
        # a 404/blocked/unreachable markdown scrape returns the error page AS IF it
        # succeeded ("never count a fake success"). The precise catalog code is absent on
        # this path (API follow-up), so surface a typed failure with the code we have.
        code = top_code if isinstance(top_code, str) else None
        ts = result.get("target_status")
        target_status = ts if isinstance(ts, int) else None
    else:
        return result

    title = code or "scrape failed"
    detail = f"Scrape failed ({title})"
    if target_status is not None:
        detail += f": target returned HTTP {target_status}"
    elif reason:
        detail += f": {reason}"
    raise ScrapeError(
        detail,
        code=code,
        retryable=retryable if retryable else _is_retryable(code),
        target_status=target_status,
        reason=reason,
        request_id=result.get("request_id") or result.get("instance"),
        body=result,
    )


async def _resolve_response(awaitable: typing.Awaitable) -> dict:
    """Await a generated builder call, translate errors, and scan the result.

    - A non-2xx problem+json response surfaces as a typed exception keyed on the
      canonical ``code`` (``_translate_kiota_error``).
    - A 200 response that reports a TARGET failure (``ok: false`` /
      ``result_error``) raises :class:`ScrapeError` (``_scan_result_error``).
    """
    try:
        raw = await awaitable
    except _KiotaAPIError as exc:
        raise _translate_kiota_error(exc) from exc
    return _scan_result_error(_bytes_to_dict(raw))


# ---------------------------------------------------------------------------
# Crawl-run completion — event-driven wait helpers
# ---------------------------------------------------------------------------

#: Terminal crawl-run states. A run in any of these has stopped moving; results
#: are present when the state is ``completed``. Anything else is still in flight.
TERMINAL_RUN_STATES: typing.FrozenSet[str] = frozenset(
    {"completed", "failed", "cancelled"}
)


def _run_is_terminal(run: typing.Mapping[str, typing.Any]) -> bool:
    """True when a crawl-run record has reached a terminal state."""
    return run.get("status") in TERMINAL_RUN_STATES


async def _resolve_run(awaitable: typing.Awaitable) -> dict:
    """Await a crawl-run builder call and return the run record.

    Unlike :func:`_resolve_response`, this does NOT apply scrape-envelope
    result-error scanning. A crawl-run's ``status`` field legitimately takes the
    terminal values ``failed`` / ``cancelled`` — those are the very run the
    caller is waiting for and must be RETURNED, not raised as a ``ScrapeError``
    (the ``status == "failed"`` scan branch is for the markdown-scrape envelope,
    a different shape). Transport / HTTP errors still surface as typed
    exceptions via :func:`_translate_kiota_error`.
    """
    try:
        raw = await awaitable
    except _KiotaAPIError as exc:
        raise _translate_kiota_error(exc) from exc
    return _bytes_to_dict(raw)


# ---------------------------------------------------------------------------
# Sub-clients — each holds a reference to the Kiota core v1 builder
# ---------------------------------------------------------------------------


class CrawlRunsClient:
    """Manage crawl runs — /v1/crawl-runs.

    Delegates to the generated ``v1.crawl_runs`` and ``v1.crawl.deep`` builders.
    """

    def __init__(self, core: _KiotaClient) -> None:
        self._core = core

    async def start(
        self,
        url: str,
        *,
        max_depth: int = 2,
        max_pages: int = 100,
        include_patterns: typing.Optional[list] = None,
        exclude_patterns: typing.Optional[list] = None,
        wait: bool = False,
        wait_timeout: int = 300,
        **kwargs: typing.Any,
    ) -> dict:
        """Start a new crawl run from a seed URL.

        Calls ``POST /v1/crawl-runs`` via the generated builder.

        Parameters
        ----------
        wait : bool
            When ``True``, start **and wait**: the server blocks event-driven
            (on the run's completion event, not a poll loop) until the run is
            terminal — ``completed`` / ``failed`` / ``cancelled`` — or
            ``wait_timeout`` seconds elapse, then returns the run record
            (results present when ``completed``). No client-side sleep loop.
        wait_timeout : int
            Overall completion budget in seconds when ``wait=True``. Sent to the
            server as ``timeout_s`` and used as the client's re-arm deadline if
            the server's long-poll window is shorter than the full budget.
            Default 300.

        Returns
        -------
        dict
            The crawl-run record. With ``wait=True`` it is the terminal run when
            it finished within ``wait_timeout``; otherwise the latest
            (non-terminal) run so the caller may :meth:`wait` again.
        """
        from _generated.v1.crawl_runs.crawl_runs_post_request_body import (
            CrawlRunsPostRequestBody,
        )

        # The /v1/crawl-runs start action expects a ``seed_urls`` list, not a
        # single ``url`` field. Accept the convenient ``url`` argument and map
        # it onto the seed-URL list the API contract requires.
        body = CrawlRunsPostRequestBody()
        body.additional_data = {
            "seed_urls": [url],
            "max_depth": max_depth,
            "max_pages": max_pages,
            **kwargs,
        }
        if include_patterns is not None:
            body.additional_data["include_patterns"] = include_patterns
        if exclude_patterns is not None:
            body.additional_data["exclude_patterns"] = exclude_patterns
        if wait:
            # Event-driven start-and-wait: the server blocks until terminal or
            # timeout_s, then returns the run.
            body.additional_data["wait_until"] = "completed"
            body.additional_data["timeout_s"] = wait_timeout

        deadline = time.monotonic() + wait_timeout
        run = await _resolve_run(self._core.v1.crawl_runs.post(body))

        # If the server's long-poll window elapsed before the run went terminal,
        # re-arm across windows until terminal or the caller's budget is spent.
        if wait and not _run_is_terminal(run):
            run_id = run.get("run_id")
            remaining = deadline - time.monotonic()
            if run_id and remaining > 0:
                run = await self.wait(run_id, timeout=remaining)
        return run

    async def wait(
        self,
        run_id: str,
        *,
        timeout: float = 300,
    ) -> dict:
        """Block until a crawl run reaches a terminal state, event-driven.

        Issues ``GET /v1/crawl-runs/{run_id}?wait=true&timeout_s=…``. Each call
        blocks **server-side** on the run's completion event until the run is
        terminal or the server's long-poll window elapses; the loop only re-arms
        across windows until the run is terminal or the overall ``timeout``
        budget is spent. There is **no fixed client-side sleep** — this replaces
        a hand-written poll-with-``sleep`` loop with server-blocking long-poll.

        Parameters
        ----------
        run_id : str
            The run to wait on.
        timeout : float
            Overall wall-clock budget in seconds. Default 300.

        Returns
        -------
        dict
            The terminal run record, or — if ``timeout`` elapses first — the
            latest non-terminal run (HTTP 200), which the caller may wait on
            again.
        """
        import urllib.parse

        base = (self._core.request_adapter.base_url or "").rstrip("/")
        deadline = time.monotonic() + timeout
        run: dict = {}
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return run
            # Ask the server to block for (at most) the remaining budget; it may
            # return sooner when its own long-poll window is shorter. The item
            # GET builder template carries no query slot, so stamp the long-poll
            # params onto a raw URL (kiota expands recognized template params
            # only) and let ``with_url`` route it verbatim.
            query = urllib.parse.urlencode(
                {"wait": "true", "timeout_s": max(int(remaining), 1)}
            )
            raw_url = f"{base}/v1/crawl-runs/{urllib.parse.quote(str(run_id))}?{query}"
            builder = self._core.v1.crawl_runs.by_run_id(run_id).with_url(raw_url)
            run = await _resolve_run(builder.get())
            if _run_is_terminal(run):
                return run

    async def list(
        self,
        *,
        limit: int = 20,
        cursor: typing.Optional[str] = None,
    ) -> dict:
        """List crawl runs.

        Calls ``GET /v1/crawl-runs`` via the generated builder.
        """
        from kiota_abstractions.base_request_configuration import RequestConfiguration

        config: RequestConfiguration = RequestConfiguration()
        config.query_parameters = {"limit": limit}
        if cursor is not None:
            config.query_parameters["cursor"] = cursor
        return await _resolve_response(self._core.v1.crawl_runs.get(config))

    async def get(self, run_id: str) -> dict:
        """Get a single crawl run by ID.

        Calls ``GET /v1/crawl-runs/{run_id}`` via the generated builder.
        """
        return await _resolve_response(self._core.v1.crawl_runs.by_run_id(run_id).get())

    async def cancel(self, run_id: str) -> dict:
        """Cancel a running crawl run.

        Calls ``POST /v1/crawl-runs/{run_id}/cancel`` via the generated builder.
        """
        return await _resolve_response(
            self._core.v1.crawl_runs.by_run_id(run_id).cancel.post(None)
        )


class SessionsClient:
    """Manage browser sessions — /v1/sessions."""

    def __init__(self, core: _KiotaClient) -> None:
        self._core = core

    async def list(self) -> dict:
        """List all active sessions."""
        return await _resolve_response(self._core.v1.sessions.get())

    async def create(self, *, profile_name: str, **kwargs: typing.Any) -> dict:
        """Create a new browser session.

        Calls ``POST /v1/sessions/create`` via the generated builder.
        """
        from _generated.models.session_create_request import SessionCreateRequest
        from _generated.models.session_create_request_profile import (
            SessionCreateRequest_profile,
        )

        body = SessionCreateRequest()
        profile_wrapper = SessionCreateRequest_profile()
        profile_wrapper.string = profile_name
        body.profile = profile_wrapper
        body.additional_data = kwargs
        return await _resolve_response(self._core.v1.sessions.create.post(body))

    async def extend(self, session_id: str, *, duration_seconds: int = 300) -> dict:
        """Extend a session's TTL.

        Sends ``{"ttl_seconds": <duration_seconds>}`` — the generated
        ``ExtendRequestBuilder.post`` rejects a null body, and the new TTL is
        carried by the ``ttl_seconds`` field (30s..24h).
        """
        from _generated.models.extend_body import ExtendBody
        from _generated.models.extend_body_ttl_seconds import (
            ExtendBody_ttl_seconds,
        )

        body = ExtendBody()
        ttl_wrapper = ExtendBody_ttl_seconds()
        ttl_wrapper.integer = duration_seconds
        body.ttl_seconds = ttl_wrapper
        return await _resolve_response(
            self._core.v1.sessions.by_profile_id(session_id).extend.post(body)
        )

    async def release(self, session_id: str) -> dict:
        """Release a session back to the pool."""
        return await _resolve_response(
            self._core.v1.sessions.by_profile_id(session_id).release.post(None)
        )


class ProfilesClient:
    """Manage identity profiles — /v1/profiles."""

    def __init__(self, core: _KiotaClient) -> None:
        self._core = core

    async def list(self) -> dict:
        """List all profiles."""
        return await _resolve_response(self._core.v1.profiles.get())

    async def get(self, name: str) -> dict:
        """Get a profile by name."""
        return await _resolve_response(self._core.v1.profiles.by_name(name).get())

    async def create(self, name: str, **config: typing.Any) -> dict:
        """Create a new profile."""
        from _generated.models.profile_create_request import ProfileCreateRequest

        body = ProfileCreateRequest()
        body.name = name
        body.additional_data = config
        return await _resolve_response(self._core.v1.profiles.post(body))

    async def update(self, name: str, **config: typing.Any) -> dict:
        """Update a profile."""
        from _generated.models.profile_update_request import ProfileUpdateRequest

        body = ProfileUpdateRequest()
        body.additional_data = config
        return await _resolve_response(self._core.v1.profiles.by_name(name).put(body))

    async def delete(self, name: str) -> dict:
        """Delete a profile."""
        raw = await self._core.v1.profiles.by_name(name).delete()
        return _bytes_to_dict(raw) if raw else {}


class WebhooksClient:
    """Manage webhooks — /v1/webhooks."""

    def __init__(self, core: _KiotaClient) -> None:
        self._core = core

    async def list(self) -> dict:
        """List all webhooks."""
        return await _resolve_response(self._core.v1.webhooks.get())

    async def get(self, webhook_id: str) -> dict:
        """Get a webhook by ID."""
        return await _resolve_response(self._core.v1.webhooks.by_webhook_id(webhook_id).get())

    async def create(
        self,
        url: str,
        *,
        event_types: typing.Optional[list] = None,
        events: typing.Optional[list] = None,
        **kwargs: typing.Any,
    ) -> dict:
        """Register a new webhook endpoint.

        The API field is ``event_types``; ``events`` is accepted as a
        back-compat alias for it.
        """
        from _generated.models.webhook_create_request import WebhookCreateRequest

        body = WebhookCreateRequest()
        body.url = url  # type: ignore[assignment]
        et = event_types if event_types is not None else events
        if et is not None:
            body.additional_data = {"event_types": et, **kwargs}
        else:
            body.additional_data = kwargs
        return await _resolve_response(self._core.v1.webhooks.post(body))

    async def delete(self, webhook_id: str) -> dict:
        """Delete a webhook."""
        raw = await self._core.v1.webhooks.by_webhook_id(webhook_id).delete()
        return _bytes_to_dict(raw) if raw else {}

    async def rotate_secret(self, webhook_id: str) -> dict:
        """Rotate the signing secret for a webhook."""
        return await _resolve_response(
            self._core.v1.webhooks.by_webhook_id(webhook_id).rotate_secret.post(None)
        )


class SchedulesClient:
    """Manage schedules — /v1/schedules."""

    def __init__(self, core: _KiotaClient) -> None:
        self._core = core

    async def list(self) -> dict:
        """List all schedules."""
        return await _resolve_response(self._core.v1.schedules.get())

    async def get(self, schedule_id: str) -> dict:
        """Get a schedule by ID."""
        return await _resolve_response(self._core.v1.schedules.by_schedule_id(schedule_id).get())

    async def create(self, cron: str, *, task: dict, **kwargs: typing.Any) -> dict:
        """Create a new schedule."""
        from _generated.models.schedule_create_request import ScheduleCreateRequest

        body = ScheduleCreateRequest()
        body.cron_expr = cron  # ScheduleCreateRequest uses cron_expr field
        body.additional_data = {"task": task, **kwargs}
        return await _resolve_response(self._core.v1.schedules.post(body))

    async def delete(self, schedule_id: str) -> dict:
        """Delete a schedule."""
        raw = await self._core.v1.schedules.by_schedule_id(schedule_id).delete()
        return _bytes_to_dict(raw) if raw else {}


class DatasetsClient:
    """Manage datasets — /v1/datasets."""

    def __init__(self, core: _KiotaClient) -> None:
        self._core = core

    async def list(self) -> dict:
        """List all datasets."""
        return await _resolve_response(self._core.v1.datasets.get())

    async def get(self, name: str) -> dict:
        """Get a dataset by name."""
        return await _resolve_response(self._core.v1.datasets.by_name(name).get())

    async def create(self, name: str, **kwargs: typing.Any) -> dict:
        """Create a new dataset."""
        from _generated.v1.datasets.datasets_post_request_body import (
            DatasetsPostRequestBody,
        )

        body = DatasetsPostRequestBody()
        body.additional_data = {"name": name, **kwargs}
        return await _resolve_response(self._core.v1.datasets.post(body))

    async def delete(self, name: str) -> dict:
        """Delete a dataset."""
        raw = await self._core.v1.datasets.by_name(name).delete()
        return _bytes_to_dict(raw) if raw else {}

    async def rows(self, name: str) -> dict:
        """Get rows from a dataset."""
        return await _resolve_response(self._core.v1.datasets.by_name(name).rows.get())

    async def append(self, name: str, rows: list) -> dict:
        """Append rows to a dataset."""
        from _generated.v1.datasets.item.rows.append.append_post_request_body import (
            AppendPostRequestBody,
        )

        body = AppendPostRequestBody()
        body.additional_data = {"rows": rows}
        return await _resolve_response(
            self._core.v1.datasets.by_name(name).rows.append.post(body)
        )


class RecordingsClient:
    """Manage session recordings — /v1/recordings."""

    def __init__(self, core: _KiotaClient) -> None:
        self._core = core

    async def list(self) -> dict:
        """List all recordings."""
        return await _resolve_response(self._core.v1.recordings.get())

    async def get(self, recording_id: str) -> dict:
        """Get a recording by ID."""
        return await _resolve_response(
            self._core.v1.recordings.by_recording_id(recording_id).get()
        )

    async def delete(self, recording_id: str) -> dict:
        """Delete a recording."""
        raw = await self._core.v1.recordings.by_recording_id(recording_id).delete()
        return _bytes_to_dict(raw) if raw else {}


class KVClient:
    """Key-value store — /v1/kv."""

    def __init__(self, core: _KiotaClient) -> None:
        self._core = core

    async def get(self, key: str) -> dict:
        """Get a value by key."""
        return await _resolve_response(self._core.v1.kv.by_key(key).get())

    async def set(self, key: str, value: typing.Any) -> dict:
        """Set a key-value pair."""
        from _generated.v1.kv.item.with_key_put_request_body import (
            WithKeyPutRequestBody,
        )

        body = WithKeyPutRequestBody()
        body.additional_data = {"value": value}
        return await _resolve_response(self._core.v1.kv.by_key(key).put(body))

    async def delete(self, key: str) -> dict:
        """Delete a key."""
        raw = await self._core.v1.kv.by_key(key).delete()
        return _bytes_to_dict(raw) if raw else {}


# ---------------------------------------------------------------------------
# Main facade
# ---------------------------------------------------------------------------


class GhostCrawlClient:
    """GhostCrawl idiomatic API client.

    Delegates all HTTP transport, auth, serialization, and model mapping to the
    Kiota-generated canonical core (``_generated/``). This facade is the shipped API.

    Every method is async. Use ``async with`` for automatic cleanup:

        async with GhostCrawlClient(token="gck_live_YOUR_KEY") as client:
            result = await client.scrape(url="https://example.com")

    Parameters
    ----------
    token : str, optional
        Your GhostCrawl API key (``gck_live_...``). If omitted, reads
        ``GHOSTCRAWL_API_KEY`` from the environment.
    api_key : str, optional
        Back-compat alias for ``token``. Existing code that constructed the old
        ``GhostCrawl(api_key=...)`` client keeps working — ``api_key`` is used
        when ``token`` is not supplied.
    base_url : str, optional
        Override the API base URL. Defaults to ``https://api.ghostcrawl.io``.
        Also reads ``GHOSTCRAWL_BASE_URL`` from the environment.

    Examples
    --------
    >>> import asyncio
    >>> from ghostcrawl import GhostCrawlClient
    >>> async def main():
    ...     client = GhostCrawlClient(token="gck_live_YOUR_KEY")
    ...     result = await client.scrape(url="https://example.com")
    ...     print(result)
    >>> asyncio.run(main())
    """

    def __init__(
        self,
        token: typing.Optional[str] = None,
        *,
        api_key: typing.Optional[str] = None,
        base_url: typing.Optional[str] = None,
        provider_config: typing.Optional[dict] = None,
    ) -> None:
        # ``api_key`` is the historical kwarg name (the pre-Kiota ``GhostCrawl``
        # client). Accept it as an alias for ``token`` so existing user code and
        # the CLI keep working without change. ``token`` wins when both are set.
        resolved_token = token or api_key or os.environ.get("GHOSTCRAWL_API_KEY", "")
        if not resolved_token:
            raise ValueError(
                "token is required (or set GHOSTCRAWL_API_KEY). "
                "Get your key at https://ghostcrawl.io. "
                "Run `ghostcrawl init` to configure."
            )
        resolved_base = (
            base_url or os.environ.get("GHOSTCRAWL_BASE_URL", "") or _DEFAULT_BASE_URL
        ).rstrip("/")
        self.base_url = resolved_base
        self._token = resolved_token
        # provider_config is the per-instance LLM model provider configuration.
        # Validated server-side; stored here for request-body injection on the
        # agent lane. NEVER include in logs — the api_key inside must not leak.
        # Passed explicitly by the caller; the SDK reads no environment variable
        # for it (that configuration is resolved server-side).
        self._provider_config: typing.Optional[dict] = provider_config

        # Build the Kiota adapter: static-token bearer provider → httpx adapter
        auth_provider = BaseBearerTokenAuthenticationProvider(
            _StaticTokenProvider(resolved_token)
        )
        # Body-capturing adapter so the problem+json `detail` survives onto the
        # raised error for statuses the generated builders don't error-map
        # (401/402/429) — see _BodyCapturingHttpxRequestAdapter.
        adapter = _BodyCapturingHttpxRequestAdapter(auth_provider)
        adapter.base_url = resolved_base

        # Instantiate the generated canonical core
        self._core = _KiotaClient(adapter)

        # Sub-clients (lazy initialization via property)
        self._crawl_runs: typing.Optional[CrawlRunsClient] = None
        self._sessions: typing.Optional[SessionsClient] = None
        self._profiles: typing.Optional[ProfilesClient] = None
        self._webhooks: typing.Optional[WebhooksClient] = None
        self._schedules: typing.Optional[SchedulesClient] = None
        self._datasets: typing.Optional[DatasetsClient] = None
        self._recordings: typing.Optional[RecordingsClient] = None
        self._kv: typing.Optional[KVClient] = None

    # Context manager support

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        if hasattr(self._core.request_adapter, "_http_client"):
            http = self._core.request_adapter._http_client  # type: ignore[attr-defined]
            if hasattr(http, "aclose"):
                await http.aclose()

    async def __aenter__(self) -> "GhostCrawlClient":
        return self

    async def __aexit__(self, *_: typing.Any) -> None:
        await self.aclose()

    # ------------------------------------------------------------------
    # Sub-client properties (lazy-initialized, share the core)
    # ------------------------------------------------------------------

    @property
    def crawl_runs(self) -> CrawlRunsClient:
        """Crawl run management."""
        if self._crawl_runs is None:
            self._crawl_runs = CrawlRunsClient(self._core)
        return self._crawl_runs

    @property
    def sessions(self) -> SessionsClient:
        """Browser session management."""
        if self._sessions is None:
            self._sessions = SessionsClient(self._core)
        return self._sessions

    @property
    def profiles(self) -> ProfilesClient:
        """Identity profile management."""
        if self._profiles is None:
            self._profiles = ProfilesClient(self._core)
        return self._profiles

    @property
    def webhooks(self) -> WebhooksClient:
        """Webhook management."""
        if self._webhooks is None:
            self._webhooks = WebhooksClient(self._core)
        return self._webhooks

    @property
    def schedules(self) -> SchedulesClient:
        """Schedule management."""
        if self._schedules is None:
            self._schedules = SchedulesClient(self._core)
        return self._schedules

    @property
    def datasets(self) -> DatasetsClient:
        """Dataset management."""
        if self._datasets is None:
            self._datasets = DatasetsClient(self._core)
        return self._datasets

    @property
    def recordings(self) -> RecordingsClient:
        """Recording management."""
        if self._recordings is None:
            self._recordings = RecordingsClient(self._core)
        return self._recordings

    @property
    def kv(self) -> KVClient:
        """Key-value store."""
        if self._kv is None:
            self._kv = KVClient(self._core)
        return self._kv

    # ------------------------------------------------------------------
    # Core operations — delegate to generated builders
    # ------------------------------------------------------------------

    async def scrape(
        self,
        url: str,
        *,
        format: str = "markdown",
        engine: str = "auto",
        javascript: bool = True,
        extract_schema: typing.Optional[dict] = None,
        **kwargs: typing.Any,
    ) -> dict:
        """Scrape a single URL and return the rendered content.

        Delegates to ``POST /v1/scrape`` via the generated ``ScrapeRequestBuilder``.

        Parameters
        ----------
        url : str
            Target URL to scrape.
        format : str
            Output format: ``"markdown"`` (default), ``"html"``, ``"text"``.
        engine : str
            Browser engine: ``"auto"`` (default), ``"chrome"``, ``"firefox"``,
            ``"webkit"``.
        javascript : bool
            Enable JavaScript rendering. Default ``True``.
        extract_schema : dict, optional
            JSON Schema for structured data extraction alongside the scrape.

        Returns
        -------
        dict
            Response with ``content``, ``url``, ``status``, and optional
            ``extracted`` fields.

        Raises
        ------
        AuthenticationError
            On 401 — missing or invalid API key.
        PaymentRequiredError
            On 402 — usage limit reached.
        RateLimitError
            On 429 — rate limit reached.
        APIError
            On 5xx server errors.
        """
        from _generated.models.scrape_request import ScrapeRequest
        from _generated.models.scrape_request_engine import ScrapeRequest_engine
        from _generated.models.scrape_request_format import ScrapeRequest_format
        from _generated.models.scrape_request_url import ScrapeRequest_url

        body = ScrapeRequest()
        url_wrapper = ScrapeRequest_url()
        url_wrapper.string = url
        body.url = url_wrapper
        body.engine = ScrapeRequest_engine(engine)
        body.format = ScrapeRequest_format(format)
        body.additional_data = {
            "javascript_enabled": javascript,
            **kwargs,
        }
        if extract_schema is not None:
            body.additional_data["extract_schema"] = extract_schema
        result = await _resolve_response(self._core.v1.scrape.post(body))
        _normalize_scrape_content(result)
        return result

    async def search(
        self,
        query: str,
        *,
        engine: str = "google",
        limit: int = 10,
        provider_key: typing.Optional[str] = None,
        **kwargs: typing.Any,
    ) -> dict:
        """Search the web and return results.

        Delegates to ``POST /v1/search`` via the generated ``SearchRequestBuilder``.

        Parameters
        ----------
        query : str
            Search query string.
        engine : str
            Search engine: ``"google"`` (default), ``"bing"``, ``"duckduckgo"``.
        limit : int
            Maximum number of results to return. Default 10.
        provider_key : str, optional
            Your own search-backend API key (BYO). ``/v1/search`` charges no
            markup — you pay the provider directly. When supplied, it is sent as
            the ``X-Provider-Authorization: Bearer <provider_key>`` header the
            backend requires (without it the API replies
            ``401 search_backend_key_missing``).

        Returns
        -------
        dict
            Response with ``results`` list and ``query`` metadata.
        """
        from _generated.models.search_request import SearchRequest
        from _generated.models.search_request_engine import SearchRequest_engine

        body = SearchRequest()
        body.query = query
        # SearchRequest_engine is a ComposedTypeWrapper — set .string for plain str values
        engine_wrapper = SearchRequest_engine()
        engine_wrapper.string = engine
        body.engine = engine_wrapper
        body.limit = limit
        body.additional_data = kwargs

        config = None
        if provider_key is not None:
            from kiota_abstractions.base_request_configuration import (
                RequestConfiguration,
            )

            config = RequestConfiguration()
            config.headers.add(
                "X-Provider-Authorization", f"Bearer {provider_key}"
            )
        return await _resolve_response(self._core.v1.search.post(body, config))

    async def extract(
        self,
        url: str,
        *,
        schema: dict,
        **kwargs: typing.Any,
    ) -> dict:
        """Extract structured data from a URL using a JSON Schema.

        Delegates to ``POST /v1/extract`` via the generated ``ExtractRequestBuilder``.

        Parameters
        ----------
        url : str
            Target URL to extract from.
        schema : dict
            JSON Schema describing the shape to extract.

        Returns
        -------
        dict
            Extracted data matching the provided schema.
        """
        from _generated.models.extract_request import ExtractRequest
        from _generated.models.extract_request_url import ExtractRequest_url

        body = ExtractRequest()
        url_wrapper = ExtractRequest_url()
        url_wrapper.string = url
        body.url = url_wrapper
        body.additional_data = {"schema": schema, **kwargs}
        return await _resolve_response(self._core.v1.extract.post(body))

    async def crawl(
        self,
        url: str,
        *,
        max_depth: int = 2,
        max_pages: int = 100,
        wait: bool = False,
        wait_timeout: int = 300,
        **kwargs: typing.Any,
    ) -> dict:
        """Start a deep crawl from a seed URL.

        Delegates to ``POST /v1/crawl/deep`` via the generated ``DeepRequestBuilder``.

        Parameters
        ----------
        url : str
            Seed URL.
        max_depth : int
            Maximum crawl depth. Default 2.
        max_pages : int
            Maximum pages to crawl. Default 100.
        wait : bool
            When ``True``, start **and wait**: the server blocks event-driven
            until the run is terminal (``completed`` / ``failed`` /
            ``cancelled``) or ``wait_timeout`` seconds elapse, then returns the
            run record (results present when ``completed``). No client poll loop.
        wait_timeout : int
            Overall completion budget in seconds when ``wait=True``. Default 300.

        Returns
        -------
        dict
            Crawl run record with ``run_id``. With ``wait=True`` it is the
            terminal run when it finished within ``wait_timeout``; otherwise the
            latest non-terminal run, which may be waited on again via
            ``client.crawl_runs.wait(run_id)``.
        """
        from _generated.models.deep_crawl_body import DeepCrawlBody

        body = DeepCrawlBody()
        body.max_depth = max_depth
        body.max_urls = max_pages
        body.additional_data = {"seed_urls": [url], **kwargs}
        if wait:
            body.additional_data["wait_until"] = "completed"
            body.additional_data["timeout_s"] = wait_timeout

        deadline = time.monotonic() + wait_timeout
        run = await _resolve_run(self._core.v1.crawl.deep.post(body))

        # Re-arm across server long-poll windows until terminal or budget spent.
        if wait and not _run_is_terminal(run):
            run_id = run.get("run_id")
            remaining = deadline - time.monotonic()
            if run_id and remaining > 0:
                run = await self.crawl_runs.wait(run_id, timeout=remaining)
        return run

    async def map(self, url: str, **kwargs: typing.Any) -> dict:
        """Map all URLs reachable from a seed URL.

        Delegates to ``POST /v1/map`` via the generated ``MapRequestBuilder``.

        Parameters
        ----------
        url : str
            Seed URL to start mapping from.

        Returns
        -------
        dict
            Response with ``urls`` list and crawl metadata.
        """
        from _generated.models.map_body import MapBody

        body = MapBody()
        body.url = url  # MapBody has a direct `url: Optional[str]` field
        if kwargs:
            body.additional_data = kwargs
        try:
            result = await self._core.v1.map.post(body)
        except _KiotaAPIError as exc:
            raise _translate_kiota_error(exc) from exc
        # map returns a MapResponse (typed Parsable), not bytes
        if result is None:
            return {}
        if isinstance(result, (bytes, bytearray)):
            return json.loads(result.decode("utf-8"))
        return _parsable_to_dict(result)

    async def agent(
        self,
        *,
        instruction: typing.Optional[str] = None,
        url: typing.Optional[str] = None,
        steps: typing.Optional[list] = None,
        task: typing.Optional[dict] = None,
        **kwargs: typing.Any,
    ) -> dict:
        """Execute an agent task via ``POST /v1/agent``.

        When ``provider_config`` was supplied at construction time, it is merged
        into the request body so the server routes through the configured LLM
        provider. The agent capability is gated per account — when it is not
        enabled the API replies ``404 not_found``; this returns that
        ``problem+json`` body as a dict (carrying ``detail``) rather than
        raising, so callers can branch on ``"detail" in response``.

        Routed through the Kiota request adapter (auth + base URL + transport) —
        the generated core has no ``agent`` builder (the route is absent from the
        customer-facing OpenAPI).

        Parameters
        ----------
        instruction : str, optional
            Natural-language instruction (required unless ``task`` is given).
        url : str, optional
            Target URL, passed as ``task.start_url`` when ``task`` is not given.
        steps : list, optional
            Explicit step list for ``task.steps``.
        task : dict, optional
            Full task dict (used directly, overriding the assembled fields).
        **kwargs
            Additional top-level body fields (e.g. ``engine="webkit"``).

        Returns
        -------
        dict
            The agent result envelope, or the ``problem+json`` body when gated.
        """
        if task is None and instruction is None:
            raise ValueError(
                "agent() requires either `instruction` or a full `task` dict"
            )
        if task is not None:
            built_task = task
        else:
            built_task = {"instruction": instruction}
            if url is not None:
                built_task["start_url"] = url
            if steps is not None:
                built_task["steps"] = steps

        body: dict = {"task": built_task}
        body.update(kwargs)
        if self._provider_config is not None:
            body["provider_config"] = self._provider_config

        from kiota_abstractions.request_information import RequestInformation
        from kiota_abstractions.method import Method

        request_info = RequestInformation(Method.POST, "{+baseurl}/v1/agent", {})
        request_info.path_parameters["baseurl"] = self._core.request_adapter.base_url
        request_info.headers.try_add("Accept", "application/json")
        # Write the JSON body as raw bytes + content-type. Using set_stream_content
        # (not set_content_from_scalar) avoids double-encoding the dict into a
        # JSON string-of-a-string.
        request_info.set_stream_content(
            json.dumps(body).encode("utf-8"), "application/json"
        )
        try:
            raw = await self._core.request_adapter.send_primitive_async(
                request_info, "bytes", None
            )
        except _KiotaAPIError as exc:
            # The agent route is account-gated: when it is not enabled the API
            # replies 404 problem+json. Surface that as a dict (with `detail`)
            # so callers can branch on ``"detail" in response`` instead of
            # handling an exception — mirroring the prior client's gated
            # pass-through. Other statuses raise the typed error as usual.
            status = getattr(exc, "response_status_code", None)
            if status == 404:
                problem = _problem_body(exc)
                if isinstance(problem, dict):
                    problem.setdefault("detail", problem.get("title", "Not Found"))
                    return problem
                # Kiota drops the body when no error class is registered for the
                # status; synthesize the gated envelope so the shape is stable.
                headers = getattr(exc, "response_headers", None)
                request_id = None
                if headers is not None:
                    try:
                        request_id = headers.get("x-request-id") or headers.get(
                            "X-Request-Id"
                        )
                        if isinstance(request_id, (list, tuple, set)):
                            request_id = next(iter(request_id), None)
                    except Exception:  # pragma: no cover - defensive
                        request_id = None
                return {
                    "detail": "Not Found",
                    "code": "not_found",
                    "status": 404,
                    "request_id": request_id,
                }
            raise _translate_kiota_error(exc) from exc
        return _bytes_to_dict(raw)

    async def pdf(
        self,
        url: str,
        *,
        paper_format: str = "a4",
        landscape: bool = False,
        engine: str = "auto",
        **kwargs: typing.Any,
    ) -> bytes:
        """Render a URL to a PDF document and return the raw ``application/pdf`` bytes.

        Delegates to ``POST /v1/pdf``. PDF output is Chrome-only — a request that
        resolves to a Firefox or WebKit identity is rejected with
        ``InvalidRequestError`` (400 ``pdf_engine_unsupported``).

        Routed through the Kiota request adapter (auth + base URL + transport) —
        the generated core has no ``pdf`` builder (the route serves binary, not
        a modeled JSON envelope). The response is returned verbatim as ``bytes``
        so callers can write it straight to disk::

            data = await client.pdf(url="https://example.com")
            with open("page.pdf", "wb") as f:
                f.write(data)

        Parameters
        ----------
        url : str
            Target URL to render.
        paper_format : str
            Page size: ``"a4"`` (default), ``"letter"``, ``"legal"``, ``"tabloid"``.
        landscape : bool
            Render in landscape orientation. Default ``False``.
        engine : str
            Browser engine. PDF is Chrome-only; ``"firefox"`` / ``"webkit"`` are
            rejected before dispatch. Default ``"auto"`` (resolves to Chrome).

        Returns
        -------
        bytes
            The rendered PDF document.
        """
        body: dict = {
            "url": url,
            "paper_format": paper_format,
            "landscape": landscape,
            "engine": engine,
        }
        body.update(kwargs)

        from kiota_abstractions.request_information import RequestInformation
        from kiota_abstractions.method import Method

        request_info = RequestInformation(Method.POST, "{+baseurl}/v1/pdf", {})
        request_info.path_parameters["baseurl"] = self._core.request_adapter.base_url
        request_info.headers.try_add("Accept", "application/pdf")
        request_info.set_stream_content(
            json.dumps(body).encode("utf-8"), "application/json"
        )
        try:
            raw = await self._core.request_adapter.send_primitive_async(
                request_info, "bytes", None
            )
        except _KiotaAPIError as exc:
            raise _translate_kiota_error(exc) from exc
        if raw is None:
            return b""
        if isinstance(raw, (bytes, bytearray)):
            return bytes(raw)
        # A stream-like fallback (defensive — the adapter returns bytes for the
        # "bytes" primitive type).
        read = getattr(raw, "read", None)
        return read() if callable(read) else bytes(raw)

    async def screenshot(
        self,
        url: str,
        *,
        format: str = "png",
        full_page: bool = False,
        screenshot_selector: typing.Optional[str] = None,
        engine: str = "auto",
        **kwargs: typing.Any,
    ) -> bytes:
        """Capture a screenshot of a URL and return the raw image ``bytes``.

        Delegates to ``POST /v1/screenshot``. Mirrors :meth:`pdf` exactly — the
        route serves binary image data (not a modeled JSON envelope), so this
        goes through the Kiota request adapter (auth + base URL + transport)
        with a raw ``RequestInformation`` and returns the response verbatim as
        ``bytes`` you can write straight to disk::

            data = await client.screenshot(url="https://example.com")
            with open("page.png", "wb") as f:
                f.write(data)

        Parameters
        ----------
        url : str
            Target URL to capture.
        format : str
            Image format: ``"png"`` (default), ``"jpeg"``, ``"webp"``.
        full_page : bool
            Capture the full scrollable page rather than just the viewport.
            Default ``False``.
        screenshot_selector : str, optional
            A CSS selector to scope the capture to a single element. Omitted
            when ``None`` (full-viewport / full-page default).
        engine : str
            Browser engine. Default ``"auto"``.

        Returns
        -------
        bytes
            The captured image.
        """
        body: dict = {
            "url": url,
            "format": format,
            "full_page": full_page,
            "engine": engine,
        }
        if screenshot_selector is not None:
            body["screenshot_selector"] = screenshot_selector
        body.update(kwargs)

        from kiota_abstractions.request_information import RequestInformation
        from kiota_abstractions.method import Method

        request_info = RequestInformation(
            Method.POST, "{+baseurl}/v1/screenshot", {}
        )
        request_info.path_parameters["baseurl"] = self._core.request_adapter.base_url
        request_info.headers.try_add("Accept", "image/png")
        request_info.set_stream_content(
            json.dumps(body).encode("utf-8"), "application/json"
        )
        try:
            raw = await self._core.request_adapter.send_primitive_async(
                request_info, "bytes", None
            )
        except _KiotaAPIError as exc:
            raise _translate_kiota_error(exc) from exc
        if raw is None:
            return b""
        if isinstance(raw, (bytes, bytearray)):
            return bytes(raw)
        # A stream-like fallback (defensive — the adapter returns bytes for the
        # "bytes" primitive type).
        read = getattr(raw, "read", None)
        return read() if callable(read) else bytes(raw)

    async def content(
        self,
        url: str,
        *,
        engine: str = "auto",
        **kwargs: typing.Any,
    ) -> dict:
        """Fetch the rendered content of a URL and return it as a ``dict``.

        Delegates to ``POST /v1/content``. Mirrors :meth:`pdf` / :meth:`agent`
        dispatch — routed through the Kiota request adapter (auth + base URL +
        transport) with a raw ``RequestInformation`` — but the route serves a
        JSON body, so the response is decoded via ``_bytes_to_dict`` (the same
        helper :meth:`agent` uses) and returned as a dict carrying the rendered
        HTML/content envelope.

        Parameters
        ----------
        url : str
            Target URL to render.
        engine : str
            Browser engine. Default ``"auto"``.
        **kwargs
            Additional top-level body fields.

        Returns
        -------
        dict
            The rendered-content envelope.
        """
        body: dict = {"url": url, "engine": engine}
        body.update(kwargs)

        from kiota_abstractions.request_information import RequestInformation
        from kiota_abstractions.method import Method

        request_info = RequestInformation(Method.POST, "{+baseurl}/v1/content", {})
        request_info.path_parameters["baseurl"] = self._core.request_adapter.base_url
        request_info.headers.try_add("Accept", "application/json")
        request_info.set_stream_content(
            json.dumps(body).encode("utf-8"), "application/json"
        )
        try:
            raw = await self._core.request_adapter.send_primitive_async(
                request_info, "bytes", None
            )
        except _KiotaAPIError as exc:
            raise _translate_kiota_error(exc) from exc
        return _bytes_to_dict(raw)

    def with_retries(self, n: int) -> "GhostCrawlClient":
        """Return a NEW client with the same auth/base/provider config.

        Back-compat with the prior ``GhostCrawl.with_retries(n)`` factory. The
        Kiota transport handles retries via middleware; this returns a fresh,
        independent client (separate adapter + httpx session) rather than
        mutating ``self``. ``n`` is accepted for API compatibility.

        Parameters
        ----------
        n : int
            Retry budget (accepted for compatibility).

        Returns
        -------
        GhostCrawlClient
            A fresh client; the original is untouched.
        """
        return GhostCrawlClient(
            token=self._token,
            base_url=self.base_url,
            provider_config=self._provider_config,
        )
