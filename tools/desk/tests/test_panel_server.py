"""The panel, asked through the desk's own port as its page asks it.

The queues are filled from the synthetic release, and the panel shows that release.
The server is started on a port the system picks, and stopped when a test ends. Every
name, id and reason is made up, and the only host reached is the loopback address.
"""

import http.client
import json
import shutil
import threading
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from burro_pipeline import changes
from desk import cli, fill, records, server
from desk.panel import kept, look, routes

pytestmark = pytest.mark.allow_hosts(["127.0.0.1"])

START = datetime(2026, 10, 6, 21, 14, 9, tzinfo=UTC)
RELEASE = cli.FIXTURE / "syn-2026-09-23-01"
AREA = "syn-n0004"
FIGURE = f"figure/{AREA}/air_no2"
# A reason no other test writes. If an answer or a log repeats what was sent, it shows.
CANARY = "Zzyzx Parva canary reason"


@pytest.fixture(scope="module")
def filled(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """The queues of the made-up city. Filled once: a test works on a copy."""
    data = tmp_path_factory.mktemp("panel") / "desk-synthetic"
    fill.fill(cli.FIXTURE, data, synthetic=True)
    return data


@pytest.fixture(scope="module")
def panel() -> routes.Panel:
    return routes.open_panel(RELEASE)


def no_sync(descriptor: int) -> None:
    """Stands in for the wait on the disk, which a test of the records holds to account."""


@dataclass
class Answer:
    status: int
    raw: bytes

    @property
    def held(self) -> dict[str, Any]:
        return json.loads(self.raw)


@dataclass
class Sitting:
    """One desk with its panel, on a copy of the made-up city, asked through its own port."""

    desk: server.Desk
    running: server.Server
    log: list[str] = field(default_factory=lambda: list[str]())

    @property
    def port(self) -> int:
        return self.running.server_address[1]

    def ask(self, method: str, path: str, sent: Any = None, shown: str | None = None) -> Answer:
        link = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            headers = {"Host": f"127.0.0.1:{self.port}"}
            body = None
            if sent is not None:
                body = json.dumps(sent).encode()
                headers |= {
                    "Content-Type": "application/json",
                    "X-Desk-Token": self.desk.token if shown is None else shown,
                }
            link.request(method, path, body=body, headers=headers)
            got = link.getresponse()
            return Answer(got.status, got.read())
        finally:
            link.close()

    def get(self, path: str) -> Answer:
        return self.ask("GET", path)

    def post(self, path: str, sent: Any, **more: Any) -> Answer:
        return self.ask("POST", path, sent, **more)

    def flag(self, of: str = FIGURE, why: str = "It looks too low.", **more: Any) -> Answer:
        return self.post("/api/panel/flag", {"of": of, "why": why, "leave_out": False, **more})

    def file(self, reviewer: str = "r1") -> Path:
        return kept.path_of(self.desk.data, reviewer)


Opener = Any


@pytest.fixture
def opener(
    filled: Path, panel: routes.Panel, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[Opener]:
    monkeypatch.setattr(records, "_sync", no_sync)
    data = tmp_path / "desk-synthetic"
    shutil.copytree(filled, data)
    held: list[server.Server] = []

    def start(reviewer: str = "r1", keep: Path | None = None, with_panel: bool = True) -> Sitting:
        log: list[str] = []
        desk = server.open_desk(
            data,
            cli.PAGE,
            cli.QUESTIONS,
            reviewer,
            clock=lambda: START,
            log=log.append,
            keep=keep,
            panel=panel if with_panel else None,
        )
        running = server.serve(desk, 0)
        held.append(running)
        threading.Thread(target=running.serve_forever, args=(0.01,), daemon=True).start()
        return Sitting(desk, running, log)

    yield start
    for running in held:
        running.shutdown()
        running.server_close()


@pytest.fixture
def sitting(opener: Opener) -> Sitting:
    return opener()


# Where it listens, and what it opens


def test_the_panel_is_served_on_the_loopback_address_alone(sitting: Sitting):
    assert server.LOOPBACK == "127.0.0.1"
    assert sitting.running.socket.getsockname()[0] == "127.0.0.1"
    assert sitting.running.server_address[0] == "127.0.0.1"


def test_the_address_of_the_desk_opens_the_panel_and_the_queues_are_a_page_of_their_own(
    sitting: Sitting, opener: Opener
):
    first = sitting.get("/")
    assert first.status == 200 and b"<title>The panel" in first.raw
    queues = sitting.get("/page/index.html")
    assert queues.status == 200 and b"Burro review desk" in queues.raw
    # With no panel the address opens the queues, as it did.
    assert b"Burro review desk" in opener(with_panel=False).get("/").raw


def test_a_desk_with_no_panel_says_what_the_panel_needs(opener: Opener):
    answer = opener(with_panel=False).get("/api/panel/home")
    assert answer.status == 404
    assert answer.held == {
        "error": "not_found",
        "message": server.NO_PANEL,
        "synthetic": True,
    }


# What it answers


def test_the_first_screen_says_what_is_served_what_waits_and_what_was_changed(sitting: Sitting):
    home = sitting.get("/api/panel/home").held
    assert home["banner"] == "MADE-UP CITY. Nothing here is a real place."
    assert home["served"]["release_id"] == "syn-2026-09-23-01"
    assert home["served"]["areas"] == 24
    assert {row["queue"] for row in home["waiting"]} >= {"names", "borders"}
    assert all(row["left"] == row["total"] for row in home["waiting"])
    assert home["changed"] == [] and home["flagged"] == 0


def test_every_answer_of_the_panel_says_whether_the_city_is_made_up(sitting: Sitting):
    asked = [
        *(f"/api/panel/{name}" for name in server.PANEL_READS),
        f"/api/panel/area/{AREA}",
        "/api/panel/measure/air_no2",
        "/api/panel/vibe/leafy",
        "/api/panel/area/syn-n9999",
        "/api/panel/nothing",
    ]
    for path in asked:
        assert sitting.get(path).held["synthetic"] is True, path
    assert sitting.flag(why="").held["synthetic"] is True


def test_an_area_a_measure_and_a_vibe_are_answered_by_their_ids(
    sitting: Sitting, panel: routes.Panel
):
    area = sitting.get(f"/api/panel/area/{AREA}").held
    assert area["area"]["name"] == "Dulcimer Green"
    assert area["figures"] == json.loads(json.dumps(look.area(panel.held, AREA)))["figures"]
    assert sitting.get("/api/panel/measure/air_no2").held["spread"]["areas"] == 24
    assert sitting.get("/api/panel/vibe/leafy").held["vibe"]["label"] == "Leafy"
    assert len(sitting.get("/api/panel/areas").held["areas"]) == 24
    assert AREA in sitting.get("/api/panel/outlines").held["outlines"]


@pytest.mark.parametrize(
    "path",
    [
        "/api/panel/area/syn-n9999",
        "/api/panel/area/..%2Fmanifest.json",
        "/api/panel/area/",
        "/api/panel/measure/cuisine_variety",
        "/api/panel/vibe/works_warehouses",
        "/api/panel/census/syn-n0004",
        "/api/panel/income",
        "/api/panel/area/syn-n0004/figures",
    ],
)
def test_a_word_that_is_no_key_finds_nothing(sitting: Sitting, path: str):
    answer = sitting.get(path)
    assert answer.status == 404 and answer.held["error"] == "not_found"


def test_what_the_panel_prints_holds_no_area_and_no_reason(sitting: Sitting):
    sitting.get(f"/api/panel/area/{AREA}")
    sitting.flag(why=CANARY)
    sitting.flag(of="figure/syn-n9999/air_no2", why=CANARY)
    printed = "\n".join(sitting.log)
    assert "GET /api/panel/area/{id} 200" in sitting.log
    assert "POST /api/panel/flag 200" in sitting.log
    assert AREA not in printed and "Zzyzx" not in printed and "air_no2" not in printed


# To flag


def test_a_flag_is_a_line_with_who_when_and_why(sitting: Sitting):
    answer = sitting.flag(why="It looks too low beside the areas round it.")
    assert answer.status == 200
    assert answer.held["line"] == {
        "n": 1,
        "on": "2026-10-06",
        "by": "r1",
        "what": "flag",
        "of": FIGURE,
        "was": None,
        "now": None,
        "why": "It looks too low beside the areas round it.",
        "takes_back": None,
    }
    written = sitting.file().read_bytes()
    assert changes.read(written)[0].why == "It looks too low beside the areas round it."
    # The file says the day and never the hour, and the reviewer by a label.
    assert b"21:14" not in written and b"T21" not in written


def test_a_flag_is_in_the_kept_copy_before_the_panel_answers(opener: Opener, tmp_path: Path):
    keep = tmp_path / "kept"
    keep.mkdir()
    sitting = opener(keep=keep)
    assert sitting.flag().status == 200
    copy = keep / "decisions" / "changes" / "r1.jsonl"
    assert copy.read_bytes() == sitting.file().read_bytes() != b""


def test_a_flag_given_twice_is_written_once(sitting: Sitting):
    assert sitting.flag().status == sitting.flag().status == 200
    assert sitting.file().read_bytes().count(b"\n") == 1


def test_the_list_of_what_is_flagged_is_one_page(sitting: Sitting, opener: Opener):
    sitting.flag(of=FIGURE, why="Too low.")
    sitting.flag(of=f"band/{AREA}/leafy", why="It is not leafy.")
    sitting.flag(of=f"name/{AREA}", why="Nobody calls it that.")
    sitting.flag(of=f"border/{AREA}", why="It runs over the river.")
    opener(reviewer="r2").flag(of=f"figure/{AREA}/buy.flat", why="Too dear.")
    listed = sitting.get("/api/panel/flags").held["flags"]
    assert [(one["by"], one["kind"], one["about"]) for one in listed] == [
        ("r1", "border", ""),
        ("r1", "name", ""),
        ("r1", "band", "Leafy"),
        ("r1", "figure", "Modelled annual mean nitrogen dioxide"),
        ("r2", "figure", "buy.flat"),
    ]
    assert all(one["area"]["name"] == "Dulcimer Green" for one in listed)
    # What is flagged is said where it is shown.
    shown = sitting.get(f"/api/panel/area/{AREA}").held["flags"]
    assert len(shown) == 5
    assert [one["of"] for one in sitting.get("/api/panel/vibe/leafy").held["flags"]] == [
        f"band/{AREA}/leafy"
    ]
    assert sitting.get("/api/panel/home").held["flagged"] == 5


def test_no_figure_is_left_out_of_a_build_yet_so_nothing_is_kept_that_a_build_would_stop_at(
    sitting: Sitting,
):
    answer = sitting.flag(why="The publisher says the monitor was moved.", leave_out=True)
    assert (answer.status, answer.held["message"]) == (400, routes.NOT_YET_LEFT_OUT)
    assert sitting.flag(of=f"band/{AREA}/leafy", leave_out=True).status == 400
    assert not (sitting.desk.data / "decisions" / "changes").exists()


@pytest.mark.parametrize(
    "sent",
    [
        {"of": FIGURE, "why": "", "leave_out": False},
        {"of": FIGURE, "why": "   ", "leave_out": False},
        {"of": FIGURE, "why": "x" * 501, "leave_out": False},
        {"of": FIGURE, "why": "two\nlines", "leave_out": False},
        {"of": FIGURE, "why": CANARY},
        {"of": FIGURE, "why": CANARY, "leave_out": "no"},
        {"of": "figure/syn-n9999/air_no2", "why": CANARY, "leave_out": False},
        {"of": f"figure/{AREA}/cuisine_variety", "why": CANARY, "leave_out": False},
        {"of": f"band/{AREA}/works_warehouses", "why": CANARY, "leave_out": False},
        {"of": f"census/{AREA}/religion", "why": CANARY, "leave_out": False},
        {"of": f"../{AREA}", "why": CANARY, "leave_out": False},
        {"of": 7, "why": CANARY, "leave_out": False},
        [FIGURE],
    ],
)
def test_a_flag_that_is_not_one_is_refused_in_fixed_words_and_nothing_is_written(
    sitting: Sitting, sent: Any
):
    answer = sitting.post("/api/panel/flag", sent)
    assert answer.status == 400 and answer.held["error"] == "bad_request"
    assert b"Zzyzx" not in answer.raw
    assert not (sitting.desk.data / "decisions" / "changes").exists()


@pytest.mark.parametrize("more", [{"now": 41.5}, {"was": 19.7}, {"value": 41.5}])
def test_no_route_takes_a_figure(sitting: Sitting, more: dict[str, Any]):
    # A figure is a publisher's. A person may flag one, and never give one.
    assert sitting.flag(**more).status == 400
    assert not sitting.file().exists()


def test_to_write_takes_the_token_the_desk_gave(sitting: Sitting):
    sent = {"of": FIGURE, "why": "Too low.", "leave_out": False}
    assert sitting.post("/api/panel/flag", sent, shown="not-the-token").status == 403
    assert sitting.ask("GET", "/api/panel/flag").status == 405
    assert sitting.ask("POST", "/api/panel/home", {}).status == 405
    assert not sitting.file().exists()


# The history, and taking a line back


def test_every_line_is_in_the_history_newest_first(sitting: Sitting):
    sitting.flag(why="Too low.")
    sitting.flag(of=f"name/{AREA}", why="Nobody calls it that.")
    history = sitting.get("/api/panel/history").held["history"]
    assert [(one["n"], one["by"], one["on"], one["why"]) for one in history] == [
        (2, "r1", "2026-10-06", "Nobody calls it that."),
        (1, "r1", "2026-10-06", "Too low."),
    ]
    assert all(one["stands"] and one["taken_back_by"] is None for one in history)


def test_any_line_can_be_taken_back_which_is_itself_a_line(sitting: Sitting):
    sitting.flag(why="Too low.")
    sitting.flag(of=f"name/{AREA}", why="Nobody calls it that.")
    answer = sitting.post("/api/panel/take-back", {"n": 1, "why": "I read the wrong row."})
    assert answer.status == 200
    assert answer.held["line"] == {
        "n": 3,
        "on": "2026-10-06",
        "by": "r1",
        "what": "take_back",
        "of": FIGURE,
        "was": None,
        "now": None,
        "why": "I read the wrong row.",
        "takes_back": 1,
    }
    history = {one["n"]: one for one in answer.held["history"]}
    assert (history[1]["stands"], history[1]["taken_back_by"]) == (False, 3)
    assert history[2]["stands"] and not history[3]["stands"]
    assert [one["of"] for one in sitting.get("/api/panel/flags").held["flags"]] == [f"name/{AREA}"]
    # Nothing was changed and nothing was removed: the file holds all three lines.
    assert [line.n for line in changes.read(sitting.file().read_bytes())] == [1, 2, 3]


def test_to_take_a_taking_back_back_puts_the_line_in_place_again(sitting: Sitting):
    sitting.flag(why="Too low.")
    sitting.post("/api/panel/take-back", {"n": 1, "why": "I read the wrong row."})
    again = sitting.post("/api/panel/take-back", {"n": 2, "why": "It was the right row."})
    assert again.status == 200
    assert [one["of"] for one in sitting.get("/api/panel/flags").held["flags"]] == [FIGURE]


@pytest.mark.parametrize(
    "sent",
    [
        {"n": 9, "why": "No such line."},
        {"n": 0, "why": "No such line."},
        {"n": "1", "why": "Not a number."},
        {"n": 1, "why": ""},
        {"n": 1},
    ],
)
def test_a_taking_back_that_names_no_line_of_the_reviewers_is_refused(sitting: Sitting, sent: Any):
    sitting.flag(why="Too low.")
    assert sitting.post("/api/panel/take-back", sent).status == 400
    assert sitting.file().read_bytes().count(b"\n") == 1


def test_a_line_is_taken_back_once(sitting: Sitting):
    sitting.flag(why="Too low.")
    assert sitting.post("/api/panel/take-back", {"n": 1, "why": "No."}).status == 200
    assert sitting.post("/api/panel/take-back", {"n": 1, "why": "No."}).status == 400


def test_a_reviewer_takes_back_no_line_of_anothers(sitting: Sitting, opener: Opener):
    sitting.flag(why="Too low.")
    second = opener(reviewer="r2")
    assert second.post("/api/panel/take-back", {"n": 1, "why": "Not mine."}).status == 400
    assert not second.file("r2").exists()


def test_a_file_of_changes_that_cannot_be_read_stops_the_panel_and_is_left_as_it_is(
    sitting: Sitting,
):
    sitting.flag(why="Too low.")
    broken = sitting.file().read_bytes() + b'{"n": 2, "by": "nobody"}\n'
    sitting.file().write_bytes(broken)
    answer = sitting.flag(of=f"name/{AREA}", why=CANARY)
    assert (answer.status, answer.held["error"]) == (500, "not_saved")
    assert sitting.get("/api/panel/history").status == 500
    assert sitting.file().read_bytes() == broken
    assert any("line 2" in line and "Zzyzx" not in line for line in sitting.log)


# The two cities


def test_no_queue_is_named_for_the_files_of_changes():
    asked = records.read_questions(cli.QUESTIONS)
    assert server.CHANGES not in asked and kept.FOLDER == server.CHANGES
