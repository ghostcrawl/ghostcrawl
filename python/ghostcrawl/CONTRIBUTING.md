# Contributing

Thanks for your interest in contributing to the GhostCrawl Python SDK!

## Getting Started

### Prerequisites

- Python 3.10+
- pip

### Installation

Install the project (editable) with its dev extras:

```bash
pip install -e ".[dev]"
```

### Testing

Run the test suite from the SDK directory (`sdks/python`):

```bash
python -m pytest tests/ ghostcrawl/tests/ -q
```

## Architecture

The SDK is two layers:

- **`_generated/`** — the canonical core. A spec-faithful request-builder +
  models package generated from the OpenAPI definition with
  [Microsoft Kiota](https://github.com/microsoft/kiota). It owns all HTTP
  transport, auth, and serialization. Treat it as generated output — regenerate
  it from the spec rather than hand-editing.
- **`ghostcrawl/`** — the hand-written public surface. The canonical client is
  `ghostcrawl/facade.py` (`GhostCrawlClient`), a thin async ergonomic layer that
  maps idiomatic calls onto the generated request-builders. The package root
  (`__init__.py`) re-exports the client, the back-compat aliases (`GhostCrawl`,
  `Client`), the typed errors, the error-code catalog (`errors/`), the helpers
  (`params.py`, `retry_policy.py`, `branded.py`), the identity sub-client
  (`identity/`), the MCP wrapper (`mcp/`), and the CLI (`cli/`).

### Adding a method to the facade

1. Find the right generated request-builder under `_generated/v1/<area>/` (read
   the file to get the exact builder + request-body class names — do not guess).
2. Add an `async def` to `GhostCrawlClient` that builds the request body and
   delegates to the builder, mirroring the existing `scrape` / `extract` / `map`
   methods.
3. Route the call through `_resolve_response(...)` so transport errors map to
   the typed exceptions and HTTP-200 target failures raise `ScrapeError`.
4. Add a test and verify against a live API where possible.

## Making Changes

1. Create a branch.
2. Make your changes (facade/CLI/errors/helpers in `ghostcrawl/`; regenerate
   `_generated/` from the spec for contract changes).
3. Run the tests: `python -m pytest tests/ ghostcrawl/tests/ -q`.
4. Commit with a clear message and open a pull request.

## License

By contributing you agree that your contributions are licensed under the same
license as the project (the GhostCrawl Software License; see LICENSE).
