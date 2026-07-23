"""GhostCrawl SDK error surface.

Re-exports the typed error hierarchy and the canonical error-code catalog.

The error classes that callers branch on (``GhostCrawlError`` and its
subclasses) are defined on :mod:`ghostcrawl.facade` and surfaced from the
package root; the identity-flow variants live in
:mod:`ghostcrawl.errors.identity_errors`. The :mod:`ghostcrawl.errors.codes`
module mirrors the server's single source of truth for error codes.
"""

from __future__ import annotations

from .codes import (
    ALL_CODES,
    RESULT_CODES,
    PROBLEM_CODES,
    ERROR_CODES,
    CHANNELS,
    ErrorCode,
    is_retryable,
)
from .identity_errors import (
    GhostCrawlError,
    AuthenticationError,
    InvalidRequestError,
    APIError,
    ProviderConfigError,
)

__all__ = [
    "ALL_CODES",
    "RESULT_CODES",
    "PROBLEM_CODES",
    "ERROR_CODES",
    "CHANNELS",
    "ErrorCode",
    "is_retryable",
    "GhostCrawlError",
    "AuthenticationError",
    "InvalidRequestError",
    "APIError",
    "ProviderConfigError",
]
