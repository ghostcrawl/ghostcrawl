"""
GhostCrawl SDK error class hierarchy.

Usage:
    from ghostcrawl.errors.identity_errors import (
        GhostCrawlError,
        AuthenticationError,
        InvalidRequestError,
        APIError,
    )

    try:
        result = await client.scrape(url="https://example.com")
    except AuthenticationError:
        # api_key is invalid or expired
        ...
    except InvalidRequestError as e:
        # caller sent a bad request (422)
        print(e.body)
    except APIError as e:
        # server-side error (5xx)
        print(e.status_code)

Security note: api_key is NEVER included in error messages or logged. Only the HTTP status
and response body (which never contains the api_key) are surfaced.
"""

from __future__ import annotations

from typing import Any, Optional


class GhostCrawlError(Exception):
    """Base error for all GhostCrawl SDK errors.

    Attributes
    ----------
    status_code : int or None
        HTTP status code returned by the server, if available.
    body : Any
        Parsed response body (usually a dict), if available.
    message : str
        Human-readable error description.
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        body: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.body = body

    def __repr__(self) -> str:
        return f"{type(self).__name__}(status_code={self.status_code!r}, message={self.message!r})"


class AuthenticationError(GhostCrawlError):
    """Raised when the server returns HTTP 401.

    Usually means the api_key is missing, invalid, or expired.
    Check your GHOSTCRAWL_API_KEY or run `ghostcrawl init` to reconfigure.
    """

    def __init__(
        self,
        message: str = "Authentication failed. Check your api_key or run `ghostcrawl init`.",
        status_code: int = 401,
        body: Any = None,
    ) -> None:
        super().__init__(message=message, status_code=status_code, body=body)


class InvalidRequestError(GhostCrawlError):
    """Raised when the server returns HTTP 422 (Unprocessable Entity).

    Usually means the request body failed validation — e.g. an unsupported
    claim_os/claim_browser combination or a missing required field.
    """

    def __init__(
        self,
        message: str = "Invalid request. Check the claim_os, claim_browser, and device_model values.",
        status_code: int = 422,
        body: Any = None,
    ) -> None:
        super().__init__(message=message, status_code=status_code, body=body)


class APIError(GhostCrawlError):
    """Raised when the server returns a 5xx error.

    This is a server-side error. Retry with exponential backoff, or contact
    support if the error persists.
    """

    def __init__(
        self,
        message: str = "Server error. Retry the request or contact support.",
        status_code: Optional[int] = None,
        body: Any = None,
    ) -> None:
        super().__init__(message=message, status_code=status_code, body=body)


class ProviderConfigError(GhostCrawlError):
    """Raised when the server returns error_code='provider_config_invalid' (HTTP 422).

    The LLM model provider configuration is invalid — check ``base_url``,
    ``api_key``, and ``model`` fields. The ``body`` attribute contains the
    structured ``provider_config_invalid`` envelope with ``details.field``
    and ``details.reason``.

    Example::

        try:
            result = client.agent(instruction="...")
        except ProviderConfigError as e:
            print(e.body["details"]["field"])   # e.g. "base_url"
            print(e.body["details"]["reason"])  # e.g. "missing provider base_url"
    """

    def __init__(
        self,
        message: str = "Invalid model provider configuration. Check base_url, api_key, and model.",
        status_code: int = 422,
        body: Any = None,
    ) -> None:
        super().__init__(message=message, status_code=status_code, body=body)
