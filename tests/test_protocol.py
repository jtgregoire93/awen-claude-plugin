"""The MCP layer: JSON-RPC handling, tool errors, version negotiation."""

from __future__ import annotations

import io
import json
import re
from pathlib import Path
from typing import Any

import pytest

import awen_mcp
from awen_mcp import PROTOCOL_VERSIONS, ReviewCore, build_server

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://awen.test"
SESSION = "S" * 43


def _rpc(method: str, params: dict[str, Any] | None = None, rid: Any = 1) -> Any:
    msg: dict[str, Any] = {"jsonrpc": "2.0", "id": rid, "method": method}
    if params is not None:
        msg["params"] = params
    return msg


@pytest.fixture
def srv() -> awen_mcp.Server:
    return build_server(ReviewCore(BASE))


def _text(reply: dict[str, Any]) -> str:
    return reply["result"]["content"][0]["text"]


@pytest.mark.parametrize("asked", PROTOCOL_VERSIONS)
def test_initialize_echoes_a_supported_version(
    srv: awen_mcp.Server, asked: str
) -> None:
    res = srv.handle(_rpc("initialize", {"protocolVersion": asked}))["result"]  # type: ignore[index]
    assert res["protocolVersion"] == asked
    assert res["capabilities"] == {"tools": {"listChanged": False}}
    assert res["serverInfo"] == {"name": "awen", "version": awen_mcp.VERSION}


def test_initialize_offers_latest_for_unknown_version(srv: awen_mcp.Server) -> None:
    res = srv.handle(_rpc("initialize", {"protocolVersion": "1999-01-01"}))
    assert res["result"]["protocolVersion"] == PROTOCOL_VERSIONS[0]  # type: ignore[index]


def test_notifications_and_responses_get_no_reply(srv: awen_mcp.Server) -> None:
    assert srv.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None
    assert srv.handle({"jsonrpc": "2.0", "id": 9, "result": {}}) is None


def test_ping_and_unknown_method(srv: awen_mcp.Server) -> None:
    assert srv.handle(_rpc("ping")) == {"jsonrpc": "2.0", "id": 1, "result": {}}
    err = srv.handle(_rpc("resources/list"))["error"]  # type: ignore[index]
    assert err["code"] == -32601


@pytest.mark.parametrize(
    "msg",
    [[], "x", {"id": 1, "method": "ping"}, _rpc("ping") | {"params": [1]}],
)
def test_malformed_requests(srv: awen_mcp.Server, msg: Any) -> None:
    reply = srv.handle(msg)
    assert reply is not None and reply["error"]["code"] in (-32600, -32602)


def test_tool_list_shape(srv: awen_mcp.Server) -> None:
    tools = srv.handle(_rpc("tools/list"))["result"]["tools"]  # type: ignore[index]
    for t in tools:
        assert t["inputSchema"]["type"] == "object"
        assert t["description"] and t["annotations"]["title"] == t["title"]
    by_name = {t["name"]: t for t in tools}
    assert by_name["get_next_section"]["annotations"]["readOnlyHint"] is True
    assert by_name["start_review"]["inputSchema"]["required"] == [
        "session_url",
        "model",
    ]


@pytest.mark.parametrize("name", ["nope", None, ["start_review"]])
def test_unknown_tool_is_a_protocol_error(srv: awen_mcp.Server, name: Any) -> None:
    reply = srv.handle(_rpc("tools/call", {"name": name, "arguments": {}}))
    assert reply["error"]["code"] == -32602  # type: ignore[index]


@pytest.mark.parametrize(
    "args, problem",
    [
        ({}, "missing argument: session_url"),
        ({"session_url": 1, "model": "m"}, "session_url must be a string"),
        ({"session_url": "x", "model": "m", "name": 3}, "name must be a string"),
    ],
)
def test_bad_arguments_are_tool_errors(
    srv: awen_mcp.Server, args: dict[str, Any], problem: str
) -> None:
    reply = srv.handle(_rpc("tools/call", {"name": "start_review", "arguments": args}))
    assert reply["result"]["isError"] is True  # type: ignore[index]
    assert problem in _text(reply)  # type: ignore[arg-type]


def test_payload_must_be_an_object(srv: awen_mcp.Server) -> None:
    reply = srv.handle(
        _rpc("tools/call", {"name": "submit_checkpoint", "arguments": {"payload": []}})
    )
    assert "payload must be a object" in _text(reply)  # type: ignore[arg-type]


def test_review_errors_reach_the_model(srv: awen_mcp.Server) -> None:
    reply = srv.handle(
        _rpc(
            "tools/call",
            {"name": "start_review", "arguments": {"session_url": "x", "model": "m"}},
        )
    )
    assert reply["result"]["isError"] is True  # type: ignore[index]
    assert "must be an Awen review link" in _text(reply)  # type: ignore[arg-type]


def test_unexpected_errors_are_not_echoed() -> None:
    def boom(req: awen_mcp.Request) -> awen_mcp.Response:
        raise RuntimeError(f"secret {req.url}")

    srv = build_server(ReviewCore(BASE, transport=boom))
    args = {"session_url": f"{BASE}/review/{SESSION}", "model": "m"}
    reply = srv.handle(_rpc("tools/call", {"name": "start_review", "arguments": args}))
    text = _text(reply)  # type: ignore[arg-type]
    assert "internal error (RuntimeError)" in text
    assert SESSION not in text and "secret" not in text


def test_serve_handles_blank_lines_batches_and_garbage(srv: awen_mcp.Server) -> None:
    stdin = io.BytesIO(
        b"\n"
        + json.dumps([_rpc("ping", rid=1), {"jsonrpc": "2.0", "method": "n"}]).encode()
        + b"\n{oops\n"
        + json.dumps(_rpc("ping", rid="a")).encode()
        + b"\n"
    )
    stdout = io.BytesIO()
    srv.serve(stdin, stdout)
    replies = [json.loads(x) for x in stdout.getvalue().splitlines()]
    assert replies[0] == [{"jsonrpc": "2.0", "id": 1, "result": {}}]
    assert replies[1]["error"]["code"] == -32700
    assert replies[2]["id"] == "a"


def test_versions_match() -> None:
    manifest = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    pyproject = (ROOT / "pyproject.toml").read_text()
    project = re.search(r'^version = "([^"]+)"$', pyproject, re.M)
    assert project is not None
    assert manifest["version"] == project.group(1) == awen_mcp.VERSION
    assert re.fullmatch(r"\d+\.\d+\.\d+", awen_mcp.VERSION)
