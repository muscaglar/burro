"""The desk's server, asked through its own port.

Every name, id and note here is made up. The only host a test reaches is the
loopback address, where the server under test listens on a port of its own.
"""

import ast
import errno
import http.client
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast
from urllib.parse import quote

import pytest
from desk import records, server
from desk.records import Unfit, path_of, read
from desk.server import Desk, open_desk, route, serve

pytestmark = pytest.mark.allow_hosts(["127.0.0.1"])

TOOLS = Path(__file__).resolve().parents[2]
START = datetime(2026, 10, 6, 21, 14, 9, tzinfo=UTC)
RULE = "Copy no name and no border from a map or a website."
# A note no other test writes. If an answer or a log repeats what was sent, it shows.
CANARY = "Zzyzx Parva canary note"


# The queues whose lines are never published, as `questions.json` has them.
PRIVATE = ("ratings", "claims", "know")
# What each queue waits on, and the queues the founder alone works.
AFTER = {"borders": ["names"], "ratings": ["names"]}
FOUNDER_ALONE = ("names",)


COVERS = {"by": "area_id", "code": "cannot_say", "label": "I do not know this area"}


def question(name: str, answers: tuple[str, ...], adds: tuple[str, ...] = ()) -> dict[str, Any]:
    return {
        **({"covers": COVERS} if name == "ratings" else {}),
        "id": name,
        "version": 1,
        "title": name.title(),
        "text": "Is this right?",
        "rule": RULE,
        "view": "map",
        "adds": list(adds),
        "after": AFTER.get(name, []),
        "open_to": "founder" if name in FOUNDER_ALONE else "all",
        "public": name not in PRIVATE,
        "answers": [{"code": code, "label": code.title()} for code in answers],
        "flags": {"one_publisher": "one publisher writes this name"},
    }


QUESTIONS: dict[str, Any] = {
    "desk": 1,
    "queues": [
        question("names", ("area", "same_ground", "inside", "wide", "drop"), ("pick",)),
        question("borders", ("right", "wrong", "unknown"), ("move",)),
        question("ratings", ("1", "2", "3", "4", "5", "cannot_say")),
        question("claims", ("accept", "not_this_place")),
        question("know", ("well", "a_little", "not")),
    ],
}


def rev_of(name: str) -> str:
    return f"{abs(hash(name)) % 16**12:012x}"


def item(name: str, **changed: Any) -> dict[str, Any]:
    held: dict[str, Any] = {
        "id": name,
        "rev": REVS.setdefault(name, f"{len(REVS) + 1:012x}"),
        "group": "quillhaven",
        "title": "Dulcimer Green, Quillhaven",
        "lines": [{"label": "As written", "value": "Dulcimer Green", "source_id": "synthetic"}],
        "text": None,
        "map": {"bbox": [-0.03, 0.02, 0.0, 0.06], "focus": "syn-n0004", "layers": ["cells"]},
        "picks": None,
        "flags": [],
        "fill": {},
        "preset": {},
    }
    return {**held, **changed}


REVS: dict[str, str] = {}
NAMES = [
    item("n:syn-n0004", picks=["Dulcimer Green", "Dulcimer"], flags=["one_publisher"]),
    item(
        "a:syn-n0004:dulcimer",
        picks=["Dulcimer"],
        preset={"of": ["syn-n0004"], "proposed": "inside"},
    ),
    item("n:syn-n0007", picks=["Alderwick"]),
]
BORDERS = [item("syn-n0007"), item("syn-n0012")]
RATINGS = [item("syn-n0004:leafy", preset={"area_id": "syn-n0004", "vibe": "leafy"})]
EVERY = [*NAMES, *BORDERS, *RATINGS]
LAYER: dict[str, Any] = {
    "type": "FeatureCollection",
    "desk": {
        "layer": "cells",
        "group": "quillhaven",
        "source_ids": ["synthetic"],
        "synthetic": True,
    },
    "features": [],
}


def write_items(data: Path, queue: str, items: list[dict[str, Any]], **header: Any) -> None:
    first: dict[str, Any] = {
        "desk": 1,
        "queue": queue,
        "question": f"{queue}@1",
        "synthetic": True,
        "made_on": "2026-09-23",
        "made_from": [],
        "count": len(items),
        **header,
    }
    folder = data / "items"
    folder.mkdir(parents=True, exist_ok=True)
    rows = "".join(json.dumps(row) + "\n" for row in (first, *items))
    (folder / f"{queue}.jsonl").write_text(rows, encoding="utf-8")


def write_layer(data: Path, folder: str, file: str, **about: Any) -> None:
    """A layer's file. What it says of itself is its folder and its name, unless `about` differs."""
    (data / "layers" / folder).mkdir(parents=True, exist_ok=True)
    held = {**LAYER, "desk": {**LAYER["desk"], "group": folder, "layer": file, **about}}
    (data / "layers" / folder / f"{file}.geojson").write_text(json.dumps(held), encoding="utf-8")


@dataclass(frozen=True)
class Made:
    """A made-up desk on disk: its data, its page and its questions."""

    data: Path
    page: Path
    questions: Path
    outside: Path

    @property
    def kept(self) -> Path:
        """Where a second copy of every line is kept, when the desk is started with one."""
        return self.data.parent / "kept"


def as_if_real(made: Made) -> None:
    """Say of the made-up items that they are real, so that the desk takes them for London."""
    for queue, items in (("names", NAMES), ("borders", BORDERS), ("ratings", RATINGS)):
        write_items(made.data, queue, items, synthetic=False)


def make(tmp_path: Path) -> Made:
    data, page = tmp_path / "data", tmp_path / "desk" / "page"
    write_items(data, "names", NAMES)
    write_items(data, "borders", BORDERS)
    write_items(data, "ratings", RATINGS)
    write_layer(data, "quillhaven", "cells")
    (page / "test").mkdir(parents=True)
    (page / "index.html").write_text("<!doctype html><title>The review desk</title>")
    (page / "desk.css").write_text("body { margin: 0 }")
    (page / "desk.mjs").write_text("export const desk = 1;")
    (page / "notes.txt").write_text("not a file of the page")
    (page / "test" / "logic.test.mjs").write_text("// a test, not the page")
    outside = tmp_path / "desk" / "outside.html"
    outside.write_text("<!doctype html><title>Not the page</title>")
    (page / "link.html").symlink_to(outside)
    questions = tmp_path / "desk" / "questions.json"
    questions.write_text(json.dumps(QUESTIONS))
    return Made(data, page, questions, outside)


@pytest.fixture
def made(tmp_path: Path) -> Made:
    return make(tmp_path)


@dataclass(frozen=True)
class Answer:
    status: int
    headers: dict[str, str]
    raw: bytes

    @property
    def held(self) -> dict[str, Any]:
        return json.loads(self.raw)

    @property
    def error(self) -> str:
        return self.held["error"]


# How long a caller waits for the desk to print the line of a request it has answered.
WAIT_FOR_A_LINE = 5.0


@dataclass
class Sitting:
    """One server, and a caller that asks it as the page would."""

    desk: Desk
    port: int
    log: list[str]
    token: str = ""
    # Whether what the desk prints reaches `log`. It does not where the desk is a program
    # of its own, whose lines are read from what it prints.
    hears: bool = True

    def ask(
        self,
        method: str,
        path: str,
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
        host: str | None = None,
    ) -> Answer:
        before = self.requests_printed()
        link = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            link.putrequest(method, path, skip_host=True, skip_accept_encoding=True)
            link.putheader("Host", f"127.0.0.1:{self.port}" if host is None else host)
            for name, value in (headers or {}).items():
                link.putheader(name, value)
            if body is not None and "Content-Length" not in (headers or {}):
                link.putheader("Content-Length", str(len(body)))
            link.endheaders(body)
            got = link.getresponse()
            answer = Answer(got.status, {k.lower(): v for k, v in got.getheaders()}, got.read())
        finally:
            link.close()
        # The desk prints the line of a request once its answer is sent, so the answer
        # can be read before the line is there. A test reads both, so it waits for the line.
        until = time.monotonic() + (WAIT_FOR_A_LINE if self.hears else 0)
        while self.requests_printed() == before and time.monotonic() < until:
            time.sleep(0.001)
        return answer

    def requests_printed(self) -> int:
        """How many lines of a request the desk has printed. A fault has a line of its own."""
        return sum(1 for line in self.log if not line.startswith("fault "))

    def get(self, path: str, **more: Any) -> Answer:
        return self.ask("GET", path, **more)

    def post(self, path: str, sent: Any, headers: dict[str, str] | None = None) -> Answer:
        if not self.token:
            self.token = self.get("/api/state").held["token"]
        own = {"Content-Type": "application/json", "X-Desk-Token": self.token}
        return self.ask("POST", path, json.dumps(sent).encode(), {**own, **(headers or {})})

    def decide(self, queue: str, item: str, answer: str, **more: Any) -> Answer:
        """Decide as a page does that shows the item as it stands now."""
        sent = decision(queue, item, answer, **more)
        if "stands" not in more:
            sent["stands"] = self.stands(queue, item, sent["part"])
        return self.post("/api/decide", sent)

    def stands(self, queue: str, item: str, part: str = "") -> int | None:
        """The number of the line that stands for an item, or for a cell of it, as the page
        is told it."""
        if not any(each["id"] == item for each in EVERY):
            return None
        shown = self.get(f"/api/item/{quote(queue)}/{quote(item, safe=':')}")
        if shown.status != 200:
            return None
        held = shown.held
        if part:
            return next((each["n"] for each in held["moves"] if each["part"] == part), None)
        return None if held["mine"] is None else held["mine"]["n"]

    def undo(self, queue: str) -> Answer:
        return self.post("/api/undo", {"queue": queue})

    def lines(self, queue: str, reviewer: str | None = None) -> tuple[records.Line, ...]:
        who = reviewer or self.desk.reviewer
        return read(path_of(self.desk.data, queue, who, private=queue in PRIVATE)).lines

    def state_of(self, queue: str, item: str) -> str:
        listed = self.get(f"/api/queue/{queue}").held["items"]
        return next(each["state"] for each in listed if each["id"] == item)


def decision(queue: str, item: str, answer: str, **more: Any) -> dict[str, Any]:
    """A decision as the page sends it: with what the item was made with as its detail."""
    none: dict[str, Any] = {}
    given: dict[str, Any] = next((each["preset"] for each in EVERY if each["id"] == item), none)
    held: dict[str, Any] = {
        "queue": queue,
        "item": item,
        "rev": REVS.get(item, "0" * 12),
        "part": "",
        "answer": answer,
        "note": "",
        "second": False,
        "settles": False,
        "detail": {} if answer == "skip" else dict(given),
        "seconds": 12,
        "stands": None,
    }
    return {**held, **more}


def move(item: str, cell: str, to: str) -> dict[str, Any]:
    return {"part": cell, "detail": {"from": item, "to": to}}


Opener = Callable[..., Sitting]


def start(
    made: Made,
    running: list[server.Server],
    reviewer: str = "r1",
    clock: Callable[[], datetime] | None = None,
    keep: Path | None = None,
) -> Sitting:
    log: list[str] = []
    desk = open_desk(
        made.data,
        made.page,
        made.questions,
        reviewer,
        clock=clock or (lambda: START),
        log=log.append,
        keep=keep,
    )
    held = serve(desk, port=0)
    running.append(held)
    threading.Thread(target=held.serve_forever, args=(0.01,), daemon=True).start()
    return Sitting(desk, held.server_address[1], log)


def no_sync(descriptor: int) -> None:
    """Stands in for the wait on the disk."""


def stop(running: list[server.Server]) -> None:
    for held in running:
        held.shutdown()
        held.server_close()


@pytest.fixture
def opener(made: Made, monkeypatch: pytest.MonkeyPatch) -> Iterator[Opener]:
    """Starts a server on the made-up desk, as any reviewer, and stops each one after."""
    # The strongest call to the disk is slow, and one test of its own holds it to account.
    monkeypatch.setattr(records, "_sync", no_sync)
    running: list[server.Server] = []
    yield lambda *args, **kwargs: start(made, running, *args, **kwargs)
    stop(running)


@pytest.fixture(scope="module")
def refusing(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Sitting]:
    """One server for every test that is refused. Nothing is ever written through it."""
    made, running = make(tmp_path_factory.mktemp("refusing")), list[server.Server]()
    yield start(made, running)
    stop(running)
    assert not list(made.data.glob("decisions*")), "a request that was refused wrote a line"


@pytest.fixture
def sitting(opener: Opener) -> Sitting:
    return opener()


def others_file(made: Made, queue: str, reviewer: str, *rows: dict[str, Any]) -> None:
    """Another reviewer's lines, as if their file had been sent back."""
    for row in rows:
        records.append(
            path_of(made.data, queue, reviewer, private=queue in PRIVATE),
            reviewer=reviewer,
            queue=queue,
            question=f"{queue}@1",
            item=row["item"],
            rev=REVS[row["item"]],
            answer=row["answer"],
            note=row.get("note", ""),
            part=row.get("part", ""),
            detail=row.get("detail"),
            synthetic=True,
            clock=lambda: START,
        )


# Starting


def test_the_server_binds_to_the_loopback_address_alone(made: Made):
    held = serve(open_desk(made.data, made.page, made.questions, "r1"), port=0)
    try:
        assert server.LOOPBACK == "127.0.0.1"
        assert held.socket.getsockname()[0] == "127.0.0.1"
    finally:
        held.server_close()


def test_the_desk_does_not_start_with_nothing_to_show(made: Made, tmp_path: Path):
    with pytest.raises(Unfit, match="make desk-fill"):
        open_desk(tmp_path / "empty", made.page, made.questions, "r1")


def test_the_desk_does_not_start_on_a_mix_of_made_up_and_real_items(made: Made):
    write_items(made.data, "claims", [item("syn-c0a1b2c3d4e5")], synthetic=False)
    with pytest.raises(Unfit, match="made-up"):
        open_desk(made.data, made.page, made.questions, "r1")


def test_the_desk_does_not_start_on_items_made_for_another_question(made: Made):
    write_items(made.data, "names", NAMES, question="names@0")
    with pytest.raises(Unfit, match="another version"):
        open_desk(made.data, made.page, made.questions, "r1")


def test_the_desk_does_not_start_on_a_queue_with_no_question(made: Made):
    write_items(made.data, "gyms", [item("syn-g0001")])
    with pytest.raises(Unfit, match="no question"):
        open_desk(made.data, made.page, made.questions, "r1")


def test_the_desk_does_not_start_without_its_page(made: Made):
    (made.page / "index.html").unlink()
    with pytest.raises(Unfit, match=r"index\.html"):
        open_desk(made.data, made.page, made.questions, "r1")


@pytest.mark.parametrize("reviewer", ["", "founder", "r0", "r100", "R1", "r1/../r2", "a name"])
def test_a_reviewer_is_a_label_and_never_a_name(made: Made, reviewer: str):
    with pytest.raises(Unfit, match="label"):
        open_desk(made.data, made.page, made.questions, reviewer)


def test_each_run_makes_a_token_of_its_own(opener: Opener):
    first, second = opener(), opener()
    assert first.desk.token != second.desk.token
    assert len(first.desk.token) >= 32


# The page


def test_the_page_is_served_at_the_root(sitting: Sitting):
    got = sitting.get("/")
    assert got.status == 200
    assert got.headers["content-type"] == "text/html; charset=utf-8"
    assert b"The review desk" in got.raw
    assert sitting.get("/page/index.html").raw == got.raw


def test_a_module_is_served_as_javascript(sitting: Sitting):
    assert sitting.get("/page/desk.mjs").headers["content-type"].startswith("text/javascript")
    assert sitting.get("/page/desk.css").headers["content-type"].startswith("text/css")


@pytest.mark.parametrize(
    "path",
    [
        "/page/notes.txt",
        "/page/link.html",
        "/page/test/logic.test.mjs",
        "/page/test%2Flogic.test.mjs",
        "/page/",
        "/page",
        "/page/..",
        "/page/../questions.json",
        "/page/..%2Fquestions.json",
        "/page/%2e%2e%2Fquestions.json",
        "/page/..%5Cquestions.json",
        "/page/%2e%2e/outside.html",
        "/page/..%2Foutside.html",
        "/page/....//outside.html",
        "/page/index.html/",
        "/page/index.html%00.png",
        "/page/%ff",
        "/../page/index.html",
        "/index.html",
        "/desk/page/index.html",
        "/etc/passwd",
        "/page//etc/passwd",
        "/page/%2Fetc%2Fpasswd",
        "/api/layer/../items/names",
        "/api/layer/..%2Fitems/names",
        "/api/layer/quillhaven/..%2F..%2Fitems%2Fnames",
        "/api/layer/quillhaven/cells.geojson",
        "/api/queue/..%2Fdecisions",
        "/api/item/names/..%2F..%2Fdecisions",
        "/api/item/names",
        "/api/state/",
        "/api",
        "/api/",
        "/api/decisions/names/r1.jsonl",
        "http://127.0.0.1/page/index.html",
    ],
)
def test_a_path_that_climbs_out_of_its_folder_finds_nothing(refusing: Sitting, path: str):
    got = refusing.get(path)
    assert (got.status, got.error) == (404, "not_found")
    assert b"Not the page" not in got.raw and b"not a file" not in got.raw


@pytest.mark.parametrize("path", ["/?x=1", "/api/state?token=1", "/page/index.html?v=2", "/#top"])
def test_a_path_with_a_query_finds_nothing(refusing: Sitting, path: str):
    assert refusing.get(path).status == 404


def test_a_path_is_cut_at_each_slash_before_it_is_decoded():
    assert route("/api/item/names/n%3Asyn-n0004") == (
        "/api/item/{queue}/{item}",
        ["names", "n:syn-n0004"],
    )
    assert route("/api/item/names/a%2Fb") == ("/api/item/{queue}/{item}", ["names", "a/b"])
    assert route("/api/item/names/a/b") is None
    assert route("/page/%2e%2e") == ("/page/{name}", [".."])


# What every answer carries


def test_every_answer_carries_the_headers_that_keep_the_page_at_home(sitting: Sitting):
    answers = [
        sitting.get("/"),
        sitting.get("/page/desk.mjs"),
        sitting.get("/api/state"),
        sitting.get("/api/layer/quillhaven/cells"),
        sitting.get("/nothing"),
        sitting.get("/", host="elsewhere.example"),
        sitting.ask("PUT", "/api/state"),
        sitting.decide("names", "n:syn-n0004", "area"),
        sitting.decide("names", "n:syn-n0004", "not an answer"),
    ]
    assert [got.status for got in answers] == [200, 200, 200, 200, 404, 403, 405, 200, 400]
    for got in answers:
        policy = got.headers["content-security-policy"]
        assert policy.startswith("default-src 'none'; script-src 'self'; style-src 'self';")
        assert "connect-src 'self'" in policy and "frame-ancestors 'none'" in policy
        assert "http" not in policy and "*" not in policy and "unsafe" not in policy
        assert got.headers["x-content-type-options"] == "nosniff"
        assert got.headers["referrer-policy"] == "no-referrer"
        assert got.headers["cache-control"] == "no-store"
        assert got.headers["server"] == "desk"
        assert not [name for name in got.headers if name.startswith("access-control-")]
        assert "set-cookie" not in got.headers


def test_every_answer_under_api_says_which_city_it_is_of(sitting: Sitting):
    answers = [
        sitting.get("/api/state"),
        sitting.get("/api/queue/names"),
        sitting.get("/api/item/names/n%3Asyn-n0004"),
        sitting.get("/api/queue/nothing"),
        sitting.get("/api/state", host="elsewhere.example"),
        sitting.ask("DELETE", "/api/state"),
        sitting.decide("names", "n:syn-n0004", "area"),
        sitting.decide("names", "n:syn-n0004", "area", rev="0" * 12),
        sitting.undo("names"),
        sitting.ask("POST", "/api/decide", b"{}"),
    ]
    for got in answers:
        assert got.headers["content-type"] == "application/json; charset=utf-8"
        assert got.held["synthetic"] is True
    assert sitting.get("/api/layer/quillhaven/cells").held["desk"]["synthetic"] is True


def test_the_banner_says_which_data_is_shown(opener: Opener, made: Made):
    assert opener().get("/api/state").held["banner"] == (
        "MADE-UP CITY. Nothing here is a real place."
    )
    as_if_real(made)
    real = opener(keep=made.kept).get("/api/state").held
    assert real["banner"] == (
        "REAL DATA FOR LONDON. A draft that nobody has checked. What you decide here is built."
    )
    assert real["synthetic"] is False


def test_real_data_is_said_to_be_a_draft_that_nobody_has_checked_wherever_it_is_said():
    # What the desk is handed of London is what a method made. The top line is on every
    # screen, so it is where a person is told that nobody has checked what they look at.
    real, made_up = server.BANNER[False], server.BANNER[True]
    assert "LONDON" in real and "A draft that nobody has checked." in real
    assert "draft" not in made_up
    assert real in server.ELSEWHERE[False].decode("utf-8")
    page = Path(server.__file__).resolve().parent / "page" / "logic.mjs"
    said = page.read_text(encoding="utf-8")
    assert f"real: '{real}'," in said, "the page's own words are the desk's"
    assert f"madeUp: '{made_up}'," in said


# Who may ask


@pytest.mark.parametrize(
    "host",
    ["elsewhere.example", "127.0.0.1", "127.0.0.1:1", "localhost", "127.0.0.1.example:{port}", ""],
)
def test_a_request_that_names_another_host_is_refused(refusing: Sitting, host: str):
    for path in ("/", "/page/desk.mjs", "/api/state"):
        got = refusing.get(path, host=host.format(port=refusing.port))
        assert (got.status, got.error) == (403, "forbidden")
        assert "token" not in got.held


def test_a_request_that_names_two_hosts_is_refused(refusing: Sitting):
    with closing(http.client.HTTPConnection("127.0.0.1", refusing.port, timeout=5)) as link:
        link.putrequest("GET", "/api/state", skip_host=True)
        link.putheader("Host", f"127.0.0.1:{refusing.port}")
        link.putheader("Host", "elsewhere.example")
        link.endheaders()
        assert link.getresponse().status == 403


def test_localhost_is_this_server_too(refusing: Sitting):
    host = f"localhost:{refusing.port}"
    assert refusing.get("/api/state", host=host).status == 200
    own = {"Origin": f"http://localhost:{refusing.port}", "Sec-Fetch-Site": "same-origin"}
    assert refusing.get("/api/state", host=host, headers=own).status == 200


@pytest.mark.parametrize(
    "origin",
    [
        "http://elsewhere.example",
        "null",
        "https://127.0.0.1:{port}",
        "http://127.0.0.1",
        "http://127.0.0.1:1",
        "http://127.0.0.1:{port}.elsewhere.example",
        "",
    ],
)
def test_a_request_from_another_origin_is_refused(refusing: Sitting, origin: str):
    headers = {"Origin": origin.format(port=refusing.port)}
    assert refusing.get("/api/state", headers=headers).status == 403
    sent = decision("names", "n:syn-n0004", "area")
    assert refusing.post("/api/decide", sent, headers).status == 403
    assert refusing.lines("names") == ()


@pytest.mark.parametrize("site", ["cross-site", "same-site"])
def test_a_request_the_browser_marks_as_from_another_site_is_refused(refusing: Sitting, site: str):
    assert refusing.get("/api/state", headers={"Sec-Fetch-Site": site}).status == 403
    assert refusing.get("/", headers={"Sec-Fetch-Site": site}).status == 403


def test_a_page_opened_by_hand_is_answered(refusing: Sitting):
    assert refusing.get("/", headers={"Sec-Fetch-Site": "none"}).status == 200


# What a browser sends when the address is opened by a click in another page, in a chat
# or in a terminal on the web.
CLICKED = {
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Dest": "document",
}


@pytest.mark.parametrize("site", ["cross-site", "same-site"])
def test_an_address_opened_from_another_page_is_told_how_to_open_the_desk(
    refusing: Sitting, site: str
):
    # At the desk the address was opened by a click, and the answer was a white page of
    # JSON that sent the person back to what they had just done.
    got = refusing.get("/", headers={**CLICKED, "Sec-Fetch-Site": site})
    assert got.status == 403, "the page itself is still not given"
    assert got.headers["content-type"] == "text/html; charset=utf-8"
    words = got.raw.decode("utf-8")
    assert words == server.ELSEWHERE[True].decode("utf-8")
    assert '<a href="/">Open the desk</a>' in words
    assert "MADE-UP CITY. Nothing here is a real place." in words
    assert "address bar" in words
    assert refusing.desk.token not in words
    for never in ("<script", "<style", "<form", "<img", "<iframe", "style=", "http"):
        assert never not in words.lower(), never
    policy = got.headers["content-security-policy"]
    assert "default-src 'none'" in policy and "frame-ancestors 'none'" in policy
    assert got.headers["cache-control"] == "no-store"


def test_the_link_on_that_page_opens_the_desk(refusing: Sitting):
    own = {"Sec-Fetch-Site": "same-origin", "Sec-Fetch-Mode": "navigate"}
    got = refusing.get("/", headers={**own, "Sec-Fetch-Dest": "document"})
    assert got.status == 200 and got.raw == refusing.get("/page/index.html").raw


@pytest.mark.parametrize(
    ("path", "headers"),
    [
        ("/api/state", CLICKED),
        ("/page/desk.mjs", CLICKED),
        ("/page/index.html", CLICKED),
        ("/nothing", CLICKED),
        ("/", {**CLICKED, "Sec-Fetch-Mode": "no-cors", "Sec-Fetch-Dest": "script"}),
        ("/", {**CLICKED, "Sec-Fetch-Mode": "cors", "Sec-Fetch-Dest": "empty"}),
        ("/", {**CLICKED, "Sec-Fetch-Dest": "iframe"}),
        ("/", {"Sec-Fetch-Site": "cross-site"}),
        ("/", {**CLICKED, "Origin": "http://elsewhere.example"}),
    ],
)
def test_nothing_else_from_another_site_is_told_anything_new(
    refusing: Sitting, path: str, headers: dict[str, str]
):
    got = refusing.get(path, headers=headers)
    assert (got.status, got.error) == (403, "forbidden")
    assert got.headers["content-type"] == "application/json; charset=utf-8"


def test_an_address_opened_from_another_page_under_another_host_is_refused(refusing: Sitting):
    got = refusing.get("/", headers=CLICKED, host="elsewhere.example")
    assert (got.status, got.error) == (403, "forbidden")


def test_nothing_is_written_from_another_site_however_it_is_sent(refusing: Sitting):
    sent = decision("names", "n:syn-n0004", "area")
    assert refusing.post("/api/decide", sent, CLICKED).status == 403
    assert refusing.ask("POST", "/", b"{}", CLICKED).status == 403
    assert refusing.lines("names") == ()


def test_the_page_that_says_how_to_open_the_desk_says_which_data_it_holds():
    for made_up, banner in server.BANNER.items():
        words = server.ELSEWHERE[made_up].decode("utf-8")
        assert banner in words
        assert words.startswith("<!doctype html>")
        assert words.count("<a ") == 1


def test_the_browser_is_given_an_icon_so_that_it_logs_no_fault(refusing: Sitting):
    got = refusing.get("/favicon.ico", headers={"Sec-Fetch-Site": "same-origin"})
    assert got.status == 200
    assert got.headers["content-type"] == "image/svg+xml"
    assert got.raw == server.ICON
    assert b"<script" not in got.raw and b"http://www.w3.org/2000/svg" in got.raw
    assert got.headers["x-content-type-options"] == "nosniff"
    assert refusing.get("/favicon.ico", headers={"Sec-Fetch-Site": "cross-site"}).status == 403
    assert refusing.ask("POST", "/favicon.ico", b"{}").status == 405


@pytest.mark.parametrize(
    "headers",
    [
        {"X-Desk-Token": ""},
        {"X-Desk-Token": "not-the-token"},
        {"Content-Type": "text/plain"},
        {"Content-Type": "application/x-www-form-urlencoded"},
        {"Content-Type": "multipart/form-data"},
        {"Content-Type": ""},
    ],
)
def test_a_write_without_the_token_or_the_kind_is_refused(
    refusing: Sitting, headers: dict[str, str]
):
    sent = decision("names", "n:syn-n0004", "area")
    for path in ("/api/decide", "/api/undo"):
        got = refusing.post(path, sent, headers)
        assert (got.status, got.error) == (403, "forbidden")
    assert refusing.lines("names") == ()


def test_the_token_of_another_run_opens_nothing(opener: Opener):
    first, second = opener(), opener()
    sent = decision("names", "n:syn-n0004", "area")
    assert first.post("/api/decide", sent, {"X-Desk-Token": second.desk.token}).status == 403


@pytest.mark.parametrize("method", ["PUT", "DELETE", "PATCH", "OPTIONS", "HEAD", "TRACE", "BREW"])
def test_a_method_it_does_not_know_is_refused(refusing: Sitting, method: str):
    for path in ("/", "/api/state", "/api/decide"):
        got = refusing.ask(method, path)
        assert got.status == 405
        assert got.headers["allow"] == "GET, POST"
        assert not [name for name in got.headers if name.startswith("access-control-")]
    assert refusing.lines("names") == ()


def test_a_route_is_answered_for_its_own_method_alone(refusing: Sitting):
    assert refusing.get("/api/decide").status == 405
    assert refusing.get("/api/undo").status == 405
    assert refusing.post("/api/state", {}).status == 405
    assert refusing.post("/", {}).status == 405


# What may be sent


def test_a_body_over_sixteen_kilobytes_is_refused(refusing: Sitting):
    sent = decision("names", "n:syn-n0004", "area", detail={"pad": "x" * 17_000})
    got = refusing.post("/api/decide", sent)
    assert (got.status, got.error) == (413, "too_large")
    assert refusing.lines("names") == ()


def test_a_body_far_too_large_is_refused_without_being_read(refusing: Sitting):
    refusing.get("/api/state")
    got = refusing.ask(
        "POST",
        "/api/decide",
        b"{}",
        {
            "Content-Type": "application/json",
            "X-Desk-Token": refusing.desk.token,
            "Content-Length": str(10**12),
        },
    )
    assert (got.status, got.error) == (413, "too_large")


@pytest.mark.parametrize(
    "headers",
    [
        {"Content-Length": "-1"},
        {"Content-Length": "two"},
        {"Content-Length": "2", "Transfer-Encoding": "chunked"},
    ],
)
def test_a_body_with_no_honest_length_is_refused(refusing: Sitting, headers: dict[str, str]):
    own = {"Content-Type": "application/json", "X-Desk-Token": refusing.desk.token, **headers}
    got = refusing.ask("POST", "/api/decide", b"{}", own)
    assert (got.status, got.error) == (400, "bad_request")


@pytest.mark.parametrize(
    "body",
    [b"", b"not json", b"[]", b"null", b'"area"', b"\xff\xfe", b'{"queue":"names"', b"{}"],
)
def test_a_body_that_is_not_a_decision_is_refused(refusing: Sitting, body: bytes):
    own = {"Content-Type": "application/json", "X-Desk-Token": refusing.desk.token}
    for path in ("/api/decide", "/api/undo"):
        got = refusing.ask("POST", path, body, own)
        assert (got.status, got.error) == (400, "bad_request")


@pytest.mark.parametrize(
    "changed",
    [
        {"reviewer": "r2"},
        {"n": 1},
        {"at": "2026-10-06T21:14:09Z"},
        {"synthetic": False},
        {"undoes": 1},
        {"question": "names@2"},
        {"note": None},
        {"note": ["a"]},
        {"note": "x" * 501},
        {"second": 1},
        {"settles": "yes"},
        {"seconds": "12"},
        {"seconds": -1},
        {"seconds": 1.5},
        {"seconds": True},
        {"detail": []},
        {"detail": None},
        {"part": None},
        {"part": "syn-oa0001"},
        {"answer": None},
        {"answer": ""},
        {"answer": "undo"},
        {"answer": "move"},
        {"answer": "right"},
        {"answer": "AREA"},
        {"detail": {"pick": "Dulcimer Grove"}},
        {"detail": {"of": "syn-n0007"}},
        {"detail": {"of": [f"syn-n000{at}" for at in range(6)]}},
        {"detail": {"of": [7]}},
        {"note": "\ud800"},
    ],
)
def test_a_decision_that_is_not_as_the_design_gives_it_is_refused(
    refusing: Sitting, changed: dict[str, Any]
):
    got = refusing.post("/api/decide", {**decision("names", "n:syn-n0004", "area"), **changed})
    assert (got.status, got.error) == (400, "bad_request")
    assert refusing.lines("names") == ()


@pytest.mark.parametrize("left_out", sorted(server.DECIDE))
def test_a_decision_with_a_field_left_out_is_refused(refusing: Sitting, left_out: str):
    sent = decision("names", "n:syn-n0004", "area")
    del sent[left_out]
    assert refusing.post("/api/decide", sent).status == 400
    assert refusing.lines("names") == ()


def test_the_reviewer_is_named_when_the_server_starts_and_never_in_a_request(opener: Opener):
    second = opener("r2")
    assert second.decide("borders", "syn-n0007", "right").held["line"]["reviewer"] == "r2"
    assert second.post(
        "/api/decide", {**decision("borders", "syn-n0012", "right"), "reviewer": "r1"}
    ).status == (400)
    assert second.lines("borders", "r1") == ()


@pytest.mark.parametrize(
    ("queue", "item"),
    [("nothing", "n:syn-n0004"), ("claims", "syn-c0a1"), ("names", "n:syn-n9999"), ("names", "")],
)
def test_a_queue_or_an_item_that_is_not_there_is_not_found(
    refusing: Sitting, queue: str, item: str
):
    sent = {**decision("names", "n:syn-n0004", "area"), "queue": queue, "item": item}
    assert refusing.post("/api/decide", sent).error == "not_found"
    assert refusing.get(f"/api/item/{queue}/{item or 'x'}").status == 404
    assert refusing.undo("nothing").status == 404


def test_a_revision_that_is_not_the_items_is_stale(refusing: Sitting):
    got = refusing.decide("names", "n:syn-n0004", "area", rev="0" * 12)
    assert (got.status, got.error) == (409, "stale_item")
    assert refusing.lines("names") == ()


def test_a_refusal_never_repeats_what_was_sent(refusing: Sitting):
    refused = [
        refusing.decide("names", "n:syn-n0004", CANARY, note=CANARY),
        refusing.decide("names", CANARY, "area", note=CANARY),
        refusing.decide(CANARY, "n:syn-n0004", "area"),
        refusing.decide("names", "n:syn-n0004", "area", detail={"pick": CANARY}),
        refusing.get(f"/api/item/names/{CANARY.replace(' ', '%20')}"),
        refusing.get(f"/page/{CANARY.replace(' ', '%20')}"),
        refusing.get("/", host=CANARY),
        refusing.get("/", headers={"Origin": CANARY}),
    ]
    for got in refused:
        assert got.status >= 400
        assert b"Zzyzx" not in got.raw
        assert "Zzyzx" not in json.dumps(got.headers)


# Writing


def test_a_line_is_on_disk_before_the_server_answers(
    sitting: Sitting, monkeypatch: pytest.MonkeyPatch
):
    file = path_of(sitting.desk.data, "names", "r1")
    sitting.get("/api/state")
    synced: list[bytes] = []
    answers: list[Answer] = []
    syncing, synced_now = threading.Event(), threading.Event()

    def held_up(descriptor: int) -> None:
        synced.append(file.read_bytes())
        syncing.set()
        synced_now.wait(5)

    monkeypatch.setattr(records, "_sync", held_up)
    note = "Both publishers write it so."
    asking = threading.Thread(
        target=lambda: answers.append(sitting.decide("names", "n:syn-n0004", "area", note=note))
    )
    asking.start()
    assert syncing.wait(5)
    asking.join(0.2)
    assert answers == [], "the server answered while the line was still on its way to the disk"
    synced_now.set()
    asking.join(5)

    (got,) = answers
    assert got.status == 200
    written = (json.dumps(got.held["line"], separators=(",", ":")) + "\n").encode()
    assert synced == [written], "the whole line was handed to the disk"
    assert file.read_bytes() == written


def test_a_line_holds_what_was_decided_on_what_when_and_by_whom(sitting: Sitting):
    got = sitting.decide(
        "names",
        "n:syn-n0004",
        "area",
        note="Both publishers write it so.",
        second=True,
        detail={"of": [], "pick": "Dulcimer Green"},
        seconds=31,
    )
    assert got.held["line"] == {
        "n": 1,
        "at": "2026-10-06T21:14:09Z",
        "reviewer": "r1",
        "queue": "names",
        "question": "names@1",
        "item": "n:syn-n0004",
        "rev": REVS["n:syn-n0004"],
        "part": "",
        "answer": "area",
        "note": "Both publishers write it so.",
        "second": True,
        "settles": False,
        "undoes": None,
        "detail": {"of": [], "pick": "Dulcimer Green"},
        "seconds": 31,
        "synthetic": True,
    }
    assert [line.as_dict() for line in sitting.lines("names")] == [got.held["line"]]


def test_an_answer_says_what_comes_next_and_how_far_the_queue_is(sitting: Sitting):
    got = sitting.decide("names", "n:syn-n0004", "area").held
    assert got["next"] == "a:syn-n0004:dulcimer"
    assert got["counts"]["queue"] == "names"
    assert (got["counts"]["total"], got["counts"]["done"]) == (3, 1)
    sitting.decide("names", "a:syn-n0004:dulcimer", "skip")
    last = sitting.decide("names", "n:syn-n0007", "drop").held
    assert last["next"] == "a:syn-n0004:dulcimer", "what was skipped comes back after the rest"
    assert sitting.decide("names", "a:syn-n0004:dulcimer", "inside").held["next"] is None


def test_a_decision_made_twice_is_written_once(sitting: Sitting):
    first = sitting.decide("names", "n:syn-n0004", "area", seconds=31)
    again = sitting.decide("names", "n:syn-n0004", "area", seconds=2)
    assert again.status == 200
    assert again.held["line"] == first.held["line"]
    assert again.held["next"] == first.held["next"]
    assert len(sitting.lines("names")) == 1
    assert again.held["counts"]["done"] == 1


def test_a_changed_answer_is_a_new_line_and_the_last_stands(sitting: Sitting):
    sitting.decide("names", "n:syn-n0004", "area")
    sitting.decide("names", "n:syn-n0004", "drop")
    assert [line.answer for line in sitting.lines("names")] == ["area", "drop"]
    assert sitting.get("/api/item/names/n%3Asyn-n0004").held["mine"]["answer"] == "drop"
    assert sitting.get("/api/state").held["queues"][0]["done"] == 1


def test_an_answer_from_an_old_window_does_not_replace_the_one_that_stands(sitting: Sitting):
    assert sitting.decide("names", "n:syn-n0004", "area").held["line"]["n"] == 1
    # A second window, opened before the answer was given, still shows the item as open.
    old = decision("names", "n:syn-n0004", "drop", stands=None)
    got = sitting.post("/api/decide", old)
    assert (got.status, got.error) == (409, "already_answered")
    assert got.held["message"] == "This item has an answer already. It is shown again."
    assert [line.answer for line in sitting.lines("names")] == ["area"]
    # Shown the answer that stands, the person may still change it: one more key.
    got = sitting.post("/api/decide", {**old, "stands": 1})
    assert (got.status, got.held["line"]["n"]) == (200, 2)
    assert [line.answer for line in sitting.lines("names")] == ["area", "drop"]


def test_an_old_window_that_gives_the_answer_that_stands_writes_nothing(sitting: Sitting):
    sitting.decide("names", "n:syn-n0004", "area")
    got = sitting.post("/api/decide", decision("names", "n:syn-n0004", "area", stands=None))
    assert (got.status, got.held["line"]["n"]) == (200, 1)
    assert len(sitting.lines("names")) == 1


def test_a_window_that_names_a_line_that_no_longer_stands_is_refused(sitting: Sitting):
    sitting.decide("names", "n:syn-n0004", "area")
    sitting.undo("names")
    got = sitting.post("/api/decide", decision("names", "n:syn-n0004", "drop", stands=1))
    assert (got.status, got.error) == (409, "already_answered")
    assert sitting.post("/api/decide", decision("names", "n:syn-n0004", "drop")).status == 200


def test_a_cell_moved_in_another_window_is_not_moved_again_from_an_old_one(sitting: Sitting):
    there = move("syn-n0007", "syn-oa0101", "syn-n0012")
    assert sitting.decide("borders", "syn-n0007", "move", **there).status == 200
    elsewhere = move("syn-n0007", "syn-oa0101", "syn-n0004")
    got = sitting.post("/api/decide", decision("borders", "syn-n0007", "move", **elsewhere))
    assert (got.status, got.error) == (409, "already_answered")
    assert len(sitting.lines("borders")) == 1


@pytest.mark.parametrize("stands", [0, -1, "1", 1.5, True, [1]])
def test_the_line_said_to_stand_is_a_number_or_nothing(refusing: Sitting, stands: Any):
    got = refusing.post("/api/decide", decision("names", "n:syn-n0004", "area", stands=stands))
    assert (got.status, got.error) == (400, "bad_request")


def test_undo_takes_back_the_last_line_and_asked_again_the_one_before(sitting: Sitting):
    sitting.decide("names", "n:syn-n0004", "area")
    sitting.decide("names", "n:syn-n0007", "drop")
    before = path_of(sitting.desk.data, "names", "r1").read_bytes()

    first = sitting.undo("names").held
    assert first["undone"]["item"] == "n:syn-n0007"
    assert first["counts"]["done"] == 1
    second = sitting.undo("names").held
    assert second["undone"]["item"] == "n:syn-n0004"
    assert second["counts"]["done"] == 0

    assert [line.answer for line in sitting.lines("names")] == ["area", "drop", "undo", "undo"]
    assert [line.undoes for line in sitting.lines("names")] == [None, None, 2, 1]
    assert path_of(sitting.desk.data, "names", "r1").read_bytes().startswith(before)
    assert sitting.state_of("names", "n:syn-n0004") == "open"


def test_undo_with_nothing_to_take_back_writes_nothing(sitting: Sitting):
    assert sitting.undo("names").held["undone"] is None
    sitting.decide("names", "n:syn-n0004", "area")
    sitting.undo("names")
    assert sitting.undo("names").held["undone"] is None
    assert len(sitting.lines("names")) == 2


def test_undo_never_takes_back_an_undo(sitting: Sitting):
    sitting.decide("names", "n:syn-n0004", "area")
    sitting.undo("names")
    sitting.decide("names", "n:syn-n0004", "drop")
    assert sitting.undo("names").held["undone"]["answer"] == "drop"
    assert sitting.state_of("names", "n:syn-n0004") == "open"
    assert sitting.undo("names").held["undone"] is None


def test_undo_in_one_queue_leaves_the_others_alone(sitting: Sitting):
    sitting.decide("names", "n:syn-n0004", "area")
    sitting.decide("ratings", "syn-n0004:leafy", "4")
    assert sitting.undo("ratings").held["undone"]["answer"] == "4"
    assert sitting.state_of("names", "n:syn-n0004") == "done"


def test_a_move_is_a_line_of_its_own_written_when_it_is_made(sitting: Sitting):
    got = sitting.decide(
        "borders", "syn-n0007", "move", **move("syn-n0007", "syn-oa0101", "syn-n0012")
    )
    assert got.status == 200
    assert got.held["next"] == "syn-n0007", "the item stays in view"
    assert got.held["counts"]["done"] == 0
    (line,) = sitting.lines("borders")
    assert (line.part, line.answer, line.detail) == (
        "syn-oa0101",
        "move",
        {"from": "syn-n0007", "to": "syn-n0012"},
    )
    shown = sitting.get("/api/item/borders/syn-n0007").held
    assert shown["mine"] is None
    assert [each["part"] for each in shown["moves"]] == ["syn-oa0101"]
    assert sitting.undo("borders").held["undone"]["part"] == "syn-oa0101"
    assert sitting.get("/api/item/borders/syn-n0007").held["moves"] == []


@pytest.mark.parametrize(
    "detail",
    [
        {},
        {"from": "syn-n0007"},
        {"from": "syn-n0007", "to": "syn-n0007"},
        {"from": "syn-n0007", "to": ""},
        {"from": "syn-n0007", "to": 12},
        {"from": "syn-n0007", "to": "syn-n0012", "why": "x"},
    ],
)
def test_a_move_says_where_from_and_where_to(refusing: Sitting, detail: dict[str, Any]):
    got = refusing.decide("borders", "syn-n0007", "move", part="syn-oa0101", detail=detail)
    assert got.status == 400
    assert refusing.lines("borders") == ()


def test_a_queue_that_does_not_add_a_move_takes_none(refusing: Sitting):
    got = refusing.decide(
        "names", "n:syn-n0004", "move", **move("syn-n0004", "syn-oa1", "syn-n0007")
    )
    assert got.status == 400


def test_another_name_is_not_made_an_area_at_the_desk(refusing: Sitting):
    # Only the areas build gives an area its id. Compile could never apply the answer.
    got = refusing.decide("names", "a:syn-n0004:dulcimer", "area")
    assert (got.status, got.error) == (400, "bad_request")
    assert got.held["message"] == (
        "The desk cannot make an area of another name. "
        "If it should be one, write a note and skip it."
    )


def test_wrong_needs_a_note(sitting: Sitting):
    got = sitting.decide("borders", "syn-n0007", "wrong")
    assert (got.status, got.held["message"]) == (400, "This answer needs a note. Say why.")
    assert (
        sitting.decide("borders", "syn-n0007", "wrong", note="The brook is the edge.").status == 200
    )


def test_an_answer_after_a_move_needs_a_note(sitting: Sitting):
    sitting.decide("borders", "syn-n0007", "move", **move("syn-n0007", "syn-oa0101", "syn-n0012"))
    assert sitting.decide("borders", "syn-n0007", "right").status == 400
    assert sitting.decide("borders", "syn-n0007", "skip").status == 200
    assert sitting.decide("borders", "syn-n0007", "right", note="The brook.").status == 200
    assert sitting.decide("borders", "syn-n0012", "right").status == 200


@pytest.mark.parametrize("note", ["two\nlines", "red \x1b[31m", "turned \u202e round", "nul \x00"])
def test_a_note_with_a_control_character_is_refused(refusing: Sitting, note: str):
    got = refusing.decide("names", "n:syn-n0004", "area", note=note)
    assert (got.status, got.error) == (400, "bad_request")
    assert got.held["message"] == "A note is one line of plain text."


@pytest.mark.parametrize(
    "detail",
    [
        {"area_id": "syn-n0004", "vibe": "leafy", "home": "12 Made-up Street"},
        {"area_id": "syn-n0004", "vibe": "quiet"},
        {"area_id": "syn-n0004"},
        {"vibe": "leafy", "area_id": ["syn-n0004"]},
        {"pick": "Dulcimer Green"},
        {"of": []},
        {},
    ],
)
def test_a_detail_the_item_does_not_give_is_refused(refusing: Sitting, detail: dict[str, Any]):
    # A line holds what the design names and no more: a detail is no second note.
    got = refusing.decide("ratings", "syn-n0004:leafy", "4", detail=detail)
    assert (got.status, got.error) == (400, "bad_request")
    assert CANARY not in got.held["message"]


def test_a_detail_is_what_the_item_was_made_with(sitting: Sitting):
    about = {"vibe": "leafy", "area_id": "syn-n0004"}
    got = sitting.decide("ratings", "syn-n0004:leafy", "4", detail=about)
    assert (got.status, got.held["line"]["detail"]) == (200, about)


def test_a_name_adds_its_spelling_and_its_areas_to_what_the_item_was_made_with(sitting: Sitting):
    chosen = {"of": ["syn-n0004", "syn-n0007"], "pick": "Dulcimer", "proposed": "inside"}
    got = sitting.decide("names", "a:syn-n0004:dulcimer", "inside", detail=chosen)
    assert (got.status, got.held["line"]["detail"]) == (200, chosen)
    assert sitting.decide("names", "n:syn-n0007", "area", detail={"kind": "x"}).status == 400


def test_a_skip_holds_no_detail_or_the_items_own(sitting: Sitting):
    assert sitting.decide("ratings", "syn-n0004:leafy", "skip", detail={}).status == 200
    about = {"vibe": "leafy", "area_id": "syn-n0004"}
    assert sitting.decide("ratings", "syn-n0004:leafy", "skip", detail=about).status == 200
    assert sitting.decide("ratings", "syn-n0004:leafy", "skip", detail={"x": "y"}).status == 400


def test_time_on_screen_is_cut_at_fifteen_minutes(sitting: Sitting):
    assert (
        sitting.decide("names", "n:syn-n0004", "area", seconds=86_400).held["line"]["seconds"]
        == 900
    )


def test_a_file_that_ends_in_half_a_line_is_counted_and_the_desk_carries_on(
    opener: Opener, made: Made
):
    first = opener()
    first.decide("names", "n:syn-n0004", "area")
    file = path_of(made.data, "names", "r1")
    whole = file.read_bytes()
    with file.open("ab") as torn:
        torn.write(whole[:80])

    again = opener()
    held = again.get("/api/state").held
    assert held["broken_lines"] == 1
    assert held["queues"][0]["done"] == 1
    assert held["resume"] == {"queue": "names", "item": "a:syn-n0004:dulcimer"}
    got = again.decide("names", "n:syn-n0007", "drop")
    assert (got.status, got.held["line"]["n"]) == (200, 3)
    assert file.read_bytes().startswith(whole + whole[:80] + b"\n")
    assert [line.answer for line in again.lines("names")] == ["area", "drop"]
    assert again.get("/api/state").held["broken_lines"] == 1


def test_when_a_line_cannot_be_written_the_answer_says_not_saved(
    sitting: Sitting, monkeypatch: pytest.MonkeyPatch
):
    sitting.decide("names", "n:syn-n0004", "area")

    def full(descriptor: int, data: bytes) -> None:
        raise OSError(errno.ENOSPC, f"No space left on device: {CANARY}")

    monkeypatch.setattr(records, "_write_all", full)
    got = sitting.decide("names", "n:syn-n0007", "drop", note=CANARY)
    assert (got.status, got.error) == (500, "not_saved")
    assert got.held["message"] == (
        "Not saved. The disk is full. Make room on it. The desk need not be started again."
    )
    assert b"Zzyzx" not in got.raw
    assert "Zzyzx" not in "".join(sitting.log)
    assert sitting.log[-1] == "POST /api/decide 500"
    assert sitting.log[-2] == f"fault OSError {errno.ENOSPC}", (
        "the number of the fault, and no word of it"
    )
    monkeypatch.undo()
    assert sitting.state_of("names", "n:syn-n0007") == "open"
    assert sitting.state_of("names", "n:syn-n0004") == "done"


@pytest.mark.parametrize(
    ("number", "words"),
    [
        (
            errno.ENOSPC,
            "Not saved. The disk is full. Make room on it. The desk need not be started again.",
        ),
        (
            errno.EDQUOT,
            "Not saved. The disk is full. Make room on it. The desk need not be started again.",
        ),
        (errno.EACCES, "Not saved. The desk may not write to its folder. Give it leave to."),
        (errno.EPERM, "Not saved. The desk may not write to its folder. Give it leave to."),
        (errno.EROFS, "Not saved. The desk may not write to its folder. Give it leave to."),
        (errno.EIO, "Not saved. Start the desk again with make desk."),
    ],
)
def test_the_words_of_a_fault_say_what_a_person_can_do_about_it(
    sitting: Sitting, monkeypatch: pytest.MonkeyPatch, number: int, words: str
):
    # A fault goes by its name. Its number is the system's own: a quota that is used up
    # is one number on one system and another on the next.
    # Starting the desk again does not make room on a disk.
    def fails(descriptor: int, data: bytes) -> None:
        raise OSError(number, f"A fault of the system: {CANARY}")

    monkeypatch.setattr(records, "_write_all", fails)
    for got in (sitting.decide("names", "n:syn-n0007", "drop"), sitting.undo("names")):
        if got.status == 200:
            continue  # There was nothing to take back, so nothing was written.
        assert (got.status, got.error, got.held["message"]) == (500, "not_saved", words)
        assert b"Zzyzx" not in got.raw


def test_a_fault_that_is_not_of_the_disk_says_to_start_the_desk_again(
    sitting: Sitting, monkeypatch: pytest.MonkeyPatch
):
    def fails(*args: object, **more: object) -> None:
        raise RuntimeError(f"a fault in the desk itself: {CANARY}")

    monkeypatch.setattr(records, "append", fails)
    got = sitting.decide("names", "n:syn-n0007", "drop")
    assert (got.status, got.held["message"]) == (
        500,
        "Not saved. Start the desk again with make desk.",
    )
    assert sitting.log[-2] == "fault RuntimeError"


# The order of the work


def waits_of(sitting: Sitting, queue: str) -> list[dict[str, Any]]:
    listed = sitting.get("/api/state").held["queues"]
    return next(each["waits"] for each in listed if each["queue"] == queue)


def test_a_queue_says_what_it_waits_on_until_the_founder_has_finished_it(opener: Opener):
    # Borders are drafted from names. A name changed afterwards reopens borders reviewed.
    sitting = opener()
    assert waits_of(sitting, "names") == []
    assert waits_of(sitting, "borders") == [{"queue": "names", "title": "Names", "left": 3}]
    got = sitting.decide("names", "n:syn-n0004", "area")
    assert got.held["counts"]["waits"] == []
    assert waits_of(sitting, "borders") == [{"queue": "names", "title": "Names", "left": 2}]
    sitting.decide("names", "a:syn-n0004:dulcimer", "skip")
    assert waits_of(sitting, "borders")[0]["left"] == 2, "a skipped name is still to decide"
    sitting.decide("names", "a:syn-n0004:dulcimer", "inside")
    sitting.decide("names", "n:syn-n0007", "drop")
    assert waits_of(sitting, "borders") == waits_of(sitting, "ratings") == []


def with_ground(made: Made) -> None:
    """The names of the made-up desk, with ground under the two that are areas, and the
    words the page is given for an answer that a build will set aside."""
    held = [
        {**each, "preset": {**each["preset"], "holds": "cells"}}
        if each["id"].startswith("n:")
        else each
        for each in NAMES
    ]
    write_items(made.data, "names", held)
    names = {**QUESTIONS["queues"][0], "set_aside": {"answers": ["inside", "wide", "drop"]}}
    asked = {**QUESTIONS, "queues": [names, *QUESTIONS["queues"][1:]]}
    made.questions.write_text(json.dumps(asked))


def test_the_desk_counts_the_names_turned_down_that_wait_for_a_new_draft(
    made: Made, opener: Opener
):
    # An area cannot be dropped while it has ground. The answer is saved, and the founder
    # is told at once that it waits, and not hours later by the step that makes the files.
    with_ground(made)
    sitting = opener()
    ground = {"detail": {"holds": "cells"}}
    got = sitting.decide("names", "n:syn-n0004", "area", **ground)
    assert (got.status, got.held["counts"]["set_aside"]) == (200, 0)
    got = sitting.decide("names", "n:syn-n0007", "drop", **ground)
    assert (got.status, got.held["counts"]["set_aside"]) == (200, 1)
    assert got.held["line"]["answer"] == "drop", "the answer is saved as it was given"
    names = sitting.get("/api/state").held["queues"][0]
    assert (names["done"], names["set_aside"]) == (2, 1)
    assert sitting.undo("names").held["counts"]["set_aside"] == 0


def test_borders_wait_on_a_new_draft_while_a_name_turned_down_has_ground(
    made: Made, opener: Opener
):
    with_ground(made)
    sitting = opener()
    ground = {"detail": {"holds": "cells"}}
    sitting.decide("names", "n:syn-n0004", "area", **ground)
    sitting.decide("names", "a:syn-n0004:dulcimer", "inside")
    sitting.decide("names", "n:syn-n0007", "drop", **ground)
    # Every name is read. The borders still wait: the draft is to be made again first.
    assert waits_of(sitting, "borders") == [
        {"queue": "names", "title": "Names", "left": 0, "set_aside": 1}
    ]
    assert waits_of(opener("r2"), "borders") == waits_of(sitting, "borders")
    sitting.decide("names", "n:syn-n0007", "area", **ground)
    assert waits_of(sitting, "borders") == []


def test_a_second_reviewer_is_told_what_the_founder_has_still_to_name(opener: Opener):
    opener("r1").decide("names", "n:syn-n0004", "area")
    assert waits_of(opener("r2"), "borders") == [{"queue": "names", "title": "Names", "left": 2}]


def test_a_second_reviewer_is_listed_only_the_queues_they_are_asked_to_work(opener: Opener):
    # Names are the founder's alone, and so are figures of crime and of prices, which no
    # rater should meet on the way to a rating.
    second = opener("r2")
    assert [each["queue"] for each in second.get("/api/state").held["queues"]] == [
        "borders",
        "ratings",
    ]
    assert second.get("/api/queue/names").status == 404
    assert second.get("/api/item/names/n%3Asyn-n0004").status == 404
    assert second.decide("names", "n:syn-n0004", "area", stands=None).status == 404
    assert not list(second.desk.data.glob("decisions*")), "and nothing is written"
    founder = opener("r1")
    assert [each["queue"] for each in founder.get("/api/state").held["queues"]] == [
        "names",
        "borders",
        "ratings",
    ]


def test_the_boroughs_a_reviewer_knows_well_are_offered_first(opener: Opener, made: Made):
    write_items(made.data, "know", [item("quillhaven"), item("marrowmere")])
    far = [item(f"syn-n01{at}", group="marrowmere") for at in (1, 2)]
    write_items(made.data, "borders", [*BORDERS, *far])
    EVERY.extend(far)
    try:
        sitting = opener()
        listed = [each["id"] for each in sitting.get("/api/queue/borders").held["items"]]
        assert listed == ["syn-n0007", "syn-n0012", "syn-n011", "syn-n012"]
        sitting.decide("know", "marrowmere", "well")
        sitting.decide("know", "quillhaven", "not")
        listed = [each["id"] for each in sitting.get("/api/queue/borders").held["items"]]
        assert listed == ["syn-n011", "syn-n012", "syn-n0007", "syn-n0012"]
        got = sitting.decide("borders", "syn-n011", "right")
        assert got.held["next"] == "syn-n012", "and the next item follows the same order"
        assert sitting.get("/api/state").held["resume"] == {"queue": "borders", "item": "syn-n012"}
        # Another reviewer knows other ground, and is offered the order of the file.
        other = [each["id"] for each in opener("r2").get("/api/queue/borders").held["items"]]
        assert other == ["syn-n0007", "syn-n0012", "syn-n011", "syn-n012"]
    finally:
        del EVERY[-2:]


# What is shown


def test_state_gives_each_queue_with_items_in_the_order_of_the_questions(sitting: Sitting):
    held = sitting.get("/api/state").held
    assert (held["desk"], held["reviewer"], held["token"]) == (1, "r1", sitting.desk.token)
    assert (held["resume"], held["broken_lines"]) == (None, 0)
    assert [each["queue"] for each in held["queues"]] == ["names", "borders", "ratings"]
    assert held["queues"][0] == {
        "queue": "names",
        "title": "Names",
        "total": 3,
        "done": 0,
        "wrong": 0,
        "not_known": 0,
        "skipped": 0,
        "stale": 0,
        "disputed": 0,
        "by_rule": 0,
        "flagged": 1,
        "flagged_left": 1,
        "second": 0,
        "median_seconds": None,
        "last_hour": 0,
        "set_aside": 0,
        "waits": [],
    }


def test_a_queue_gives_its_question_as_the_file_holds_it_and_each_items_state(sitting: Sitting):
    sitting.decide("names", "n:syn-n0004", "area")
    sitting.decide("names", "n:syn-n0007", "skip")
    held = sitting.get("/api/queue/names").held
    assert held["question"] == QUESTIONS["queues"][0]
    # An item says whether it is flagged, so that a key can go to the next that is.
    assert held["items"] == [
        {"id": "n:syn-n0004", "group": "quillhaven", "state": "done", "flagged": True},
        {"id": "a:syn-n0004:dulcimer", "group": "quillhaven", "state": "open", "flagged": False},
        {"id": "n:syn-n0007", "group": "quillhaven", "state": "skipped", "flagged": False},
    ]


def test_a_queue_with_an_answer_for_a_whole_part_says_which_part_each_item_is_of(
    sitting: Sitting,
):
    rated = sitting.get("/api/queue/ratings").held["items"]
    assert rated == [
        {
            "id": "syn-n0004:leafy",
            "group": "quillhaven",
            "state": "open",
            "flagged": False,
            "part": "syn-n0004",
        }
    ]
    named = sitting.get("/api/queue/names").held["items"]
    assert all(set(each) == {"id", "group", "state", "flagged"} for each in named)


def test_names_are_offered_in_the_order_of_the_boroughs_the_reviewer_knows(
    made: Made, opener: Opener
):
    held = [
        item("n:syn-n0004", picks=["Dulcimer Green"]),
        item("a:syn-n0004:dulcimer", picks=["Dulcimer"], preset={"of": ["syn-n0004"]}),
        item("n:syn-n0012", group="marrowmere", picks=["Thrushcombe"]),
        item("a:syn-n0012:osier", group="marrowmere", picks=["Osier"]),
    ]
    write_items(made.data, "names", held)
    boroughs = [item("quillhaven", group="all"), item("marrowmere", group="all")]
    write_items(made.data, "know", boroughs)
    sitting = opener()
    before = [each["id"] for each in sitting.get("/api/queue/names").held["items"]]
    assert before == [each["id"] for each in held]
    assert sitting.decide("know", "marrowmere", "well").status == 200
    after = [each["id"] for each in sitting.get("/api/queue/names").held["items"]]
    # The borough that is known comes first, whole, and then the next.
    assert after == ["n:syn-n0012", "a:syn-n0012:osier", "n:syn-n0004", "a:syn-n0004:dulcimer"]


def test_an_item_is_given_as_its_file_holds_it(sitting: Sitting):
    held = sitting.get("/api/item/names/n%3Asyn-n0004").held
    assert held["item"] == NAMES[0]
    assert (held["state"], held["mine"], held["moves"], held["others"]) == ("open", None, [], [])


def test_the_desk_opens_where_the_reviewer_left_off(opener: Opener):
    clock = iter(START + timedelta(minutes=at) for at in range(10))
    first = opener(clock=lambda: next(clock))
    first.decide("names", "n:syn-n0004", "area")
    first.decide("borders", "syn-n0007", "right")
    assert first.get("/api/state").held["resume"] == {"queue": "borders", "item": "syn-n0012"}
    first.decide("borders", "syn-n0012", "right")

    again = opener()
    assert again.desk.token != first.desk.token
    held = again.get("/api/state").held
    assert held["resume"] == {"queue": "names", "item": "a:syn-n0004:dulcimer"}
    assert [each["done"] for each in held["queues"]] == [1, 2, 0]


def test_an_item_that_changed_is_open_again_with_the_old_answer_shown(opener: Opener, made: Made):
    opener().decide("names", "n:syn-n0004", "area")
    changed = [{**NAMES[0], "title": "Dulcimer, Quillhaven", "rev": "f" * 12}, *NAMES[1:]]
    write_items(made.data, "names", changed)

    again = opener()
    shown = again.get("/api/item/names/n%3Asyn-n0004").held
    assert (shown["state"], shown["mine"]["answer"]) == ("stale", "area")
    counts = again.get("/api/state").held["queues"][0]
    assert (counts["done"], counts["stale"]) == (0, 1)
    assert again.get("/api/state").held["resume"] == {"queue": "names", "item": "n:syn-n0004"}
    assert len(again.lines("names")) == 1, "the old line is kept"


def test_a_clock_that_goes_backwards_changes_nothing_that_stands(opener: Opener):
    clock = iter(START - timedelta(hours=at) for at in range(10))
    sitting = opener(clock=lambda: next(clock))
    sitting.decide("names", "n:syn-n0004", "area")
    sitting.decide("names", "n:syn-n0004", "drop")
    sitting.decide("names", "n:syn-n0007", "area")
    times = [line.at for line in sitting.lines("names")]
    assert times == sorted(times, reverse=True) and len(set(times)) == 3
    assert sitting.get("/api/item/names/n%3Asyn-n0004").held["mine"]["answer"] == "drop"
    assert sitting.undo("names").held["undone"]["item"] == "n:syn-n0007"
    counts = sitting.get("/api/state").held["queues"][0]
    assert (counts["done"], counts["median_seconds"]) == (1, 12)
    assert 0 <= counts["last_hour"] <= 3


# Two reviewers


def test_another_reviewers_answer_is_shown_only_once_mine_stands(opener: Opener, made: Made):
    others_file(
        made, "borders", "r2", {"item": "syn-n0007", "answer": "right", "note": "Walked it."}
    )
    sitting = opener()
    before = sitting.get("/api/item/borders/syn-n0007").held
    assert (before["state"], before["others"]) == ("open", [])
    sitting.decide("borders", "syn-n0007", "skip")
    assert sitting.get("/api/item/borders/syn-n0007").held["others"] == []

    sitting.decide("borders", "syn-n0007", "right")
    after = sitting.get("/api/item/borders/syn-n0007").held
    assert after["state"] == "done"
    assert after["others"] == [
        {
            "reviewer": "r2",
            "answer": "right",
            "note": "Walked it.",
            "at": "2026-10-06T21:14:09Z",
            "moves": [],
        }
    ]


def test_the_cells_another_reviewer_moved_are_shown_once_mine_stands(opener: Opener, made: Made):
    # The founder settles a border, or reads a reviewer's work, with the cells in view.
    moved = {"item": "syn-n0007", "answer": "move", **move("syn-n0007", "syn-oa0101", "syn-n0012")}
    told = {"item": "syn-n0007", "answer": "right", "note": "Walked it."}
    others_file(made, "borders", "r2", moved, told)
    sitting = opener()
    assert sitting.get("/api/item/borders/syn-n0007").held["others"] == []
    sitting.decide("borders", "syn-n0007", "unknown")
    after = sitting.get("/api/item/borders/syn-n0007").held
    assert after["state"] == "done", "not knowing is no dispute"
    assert after["moves"] == [], "my own moves, of which there are none"
    assert [(each["reviewer"], each["answer"], each["moves"]) for each in after["others"]] == [
        ("r2", "right", [{"part": "syn-oa0101", "from": "syn-n0007", "to": "syn-n0012"}])
    ]
    counts = sitting.get("/api/state").held["queues"][1]
    assert (counts["done"], counts["disputed"]) == (1, 0)


def test_two_reviewers_who_disagree_are_in_dispute_until_the_founder_settles(
    opener: Opener, made: Made
):
    others_file(made, "borders", "r2", {"item": "syn-n0007", "answer": "right"})
    sitting = opener()
    sitting.decide("borders", "syn-n0007", "wrong", note="The brook is the edge.")
    assert sitting.state_of("borders", "syn-n0007") == "disputed"
    counts = sitting.get("/api/state").held["queues"][1]
    assert (counts["done"], counts["disputed"]) == (0, 1)

    settled = sitting.decide(
        "borders", "syn-n0007", "wrong", note="Walked it. The brook.", settles=True
    )
    assert settled.held["line"]["settles"] is True
    assert sitting.state_of("borders", "syn-n0007") == "done"
    assert sitting.undo("borders").held["undone"]["settles"] is True
    assert sitting.state_of("borders", "syn-n0007") == "disputed"


def test_only_the_founder_settles_and_only_a_dispute(opener: Opener, made: Made):
    others_file(made, "borders", "r1", {"item": "syn-n0007", "answer": "right"})
    second = opener("r2")
    second.decide("borders", "syn-n0007", "wrong", note="The lane.")
    got = second.decide("borders", "syn-n0007", "wrong", note="The lane.", settles=True)
    assert (got.status, got.held["message"]) == (400, "Only the first reviewer settles a dispute.")

    founder = opener("r1")
    nothing = founder.decide("borders", "syn-n0012", "right", settles=True)
    assert (nothing.status, nothing.held["message"]) == (
        400,
        "There is no dispute on this item to settle.",
    )
    assert founder.decide("borders", "syn-n0007", "right", settles=True).status == 200


def test_what_the_founder_marked_comes_first_for_the_second_reviewer(opener: Opener):
    opener("r1").decide("borders", "syn-n0012", "right", second=True)
    second = opener("r2")
    assert [each["id"] for each in second.get("/api/queue/borders").held["items"]] == [
        "syn-n0012",
        "syn-n0007",
    ]
    assert second.decide("borders", "syn-n0012", "right").held["next"] == "syn-n0007"


def test_each_reviewer_writes_a_file_of_their_own(opener: Opener, made: Made):
    opener("r1").decide("ratings", "syn-n0004:leafy", "2")
    opener("r7").decide("ratings", "syn-n0004:leafy", "5")
    folder = made.data / "decisions-private" / "ratings"
    assert sorted(path.name for path in folder.iterdir()) == ["r1.jsonl", "r7.jsonl"]
    assert not (made.data / "decisions").exists(), "a rating is never among what is published"
    assert opener("r7").state_of("ratings", "syn-n0004:leafy") == "done", "a rating is no dispute"


def test_the_server_writes_nowhere_but_the_folders_of_decisions(sitting: Sitting, made: Made):
    def files() -> set[str]:
        root = made.data.parent
        return {str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()}

    before = files()
    sitting.decide("names", "n:syn-n0004", "area")
    sitting.decide("borders", "syn-n0007", "move", **move("syn-n0007", "syn-oa0101", "syn-n0012"))
    sitting.undo("borders")
    sitting.decide("ratings", "syn-n0004:leafy", "4")
    sitting.get("/api/layer/quillhaven/cells")
    assert files() - before == {
        "data/decisions/names/r1.jsonl",
        "data/decisions/borders/r1.jsonl",
        "data/decisions-private/ratings/r1.jsonl",
    }


def test_the_desk_does_not_start_on_lines_in_the_wrong_folder(made: Made):
    # As a folder of decisions from before the two were kept apart. No line is passed over.
    others_file(made, "names", "r1", {"item": "n:syn-n0004", "answer": "area"})
    (made.data / "decisions" / "names").rename(made.data / "decisions" / "ratings")
    with pytest.raises(Unfit, match="wrong folder: decisions/ratings"):
        open_desk(made.data, made.page, made.questions, "r1")


# What an answer costs


def test_an_answer_reads_no_file_of_decisions_again(
    sitting: Sitting, monkeypatch: pytest.MonkeyPatch
):
    # An answer read its file three times, so each answer was slower than the last.
    sitting.decide("names", "n:syn-n0004", "area")
    sitting.decide("borders", "syn-n0007", "right")
    sitting.get("/api/state")
    read_whole: list[int] = []
    real = records.read_bytes

    def counted(data: bytes) -> records.Read:
        read_whole.append(len(data))
        return real(data)

    monkeypatch.setattr(records, "read_bytes", counted)
    assert sitting.decide("borders", "syn-n0012", "right", stands=None).status == 200
    assert sitting.undo("borders").status == 200
    assert sitting.get("/api/state").status == 200
    assert sitting.get("/api/queue/borders").status == 200
    assert sitting.get("/api/item/borders/syn-n0012").status == 200
    assert read_whole == []
    assert [line.answer for line in sitting.lines("borders")] == ["right", "right", "undo"]


def test_what_another_desk_wrote_is_seen_at_the_next_request(opener: Opener, made: Made):
    mine, other = opener(), opener()
    mine.decide("names", "n:syn-n0004", "area")
    assert other.state_of("names", "n:syn-n0004") == "done"
    other.decide("names", "n:syn-n0007", "drop")
    assert mine.state_of("names", "n:syn-n0007") == "done"
    got = mine.decide("names", "a:syn-n0004:dulcimer", "inside")
    assert got.held["line"]["n"] == 3
    assert [line.n for line in mine.lines("names")] == [1, 2, 3]


def test_a_file_sent_back_by_another_reviewer_is_seen_without_a_new_start(
    opener: Opener, made: Made
):
    sitting = opener()
    sitting.decide("borders", "syn-n0007", "right")
    assert sitting.get("/api/item/borders/syn-n0007").held["others"] == []
    others_file(made, "borders", "r2", {"item": "syn-n0007", "answer": "right"})
    assert [
        each["reviewer"] for each in sitting.get("/api/item/borders/syn-n0007").held["others"]
    ] == ["r2"]


# The kept copy


def copies(made: Made) -> dict[str, bytes]:
    return {
        str(path.relative_to(made.kept)): path.read_bytes()
        for path in sorted(made.kept.rglob("*.jsonl"))
    }


def lines_on_disk(made: Made) -> dict[str, bytes]:
    return {
        str(path.relative_to(made.data)): path.read_bytes()
        for path in sorted(made.data.glob("decisions*/*/*.jsonl"))
    }


def test_every_line_is_in_the_kept_copy_before_the_server_answers(opener: Opener, made: Made):
    # `git clean -x` takes `data/raw/`. The copy is outside the repository.
    sitting = opener(keep=made.kept)
    assert sitting.decide("names", "n:syn-n0004", "area").status == 200
    assert copies(made) == lines_on_disk(made) != {}
    sitting.decide("borders", "syn-n0007", "move", **move("syn-n0007", "syn-oa0101", "syn-n0012"))
    sitting.undo("borders")
    sitting.decide("ratings", "syn-n0004:leafy", "4")
    assert copies(made) == lines_on_disk(made)
    assert sorted(copies(made)) == [
        "decisions-private/ratings/r1.jsonl",
        "decisions/borders/r1.jsonl",
        "decisions/names/r1.jsonl",
    ]
    assert all(path.stat().st_mode & 0o777 == 0o600 for path in made.kept.rglob("*.jsonl"))


def test_with_no_kept_copy_asked_for_the_made_up_city_keeps_none(sitting: Sitting, made: Made):
    sitting.decide("names", "n:syn-n0004", "area")
    assert not made.kept.exists()


def test_the_desk_does_not_start_on_real_data_without_a_kept_copy(made: Made):
    as_if_real(made)
    with pytest.raises(Unfit, match=r"make desk KEEP=FOLDER"):
        open_desk(made.data, made.page, made.questions, "r1")
    assert open_desk(made.data, made.page, made.questions, "r1", keep=made.kept).keep == made.kept


@pytest.mark.parametrize("where", ["data", "data/decisions", "desk/page"])
def test_the_kept_copy_is_kept_apart_from_what_it_copies(made: Made, where: str):
    inside = made.data.parent / where
    with pytest.raises(Unfit, match="apart from the desk's own folders"):
        open_desk(made.data, made.page, made.questions, "r1", keep=inside)


def test_the_kept_copy_is_outside_the_repository(made: Made):
    repository = made.data.parent / "repository"
    with pytest.raises(Unfit, match="outside the repository"):
        open_desk(
            made.data, made.page, made.questions, "r1", keep=repository / "kept", outside=repository
        )
    assert not repository.exists()


def test_when_the_kept_copy_cannot_be_written_the_answer_says_not_saved_and_is_kept_once_it_can(
    opener: Opener, made: Made, monkeypatch: pytest.MonkeyPatch
):
    sitting = opener(keep=made.kept)
    sitting.decide("names", "n:syn-n0004", "area")
    kept = records.keep_up

    def full(file: Path, copy: Path) -> int:
        raise OSError(errno.ENOSPC, f"No space left on device: {CANARY}")

    monkeypatch.setattr(records, "keep_up", full)
    got = sitting.decide("names", "n:syn-n0007", "drop", note=CANARY)
    assert (got.status, got.error) == (500, "not_saved")
    assert got.held["message"].startswith("Not saved. The disk is full.")
    assert b"Zzyzx" not in got.raw and "Zzyzx" not in "".join(sitting.log)
    assert copies(made) != lines_on_disk(made)
    # The page keeps the answer and sends it again. It is written once, and then kept.
    monkeypatch.setattr(records, "keep_up", kept)
    again = sitting.decide("names", "n:syn-n0007", "drop", note=CANARY, stands=None)
    assert (again.status, again.held["line"]["n"]) == (200, 2)
    assert len(sitting.lines("names")) == 2
    assert copies(made) == lines_on_disk(made)


def test_a_kept_copy_that_differs_while_the_desk_runs_stops_the_answer_and_says_so(
    opener: Opener, made: Made
):
    sitting = opener(keep=made.kept)
    sitting.decide("names", "n:syn-n0004", "area")
    copy = made.kept / "decisions" / "names" / "r1.jsonl"
    copy.write_bytes(copy.read_bytes() + b"a line the folder does not hold\n")
    got = sitting.decide("names", "n:syn-n0007", "drop")
    assert (got.status, got.error) == (500, "not_saved")
    assert got.held["message"] == (
        "Not saved in the kept copy, which holds what the desk's folder does not. "
        "Stop the desk, and look at both."
    )
    assert copy.read_bytes().endswith(b"a line the folder does not hold\n")


def test_a_kept_copy_that_is_behind_is_brought_up_when_the_desk_starts(opener: Opener, made: Made):
    opener(keep=made.kept).decide("names", "n:syn-n0004", "area")
    opener().decide("names", "n:syn-n0007", "drop")
    assert copies(made) != lines_on_disk(made)
    again = opener(keep=made.kept)
    assert copies(made) == lines_on_disk(made)
    assert again.desk.brought_up == 1


def test_the_desk_does_not_start_when_the_kept_copy_holds_what_the_folder_has_lost(
    opener: Opener, made: Made
):
    sitting = opener(keep=made.kept)
    sitting.decide("names", "n:syn-n0004", "area")
    sitting.decide("ratings", "syn-n0004:leafy", "4")
    kept = copies(made)
    shutil.rmtree(made.data / "decisions")
    with pytest.raises(Unfit) as refusal:
        open_desk(made.data, made.page, made.questions, "r1", keep=made.kept)
    said = str(refusal.value)
    assert "The kept copy holds decisions that the desk's folder has lost" in said
    assert "decisions/names/r1.jsonl" in said and "Copy them back" in said
    assert copies(made) == kept, "and the copy is left as it was"


def test_the_desk_does_not_start_when_the_two_copies_differ(opener: Opener, made: Made):
    opener(keep=made.kept).decide("names", "n:syn-n0004", "area")
    file = path_of(made.data, "names", "r1")
    file.write_bytes(file.read_bytes().replace(b'"area"', b'"drop"'))
    with pytest.raises(Unfit, match=r"differ: decisions/names/r1\.jsonl"):
        open_desk(made.data, made.page, made.questions, "r1", keep=made.kept)


# Layers


def test_a_layer_is_served_as_its_file_holds_it(sitting: Sitting, made: Made):
    got = sitting.get("/api/layer/quillhaven/cells")
    assert got.status == 200
    assert got.raw == (made.data / "layers" / "quillhaven" / "cells.geojson").read_bytes()


def test_a_layer_of_the_other_city_is_never_served(opener: Opener, made: Made):
    write_layer(made.data, "quillhaven", "roads", synthetic=False)
    write_layer(made.data, "quillhaven", "wards", layer="roads")
    write_layer(made.data, "all", "boroughs", group="quillhaven")
    (made.data / "layers" / "quillhaven" / "names.geojson").write_text("not json")
    (made.data / "layers" / "quillhaven" / "seeds.geojson").write_text("[]")
    sitting = opener()
    for name in ("roads", "wards", "names", "seeds", "nothing"):
        assert sitting.get(f"/api/layer/quillhaven/{name}").status == 404
    assert sitting.get("/api/layer/all/boroughs").status == 404


def test_a_layer_is_not_followed_out_of_its_folder(opener: Opener, made: Made, tmp_path: Path):
    elsewhere = tmp_path / "elsewhere.geojson"
    elsewhere.write_text(json.dumps(LAYER))
    (made.data / "layers" / "quillhaven" / "roads.geojson").symlink_to(elsewhere)
    assert opener().get("/api/layer/quillhaven/roads").status == 404


# What is printed


def test_the_line_of_a_request_is_there_when_its_answer_is_read(sitting: Sitting):
    # The desk prints the line of a request once its answer is sent. A caller that reads
    # what was printed straight after an answer must find the line, however late it is.
    write = sitting.desk.log

    def late(line: str) -> None:
        time.sleep(0.2)
        write(line)

    object.__setattr__(sitting.desk, "log", late)
    assert sitting.get("/api/state").status == 200
    assert sitting.log == ["GET /api/state 200"]


def test_the_log_holds_the_method_the_template_and_the_status_and_nothing_sent(sitting: Sitting):
    sitting.get("/")
    sitting.get("/page/desk.mjs")
    sitting.get("/api/item/names/n%3Asyn-n0004")
    sitting.get("/api/layer/quillhaven/cells")
    sitting.decide("names", "n:syn-n0004", "area", note=CANARY, stands=None)
    sitting.decide("names", CANARY, "area")
    sitting.undo("names")
    sitting.get(f"/page/{CANARY.replace(' ', '%20')}")
    sitting.get("/nothing/at/all")
    sitting.ask("BREW", "/api/state")
    sitting.get("/", host=CANARY)
    assert sitting.log == [
        "GET / 200",
        "GET /page/{name} 200",
        "GET /api/item/{queue}/{item} 200",
        "GET /api/layer/{group}/{layer} 200",
        "GET /api/state 200",
        "POST /api/decide 200",
        "POST /api/decide 404",
        "POST /api/undo 200",
        "GET /page/{name} 404",
        "GET - 404",
        "- - 405",
        "GET - 403",
    ]


# The one command


def run_desk(*args: str, cwd: Path) -> subprocess.Popen[str]:
    """The desk as `make desk` starts it: `python -m desk`, with `tools` on the path."""
    environ = {**os.environ, "PYTHONPATH": str(TOOLS)}
    return subprocess.Popen(
        [sys.executable, "-m", "desk", *args],
        cwd=cwd,
        env=environ,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def test_the_one_command_starts_the_desk_prints_the_address_and_opens_nothing(tmp_path: Path):
    data = tmp_path / "desk-synthetic"
    filled = run_desk("fill", "--made-up", "--data", str(data), cwd=tmp_path)
    assert filled.wait(timeout=20) == 0

    desk = run_desk("serve", "--data", str(data), "--port", "0", "--reviewer", "r1", cwd=tmp_path)
    stop = threading.Timer(20, desk.kill)
    stop.start()
    try:
        assert desk.stdout is not None
        said = [desk.stdout.readline() for _ in range(5)]
        assert said[:2] == [
            "The review desk, as r1.\n",
            "MADE-UP CITY. Nothing here is a real place.\n",
        ]
        address = re.fullmatch(r"Open http://127\.0\.0\.1:(\d+)/\n", said[3])
        assert address is not None, "the desk prints the address to open"
        sitting = Sitting(cast(Desk, None), int(address[1]), [], hears=False)

        assert b"<html" in sitting.get("/").raw.lower()
        assert desk.stdout.readline() == "GET / 200\n", "a line is printed when it happens"
        state = sitting.get("/api/state").held
        assert (state["synthetic"], state["reviewer"], len(state["queues"])) == (True, "r1", 12)
        first = sitting.get("/api/queue/names").held["items"][0]["id"]
        shown = sitting.get(f"/api/item/names/{quote(first, safe='')}").held["item"]
        sent = decision("names", first, "area", rev=shown["rev"], detail=shown["preset"])
        sitting.token = state["token"]
        assert sitting.post("/api/decide", sent).held["line"]["n"] == 1

        desk.send_signal(signal.SIGINT)
        assert desk.wait(timeout=10) == 0
        rest = desk.stdout.read()
    finally:
        stop.cancel()
        desk.kill()
    assert rest.endswith("Stopped.\n")
    assert "POST /api/decide 200" in rest
    assert first not in rest and shown["title"] not in rest, "what is printed names no item"

    made = run_desk("compile", "--data", str(data), cwd=tmp_path)
    assert made.wait(timeout=20) == 0
    lines = path_of(data, "names", "r1").read_bytes()
    assert lines.count(b"\n") == 1
    states = {
        row.split(",")[0]: row.split(",")[5]
        for row in (data / "gazetteer" / "areas.csv").read_text().splitlines()
    }
    assert states[first.removeprefix("n:")] == "name_checked"
    assert sorted(path.name for path in data.iterdir()) == [
        "decisions",
        "draft",
        "gazetteer",
        "items",
        "layers",
        "out",
    ]


def test_an_older_python_is_told_what_the_desk_needs():
    main = (TOOLS / "desk" / "__main__.py").read_text(encoding="utf-8")
    tree = ast.parse(main, feature_version=(3, 8))
    assert isinstance(tree.body[2], ast.If), "the check comes before the desk is read"
    assert "make desk" in main


def test_the_desk_opens_nothing_and_starts_no_other_program():
    for name in ("__init__", "__main__", "cli", "records", "server", "compile"):
        tree = ast.parse((TOOLS / "desk" / f"{name}.py").read_text(encoding="utf-8"))
        named = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import | ast.ImportFrom)
            for alias in (
                [ast.alias(node.module or "")] if isinstance(node, ast.ImportFrom) else node.names
            )
        }
        assert not named & {"webbrowser", "subprocess", "urllib3", "requests", "socket", "ssl"}, (
            name
        )
        called = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        assert not called & {"system", "startfile", "popen", "urlopen", "spawnl", "execv"}, name


def test_make_desk_runs_the_command_and_nothing_more():
    makefile = (TOOLS.parent / "Makefile").read_text(encoding="utf-8")
    recipe = re.search(r"^desk:.*\n((?:\t.*\n)+)", makefile, re.MULTILINE)
    assert recipe is not None
    assert recipe[1] == (
        "\t@PYTHONPATH=tools uv run --no-project python -m desk serve "
        "--reviewer $(REVIEWER) $(if $(KEEP),--keep $(KEEP)) $(ARGS)\n"
    )
