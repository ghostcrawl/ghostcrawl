"""Phase 140.5 Plan 14 — Python cookie URL-encode helper (D-05e item 5).

Tests `format_cookies_urlencoded` and confirms the plain `format_cookies`
joiner is left unchanged (back-compat / zero-loss-of-functionality).
"""
from __future__ import annotations

# NOTE: import ``ghostcrawl.params`` lazily inside each test (not at module top).
# The repo root ``ghostcrawl/`` SaaS package and the SDK ``sdks/python/ghostcrawl``
# share a name; a module-top ``from ghostcrawl...`` would cache the root package in
# sys.modules and poison sibling SDK tests (e.g. test_fern_hygiene). Deferring the
# import — the same pattern as test_aiohttp_autodetect.py — keeps resolution clean.


def test_urlencodes_a_single_cookie_value() -> None:
    from ghostcrawl.params import format_cookies_urlencoded

    assert format_cookies_urlencoded({"a": "b c"}) == "a=b%20c"


def test_urlencodes_special_characters_and_joins() -> None:
    from ghostcrawl.params import format_cookies_urlencoded

    assert format_cookies_urlencoded({"a": "x&y", "b": "1"}) == "a=x%26y; b=1"


def test_empty_dict_yields_empty_string() -> None:
    from ghostcrawl.params import format_cookies_urlencoded

    assert format_cookies_urlencoded({}) == ""


def test_plain_format_cookies_is_unchanged() -> None:
    from ghostcrawl.params import format_cookies

    # Back-compat: the plain joiner must NOT URL-encode.
    assert format_cookies({"a": "b c"}) == "a=b c"
