"""Invoke a GhostCrawl LangChain tool directly.

    pip install ghostcrawl-langchain
    export GHOSTCRAWL_API_KEY=YOUR_API_KEY
    python tool.py

The tools read your key from the GHOSTCRAWL_API_KEY environment variable and
default to https://api.ghostcrawl.io.
"""

from ghostcrawl_langchain import GhostcrawlScrapeTool

scrape = GhostcrawlScrapeTool()

# Returns the page content (Markdown by default) plus metadata.
print(scrape.invoke({"url": "https://example.com"}))
