"""Shared httpx client factory for ghostcrawl-langchain tools."""
from __future__ import annotations
import os
import platform
import sys
from importlib.metadata import PackageNotFoundError, version

import httpx


def _ua() -> str:
    try:
        v = version("ghostcrawl-langchain")
    except PackageNotFoundError:
        v = "0.0.0"
    return (
        f"ghostcrawl-langchain/{v} "
        f"Python/{sys.version_info.major}.{sys.version_info.minor} "
        f"{platform.system()}"
    )


def get_client(
    api_key: str | None = None,
    base_url: str | None = None,
) -> httpx.Client:
    """Return a configured httpx.Client with Bearer auth and branded User-Agent.

    Auth is read from the ``api_key`` argument first, then the
    ``GHOSTCRAWL_API_KEY`` environment variable.  Raises ``ValueError`` if
    neither is set.

    The ``base_url`` argument overrides ``GHOSTCRAWL_BASE_URL`` (defaults to
    ``https://api.ghostcrawl.io``).
    """
    key = (api_key or os.environ.get("GHOSTCRAWL_API_KEY", "")).strip()
    if not key:
        raise ValueError(
            "ghostcrawl-langchain: GHOSTCRAWL_API_KEY is not set. "
            "Set the GHOSTCRAWL_API_KEY environment variable or pass api_key to get_client()."
        )
    resolved_base = (
        base_url
        or os.environ.get("GHOSTCRAWL_BASE_URL", "https://api.ghostcrawl.io")
    ).rstrip("/")
    return httpx.Client(
        base_url=resolved_base,
        headers={
            "Authorization": f"Bearer {key}",
            "User-Agent": _ua(),
            "Content-Type": "application/json",
        },
        timeout=60.0,
    )


def get_async_client(
    api_key: str | None = None,
    base_url: str | None = None,
) -> httpx.AsyncClient:
    """Return a configured ``httpx.AsyncClient`` mirroring :func:`get_client`.

    Used by LangChain BaseTool ``_arun`` overrides so the async path does not
    block the event loop on synchronous I/O.
    """
    key = (api_key or os.environ.get("GHOSTCRAWL_API_KEY", "")).strip()
    if not key:
        raise ValueError(
            "ghostcrawl-langchain: GHOSTCRAWL_API_KEY is not set. "
            "Set the GHOSTCRAWL_API_KEY environment variable or pass api_key to get_async_client()."
        )
    resolved_base = (
        base_url
        or os.environ.get("GHOSTCRAWL_BASE_URL", "https://api.ghostcrawl.io")
    ).rstrip("/")
    return httpx.AsyncClient(
        base_url=resolved_base,
        headers={
            "Authorization": f"Bearer {key}",
            "User-Agent": _ua(),
            "Content-Type": "application/json",
        },
        timeout=60.0,
    )
