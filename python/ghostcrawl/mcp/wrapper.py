"""Typed MCP client wrapping mcp.ClientSession over streamable-HTTP transport.

Hand-written (~200 LOC); a thin typed layer over the MCP tool surface, distinct
from the REST client.

Transport: ``mcp.client.streamable_http.streamable_http_client``
(the current name; the old non-underscore alias is deprecated).

Every method below corresponds to a registered MCP tool on the GhostCrawl
server. Methods where the tool schema requires a primary positional argument
expose that argument explicitly; all other parameters flow through ``**kwargs``.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client  # current name; old alias is deprecated


# ----------------------------------------------------------------------------
# Canonical tool-name reconciliation (D-11)
# ----------------------------------------------------------------------------
# The native GhostCrawl MCP server (``ghostcrawl.mcp.tools.TOOL_REGISTRY``) exposes
# every tool under the canonical ``ghostcrawl_*`` (data-plane) / ``act_*`` (browser
# primitive) / ``action_record_*`` namespaces — NOT the bare ``navigate`` / ``act``
# aliases the standalone (now-retired) server used. This wrapper keeps ergonomic
# method names but reconciles each call to the real registry tool name before it
# hits the wire, so it drives the native streamable-HTTP server directly.
_TOOL_NAMES: dict[str, str] = {
    "navigate": "ghostcrawl_navigate",
    "act": "ghostcrawl_act",
    "act_on": "ghostcrawl_act",
    "observe": "ghostcrawl_observe",
    "extract": "ghostcrawl_extract",
    "scrape": "ghostcrawl_scrape",
    "screenshot": "ghostcrawl_screenshot",
    "screenshot_of": "ghostcrawl_screenshot",
    "search": "ghostcrawl_search",
    "google_search": "ghostcrawl_search",
    "map_site": "ghostcrawl_map",
    "pdf": "ghostcrawl_pdf",
    "crawl": "ghostcrawl_crawl",
    "eval": "act_evaluate",
    "run_script": "ghostcrawl_script_run",
    "upload_file": "act_upload",
    "start": "ghostcrawl_session_create",
    "end": "ghostcrawl_session_terminate",
    "start_recording": "action_record_start",
    "stop_recording": "action_record_stop",
    "ping": "ping",  # server health tool is registered literally as ``ping``
}

_CANONICAL_PREFIXES = ("ghostcrawl_", "act_", "action_")


def _canonical_tool(name: str) -> str:
    """Map a wrapper method's logical name to the real MCP registry tool name.

    Explicit mappings win; anything already in a canonical namespace passes
    through unchanged; everything else takes the ``ghostcrawl_`` data-plane
    prefix (the naming rule the server enforces for GhostCrawl-owned tools).
    """
    if name in _TOOL_NAMES:
        return _TOOL_NAMES[name]
    if name.startswith(_CANONICAL_PREFIXES) or name == "ping":
        return name
    return f"ghostcrawl_{name}"


class GhostCrawlMCPClient:
    """Typed wrapper for the ghostcrawl MCP tool surface via streamable-HTTP.

    Parameters
    ----------
    mcp_url:
        Full URL of the MCP endpoint, e.g. ``http://localhost:8090/mcp``.
    api_key:
        Bearer token for the API.  Read from ``GHOSTCRAWL_API_KEY`` env var
        in CLI contexts; passed explicitly when constructing programmatically.
    timeout:
        Per-request timeout in seconds (default: 30).
    """

    def __init__(self, mcp_url: str, api_key: str, timeout: float = 30.0) -> None:
        if not mcp_url:
            raise ValueError("mcp_url is required and must not be empty")
        if not api_key:
            raise ValueError("api_key is required and must not be empty")
        self._url = mcp_url
        self._api_key = api_key
        self._timeout = timeout
        self._headers: dict[str, str] = {"Authorization": f"Bearer {api_key}"}

    # ------------------------------------------------------------------
    # Session context manager
    # ------------------------------------------------------------------

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[ClientSession, None]:
        """Open an MCP session over streamable-HTTP and yield it.

        Callers should use this when they want to batch multiple tool calls
        in a single connection.  All public tool methods open their own
        short-lived sessions via this context manager internally.
        """
        http = httpx.AsyncClient(headers=self._headers, timeout=self._timeout)
        try:
            async with streamable_http_client(self._url, http_client=http) as (
                read,
                write,
                _get_session_id,
            ):
                async with ClientSession(read, write) as s:
                    await s.initialize()
                    yield s
        finally:
            await http.aclose()

    # ------------------------------------------------------------------
    # Internal helper
    # ------------------------------------------------------------------

    async def _call(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Open a session, call *tool_name* with *arguments*, and return the result.

        *tool_name* is reconciled to the canonical native-registry name
        (``ghostcrawl_*`` / ``act_*``) via :func:`_canonical_tool` before the call.
        """
        async with self.session() as s:
            return await s.call_tool(_canonical_tool(tool_name), arguments)

    # ------------------------------------------------------------------
    # Browser / navigation tools
    # ------------------------------------------------------------------

    async def navigate(self, url: str, **kwargs: Any) -> Any:
        """Navigate the current browser context to *url*."""
        return await self._call("navigate", {"url": url, **kwargs})

    async def act(self, goal: str, **kwargs: Any) -> Any:
        """Perform a high-level browser action described by *goal*."""
        return await self._call("act", {"goal": goal, **kwargs})

    async def observe(self, **kwargs: Any) -> Any:
        """Return an observation of the current browser state."""
        return await self._call("observe", kwargs)

    async def extract(self, **kwargs: Any) -> Any:
        """Extract structured data from the current page."""
        return await self._call("extract", kwargs)

    async def scrape(self, url: str, **kwargs: Any) -> Any:
        """Scrape content from *url* and return extracted data."""
        return await self._call("scrape", {"url": url, **kwargs})

    async def screenshot(self, **kwargs: Any) -> Any:
        """Take a screenshot of the current page or a given URL."""
        return await self._call("screenshot", kwargs)

    async def screenshot_of(self, selector: str, **kwargs: Any) -> Any:
        """Take a screenshot of the element matching *selector*."""
        return await self._call("screenshot_of", {"selector": selector, **kwargs})

    async def dom_snapshot(self, **kwargs: Any) -> Any:
        """Return a DOM snapshot of the current page."""
        return await self._call("dom_snapshot", kwargs)

    async def network(self, **kwargs: Any) -> Any:
        """Retrieve network request/response data for the current page."""
        return await self._call("network", kwargs)

    async def network_har(self, **kwargs: Any) -> Any:
        """Return a HAR archive of network traffic for the current page."""
        return await self._call("network_har", kwargs)

    async def scroll(self, **kwargs: Any) -> Any:
        """Scroll the page or a specific element."""
        return await self._call("scroll", kwargs)

    async def cookies(self, **kwargs: Any) -> Any:
        """Get or set cookies for the current browser context."""
        return await self._call("cookies", kwargs)

    async def wait(self, **kwargs: Any) -> Any:
        """Wait for a condition (selector, network idle, timeout, etc.)."""
        return await self._call("wait", kwargs)

    async def eval(self, **kwargs: Any) -> Any:
        """Evaluate arbitrary JavaScript in the current page context."""
        return await self._call("eval", kwargs)

    async def run_script(self, **kwargs: Any) -> Any:
        """Run a pre-defined browser script by name."""
        return await self._call("run_script", kwargs)

    async def act_on(self, **kwargs: Any) -> Any:
        """Perform an action on a specific element."""
        return await self._call("act_on", kwargs)

    # ------------------------------------------------------------------
    # File / storage tools
    # ------------------------------------------------------------------

    async def upload_file(self, **kwargs: Any) -> Any:
        """Upload a file to the current page context."""
        return await self._call("upload_file", kwargs)

    async def download_file(self, **kwargs: Any) -> Any:
        """Download a file from the current page."""
        return await self._call("download_file", kwargs)

    async def storage_state(self, **kwargs: Any) -> Any:
        """Get or set the storage state (cookies, localStorage) of the context."""
        return await self._call("storage_state", kwargs)

    # ------------------------------------------------------------------
    # Crawl / dataset tools
    # ------------------------------------------------------------------

    async def crawl(self, **kwargs: Any) -> Any:
        """Start or manage a crawl job."""
        return await self._call("crawl", kwargs)

    async def dataset(self, **kwargs: Any) -> Any:
        """Interact with a ghostcrawl dataset resource."""
        return await self._call("dataset", kwargs)

    # ------------------------------------------------------------------
    # Session lifecycle tools
    # ------------------------------------------------------------------

    async def start(self, **kwargs: Any) -> Any:
        """Start a new browser session."""
        return await self._call("start", kwargs)

    async def end(self, **kwargs: Any) -> Any:
        """End an existing browser session."""
        return await self._call("end", kwargs)

    async def start_many(self, **kwargs: Any) -> Any:
        """Start multiple browser sessions at once."""
        return await self._call("start_many", kwargs)

    async def end_all(self, **kwargs: Any) -> Any:
        """End all active browser sessions."""
        return await self._call("end_all", kwargs)

    # ------------------------------------------------------------------
    # Recording tools
    # ------------------------------------------------------------------

    async def start_recording(self, **kwargs: Any) -> Any:
        """Start recording a browser session."""
        return await self._call("start_recording", kwargs)

    async def stop_recording(self, **kwargs: Any) -> Any:
        """Stop the current recording."""
        return await self._call("stop_recording", kwargs)

    async def list_recordings(self, **kwargs: Any) -> Any:
        """List all stored recordings."""
        return await self._call("list_recordings", kwargs)

    async def get_recording(self, **kwargs: Any) -> Any:
        """Retrieve a specific recording by ID."""
        return await self._call("get_recording", kwargs)

    async def delete_recording(self, **kwargs: Any) -> Any:
        """Delete a recording by ID."""
        return await self._call("delete_recording", kwargs)

    async def ping(self) -> Any:
        """Health-check tool.  Returns 'pong'.  Verifies server is reachable.

        Mirrors the server-side ``@mcp.tool() ping()`` registered in
        ``ghostcrawl_mcp_server/server.py``.
        """
        return await self._call("ping", {})

    # ------------------------------------------------------------------
    # Search tools
    # ------------------------------------------------------------------

    async def search(self, query: str, **kwargs: Any) -> Any:
        """Search the web and return structured results."""
        return await self._call("search", {"query": query, **kwargs})

    async def google_search(self, query: str, **kwargs: Any) -> Any:
        """Search Google (or a specific Google vertical) and return SERP results."""
        return await self._call("google_search", {"query": query, **kwargs})

    # ------------------------------------------------------------------
    # Site map tools
    # ------------------------------------------------------------------

    async def map_site(self, url: str, **kwargs: Any) -> Any:
        """Map all pages on a website starting from *url*."""
        return await self._call("map_site", {"url": url, **kwargs})

    async def discovery(self, domain: str, **kwargs: Any) -> Any:
        """Retrieve previously discovered links for *domain*."""
        return await self._call("discovery", {"domain": domain, **kwargs})

    # ------------------------------------------------------------------
    # Identity / profile tools
    # ------------------------------------------------------------------

    async def identity(self, **kwargs: Any) -> Any:
        """Materialise a fresh browser identity."""
        return await self._call("identity", kwargs)

    async def profiles(self, **kwargs: Any) -> Any:
        """Create, get, list, delete, or view recent browser profiles."""
        return await self._call("profiles", kwargs)

    # ------------------------------------------------------------------
    # PDF tool
    # ------------------------------------------------------------------

    async def pdf(self, url: str, **kwargs: Any) -> Any:
        """Render a web page at *url* to PDF."""
        return await self._call("pdf", {"url": url, **kwargs})

    # ------------------------------------------------------------------
    # Key-value store
    # ------------------------------------------------------------------

    async def kv(self, **kwargs: Any) -> Any:
        """Read, write, or delete entries in the persistent key-value store."""
        return await self._call("kv", kwargs)

    # ------------------------------------------------------------------
    # Schedule tools
    # ------------------------------------------------------------------

    async def schedule(self, **kwargs: Any) -> Any:
        """Create, list, get, update, or delete recurring schedules."""
        return await self._call("schedule", kwargs)

    # ------------------------------------------------------------------
    # Webhook tools
    # ------------------------------------------------------------------

    async def webhook(self, **kwargs: Any) -> Any:
        """Register, list, inspect, retry, or rotate secrets for webhooks."""
        return await self._call("webhook", kwargs)

    # ------------------------------------------------------------------
    # Budget / usage tools
    # ------------------------------------------------------------------

    async def budget(self, **kwargs: Any) -> Any:
        """Manage spending controls and view usage for your account."""
        return await self._call("budget", kwargs)

    # ------------------------------------------------------------------
    # Unblock tool
    # ------------------------------------------------------------------

    async def unblock(self, url: str, **kwargs: Any) -> Any:
        """Retrieve *url* reliably through the managed browser fleet."""
        return await self._call("unblock", {"url": url, **kwargs})

    # ------------------------------------------------------------------
    # Lighthouse tool
    # ------------------------------------------------------------------

    async def lighthouse(self, url: str, **kwargs: Any) -> Any:
        """Run a performance and quality audit on *url*."""
        return await self._call("lighthouse", {"url": url, **kwargs})

    # ------------------------------------------------------------------
    # Queue tools
    # ------------------------------------------------------------------

    async def queue(self, **kwargs: Any) -> Any:
        """Push, pop, acknowledge, or view stats for a named task queue."""
        return await self._call("queue", kwargs)

    # ------------------------------------------------------------------
    # Self-host / account utilities
    # ------------------------------------------------------------------

    async def check_updates(self, **kwargs: Any) -> Any:
        """Check for available platform updates."""
        return await self._call("check_updates", kwargs)

    async def registry_token(self, **kwargs: Any) -> Any:
        """Obtain a short-lived container image pull token."""
        return await self._call("registry_token", kwargs)

    # ------------------------------------------------------------------
    # Takeover tools
    # ------------------------------------------------------------------

    async def takeover_token(self, session_id: str, **kwargs: Any) -> Any:
        """Mint a short-lived token to take live control of *session_id*."""
        return await self._call("takeover_token", {"session_id": session_id, **kwargs})

    async def takeover_release(self, session_id: str, **kwargs: Any) -> Any:
        """Release a live-view token for *session_id*."""
        return await self._call("takeover_release", {"session_id": session_id, **kwargs})
