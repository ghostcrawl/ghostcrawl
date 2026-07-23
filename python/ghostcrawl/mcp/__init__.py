"""Typed MCP wrapper for ghostcrawl REST SDK.

Provides ``GhostCrawlMCPClient`` — an async client that connects to the
ghostcrawl MCP server via the streamable-HTTP transport and exposes a typed
method for every registered ``@mcp.tool()`` function.

Usage::

    import asyncio
    from ghostcrawl.mcp import GhostCrawlMCPClient

    async def main():
        client = GhostCrawlMCPClient(
            mcp_url="http://localhost:8090/mcp",
            api_key="your-api-key",
        )
        result = await client.navigate(url="https://example.com")
        print(result)

    asyncio.run(main())
"""

from .wrapper import GhostCrawlMCPClient

__all__ = ["GhostCrawlMCPClient"]
