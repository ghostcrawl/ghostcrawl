"""Batch scrape runner for the ghostcrawl CLI.

A resumable, plan-aware, machine-readable batch surface over the existing
single-URL ``/v1/scrape`` lane: read an input file of URLs, scrape them
concurrently (bounded by the plan cap fetched from ``/v1/usage``), write one
NDJSON line per URL to an output directory, and record a checkpoint so a
``--resume`` run can skip already-completed URLs.

Attribution (no Frankenstein):
    Adapted from the upstream CLI batch mode — its ``run_batch_async`` /
    ``resolve_batch_concurrency`` technique.
    NOTHING is copied: this module is rewritten in ghostcrawl style — typer +
    the existing ``_get_client`` / ``_emit`` / ``_to_dict`` helpers, an
    ``asyncio.Semaphore`` fan-out, Bearer auth (never query-string auth), the
    ``/v1/usage`` plan cap, and a ``~/.ghostcrawl/`` checkpoint path (never the
    upstream config dir, never any upstream header prefix or proxy-bundle name).
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Optional


# ---------------------------------------------------------------------------
# Concurrency resolution
# ---------------------------------------------------------------------------

def resolve_concurrency(usage: dict, requested: int) -> int:
    """Resolve the effective batch concurrency from a ``/v1/usage`` report.

    The ``/v1/usage`` response has NO guaranteed concurrency field (it is a
    usage/cost rollup), so a missing cap is a NORMAL path, not an error. Probe
    the dict defensively for, in order:
        ``concurrency`` → ``max_concurrency`` →
        nested ``limits.concurrency`` → nested ``plan.concurrency``.
    If none are present, fall back to the caller's ``requested`` value.

    Always returns ``min(cap, requested)`` so the operator may voluntarily run
    below the cap but can never exceed it.
    """
    cap: Optional[int] = None
    if isinstance(usage, dict):
        for key in ("concurrency", "max_concurrency"):
            val = usage.get(key)
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                cap = int(val)
                break
        if cap is None:
            for parent in ("limits", "plan"):
                nested = usage.get(parent)
                if isinstance(nested, dict):
                    val = nested.get("concurrency")
                    if isinstance(val, (int, float)) and not isinstance(val, bool):
                        cap = int(val)
                        break
    if cap is None:
        cap = requested
    return max(1, min(cap, requested))


# ---------------------------------------------------------------------------
# Checkpoint file handling
# ---------------------------------------------------------------------------

def checkpoint_path(input_file: Path) -> Path:
    """Return ``~/.ghostcrawl/batch-checkpoint-<job-id>.json`` for *input_file*.

    ``<job-id>`` is a stable 16-hex-char SHA-256 of the resolved absolute input
    path, so the same input file always maps to the same checkpoint (enabling
    ``--resume``) while different input files never collide. The parent dir is
    created if absent.
    """
    job_id = hashlib.sha256(str(input_file.resolve()).encode()).hexdigest()[:16]
    base = Path.home() / ".ghostcrawl"
    base.mkdir(parents=True, exist_ok=True)
    return base / f"batch-checkpoint-{job_id}.json"


def load_checkpoint(path: Path) -> set[str]:
    """Return the set of completed URLs recorded in *path*.

    Tolerates a missing or corrupt/unreadable file by returning an empty set —
    a fresh run simply has no checkpoint yet.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, ValueError):
        return set()
    completed = data.get("completed") if isinstance(data, dict) else None
    if isinstance(completed, list):
        return {str(u) for u in completed}
    return set()


def _write_checkpoint(path: Path, completed: set[str]) -> None:
    """Atomically rewrite the checkpoint file with the current completed set."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps({"completed": sorted(completed)}), encoding="utf-8")
    tmp.replace(path)


# ---------------------------------------------------------------------------
# URL parsing
# ---------------------------------------------------------------------------

def _read_urls(input_file: Path) -> list[str]:
    """One URL per line; strip whitespace; skip blank lines and ``#`` comments."""
    urls: list[str] = []
    for raw in input_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(line)
    return urls


async def _read_usage(client: Any) -> dict:
    """Read the usage report from the client.

    Calls ``client.usage()`` (awaiting it when it returns a coroutine, as the
    canonical async client does). Returns ``{}`` on any failure so a missing
    cap field degrades to the ``--concurrency`` fallback.
    """
    try:
        if not hasattr(client, "usage"):
            return {}
        result = client.usage()
        if asyncio.iscoroutine(result):
            result = await result
    except Exception:
        return {}
    if hasattr(result, "model_dump"):
        result = result.model_dump()
    return result if isinstance(result, dict) else {}


# ---------------------------------------------------------------------------
# The batch runner
# ---------------------------------------------------------------------------

def _to_dict(obj: object) -> object:
    """Local copy of main.py's _to_dict (avoids a circular import at module load)."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if isinstance(obj, list):
        return [_to_dict(item) for item in obj]
    return obj


async def run_batch(
    *,
    input_file: Path,
    output_dir: Path,
    concurrency: int,
    resume: bool,
    client_factory: Callable[[], Any],
) -> dict:
    """Scrape every URL in *input_file* concurrently and emit NDJSON results.

    The Typer command owns the event-loop entry (``asyncio.run``); this coroutine
    stays unit-testable with an injected ``client_factory`` (the real CLI passes
    ``_get_client``; tests pass a fake/respx-backed client).

    Returns a summary dict: ``{total, completed, failed, skipped, concurrency,
    output}``.
    """
    client = client_factory()

    usage = await _read_usage(client)
    effective_cap = resolve_concurrency(usage, concurrency)

    all_urls = _read_urls(input_file)
    cp_path = checkpoint_path(input_file)
    already_done = load_checkpoint(cp_path) if resume else set()
    work = [u for u in all_urls if u not in already_done]
    skipped = len(all_urls) - len(work)

    output_dir.mkdir(parents=True, exist_ok=True)
    results_path = output_dir / "results.ndjson"

    completed: set[str] = set(already_done)
    counters = {"completed": 0, "failed": 0}

    # Open in append mode so a --resume run extends the prior NDJSON file.
    # The context manager unconditionally closes the handle, so no early
    # failure between open and gather can leak the file descriptor (WR-05).
    with results_path.open("a", encoding="utf-8") as fh:
        semaphore = asyncio.Semaphore(effective_cap)
        write_lock = asyncio.Lock()

        async def _maybe_await(value: Any) -> Any:
            if asyncio.iscoroutine(value):
                return await value
            return value

        async def _scrape_one(url: str) -> None:
            async with semaphore:
                try:
                    res = await _maybe_await(
                        client.scrape(
                            url=url,
                            render_js=False,
                            country="us",
                            output_format="html",
                        )
                    )
                    line = json.dumps({"url": url, "result": _to_dict(res)}, default=str)
                    marked = True
                except Exception as exc:  # noqa: BLE001 — a failed URL must not abort the batch
                    line = json.dumps(
                        {"url": url, "error": f"{type(exc).__name__}: {exc}"}, default=str
                    )
                    marked = False
                async with write_lock:
                    fh.write(line + "\n")
                    fh.flush()
                    if marked:
                        completed.add(url)
                        counters["completed"] += 1
                        _write_checkpoint(cp_path, completed)
                    else:
                        counters["failed"] += 1

        await asyncio.gather(*(_scrape_one(u) for u in work))

    return {
        "total": len(all_urls),
        "completed": counters["completed"],
        "failed": counters["failed"],
        "skipped": skipped,
        "concurrency": effective_cap,
        "output": str(results_path),
    }
