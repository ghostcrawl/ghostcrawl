#!/usr/bin/env bash
# A short tour of the GhostCrawl CLI.
#
#   npm install -g @ghostcrawl/cli
#   export GHOSTCRAWL_API_KEY=YOUR_API_KEY
#   ./commands.sh
set -euo pipefail

: "${GHOSTCRAWL_API_KEY:?set GHOSTCRAWL_API_KEY}"

# Who am I? (tier, email, team)
ghostcrawl me

# Scrape a single page.
ghostcrawl scrape https://example.com --engine chrome

# Start a crawl run.
ghostcrawl crawl https://example.com --max-depth 2 --max-pages 25

# Extract structured data.
ghostcrawl extract https://example.com \
  --schema '{"type":"object","properties":{"title":{"type":"string"}}}'

# Search the web.
ghostcrawl search "best web scraping api"
