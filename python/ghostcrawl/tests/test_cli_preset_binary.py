"""Phase 140.5 Plan 14 — CLI scrape --preset + binary auto-save (D-05e items 4, 3).

Uses typer's CliRunner with a monkeypatched _get_client that records the scrape
kwargs (preset assertions) and returns a stubbed result (auto-save assertion).
"""
from __future__ import annotations


def _runner():
    from typer.testing import CliRunner

    return CliRunner()


class _FakeResult:
    """Stub scrape result exposing a content_type + bytes body."""

    def __init__(self, content_type: str, body):
        self.content_type = content_type
        self.body = body

    def model_dump(self):  # mirrors a pydantic result for _to_dict
        return {"content_type": self.content_type, "body": self.body}


def _patch_client(monkeypatch, *, result):
    """Install a fake client whose .scrape records kwargs and returns *result*."""
    calls: dict = {}

    class _FakeClient:
        def scrape(self, **kwargs):
            calls.update(kwargs)
            return result

    from ghostcrawl.cli import main as cli_main

    monkeypatch.setattr(cli_main, "_get_client", lambda: _FakeClient())
    return calls, cli_main


def test_preset_screenshot_expands_kwargs(monkeypatch):
    calls, cli_main = _patch_client(
        monkeypatch, result=_FakeResult("application/json", {"ok": True})
    )
    res = _runner().invoke(cli_main.app, ["scrape", "https://x.test", "--preset", "screenshot"])
    assert res.exit_code == 0, res.output
    assert calls.get("render_js") is True
    assert calls.get("screenshot") is True


def test_explicit_flag_overrides_preset(monkeypatch):
    calls, cli_main = _patch_client(
        monkeypatch, result=_FakeResult("application/json", {"ok": True})
    )
    # fetch preset sets render_js False; explicit --render-js must win → True.
    res = _runner().invoke(
        cli_main.app, ["scrape", "https://x.test", "--preset", "fetch", "--render-js"]
    )
    assert res.exit_code == 0, res.output
    assert calls.get("render_js") is True


def test_unknown_preset_exits_nonzero(monkeypatch):
    _calls, cli_main = _patch_client(
        monkeypatch, result=_FakeResult("application/json", {"ok": True})
    )
    res = _runner().invoke(cli_main.app, ["scrape", "https://x.test", "--preset", "nope"])
    assert res.exit_code != 0
    assert "preset" in res.output.lower()


def test_binary_response_auto_saves_to_output(monkeypatch, tmp_path):
    png_bytes = b"\x89PNG\r\n\x1a\nFAKE"
    _calls, cli_main = _patch_client(
        monkeypatch, result=_FakeResult("image/png", png_bytes)
    )
    out = tmp_path / "shot.png"
    res = _runner().invoke(
        cli_main.app, ["scrape", "https://x.test", "--output", str(out)]
    )
    assert res.exit_code == 0, res.output
    assert out.read_bytes() == png_bytes
    assert "saved" in res.output.lower()
    assert str(out) in res.output


def test_non_binary_without_output_prints_json(monkeypatch):
    _calls, cli_main = _patch_client(
        monkeypatch, result=_FakeResult("text/html", "<html></html>")
    )
    res = _runner().invoke(cli_main.app, ["scrape", "https://x.test"])
    assert res.exit_code == 0, res.output
    # JSON dump of the result dict (not a "saved ..." line).
    assert "saved" not in res.output.lower()
    assert "content_type" in res.output
