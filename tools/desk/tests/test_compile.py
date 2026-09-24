"""The step that makes a build's files from the lines of decisions.

Every name, id and note here is made up, and the draft is of a city that does not
exist. No socket is opened.
"""

import csv
import io
import json
import random
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from desk import compile as make
from desk import records
from desk.compile import Refused, build, load, run
from desk.records import Unfit, path_of

START = datetime(2026, 10, 6, 21, 14, 9, tzinfo=UTC)
CANARY = "Zzyzx Parva canary note"

AREAS = """\
area_id,slug,name,primary_borough,seed_record,review_state,superseded_by
syn-n0001,alderwick,Alderwick,Quillhaven,syn-r0001,drafted,
syn-n0002,brindle-cross,Brindle Cross,Quillhaven,syn-r0002,drafted,
syn-n0003,dulcimer-green,Dulcimer Green,Quillhaven,syn-r0003,drafted,
syn-n0004,thrushcombe-marrowmere,Thrushcombe,Marrowmere,syn-r0004,boundary_checked,
"""
CELLS = """\
oa21cd,area_id,basis,evidence,decided_by,decided_on,reason
syn-oa0001,syn-n0001,auto,margin=40;second=syn-n0002,,,
syn-oa0002,syn-n0001,auto,margin=7;second=syn-n0002,,,
syn-oa0003,syn-n0002,auto,margin=30;second=syn-n0001,,,
syn-oa0004,syn-n0002,auto,margin=9;second=syn-n0003,,,
syn-oa0005,syn-n0003,auto,margin=55;second=syn-n0002,,,
syn-oa0006,syn-n0004,auto,margin=60;second=syn-n0003,,,
"""
ALIASES = """\
alias,area_id,kind,source_id,record_id
Dulcimer,syn-n0003,inside,synthetic-names,syn-r0009
The Brindles,syn-n0001,wide,synthetic-names,syn-r0010
The Brindles,syn-n0002,wide,synthetic-names,syn-r0010
"""
EVIDENCE_COLUMNS = make.COLUMNS[make.EVIDENCE]


def evidence(area: str, name: str, role: str, source: str, record: str, wrote: str) -> str:
    held = [area, name, role, source, record, wrote, "NAME1", "point_inside"]
    return ",".join([*held, "2026-09", "2026-09-23", "0" * 64, "true", "", ""])


EVIDENCE = "\n".join(
    [
        ",".join(EVIDENCE_COLUMNS),
        evidence("syn-n0001", "Alderwick", "primary", "synthetic-names", "syn-r0001", "Alderwick"),
        evidence("syn-n0001", "Alderwick", "primary", "synthetic-places", "syn-q0001", "Alderwyck"),
        evidence(
            "syn-n0001", "The Brindles", "wide", "synthetic-names", "syn-r0010", "The Brindles"
        ),
        evidence(
            "syn-n0002", "Brindle Cross", "primary", "synthetic-names", "syn-r0002", "Brindle Cross"
        ),
        evidence(
            "syn-n0002", "The Brindles", "wide", "synthetic-names", "syn-r0010", "The Brindles"
        ),
        evidence("syn-n0003", "Dulcimer", "alias", "synthetic-names", "syn-r0009", "Dulcimer"),
        evidence(
            "syn-n0003",
            "Dulcimer Green",
            "primary",
            "synthetic-names",
            "syn-r0003",
            "Dulcimer Green",
        ),
        evidence(
            "syn-n0004", "Thrushcombe", "primary", "synthetic-names", "syn-r0004", "Thrushcombe"
        ),
        "",
    ]
)


# The queues whose lines are never published, as `questions.json` has them.
PRIVATE = ("claims", "sentences", "ratings", "know")
# What is made from them, and the one list that holds the notes of every queue.
PRIVATE_FILES = {
    *("claims_review.jsonl", "golden.jsonl", "ratings.csv", "know.csv"),
    "to_look_at.csv",
}


def question(name: str, answers: tuple[str, ...], adds: tuple[str, ...] = ()) -> dict[str, Any]:
    codes = [{"code": code, "label": code} for code in answers]
    about = {"id": name, "version": 1, "title": name.title(), "public": name not in PRIVATE}
    return {**about, "adds": list(adds), "answers": codes}


QUESTIONS: dict[str, Any] = {
    "queues": [
        question("claims", ("accept", "not_this_place", "describes_people")),
        question("borders", ("right", "wrong", "unknown"), ("move",)),
        question("names", ("area", "same_ground", "inside", "wide", "drop"), ("pick",)),
        question("whole", ("right", "wrong", "unknown"), ("move",)),
        question("sentences", ("fit", "residents", "praise")),
        question("ratings", ("1", "2", "3", "4", "5", "cannot_say")),
        question("kinds", ("yes", "no", "cannot_tell")),
        question("know", ("well", "a_little", "not")),
    ]
}
REV = "9f2c41d07ab3"


def item(name: str, picks: list[str] | None = None, **preset: Any) -> dict[str, Any]:
    return {
        "id": name,
        "rev": REV,
        "group": "quillhaven",
        "title": "",
        "lines": [],
        "text": None,
        "map": None,
        "picks": picks,
        "flags": [],
        "fill": {},
        "preset": preset,
    }


ITEMS: dict[str, list[dict[str, Any]]] = {
    "names": [
        item("n:syn-n0001", ["Alderwick", "Alderwyck"], of=[], pick="Alderwick"),
        item("n:syn-n0002", ["Brindle Cross"], of=[], pick="Brindle Cross"),
        item("n:syn-n0003", ["Dulcimer Green"], of=[], pick="Dulcimer Green"),
        item("n:syn-n0004", ["Thrushcombe"], of=[], pick="Thrushcombe"),
        item("a:syn-n0003:dulcimer", ["Dulcimer"], of=["syn-n0003"], pick="Dulcimer"),
        item("a:syn-n0001:the-brindles", ["The Brindles"], of=["syn-n0001", "syn-n0002"]),
    ],
    "borders": [item(f"syn-n000{at}") for at in (1, 2, 3, 4)],
    "whole": [item("quillhaven"), item("marrowmere")],
    "claims": [item(f"syn-c00000000000{at}") for at in (1, 2, 3)],
    "sentences": [
        item(f"syn-page-3:{at}", page_id=3, revision_id=1, sentence=at) for at in (17, 18)
    ],
    "ratings": [item("syn-n0001:leafy", area_id="syn-n0001", vibe="leafy")],
    "kinds": [
        item("syn-p0037", kind="theatre", source_id="synthetic"),
        item("syn-p0038", kind="theatre", source_id="synthetic"),
        item("syn-p0039", kind="landmark", source_id="synthetic"),
    ],
    "know": [item("quillhaven"), item("marrowmere")],
}
DRAFT = {
    "areas.csv": AREAS,
    "oa_to_area.csv": CELLS,
    "aliases.csv": ALIASES,
    "name_evidence.csv": EVIDENCE,
}
NAMES_ONLY = {name: text for name, text in DRAFT.items() if name != "oa_to_area.csv"}


@dataclass
class Made:
    """A made-up desk on disk, and the lines written at it."""

    root: Path
    synthetic: bool = True
    at: datetime = START

    @property
    def data(self) -> Path:
        return self.root / "data"

    @property
    def gazetteer(self) -> Path:
        return self.data / "gazetteer"

    @property
    def questions(self) -> Path:
        return self.root / "questions.json"

    def draft(self, tables: dict[str, str]) -> "Made":
        folder = self.data / "draft"
        folder.mkdir(parents=True, exist_ok=True)
        for path in folder.iterdir():
            path.unlink()
        for name, text in tables.items():
            (folder / name).write_text(text, encoding="utf-8")
        return self

    def items(self, queue: str, rows: list[dict[str, Any]], **header: Any) -> None:
        first: dict[str, Any] = {
            "desk": 1,
            "queue": queue,
            "question": f"{queue}@1",
            "synthetic": self.synthetic,
            "made_on": "2026-09-23",
            "made_from": [],
            "count": len(rows),
            **header,
        }
        folder = self.data / "items"
        folder.mkdir(parents=True, exist_ok=True)
        text = "".join(json.dumps(row) + "\n" for row in (first, *rows))
        (folder / f"{queue}.jsonl").write_text(text, encoding="utf-8")

    def line(self, queue: str, name: str, answer: str, by: str = "r1", **more: Any) -> records.Line:
        """One line, as the server writes it. Each is written a minute after the last."""
        self.at += timedelta(minutes=1)
        held: dict[str, Any] = {"rev": REV, "synthetic": self.synthetic, **more}
        return records.append(
            path_of(self.data, queue, by, private=queue in PRIVATE),
            reviewer=by,
            queue=queue,
            question=f"{queue}@1",
            item=name,
            answer=answer,
            clock=lambda: self.at,
            **held,
        )

    def move(
        self, queue: str, name: str, cell: str, to: str, by: str = "r1", **more: Any
    ) -> records.Line:
        area = self.cells().get(cell, {}).get("area_id", name)
        detail = {"from": area, "to": to}
        return self.line(queue, name, "move", by, part=cell, detail=detail, **more)

    def undo(self, queue: str, of: records.Line) -> records.Line:
        return self.line(queue, of.item, "undo", of.reviewer, part=of.part, undoes=of.n, rev=of.rev)

    def build(self) -> make.Built:
        return build(load(self.data, self.questions))

    def table(self, name: str) -> list[dict[str, str]]:
        return rows_of(self.build().gazetteer[name])

    def cells(self) -> dict[str, dict[str, str]]:
        return {row["oa21cd"]: row for row in rows_of(CELLS.encode())}

    def areas(self) -> dict[str, dict[str, str]]:
        return {row["area_id"]: row for row in self.table("areas.csv")}

    def not_applied(self) -> list[tuple[str, str, str, str]]:
        return [
            (row["queue"], row["item"], row["part"], row["why"])
            for row in self.table("not_applied.csv")
        ]


def rows_of(held: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(held.decode("utf-8"), newline="")))


def lines_of(held: bytes) -> list[dict[str, Any]]:
    return [json.loads(row) for row in held.decode("utf-8").splitlines()]


@pytest.fixture(autouse=True)
def no_wait_on_the_disk(monkeypatch: pytest.MonkeyPatch) -> None:
    def no_sync(descriptor: int) -> None:
        """Stands in for the wait on the disk, which the tests of the records hold to account."""

    monkeypatch.setattr(records, "_sync", no_sync)


@pytest.fixture
def made(tmp_path: Path) -> Made:
    held = Made(tmp_path).draft(DRAFT)
    held.questions.write_text(json.dumps(QUESTIONS), encoding="utf-8")
    for queue, rows in ITEMS.items():
        held.items(queue, rows)
    return held


@pytest.fixture
def naming(made: Made) -> Made:
    """The desk as it is while names are decided: no border has been drafted yet."""
    return made.draft(NAMES_ONLY)


def every_file(built: make.Built) -> dict[str, bytes]:
    return {**{f"gazetteer/{k}": v for k, v in built.gazetteer.items()}, **built.out}


# The same lines, the same bytes


def a_sitting(made: Made) -> None:
    """Lines in every queue, with an undo, a dispute, a skip and a changed answer among them."""
    made.line("names", "n:syn-n0001", "area", detail={"of": [], "pick": "Alderwyck"})
    dropped = made.line("names", "a:syn-n0003:dulcimer", "drop")
    made.undo("names", dropped)
    made.line(
        "names", "a:syn-n0001:the-brindles", "wide", detail={"of": ["syn-n0001", "syn-n0002"]}
    )
    made.move("borders", "syn-n0001", "syn-oa0002", "syn-n0002")
    made.line("borders", "syn-n0001", "right", note="The brook is the edge.")
    made.line("borders", "syn-n0002", "right")
    made.line("borders", "syn-n0002", "right", by="r2")
    made.line("borders", "syn-n0003", "wrong", note="The lane.")
    made.line("borders", "syn-n0003", "right", by="r2")
    made.line("whole", "marrowmere", "right")
    made.line("claims", "syn-c000000000001", "accept")
    made.line("claims", "syn-c000000000002", "describes_people", note=CANARY)
    made.line("claims", "syn-c000000000003", "skip")
    made.line(
        "sentences", "syn-page-3:17", "fit", detail={"page_id": 3, "revision_id": 1, "sentence": 17}
    )
    made.line("ratings", "syn-n0001:leafy", "2", detail={"area_id": "syn-n0001", "vibe": "leafy"})
    made.line("ratings", "syn-n0001:leafy", "4", detail={"area_id": "syn-n0001", "vibe": "leafy"})
    made.line(
        "ratings", "syn-n0001:leafy", "5", by="r7", detail={"area_id": "syn-n0001", "vibe": "leafy"}
    )
    made.line("kinds", "syn-p0037", "no", detail={"kind": "theatre", "source_id": "synthetic"})


def test_the_same_lines_give_the_same_bytes_in_whatever_order_they_were_written(made: Made):
    a_sitting(made)
    first = every_file(made.build())
    assert sorted(first) == [
        "borders.csv",
        "claims_review.jsonl",
        "gazetteer/aliases.csv",
        "gazetteer/areas.csv",
        "gazetteer/name_evidence.csv",
        "gazetteer/not_applied.csv",
        "gazetteer/oa_to_area.csv",
        "golden.jsonl",
        "kinds.csv",
        "kinds_counts.csv",
        "know.csv",
        "names.csv",
        "ratings.csv",
        "to_look_at.csv",
        "whole.csv",
    ]
    shuffled = random.Random(11)  # noqa: S311 a fixed order, for a test
    for _ in range(5):
        for path in sorted(made.data.glob("decisions*/*/*.jsonl")):
            rows = path.read_bytes().splitlines(keepends=True)
            shuffled.shuffle(rows)
            path.write_bytes(b"".join(rows))
        assert every_file(made.build()) == first


def test_the_files_do_not_change_with_the_day_they_are_made_on(
    made: Made, monkeypatch: pytest.MonkeyPatch
):
    a_sitting(made)
    first = every_file(made.build())

    def no_clock() -> datetime:
        raise AssertionError("the step read the clock")

    monkeypatch.setattr(records, "now", no_clock)
    assert every_file(made.build()) == first
    assert b"2026-09-23" not in b"".join(made.build().out.values()), "the day the items were made"


def test_with_no_line_the_draft_stands(made: Made):
    built = made.build()
    assert built.gazetteer["areas.csv"] == AREAS.encode()
    assert built.gazetteer["oa_to_area.csv"] == CELLS.encode()
    assert built.gazetteer["aliases.csv"] == ALIASES.encode()
    assert built.gazetteer["name_evidence.csv"] == EVIDENCE.encode()
    assert rows_of(built.gazetteer["not_applied.csv"]) == []
    assert lines_of(built.out["claims_review.jsonl"]) == []


def test_what_is_made_is_written_and_a_second_run_changes_nothing(made: Made):
    a_sitting(made)
    built = run(made.data, made.gazetteer, made.questions).built
    assert {path.name for path in made.gazetteer.iterdir()} == set(built.gazetteer)
    kept = made.data / "out" / "private"
    assert {path.name for path in kept.iterdir()} == built.private == PRIVATE_FILES
    assert {path.name for path in (made.data / "out").iterdir() if path.is_file()} == (
        set(built.out) - built.private
    )
    first = {path: path.read_bytes() for path in made.root.rglob("*") if path.is_file()}
    run(made.data, made.gazetteer, made.questions)
    assert {path: path.read_bytes() for path in made.root.rglob("*") if path.is_file()} == first


def test_a_file_of_an_earlier_run_does_not_outlive_it(made: Made):
    # A file that stays when its queue has gone would be read as if it were of today.
    a_sitting(made)
    run(made.data, made.gazetteer, made.questions)
    kept, out = made.data / "out" / "private", made.data / "out"
    assert (kept / "ratings.csv").is_file() and (out / "kinds.csv").is_file()
    (out / "left-by-hand.csv").write_text("x\n", encoding="utf-8")
    (made.gazetteer / "relations.csv").write_text("x\n", encoding="utf-8")
    (out / "notes").mkdir()
    for queue in ("ratings", "kinds"):
        (made.data / "items" / f"{queue}.jsonl").unlink()

    built = run(made.data, made.gazetteer, made.questions).built
    assert "ratings.csv" not in built.out and "kinds.csv" not in built.out
    assert {path.name for path in kept.iterdir()} == built.private
    assert {path.name for path in out.iterdir() if path.is_file()} == (
        set(built.out) - built.private
    )
    assert {path.name for path in made.gazetteer.iterdir()} == set(built.gazetteer)
    assert (out / "notes").is_dir(), "a folder is nobody's file, and is left"


def test_a_build_of_london_removes_nothing_from_the_gazetteer(tmp_path: Path):
    # The folder of London is committed, and holds files the desk does not make.
    real = Made(tmp_path, synthetic=False).draft(
        {name: text.replace("syn-", "lon-") for name, text in NAMES_ONLY.items()}
    )
    real.questions.write_text(json.dumps(QUESTIONS), encoding="utf-8")
    real.items("claims", [item("lon-c000000000001")])
    gazetteer = tmp_path / "gazetteer" / "london"
    gazetteer.mkdir(parents=True)
    (gazetteer / "relations.csv").write_text("x\n", encoding="utf-8")
    assert run(real.data, gazetteer, real.questions).gazetteer == gazetteer
    assert (gazetteer / "relations.csv").read_text(encoding="utf-8") == "x\n"
    assert (gazetteer / "areas.csv").is_file()


def test_the_made_up_city_is_written_under_its_own_folder_and_nowhere_else(
    made: Made, tmp_path: Path
):
    a_sitting(made)
    for elsewhere in (tmp_path / "gazetteer" / "london", made.data, made.data / ".." / "london"):
        with pytest.raises(Refused, match="nowhere else"):
            run(made.data, elsewhere, made.questions)
    assert not (made.data / "out").exists()
    assert run(made.data, None, made.questions).gazetteer == made.data / "gazetteer"
    assert (made.gazetteer / "areas.csv").is_file()


def test_without_a_gazetteer_only_the_files_of_out_are_written_for_london(tmp_path: Path):
    real = Made(tmp_path, synthetic=False).draft({})
    real.questions.write_text(json.dumps(QUESTIONS), encoding="utf-8")
    real.items("claims", [item("lon-c000000000001")])
    real.line("claims", "lon-c000000000001", "accept")
    assert run(real.data, None, real.questions).gazetteer is None
    assert sorted(path.name for path in (real.data / "out").rglob("*") if path.is_file()) == [
        "claims_review.jsonl",
        "to_look_at.csv",
    ]
    assert not (real.data / "gazetteer").exists()


# Names


def test_a_name_the_founder_calls_an_area_is_checked_and_its_evidence_says_who_chose_it(
    naming: Made,
):
    naming.line("names", "n:syn-n0001", "area", detail={"of": [], "pick": "Alderwick"})
    assert naming.areas()["syn-n0001"]["review_state"] == "name_checked"
    assert naming.areas()["syn-n0002"]["review_state"] == "drafted"
    chosen = [
        (row["source_id"], row["chosen_by"], row["chosen_on"])
        for row in naming.table("name_evidence.csv")
        if row["area_id"] == "syn-n0001" and row["role"] == "primary"
    ]
    assert chosen == [
        ("synthetic-names", "founder", "2026-10-06"),
        ("synthetic-places", "founder", "2026-10-06"),
    ]
    assert {row["chosen_by"] for row in naming.table("name_evidence.csv")} == {"founder", ""}


def test_a_spelling_is_set_only_to_a_form_a_source_wrote(naming: Made):
    naming.line("names", "n:syn-n0001", "area", detail={"of": [], "pick": "Alderwyck"})
    area = naming.areas()["syn-n0001"]
    assert (area["name"], area["slug"]) == ("Alderwyck", "alderwyck")

    naming.line("names", "n:syn-n0002", "area", detail={"of": [], "pick": "Brindle Town"})
    assert naming.areas()["syn-n0002"]["name"] == "Brindle Cross"
    assert naming.not_applied() == [("names", "n:syn-n0002", "", "not_a_spelling")]


def test_what_the_draft_added_to_a_slug_to_tell_two_areas_apart_is_kept(naming: Made):
    rows = [item("n:syn-n0004", ["Thrushcombe", "Thrushcombe Magna"], of=[])]
    naming.items("names", rows)
    wrote = evidence(
        "syn-n0004", "Thrushcombe", "primary", "synthetic-places", "syn-q4", "Thrushcombe Magna"
    )
    naming.draft({**NAMES_ONLY, "name_evidence.csv": EVIDENCE + wrote + "\n"})
    naming.line("names", "n:syn-n0004", "area", detail={"of": [], "pick": "Thrushcombe Magna"})
    assert naming.areas()["syn-n0004"]["slug"] == "thrushcombe-magna-marrowmere"


def test_a_state_never_falls(naming: Made):
    naming.line("names", "n:syn-n0004", "area")
    assert naming.areas()["syn-n0004"]["review_state"] == "boundary_checked"


def stands_by_rule(made: Made, tables: dict[str, str]) -> Made:
    """The desk as it is where the name of Brindle Cross stands by a rule the founder has
    decided already: the draft says so of the area, and the desk makes no item of it."""
    areas = tables["areas.csv"].replace("syn-r0002,drafted,", "syn-r0002,named_by_rule,")
    made.draft({**tables, "areas.csv": areas})
    made.items("names", [row for row in ITEMS["names"] if row["id"] != "n:syn-n0002"])
    return made


def test_a_name_that_stands_by_a_rule_says_so_and_no_person_is_said_to_have_chosen_it(
    made: Made,
):
    naming = stands_by_rule(made, NAMES_ONLY)
    naming.line("names", "n:syn-n0001", "area")
    states = {name: row["review_state"] for name, row in naming.areas().items()}
    assert states["syn-n0002"] == "named_by_rule"
    assert states["syn-n0001"] == "name_checked"
    chosen = {
        row["chosen_by"]
        for row in naming.table("name_evidence.csv")
        if row["area_id"] == "syn-n0002"
    }
    assert chosen == {""}
    built = naming.build()
    assert (built.applied["names"], built.set_aside["names"]) == (1, 0)
    assert not built.by_rule, "a rule the founder adopts at the desk is counted apart"


def test_a_name_that_stands_by_a_rule_is_below_one_a_person_has_read(made: Made):
    """A state never falls, and the state of a name that nobody read is no higher than
    that of one a person checked."""
    states = make.STATES
    assert states.index("drafted") < states.index("named_by_rule") < states.index("name_checked")
    held = stands_by_rule(made, DRAFT)
    assert held.areas()["syn-n0002"]["review_state"] == "named_by_rule"
    held.line("borders", "syn-n0002", "right")
    assert held.areas()["syn-n0002"]["review_state"] == "boundary_checked"


def test_a_name_that_is_dropped_has_no_row(naming: Made):
    naming.line("names", "n:syn-n0002", "drop")
    naming.line("names", "a:syn-n0003:dulcimer", "drop")
    naming.line("names", "a:syn-n0001:the-brindles", "wide", detail={"of": ["syn-n0001"]})
    assert list(naming.areas()) == ["syn-n0001", "syn-n0003", "syn-n0004"]
    assert [(row["alias"], row["area_id"]) for row in naming.table("aliases.csv")] == [
        ("The Brindles", "syn-n0001")
    ]
    left = {(row["area_id"], row["name"]) for row in naming.table("name_evidence.csv")}
    assert left == {
        ("syn-n0001", "Alderwick"),
        ("syn-n0001", "The Brindles"),
        ("syn-n0003", "Dulcimer Green"),
        ("syn-n0004", "Thrushcombe"),
    }


def test_another_name_is_a_row_for_each_area_it_is_given_to(naming: Made):
    naming.line(
        "names",
        "a:syn-n0003:dulcimer",
        "same_ground",
        detail={"of": ["syn-n0003", "syn-n0004"], "pick": "Dulcimer"},
    )
    rows = [row for row in naming.table("aliases.csv") if row["alias"] == "Dulcimer"]
    assert [(row["area_id"], row["kind"], row["record_id"]) for row in rows] == [
        ("syn-n0003", "same_ground", "syn-r0009"),
        ("syn-n0004", "same_ground", "syn-r0009"),
    ]
    told = [row for row in naming.table("name_evidence.csv") if row["name"] == "Dulcimer"]
    assert [(row["area_id"], row["role"], row["chosen_by"]) for row in told] == [
        ("syn-n0003", "alias", "founder"),
        ("syn-n0004", "alias", "founder"),
    ]


def test_a_name_proposed_as_an_area_becomes_another_name_of_the_area_it_is_given_to(naming: Made):
    naming.line(
        "names", "n:syn-n0002", "inside", detail={"of": ["syn-n0001"], "pick": "Brindle Cross"}
    )
    assert naming.not_applied() == [("names", "n:syn-n0002", "", "area_has_names")]
    assert "syn-n0002" in naming.areas(), "while another name is given to it, the draft stands"

    naming.line("names", "a:syn-n0001:the-brindles", "drop")
    assert "syn-n0002" not in naming.areas()
    rows = [row for row in naming.table("aliases.csv") if row["alias"] == "Brindle Cross"]
    assert [(row["area_id"], row["kind"], row["record_id"]) for row in rows] == [
        ("syn-n0001", "inside", "syn-r0002")
    ]
    assert naming.not_applied() == []


# The draft is made again from the table of names. A name that was turned down is then no
# area, and the desk is handed no item of it.


TURNS_DOWN = {"answers": ["same_ground", "inside", "wide", "drop"]}


def asked_with(made: Made) -> Made:
    """The questions, with the answers of `names` that turn a name down."""
    asked = [
        {**queue, "set_aside": TURNS_DOWN} if queue["id"] == "names" else queue
        for queue in QUESTIONS["queues"]
    ]
    made.questions.write_text(json.dumps({"queues": asked}), encoding="utf-8")
    return made


def turned_down(made: Made) -> Made:
    """The desk after the draft was made again: a name the founder turned down is no
    item of the queue, and another that the founder kept is."""
    asked_with(made)
    made.line("names", "n:syn-n0002", "drop", detail={"of": [], "pick": "Brindle Cross"})
    made.line("names", "n:syn-n0001", "area", detail={"of": [], "pick": "Alderwick"})
    made.items("names", [each for each in ITEMS["names"] if each["id"] != "n:syn-n0002"])
    return made


def test_a_name_that_was_turned_down_stays_turned_down_when_the_draft_is_made_again(
    made: Made,
):
    # The draft reads the table of names each time it is made again. Were the answer
    # left out once its item is gone, the next draft would make the name an area again.
    rows = {row["item"]: row for row in rows_of(turned_down(made).build().out["names.csv"])}
    assert set(rows) == {"n:syn-n0001", "n:syn-n0002"}
    gone = rows["n:syn-n0002"]
    assert (gone["answer"], gone["reviewer"], gone["asked_today"]) == ("drop", "r1", "false")
    assert rows["n:syn-n0001"]["asked_today"] == "true"
    assert (gone["decided_on"], gone["synthetic"]) == ("2026-10-06", "true")


def test_only_a_name_the_founder_turned_down_is_kept_once_its_item_is_gone(made: Made):
    asked_with(made)
    made.line("names", "n:syn-n0002", "area", detail={"of": [], "pick": "Brindle Cross"})
    made.line("names", "n:syn-n0003", "skip")
    made.line("names", "n:syn-n0004", "drop", by="r2")
    dropped = made.line("names", "a:syn-n0003:dulcimer", "drop")
    taken_back = made.line("names", "n:syn-n0001", "drop")
    made.undo("names", taken_back)
    made.items("names", [])
    built = made.build()
    # Kept as an area, skipped, of another reviewer, of another name, and taken back.
    assert rows_of(built.out["names.csv"]) == []
    assert dropped.answer == "drop" and built.applied["names"] == 0


def test_a_name_that_is_gone_is_applied_to_no_file_of_the_gazetteer(made: Made):
    before = asked_with(Made(made.root / "as-drafted").draft(DRAFT))
    for queue, rows in ITEMS.items():
        before.items(queue, rows if queue != "names" else [])
    built = turned_down(made).build()
    assert built.gazetteer["oa_to_area.csv"] == before.build().gazetteer["oa_to_area.csv"]
    assert (built.applied["names"], built.set_aside["names"]) == (1, 0)


def test_a_name_that_is_not_an_area_waits_until_it_is_given_one(naming: Made):
    naming.line("names", "n:syn-n0002", "inside", detail={"of": [], "pick": "Brindle Cross"})
    assert naming.areas()["syn-n0002"]["review_state"] == "drafted", "the draft stands"
    assert naming.not_applied() == [("names", "n:syn-n0002", "", "no_area_named")]
    assert naming.build().set_aside["names"] == 1


def test_an_area_goes_only_once_no_other_name_is_given_to_it(naming: Made):
    naming.line("names", "n:syn-n0003", "drop")
    assert "syn-n0003" in naming.areas()
    assert naming.not_applied() == [("names", "n:syn-n0003", "", "area_has_names")]

    naming.line("names", "a:syn-n0003:dulcimer", "inside", detail={"of": ["syn-n0004"]})
    assert "syn-n0003" not in naming.areas()
    assert ("Dulcimer", "syn-n0004") in {
        (row["alias"], row["area_id"]) for row in naming.table("aliases.csv")
    }


def test_a_name_is_given_only_to_an_area_that_is_there(naming: Made):
    naming.line("names", "a:syn-n0003:dulcimer", "inside", detail={"of": ["syn-n9999"]})
    naming.line("names", "n:syn-n0004", "inside", detail={"of": ["syn-n0004"]})
    assert naming.build().gazetteer["aliases.csv"] == ALIASES.encode()
    assert naming.not_applied() == [
        ("names", "a:syn-n0003:dulcimer", "", "no_such_area"),
        ("names", "n:syn-n0004", "", "no_such_area"),
    ]


def test_another_name_cannot_become_an_area_without_an_id(naming: Made):
    naming.line("names", "a:syn-n0003:dulcimer", "area")
    assert naming.not_applied() == [("names", "a:syn-n0003:dulcimer", "", "no_area_id")]
    assert naming.build().gazetteer["aliases.csv"] == ALIASES.encode()


def test_an_area_that_has_cells_is_not_taken_away(made: Made):
    made.line("names", "n:syn-n0002", "drop")
    assert "syn-n0002" in made.areas()
    assert made.not_applied() == [("names", "n:syn-n0002", "", "area_has_cells")]


def test_names_are_decided_by_the_founder_alone(naming: Made):
    naming.line("names", "n:syn-n0001", "drop", by="r2")
    naming.line("names", "n:syn-n0002", "area", by="r2")
    built = naming.build()
    assert built.gazetteer["areas.csv"] == AREAS.encode()
    assert rows_of(built.gazetteer["not_applied.csv"]) == []


# Borders, and whole boroughs


def test_a_move_that_stands_sets_the_area_and_says_who_when_and_why(made: Made):
    made.move("borders", "syn-n0001", "syn-oa0002", "syn-n0002")
    made.line("borders", "syn-n0001", "right", note="The brook is the edge.")
    rows = {row["oa21cd"]: row for row in made.table("oa_to_area.csv")}
    assert rows["syn-oa0002"] == {
        "oa21cd": "syn-oa0002",
        "area_id": "syn-n0002",
        "basis": "reviewed",
        "evidence": "margin=7;second=syn-n0002",
        "decided_by": "founder",
        "decided_on": "2026-10-06",
        "reason": "The brook is the edge.",
    }
    assert {key: row for key, row in rows.items() if key != "syn-oa0002"} == {
        key: row for key, row in made.cells().items() if key != "syn-oa0002"
    }
    assert made.not_applied() == []


def test_every_cell_has_one_row_whatever_was_moved(made: Made):
    for cell in ("syn-oa0001", "syn-oa0002", "syn-oa0005"):
        made.move("borders", "syn-n0001", cell, "syn-n0004")
        made.move("whole", "quillhaven", cell, "syn-n0004")
    made.line("borders", "syn-n0001", "right", note="The brook.")
    made.line("whole", "quillhaven", "wrong", note="The brook.")
    assert [row["oa21cd"] for row in made.table("oa_to_area.csv")] == list(made.cells())
    assert count_of(made.table("oa_to_area.csv"), "area_id") == {
        "syn-n0002": 2,
        "syn-n0004": 4,
    }


def count_of(rows: list[dict[str, str]], column: str) -> dict[str, int]:
    held: dict[str, int] = {}
    for row in rows:
        held[row[column]] = held.get(row[column], 0) + 1
    return held


def test_a_move_with_no_note_on_its_item_is_not_applied(made: Made):
    made.move("borders", "syn-n0001", "syn-oa0002", "syn-n0002")
    assert made.build().gazetteer["oa_to_area.csv"] == CELLS.encode()
    assert made.not_applied() == [("borders", "syn-n0001", "syn-oa0002", "no_note")]

    made.line("borders", "syn-n0001", "skip")
    assert made.not_applied() == [("borders", "syn-n0001", "syn-oa0002", "no_note")]
    made.line("borders", "syn-n0001", "right", note="The brook.")
    assert made.not_applied() == []


def test_a_move_that_was_taken_back_is_not_applied(made: Made):
    moved = made.move("borders", "syn-n0001", "syn-oa0002", "syn-n0002")
    made.line("borders", "syn-n0001", "right", note="The brook.")
    made.undo("borders", moved)
    assert made.build().gazetteer["oa_to_area.csv"] == CELLS.encode()
    assert made.not_applied() == []


def test_two_reviewers_who_disagree_apply_nothing_until_the_founder_settles(made: Made):
    made.move("borders", "syn-n0001", "syn-oa0002", "syn-n0002")
    made.line("borders", "syn-n0001", "right", note="The brook is the edge.")
    made.line("borders", "syn-n0001", "wrong", by="r2", note="The lane is the edge.")
    made.move("borders", "syn-n0001", "syn-oa0001", "syn-n0002", by="r2")

    assert made.build().gazetteer["oa_to_area.csv"] == CELLS.encode()
    assert made.areas()["syn-n0001"]["review_state"] == "drafted"
    assert made.not_applied() == [
        ("borders", "syn-n0001", "syn-oa0001", "disputed"),
        ("borders", "syn-n0001", "syn-oa0002", "disputed"),
    ]

    made.line("borders", "syn-n0001", "right", note="Walked it. The brook.", settles=True)
    rows = {row["oa21cd"]: row for row in made.table("oa_to_area.csv")}
    assert (rows["syn-oa0002"]["area_id"], rows["syn-oa0002"]["reason"]) == (
        "syn-n0002",
        "Walked it. The brook.",
    )
    assert rows["syn-oa0001"]["area_id"] == "syn-n0001", "the other reviewer's move is not applied"
    assert made.not_applied() == [("borders", "syn-n0001", "syn-oa0001", "disputed")]
    assert made.areas()["syn-n0001"]["review_state"] == "boundary_checked"
    built = made.build()
    assert (built.applied["borders"], built.set_aside["borders"]) == (2, 1), "counted, for a person"


def test_a_cell_moved_to_two_areas_is_not_applied(made: Made):
    made.move("borders", "syn-n0001", "syn-oa0002", "syn-n0002")
    made.line("borders", "syn-n0001", "right", note="The brook.")
    made.move("whole", "quillhaven", "syn-oa0002", "syn-n0003")
    made.line("whole", "quillhaven", "right", note="The lane.")
    assert made.build().gazetteer["oa_to_area.csv"] == CELLS.encode()
    assert made.not_applied() == [
        ("borders", "syn-n0001", "syn-oa0002", "moved_to_two_areas"),
        ("whole", "quillhaven", "syn-oa0002", "moved_to_two_areas"),
    ]


def test_a_move_on_an_item_that_changed_is_not_applied_and_is_listed(made: Made):
    made.move("borders", "syn-n0001", "syn-oa0002", "syn-n0002", rev="0" * 12)
    made.line("borders", "syn-n0001", "right", note="The brook.")
    assert made.build().gazetteer["oa_to_area.csv"] == CELLS.encode()
    assert made.not_applied() == [("borders", "syn-n0001", "syn-oa0002", "item_changed")]


@pytest.mark.parametrize(("cell", "to"), [("syn-oa9999", "syn-n0002"), ("syn-oa0002", "syn-n9999")])
def test_a_move_of_a_cell_or_to_an_area_that_is_not_there_fails_the_check(
    made: Made, cell: str, to: str
):
    made.move("borders", "syn-n0001", cell, to)
    made.line("borders", "syn-n0001", "right", note="The brook.")
    with pytest.raises(Refused, match="names a cell or an area that the draft does not hold"):
        made.build()


def test_right_from_one_reviewer_is_checked_and_from_two_checked_twice(made: Made):
    made.line("borders", "syn-n0001", "right")
    made.line("borders", "syn-n0002", "right")
    made.line("borders", "syn-n0002", "right", by="r2")
    made.line("borders", "syn-n0003", "unknown")
    states = {name: row["review_state"] for name, row in made.areas().items()}
    assert states == {
        "syn-n0001": "boundary_checked",
        "syn-n0002": "checked_twice",
        "syn-n0003": "drafted",
        "syn-n0004": "boundary_checked",
    }


def look_at(made: Made) -> list[dict[str, str]]:
    return rows_of(made.build().out["to_look_at.csv"])


def test_a_border_mended_and_called_right_is_checked(made: Made):
    # The person moved a cell and then said the border is right, as it now stands.
    made.move("borders", "syn-n0001", "syn-oa0002", "syn-n0002")
    made.line("borders", "syn-n0001", "right", note="The brook is the edge.")
    rows = {row["oa21cd"]: row for row in made.table("oa_to_area.csv")}
    assert (rows["syn-oa0002"]["area_id"], rows["syn-oa0002"]["basis"]) == ("syn-n0002", "reviewed")
    assert rows["syn-oa0002"]["reason"] == "The brook is the edge."
    assert made.areas()["syn-n0001"]["review_state"] == "boundary_checked"
    assert look_at(made) == []


def test_an_area_called_wrong_is_listed_with_its_note(made: Made):
    made.line("borders", "syn-n0001", "wrong", note="The lane is the edge, not the brook.")
    made.move("borders", "syn-n0002", "syn-oa0004", "syn-n0003")
    made.line("borders", "syn-n0002", "wrong", note="Better, and still wrong to the east.")
    states = {name: row["review_state"] for name, row in made.areas().items()}
    assert (states["syn-n0001"], states["syn-n0002"]) == ("drafted", "drafted")
    rows = {row["oa21cd"]: row for row in made.table("oa_to_area.csv")}
    assert rows["syn-oa0004"]["area_id"] == "syn-n0003", "the move is applied all the same"
    assert [(row["queue"], row["item"], row["why"], row["note"]) for row in look_at(made)] == [
        ("borders", "syn-n0001", "wrong", "The lane is the edge, not the brook."),
        ("borders", "syn-n0002", "wrong", "Better, and still wrong to the east."),
    ]


def test_what_a_person_flagged_is_in_one_list_with_its_note(made: Made):
    about = {"area_id": "syn-n0001", "vibe": "leafy"}
    made.line("whole", "quillhaven", "unknown", note="Never been.")
    made.line("kinds", "syn-p0037", "cannot_tell", note="The name does not say.")
    made.line("kinds", "syn-p0038", "yes", second=True)
    made.line("kinds", "syn-p0039", "skip", note="Should be a new kind.")
    made.line("names", "a:syn-n0003:dulcimer", "skip", second=True, note="Should be an area.")
    made.line("names", "n:syn-n0002", "area", note="https://example.org/made-up-document")
    made.line("claims", "syn-c000000000001", "accept", second=True)
    made.line("ratings", "syn-n0001:leafy", "cannot_say", detail=about)
    made.line("borders", "syn-n0003", "right")
    found = [
        (row["queue"], row["item"], row["reviewer"], row["answer"], row["why"], row["note"])
        for row in look_at(made)
    ]
    assert found == [
        ("claims", "syn-c000000000001", "r1", "accept", "marked", ""),
        ("names", "a:syn-n0003:dulcimer", "r1", "skip", "skipped", "Should be an area."),
        ("whole", "quillhaven", "r1", "unknown", "not_known", "Never been."),
        ("kinds", "syn-p0037", "r1", "cannot_tell", "not_known", "The name does not say."),
        ("kinds", "syn-p0038", "r1", "yes", "marked", ""),
        ("kinds", "syn-p0039", "r1", "skip", "skipped", "Should be a new kind."),
    ], "a rating that cannot be given is what a rater is asked to say, and is not listed"
    built = made.build()
    assert "to_look_at.csv" in built.private, "it holds the notes of private queues"
    assert dict(built.look) == {"marked": 2, "skipped": 2, "not_known": 2}


def test_every_answer_is_written_with_its_note_and_its_mark(made: Made):
    # A note that is read by nothing is a flag that is never seen again.
    made.line("names", "n:syn-n0002", "area", note="https://example.org/made-up-document")
    made.line("names", "a:syn-n0003:dulcimer", "inside", detail={"of": ["syn-n0003"]})
    made.line("borders", "syn-n0003", "right", second=True)
    made.line("kinds", "syn-p0037", "no", note="A stage school.", second=True)
    made.line("claims", "syn-c000000000001", "not_this_place", note="It is of Foxholt.")
    made.line("sentences", "syn-page-3:17", "praise", note="A superlative.")
    built = made.build()
    names = {row["item"]: row for row in rows_of(built.out["names.csv"])}
    assert names["n:syn-n0002"] == {
        "item": "n:syn-n0002",
        "reviewer": "r1",
        "answer": "area",
        "of": "",
        "pick": "Brindle Cross",
        "note": "https://example.org/made-up-document",
        "second": "false",
        "decided_on": "2026-10-06",
        "synthetic": "true",
    }
    assert names["a:syn-n0003:dulcimer"]["of"] == "syn-n0003"
    assert rows_of(built.out["borders.csv"])[0]["second"] == "true"
    (kind,) = rows_of(built.out["kinds.csv"])
    assert (kind["note"], kind["second"], kind["synthetic"]) == ("A stage school.", "true", "true")
    (claim,) = lines_of(built.out["claims_review.jsonl"])
    assert (claim["note"], claim["second"], claim["synthetic"]) == (
        "It is of Foxholt.",
        False,
        True,
    )
    (golden,) = lines_of(built.out["golden.jsonl"])
    assert (golden["note"], golden["second"], golden["synthetic"]) == (
        "A superlative.",
        False,
        True,
    )
    assert not {"names.csv", "borders.csv", "whole.csv", "kinds.csv"} & built.private


def test_every_file_made_from_the_made_up_city_says_so(made: Made):
    a_sitting(made)
    made.line("know", "quillhaven", "well")
    made.line("whole", "quillhaven", "wrong", note="The lane.")
    built = made.build()
    assert len(built.out) == 10
    for name, held in built.out.items():
        if name.endswith(".jsonl"):
            rows = lines_of(held)
            assert rows and all(row["synthetic"] is True for row in rows), name
        else:
            rows = rows_of(held)
            assert rows and all(row["synthetic"] == "true" for row in rows), name
            assert held.splitlines()[0].decode().split(",")[-1] == "synthetic", name


def test_a_file_made_from_london_says_that_it_is_not_made_up(tmp_path: Path):
    real = Made(tmp_path, synthetic=False).draft({})
    real.questions.write_text(json.dumps(QUESTIONS), encoding="utf-8")
    real.items("claims", [item("lon-c000000000001")])
    real.items("kinds", [item("lon-p0037", kind="theatre", source_id="overture-places")])
    real.line("claims", "lon-c000000000001", "accept")
    real.line("kinds", "lon-p0037", "yes")
    built = real.build()
    assert [row["synthetic"] for row in lines_of(built.out["claims_review.jsonl"])] == [False]
    assert [row["synthetic"] for row in rows_of(built.out["kinds.csv"])] == ["false"]
    assert [row["synthetic"] for row in rows_of(built.out["kinds_counts.csv"])] == ["false"]


def test_what_is_flagged_is_not_counted_as_applied(made: Made):
    made.line("borders", "syn-n0001", "right")
    made.line("borders", "syn-n0002", "wrong", note="The lane.")
    made.line("borders", "syn-n0003", "unknown")
    made.line("kinds", "syn-p0037", "yes")
    made.line("kinds", "syn-p0038", "cannot_tell")
    built = made.build()
    assert (built.applied["borders"], built.flagged["borders"]) == (1, 2)
    assert (built.applied["kinds"], built.flagged["kinds"]) == (1, 1)


def test_the_founder_not_knowing_lets_the_reviewers_answer_and_moves_stand(made: Made):
    made.line("borders", "syn-n0001", "unknown")
    made.move("borders", "syn-n0001", "syn-oa0002", "syn-n0002", by="r2")
    made.line("borders", "syn-n0001", "right", by="r2", note="Walked it. The brook.")
    rows = {row["oa21cd"]: row for row in made.table("oa_to_area.csv")}
    assert (rows["syn-oa0002"]["area_id"], rows["syn-oa0002"]["decided_by"]) == (
        "syn-n0002",
        "reviewer-2",
    )
    assert rows["syn-oa0002"]["reason"] == "Walked it. The brook."
    assert made.areas()["syn-n0001"]["review_state"] == "boundary_checked"
    assert made.not_applied() == []


def test_an_area_the_founder_did_not_know_is_never_said_to_be_checked_twice(made: Made):
    made.line("borders", "syn-n0001", "unknown")
    made.line("borders", "syn-n0001", "right", by="r2")
    assert made.areas()["syn-n0001"]["review_state"] == "boundary_checked"


def test_a_borough_that_is_right_checks_each_area_nobody_called_wrong(made: Made):
    made.line("whole", "quillhaven", "right")
    made.line("borders", "syn-n0001", "right", by="r2")
    made.line("borders", "syn-n0002", "wrong", note="The lane.")
    made.line("borders", "syn-n0003", "right")
    states = {name: row["review_state"] for name, row in made.areas().items()}
    assert states == {
        "syn-n0001": "checked_twice",
        "syn-n0002": "drafted",
        "syn-n0003": "boundary_checked",
        "syn-n0004": "boundary_checked",
    }


def test_a_third_reviewer_has_no_role_in_the_gazetteer(made: Made):
    made.line("borders", "syn-n0001", "right", by="r3")
    with pytest.raises(Refused, match="r3 has no role to be written as"):
        made.build()


# Claims, sentences and the rest


def test_an_accepted_claim_is_accepted_and_any_other_is_rejected_with_its_reason(made: Made):
    made.line("claims", "syn-c000000000002", "describes_people", note=CANARY)
    made.line("claims", "syn-c000000000001", "accept")
    made.line("claims", "syn-c000000000003", "accept", by="r2")
    said = {"note": "", "second": False, "synthetic": True}
    assert lines_of(made.build().out["claims_review.jsonl"]) == [
        {
            "claim_id": "syn-c000000000001",
            "review": {
                "status": "accepted",
                "reviewed_on": "2026-10-06",
                "reviewer": "founder",
                "reason": None,
            },
            **said,
        },
        {
            "claim_id": "syn-c000000000002",
            "review": {
                "status": "rejected",
                "reviewed_on": "2026-10-06",
                "reviewer": "founder",
                "reason": "describes_people",
            },
            **said,
            "note": CANARY,
        },
        {
            "claim_id": "syn-c000000000003",
            "review": {
                "status": "accepted",
                "reviewed_on": "2026-10-06",
                "reviewer": "second",
                "reason": None,
            },
            **said,
        },
    ]


def test_a_claim_in_dispute_a_skip_and_a_stale_answer_give_no_row(made: Made):
    made.line("claims", "syn-c000000000001", "accept")
    made.line("claims", "syn-c000000000001", "not_this_place", by="r2")
    made.line("claims", "syn-c000000000002", "skip")
    made.line("claims", "syn-c000000000003", "accept", rev="0" * 12)
    built = made.build()
    assert lines_of(built.out["claims_review.jsonl"]) == []
    assert built.set_aside["claims"] == 1


def test_the_golden_set_says_of_each_sentence_whether_it_is_fit(made: Made):
    made.line("sentences", "syn-page-3:18", "praise")
    made.line("sentences", "syn-page-3:17", "fit")
    said = {"note": "", "second": False, "synthetic": True}
    assert lines_of(made.build().out["golden.jsonl"]) == [
        {"page_id": 3, "revision_id": 1, "sentence": 17, "fit": True, "code": "fit", **said},
        {"page_id": 3, "revision_id": 1, "sentence": 18, "fit": False, "code": "praise", **said},
    ]


def test_each_raters_rating_is_a_row_of_its_own(made: Made):
    about = {"area_id": "syn-n0001", "vibe": "leafy"}
    made.line("ratings", "syn-n0001:leafy", "2", detail=about)
    made.line("ratings", "syn-n0001:leafy", "5", by="r12", detail=about)
    made.line("ratings", "syn-n0001:leafy", "4", by="r3", detail=about)
    made.line("ratings", "syn-n0001:leafy", "3", detail=about)
    assert rows_of(made.build().out["ratings.csv"]) == [
        {
            "item": "syn-n0001:leafy",
            "reviewer": reviewer,
            "answer": answer,
            **about,
            "note": "",
            "second": "false",
            "decided_on": "2026-10-06",
            "synthetic": "true",
        }
        for reviewer, answer in (("r1", "3"), ("r3", "4"), ("r12", "5"))
    ]


def test_a_row_holds_what_the_item_was_made_with_whatever_the_line_says(made: Made):
    # A file sent back by another reviewer never went through the server.
    made.line("ratings", "syn-n0001:leafy", "2", by="r2", detail={"home": CANARY, "vibe": "x"})
    made.line("kinds", "syn-p0037", "no", detail={})
    built = made.build()
    assert rows_of(built.out["ratings.csv"])[0] == {
        "item": "syn-n0001:leafy",
        "reviewer": "r2",
        "answer": "2",
        "area_id": "syn-n0001",
        "vibe": "leafy",
        "note": "",
        "second": "false",
        "decided_on": "2026-10-06",
        "synthetic": "true",
    }
    assert rows_of(built.out["kinds.csv"])[0]["kind"] == "theatre"
    assert not [name for name, held in every_file(built).items() if b"Zzyzx" in held]


def test_kinds_are_counted_by_kind(made: Made):
    made.line("kinds", "syn-p0037", "no", detail={"kind": "theatre", "source_id": "synthetic"})
    made.line("kinds", "syn-p0038", "yes", detail={"kind": "theatre", "source_id": "synthetic"})
    made.line("kinds", "syn-p0039", "yes", detail={"kind": "landmark", "source_id": "synthetic"})
    made.line("kinds", "syn-p0039", "skip", detail={"kind": "landmark", "source_id": "synthetic"})
    built = made.build()
    assert [row["item"] for row in rows_of(built.out["kinds.csv"])] == ["syn-p0037", "syn-p0038"]
    assert rows_of(built.out["kinds_counts.csv"]) == [
        {
            "kind": "theatre",
            "asked": "2",
            "yes": "1",
            "no": "1",
            "cannot_tell": "0",
            "synthetic": "true",
        }
    ]


# What keeps the files safe


def test_what_is_made_from_private_lines_is_the_owners_alone(made: Made):
    a_sitting(made)
    made.line("know", "quillhaven", "well")
    built = run(made.data, made.gazetteer, made.questions).built
    kept = made.data / "out" / "private"
    assert kept.stat().st_mode & 0o777 == 0o700
    assert built.private == PRIVATE_FILES
    for name in built.private:
        assert (kept / name).stat().st_mode & 0o777 == 0o600, name
        assert not (made.data / "out" / name).exists(), name
    for name in set(built.out) - built.private:
        assert (made.data / "out" / name).is_file(), name
        assert not (kept / name).exists(), name


def test_lines_in_the_wrong_folder_stop_the_build_and_are_named(made: Made):
    # As a folder of decisions from before the two were kept apart.
    records.append(
        path_of(made.data, "ratings", "r1"),
        reviewer="r1",
        queue="ratings",
        question="ratings@1",
        item="syn-n0001:leafy",
        rev=REV,
        answer="2",
        synthetic=True,
        clock=lambda: START,
    )
    with pytest.raises(Unfit, match="wrong folder: decisions/ratings"):
        made.build()


def test_in_the_gazetteer_a_note_is_written_only_as_the_reason_of_a_move(made: Made):
    made.line("names", "n:syn-n0001", "area", note=CANARY)
    made.line("whole", "quillhaven", "unknown", note=CANARY)
    made.move("borders", "syn-n0001", "syn-oa0002", "syn-n0002")
    made.line("borders", "syn-n0001", "right", note="The brook is the edge.")
    built = made.build()
    assert not [name for name, held in built.gazetteer.items() if b"Zzyzx" in held]
    assert [name for name, held in built.gazetteer.items() if b"The brook" in held] == [
        "oa_to_area.csv"
    ]


def test_the_note_of_a_private_queue_is_in_no_file_but_a_private_one(made: Made):
    about = {"area_id": "syn-n0001", "vibe": "leafy"}
    made.line("claims", "syn-c000000000001", "not_this_place", note=CANARY, second=True)
    made.line("sentences", "syn-page-3:17", "praise", note=CANARY)
    made.line("ratings", "syn-n0001:leafy", "2", note=CANARY, detail=about)
    made.line("know", "quillhaven", "not", note=CANARY)
    made.line("kinds", "syn-p0037", "no", note="A stage school.")
    built = made.build()
    holds = {name for name, held in every_file(built).items() if b"Zzyzx" in held}
    assert holds == PRIVATE_FILES
    assert holds <= built.private
    assert {name for name, held in every_file(built).items() if b"stage school" in held} == {
        "kinds.csv"
    }


@pytest.mark.parametrize("start", ["=", "+", "-", "@"])
def test_a_cell_a_spreadsheet_would_run_gains_an_apostrophe(made: Made, start: str):
    note = f'{start}HYPERLINK("https://elsewhere.example","x")'
    made.move("borders", "syn-n0001", "syn-oa0002", "syn-n0002")
    made.line("borders", "syn-n0001", "right", note=note)
    rows = {row["oa21cd"]: row for row in made.table("oa_to_area.csv")}
    assert rows["syn-oa0002"]["reason"] == f"'{note}"
    assert rows["syn-oa0001"]["evidence"] == "margin=40;second=syn-n0002"


@pytest.mark.parametrize("start", ["\t", "\r"])
def test_a_cell_of_a_draft_that_begins_with_a_tab_gains_an_apostrophe_too(start: str):
    # A note cannot hold one. A cell of the draft can, and is written out again.
    held = make.written(("name",), [{"name": f"{start}=1+1"}])
    assert rows_of(held) == [{"name": f"'{start}=1+1"}]


def test_a_line_of_the_other_city_is_never_mixed_in(made: Made):
    made.line("claims", "syn-c000000000001", "accept")
    made.line("claims", "syn-c000000000002", "accept", synthetic=False)
    with pytest.raises(Refused, match="never mixed"):
        made.build()


def test_items_of_both_cities_are_never_read_together(made: Made):
    made.items("claims", ITEMS["claims"], synthetic=False)
    with pytest.raises(Unfit, match="made-up"):
        made.build()


def test_london_is_never_written_as_the_made_up_city(tmp_path: Path):
    real = Made(tmp_path, synthetic=False).draft(NAMES_ONLY)
    real.questions.write_text(json.dumps(QUESTIONS), encoding="utf-8")
    real.items("names", ITEMS["names"])
    with pytest.raises(Refused, match="the made-up city and London are in one file"):
        real.build()


def test_the_made_up_city_is_never_written_over_london(made: Made):
    made.gazetteer.mkdir()
    london = AREAS.replace("syn-n", "lon-n")
    (made.gazetteer / "areas.csv").write_text(london, encoding="utf-8")
    with pytest.raises(Refused, match="holds the other city"):
        run(made.data, made.gazetteer, made.questions)
    assert (made.gazetteer / "areas.csv").read_text(encoding="utf-8") == london
    assert not (made.data / "out").exists()


def test_when_a_check_fails_nothing_is_written(made: Made):
    a_sitting(made)
    run(made.data, made.gazetteer, made.questions)
    before = {path: path.read_bytes() for path in made.root.rglob("*") if path.is_file()}
    made.line("claims", "syn-c000000000001", "not_this_place")
    made.move("borders", "syn-n0003", "syn-oa0005", "syn-n9999", by="r2")
    made.line("borders", "syn-n0003", "wrong", by="r2", note="The lane.", rev=REV)
    made.line("borders", "syn-n0003", "wrong", note="The lane.", settles=False)
    lines = {path for path in before if {"decisions", "decisions-private"} & set(path.parts)}
    with pytest.raises(Refused):
        run(made.data, made.gazetteer, made.questions)
    after = {path: path.read_bytes() for path in made.root.rglob("*") if path.is_file()}
    assert {path: held for path, held in after.items() if path not in lines} == {
        path: held for path, held in before.items() if path not in lines
    }


def test_every_check_that_failed_is_said(made: Made):
    made.line("borders", "syn-n0001", "right", by="r3")
    made.move("borders", "syn-n0002", "syn-oa0003", "syn-n9999")
    made.line("borders", "syn-n0002", "right", note="The brook.")
    with pytest.raises(Refused) as refusal:
        made.build()
    assert len(refusal.value.problems) == 2
    assert "Zzyzx" not in str(refusal.value)


@pytest.mark.parametrize(
    ("name", "text"),
    [
        ("areas.csv", AREAS.replace("area_id,slug", "slug,area_id")),
        ("areas.csv", AREAS.replace(",superseded_by", ",superseded_by,residents")),
        ("oa_to_area.csv", CELLS.replace("syn-n0001,auto", "syn-n0001,auto,more", 1)),
        ("aliases.csv", "alias,area_id\nDulcimer,syn-n0003\n"),
        ("name_evidence.csv", "�\n"),
    ],
)
def test_a_draft_that_is_not_as_the_design_gives_it_is_refused(made: Made, name: str, text: str):
    made.draft({**DRAFT, name: text})
    with pytest.raises(Unfit, match=f"draft/{name}"):
        made.build()


def test_a_draft_that_holds_a_cell_twice_fails_the_check(made: Made):
    made.draft({**DRAFT, "oa_to_area.csv": CELLS + "syn-oa0001,syn-n0002,auto,,,,\n"})
    with pytest.raises(Refused, match="a cell has two rows"):
        made.build()


def test_a_file_that_ends_in_half_a_line_is_counted_and_the_rest_is_made(made: Made):
    made.line("claims", "syn-c000000000001", "accept")
    file = path_of(made.data, "claims", "r1", private=True)
    with file.open("ab") as torn:
        torn.write(file.read_bytes()[:90])
    built = made.build()
    assert built.broken == 1
    assert [row["claim_id"] for row in lines_of(built.out["claims_review.jsonl"])] == [
        "syn-c000000000001"
    ]


def test_a_clock_that_goes_backwards_changes_no_file_but_the_day_it_says(made: Made):
    made.line("claims", "syn-c000000000001", "accept")
    made.at -= timedelta(days=3)
    made.line("claims", "syn-c000000000001", "not_this_place")
    (row,) = lines_of(made.build().out["claims_review.jsonl"])
    assert row["review"] == {
        "status": "rejected",
        "reviewed_on": "2026-10-03",
        "reviewer": "founder",
        "reason": "not_this_place",
    }
