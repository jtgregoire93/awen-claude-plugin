"""FastMCP wiring: exactly three tools, bound to ReviewCore."""

from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from .core import DEFAULT_BASE_URL, ReviewCore


def build_server(core: ReviewCore | None = None) -> FastMCP:
    core = core or ReviewCore(os.environ.get("AWEN_BASE_URL") or DEFAULT_BASE_URL)
    mcp = FastMCP(
        "awen",
        instructions=(
            "Runs a gated Awen beta-read. start_review, then alternate "
            "get_next_section and submit_checkpoint until done. Follow the "
            "rules and rubric start_review returns, exactly."
        ),
    )

    @mcp.tool()
    def start_review(session_url: str, model: str, name: str = "") -> dict[str, Any]:
        """Begin a beta-read from the author's Awen review link. Returns the
        book's rules, rubric and submission schema."""
        return core.start_review(session_url, model, name)

    @mcp.tool()
    def get_next_section() -> dict[str, Any]:
        """Fetch the next unread section. Awen decides which one."""
        return core.get_next_section()

    @mcp.tool()
    def submit_checkpoint(payload: dict[str, Any]) -> dict[str, Any]:
        """Submit the ratings for the section just read, as the schema from
        start_review describes."""
        return core.submit_checkpoint(payload)

    return mcp


def run_stdio() -> None:
    build_server().run(transport="stdio")
