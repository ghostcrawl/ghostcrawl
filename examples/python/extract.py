"""Extract structured JSON from a page against a schema.

    pip install ghostcrawl
    export GHOSTCRAWL_API_KEY=YOUR_API_KEY
    python extract.py
"""

import os

from ghostcrawl import GhostcrawlClient

client = GhostcrawlClient(api_key=os.environ["GHOSTCRAWL_API_KEY"])

result = client.page.extract(
    url="https://example.com",
    engine="auto",
    schema={
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "summary": {"type": "string"},
        },
    },
)
print(result)
