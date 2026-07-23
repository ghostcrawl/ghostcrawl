"""Canonical GhostCrawl error codes.

SDK-side mirror of the server's single source of truth
(``ghostcrawl/errors/codes.json``, generated from the server error catalog).
The values here are copied verbatim from that catalog so the tools never invent
their own vocabulary — keep them in lockstep when the catalog changes.

Two channels:

* ``problem`` — OUR failure. The API returns a non-2xx
  ``application/problem+json`` body. The tool raises a typed ``GhostCrawl*``
  exception keyed on the ``code`` so the agent's error path is a hard failure.
* ``result`` — TARGET failure. The API returns HTTP 200 with ``ok: false`` +
  ``result_error: {code, retryable, target_status?}``. The tool embeds the
  ``code`` (and whether it is retryable) into the text returned to the LLM so
  the agent can reason about it (e.g. rotate identity on ``blocked``) instead of
  treating a blocked / errored scrape as a success.
"""

from __future__ import annotations

from typing import Dict, NamedTuple, Optional


class ErrorCode(NamedTuple):
    """One canonical error code and its catalog metadata."""

    code: str
    http: int
    retryable: bool
    channel: str
    title: str
    retry_after: Optional[int]


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

#: Every canonical code string.
ALL_CODES = tuple(ERROR_CODES.keys())

#: Codes whose ``channel`` is ``"result"`` (TARGET failures returned on HTTP 200).
RESULT_CODES = frozenset(c for c, e in ERROR_CODES.items() if e.channel == "result")

#: Codes whose ``channel`` is ``"problem"`` (OUR failures returned as non-2xx).
PROBLEM_CODES = frozenset(c for c, e in ERROR_CODES.items() if e.channel == "problem")

#: Fallback HTTP-status -> canonical-code map for problem responses with no code.
STATUS_TO_CODE: Dict[int, str] = {
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


def is_retryable(code: Optional[str]) -> bool:
    """Return the catalog ``retryable`` flag for ``code`` (False if unknown)."""
    entry = ERROR_CODES.get(code or "")
    return bool(entry.retryable) if entry is not None else False


__all__ = [
    "ErrorCode",
    "ERROR_CODES",
    "ALL_CODES",
    "RESULT_CODES",
    "PROBLEM_CODES",
    "STATUS_TO_CODE",
    "is_retryable",
]
