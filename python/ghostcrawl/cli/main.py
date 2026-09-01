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
Read path precedence: GHOSTCRAWL_API_KEY env > ./ghostcrawl.toml (cwd) >
~/.config/ghostcrawl/config.toml (fallback for existing users).
In `init` only: interactive hidden prompt (bash history safe — no arg path).
"""

from __future__ import annotations

import asyncio
import json
import os
import pathlib
import tempfile
import time
from typing import Any

import typer

from ghostcrawl import GhostCrawl, GhostCrawlClient
from ghostcrawl.cli._batch import run_batch
from ghostcrawl.errors.identity_errors import AuthenticationError


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

__version__ = "2.3.6"  # keep in sync with sdks/python/pyproject.toml (test_version_matches_pyproject guards drift)


def _version_callback(value: bool) -> None:
    """Typer --version callback. Prints version and exits 0."""
    if value:
        typer.echo(f"ghostcrawl {__version__}")
        raise typer.Exit(code=0)


app = typer.Typer(
    name="ghostcrawl",
    # Version banner MUST track __version__ (2.3.6) — check_version_stamp.sh gates
    # this exact line so a stale literal (the old v0.5.0 drift) cannot linger.
    help="GhostCrawl command-line interface (v2.3.6).",
    no_args_is_help=True,
    add_completion=False,
)


@app.callback()
def _main(
    version: bool | None = typer.Option(
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


# Working-directory config file name. The cwd config takes precedence over
# the ~/.config fallback so a project can pin its own key next to its code.
_CWD_CONFIG_FILENAME = "ghostcrawl.toml"


def _cwd_config_path() -> pathlib.Path:
    """Return the working-directory config path (``./ghostcrawl.toml``)."""
    return pathlib.Path.cwd() / _CWD_CONFIG_FILENAME


def _parse_api_key_from_file(path: pathlib.Path) -> str | None:
    """Parse ``api_key = "..."`` from a TOML-ish config file (comment-safe)."""
    if not path.exists():
        return None
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("api_key"):
                parts = line.split("=", 1)
                if len(parts) == 2:
                    val = parts[1].strip().strip('"').strip("'")
                    return val if val else None
    except OSError:
        return None
    return None


def _read_config_key() -> str | None:
    """Read api_key from ~/.config config.toml. None if file absent or key missing."""
    return _parse_api_key_from_file(_config_path())


def _read_cwd_config_key() -> str | None:
    """Read api_key from ``./ghostcrawl.toml``. None if file absent or key missing."""
    return _parse_api_key_from_file(_cwd_config_path())


def _resolve_api_key() -> str | None:
    """Key resolution: env WINS, then the working-dir file, then ~/.config.

    Resolution order (highest priority first):
        1. ``GHOSTCRAWL_API_KEY`` environment variable
        2. ``./ghostcrawl.toml`` (working directory)
        3. ``~/.config/ghostcrawl/config.toml`` (fallback for existing users,
           via the legacy reader → ``_config_store``)
    """
    env_key = os.environ.get("GHOSTCRAWL_API_KEY", "").strip()
    if env_key:
        return env_key
    cwd_key = _read_cwd_config_key()
    if cwd_key:
        return cwd_key
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
    return None


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


def _write_config(api_key: str) -> pathlib.Path:
    """Persist *api_key* to config.toml with hardened permissions.

    Directory chmod 0o700, file chmod 0o600 (owner read/write only) — the key
    is never world-readable. Returns the config path.
    """
    config_dir = _config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    config_dir.chmod(0o700)
    config_path = _config_path()
    config_path.write_text(f'api_key = "{api_key}"\n', encoding="utf-8")
    config_path.chmod(0o600)
    return config_path


def _write_cwd_config(api_key: str) -> pathlib.Path:
    """Persist *api_key* to ``./ghostcrawl.toml`` (cwd default), chmod 0o600.

    Returns the absolute path written so the caller can surface it to the user.
    The key is never world-readable.
    """
    config_path = _cwd_config_path().resolve()
    config_path.write_text(f'api_key = "{api_key}"\n', encoding="utf-8")
    try:
        config_path.chmod(0o600)
    except OSError:  # pragma: no cover - non-POSIX / permission edge
        pass
    return config_path


def _safe_close(client: Any) -> None:
    """Best-effort close of a sync client (no-op if it has no ``close``)."""
    close = getattr(client, "close", None)
    if callable(close):
        try:
            close()
        except Exception:  # pragma: no cover - cleanup is best-effort
            pass


def _probe_me_no_spend(api_key: str, base_url: str) -> bool:
    """No-spend key probe against ``GET /v1/me``.

    Returns ``True`` ONLY on a 200 (the endpoint exists AND accepts this key —
    validated with zero scrape spend, per 189-06). Any other status (404/405 =
    endpoint absent; 401/403 = does not accept this key type) OR a transport
    error returns ``False`` so the caller falls back to the real ``POST /v1/scrape``
    auth path — a ``/v1/me`` non-200 is NEVER a final auth verdict.

    Only attempted for live-format keys (``gck_live_``): the no-spend probe is
    meaningful only for a real API key; other formats validate via the real auth
    path directly. The key travels only in the ``Authorization`` header over
    HTTPS and is never logged.
    """
    if not api_key.startswith("gck_live_"):
        return False
    import httpx

    url = base_url.rstrip("/") + "/v1/me"
    try:
        resp = httpx.get(
            url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=httpx.Timeout(6.0, connect=3.0),
        )
    except Exception:  # noqa: BLE001 - any transport error → fall back to scrape
        return False
    return resp.status_code == 200


def _validate_key(api_key: str, base_url: str) -> None:
    """Validate *api_key* against the REAL auth path a working key passes.

    Order: (1) prefer a no-spend ``GET /v1/me``; (2) if it cannot validate
    this key type, fall back to a trivial ``POST /v1/scrape`` — the exact auth
    path a working key passes. Raises ``AuthenticationError`` on genuine
    rejection; other exceptions propagate for the caller to downgrade to a single
    honest message. Never calls ``/v1/profiles`` (the old false-negative path).
    """
    if _probe_me_no_spend(api_key, base_url):
        return
    # Real auth path — a minimal scrape of a trivial URL via the sync client
    # (no per-call asyncio.run; the footgun the CLI used to carry).
    client = GhostCrawl(token=api_key, base_url=base_url)
    try:
        client.scrape(url="https://example.com", render_js=False)
    finally:
        _safe_close(client)


# ---------------------------------------------------------------------------
# Self-host init kit
# ---------------------------------------------------------------------------

# Customer-safe image tag — never expose engine codenames or internal mechanics
# on this surface (self-host ships as ghostcrawl:2.3.6).
_SELF_HOST_IMAGE = "ghostcrawl:2.3.6"
_SELF_HOST_BASE_URL = "http://localhost:8080"

_SELF_HOST_CONFIG_TEMPLATE = f"""# GhostCrawl self-host configuration.
# The SDK/CLI talks to your local GhostCrawl container — no cloud key required.
# Point base_url at wherever you expose the container (default below).
base_url = "{_SELF_HOST_BASE_URL}"

# A self-host deployment does not need a cloud API key. If your deployment is
# configured to require one, uncomment and set it here (kept out of version control):
# api_key = "your-self-host-key"
"""

_SELF_HOST_ENV_TEMPLATE = """# GhostCrawl self-host environment.
# Copy/edit as needed, then `docker compose up -d`.

# Host port the API is published on (matches base_url in ghostcrawl.toml).
HOST_PORT=8080

# License key for your self-host deployment (obtain from your account portal).
GHOSTCRAWL_LICENSE_KEY=
"""

_SELF_HOST_COMPOSE_TEMPLATE = f"""# GhostCrawl self-host stack.
# Start with:  docker compose up -d
# Then point the SDK/CLI at http://localhost:8080 (see ghostcrawl.toml).
services:
  ghostcrawl:
    image: {_SELF_HOST_IMAGE}
    restart: unless-stopped
    ports:
      - "${{HOST_PORT:-8080}}:8080"
    environment:
      GHOSTCRAWL_LICENSE_KEY: "${{GHOSTCRAWL_LICENSE_KEY:-}}"
    # The onefile extracts to an exec-capable tmpfs at runtime.
    tmpfs:
      - /run/gc:mode=1777,exec
    healthcheck:
      test: ["CMD", "python3", "/healthz"]
      interval: 30s
      timeout: 5s
      retries: 5
"""

_SELF_HOST_README_TEMPLATE = f"""# GhostCrawl self-host kit

This directory contains everything you need to run GhostCrawl locally and point
the SDK/CLI at it — no cloud account required.

## Files

- `docker-compose.yml` — the {_SELF_HOST_IMAGE} service.
- `.env` — host port and license key.
- `ghostcrawl.toml` — SDK/CLI config with `base_url` pointed at your local instance.

## Run it

```bash
# 1. Set your license key (and any options) in .env
#    GHOSTCRAWL_LICENSE_KEY=...

# 2. Start the stack
docker compose up -d

# 3. Verify it is healthy
docker compose ps

# 4. Use the SDK/CLI against your local instance (reads ./ghostcrawl.toml)
ghostcrawl scrape https://example.com
```

The SDK resolves configuration with the precedence
`GHOSTCRAWL_API_KEY` env > `./ghostcrawl.toml` (this file) > `~/.config`.
Because `base_url` here points at `{_SELF_HOST_BASE_URL}`, every request stays
on your machine.
"""


def _write_self_host_kit() -> list[pathlib.Path]:
    """Drop a ready-to-run self-host kit into the working directory.

    Writes ``ghostcrawl.toml`` (base_url → local), ``docker-compose.yml``, ``.env``,
    and ``README.md``. Requires NO cloud key. Returns the written paths. Existing
    files are left untouched (never clobber a user's edits).
    """
    cwd = pathlib.Path.cwd()
    files = {
        "ghostcrawl.toml": _SELF_HOST_CONFIG_TEMPLATE,
        "docker-compose.yml": _SELF_HOST_COMPOSE_TEMPLATE,
        ".env": _SELF_HOST_ENV_TEMPLATE,
        "README.md": _SELF_HOST_README_TEMPLATE,
    }
    written: list[pathlib.Path] = []
    for name, content in files.items():
        path = (cwd / name).resolve()
        if path.exists():
            typer.echo(f"Skipping existing {name} (not overwritten).")
            written.append(path)
            continue
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written


@app.command()
def init(
    self_host: bool = typer.Option(
        False,
        "--self-host",
        help=(
            "Drop a ready-to-run self-host kit (ghostcrawl.toml + docker-compose.yml "
            "+ .env + README.md) into the working directory. Needs no cloud key."
        ),
    ),
) -> None:
    """Interactive first-time setup: resolve/prompt for the API key and write ./ghostcrawl.toml.

    Writes ``./ghostcrawl.toml`` in the working directory (chmod 0o600) by default
    and prints the exact absolute path written. Validates the key against
    the real auth path — a no-spend ``GET /v1/me`` when it accepts the key type,
    otherwise a trivial ``POST /v1/scrape`` (the same path a working ``gck_live_``
    key passes). Prints exactly ONE truthful outcome.

    Config precedence: ``GHOSTCRAWL_API_KEY`` env > ``./ghostcrawl.toml``
    (cwd) > ``~/.config/ghostcrawl/config.toml`` (fallback for existing users);
    the resolution order is surfaced in the output.

    With ``--self-host``: instead of prompting for a cloud key, drop a
    ready-to-run kit (``ghostcrawl.toml`` + ``docker-compose.yml`` + ``.env`` +
    ``README.md``) into the working directory. The SDK/CLI then works fully against
    the local self-host ``base_url`` with no cloud dependency.

    Security: the key is entered via hidden prompt only (never a CLI argument, so
    not visible in ps(1) or shell history) and is never echoed to the terminal.
    """
    if self_host:
        written = _write_self_host_kit()
        typer.echo("Self-host kit written:")
        for path in written:
            typer.echo(f"  {path}")
        typer.echo(
            "Next: set GHOSTCRAWL_LICENSE_KEY in .env, run `docker compose up -d`, "
            "then `ghostcrawl scrape https://example.com`."
        )
        return

    base_url = os.environ.get("GHOSTCRAWL_BASE_URL", "").strip() or "https://api.ghostcrawl.io"

    # Surface the resolution order (env > cwd file > home fallback).
    typer.echo(
        "Resolution order: GHOSTCRAWL_API_KEY env > "
        "./ghostcrawl.toml > ~/.config/ghostcrawl/config.toml"
    )

    env_key = os.environ.get("GHOSTCRAWL_API_KEY", "").strip()

    while True:
        if env_key:
            api_key: str = env_key
            typer.echo(
                "Using the key from GHOSTCRAWL_API_KEY (env overrides the config file)."
            )
        else:
            api_key = typer.prompt(
                "GhostCrawl API key",
                hide_input=True,
                prompt_suffix=": ",
            )

        try:
            _validate_key(api_key, base_url)
        except AuthenticationError:
            typer.echo(
                "Key rejected (401). Run `ghostcrawl init` again with the correct key.",
                err=True,
            )
            raise typer.Exit(code=1) from None
        except Exception as exc:  # noqa: BLE001 - one honest outcome, never both
            # Single honest message (never a warning AND "validated"): save so the
            # user isn't blocked by a transient network hiccup, but say so plainly.
            config_path = _write_cwd_config(api_key)
            typer.echo(
                f"Saved to {config_path}, but could not verify the key "
                f"(check network/key): {type(exc).__name__}.",
                err=True,
            )
            break

        config_path = _write_cwd_config(api_key)
        typer.echo(f"Config written to {config_path}; key validated.")
        break


# ---------------------------------------------------------------------------
# install command
# ---------------------------------------------------------------------------


def _is_cloud_mode(license_token_path: pathlib.Path | None) -> bool:
    """Detect the hosted-API (cloud) user.

    Cloud = the base URL is the hosted API (``api.ghostcrawl.io``) AND there is
    no self-host signal — no ``--license-token``, no ``GHOSTCRAWL_BINARY_URL``,
    and no ``GHOSTCRAWL_LICENSE_KEY``. Any of those present means the user is
    setting up a self-host / local-engine install, which reaches the download
    path. Cloud users must never hit the ``GHOSTCRAWL_BINARY_URL`` wall.
    """
    base_url = (
        os.environ.get("GHOSTCRAWL_BASE_URL", "").strip() or "https://api.ghostcrawl.io"
    )
    is_hosted_api = "api.ghostcrawl.io" in base_url
    has_selfhost_signal = bool(
        license_token_path is not None
        or os.environ.get("GHOSTCRAWL_BINARY_URL", "").strip()
        or os.environ.get("GHOSTCRAWL_LICENSE_KEY", "").strip()
    )
    return is_hosted_api and not has_selfhost_signal


@app.command()
def install(
    os_target: str = typer.Option("linux-x86_64", "--os", help="Target OS/arch (e.g. linux-x86_64)."),
    license_token_path: pathlib.Path | None = typer.Option(
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

    Mode-aware: hosted-API (cloud) users have nothing to install and get a
    friendly exit 0 — never the GHOSTCRAWL_BINARY_URL wall. Only self-host /
    local-engine setups reach the binary-download path.
    """
    import httpx

    # ---- Cloud users need no local engine — friendly exit before any wall ----
    if _is_cloud_mode(license_token_path):
        typer.echo(
            "You're using the hosted GhostCrawl API — `install` is only for "
            "self-host / local-engine deployments. Nothing to install."
        )
        raise typer.Exit(code=0)

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
        raise typer.Exit(1) from None
    except Exception as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1) from None

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
    preset: str | None = typer.Option(
        None,
        "--preset",
        help=(
            "Expand a locked scrape-param bundle: "
            "screenshot | fetch | premium-render | fast-html | resilient. "
            "Explicit flags override preset values."
        ),
    ),
    output: pathlib.Path | None = typer.Option(
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
        raise typer.Exit(1) from None

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
        raise typer.Exit(1) from None
    _emit(summary, pretty=True)


# ---------------------------------------------------------------------------
# extract command
# ---------------------------------------------------------------------------


@app.command()
def extract(
    url: str = typer.Argument(..., help="URL to extract structured data from."),
    schema_path: pathlib.Path | None = typer.Option(None, "--schema", help="Path to JSON schema file."),
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
        raise typer.Exit(1) from None
    except Exception as exc:
        typer.echo(f"Error: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(1) from None
    _emit(_to_dict(result), pretty)


# ---------------------------------------------------------------------------
# crawl command (legacy, kept)
# ---------------------------------------------------------------------------


@app.command()
def crawl(
    url: str = typer.Argument(..., help="Seed URL for the crawl."),
    max_depth: int = typer.Option(2, "--max-depth", help="Maximum crawl depth."),
    out: str | None = typer.Option(None, "--out", help="Output file path (JSON)."),
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
        raise typer.Exit(1) from None
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
        raise typer.Exit(1) from None
    _emit(_to_dict(result), pretty)


# ---------------------------------------------------------------------------
# content command (parity with the Node CLI's `content`)
# ---------------------------------------------------------------------------


@app.command()
def content(
    url: str = typer.Argument(..., help="URL to fetch content from."),
    engine: str = typer.Option(
        "auto", "--engine", help="Browser engine (auto | chrome | firefox | webkit)."
    ),
    pretty: bool = typer.Option(False, "--pretty", help="Indent JSON output."),
) -> None:
    """Fetch a URL's rendered content via /v1/content."""
    client = _get_client()
    try:
        result = _run(client.content(url=url, engine=engine))
    except Exception as exc:
        typer.echo(f"Error: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(1) from None
    _emit(_to_dict(result), pretty)


# ---------------------------------------------------------------------------
# pdf command (parity with the Node CLI's `pdf`)
# ---------------------------------------------------------------------------


@app.command()
def pdf(
    url: str = typer.Argument(..., help="URL to render to PDF."),
    paper_format: str = typer.Option(
        "a4", "--paper-format", help="Paper format (a4 | letter | legal | tabloid)."
    ),
    landscape: bool = typer.Option(False, "--landscape", help="Landscape orientation."),
    out: pathlib.Path | None = typer.Option(
        None, "--out", help="Output file path (default: a temp file)."
    ),
    pretty: bool = typer.Option(False, "--pretty", help="Indent JSON output."),
) -> None:
    """Render a URL to PDF via /v1/pdf (Chrome-only; writes PDF bytes to a file).

    PDF output is Chrome-only, so — mirroring the Node CLI — the engine is
    pinned to ``"chrome"`` rather than exposed as a flag.
    """
    client = _get_client()
    try:
        data = _run(
            client.pdf(url=url, paper_format=paper_format, landscape=landscape, engine="chrome")
        )
    except Exception as exc:
        typer.echo(f"Error: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(1) from None
    payload = bytes(data)
    dest = out if out is not None else (
        pathlib.Path(tempfile.gettempdir()) / f"ghostcrawl-page-{int(time.time() * 1000)}.pdf"
    )
    dest.write_bytes(payload)
    _emit({"url": url, "bytes": len(payload), "path": str(dest)}, pretty)


# ---------------------------------------------------------------------------
# screenshot command (parity with the Node CLI's `screenshot`)
# ---------------------------------------------------------------------------


@app.command()
def screenshot(
    url: str = typer.Argument(..., help="URL to screenshot."),
    output_format: str = typer.Option("png", "--format", help="Image format (png | jpeg | webp)."),
    full_page: bool = typer.Option(False, "--full-page", help="Capture the full scrollable page."),
    selector: str | None = typer.Option(
        None, "--selector", help="CSS selector scoping the capture to one element."
    ),
    out: pathlib.Path | None = typer.Option(
        None, "--out", help="Output file path (default: a temp file)."
    ),
    pretty: bool = typer.Option(False, "--pretty", help="Indent JSON output."),
) -> None:
    """Capture a screenshot via /v1/screenshot (writes image bytes to a file)."""
    client = _get_client()
    kwargs: dict = {"format": output_format, "full_page": full_page}
    if selector is not None:
        kwargs["screenshot_selector"] = selector
    try:
        data = _run(client.screenshot(url=url, **kwargs))
    except Exception as exc:
        typer.echo(f"Error: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(1) from None
    payload = bytes(data)
    dest = out if out is not None else (
        pathlib.Path(tempfile.gettempdir())
        / f"ghostcrawl-screenshot-{int(time.time() * 1000)}.{output_format}"
    )
    dest.write_bytes(payload)
    _emit({"url": url, "format": output_format, "bytes": len(payload), "path": str(dest)}, pretty)


# ---------------------------------------------------------------------------
# search command (parity with the Node CLI's `search`)
# ---------------------------------------------------------------------------


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query string."),
    engine: str = typer.Option("google", "--engine", help="Search backend (google | bing | duckduckgo)."),
    limit: int = typer.Option(10, "--limit", help="Max results (1-20)."),
    provider_key: str | None = typer.Option(
        None,
        "--provider-key",
        help=(
            "Your BYO search-backend API key (sent as "
            "X-Provider-Authorization: Bearer). Without it the API replies "
            "401 search_backend_key_missing."
        ),
    ),
    pretty: bool = typer.Option(False, "--pretty", help="Indent JSON output."),
) -> None:
    """Web search via /v1/search (BYO — needs your own search-backend key)."""
    client = _get_client()
    try:
        result = _run(
            client.search(query, engine=engine, limit=limit, provider_key=provider_key)
        )
    except Exception as exc:
        typer.echo(f"Error: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(1) from None
    _emit(_to_dict(result), pretty)


# ---------------------------------------------------------------------------
# crawl-runs command (parity with the Node CLI's flat `crawl-runs` list)
# ---------------------------------------------------------------------------


@app.command("crawl-runs")
def crawl_runs_list(
    pretty: bool = typer.Option(False, "--pretty", help="Indent JSON output."),
) -> None:
    """List crawl-run status via GET /v1/crawl-runs."""
    client = _get_client()
    crawl_runs = getattr(client, "crawl_runs", None)
    if crawl_runs is None:
        typer.echo("Error: crawl_runs sub-client missing on the client", err=True)
        raise typer.Exit(1)
    try:
        result = _run(crawl_runs.list())
    except Exception as exc:
        typer.echo(f"Error: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(1) from None
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
        raise typer.Exit(1) from None
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
    from ._config_store import config_path, read_api_key
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
