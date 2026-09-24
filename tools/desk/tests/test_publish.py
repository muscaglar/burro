"""The step that makes the copy of the decisions that may be published.

Every name, id and note here is made up. The city is called London only so that the step
takes it: no file of London is read. No socket is opened.
"""

import json
import stat
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from desk import cli, publish, records
from desk.records import Unfit, path_of

START = datetime(2026, 10, 6, 21, 14, 9, tzinfo=UTC)
CANARY = "Zzyzx Parva canary note"
REV = "9f2c41d07ab3"
QUESTIONS = json.loads(cli.QUESTIONS.read_text(encoding="utf-8"))["queues"]
PUBLIC = {queue["id"]: queue["public"] for queue in QUESTIONS}
FIRST = {queue["id"]: queue["answers"][0]["code"] for queue in QUESTIONS}


def item(name: str, **preset: Any) -> dict[str, Any]:
    return {
        "id": name,
        "rev": REV,
        "group": "made-up-borough",
        "title": "A made-up item",
        "lines": [],
        "text": None,
        "map": None,
        "picks": None,
        "flags": [],
        "fill": {},
        "preset": preset,
    }


@dataclass
class Made:
    """A desk on disk that says it is of London, with one item in every queue."""

    data: Path
    synthetic: bool = False
    at: datetime = START

    def items(self) -> "Made":
        folder = self.data / "items"
        folder.mkdir(parents=True)
        for queue in PUBLIC:
            first: dict[str, Any] = {
                "desk": 1,
                "queue": queue,
                "question": f"{queue}@1",
                "synthetic": self.synthetic,
                "made_on": "2026-09-23",
                "made_from": [],
                "count": 2,
            }
            rows = (first, item(f"x-{queue}-1"), item(f"x-{queue}-2"))
            text = "".join(json.dumps(row) + "\n" for row in rows)
            (folder / f"{queue}.jsonl").write_text(text, encoding="utf-8")
        return self

    def line(self, queue: str, at: int, answer: str, by: str = "r1", **more: Any) -> records.Line:
        self.at += timedelta(hours=7, minutes=13, seconds=5)
        held: dict[str, Any] = {"rev": REV, "synthetic": self.synthetic, "seconds": 41, **more}
        return records.append(
            path_of(self.data, queue, by, private=not PUBLIC[queue]),
            reviewer=by,
            queue=queue,
            question=f"{queue}@1",
            item=f"x-{queue}-{at}",
            answer=answer,
            clock=lambda: self.at,
            **held,
        )

    def published(self, to: Path) -> dict[str, list[dict[str, Any]]]:
        found: dict[str, list[dict[str, Any]]] = {}
        for path in sorted(each for each in to.rglob("*") if each.is_file()):
            rows = path.read_text(encoding="utf-8").splitlines()
            found[str(path.relative_to(to))] = [json.loads(row) for row in rows]
        return found


@pytest.fixture(autouse=True)
def no_wait_on_the_disk(monkeypatch: pytest.MonkeyPatch) -> None:
    def no_sync(descriptor: int) -> None:
        """Stands in for the wait on the disk."""

    monkeypatch.setattr(records, "_sync", no_sync)


@pytest.fixture
def made(tmp_path: Path) -> Made:
    return Made(tmp_path / "desk").items()


def a_line_in_every_queue(made: Made) -> None:
    for queue in PUBLIC:
        made.line(queue, 1, FIRST[queue], note=f"{CANARY} of {queue}")


def test_no_line_of_a_private_queue_is_ever_published(made: Made, tmp_path: Path):
    a_line_in_every_queue(made)
    to = tmp_path / "gazetteer" / "london"
    found = publish.run(made.data, to, cli.QUESTIONS)
    held = made.published(to)
    public = sorted(queue for queue, may in PUBLIC.items() if may)
    assert sorted(held) == [f"decisions/{queue}/r1.jsonl" for queue in public]
    assert found.queues == tuple(queue for queue in PUBLIC if PUBLIC[queue])
    everything = b"".join(path.read_bytes() for path in to.rglob("*") if path.is_file())
    for queue, may in PUBLIC.items():
        assert (f"{CANARY} of {queue}".encode() in everything) is may, queue
        assert (f"x-{queue}-1".encode() in everything) is may, queue
    assert {queue for queue, may in PUBLIC.items() if not may} == {
        *("claims", "sentences", "ratings", "know"),
    }


def test_a_published_line_says_the_day_and_never_the_hour(made: Made, tmp_path: Path):
    # A line to the second would publish the hours a person works, night by night.
    made.line("names", 1, "area", note="A made-up note.", second=True)
    made.line("names", 2, "drop")
    to = tmp_path / "out"
    publish.run(made.data, to, cli.QUESTIONS)
    first, second = made.published(to)["decisions/names/r1.jsonl"]
    assert first == {
        "n": 1,
        "at": "2026-10-07",
        "reviewer": "r1",
        "queue": "names",
        "question": "names@1",
        "item": "x-names-1",
        "rev": REV,
        "part": "",
        "answer": "area",
        "note": "A made-up note.",
        "second": True,
        "settles": False,
        "detail": {},
        "synthetic": False,
    }
    assert (second["n"], second["at"]) == (2, "2026-10-07")
    everything = b"".join(path.read_bytes() for path in to.rglob("*") if path.is_file())
    assert b"seconds" not in everything
    assert b"T04:" not in everything and b"T11:" not in everything and b"Z" not in everything


def test_only_what_stands_is_published(made: Made, tmp_path: Path):
    # A line that was taken back may hold a note written by mistake.
    taken_back = made.line("kinds", 1, "yes", note=CANARY)
    made.line("kinds", 1, "undo", undoes=taken_back.n)
    made.line("kinds", 1, "no", note="A stage school.")
    made.line("kinds", 2, "skip", note=CANARY)
    made.line("commons", 1, "in_file", rev="0" * 12, note=CANARY)
    to = tmp_path / "out"
    publish.run(made.data, to, cli.QUESTIONS)
    held = made.published(to)
    assert [(row["n"], row["answer"]) for row in held["decisions/kinds/r1.jsonl"]] == [(3, "no")]
    assert "decisions/commons/r1.jsonl" not in held, "the item has changed since"
    assert CANARY not in json.dumps(held)


def test_a_move_and_each_reviewers_lines_are_published(made: Made, tmp_path: Path):
    made.line("borders", 1, "move", part="x-cell-1", detail={"from": "a", "to": "b"})
    made.line("borders", 1, "right", note="The brook.")
    made.line("borders", 1, "right", by="r2")
    to = tmp_path / "out"
    publish.run(made.data, to, cli.QUESTIONS)
    held = made.published(to)
    assert sorted(held) == ["decisions/borders/r1.jsonl", "decisions/borders/r2.jsonl"]
    assert [(row["part"], row["answer"]) for row in held["decisions/borders/r1.jsonl"]] == [
        ("x-cell-1", "move"),
        ("", "right"),
    ]


def test_the_made_up_city_is_never_published(tmp_path: Path):
    made = Made(tmp_path / "desk-synthetic", synthetic=True).items()
    made.line("names", 1, "area")
    to = tmp_path / "out"
    with pytest.raises(publish.Refused, match="made-up city is never published"):
        publish.run(made.data, to, cli.QUESTIONS)
    assert not to.exists()


def test_the_same_lines_give_the_same_files_and_a_second_run_changes_nothing(
    made: Made, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    a_line_in_every_queue(made)

    def no_clock() -> datetime:
        raise AssertionError("the step read the clock")

    monkeypatch.setattr(records, "now", no_clock)
    to = tmp_path / "out"
    publish.run(made.data, to, cli.QUESTIONS)
    first = {path: path.read_bytes() for path in to.rglob("*") if path.is_file()}
    publish.run(made.data, to, cli.QUESTIONS)
    assert {path: path.read_bytes() for path in to.rglob("*") if path.is_file()} == first
    assert all(stat.S_IMODE(path.stat().st_mode) == 0o644 for path in first)


def test_a_file_published_before_does_not_outlive_its_lines(made: Made, tmp_path: Path):
    written = made.line("kinds", 1, "yes")
    to = tmp_path / "out"
    publish.run(made.data, to, cli.QUESTIONS)
    assert (to / "decisions" / "kinds" / "r1.jsonl").is_file()
    (to / "decisions" / "README.md").write_text("kept\n", encoding="utf-8")
    made.line("kinds", 1, "undo", undoes=written.n)
    publish.run(made.data, to, cli.QUESTIONS)
    assert not (to / "decisions" / "kinds" / "r1.jsonl").exists()
    assert (to / "decisions" / "README.md").read_text(encoding="utf-8") == "kept\n"


def test_every_note_that_would_be_published_is_given_once_to_be_read(made: Made, tmp_path: Path):
    made.line("names", 1, "area", note="The same note.")
    made.line("names", 2, "drop", note="The same note.")
    made.line("kinds", 1, "yes", note="Another note.")
    made.line("kinds", 2, "no")
    made.line("ratings", 1, "3", note=CANARY)
    found = publish.run(made.data, tmp_path / "out", cli.QUESTIONS)
    assert found.notes == ("Another note.", "The same note.")
    assert found.lines == 4


def test_lines_in_the_wrong_tree_are_never_published(made: Made, tmp_path: Path):
    records.append(
        path_of(made.data, "know", "r1"),
        reviewer="r1",
        queue="know",
        question="know@1",
        item="x-know-1",
        rev=REV,
        answer="well",
        synthetic=False,
        clock=lambda: START,
    )
    with pytest.raises(Unfit, match="wrong folder: decisions/know"):
        publish.run(made.data, tmp_path / "out", cli.QUESTIONS)
    assert not (tmp_path / "out").exists()


def test_the_command_prints_each_note_and_says_what_to_do_next(
    made: Made, tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.chdir(tmp_path)
    made.line("names", 1, "area", note="A made-up note.")
    made.line("know", 1, "well", note=CANARY)
    assert cli.main(["publish", "--data", str(made.data), "--to", "gazetteer/london"]) == cli.OK
    said = capsys.readouterr().out
    assert said.splitlines() == [
        "Wrote 1 line of 1 queue to gazetteer/london/decisions.",
        "Each line says the day it was written, and not the hour.",
        "These notes are in it. Read each one before you commit:",
        "  A made-up note.",
    ]
    assert cli.main(["publish", "--data", str(made.data)]) == cli.REFUSED
    assert "Say where the copy goes: --to FOLDER" in capsys.readouterr().err


def test_the_command_refuses_the_made_up_city_in_one_line(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    made = Made(tmp_path / "desk-synthetic", synthetic=True).items()
    made.line("names", 1, "area")
    to = tmp_path / "out"
    assert cli.main(["publish", "--data", str(made.data), "--to", str(to)]) == cli.REFUSED
    assert capsys.readouterr().err == "Nothing was written. The made-up city is never published.\n"
