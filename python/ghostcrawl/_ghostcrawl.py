"""Public client aliases — sync default (``GhostCrawl``) + async twin (``AsyncGhostCrawl``).

``from ghostcrawl import GhostCrawl`` now gives a **synchronous** client
(:class:`ghostcrawl._sync.SyncGhostCrawl`) so ``GhostCrawl(token=...).scrape(url)``
returns rendered content directly — no ``await``, no ``asyncio.run`` footgun
. ``Client`` is the same sync default.

The async facade (:class:`ghostcrawl.facade.GhostCrawlClient`) remains the
awaitable opt-in under two names: the new ``AsyncGhostCrawl`` and the historical
``GhostCrawlClient`` (kept so existing ``await``-ing code is unaffected).

**Migration note:** if you previously did ``await GhostCrawl(...).scrape(url)``,
the ``GhostCrawl`` alias is now synchronous — drop the ``await`` (``GhostCrawl(...).scrape(url)``),
or switch the import to ``AsyncGhostCrawl`` to keep the awaitable surface.

Everything HTTP, auth, serialization, and model mapping lives in the generated
core (``ghostcrawl/_generated/``); the sync client is a pure delegation bridge
over the async facade (no duplicated transport).
"""

from __future__ import annotations

# The synchronous default — a loop-thread bridge over the async facade.
from ._sync import SyncGhostCrawl
from .errors.identity_errors import ProviderConfigError  # noqa: F401

# Back-compat error names. ``GhostCrawlError`` / ``AuthenticationError`` /
# ``InvalidRequestError`` / ``APIError`` are the facade's typed errors (carrying
# the canonical code/retryable fields); ``ProviderConfigError`` keeps its
# dedicated meaning from the identity error module.
from .facade import (
    APIError,  # noqa: F401
    AuthenticationError,  # noqa: F401
    GhostCrawlError,  # noqa: F401 — re-exported for back-compat
    InvalidRequestError,  # noqa: F401
)

# The async facade is the canonical client the sync twin delegates to. It stays
# exposed under ``AsyncGhostCrawl`` (new) and ``GhostCrawlClient`` (historical).
from .facade import GhostCrawlClient as _GhostCrawlClient

# Sync default: ``GhostCrawl`` / ``Client`` -> the loop-thread-bridged
# synchronous client. Async twin: ``AsyncGhostCrawl`` (new) and
# ``GhostCrawlClient`` (historical) both resolve to the awaitable facade.
GhostCrawl = SyncGhostCrawl
Client = SyncGhostCrawl
AsyncGhostCrawl = _GhostCrawlClient
GhostCrawlClient = _GhostCrawlClient


__all__ = [
    "GhostCrawl",
    "Client",
    "SyncGhostCrawl",
    "AsyncGhostCrawl",
    "GhostCrawlClient",
    "GhostCrawlError",
    "AuthenticationError",
    "InvalidRequestError",
    "APIError",
    "ProviderConfigError",
]
