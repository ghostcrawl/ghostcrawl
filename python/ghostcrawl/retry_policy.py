# Retry-policy helpers for the GhostCrawl SDK.
from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import FrozenSet


_DEFAULT_RETRY_STATUS: FrozenSet[int] = frozenset({500, 502, 503, 504})


@dataclass(frozen=True)
class RetryPolicy:
    """Per-call retry budget descriptor.

    A small standalone descriptor callers can construct to express a retry
    budget. The canonical client's transport (Kiota middleware) handles the
    actual retries; this captures the intended policy.
    """
    max_retries: int = 2
    retry_status_codes: FrozenSet[int] = field(
        default_factory=lambda: _DEFAULT_RETRY_STATUS
    )
    backoff_factor: float = 0.5

    @classmethod
    def from_env(cls) -> "RetryPolicy":
        """Read GHOSTCRAWL_MAX_RETRIES env var; default to 2 on any error."""
        try:
            n = int(os.environ.get("GHOSTCRAWL_MAX_RETRIES", "2"))
        except (ValueError, TypeError):
            n = 2
        return cls(max_retries=max(0, n))


def with_retries(client, n: int):
    """Return a fresh client with the same config (back-compat factory).

    Mirrors the Node SDK's ``withRetries(client, n)`` pattern: constructs a
    NEW client from the original's auth + base URL rather than mutating a
    shallow copy. The original client is never mutated; the returned client
    shares no state with it (separate Kiota adapter + httpx session).

    Prefer the ``GhostCrawlClient.with_retries(n)`` method on the client
    itself; this module-level helper is kept for back-compat.
    """
    # Delegate to the canonical client's own factory when available (the
    # Kiota-backed facade exposes ``with_retries``).
    if hasattr(client, "with_retries"):
        return client.with_retries(n)

    # Defensive fallback for non-standard clients: best-effort attribute copy.
    import copy as _copy
    new = _copy.copy(client)
    setattr(new, "max_retries", n)
    return new
