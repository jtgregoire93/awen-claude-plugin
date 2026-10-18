# awen-claude-plugin — Claude Code notes

Public repo. The `awen` Claude plugin: a stdio MCP client for Awen's review
API, plus the `awen-review` skill. The Awen platform itself is closed source
and lives in the private `awen` repo. Nothing from it is copied here.

## Rules

- The plugin is the repository root. The Claude directory submission is
  locked to this repo and folder, so don't move `.claude-plugin/` into a
  subfolder.
- The API contract lives in the private repo at
  `awen/api/routers/review_surface.py` (`/api/review/{token}/...`). Change both
  sides together.
- The server is one file, `server/awen_mcp.py`, standard library only, and
  `.mcp.json` runs it as `python3 -I`. Keep it that way: the directory holds
  any plugin that installs packages, and pydantic-core can't be bundled as
  readable source. Keep it runnable on Python 3.9, the macOS system Python.
  Ruff targets py39, and `/usr/bin/python3 -I server/awen_mcp.py` is the check.
- `pyproject.toml` and `uv.lock` are for dev tools only. Users never run uv.
- Each release raises `version` in `.claude-plugin/plugin.json`,
  `pyproject.toml`, and `VERSION` in the server (a test checks they match).
  The directory picks up new commits on `main`.
- `.claude-plugin/icon.png` became the listing icon when the plugin was first
  saved in the developer portal. Changing the file later doesn't change the
  listing.
- The README's "What it sends, and where" section must match what the code
  does. The directory's security scan checks for undisclosed traffic.

## Commands

```sh
uv sync
uv run pytest
uv run ruff check .
claude plugin validate . --strict
```
