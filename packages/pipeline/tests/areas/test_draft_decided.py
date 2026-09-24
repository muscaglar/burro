"""One official publisher is enough for a name: what the rule fits, and what it settles.

Every name here is made up. The first tests hold the rule to plain values. The rest
read the whole draft of the made-up town, which `draft_support.py` makes.
"""

import json
from pathlib import Path

import pytest
from burro_pipeline.areas import draft_decided, draft_files
from burro_pipeline.areas.draft_names import (
    INSIDE,
    OUTLINE,
    POINT,
    WIDE,
    Name,
    Naming,
    Record,
    name_areas,
)

from .draft_support import SETTINGS, Made, given, made

SURVEY, CENTRES, WARDS = "os-open-names", "gla-town-centre-boundaries", "os-boundary-line"
ADR = Path(__file__).resolve().parents[4] / "docs" / "adr"


def row(
    source: str, locates: str, *, exactly: bool = True, area: str = "lon-n0001"
) -> dict[str, str]:
    return {
        "area_id": area,
        "name": "Alderwick",
        "role": "primary",
        "source_id": source,
        "record_id": f"{source}-1",
        "as_written": "Alderwick" if exactly else "Alderwick Ward",
        "locates": locates,
        "letter_for_letter": "true" if exactly else "false",
    }


# The rule


def test_a_name_an_official_publisher_writes_at_a_point_inside_the_area_is_a_name():
    found = draft_decided.fits([row(SURVEY, "point_inside")])
    assert found is not None and found["record_id"] == "os-open-names-1"
    # A second publisher adds nothing to it, and takes nothing from it.
    both = [row(CENTRES, "polygon_overlap"), row(SURVEY, "point_inside")]
    assert draft_decided.fits(both) == found


@pytest.mark.parametrize(
    "rows",
    [
        # An outline that lies over the area is no point.
        [row(CENTRES, "polygon_overlap")],
        [row(WARDS, "polygon_overlap", exactly=False)],
        # A point that lies outside the area puts the name nowhere in it.
        [row(SURVEY, "label_only")],
        # A label that holds the name among other words does not write it.
        [row(SURVEY, "point_inside", exactly=False)],
        # A point of a publisher that lists no populated places is not what the rule asks.
        [row(CENTRES, "point_inside")],
        [],
    ],
)
def test_the_rule_does_not_fit_a_name_that_no_such_record_puts_inside_the_area(
    rows: list[dict[str, str]],
):
    assert draft_decided.fits(rows) is None


def test_the_rule_is_said_in_words_and_names_the_record_of_the_decision():
    assert draft_decided.SAYS.startswith(
        "A name that an official publisher writes for a populated place, at a point inside "
        "the area, is a name."
    )
    [record] = ADR.glob(f"{draft_decided.RECORD}-*.md")
    text = record.read_text(encoding="utf-8")
    assert draft_decided.DECIDED_ON in text
    assert "one official publisher" in text.casefold()
    assert record.name in (ADR / "README.md").read_text(encoding="utf-8")


# What it settles, on plain values


def record(source: str, name: str, oa: str, *, gives: str = POINT) -> Record:
    publisher = "Ordnance Survey" if source != CENTRES else "Greater London Authority"
    return Record(
        source, f"{source}-{name}", publisher, "NAME1", name, gives, "same", True, {oa: 1.0}
    )


def town() -> tuple[Naming, list[dict[str, str]]]:
    """Three areas. Alderwick and Wexmoor are written by Ordnance Survey at a point
    inside, and Osierholm by a town centre alone. Foxholt is a place inside Alderwick,
    and Quillhaven a wide name over all three."""
    names = [
        Name("lon-n0001", "Alderwick", "area", 9, (record(SURVEY, "Alderwick", "a1"),)),
        Name("lon-n0002", "Wexmoor", "area", 6, (record(SURVEY, "Wexmoor", "b1"),)),
        Name(
            "lon-n0003",
            "Osierholm",
            "area",
            6,
            (record(CENTRES, "Osierholm", "c1", gives=OUTLINE),),
        ),
        Name(
            "lon-n0004",
            "Foxholt",
            INSIDE,
            3,
            (record(SURVEY, "Foxholt", "a2"),),
            of=("lon-n0001",),
        ),
        Name(
            "lon-n0005",
            "Quillhaven",
            WIDE,
            3,
            (record(SURVEY, "Quillhaven", "a1"),),
            of=("lon-n0001", "lon-n0002", "lon-n0003"),
        ),
    ]
    area_of = {"a1": "lon-n0001", "a2": "lon-n0001", "b1": "lon-n0002", "c1": "lon-n0003"}
    naming = name_areas(names, area_of, {area: area for area in set(area_of.values())})
    evidence = [
        {
            "area_id": area,
            "name": offered.as_offered,
            "role": offered.role,
            "source_id": each.record.source_id,
            "record_id": each.record.record_id,
            "as_written": each.record.as_written,
            "locates": each.locates,
            "letter_for_letter": "true",
        }
        for area in sorted(naming.first)
        for offered in naming.offered(area)
        for each in offered.records
    ]
    return naming, evidence


def look(item: str, mark: str, area: str = "") -> dict[str, str]:
    return {"item": item, "mark": mark, "area_id": area or item.split(":")[1]}


def test_the_name_of_an_area_stands_by_the_rule_where_the_draft_has_no_mark_on_it():
    naming, evidence = town()
    by_outline = look("n:lon-n0003", "by_an_outline_alone")
    found = draft_decided.decide(naming, evidence, [by_outline])
    assert found.stands == {"lon-n0001", "lon-n0002"}
    assert found.left_out == {"n:lon-n0001", "n:lon-n0002"}
    # A town centre alone writes Osierholm, over the area: the rule does not fit it.
    assert "n:lon-n0003" not in found.fitted and "lon-n0003" not in found.by
    assert found.hours == pytest.approx(2 * 45 / 3600)


def test_a_name_with_a_mark_is_still_asked_at_the_desk_though_the_rule_fits_it():
    naming, evidence = town()
    found = draft_decided.decide(naming, evidence, [look("n:lon-n0002", "same_name_elsewhere")])
    assert "n:lon-n0002" in found.fitted
    assert found.stands == {"lon-n0001"}
    assert found.asked == {"lon-n0002": "the draft has a mark on it"}


@pytest.mark.parametrize("mark", sorted(draft_decided.BEAR_ON_THE_AREA))
def test_a_mark_that_is_listed_on_another_name_and_bears_on_the_area_holds_its_name_back(
    mark: str,
):
    """A heavier name that lies in an area is marked on that name's own item. It says
    that the area may be better named for it, so the area's name is read by a person."""
    naming, evidence = town()
    found = draft_decided.decide(naming, evidence, [look("a:lon-n0001:foxholt", mark, "lon-n0001")])
    assert found.stands == {"lon-n0002"}
    # Any other mark on another name of the area says nothing of the area's own name.
    other = look("a:lon-n0001:foxholt", "may_be_a_built_thing", "lon-n0001")
    assert draft_decided.decide(naming, evidence, [other]).stands == {"lon-n0001", "lon-n0002"}


def test_another_name_the_rule_fits_is_still_asked_at_the_desk_and_a_wide_name_is_not_fitted():
    naming, evidence = town()
    found = draft_decided.decide(naming, evidence, [])
    assert "a:lon-n0001:foxholt" in found.fitted
    assert not [item for item in found.fitted if "quillhaven" in item]
    assert not [item for item in found.left_out if item.startswith("a:")]


def test_a_name_a_person_answered_at_the_desk_is_not_taken_out_of_their_hands():
    naming, evidence = town()
    found = draft_decided.decide(naming, evidence, [], answered={"lon-n0001"})
    assert found.stands == {"lon-n0002"}
    assert found.asked == {"lon-n0001": "a person answered it at the desk"}


def test_with_every_name_read_the_rule_fits_the_same_names_and_none_stands_by_it_alone():
    naming, evidence = town()
    found = draft_decided.decide(naming, evidence, [], read_every_name=True)
    assert found.fitted == draft_decided.decide(naming, evidence, []).fitted
    assert found.stands == frozenset() and found.left_out == frozenset()
    assert set(found.asked.values()) == {"every name is read"}


# What it settles, on the whole draft of the made-up town


@pytest.fixture(scope="module")
def draft() -> Made:
    return made()


def test_an_area_that_stands_by_the_rule_says_so_and_every_other_is_as_drafted(draft: Made):
    states = {row["area_id"]: row["review_state"] for row in draft.rows("areas.csv")}
    # Alderwick and Thrushcombe: Ordnance Survey writes each at a point inside, and the
    # draft has no mark on either. One publisher writes Thrushcombe.
    assert states == {
        "lon-n0001": "named_by_rule",
        "lon-n0006": "drafted",
        "lon-n0008": "drafted",
        "lon-n0009": "drafted",
        "lon-n0010": "named_by_rule",
    }
    assert states == {
        row["area_id"]: row["review_state"] for row in draft.rows("desk/draft/areas.csv")
    }


def test_a_name_still_says_how_many_publishers_write_it(draft: Made):
    """The rule takes away no record, and an area says who writes its name."""
    writing = {row["area_id"]: row["publishers_writing"] for row in draft.rows("areas.csv")}
    assert writing["lon-n0001"] == "Greater London Authority;Ordnance Survey"
    assert writing["lon-n0010"] == "Ordnance Survey"
    evidence = [row for row in draft.rows("name_evidence.csv") if row["role"] == "primary"]
    assert {row["source_id"] for row in evidence if row["area_id"] == "lon-n0001"} == {
        "os-open-names",
        "gla-town-centre-boundaries",
        "os-boundary-line",
    }
    assert [row["source_id"] for row in evidence if row["area_id"] == "lon-n0010"] == [
        "os-open-names"
    ]


def test_the_flag_for_one_publisher_is_raised_only_where_the_rule_does_not_fit(draft: Made):
    flagged = {
        row["item"]
        for row in draft.rows("desk/draft/flags.csv")
        if (row["queue"], row["flag"]) == ("names", "one_publisher")
    }
    # Each is written by a town centre alone, or is a wide name.
    assert flagged == {
        "a:lon-n0001:quillhaven",
        "a:lon-n0006:osierholm",
        "a:lon-n0008:kindlewharf-high-street",
        "a:lon-n0009:grapnel-dock-cindermoor",
        "a:lon-n0010:pellam-cross",
    }
    sources = {
        (row["area_id"], row["name"]): row["source_id"] for row in draft.rows("name_evidence.csv")
    }
    assert sources["lon-n0006", "Osierholm"] == "gla-town-centre-boundaries"


def test_every_name_the_rule_fits_is_listed_for_a_person_to_skim(draft: Made):
    listed = draft.rows("named_by_the_rule.csv")
    assert draft.columns("named_by_the_rule.csv") == draft_decided.COLUMNS
    assert [(row["area_id"], row["asked_at_the_desk"], row["why"]) for row in listed] == [
        ("lon-n0001", "false", ""),
        ("lon-n0010", "false", ""),
        ("lon-n0006", "true", "the draft has a mark on it"),
        ("lon-n0008", "true", "the draft has a mark on it"),
        ("lon-n0009", "true", "the draft has a mark on it"),
    ]
    for row in listed:
        assert (row["source_id"], row["as_written"]) == ("os-open-names", row["name"])


def test_the_desk_is_handed_no_line_no_flag_and_no_rule_of_a_name_that_stands(draft: Made):
    """The desk refuses a line of an item it does not make, so that no doubt is lost
    without a word. A name that stands has no doubt, and is no item."""
    left_out = {"n:lon-n0001", "n:lon-n0010"}
    for name in ("lines.csv", "flags.csv", "rules_items.csv"):
        rows = [row for row in draft.rows(f"desk/draft/{name}") if row["queue"] == "names"]
        assert rows and not left_out & {row["item"] for row in rows}
    # Its border is still looked at, and says what its name rests on.
    borders = {row["item"] for row in draft.rows("desk/draft/order.csv")}
    assert {"lon-n0001", "lon-n0010"} <= borders


def test_what_the_decision_settled_is_counted(draft: Made):
    counted = json.loads((draft.out / "counts.json").read_bytes())["one_official_publisher"]
    assert counted == {
        "decided_on": "2026-09-24",
        "record": "0022",
        "areas": 5,
        "areas_the_rule_fits": 5,
        "areas_the_rule_does_not_fit": 0,
        "of_them_one_publisher_writes": 3,
        "areas_named_by_the_rule_alone": 2,
        "of_them_one_publisher_writes_the_name": 1,
        "areas_the_rule_fits_that_are_still_asked_at_the_desk": 3,
        "items_that_leave_the_queue_of_names": 2,
        "hours_they_would_have_taken": 0.0,
        "names_the_rule_fits": 10,
    }


def test_with_every_name_read_every_area_is_as_drafted_and_the_flag_is_still_lifted(
    tmp_path: Path,
):
    from dataclasses import replace

    from burro_pipeline.areas import draft_run

    found = given(tmp_path)
    settings = replace(SETTINGS, read_every_name=True)
    draft_run.make(found.inputs, tmp_path / "out", settings=settings)
    read = Made(tmp_path / "out", found.store, {})
    assert {row["review_state"] for row in read.rows("areas.csv")} == {"drafted"}
    flagged = {
        row["item"]
        for row in read.rows("desk/draft/flags.csv")
        if (row["queue"], row["flag"]) == ("names", "one_publisher")
    }
    assert not [item for item in flagged if item.startswith("n:")]
    lines = {row["item"] for row in read.rows("desk/draft/lines.csv") if row["queue"] == "names"}
    assert {"n:lon-n0001", "n:lon-n0010"} <= lines
    assert {row["asked_at_the_desk"] for row in read.rows("named_by_the_rule.csv")} == {"true"}


def test_the_state_of_an_area_that_stands_is_one_the_desk_knows():
    assert draft_decided.NAMED_BY_RULE == "named_by_rule"
    assert draft_files.DRAFTED == "drafted"


# The border of an area whose name stands


def test_the_border_of_an_area_whose_name_nobody_read_says_so(draft: Made):
    """Nothing asks about a name that stands. Its border is looked at under that name, so
    whoever looks at the border is told that nobody read it, and what to do if it is wrong."""
    said = {
        row["item"]: row["value"]
        for row in draft.rows("desk/draft/lines.csv")
        if (row["queue"], row["label"]) == ("borders", "Name")
    }
    assert sorted(said) == ["lon-n0001", "lon-n0010"]
    assert said["lon-n0010"] == (
        "Nobody has read the name of this area. It stands by the rule that one official "
        "publisher is enough: it is written for a populated place at a point inside the "
        "area, by Ordnance Survey, OS Open Names. If the name looks wrong, say so in a note: "
        "a name that stands is turned down by hand."
    )
    lines = [row for row in draft.rows("desk/draft/lines.csv") if row["item"] == "lon-n0010"]
    assert lines[0]["label"] == "Name", "it is read first"
    assert lines[0]["source_id"] == "os-open-names"


def test_the_border_of_an_area_whose_name_is_read_says_nothing_of_it():
    found = draft_decided.decide(*town(), [look("n:lon-n0002", "same_name_elsewhere")])
    words = {SURVEY: "Ordnance Survey, OS Open Names"}
    assert sorted(draft_decided.unread(found, words)) == ["lon-n0001"]
    assert draft_decided.unread(draft_decided.NOTHING, words) == {}
