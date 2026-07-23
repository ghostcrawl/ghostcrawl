"""Example: fetch YouTube video metadata via ghostcrawl /v1/scrape against
YouTube's public oEmbed endpoint.

Docs-only example (parallels MKT-AMAZON-REVIEWS-EXAMPLE per Phase 140.2 D-08).
ghostcrawl does NOT own a YouTube oEmbed route — this example shows how to
hit youtube.com/oembed through ghostcrawl's generic /v1/scrape, which keeps
auth + stealth + observability consistent with the rest of the SaaS.

Run with:

    GHOSTCRAWL_API_KEY=gck_live_... python examples/youtube-oembed-example.py \\
        https://www.youtube.com/watch?v=dQw4w9WgXcQ
"""
from __future__ import annotations
import asyncio
import json
import os
import sys
import urllib.parse
from ghostcrawl import GhostCrawlClient

OEMBED_BASE = "https://www.youtube.com/oembed"


def build_oembed_url(video_url: str) -> str:
    qs = urllib.parse.urlencode({"url": video_url, "format": "json"})
    return f"{OEMBED_BASE}?{qs}"


async def main(video_url: str | None = None) -> int:
    api_key = os.environ.get("GHOSTCRAWL_API_KEY", "")
    if not api_key:
        print("Error: GHOSTCRAWL_API_KEY environment variable required", file=sys.stderr)
        return 1
    target = video_url or "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    oembed = build_oembed_url(target)
    async with GhostCrawlClient(token=api_key) as gc:
        # /v1/scrape returns the oembed JSON body as the page content.
        result = await gc.scrape(url=oembed)
    content = result.get("content") or result.get("markdown") or result.get("html", "")
    print(content if isinstance(content, str) else json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else None)))
