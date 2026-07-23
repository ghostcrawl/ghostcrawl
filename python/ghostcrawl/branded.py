# Branded User-Agent factory for ghostcrawl-python SDK
from __future__ import annotations
import platform
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import Optional


def _ua_string() -> str:
    """Build the branded User-Agent header value for this SDK.

    Format: ghostcrawl-python/<pkg_version> Python/<py_version> <OS>/<arch>
    """
    try:
        pkg_ver = version("ghostcrawl")
    except PackageNotFoundError:
        pkg_ver = "0.0.0"
    py_ver = (
        f"{sys.version_info.major}"
        f".{sys.version_info.minor}"
        f".{sys.version_info.micro}"
    )
    return (
        f"ghostcrawl-python/{pkg_ver}"
        f" Python/{py_ver}"
        f" {platform.system()}/{platform.machine()}"
    )


def branded_client(
    api_key: str,
    base_url: Optional[str] = None,
    **kwargs,
):
    """Construct the canonical ``GhostCrawlClient`` (Kiota-backed facade).

    The branded User-Agent is set on the underlying httpx session so requests
    carry the SDK identifier. The bearer token flows through the facade's
    Kiota auth provider.

    Parameters
    ----------
    api_key : str
        GhostCrawl API key; supplied as the bearer token.
    base_url : str, optional
        Override API base URL. Defaults to https://api.ghostcrawl.io if not set.
    **kwargs
        Reserved for forward-compat; ignored by the facade constructor.
    """
    from ghostcrawl.facade import GhostCrawlClient  # avoid circular at module import

    resolved_base = base_url or "https://api.ghostcrawl.io"
    client = GhostCrawlClient(token=api_key, base_url=resolved_base)

    # Set the branded User-Agent on the underlying httpx session so every
    # request carries the SDK identifier. The Kiota httpx adapter owns the
    # session; update its default headers in place.
    try:
        http = client._core.request_adapter._http_client  # type: ignore[attr-defined]
        if hasattr(http, "headers"):
            http.headers.setdefault("User-Agent", _ua_string())
    except Exception:  # pragma: no cover - defensive; UA is best-effort
        pass

    return client


def google_hotels(
    api_key: str,
    query: str,
    *,
    check_in: str,
    check_out: str,
    adults: int = 2,
    rooms: int = 1,
    currency: str = "USD",
    country_code: str = "us",
    base_url: Optional[str] = None,
    **kwargs,
):
    """Fetch Google Hotels (Travel) listings via POST /v1/google/hotels.

    Convenience peer of the Google SERP reach. Wraps :func:`branded_client`
    (branded UA + Bearer auth) and POSTs the hotels sugar route, returning the parsed JSON ``SearchResult`` (hotels_results[]
    with name, price, total_price, rating, amenities, booking_providers).

    Parameters
    ----------
    api_key : str
        GhostCrawl API key (Bearer).
    query : str
        Hotel search query, e.g. ``"hotels in san francisco"``.
    check_in, check_out : str
        ISO 8601 (YYYY-MM-DD); check_out must be after check_in (server-enforced).
    adults, rooms : int
        Guest / room counts (defaults 2 / 1).
    currency : str
        ISO 4217 currency code (default ``"USD"``).
    country_code : str
        ISO 3166-1 alpha-2 SERP region (default ``"us"``).
    base_url : str, optional
        Override API base URL.
    **kwargs
        Forwarded to :func:`branded_client`.
    """
    import httpx  # local import keeps module-import cost off the UA-only path

    resolved_base = (base_url or "https://api.ghostcrawl.io").rstrip("/")
    headers = {
        "User-Agent": _ua_string(),
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=kwargs.pop("timeout", 60)) as c:
        resp = c.post(
            f"{resolved_base}/v1/google/hotels",
            headers=headers,
            json={
                "q": query,
                "check_in": check_in,
                "check_out": check_out,
                "adults": adults,
                "rooms": rooms,
                "currency": currency,
                "country_code": country_code,
            },
        )
        resp.raise_for_status()
        return resp.json()


def google_sports(
    api_key: str,
    query: str,
    *,
    country_code: str = "us",
    base_url: Optional[str] = None,
    **kwargs,
):
    """Fetch the Google sports knowledge panel via POST /v1/google/sports.

    Convenience peer of the Google SERP reach. Wraps :func:`branded_client`
    (branded UA + Bearer auth) and POSTs the sports sugar route, returning the parsed JSON ``SearchResult``. The structured
    match + standings live under ``extras.sports_results`` (match:
    {home_team, away_team, scores, status}; standings: [...]).

    Parameters
    ----------
    api_key : str
        GhostCrawl API key (Bearer).
    query : str
        Sports query, e.g. ``"lakers score"`` or ``"premier league"``.
    country_code : str
        ISO 3166-1 alpha-2 SERP region (default ``"us"``).
    base_url : str, optional
        Override API base URL.
    **kwargs
        Forwarded to the underlying HTTP client (e.g. ``timeout``).
    """
    import httpx  # local import keeps module-import cost off the UA-only path

    resolved_base = (base_url or "https://api.ghostcrawl.io").rstrip("/")
    headers = {
        "User-Agent": _ua_string(),
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=kwargs.pop("timeout", 60)) as c:
        resp = c.post(
            f"{resolved_base}/v1/google/sports",
            headers=headers,
            json={
                "q": query,
                "country_code": country_code,
            },
        )
        resp.raise_for_status()
        return resp.json()
