# @ghostcrawl/sdk

The official TypeScript/JavaScript client for the [GhostCrawl](https://ghostcrawl.io) API. Collect web data at scale — scrape, crawl, search, extract structured data, manage browser sessions, and automate the full data-collection pipeline.

- **ESM + CJS dual build** with full `.d.ts` type declarations.
- **Zero runtime HTTP dependency** — built on `globalThis.fetch` (Node.js 18+).
- **TypeScript-first**, works from plain JavaScript too.

## Install

```bash
npm install @ghostcrawl/sdk
```

Requires Node.js >= 18.

## Quickstart

Copy-paste, drop in your key, run:

```typescript
import { createGhostCrawlClient } from "@ghostcrawl/sdk";

const client = createGhostCrawlClient({ token: "gck_live_YOUR_KEY" });
const result = await client.scrape({ url: "https://example.com" });
console.log(result.content); // typed field — result["content"] also works
```

`result` is a typed `ScrapeResult` (`status`, `content`, `markdown`, `html`,
`status_code`, `bytes`, `url`, `format`, `warnings`) that is ALSO index-accessible,
so `result.content` and `result["content"]` both work — existing code that treats
the response as a plain object keeps working unchanged.

### Search — block until results are ready

`search` runs on two paths. On a warm rotation the backend answers immediately; on
a cold rotation it queues a job. Pass `wait: true` and the SDK owns a **bounded
client-side poll** (honoring `Retry-After` and the server deadline) so you write
zero poll code:

```typescript
import { createGhostCrawlClient } from "@ghostcrawl/sdk";

const client = createGhostCrawlClient({ token: "gck_live_YOUR_KEY" });
const results = await client.search({ query: "latest AI research", wait: true });
console.log(results.status, results.results); // SearchResult: status, results, query
```

> `search` wait is a client-side bounded poll (the search-job contract has no
> server `?wait=true`); `crawl` wait is a server-side long-poll. Same `wait` DX,
> different mechanism under the hood — see below.

### Concurrency — the idiomatic async shape

This client is **async-native**: every method returns a `Promise`, and the
idiomatic way to run work in parallel is `await` + `Promise.all` — no thread pool,
no bolt-on "sync" wrapper. Batch a set of scrapes concurrently:

```typescript
import { createGhostCrawlClient } from "@ghostcrawl/sdk";

const client = createGhostCrawlClient({ token: "gck_live_YOUR_KEY" });
const urls = ["https://example.com", "https://example.org", "https://example.net"];
const pages = await Promise.all(urls.map((url) => client.scrape({ url })));
console.log(pages.map((p) => p.status_code));
```

## Crawl runs — wait for completion

A crawl run is asynchronous. Rather than hand-writing a `while` + `sleep` poll loop,
use the event-driven wait: it long-polls a server endpoint that **blocks** until the
run reaches a terminal state (`completed` | `failed` | `cancelled`), so you get the
result the moment it's ready — no client-side timers, no wasted requests.

```typescript
import { createGhostCrawlClient, GhostCrawlTimeoutError } from "@ghostcrawl/sdk";

const client = createGhostCrawlClient({ token: "gck_live_YOUR_KEY" });

// Option A — start, then wait on the run id:
const { run_id } = await client.crawlRuns.start({ url: "https://example.com", maxDepth: 2 });
try {
  const run = await client.crawlRuns.wait(run_id, { timeout: 600 }); // seconds
  console.log(run.status, run.pages_crawled);
} catch (err) {
  if (err instanceof GhostCrawlTimeoutError) {
    // Still running past our deadline — call wait(run_id) again to resume.
  } else {
    throw err;
  }
}

// Option B — start and block in a single call:
const run = await client.crawlRuns.start({ url: "https://example.com", wait: true, timeout: 600 });
console.log(run.status);
```

For long crawls, prefer a **webhook** instead of holding a connection open — register
`client.webhooks.create({ url, event_types: ["crawl.completed"] })` and the server calls
you back when the run finishes.

## Authentication

```typescript
import { createGhostCrawlClient } from "@ghostcrawl/sdk";

// Option 1: pass token directly
const client = createGhostCrawlClient({ token: "gck_live_YOUR_KEY" });

// Option 2: set environment variable (recommended for production)
process.env.GHOSTCRAWL_API_KEY = "gck_live_YOUR_KEY";
const client2 = createGhostCrawlClient();
```

Every request sends `Authorization: Bearer <token>`. This is the only auth scheme the API accepts.

## Extract structured data

```typescript
import { createGhostCrawlClient } from "@ghostcrawl/sdk";

const client = createGhostCrawlClient({ token: "gck_live_YOUR_KEY" });

const data = await client.extract({
  url: "https://example.com/product",
  schema: {
    type: "object",
    properties: {
      name: { type: "string" },
      price: { type: "number" },
      description: { type: "string" },
    },
  },
});
console.log(data.name, data.price);
```

## Browser utilities — content, screenshot, PDF

```typescript
import { writeFileSync } from "node:fs";
import { createGhostCrawlClient } from "@ghostcrawl/sdk";

const client = createGhostCrawlClient({ token: "gck_live_YOUR_KEY" });

// Rendered content as a JSON envelope: { url, status, format, status_code, content, bytes }
const page = await client.content({ url: "https://example.com" });
console.log(page.status_code, page.bytes, "bytes");

// Screenshot — returns a Uint8Array of PNG bytes
const png = await client.screenshot({ url: "https://example.com", full_page: true });
writeFileSync("page.png", png);

// PDF — returns a Uint8Array of application/pdf bytes (Chrome-only; a Firefox/WebKit
// identity throws an Error carrying statusCode 400 pdf_engine_unsupported)
const pdf = await client.pdf({ url: "https://example.com", paperFormat: "a4" });
writeFileSync("page.pdf", pdf);
```

## Agent (BYO model, account-gated)

The agent lane runs a natural-language browser task. It is **bring-your-own-model** (pass your
own `provider_config` in the request body) and **account-gated**: the API replies `404 not_found`
unless the capability is enabled for your account. Handle that 404 explicitly — it is the
expected "not enabled" answer, not a transport failure.

```typescript
import { createGhostCrawlClient } from "@ghostcrawl/sdk";

const client = createGhostCrawlClient({ token: "gck_live_YOUR_KEY" });

try {
  const result = await client.agent({
    task: {
      instruction: "click the 'Books to Scrape' link",
      start_url: "https://books.toscrape.com",
    },
    // provider_config is BYO — reference your provider key by env-var name, never a literal.
    provider_config: {
      provider: "openai",
      api_key: "OPENAI_API_KEY",
      model: "gpt-4o",
    },
  });
  console.log(result);
} catch (err) {
  const status = (err as { statusCode?: number }).statusCode;
  if (status === 404) {
    console.log("agent lane not enabled for this account (BYO/gated)");
  } else {
    throw err;
  }
}
```

## Browser sessions

```typescript
import { createGhostCrawlClient } from "@ghostcrawl/sdk";

const client = createGhostCrawlClient({ token: "gck_live_YOUR_KEY" });

const session = await client.sessions.create({ profileName: "my-profile" });
const sessionId = session.sessionId as string;

await client.sessions.extend(sessionId, 600);
await client.sessions.release(sessionId);
```

## Error handling

```typescript
import {
  createGhostCrawlClient,
  AuthenticationError,
  RateLimitError,
  APIError,
} from "@ghostcrawl/sdk";

const client = createGhostCrawlClient({ token: "gck_live_YOUR_KEY" });

try {
  const result = await client.scrape({ url: "https://example.com" });
} catch (err) {
  if (err instanceof AuthenticationError) {
    console.error("Invalid API key — check your token");
  } else if (err instanceof RateLimitError) {
    console.error("Rate limit reached — retry after a short delay");
  } else if (err instanceof APIError) {
    console.error(`Server error: ${err.statusCode}`);
  }
}
```

## MCP Wrapper

The MCP wrapper drives the same API as `createGhostCrawlClient`, over the Model
Context Protocol. It is **optional** — the MCP SDK is not installed by default, so
install the peer dependency first:

```bash
npm install @modelcontextprotocol/sdk
```

```typescript
// Same API as createGhostCrawlClient, exposed over MCP.
import { GhostCrawlMCPClient } from "@ghostcrawl/sdk";

const mcp = new GhostCrawlMCPClient({
  mcpUrl: "https://api.ghostcrawl.io/mcp",
  apiKey: "gck_live_YOUR_KEY",
});

await mcp.connect();
const nav = await mcp.navigate({ url: "https://example.com" });
await mcp.close();
```

## All resources

| Resource | Client attribute | Key operations |
|----------|-----------------|----------------|
| Scraping | `client.scrape({ url })` | Render and return page content |
| Web search | `client.search({ query })` | Search Google, Bing, DuckDuckGo |
| Data extraction | `client.extract({ url, schema })` | Structured JSON from any page |
| Deep crawl | `client.crawl({ url })` | Crawl a site depth-first |
| URL map | `client.map({ url })` | Discover all reachable URLs |
| Content | `client.content({ url })` | Rendered content JSON envelope |
| Screenshot | `client.screenshot({ url })` | Capture a URL to PNG bytes |
| PDF | `client.pdf({ url })` | Render a URL to PDF bytes (Chrome-only) |
| Agent (BYO) | `client.agent({ task })` | NL browser task — account-gated, BYO model |
| Crawl runs | `client.crawlRuns` | start, list, get, cancel |
| Sessions | `client.sessions` | create, extend, release |
| Profiles | `client.profiles` | list, get, create, update, delete |
| Webhooks | `client.webhooks` | list, get, create, delete, rotateSecret |
| Schedules | `client.schedules` | list, get, create, delete |
| Datasets | `client.datasets` | list, get, create, delete, rows, append |
| Recordings | `client.recordings` | list, get, delete |
| Key-Value Store | `client.kv` | get, set, delete |

## CLI

```bash
npm install -g @ghostcrawl/cli

# Set your API key
export GHOSTCRAWL_API_KEY=gck_live_YOUR_KEY

# Scrape a URL
ghostcrawl scrape https://example.com

# Start a crawl
ghostcrawl crawl https://example.com --max-depth 2
```

## Self-hosted

```typescript
const client = createGhostCrawlClient({
  token: "gck_live_YOUR_KEY",
  baseUrl: "http://localhost:8080",
});
```

## Account & session persona

`me()` returns your account profile — including `max_concurrency`, the number of
sessions your plan may run at once. `usage()` reports the current billing window.
`sessionPersona(sessionId)` returns a running session's customer-safe persona: a
display-only whitelist of `device_class`, `os_class`, `browser_class`, and `locale`
(never any raw or internal detail).

```typescript
const me = await client.me();
console.log(me.max_concurrency);                 // concurrent-session ceiling for your plan

const persona = await client.sessionPersona(sessionId);
console.log(persona.device_class, persona.os_class, persona.browser_class, persona.locale);
```

## License

Proprietary — GhostCrawl Software License. See [LICENSE](LICENSE).
