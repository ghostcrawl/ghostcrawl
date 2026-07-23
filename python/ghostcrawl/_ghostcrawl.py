"""Back-compat aliases for the canonical Kiota-backed client surface.

Historically this module hosted a hand-written synchronous ``GhostCrawl``
class. The single canonical client is now the Kiota-backed async
:class:`ghostcrawl.facade.GhostCrawlClient`. To keep existing user code working
without change, ``GhostCrawl`` and ``Client`` are aliases of that facade, and
the functional ``identity(...)`` convenience wrapper resolves through it.

Everything HTTP, auth, serialization, and model mapping lives in the generated
core (``_generated/``); this module is purely a thin compatibility shim.
"""

from __future__ import annotations

# The canonical client + error surface live on the facade. Re-export them under
# the historical names so ``from ghostcrawl import GhostCrawl`` / ``Client``
# keep resolving.
from .facade import GhostCrawlClient as _GhostCrawlClient

# Back-compat error names. ``GhostCrawlError`` / ``AuthenticationError`` /
# ``InvalidRequestError`` / ``APIError`` are the facade's typed errors (carrying
# the canonical code/retryable fields); ``ProviderConfigError`` keeps its
# dedicated meaning from the identity error module.
from .facade import (
    GhostCrawlError,  # noqa: F401 — re-exported for back-compat
    AuthenticationError,  # noqa: F401
    InvalidRequestError,  # noqa: F401
    APIError,  # noqa: F401
)
from .errors.identity_errors import ProviderConfigError  # noqa: F401


# ``GhostCrawl`` and ``Client`` are the canonical client under their historical
# names. New code should import ``GhostCrawlClient`` directly.
GhostCrawl = _GhostCrawlClient
Client = _GhostCrawlClient


__all__ = [
    "GhostCrawl",
    "Client",
    "GhostCrawlError",
    "AuthenticationError",
    "InvalidRequestError",
    "APIError",
    "ProviderConfigError",
]
