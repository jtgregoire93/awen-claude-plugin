"""CLI entrypoint for awen-mcp (stdio only)."""

from __future__ import annotations

import sys


def main() -> int:
    from .server import run_stdio

    try:
        run_stdio()
    except ValueError as exc:  # bad AWEN_BASE_URL
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
