"""GhostCrawl typer CLI entry point.

The ``app`` object here is registered as the ``ghostcrawl`` shell command
via ``[project.scripts]`` in ``pyproject.toml``::

    ghostcrawl = "ghostcrawl.cli:app"

Subcommands:
    scrape  — scrape a URL, emit JSON to stdout
    crawl   — start a crawl run (v1.3 /v1/crawl-runs, NOT legacy /v1/crawl)
    session — session management (list)
    auth    — auth helpers (login)
"""

from .main import app

__all__ = ["app"]
