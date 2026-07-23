# Phase 178 — node lane one-command parity runner (R3).
#
# `make parity-e2e` runs test/parity_e2e.test.ts (vitest), which exercises EVERY
# user-surface row in scripts/phase178/rowset.json ONCE against the REAL cloud
# test tenant and writes one transcript per row to 178-EVIDENCE/node/
# (TRANSCRIPT-SCHEMA.md).
#
# Secrets (D-04): the token is read from GHOSTCRAWL_API_KEY (NEVER hardcoded); if
# it is unset the suite throws the auth gate and fabricates nothing. The
# real-backend sweep is wrapped in the shared flock run-lock
# (scripts/phase178/parity-run.sh) so concurrent-wave lanes serialize their hits
# to the single shared tenant (W2). NOTE: this is a live-network integration run
# and is EXPECTED to exceed the 30s soft-latency guidance — network-bound (W5).
#
#   export GHOSTCRAWL_API_KEY='<locked-down test-tenant token>'   # revoked after run
#   export GHOSTCRAWL_BASE_URL='<cloud test tenant base URL>'     # optional
#   make -C sdks/node parity-e2e             # all rows
#   make -C sdks/node parity-e2e ROW=pdf     # one row
SHELL := /bin/bash
REPO_ROOT := $(shell cd ../.. && pwd)

.PHONY: parity-e2e

node_modules:
	npm ci --no-audit --no-fund

parity-e2e: node_modules
	@node scripts/gen-version.mjs
	@ROW="$(ROW)" $(REPO_ROOT)/scripts/phase178/parity-run.sh node -- npx vitest run --config vitest.parity.config.ts
