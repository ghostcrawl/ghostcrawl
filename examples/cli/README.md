# CLI examples

```bash
npm install -g @ghostcrawl/cli
export GHOSTCRAWL_API_KEY="YOUR_API_KEY"
```

See [`commands.sh`](commands.sh) for a runnable tour. Common commands:

```bash
# Scrape a page
ghostcrawl scrape https://example.com --engine chrome

# Start a crawl run
ghostcrawl crawl https://example.com --max-depth 2 --max-pages 25

# Extract structured data against an inline schema
ghostcrawl extract https://example.com --schema '{"type":"object","properties":{"title":{"type":"string"}}}'

# Run a search query
ghostcrawl search "best web scraping api"

# Check who you are and your current tier
ghostcrawl me
```

Point the same CLI at a local self-host by setting `base_url` /
`GHOSTCRAWL_BASE_URL` to `http://localhost:47700` and using the per-boot token
from `LOCAL_ADMIN_READY` — see the [self-host guide](../../docs/usage-selfhost.md).
Container lifecycle is Docker (`docker run` / Compose), not separate CLI verbs.

Run `ghostcrawl --help` for the full command list.
