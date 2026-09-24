"""The items of each queue, made from a draft folder: the rules, on small drafts.

Every draft here is written by the test that reads it, and every name in it is made up.
The queues as they are filled from the synthetic release are held in `test_queues.py`.
"""

import json
import math
from pathlib import Path
from typing import Any

import pytest
from desk.fill import draft
from desk.fill.draft import Draft
from desk.fill.layers import Unfit

QUESTIONS = json.loads(draft.QUESTIONS.read_text(encoding="utf-8"))["queues"]


def test_every_queue_of_the_questions_has_a_step_that_fills_it():
    asked = [queue["id"] for queue in QUESTIONS]
    assert list(draft.QUEUES) == list(draft.MAKERS) == asked
    assert {queue: held.version for queue, held in draft.questions().items()} == {
        queue: f"{queue}@1" for queue in asked
    }


def test_every_queue_says_in_one_line_how_it_is_put_in_order():
    assert set(draft.ORDER) == set(draft.QUEUES)
    assert all(0 < len(words) <= 160 and words.endswith(".") for words in draft.ORDER.values())


@pytest.mark.parametrize(
    "row",
    [
        {"area_id": "syn-n9999", "qid": "syn-q1", "role": "own"},
        {"area_id": "syn-n0001", "qid": "", "role": "own"},
        {"area_id": "syn-n0001", "qid": "syn-q1", "role": "neighbour"},
    ],
)
def test_a_row_of_the_map_that_names_no_area_no_item_or_no_role_is_refused(
    tmp_path: Path, row: dict[str, str]
):
    areas = [{"area_id": "syn-n0001", "name": "Alderwick", "primary_borough": "Quillhaven"}]
    draft.write_table(tmp_path, "areas.csv", areas)
    about = {"source_id": "synthetic-items", "page_id": "4021", "title": "Alderwick"}
    draft.write_table(tmp_path, "area_sources.csv", [{**about, **row}])
    with pytest.raises(Unfit, match=r"area_sources\.csv") as refusal:
        draft.articles(Draft(tmp_path, synthetic=True))
    assert "Alderwick" not in str(refusal.value)


def test_an_area_that_another_took_the_place_of_is_not_asked_about(tmp_path: Path):
    rows = [
        {"area_id": "syn-n0001", "name": "Alderwick", "primary_borough": "Quillhaven"},
        {"area_id": "syn-n0002", "name": "Old Alderwick", "superseded_by": "syn-n0001"},
    ]
    draft.write_table(tmp_path, "areas.csv", rows)
    draft.write_table(tmp_path, "name_evidence.csv", [])
    assert [item["id"] for item in draft.names(Draft(tmp_path, True))] == ["n:syn-n0001"]


def test_a_name_that_stands_inside_two_areas_is_asked_about_in_each(tmp_path: Path):
    # Two places of one name, each a smaller place inside its own area. One was once
    # left out, and nobody would have been asked about it.
    areas = [
        {"area_id": f"syn-n000{at}", "name": name, "primary_borough": "Quillhaven"}
        for at, name in ((1, "Alderwick"), (2, "Foxholt"))
    ]
    draft.write_table(tmp_path, "areas.csv", areas)
    draft.write_table(tmp_path, "name_evidence.csv", [])
    about = {"alias": "Pellam", "kind": "inside", "source_id": "synthetic-names"}
    rows = [
        {**about, "area_id": "syn-n0001", "record_id": "syn-r0001"},
        {**about, "area_id": "syn-n0002", "record_id": "syn-r0002"},
        {**about, "alias": "Quillhaven Waterside", "kind": "wide", "area_id": "syn-n0001"},
        {**about, "alias": "Quillhaven Waterside", "kind": "wide", "area_id": "syn-n0002"},
    ]
    draft.write_table(tmp_path, "aliases.csv", rows)
    found = {item["id"]: item for item in draft.names(Draft(tmp_path, synthetic=True))}
    assert sorted(found) == [
        "a:syn-n0001:pellam",
        "a:syn-n0001:quillhaven-waterside",
        "a:syn-n0002:pellam",
        "n:syn-n0001",
        "n:syn-n0002",
    ]
    assert found["a:syn-n0001:pellam"]["preset"]["of"] == ["syn-n0001"]
    assert found["a:syn-n0002:pellam"]["preset"]["of"] == ["syn-n0002"]
    # A wide name is one item over all its areas.
    assert found["a:syn-n0001:quillhaven-waterside"]["preset"]["of"] == ["syn-n0001", "syn-n0002"]


def boroughs_of(folder: Path, order: str = "") -> Draft:
    """A draft of two boroughs, Alderwick with two areas and Foxholt with three, each area
    of one cell, with one other name in each borough. `order` is what the draft says of
    the order to look at them in."""
    squares(folder, 5)
    named = [
        {
            "area_id": f"syn-n{at:04d}",
            "name": f"Area {at}",
            "primary_borough": "Alderwick" if at <= 2 else "Foxholt",
        }
        for at in range(1, 6)
    ]
    draft.write_table(folder, "areas.csv", named)
    draft.write_table(folder, "name_evidence.csv", [])
    about = {"kind": "inside", "source_id": "synthetic-names"}
    others = [
        {**about, "alias": "Pellam", "area_id": "syn-n0002", "record_id": "syn-r0001"},
        {**about, "alias": "Osier", "area_id": "syn-n0004", "record_id": "syn-r0002"},
    ]
    draft.write_table(folder, "aliases.csv", others)
    flags = [{"queue": "borders", "item": "syn-n0003", "flag": "two_centres"}]
    draft.write_table(folder, "flags.csv", flags)
    if order:
        (folder / "order.csv").write_text(f"queue,item,rank\n{order}", encoding="utf-8")
    return Draft.open(folder, synthetic=True)


# Foxholt holds more that is at stake than Alderwick, and its fifth area the most of all.
AT_STAKE = (
    "whole,foxholt,1\nwhole,alderwick,2\n"
    "borders,syn-n0005,1\nborders,syn-n0002,2\nborders,syn-n0004,3\n"
    "borders,syn-n0003,4\nborders,syn-n0001,5\n"
)


def ids(items: list[dict[str, Any]]) -> list[str]:
    return [item["id"] for item in items]


def test_with_no_order_from_the_draft_the_boroughs_run_by_name(tmp_path: Path):
    held = boroughs_of(tmp_path)
    assert ids(draft.borders(held)) == [
        *("syn-n0001", "syn-n0002"),
        *("syn-n0003", "syn-n0004", "syn-n0005"),
    ]
    assert ids(draft.names(held)) == [
        *("n:syn-n0001", "n:syn-n0002", "a:syn-n0002:pellam"),
        *("n:syn-n0003", "n:syn-n0004", "n:syn-n0005", "a:syn-n0004:osier"),
    ]


def test_the_borough_with_most_at_stake_comes_first_and_is_finished_before_the_next(
    tmp_path: Path,
):
    held = boroughs_of(tmp_path, AT_STAKE)
    # In a borough a flagged border comes first, and then the most at stake.
    assert ids(draft.borders(held)) == [
        *("syn-n0003", "syn-n0005", "syn-n0004"),
        *("syn-n0002", "syn-n0001"),
    ]
    # Names run in the same order. The other names of a borough come after its areas,
    # and before the next borough.
    assert ids(draft.names(held)) == [
        *("n:syn-n0005", "n:syn-n0004", "n:syn-n0003", "a:syn-n0004:osier"),
        *("n:syn-n0002", "n:syn-n0001", "a:syn-n0002:pellam"),
    ]
    assert ids(draft.whole(held)) == ["foxholt", "alderwick"]


def test_what_the_draft_does_not_place_comes_after_what_it_does(tmp_path: Path):
    held = boroughs_of(tmp_path, "whole,foxholt,1\nborders,syn-n0004,1\n")
    assert ids(draft.borders(held)) == [
        *("syn-n0003", "syn-n0004", "syn-n0005"),
        *("syn-n0001", "syn-n0002"),
    ]


@pytest.mark.parametrize(
    ("order", "refusal"),
    [
        ("borders,syn-n0001,first\n", "order.csv gives a place that is no whole number"),
        ("borders,syn-n0001,0\n", "order.csv gives a place that is no whole number"),
        ("streets,syn-n0001,1\n", "order.csv names a queue the desk does not have"),
        ("borders,syn-n0001,1\nborders,syn-n0001,2\n", "order.csv places an item twice"),
    ],
)
def test_an_order_that_is_not_as_the_design_gives_it_is_refused(
    tmp_path: Path, order: str, refusal: str
):
    with pytest.raises(Unfit, match=refusal):
        draft.borders(boroughs_of(tmp_path, order))


def test_before_any_border_is_drawn_an_area_holds_only_the_names_given_to_it(tmp_path: Path):
    # A draft of names alone has no ground to take. An area may then be turned down at
    # the desk, once no other name is given to it.
    areas = [
        {"area_id": f"syn-n000{at}", "name": name, "primary_borough": "Quillhaven"}
        for at, name in ((1, "Alderwick"), (2, "Foxholt"))
    ]
    draft.write_table(tmp_path, "areas.csv", areas)
    draft.write_table(tmp_path, "name_evidence.csv", [])
    other = {"alias": "Pellam", "kind": "inside", "source_id": "synthetic-names"}
    draft.write_table(tmp_path, "aliases.csv", [{**other, "area_id": "syn-n0002"}])
    found = {item["id"]: item["preset"] for item in draft.names(Draft(tmp_path, synthetic=True))}
    assert "holds" not in found["n:syn-n0001"]
    assert found["n:syn-n0002"]["holds"] == "names"
    assert "holds" not in found["a:syn-n0002:pellam"]


def test_evidence_of_a_kind_the_design_does_not_name_is_refused():
    row = {"evidence": "margin=7;second=syn-n0012;ward=Foxholt"}
    assert draft.evidence_of(row) == {"margin": "7", "second": "syn-n0012", "ward": "Foxholt"}
    for unfit in ("income=low", "margin=7;tenure=rented", "a note in words"):
        with pytest.raises(Unfit, match="gives evidence that is not one of"):
            draft.evidence_of({"evidence": unfit})


def squares(folder: Path, areas: int) -> None:
    """A draft of a row of areas, each one cell, each beside the next."""
    cells = [
        {
            "type": "Feature",
            "id": f"syn-oa{at:04d}",
            "properties": {"area": f"syn-n{at:04d}", "colour": at % 12, "borough": "Quillhaven"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[at, 0], [at + 1, 0], [at + 1, 1], [at, 1], [at, 0]]],
            },
        }
        for at in range(1, areas + 1)
    ]
    about = {
        "layer": "cells",
        "group": "quillhaven",
        "source_ids": ["synthetic"],
        "synthetic": True,
    }
    (folder / "layers" / "quillhaven").mkdir(parents=True)
    (folder / "layers" / "quillhaven" / "cells.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "desk": about, "features": cells}),
        encoding="utf-8",
    )
    named = [
        {"area_id": f"syn-n{at:04d}", "name": f"Area {at}", "primary_borough": "Quillhaven"}
        for at in range(1, areas + 1)
    ]
    draft.write_table(folder, "areas.csv", named)
    draft.write_table(
        folder,
        "oa_to_area.csv",
        [{"oa21cd": f"syn-oa{at:04d}", "area_id": f"syn-n{at:04d}"} for at in range(1, areas + 1)],
    )


def figures_of(folder: Path, values: list[str], **more: list[str]) -> dict[str, list[str]]:
    """The flags of each figure of a row of areas, given the figure of each in turn."""
    squares(folder, len(values))
    rows = [
        {
            "area_id": f"syn-n{at:04d}",
            "feature_id": "green_cover",
            "value": value,
            "unit": "%",
            "source_id": "synthetic",
            "vintage": "2025",
            "flag": more.get("flag", [""] * len(values))[at - 1],
        }
        for at, value in enumerate(values, 1)
    ]
    draft.write_table(folder, "figures.csv", rows)
    if "before" in more:
        was = [{**row, "value": value} for row, value in zip(rows, more["before"], strict=True)]
        draft.write_table(folder, "figures_before.csv", was)
    found = draft.figures(Draft.open(folder, synthetic=True))
    return {item["preset"]["area_id"][-1]: item["flags"] for item in found}


LEVEL = ["10", "11", "12", "13", "14", "15", "16", "17", "18"]


def test_a_figure_far_from_every_neighbour_is_picked(tmp_path: Path):
    values = [*LEVEL[:4], "40", *LEVEL[5:]]
    assert figures_of(tmp_path, values) == {"5": ["far_from_neighbours"]}


def test_a_figure_that_rises_as_its_neighbours_do_is_not_picked(tmp_path: Path):
    assert figures_of(tmp_path, LEVEL) == {}


def test_a_figure_is_not_compared_with_one_neighbour_alone(tmp_path: Path):
    assert figures_of(tmp_path, ["90", *LEVEL[1:]]) == {}


def test_a_figure_that_moved_by_a_fifth_since_the_release_before_is_picked(tmp_path: Path):
    before = ["10", "11", "10", "13", "14", "15", "16", "17", "0"]
    assert figures_of(tmp_path, LEVEL, before=before) == {
        "3": ["moved_between_releases"],
        "9": ["moved_between_releases"],
    }


def test_a_zero_is_picked_where_the_report_says_cover_is_thin(tmp_path: Path):
    values = ["0", "0", *LEVEL[2:]]
    flag = ["partial", "", "partial", *[""] * 6]
    assert figures_of(tmp_path, values, flag=flag) == {"1": ["zero_thin_cover"]}


def test_a_figure_with_no_evidence_behind_it_is_picked_as_the_pipeline_names_it(tmp_path: Path):
    flag = ["no_record", "fact_has_a_row", "present", "partial no_record", *[""] * 5]
    found = figures_of(tmp_path, LEVEL, flag=flag)
    assert found == {"1": ["no_evidence"], "2": ["no_evidence"], "4": ["no_evidence"]}


def test_a_sample_is_large_enough_to_be_right_to_within_ten_in_a_hundred():
    assert draft.sample_size(10**9) == 97
    assert [draft.sample_size(n) for n in (0, 1, 6, 14, 120, 1000)] == [0, 1, 6, 13, 54, 88]
    for records in (2, 14, 97, 120, 1000, 100_000):
        drawn = draft.sample_size(records)
        # The widest the doubt can be: half the records are the kind, and half are not.
        spread = math.sqrt(0.25 / drawn * (records - drawn) / (records - 1))
        assert draft.SURE * spread <= draft.WITHIN + 1e-9, records
        assert draft.sample_size(records) <= records


# What an item is


def test_a_name_in_lower_case_with_hyphens_is_a_slug():
    assert draft.slug("Dulcimer Green") == "dulcimer-green"
    assert draft.slug(" St. Foxholt's-on-the-Hill ") == "st-foxholt-s-on-the-hill"
    assert draft.slug("community_hall") == "community-hall"


def test_the_revision_of_an_item_is_of_what_is_shown_and_not_of_itself():
    item: dict[str, Any] = {"id": "n:syn-n0004", "title": "Dulcimer Green", "picks": ["Dulcimer"]}
    rev = draft.revision(item)
    assert len(rev) == 12 and int(rev, 16) >= 0
    assert draft.revision({**item, "rev": rev}) == rev
    assert (
        draft.revision({"picks": ["Dulcimer"], "title": "Dulcimer Green", "id": "n:syn-n0004"})
        == rev
    )
    assert draft.revision({**item, "title": "Dulcimer"}) != rev


def test_a_number_is_written_as_a_person_writes_it():
    assert [draft.plain(value) for value in (290.0, 21.4, 0.0, 1060000.0, 0.1335)] == [
        "290",
        "21.4",
        "0",
        "1060000",
        "0.1335",
    ]


# Kinds of venue, and claims


def venues(kind: str, count: int) -> list[dict[str, str]]:
    return [
        {
            "record_id": f"syn-v{at:04d}",
            "source_id": "synthetic",
            "kind": kind,
            "name": f"Foxholt Made-up Venue {at}",
        }
        for at in range(1, count + 1)
    ]


def test_the_same_records_are_drawn_whatever_order_the_file_is_in(tmp_path: Path):
    rows = venues("cafe", 300)
    draft.write_table(tmp_path / "one", "kinds.csv", rows)
    draft.write_table(tmp_path / "two", "kinds.csv", reversed(rows))
    one = [item["id"] for item in draft.kinds(Draft(tmp_path / "one", True))]
    two = [item["id"] for item in draft.kinds(Draft(tmp_path / "two", True))]
    assert one == two and len(one) == draft.sample_size(300) == 73
    assert one != sorted(one), "the sample is not the first records of the file"


def test_a_kind_with_few_records_is_read_whole(tmp_path: Path):
    draft.write_table(tmp_path, "kinds.csv", venues("library", 6))
    assert len(draft.kinds(Draft(tmp_path, True))) == 6


def claim(name: str, status: str) -> dict[str, Any]:
    return {
        "claim_id": name,
        "area_id": "syn-n0001",
        "kind": "history",
        "quote": "The station at Alderwick opened in 1907.",
        "thing": None,
        "source_id": "synthetic",
        "title": "Alderwick",
        "url": "",
        "page_id": 4021,
        "revision_id": 88213,
        "section": "History",
        "has_reference": True,
        "review": {"status": status},
    }


def test_a_claim_that_was_decided_before_is_not_asked_again(tmp_path: Path):
    rows = [claim("syn-c000000000001", "accepted"), claim("syn-c000000000002", "rejected")]
    draft.write_lines(tmp_path, "claims.jsonl", [*rows, claim("syn-c000000000003", "pending")])
    assert [item["id"] for item in draft.claims(Draft(tmp_path, True))] == ["syn-c000000000003"]


def test_a_claim_is_shown_with_the_sentence_each_side_where_the_page_is_held(tmp_path: Path):
    said = ("Alderwick is a district.", "The station at Alderwick opened in 1907.", "It closed.")
    page = [
        {
            "page_id": 4021,
            "revision_id": 88213,
            "title": "Alderwick",
            "section": "",
            "sentence": at,
            "text": text,
        }
        for at, text in enumerate(said, 1)
    ]
    draft.write_lines(tmp_path, "claims.jsonl", [claim("syn-c000000000003", "pending")])
    (item,) = draft.claims(Draft(tmp_path, True))
    assert item["text"] == {"before": "", "body": said[1], "after": ""}
    draft.write_lines(tmp_path, "claim_sentences.jsonl", page)
    (item,) = draft.claims(Draft(tmp_path, True))
    assert item["text"] == {"before": said[0], "body": said[1], "after": said[2]}
