"""GhostCrawl Python SDK — public package surface.

The default client ``GhostCrawl`` is **synchronous** — it Just Works with no
``await`` and no ``asyncio.run`` footgun, even inside Jupyter / a running event
loop. It is a thin loop-thread bridge over the async facade
:class:`ghostcrawl.facade.GhostCrawlClient` (exported as ``AsyncGhostCrawl``),
which itself delegates all HTTP transport, auth, serialization, and model
mapping to the Kiota-generated core (``ghostcrawl/_generated/``).

Quick start (sync default — no ``await``, no ``asyncio.run``)::

    from ghostcrawl import GhostCrawl

    client = GhostCrawl(token="gck_live_YOUR_KEY")
    result = client.scrape(url="https://example.com", format="markdown")
    print(result.markdown)          # typed field; result["markdown"] also works

Async twin (opt-in, only inside ``async def`` code)::

    import asyncio
    from ghostcrawl import AsyncGhostCrawl

    async def main():
        async with AsyncGhostCrawl(token="gck_live_YOUR_KEY") as client:
            result = await client.scrape(url="https://example.com")
            print(result["markdown"])

    asyncio.run(main())

Names: ``GhostCrawl`` / ``Client`` -> the sync default (``SyncGhostCrawl``);
``AsyncGhostCrawl`` / ``GhostCrawlClient`` -> the awaitable async facade.
``token=`` (or ``api_key=`` for back-compat) is required.

Migration: if you previously ``await``-ed the ``GhostCrawl`` alias, either drop
the ``await`` (it is now synchronous) or switch the import to ``AsyncGhostCrawl``.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError

# ---------------------------------------------------------------------------
# Package version — sourced from installed distribution metadata (single source
# of truth = pyproject.toml), so ``ghostcrawl.__version__`` never drifts from
# the published version. Falls back to "0.0.0" only for an uninstalled tree.
# ---------------------------------------------------------------------------
from importlib.metadata import version as _pkg_version

# ---------------------------------------------------------------------------
# Back-compat aliases: ``GhostCrawl`` / ``Client`` -> GhostCrawlClient, and
# ``ProviderConfigError``.
# ---------------------------------------------------------------------------
from ._ghostcrawl import (
    AsyncGhostCrawl,
    Client,
    GhostCrawl,
    ProviderConfigError,
    SyncGhostCrawl,
)

# ---------------------------------------------------------------------------
# Typed-but-dict-accessible result models. Imported straight from the
# stdlib-only ``_results`` module (no kiota dependency) so the types are the
# canonical, parity-locked surface the six non-Python SDKs mirror.
# ---------------------------------------------------------------------------
from ._results import (
    BinaryResult,
    CrawlRun,
    Document,
    ScrapeResult,
    SearchResult,
)

# ---------------------------------------------------------------------------
# Canonical error-code catalog (mirror of the server's codes.json single
# source of truth). Re-exported so callers can branch on stable code strings,
# e.g. ``if err.code in ghostcrawl.RESULT_CODES``.
# ---------------------------------------------------------------------------
from .errors.codes import (
    ALL_CODES,
    ERROR_CODES,
    PROBLEM_CODES,
    RESULT_CODES,
    is_retryable,
)

# ---------------------------------------------------------------------------
# Canonical client + idiomatic surface (Kiota-backed facade)
# ---------------------------------------------------------------------------
from .facade import (
    APIError,
    AuthenticationError,
    CrawlRunsClient,
    DatasetsClient,
    GhostCrawlClient,
    GhostCrawlConnectionError,
    GhostCrawlError,
    GhostCrawlTimeoutError,
    InvalidRequestError,
    KVClient,
    PaymentRequiredError,
    ProfilesClient,
    RateLimitError,
    RecordingsClient,
    SchedulesClient,
    ScrapeError,
    SessionsClient,
    WebhooksClient,
)

# ---------------------------------------------------------------------------
# Request-parameter + retry helpers (standalone ergonomic extensions).
# ---------------------------------------------------------------------------
from .params import (
    build_extract_rules,
    build_js_scenario,
    encode_js_snippet,
    format_cookies,
    format_cookies_urlencoded,
)
from .retry_policy import RetryPolicy, with_retries

try:
    __version__ = _pkg_version("ghostcrawl")
except PackageNotFoundError:  # source tree not pip-installed
    __version__ = "0.0.0"

__all__ = [
    "__version__",
    # Sync default + async twin
    "GhostCrawl",
    "Client",
    "SyncGhostCrawl",
    "AsyncGhostCrawl",
    "GhostCrawlClient",
    # Resource sub-clients
    "CrawlRunsClient",
    "SessionsClient",
    "ProfilesClient",
    "WebhooksClient",
    "SchedulesClient",
    "DatasetsClient",
    "RecordingsClient",
    "KVClient",
    # Typed result models
    "ScrapeResult",
    "SearchResult",
    "CrawlRun",
    "Document",
    "BinaryResult",
    # Errors
    "GhostCrawlError",
    "AuthenticationError",
    "RateLimitError",
    "PaymentRequiredError",
    "InvalidRequestError",
    "APIError",
    "ScrapeError",
    "GhostCrawlConnectionError",
    "GhostCrawlTimeoutError",
    "ProviderConfigError",
    # Error-code catalog
    "ALL_CODES",
    "RESULT_CODES",
    "PROBLEM_CODES",
    "ERROR_CODES",
    "is_retryable",
    # Helpers
    "encode_js_snippet",
    "format_cookies",
    "format_cookies_urlencoded",
    "build_extract_rules",
    "build_js_scenario",
    "RetryPolicy",
    "with_retries",
]
