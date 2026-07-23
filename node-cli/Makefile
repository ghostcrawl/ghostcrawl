# Phase 178 — node-cli framework-lane one-command parity runner (R8).
#
# `make parity-e2e` builds the real @ghostcrawl/sdk node facade (which the CLI wraps —
# incl. content()/screenshot()/pdf() from Plan 02), builds the CLI, then runs
# tests/parity_e2e.test.ts (vitest, dedicated vitest.parity.config.ts). The runner spawns
# the COMPILED CLI (dist/index.js) as a black box against the REAL cloud test tenant,
# exercising the idiomatic CLI-subcommand subset (scrape/content/screenshot/pdf/map/crawl/
# crawl-runs/extract/sessions/identity/me/usage) → GREEN, marking search N/A (BYO) and
# every CLI-awkward capability N/A with a one-line WHY. One transcript per rowset row lands
# in 178-EVIDENCE/node-cli/ (TRANSCRIPT-SCHEMA.md — counts + var-names only, D-04).
#
# Secrets (D-04): the token is read from GHOSTCRAWL_API_KEY (NEVER hardcoded); unset → the
# runner fails the auth-gate assertion and fabricates nothing. The real-backend sweep is
# wrapped in the shared flock run-lock (scripts/phase178/parity-run.sh) so concurrent-wave
# lanes serialize on the shared tenant (W2). Live-network; exceeds the 30s soft-latency
# guidance by design (W5).
#
#   export GHOSTCRAWL_API_KEY='<locked-down test-tenant token>'   # revoked after run
#   export GHOSTCRAWL_BASE_URL='<cloud test tenant base URL>'     # optional
#   make -C sdks/node-cli parity-e2e             # all rows
#   make -C sdks/node-cli parity-e2e ROW=scrape  # one row
SHELL := /bin/bash
REPO_ROOT := $(shell cd ../.. && pwd)

.PHONY: parity-e2e sdk-build cli-build

# Build the linked @ghostcrawl/sdk facade first (dist/index.cjs the CLI imports at runtime).
sdk-build:
	cd ../node && npm ci --no-audit --no-fund && npm run build

# Install (links @ghostcrawl/sdk -> ../node) + compile the CLI to dist/index.js.
cli-build: sdk-build
	npm ci --no-audit --no-fund
	npm run build

parity-e2e: cli-build
	@ROW="$(ROW)" $(REPO_ROOT)/scripts/phase178/parity-run.sh node-cli -- npx vitest run --config vitest.parity.config.ts
