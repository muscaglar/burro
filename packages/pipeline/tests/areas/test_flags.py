"""What makes a border flagged, on a made-up town.

Every name, code and number here is made up. The town is drawn in
`flags_support.py`, in squares of 100 metres.
"""

import dataclasses
import json
from pathlib import Path

import pytest
from burro_pipeline.areas import flags
from burro_pipeline.areas.flags import BORDERS, NAMES, Area, Cell, Draft, Flag, Rules, Side

from .flags_support import SURVEY, area_id, oa, town

QUIET = ("AAABBB", "AAABBB", "AAABBB")
# The questions of the review desk, which hold the words it shows for a flag.
QUESTIONS = Path(__file__).resolve().parents[4] / "tools" / "desk" / "questions.json"


def raised(found: list[Flag], code: str, queue: str = BORDERS) -> dict[str, Flag]:
    return {flag.area: flag for flag in found if flag.code == code and flag.queue == queue}


# A name and its publishers


def test_an_area_whose_name_one_publisher_writes_is_flagged_in_both_queues():
    draft = town(QUIET, publishers={"A": (SURVEY, SURVEY)})

    found = flags.one_publisher(draft, Rules())

    assert [(flag.queue, flag.item) for flag in found] == [
        (BORDERS, area_id("A")),
        (NAMES, f"n:{area_id('A')}"),
    ]
    assert found[0].why == (
        "One publisher writes its name: The Made-up Survey. It does not write it for a "
        "populated place at a point inside the area."
    )


def test_two_publishers_of_one_name_raise_no_flag():
    assert flags.one_publisher(town(QUIET), Rules()) == []


def test_one_official_publisher_is_enough_where_it_writes_the_name_at_a_point_inside():
    """The founder decided so. A name one publisher writes is flagged only where no
    official publisher writes it for a populated place at a point inside the area."""
    draft = town(QUIET, publishers={"A": (SURVEY,), "B": (SURVEY,)})
    fitted = dataclasses.replace(draft.areas[area_id("A")], by_the_rule=True)
    draft = dataclasses.replace(draft, areas={**draft.areas, area_id("A"): fitted})

    found = flags.one_publisher(draft, Rules())

    assert {flag.area for flag in found} == {area_id("B")}
    assert "one publisher" in flags.WORDS[NAMES][flags.ONE_PUBLISHER]


def test_the_words_of_the_flag_say_that_one_publisher_is_not_enough_and_not_where_it_writes():
    """The flag is raised on a wide name too, which its publisher may write at a point
    inside the area, and on an area with no name. So its words say nothing of a point:
    the line of the item says why one publisher is not enough for it."""
    for queue in (NAMES, BORDERS):
        said = flags.WORDS[queue][flags.ONE_PUBLISHER]
        assert "one is not enough" in said
        assert "point" not in said and "inside" not in said


def test_a_name_no_record_was_checked_for_says_so_and_names_no_publisher():
    found = flags.one_publisher(town(QUIET, publishers={"B": ()}), Rules())

    assert found[0].why == "No publisher's record of its name has been checked."


def test_an_area_that_rests_on_a_file_with_no_receipt_names_the_source():
    draft = town(QUIET, unreceipted={"B": ("synthetic-centres",)})

    found = raised(flags.no_receipt(draft, Rules()), flags.NO_RECEIPT)

    assert list(found) == [area_id("B")]
    assert "synthetic-centres" in found[area_id("B")].why


def test_two_areas_of_one_name_are_flagged_for_the_names_queue_alone():
    draft = town(QUIET, split=3)
    areas = {
        **draft.areas,
        area_id("B"): dataclasses.replace(draft.areas[area_id("B")], name="ALDERWICK"),
    }
    draft = Draft(areas, draft.cells, draft.sides, draft.boroughs)

    found = flags.same_name(draft, Rules())

    assert {(flag.queue, flag.area) for flag in found} == {
        (NAMES, area_id("A")),
        (NAMES, area_id("B")),
    }
    assert raised(found, flags.SAME_NAME, NAMES)[area_id("A")].why == (
        "1 other area has the same name, in Tallowgate."
    )


# Seeds


def test_two_seeds_within_600_metres_are_flagged_and_each_names_the_other():
    draft = town(QUIET, seeds={"A": (1, 2), "B": (1, 3)})

    found = raised(flags.seeds_close(draft, Rules()), flags.SEEDS_CLOSE)

    assert found[area_id("A")].why == (
        "Its seed is 100 m from the seed of Brackenhythe, in a straight line. "
        "Under 600 m is flagged."
    )
    assert "Alderwick" in found[area_id("B")].why
    # The cells in doubt are those of the area on the border between the two.
    assert found[area_id("A")].cells == (oa(0, 2), oa(1, 2), oa(2, 2))
    assert found[area_id("A")].doubt == (0.5, 0.5, 0.5)


def test_two_seeds_600_metres_apart_are_not_flagged():
    draft = town(("AAAAAABBBBBB",), seeds={"A": (0, 2), "B": (0, 8)})

    assert flags.seeds_close(draft, Rules()) == []


def test_an_area_with_no_seed_is_not_measured_against_any():
    draft = town(QUIET, seeds={"A": (1, 2)})

    assert flags.seeds_close(draft, Rules()) == []


# What a border follows


def test_a_border_that_follows_nothing_is_flagged_with_its_share():
    found = raised(flags.follows_nothing(town(QUIET), Rules()), flags.FOLLOWS_NOTHING)

    assert found[area_id("A")].why == (
        "0% of its border with other areas runs along a borough line, a ward line or a "
        "main road. Under 25% is flagged."
    )
    # It is a flag of the whole area. The cells on the loose stretches are pointed at to
    # be shown, and none is more in doubt for it.
    assert found[area_id("A")].whole
    assert found[area_id("A")].cells == (oa(0, 2), oa(1, 2), oa(2, 2))
    assert found[area_id("A")].doubt == (0.0, 0.0, 0.0)


@pytest.mark.parametrize(
    "follows",
    [
        {"split": 3},
        {"wards": ("PPPQQQ", "PPPQQQ", "PPPQQQ")},
        {"roads": [((row, 2), (row, 3)) for row in range(3)]},
    ],
    ids=["a borough line", "a ward line", "a main road"],
)
def test_a_border_along_a_line_that_can_be_named_is_not_flagged(follows: dict[str, object]):
    assert flags.follows_nothing(town(QUIET, **follows), Rules()) == []  # type: ignore[arg-type]


def test_a_border_is_held_to_the_share_of_its_length_that_follows_a_line():
    rows = ("AAABBB",) * 5
    one_of_five = town(rows, roads=[((0, 2), (0, 3))])
    two_of_five = town(rows, roads=[((0, 2), (0, 3)), ((1, 2), (1, 3))])

    assert len(flags.follows_nothing(one_of_five, Rules())) == 2
    assert flags.follows_nothing(two_of_five, Rules()) == []
    assert len(flags.follows_nothing(two_of_five, Rules(follows_share=0.5))) == 2


def test_a_ward_that_was_not_read_is_no_line():
    """Two cells with no ward are not taken to be in two wards."""
    draft = town(QUIET)
    assert all(cell.ward == "" for cell in draft.cells.values())

    assert len(flags.follows_nothing(draft, Rules())) == 2


# Size


def test_an_area_far_smaller_than_the_areas_beside_it_is_flagged_as_a_whole():
    draft = town(("AAAABBBB", "AAAABBBB", "AAAACBBB"))

    found = raised(flags.size_unlike_neighbours(draft, Rules()), flags.SIZE)

    assert list(found) == [area_id("C")]
    assert found[area_id("C")].why == (
        "It holds 1 output area. The 2 areas beside it hold 12 at the median. It is far smaller."
    )
    assert found[area_id("C")].whole and found[area_id("C")].cells == ()


def test_an_area_far_larger_is_flagged_and_points_at_no_cell():
    draft = town(("AAAAAAAAAABC", "AAAAAAAAAABC"))

    found = raised(flags.size_unlike_neighbours(draft, Rules()), flags.SIZE)

    assert found[area_id("A")].whole and found[area_id("A")].cells == ()
    assert found[area_id("A")].why.endswith("It is far larger.")


def test_size_is_counted_in_homes_where_every_cell_has_a_count_of_them():
    rows = ("AABB", "AABB")
    crowded = {(row, column): 900 for row in range(2) for column in (2, 3)}

    found = raised(flags.size_unlike_neighbours(town(rows, homes=crowded), Rules()), flags.SIZE)

    assert found[area_id("A")].why.startswith("It holds 400 homes.")
    assert flags.size_unlike_neighbours(town(rows), Rules()) == []


# Pieces


def test_an_area_in_two_pieces_is_flagged_and_points_at_the_cells_cut_off():
    draft = town(("AAABBA", "AAABBB"))

    found = raised(flags.two_pieces(draft, Rules()), flags.TWO_PIECES)

    assert found[area_id("A")].why == (
        "It is in 2 pieces. 1 of its 7 output areas is cut off from the largest."
    )
    assert found[area_id("A")].cells == (oa(0, 5),)
    assert area_id("B") not in found


def test_two_cells_that_meet_at_a_corner_alone_are_two_pieces():
    found = raised(flags.two_pieces(town(("AB", "BA")), Rules()), flags.TWO_PIECES)

    assert set(found) == {area_id("A"), area_id("B")}


# Boroughs


def test_an_area_across_a_borough_line_names_both_boroughs_main_first():
    draft = town(("AAAB", "AAAB"), split=2)

    found = raised(flags.two_boroughs(draft, Rules()), flags.TWO_BOROUGHS)

    assert found[area_id("A")].why == (
        "It lies in Quillhaven and Tallowgate. 2 of its 6 output areas are outside "
        "Quillhaven: 33.3% of its output areas."
    )
    assert found[area_id("A")].cells == (oa(0, 2), oa(1, 2))
    # The method chose each by distance, and the design doubts the choice: a half.
    assert found[area_id("A")].doubt == (0.5, 0.5)
    assert area_id("B") not in found


def test_the_main_borough_is_the_one_with_most_homes_and_not_most_cells():
    draft = town(("AAA",), split=2, homes={(0, 0): 50, (0, 1): 50, (0, 2): 500})

    assert flags.main_borough(draft, area_id("A")) == "E09000902"


# Margins


def test_a_cell_nearly_as_close_to_the_next_area_is_in_doubt_by_its_margin():
    draft = town(("AAB", "AAB"), margins={(0, 1): 0.0, (1, 1): 5.0, (0, 2): 10.0})

    found = raised(flags.margin_under(draft, Rules()), flags.MARGIN)

    assert found[area_id("A")].cells == (oa(0, 1), oa(1, 1))
    assert found[area_id("A")].doubt == (1.0, 0.5)
    assert found[area_id("A")].why == (
        "2 of its 4 output areas are nearly as close to the next area, with a margin "
        "under 10%: 50% of its output areas."
    )
    # A margin of 10% is not under 10%.
    assert area_id("B") not in found


def test_an_area_with_few_close_cells_is_not_flagged_for_them():
    rows = ("AAAAAAAAAAAB",)
    assert flags.margin_under(town(("AAAAAB",), margins={(0, 4): 1.0}), Rules()) != []

    assert flags.margin_under(town(rows, margins={(0, 10): 1.0}), Rules()) == []
    assert flags.close_cells(town(rows, margins={(0, 10): 1.0}), Rules(), area_id("A")) == {
        oa(0, 10): 0.9
    }


def test_a_draft_with_no_margin_raises_no_flag_and_says_what_was_not_worked_out():
    draft = town(QUIET, no_margin=True)

    assert flags.margin_under(draft, Rules()) == []
    assert flags.MARGIN in flags.not_worked_out(draft)


# Shape, and town centres


def test_the_least_compact_twentieth_is_flagged_and_at_least_one_area_is():
    draft = town(("AAAAAAAAAAAA", "BBBBCCCCDDDD", "BBBBCCCCDDDD", "BBBBCCCCDDDD"))

    found = raised(flags.least_compact(draft, Rules()), flags.LEAST_COMPACT)

    assert list(found) == [area_id("A")]
    assert found[area_id("A")].why.startswith("Its shape is the 1st least compact of 4 areas.")


def test_a_square_is_more_compact_than_a_strip_of_the_same_ground():
    draft = town(("AAAA", "BB..", "BB.."))

    assert draft.compactness[area_id("B")] == pytest.approx(0.785, abs=0.001)
    assert draft.compactness[area_id("A")] == pytest.approx(0.503, abs=0.001)


def test_an_area_with_two_town_centres_names_them_as_written():
    draft = town(QUIET, centres={"A": ("Tallowgate Cross", "Quillhaven Market")})

    found = raised(flags.two_centres(draft, Rules()), flags.TWO_CENTRES)

    assert found[area_id("A")].why == (
        "2 town centres lie mostly in it: Tallowgate Cross and Quillhaven Market."
    )


def test_what_the_draft_lists_as_wrong_with_an_area_is_a_flag_of_the_whole_area():
    draft = town(QUIET)
    areas = {
        **draft.areas,
        area_id("A"): dataclasses.replace(
            draft.areas[area_id("A")], listed=("both_banks", "seed_outside", "in_pieces")
        ),
    }

    found = flags.listed(Draft(areas, draft.cells, draft.sides, draft.boroughs), Rules())

    # Pieces are counted here from the sides, and not taken from the draft's word.
    assert [(flag.area, flag.code, flag.whole) for flag in found] == [
        (area_id("A"), flags.BOTH_BANKS, True),
        (area_id("A"), flags.SEED_OUTSIDE, True),
    ]
    assert found[1].why == "Its seed lies in an output area of another area."


# All of it


def test_every_flag_has_a_rule_in_one_line_and_words_for_the_desk():
    lines = Rules().lines()
    draft = town(
        ("AAABBA", "AAABBB"),
        split=4,
        publishers={"A": (SURVEY,)},
        unreceipted={"A": ("synthetic-centres",)},
        centres={"A": ("Tallowgate Cross", "Quillhaven Market")},
        seeds={"A": (0, 2), "B": (0, 3)},
        margins={(0, 2): 1.0, (1, 2): 2.0},
    )

    found = flags.flags_of(draft)

    assert {flag.code for flag in found} >= {
        flags.ONE_PUBLISHER,
        flags.SEEDS_CLOSE,
        flags.FOLLOWS_NOTHING,
        flags.TWO_PIECES,
        flags.TWO_BOROUGHS,
        flags.MARGIN,
        flags.LEAST_COMPACT,
        flags.TWO_CENTRES,
        flags.NO_RECEIPT,
    }
    for flag in found:
        assert flag.code in lines
        assert flag.code in flags.WORDS[flag.queue]
        assert flag.why.endswith(".")
        assert len(flag.cells) == len(flag.doubt)


def test_the_number_a_rule_turns_on_is_in_its_line():
    lines = Rules(seeds_metres=450, margin_percent=7.5, size_times=4).lines()

    assert "450 m" in lines[flags.SEEDS_CLOSE]
    assert "7.5%" in lines[flags.MARGIN]
    assert "over 4 times" in lines[flags.SIZE]


def test_the_desk_has_the_words_of_every_flag_this_part_can_raise():
    """A flag the desk has no words for stops its fill. So the two are held together."""
    asked = json.loads(QUESTIONS.read_bytes())["queues"]
    desk = {queue["id"]: queue["flags"] for queue in asked}
    for queue, words in flags.WORDS.items():
        assert {code: desk[queue].get(code) for code in words} == dict(words), queue


def test_the_same_draft_gives_the_same_flags_whatever_order_it_is_held_in():
    draft = town(("AAABBA", "AAABBB"), split=4, margins={(0, 2): 1.0})
    turned = Draft(
        dict(reversed(list(draft.areas.items()))),
        dict(reversed(list(draft.cells.items()))),
        list(reversed(draft.sides)),
        draft.boroughs,
    )

    assert flags.flags_of(turned) == flags.flags_of(draft)


def test_a_cell_in_an_area_the_draft_does_not_hold_is_refused():
    with pytest.raises(ValueError, match="an area the draft does not hold"):
        Draft({}, {"E00999001": Cell("E00999001", "syn-n0001", "E09000901")}, [])


def test_a_side_of_a_cell_the_draft_does_not_hold_is_refused():
    area = Area("syn-n0001", "Alderwick")
    cell = Cell("E00999001", "syn-n0001", "E09000901")
    with pytest.raises(ValueError, match="an output area the draft does not hold"):
        Draft({area.area_id: area}, {cell.oa: cell}, [Side(cell.oa, "E00999002", 100.0)])


def test_a_flag_about_the_name_is_of_no_cell_and_not_of_the_whole_area():
    draft = town(QUIET, publishers={"A": (SURVEY,)}, unreceipted={"A": ("synthetic-centres",)})

    found = [flag for flag in flags.flags_of(draft) if flag.code in flags.ABOUT_THE_NAME]

    assert {flag.code for flag in found} == {flags.ONE_PUBLISHER, flags.NO_RECEIPT}
    assert all(not flag.whole and flag.cells == () for flag in found)


def test_only_the_queues_that_are_asked_for_are_flagged():
    draft = town(QUIET, publishers={"A": (SURVEY,)})

    assert {flag.queue for flag in flags.flags_of(draft)} == {BORDERS, NAMES}
    assert {flag.queue for flag in flags.flags_of(draft, queues=(BORDERS,))} == {BORDERS}


def test_nothing_a_rule_reads_describes_who_lives_anywhere():
    """Rule 8. An area is drawn from places and land, and a count of homes is of buildings."""
    read = {
        field.name for record in (Area, Cell, Side, Draft) for field in dataclasses.fields(record)
    }

    assert read == {
        *("area_id", "name", "seed", "publishers", "unreceipted", "centres", "listed"),
        "by_the_rule",
        *("oa", "area", "borough", "ward", "hectares", "perimeter", "margin", "second", "homes"),
        *("a", "b", "metres", "along_a_road"),
        *("areas", "cells", "sides", "boroughs"),
    }
