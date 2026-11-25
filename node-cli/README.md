# @ghostcrawl/cli

Official `ghostcrawl` command-line interface for the GhostCrawl orchestration API.
TypeScript implementation using `commander.js`, wrapping `@ghostcrawl/sdk`.

Parallel to the Python CLI (`pip install ghostcrawl`) — same command surface,
same JSON output format.

## Install

Product version **2.4.0**; published npm package latest **2.3.91** (a 2.3.9-band patch identifier from the prior release — registry artifacts are immutable; product is now 2.4.0). Source version files remain at 2.4.0:

```bash
npm install -g @ghostcrawl/cli@2.4.0
```

Requires Node.js 22 or newer (Node.js >= 22 in `package.json` engines). The `ghostcrawl init` and `ghostcrawl install` verbs below
are the CLI's own first-run commands; keep them — they are the real CLI surface,
not a per-SDK runtime installer.

### First step: runtime setup

The CLI talks to the GhostCrawl API (hosted cloud or your own machine). To run it
locally, use the single unified terminal-install path — Docker, the three browser
engines and your API key — documented at
**https://docs.ghostcrawl.io/self-host**. One launcher covers Linux, macOS and
Windows; no per-SDK installer is needed.

## First-time setup

```bash
# Save + validate your API key (writes ~/.config/ghostcrawl/config.toml, mode 0600)
ghostcrawl init
```

`init` validates the key against the real auth path (a no-spend `GET /v1/me`,
falling back to a trivial scrape) and prints exactly one truthful outcome — a
valid key is never reported as unverified.

Hosted-API (cloud) users have nothing to install locally — `ghostcrawl install`
exits 0 with a friendly note. `install` only downloads a local engine for
self-host deployments (when a `--license-token`, `GHOSTCRAWL_BINARY_URL`, or
`GHOSTCRAWL_LICENSE_KEY` signal is present).

## Quick Start

```bash
# Set your API key
export GHOSTCRAWL_API_KEY=...

# Scrape a URL (JSON to stdout)
ghostcrawl scrape https://example.com --pretty

# Fetch rendered content / structured extraction / site map
ghostcrawl content https://example.com
ghostcrawl extract https://example.com --schema schema.json
ghostcrawl map https://example.com

# Binary captures (bytes written to --out, a JSON manifest to stdout)
ghostcrawl screenshot https://example.com --out page.png
ghostcrawl pdf https://example.com --out page.pdf

# Crawl + crawl-run status
ghostcrawl crawl https://example.com --max-pages 1 --out crawl.json
ghostcrawl crawl-runs

# Sessions / identity / usage / auth
ghostcrawl session list

# Web search — BYO: needs your own search-backend key
ghostcrawl search "web scraping" --provider-key "$MY_SEARCH_KEY"
```

## Commands

Each subcommand wraps the real `@ghostcrawl/sdk` node facade method.

| Command | Description |
|---------|-------------|
| `ghostcrawl scrape <url>` | Scrape a URL; emit content as JSON (`POST /v1/scrape`) |
| `ghostcrawl batch --input-file <f>` | Batch-scrape every URL in a file; write NDJSON per URL to `--output-dir` |
| `ghostcrawl content <url>` | Fetch a URL's rendered content (`POST /v1/content`) |
| `ghostcrawl screenshot <url>` | Capture a screenshot; write image bytes to `--out` (`POST /v1/screenshot`) |
| `ghostcrawl pdf <url>` | Render a URL to PDF (any engine); write bytes to `--out` (`POST /v1/pdf`) |
| `ghostcrawl extract <url> --schema <f>` | Extract structured data via a JSON schema (`POST /v1/extract`) |
| `ghostcrawl map <url>` | Discover reachable URLs (`POST /v1/map`) |
| `ghostcrawl crawl <url>` | Start a crawl run (`POST /v1/crawl-runs`) |
| `ghostcrawl crawl-runs` | List crawl-run status (`GET /v1/crawl-runs`) |
| `ghostcrawl search <query>` | Web search — **BYO** search-backend key via `--provider-key` (`POST /v1/search`) |
| `ghostcrawl session list` | List active sessions (`GET /v1/sessions`) |
| `ghostcrawl auth login` | Set or rotate the API key |
| `ghostcrawl config`, `init`, `install` | Local config / setup helpers |

**Framework-lane note:** the CLI covers the idiomatic one-shot subcommand
subset. Interactive/admin surfaces (agent BYO, `kv`/`profiles` admin, webhooks/schedules/
datasets/recordings/storage-states management) are intentionally **N/A** — CLI-awkward,
not shipped as subcommands. Every shipped command is verified by a real-execution
parity suite (re-run: `make -C sdks/node-cli parity-e2e`).

## Options (global)

| Flag | Description |
|------|-------------|
| `--api-key <key>` | Override `GHOSTCRAWL_API_KEY` env var |
| `--base-url <url>` | Override the default API base URL |
| `--pretty` | Pretty-print JSON output (default: compact) |
| `--version` | Print version |
| `--help` | Print help |

## Install Channels

The `ghostcrawl` CLI is available via two install channels:

1. **npm (this package)**
   ```bash
   npm install -g @ghostcrawl/cli
   ```

2. **pip (Python CLI — same command surface)**
   ```bash
   pip install ghostcrawl
   ```

## License

MIT — see [LICENSE](LICENSE).
