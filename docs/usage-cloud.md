# Cloud usage

The managed cloud is the fastest way to get authentic browser results at scale.
You bring an API key; ghostcrawl runs the browsers, picks the engine, and routes
every request through a managed pool of exits automatically.

---

## Authenticate

Every request sends your API key as a bearer token. Get a key by signing up,
verifying your email, logging in, and minting one from your dashboard.

```python
from ghostcrawl import GhostcrawlClient

client = GhostcrawlClient(api_key="YOUR_API_KEY")
```

```typescript
import { GhostcrawlClient } from '@ghostcrawl/sdk';

const client = new GhostcrawlClient({ apiKey: process.env.GHOSTCRAWL_API_KEY! });
```

The default base URL is the managed API. You only override it when pointing the
SDK at a self-hosted instance.

---

## Scrape a page

```python
result = client.page.scrape(url="https://example.com", engine="chrome")
print(result)
```

```typescript
const result = await client.page.scrape({ url: 'https://example.com', engine: 'chrome' });
console.log(result);
```

---

## Pick an engine

The public engine set is `chrome`, `firefox`, and `webkit`. Use `auto` to let
the orchestrator choose the best engine for the request.

```python
result = client.page.scrape(url="https://example.com", engine="auto")
```

---

## MCP (agents)

Point any agent at `mcp.ghostcrawl.io` with your API key and start crawling.

```python
from ghostcrawl.mcp import GhostcrawlMCPClient

mcp = GhostcrawlMCPClient(mcp_url="https://mcp.ghostcrawl.io", api_key="YOUR_API_KEY")
await mcp.connect()
await mcp.navigate(url="https://example.com")
await mcp.act(goal="Find the contact email")
data = await mcp.extract(schema={"type": "object", "properties": {"title": {"type": "string"}}})
await mcp.close()
```

The MCP surface exposes navigate, act, extract, screenshot, and more — the same
managed browsers behind the REST API.

---

## Managed routing

There is nothing to configure. Every request rotates through a managed pool of
exits selected automatically. You do not supply proxies, manage rotation, or
pick exit IPs — that is included in your plan.

---

## Live view

Paid plans can watch a running cloud session live from the dashboard. Open the
Live view, select an active session, and the browser streams to your screen.

---

## Limits and tiers

Concurrency and request quotas depend on your plan. `GET /v1/me` reports
your current tier, email, and team. Self-host users can also run
`ghostcrawl status` to see container state, API health, and quota usage.
