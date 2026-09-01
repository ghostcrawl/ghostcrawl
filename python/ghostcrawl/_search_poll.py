"""SDK-owned bounded client-side poll for ``search(wait=True)``.

Unlike ``crawl`` — whose ``GET /v1/crawl-runs/{id}?wait=true&timeout_s=N`` blocks
**server-side** on a completion event — the search-job contract is a **client
poll**: ``POST /v1/search`` on a cold rotation returns ``202 {status:"running",
poll_url, deadline, poll_max_seconds, poll_terminal_on_404}`` and
``GET {poll_url}`` returns ``202 running`` (with ``Retry-After``) until a terminal
``200``. The SDK owns the loop so the user writes zero poll code — **same
``wait=True`` DX, different mechanism under the hood** (documented honestly on
``search()``).

This module is pure stdlib + ``httpx`` (no kiota dependency) so the poll contract
is unit-testable in isolation from the generated core.
"""

from __future__ import annotations

import asyncio
import time
import typing

import httpx

#: Terminal search-job states (mirrors ``facade.TERMINAL_RUN_STATES`` idiom).
SEARCH_TERMINAL_STATES: frozenset[str] = frozenset(
    {"completed", "done", "failed", "cancelled", "error"}
)

#: Overall client-side wait budget (seconds) when the server gives no bound.
DEFAULT_TIMEOUT = 300.0
#: Fallback inter-poll interval when the server sends no ``Retry-After``.
DEFAULT_POLL_INTERVAL = 3.0


def search_is_terminal(job: typing.Mapping[str, typing.Any]) -> bool:
    """True when a search-job record has reached a terminal state."""
    return isinstance(job, typing.Mapping) and job.get("status") in SEARCH_TERMINAL_STATES


def parse_retry_after(raw: typing.Any) -> float | None:
    """Parse a ``Retry-After`` header value (delta-seconds) to a float ≥ 0."""
    if raw is None:
        return None
    if isinstance(raw, (list, tuple)):
        raw = raw[0] if raw else None
    try:
        return max(0.0, float(raw))
    except (TypeError, ValueError):
        return None


async def poll_search_job(
    http: httpx.AsyncClient,
    base_url: str,
    job: typing.Mapping[str, typing.Any],
    headers: typing.Mapping[str, str],
    *,
    error_factory: typing.Callable[[httpx.Response], Exception],
    timeout: float | None = None,
    initial_retry: float | None = None,
) -> dict:
    """Bounded client-side poll of a cold search job to a terminal result.

    Copies the STRUCTURE of ``CrawlRunsClient.wait`` (deadline + re-arm loop) but
    implements the client-poll contract:

    * follows the ``poll_url`` from the 202 body (absolute or base-relative);
    * honors ``Retry-After`` between polls, bounded by ``poll_max_seconds`` /
      explicit ``timeout`` / :data:`DEFAULT_TIMEOUT`;
    * treats a terminal ``200`` (or a body whose ``status`` is terminal) as done;
    * treats ``404`` as terminal when ``poll_terminal_on_404`` (default true) —
      raising ``error_factory(resp)`` so it surfaces promptly instead of spinning;
    * returns the latest non-terminal record if the deadline elapses first.

    ``error_factory`` maps a non-2xx response onto the caller's typed error (kept
    in the facade so the error classes stay there). Never echoes credentials.
    """
    poll_url = job.get("poll_url") if isinstance(job, typing.Mapping) else None
    if not poll_url:
        # No poll handle — nothing to poll; the 202 body is all we have.
        return dict(job) if isinstance(job, typing.Mapping) else {}

    if str(poll_url).startswith(("http://", "https://")):
        url = str(poll_url)
    else:
        url = f"{base_url.rstrip('/')}/{str(poll_url).lstrip('/')}"

    poll_max = job.get("poll_max_seconds")
    terminal_on_404 = bool(job.get("poll_terminal_on_404", True))

    if timeout is not None:
        deadline = time.monotonic() + float(timeout)
    elif isinstance(poll_max, (int, float)):
        deadline = time.monotonic() + float(poll_max)
    else:
        deadline = time.monotonic() + DEFAULT_TIMEOUT

    retry_after = initial_retry
    latest: dict = dict(job) if isinstance(job, typing.Mapping) else {}
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return latest
        wait_s = retry_after if retry_after is not None else DEFAULT_POLL_INTERVAL
        wait_s = max(0.0, min(wait_s, remaining))
        if wait_s > 0:
            await asyncio.sleep(wait_s)
            if time.monotonic() >= deadline:
                return latest

        resp = await http.get(url, headers=dict(headers))
        status = resp.status_code
        if status == 404:
            if terminal_on_404:
                raise error_factory(resp)
            return latest
        if status >= 400:
            raise error_factory(resp)

        data = resp.json() if resp.content else {}
        if status == 200 or search_is_terminal(data):
            return data if isinstance(data, dict) else latest
        # Still running (202) — re-arm with the server's next Retry-After.
        if isinstance(data, dict) and data:
            latest = data
        retry_after = parse_retry_after(resp.headers.get("Retry-After"))
