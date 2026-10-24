# awen-claude-plugin — Claude Code notes

Public repo. The `awen` Claude plugin: a connection to Awen's hosted review
MCP server (`https://awen.press/mcp`), plus the `awen-review` skill. The
Awen platform itself is closed source and lives in the private `awen` repo.
Nothing from it is copied here.

## Rules

- The plugin is the repository root. The Claude directory submission is
  locked to this repo and folder, so don't move `.claude-plugin/` into a
  subfolder.
- The API contract lives in the private repo at
  `awen/api/routers/review_surface.py` (`/api/review/{token}/...`). Change both
  sides together.
- `.mcp.json` points at the hosted server (`type: http`). The server lives in
  the private repo at `awen/api/routers/mcp.py` and `awen/api/mcp_review.py`;
  tool names, schemas, descriptions and annotations here (README, skill) must
  match it. Ship the server before merging a plugin change that depends on it.
- `server/awen_mcp.py` is the documented local/offline fallback, not wired
  into `.mcp.json`. One file, standard library only, runnable on Python 3.9
  (the macOS system Python). Ruff targets py39, and
  `/usr/bin/python3 -I server/awen_mcp.py` is the check.
- `pyproject.toml` and `uv.lock` are for dev tools only. Users never run uv.
- Each release raises `version` in `.claude-plugin/plugin.json`,
  `pyproject.toml`, and `VERSION` in the server (a test checks they match).
  The directory picks up new commits on `main`.
- The listing icon was fixed when the plugin was first saved in the developer
  portal. Replacing the icon file later doesn't change the listing. Never
  write an image's path in a file here, in backticks or a code block: the
  directory holds the plugin for review when it does.
- The README's "What it sends, and where" section must match what the code
  does. The directory's security scan checks for undisclosed traffic.

## Commands

```sh
uv sync
uv run pytest
uv run ruff check .
claude plugin validate . --strict
```
