"""Scrape several pages concurrently with the async client.

    pip install ghostcrawl
    export GHOSTCRAWL_API_KEY=YOUR_API_KEY
    python async_scrape.py
"""

import asyncio
import os

from ghostcrawl import AsyncGhostCrawl

URLS = [
    "https://example.com",
    "https://example.org",
    "https://example.net",
]


async def main() -> None:
    async with AsyncGhostCrawl(api_key=os.environ["GHOSTCRAWL_API_KEY"]) as client:
        results = await asyncio.gather(
            *(client.scrape(url=url, engine="auto") for url in URLS)
        )
        for url, result in zip(URLS, results):
            print(url, "->", result)


if __name__ == "__main__":
    asyncio.run(main())
