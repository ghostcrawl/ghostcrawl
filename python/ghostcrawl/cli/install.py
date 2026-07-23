"""SDK install-token plumbing.

This module is the ``run(argv)`` entry point exercised by
``sdks/python/tests/test_cli_install_token.py``. It implements the token-write
slice of ``ghostcrawl install`` independently of the binary-download flow in
``ghostcrawl.cli.main`` so the unit tests can drive it without HTTP plumbing.

Behaviour:

* ``--token VALUE``       — the license token string (must start with ``ghc_``).
* ``--token-path PATH``   — file to write the token to (atomic, mode 0o600).

Atomic write: write to ``<path>.tmp`` then ``Path.replace()``.
The phone-home reader opens the file fresh each cycle, so an atomic rename is
invisible to it. POSIX rename(2) preserves the 0o600 mode bits set on the temp
file.

Return value: an integer exit code (0 on success, 1 on user error). Callers
that prefer typer's ``Exit`` semantics can use ``main.install`` instead.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ghostcrawl install",
        description="Write a GhostCrawl license token to disk.",
    )
    parser.add_argument(
        "--token",
        required=True,
        help="The license token string (must start with 'ghc_').",
    )
    parser.add_argument(
        "--token-path",
        required=True,
        type=Path,
        help="Destination path for the token file (mode 0o600).",
    )
    return parser


def run(argv: Sequence[str]) -> int:
    """Parse ``argv`` and write the token. Returns the process exit code."""
    parser = _build_parser()
    try:
        args = parser.parse_args(list(argv))
    except SystemExit as exc:
        # argparse exits 2 on parse errors; surface as exit-code 1 for callers
        # that treat any non-zero as failure.
        return int(exc.code) if isinstance(exc.code, int) else 1

    token: str = args.token
    token_path: Path = args.token_path

    # Reject empty token (whitespace-only counts as empty).
    if not token or not token.strip():
        print("Error: --token must not be empty.", file=sys.stderr)
        return 1

    token = token.strip()

    # Token format gate: the token must start with "ghc_".
    if not token.startswith("ghc_"):
        print("Error: token format invalid (expect ghc_...)", file=sys.stderr)
        return 1

    # Ensure the install directory exists at mode 0o700.
    install_dir = token_path.parent
    if str(install_dir):
        install_dir.mkdir(parents=True, exist_ok=True)
        try:
            install_dir.chmod(0o700)
        except OSError:
            # Non-fatal — some filesystems (CIFS, FAT) don't support chmod.
            pass

    # Atomic write: write tmp + chmod, then Path.replace().
    tmp = token_path.with_suffix(token_path.suffix + ".tmp")
    tmp.write_text(token)
    try:
        tmp.chmod(0o600)
    except OSError:
        pass
    tmp.replace(token_path)  # atomic POSIX rename — preserves 0o600

    print(f"License token written to {token_path}")
    print(
        "A future release will wire the container pull + start flow "
        "against the registry."
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(run(sys.argv[1:]))
