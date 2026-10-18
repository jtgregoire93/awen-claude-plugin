"""Real stdio round-trip: spawn the server process, speak MCP to it."""

from __future__ import annotations

import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def _run() -> tuple[set[str], bool, str]:
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "awen_mcp"],
        env={"AWEN_BASE_URL": "https://awen.test"},
    )
    async with stdio_client(params) as (r, w), ClientSession(r, w) as session:
        await session.initialize()
        names = {t.name for t in (await session.list_tools()).tools}
        res = await session.call_tool("get_next_section", {})
        text = res.content[0].text  # type: ignore[union-attr]
        return names, bool(res.isError), text


def test_stdio_lists_three_tools_and_gates_without_session() -> None:
    names, is_error, text = asyncio.run(_run())
    assert names == {"start_review", "get_next_section", "submit_checkpoint"}
    assert is_error and "start_review" in text
