"""Facade ergonomics + agent security (post-Kiota migration).

The canonical client is the async ``GhostCrawlClient``. These tests cover the
observable contract that replaced the prior synchronous wrapper:

  - the client is an async context manager that closes its httpx session;
    ``aclose()`` is idempotent.
  - ``agent(...)`` threads ``provider_config`` into the request body and the
    bearer is delivered by the Kiota auth provider (so it cannot be spoofed or
    clobbered by request-body fields).

Network is mocked via respx so no live /v1/agent call is made.
"""
from __future__ import annotations

import json

import httpx
import pytest
import respx

# NOTE: import ``GhostCrawlClient`` lazily inside the helpers (not at module
# top). The repo root ``ghostcrawl/`` SaaS package and the SDK
# ``sdks/python/ghostcrawl`` package share a name; deferring the import
# guarantees the SDK package is resolved, not the root SaaS package.

_BASE = "https://api.test"
_AGENT_OK = {"status": "completed", "payload": {}}


def _build(api_key: str = "gc_secrettoken", *, provider_config=None):
    from ghostcrawl import GhostCrawlClient

    return GhostCrawlClient(
        token=api_key, base_url=_BASE, provider_config=provider_config
    )


# ---------------------------------------------------------------------------
# Context-manager + close semantics
# ---------------------------------------------------------------------------


async def test_async_context_manager_closes_http() -> None:
    async with _build() as c:
        http = c._core.request_adapter._http_client
        assert http.is_closed is False
    assert http.is_closed is True


async def test_aclose_is_idempotent() -> None:
    c = _build()
    await c.aclose()
    await c.aclose()  # must not raise


# ---------------------------------------------------------------------------
# agent() — provider_config threading + bearer integrity
# ---------------------------------------------------------------------------


@respx.mock
async def test_agent_threads_provider_config_and_bearer_is_authoritative() -> None:
    """provider_config rides the body; the bearer is set by the auth provider.

    A caller cannot clobber the Authorization header through body fields — the
    Kiota auth provider stamps the bearer on every request, so the security
    property (bearer cannot be spoofed) holds by construction.
    """
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["auth"] = request.headers.get("authorization")
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json=_AGENT_OK)

    route = respx.post(f"{_BASE}/v1/agent").mock(side_effect=handler)

    client = _build(
        provider_config={"base_url": "https://p", "api_key": "sk", "model": "m"}
    )
    # A body field that tries to masquerade as auth must not become the header.
    await client.agent(instruction="do thing", authorization="Bearer EVIL")

    assert route.called
    assert captured["auth"] == "Bearer gc_secrettoken"
    assert captured["body"]["provider_config"]["model"] == "m"
    # The bogus body field is just a body field — never the header.
    assert captured["body"].get("authorization") == "Bearer EVIL"
    assert captured["auth"] != "Bearer EVIL"


@respx.mock
async def test_agent_without_instruction_or_task_raises() -> None:
    client = _build()
    with pytest.raises(ValueError):
        await client.agent()
