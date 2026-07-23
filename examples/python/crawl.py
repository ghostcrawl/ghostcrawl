"""Start a crawl run and wait for it to finish.

    pip install ghostcrawl
    export GHOSTCRAWL_API_KEY=YOUR_API_KEY
    python crawl.py
"""

import asyncio
import os

from ghostcrawl import GhostcrawlClient


async def main() -> None:
    async with GhostcrawlClient(api_key=os.environ["GHOSTCRAWL_API_KEY"]) as client:
        # Start the crawl and wait for it in one call. This is event-driven:
        # the server blocks until the run is terminal (completed/failed/
        # cancelled) or the timeout elapses — there is no client poll loop.
        run = await client.crawl_runs.start(
            url="https://example.com",
            max_depth=2,
            max_pages=25,
            wait=True,          # start-and-wait (server blocks)
            wait_timeout=300,   # completion budget, seconds
        )
        print("run id:", run["run_id"])
        print("status:", run.get("status"))
        print("pages crawled:", run.get("pages_crawled", 0))


if __name__ == "__main__":
    asyncio.run(main())
