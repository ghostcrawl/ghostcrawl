"""Drive GhostCrawl's MCP surface from Python.

    pip install ghostcrawl
    export GHOSTCRAWL_API_KEY=YOUR_API_KEY
    python client.py

The Python SDK ships a typed wrapper over the MCP streamable-HTTP transport.
"""

import asyncio
import os

from ghostcrawl.mcp import GhostcrawlMCPClient


async def main() -> None:
    mcp = GhostcrawlMCPClient(
        mcp_url="https://mcp.ghostcrawl.io",
        api_key=os.environ["GHOSTCRAWL_API_KEY"],
    )
    await mcp.connect()
    try:
        await mcp.navigate(url="https://example.com")
        await mcp.act(goal="Find the contact email")
        data = await mcp.extract(
            schema={
                "type": "object",
                "properties": {"title": {"type": "string"}},
            }
        )
        print(data)
    finally:
        await mcp.close()


if __name__ == "__main__":
    asyncio.run(main())
