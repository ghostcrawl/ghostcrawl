"""XDG-compliant config storage for ghostcrawl CLI API key.

Read/write companion for the existing main.py XDG config layout. Existing
main.py functions (_config_dir, _config_path, _read_config_key) remain for
backwards compat; this module is the authoritative read/write surface for
new commands (`config set-key`, `config show`) and is also lazily imported
by main.py's _resolve_api_key() chain.
"""
from __future__ import annotations
import os
import pathlib
from typing import Optional

_CONFIG_FILENAME = "config.toml"
_APP_NAME = "ghostcrawl"


def _xdg_config_home() -> pathlib.Path:
    raw = os.environ.get("XDG_CONFIG_HOME", "").strip()
    if raw:
        return pathlib.Path(raw)
    return pathlib.Path.home() / ".config"


def config_path() -> pathlib.Path:
    return _xdg_config_home() / _APP_NAME / _CONFIG_FILENAME


def write_api_key(key: str) -> pathlib.Path:
    """Persist API key as `api_key = "<key>"` in $XDG_CONFIG_HOME/ghostcrawl/config.toml."""
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    safe = key.replace("\\", "\\\\").replace('"', '\\"')
    path.write_text(f'api_key = "{safe}"\n', encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return path


def read_api_key() -> Optional[str]:
    """Read api_key from config; returns None if missing/unreadable."""
    path = config_path()
    if not path.exists():
        return None
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("api_key"):
                _, _, rhs = line.partition("=")
                rhs = rhs.strip()
                if rhs.startswith('"') and rhs.endswith('"'):
                    return rhs[1:-1].replace('\\"', '"').replace('\\\\', '\\')
                return rhs
    except OSError:
        return None
    return None
