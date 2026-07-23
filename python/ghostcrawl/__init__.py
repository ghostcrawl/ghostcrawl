"""GhostCrawl Python SDK — public package surface.

The canonical client is :class:`ghostcrawl.facade.GhostCrawlClient`, a thin
async ergonomic layer over the Kiota-generated core (``_generated/``). All HTTP
transport, auth, serialization, and model mapping live in the generated core;
the facade maps idiomatic calls onto the generated request-builders.

Quick start::

    import asyncio
    from ghostcrawl import GhostCrawlClient

    async def main():
        async with GhostCrawlClient(token="gck_live_YOUR_KEY") as client:
            result = await client.scrape(url="https://example.com")
            print(result["markdown"])

    asyncio.run(main())

Back-compat: ``GhostCrawl`` and ``Client`` are aliases of ``GhostCrawlClient``;
``GhostCrawlClient(api_key=...)`` is accepted as an alias for ``token=``.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Canonical client + idiomatic surface (Kiota-backed facade)
# ---------------------------------------------------------------------------
from .facade import (
    GhostCrawlClient,
    GhostCrawlError,
    AuthenticationError,
    RateLimitError,
    PaymentRequiredError,
    InvalidRequestError,
    APIError,
    ScrapeError,
    CrawlRunsClient,
    SessionsClient,
    ProfilesClient,
    WebhooksClient,
    SchedulesClient,
    DatasetsClient,
    RecordingsClient,
    KVClient,
)

# ---------------------------------------------------------------------------
# Back-compat aliases: ``GhostCrawl`` / ``Client`` -> GhostCrawlClient, and
# ``ProviderConfigError``.
# ---------------------------------------------------------------------------
from ._ghostcrawl import (
    GhostCrawl,
    Client,
    ProviderConfigError,
)

# ---------------------------------------------------------------------------
# Canonical error-code catalog (mirror of the server's codes.json single
# source of truth). Re-exported so callers can branch on stable code strings,
# e.g. ``if err.code in ghostcrawl.RESULT_CODES``.
# ---------------------------------------------------------------------------
from .errors.codes import (
    ALL_CODES,
    RESULT_CODES,
    PROBLEM_CODES,
    ERROR_CODES,
    is_retryable,
)

# ---------------------------------------------------------------------------
# Request-parameter + retry helpers (standalone ergonomic extensions).
# ---------------------------------------------------------------------------
from .params import (
    encode_js_snippet,
    format_cookies,
    format_cookies_urlencoded,
    build_extract_rules,
    build_js_scenario,
)
from .retry_policy import RetryPolicy, with_retries

# ---------------------------------------------------------------------------
# Package version — sourced from installed distribution metadata (single source
# of truth = pyproject.toml), so ``ghostcrawl.__version__`` never drifts from
# the published version. Falls back to "0.0.0" only for an uninstalled tree.
# ---------------------------------------------------------------------------
from importlib.metadata import version as _pkg_version, PackageNotFoundError

try:
    __version__ = _pkg_version("ghostcrawl")
except PackageNotFoundError:  # source tree not pip-installed
    __version__ = "0.0.0"

__all__ = [
    "__version__",
    # Canonical client + aliases
    "GhostCrawlClient",
    "GhostCrawl",
    "Client",
    # Resource sub-clients
    "CrawlRunsClient",
    "SessionsClient",
    "ProfilesClient",
    "WebhooksClient",
    "SchedulesClient",
    "DatasetsClient",
    "RecordingsClient",
    "KVClient",
    # Errors
    "GhostCrawlError",
    "AuthenticationError",
    "RateLimitError",
    "PaymentRequiredError",
    "InvalidRequestError",
    "APIError",
    "ScrapeError",
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
