# Examples

Runnable examples for every GhostCrawl surface. Each example reads your API key
from the `GHOSTCRAWL_API_KEY` environment variable:

```bash
export GHOSTCRAWL_API_KEY="YOUR_API_KEY"
```

Get a key from your dashboard at [ghostcrawl.io](https://ghostcrawl.io). All
examples target the managed cloud at `https://api.ghostcrawl.io`. To run them
against a self-hosted instance, point the SDK at `http://localhost:8000` (see the
[self-host guide](../docs/usage-selfhost.md)).

| Directory | Surface |
|-----------|---------|
| [`curl/`](curl/) | Plain HTTP — scrape, crawl, extract, search. |
| [`python/`](python/) | `ghostcrawl` Python SDK — sync + async. |
| [`node/`](node/) | `@ghostcrawl/sdk` TypeScript SDK. |
| [`cli/`](cli/) | `@ghostcrawl/cli` command-line examples. |
| [`langchain/`](langchain/) | `ghostcrawl-langchain` tools for LLM agents. |
| [`mcp/`](mcp/) | MCP client configuration for agents. |

## Engines

Every example accepts an `engine` of `chrome`, `firefox`, or `webkit`. Use
`auto` to let the orchestrator pick the best engine for the request.
