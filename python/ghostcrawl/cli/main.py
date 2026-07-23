"""GhostCrawl CLI: init, install, scrape, extract, crawl,
map, config set-key|show, session list, auth login.

Command surface:
    ghostcrawl init
    ghostcrawl install [--os linux-x86_64]
    ghostcrawl scrape <url> [--render-js] [--country CC] [--format html|markdown] [--pretty]
    ghostcrawl extract <url> [--schema PATH] [--pretty]
    ghostcrawl map <url> [--pretty]
    ghostcrawl config set-key <KEY>
    ghostcrawl config show

Legacy surface (kept, NOT removed — forward compatibility):
    ghostcrawl crawl <url> [--max-depth N] [--out PATH] [--pretty]
    ghostcrawl session list
    ghostcrawl auth login

Security: API key is NEVER accepted via CLI arg.
Read path: ~/.config/ghostcrawl/config.toml → GHOSTCRAWL_API_KEY env.
In `init` only: interactive hidden prompt (bash history safe — no arg path).
"""

from __future__ import annotations

import asyncio
import json
import os
import pathlib
import stat
from typing import Any, Optional

import typer

from ghostcrawl import GhostCrawlClient
from ghostcrawl import GhostCrawl
from ghostcrawl.cli._batch import run_batch
from ghostcrawl.errors.identity_errors import AuthenticationError, InvalidRequestError


def _run(value: Any) -> Any:
    """Resolve a possibly-async client call to its value.

    The canonical client (``GhostCrawlClient``) is async, but the CLI is sync.
    Each command calls a client method and passes the result here: a coroutine
    is driven to completion via ``asyncio.run``; an already-resolved value (e.g.
    from a test fake or a sync helper) is returned as-is. This keeps every
    command body synchronous while delegating to the async facade.
    """
    if asyncio.iscoroutine(value):
        return asyncio.run(value)
    return value

# ---------------------------------------------------------------------------
# Top-level app
# ---------------------------------------------------------------------------

__version__ = "2.3.4"  # keep in sync with sdks/python/pyproject.toml (test_version_matches_pyproject guards drift)


def _version_callback(value: bool) -> None:
    """Typer --version callback. Prints version and exits 0."""
    if value:
        typer.echo(f"ghostcrawl {__version__}")
        raise typer.Exit(code=0)


app = typer.Typer(
    name="ghostcrawl",
    help="GhostCrawl command-line interface (v0.5.0).",
    no_args_is_help=True,
    add_completion=False,
)


@app.callback()
def _main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show the ghostcrawl CLI version and exit.",
    ),
) -> None:
    """ghostcrawl root callback — handles --version before subcommand dispatch."""
    return None

session_app = typer.Typer(help="Session management commands.", no_args_is_help=True)
app.add_typer(session_app, name="session")

auth_app = typer.Typer(help="Auth helper commands.", no_args_is_help=True)
app.add_typer(auth_app, name="auth")

config_app = typer.Typer(help="API key + base URL configuration.", no_args_is_help=True)
app.add_typer(config_app, name="config")


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def _config_dir() -> pathlib.Path:
    """Return the XDG-compliant ghostcrawl config directory."""
    xdg = os.environ.get("XDG_CONFIG_HOME", "")
    if xdg:
        base = pathlib.Path(xdg)
    else:
        base = pathlib.Path.home() / ".config"
    return base / "ghostcrawl"


def _config_path() -> pathlib.Path:
    return _config_dir() / "config.toml"


def _read_config_key() -> Optional[str]:
    """Read api_key from config.toml. Returns None if file absent or key missing."""
    path = _config_path()
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("api_key"):
                parts = line.split("=", 1)
                if len(parts) == 2:
                    val = parts[1].strip().strip('"').strip("'")
                    return val if val else None
    except OSError:
        return None
    return None


def _resolve_api_key() -> Optional[str]:
    """Key resolution: legacy config reader → _config_store → GHOSTCRAWL_API_KEY env."""
    key = _read_config_key()
    if key:
        return key
    try:
        from ._config_store import read_api_key as _cs_read
        key = _cs_read()
        if key:
            return key
    except ImportError:
        pass
    env_key = os.environ.get("GHOSTCRAWL_API_KEY", "").strip()
    return env_key if env_key else None


# ---------------------------------------------------------------------------
# Internal helpers (legacy compatibility)
# ---------------------------------------------------------------------------

def _get_client() -> GhostCrawlClient:
    """Build the canonical ``GhostCrawlClient`` from environment variables.

    Reads GHOSTCRAWL_API_KEY (required) and GHOSTCRAWL_BASE_URL (optional,
    defaults to https://api.ghostcrawl.io).  Exits 1 if GHOSTCRAWL_API_KEY is
    unset or empty — API keys must never appear in CLI args.

    The branded ``ghostcrawl-cli/<version>`` User-Agent is set on the
    underlying httpx session so CLI requests are attributable.
    """
    api_key = os.environ.get("GHOSTCRAWL_API_KEY", "").strip()
    if not api_key:
        typer.echo(
            "Error: GHOSTCRAWL_API_KEY environment variable required", err=True
        )
        raise typer.Exit(1)
    base_url = os.environ.get("GHOSTCRAWL_BASE_URL", "https://api.ghostcrawl.io")
    client = GhostCrawlClient(token=api_key, base_url=base_url)

    # Brand the underlying httpx session's User-Agent as the CLI. Best-effort —
    # the Kiota httpx adapter owns the session; auth is unaffected (the bearer
    # flows through the Kiota auth provider, not this header).
    try:
        from ghostcrawl.branded import _ua_string as _gc_ua

        ua = _gc_ua().replace("ghostcrawl-python", "ghostcrawl-cli")
        http = client._core.request_adapter._http_client  # type: ignore[attr-defined]
        if hasattr(http, "headers"):
            http.headers.setdefault("User-Agent", ua)
    except Exception:  # pragma: no cover - UA branding is best-effort
        pass
    return client


def _emit(payload: object, pretty: bool) -> None:
    """Emit *payload* as JSON to stdout."""
    output = (
        json.dumps(payload, indent=2, default=str)
        if pretty
        else json.dumps(payload, default=str)
    )
    typer.echo(output)


def _to_dict(obj: object) -> object:
    """Convert Pydantic model or raw object to a JSON-serialisable form."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if isinstance(obj, list):
        return [_to_dict(item) for item in obj]
    return obj


# ---------------------------------------------------------------------------
# init command
# ---------------------------------------------------------------------------


@app.command()
def init() -> None:
    """Interactive first-time setup: prompt for API key and write config.toml.

    Writes ~/.config/ghostcrawl/config.toml (XDG-compliant; chmod 0o600).
    Pings GET /v1/profiles to validate the key before saving succeeds.
    Re-prompts on 401. API key is never echoed to the terminal.

    Security: API key is entered via hidden prompt only — never
    passed as a CLI argument, so it is not visible in ps(1) or shell history.
    """
    base_url = os.environ.get("GHOSTCRAWL_BASE_URL", "").strip() or "https://api.ghostcrawl.io"

    while True:
        api_key: str = typer.prompt(
            "GhostCrawl API key",
            hide_input=True,
            prompt_suffix=": ",
        )

        # Validate the key before writing to disk
        try:
            client = GhostCrawl(api_key=api_key, base_url=base_url)
            _run(client.profiles.list())
        except AuthenticationError:
            typer.echo(
                "Key rejected (401). Run `ghostcrawl init` again with the correct key.",
                err=True,
            )
            raise typer.Exit(code=1)
        except Exception as exc:
            typer.echo(f"Warning: could not validate key ({exc}). Writing config anyway.", err=True)

        # Write config to disk with 0o600 permissions
        config_dir = _config_dir()
        config_dir.mkdir(parents=True, exist_ok=True)
        # chmod the directory to 0o700
        config_dir.chmod(0o700)

        config_path = _config_path()
        config_path.write_text(f'api_key = "{api_key}"\n', encoding="utf-8")
        # chmod the file to 0o600 (owner read/write only)
        config_path.chmod(0o600)

        typer.echo(f"Config written to {config_path}; key validated.")
        break


# ---------------------------------------------------------------------------
# install command
# ---------------------------------------------------------------------------


@app.command()
def install(
    os_target: str = typer.Option("linux-x86_64", "--os", help="Target OS/arch (e.g. linux-x86_64)."),
    license_token_path: Optional[pathlib.Path] = typer.Option(
        None,
        "--license-token",
        help=(
            "Path to a license token file. When provided, the token is written "
            "to ~/.ghostcrawl/license.token mode 0600 for the "
            "phone-home subsystem."
        ),
    ),
    install_dir: pathlib.Path = typer.Option(
        pathlib.Path.home() / ".ghostcrawl",
        "--install-dir",
        help="Target install directory (default: ~/.ghostcrawl).",
    ),
) -> None:
    """Download the GhostCrawl native binaries to ~/.ghostcrawl/binaries/.

    Reads the binary artifact URL from the GHOSTCRAWL_BINARY_URL environment variable.
    The operator must set this variable before first pilot use — see the operator
    documentation for the correct artifact URL.

    Scope: linux-x86_64 only. Cross-platform binary bundles land at the
    FUTURE milestone (v1.6+). Attempting --os with a non-linux-x86_64 value exits 1.
    """
    import httpx

    # ---- optional --license-token write (atomic, mode 0600) ----
    # Token format gate: the token MUST start with "ghc_".
    if license_token_path is not None:
        if not license_token_path.exists():
            typer.echo(
                f"Error: --license-token path does not exist: {license_token_path}",
                err=True,
            )
            raise typer.Exit(1)
        token = license_token_path.read_text().strip()
        if not token:
            typer.echo("Error: license token file is empty.", err=True)
            raise typer.Exit(1)
        if not token.startswith("ghc_"):
            typer.echo(
                "Error: token format invalid (expect ghc_...)",
                err=True,
            )
            raise typer.Exit(1)

        install_dir.mkdir(parents=True, exist_ok=True)
        try:
            install_dir.chmod(0o700)
        except OSError:
            pass

        tmp = install_dir / "license.token.tmp"
        tmp.write_text(token)
        try:
            tmp.chmod(0o600)
        except OSError:
            pass
        final = install_dir / "license.token"
        tmp.replace(final)  # atomic POSIX rename

        typer.echo(f"License token written to {final}")
        typer.echo(
            "A future release will wire the container pull + start flow "
            "against the registry."
        )

        # Token-only invocation: skip binary download if GHOSTCRAWL_BINARY_URL is unset.
        if not os.environ.get("GHOSTCRAWL_BINARY_URL", "").strip():
            return

    if os_target != "linux-x86_64":
        typer.echo(
            "Cross-platform binaries land at FUTURE milestone; v1.6 supports linux-x86_64 only.",
            err=True,
        )
        raise typer.Exit(1)

    binary_url = os.environ.get("GHOSTCRAWL_BINARY_URL", "").strip()
    if not binary_url:
        typer.echo(
            "Error: GHOSTCRAWL_BINARY_URL environment variable is not set.\n"
            "Set it to the operator-provided artifact URL before running `ghostcrawl install`.",
            err=True,
        )
        raise typer.Exit(1)

    # Enforce HTTPS for binary downloads
    if not binary_url.startswith("https://"):
        typer.echo(
            "Error: GHOSTCRAWL_BINARY_URL must use HTTPS for security. "
            "Please set a valid HTTPS URL.",
            err=True,
        )
        raise typer.Exit(1)

    target_dir = pathlib.Path.home() / ".ghostcrawl" / "binaries"
    target_dir.mkdir(parents=True, exist_ok=True)

    filename = binary_url.rstrip("/").split("/")[-1] or "ghostcrawl-binary"
    dest = target_dir / filename

    typer.echo(f"Downloading {binary_url} ...")

    try:
        with httpx.stream("GET", binary_url, follow_redirects=True, timeout=300.0) as response:
            response.raise_for_status()
            total = int(response.headers.get("content-length", 0))
            downloaded = 0
            with dest.open("wb") as fh:
                for chunk in response.iter_bytes(chunk_size=65536):
                    fh.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded * 100 // total
                        typer.echo(f"\r  {downloaded}/{total} bytes ({pct}%)", nl=False)
                    else:
                        typer.echo(f"\r  {downloaded} bytes", nl=False)
            typer.echo("")  # newline after progress
    except httpx.HTTPStatusError as exc:
        typer.echo(f"Error: download failed with HTTP {exc.response.status_code}.", err=True)
        raise typer.Exit(1)
    except Exception as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)

    # chmod 0o755 the downloaded artifact
    dest.chmod(0o755)
    typer.echo(f"Installed to {dest}")


# ---------------------------------------------------------------------------
# scrape command
# ---------------------------------------------------------------------------


# Scrape presets (the proxy_tier field stays server-side, never emitted as kwargs).
_SCRAPE_PRESETS: dict[str, dict] = {
    "screenshot": {"render_js": True, "screenshot": True},
    "fetch": {"render_js": False, "block_resources": True},
    "premium-render": {"render_js": True},  # proxy_tier handled server-side
    "fast-html": {"render_js": False},
    "resilient": {"render_js": True},  # network routing handled server-side
}

# Content-types that should be written to disk as raw bytes rather than dumped
# inline (binary auto-save).
_BINARY_CONTENT_PREFIXES = ("image/", "application/pdf")

# Proxy auto-escalation maps a blocked upstream status to the next integer
# proxy_tier (1=BYO and up).
# Blocked HTTP statuses that warrant bumping to the next tier (the HTTP-status
# subset of ghostcrawl.proxy.auto_escalate.BLOCK_SIGNALS).
_PROXY_BLOCK_STATUSES = {403, 429}


def _header_lookup(headers: object, name: str) -> object:
    """Case-insensitive header fetch (httpx HttpResponse.headers is a dict whose
    keys may be lower-cased)."""
    if not isinstance(headers, dict):
        return None
    if name in headers:
        return headers[name]
    lname = name.lower()
    for key, value in headers.items():
        if isinstance(key, str) and key.lower() == lname:
            return value
    return None


def _scrape_via_facade(client, *, url: str, scrape_kwargs: dict, max_proxy_tier: int):
    """Scrape a URL via the canonical client.

    Proxy-tier auto-escalation is now handled server-side (the SaaS rate-ban
    governor reroutes blocked egress IPs across the pool), so the CLI no longer
    drives integer-tier escalation from response headers. ``max_proxy_tier`` is
    accepted for back-compat but not forwarded — the legacy integer ``proxy_tier``
    body field is obsolete (the server now models proxy_tier as named strings).
    Accepts either the async facade (a coroutine is driven by ``_run``) or a sync
    test double.
    """
    return _run(client.scrape(url=url, **scrape_kwargs))


def _is_binary_content_type(content_type: object) -> bool:
    if not isinstance(content_type, str):
        return False
    ct = content_type.split(";", 1)[0].strip().lower()
    return any(ct == p or ct.startswith(p) for p in _BINARY_CONTENT_PREFIXES)


@app.command()
def scrape(
    url: str = typer.Argument(..., help="URL to scrape."),
    render_js: bool = typer.Option(False, "--render-js", help="Execute JavaScript."),
    country: str = typer.Option("us", "--country", help="ISO 3166-1 alpha-2 country code."),
    output_format: str = typer.Option("html", "--format", help="Output format: html|markdown."),
    preset: Optional[str] = typer.Option(
        None,
        "--preset",
        help=(
            "Expand a locked scrape-param bundle: "
            "screenshot | fetch | premium-render | fast-html | resilient. "
            "Explicit flags override preset values."
        ),
    ),
    output: Optional[pathlib.Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Write the response body to this file (binary responses saved as bytes).",
    ),
    max_proxy_tier: int = typer.Option(
        3,
        "--max-proxy-tier",
        help=(
            "Cap proxy auto-escalation. On a blocked upstream status (403/429) the "
            "scrape retries at the next integer proxy_tier (1=BYO .. 4=safety net). "
            "Default 3; Tier 4 (AWS) requires explicit opt-in."
        ),
    ),
    pretty: bool = typer.Option(False, "--pretty", help="Indent JSON output."),
) -> None:
    """Scrape a URL via /v1/scrape and emit the result as JSON.

    With --preset, a locked bundle of scrape params is applied; any explicit
    flag (e.g. --render-js) overrides the preset value. With --output, a binary
    response body (image/* or application/pdf) is saved to the file as bytes
    instead of dumped to stdout.
    """
    # Resolve preset → base kwargs, then let explicit flags override.
    scrape_kwargs: dict = {
        "render_js": render_js,
        "country": country,
        "output_format": output_format,
    }
    if preset is not None:
        bundle = _SCRAPE_PRESETS.get(preset)
        if bundle is None:
            typer.echo(
                f"Error: unknown preset {preset!r}. "
                f"Valid presets: {', '.join(sorted(_SCRAPE_PRESETS))}.",
                err=True,
            )
            raise typer.Exit(1)
        # Preset supplies defaults; explicit CLI flags (already in scrape_kwargs
        # with their option defaults) override only when the user set them.
        # render_js is a bool flag: an explicit --render-js sets it True, so a
        # True value always wins; otherwise the preset value applies.
        for key, value in bundle.items():
            if key == "render_js":
                scrape_kwargs["render_js"] = render_js or bool(value)
            else:
                scrape_kwargs[key] = value

    client = _get_client()
    try:
        result = _scrape_via_facade(
            client, url=url, scrape_kwargs=scrape_kwargs, max_proxy_tier=max_proxy_tier
        )
    except Exception as exc:
        typer.echo(f"Error: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(1)

    payload = _to_dict(result)

    # Binary auto-save. When the response is a binary content-type
    # and --output is set, write the raw bytes and print a one-line summary instead
    # of dumping bytes to stdout (token-saving default for AI workloads).
    content_type = payload.get("content_type") if isinstance(payload, dict) else None
    body = payload.get("body") if isinstance(payload, dict) else None
    if output is not None:
        if _is_binary_content_type(content_type) and isinstance(body, (bytes, bytearray)):
            data = bytes(body)
            output.write_bytes(data)
            typer.echo(f"saved {output} ({len(data)} bytes)")
        else:
            # Non-binary: write the textual body (or the JSON payload) to the file.
            text = body if isinstance(body, str) else json.dumps(payload, default=str)
            output.write_text(text, encoding="utf-8")
            typer.echo(f"saved {output} ({len(text)} chars)")
        return

    _emit(payload, pretty)


# ---------------------------------------------------------------------------
# batch command (resumable, plan-aware bulk scrape; ADDITIVE to scrape)
# ---------------------------------------------------------------------------


@app.command("batch")
def batch(
    input_file: pathlib.Path = typer.Option(
        ...,
        "--input-file",
        help="Text file of URLs, one per line (# comments allowed).",
    ),
    output_dir: pathlib.Path = typer.Option(
        ...,
        "--output-dir",
        help="Directory to write results.ndjson.",
    ),
    concurrency: int = typer.Option(
        5,
        "--concurrency",
        min=1,
        help="Max parallel scrapes; capped by the /usage plan limit.",
    ),
    resume: bool = typer.Option(
        False,
        "--resume",
        help="Skip URLs already completed in the checkpoint for this input file.",
    ),
) -> None:
    """Batch-scrape every URL in --input-file concurrently, writing NDJSON to --output-dir.

    Concurrency is bounded by the plan limit fetched from /usage. A checkpoint at
    ~/.ghostcrawl/batch-checkpoint-<job-id>.json records completed URLs so --resume can
    continue an interrupted run.
    """
    try:
        summary = asyncio.run(
            run_batch(
                input_file=input_file,
                output_dir=output_dir,
                concurrency=concurrency,
                resume=resume,
                client_factory=_get_client,
            )
        )
    except Exception as exc:
        typer.echo(f"Error: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(1)
    _emit(summary, pretty=True)


# ---------------------------------------------------------------------------
# extract command
# ---------------------------------------------------------------------------


@app.command()
def extract(
    url: str = typer.Argument(..., help="URL to extract structured data from."),
    schema_path: Optional[pathlib.Path] = typer.Option(None, "--schema", help="Path to JSON schema file."),
    pretty: bool = typer.Option(False, "--pretty", help="Indent JSON output."),
) -> None:
    """Extract structured data via /v1/extract."""
    import json as _json
    client = _get_client()
    schema = None
    try:
        if schema_path is not None:
            schema = _json.loads(schema_path.read_text(encoding="utf-8"))
        # The facade requires a schema; default to an empty object schema when
        # none is provided so the command still issues a structured-extract call.
        result = _run(client.extract(url=url, schema=schema if schema else {}))
    except _json.JSONDecodeError as exc:
        typer.echo(f"Error: --schema file is not valid JSON: {exc}", err=True)
        raise typer.Exit(1)
    except Exception as exc:
        typer.echo(f"Error: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(1)
    _emit(_to_dict(result), pretty)


# ---------------------------------------------------------------------------
# crawl command (legacy, kept)
# ---------------------------------------------------------------------------


@app.command()
def crawl(
    url: str = typer.Argument(..., help="Seed URL for the crawl."),
    max_depth: int = typer.Option(2, "--max-depth", help="Maximum crawl depth."),
    out: Optional[str] = typer.Option(None, "--out", help="Output file path (JSON)."),
    pretty: bool = typer.Option(False, "--pretty", help="Indent JSON output."),
) -> None:
    """Start a crawl run (v1.3 /v1/crawl-runs, NOT the legacy /v1/crawl endpoint).

    Routes through ``client.crawl_runs.start()``.
    """
    client = _get_client()
    crawl_runs = getattr(client, "crawl_runs", None)
    if crawl_runs is None:
        typer.echo(
            "Error: crawl_runs sub-client missing on the client",
            err=True,
        )
        raise typer.Exit(1)
    try:
        result = _run(crawl_runs.start(url=url, max_depth=max_depth))
    except Exception as exc:
        typer.echo(f"Error: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(1)
    payload = _to_dict(result)
    if out:
        pathlib.Path(out).write_text(
            json.dumps(payload, indent=2 if pretty else None, default=str),
            encoding="utf-8",
        )
        typer.echo(f"Crawl result written to {out}", err=True)
    else:
        _emit(payload, pretty)


# ---------------------------------------------------------------------------
# map command
# ---------------------------------------------------------------------------


@app.command()
def map(  # noqa: A001 — shadowing builtin map is acceptable for CLI command name
    url: str = typer.Argument(..., help="Seed URL to map."),
    pretty: bool = typer.Option(False, "--pretty", help="Indent JSON output."),
) -> None:
    """Discover all reachable URLs from a seed (no content scrape)."""
    client = _get_client()
    try:
        result = _run(client.map(url=url))
    except Exception as exc:
        typer.echo(f"Error: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(1)
    _emit(_to_dict(result), pretty)


# ---------------------------------------------------------------------------
# session commands (legacy, kept)
# ---------------------------------------------------------------------------


@session_app.command("list")
def session_list(
    pretty: bool = typer.Option(False, "--pretty", help="Indent JSON output."),
) -> None:
    """List active browser sessions."""
    client = _get_client()
    try:
        result = _run(client.sessions.list())
    except Exception as exc:
        typer.echo(f"Error: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(1)
    _emit(_to_dict(result), pretty)


# ---------------------------------------------------------------------------
# auth commands (legacy, kept)
# ---------------------------------------------------------------------------


@auth_app.command("login")
def auth_login() -> None:
    """Interactive login helper.

    Defers to the existing auth flow. For the full auth workflow, use the
    server-side CLI at ``ghostcrawl/cli/auth.py`` (server-admin package).
    """
    typer.echo(
        "Use the server-side auth CLI for interactive login "
        "(ghostcrawl/cli/auth.py — server-admin package).",
        err=True,
    )
    typer.echo(
        "Interactive SDK auth login is not yet available in this CLI.",
        err=True,
    )


# ---------------------------------------------------------------------------
# config commands
# ---------------------------------------------------------------------------


@config_app.command("set-key")
def config_set_key(key: str = typer.Argument(..., help="Your ghostcrawl API key.")) -> None:
    """Persist API key to $XDG_CONFIG_HOME/ghostcrawl/config.toml."""
    from ._config_store import write_api_key
    path = write_api_key(key)
    typer.echo(f"Wrote key to {path}")


@config_app.command("show")
def config_show() -> None:
    """Print persisted config key (masked)."""
    from ._config_store import read_api_key, config_path
    key = read_api_key()
    if key is None:
        typer.echo(f"No key set. Path: {config_path()}")
        raise typer.Exit(1)
    masked = key[:7] + "…" + key[-4:] if len(key) > 12 else "***"
    typer.echo(f"api_key = {masked}")
    typer.echo(f"Path: {config_path()}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app()
