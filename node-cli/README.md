# @ghostcrawl/cli

Official `ghostcrawl` command-line interface for the GhostCrawl orchestration API.
TypeScript implementation using `commander.js`, wrapping `@ghostcrawl/sdk`.

Parallel to the Python CLI (`pip install ghostcrawl`) — same command surface,
same JSON output format.

## Install

```bash
npm install -g @ghostcrawl/cli
```

Requires Node.js >= 18.

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
| `ghostcrawl content <url>` | Fetch a URL's rendered content (`POST /v1/content`) |
| `ghostcrawl screenshot <url>` | Capture a screenshot; write image bytes to `--out` (`POST /v1/screenshot`) |
| `ghostcrawl pdf <url>` | Render a URL to PDF (Chrome-only); write bytes to `--out` (`POST /v1/pdf`) |
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

Proprietary — GhostCrawl Software License. See [LICENSE](LICENSE).
