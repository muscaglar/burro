"""A name decided at the review desk takes the place of the name that was drafted.

The desk compiles its decisions into the files of a gazetteer, and a build
reads those files. These tests hold the two to each other: what the desk's own
step writes is what a build reads, and a name a person chose is served as they
spelt it, and is said to be checked.

Nothing here is real. The town, its names and the answers are made up, and
every name is one the synthetic release already holds.
"""

import csv
import io
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import desk
import pytest
from burro_core.ids import NameState
from burro_pipeline.assemble import names
from desk import compile as compiled
from desk import records

from . import names_support as drafts
from .names_support import ALDERWICK, ESKERFOLD, FOXHOLT

QUESTIONS = Path(desk.__file__).parent / "questions.json"
# The ids of the made-up town are shaped as London's are, as those of every made-up build
# are, so the desk is told that the draft is not of its own made-up city.
MADE_UP_CITY = False
REV = "9f2c41d07ab3"
START = datetime(2026, 10, 6, 21, 14, 9, tzinfo=UTC)
ONE, TWO, THREE = "lon-ne02999001", "lon-ne02999002", "lon-ne02999003"
# A second spelling of one name, which a second record writes.
OTHER_SPELLING = "Eskerfold Green"
EVIDENCE = (
    *drafts.EVIDENCE[:2],
    *(row for row in drafts.EVIDENCE[3:] if row.role == names.PRIMARY),
    drafts.Wrote(ESKERFOLD, drafts.CENTRES, OTHER_SPELLING),
)
NEIGHBOURHOODS = {place: name for place, name in drafts.NEIGHBOURHOODS.items() if name}


def as_the_desk_reads_it() -> dict[str, bytes]:
    """The made-up draft under the columns of the areas design, in their order."""
    held = drafts.files(
        neighbourhoods=NEIGHBOURHOODS,
        given={number: place for number, place in drafts.GIVEN.items() if place in NEIGHBOURHOODS},
        evidence=EVIDENCE,
    )
    columns = compiled.COLUMNS
    found: dict[str, bytes] = {}
    for name in (names.AREAS, names.GIVEN, names.EVIDENCE):
        rows = csv.DictReader(io.StringIO(held[name].decode("utf-8"), newline=""))
        found[name] = compiled.written(columns[name], list(rows))
    found[compiled.ALIASES] = compiled.written(columns[compiled.ALIASES], [])
    return found


class Desk:
    """A made-up desk on disk: the draft it was filled from, and the lines written at it."""

    def __init__(self, root: Path) -> None:
        self.data = root / "data"
        self.at = START
        (self.data / "draft").mkdir(parents=True)
        for name, content in as_the_desk_reads_it().items():
            (self.data / "draft" / name).write_bytes(content)
        items: list[dict[str, Any]] = [
            {
                "id": f"n:{place}",
                "rev": REV,
                "group": "quillhaven",
                "title": "",
                "lines": [],
                "text": None,
                "map": None,
                "picks": sorted({row.as_written for row in EVIDENCE if row.place_id == place}),
                "flags": [],
                "fill": {},
                "preset": {"of": [], "pick": name},
            }
            for place, name in NEIGHBOURHOODS.items()
        ]
        first: dict[str, Any] = {
            "desk": 1,
            "queue": "names",
            "question": "names@1",
            "synthetic": MADE_UP_CITY,
            "made_on": "2026-09-23",
            "made_from": [],
            "count": len(items),
        }
        (self.data / "items").mkdir()
        (self.data / "items" / "names.jsonl").write_text(
            "".join(json.dumps(row) + "\n" for row in (first, *items)), encoding="utf-8"
        )

    def decide(self, place: str, answer: str, **detail: Any) -> None:
        """One answer of the founder's about one name, as the desk's server writes it."""
        self.at += timedelta(minutes=1)
        records.append(
            records.path_of(self.data, "names", "r1"),
            reviewer="r1",
            queue="names",
            question="names@1",
            item=f"n:{place}",
            rev=REV,
            answer=answer,
            synthetic=MADE_UP_CITY,
            detail=detail,
            clock=lambda: self.at,
        )

    def gazetteer(self) -> dict[str, bytes]:
        """The files of the gazetteer, as the desk's own step makes them from the lines."""
        built = compiled.build(compiled.load(self.data, QUESTIONS))
        return {name: built.gazetteer[name] for name in names.COLUMNS}


@pytest.fixture(autouse=True)
def no_wait_on_the_disk(monkeypatch: pytest.MonkeyPatch) -> None:
    def no_sync(descriptor: int) -> None:
        """Stands in for the wait on the disk, which the desk's own tests hold to account."""

    monkeypatch.setattr(records, "_sync", no_sync)


def named(files: dict[str, bytes]) -> dict[str, names.Bears]:
    return names.name_areas(
        names.draft_of(files), drafts.areas(), drafts.cells(), drafts.CENTRES_OF
    )


def test_a_build_reads_the_files_of_the_gazetteer_as_the_desk_compiles_them(tmp_path: Path):
    found = named(Desk(tmp_path).gazetteer())
    assert {area: borne.name for area, borne in found.items()} == {
        ONE: "Alderwick, west",
        TWO: "Alderwick, east",
        THREE: "Eskerfold",
    }
    # Nobody has answered anything, so every name is a draft.
    assert {borne.written.state for borne in found.values()} == {NameState.DRAFT}


def test_a_name_a_person_called_right_at_the_desk_is_served_as_checked(tmp_path: Path):
    at_the_desk = Desk(tmp_path)
    at_the_desk.decide(ESKERFOLD, "area", of=[], pick="Eskerfold")
    found = named(at_the_desk.gazetteer())
    assert (found[THREE].name, found[THREE].written.state) == ("Eskerfold", NameState.CHECKED)
    assert found[ONE].written.state is NameState.DRAFT


def test_the_spelling_a_person_chose_at_the_desk_takes_the_place_of_the_drafted_one(
    tmp_path: Path,
):
    at_the_desk = Desk(tmp_path)
    at_the_desk.decide(ESKERFOLD, "area", of=[], pick=OTHER_SPELLING)
    found = named(at_the_desk.gazetteer())
    assert found[THREE].name == OTHER_SPELLING
    assert found[THREE].written.checked
    # Every record the person chose the name from stands behind it.
    assert found[THREE].source_ids == (drafts.CENTRES, drafts.PLACES)


def test_a_name_the_desk_set_aside_stands_as_it_was_drafted_until_the_draft_is_made_again(
    tmp_path: Path,
):
    # The desk cannot take the ground from under an area: a name that is turned down while
    # output areas are drafted to it is set aside, and the draft stands.
    at_the_desk = Desk(tmp_path)
    at_the_desk.decide(FOXHOLT, "drop", of=[])
    found = named(at_the_desk.gazetteer())
    assert found[ONE].written.place_id == ALDERWICK
    assert {borne.written.state for borne in found.values()} == {NameState.DRAFT}
