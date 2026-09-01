# GhostCrawl Node/TypeScript SDK Changelog

All notable changes to the GhostCrawl Node client are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/) and this
project follows semantic versioning.

## [2.3.6] - 2026-08-22

### Added

- Full /v1 parity: `sessionPersona(sessionId)` returns a running session's
  customer-safe persona (`device_class` / `os_class` / `browser_class` / `locale`),
  and `me()` surfaces the `max_concurrency` field (your plan's concurrent-session
  ceiling).
- Typed, dict-accessible results: `scrape`, `search`, and `crawl` responses expose
  typed fields with full TypeScript typings and matching field names across every SDK.
- `search(url, { wait: true })` blocks until the job reaches a terminal state via a
  bounded client-side poll that honors `Retry-After`.
- The bundled CLI is shipped as a first-class product surface: `install` is mode-aware
  and returns a friendly exit for cloud users.

### Changed

- ESM and CommonJS builds are both published; import either `import { GhostCrawl }` or
  `require('ghostcrawl')`.
- Config precedence is explicit: the `GHOSTCRAWL_API_KEY` environment variable takes
  precedence over the on-disk config file.

### Migrating to 2.3.6

- No request or response field names changed. Result objects are typed but remain
  index-accessible, so existing `result.content` code keeps working.
- If you used the CLI `install` command as a cloud user, it now exits cleanly instead
  of prompting for a binary download.
