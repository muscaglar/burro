"""The curated files of a draft: what each row holds, and that each says it is a draft.

Nothing here is real. `draft_support.py` makes the whole draft of the made-up
town once, and these read what it wrote.
"""

import json
import re
from pathlib import Path

import pytest
from burro_core.ids import AREA_ID_PATTERN, SLUG_PATTERN
from burro_pipeline.areas import draft_files
from burro_pipeline.areas.draft_files import (
    ALIASES,
    AREAS,
    COLUMNS,
    EVIDENCE,
    GIVEN,
    MORE,
    OF_THE_DESIGN,
    RELATIONS,
    SNAPSHOTS,
    STATE,
    slugs_of,
)
from burro_pipeline.areas.draft_marks import desk_slug

from . import names_support as town
from .draft_support import Made, made

DESK = Path("desk") / "draft"
# Words that would say who lives somewhere. No column of a draft is named for one.
ABOUT_RESIDENTS = re.compile(
    r"resident|people|population|person|age|ethnic|religio|income|depriv|price|rent|tenure|home"
)
LOCATES_IN = ("point_inside", "polygon_overlap")


@pytest.fixture(scope="module")
def draft() -> Made:
    return made()


# Each row says what it is


@pytest.mark.parametrize("name", OF_THE_DESIGN)
def test_a_curated_file_holds_the_columns_of_the_design_and_then_its_state(draft: Made, name: str):
    assert draft.columns(name) == (*COLUMNS[name], *MORE.get(name, ()), "state")
    assert draft.columns(name)[: len(COLUMNS[name])] == COLUMNS[name]


def test_every_area_and_every_other_name_says_whether_it_rests_on_a_file_with_no_receipt(
    draft: Made,
):
    """The town centres have no receipt. What rests on them says so in its own row."""
    seeds = {row["area_id"]: row["no_receipt"] for row in draft.rows("made/names/places.csv")}
    areas = {row["area_id"]: row["no_receipt"] for row in draft.rows(AREAS)}
    assert areas == {area: seeds[area] for area in areas}
    assert set(areas.values()) == {"true"}
    others = {row["alias"]: row["no_receipt"] for row in draft.rows(ALIASES)}
    # Eskerfold has no town centre near it, and no ward. Pellam Cross is a town centre.
    assert (others["Eskerfold"], others["Pellam Cross"]) == ("false", "true")
    counted = json.loads((draft.out / "counts.json").read_bytes())["naming"]
    assert counted["areas_that_rest_on_a_file_with_no_receipt"] == len(areas)


def test_an_area_says_every_borough_it_lies_in_and_whether_its_main_borough_is_a_tie(
    draft: Made,
):
    """The design asks for the borough with most of an area's homes. The draft counts
    output areas, and says so where two boroughs hold as many as each other."""
    areas = {row["area_id"]: row for row in draft.rows(AREAS)}
    assert areas["lon-n0009"]["boroughs"] == "Tallowgate: 5; Quillhaven: 4"
    assert areas["lon-n0001"]["boroughs"] == "Quillhaven: 10"
    assert {row["borough_is_a_tie"] for row in areas.values()} == {"false"}
    for row in areas.values():
        assert row["boroughs"].startswith(f"{row['primary_borough']}: ")
    assert draft_files.is_a_tie({"E09000901": 14, "E09000902": 14, "E09000903": 2})
    assert not draft_files.is_a_tie({"E09000901": 14, "E09000902": 13})
    assert not draft_files.is_a_tie({"E09000901": 14})


def test_the_largest_areas_are_listed_with_the_other_names_that_lie_in_each(draft: Made):
    rows = draft.rows("largest_areas.csv")
    assert draft.columns("largest_areas.csv") == draft_files.LARGEST_COLUMNS
    sizes = [int(row["output_areas"]) for row in rows]
    assert sizes == sorted(sizes, reverse=True) and sizes[0] == 10
    assert [row["rank"] for row in rows] == [str(at) for at in range(1, len(rows) + 1)]
    first = rows[0]
    assert (first["area_id"], first["other_names_inside"], first["places_inside"]) == (
        "lon-n0001",
        "1",
        "Foxholt",
    )
    given = [row["area_id"] for row in draft.rows(GIVEN)]
    assert all(int(row["output_areas"]) == given.count(row["area_id"]) for row in rows)


def test_a_row_of_evidence_says_how_its_label_writes_the_name_and_how_far_off_it_lies(
    draft: Made,
):
    rows = draft.rows(EVIDENCE)
    assert {row["match"] for row in rows} == {"same", "part"}
    for row in rows:
        assert row["letter_for_letter"] == ("true" if row["as_written"] == row["name"] else "false")
        assert (row["metres_outside"] != "") == (row["locates"] == "label_only"), row
        assert 0.0 <= float(row["share"]) <= 1.0
    # A ward writes a name with the publisher's word for a ward after it.
    ward = next(row for row in rows if row["as_written"] == "Alderwick Ward")
    assert (ward["match"], ward["letter_for_letter"]) == ("same", "false")
    outside = [row for row in rows if row["locates"] == "label_only"]
    assert all(float(row["metres_outside"]) >= 0 for row in outside)
    counted = json.loads((draft.out / "counts.json").read_bytes())["naming"]
    assert (
        counted["areas_whose_name_two_publishers_write_letter_for_letter"]
        <= counted["areas_whose_name_two_publishers_write"]
    )


@pytest.mark.parametrize("name", OF_THE_DESIGN)
def test_every_row_says_it_is_a_draft_made_by_method_and_checked_by_nobody(draft: Made, name: str):
    rows = draft.rows(name)
    assert {row["state"] for row in rows} <= {STATE}
    assert rows or name == RELATIONS
    assert STATE == "draft, made by method, checked by nobody"


def test_no_row_says_that_a_person_decided_or_chose_anything(draft: Made):
    # A name that stands by the rule on one official publisher says so. No person read
    # it, so it does not say that its name was checked.
    assert {row["review_state"] for row in draft.rows(AREAS)} == {"drafted", "named_by_rule"}
    assert {row["superseded_by"] for row in draft.rows(AREAS)} == {""}
    given = draft.rows(GIVEN)
    assert {row["basis"] for row in given} == {"auto"}
    assert {(row["decided_by"], row["decided_on"], row["reason"]) for row in given} == {("",) * 3}
    assert {(row["chosen_by"], row["chosen_on"]) for row in draft.rows(EVIDENCE)} == {("", "")}


def test_every_file_that_was_read_is_listed_with_its_hash_and_says_whether_it_has_a_receipt(
    draft: Made,
):
    held = json.loads((draft.out / SNAPSHOTS).read_bytes())
    assert {each["state"] for each in held} == {STATE}
    by_source = {(each["source_id"], each["version"]): each for each in held}
    assert {source for source, _ in by_source} == {
        *(town.NAMES, town.CENTRES, town.LINE, town.ROADS, town.OUTLINES, town.LOOKUP),
        "ons-oa-pwc-2021",
    }
    for each in held:
        assert re.fullmatch(r"[0-9a-f]{64}", each["sha256"]) and each["bytes"] > 0
    [without] = [each for each in held if not each["has_receipt"]]
    assert without["source_id"] == town.CENTRES
    # Nothing is put in the place of what the publisher does not state.
    assert (without["url"], without["retrieved_on"], without["version"]) == ("", "", "")
    assert without["sha256"] == town.sha256_of("centres")


# The files fit together


def test_every_output_area_is_in_exactly_one_area_and_every_row_names_an_area_that_stands(
    draft: Made,
):
    given = draft.rows(GIVEN)
    cells = [row["oa21cd"] for row in given]
    assert sorted(cells) == sorted(town.oa(square) for square in town.LONDON)
    assert len(set(cells)) == len(cells)
    areas = [row["area_id"] for row in draft.rows(AREAS)]
    assert len(set(areas)) == len(areas) == draft.counted["areas"]
    assert {row["area_id"] for row in given} == set(areas)
    assert all(re.fullmatch(AREA_ID_PATTERN, area) for area in areas)


def test_every_name_of_an_area_rests_on_a_checked_record_that_puts_it_inside(draft: Made):
    """Section 6 of the design: one record that puts the name on the map, inside the area."""
    evidence = draft.rows(EVIDENCE)
    assert {row["checked"] for row in evidence} == {"true"}
    for area in draft.rows(AREAS):
        rows = [
            row
            for row in evidence
            if (row["area_id"], row["name"], row["role"])
            == (area["area_id"], area["name"], "primary")
        ]
        assert rows, area["area_id"]
        assert any(row["locates"] in LOCATES_IN for row in rows), area["area_id"]
        assert all(re.fullmatch(r"[0-9a-f]{64}", row["snapshot_sha256"]) for row in rows)


def test_every_other_name_that_is_not_wide_has_a_record_that_lies_inside_its_area(draft: Made):
    evidence = draft.rows(EVIDENCE)
    others = draft.rows(ALIASES)
    assert {row["kind"] for row in others} == {"inside", "same_ground", "wide"}
    for other in others:
        rows = [
            row
            for row in evidence
            if (row["area_id"], row["name"]) == (other["area_id"], other["alias"])
            and row["role"] != "primary"
        ]
        assert rows, other["alias"]
        assert {row["role"] for row in rows} == {"wide" if other["kind"] == "wide" else "alias"}
        if other["kind"] != "wide":
            assert any(row["locates"] in LOCATES_IN for row in rows), other["alias"]


def test_a_name_is_written_as_its_publisher_writes_it_and_never_changed(draft: Made):
    written = {record.name for record in town.PLACES} | {each.name for each in town.TOWN_CENTRES}
    written |= {record.second for record in town.PLACES if record.second}
    offered = {row["name"] for row in draft.rows(AREAS)}
    offered |= {row["alias"] for row in draft.rows(ALIASES)}
    assert offered <= written
    for row in draft.rows(EVIDENCE):
        assert row["as_written"] in written | {ward.name for ward in town.WARDS}


def test_the_borough_of_an_area_is_the_one_that_holds_most_of_its_output_areas(draft: Made):
    borough_of = {
        town.oa(square): town.BOROUGH_NAMES[town.borough_of(square)] for square in town.LONDON
    }
    held: dict[str, list[str]] = {}
    for row in draft.rows(GIVEN):
        held.setdefault(row["area_id"], []).append(borough_of[row["oa21cd"]])
    for area in draft.rows(AREAS):
        inside = held[area["area_id"]]
        most = max(sorted(set(inside)), key=inside.count)
        assert inside.count(area["primary_borough"]) == inside.count(most), area["area_id"]


# Slugs


def test_a_slug_is_the_name_in_lower_case_with_hyphens_and_none_is_there_twice(draft: Made):
    slugs = [row["slug"] for row in draft.rows(AREAS)]
    assert len(set(slugs)) == len(slugs)
    assert all(re.fullmatch(SLUG_PATTERN, slug) for slug in slugs)


def test_two_areas_of_one_name_have_the_borough_added_and_an_area_with_no_name_has_no_slug():
    names = {"lon-n0001": "Farrowmere", "lon-n0002": "Farrowmere", "lon-n0003": "Pellam Cross"}
    names |= {"lon-n0004": "", "lon-n0005": "Farrowmere"}
    boroughs = dict.fromkeys(names, "Tallowgate") | {"lon-n0001": "Quillhaven"}
    assert slugs_of(names, boroughs) == {
        "lon-n0001": "farrowmere-quillhaven",
        "lon-n0002": "farrowmere-tallowgate",
        "lon-n0003": "pellam-cross",
        "lon-n0005": "farrowmere-tallowgate-2",
    }


# What the review desk reads


def test_the_desk_is_handed_the_same_rows_under_the_columns_of_the_design_and_no_other(
    draft: Made,
):
    for name in (AREAS, GIVEN, ALIASES, EVIDENCE):
        assert draft.columns(str(DESK / name)) == COLUMNS[name]
        ours = [
            {k: v for k, v in row.items() if k in COLUMNS[name]}
            for row in draft.rows(name)
            if name != EVIDENCE or row["source_id"] != town.LINE
        ]
        assert draft.rows(str(DESK / name)) == ours, name
    assert draft.columns(str(DESK / "flags.csv")) == ("queue", "item", "flag")


def test_the_label_of_a_ward_is_never_offered_to_the_desk_as_the_spelling_of_a_name(
    draft: Made,
):
    """The desk offers every form a row of evidence writes as a spelling to choose. The
    design gives the order of spelling: Ordnance Survey's names, then the town centres. A
    ward is not in it, and its label ends with the publisher's word for a ward."""
    ours = draft.rows(EVIDENCE)
    wards = [row for row in ours if row["source_id"] == town.LINE]
    assert wards and all(row["as_written"] != row["name"] for row in wards)
    desk = draft.rows(str(DESK / EVIDENCE))
    assert desk and not [row for row in desk if row["source_id"] == town.LINE]
    # What may be chosen at the desk is the name, or a form a publisher of names wrote.
    assert {row["source_id"] for row in desk} == {town.NAMES, town.CENTRES}
    # The flags and the layers read every row: a ward still says who writes a name.
    assert [{k: v for k, v in row.items() if k in COLUMNS[EVIDENCE]} for row in ours] == draft.rows(
        "made/draft/name_evidence.csv"
    )


def test_every_flag_of_a_name_is_on_an_item_the_desk_makes_of_the_draft(draft: Made):
    """The desk names an item `n:` and an area, or `a:`, an area and the name as a slug."""
    items = {f"n:{row['area_id']}" for row in draft.rows(str(DESK / AREAS))}
    first: dict[tuple[str, str], str] = {}
    for row in draft.rows(str(DESK / ALIASES)):
        key = (row["alias"], row["kind"] if row["kind"] == "wide" else row["area_id"])
        first.setdefault(key, row["area_id"])
    items |= {f"a:{area}:{desk_slug(alias)}" for (alias, _), area in first.items()}
    flags = [row for row in draft.rows(str(DESK / "flags.csv")) if row["queue"] == "names"]
    assert flags and {row["item"] for row in flags} <= items
    assert {row["flag"] for row in flags} <= {
        "one_publisher",
        "same_name_elsewhere",
        "describes_residents",
        "look_hard",
    }
    borders = [row for row in draft.rows(str(DESK / "flags.csv")) if row["queue"] == "borders"]
    assert {row["item"] for row in borders} <= {row["area_id"] for row in draft.rows(AREAS)}


def test_what_stands_beside_a_border_is_said_in_the_keys_the_desk_knows(draft: Made):
    keys = {
        part.split("=", 1)[0]
        for row in draft.rows(str(DESK / GIVEN))
        for part in row["evidence"].split(";")
        if part
    }
    assert keys <= {"margin", "second", "roads", "ward", "msoa", "centre"}


# For a person's eyes


def test_every_area_has_a_row_that_says_which_name_is_offered_first_and_who_writes_it(
    draft: Made,
):
    rows = draft.rows(draft_files.AREA_NAMES)
    first = {row["area_id"]: row for row in rows if row["offered"] == "first"}
    assert set(first) == {row["area_id"] for row in draft.rows(AREAS)}
    for area in draft.rows(AREAS):
        assert first[area["area_id"]]["name"] == area["name"]
        assert first[area["area_id"]]["publishers_writing"]
    others = [(row["area_id"], row["name"]) for row in rows if row["offered"] == "other"]
    assert sorted(others) == sorted((row["area_id"], row["alias"]) for row in draft.rows(ALIASES))


def test_no_column_of_any_file_is_about_who_lives_anywhere(draft: Made):
    for path in sorted(draft.out.rglob("*.csv")):
        for column in draft.columns(str(path.relative_to(draft.out))):
            assert not ABOUT_RESIDENTS.search(column.replace("publisher", "")), (path.name, column)
