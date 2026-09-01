# GhostCrawl Python SDK Changelog

All notable changes to the GhostCrawl Python client are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/) and this
project follows semantic versioning.

## [2.3.6] - 2026-08-22

### Added

- Full /v1 parity: `session_persona(session_id)` returns a running session's
  customer-safe persona (`device_class` / `os_class` / `browser_class` / `locale`),
  and `me()` surfaces the `max_concurrency` field (your plan's concurrent-session
  ceiling).
- Synchronous client is now the default: `from ghostcrawl import GhostCrawl` returns
  a sync client, so `.scrape(url)` returns content with no `await`. The async client
  remains available as `AsyncGhostCrawl` for `asyncio` codebases.
- Typed, dict-accessible results: `scrape`, `search`, and `crawl` responses support both
  attribute access (`result.content`) and mapping access (`result["content"]`), with
  `.to_dict()` for a plain dictionary.
- `search(wait=True)` blocks until the job reaches a terminal state via a bounded
  client-side poll that honors `Retry-After`.
- `ghostcrawl init` validates a live API key with a single truthful outcome using a
  no-spend account probe (no accidental billable request).

### Changed

- Config precedence is explicit and surfaced: the `GHOSTCRAWL_API_KEY` environment
  variable takes precedence over `~/.config/ghostcrawl/config.toml`.
- `ghostcrawl install` is mode-aware — cloud users get a friendly exit instead of a
  binary-download prompt.

### Migrating to 2.3.6

- The sync client is the default. If you previously wrote `await client.scrape(...)`,
  drop the `await` (or switch to `AsyncGhostCrawl` to keep the async API). The sync
  client is safe to call from inside a running event loop.
- No request or response field names changed; typed results are a superset of the prior
  dictionary access, so existing `result["field"]` code keeps working.
