#!/usr/bin/env bash
# Scrape a single page rendered by a real browser.
# Usage: GHOSTCRAWL_API_KEY=YOUR_API_KEY ./scrape.sh [URL] [ENGINE]
set -euo pipefail

URL="${1:-https://example.com}"
ENGINE="${2:-chrome}"

curl -sS https://api.ghostcrawl.io/v1/scrape \
  -H "Authorization: Bearer ${GHOSTCRAWL_API_KEY:?set GHOSTCRAWL_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"${URL}\", \"engine\": \"${ENGINE}\"}"
