"""Typed-but-dict-accessible result models for the GhostCrawl SDK.

This is the **canonical reference implementation** the six non-Python SDKs
mirror. The per-lane field names are the single source of truth in
``parity/sdk_surface_contract.json`` (``lanes.*``) and MUST be byte-identical
across all seven SDKs. Pure stdlib — **no pydantic**, no new runtime dependency
(operator directive "wire our own with what we have"; RESEARCH Standard Stack).

Every result is BOTH:

* attribute-accessible — ``result.markdown`` / ``result.status`` / ``result.content``
* dict-accessible      — ``result["markdown"]`` / ``result["status"]``

so existing callers that treat a result as a plain ``dict`` keep working
unchanged (back-compat), while new code gets discoverable typed attributes.

The raw kiota ``_generated/`` models are NEVER returned to the user; the
facade wraps every response into one of these owned types.
"""

from __future__ import annotations

import collections.abc
import typing

__all__ = [
    "ScrapeResult",
    "SearchResult",
    "CrawlRun",
    "Document",
    "BinaryResult",
    "wrap_scrape",
    "wrap_search",
    "wrap_crawl",
    "wrap_document",
    "wrap_binary",
]


def _surface_content(data: dict) -> None:
    """Mirror the rendered output under the documented ``content`` key, in place.

    Semantics are identical to ``facade._normalize_scrape_content``: surface the
    format-specific rendered field (``markdown`` / ``html`` / ``text``) under
    ``content`` so the quickstart works regardless of ``format`` — without
    dropping the format-specific key. Kept here (not imported from ``facade``) so
    this module stays free of the kiota-dependent facade import chain.
    """
    if not isinstance(data, dict) or "content" in data:
        return
    fmt = data.get("format")
    value = data.get(fmt) if isinstance(fmt, str) else None
    if not isinstance(value, str):
        for key in ("markdown", "html", "text"):
            candidate = data.get(key)
            if isinstance(candidate, str):
                value = candidate
                break
    if isinstance(value, str):
        data["content"] = value


class _MappingResult(collections.abc.Mapping):
    """Base: an immutable ``Mapping`` over a response dict with attribute access.

    Subclasses declare the canonical lane field names in ``_FIELDS``; those
    become attributes that read straight from the underlying payload (returning
    ``None`` when absent). Any key present in the payload is ALSO reachable by
    dict access even when it is not a declared field, so unknown / extra server
    fields are never lost.
    """

    #: Canonical lane field names (from parity/sdk_surface_contract.json).
    _FIELDS: tuple[str, ...] = ()

    def __init__(
        self, data: typing.Mapping[str, typing.Any] | None = None
    ) -> None:
        self._data: dict = dict(data) if data else {}

    # -- Mapping protocol (dict access) ------------------------------------
    def __getitem__(self, key: str) -> typing.Any:
        return self._data[key]

    def __iter__(self) -> typing.Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    # -- attribute access ---------------------------------------------------
    def __getattr__(self, name: str) -> typing.Any:
        # Only reached when normal attribute lookup fails. Declared lane fields
        # resolve to the payload value (or None); anything else is an error.
        # The leading-underscore guard prevents recursion when ``_data`` is not
        # yet set (e.g. during copy / unpickle).
        if name.startswith("_"):
            raise AttributeError(name)
        if name in type(self)._FIELDS:
            return self._data.get(name)
        raise AttributeError(f"{type(self).__name__!r} object has no attribute {name!r}")

    # -- ergonomics ---------------------------------------------------------
    def to_dict(self) -> dict:
        """Return a shallow copy of the underlying response dict."""
        return dict(self._data)

    def __repr__(self) -> str:
        shown = {k: self._data[k] for k in type(self)._FIELDS if k in self._data}
        extra = len(self._data) - len(shown)
        suffix = f", +{extra} more" if extra > 0 else ""
        return f"{type(self).__name__}({shown!r}{suffix})"


class ScrapeResult(_MappingResult):
    """Result of ``scrape`` / ``content`` — parity lane ``scrape``.

    Canonical fields: ``status``, ``content``, ``markdown``, ``html``,
    ``status_code``, ``bytes``, ``url``, ``format``, ``warnings``. ``content`` is
    the cross-format alias for the rendered output, surfaced on construction.
    """

    _FIELDS = (
        "status",
        "content",
        "markdown",
        "html",
        "status_code",
        "bytes",
        "url",
        "format",
        "warnings",
    )

    def __init__(
        self, data: typing.Mapping[str, typing.Any] | None = None
    ) -> None:
        super().__init__(data)
        _surface_content(self._data)


class SearchResult(_MappingResult):
    """Result of ``search`` — parity lane ``search`` (``status``, ``results``, ``query``)."""

    _FIELDS = ("status", "results", "query")

    def __init__(
        self, data: typing.Mapping[str, typing.Any] | None = None
    ) -> None:
        super().__init__(data)
        # The ``/v1/search`` payload carries the hit list under ``items``; the
        # SDK's canonical parity field is ``results``. Surface ``results`` as an
        # alias so ``result.results`` / ``result["results"]`` work as documented,
        # while the raw ``items`` key stays accessible for anyone who wants it.
        if "results" not in self._data and "items" in self._data:
            self._data["results"] = self._data["items"]
        # STABLE SHAPE GUARANTEE (LAUNCH hardening): a ``search`` result is NEVER
        # a surprise shape — even a client-poll that timed out before the job
        # reached terminal (the cold-rotation 202 handle: ``{status:"running",
        # job_id, poll_url,...}`` with no ``items``) still exposes ``results`` (an
        # empty list), ``query`` and ``status`` by BOTH dict- and attribute-access.
        # Without this, ``result["results"]`` / ``result["query"]`` raised
        # ``KeyError`` on the timed-out handle. The facade injects the real
        # ``query``/``engine`` before wrapping; these defaults are the last line so
        # any construction path (``wait=False``, direct ``wrap_search``) is safe.
        if self._data.get("results") is None:
            self._data["results"] = []
        self._data.setdefault("query", None)
        self._data.setdefault("status", None)


class CrawlRun(_MappingResult):
    """A crawl run — parity lane ``crawl`` (``run_id``, ``status``, ``results``)."""

    _FIELDS = ("run_id", "status", "results")


class Document(_MappingResult):
    """A single crawled/searched document — parity lane ``document``."""

    _FIELDS = ("title", "url", "content")


class BinaryResult(bytes):
    """Binary lane result (``pdf`` / ``screenshot``) — parity lane ``pdf`` / ``screenshot``.

    A GENUINE ``bytes`` object (full back-compat: ``f.write(result)`` / slicing /
    ``len()`` all still work exactly as before) that is ALSO attribute- and
    dict-accessible via ``.bytes`` / ``.content_type`` and
    ``result["bytes"]`` / ``result["content_type"]`` — so binary lanes read
    uniformly with the other typed results.
    """

    _content_type: str | None

    def __new__(
        cls,
        data: bytes | bytearray | None = b"",
        *,
        content_type: str | None = None,
    ) -> BinaryResult:
        raw = bytes(data) if data is not None else b""
        obj = super().__new__(cls, raw)
        obj._content_type = content_type
        return obj

    @property
    def bytes(self) -> bytes:  # noqa: A003 - canonical parity field name
        """The raw binary payload as plain ``bytes``."""
        return bytes(self)

    @property
    def content_type(self) -> str | None:
        """The response ``Content-Type`` (e.g. ``application/pdf``)."""
        return self._content_type

    def __getitem__(self, key: typing.Any) -> typing.Any:
        # String keys expose the parity fields; int / slice keep normal bytes
        # indexing behavior.
        if key == "bytes":
            return bytes(self)
        if key == "content_type":
            return self._content_type
        return super().__getitem__(key)

    def to_dict(self) -> dict:
        return {"bytes": bytes(self), "content_type": self._content_type}

    def __repr__(self) -> str:
        return (
            f"BinaryResult(<{len(self)} bytes>, content_type={self._content_type!r})"
        )


# ---------------------------------------------------------------------------
# Wrap helpers — the facade calls these on the raw dict/bytes so the raw
# generated model is never returned to the user. Idempotent: an already
# wrapped value passes through unchanged.
# ---------------------------------------------------------------------------


def wrap_scrape(data: typing.Any) -> typing.Any:
    if isinstance(data, ScrapeResult) or not isinstance(data, collections.abc.Mapping):
        return data
    return ScrapeResult(data)


def wrap_search(data: typing.Any) -> typing.Any:
    if isinstance(data, SearchResult) or not isinstance(data, collections.abc.Mapping):
        return data
    return SearchResult(data)


def wrap_crawl(data: typing.Any) -> typing.Any:
    if isinstance(data, CrawlRun) or not isinstance(data, collections.abc.Mapping):
        return data
    return CrawlRun(data)


def wrap_document(data: typing.Any) -> typing.Any:
    if isinstance(data, Document) or not isinstance(data, collections.abc.Mapping):
        return data
    return Document(data)


def wrap_binary(
    data: bytes | bytearray | None,
    content_type: str | None = None,
) -> BinaryResult:
    if isinstance(data, BinaryResult):
        return data
    return BinaryResult(data or b"", content_type=content_type)
