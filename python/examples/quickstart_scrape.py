"""Quickstart: scrape a single page.

Run with:
    GHOSTCRAWL_API_KEY=gck_live_YOUR_KEY python examples/quickstart_scrape.py
"""

from __future__ import annotations

import asyncio
import os
import sys


async def main() -> None:
    token = os.environ.get("GHOSTCRAWL_API_KEY")
    if not token:
        print("Set GHOSTCRAWL_API_KEY in your environment.", file=sys.stderr)
        sys.exit(1)

    from ghostcrawl import GhostCrawlClient

    async with GhostCrawlClient(token=token) as client:
        result = await client.scrape(url="https://example.com", format="markdown")
        print("Scrape status:", result.get("status", "unknown"))
        # identity_id (Phase 140.4-16 response envelope field) — printed so a caller can
        # correlate this exact drive to its server-side egress-exit assignment (D-04, phase 177).
        print("identity_id:", result.get("identity_id", "unknown"))
        # The API returns content in the field matching the requested format.
        # format="markdown" → result["markdown"]; format="html" → result["html"]
        content = result.get("markdown") or result.get("content") or result.get("html", "")
        print("Content preview:")
        print(content[:500] if isinstance(content, str) else str(content)[:500])


if __name__ == "__main__":
    asyncio.run(main())
