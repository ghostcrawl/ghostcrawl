# GhostCrawl Node/TypeScript SDK Changelog

All notable changes to the GhostCrawl Node client are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/) and this
project follows semantic versioning.

## [2.3.7] - 2026-11-16

### Added

- **Playwright / Puppeteer drop-in adapters** — `@ghostcrawl/sdk/automation` mints a
  live session and returns the endpoint your own client library already understands.
  `chromium.connect()` speaks Chrome CDP (`puppeteer.connect` /
  `playwright.chromium.connectOverCDP`); `firefox.connect()` and `webkit.connect()`
  speak Playwright-wire. Each adapter rejects a socket whose minted protocol does not
  match, so the wrong client library cannot be attached by accident. `locale` and
  `timezone` are accepted but never applied as CDP emulation overrides (they are
  detectable) — they travel through the identity request instead.
- **Device class on session create and scrape** — pass `device` to constrain the
  identity population (`random_mobile`, `random_ios`, …); a device/engine mismatch is
  rejected rather than silently re-routed.
- **Engine-agnostic in-page actions** (parity with the Python SDK) —
  `client.page.mouse(ops, fields?)` replays a mouse op-stream
  (move/down/up/wheel/dwell) natively on the live page (POST /v1/page/mouse);
  `client.page.arrival(destUrl, sourceUrl, fields?)` arrives at a page through
  a native link click so `document.referrer`, `Referer` and `Sec-Fetch-*` are
  native (POST /v1/page/arrival; optional `referrer_shape`, `source_title`);
  `client.page.tabVisit({ url, dwell_s })` opens a real background tab, reads
  it and closes it (POST /v1/page/tab-visit; Chrome engine only).
- Generated core: request builders for `/v1/page/{mouse,arrival,tab-visit,
  close-popups,touch}` and their request-body models.
- `CrawlRun` / `CrawlRunStarted` are exported. `crawlRuns.start()` now returns
  `CrawlRunStarted`, whose `run_id` is a required `string`, so
  `const { run_id } = await client.crawlRuns.start(...)` flows straight into
  `crawlRuns.wait(run_id)` without a cast.

### Changed

- The `@microsoft/kiota-*` runtime floor is now `^1.0.0-preview.108`. Older
  `kiota-serialization-json` builds emitted invalid JSON (`},,{`) for a list of
  objects in a request body (e.g. mouse `ops`, cookie lists).
- Identity seeds are org-scoped on every reuse path; `search` returns a stable
  result shape when a poll times out.

### Notes

- This SDK does NOT provide an AI/LLM backend — model/key passthrough only
  (bring your own). The page actions and automation adapters are browser
  primitives, no model.

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
