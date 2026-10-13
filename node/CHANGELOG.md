# GhostCrawl Node/TypeScript SDK Changelog

All notable changes to the GhostCrawl Node client are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/) and this
project follows semantic versioning.

## [Unreleased]

### Added

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

### Changed

- The `@microsoft/kiota-*` runtime floor is now `^1.0.0-preview.108`. Older
  `kiota-serialization-json` builds emitted invalid JSON (`},,{`) for a list of
  objects in a request body (e.g. mouse `ops`, cookie lists).

### Notes

- This SDK does NOT provide an AI/LLM backend — model/key passthrough only
  (bring your own). The new page actions are browser primitives, no model.
- The generated-core additions were added directly (spec-faithful to the
  published customer spec) rather than by a full regen: Kiota 1.32.2's
  TypeScript writer aborts on nullable formatted strings
  (`anyOf: [{type: string, format: date-time|uuid}, {type: null}]`), and
  Kiota 1.35.0's full output does not type-check under `strict`.

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
