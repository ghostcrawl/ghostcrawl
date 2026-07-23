# Model Provider Configuration

## ghostcrawl does NOT ship a default model

ghostcrawl does NOT ship a default model. You must configure a model provider
before using `/v1/agent`.

The agent execution layer requires a live LLM endpoint to process `act`,
`observe`, and `extract` steps. Without a configured provider, `/v1/agent`
falls back to the offline deterministic backend
(`GHOSTCRAWL_LLM_PROVIDER=offline`), which is suitable for CI testing but does
not perform real LLM reasoning.

---

## Configuring a Model Provider

Two configuration paths are supported. Per-request body takes precedence over
the server-side environment variable.

### Per-instance SDK kwarg

Pass `provider_config` to the `GhostCrawl` constructor. Every `agent()` call
from that client instance will include the config in the request body:

```python
from ghostcrawl import GhostCrawl

client = GhostCrawl(
    api_key="gc_...",
    provider_config={
        "base_url": "https://api.openai.com",
        "api_key": "sk-...",
        "model": "gpt-4o",
    }
)

result = client.agent(instruction="click the login button", url="https://example.com")
```

The `provider_config` dict is threaded into every `/v1/agent` request body as
`body["provider_config"]`. The SDK does NOT validate the config locally —
validation happens server-side via the `provider_config_invalid` envelope
(see Error Envelope below).

### Environment variable (server-side)

Set `GHOSTCRAWL_PROVIDER_CONFIG` to the path of a JSON file on the server
process. The file must contain a JSON object with the same `base_url`,
`api_key`, and `model` keys:

```bash
export GHOSTCRAWL_PROVIDER_CONFIG=/etc/ghostcrawl/provider.json
```

Example `/etc/ghostcrawl/provider.json`:

```json
{
  "base_url": "https://api.openai.com",
  "api_key": "sk-...",
  "model": "gpt-4o"
}
```

The server loads this file lazily on the first `/v1/agent` request and caches
the result for the process lifetime ("configure once at startup"). Restart the
server process to pick up changes.

**Precedence:** when a request body includes `provider_config`, it wins over
the environment variable. Per-request body overrides env var per-request.

**Note:** `GHOSTCRAWL_PROVIDER_CONFIG` is a server-side configuration variable.
The Python SDK does NOT read this env var — set it in the environment of the
server process running ghostcrawl, not in the client environment.

---

## Supported Providers

Any OpenAI-compatible HTTP endpoint is supported. ghostcrawl sends requests to
`{base_url}/v1/chat/completions` with a Bearer token.

Non-exhaustive list of compatible providers:

| Provider | `base_url` example |
|----------|-------------------|
| OpenAI | `https://api.openai.com` |
| Anthropic via gateway | `https://gateway.anthropic.com/v1` |
| Local Ollama with `/v1` shim | `http://localhost:11434` |
| vLLM | `http://vllm-host:8000` |
| Together AI | `https://api.together.xyz` |
| Azure OpenAI | `https://{resource}.openai.azure.com/openai/deployments/{deployment}` |

---

## Provider Configuration Schema

The `provider_config` object accepts exactly three fields — all required:

| Field | Type | Description |
|-------|------|-------------|
| `base_url` | string | HTTP or HTTPS base URL of the provider endpoint. Must start with `http://` or `https://`. |
| `api_key` | string | API key for the provider. Transmitted in `Authorization: Bearer` header. Never logged by ghostcrawl. |
| `model` | string | Model identifier as the provider expects it (e.g. `"gpt-4o"`, `"claude-3-5-sonnet-20241022"`). |

All three fields are validated on the server. Format errors return a structured
`provider_config_invalid` error envelope (see below).

---

## Error Envelope

When `provider_config` fails server-side validation, the server returns HTTP 422
with the following envelope:

```json
{
  "error_code": "provider_config_invalid",
  "details": {
    "field": "base_url",
    "reason": "missing provider base_url"
  }
}
```

The `details.field` value identifies which field caused the error
(`"base_url"`, `"api_key"`, `"model"`, or `"unknown"`).

This envelope mirrors the standard `invalid_request` pattern for consistency.

In the Python SDK, receiving `provider_config_invalid` raises a
`ProviderConfigError` exception (a subclass of `GhostCrawlError`):

```python
from ghostcrawl import GhostCrawl, ProviderConfigError

try:
    result = client.agent(instruction="...")
except ProviderConfigError as e:
    print(e.body["details"]["field"])   # e.g. "base_url"
    print(e.body["details"]["reason"])  # e.g. "missing provider base_url"
```

**Security note:** the `api_key` inside `provider_config` is NEVER included in
ghostcrawl log output. Only the first 4 characters appear in debug traces when
`GHOSTCRAWL_DEBUG_PROVIDER=1`.

If `GHOSTCRAWL_PROVIDER_CONFIG` points at a missing or malformed JSON file, the
server returns HTTP 500 with `error_code: "provider_config_env_load_failed"`.
Fix the file and restart the server.

---

## MCP Integration

ghostcrawl ships an MCP (Model Context Protocol) server. MCP is the standard
interop protocol for connecting external LLMs to tools and context sources; it
provides a structured interface for LLM providers that support the protocol
natively. See the MCP integration guide for the tool registry and connection
details.

---

## What This Doc Is Not

This document covers ghostcrawl's model provider configuration surface. A few
clarifications on scope:

- **Not proxy configuration**: residential proxy selection and exit routing is
  an operator-deploy concern. See the operator deployment guide for proxy
  configuration.
- **Not a request-level override per step**: `provider_config` is per-instance
  (SDK) or per-process (env var). Per-step LLM routing is not supported.
