"""A sitting at the desk, walked through its own port with no browser.

The queues are filled from the synthetic release and the server is started on a port
the system picks. Every request is one the page makes, built as the page builds it:
the same paths, the same headers, the same ten fields of a decision. Ten items of each
queue are answered, with a move, a skip, a mark for a second reviewer, an undo, a note,
and the server stopped and started again in the middle. A second reviewer then differs
on one claim, and the first settles it. Last, the build's files are made from the lines,
and read.

This is what holds the three parts of the desk together: the step that fills the queues,
the server, and what the page asks and reads. Every name is of the made-up city, and the
only host reached is the loopback address.
"""

import csv
import http.client
import io
import json
import re
import threading
import tomllib
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast
from urllib.parse import quote

import pytest
from desk import cli, fill, records, server
from desk import compile as make

pytestmark = pytest.mark.allow_hosts(["127.0.0.1"])

# In the order of the work, which is the order the page lists them in.
QUEUES = (
    *("rules", "know", "kinds", "commons", "figures", "sentences"),
    *("names", "borders", "whole", "ratings", "articles", "claims"),
)
ITEMS_EACH = 10
NOTE = "A made-up reason, for the walk"
START = datetime(2026, 10, 6, 21, 14, 9, tzinfo=UTC)
# The answers that give a name to an area. The page waits until one is named.
NAMES_AN_AREA = ("same_ground", "inside", "wide")
# What a browser asks for when it opens the page.
LOADED = ("/", "/page/desk.css", "/page/desk.mjs", "/page/logic.mjs", "/page/map.mjs")

# What the page reads from each answer, by route. logic.mjs and desk.mjs are the source.
STATE_READS = {"synthetic", "banner", "reviewer", "token", "resume", "broken_lines", "queues"}
COUNTS_READ = {
    *("queue", "title", "total", "done", "wrong", "not_known", "disputed"),
    *("median_seconds", "flagged_left"),
}
QUESTION_READS = {"text", "rule", "view", "adds", "answers", "flags"}
ITEM_READS = {"item", "state", "mine", "moves", "others"}
OTHERS_READ = {"reviewer", "answer", "note", "at", "moves"}
STATES = {"open", "done", "skipped", "stale", "disputed"}
# What the page reads of a feature, by layer. map.mjs is the source.
PROPERTIES_READ = {
    "cells": ("area", "colour", "borough"),
    "areas": ("name",),
    "boroughs": ("name",),
    "wards": ("name",),
    "centres": ("name",),
    "roads": ("class", "name"),
    "names": ("name",),
    "seeds": ("area", "name"),
    "records": ("source_id", "as_written"),
}


REGISTRY = cli.ROOT / "registry" / "sources"
# The queues whose lines are never published, as the questions say.
PRIVATE = {
    queue["id"]
    for queue in json.loads(cli.QUESTIONS.read_text(encoding="utf-8"))["queues"]
    if not queue["public"]
}


def lines_of(data: Path, queue: str, reviewer: str = "r1") -> records.Read:
    """What one reviewer's file of a queue holds, in whichever tree it is kept."""
    return records.read(records.path_of(data, queue, reviewer, private=queue in PRIVATE))


def out_of(data: Path, name: str) -> Path:
    """A file of `out`, which is under `private` when it is made from private lines."""
    kept = data / "out" / "private" / name
    return kept if kept.is_file() else data / "out" / name


def of_the_map(pattern: str) -> str:
    """A value that map.mjs holds, read from the page itself."""
    found = re.search(pattern, (cli.PAGE / "map.mjs").read_text(encoding="utf-8"))
    assert found is not None, "map.mjs says what the page may draw, and what it never draws"
    return found[1]


def may_draw() -> list[str]:
    """The layers the page may ask for."""
    return json.loads(of_the_map(r"export const MAY_DRAW = (\[[^\]]+\]);").replace("'", '"'))


def path_of(*words: str) -> str:
    """A path as the page builds it: each word escaped, and a colon left as it is."""
    return "/api/" + "/".join(quote(word, safe="-_.!~*'():") for word in words)


@dataclass
class Page:
    """Asks the desk as the page does, and keeps what the page keeps."""

    port: int
    token: str = ""
    synthetic: bool | None = None
    layers: dict[str, dict[str, Any]] = field(default_factory=lambda: dict[str, dict[str, Any]]())
    asked: list[str] = field(default_factory=lambda: list[str]())

    def ask(self, method: str, path: str, sent: Any = None) -> tuple[int, dict[str, str], bytes]:
        own = f"http://127.0.0.1:{self.port}"
        headers = {"Accept": "application/json", "Sec-Fetch-Site": "same-origin"}
        body = None
        if method == "POST":
            body = json.dumps(sent).encode()
            headers |= {
                "Origin": own,
                "Content-Type": "application/json",
                "X-Desk-Token": self.token,
            }
        self.asked.append(f"{method} {path}")
        link = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            link.request(method, path, body, headers)
            got = link.getresponse()
            return got.status, {k.lower(): v for k, v in got.getheaders()}, got.read()
        finally:
            link.close()

    def get(self, path: str) -> dict[str, Any]:
        status, _, raw = self.ask("GET", path)
        assert status == 200, f"GET {path} gave {status}"
        held: dict[str, Any] = json.loads(raw)
        self.same_city(held if "desk" not in held or "token" in held else held["desk"])
        return held

    def same_city(self, held: dict[str, Any]) -> None:
        """Every answer says which data it is of. The page stops if two differ."""
        assert isinstance(held.get("synthetic"), bool), "an answer does not say which data it is of"
        if self.synthetic is None:
            self.synthetic = held["synthetic"]
        assert held["synthetic"] is self.synthetic

    def open(self) -> dict[str, Any]:
        held = self.get("/api/state")
        self.token = held["token"]
        return held

    def post(self, what: str, sent: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        """Send a write. If the desk was started again, ask who it is now and send again."""
        status, _, raw = self.ask("POST", f"/api/{what}", sent)
        if status == 403:
            self.open()
            status, _, raw = self.ask("POST", f"/api/{what}", sent)
        held: dict[str, Any] = json.loads(raw)
        self.same_city(held)
        return status, held

    def item(self, queue: str, name: str) -> dict[str, Any]:
        """An item, and every layer of its map that the page does not hold yet."""
        held = self.get(path_of("item", queue, name))
        drawn = cast(dict[str, list[str]], held["item"]["map"] or {})
        for layer in drawn.get("layers", []):
            group: str = "all" if layer == "boroughs" else held["item"]["group"]
            if f"{group}/{layer}" not in self.layers:
                self.layers[f"{group}/{layer}"] = self.get(path_of("layer", group, layer))
        return held

    def layer(self, shown: dict[str, Any], layer: str) -> dict[str, Any]:
        return self.layers[f"{shown['item']['group']}/{layer}"]


def next_open(entries: list[dict[str, Any]], after: str | None) -> str | None:
    """The next item as the page chooses it: the first open after this one, going round
    to the start. When none is open, the first that was skipped."""
    ids = [entry["id"] for entry in entries]
    at = ids.index(after) if after in ids else -1
    order = [entries[(at + step) % len(entries)] for step in range(1, len(entries) + 1)]
    for wanted in (("open", "stale", "disputed"), ("skipped",)):
        for entry in order:
            if entry["state"] in wanted:
                return entry["id"]
    return None


def detail_of(question: dict[str, Any], item: dict[str, Any], of: list[str]) -> dict[str, Any]:
    """What the page adds to a line: the item's preset, the spelling and the areas named."""
    detail = dict(item["preset"])
    if "pick" in question["adds"] and item["picks"]:
        detail["pick"] = item["picks"][-1]
    if "pick" in question["adds"] and isinstance(item["preset"].get("of"), list):
        detail["of"] = of
    return detail


def decision(queue: str, shown: dict[str, Any], answer: str, **more: Any) -> dict[str, Any]:
    """A decision as the page sends it, with the line it was shown as standing."""
    part = more.get("part", "")
    moved = next((each["n"] for each in shown["moves"] if each["part"] == part), None)
    mine = None if shown["mine"] is None else shown["mine"]["n"]
    held: dict[str, Any] = {
        "queue": queue,
        "item": shown["item"]["id"],
        "rev": shown["item"]["rev"],
        "part": "",
        "answer": answer,
        "note": "",
        "second": False,
        "settles": False,
        "detail": {},
        "seconds": 12,
        "stands": moved if part else mine,
    }
    return {**held, **more}


@dataclass
class Sat:
    """What happened in one queue."""

    question: dict[str, Any]
    entries: list[dict[str, Any]]
    # By item: the answer given, as the page sent it. A skipped item is not here.
    answered: dict[str, dict[str, Any]] = field(default_factory=lambda: dict[str, dict[str, Any]]())
    shown: dict[str, dict[str, Any]] = field(default_factory=lambda: dict[str, dict[str, Any]]())
    moved: dict[str, Any] | None = None
    skipped: str = ""
    undone: dict[str, Any] | None = None
    refused_without_note: dict[str, Any] | None = None
    resumed: dict[str, Any] | None = None
    # The item whose answer was sent to a desk that had been stopped and started again.
    across: str = ""
    lines: int = 0
    counts: dict[str, Any] = field(default_factory=lambda: dict[str, Any]())


@dataclass
class Walked:
    data: Path
    first: dict[str, Any]
    files: dict[str, tuple[dict[str, str], bytes]]
    sat: dict[str, Sat]
    layers: dict[str, dict[str, Any]]
    log: list[str]
    asked: list[str]
    tokens: set[str]
    dispute: dict[str, Any]
    built: make.Built
    again: make.Built


class Running:
    """The desk, which can be stopped and started again on the port it had."""

    def __init__(self, data: Path, log: list[str]) -> None:
        self.data, self.log, self.ticks, self.port = data, log, 0, 0
        self.held: list[server.Server] = []

    def clock(self) -> datetime:
        self.ticks += 1
        return START + timedelta(seconds=7 * self.ticks)

    def start(self, reviewer: str = "r1") -> int:
        """Start the desk, and give its port. The first reviewer's keeps the port it had."""
        desk = server.open_desk(
            self.data, cli.PAGE, cli.QUESTIONS, reviewer, clock=self.clock, log=self.log.append
        )
        held = server.serve(desk, self.port if reviewer == "r1" else 0)
        threading.Thread(target=held.serve_forever, args=(0.01,), daemon=True).start()
        self.held.append(held)
        if reviewer == "r1":
            self.port = held.server_address[1]
        return held.server_address[1]

    def stop(self) -> None:
        while self.held:
            held = self.held.pop()
            held.shutdown()
            held.server_close()


def no_sync(descriptor: int) -> None:
    """Stands in for the wait on the disk."""


def a_move(page: Page, shown: dict[str, Any]) -> dict[str, Any]:
    """A cell of the item's own area, and the area of another cell on its map."""
    cells = page.layer(shown, "cells")["features"]
    focus = shown["item"]["map"]["focus"]
    own = cast(list[str], focus if isinstance(focus, list) else [focus])
    cell = next(each for each in cells if each["properties"]["area"] in own)
    here = cell["properties"]["area"]
    there = next(each["properties"]["area"] for each in cells if each["properties"]["area"] != here)
    return {"part": cell["id"], "detail": {"from": here, "to": there}}


def another_area(page: Page, shown: dict[str, Any]) -> list[str]:
    """An area that is not the one the name was proposed as, as a click on a cell gives it."""
    own = shown["item"]["id"].removeprefix("n:")
    areas = page.layer(shown, "areas")["features"]
    return [next(each["id"] for each in areas if each["id"] != own)]


def sit(running: Running, page: Page, queue: str, tokens: set[str]) -> Sat:
    """Answer ten items of a queue, as a person at the page would.

    A move comes first, then an undo, a skip and a mark for a second reviewer. The desk is
    stopped and started in the middle, and a note is written after it. A queue of three
    items has them all: its skipped item comes back as a fourth turn.
    """
    listed = page.get(path_of("queue", queue))
    sat = Sat(listed["question"], listed["items"])
    codes = [each["code"] for each in sat.question["answers"]]
    most = min(ITEMS_EACH, len(sat.entries))
    stop_at, note_at = min(5, most), min(6, most)
    now = next_open(sat.entries, None)
    turn = 0
    while now is not None and turn < ITEMS_EACH:
        shown = page.item(queue, now)
        sat.shown.setdefault(now, shown)
        entry = next(each for each in sat.entries if each["id"] == now)
        code = codes[turn % len(codes)]
        if queue == "rules":
            # No rule is adopted on this walk, so that every other line is a person's.
            # What a yes does is held in `test_rules.py`.
            code = "no"
        if code == "area" and now.startswith("a:"):
            # The page sends no such answer: another name is never made an area at the
            # desk. A borough is read whole, so its other names come among the first ten.
            code = codes[(turn + 1) % len(codes)]
        named = list(shown["item"]["preset"].get("of", []))
        if code in NAMES_AN_AREA and not named:
            named = another_area(page, shown)
        sent = decision(queue, shown, code, detail=detail_of(sat.question, shown["item"], named))
        if turn == 0 and "move" in sat.question["adds"]:
            moved = decision(queue, shown, "move", **a_move(page, shown))
            status, held = page.post("decide", moved)
            assert (status, held["next"]) == (200, now), "after a move the item stays in view"
            sat.moved = held["line"]
            status, sat.refused_without_note = page.post("decide", sent)
            assert status == 400
            sent["note"] = NOTE
        if code == "wrong" or turn == note_at:
            sent["note"] = NOTE
        if turn == 2 and not sat.skipped:
            sent = decision(queue, shown, "skip")
            sat.skipped = now
        if turn == 3:
            sent["second"] = True
        if turn == stop_at:
            # The desk stops and is started again. The page is not loaded again: it holds
            # the token of the run before, is refused, asks who the desk is now, and sends
            # the same answer again.
            running.stop()
            running.start()
            sat.resumed, sat.across = page.get("/api/state")["resume"], now
        status, held = page.post("decide", sent)
        assert status == 200, f"{queue}, turn {turn}: {held.get('message')}"
        tokens.add(page.token)
        if turn == 1:
            status, back = page.post("undo", {"queue": queue})
            assert status == 200
            sat.undone = back["undone"]
            again = page.get(path_of("queue", queue))["items"]
            assert next(e for e in again if e["id"] == now)["state"] == entry["state"]
            status, held = page.post("decide", sent)
            assert status == 200
        entry["state"] = "skipped" if sent["answer"] == "skip" else "done"
        if sent["answer"] != "skip":
            sat.answered[now] = held["line"]
        sat.counts = held["counts"]
        after = next_open(sat.entries, now)
        assert held["next"] == after, f"{queue}: the desk and the page differ on what comes next"
        now, turn = after, turn + 1
    sat.lines = len(lines_of(running.data, queue).lines)
    return sat


def differ_and_settle(running: Running, page: Page, sat: Sat) -> dict[str, Any]:
    """A second reviewer agrees on one claim and differs on another. The first settles it."""
    agreed, differed = list(sat.answered)[:2]
    second = Page(running.start("r2"))
    second.open()
    codes = [each["code"] for each in sat.question["answers"]]
    hidden = second.item("claims", differed)["others"]
    for name, code in (
        (agreed, sat.answered[agreed]["answer"]),
        (differed, next(code for code in codes if code != sat.answered[differed]["answer"])),
    ):
        status, _ = second.post("decide", decision("claims", second.item("claims", name), code))
        assert status == 200
    seen = page.item("claims", differed)
    sent = decision("claims", seen, sat.answered[differed]["answer"], settles=True)
    status, held = page.post("decide", sent)
    assert status == 200
    return {
        "asked": second.asked,
        "hidden": hidden,
        "agreed": page.item("claims", agreed),
        "before": seen,
        "after": page.item("claims", differed),
        "settled": held["line"],
        "item": differed,
    }


@pytest.fixture(scope="module")
def walked(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Walked]:
    data = tmp_path_factory.mktemp("walk") / "desk-synthetic"
    fill.fill(cli.FIXTURE, data, synthetic=True)
    log: list[str] = []
    running = Running(data, log)
    patch = pytest.MonkeyPatch()
    # The strongest call to the disk is slow, and a test of the records holds it to account.
    patch.setattr(records, "_sync", no_sync)
    try:
        page = Page(running.start())
        files = {name: page.ask("GET", name)[1:] for name in LOADED}
        first = page.open()
        tokens = {page.token}
        sat = {queue: sit(running, page, queue, tokens) for queue in QUEUES}
        dispute = differ_and_settle(running, page, sat["claims"])
        running.stop()
        built = make.run(data, None, cli.QUESTIONS).built
        again = make.run(data, None, cli.QUESTIONS).built
        yield Walked(
            data, first, files, sat, page.layers, log, page.asked, tokens, dispute, built, again
        )
    finally:
        running.stop()
        patch.undo()


def table(data: Path, *where: str) -> list[dict[str, str]]:
    path = out_of(data, where[1]) if where[0] == "out" else data.joinpath(*where)
    return list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"), newline="")))


def rows(data: Path, name: str) -> list[dict[str, Any]]:
    text = out_of(data, name).read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines()]


# The parts fit


def test_every_file_the_page_loads_is_served(walked: Walked):
    page = cli.PAGE
    named = set(re.findall(r'(?:href|src)="(/page/[^"]+)"', (page / "index.html").read_text()))
    for module in ("desk.mjs", "logic.mjs", "map.mjs"):
        found = re.findall(r"from '\./([a-z]+\.mjs)'", (page / module).read_text())
        named |= {f"/page/{name}" for name in found}
    assert named == set(walked.files) - {"/"}, "the walk loads what the page loads"
    for name, (headers, raw) in walked.files.items():
        kind = "text/html" if name == "/" else "text/css" if name.endswith(".css") else "text/java"
        assert headers["content-type"].startswith(kind), name
        assert "connect-src 'self'" in headers["content-security-policy"], name
        assert raw == (page / (name.removeprefix("/page/").strip("/") or "index.html")).read_bytes()


def test_the_page_opens_on_the_list_of_queues_the_first_time(walked: Walked):
    assert walked.first["resume"] is None
    assert [row["queue"] for row in walked.first["queues"]] == list(QUEUES)
    assert walked.first["banner"] == "MADE-UP CITY. Nothing here is a real place."
    assert (walked.first["reviewer"], walked.first["broken_lines"]) == ("r1", 0)


def test_the_head_of_the_design_says_how_to_sit_down_at_the_draft_of_london():
    design = (cli.ROOT / "docs" / "design" / "desk.md").read_text(encoding="utf-8")
    head = design.split("\nStatus:")[0]
    parts = head.split("**To sit down at the draft of London.**")
    assert len(parts) == 2, "it is said once, before the status"
    lines = [line for line in parts[1].splitlines() if line.strip()]
    assert [line.split(". ")[0] for line in lines[1:]] == [str(n) for n in range(1, 11)]
    assert len(lines) == 11, "a line that says what it is, and ten lines"
    said = "\n".join(lines)
    # What is typed, in the order it is typed.
    typed = (
        "uv run python -m burro_pipeline.areas.draft_run --out data/raw/areas-draft`",
        "`make desk-take DRAFT=data/raw/areas-draft`",
        "`make desk KEEP=FOLDER`",
        '`make desk-compile ARGS="--data data/raw/desk"`',
        "--decided data/raw/desk/out/names.csv --ids data/raw/areas-draft/made/names/ids.csv",
        "`make desk-take DRAFT=data/raw/areas-draft-2`",
    )
    places = [said.find(each) for each in typed]
    assert all(at >= 0 for at in places) and places == sorted(places), places
    # What is seen, what is done first, and what is not done yet.
    assert f'"{server.BANNER[False]}"' in said
    assert f"`Open http://127.0.0.1:{server.PORT}/`" in said
    asked = json.loads(cli.QUESTIONS.read_text(encoding="utf-8"))["queues"]
    title = {queue["id"]: queue["title"] for queue in asked}
    filled = ("rules", "know", "names", "borders", "whole")
    assert ", ".join(title[queue] for queue in filled) in said
    assert f"Press `1` for {title['rules']}" in said
    assert f"**Not yet: {title['borders']} and {title['whole']}.**" in said
    # The folder of fetched files is on one machine, and a tracked file names no such place.
    assert "BURRO_STORE_FOLDER=FOLDER" in said
    assert "the folder that holds the fetched files" in said
    for folder in ("Users", "home", "private", "tmp", "var"):
        assert f"/{folder}/" not in said, folder
    for place in ("~/", "$HOME", "C:\\"):
        assert place not in said, place


def test_the_head_of_the_design_says_what_a_person_types_and_sees(walked: Walked):
    design = (cli.ROOT / "docs" / "design" / "desk.md").read_text(encoding="utf-8")
    head = design.split("\nStatus:")[0].splitlines()[2:7]
    assert [line[:3] for line in head] == ["1. ", "2. ", "3. ", "4. ", "5. "], "five lines"
    said = "\n".join(head)
    assert "type `make desk`" in said
    assert f"`Open http://127.0.0.1:{server.PORT}/`" in said
    assert f'"{server.BANNER[True]}"' in said and f'"{server.BANNER[False]}"' in said
    titles = [row["title"] for row in walked.first["queues"]]
    assert f"Press `3` for {titles[2]}" in said and f"`8`, for {titles[7]}," in said
    assert (titles[2], titles[7]) == ("Kinds of venue", "Borders")
    assert walked.sat["kinds"].question["view"] == "text"
    assert walked.sat["borders"].question["view"] == "map"
    assert f"`{cli.MADE_UP.relative_to(cli.ROOT)}/decisions/`" in said
    assert f"`{cli.REAL.relative_to(cli.ROOT)}/`" in said


def test_each_answer_holds_what_the_page_reads_of_it(walked: Walked):
    assert set(walked.first) >= STATE_READS
    for row in walked.first["queues"]:
        assert set(row) >= COUNTS_READ
    for queue, sat in walked.sat.items():
        assert set(sat.question) >= QUESTION_READS, queue
        assert set(sat.counts) >= COUNTS_READ, queue
        for entry in sat.entries:
            part = {"part"} if "covers" in sat.question else set[str]()
            read = {"id", "group", "state", "flagged"} | part
            assert set(entry) == read and entry["state"] in STATES
            assert type(entry["flagged"]) is bool
        for shown in sat.shown.values():
            assert set(shown) >= ITEM_READS, queue
            assert set(shown["item"]) == records.ITEM_KEYS
            assert shown["state"] in STATES
        for line in sat.answered.values():
            assert tuple(line) == records.FIELDS, "a line comes back as it was written"
    others = walked.dispute["after"]["others"]
    assert others and all(set(other) == OTHERS_READ for other in others)


def test_every_queue_that_is_filled_is_one_the_page_can_show(walked: Walked):
    layers = may_draw()
    for queue, sat in walked.sat.items():
        asked = sat.question
        assert asked["view"] in ("map", "text"), queue
        assert set(asked["adds"]) <= {"pick", "move"} and len(asked["adds"]) <= 1, queue
        assert 1 <= len(asked["answers"]) <= 9, "each answer is one digit"
        assert all(set(each) == {"code", "label"} for each in asked["answers"])
        for shown in sat.shown.values():
            item = shown["item"]
            words = set(re.findall(r"\{([a-z_]+)\}", asked["text"]))
            assert all(item["fill"].get(word) for word in words), "the question is asked whole"
            assert set(item["flags"]) <= set(asked["flags"]), "each flag has words to be said in"
            assert len(item["picks"] or []) <= 5, "a spelling is one of the letters a to e"
            if asked["view"] == "map":
                assert set(item["map"]["layers"]) <= set(layers)
                west, south, east, north = item["map"]["bbox"]
                assert west < east and south < north
            else:
                assert item["text"] or item["lines"], "there is something to read"
            for line in item["lines"]:
                assert set(line) == {"label", "value", "source_id"}


def test_every_layer_is_one_the_page_draws(walked: Walked):
    assert len(walked.layers) == 25, "every layer that was filled was asked for"
    for key, held in walked.layers.items():
        group, layer = key.split("/")
        about = held["desk"]
        assert held["type"] == "FeatureCollection"
        assert (about["layer"], about["group"], about["synthetic"]) == (layer, group, True)
        assert about["source_ids"], "the line under the map names its sources"
        assert all(name.startswith("synthetic") for name in about["source_ids"])
        for feature in held["features"]:
            assert isinstance(feature["id"], str)
            assert set(PROPERTIES_READ[layer]) <= set(feature["properties"]), key


def test_the_page_draws_every_source_the_registry_lets_behind_a_border():
    # The page leaves out a layer whose source's id holds a word it never draws. No
    # source that is registered for the gazetteer may be caught by it, or a border of
    # London would be decided with nothing behind it.
    never = re.compile(of_the_map(r"const NEVER = /(.+)/;"))
    sources = [
        source
        for path in sorted(REGISTRY.glob("*.toml"))
        for source in tomllib.loads(path.read_text(encoding="utf-8"))["source"]
    ]
    behind = [source["id"] for source in sources if "gazetteer" in source.get("uses", [])]
    assert "ons-output-areas-2021" in behind and "os-open-roads" in behind
    assert [name for name in behind if never.search(name)] == []
    for kept_out in ("osm-geofabrik-greater-london", "protomaps-basemap-london"):
        assert kept_out in {source["id"] for source in sources} and never.search(kept_out)


def test_every_answer_says_the_city_is_made_up(walked: Walked):
    for sat in walked.sat.values():
        for shown in sat.shown.values():
            assert shown["synthetic"] is True
            assert shown["item"]["title"].endswith("(made up)")
        assert all(line["synthetic"] is True for line in sat.answered.values())


# The sitting


def test_ten_items_of_each_queue_are_answered_and_every_line_is_on_disk(walked: Walked):
    for queue, sat in walked.sat.items():
        # In a queue of fewer than ten the skipped item comes back, and is answered.
        turns = min(ITEMS_EACH, len(sat.entries) + 1)
        assert len(sat.answered) == min(turns - 1, len(sat.entries)), queue
        # One line for each turn, two more for the undo and the answer after it, and one
        # for a move.
        assert sat.lines == turns + 2 + (1 if sat.moved else 0), queue
        held = lines_of(walked.data, queue)
        assert (held.broken, held.torn) == (0, False)
        assert [line.n for line in held.lines][: sat.lines] == list(range(1, sat.lines + 1))


def test_the_page_and_the_desk_agree_on_how_each_item_stands(walked: Walked):
    for queue, sat in walked.sat.items():
        assert sat.counts["done"] == len(sat.answered), queue
        assert sat.counts["total"] == len(sat.entries)
        assert sat.counts["skipped"] == sum(e["state"] == "skipped" for e in sat.entries)
        assert sat.counts["second"] == 1, "one answer asked for a second reviewer"
        assert sat.counts["median_seconds"] == 12


def test_a_skipped_item_comes_back_after_the_rest(walked: Walked):
    for queue in ("whole", "know", "commons"):
        sat = walked.sat[queue]
        assert list(sat.answered)[-1] == sat.skipped, queue
        assert all(entry["state"] == "done" for entry in sat.entries)
    for queue in ("ratings", "kinds"):
        sat = walked.sat[queue]
        assert next(e for e in sat.entries if e["id"] == sat.skipped)["state"] == "skipped"


def test_undo_takes_back_the_last_answer_and_the_item_is_open_again(walked: Walked):
    for queue, sat in walked.sat.items():
        assert sat.undone is not None, queue
        held = lines_of(walked.data, queue).lines
        undo = next(line for line in held if line.answer == "undo")
        assert (undo.undoes, undo.item) == (sat.undone["n"], sat.undone["item"])
        assert sat.answered[undo.item]["n"] == undo.n + 1, "and it was answered again"


def test_a_desk_that_is_started_again_takes_the_answer_once(walked: Walked):
    assert len(walked.tokens) == 1 + len(QUEUES), "each run makes a token of its own"
    assert walked.log.count("POST /api/decide 403") == len(QUEUES)
    for queue, sat in walked.sat.items():
        held = lines_of(walked.data, queue).lines
        sent = [line for line in held[: sat.lines] if line.item == sat.across and line.decides]
        assert len(sent) == 1, f"{queue}: the answer sent across the stop is written once"
        standing = records.standing(held).answers
        assert set(sat.answered) <= set(standing), "and nothing answered before it was lost"


def test_a_desk_that_is_started_again_opens_where_the_person_left_off(walked: Walked):
    for queue, sat in walked.sat.items():
        at = min(5, len(sat.entries))
        shown = [*sat.shown, sat.skipped]
        assert sat.resumed == {"queue": queue, "item": shown[at]}, queue


def test_a_move_is_written_when_it_is_made_and_the_answer_after_it_needs_a_note(walked: Walked):
    for queue in ("borders", "whole"):
        sat = walked.sat[queue]
        assert sat.moved is not None and sat.refused_without_note is not None
        assert (sat.moved["n"], sat.moved["answer"], sat.moved["note"]) == (1, "move", "")
        assert sat.refused_without_note["error"] == "bad_request"
        assert sat.refused_without_note["message"] == "This answer needs a note. Say why."
        first = next(iter(sat.answered.values()))
        assert (first["item"], first["note"]) == (sat.moved["item"], NOTE)
    assert all(walked.sat[queue].moved is None for queue in QUEUES if queue[0] not in "bw")


def test_another_reviewers_answer_is_shown_only_once_your_own_stands(walked: Walked):
    found = walked.dispute
    assert found["hidden"] == []
    assert found["agreed"]["state"] == "done"
    assert [other["reviewer"] for other in found["agreed"]["others"]] == ["r2"]
    assert found["before"]["state"] == "disputed"
    assert (found["after"]["state"], found["settled"]["settles"]) == ("done", True)


def test_nothing_the_desk_prints_names_an_item_an_answer_or_a_note(walked: Walked):
    templates = "|".join(re.escape(route) for route in server.ROUTES)
    assert walked.log and all(
        re.fullmatch(rf"(GET|POST) ({templates}) \d{{3}}", line) for line in walked.log
    )
    asked = len(walked.asked) + len(walked.dispute["asked"])
    assert len(walked.log) == asked, "one line for each request, and no more"


# The build's files, made from the lines and read


def test_the_same_lines_give_the_same_files(walked: Walked):
    assert walked.built.gazetteer == walked.again.gazetteer
    assert walked.built.out == walked.again.out
    assert sorted(walked.built.out) == [
        *("articles.csv", "borders.csv", "claims_review.jsonl", "commons.csv"),
        "figures_to_check.csv",
        *("golden.jsonl", "kinds.csv", "kinds_counts.csv", "know.csv", "names.csv"),
        *("ratings.csv", "rules.csv", "to_look_at.csv", "whole.csv"),
    ]
    made_from_private = {"claims_review.jsonl", "golden.jsonl", "know.csv", "ratings.csv"}
    assert walked.built.private == {*made_from_private, "to_look_at.csv"}
    assert sorted(walked.built.gazetteer) == [
        *("aliases.csv", "areas.csv", "name_evidence.csv", "not_applied.csv", "oa_to_area.csv"),
    ]
    assert walked.built.broken == 0


def test_a_cell_that_was_moved_is_in_its_new_area_with_the_note_as_the_reason(walked: Walked):
    cells = {row["oa21cd"]: row for row in table(walked.data, "gazetteer", "oa_to_area.csv")}
    drafted = {row["oa21cd"]: row for row in table(walked.data, "draft", "oa_to_area.csv")}
    moved = walked.sat["borders"].moved
    assert moved is not None
    row = cells[moved["part"]]
    assert drafted[moved["part"]]["area_id"] == moved["detail"]["from"]
    assert (row["area_id"], row["basis"]) == (moved["detail"]["to"], "reviewed")
    assert (row["decided_by"], row["decided_on"], row["reason"]) == ("founder", "2026-10-06", NOTE)
    assert set(cells) == set(drafted), "every cell still has one row"


def test_an_area_that_was_checked_says_so_and_no_other_does(walked: Walked):
    written = table(walked.data, "gazetteer", "areas.csv")
    areas = {row["area_id"]: row["review_state"] for row in written}
    right = {
        name for name, line in walked.sat["borders"].answered.items() if line["answer"] == "right"
    }
    whole = walked.sat["whole"].answered
    assert right and all(areas[name] == "boundary_checked" for name in right)
    named = {
        name.removeprefix("n:")
        for name, line in walked.sat["names"].answered.items()
        if line["answer"] == "area" and name.startswith("n:")
    }
    assert named and all(areas[name] in ("name_checked", "boundary_checked") for name in named)
    assert any(line["answer"] == "right" for line in whole.values())
    assert "drafted" in areas.values(), "an area nobody looked at is as it was drafted"


def test_what_was_not_applied_is_listed_with_its_reason(walked: Walked):
    listed = table(walked.data, "gazetteer", "not_applied.csv")
    names = walked.sat["names"].answered
    assert {row["why"] for row in listed} <= {
        *("no_note", "disputed", "moved_to_two_areas", "item_changed", "no_area_named"),
        *("no_area_id", "no_such_area", "not_a_spelling", "area_has_cells", "area_has_names"),
    }
    assert "no_area_named" not in {row["why"] for row in listed}, "the page names the area"
    assert walked.built.applied["names"] + walked.built.set_aside["names"] == len(names)
    assert all(row["decided_by"] == "founder" for row in listed)


def test_each_claim_and_each_sentence_is_written_with_its_answer(walked: Walked):
    claims = {row["claim_id"]: row["review"] for row in rows(walked.data, "claims_review.jsonl")}
    answered = walked.sat["claims"].answered
    assert set(claims) == set(answered)
    for name, line in answered.items():
        accepted = line["answer"] == "accept"
        assert claims[name]["status"] == ("accepted" if accepted else "rejected")
        assert claims[name]["reason"] == (None if accepted else line["answer"])
        assert claims[name]["reviewer"] == "founder"
    golden = rows(walked.data, "golden.jsonl")
    sentences = walked.sat["sentences"].answered
    assert len(golden) == len(sentences)
    assert {row["code"] for row in golden} == {line["answer"] for line in sentences.values()}
    assert all(row["fit"] == (row["code"] == "fit") for row in golden)
    said = {"note", "second", "synthetic"}
    assert all(
        set(row) == {"page_id", "revision_id", "sentence", "fit", "code", *said} for row in golden
    )
    assert all(row["synthetic"] is True for row in golden)


def test_each_of_the_other_queues_is_a_table_with_a_row_for_each_answer(walked: Walked):
    for queue, name in (
        ("articles", "articles.csv"),
        ("ratings", "ratings.csv"),
        ("figures", "figures_to_check.csv"),
        ("kinds", "kinds.csv"),
        ("know", "know.csv"),
        ("commons", "commons.csv"),
    ):
        found = {row["item"]: row for row in table(walked.data, "out", name)}
        answered = walked.sat[queue].answered
        assert set(found) == set(answered), queue
        for item, line in answered.items():
            assert (found[item]["reviewer"], found[item]["answer"]) == ("r1", line["answer"])
            about = {key: value for key, value in line["detail"].items() if key != "proposed"}
            assert all(found[item][key] == str(value) for key, value in about.items())
    counts = table(walked.data, "out", "kinds_counts.csv")
    assert sum(int(row["asked"]) for row in counts) == len(walked.sat["kinds"].answered)


def test_every_note_is_in_the_file_of_its_queue_and_a_private_one_in_no_other(walked: Walked):
    noted = {
        queue
        for queue, sat in walked.sat.items()
        if any(line["note"] == NOTE for line in sat.answered.values())
    }
    assert noted == set(QUEUES), "a note was written in every queue"
    holds = {name for name, held in walked.built.out.items() if NOTE.encode() in held}
    assert holds == set(walked.built.out) - {"kinds_counts.csv"}
    for name in walked.built.private:
        assert out_of(walked.data, name).parent.name == "private", name
        assert not (walked.data / "out" / name).exists(), name
    in_gazetteer = {name for name, held in walked.built.gazetteer.items() if NOTE.encode() in held}
    assert in_gazetteer == {"oa_to_area.csv"}, "in the gazetteer, only as the reason of a move"


def test_what_was_called_wrong_or_marked_is_listed_with_its_note(walked: Walked):
    listed = table(walked.data, "out", "to_look_at.csv")
    assert {row["queue"] for row in listed} >= {"borders", "whole", "figures", "kinds"}
    by_why = Counter(row["why"] for row in listed)
    assert by_why == walked.built.look
    assert by_why["marked"] + by_why["wrong"] + by_why["not_known"] >= len(QUEUES)
    wrong = [row for row in listed if row["why"] == "wrong"]
    assert wrong and all(row["note"] == NOTE for row in wrong if row["queue"] != "figures")
    assert all(row["synthetic"] == "true" for row in listed)
