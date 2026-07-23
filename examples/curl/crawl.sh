#!/usr/bin/env bash
# Start a crawl run and wait for it to finish — the server holds the request open and
# returns the completed run, so there is no client-side polling loop.
# Usage: GHOSTCRAWL_API_KEY=YOUR_API_KEY ./crawl.sh [SEED_URL]
set -euo pipefail

SEED="${1:-https://example.com}"
AUTH="Authorization: Bearer ${GHOSTCRAWL_API_KEY:?set GHOSTCRAWL_API_KEY}"

# Start the crawl and block until it completes (wait_until + timeout_s). The response is
# the finished run, with results — one call, no polling.
curl -sS https://api.ghostcrawl.io/v1/crawl-runs \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d "{\"action\": \"start\", \"seed_urls\": [\"${SEED}\"], \"max_depth\": 2, \"max_pages\": 25, \"wait_until\": \"completed\", \"timeout_s\": 300}"

# For long crawls, prefer a webhook (register a URL; we POST crawl_run.completed on finish).
# To wait on a run you already started:
#   curl -sS "https://api.ghostcrawl.io/v1/crawl-runs/RUN_ID?wait=true&timeout_s=300" -H "$AUTH"
