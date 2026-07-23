#!/usr/bin/env bash
# Run a search/SERP query.
# Usage: GHOSTCRAWL_API_KEY=YOUR_API_KEY ./search.sh "your query"
set -euo pipefail

QUERY="${1:-best web scraping api}"

curl -sS https://api.ghostcrawl.io/v1/search \
  -H "Authorization: Bearer ${GHOSTCRAWL_API_KEY:?set GHOSTCRAWL_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"${QUERY}\", \"engine\": \"brave\"}"
