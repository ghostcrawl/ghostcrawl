"""Example: scrape Amazon product reviews via ghostcrawl /v1/extract schema rules.

Docs-only example. Uses /v1/extract
with a JSON schema — zero parser maintenance for ghostcrawl since Amazon DOM
drift is handled by updating the schema below.

Run with:

    GHOSTCRAWL_API_KEY=gck_live_YOUR_KEY python examples/amazon-review-scraper.py
"""
from __future__ import annotations
import json
import os
import sys
from ghostcrawl import GhostCrawl, InvalidRequestError


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


def main(url: str | None = None) -> int:
    token = os.environ.get("GHOSTCRAWL_API_KEY", "")
    if not token:
        print("Error: GHOSTCRAWL_API_KEY environment variable required", file=sys.stderr)
        return 1
    target = url or "https://www.amazon.com/dp/B08N5WRWNW"
    gc = GhostCrawl(token=token)
    try:
        result = gc.extract(url=target, schema=REVIEW_SCHEMA)
    except InvalidRequestError as exc:
        print(f"Extraction did not satisfy the schema (HTTP {exc.status_code}).")
        if exc.body:
            print(exc.body)
        return 0
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
