"""The page's own code, run against the desk's own server.

`test_walk.py` asks the desk as the page would, in words written by hand. This runs the
page itself: `page/test/support/at-the-desk.mjs` starts the desk on the loopback address,
hands the page a stand-in for the browser and strikes keys. Here what came on the screen
is read, and then the lines on the disk. So a change to the page, to the server or to the
step that fills the queues that the other two do not follow is caught.

It needs Node, as `make desk-check` does, and is left out where there is none. No browser
is opened, so nothing here says how the page looks.
"""

import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import pytest
from desk import cli, fill, records, server

NODE = shutil.which("node")
DRIVER = cli.PAGE / "test" / "support" / "at-the-desk.mjs"
MADE_UP = "MADE-UP CITY. Nothing here is a real place."

pytestmark = pytest.mark.skipif(NODE is None, reason="Node is not on the PATH")


@dataclass(frozen=True)
class Sat:
    data: Path
    # What came on the screen, as the driver wrote it down.
    seen: dict[str, Any]

    def lines(self, queue: str) -> tuple[records.Line, ...]:
        private = not questions()[queue]["public"]
        return records.read(records.path_of(self.data, queue, "r1", private=private)).lines

    def step(self, part: str, what: str) -> dict[str, Any]:
        return next(each for each in self.seen[part] if each["what"] == what)


@pytest.fixture(scope="module")
def sat(tmp_path_factory: pytest.TempPathFactory) -> Sat:
    data = tmp_path_factory.mktemp("page") / "desk-synthetic"
    fill.fill(cli.FIXTURE, data, synthetic=True)
    assert NODE is not None
    ran = subprocess.run(
        [NODE, str(DRIVER), sys.executable, str(cli.ROOT / "tools"), str(data)],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert ran.returncode == 0, ran.stderr[-2000:]
    return Sat(data, json.loads(ran.stdout))


def questions() -> dict[str, Any]:
    held = json.loads(cli.QUESTIONS.read_text(encoding="utf-8"))
    return {queue["id"]: queue for queue in held["queues"]}


def test_the_page_opens_on_the_list_of_queues_and_says_the_city_is_made_up(sat: Sat):
    first = sat.seen["first"]
    assert (first["list"], first["banner"]) == ("Queues", MADE_UP)
    assert first["tab"] == "Made-up city - Burro review desk"
    assert (first["item"], first["answers"], first["trouble"]) == (None, [], "")


def test_the_page_shows_the_first_item_of_every_queue_the_desk_holds(sat: Sat):
    asked = questions()
    assert list(sat.seen["queues"]) == list(asked)
    for queue, held in sat.seen["queues"].items():
        opened, items = held["opened"], records.read_items(sat.data / "items" / f"{queue}.jsonl")
        # The first borough was marked as known well, in the first queue. So where the
        # ground is decided, its items are offered first.
        well = sat.lines("know")[0].item
        known = [item for item in items.items if well in (item.group, item.id)]
        first = (known if queue in records.BY_KNOWN else items.items)[0]
        assert opened["banner"] == MADE_UP, queue
        assert opened["item"] == first.id, "in the order of the file, known boroughs first"
        assert opened["title"] == first.held["title"]
        # Ratings are counted in areas: a rater is asked about areas, not about vibes.
        parts = {item.id.rsplit(":", 1)[0] for item in items.items}
        areas = len(parts) if queue == "ratings" else 0
        counted = f"0 of {areas} areas done, " if queue == "ratings" else "0 done, "
        assert opened["progress"].startswith(f"{asked[queue]['title']}: {counted}")
        assert opened["question"] and not re.search(r"[{}]", opened["question"]), queue
        preset = cast(dict[str, Any], first.held["preset"])
        proposed = preset.get("proposed")
        # An answer that a build will set aside is marked, where the area has ground.
        aside: dict[str, Any] = asked[queue].get("set_aside", {}) if preset.get("holds") else {}
        turned_down: list[str] = aside.get("answers", [])
        waits: dict[str, str] = {code: f" ({aside['mark']})" for code in turned_down}
        labels = [
            answer["label"]
            + (
                " (proposed: Enter)"
                if answer["code"] == proposed
                else waits.get(answer["code"], "")
            )
            for answer in asked[queue]["answers"]
        ]
        labels += [asked[queue]["covers"]["label"]] if "covers" in asked[queue] else []
        assert opened["answers"] == [f"{at}{label}" for at, label in enumerate(labels, start=1)]
        assert (opened["trouble"], opened["list"]) == ("", "")


def test_the_page_draws_every_layer_the_desk_sends_it(sat: Sat):
    asked = questions()
    for queue, held in sat.seen["queues"].items():
        opened = held["opened"]
        if asked[queue]["view"] == "map":
            assert opened["shown"] == ["map-box"], queue
            assert opened["drawn"].startswith("Drawn from: synthetic"), queue
            assert opened["drawn"].endswith("No other map is behind it."), queue
            assert "is not drawn" not in opened["drawn"], "the page refused a layer"
        else:
            assert opened["shown"] in (["text-box"], ["record"]), queue
    layers = {line for line in sat.seen["asked"] if line.startswith("GET /api/layer/")}
    assert len(layers) == len(list((sat.data / "layers").glob("*/*.geojson")))


def test_one_key_on_the_page_writes_one_line_at_the_desk(sat: Sat):
    for queue, asked in questions().items():
        held = sat.seen["queues"][queue]
        line = sat.lines(queue)[0]
        # To a rule the page answers no, which changes nothing: the sitting is a person's.
        given = asked["answers"][1 if queue == "rules" else 0]
        assert (line.item, line.answer) == (held["opened"]["item"], given["code"])
        assert (line.part, line.note, line.second, line.synthetic) == ("", "", False, True)
        label = given["label"]
        # Where an area is asked about many times, the page says which question it was.
        by = asked.get("covers", {}).get("by")
        detail = cast(dict[str, Any], line.detail)
        which = "".join(f", on {value}" for key, value in detail.items() if by and key != by)
        title = held["opened"]["title"]
        waits = ""
        if detail.get("holds") and "set_aside" in asked:
            aside = asked["set_aside"]
            waits = f" {aside['cells']['saved']}" if line.answer in aside["answers"] else ""
        ruled = " Nothing was changed." if queue == "rules" else ""
        said = f"Saved: {label}{which}, for {title}.{waits}{ruled} Next: {held['after']['title']}."
        assert (held["after"]["said"], held["after"]["trouble"]) == (said, "")
        assert held["after"]["item"] not in (None, held["opened"]["item"])


def test_a_skip_a_mark_a_note_and_an_undo_are_on_the_disk_as_the_page_meant_them(sat: Sat):
    codes = [answer["code"] for answer in questions()["claims"]["answers"]]
    held = sat.lines("claims")[1:6]
    assert [line.answer for line in held] == ["skip", codes[0], codes[1], "undo", codes[2]]
    assert [line.second for line in held] == [False, True, False, False, False]
    note = "A made-up note, from the page"
    assert [line.note for line in held] == ["", "", note, "", note], "an undo gives the note back"
    assert (held[3].undoes, held[3].item, held[4].item) == (held[2].n, held[2].item, held[2].item)
    assert re.match(
        r"Skipped: .+\. It comes back after the rest\.", sat.step("claims", "skip")["said"]
    )
    label = questions()["claims"]["answers"][1]["label"]
    taken_back = sat.step("claims", "undo")
    assert taken_back["said"] == f"Taken back: {label}, for {taken_back['title']}."
    assert sat.step("claims", "undo")["item"] == held[2].item, "the item taken back is shown"
    before = records.read_items(sat.data / "items" / "claims.jsonl").items
    open_before = [item.id for item in before[: [item.id for item in before].index(held[2].item)]]
    assert set(open_before) - {line.item for line in held}, "though an item before it is open"


def test_the_page_keeps_an_answer_while_the_desk_is_down_and_sends_it_once(sat: Sat):
    down, back = sat.step("claims", "down"), sat.step("claims", "back")
    assert down["trouble"].startswith(server.WORDS[server.NOT_SAVED])
    assert down["trouble"].endswith("Do not close this page.")
    assert "Saved." not in down["said"], "it does not say Saved while it says Not saved"
    assert sat.seen["unsaved"] is True, "the browser asks before the page is closed"
    assert (back["trouble"], back["item"] != down["item"]) == ("", True)
    sent = [line for line in sat.lines("claims") if line.item == down["item"]]
    assert [line.answer for line in sent] == [questions()["claims"]["answers"][3]["code"]]
    # The page asks the desk who it is now, and only then sends the answer it kept.
    second = sat.seen["printed"].split("Stopped.\n")[1].splitlines()
    asked = [line for line in second if line.startswith(("GET", "POST"))]
    assert asked[:2] == ["GET /api/state 200", "POST /api/decide 200"]
    assert " 403" not in sat.seen["printed"]


def test_a_cell_is_moved_with_no_mouse_and_the_answer_after_it_waits_for_a_note(sat: Sat):
    taken, moved = sat.step("borders", "taken"), sat.step("borders", "moved")
    asked, answered = sat.step("borders", "asked"), sat.step("borders", "answered")
    move, answer = sat.lines("borders")[1:3]
    assert taken["said"].startswith(f"Took up cell {move.part}.")
    assert moved["said"].startswith("Moved.") and moved["moves"].startswith(f"Cell {move.part}:")
    assert (move.answer, move.item, move.detail["from"]) == ("move", taken["item"], taken["item"])
    assert move.detail["to"] != move.detail["from"]
    assert (asked["note"], asked["item"]) == (True, taken["item"])
    assert (answer.answer, answer.note) == ("right", "A made-up reason, from the page")
    # Once a cell is moved the page asks about the border as it now stands.
    borders = questions()["borders"]
    assert taken["question"] == borders["text"]
    assert moved["question"] == borders["moved"]["text"] == "With your moves, is it right now?"
    assert moved["answers"][:2] == ["1Right now", "2Still wrong"]
    assert taken["answers"][:2] == ["1Right", "2Wrong"]
    assert answered["said"].startswith(f"Saved: Right now, with a note, for {taken['title']}.")
    assert answered["item"] != taken["item"]


def test_an_area_is_named_with_no_mouse_before_a_name_is_given_to_it(sat: Sat):
    asked, own = sat.step("names", "asked"), sat.step("names", "own")
    named, answered = sat.step("names", "named"), sat.step("names", "answered")
    assert asked["said"].startswith("Say which area this is a name of.")
    assert own["said"] == "That is the area this name was proposed as. Choose another."
    assert named["of"].startswith("A name of: ")
    line = sat.lines("names")[1]
    assert (line.item, line.answer) == (asked["item"], "same_ground")
    detail = cast(dict[str, Any], line.detail)
    (area,) = detail["of"]
    assert isinstance(area, str) and area != asked["item"].removeprefix("n:")
    shown = records.read_items(sat.data / "items" / "names.jsonl").by_id[line.item]
    assert detail["pick"] in (shown.picks or ())
    assert answered["said"].startswith("Saved: ") and len(sat.lines("names")) == 2


def test_the_page_loaded_again_opens_on_an_item_that_is_not_yet_decided(sat: Sat):
    again = sat.seen["again"]
    assert (again["list"], again["banner"], again["trouble"]) == ("", MADE_UP, "")
    assert again["item"] is not None and again["answers"]
    decided = {line.item for queue in questions() for line in sat.lines(queue) if line.decides}
    assert again["item"] not in decided


def test_the_page_asks_the_desk_by_a_path_and_nothing_else(sat: Sat):
    routes = r"state|queue/[a-z]+|item/[a-z]+/[^/ ]+|layer/[a-z-]+/[a-z]+|decide|undo"
    assert len(sat.seen["asked"]) > 100
    for line in sat.seen["asked"]:
        assert re.fullmatch(rf"(GET|POST) /api/({routes})", line), "a path the desk does not know"


def test_the_desk_prints_nothing_of_what_the_page_asked_or_sent(sat: Sat):
    templates = "|".join(re.escape(route) for route in server.ROUTES)
    said = (
        r"The review desk, as r1\.|MADE-UP CITY\. Nothing here is a real place\."
        r"|Decisions are kept in .+|Open http://127\.0\.0\.1:\d+/"
        r"|The panel shows the release in [a-z/]+/syn-2026-09-23-01\."
        r"|Ctrl-C stops it\. Every decision is on disk already\.|Stopped\.|"
    )
    for line in sat.seen["printed"].splitlines():
        assert re.fullmatch(rf"(GET|POST) ({templates}) \d{{3}}|{said}", line), "a line of its own"
    # The release is named by its id, which names no place. No id of an item is printed.
    printed = sat.seen["printed"].replace("/syn-2026-09-23-01.", "")
    assert "A made-up" not in printed and "syn-" not in printed
