"""Candidate names: what is one place, what a label holds, and where a record lies.

Every name here is made up, and every file is in the publisher's own layout.
"""

import pytest
from burro_pipeline.areas import names_candidates, names_centres, names_wards
from burro_pipeline.areas.names_candidates import Candidates, Match, Place, fold, match, parts

from ..cells.support import CANARY
from .names_support import (
    CENTRE_OF_ALDERWICK,
    CENTRE_OF_WEXMOOR,
    CENTRES,
    HIGH_STREET,
    LINE,
    NAMES,
    OF_TWO_NAMES,
    PLACES,
    QUILLHAVEN,
    TALLOWGATE,
    TOWN_CENTRES,
    WARDS,
    held,
    oa,
)

WARD_ENDS = names_candidates.ENDINGS[names_wards.SOURCE]
CENTRE_ENDS = names_candidates.ENDINGS[names_centres.SOURCE]


def found() -> Candidates:
    read = held()
    return names_candidates.join(
        read.london, read.names, read.centres, read.wards, read.boroughs, read.files
    )


def place(name: str, kind: str | None = None) -> Place:
    same = [each for each in found().places if each.name == name and kind in (None, each.key.kind)]
    assert len(same) == 1
    return same[0]


# What a label holds


@pytest.mark.parametrize(
    ("name", "label", "endings", "how"),
    [
        ("Alderwick", "Alderwick", (), Match.SAME),
        ("Alderwick", "ALDERWICK", (), Match.SAME),
        ("Foxholt's End", "Foxholts End", (), Match.SAME),
        ("Foxholt\N{RIGHT SINGLE QUOTATION MARK}s End", "Foxholt's End", (), Match.SAME),
        ("Alderwick & Foxholt", "Alderwick and Foxholt", (), Match.SAME),
        ("Alderwick", "Alderwick Ward", WARD_ENDS, Match.SAME),
        ("Quillhaven", "Quillhaven London Boro", WARD_ENDS, Match.SAME),
        ("Alderwick", "Alderwick Town Centre", CENTRE_ENDS, Match.SAME),
        ("Alderwick", "Alderwick District Centre", CENTRE_ENDS, Match.SAME),
        # A word for a kind is left out only where the publisher's own file uses it so.
        ("Alderwick", "Alderwick Ward", (), Match.HELD),
        ("Cindermoor", "Brackenhythe & Cindermoor Ward", WARD_ENDS, Match.PART),
        ("Cindermoor", "Grapnel Dock/ Cindermoor", CENTRE_ENDS, Match.PART),
        ("Cindermoor", "Cindermoor (part)", (), Match.PART),
        ("Cindermoor", "Cindermoor, Quillhaven", (), Match.PART),
        ("Cindermoor", "Wexmoor - Cindermoor", (), Match.PART),
        ("Grapnel Dock", "Grapnel Dock and Cindermoor/ Wexmoor", (), Match.PART),
        ("Kindlewharf", "Kindlewharf High Street", CENTRE_ENDS, Match.HELD),
        ("Kindlewharf", "North Kindlewharf Ward", WARD_ENDS, Match.HELD),
        ("Kindlewharf High Street", "Kindlewharf", (), Match.HOLDS),
        # Whole words only: a name is not found inside a longer word.
        ("Alder", "Alderwick", (), None),
        ("Wick", "Alderwick Ward", WARD_ENDS, None),
        ("Alderwick", "Foxholt", (), None),
        ("", "Alderwick", (), None),
    ],
)
def test_a_label_writes_a_name_or_holds_it_or_does_neither(
    name: str, label: str, endings: tuple[str, ...], how: Match | None
):
    assert match(name, label, endings) == how


def test_a_fold_is_for_comparing_and_leaves_no_mark_on_the_name():
    written = "St Marrowfen's-under-Larkspur"
    assert fold(written) == "st marrowfens under larkspur"
    assert written == "St Marrowfen's-under-Larkspur"
    assert parts("Alderwick") == ()
    assert parts("Grapnel Dock/ Cindermoor") == ("grapnel dock", "cindermoor")


# What is one place


def test_every_record_of_every_file_is_a_candidate_as_its_publisher_writes_it():
    records = found().records
    written = {(record.source_id, record.as_written) for record in records}
    assert {name for source, name in written if source == NAMES} == {
        each.name for each in PLACES if each.name != "Gorsebeck"
    }
    assert {name for source, name in written if source == CENTRES} == {
        each.name for each in TOWN_CENTRES
    }
    assert {name for source, name in written if source == LINE} >= {
        each.name for each in WARDS if each.kind == "LBW"
    }
    assert {record.publisher for record in records} == {
        "Ordnance Survey",
        "Greater London Authority",
    }
    assert CANARY not in " ".join(record.as_written for record in records)


def test_a_record_says_the_file_it_came_from_and_whether_that_file_has_a_receipt():
    for record in found().records:
        assert record.file.file_id.startswith("f-") and len(record.file.sha256) == 64
        assert record.file.has_receipt == (record.source_id != CENTRES)


def test_a_place_outside_london_is_left_out_and_counted():
    assert "Gorsebeck" not in {each.name for each in found().places}
    assert "Osierholm" not in {station.as_written for station in found().stations}
    assert found().outside == {
        "os-open-names:populatedPlace": 1,
        "os-open-names:Railway Station": 1,
        CENTRES: 0,
    }


def test_the_borough_of_a_record_is_the_borough_of_its_output_area_and_not_what_it_writes():
    assert place("Alderwick").key.borough == QUILLHAVEN
    assert place("Farrowmere", "Village").key.borough == TALLOWGATE
    assert place("Alderwick").key.cell == oa((1, 1))


def test_a_point_on_the_line_between_two_output_areas_goes_to_the_code_that_sorts_first():
    on_the_line = place("Thrushcombe")
    assert held().london.ground.holding(on_the_line.at) == (oa((1, 3)), oa((2, 3)))
    assert on_the_line.key.cell == oa((1, 3))


def test_a_town_centre_of_the_same_name_within_a_kilometre_is_the_same_place():
    alderwick = place("Alderwick")
    assert alderwick.publishers == ("Greater London Authority", "Ordnance Survey")
    centre = alderwick.written_by(CENTRES)
    assert [(each.candidate.record_id, each.match, each.metres) for each in centre] == [
        (CENTRE_OF_ALDERWICK, Match.SAME, 0.0)
    ]
    assert "Alderwick" not in {each.name for each in found().places if each.centre is not None}


def test_a_town_centre_in_the_box_of_its_place_is_the_same_place_however_far_and_says_so():
    wexmoor = place("Wexmoor")
    (centre,) = wexmoor.written_by(CENTRES)
    assert (centre.candidate.record_id, centre.match) == (CENTRE_OF_WEXMOOR, Match.SAME)
    assert centre.metres == 1_150.0 and centre.beyond
    assert wexmoor.publishers == ("Greater London Authority", "Ordnance Survey")


def test_a_town_centre_with_a_name_of_its_own_is_a_place_that_one_publisher_writes():
    alone = {each.name: each for each in found().places if each.centre is not None}
    assert set(alone) == {
        "Kindlewharf High Street",
        "Pellam Cross",
        "Grapnel Dock/ Cindermoor",
        "Osierholm",
    }
    assert all(each.publishers == ("Greater London Authority",) for each in alone.values())
    assert all(each.record is None and each.roads == 0 for each in alone.values())


def test_a_label_of_several_names_writes_each_and_a_label_that_holds_a_name_does_not():
    cindermoor = place("Cindermoor")
    assert [(each.candidate.record_id, each.match) for each in cindermoor.written_by(CENTRES)] == [
        (OF_TWO_NAMES, Match.PART)
    ]
    assert cindermoor.publishers == ("Greater London Authority", "Ordnance Survey")
    kindlewharf = place("Kindlewharf")
    assert [(each.candidate.record_id, each.match) for each in kindlewharf.written_by(CENTRES)] == [
        (HIGH_STREET, Match.HELD)
    ]
    assert kindlewharf.publishers == ("Ordnance Survey",)


def test_two_files_of_one_publisher_are_one_publisher():
    """A ward that writes a name is Ordnance Survey's, as the place is."""
    alderwick = place("Alderwick")
    assert [each.candidate.as_written for each in alderwick.written_by(LINE)] == ["Alderwick Ward"]
    assert alderwick.publishers.count("Ordnance Survey") == 1


def test_a_ward_is_beside_a_place_only_within_a_kilometre_of_it():
    assert place("Foxholt").written_by(LINE) == ()
    assert [each.match for each in place("Cindermoor").written_by(LINE)] == [Match.PART]


def test_the_same_name_in_two_places_is_two_places():
    same = [each for each in found().places if each.name == "Farrowmere"]
    assert sorted(each.key.borough for each in same) == [QUILLHAVEN, TALLOWGATE]
    assert len({each.key.record_id for each in same}) == 2


def test_a_ward_is_never_a_place_of_its_own():
    assert not {each.key.source_id for each in found().places} & {LINE}
    assert len(found().places) == 14


def test_a_place_knows_how_many_roads_give_it_as_their_settlement():
    assert place("Alderwick").roads == 60
    assert place("Foxholt").roads == 10
    # Three roads write the name of Cindermoor and give the address of Eskerfold.
    assert (place("Eskerfold").roads, place("Cindermoor").roads) == (3, 0)


def test_the_same_files_give_the_same_places_in_the_same_order():
    assert found() == found()
    assert [each.key.key for each in found().places] == sorted(
        each.key.key for each in found().places
    )
