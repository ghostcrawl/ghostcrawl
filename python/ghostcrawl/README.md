# ghostcrawl — Python SDK

[![pypi](https://img.shields.io/pypi/v/ghostcrawl)](https://pypi.python.org/pypi/ghostcrawl)

The official Python client for the [GhostCrawl](https://ghostcrawl.io) API —
scrape, crawl, search, extract structured data, manage browser sessions, and
automate the full data-collection pipeline.

The full, canonical README lives at the package root: [`../README.md`](../README.md).

## Install

```sh
pip install ghostcrawl
```

Requires Python 3.10+.

## Quickstart

The canonical client is `GhostCrawlClient`, an async client. `GhostCrawl` and
`Client` are aliases of it for back-compat.

```python
import asyncio
from ghostcrawl import GhostCrawlClient

async def main():
    async with GhostCrawlClient(token="gck_live_YOUR_KEY") as client:
        result = await client.scrape(url="https://example.com", format="markdown")
        print(result["markdown"])

asyncio.run(main())
```

Set `GHOSTCRAWL_API_KEY` in the environment instead of passing `token=`, and
override the base URL with `base_url=` or `GHOSTCRAWL_BASE_URL`.

## Errors

Failures raise typed exceptions from the package root:

```python
from ghostcrawl import (
    GhostCrawlError, AuthenticationError, RateLimitError,
    PaymentRequiredError, InvalidRequestError, APIError, ScrapeError,
)

try:
    await client.scrape(url="https://example.com")
except RateLimitError as e:
    print(e.retry_after, e.retryable)
except ScrapeError as e:        # target failure on an HTTP-200 result
    print(e.code, e.target_status)
```

## CLI

```sh
ghostcrawl init
ghostcrawl scrape https://example.com
ghostcrawl usage
```

## Contributing

See [`CONTRIBUTING.md`](./CONTRIBUTING.md).
