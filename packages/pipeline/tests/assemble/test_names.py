"""The name each area of a build bears, chosen from a made-up draft of names.

Nothing here is real: the town and its names are made up, and every name is
one the synthetic release already holds.
"""

import dataclasses
from collections.abc import Mapping
from pathlib import Path

import pytest
from burro_core.ids import NameState
from burro_pipeline.assemble import names
from burro_pipeline.assemble.names import Bears, NamesError, Naming
from burro_pipeline.evidence.lock import Lock, locked

from ..cells.support import registry
from .names_support import (
    ALDERWICK,
    CENTRES,
    CENTRES_OF,
    ESKERFOLD,
    EVIDENCE,
    FOUNDER,
    FOXHOLT,
    GIVEN,
    NEIGHBOURHOODS,
    NO_NAME,
    PLACES,
    WARDS,
    Wrote,
    areas,
    cells,
    files,
    receipts,
    table,
)

ONE, TWO, THREE = "lon-ne02999001", "lon-ne02999002", "lon-ne02999003"
COMMIT = "0" * 40


def named(given: Mapping[str, bytes] | None = None, lock: Lock | None = None) -> Naming:
    drafted = files() if given is None else given
    return names.build(drafted, areas(), cells(), CENTRES_OF, receipts(), lock, registry())


def shown(found: Naming) -> dict[str, str]:
    return {area: borne.name for area, borne in found.bears.items()}


def lock_of(drafted: Mapping[str, bytes], *, without: str = "") -> Lock:
    """A lock that names the files of a build: those of the draft, and those that write a name."""
    held = [
        *names.to_lock(drafted),
        *(locked(receipt) for receipt in receipts() if receipt.source_id != without),
    ]
    return Lock(
        release_id="lon-2026-09-23-01",
        built_at="2026-09-23T00:00:00Z",
        commit=COMMIT,
        inputs=tuple(sorted(held, key=lambda given: given.name)),
    )


# Which name an area bears


def test_an_area_bears_the_name_of_the_neighbourhood_that_holds_most_of_its_output_areas():
    found = named()
    # Eskerfold holds three of the four output areas of the third area, and Foxholt one.
    assert found.bears[THREE].written.name == "Eskerfold"
    assert (found.bears[THREE].held, found.bears[THREE].of) == (3, 4)
    assert (found.bears[ONE].held, found.bears[ONE].of) == (4, 4)


def test_of_two_neighbourhoods_that_hold_as_many_the_one_whose_id_sorts_first_gives_the_name():
    level = files(given=GIVEN | {5: FOXHOLT, 6: FOXHOLT, 7: ALDERWICK, 8: ALDERWICK})
    assert named(level).bears[TWO].written.place_id == ALDERWICK
    other_way = files(given=GIVEN | {5: ALDERWICK, 6: ALDERWICK, 7: FOXHOLT, 8: FOXHOLT})
    assert named(other_way).bears[TWO].written.place_id == ALDERWICK


def test_a_neighbourhood_with_no_name_gives_none_and_the_next_gives_its_own():
    # The second area has one output area in a neighbourhood that no record names.
    most_in_none = files(given=GIVEN | {5: NO_NAME, 6: NO_NAME, 7: NO_NAME, 8: FOXHOLT})
    found = named(most_in_none)
    assert found.bears[TWO].written.name == "Foxholt"
    assert (found.bears[TWO].held, found.bears[TWO].of) == (1, 4)


def test_an_area_that_lies_in_no_named_neighbourhood_keeps_its_label():
    nowhere = files(given={**GIVEN, **dict.fromkeys((5, 6, 7, 8), NO_NAME)})
    found = named(nowhere)
    assert TWO not in found.bears
    assert sorted(found.bears) == [ONE, THREE]
    counted = found.counts()
    assert counted["areas_that_bear_a_name"] == 2
    assert counted["areas_that_keep_their_label"] == 1
    # An output area the draft does not hold lies in no neighbourhood, and stops nothing.
    fewer = files(given={number: place for number, place in GIVEN.items() if number > 4})
    assert ONE not in named(fewer).bears


def test_a_name_is_one_a_publisher_writes_letter_for_letter_and_no_other():
    # A ward's label holds the name among other words, and another name is no name of the
    # neighbourhood itself. Neither writes the name, so the neighbourhood gives none.
    only_held = files(
        evidence=(
            Wrote(ALDERWICK, WARDS, "Alderwick Ward"),
            Wrote(ALDERWICK, PLACES, "Alderwick", role="alias"),
            Wrote(ALDERWICK, PLACES, "alderwick"),
            *(row for row in EVIDENCE if row.place_id != ALDERWICK),
        )
    )
    found = named(only_held)
    assert ONE not in found.bears
    assert found.bears[TWO].written.name == "Foxholt"


def test_an_area_says_every_publisher_that_writes_its_name_and_no_other():
    found = named()
    assert found.bears[ONE].source_ids == (CENTRES, PLACES)
    assert found.bears[THREE].source_ids == (PLACES,)
    assert found.source_ids == (CENTRES, PLACES)
    # The files the names rest on, in the order of their ids.
    assert [receipt.file_id for receipt in found.files] == sorted(
        receipt.file_id for receipt in receipts()
    )
    # A build whose names one publisher writes rests on the one file.
    one = named(files(evidence=[row for row in EVIDENCE if row.source_id == PLACES]))
    assert one.source_ids == (PLACES,)


# Two areas of one name


def test_two_areas_of_one_borough_that_bear_one_name_each_say_the_side_they_lie_on():
    found = named()
    assert shown(found) == {ONE: "Alderwick, west", TWO: "Alderwick, east", THREE: "Eskerfold"}
    # The name alone is another name of each, so that a search for it finds both.
    assert found.bears[ONE].aliases == found.bears[TWO].aliases == ("Alderwick",)
    assert found.bears[THREE].aliases == ()


def test_two_areas_of_two_boroughs_that_bear_one_name_say_their_borough_and_no_side():
    across = files(
        given={
            **dict.fromkeys(range(1, 5), ALDERWICK),
            **dict.fromkeys(range(5, 9), FOXHOLT),
            **dict.fromkeys(range(9, 13), ALDERWICK),
        }
    )
    found = named(across)
    assert shown(found) == {ONE: "Alderwick", TWO: "Foxholt", THREE: "Alderwick"}
    assert found.counts()["names_borne_by_two_areas_or_more"] == 1
    assert found.counts()["areas_that_say_a_side"] == 0


@pytest.mark.parametrize(
    ("centres", "said"),
    [
        ({"a": (0.0, 0.0), "b": (0.0, 9.0)}, {"a": "south", "b": "north"}),
        ({"a": (0.0, 0.0), "b": (9.0, 1.0)}, {"a": "west", "b": "east"}),
        # Three in a row: the one in the middle lies the way the pull of the others leaves it.
        (
            {"a": (0.0, 0.0), "b": (10.0, 0.0), "c": (5.0, 8.0)},
            {"a": "west", "b": "east", "c": "north"},
        ),
        # Two that lie north say which way of north each lies, and the third is as it was.
        (
            {"a": (-4.0, 6.0), "b": (4.0, 7.0), "c": (0.0, -13.0)},
            {"a": "north-west", "b": "north-east", "c": "south"},
        ),
        ({"a": (3.0, 4.0)}, {"a": ""}),
        ({}, {}),
    ],
)
def test_a_side_is_the_nearest_of_four_points_and_of_eight_where_two_would_say_the_same(
    centres: dict[str, tuple[float, float]], said: dict[str, str]
):
    assert names.sides_of(centres) == said


def test_two_that_lie_the_same_way_from_the_middle_say_the_same_and_nothing_is_made_up():
    # Two lie due north of the middle, one behind the other. Each says north.
    found = names.sides_of({"a": (0.0, 5.0), "b": (0.0, 9.0), "c": (0.0, -14.0)})
    assert found == {"a": "north", "b": "north", "c": "south"}


def test_a_degree_of_longitude_is_shorter_than_one_of_latitude():
    # Two areas as many degrees apart each way lie more north and south than east and west,
    # at the latitude of the town: they are nearer each other east and west than the
    # degrees say.
    drafted = names.draft_of(files(given=dict.fromkeys(range(1, 9), ALDERWICK)))
    apart = CENTRES_OF | {TWO: (2.0022, 53.4012)}
    found = names.name_areas(drafted, areas(), cells(), apart)
    assert {area: borne.side for area, borne in found.items()} == {ONE: "south", TWO: "north"}
    level = names.name_areas(drafted, areas(), cells(), CENTRES_OF)
    assert {area: borne.side for area, borne in level.items()} == {ONE: "west", TWO: "east"}


# A draft, and what a person decided


def test_a_name_is_a_draft_until_a_person_has_chosen_it_at_the_review_desk():
    assert {borne.written.state for borne in named().bears.values()} == {NameState.DRAFT}
    chosen = files(
        evidence=(
            Wrote(ESKERFOLD, PLACES, "Eskerfold", chosen_by=FOUNDER),
            *(row for row in EVIDENCE if row.place_id != ESKERFOLD),
        )
    )
    found = named(chosen)
    assert found.bears[THREE].written.state is NameState.CHECKED
    assert found.bears[ONE].written.state is NameState.DRAFT
    assert found.counts()["names_a_person_has_checked"] == 1


def test_the_name_a_person_decided_takes_the_place_of_the_name_that_was_drafted():
    # The desk writes the spelling a person chose as the name, in every row of its evidence.
    decided = files(
        neighbourhoods=NEIGHBOURHOODS | {ESKERFOLD: "Eskerfold Green"},
        evidence=(
            Wrote(ESKERFOLD, PLACES, "Eskerfold", chosen_by=FOUNDER),
            Wrote(ESKERFOLD, PLACES, "Eskerfold Green", chosen_by=FOUNDER),
            *(row for row in EVIDENCE if row.place_id != ESKERFOLD),
        ),
    )
    found = named(decided)
    assert found.bears[THREE].name == "Eskerfold Green"
    assert found.bears[THREE].written.checked


def test_a_name_a_person_chose_from_a_label_of_two_names_is_the_name_of_the_area():
    # A town centre's label holds two names, and the person chose one of them at the desk.
    decided = files(
        evidence=(
            Wrote(ESKERFOLD, CENTRES, "Eskerfold / Foxholt", chosen_by=FOUNDER),
            *(row for row in EVIDENCE if row.place_id != ESKERFOLD),
        ),
    )
    found = named(decided)
    assert found.bears[THREE].name == "Eskerfold"
    assert found.bears[THREE].source_ids == (CENTRES,)
    assert found.bears[THREE].written.checked
    # Drafted, the same label writes another name, and the neighbourhood gives none.
    drafted = files(
        evidence=(
            Wrote(ESKERFOLD, CENTRES, "Eskerfold / Foxholt"),
            *(row for row in EVIDENCE if row.place_id != ESKERFOLD),
        ),
    )
    assert named(drafted).bears[THREE].written.name == "Foxholt"


# What is refused


@pytest.mark.parametrize(
    ("broken", "why"),
    [
        ({names.AREAS: b"\xff\xfe not a table"}, names.UNREADABLE),
        ({names.AREAS: table(("area_id",), [{"area_id": ALDERWICK}])}, names.LACKS_A_COLUMN),
        ({names.GIVEN: table(("oa21cd",), [])}, names.LACKS_A_COLUMN),
        ({names.EVIDENCE: table(("area_id", "role"), [])}, names.LACKS_A_COLUMN),
        ({names.AREAS: b"area_id,name\nlon-n0001,Alderwick,Foxholt\n"}, names.UNREADABLE),
        (
            {
                names.AREAS: table(
                    ("area_id", "name"),
                    [{"area_id": ALDERWICK, "name": name} for name in ("Alderwick", "Foxholt")],
                )
            },
            names.GIVEN_TWICE,
        ),
        (
            {
                names.GIVEN: table(
                    ("oa21cd", "area_id"),
                    [{"oa21cd": "E00999001", "area_id": place} for place in (ALDERWICK, FOXHOLT)],
                )
            },
            names.GIVEN_TWICE,
        ),
    ],
)
def test_a_draft_that_cannot_be_read_is_refused_in_words_that_repeat_nothing_of_it(
    broken: dict[str, bytes], why: str
):
    with pytest.raises(NamesError) as caught:
        named(files() | broken)
    assert str(caught.value) == why
    assert not any(name in str(caught.value) for name in NEIGHBOURHOODS.values() if name)


def test_a_folder_that_lacks_a_file_of_the_draft_is_refused(tmp_path: Path):
    for name, content in files().items():
        if name != names.EVIDENCE:
            (tmp_path / name).write_bytes(content)
    with pytest.raises(NamesError) as caught:
        names.files_of(tmp_path)
    assert str(caught.value) == names.UNREADABLE
    (tmp_path / names.EVIDENCE).write_bytes(files()[names.EVIDENCE])
    (tmp_path / "about.txt").write_text("A draft holds other files, which are not read.")
    assert names.files_of(tmp_path) == files()


def test_a_name_that_rests_on_a_file_that_is_no_file_of_the_build_is_refused():
    drafted = files()
    with pytest.raises(NamesError) as caught:
        names.build(drafted, areas(), cells(), CENTRES_OF, receipts()[:1], None, registry())
    assert str(caught.value) == names.NOT_IN_THE_BUILD
    # A receipt in the folder is not enough: the lock of the build must name the file.
    with pytest.raises(NamesError) as caught:
        named(drafted, lock_of(drafted, without=CENTRES))
    assert str(caught.value) == names.NOT_IN_THE_BUILD
    # A file of another edition than the draft read is another file.
    other = dataclasses.replace(EVIDENCE[0], source_id=WARDS, as_written="Alderwick")
    with pytest.raises(NamesError):
        named(files(evidence=(other, *EVIDENCE[1:])))


def test_the_files_of_a_draft_are_read_only_as_the_lock_names_them():
    drafted = files()
    assert shown(named(drafted, lock_of(drafted))) == shown(named(drafted))
    assert [given.name for given in names.to_lock(drafted)] == [
        "gazetteer/areas.csv",
        "gazetteer/name_evidence.csv",
        "gazetteer/oa_to_area.csv",
    ]
    changed = drafted | {names.AREAS: drafted[names.AREAS].replace(b"Foxholt", b"Foxhole")}
    with pytest.raises(NamesError) as caught:
        named(changed, lock_of(drafted))
    assert str(caught.value) == names.NOT_IN_THE_BUILD


def test_a_name_written_by_a_source_the_registry_does_not_allow_for_names_is_refused():
    # The table of homes is allowed for scoring, and not for naming a place.
    homes = "ons-census-2021-housing-tables"
    refused = receipts()[0].model_copy(update={"source_id": homes})
    drafted = files(evidence=(Wrote(ALDERWICK, homes, "Alderwick"), *EVIDENCE[3:]))
    with pytest.raises(NamesError) as caught:
        names.build(drafted, areas(), cells(), CENTRES_OF, [refused], None, registry())
    assert str(caught.value) == names.NOT_ALLOWED


# What is counted, and what is said


def test_what_is_counted_of_the_names_of_a_build_holds_no_name():
    counted = named().counts()
    assert counted == {
        "areas": 3,
        "areas_that_bear_a_name": 3,
        "areas_that_keep_their_label": 0,
        "names": 2,
        "names_borne_by_two_areas_or_more": 1,
        "areas_that_say_a_side": 2,
        "areas_shown_under_a_name_another_area_is_shown_under": 0,
        "names_a_person_has_checked": 0,
    }


def test_the_method_is_one_sentence_that_a_methods_page_can_print():
    assert names.NAMED.derivation_id == "name_from_the_draft@1"
    assert names.NAMED.code == "burro_pipeline.assemble.names"
    assert names.NAMED.sentence.count(".") == 1


def test_what_an_area_bears_is_the_name_with_its_side_and_never_a_made_up_word():
    borne = Bears(named().bears[THREE].written, "north", 3, 4)
    assert (borne.name, borne.aliases) == ("Eskerfold, north", ("Eskerfold",))
    assert set(names.FOUR) <= set(names.EIGHT)
    assert len(set(names.EIGHT)) == 8
