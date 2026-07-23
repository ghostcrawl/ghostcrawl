# Phase 178 — python-langchain framework-lane one-command parity runner (R8).
#
# `make parity-e2e` runs tests/parity_e2e.py, which exercises the idiomatic
# LangChain-tool retrieval subset (scrape/content/extract/map/crawl/usage) against
# the REAL cloud test tenant as real GhostCrawl*Tool round-trips, marks search as
# N/A (BYO) and every non-retrieval capability as N/A (not idiomatic as an LC tool)
# with a one-line WHY, and writes one transcript per rowset row to
# 178-EVIDENCE/python-langchain/ (TRANSCRIPT-SCHEMA.md — counts + var-names only).
#
# Secrets (D-04): the token is read from GHOSTCRAWL_API_KEY (NEVER hardcoded); if it
# is unset the runner STOPS and fabricates nothing. The real-backend sweep is wrapped
# in the shared flock run-lock (scripts/phase178/parity-run.sh) so concurrent-wave
# lanes serialize their hits to the single shared tenant (W2). This is a live-network
# integration run and is EXPECTED to exceed the 30s soft-latency guidance (W5).
#
#   export GHOSTCRAWL_API_KEY='<locked-down test-tenant token>'   # revoked after run
#   export GHOSTCRAWL_BASE_URL='<cloud test tenant base URL>'     # optional
#   make -C sdks/python-langchain parity-e2e             # all rows
#   make -C sdks/python-langchain parity-e2e ROW=scrape  # one row
SHELL := /bin/bash
REPO_ROOT := $(shell cd ../.. && pwd)
VENV := .venv-parity
PY := $(VENV)/bin/python

.PHONY: parity-e2e parity-clean

# Isolated venv with the langchain lane installed editable. .venv-* is gitignored.
$(PY):
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install -q --upgrade pip
	$(VENV)/bin/pip install -q -e .

parity-e2e: $(PY)
	@ROW="$(ROW)" $(REPO_ROOT)/scripts/phase178/parity-run.sh python-langchain -- $(PY) tests/parity_e2e.py

parity-clean:
	rm -rf $(VENV)
