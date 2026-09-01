# ghostcrawl-langchain

LangChain tool integration for the [GhostCrawl](https://pypi.org/project/ghostcrawl/)
web data API.

Exposes the GhostCrawl scrape / content / map / search / extract / crawl /
usage / Google-vertical surfaces as LangChain `BaseTool` subclasses with shared
Pydantic params validation.

## Install

```bash
pip install ghostcrawl-langchain
```

**Publish = yes** (public PyPI `ghostcrawl-langchain`).

## Quickstart

Each tool is a standard LangChain `BaseTool`. Call it synchronously with
`.invoke(...)` — no `await`, no `asyncio.run`. Set `GHOSTCRAWL_API_KEY` (use your
real `gck_live_YOUR_KEY`) in the environment first:

```python
from ghostcrawl_langchain import GhostCrawlScrapeTool

# Reads GHOSTCRAWL_API_KEY from the environment (gck_live_YOUR_KEY).
tool = GhostCrawlScrapeTool()
result = tool.invoke({"url": "https://example.com", "output_format": "markdown"})
print(result)
```

Bind the tools to an agent/LLM exactly as you would any LangChain tool:

```python
from ghostcrawl_langchain import GhostCrawlScrapeTool, GhostCrawlSearchTool

tools = [GhostCrawlScrapeTool(), GhostCrawlSearchTool()]
# llm.bind_tools(tools)  # your model of choice
```

Inside an `async def` (an async agent), use the awaitable twin `await tool.ainvoke(...)`.

## Framework-lane surface (idiomatic retrieval subset vs N/A)

`ghostcrawl-langchain` is a **framework lane**, not a full SDK: it wraps the
idiomatic *retrieval* subset of the GhostCrawl API as LangChain tools an agent
can call. Everything else is an explicit **N/A** — not a gap, just not idiomatic
as an LC retrieval `Tool`/loader (zero blank cells, zero padded-green).

| Capability | Status | Tool / rationale |
|------------|--------|------------------|
| scrape | ✅ GREEN | `GhostCrawlScrapeTool` → `POST /v1/scrape` |
| content | ✅ GREEN | `GhostCrawlContentTool` → `POST /v1/content` |
| extract | ✅ GREEN | `GhostCrawlExtractTool` → `POST /v1/extract` |
| map | ✅ GREEN | `GhostCrawlMapTool` → `POST /v1/map` |
| crawl | ✅ GREEN | `GhostCrawlCrawlTool` → `POST /v1/crawl` (seeds `seed_urls`) |
| search | N/A (BYO) | `GhostCrawlSearchTool` reaches `/v1/search`, which needs a user-supplied search-backend key (`X-Provider-Authorization`); a call without that search-backend key returns `401 search_backend_key_missing`. The built-in `ghostcrawl_google_search` tool — GhostCrawl is the search provider, so no separate search key is needed — is the LC-idiomatic alternative. |
| crawl-runs, schedules, webhooks, recordings, kv, profiles, sessions, datasets, identity, me, storage-states | N/A | management / mutation — not a retrieval tool for an agent |
| pdf, screenshot | N/A | binary capture — not idiomatic as a text-returning LC tool/loader |
| agent | N/A (BYO) | agent is BYO/not-hosted (`require_agent_enabled()` 404); the developer supplies the LLM |

Every tool is verified by a real-execution parity suite (transcripts record counts
+ variable names only); re-run with `make -C sdks/python-langchain parity-e2e`.

## License

Proprietary — GhostCrawl Software License. See [LICENSE](LICENSE).
