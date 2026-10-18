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
- `.mcp.json` runs `uv run --frozen`, so `uv.lock` must be committed and
  current. Run `uv lock` after any dependency change.
- Each release raises `version` in both `.claude-plugin/plugin.json` and
  `pyproject.toml`. The directory picks up new commits on `main`.
- The README's "What it sends, and where" section must match what the code
  does. The directory's security scan checks for undisclosed traffic.

## Commands

```sh
uv sync
uv run pytest
uv run ruff check .
claude plugin validate . --strict
```
