"""Real stdio round-trips: spawn the server the way .mcp.json does."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "server" / "awen_mcp.py"
ENV = {"AWEN_BASE_URL": "https://awen.test"}


def _args() -> list[str]:
    cfg = json.loads((ROOT / ".mcp.json").read_text())["mcpServers"]["awen"]
    return [a.replace("${CLAUDE_PLUGIN_ROOT}", str(ROOT)) for a in cfg["args"]]


def test_mcp_json_runs_the_bundled_file_directly() -> None:
    cfg = json.loads((ROOT / ".mcp.json").read_text())["mcpServers"]["awen"]
    assert cfg["command"] == "python3"
    assert _args() == ["-I", str(SERVER)]


def test_raw_json_rpc_session() -> None:
    lines = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2025-06-18", "capabilities": {}},
        },
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "get_next_section", "arguments": {}},
        },
    ]
    stdin = "".join(json.dumps(m) + "\n" for m in lines) + "not json\n"
    proc = subprocess.run(
        [sys.executable, *_args()],
        input=stdin.encode(),
        capture_output=True,
        env=ENV,
        timeout=20,
    )
    assert proc.returncode == 0, proc.stderr
    replies = [json.loads(x) for x in proc.stdout.decode().splitlines()]
    assert [r["id"] for r in replies] == [1, 2, 3, None]
    assert replies[0]["result"]["protocolVersion"] == "2025-06-18"
    names = {t["name"] for t in replies[1]["result"]["tools"]}
    assert names == {"start_review", "get_next_section", "submit_checkpoint"}
    assert replies[2]["result"]["isError"] is True
    assert "start_review" in replies[2]["result"]["content"][0]["text"]
    assert replies[3]["error"]["code"] == -32700


def test_bad_base_url_exits_cleanly() -> None:
    proc = subprocess.run(
        [sys.executable, *_args()],
        input=b"",
        capture_output=True,
        env={"AWEN_BASE_URL": "http://awen.press"},
        timeout=20,
    )
    assert proc.returncode == 2
    assert b"must be https" in proc.stderr and proc.stdout == b""


def test_official_mcp_client_interop() -> None:
    mcp = pytest.importorskip("mcp")
    from mcp.client.stdio import stdio_client

    async def run() -> tuple[set[str], bool, str]:
        params = mcp.StdioServerParameters(
            command=sys.executable, args=_args(), env=ENV
        )
        async with stdio_client(params) as (r, w), mcp.ClientSession(r, w) as s:
            await s.initialize()
            names = {t.name for t in (await s.list_tools()).tools}
            res = await s.call_tool("get_next_section", {})
            return names, bool(res.isError), res.content[0].text  # type: ignore[union-attr]

    names, is_error, text = asyncio.run(run())
    assert names == {"start_review", "get_next_section", "submit_checkpoint"}
    assert is_error and "start_review" in text
