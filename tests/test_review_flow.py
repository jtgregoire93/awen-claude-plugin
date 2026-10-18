"""ReviewCore against a fake Awen transport. No network."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlsplit

import pytest

from awen_mcp import Request, Response, ReviewCore, ReviewError, build_server

BASE = "https://awen.test"
SESSION = "S" * 43
REVIEWER = "R" * 43
URL = f"{BASE}/review/{SESSION}"


def _json(status: int, body: Any) -> Response:
    return Response(status, json.dumps(body).encode())


class FakeAwen:
    def __init__(self, sections: int = 2) -> None:
        self.sections = sections
        self.responded: set[int] = set()
        self.calls: list[Request] = []
        self.session_status = 200
        self.redirect = False

    def __call__(self, req: Request) -> Response:
        self.calls.append(req)
        if self.redirect:
            return Response(302, b"")
        path = urlsplit(req.url).path
        if self.session_status != 200:
            return _json(self.session_status, {"error": "session gone"})
        if path.endswith("/manifest"):
            return _json(
                200,
                {
                    "book_title": "T",
                    "section_count": self.sections,
                    # the real server fills the session token into manifest text
                    "rules": [f"Rule. link /api/review/{SESSION}/x"],
                    "guidance": "g",
                    "rubric": {"scale": "1-5"},
                    "checkpoints": [
                        {"index": i, "rating_node_ids": [f"scene-{i}"]}
                        for i in range(1, self.sections + 1)
                    ],
                    "roles": {
                        "beta-reader": {
                            "brief": f"POST /api/review/{SESSION}/sections/{{n}}",
                            "schema": {"type": "object"},
                        }
                    },
                },
            )
        if path.endswith("/reviewers"):
            return _json(200, {"reviewer_token": REVIEWER})
        if req.headers.get("Authorization") != f"Bearer {REVIEWER}":
            return _json(401, {"error": "bad token"})
        n = int(path.split("/sections/")[1].split("/")[0])
        if n != 1 and (n - 1) not in self.responded:
            return _json(403, {"error": "section not yet unlocked", "frontier": 1})
        if path.endswith("/response"):
            body = json.loads(req.body or b"")
            if "ratings" not in body:
                return _json(
                    422, {"detail": "Grade every rubric area", "missing": ["x"]}
                )
            self.responded.add(n)
            return (
                _json(200, {"done": True})
                if n == self.sections
                else _json(200, {"next": n + 1})
            )
        return _json(
            200,
            {
                "index": n,
                "title": f"Scene {n}",
                "html": f"<p>Text {n}. Echo {REVIEWER}</p><script>x</script>",
                "checkpoint": {"index": n, "rating_node_ids": [f"scene-{n}"]},
            },
        )


@pytest.fixture
def fake() -> FakeAwen:
    return FakeAwen()


@pytest.fixture
def core(fake: FakeAwen) -> ReviewCore:
    return ReviewCore(BASE, transport=fake)


def _all_text(*objs: Any) -> str:
    return json.dumps(objs, default=str)


GOOD = {"schema_version": 3, "ratings": [{"node_id": "scene-1"}]}


def test_full_flow(core: ReviewCore) -> None:
    started = core.start_review(URL, "claude-x")
    assert started["section_count"] == 2
    s1 = core.get_next_section()
    assert s1["section"] == 1 and "Text 1" in s1["text"] and "script" not in s1["text"]
    assert core.submit_checkpoint(GOOD) == {
        "accepted": True,
        "next_section": 2,
        "of": 2,
    }
    assert core.get_next_section()["section"] == 2
    assert core.submit_checkpoint(GOOD)["done"] is True
    with pytest.raises(ReviewError):
        core.get_next_section()


def test_no_token_leaks_anywhere(core: ReviewCore, fake: FakeAwen) -> None:
    outs = [core.start_review(URL, "m"), core.get_next_section()]
    outs.append(core.submit_checkpoint(GOOD))
    errors = []
    for fn in (
        lambda: core.submit_checkpoint({"bad": 1}),
        lambda: core.start_review("https://evil.test/review/" + SESSION, "m"),
    ):
        try:
            fn()
        except ReviewError as exc:
            errors.append(str(exc))
    blob = _all_text(outs, errors, repr(core))
    assert SESSION not in blob and REVIEWER not in blob


def test_errors_scrub_tokens(core: ReviewCore, fake: FakeAwen) -> None:
    core.start_review(URL, "m")
    core.get_next_section()
    fake.session_status = 410
    with pytest.raises(ReviewError) as exc:
        core.get_next_section()
    assert SESSION not in str(exc.value)


def test_sequencing(core: ReviewCore) -> None:
    with pytest.raises(ReviewError, match="start_review"):
        core.get_next_section()
    with pytest.raises(ReviewError, match="start_review"):
        core.submit_checkpoint(GOOD)
    core.start_review(URL, "m")
    with pytest.raises(ReviewError, match="get_next_section"):
        core.submit_checkpoint(GOOD)
    core.get_next_section()
    core.submit_checkpoint(GOOD)
    # submitted section 1; cannot submit again without reading 2
    with pytest.raises(ReviewError, match="get_next_section"):
        core.submit_checkpoint(GOOD)


def test_rereading_current_section_is_idempotent(core: ReviewCore) -> None:
    core.start_review(URL, "m")
    assert core.get_next_section()["section"] == 1
    assert core.get_next_section()["section"] == 1


@pytest.mark.parametrize("status", [404, 410])
def test_invalid_session(fake: FakeAwen, core: ReviewCore, status: int) -> None:
    fake.session_status = status
    with pytest.raises(ReviewError, match=str(status)):
        core.start_review(URL, "m")
    with pytest.raises(ReviewError, match="start_review"):
        core.get_next_section()


@pytest.mark.parametrize(
    "url",
    [
        "https://evil.test/review/" + SESSION,
        f"http://awen.test/review/{SESSION}",
        f"https://user:pw@awen.test/review/{SESSION}",
        f"https://awen.test.evil.test/review/{SESSION}",
        f"{BASE}/other/{SESSION}",
        f"{BASE}/review/short",
        "not a url",
        "",
    ],
)
def test_rejects_foreign_or_malformed_urls(
    core: ReviewCore, fake: FakeAwen, url: str
) -> None:
    with pytest.raises(ReviewError):
        core.start_review(url, "m")
    assert fake.calls == []


def test_accepts_api_and_start_link_forms(core: ReviewCore) -> None:
    core.start_review(f"{BASE}/api/review/{SESSION}/start?role=beta-reader", "m")


def test_redirects_are_refused(core: ReviewCore, fake: FakeAwen) -> None:
    fake.redirect = True
    with pytest.raises(ReviewError, match="redirect"):
        core.start_review(URL, "m")
    assert len(fake.calls) == 1  # never followed


@pytest.mark.parametrize(
    "payload",
    [None, [], "x", {}, {"a": float("nan")}, {"a": object()}, {"a": "x" * 70_000}],
)
def test_malformed_submissions_never_reach_awen(
    core: ReviewCore, fake: FakeAwen, payload: Any
) -> None:
    core.start_review(URL, "m")
    core.get_next_section()
    before = len(fake.calls)
    with pytest.raises(ReviewError):
        core.submit_checkpoint(payload)
    assert len(fake.calls) == before


def test_server_validation_error_is_surfaced_and_state_kept(
    core: ReviewCore,
) -> None:
    core.start_review(URL, "m")
    core.get_next_section()
    with pytest.raises(ReviewError, match="Grade every rubric area"):
        core.submit_checkpoint({"nope": 1})
    assert core.submit_checkpoint(GOOD)["accepted"] is True  # can retry


def test_requests_are_pinned_to_base_and_role(core: ReviewCore, fake: FakeAwen) -> None:
    core.start_review(URL, "m")
    core.get_next_section()
    assert {urlsplit(r.url).hostname for r in fake.calls} == {"awen.test"}
    assert all(
        urlsplit(r.url).path.startswith(f"/api/review/{SESSION}/") for r in fake.calls
    )


def test_insecure_base_url_rejected() -> None:
    with pytest.raises(ValueError):
        ReviewCore("http://awen.press")
    ReviewCore("http://localhost:8000")


def test_exactly_three_tools() -> None:
    srv = build_server(ReviewCore(BASE))
    reply = srv.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert reply is not None
    names = {t["name"] for t in reply["result"]["tools"]}
    assert names == {"start_review", "get_next_section", "submit_checkpoint"}


def test_http_client_logs_no_urls(
    core: ReviewCore, caplog: pytest.LogCaptureFixture
) -> None:
    import logging

    with caplog.at_level(logging.DEBUG):
        core.start_review(URL, "m")
        core.get_next_section()
    assert SESSION not in caplog.text
