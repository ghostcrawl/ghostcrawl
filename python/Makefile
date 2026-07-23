# Phase 178 — python lane one-command parity runner (R3).
#
# `make parity-e2e` runs tests/parity_e2e.py, which exercises EVERY user-surface
# row in scripts/phase178/rowset.json ONCE against the REAL cloud test tenant and
# writes one transcript per row to 178-EVIDENCE/python/ (TRANSCRIPT-SCHEMA.md).
#
# Secrets (D-04): the token is read from GHOSTCRAWL_API_KEY (NEVER hardcoded); if
# it is unset the runner STOPS and fabricates nothing. The real-backend sweep is
# wrapped in the shared flock run-lock (scripts/phase178/parity-run.sh) so
# concurrent-wave lanes serialize their hits to the single shared tenant (W2).
# NOTE: this is a live-network integration run and is EXPECTED to exceed the 30s
# soft-latency guidance — network-bound, not a hang (W5).
#
#   export GHOSTCRAWL_API_KEY='<locked-down test-tenant token>'   # revoked after run
#   export GHOSTCRAWL_BASE_URL='<cloud test tenant base URL>'     # optional
#   make -C sdks/python parity-e2e            # all rows
#   make -C sdks/python parity-e2e ROW=pdf    # one row
SHELL := /bin/bash
REPO_ROOT := $(shell cd ../.. && pwd)
VENV := .venv-parity
PY := $(VENV)/bin/python

.PHONY: parity-e2e parity-clean

# Isolated venv with the SDK installed editable (kiota runtime deps). Built once.
# .venv-* is gitignored (**/.venv-*/), so it never enters a commit.
$(PY):
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install -q --upgrade pip
	$(VENV)/bin/pip install -q -e .

parity-e2e: $(PY)
	@ROW="$(ROW)" $(REPO_ROOT)/scripts/phase178/parity-run.sh python -- $(PY) tests/parity_e2e.py

parity-clean:
	rm -rf $(VENV)
