"""A rule the founder adopts, from the desk's own port to the files of a build.

The queues are filled from the synthetic release, which puts five made-up rules. The
server is started on a port the system picks, and asked as the page asks it. Every name
and every rule is made up, and the only host reached is the loopback address.
"""

import csv
import http.client
import io
import json
import shutil
import threading
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import quote

import pytest
from desk import cli, fill, publish, records, server
from desk import compile as make

pytestmark = pytest.mark.allow_hosts(["127.0.0.1"])

START = datetime(2026, 10, 6, 21, 14, 9, tzinfo=UTC)
ACCEPTS, SMALLER, DROPS, LEAVES = (
    "two_made_up_publishers_write_it",
    "a_made_up_smaller_place",
    "named_for_a_made_up_building",
    "every_made_up_border",
)


@pytest.fixture(scope="module")
def filled(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """The queues of the made-up city. Filled once: a test works on a copy."""
    data = tmp_path_factory.mktemp("rules") / "desk-synthetic"
    fill.fill(cli.FIXTURE, data, synthetic=True)
    return data


def no_sync(descriptor: int) -> None:
    """Stands in for the wait on the disk, which a test of the records holds to account."""


@dataclass
class Desk:
    """One desk on a copy of the made-up city, asked through its own port."""

    data: Path
    keep: Path | None = None
    ticks: int = 0
    held: list[server.Server] = field(default_factory=lambda: list[server.Server]())
    ports: dict[str, int] = field(default_factory=lambda: dict[str, int]())
    tokens: dict[str, str] = field(default_factory=lambda: dict[str, str]())

    def clock(self) -> datetime:
        self.ticks += 1
        return START + timedelta(seconds=7 * self.ticks)

    def start(self, reviewer: str = "r1") -> "Desk":
        desk = server.open_desk(
            self.data,
            cli.PAGE,
            cli.QUESTIONS,
            reviewer,
            clock=self.clock,
            log=lambda _: None,
            keep=self.keep,
        )
        held = server.serve(desk, 0)
        threading.Thread(target=held.serve_forever, args=(0.01,), daemon=True).start()
        self.held.append(held)
        self.ports[reviewer] = held.server_address[1]
        self.tokens[reviewer] = desk.token
        return self

    def stop(self) -> None:
        while self.held:
            held = self.held.pop()
            held.shutdown()
            held.server_close()

    def ask(
        self, method: str, path: str, sent: Any = None, reviewer: str = "r1"
    ) -> tuple[int, dict[str, Any]]:
        headers = {"Accept": "application/json"}
        body = None
        if sent is not None:
            body = json.dumps(sent).encode()
            headers |= {"Content-Type": "application/json", "X-Desk-Token": self.tokens[reviewer]}
        link = http.client.HTTPConnection("127.0.0.1", self.ports[reviewer], timeout=5)
        try:
            link.request(method, path, body, headers)
            got = link.getresponse()
            return got.status, json.loads(got.read())
        finally:
            link.close()

    def get(self, *words: str, reviewer: str = "r1") -> dict[str, Any]:
        path = "/api/" + "/".join(quote(word, safe="-_.!~*'():") for word in words)
        status, held = self.ask("GET", path, reviewer=reviewer)
        assert status == 200, held
        return held

    def decide(
        self, queue: str, item: str, answer: str, note: str = ""
    ) -> tuple[int, dict[str, Any]]:
        """Decide as the page does: with what the item holds, and the line it shows."""
        shown = self.get("item", queue, item)
        sent: dict[str, Any] = {
            "queue": queue,
            "item": item,
            "rev": shown["item"]["rev"],
            "part": "",
            "answer": answer,
            "note": note,
            "second": False,
            "settles": False,
            "detail": {} if answer == "skip" else shown["item"]["preset"],
            "seconds": 9,
            "stands": None if shown["mine"] is None else shown["mine"]["n"],
        }
        return self.ask("POST", "/api/decide", sent)

    def undo(self, queue: str) -> dict[str, Any]:
        status, held = self.ask("POST", "/api/undo", {"queue": queue})
        assert status == 200, held
        return held

    def lines(self, queue: str, reviewer: str = "r1") -> tuple[records.Line, ...]:
        return records.read(records.path_of(self.data, queue, reviewer)).lines

    def stands(self, queue: str) -> records.Standing:
        return records.standing(self.lines(queue))

    def states(self, queue: str) -> dict[str, str]:
        return {each["id"]: each["state"] for each in self.get("queue", queue)["items"]}

    def counts(self, queue: str) -> dict[str, Any]:
        return next(row for row in self.get("state")["queues"] if row["queue"] == queue)

    def fits(self, rule: str) -> list[str]:
        """The items a rule fits, in the order of their queue."""
        queue = self.get("item", "rules", rule)["item"]["preset"]["queue"]
        return [
            item.id
            for item in records.read_items(self.data / "items" / f"{queue}.jsonl").items
            if isinstance(item.held["preset"], dict) and item.held["preset"].get("fits") == rule
        ]


@pytest.fixture
def desk(filled: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Desk]:
    monkeypatch.setattr(records, "_sync", no_sync)
    data = tmp_path / "desk-synthetic"
    shutil.copytree(filled, data)
    held = Desk(data).start()
    yield held
    held.stop()


def table(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"), newline="")))


# Yes, no, and taking either back


def test_the_rules_are_offered_first_and_none_is_adopted_until_the_founder_says_yes(desk: Desk):
    state = desk.get("state")
    assert next(row["queue"] for row in state["queues"]) == "rules"
    assert desk.counts("rules")["total"] == 5
    assert {row["queue"]: row["by_rule"] for row in state["queues"]} == {
        row["queue"]: 0 for row in state["queues"]
    }
    assert set(desk.states("names").values()) == {"open"}
    assert not desk.lines("names") and not desk.lines("borders")
    waits = {row["queue"]: [each["queue"] for each in row["waits"]] for row in state["queues"]}
    assert waits["names"] == ["rules"] and waits["borders"] == ["rules", "names"]


def test_yes_settles_every_item_the_rule_fits_and_names_the_rule_in_every_line(desk: Desk):
    fits = desk.fits(ACCEPTS)
    status, held = desk.decide("rules", ACCEPTS, "yes")
    assert status == 200
    assert held["ruled"] == {"settled": len(fits), "taken_back": 0} and len(fits) == 17
    assert held["line"]["answer"] == "yes"
    written = desk.lines("names")
    assert [line.item for line in written] == fits
    for line in written:
        assert (line.answer, line.detail["rule"], line.reviewer) == ("area", ACCEPTS, "r1")
        assert (line.note, line.second, line.seconds, line.synthetic) == ("", False, 0, True)
        assert records.by_rule(line) == ACCEPTS
    states = desk.states("names")
    assert {states[name] for name in fits} == {"done"}
    assert Counter(states.values()) == {"done": 17, "open": 20}
    counts = desk.counts("names")
    assert (counts["done"], counts["by_rule"], counts["median_seconds"]) == (17, 17, None)
    assert desk.counts("rules")["done"] == 1


def test_a_line_a_rule_writes_holds_what_the_item_holds_and_the_rule(desk: Desk):
    desk.decide("rules", SMALLER, "yes")
    for line in desk.lines("names"):
        item = desk.get("item", "names", line.item)
        assert line.detail == {**item["item"]["preset"], "rule": SMALLER}
        assert (line.answer, line.rev) == ("inside", item["item"]["rev"])
        assert item["state"] == "done" and item["mine"]["detail"]["rule"] == SMALLER


def test_no_changes_nothing(desk: Desk):
    status, held = desk.decide("rules", ACCEPTS, "no")
    assert (status, held["ruled"]) == (200, {"settled": 0, "taken_back": 0})
    assert not desk.lines("names")
    assert set(desk.states("names").values()) == {"open"}
    assert (desk.counts("rules")["done"], desk.counts("names")["by_rule"]) == (1, 0)


def test_undo_takes_back_the_yes_and_every_line_it_wrote(desk: Desk):
    fits = desk.fits(ACCEPTS)
    desk.decide("rules", ACCEPTS, "yes")
    back = desk.undo("rules")
    assert back["undone"]["answer"] == "yes"
    assert back["ruled"] == {"settled": 0, "taken_back": len(fits)}
    assert set(desk.states("names").values()) == {"open"}
    assert desk.states("rules")[ACCEPTS] == "open"
    # Nothing is removed: each line is taken back by a line of its own.
    assert Counter(line.answer for line in desk.lines("names")) == {"area": 17, "undo": 17}
    assert not desk.stands("names").answers
    assert desk.counts("names")["by_rule"] == 0


def test_a_yes_that_is_changed_to_no_takes_back_what_the_yes_settled(desk: Desk):
    desk.decide("rules", DROPS, "yes")
    assert desk.counts("names")["by_rule"] == len(desk.fits(DROPS)) > 0
    status, held = desk.decide("rules", DROPS, "no")
    assert (status, held["ruled"]) == (200, {"settled": 0, "taken_back": len(desk.fits(DROPS))})
    assert set(desk.states("names").values()) == {"open"}
    status, held = desk.decide("rules", DROPS, "yes")
    assert held["ruled"] == {"settled": len(desk.fits(DROPS)), "taken_back": 0}


def test_a_yes_given_twice_settles_once(desk: Desk):
    desk.decide("rules", ACCEPTS, "yes")
    before = desk.lines("names")
    shown = desk.get("item", "rules", ACCEPTS)
    sent = {
        **{"queue": "rules", "item": ACCEPTS, "rev": shown["item"]["rev"], "part": ""},
        **{"answer": "yes", "note": "", "second": False, "settles": False},
        **{"detail": shown["item"]["preset"], "seconds": 9, "stands": None},
    }
    status, held = desk.ask("POST", "/api/decide", sent)
    assert (status, held["ruled"]) == (200, {"settled": 0, "taken_back": 0})
    assert desk.lines("names") == before


def test_a_rule_whose_list_has_changed_is_open_again_and_what_it_settled_stands(
    desk: Desk, tmp_path: Path
):
    # The queues are filled again from a draft that gives the rule one item fewer. The
    # yes was given to another list, so the rule is asked again. Until it is answered,
    # nothing it settled is taken back, whatever else the founder answers.
    desk.decide("rules", ACCEPTS, "yes")
    desk.stop()
    path = desk.data / "items" / "rules.jsonl"
    rows = [json.loads(row) for row in path.read_text(encoding="utf-8").splitlines()]
    for row in rows[1:]:
        if row["id"] == ACCEPTS:
            row["preset"]["settles"] = "0" * 12
            row["rev"] = "f" * 12
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    desk.start()
    assert desk.states("rules")[ACCEPTS] == "stale"
    assert desk.counts("names")["by_rule"] == 17
    _, held = desk.decide("rules", SMALLER, "no")
    assert held["ruled"] == {"settled": 0, "taken_back": 0}
    assert desk.counts("names")["by_rule"] == 17
    # Asked again, the founder says no: what the rule settled is taken back.
    _, held = desk.decide("rules", ACCEPTS, "no")
    assert held["ruled"] == {"settled": 0, "taken_back": 17}
    assert desk.counts("names")["by_rule"] == 0


def test_a_rule_that_is_taken_back_takes_back_its_answer_to_an_item_that_is_gone(desk: Desk):
    # The draft was made again without a name that a rule turned down. The founder then
    # takes the rule back: the answer is taken back too, so that the next draft may make
    # the name an area again.
    desk.decide("rules", DROPS, "yes")
    gone = next(name for name in desk.fits(DROPS) if name.startswith("n:"))
    desk.stop()
    path = desk.data / "items" / "names.jsonl"
    rows = [json.loads(row) for row in path.read_text(encoding="utf-8").splitlines()]
    kept = [row for row in rows[1:] if row["id"] != gone]
    rows[0]["count"] = len(kept)
    path.write_text("".join(json.dumps(row) + "\n" for row in (rows[0], *kept)), encoding="utf-8")
    desk.start()
    assert gone in desk.stands("names").answers
    desk.undo("rules")
    assert gone not in desk.stands("names").answers


# A rule that leans on others

LEANS = "a_made_up_flag_that_asks_nothing"


def test_a_rule_that_leans_settles_nothing_until_the_rule_its_item_leans_on_is_adopted(
    desk: Desk,
):
    """The fault this holds: a rule that lets a name through to another rule settled
    the name whether or not the founder had adopted that other rule."""
    (item,) = desk.fits(LEANS)
    status, held = desk.decide("rules", LEANS, "yes")
    assert status == 200
    assert held["ruled"] == {"settled": 0, "taken_back": 0, "held_back": 1}
    assert not desk.lines("names") and desk.states("names")[item] == "open"
    # A rule it leans on is adopted, and not the one this item leans on: it still waits.
    _, held = desk.decide("rules", ACCEPTS, "yes")
    assert held["ruled"] == {"settled": len(desk.fits(ACCEPTS)), "taken_back": 0, "held_back": 1}
    assert item not in {line.item for line in desk.lines("names")}
    # The rule the item leans on is adopted: it is settled, and its line names both.
    _, held = desk.decide("rules", SMALLER, "yes")
    assert held["ruled"] == {"settled": len(desk.fits(SMALLER)) + 1, "taken_back": 0}
    line = desk.stands("names").answers[item]
    assert (line.answer, line.detail["rule"], line.detail["leans_on"]) == ("inside", LEANS, SMALLER)
    assert records.by_rule(line) == LEANS and desk.states("names")[item] == "done"


def test_the_order_in_which_the_two_rules_are_adopted_changes_nothing(desk: Desk):
    (item,) = desk.fits(LEANS)
    desk.decide("rules", SMALLER, "yes")
    assert item not in desk.stands("names").answers
    _, held = desk.decide("rules", LEANS, "yes")
    assert held["ruled"] == {"settled": 1, "taken_back": 0}
    assert records.by_rule(desk.stands("names").answers[item]) == LEANS


def test_what_a_rule_settled_by_leaning_is_taken_back_with_the_rule_it_leant_on(desk: Desk):
    (item,) = desk.fits(LEANS)
    desk.decide("rules", LEANS, "yes")
    desk.decide("rules", SMALLER, "yes")
    assert item in desk.stands("names").answers
    _, held = desk.decide("rules", SMALLER, "no")
    assert held["ruled"] == {
        "settled": 0,
        "taken_back": len(desk.fits(SMALLER)) + 1,
        "held_back": 1,
    }
    assert not desk.stands("names").answers and desk.states("names")[item] == "open"
    # The yes to the rule that leans still stands: it settles again once it may.
    assert desk.stands("rules").answers[LEANS].answer == "yes"
    _, held = desk.decide("rules", SMALLER, "yes")
    assert held["ruled"] == {"settled": len(desk.fits(SMALLER)) + 1, "taken_back": 0}


def test_the_founders_own_answer_stands_whatever_the_rules_that_lean_do(desk: Desk):
    (item,) = desk.fits(LEANS)
    assert desk.decide("names", item, "drop")[0] == 200
    desk.decide("rules", LEANS, "yes")
    _, held = desk.decide("rules", SMALLER, "yes")
    assert held["ruled"] == {"settled": len(desk.fits(SMALLER)), "taken_back": 0}
    line = desk.stands("names").answers[item]
    assert (line.answer, records.by_rule(line)) == ("drop", "")


def test_a_rule_that_leans_says_on_its_item_how_each_rule_it_leans_on_stands(desk: Desk):
    def leans() -> list[dict[str, Any]]:
        return desk.get("item", "rules", LEANS)["leans"]

    assert leans() == [
        {"rule": ACCEPTS, "stands": "not_adopted", "items": 0},
        {"rule": SMALLER, "stands": "not_adopted", "items": 1},
    ]
    desk.decide("rules", SMALLER, "yes")
    assert [each["stands"] for each in leans()] == ["not_adopted", "adopted"]
    desk.undo("rules")
    assert [each["stands"] for each in leans()] == ["not_adopted", "not_adopted"]
    # A rule that stands by itself leans on none, and an item of another queue says nothing.
    assert desk.get("item", "rules", ACCEPTS)["leans"] == []
    assert "leans" not in desk.get("item", "names", desk.fits(LEANS)[0])


# A person's answer, and a rule's


def test_an_item_the_founder_answered_keeps_the_founders_answer(desk: Desk):
    first, second, *_ = desk.fits(ACCEPTS)
    desk.decide("names", first, "drop", note="A made-up reason.")
    desk.decide("names", second, "skip")
    _, held = desk.decide("rules", ACCEPTS, "yes")
    assert held["ruled"]["settled"] == len(desk.fits(ACCEPTS)) - 1
    stands = desk.stands("names").answers
    assert (stands[first].answer, records.by_rule(stands[first])) == ("drop", "")
    # A skip decides nothing, so the rule settles the item.
    assert (stands[second].answer, records.by_rule(stands[second])) == ("area", ACCEPTS)


def test_the_founder_may_answer_an_item_that_a_rule_settled(desk: Desk):
    first = desk.fits(ACCEPTS)[0]
    desk.decide("rules", ACCEPTS, "yes")
    status, held = desk.decide("names", first, "drop", note="A made-up reason.")
    assert status == 200 and held["line"]["detail"].get("rule") is None
    assert desk.counts("names")["by_rule"] == len(desk.fits(ACCEPTS)) - 1
    # Taking the founder's answer back leaves what the rule settled.
    assert desk.undo("names")["undone"]["answer"] == "drop"
    assert records.by_rule(desk.stands("names").answers[first]) == ACCEPTS


def test_when_a_rule_is_taken_back_an_answer_it_gave_under_the_founders_own_goes_too(
    desk: Desk,
):
    first = desk.fits(ACCEPTS)[0]
    desk.decide("rules", ACCEPTS, "yes")
    desk.decide("names", first, "drop", note="A made-up reason.")
    desk.undo("rules")
    assert desk.stands("names").answers[first].answer == "drop"
    desk.undo("names")
    assert first not in desk.stands("names").answers, "what the rule gave does not come back"
    assert desk.states("names")[first] == "open"


def test_undo_in_a_queue_never_takes_back_a_line_that_a_rule_wrote(desk: Desk):
    desk.decide("rules", ACCEPTS, "yes")
    assert desk.undo("names")["undone"] is None
    other = next(name for name, state in desk.states("names").items() if state == "open")
    desk.decide("names", other, "skip")
    assert desk.undo("names")["undone"]["item"] == other
    assert desk.counts("names")["by_rule"] == len(desk.fits(ACCEPTS))


def test_the_desk_opens_again_at_the_rules_and_not_at_what_a_rule_wrote(desk: Desk):
    desk.decide("rules", ACCEPTS, "yes")
    resume = desk.get("state")["resume"]
    assert resume == {"queue": "rules", "item": SMALLER}


def test_no_request_may_give_the_answer_of_a_rule_or_name_one(desk: Desk):
    border = desk.fits(LEAVES)[0]
    assert desk.decide("borders", border, "rule")[0] == 400
    shown = desk.get("item", "borders", border)["item"]
    sent = {
        **{"queue": "borders", "item": border, "rev": shown["rev"], "part": ""},
        **{"answer": "right", "note": "", "second": False, "settles": False},
        **{"detail": {**shown["preset"], "rule": LEAVES}, "seconds": 9, "stands": None},
    }
    assert desk.ask("POST", "/api/decide", sent)[0] == 400
    assert not desk.lines("borders")


def test_a_second_reviewer_is_offered_no_rule(desk: Desk):
    desk.start("r2")
    queues = [row["queue"] for row in desk.get("state", reviewer="r2")["queues"]]
    assert "rules" not in queues and "borders" in queues
    assert desk.ask("GET", "/api/queue/rules", reviewer="r2")[0] == 404


# A border left as drafted


def test_a_border_a_rule_leaves_as_drafted_is_offered_to_nobody(desk: Desk):
    fits = desk.fits(LEAVES)
    before = desk.counts("borders")
    _, held = desk.decide("rules", LEAVES, "yes")
    assert held["ruled"] == {"settled": len(fits), "taken_back": 0} and len(fits) == 16
    for line in desk.lines("borders"):
        assert (line.answer, line.detail) == ("rule", {"fits": LEAVES, "rule": LEAVES})
    after = desk.counts("borders")
    assert (after["done"], after["by_rule"]) == (16, 16)
    assert (after["flagged"], after["flagged_left"]) == (before["flagged"], before["flagged_left"])
    assert {desk.states("borders")[name] for name in fits} == {"done"}
    desk.start("r2")
    second = {
        each["id"]: each["state"] for each in desk.get("queue", "borders", reviewer="r2")["items"]
    }
    assert set(second.values()) == {"open"}, "a second reviewer may still look at each"


# The files of a build


def built(desk: Desk) -> make.Written:
    return make.run(desk.data, None, cli.QUESTIONS)


def test_a_name_a_rule_accepts_is_built_as_the_founder_adopted_it(desk: Desk):
    desk.decide("rules", ACCEPTS, "yes")
    desk.decide("rules", SMALLER, "yes")
    made = built(desk)
    fits = desk.fits(ACCEPTS)
    assert made.built.by_rule == {"names": len(fits) + len(desk.fits(SMALLER))}
    assert made.built.applied["names"] == len(fits) + len(desk.fits(SMALLER))
    rows = {row["item"]: row for row in table(desk.data / "out" / "names.csv")}
    assert {name: rows[name]["rule"] for name in fits} == {name: ACCEPTS for name in fits}
    assert {rows[name]["answer"] for name in fits} == {"area"}
    assert {rows[name]["answer"] for name in desk.fits(SMALLER)} == {"inside"}
    areas = {row["area_id"]: row for row in table(desk.data / "gazetteer" / "areas.csv")}
    assert {areas[name.removeprefix("n:")]["review_state"] for name in fits} == {"name_checked"}
    assert Counter(row["review_state"] for row in areas.values()) == {
        "name_checked": len(fits),
        "drafted": len(areas) - len(fits),
    }


def test_a_name_a_rule_drops_waits_for_a_new_draft_where_its_area_has_ground(desk: Desk):
    fits = desk.fits(DROPS)
    areas = [name for name in fits if name.startswith("n:")]
    _, held = desk.decide("rules", DROPS, "yes")
    assert held["counts"]["queue"] == "rules"
    # They are counted as the rule's. The borders wait on every one, whoever gave it.
    names = desk.counts("names")
    assert (names["by_rule"], names["set_aside"]) == (len(fits), 0) and areas
    waits = {row["queue"]: row for row in desk.counts("borders")["waits"]}
    assert waits["names"]["set_aside"] == len(areas)
    made = built(desk)
    assert made.built.waits == len(areas)
    listed = table(desk.data / "gazetteer" / "not_applied.csv")
    assert sorted(row["item"] for row in listed) == sorted(areas)
    assert {row["why"] for row in listed} == {"area_has_cells"}
    # The draft is made again from this table. It reads the answer and who gave it.
    rows = {row["item"]: row for row in table(desk.data / "out" / "names.csv")}
    assert {(rows[name]["answer"], rows[name]["reviewer"]) for name in areas} == {("drop", "r1")}
    assert {rows[name]["rule"] for name in fits} == {DROPS}


def test_a_border_left_as_drafted_is_never_said_to_be_checked(desk: Desk):
    desk.decide("rules", LEAVES, "yes")
    made = built(desk)
    assert made.built.by_rule == {"borders": 16}
    assert (made.built.applied["borders"], made.built.flagged["borders"]) == (0, 0)
    areas = table(desk.data / "gazetteer" / "areas.csv")
    assert {row["review_state"] for row in areas} == {"drafted"}
    rows = table(desk.data / "out" / "borders.csv")
    assert {(row["answer"], row["rule"]) for row in rows} == {("rule", LEAVES)}
    looked = table(desk.data / "out" / "private" / "to_look_at.csv")
    assert not [row for row in looked if row["queue"] == "borders"]


def test_a_whole_borough_called_right_checks_a_border_that_a_rule_left_as_drafted(desk: Desk):
    desk.decide("rules", LEAVES, "yes")
    borough = next(iter(desk.states("whole")))
    desk.decide("whole", borough, "right")
    areas = table(built(desk).gazetteer / "areas.csv")  # type: ignore[operator]
    held = {row["area_id"]: row for row in areas}
    inside = [name for name in desk.fits(LEAVES) if slug(held[name]["primary_borough"]) == borough]
    assert inside and {held[name]["review_state"] for name in inside} == {"boundary_checked"}


def slug(name: str) -> str:
    return make.slug(name)


def test_the_step_that_makes_the_files_says_how_many_a_rule_settled(
    desk: Desk, capsys: pytest.CaptureFixture[str]
):
    desk.decide("rules", ACCEPTS, "yes")
    desk.decide("rules", LEAVES, "yes")
    assert cli.main(["compile", "--data", str(desk.data)]) == cli.OK
    said = capsys.readouterr().out
    assert "Settled by a rule the founder adopted: 17 in names, 16 in borders.\n" in said


def test_the_copy_that_may_be_committed_names_the_rule_in_every_line(desk: Desk, tmp_path: Path):
    desk.decide("rules", SMALLER, "yes")
    real = tmp_path / "desk"
    shutil.copytree(desk.data, real)
    for path in sorted(real.rglob("*.jsonl")):
        text = path.read_text(encoding="utf-8").replace('"synthetic":true', '"synthetic":false')
        path.write_text(text, encoding="utf-8")
    found = publish.build(make.load(real, cli.QUESTIONS))
    names = [json.loads(row) for row in found.files["names", "r1"].splitlines()]
    assert len(names) == len(desk.fits(SMALLER))
    assert {row["detail"]["rule"] for row in names} == {SMALLER}
    rules = [json.loads(row) for row in found.files["rules", "r1"].splitlines()]
    assert [(row["item"], row["answer"]) for row in rules] == [(SMALLER, "yes")]


def test_every_line_a_rule_writes_is_in_the_kept_copy_before_the_desk_answers(
    filled: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(records, "_sync", no_sync)
    data = tmp_path / "desk-synthetic"
    shutil.copytree(filled, data)
    held = Desk(data, keep=tmp_path / "kept").start()
    try:
        held.decide("rules", ACCEPTS, "yes")
        kept = tmp_path / "kept" / "decisions" / "names" / "r1.jsonl"
        assert kept.read_bytes() == records.path_of(data, "names", "r1").read_bytes()
        held.undo("rules")
        assert kept.read_bytes() == records.path_of(data, "names", "r1").read_bytes()
    finally:
        held.stop()
