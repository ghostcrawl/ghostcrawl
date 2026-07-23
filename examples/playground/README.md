# Playground data

This directory holds the cached results that power the **non-interactive**
(replayed) examples on the docs and marketing sites. Each site is scraped **once**
against the real ghostcrawl backend (and rendered once for the screenshot lane);
the genuine results are stored here and replayed verbatim in the UI. Nothing is
fabricated — these are real captures, just cached so the examples render instantly
without spending the visitor's quota.

The **interactive** (bring-your-own-key) examples do not read this directory —
they POST live to `${API_BASE}/v1/{lane}` through the BFF and render the real
response. There are no hardcoded mock responses anywhere in the example surfaces.

## Layout

| Path | Contents |
|------|----------|
| `manifest.json` | Allowlist of cached sites + the lane list + hero/default site. |
| `sites/<id>.json` | The cached per-lane results for one site. |
| `shots/<id>.jpg` | The cached screenshot for one site. |

## The 6 cached sites

| id | Label | URL |
|----|-------|-----|
| `ghostcrawl` | ghostcrawl.io | https://ghostcrawl.io |
| `example` | example.com | https://example.com |
| `books` | Books to Scrape | https://books.toscrape.com |
| `quotes` | Quotes to Scrape | https://quotes.toscrape.com |
| `hackernews` | Hacker News | https://news.ycombinator.com |
| `wikipedia` | Wikipedia | https://en.wikipedia.org |

`ghostcrawl` is both the hero site and the default site.

## Regenerating

The captures are produced by `ghostcrawl.io/scripts/capture_playground.py`, which
runs each site through the real backend once and writes `sites/<id>.json` plus the
binary screenshot assets. Regenerate when the cached examples go stale or a site's
structure changes — never hand-edit the cached JSON.
