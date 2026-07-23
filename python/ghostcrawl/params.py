# Request-parameter helpers for the GhostCrawl SDK.
from __future__ import annotations
import base64
import json
from typing import Dict, List, Union
from urllib.parse import quote


def encode_js_snippet(code: str) -> str:
    """Base64-encode a JS snippet for use with the js_snippet param."""
    return base64.b64encode(code.encode("utf-8")).decode("ascii")


def format_cookies(cookies: Dict[str, str]) -> str:
    """Stringify a cookie dict to 'k=v; k2=v2' format."""
    return "; ".join(f"{k}={v}" for k, v in cookies.items())


def format_cookies_urlencoded(cookies: Dict[str, str]) -> str:
    """Stringify a cookie dict to 'k=v; k2=v2', URL-encoding each value.

    Distinct from :func:`format_cookies`, which leaves values unencoded for
    header contexts. Use this when the cookie string is destined for a URL or
    query-string context.

    URL-encodes each cookie name/value pair (ghostcrawl idiom).
    """
    return "; ".join(f"{k}={quote(v)}" for k, v in cookies.items())


def build_extract_rules(rules: Dict[str, Union[str, dict]]) -> str:
    """JSON-encode extract_rules for the /v1/extract schema param."""
    return json.dumps(rules)


def build_js_scenario(steps: List[dict]) -> str:
    """JSON-encode a js_scenario step list."""
    return json.dumps(steps)
