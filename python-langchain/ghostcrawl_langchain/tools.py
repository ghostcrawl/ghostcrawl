"""LangChain BaseTool subclasses for GhostCrawl REST endpoints.

Auth: Authorization: Bearer <token>.

- _handle_error maps httpx.HTTPStatusError to GhostCrawl* domain subclasses.
- All _run() bodies wrap the httpx call in try/except -> _handle_error.
- All _arun() bodies use httpx.AsyncClient.
"""
from __future__ import annotations

import ast
import json
from typing import Any, Dict, NoReturn, Optional, Type
from urllib.parse import parse_qs

import httpx
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, field_validator

from ._client import get_async_client, get_client
from .codes import ALL_CODES, RESULT_CODES, STATUS_TO_CODE, is_retryable
from .errors import (
    GhostCrawlAuthError,
    GhostCrawlError,
    GhostCrawlInvalidRequestError,
    GhostCrawlQuotaError,
    GhostCrawlRateLimitError,
    GhostCrawlServerError,
)


# ---------------------------------------------------------------------------
# Error mapping (PROBLEM channel → raise) — the hard-failure path
# ---------------------------------------------------------------------------

def _problem_fields(resp: httpx.Response) -> tuple[Optional[str], Optional[int], Optional[str]]:
    """Pull (code, retry_after, request_id) from a problem+json body, if present.

    The canonical ``code`` (preferred over status) rides on the response body;
    ``instance`` carries the request id; ``retry_after`` may be in the body or
    the ``Retry-After`` header.
    """
    code: Optional[str] = None
    retry_after: Optional[int] = None
    request_id: Optional[str] = None
    try:
        body = resp.json()
    except (json.JSONDecodeError, ValueError):
        body = None
    if isinstance(body, dict):
        bc = body.get("code")
        if isinstance(bc, str) and bc in ALL_CODES:
            code = bc
        request_id = body.get("instance") or body.get("request_id")
        if isinstance(body.get("retry_after"), int):
            retry_after = body["retry_after"]
    if retry_after is None:
        raw = resp.headers.get("Retry-After")
        try:
            retry_after = int(raw) if raw is not None else None
        except (TypeError, ValueError):
            retry_after = None
    return code, retry_after, request_id


def _handle_error(exc: httpx.HTTPStatusError) -> NoReturn:
    """Map an ``httpx.HTTPStatusError`` to the right ``GhostCrawl*`` subclass.

    This is the PROBLEM-channel (OUR-failure) path: a non-2xx response is always
    re-raised as a typed exception, so the agent sees a hard failure. Mapping is
    kept lock-step across the official SDKs (see ``errors.py`` and
    ``sdks/node/src/errors.ts``): it prefers the canonical problem+json ``code``,
    falling back to the HTTP status — 401 → auth, 402 → quota,
    429 → rate-limit (with ``retry_after``), 400/422 → invalid-request,
    5xx → retryable server error, anything else → generic ``GhostCrawlError``.
    """
    status = exc.response.status_code
    body = exc.response.text
    code, retry_after, request_id = _problem_fields(exc.response)
    if code is None:
        code = STATUS_TO_CODE.get(status)

    if code == "unauthorized" or status == 401:
        raise GhostCrawlAuthError(
            f"401 Unauthorized: {body}", code=code, request_id=request_id
        ) from exc
    if code == "payment_required" or status == 402:
        raise GhostCrawlQuotaError(
            f"402 Payment Required: {body}", code=code, request_id=request_id
        ) from exc
    if code == "rate_limited" or status == 429:
        raise GhostCrawlRateLimitError(
            f"429 Too Many Requests: {body}",
            retry_after=retry_after,
            code=code,
            request_id=request_id,
        ) from exc
    if code in ("bad_request", "byo_proxy_invalid", "tier_unavailable") or status in (400, 422):
        raise GhostCrawlInvalidRequestError(
            f"{status} Invalid Request: {body}", code=code, request_id=request_id
        ) from exc
    if 500 <= status < 600:
        raise GhostCrawlServerError(
            f"{status} Server Error: {body}",
            code=code,
            retryable=True,
            request_id=request_id,
        ) from exc
    raise GhostCrawlError(
        f"{status} HTTP error: {body}", code=code, retryable=is_retryable(code), request_id=request_id
    ) from exc


# ---------------------------------------------------------------------------
# Result annotation (RESULT channel → embed code in the LLM-visible text)
# ---------------------------------------------------------------------------

def _annotate_result(text: str) -> str:
    """Make a TARGET failure legible to the agent in the returned text.

    On a 200 response the body may report ``ok: false`` + a ``result_error``
    (the site blocked us, presented a CAPTCHA, returned an HTTP error, could not
    be reached, or had no extractable content). Returning that raw JSON makes the
    agent treat a failed scrape as a success. Instead we prepend a single,
    machine-readable advisory line carrying the canonical ``code``, whether it is
    ``retryable``, the recommended next action, and any ``target_status`` — so
    the LLM can reason about it (e.g. rotate identity on ``blocked``). A clean
    success is returned unchanged.
    """
    try:
        body = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return text
    if not isinstance(body, dict):
        return text

    # The scrape/extract/crawl APIs wrap per-URL results in a `results` envelope
    # ({"status": ..., "results": [{ok, result_error, code, target_status, ...}]});
    # the target failure lives on the INNER result, not the envelope top level
    # (which carries only status="failed" and no code). Without descending here
    # the advisory came out as code=None / target_status=None. Mirror the SDK
    # facades' results[] descent: inspect the first failing inner result, falling
    # back to the first result. The flat markdown-build envelope (no `results`)
    # keeps its top-level result_error/status="failed" path unchanged.
    inner = body.get("results")
    if isinstance(inner, list) and inner:
        failing = next(
            (
                item
                for item in inner
                if isinstance(item, dict)
                and (
                    isinstance(item.get("result_error"), dict)
                    or item.get("ok") is False
                    or item.get("status") == "failed"
                    or (isinstance(item.get("code"), str) and item["code"] in RESULT_CODES)
                )
            ),
            None,
        )
        if failing is not None:
            body = failing
        elif isinstance(inner[0], dict):
            # No inner failure signalled — a clean multi-result success.
            return text

    result_error = body.get("result_error")
    top_code = body.get("code")
    ok = body.get("ok")

    code: Optional[str] = None
    retryable = False
    target_status: Optional[int] = None
    reason: Optional[str] = None

    if isinstance(result_error, dict):
        code = result_error.get("code") or (top_code if isinstance(top_code, str) else None)
        retryable = bool(result_error.get("retryable"))
        ts = result_error.get("target_status")
        target_status = ts if isinstance(ts, int) else None
        reason = result_error.get("reason")
    elif ok is False and isinstance(top_code, str) and top_code in RESULT_CODES:
        code = top_code
        retryable = is_retryable(code)
        ts = body.get("target_status")
        target_status = ts if isinstance(ts, int) else None
    elif body.get("status") == "failed":
        # The flat markdown-build envelope reports a target failure ONLY via
        # status="failed" (no ok/result_error) — annotate it, never silent success.
        code = top_code if isinstance(top_code, str) else None
        ts = body.get("target_status")
        target_status = ts if isinstance(ts, int) else None
    else:
        return text

    retryable = retryable or is_retryable(code)
    if code in ("blocked", "captcha_required"):
        action = "retry with a different identity/proxy"
    elif retryable:
        action = "retry"
    else:
        action = "do not retry the same request"
    parts = [
        f"code={code}",
        f"retryable={'true' if retryable else 'false'}",
        f"action={action}",
    ]
    if target_status is not None:
        parts.append(f"target_status={target_status}")
    if reason:
        parts.append(f"reason={reason}")
    advisory = "GHOSTCRAWL_ERROR: " + " ".join(parts)
    return f"{advisory}\n{text}"


# ---------------------------------------------------------------------------
# Input schemas
# ---------------------------------------------------------------------------

def _coerce_scalar(raw: Any) -> Any:
    """Narrow a URL ``k=v`` value to bool/int when it matches exactly.

    Pure value-narrowing — no ``eval``, no attribute access. Lists (repeated
    keys) and anything that is not an exact true/false/digit-string pass
    through unchanged as inert values.
    """
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        low = raw.lower()
        if low == "true":
            return True
        if low == "false":
            return False
        if raw.isdigit():
            return int(raw)
    return raw


class _GhostCrawlBaseInput(BaseModel):
    """Shared base carrying the single 3-stage ``params`` coercion validator.

    Merged into ONE base class so every params-bearing tool input inherits the
    same coercion — replacing five independent JSON-only ``_coerce_params``
    validators.

    Stage 2 uses ``ast.literal_eval`` which is literal-only (dict/list/str/
    num/bool/None): it never executes code, calls functions, or imports. A
    call-expression string is rejected by the literal stage and (lacking
    ``=``) falls through stage 3 to ``{}`` — never executing attacker input.

    The validator is declared ``check_fields=False`` so this base (and any
    subclass without a ``params`` field, e.g. ``_EmptyInput``) imports without
    a PydanticUserError.
    """

    @field_validator("params", mode="before", check_fields=False)
    @classmethod
    def _coerce_params(cls, v: Any) -> dict:
        if isinstance(v, dict):
            return v
        if not isinstance(v, str):
            return v or {}
        s = v.strip()
        if not s:
            return {}

        # Stage 1 — JSON object string ({"render_js": true}).
        try:
            parsed = json.loads(s)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, ValueError):
            pass

        # Stage 2 — Python-literal dict string ({'render_js': True}).
        # literal-only via ast.literal_eval: no code execution / no imports.
        try:
            literal = ast.literal_eval(s)
            if isinstance(literal, dict):
                return literal
        except (ValueError, SyntaxError, TypeError):
            pass

        # Stage 3 — URL k=v string (screenshot=true&wait=3000).
        if "=" in s:
            parsed_qs = parse_qs(s, keep_blank_values=True)
            return {
                key: _coerce_scalar(vals[0] if len(vals) == 1 else vals)
                for key, vals in parsed_qs.items()
            }
        return {}


class _ScrapeInput(_GhostCrawlBaseInput):
    url: str = Field(..., description="URL to scrape (http/https).")
    render_js: bool = Field(
        False,
        description="Execute JavaScript before extraction. Required for SPAs and lazy-loaded content.",
    )
    output_format: str = Field(
        "markdown",
        description="Content format to return: 'html' returns raw HTML; 'markdown' returns cleaned Markdown.",
    )
    params: dict = Field(
        default_factory=dict,
        description=(
            "Extra /v1/scrape parameters as a dict or JSON string. "
            "Supported keys: wait_for (CSS selector), extract_schema (JSON schema object), "
            "country (ISO 3166-1 alpha-2), screenshot (bool), full_page (bool), "
            "screenshot_selector (CSS selector for element-scoped capture)."
        ),
    )


class _SearchInput(_GhostCrawlBaseInput):
    query: str = Field(..., description="Search query string.")
    engine: str = Field(
        "brave",
        description="Search engine: 'brave' or 'tavily'. Requires your own provider API key via X-Provider-Authorization.",
    )
    limit: int = Field(
        10,
        ge=1,
        le=20,
        description="Maximum number of results to return (1–20).",
    )
    provider_key: Optional[str] = Field(
        None,
        description=(
            "Your own search-backend API key (BYO; ghostcrawl charges no markup). "
            "Sent as the X-Provider-Authorization: Bearer <key> header /v1/search "
            "requires. Without it the API replies 401 search_backend_key_missing."
        ),
    )
    params: dict = Field(
        default_factory=dict,
        description="Extra /v1/search parameters as a dict or JSON string.",
    )


class _ExtractInput(_GhostCrawlBaseInput):
    url: str = Field(..., description="URL to extract structured data from (http/https).")
    schema_: dict = Field(
        default_factory=dict,
        description=(
            "JSON Schema object describing the fields to extract. "
            "Example: {\"type\": \"object\", \"properties\": {\"title\": {\"type\": \"string\"}}}. "
            "When omitted, ghostcrawl returns the full page content."
        ),
    )
    params: dict = Field(
        default_factory=dict,
        description="Extra /v1/extract parameters as a dict or JSON string.",
    )

    @field_validator("schema_", mode="before")
    @classmethod
    def _coerce_schema(cls, v: Any) -> dict:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, ValueError) as e:
                raise ValueError(f"schema must be valid JSON: {e}") from e
        return v or {}


class _CrawlInput(_GhostCrawlBaseInput):
    url: str = Field(..., description="Seed URL to start crawling from (http/https).")
    max_pages: int = Field(
        10,
        ge=1,
        le=500,
        description="Maximum number of pages to crawl from the seed URL (1–500).",
    )
    same_origin: bool = Field(
        True,
        description="Restrict crawl to the same origin (scheme + host + port). Disable to follow cross-origin links.",
    )
    params: dict = Field(
        default_factory=dict,
        description="Extra /v1/crawl parameters as a dict or JSON string.",
    )


class _ContentInput(_GhostCrawlBaseInput):
    url: str = Field(..., description="URL to fetch rendered content from (http/https).")
    params: dict = Field(
        default_factory=dict,
        description="Extra /v1/content parameters as a dict or JSON string (e.g. engine, format).",
    )


class _MapInput(_GhostCrawlBaseInput):
    url: str = Field(..., description="Seed URL whose reachable links to discover (http/https).")
    params: dict = Field(
        default_factory=dict,
        description="Extra /v1/map parameters as a dict or JSON string.",
    )


class _GoogleSearchInput(_GhostCrawlBaseInput):
    query: str = Field(..., description="Google search query string.")
    country: str = Field(
        "us",
        description="ISO 3166-1 alpha-2 country code for regional Google SERP results.",
    )
    params: dict = Field(
        default_factory=dict,
        description="Extra /v1/google/search parameters as a dict or JSON string.",
    )


class _GoogleHotelsInput(_GhostCrawlBaseInput):
    """Args for the Google Hotels SERP tool.

    Inherits ``_GhostCrawlBaseInput`` so the shared
    3-stage ``params`` coercion validator applies — no per-class validator.
    """

    query: str = Field(..., description="Hotel search query, e.g. 'hotels in san francisco'.")
    check_in: str = Field(..., description="Check-in date, ISO 8601 (YYYY-MM-DD).")
    check_out: str = Field(..., description="Check-out date, ISO 8601 (YYYY-MM-DD).")
    adults: int = Field(2, description="Number of adult guests (default 2).")
    rooms: int = Field(1, description="Number of rooms (default 1).")
    currency: str = Field("USD", description="ISO 4217 currency code (default USD).")
    country: str = Field("us", description="ISO 3166-1 alpha-2 region code (default us).")
    params: dict = Field(
        default_factory=dict,
        description="Extra /v1/google/hotels parameters as a dict or JSON string.",
    )


class _GoogleSportsInput(_GhostCrawlBaseInput):
    """Args for the Google Sports SERP tool.

    Inherits ``_GhostCrawlBaseInput`` so the shared
    3-stage ``params`` coercion validator applies — no per-class validator.
    """

    query: str = Field(..., description="Sports query, e.g. 'lakers score' or 'premier league'.")
    country: str = Field("us", description="ISO 3166-1 alpha-2 region code (default us).")
    params: dict = Field(
        default_factory=dict,
        description="Extra /v1/google/sports parameters as a dict or JSON string.",
    )


class _EmptyInput(BaseModel):
    """Empty args schema for tools that take no parameters.

    Stays on bare ``BaseModel`` (NOT ``_GhostCrawlBaseInput``): it carries no
    ``params`` field, so inheriting the validator buys nothing. Leaving it on
    ``BaseModel`` keeps the empty-tool args schema minimal and decoupled.
    """


# ---------------------------------------------------------------------------
# BaseTool subclasses
# ---------------------------------------------------------------------------

class GhostCrawlScrapeTool(BaseTool):
    """LangChain tool: scrape a single URL via GhostCrawl's managed browser fleet."""

    name: str = "ghostcrawl_scrape"
    description: str = (
        "Scrape a webpage using GhostCrawl's managed browser fleet and return the content "
        "as HTML or Markdown. Suitable for news articles, landing pages, product pages, "
        "and any publicly accessible URL. "
        "SUPPORTED: render_js (bool — execute JavaScript before extraction), "
        "output_format ('html' | 'markdown'), wait_for (CSS selector to await), "
        "extract_schema (JSON schema for structured extraction), country (ISO 3166-1 alpha-2 "
        "for geo-targeted content). "
        "UNSUPPORTED: CAPTCHA solving, multi-step login sessions (use ghostcrawl_crawl with "
        "agent-mode for session-based flows). "
        "Returns: page content as HTML or Markdown plus metadata including title and HTTP status_code. "
        "Uses POST /v1/scrape with Authorization: Bearer token auth."
    )
    args_schema: Type[BaseModel] = _ScrapeInput

    def _run(
        self,
        url: str,
        render_js: bool = False,
        output_format: str = "markdown",
        params: Optional[dict] = None,
        **_: Any,
    ) -> str:
        body: Dict[str, Any] = {
            "url": url,
            # Map the tool's ergonomic field names onto the /v1/scrape contract:
            # the API reads `format` (not `output_format`); an unmapped `output_format`
            # was silently ignored → the call fell back to the default html-envelope
            # shape instead of the requested markdown. render_js is kept for schema
            # back-compat (the browser render always executes JS).
            "render_js": render_js,
            "format": output_format,
            **(params or {}),
        }
        with get_client() as c:
            r = c.post("/v1/scrape", json=body)
            try:
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                _handle_error(e)
            return _annotate_result(r.text)

    async def _arun(
        self,
        url: str,
        render_js: bool = False,
        output_format: str = "markdown",
        params: Optional[dict] = None,
        **kwargs: Any,
    ) -> str:
        body: Dict[str, Any] = {
            "url": url,
            # Map the tool's ergonomic field names onto the /v1/scrape contract:
            # the API reads `format` (not `output_format`); an unmapped `output_format`
            # was silently ignored → the call fell back to the default html-envelope
            # shape instead of the requested markdown. render_js is kept for schema
            # back-compat (the browser render always executes JS).
            "render_js": render_js,
            "format": output_format,
            **(params or {}),
        }
        async with get_async_client() as c:
            r = await c.post("/v1/scrape", json=body)
            try:
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                _handle_error(e)
            return _annotate_result(r.text)


class GhostCrawlSearchTool(BaseTool):
    """LangChain tool: run a web search via Brave or Tavily through ghostcrawl."""

    name: str = "ghostcrawl_search"
    description: str = (
        "Run a web search through ghostcrawl and return normalized results. "
        "Supports multiple search backends: 'brave' (default) or 'tavily'. "
        "SUPPORTED: query (the search string), engine ('brave' | 'tavily'), "
        "limit (1–20 results), country (ISO 3166-1 alpha-2 for regional results). "
        "UNSUPPORTED: image search, news-only verticals (use ghostcrawl_scrape on Google News). "
        "Returns: list of results with url, title, snippet, published_at, and relevance score. "
        "ghostcrawl charges no markup — you pay Brave or Tavily directly via your provider key "
        "passed as X-Provider-Authorization: Bearer <YOUR_KEY>. "
        "Uses POST /v1/search with Authorization: Bearer token auth."
    )
    args_schema: Type[BaseModel] = _SearchInput

    def _run(
        self,
        query: str,
        engine: str = "brave",
        limit: int = 10,
        params: Optional[dict] = None,
        provider_key: Optional[str] = None,
        **_: Any,
    ) -> str:
        body: Dict[str, Any] = {
            "query": query,
            "engine": engine,
            "limit": limit,
            **(params or {}),
        }
        # /v1/search needs a BYO provider key as X-Provider-Authorization; without
        # it the API replies 401 search_backend_key_missing.
        headers = (
            {"X-Provider-Authorization": f"Bearer {provider_key}"}
            if provider_key
            else None
        )
        with get_client() as c:
            r = c.post("/v1/search", json=body, headers=headers)
            try:
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                _handle_error(e)
            return _annotate_result(r.text)

    async def _arun(
        self,
        query: str,
        engine: str = "brave",
        limit: int = 10,
        params: Optional[dict] = None,
        provider_key: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        body: Dict[str, Any] = {
            "query": query,
            "engine": engine,
            "limit": limit,
            **(params or {}),
        }
        headers = (
            {"X-Provider-Authorization": f"Bearer {provider_key}"}
            if provider_key
            else None
        )
        async with get_async_client() as c:
            r = await c.post("/v1/search", json=body, headers=headers)
            try:
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                _handle_error(e)
            return _annotate_result(r.text)


class GhostCrawlGoogleSearchTool(BaseTool):
    """LangChain tool: run a Google SERP query via ghostcrawl's /v1/google/search.

    Lets LangChain users reach the Google SERP surface without dropping to
    raw HTTP.
    """

    name: str = "ghostcrawl_google_search"
    description: str = (
        "Run a Google SERP query through ghostcrawl and return normalized results. "
        "SUPPORTED: query (search string), country (ISO 3166-1 alpha-2 code for "
        "regional results, e.g. 'us', 'gb', 'de'). "
        "UNSUPPORTED: image search, news verticals, knowledge-panel deep extraction "
        "(use ghostcrawl_scrape on the relevant Google result page). "
        "Returns: list of organic results with url, title, snippet, position; plus "
        "any featured snippet and related-searches metadata. "
        "Differs from ghostcrawl_search (Brave/Tavily) — this hits Google directly "
        "via /v1/google/search and does NOT require a third-party provider key. "
        "Uses POST /v1/google/search with Authorization: Bearer token auth."
    )
    args_schema: Type[BaseModel] = _GoogleSearchInput

    def _run(
        self,
        query: str,
        country: str = "us",
        params: Optional[dict] = None,
        **_: Any,
    ) -> str:
        with get_client() as c:
            body: Dict[str, Any] = {
                "q": query,
                "country_code": country,
                **(params or {}),
            }
            r = c.post("/v1/google/search", json=body)
            try:
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                _handle_error(e)
            return _annotate_result(r.text)

    async def _arun(
        self,
        query: str,
        country: str = "us",
        params: Optional[dict] = None,
        **kwargs: Any,
    ) -> str:
        async with get_async_client() as c:
            body: Dict[str, Any] = {
                "q": query,
                "country_code": country,
                **(params or {}),
            }
            r = await c.post("/v1/google/search", json=body)
            try:
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                _handle_error(e)
            return _annotate_result(r.text)


class GhostCrawlGoogleHotelsTool(BaseTool):
    """LangChain tool: fetch Google Hotels listings via ghostcrawl's /v1/google/hotels.

    Parity peer of ``GhostCrawlGoogleSearchTool``.
    Reaches the Google Travel (hotels) SERP without dropping to raw HTTP.
    """

    name: str = "ghostcrawl_google_hotels"
    description: str = (
        "Fetch Google Hotels (Travel) listings through ghostcrawl. "
        "SUPPORTED: query (hotel search string), check_in / check_out (ISO 8601 "
        "YYYY-MM-DD; check_out must be after check_in), adults (default 2), rooms "
        "(default 1), currency (ISO 4217, default USD), country (ISO 3166-1 alpha-2). "
        "Returns: hotels_results with name, price, total_price, rating, amenities, "
        "booking_providers. HIGH BRITTLENESS (obfuscated Google Travel SPA classes). "
        "Uses POST /v1/google/hotels with Authorization: Bearer token auth."
    )
    args_schema: Type[BaseModel] = _GoogleHotelsInput

    def _run(
        self,
        query: str,
        check_in: str,
        check_out: str,
        adults: int = 2,
        rooms: int = 1,
        currency: str = "USD",
        country: str = "us",
        params: Optional[dict] = None,
        **_: Any,
    ) -> str:
        with get_client() as c:
            body: Dict[str, Any] = {
                "q": query,
                "check_in": check_in,
                "check_out": check_out,
                "adults": adults,
                "rooms": rooms,
                "currency": currency,
                "country_code": country,
                **(params or {}),
            }
            r = c.post("/v1/google/hotels", json=body)
            try:
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                _handle_error(e)
            return _annotate_result(r.text)

    async def _arun(
        self,
        query: str,
        check_in: str,
        check_out: str,
        adults: int = 2,
        rooms: int = 1,
        currency: str = "USD",
        country: str = "us",
        params: Optional[dict] = None,
        **_: Any,
    ) -> str:
        async with get_async_client() as c:
            body: Dict[str, Any] = {
                "q": query,
                "check_in": check_in,
                "check_out": check_out,
                "adults": adults,
                "rooms": rooms,
                "currency": currency,
                "country_code": country,
                **(params or {}),
            }
            r = await c.post("/v1/google/hotels", json=body)
            try:
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                _handle_error(e)
            return _annotate_result(r.text)


class GhostCrawlGoogleSportsTool(BaseTool):
    """LangChain tool: fetch the Google sports knowledge panel via /v1/google/sports.

    Parity peer of ``GhostCrawlGoogleHotelsTool``.
    Reaches the Google sports SERP knowledge panel without dropping to raw HTTP.
    """

    name: str = "ghostcrawl_google_sports"
    description: str = (
        "Fetch the Google sports knowledge panel (match summary + standings) through ghostcrawl. "
        "SUPPORTED: query (sports search string, e.g. 'lakers score'), country (ISO 3166-1 "
        "alpha-2, default us). "
        "Returns: SearchResult with extras.sports_results = {match: {home_team, away_team, "
        "scores, status}, standings: [...]}. HIGH BRITTLENESS (Google knowledge-panel classes "
        "drift on deploy cadence). "
        "Uses POST /v1/google/sports with Authorization: Bearer token auth."
    )
    args_schema: Type[BaseModel] = _GoogleSportsInput

    def _run(
        self,
        query: str,
        country: str = "us",
        params: Optional[dict] = None,
        **_: Any,
    ) -> str:
        with get_client() as c:
            body: Dict[str, Any] = {
                "q": query,
                "country_code": country,
                **(params or {}),
            }
            r = c.post("/v1/google/sports", json=body)
            try:
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                _handle_error(e)
            return _annotate_result(r.text)

    async def _arun(
        self,
        query: str,
        country: str = "us",
        params: Optional[dict] = None,
        **_: Any,
    ) -> str:
        async with get_async_client() as c:
            body: Dict[str, Any] = {
                "q": query,
                "country_code": country,
                **(params or {}),
            }
            r = await c.post("/v1/google/sports", json=body)
            try:
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                _handle_error(e)
            return _annotate_result(r.text)


class GhostCrawlExtractTool(BaseTool):
    """LangChain tool: extract structured data from a URL via ghostcrawl."""

    name: str = "ghostcrawl_extract"
    description: str = (
        "Extract structured data from a URL by providing a JSON Schema. "
        "GhostCrawl fetches the page through its managed browser fleet, then uses the schema "
        "to identify and return matching fields as a structured JSON object. "
        "SUPPORTED: url (the target page), schema (JSON Schema object describing the fields "
        "to extract — e.g. product title, price, reviews), render_js (bool), "
        "session_id (existing session for stateful extraction). "
        "UNSUPPORTED: extracting from binary files (PDF/DOCX) — convert to HTML first. "
        "Returns: data dict keyed by the schema's property names, plus metadata. "
        "Use this tool instead of ghostcrawl_scrape when you need structured output "
        "rather than raw page content. "
        "Uses POST /v1/extract with Authorization: Bearer token auth."
    )
    args_schema: Type[BaseModel] = _ExtractInput

    def _run(
        self,
        url: str,
        schema_: Optional[dict] = None,
        schema: Optional[dict] = None,
        params: Optional[dict] = None,
        **_: Any,
    ) -> str:
        resolved_schema = schema_ or schema or {}
        body: Dict[str, Any] = {
            "url": url,
            **({"schema": resolved_schema} if resolved_schema else {}),
            **(params or {}),
        }
        with get_client() as c:
            r = c.post("/v1/extract", json=body)
            try:
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                _handle_error(e)
            return _annotate_result(r.text)

    async def _arun(
        self,
        url: str,
        schema_: Optional[dict] = None,
        schema: Optional[dict] = None,
        params: Optional[dict] = None,
        **kwargs: Any,
    ) -> str:
        resolved_schema = schema_ or schema or {}
        body: Dict[str, Any] = {
            "url": url,
            **({"schema": resolved_schema} if resolved_schema else {}),
            **(params or {}),
        }
        async with get_async_client() as c:
            r = await c.post("/v1/extract", json=body)
            try:
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                _handle_error(e)
            return _annotate_result(r.text)


class GhostCrawlContentTool(BaseTool):
    """LangChain tool: fetch a page's rendered content via ghostcrawl's /v1/content.

    The dedicated "browser-utility lane" retrieval route (parity peer of the SDK
    ``content()`` facade method). Idiomatic as an LC document loader — returns the
    rendered page content (HTML/text) for an agent to reason over.
    """

    name: str = "ghostcrawl_content"
    description: str = (
        "Fetch a webpage's rendered content through ghostcrawl's managed browser fleet. "
        "SUPPORTED: url (the target page), engine (browser engine), format (content format). "
        "Returns: the rendered content plus metadata (url, status, status_code, bytes). "
        "Use this when you need the page body itself (not structured extraction). "
        "Uses POST /v1/content with Authorization: Bearer token auth."
    )
    args_schema: Type[BaseModel] = _ContentInput

    def _run(self, url: str, params: Optional[dict] = None, **_: Any) -> str:
        body: Dict[str, Any] = {"url": url, **(params or {})}
        with get_client() as c:
            r = c.post("/v1/content", json=body)
            try:
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                _handle_error(e)
            return _annotate_result(r.text)

    async def _arun(self, url: str, params: Optional[dict] = None, **kwargs: Any) -> str:
        body: Dict[str, Any] = {"url": url, **(params or {})}
        async with get_async_client() as c:
            r = await c.post("/v1/content", json=body)
            try:
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                _handle_error(e)
            return _annotate_result(r.text)


class GhostCrawlMapTool(BaseTool):
    """LangChain tool: discover a site's reachable URLs via ghostcrawl's /v1/map.

    Retrieval-shaped (URL discovery, no content fetch) — idiomatic as an LC tool
    that returns a link inventory for an agent to plan follow-up scrapes.
    """

    name: str = "ghostcrawl_map"
    description: str = (
        "Discover the reachable URLs from a seed page through ghostcrawl (no content scrape). "
        "SUPPORTED: url (the seed page). "
        "Returns: a list of discovered URLs the agent can then scrape/extract selectively. "
        "Uses POST /v1/map with Authorization: Bearer token auth."
    )
    args_schema: Type[BaseModel] = _MapInput

    def _run(self, url: str, params: Optional[dict] = None, **_: Any) -> str:
        body: Dict[str, Any] = {"url": url, **(params or {})}
        with get_client() as c:
            r = c.post("/v1/map", json=body)
            try:
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                _handle_error(e)
            return _annotate_result(r.text)

    async def _arun(self, url: str, params: Optional[dict] = None, **kwargs: Any) -> str:
        body: Dict[str, Any] = {"url": url, **(params or {})}
        async with get_async_client() as c:
            r = await c.post("/v1/map", json=body)
            try:
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                _handle_error(e)
            return _annotate_result(r.text)


class GhostCrawlCrawlTool(BaseTool):
    """LangChain tool: crawl a site starting from a seed URL via ghostcrawl."""

    name: str = "ghostcrawl_crawl"
    description: str = (
        "Crawl a website starting from a seed URL and return content from multiple pages. "
        "GhostCrawl follows links using its managed browser fleet, respecting same-origin and "
        "max_pages bounds to avoid unbounded crawls. "
        "SUPPORTED: url (seed URL), max_pages (1–500, default 10), same_origin (bool — "
        "restrict to same scheme+host+port, default true), render_js (bool for JS-heavy sites). "
        "UNSUPPORTED: authenticated crawls requiring session cookies (use ghostcrawl_scrape "
        "in a loop with session_id for authenticated pages). "
        "Returns: list of crawled pages with url, content, title, and status_code per page. "
        "QUOTA NOTE: each page counts as one ghostcrawl credit. "
        "Uses POST /v1/crawl with Authorization: Bearer token auth."
    )
    args_schema: Type[BaseModel] = _CrawlInput

    def _run(
        self,
        url: str,
        max_pages: int = 10,
        same_origin: bool = True,
        params: Optional[dict] = None,
        **_: Any,
    ) -> str:
        # /v1/crawl requires ``seed_urls`` (array) — a bare ``url`` field is a 422
        # "Field required" (verified by real execution, Phase 178). Map the tool's
        # ergonomic ``url`` onto the ``seed_urls`` the crawl route contract expects.
        body: Dict[str, Any] = {
            "seed_urls": [url],
            "max_pages": max_pages,
            "same_origin": same_origin,
            **(params or {}),
        }
        with get_client() as c:
            r = c.post("/v1/crawl", json=body)
            try:
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                _handle_error(e)
            return _annotate_result(r.text)

    async def _arun(
        self,
        url: str,
        max_pages: int = 10,
        same_origin: bool = True,
        params: Optional[dict] = None,
        **kwargs: Any,
    ) -> str:
        # /v1/crawl requires ``seed_urls`` (array) — see the sync path above.
        body: Dict[str, Any] = {
            "seed_urls": [url],
            "max_pages": max_pages,
            "same_origin": same_origin,
            **(params or {}),
        }
        async with get_async_client() as c:
            r = await c.post("/v1/crawl", json=body)
            try:
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                _handle_error(e)
            return _annotate_result(r.text)
