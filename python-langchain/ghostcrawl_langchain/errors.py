"""ghostcrawl-langchain error classes.

This is the canonical Python status_code → exception class mapping; the Node SDK
(sdks/node/src/errors.ts) and the other official SDK surfaces are kept in lockstep
with it.

Third-party attribution: see sdks/python-langchain/LICENSE-NOTICE.md.
"""
from __future__ import annotations


class GhostCrawlError(Exception):
    """Base class for all ghostcrawl-langchain errors.

    Carries the canonical two-channel fields when known so callers can branch on
    ``code`` / ``retryable`` without parsing the message.
    """

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        retryable: bool = False,
        request_id: str | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.retryable = retryable
        self.request_id = request_id


class GhostCrawlAuthError(GhostCrawlError):
    """401 — Invalid API key or missing Authorization header."""


class GhostCrawlQuotaError(GhostCrawlError):
    """402 — Quota exceeded; upgrade your plan or contact us at https://ghostcrawl.io/billing."""


class GhostCrawlRateLimitError(GhostCrawlError):
    """429 — Rate limited; check retry_after attribute (seconds)."""

    def __init__(
        self,
        message: str,
        retry_after: int | None = None,
        *,
        code: str | None = None,
        request_id: str | None = None,
    ):
        super().__init__(message, code=code, retryable=True, request_id=request_id)
        self.retry_after = retry_after


class GhostCrawlInvalidRequestError(GhostCrawlError):
    """400 / 422 — The request was rejected as invalid before it ran."""


class GhostCrawlServerError(GhostCrawlError):
    """5xx — Retryable server-side error."""


class GhostCrawlScrapeError(GhostCrawlError):
    """A TARGET-side failure reported on an HTTP-200 result.

    The request reached the API fine, but the *target* failed
    (``blocked`` / ``captcha_required`` / ``target_http_error`` /
    ``navigation_failed`` / ``empty_content``). The LangChain tools surface this
    to the LLM as annotated text (so the agent can reason about it) rather than
    raising; this class exists for callers that prefer to ``raise_on_target=True``
    and catch it by type.
    """

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        retryable: bool = False,
        target_status: int | None = None,
        request_id: str | None = None,
    ):
        super().__init__(message, code=code, retryable=retryable, request_id=request_id)
        self.target_status = target_status
