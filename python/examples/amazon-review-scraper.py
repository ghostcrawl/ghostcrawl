"""Example: scrape Amazon product reviews via ghostcrawl /v1/extract schema rules.

Docs-only example (HYBRID-EXAMPLE-DOCS per Phase 140.2 D-06). Uses /v1/extract
with a JSON schema — zero parser maintenance for ghostcrawl since Amazon DOM
drift is handled by updating the schema below.

Run with:

    GHOSTCRAWL_API_KEY=gck_live_... python examples/amazon-review-scraper.py
"""
from __future__ import annotations
import asyncio
import json
import os
import sys
from ghostcrawl import GhostCrawlClient, InvalidRequestError


REVIEW_SCHEMA = {
    "reviews": {
        "selector": "div[data-hook=review]",
        "type": "list",
        "output": {
            "title": {"selector": "a[data-hook=review-title] span", "output": "text"},
            "rating": {"selector": "i[data-hook=review-star-rating] span", "output": "text"},
            "reviewer": {"selector": "span.a-profile-name", "output": "text"},
            "date": {"selector": "span[data-hook=review-date]", "output": "text"},
            "verified_purchase": {"selector": "span[data-hook=avp-badge]", "output": "exists"},
            "review_text": {"selector": "span[data-hook=review-body] span", "output": "text"},
        },
    }
}


async def main(url: str | None = None) -> int:
    api_key = os.environ.get("GHOSTCRAWL_API_KEY", "")
    if not api_key:
        print("Error: GHOSTCRAWL_API_KEY environment variable required", file=sys.stderr)
        return 1
    target = url or "https://www.amazon.com/dp/B08N5WRWNW"
    async with GhostCrawlClient(token=api_key) as gc:
        try:
            result = await gc.extract(url=target, schema=REVIEW_SCHEMA)
        except InvalidRequestError as exc:
            print(f"Extraction did not satisfy the schema (HTTP {exc.status_code}).")
            if exc.body:
                print(exc.body)
            return 0
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else None)))
