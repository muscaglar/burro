"""The names a person must look at hardest, and why each is marked.

Every name here is made up. `names_support.py` draws the town.
"""

from dataclasses import replace

import pytest
from burro_pipeline.areas import names_look
from burro_pipeline.areas.names_look import BUILT, GRAVE, PEOPLE, Look, Mark
from burro_pipeline.areas.seeds import Seed

from .names_support import CENTRES, LINE, NAMES, drafted, held, seed


def looks(name: str, mark: Mark, kind: str | None = None) -> list[Look]:
    key = seed(name, kind).key
    return [look for look in drafted().looks if look.key == key and look.mark is mark]


def one(name: str, mark: Mark, kind: str | None = None) -> Look:
    (found,) = looks(name, mark, kind)
    return found


def marked(mark: Mark) -> set[str]:
    return {look.name for look in drafted().looks if look.mark is mark}


def renamed(given: Seed, name: str) -> Seed:
    """A seed under another name: its record says the name, and nothing else changes."""
    key = replace(given.place.key, as_written=name)
    return replace(given, place=replace(given.place, key=key, others=()))


def marks_of(given: Seed) -> list[Look]:
    read = held()
    return list(names_look.marks([given], [], [], [], read.london.borough_names, read.files))


# The same name in two places


def test_the_same_name_in_two_places_is_marked_on_both_with_where_the_other_is():
    west = one("Farrowmere", Mark.SAME_NAME_ELSEWHERE, "Suburban Area")
    east = one("Farrowmere", Mark.SAME_NAME_ELSEWHERE, "Village")
    assert west.record_id == seed("Farrowmere", "Village").place.key.record_id
    assert east.record_id == seed("Farrowmere", "Suburban Area").place.key.record_id
    assert "in Tallowgate" in west.why and "in Quillhaven" in east.why
    assert "2.5 km" in west.why and west.grave
    assert marked(Mark.SAME_NAME_ELSEWHERE) == {"Farrowmere"}


# Two names for one place


def test_a_second_name_of_one_record_is_marked():
    found = looks("Kindlewharf", Mark.TWO_NAMES_ONE_PLACE)
    assert ['"Lantern Yard"' in look.why for look in found] == [True]
    assert found[0].grave


def test_a_label_of_several_names_is_marked_on_the_place_it_names_and_on_itself():
    assert "Grapnel Dock/ Cindermoor" in one("Cindermoor", Mark.TWO_NAMES_ONE_PLACE).why
    assert looks("Grapnel Dock/ Cindermoor", Mark.TWO_NAMES_ONE_PLACE)


def test_a_seed_that_gave_way_to_one_close_by_is_marked_with_how_far_and_how_many_points():
    found = one("Foxholt", Mark.TWO_NAMES_ONE_PLACE)
    assert '"Alderwick"' in found.why and "500 m" in found.why
    assert "9 points to its 6" in found.why
    assert found.record_id == seed("Alderwick").place.key.record_id


# A name that is also a borough, a ward or a station


def test_a_name_that_is_also_a_borough_is_marked():
    found = one("Quillhaven", Mark.ALSO_A_BOROUGH)
    assert "Quillhaven London Boro" in found.why and found.source_id == LINE
    assert found.grave
    assert marked(Mark.ALSO_A_BOROUGH) == {"Quillhaven"}


def test_a_borough_that_only_the_lookup_names_is_found_too():
    read = held()
    found = names_look.marks(
        [seed("Quillhaven")], [], [], [], read.london.borough_names, read.files
    )
    assert [look.why for look in found if look.mark is Mark.ALSO_A_BOROUGH] == [
        'The borough "Quillhaven" has the same name.'
    ]


def test_a_station_of_the_same_name_where_the_place_stands_is_marked_and_is_not_grave():
    found = one("Alderwick", Mark.ALSO_A_STATION)
    assert "60 m" in found.why and found.source_id == NAMES
    assert not found.elsewhere and not found.grave


def test_a_station_of_the_same_name_elsewhere_is_grave():
    found = one("Eskerfold", Mark.ALSO_A_STATION)
    assert "3.6 km away" in found.why and found.elsewhere and found.grave
    assert marked(Mark.ALSO_A_STATION) == {"Alderwick", "Eskerfold"}


def test_a_ward_of_the_same_name_is_marked_near_the_place_and_far_from_it():
    near, far = one("Alderwick", Mark.ALSO_A_WARD), one("Foxholt", Mark.ALSO_A_WARD)
    assert "holds the place" in near.why and not near.grave
    assert "1.9 km away" in far.why and far.grave
    # A ward that names a place beside another name is no ward of the same name.
    assert marked(Mark.ALSO_A_WARD) == {"Alderwick", "Foxholt"}


# A name that describes who lives there


@pytest.mark.parametrize("word", ["Students", "students", "WORKERS", "Quakers"])
def test_a_name_that_holds_a_word_for_a_group_of_people_is_marked(word: str):
    found = marks_of(renamed(seed("Eskerfold"), f"Eskerfold {word}"))
    (look,) = (each for each in found if each.mark is Mark.MAY_DESCRIBE_RESIDENTS)
    assert f'"{word.casefold()}"' in look.why and look.grave
    # It is kept as the publisher writes it. The mark says who writes it, and changes nothing.
    assert look.name == f"Eskerfold {word}" and "Ordnance Survey writes it" in look.why


def test_a_word_is_looked_for_whole_and_a_name_is_never_marked_for_part_of_a_word():
    for name in ("Blackthorn", "Whitewater", "Richmere", "Polishing", "Kingsholt"):
        found = marks_of(renamed(seed("Eskerfold"), name))
        assert Mark.MAY_DESCRIBE_RESIDENTS not in {look.mark for look in found}


def test_no_name_of_the_made_up_town_is_marked_for_describing_residents():
    assert marked(Mark.MAY_DESCRIBE_RESIDENTS) == set()


def test_the_words_for_people_hold_no_word_for_a_rank_or_a_calling():
    assert not PEOPLE & {"kings", "queens", "bishops", "abbots", "knights", "monks", "nuns"}
    assert not PEOPLE & set(BUILT)
    assert all(word == word.casefold() and word.isalpha() for word in (*PEOPLE, *BUILT))


# A name that is an estate, a business or a building


@pytest.mark.parametrize(
    ("name", "word", "kind"),
    [
        ("Eskerfold Estate", "estate", "an estate or a development"),
        ("Eskerfold Wharf", "wharf", "an estate or a development"),
        ("Eskerfold Works", "works", "a business"),
        ("The Eskerfold Arms", "arms", "a business"),
        ("Eskerfold House", "house", "a building"),
        ("Eskerfold Road", "road", "a road"),
    ],
)
def test_a_name_that_holds_a_word_for_a_thing_that_is_built_is_marked(
    name: str, word: str, kind: str
):
    found = marks_of(renamed(seed("Alderwick"), name))
    (look,) = (each for each in found if each.mark is Mark.MAY_BE_A_BUILT_THING)
    assert look.why == f'It holds the word "{word}", as {kind} may.'


def test_a_place_in_the_smallest_box_the_file_draws_is_marked():
    found = looks("Eskerfold", Mark.MAY_BE_A_BUILT_THING)
    assert [look.why for look in found] == [
        "Its box is 500 m by 500 m, the smallest the file draws round a place."
    ]
    assert not looks("Alderwick", Mark.MAY_BE_A_BUILT_THING)


# One publisher, and no receipt


def test_a_name_one_publisher_writes_is_marked_with_who_writes_it():
    assert "Only Ordnance Survey writes it" in one("Foxholt", Mark.ONE_PUBLISHER).why
    assert "Only Greater London Authority" in one("Osierholm", Mark.ONE_PUBLISHER).why
    assert not looks("Alderwick", Mark.ONE_PUBLISHER)
    assert not looks("Cindermoor", Mark.ONE_PUBLISHER)
    # Eleven places of fourteen, under ten names: two places share a name.
    assert len(marked(Mark.ONE_PUBLISHER)) == 10


def test_all_that_rests_on_the_file_with_no_receipt_is_marked():
    """Its name, its points or where its seed stands: any of the three."""
    rests = marked(Mark.NO_RECEIPT)
    # The town centre writes its name, gives it points, or is where its seed stands.
    assert {"Alderwick", "Cindermoor", "Foxholt", "Kindlewharf", "Osierholm"} <= rests
    # No town centre lies within 800 m of either, and none writes its name.
    assert not rests & {"Eskerfold"}
    assert names_look.rests_on(seed("Eskerfold")) == (NAMES,)
    assert names_look.rests_on(seed("Foxholt")) == (CENTRES, NAMES)
    assert names_look.rests_on(seed("Alderwick")) == (CENTRES, LINE, NAMES)
    assert all(look.source_id == "" for look in drafted().looks if look.mark is Mark.NO_RECEIPT)


def test_what_rests_on_a_file_is_said_as_the_name_its_points_or_its_seed():
    assert names_look.what_rests_on(seed("Eskerfold")) == {NAMES: ("name", "points", "seed")}
    # A town centre of district class near Foxholt gives it points, and nothing more.
    assert names_look.what_rests_on(seed("Foxholt")) == {
        CENTRES: ("points",),
        NAMES: ("name", "points", "seed"),
    }
    assert names_look.what_rests_on(seed("Alderwick")) == {
        CENTRES: ("name", "points", "seed"),
        LINE: ("name", "points"),
        NAMES: ("name", "points"),
    }
    assert one("Foxholt", Mark.NO_RECEIPT).why == (
        f"Its points rest on {CENTRES}, a file that has no receipt."
    )
    assert one("Osierholm", Mark.NO_RECEIPT).why == (
        f"Its name, its points and its seed rest on {CENTRES}, a file that has no receipt."
    )


# What was done that the design did not say


def test_two_records_joined_though_over_a_kilometre_apart_are_marked():
    found = one("Wexmoor", Mark.JOINED_BEYOND_1KM)
    assert "Its outline is 1,150 m from the place's point" in found.why
    assert found.source_id == CENTRES and found.grave
    assert marked(Mark.JOINED_BEYOND_1KM) == {"Wexmoor"}


def test_a_seed_that_stands_far_from_its_place_is_marked():
    assert one("Wexmoor", Mark.SEED_FAR_FROM_PLACE).why == (
        "Its seed stands where its town centre is taken to stand, 1,200 m from the point "
        "that Ordnance Survey gives the place."
    )
    assert marked(Mark.SEED_FAR_FROM_PLACE) == {"Wexmoor"}


def test_a_seed_moved_to_a_town_centre_whose_label_only_holds_its_name_is_marked():
    """Every such seed is marked, and not only the one that lost its name by the move."""
    found = one("Kindlewharf", Mark.SEED_ON_A_LABEL_THAT_HOLDS_IT)
    assert '"Kindlewharf High Street"' in found.why and "200 m" in found.why
    assert found.source_id == CENTRES and not found.grave
    # A centre of its own name, and one whose label is several names, are not marked.
    assert marked(Mark.SEED_ON_A_LABEL_THAT_HOLDS_IT) == {"Kindlewharf"}


def test_points_that_rest_on_a_class_that_was_read_are_marked():
    assert {"Thrushcombe", "Pellam Cross"} <= marked(Mark.CLASS_WAS_READ)
    assert "Alderwick" not in marked(Mark.CLASS_WAS_READ)


# The marks as a whole


def test_the_gravest_marks_come_first_and_each_is_said_once():
    found = drafted().looks
    order = [names_look.ORDER[look.mark] for look in found]
    assert order == sorted(order)
    assert len({(look.key, look.mark, look.why) for look in found}) == len(found)
    assert next(iter(Mark)) is Mark.MAY_DESCRIBE_RESIDENTS
    assert {Mark.ONE_PUBLISHER, Mark.NO_RECEIPT, Mark.ALSO_A_WARD}.isdisjoint(GRAVE)


def test_every_name_in_the_words_of_a_mark_is_a_name_a_file_holds():
    written = {record.as_written for record in drafted().candidates.records}
    written |= {station.as_written for station in drafted().candidates.stations}
    written |= {"Lantern Yard"}
    for look in drafted().looks:
        quoted = look.why.split('"')[1::2]
        if look.mark in (Mark.MAY_DESCRIBE_RESIDENTS, Mark.MAY_BE_A_BUILT_THING):
            continue
        if look.why.startswith("Its label is several names"):
            continue
        assert set(quoted) <= written, look.why


def test_a_mark_changes_no_name_no_tier_and_no_seed():
    before = drafted().seeds
    read = held()
    names_look.marks(
        before.seeds, drafted().candidates.stations, [], [], read.london.borough_names, read.files
    )
    assert drafted().seeds == before
