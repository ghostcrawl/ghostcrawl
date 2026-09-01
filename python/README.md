# ghostcrawl — Python SDK

The official Python client for the [GhostCrawl](https://ghostcrawl.io) API. Collect web data at scale — scrape, crawl, search, extract structured data, manage browser sessions, and automate the full data-collection pipeline.

## Install

```bash
pip install ghostcrawl
```

Requires Python 3.10+. Runtime dependencies: `httpx>=0.28.1`.

> The default client is **synchronous** — no `await`, no `asyncio.run`. Every
> method returns a typed result directly. Prefer async? Import `AsyncGhostCrawl`
> for the awaitable twin (see [Async](#async-twin) below).

## Quickstart

```python
from ghostcrawl import GhostCrawl

# Reads GHOSTCRAWL_API_KEY from environment, or pass token= explicitly
client = GhostCrawl(token="gck_live_YOUR_KEY")

# Scrape a URL — returns a typed ScrapeResult
result = client.scrape(url="https://example.com", format="markdown")
print(result.markdown)

# Start a crawl and wait for it to finish in one call. The server blocks until
# the run is terminal (completed/failed/cancelled) or the timeout elapses —
# no client-side poll loop.
run = client.crawl(
    url="https://example.com", max_depth=2, max_pages=50,
    wait=True, wait_timeout=300,
)
print(run["run_id"], run["status"])

# Web search — pass wait=True and the SDK blocks until results are ready,
# then hands you a typed SearchResult (no hand-rolled poll).
results = client.search(query="latest AI research", wait=True)
for r in results.results:
    print(r["title"], r["url"])
```

`result` is a typed `ScrapeResult` — read `result.markdown`, `result.html`,
`result.status_code`, or `result.url`. Every field is also dict-accessible
(`result["markdown"]`) if you prefer.

## Authentication

```python
import os
from ghostcrawl import GhostCrawl

# Option 1: pass token directly
client = GhostCrawl(token="gck_live_YOUR_KEY")

# Option 2: set environment variable (recommended for production)
os.environ["GHOSTCRAWL_API_KEY"] = "gck_live_YOUR_KEY"
client = GhostCrawl()
```

Every request sends `Authorization: Bearer <token>`. This is the only auth scheme the API accepts.

## Extract structured data

```python
from ghostcrawl import GhostCrawl

client = GhostCrawl(token="gck_live_YOUR_KEY")

# Define a schema and extract matching data
data = client.extract(
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
```

## Browser utilities — content, screenshot, PDF

```python
from ghostcrawl import GhostCrawl

client = GhostCrawl(token="gck_live_YOUR_KEY")

# Rendered content as a JSON envelope: {url, status, format, status_code, content, bytes}
page = client.content(url="https://example.com", engine="auto")
print(page["status_code"], page["bytes"], "bytes")
print(page["content"][:200])

# Screenshot — returns raw PNG bytes you can write straight to disk
png = client.screenshot(url="https://example.com", full_page=True)
with open("page.png", "wb") as f:
    f.write(png)

# PDF — returns raw application/pdf bytes (Chrome-only; a Firefox/WebKit
# identity raises InvalidRequestError with 400 pdf_engine_unsupported)
pdf = client.pdf(url="https://example.com", paper_format="a4")
with open("page.pdf", "wb") as f:
    f.write(pdf)
```

## Agent (BYO model, account-gated)

The agent lane runs a natural-language browser task. It is **bring-your-own-model** — you
supply your own LLM provider via `provider_config` — and **account-gated**: the API replies
`404 not_found` unless the capability is enabled for your account. `agent()` does **not** raise
on that 404; it returns the `problem+json` body so you branch on `"detail" in result`.

```python
from ghostcrawl import GhostCrawl

# provider_config is BYO — reference your provider key by ENV-VAR NAME only,
# never a literal key in committed code.
client = GhostCrawl(
    token="gck_live_YOUR_KEY",
    provider_config={
        "provider": "openai",
        "api_key": "OPENAI_API_KEY",   # resolved from env by the caller
        "model": "gpt-4o",
    },
)
result = client.agent(
    url="https://books.toscrape.com",
    instruction="click the 'Books to Scrape' link",
)
if "detail" in result:
    print(f"agent lane not enabled for this account: {result['detail']}")
else:
    print(result)
```

> The interactive MCP lane (`navigate` / `act` / `observe`) is available in the Python and
> Node SDKs only — see `ghostcrawl.mcp.wrapper.GhostCrawlMCPClient`. It is also BYO.
> The MCP client is **optional**: it is not pulled into the default install, so add the
> extra when you need it — `pip install ghostcrawl[mcp]`.

## Browser sessions

```python
from ghostcrawl import GhostCrawl

client = GhostCrawl(token="gck_live_YOUR_KEY")

# Create a session
session = client.sessions.create(profile_name="my-profile")
session_id = session["session_id"]

# Extend and release
client.sessions.extend(session_id, duration_seconds=600)
client.sessions.release(session_id)
```

## Error handling

```python
from ghostcrawl import GhostCrawl, AuthenticationError, RateLimitError, APIError

client = GhostCrawl(token="gck_live_YOUR_KEY")

try:
    result = client.scrape(url="https://example.com")
except AuthenticationError:
    print("Invalid API key — check your token")
except RateLimitError:
    print("Rate limit reached — retry after a short delay")
except APIError as e:
    print(f"Server error: {e.status_code}")
```

## Closing the client

The client cleans itself up when it goes out of scope, but you can close it
explicitly (or use it as a context manager) to release the HTTP connection
deterministically:

```python
from ghostcrawl import GhostCrawl

with GhostCrawl(token="gck_live_YOUR_KEY") as client:
    result = client.scrape(url="https://example.com")
    print(result.markdown)
# HTTP connection is closed automatically on block exit
```

<a id="async-twin"></a>

## Async twin

Prefer `async`/`await`? Import `AsyncGhostCrawl` — the genuine awaitable twin.
Every method is a coroutine and the client supports `async with`:

```python
import asyncio
from ghostcrawl import AsyncGhostCrawl

async def main():
    async with AsyncGhostCrawl(token="gck_live_YOUR_KEY") as client:
        result = await client.scrape(url="https://example.com", format="markdown")
        print(result.markdown)

asyncio.run(main())
```

Both clients are real: `GhostCrawl` is the synchronous default, `AsyncGhostCrawl`
is the awaitable twin. Pick whichever matches your program — they share the same method
names, parameters, and typed results.

## All resources

| Resource | Client attribute | Key operations |
|----------|-----------------|----------------|
| Scraping | `client.scrape(url=…)` | Render and return page content |
| Web search | `client.search(query=…, wait=True)` | Search Google, Bing, DuckDuckGo |
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
from ghostcrawl import GhostCrawl

client = GhostCrawl(
    token="gck_live_YOUR_KEY",
    base_url="http://localhost:8080",  # your self-hosted instance
)
```

## Account & session persona

`me()` returns your account profile — including `max_concurrency`, the number of
sessions your plan may run at once. `usage()` reports the current billing window.
`session_persona(session_id)` returns a running session's customer-safe persona: a
display-only whitelist of `device_class`, `os_class`, `browser_class`, and `locale`
(never any raw or internal detail).

```python
me = client.me()
print(me["max_concurrency"])                 # concurrent-session ceiling for your plan

persona = client.session_persona(session_id)
print(persona["device_class"], persona["os_class"],
      persona["browser_class"], persona["locale"])
```

## License

Proprietary — GhostCrawl Software License. See [LICENSE](LICENSE).
