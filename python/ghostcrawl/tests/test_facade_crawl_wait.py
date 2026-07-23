"""Event-driven crawl-run completion — ``start(wait=True)`` and ``wait()``.

These lock the contract that the SDK never hand-rolls a poll-with-sleep loop:

  - ``crawl_runs.start(wait=True)`` sends ``wait_until="completed"`` +
    ``timeout_s`` on the POST body and returns the terminal run the server
    hands back (the server blocks event-driven; the SDK does not poll).
  - ``crawl_runs.wait(run_id)`` issues ``GET …?wait=true&timeout_s=…`` and
    returns as soon as the run is terminal — with NO fixed client-side sleep
    between the (server-blocking) long-poll windows.

Network is mocked with respx; no live call is made. See test_facade_extras.py
for why ``GhostCrawlClient`` is imported lazily inside each helper.
"""
from __future__ import annotations

import json

import httpx
import respx

_BASE = "https://api.test"


def _build(api_key: str = "gc_secrettoken"):
    from ghostcrawl import GhostCrawlClient

    return GhostCrawlClient(token=api_key, base_url=_BASE)


# ---------------------------------------------------------------------------
# start(wait=True) — sends wait_until + timeout_s, returns the terminal run
# ---------------------------------------------------------------------------


@respx.mock
async def test_start_wait_true_sends_wait_until_and_returns_terminal_run() -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        # Event-driven server: it blocked and hands back the completed run.
        return httpx.Response(
            200,
            json={"run_id": "run_123", "status": "completed", "pages_crawled": 7},
        )

    route = respx.post(f"{_BASE}/v1/crawl-runs").mock(side_effect=handler)

    async with _build() as client:
        run = await client.crawl_runs.start(
            url="https://example.com", wait=True, wait_timeout=120
        )

    assert route.called
    # The start-and-wait contract rode the POST body.
    assert captured["body"]["wait_until"] == "completed"
    assert captured["body"]["timeout_s"] == 120
    # A single POST resolved it — no follow-up GET poll was needed.
    assert run["status"] == "completed"
    assert run["pages_crawled"] == 7


@respx.mock
async def test_start_without_wait_omits_wait_fields() -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"run_id": "run_9", "status": "running"})

    respx.post(f"{_BASE}/v1/crawl-runs").mock(side_effect=handler)

    async with _build() as client:
        run = await client.crawl_runs.start(url="https://example.com")

    assert "wait_until" not in captured["body"]
    assert "timeout_s" not in captured["body"]
    assert run["status"] == "running"


# ---------------------------------------------------------------------------
# wait(run_id) — long-poll to a terminal status, no fixed client sleep
# ---------------------------------------------------------------------------


@respx.mock
async def test_wait_returns_on_terminal_status_with_no_client_sleep() -> None:
    calls: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(dict(httpx.QueryParams(request.url.query)))
        return httpx.Response(
            200, json={"run_id": "run_123", "status": "completed"}
        )

    route = respx.get(url__regex=rf"{_BASE}/v1/crawl-runs/run_123").mock(
        side_effect=handler
    )

    import ghostcrawl.facade as facade

    # Fail loudly if the implementation ever falls back to a client-side sleep.
    def _no_sleep(*_a, **_k):  # pragma: no cover - only hit on regression
        raise AssertionError("wait() must not sleep client-side; use long-poll")

    orig_sleep = facade.time.sleep
    facade.time.sleep = _no_sleep  # type: ignore[assignment]
    try:
        async with _build() as client:
            run = await client.crawl_runs.wait("run_123", timeout=30)
    finally:
        facade.time.sleep = orig_sleep  # type: ignore[assignment]

    assert route.called
    # It long-polled the server: wait=true rode the query string.
    assert calls[0]["wait"] == "true"
    assert int(calls[0]["timeout_s"]) >= 1
    # Terminal on the first window — returned immediately, no re-arm needed.
    assert len(calls) == 1
    assert run["status"] == "completed"


@respx.mock
async def test_wait_rearms_across_windows_until_terminal() -> None:
    """A server window that returns non-terminal re-arms; terminal ends it."""
    responses = [
        httpx.Response(200, json={"run_id": "r", "status": "running"}),
        httpx.Response(200, json={"run_id": "r", "status": "running"}),
        httpx.Response(200, json={"run_id": "r", "status": "completed"}),
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        return responses.pop(0)

    respx.get(url__regex=rf"{_BASE}/v1/crawl-runs/r").mock(side_effect=handler)

    async with _build() as client:
        run = await client.crawl_runs.wait("r", timeout=30)

    # Exhausted the two non-terminal windows, returned on the terminal one.
    assert responses == []
    assert run["status"] == "completed"


@respx.mock
async def test_start_wait_rearms_when_start_returns_non_terminal() -> None:
    """If start-and-wait times out its window non-terminal, re-arm via GET."""

    def post_handler(request: httpx.Request) -> httpx.Response:
        # Server's long-poll window elapsed before terminal.
        return httpx.Response(200, json={"run_id": "run_x", "status": "running"})

    def get_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"run_id": "run_x", "status": "failed"})

    respx.post(f"{_BASE}/v1/crawl-runs").mock(side_effect=post_handler)
    get_route = respx.get(url__regex=rf"{_BASE}/v1/crawl-runs/run_x").mock(
        side_effect=get_handler
    )

    async with _build() as client:
        run = await client.crawl_runs.start(
            url="https://example.com", wait=True, wait_timeout=30
        )

    assert get_route.called  # it re-armed with a long-poll GET
    assert run["status"] == "failed"
