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

## Framework-lane surface (idiomatic retrieval subset vs N/A)

`ghostcrawl-langchain` is a **framework lane**, not a full SDK: it wraps the
idiomatic *retrieval* subset of the GhostCrawl API as LangChain tools an agent
can call. Everything else is an explicit **N/A** — not a gap, just not idiomatic
as an LC retrieval `Tool`/loader (zero blank cells, zero padded-green; D-10/D-11).

| Capability | Status | Tool / rationale |
|------------|--------|------------------|
| scrape | ✅ GREEN | `GhostCrawlScrapeTool` → `POST /v1/scrape` |
| content | ✅ GREEN | `GhostCrawlContentTool` → `POST /v1/content` |
| extract | ✅ GREEN | `GhostCrawlExtractTool` → `POST /v1/extract` |
| map | ✅ GREEN | `GhostCrawlMapTool` → `POST /v1/map` |
| crawl | ✅ GREEN | `GhostCrawlCrawlTool` → `POST /v1/crawl` (seeds `seed_urls`) |
| search | N/A (BYO) | `GhostCrawlSearchTool` reaches `/v1/search`, which needs a user-supplied search-backend key (`X-Provider-Authorization`); a keyless call returns `401 search_backend_key_missing`. The keyless `ghostcrawl_google_search` tool is the LC-idiomatic alternative. |
| crawl-runs, schedules, webhooks, recordings, kv, profiles, sessions, datasets, identity, me, storage-states | N/A | management / mutation — not a retrieval tool for an agent |
| pdf, screenshot | N/A | binary capture — not idiomatic as a text-returning LC tool/loader |
| agent | N/A (BYO) | agent is BYO/not-hosted (`require_agent_enabled()` 404); the developer supplies the LLM |

Every tool is verified by a real-execution parity suite (transcripts record counts
+ variable names only); re-run with `make -C sdks/python-langchain parity-e2e`.

## License

Proprietary — GhostCrawl Software License. See [LICENSE](LICENSE).
