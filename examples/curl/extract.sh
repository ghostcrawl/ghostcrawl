#!/usr/bin/env bash
# Extract structured JSON from a page against a schema you provide.
# Usage: GHOSTCRAWL_API_KEY=YOUR_API_KEY ./extract.sh [URL]
set -euo pipefail

URL="${1:-https://example.com}"

curl -sS https://api.ghostcrawl.io/v1/extract \
  -H "Authorization: Bearer ${GHOSTCRAWL_API_KEY:?set GHOSTCRAWL_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"url\": \"${URL}\",
    \"engine\": \"auto\",
    \"schema\": {
      \"type\": \"object\",
      \"properties\": {
        \"title\":   {\"type\": \"string\"},
        \"summary\": {\"type\": \"string\"}
      }
    }
  }"
