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

import asyncio
import collections.abc
import json
import os
import time
import typing

import httpx
from kiota_abstractions.api_error import APIError as _KiotaAPIError
from kiota_abstractions.authentication import (
    AccessTokenProvider,
    AllowedHostsValidator,
    BaseBearerTokenAuthenticationProvider,
)
from kiota_http.httpx_request_adapter import HttpxRequestAdapter
from kiota_http.kiota_client_factory import KiotaClientFactory
from kiota_http.middleware.options import RetryHandlerOption

# _generated/ lives at sdks/python/_generated/ (sibling to ghostcrawl/).
# Include _generated* in pyproject.toml packages.find so it ships with the SDK.
from ghostcrawl._generated.ghostcrawl_client import (
    GhostCrawlClient as _KiotaClient,  # type: ignore[import]
)

# Search(wait=) client-side bounded poll. Stdlib+httpx, no kiota dep, so
# the poll contract is unit-testable in isolation (tests/test_search_wait.py).
from . import _search_poll

# Typed-but-dict-accessible result models. The facade wraps every raw
# response into one of these OWNED types so the generated core models never reach
# the user surface. Field names are parity-locked in
# parity/sdk_surface_contract.json. Stdlib-only, no runtime dependency.
from ._results import (
    SearchResult,
    wrap_binary,
    wrap_crawl,
    wrap_scrape,
    wrap_search,
)

# Canonical error catalog (mirror of ghostcrawl/errors/codes.json). Used to map
# the problem+json ``code`` and the result-envelope ``result_error.code`` onto
# typed exceptions and the ``retryable`` flag.
from .errors.codes import ALL_CODES, RESULT_CODES
from .errors.codes import is_retryable as _is_retryable

# Public ghostcrawl error classes (the ones re-exported from the package root).
# Aliased so transport errors from the generated core can be re-raised as the
# documented types without colliding with the facade-local classes below.

_DEFAULT_BASE_URL = "https://api.ghostcrawl.io"


def _read_config_value(key_name: str) -> str | None:
    """Best-effort read of ``<key_name> = "..."`` from the CLI's config files.

    Mirrors the CLI's file chain so that ``ghostcrawl init`` output is honored by
    the SDK constructor, not only the CLI: ``./ghostcrawl.toml`` (cwd) first, then
    ``$XDG_CONFIG_HOME/ghostcrawl/config.toml`` (``~/.config`` fallback). Returns
    the first non-empty value, or ``None``. Never raises — config is optional.
    """
    import pathlib  # noqa: PLC0415 — keep the import local to this cold path

    xdg = os.environ.get("XDG_CONFIG_HOME", "").strip()
    xdg_base = pathlib.Path(xdg) if xdg else pathlib.Path.home() / ".config"
    candidates = [
        pathlib.Path.cwd() / "ghostcrawl.toml",
        xdg_base / "ghostcrawl" / "config.toml",
    ]
    for path in candidates:
        try:
            if not path.exists():
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or not line.startswith(key_name):
                    continue
                parts = line.split("=", 1)
                if len(parts) == 2:
                    val = parts[1].strip().strip('"').strip("'")
                    if val:
                        return val
        except OSError:
            continue
    return None


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
        body: typing.Any | None = None,
        *,
        code: str | None = None,
        retryable: bool = False,
        retry_after: int | None = None,
        request_id: str | None = None,
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
        code: str | None = None,
        retryable: bool = False,
        target_status: int | None = None,
        reason: str | None = None,
        request_id: str | None = None,
        body: typing.Any | None = None,
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


class GhostCrawlConnectionError(GhostCrawlError):
    """Raised when the SDK cannot reach the API at all.

    A DNS/connect/network transport failure (no HTTP response was received).
    Distinct from :class:`APIError` (the server answered with a 5xx). Retryable —
    a transient network blip is the common cause.
    """

    def __init__(self, message: str, body: typing.Any | None = None) -> None:
        super().__init__(message, status_code=0, body=body, retryable=True)


class GhostCrawlTimeoutError(GhostCrawlConnectionError):
    """Raised when a request to the API times out before a response arrives.

    A specialization of :class:`GhostCrawlConnectionError` (catch the parent to
    handle any transport failure; catch this to single out timeouts).
    """


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
        captured: dict | None = None
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
        additional_authentication_context: dict[str, typing.Any] | None = None,
    ) -> str:
        return self._token

    def get_allowed_hosts_validator(self) -> AllowedHostsValidator:
        # Allow all hosts (an empty list = no restriction; the validator
        # requires the argument and rejects a missing/non-list value).
        return AllowedHostsValidator([])


# ---------------------------------------------------------------------------
# Response helper: Kiota returns bytes for most endpoints; decode to dict
# ---------------------------------------------------------------------------


def _bytes_to_dict(raw: bytes | None) -> dict:
    """Decode bytes JSON response from the Kiota adapter to a plain dict."""
    if raw is None:
        return {}
    if isinstance(raw, (bytes, bytearray)):
        try:
            return json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            # A malformed 200 body must still surface as a typed GhostCrawlError,
            # never a raw stdlib json.JSONDecodeError — the SDK contract is that
            # every failure a caller catches is a GhostCrawlError.
            raise APIError(
                "The GhostCrawl API returned a malformed response body "
                "(could not be decoded as JSON)."
            ) from exc
    # Already deserialized (Parsable objects from typed endpoints)
    if hasattr(raw, "__dict__"):
        return _parsable_to_dict(raw)
    return raw  # type: ignore[return-value]


def _translate_transport_error(exc: Exception) -> GhostCrawlError | None:
    """Map an httpx transport failure to a typed SDK error.

    Returns the typed error for a connection/timeout failure (no HTTP response
    was received), or ``None`` when ``exc`` is not a transport error so the
    caller re-raises it unchanged. HTTP error *responses* are handled elsewhere
    (:func:`_translate_kiota_error` / :func:`_error_from_http_response`).
    """
    if isinstance(exc, httpx.TimeoutException):
        return GhostCrawlTimeoutError(f"The request to the GhostCrawl API timed out: {exc}")
    if isinstance(exc, httpx.TransportError):
        # ConnectError / NetworkError / ProtocolError / … — the round-trip never
        # completed. (TimeoutException is checked first: it is also a TransportError.)
        return GhostCrawlConnectionError(f"Could not connect to the GhostCrawl API: {exc}")
    return None


def _safe_response_json(resp: httpx.Response) -> dict:
    """Decode an httpx response body as JSON, mapping a malformed body to a typed error.

    An empty body decodes to ``{}``. A non-JSON 2xx body raises :class:`APIError`
    (a typed GhostCrawlError) instead of a raw ``json.JSONDecodeError`` so the
    "every failure is a GhostCrawlError" contract holds on the direct-httpx path.
    """
    if not resp.content:
        return {}
    try:
        return resp.json()
    except ValueError as exc:
        raise APIError(
            "The GhostCrawl API returned a malformed response body "
            "(could not be decoded as JSON)."
        ) from exc


def _finalize_search(
    data: typing.Any, query: str, engine: str
) -> dict:
    """Guarantee a stable ``search`` result shape regardless of poll outcome.

    The cold-rotation search-job contract can hand back a raw *running* handle
    (``{status:"running", job_id, poll_url, ...}`` — no ``items``) when the
    client-side poll budget elapses before the job reaches terminal. Left raw,
    ``result["query"]`` / ``result["results"]`` raise ``KeyError`` — a surprise
    shape the caller cannot code against. This injects the caller's ``query`` and
    ``engine`` (only the SDK knows them) and normalizes ``results`` to a list, so
    every ``search`` return — warm ``200``, ``wait=False`` handle, or timed-out
    poll — always carries ``query``/``engine``/``results``. ``SearchResult`` then
    adds the final dict-access guarantees.
    """
    d: dict = dict(data) if isinstance(data, collections.abc.Mapping) else {}
    # ``items`` is the server's hit-list key; ``results`` is our canonical field.
    if d.get("results") is None:
        d["results"] = d.get("items") if isinstance(d.get("items"), list) else []
    # Real query/engine always win over an absent/empty value from a bare handle.
    if not d.get("query"):
        d["query"] = query
    d.setdefault("engine", engine)
    return d


async def _send_bytes(adapter: typing.Any, request_info: typing.Any) -> bytes | None:
    """Send a request whose response is raw bytes; return the body (or ``None``).

    Kiota's ``RequestAdapter.send_primitive_async`` is declared with an
    unconstrained return type variable that a static type checker resolves to
    ``None``, even though the ``"bytes"`` response type yields a byte string at
    runtime. This thin wrapper pins the real return type at the untyped-library
    boundary so every call site stays type-checkable without silencing.
    """
    send = typing.cast(
        typing.Callable[..., typing.Awaitable["bytes | None"]],
        adapter.send_primitive_async,
    )
    try:
        return await send(request_info, "bytes", None)
    except _KiotaAPIError:
        # An HTTP error *response* — the caller translates it (has status/body).
        raise
    except Exception as exc:
        # A connection/timeout failure never reached the server: surface it typed.
        typed = _translate_transport_error(exc)
        if typed is not None:
            raise typed from exc
        raise


def _parsable_to_dict(obj: typing.Any, _seen: set | None = None) -> typing.Any:
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
        fields = obj.__dataclass_fields__  # type: ignore[attr-defined]
        # Kiota composed-type UNION wrapper: a scalar branch (e.g. ``string`` /
        # ``double`` / ``boolean`` / ``integer``) plus a ``<name>_member1`` object
        # branch, and NO ``additional_data``. The generator emits one of these per
        # ``string | Object`` field (markdown/status/format/…). Left un-unwrapped
        # it renders as ``{'string': '# Example Domain'}`` — the #1 typed-result
        # DX defect. Unwrap to whichever branch is populated. This is the
        # Python analog of the Node SDK's ``unwrapKiota`` (FACADE-PATTERN.md).
        if "additional_data" not in fields and any(f.endswith("_member1") for f in fields):
            for field_name in fields:
                val = getattr(obj, field_name, None)
                if val is not None:
                    return _parsable_to_dict(val, _seen)
            return None
        result = {}
        for field_name in fields:
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
_STATUS_TO_CODE: dict[int, str] = {
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


def _problem_body(exc: Exception) -> dict | None:
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


def _retry_after_from_headers(exc: Exception) -> int | None:
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


def _error_from_http_response(resp: httpx.Response) -> Exception:
    """Map a non-2xx raw-httpx response onto a public ghostcrawl error type.

    Mirrors :func:`_translate_kiota_error` for the ``search(wait=)`` poll path,
    which talks HTTP directly (to read the status code + ``Retry-After`` the
    generated builder abstracts away) and so must build its error from the
    response itself. NEVER echoes the api_key — only the
    server-supplied problem+json fields are surfaced.
    """
    status = resp.status_code
    body: dict | None = None
    try:
        if "json" in resp.headers.get("content-type", ""):
            body = resp.json()
    except Exception:  # pragma: no cover - defensive; never mask the real error
        body = None

    code = body.get("code") if isinstance(body, dict) else None
    if code not in ALL_CODES:
        code = None
    if code is None:
        code = _STATUS_TO_CODE.get(status)

    message = None
    if isinstance(body, dict):
        message = body.get("detail") or body.get("title")
    message = message or f"HTTP {status}"

    retry_after: int | None = None
    if isinstance(body, dict) and isinstance(body.get("retry_after"), int):
        retry_after = body["retry_after"]
    if retry_after is None:
        ra = _search_poll.parse_retry_after(resp.headers.get("Retry-After"))
        retry_after = int(ra) if ra is not None else None

    request_id = None
    if isinstance(body, dict):
        request_id = body.get("instance") or body.get("request_id")

    retryable = (
        bool(body.get("retryable"))
        if isinstance(body, dict) and "retryable" in body
        else _is_retryable(code)
    )

    common: dict[str, typing.Any] = dict(
        status_code=status,
        body=body,
        code=code,
        retryable=retryable,
        retry_after=retry_after,
        request_id=request_id,
    )
    if code == "unauthorized" or status == 401:
        return AuthenticationError(message, **common)
    if code == "payment_required" or status == 402:
        return PaymentRequiredError(message, **common)
    if code == "rate_limited" or status == 429:
        return RateLimitError(message, **common)
    if code in ("bad_request", "byo_proxy_invalid", "tier_unavailable") or status in (
        400,
        422,
    ):
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

    code: str | None = None
    retryable = False
    target_status: int | None = None
    reason: str | None = None

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
    except Exception as exc:
        typed = _translate_transport_error(exc)
        if typed is not None:
            raise typed from exc
        raise
    return _scan_result_error(_bytes_to_dict(raw))


# ---------------------------------------------------------------------------
# Crawl-run completion — event-driven wait helpers
# ---------------------------------------------------------------------------

#: Terminal crawl-run states. A run in any of these has stopped moving; results
#: are present when the state is ``completed``. Anything else is still in flight.
TERMINAL_RUN_STATES: frozenset[str] = frozenset(
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


async def _post_json_via_adapter(
    core: _KiotaClient, path: str, body: dict | None = None
) -> dict:
    """POST ``path`` through the shared Kiota request adapter, decoded to a dict.

    Delegates to the Kiota core transport (auth + base URL + middleware) via a
    raw ``RequestInformation`` — NOT a hand-rolled HTTP client. Used for the
    handful of customer routes with no generated builder (``cdp.input``).
    """
    from kiota_abstractions.method import Method
    from kiota_abstractions.request_information import RequestInformation

    request_info = RequestInformation(Method.POST, "{+baseurl}" + path, {})
    request_info.path_parameters["baseurl"] = core.request_adapter.base_url
    request_info.headers.try_add("Accept", "application/json")
    request_info.set_stream_content(
        json.dumps(body or {}).encode("utf-8"), "application/json"
    )
    try:
        raw = await _send_bytes(core.request_adapter, request_info)
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
        include_patterns: list | None = None,
        exclude_patterns: list | None = None,
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
        from ghostcrawl._generated.v1.crawl_runs.crawl_runs_post_request_body import (
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
        return wrap_crawl(run)

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
                return wrap_crawl(run)
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
                return wrap_crawl(run)

    async def list(
        self,
        *,
        limit: int = 20,
        cursor: str | None = None,
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
        return wrap_crawl(
            await _resolve_response(self._core.v1.crawl_runs.by_run_id(run_id).get())
        )

    async def cancel(self, run_id: str) -> dict:
        """Cancel a running crawl run.

        Calls ``POST /v1/crawl-runs/{run_id}/cancel`` via the generated builder.
        """
        return await _resolve_response(
            self._core.v1.crawl_runs.by_run_id(run_id).cancel.post(None)
        )

    async def resume(self, run_id: str) -> dict:
        """Resume a paused or interrupted crawl run.

        Calls ``POST /v1/crawl-runs/{run_id}/resume`` via the generated builder.
        Returns the (re-armed) crawl-run record.
        """
        return wrap_crawl(
            await _resolve_run(self._core.v1.crawl_runs.by_run_id(run_id).resume.post(None))
        )


class SessionsClient:
    """Manage browser sessions — /v1/sessions."""

    def __init__(self, core: _KiotaClient) -> None:
        self._core = core

    async def list(self) -> dict:
        """List all active sessions."""
        return await _resolve_response(self._core.v1.sessions.get())

    async def create(
        self,
        *,
        profile_name: str | None = None,
        engine: str | None = None,
        **kwargs: typing.Any,
    ) -> dict:
        """Create a new browser session.

        Calls ``POST /v1/sessions/create`` via the generated builder.

        Two creation modes:

        * **profile-based** — pass ``profile_name`` to rehydrate a saved identity
          profile (the org must already own a profile of that name, else the API
          replies ``404 no profile named ...``);
        * **engine-based (ad-hoc)** — omit ``profile_name`` and the API opens a
          fresh session on ``engine`` (``"chrome"`` / ``"firefox"`` / ``"webkit"``
          / ``"auto"``; default ``"auto"``) with no saved profile required. This is
          the zero-setup path — a brand-new key with no profiles can open a session.

        Passing both is a validation error server-side; pass exactly one.
        """
        from ghostcrawl._generated.models.session_create_request import SessionCreateRequest

        body = SessionCreateRequest()
        if profile_name is not None:
            from ghostcrawl._generated.models.session_create_request_profile import (
                SessionCreateRequest_profile,
            )

            profile_wrapper = SessionCreateRequest_profile()
            profile_wrapper.string = profile_name
            body.profile = profile_wrapper
        else:
            # engine-based ad-hoc session (no profile) — works on a fresh org with
            # zero saved profiles, which is the common case.
            from ghostcrawl._generated.models.session_create_request_engine import (
                SessionCreateRequest_engine,
            )

            body.engine = SessionCreateRequest_engine(engine or "auto")
        body.additional_data = kwargs
        return await _resolve_response(self._core.v1.sessions.create.post(body))

    async def extend(self, session_id: str, *, duration_seconds: int = 300) -> dict:
        """Extend a session's TTL.

        Sends ``{"ttl_seconds": <duration_seconds>}`` — the generated
        ``ExtendRequestBuilder.post`` rejects a null body, and the new TTL is
        carried by the ``ttl_seconds`` field (30s..24h).
        """
        from ghostcrawl._generated.models.extend_body import ExtendBody
        from ghostcrawl._generated.models.extend_body_ttl_seconds import (
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

    async def pin(self, session_id: str) -> dict:
        """Pin a session so the pool keeps it warm for reuse.

        Calls ``POST /v1/sessions/{session_id}/pin`` via the generated builder.
        """
        return await _resolve_response(
            self._core.v1.sessions.by_profile_id(session_id).pin.post(None)
        )

    async def terminate(self, session_id: str) -> dict:
        """Terminate a session immediately (hard stop, no return-to-pool).

        Calls ``POST /v1/sessions/{session_id}/terminate``. The generated core
        has no ``terminate`` builder (the route is absent from the customer-facing
        OpenAPI), so this is routed through the shared Kiota request adapter (auth
        + base URL + transport) via a raw ``RequestInformation`` — no hand-rolled
        HTTP client.
        """
        return await self._post_json(f"/v1/sessions/{session_id}/terminate")

    async def takeover(
        self,
        session_id: str,
        *,
        action: str | None = None,
        **kwargs: typing.Any,
    ) -> dict:
        """Take interactive control of a running session (human-in-the-loop).

        Calls ``POST /v1/sessions/{session_id}/takeover`` via the generated
        builder. ``action`` and any extra fields are sent in the request body.
        """
        from ghostcrawl._generated.models.takeover_action_body import TakeoverActionBody

        body = TakeoverActionBody()
        data: dict = dict(kwargs)
        if action is not None:
            data["action"] = action
        body.additional_data = data
        return await _resolve_response(
            self._core.v1.sessions.by_profile_id(session_id).takeover.post(body)
        )

    async def takeover_token(self, session_id: str) -> dict:
        """Mint a one-time interactive-takeover token for a session.

        Calls ``POST /v1/sessions/{session_id}/takeover_token`` via the generated
        builder. The returned token authorizes a browser-based takeover UI.
        """
        return await _resolve_response(
            self._core.v1.sessions.by_profile_id(session_id).takeover_token.post(None)
        )

    async def takeover_release(self, session_id: str) -> dict:
        """Release an interactive takeover and hand control back to automation.

        Calls ``POST /v1/sessions/{session_id}/takeover_release`` via the
        generated builder.
        """
        return await _resolve_response(
            self._core.v1.sessions.by_profile_id(session_id).takeover_release.post(None)
        )

    async def recording_start(self, profile_id: str) -> dict:
        """Start a session recording for ``profile_id``.

        Calls ``POST /v1/sessions/{profile_id}/recording/start`` via the
        generated builder.
        """
        return await _resolve_response(
            self._core.v1.sessions.by_profile_id(profile_id).recording.start.post(None)
        )

    async def recording_stop(self, profile_id: str) -> dict:
        """Stop the in-progress session recording for ``profile_id``.

        Calls ``POST /v1/sessions/{profile_id}/recording/stop`` via the
        generated builder.
        """
        return await _resolve_response(
            self._core.v1.sessions.by_profile_id(profile_id).recording.stop.post(None)
        )

    async def _post_json(
        self, path: str, body: dict | None = None
    ) -> dict:
        """POST ``path`` through the shared Kiota request adapter, decoded to a dict.

        Delegates to the Kiota core transport (auth + base URL + middleware) via a
        raw ``RequestInformation`` — NOT a hand-rolled HTTP client. Used for
        session-lifecycle routes that have no generated builder (``terminate``).
        """
        from kiota_abstractions.method import Method
        from kiota_abstractions.request_information import RequestInformation

        request_info = RequestInformation(Method.POST, "{+baseurl}" + path, {})
        request_info.path_parameters["baseurl"] = self._core.request_adapter.base_url
        request_info.headers.try_add("Accept", "application/json")
        request_info.set_stream_content(
            json.dumps(body or {}).encode("utf-8"), "application/json"
        )
        try:
            raw = await _send_bytes(self._core.request_adapter, request_info)
        except _KiotaAPIError as exc:
            raise _translate_kiota_error(exc) from exc
        return _bytes_to_dict(raw)


class CdpClient:
    """Low-level CDP primitives for a live session — /v1/cdp.

    These are first-class customer surface. Delegates to the
    generated ``v1.cdp`` builders (``frame`` / ``url``); ``input`` has no
    generated builder (absent from the customer-facing OpenAPI) and is routed
    through the shared Kiota request adapter via a raw ``RequestInformation``.
    """

    def __init__(self, core: _KiotaClient) -> None:
        self._core = core

    async def frame(self, **kwargs: typing.Any) -> dict:
        """Drive a CDP ``frame`` command against the live page (POST /v1/cdp/frame)."""
        from ghostcrawl._generated.models.cdp_frame_request import CdpFrameRequest

        body = CdpFrameRequest()
        body.additional_data = dict(kwargs)
        return await _resolve_response(self._core.v1.cdp.frame.post(body))

    async def url(self, **kwargs: typing.Any) -> dict:
        """Navigate / read the live page URL over CDP (POST /v1/cdp/url)."""
        from ghostcrawl._generated.models.cdp_url_request import CdpUrlRequest

        body = CdpUrlRequest()
        body.additional_data = dict(kwargs)
        return await _resolve_response(self._core.v1.cdp.url.post(body))

    async def input(self, **kwargs: typing.Any) -> dict:
        """Dispatch a CDP ``Input`` event to the live page (POST /v1/cdp/input).

        The generated core has no ``cdp.input`` builder (the route is absent from
        the customer-facing OpenAPI), so this is routed through the shared Kiota
        request adapter (auth + base URL + transport) via a raw
        ``RequestInformation`` — no hand-rolled HTTP client.
        """
        return await _post_json_via_adapter(self._core, "/v1/cdp/input", dict(kwargs))


class PageClient:
    """High-level page primitives for a live session — /v1/page.

    These are first-class customer surface. Delegates to the
    generated ``v1.page`` builders (cookies get/set/delete, dom_snapshot,
    download, eval, har, scroll, upload, wait).
    """

    def __init__(self, core: _KiotaClient) -> None:
        self._core = core

    async def get_cookies(
        self,
        *,
        profile_id: str | None = None,
        domain: str | None = None,
        name: str | None = None,
    ) -> dict:
        """Read cookies from the live page (GET /v1/page/cookies)."""
        from kiota_abstractions.base_request_configuration import RequestConfiguration

        config: RequestConfiguration = RequestConfiguration()
        qp: dict = {}
        if profile_id is not None:
            qp["profile_id"] = profile_id
        if domain is not None:
            qp["domain"] = domain
        if name is not None:
            qp["name"] = name
        config.query_parameters = qp
        return await _resolve_response(self._core.v1.page.cookies.get(config))

    async def set_cookies(self, cookies: list, **kwargs: typing.Any) -> dict:
        """Set cookies on the live page (POST /v1/page/cookies)."""
        from ghostcrawl._generated.models.cookies_set_body import CookiesSetBody

        body = CookiesSetBody()
        body.additional_data = {"cookies": cookies, **kwargs}
        return await _resolve_response(self._core.v1.page.cookies.post(body))

    async def delete_cookies(self, **kwargs: typing.Any) -> dict:
        """Delete cookies from the live page (DELETE /v1/page/cookies)."""
        from ghostcrawl._generated.models.cookies_delete_body import CookiesDeleteBody

        body = CookiesDeleteBody()
        body.additional_data = dict(kwargs)
        raw = await self._core.v1.page.cookies.delete(body)
        return _bytes_to_dict(raw) if raw else {}

    async def dom_snapshot(self, **kwargs: typing.Any) -> dict:
        """Capture a DOM snapshot of the live page (POST /v1/page/dom_snapshot)."""
        from ghostcrawl._generated.models.dom_snapshot_body import DomSnapshotBody

        body = DomSnapshotBody()
        body.additional_data = dict(kwargs)
        return await _resolve_response(self._core.v1.page.dom_snapshot.post(body))

    async def download(self, **kwargs: typing.Any) -> dict:
        """Trigger / capture a file download on the live page (POST /v1/page/download)."""
        from ghostcrawl._generated.models.download_body import DownloadBody

        body = DownloadBody()
        body.additional_data = dict(kwargs)
        return await _resolve_response(self._core.v1.page.download.post(body))

    async def eval(self, expression: str, **kwargs: typing.Any) -> dict:
        """Evaluate an expression in the live page context (POST /v1/page/eval)."""
        from ghostcrawl._generated.models.eval_body import EvalBody

        body = EvalBody()
        body.additional_data = {"expression": expression, **kwargs}
        return await _resolve_response(self._core.v1.page.eval.post(body))

    async def har(self, **kwargs: typing.Any) -> dict:
        """Capture the live page's network HAR log (POST /v1/page/har)."""
        from ghostcrawl._generated.models.har_body import HarBody

        body = HarBody()
        body.additional_data = dict(kwargs)
        return await _resolve_response(self._core.v1.page.har.post(body))

    async def scroll(self, **kwargs: typing.Any) -> dict:
        """Scroll the live page (POST /v1/page/scroll)."""
        from ghostcrawl._generated.models.scroll_body import ScrollBody

        body = ScrollBody()
        body.additional_data = dict(kwargs)
        return await _resolve_response(self._core.v1.page.scroll.post(body))

    async def upload(self, **kwargs: typing.Any) -> dict:
        """Attach a file to a file input on the live page (POST /v1/page/upload)."""
        from ghostcrawl._generated.models.upload_body import UploadBody

        body = UploadBody()
        body.additional_data = dict(kwargs)
        return await _resolve_response(self._core.v1.page.upload.post(body))

    async def wait(self, **kwargs: typing.Any) -> dict:
        """Wait for a condition on the live page (POST /v1/page/wait).

        e.g. ``selector=...`` / ``timeout_ms=...`` / ``state="visible"`` — passed
        through as the request body.
        """
        from ghostcrawl._generated.models.wait_body import WaitBody

        body = WaitBody()
        body.additional_data = dict(kwargs)
        return await _resolve_response(self._core.v1.page.wait.post(body))


class DownloadsClient:
    """Manage captured file downloads — /v1/downloads."""

    def __init__(self, core: _KiotaClient) -> None:
        self._core = core

    async def list(self) -> dict:
        """List captured downloads (GET /v1/downloads)."""
        return await _resolve_response(self._core.v1.downloads.get())

    async def get(self, download_id: str) -> dict:
        """Get a single download's metadata (GET /v1/downloads/{download_id})."""
        return await _resolve_response(
            self._core.v1.downloads.by_download_id(download_id).get()
        )

    async def delete(self, download_id: str) -> dict:
        """Delete a captured download (DELETE /v1/downloads/{download_id})."""
        # DELETE returns 204 No Content — no body to decode.
        await self._core.v1.downloads.by_download_id(download_id).delete()
        return {}


class StorageStatesClient:
    """Manage reusable storage states (cookies/localStorage) — /v1/storage-states."""

    def __init__(self, core: _KiotaClient) -> None:
        self._core = core

    async def list(self) -> dict:
        """List saved storage states (GET /v1/storage-states)."""
        return await _resolve_response(self._core.v1.storage_states.get())

    async def create(self, **kwargs: typing.Any) -> dict:
        """Create/capture a new storage state (POST /v1/storage-states)."""
        from ghostcrawl._generated.v1.storage_states.storage_states_post_request_body import (
            StorageStatesPostRequestBody,
        )

        body = StorageStatesPostRequestBody()
        body.additional_data = dict(kwargs)
        return await _resolve_response(self._core.v1.storage_states.post(body))

    async def get(self, id_or_name: str) -> dict:
        """Get a storage state by id or name (GET /v1/storage-states/{id_or_name})."""
        return await _resolve_response(
            self._core.v1.storage_states.by_id_or_name(id_or_name).get()
        )

    async def delete(self, id_or_name: str) -> dict:
        """Delete a storage state (DELETE /v1/storage-states/{id_or_name})."""
        raw = await self._core.v1.storage_states.by_id_or_name(id_or_name).delete()
        return _bytes_to_dict(raw) if raw else {}

    async def attach(self, id_or_name: str, *, profile_id: str) -> dict:
        """Attach a storage state to a profile (POST .../{id_or_name}/attach)."""
        from ghostcrawl._generated.models.storage_state_attach_request import (
            StorageStateAttachRequest,
        )

        body = StorageStateAttachRequest()
        body.profile_id = profile_id
        return await _resolve_response(
            self._core.v1.storage_states.by_id_or_name(id_or_name).attach.post(body)
        )

    async def detach(self, *, profile_id: str) -> dict:
        """Detach the storage state from a profile (POST /v1/storage-states/detach)."""
        from ghostcrawl._generated.models.storage_state_detach_request import (
            StorageStateDetachRequest,
        )

        body = StorageStateDetachRequest()
        body.profile_id = profile_id
        return await _resolve_response(self._core.v1.storage_states.detach.post(body))


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
        from ghostcrawl._generated.models.profile_create_request import ProfileCreateRequest

        body = ProfileCreateRequest()
        body.name = name
        body.additional_data = config
        return await _resolve_response(self._core.v1.profiles.post(body))

    async def update(self, name: str, **config: typing.Any) -> dict:
        """Update a profile."""
        from ghostcrawl._generated.models.profile_update_request import ProfileUpdateRequest

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
        event_types: typing.Sequence[str] | None = None,
        events: typing.Sequence[str] | None = None,
        **kwargs: typing.Any,
    ) -> dict:
        """Register a new webhook endpoint.

        The API field is ``event_types``; ``events`` is accepted as a
        back-compat alias for it.
        """
        from ghostcrawl._generated.models.webhook_create_request import WebhookCreateRequest

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
        # DELETE returns 204 No Content — no body to decode.
        await self._core.v1.webhooks.by_webhook_id(webhook_id).delete()
        return {}

    async def rotate_secret(self, webhook_id: str) -> dict:
        """Rotate the signing secret for a webhook."""
        return await _resolve_response(
            self._core.v1.webhooks.by_webhook_id(webhook_id).rotate_secret.post(None)
        )

    async def list_deliveries(self, webhook_id: str) -> dict:
        """List recent delivery attempts for a webhook (GET .../deliveries).

        Returns the delivery history so you can see which events were delivered,
        which failed, and why — the input to :meth:`retry_delivery`.
        """
        return await _resolve_response(
            self._core.v1.webhooks.by_webhook_id(webhook_id).deliveries.get()
        )

    async def retry_delivery(self, webhook_id: str, delivery_id: str) -> dict:
        """Re-attempt a single failed delivery (POST .../deliveries/{id}/retry)."""
        return await _resolve_response(
            self._core.v1.webhooks.by_webhook_id(webhook_id)
            .deliveries.by_delivery_id(delivery_id)
            .retry.post(None)
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
        from ghostcrawl._generated.models.schedule_create_request import ScheduleCreateRequest

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
        from ghostcrawl._generated.v1.datasets.datasets_post_request_body import (
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

    async def append(self, name: str, rows: typing.Sequence[typing.Any]) -> dict:
        """Append rows to a dataset."""
        from ghostcrawl._generated.v1.datasets.item.rows.append.append_post_request_body import (
            AppendPostRequestBody,
        )

        body = AppendPostRequestBody()
        body.additional_data = {"rows": rows}
        return await _resolve_response(
            self._core.v1.datasets.by_name(name).rows.append.post(body)
        )


def _auth_context_body() -> typing.Any:
    """An empty request body for the visual-recording builders.

    The generated ``visual.start`` / ``visual.stop`` / ``visual.frames`` builders
    require a non-null body (the spec models the tenant ``AuthContext`` there), but
    the live routes ignore it — the tenant is resolved from the Bearer token. This
    returns an empty ``AuthContext`` that serialises to ``{}`` so the generated
    builder's not-null guard is satisfied while sending no meaningful payload.
    """
    from ghostcrawl._generated.models.auth_context import AuthContext

    return AuthContext()


class VisualRecordingClient:
    """Live visual-recording lifecycle for one session — ``recordings.visual``.

    Delegates to the generated ``recordings.by_recording_id(session_id).visual``
    builders (``start`` / ``stop`` / ``frames`` + the manifest ``get``). This is
    the live-observability surface (watch your browser working in near real time).
    """

    def __init__(self, core: _KiotaClient, session_id: str) -> None:
        self._core = core
        self._session_id = session_id

    def _visual(self):
        return self._core.v1.recordings.by_recording_id(self._session_id).visual

    async def start(self) -> dict:
        """Start a visual recording for the live session (POST .../visual/start)."""
        return await _resolve_response(self._visual().start.post(_auth_context_body()))

    async def stop(self) -> dict:
        """Stop the visual recording and finalise it (POST .../visual/stop)."""
        return await _resolve_response(self._visual().stop.post(_auth_context_body()))

    async def manifest(self) -> dict:
        """Get the recording manifest pointer (GET .../visual)."""
        return await _resolve_response(self._visual().get(_auth_context_body()))

    async def frames(self, *, cursor: int = 0, limit: int = 100) -> dict:
        """List a page of frame references (GET .../visual/frames).

        Returns ``{frames: [str], next_cursor: int, session_id: str}``;
        ``next_cursor == -1`` means no more pages.
        """
        from kiota_abstractions.base_request_configuration import RequestConfiguration

        from ghostcrawl._generated.v1.recordings.item.visual.frames.frames_request_builder import (
            FramesRequestBuilder,
        )

        qp = FramesRequestBuilder.FramesRequestBuilderGetQueryParameters()
        qp.cursor = cursor
        qp.limit = limit
        config: RequestConfiguration = RequestConfiguration()
        config.query_parameters = qp
        return await _resolve_response(
            self._visual().frames.get(_auth_context_body(), config)
        )

    async def watch(
        self,
        *,
        interval: float = 1.0,
        max_frames: int | None = None,
        auto_start: bool = True,
        auto_stop: bool = True,
    ) -> typing.AsyncIterator[str]:
        """Start recording and yield frame references as they are produced.

        A convenience over ``start`` + repeated ``frames`` polling: it starts the
        recording (unless ``auto_start=False``), yields each new frame reference,
        sleeping ``interval`` seconds when the buffer is momentarily empty, and
        stops the recording on exit (unless ``auto_stop=False``). Stop iterating
        (``break``) or set ``max_frames`` to bound it::

            async for frame_ref in client.recordings.visual(session_id).watch():
                print(frame_ref)
        """
        if auto_start:
            await self.start()
        seen = 0
        cursor = 0
        try:
            while True:
                page = await self.frames(cursor=cursor)
                refs = page.get("frames") or []
                for ref in refs:
                    yield ref
                    seen += 1
                    if max_frames is not None and seen >= max_frames:
                        return
                next_cursor = page.get("next_cursor", -1)
                if isinstance(next_cursor, int) and next_cursor >= 0:
                    cursor = next_cursor
                else:
                    await asyncio.sleep(interval)
        finally:
            if auto_stop:
                await self.stop()

    def live_view(self, **kwargs: typing.Any) -> typing.AsyncIterator[str]:
        """Alias for :meth:`watch` — the live-view frame stream."""
        return self.watch(**kwargs)


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
        # DELETE returns 204 No Content — no body to decode.
        await self._core.v1.recordings.by_recording_id(recording_id).delete()
        return {}

    def visual(self, session_id: str) -> VisualRecordingClient:
        """Live visual-recording surface for ``session_id`` (start/stop/frames/watch)."""
        return VisualRecordingClient(self._core, session_id)

    def watch(self, session_id: str, **kwargs: typing.Any) -> typing.AsyncIterator[str]:
        """Convenience: start a live visual recording for ``session_id`` and stream
        frame references (see :meth:`VisualRecordingClient.watch`)."""
        return self.visual(session_id).watch(**kwargs)

    def live_view(self, session_id: str, **kwargs: typing.Any) -> typing.AsyncIterator[str]:
        """Alias for :meth:`watch` — the live-view frame stream for ``session_id``."""
        return self.visual(session_id).watch(**kwargs)


class KVClient:
    """Key-value store — /v1/kv."""

    def __init__(self, core: _KiotaClient) -> None:
        self._core = core

    async def get(self, key: str) -> dict:
        """Get a value by key."""
        return await _resolve_response(self._core.v1.kv.by_key(key).get())

    async def set(self, key: str, value: typing.Any) -> dict:
        """Set a key-value pair."""
        from ghostcrawl._generated.v1.kv.item.with_key_put_request_body import (
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
    """GhostCrawl idiomatic API client — the **async twin**.

    Delegates all HTTP transport, auth, serialization, and model mapping to the
    Kiota-generated canonical core (``_generated/``). This facade is the shipped API.

    Most users want the **synchronous default** :class:`~ghostcrawl.GhostCrawl`
    instead — it Just Works with no ``await`` and no ``asyncio.run`` footgun::

        from ghostcrawl import GhostCrawl
        client = GhostCrawl(token="gck_live_YOUR_KEY")
        print(client.scrape(url="https://example.com", format="markdown").markdown)

    This class (exported as ``AsyncGhostCrawl`` / ``GhostCrawlClient``) is the
    awaitable opt-in for ``async def`` code. Every method is async; use
    ``async with`` for automatic cleanup::

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
    Sync default (recommended for most callers):

    >>> from ghostcrawl import GhostCrawl
    >>> client = GhostCrawl(token="gck_live_YOUR_KEY")
    >>> print(client.scrape(url="https://example.com", format="markdown").markdown)

    Async twin (only inside ``async def`` code):

    >>> import asyncio
    >>> from ghostcrawl import AsyncGhostCrawl
    >>> async def main():
    ...     async with AsyncGhostCrawl(token="gck_live_YOUR_KEY") as client:
    ...         result = await client.scrape(url="https://example.com", format="markdown")
    ...         print(result.markdown)
    >>> asyncio.run(main())
    """

    def __init__(
        self,
        token: str | None = None,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        provider_config: dict | None = None,
        max_retries: int | None = None,
    ) -> None:
        # ``api_key`` is the historical kwarg name (the pre-Kiota ``GhostCrawl``
        # client). Accept it as an alias for ``token`` so existing user code and
        # the CLI keep working without change. ``token`` wins when both are set.
        #
        # Resolution (matches the CLI's documented order): explicit arg > env >
        # ``./ghostcrawl.toml`` (cwd) > ``~/.config/ghostcrawl/config.toml``. The
        # file fallbacks are what make ``ghostcrawl init`` actually take effect for
        # the SDK, not only the CLI.
        resolved_token = (
            token
            or api_key
            or os.environ.get("GHOSTCRAWL_API_KEY", "")
            or _read_config_value("api_key")
            or ""
        )
        if not resolved_token:
            raise ValueError(
                "token is required (or set GHOSTCRAWL_API_KEY). "
                "Get your key at https://ghostcrawl.io. "
                "Run `ghostcrawl init` to configure."
            )
        resolved_base = (
            base_url
            or os.environ.get("GHOSTCRAWL_BASE_URL", "")
            or _read_config_value("base_url")
            or _DEFAULT_BASE_URL
        ).rstrip("/")
        self.base_url = resolved_base
        self._token = resolved_token
        # provider_config is the per-instance LLM model provider configuration.
        # Validated server-side; stored here for request-body injection on the
        # agent lane. NEVER include in logs — the api_key inside must not leak.
        # Passed explicitly by the caller; the SDK reads no environment variable
        # for it (that configuration is resolved server-side).
        self._provider_config: dict | None = provider_config
        # Transport retry budget. ``None`` uses the Kiota middleware default;
        # ``with_retries(n)`` propagates an explicit budget onto a fresh client.
        self._max_retries: int | None = max_retries

        # Build the Kiota adapter: static-token bearer provider → httpx adapter
        auth_provider = BaseBearerTokenAuthenticationProvider(
            _StaticTokenProvider(resolved_token)
        )
        # When an explicit retry budget is set, build the httpx client with the
        # RetryHandler middleware configured to that budget so retryable failures
        # (5xx / 429, honouring Retry-After) are retried up to ``max_retries``
        # times. Otherwise the adapter installs Kiota's default middleware.
        http_client = None
        if max_retries is not None:
            http_client = KiotaClientFactory.create_with_default_middleware(
                options={
                    RetryHandlerOption().get_key(): RetryHandlerOption(
                        max_retries=max(0, max_retries)
                    )
                }
            )
        # Body-capturing adapter so the problem+json `detail` survives onto the
        # raised error for statuses the generated builders don't error-map
        # (401/402/429) — see _BodyCapturingHttpxRequestAdapter.
        adapter = _BodyCapturingHttpxRequestAdapter(auth_provider, http_client=http_client)
        adapter.base_url = resolved_base

        # Instantiate the generated canonical core
        self._core = _KiotaClient(adapter)

        # Sub-clients (lazy initialization via property)
        self._crawl_runs: CrawlRunsClient | None = None
        self._sessions: SessionsClient | None = None
        self._profiles: ProfilesClient | None = None
        self._webhooks: WebhooksClient | None = None
        self._schedules: SchedulesClient | None = None
        self._datasets: DatasetsClient | None = None
        self._recordings: RecordingsClient | None = None
        self._kv: KVClient | None = None
        self._cdp: CdpClient | None = None
        self._page: PageClient | None = None
        self._downloads: DownloadsClient | None = None
        self._storage_states: StorageStatesClient | None = None

    # Context manager support

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        if hasattr(self._core.request_adapter, "_http_client"):
            http = self._core.request_adapter._http_client  # type: ignore[attr-defined]
            if hasattr(http, "aclose"):
                await http.aclose()

    async def __aenter__(self) -> GhostCrawlClient:
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

    @property
    def cdp(self) -> CdpClient:
        """Low-level CDP primitives for a live session (frame/input/url)."""
        if self._cdp is None:
            self._cdp = CdpClient(self._core)
        return self._cdp

    @property
    def page(self) -> PageClient:
        """High-level page primitives for a live session (cookies/eval/scroll/…)."""
        if self._page is None:
            self._page = PageClient(self._core)
        return self._page

    @property
    def downloads(self) -> DownloadsClient:
        """Captured file-download management."""
        if self._downloads is None:
            self._downloads = DownloadsClient(self._core)
        return self._downloads

    @property
    def storage_states(self) -> StorageStatesClient:
        """Reusable storage-state (cookies/localStorage) management."""
        if self._storage_states is None:
            self._storage_states = StorageStatesClient(self._core)
        return self._storage_states

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
        extract_schema: dict | None = None,
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
        from ghostcrawl._generated.models.scrape_request import ScrapeRequest
        from ghostcrawl._generated.models.scrape_request_engine import ScrapeRequest_engine
        from ghostcrawl._generated.models.scrape_request_format import ScrapeRequest_format
        from ghostcrawl._generated.models.scrape_request_url import ScrapeRequest_url

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
        # ``ScrapeResult`` surfaces the rendered output under ``content`` on
        # construction (same behavior as ``_normalize_scrape_content``) and is
        # dict-accessible, so existing ``result["markdown"]`` callers keep working.
        return wrap_scrape(result)

    async def scrape_batch(
        self,
        urls: list,
        *,
        format: str = "markdown",
        engine: str = "auto",
        javascript: bool = True,
        **kwargs: typing.Any,
    ) -> dict:
        """Scrape many URLs in one request — ``POST /v1/scrape/batch``.

        Delegates to the generated ``v1.scrape.batch`` builder. ``urls`` is the
        list of targets; the response is a collection of per-URL scrape results
        (``{"results": [...]}``). Common per-request options (``format`` /
        ``engine`` / ``javascript``) apply to every URL in the batch.

        Parameters
        ----------
        urls : list of str
            The target URLs to scrape.
        format : str
            Output format for every URL: ``"markdown"`` (default), ``"html"``,
            ``"text"``.
        engine : str
            Browser engine: ``"auto"`` (default), ``"chrome"``, ``"firefox"``,
            ``"webkit"``.
        javascript : bool
            Enable JavaScript rendering. Default ``True``.

        Returns
        -------
        dict
            The batch envelope with a ``results`` collection.
        """
        from ghostcrawl._generated.models.batch_scrape_request import BatchScrapeRequest

        body = BatchScrapeRequest()
        body.additional_data = {
            "urls": urls,
            "format": format,
            "engine": engine,
            "javascript_enabled": javascript,
            **kwargs,
        }
        return await _resolve_response(self._core.v1.scrape.batch.post(body))

    async def search_job(self, job_id: str) -> SearchResult:
        """Poll a queued async search job to its terminal state — ``GET /v1/search/jobs/{job_id}``.

        Delegates to the generated ``v1.search.jobs.by_job_id`` builder. Use this
        when you called :meth:`search` with ``wait=False`` and want to fetch the
        result of a cold (``202``) job yourself. Returns a typed, dict-accessible
        :class:`SearchResult`.
        """
        return wrap_search(
            await _resolve_response(
                self._core.v1.search.jobs.by_job_id(job_id).get()
            )
        )

    async def crawl_status(self, run_id: str) -> dict:
        """Get a deep-crawl run's status — ``GET /v1/crawl/deep/{run_id}``.

        Delegates to the generated ``v1.crawl.deep.by_run_id`` builder. Returns
        the run record (typed :class:`CrawlRun`); its ``status`` field carries
        the terminal state when the crawl has finished.
        """
        return wrap_crawl(
            await _resolve_run(self._core.v1.crawl.deep.by_run_id(run_id).get())
        )

    async def me(self) -> dict:
        """Return the caller's account profile — ``GET /v1/me``.

        The identity behind your API key: user, primary team, and tier. Goes
        through the shared Kiota request adapter (same Bearer token + base URL +
        middleware as the modeled calls); the route is real and in-schema but
        pruned from the published spec, so there is no generated builder for it.
        """
        return await self._get_json("/v1/me")

    async def session_persona(self, session_id: str) -> dict:
        """Return the customer-safe persona for a session — ``GET /v1/me/identities/{session_id}/persona``.

        Who a given running session *is*, shaped for display: a whitelist of
        ``device_class`` / ``os_class`` / ``browser_class`` / ``locale`` only — never
        a raw user-agent or any internal detail. Session-scoped (keyed to
        ``session_id``) so each session reports its own persona, distinct from the
        account-level entitlements on :meth:`me`. An unknown/foreign session raises
        a not-found error (the same anti-enumeration shape as the rest of ``/v1/me``).
        """
        return await self._get_json(
            f"/v1/me/identities/{session_id}/persona"
        )

    async def usage(self, *, period: str | None = None) -> dict:
        """Return the caller's usage + quota report — ``GET /v1/me/usage``.

        The quota-visibility surface: cost/usage for the current billing window
        plus the prepaid wallet balance, scoped to your team. ``period`` is one of
        ``"day"`` (server default), ``"week"``, or ``"month"``.
        """
        path = "/v1/me/usage"
        if period is not None:
            path += f"?period={period}"
        return await self._get_json(path)

    async def _get_json(self, path: str) -> dict:
        """GET ``path`` through the shared Kiota request adapter, decoded to a dict.

        Delegates to the Kiota core transport (auth + base URL + middleware) via a
        raw ``RequestInformation`` — NOT a hand-rolled HTTP client. Used for the
        promoted ``me()`` / ``usage()`` routes that have no generated builder.
        """
        from kiota_abstractions.method import Method
        from kiota_abstractions.request_information import RequestInformation

        request_info = RequestInformation(
            Method.GET, "{+baseurl}" + path, {}
        )
        request_info.path_parameters["baseurl"] = self._core.request_adapter.base_url
        request_info.headers.try_add("Accept", "application/json")
        try:
            raw = await _send_bytes(self._core.request_adapter, request_info)
        except _KiotaAPIError as exc:
            raise _translate_kiota_error(exc) from exc
        return _bytes_to_dict(raw)

    def _acquire_http_client(self) -> tuple[httpx.AsyncClient, bool]:
        """Return ``(client, owned)`` — the adapter's httpx client, or a new one.

        The generated kiota adapter owns an ``httpx.AsyncClient`` we reuse for the
        raw-HTTP ``search`` poll (so connection pooling + TLS config are shared).
        When it is not available, we create a short-lived client the caller must
        close (``owned=True``).
        """
        http = getattr(self._core.request_adapter, "_http_client", None)
        if isinstance(http, httpx.AsyncClient):
            return http, False
        return httpx.AsyncClient(), True

    async def search(
        self,
        query: str,
        *,
        engine: str = "google",
        limit: int = 10,
        provider_key: str | None = None,
        wait: bool = True,
        timeout: float | None = None,
        **kwargs: typing.Any,
    ) -> SearchResult:
        """Search the web and return results.

        Calls ``POST /v1/search``. Returns a :class:`SearchResult` (typed AND
        dict-accessible — ``result.results`` / ``result["results"]`` both work).

        ``search`` runs on two paths. On a **warm** rotation the backend returns
        the results synchronously (``200``) and this returns immediately. On a
        **cold** rotation it returns ``202 running`` with a ``poll_url``; with
        ``wait=True`` (the default, matching ``crawl``'s DX) the SDK owns a
        **bounded client-side poll** that honors ``Retry-After`` and stops at the
        server's ``deadline`` / ``poll_max_seconds`` (or ``timeout``), so you
        write **zero** poll code.

        .. note::
           ``search`` wait is a **client-side bounded poll** (the search-job
           contract has no server ``?wait=true``); ``crawl`` wait is a
           **server-side long-poll** on a completion event. Same ``wait=True``
           DX, different mechanism under the hood.

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
        wait : bool
            When ``True`` (default), block until the search job is terminal via
            the SDK-owned bounded poll. When ``False``, return immediately — a
            warm ``200`` carries the results, a cold ``202`` carries the raw
            job/poll handle (``poll_url`` / ``deadline``) for advanced callers.
        timeout : float, optional
            Overall client-side wait budget in seconds (``wait=True`` only).
            Defaults to the server's ``poll_max_seconds`` when present, else
            :data:`ghostcrawl._search_poll.DEFAULT_TIMEOUT`.

        Returns
        -------
        SearchResult
            Typed, dict-accessible result with ``results`` / ``query`` / ``status``.
        """
        body: dict = {"query": query, "engine": engine, "limit": limit}
        body.update(kwargs)

        headers: dict[str, str] = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if provider_key is not None:
            headers["X-Provider-Authorization"] = f"Bearer {provider_key}"

        http, owned = self._acquire_http_client()
        try:
            try:
                resp = await http.post(
                    f"{self.base_url}/v1/search", json=body, headers=headers
                )
            except Exception as exc:
                typed = _translate_transport_error(exc)
                if typed is not None:
                    raise typed from exc
                raise
            status = resp.status_code
            if status == 200:
                # Warm path: results returned synchronously — no polling.
                return wrap_search(_finalize_search(_safe_response_json(resp), query, engine))
            if status != 202:
                raise _error_from_http_response(resp)

            # Cold path: 202 running with a poll handle.
            job = _safe_response_json(resp)
            if not wait:
                # Advanced users get the raw job/poll handle (still typed) — but
                # still carrying ``query``/``results`` so the shape never surprises.
                return wrap_search(_finalize_search(job, query, engine))

            initial_retry = _search_poll.parse_retry_after(
                resp.headers.get("Retry-After")
            )
            terminal = await _search_poll.poll_search_job(
                http,
                self.base_url,
                job,
                headers,
                error_factory=_error_from_http_response,
                timeout=timeout,
                initial_retry=initial_retry,
            )
            # Whether the poll reached a terminal result OR timed out and returned
            # the raw running handle, inject the caller's ``query``/``engine`` so
            # ``result["query"]`` / ``result["results"]`` are ALWAYS present.
            return wrap_search(_finalize_search(terminal, query, engine))
        finally:
            if owned:
                await http.aclose()

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
        from ghostcrawl._generated.models.extract_request import ExtractRequest
        from ghostcrawl._generated.models.extract_request_url import ExtractRequest_url

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
        from ghostcrawl._generated.models.deep_crawl_body import DeepCrawlBody

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
        return wrap_crawl(run)

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
        from ghostcrawl._generated.models.map_body import MapBody

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
        instruction: str | None = None,
        url: str | None = None,
        steps: list | None = None,
        task: dict | None = None,
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

        from kiota_abstractions.method import Method
        from kiota_abstractions.request_information import RequestInformation

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
            raw = await _send_bytes(self._core.request_adapter, request_info)
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

        from kiota_abstractions.method import Method
        from kiota_abstractions.request_information import RequestInformation

        request_info = RequestInformation(Method.POST, "{+baseurl}/v1/pdf", {})
        request_info.path_parameters["baseurl"] = self._core.request_adapter.base_url
        request_info.headers.try_add("Accept", "application/pdf")
        request_info.set_stream_content(
            json.dumps(body).encode("utf-8"), "application/json"
        )
        try:
            raw = await _send_bytes(self._core.request_adapter, request_info)
        except _KiotaAPIError as exc:
            raise _translate_kiota_error(exc) from exc
        if raw is None:
            return wrap_binary(b"", "application/pdf")
        if isinstance(raw, (bytes, bytearray)):
            return wrap_binary(bytes(raw), "application/pdf")
        # A stream-like fallback (defensive — the adapter returns bytes for the
        # "bytes" primitive type).
        read = getattr(raw, "read", None)
        payload = read() if callable(read) else bytes(raw)
        return wrap_binary(payload, "application/pdf")

    async def screenshot(
        self,
        url: str,
        *,
        format: str = "png",
        full_page: bool = False,
        screenshot_selector: str | None = None,
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

        from kiota_abstractions.method import Method
        from kiota_abstractions.request_information import RequestInformation

        request_info = RequestInformation(
            Method.POST, "{+baseurl}/v1/screenshot", {}
        )
        request_info.path_parameters["baseurl"] = self._core.request_adapter.base_url
        request_info.headers.try_add("Accept", "image/png")
        request_info.set_stream_content(
            json.dumps(body).encode("utf-8"), "application/json"
        )
        try:
            raw = await _send_bytes(self._core.request_adapter, request_info)
        except _KiotaAPIError as exc:
            raise _translate_kiota_error(exc) from exc
        image_ctype = {
            "png": "image/png",
            "jpeg": "image/jpeg",
            "jpg": "image/jpeg",
            "webp": "image/webp",
        }.get(format, "image/png")
        if raw is None:
            return wrap_binary(b"", image_ctype)
        if isinstance(raw, (bytes, bytearray)):
            return wrap_binary(bytes(raw), image_ctype)
        # A stream-like fallback (defensive — the adapter returns bytes for the
        # "bytes" primitive type).
        read = getattr(raw, "read", None)
        payload = read() if callable(read) else bytes(raw)
        return wrap_binary(payload, image_ctype)

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

        from kiota_abstractions.method import Method
        from kiota_abstractions.request_information import RequestInformation

        request_info = RequestInformation(Method.POST, "{+baseurl}/v1/content", {})
        request_info.path_parameters["baseurl"] = self._core.request_adapter.base_url
        request_info.headers.try_add("Accept", "application/json")
        request_info.set_stream_content(
            json.dumps(body).encode("utf-8"), "application/json"
        )
        try:
            raw = await _send_bytes(self._core.request_adapter, request_info)
        except _KiotaAPIError as exc:
            raise _translate_kiota_error(exc) from exc
        # ``/v1/content`` serves the same rendered-output shape as ``scrape``
        # (parity lane ``scrape``) — wrap as a typed, dict-accessible ScrapeResult.
        return wrap_scrape(_bytes_to_dict(raw))

    def with_retries(self, n: int) -> GhostCrawlClient:
        """Return a NEW client whose transport retries retryable failures ``n`` times.

        The returned client shares this client's auth / base URL / provider
        config but installs the transport RetryHandler with a budget of ``n``:
        retryable failures (5xx / 429, honouring ``Retry-After``) are retried up
        to ``n`` times before the typed error is raised. ``self`` is never
        mutated — the fresh client owns its own adapter + httpx session.

        Parameters
        ----------
        n : int
            Retry budget (number of automatic retries; ``0`` disables retries).

        Returns
        -------
        GhostCrawlClient
            A fresh client with the retry budget applied; the original is untouched.
        """
        return GhostCrawlClient(
            token=self._token,
            base_url=self.base_url,
            provider_config=self._provider_config,
            max_retries=n,
        )
