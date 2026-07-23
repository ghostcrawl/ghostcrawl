"""Quickstart: extract structured data from a page.

Run with:
    GHOSTCRAWL_API_KEY=gck_live_YOUR_KEY python examples/quickstart_extract.py
"""

from __future__ import annotations

import asyncio
import os
import sys

from ghostcrawl import GhostCrawlClient, InvalidRequestError


PRODUCT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "price": {"type": "number"},
        "in_stock": {"type": "boolean"},
    },
    "required": ["title"],
}


async def main() -> None:
    token = os.environ.get("GHOSTCRAWL_API_KEY")
    if not token:
        print("Set GHOSTCRAWL_API_KEY in your environment.", file=sys.stderr)
        sys.exit(1)

    target = os.environ.get("TARGET_URL", "https://example.com")

    async with GhostCrawlClient(token=token) as client:
        try:
            data = await client.extract(url=target, schema=PRODUCT_SCHEMA)
        except InvalidRequestError as exc:
            # The page may not contain every required field — the server
            # validates the extracted result against the schema and returns
            # a 422 when a required property cannot be found.
            print(f"Extraction did not satisfy the schema (HTTP {exc.status_code}).")
            if exc.body:
                print(exc.body)
            return

        print("Extracted data:")
        print(f"  title: {data.get('title')}")
        print(f"  price: {data.get('price')}")
        print(f"  in_stock: {data.get('in_stock')}")


if __name__ == "__main__":
    asyncio.run(main())
