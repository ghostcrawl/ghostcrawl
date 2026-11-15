"""Scrape a single page with the GhostCrawl Python SDK.

    pip install ghostcrawl
    export GHOSTCRAWL_API_KEY=YOUR_API_KEY
    python scrape.py
"""

import os

from ghostcrawl import GhostCrawl

client = GhostCrawl(api_key=os.environ["GHOSTCRAWL_API_KEY"])

result = client.scrape(url="https://example.com", engine="chrome")
print(result)
