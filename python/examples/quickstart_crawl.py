"""Quickstart: crawl a site and wait for the run to finish.

Run with:
    GHOSTCRAWL_API_KEY=gck_live_YOUR_KEY python examples/quickstart_crawl.py
"""

from __future__ import annotations

import os
import sys
import time

from ghostcrawl import GhostCrawl, APIError

# Gateway statuses that mean "try again" — the crawl worker can cold-start.
_RETRYABLE = {502, 503, 504}


def main() -> None:
    token = os.environ.get("GHOSTCRAWL_API_KEY")
    if not token:
        print("Set GHOSTCRAWL_API_KEY in your environment.", file=sys.stderr)
        sys.exit(1)

    client = GhostCrawl(token=token)

    # Start the crawl and wait for it in one call. This is EVENT-DRIVEN:
    # the server blocks until the run is terminal (completed/failed/
    # cancelled) or wait_timeout elapses — there is NO client poll loop.
    # The transient-error retry below is still legitimate: it rides through
    # a cold-starting worker before the run even begins.
    run = None
    max_attempts = 12
    for attempt in range(max_attempts):
        try:
            run = client.crawl(
                url="https://example.com",
                max_depth=2,
                max_pages=25,
                wait=True,          # start-and-wait (server blocks)
                wait_timeout=300,   # overall completion budget, seconds
            )
            break
        except APIError as exc:
            if exc.status_code in _RETRYABLE and attempt < max_attempts - 1:
                time.sleep(2)
                continue
            raise

    print(f"Run {run['run_id']} finished: {run.get('status')}")
    print(f"Pages crawled: {run.get('pages_crawled', 0)}")


if __name__ == "__main__":
    main()
