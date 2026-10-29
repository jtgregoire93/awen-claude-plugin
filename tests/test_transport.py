"""The real urllib transport against a local HTTP server."""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from awen_mcp import MAX_RESPONSE_BYTES, ReviewCore, ReviewError

SESSION = "S" * 43


class _Handler(BaseHTTPRequestHandler):
    mode = "json"
    hits: list[str] = []

    def do_GET(self) -> None:  # noqa: N802
        type(self).hits.append(self.path)
        if self.mode == "redirect":
            self.send_response(302)
            self.send_header("Location", "https://evil.test/x")
            self.end_headers()
            return
        if self.mode == "huge":
            body = b"[" + b"0," * MAX_RESPONSE_BYTES + b"0]"
        else:
            body = json.dumps({"error": "session not found"}).encode()
        self.send_response(404)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        pass


@pytest.fixture
def base() -> Iterator[str]:
    _Handler.hits = []
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"http://localhost:{srv.server_address[1]}"
    srv.shutdown()
    srv.server_close()


def _start(base: str) -> None:
    ReviewCore(base).start_review(f"{base}/review/{SESSION}", "m")


def test_error_status_is_read_not_raised(base: str) -> None:
    _Handler.mode = "json"
    with pytest.raises(ReviewError, match="HTTP 404.*session not found"):
        _start(base)
    assert _Handler.hits == [f"/api/review/{SESSION}/manifest?role=beta-reader"]


def test_redirects_are_not_followed(base: str) -> None:
    _Handler.mode = "redirect"
    with pytest.raises(ReviewError, match="redirect"):
        _start(base)
    assert len(_Handler.hits) == 1


def test_oversized_responses_are_refused(base: str) -> None:
    _Handler.mode = "huge"
    with pytest.raises(ReviewError, match="too large"):
        _start(base)


def test_unreachable_host_names_no_url() -> None:
    base = "http://localhost:9"  # discard port; nothing listens
    with pytest.raises(ReviewError, match=r"Could not reach Awen \(\w+\)") as exc:
        _start(base)
    assert SESSION not in str(exc.value)
