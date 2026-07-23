# ghostcrawl — Python SDK

The official Python client for the [GhostCrawl](https://ghostcrawl.io) API. Collect web data at scale — scrape, crawl, search, extract structured data, manage browser sessions, and automate the full data-collection pipeline.

## Install

```bash
pip install ghostcrawl
```

Requires Python 3.10+. Runtime dependencies: `httpx>=0.28.1`.

> The client is **async** — every request method is a coroutine. Call them with
> `await` inside an `async` function and drive it with `asyncio.run(...)`.

## Quickstart

```python
import asyncio
from ghostcrawl import GhostCrawlClient

async def main():
    # Reads GHOSTCRAWL_API_KEY from environment, or pass token= explicitly
    async with GhostCrawlClient(token="gck_live_YOUR_KEY") as client:
        # Scrape a URL
        result = await client.scrape(url="https://example.com", format="markdown")
        print(result["content"])

        # Start a crawl and wait for it to finish — EVENT-DRIVEN: the server
        # blocks until the run is terminal (completed/failed/cancelled) or the
        # timeout elapses, then returns the run. No client-side poll loop.
        run = await client.crawl_runs.start(
            url="https://example.com", max_depth=2, max_pages=50,
            wait=True, wait_timeout=300,
        )
        print(run["run_id"], run["status"])

        # Already have a run_id? Long-poll it to completion the same way:
        #   run = await client.crawl_runs.wait(run_id, timeout=300)
        # Or skip waiting entirely and get notified via a webhook (see Webhooks)
        # by omitting wait= and registering a delivery URL with client.webhooks.

        # Web search
        results = await client.search(query="latest AI research", engine="google", limit=10)
        for r in results["results"]:
            print(r["title"], r["url"])

asyncio.run(main())
```

## Authentication

```python
import os
from ghostcrawl import GhostCrawlClient

# Option 1: pass token directly
client = GhostCrawlClient(token="gck_live_YOUR_KEY")

# Option 2: set environment variable (recommended for production)
os.environ["GHOSTCRAWL_API_KEY"] = "gck_live_YOUR_KEY"
client = GhostCrawlClient()
```

Every request sends `Authorization: Bearer <token>`. This is the only auth scheme the API accepts.

## Extract structured data

```python
import asyncio
from ghostcrawl import GhostCrawlClient

async def main():
    async with GhostCrawlClient(token="gck_live_YOUR_KEY") as client:
        # Define a schema and extract matching data
        data = await client.extract(
            url="https://example.com/product",
            schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "price": {"type": "number"},
                    "description": {"type": "string"},
                },
            },
        )
        print(data["name"], data["price"])

asyncio.run(main())
```

## Browser utilities — content, screenshot, PDF

```python
import asyncio
from ghostcrawl import GhostCrawlClient

async def main():
    async with GhostCrawlClient(token="gck_live_YOUR_KEY") as client:
        # Rendered content as a JSON envelope: {url, status, format, status_code, content, bytes}
        page = await client.content(url="https://example.com", engine="auto")
        print(page["status_code"], page["bytes"], "bytes")
        print(page["content"][:200])

        # Screenshot — returns raw PNG bytes you can write straight to disk
        png = await client.screenshot(url="https://example.com", full_page=True)
        with open("page.png", "wb") as f:
            f.write(png)

        # PDF — returns raw application/pdf bytes (Chrome-only; a Firefox/WebKit
        # identity raises InvalidRequestError with 400 pdf_engine_unsupported)
        pdf = await client.pdf(url="https://example.com", paper_format="a4")
        with open("page.pdf", "wb") as f:
            f.write(pdf)

asyncio.run(main())
```

## Agent (BYO model, account-gated)

The agent lane runs a natural-language browser task. It is **bring-your-own-model** — you
supply your own LLM provider via `provider_config` — and **account-gated**: the API replies
`404 not_found` unless the capability is enabled for your account. `agent()` does **not** raise
on that 404; it returns the `problem+json` body so you branch on `"detail" in result`.

```python
import asyncio
from ghostcrawl import GhostCrawlClient

async def main():
    # provider_config is BYO — reference your provider key by ENV-VAR NAME only,
    # never a literal key in committed code.
    client = GhostCrawlClient(
        token="gck_live_YOUR_KEY",
        provider_config={
            "provider": "openai",
            "api_key": "OPENAI_API_KEY",   # resolved from env by the caller
            "model": "gpt-4o",
        },
    )
    result = await client.agent(
        url="https://books.toscrape.com",
        instruction="click the 'Books to Scrape' link",
    )
    if "detail" in result:
        print(f"agent lane not enabled for this account: {result['detail']}")
    else:
        print(result)

asyncio.run(main())
```

> The interactive MCP lane (`navigate` / `act` / `observe`) is available in the Python and
> Node SDKs only — see `ghostcrawl.mcp.wrapper.GhostCrawlMCPClient`. It is also BYO.

## Browser sessions

```python
import asyncio
from ghostcrawl import GhostCrawlClient

async def main():
    async with GhostCrawlClient(token="gck_live_YOUR_KEY") as client:
        # Create a session
        session = await client.sessions.create(profile_name="my-profile")
        session_id = session["session_id"]

        # Extend and release
        await client.sessions.extend(session_id, duration_seconds=600)
        await client.sessions.release(session_id)

asyncio.run(main())
```

## Error handling

```python
import asyncio
from ghostcrawl import GhostCrawlClient, AuthenticationError, RateLimitError, APIError

async def main():
    async with GhostCrawlClient(token="gck_live_YOUR_KEY") as client:
        try:
            result = await client.scrape(url="https://example.com")
        except AuthenticationError:
            print("Invalid API key — check your token")
        except RateLimitError:
            print("Rate limit reached — retry after a short delay")
        except APIError as e:
            print(f"Server error: {e.status_code}")

asyncio.run(main())
```

## Context manager

```python
import asyncio
from ghostcrawl import GhostCrawlClient

async def main():
    async with GhostCrawlClient(token="gck_live_YOUR_KEY") as client:
        result = await client.scrape(url="https://example.com")
        print(result)
    # HTTP connection is closed automatically

asyncio.run(main())
```

## All resources

Every operation below is a coroutine — prefix each call with `await` inside an `async` function.

| Resource | Client attribute | Key operations |
|----------|-----------------|----------------|
| Scraping | `client.scrape(url=…)` | Render and return page content |
| Web search | `client.search(query=…)` | Search Google, Bing, DuckDuckGo |
| Data extraction | `client.extract(url=…, schema=…)` | Structured JSON from any page |
| Deep crawl | `client.crawl(url=…)` | Crawl a site depth-first |
| URL map | `client.map(url=…)` | Discover all reachable URLs |
| Content | `client.content(url=…)` | Rendered content JSON envelope |
| Screenshot | `client.screenshot(url=…)` | Capture a URL to PNG bytes |
| PDF | `client.pdf(url=…)` | Render a URL to PDF bytes (Chrome-only) |
| Agent (BYO) | `client.agent(url=…, instruction=…)` | NL browser task — account-gated, BYO model |
| Crawl runs | `client.crawl_runs` | start (`wait=True`), wait, list, get, cancel |
| Sessions | `client.sessions` | create, extend, release |
| Profiles | `client.profiles` | list, get, create, update, delete |
| Webhooks | `client.webhooks` | list, get, create, delete, rotate-secret |
| Schedules | `client.schedules` | list, get, create, delete |
| Datasets | `client.datasets` | list, get, create, delete, append rows |
| Recordings | `client.recordings` | list, get, delete |
| Key-Value Store | `client.kv` | get, set, delete |

## LangChain integration

```bash
pip install ghostcrawl-langchain
```

```python
from ghostcrawl_langchain import GhostCrawlScrape, GhostCrawlSearch

scrape_tool = GhostCrawlScrape()
search_tool = GhostCrawlSearch()
```

## Self-hosted

```python
client = GhostCrawlClient(
    token="gck_live_YOUR_KEY",
    base_url="http://localhost:8080",  # your self-hosted instance
)
```

## License

Proprietary — GhostCrawl Software License. See [LICENSE](LICENSE).
