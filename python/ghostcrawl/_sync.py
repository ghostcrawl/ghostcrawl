"""Synchronous default client — the loop-thread-bridged twin of the async facade.

Python's canonical client is async (:class:`ghostcrawl.facade.GhostCrawlClient`),
which makes ``print(client.scrape(url))`` return a bare coroutine ("was never
awaited") — the #1 first-use DX cliff. :class:`SyncGhostCrawl` closes
that cliff: it exposes the *same* surface synchronously so
``GhostCrawl(token=...).scrape(url)`` returns rendered content directly, with no
``await`` and no ``asyncio.run`` footgun.

Mechanism (the standard sync-over-async bridge used by mature async-first
SDKs): a single long-lived event loop runs on a private **daemon** thread;
every sync method submits the async-facade coroutine to that loop via
``asyncio.run_coroutine_threadsafe(coro, loop).result()``. Because the coroutine
runs on a *different* loop/thread, calling a sync method from *inside* an already
running event loop (Jupyter / an async app) does NOT raise
``RuntimeError: asyncio.run() cannot be called from a running event loop``.

This is a pure **delegation** layer: it owns no HTTP transport of its own and
duplicates nothing — it reuses the existing delegating async facade verbatim
(FACADE-PATTERN "MANDATORY DELEGATION"). Results are the exact typed,
dict-accessible objects the async facade returns (the typed wrappers flow through
unchanged).
"""

from __future__ import annotations

import asyncio
import inspect
import threading
import typing

from .facade import GhostCrawlClient as _AsyncGhostCrawlClient

__all__ = ["SyncGhostCrawl"]


class _SyncSubClient:
    """Blocking proxy over an async sub-client (``crawl_runs``/``sessions``/…).

    The async facade's sub-clients expose ``async def`` methods. On the sync
    default client we wrap each coroutine-returning call through the same
    loop-thread bridge so ``client.sessions.create(...)`` returns a result
    directly — never a bare un-awaited coroutine (the sync-first contract;
    no "coroutine was never awaited" footgun on the sub-client surface either).
    Non-coroutine attributes pass through unchanged.
    """

    __slots__ = ("_bridge", "_target")

    def __init__(self, bridge: SyncGhostCrawl, target: typing.Any) -> None:
        object.__setattr__(self, "_bridge", bridge)
        object.__setattr__(self, "_target", target)

    def __getattr__(self, name: str) -> typing.Any:
        attr = getattr(self._target, name)
        if callable(attr) and not inspect.isclass(attr):
            def _wrapped(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
                result = attr(*args, **kwargs)
                if inspect.isawaitable(result):
                    return self._bridge._call(result)
                # A method that returns a NESTED facade sub-client (e.g.
                # ``recordings.visual(session_id)`` -> VisualRecordingClient) must
                # itself be bridged so its ``async def`` methods
                # (``.start()`` / ``.stop()`` / ``.frames()``) also block and
                # return results directly on the sync client. Detect a facade
                # sub-client by its ``_core`` handle and wrap it. Async generators
                # (``watch()``) stay async — streaming is inherently async.
                if not inspect.isasyncgen(result) and hasattr(result, "_core"):
                    return _SyncSubClient(self._bridge, result)
                return result
            return _wrapped
        return attr

    def __repr__(self) -> str:
        return f"_SyncSubClient({type(self._target).__name__})"


class SyncGhostCrawl:
    """Synchronous GhostCrawl client (the default ``GhostCrawl`` / ``Client``).

    Mirrors :class:`ghostcrawl.facade.GhostCrawlClient` method-for-method, but
    every method blocks and returns the resolved value instead of a coroutine::

        from ghostcrawl import GhostCrawl

        client = GhostCrawl(token="gck_live_YOUR_KEY")
        result = client.scrape("https://example.com")
        print(result["markdown"])          # no await, no asyncio.run
        client.close()

    Works inside a running event loop (Jupyter, an async app) without raising —
    the async work runs on a private background loop, not the caller's loop.

    Use it as a context manager for deterministic cleanup::

        with GhostCrawl(token="gck_live_YOUR_KEY") as client:
            print(client.scrape("https://example.com")["markdown"])

    Constructor parameters are identical to
    :class:`~ghostcrawl.facade.GhostCrawlClient` (``token`` / ``api_key`` /
    ``base_url`` / ``provider_config``). Prefer the async twin
    :class:`~ghostcrawl.facade.GhostCrawlClient` (exported as ``AsyncGhostCrawl``)
    when you are already inside ``async def`` code and want to ``await`` directly.
    """

    def __init__(
        self,
        *args: typing.Any,
        _async_client: _AsyncGhostCrawlClient | None = None,
        **kwargs: typing.Any,
    ) -> None:
        # One long-lived event loop on a private daemon thread. Daemon so a
        # forgotten ``close()`` never blocks interpreter exit; the
        # explicit ``close()`` / context-manager exit stops+joins it cleanly.
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._loop.run_forever,
            name="ghostcrawl-sync-loop",
            daemon=True,
        )
        self._thread.start()
        self._closed = False
        # Reuse the delegating async facade verbatim — no duplicated transport.
        # ``_async_client`` lets ``with_retries`` wrap an already-built facade.
        self._async = _async_client or _AsyncGhostCrawlClient(*args, **kwargs)

    # ------------------------------------------------------------------
    # Bridge core
    # ------------------------------------------------------------------

    def _call(self, coro: typing.Coroutine[typing.Any, typing.Any, typing.Any]) -> typing.Any:
        """Run ``coro`` on the private loop-thread and block for its result.

        Uses ``run_coroutine_threadsafe`` (never ``asyncio.run``) so this is
        safe to call from inside another running event loop.
        """
        if self._closed:
            raise RuntimeError("SyncGhostCrawl is closed")
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the underlying HTTP client and stop the background loop/thread."""
        self._shutdown(graceful=True)

    def _shutdown(self, graceful: bool) -> None:
        """Stop the loop/thread; optionally close the HTTP client gracefully first.

        The graceful async ``aclose()`` round-trip is BOUNDED (``fut.result``
        timeout) so a wedged transport can never hang an explicit ``close()`` /
        context-manager exit. The finalizer path (``graceful=False``) skips the
        round-trip entirely: at interpreter shutdown the daemon loop-thread may
        already be stopping, an unbounded ``fut.result()`` there blocks forever,
        and the OS reclaims the socket on exit regardless. Skipping it kills the
        "plain quickstart script hangs on exit" footgun (no context manager
        in the canonical quickstart).
        """
        if self._closed:
            return
        self._closed = True
        if graceful:
            try:
                if self._loop.is_running():
                    fut = asyncio.run_coroutine_threadsafe(self._async.aclose(), self._loop)
                    fut.result(timeout=10)
            except Exception:  # noqa: BLE001 — best-effort cleanup; still stop the loop
                pass
        try:
            self._loop.call_soon_threadsafe(self._loop.stop)
        except Exception:  # noqa: BLE001 — loop may already be torn down at shutdown
            pass
        self._thread.join(timeout=5)

    def __enter__(self) -> SyncGhostCrawl:
        return self

    def __exit__(self, *_: typing.Any) -> None:
        self.close()

    def __del__(self) -> None:  # pragma: no cover - best-effort finalizer
        try:
            self._shutdown(graceful=False)
        except Exception:  # noqa: BLE001
            pass

    def __repr__(self) -> str:  # never leak the token
        return f"SyncGhostCrawl(base_url={self._async.base_url!r})"

    # ------------------------------------------------------------------
    # Sub-client passthrough — each is wrapped in a blocking proxy so the sync
    # client's sub-client methods (``client.sessions.create(...)`` etc.) return
    # results directly, never bare coroutines (sync-first).
    # ------------------------------------------------------------------

    @property
    def crawl_runs(self) -> typing.Any:
        return _SyncSubClient(self, self._async.crawl_runs)

    @property
    def sessions(self) -> typing.Any:
        return _SyncSubClient(self, self._async.sessions)

    @property
    def profiles(self) -> typing.Any:
        return _SyncSubClient(self, self._async.profiles)

    @property
    def webhooks(self) -> typing.Any:
        return _SyncSubClient(self, self._async.webhooks)

    @property
    def schedules(self) -> typing.Any:
        return _SyncSubClient(self, self._async.schedules)

    @property
    def datasets(self) -> typing.Any:
        return _SyncSubClient(self, self._async.datasets)

    @property
    def recordings(self) -> typing.Any:
        return _SyncSubClient(self, self._async.recordings)

    @property
    def kv(self) -> typing.Any:
        return _SyncSubClient(self, self._async.kv)

    @property
    def cdp(self) -> typing.Any:
        return _SyncSubClient(self, self._async.cdp)

    @property
    def page(self) -> typing.Any:
        return _SyncSubClient(self, self._async.page)

    @property
    def downloads(self) -> typing.Any:
        return _SyncSubClient(self, self._async.downloads)

    @property
    def storage_states(self) -> typing.Any:
        return _SyncSubClient(self, self._async.storage_states)

    @property
    def base_url(self) -> str:
        return self._async.base_url

    # ------------------------------------------------------------------
    # Core operations — one delegating line each (mirror the async facade).
    # ``wait`` for search/crawl flows through **kwargs unchanged.
    # ------------------------------------------------------------------

    def scrape(self, url: str, **kwargs: typing.Any) -> typing.Any:
        """Scrape a single URL and return the rendered content (sync)."""
        return self._call(self._async.scrape(url, **kwargs))

    def scrape_batch(self, urls: list, **kwargs: typing.Any) -> typing.Any:
        """Scrape many URLs in one request (sync)."""
        return self._call(self._async.scrape_batch(urls, **kwargs))

    def search_job(self, job_id: str) -> typing.Any:
        """Poll a queued async search job to terminal (sync)."""
        return self._call(self._async.search_job(job_id))

    def crawl_status(self, run_id: str) -> typing.Any:
        """Get a deep-crawl run's status (sync)."""
        return self._call(self._async.crawl_status(run_id))

    def search(self, query: str, **kwargs: typing.Any) -> typing.Any:
        """Search the web and return results (sync). ``wait=True`` by default."""
        return self._call(self._async.search(query, **kwargs))

    def extract(self, url: str, **kwargs: typing.Any) -> typing.Any:
        """Scrape + structured extraction against a schema (sync)."""
        return self._call(self._async.extract(url, **kwargs))

    def crawl(self, url: str, **kwargs: typing.Any) -> typing.Any:
        """Start (and optionally ``wait`` for) a deep crawl (sync)."""
        return self._call(self._async.crawl(url, **kwargs))

    def map(self, url: str, **kwargs: typing.Any) -> typing.Any:
        """Map all URLs reachable from a seed URL (sync)."""
        return self._call(self._async.map(url, **kwargs))

    def agent(self, **kwargs: typing.Any) -> typing.Any:
        """Execute an agent task (sync)."""
        return self._call(self._async.agent(**kwargs))

    def pdf(self, url: str, **kwargs: typing.Any) -> typing.Any:
        """Render a URL to PDF bytes (sync)."""
        return self._call(self._async.pdf(url, **kwargs))

    def screenshot(self, url: str, **kwargs: typing.Any) -> typing.Any:
        """Capture a screenshot as image bytes (sync)."""
        return self._call(self._async.screenshot(url, **kwargs))

    def content(self, url: str, **kwargs: typing.Any) -> typing.Any:
        """Fetch the rendered content of a URL as a dict (sync)."""
        return self._call(self._async.content(url, **kwargs))

    def me(self) -> typing.Any:
        """Return the caller's account profile — ``GET /v1/me`` (sync)."""
        return self._call(self._async.me())

    def usage(self, **kwargs: typing.Any) -> typing.Any:
        """Return the caller's usage + quota report — ``GET /v1/me/usage`` (sync)."""
        return self._call(self._async.usage(**kwargs))

    def with_retries(self, n: int) -> SyncGhostCrawl:
        """Return a NEW sync client with the same config and a retry budget.

        Mirrors :meth:`GhostCrawlClient.with_retries` — wraps the fresh async
        facade in its own sync loop-thread bridge.
        """
        return SyncGhostCrawl(_async_client=self._async.with_retries(n))
