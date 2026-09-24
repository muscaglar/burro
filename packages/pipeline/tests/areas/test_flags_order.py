"""The order a person is shown the areas in, on a made-up town.

Every name, code and number here is made up. The town is drawn in
`flags_support.py`, in squares of 100 metres.
"""

import pytest
from burro_pipeline.areas import flags, flags_order
from burro_pipeline.areas.flags import BORDERS, Draft, Rules
from burro_pipeline.areas.flags_order import Placed

from .flags_support import QUILLHAVEN, SURVEY, TALLOWGATE, area_id, town

GROUPS = {QUILLHAVEN: "quillhaven", TALLOWGATE: "tallowgate"}
# In a town of two or three areas the least compact twentieth is always one of them. It
# is left out here, so that a test shows the one thing it is about.
PLAIN = Rules(least_compact_share=0.0)
# Two areas of four cells side by side, with a ward line between them.
TWO, WARDS = ("AAAABBBB",), ("PPPPQQQQ",)


def order_of(draft: Draft, rules: Rules = PLAIN) -> list[Placed]:
    return flags_order.areas_in_order(draft, flags.flags_of(draft, rules), rules)


def by_item(placed: list[Placed]) -> dict[str, Placed]:
    return {each.item: each for each in placed}


def test_the_area_with_most_homes_at_stake_comes_first():
    """Two areas with one close cell each: the cell with more homes puts its area first."""
    draft = town(
        TWO, margins={(0, 3): 2.0, (0, 4): 2.0}, homes={(0, 3): 100, (0, 4): 400}, wards=WARDS
    )

    placed = order_of(draft)

    assert [each.item for each in placed] == [area_id("B"), area_id("A")]
    assert [each.rank for each in placed] == [1, 2]
    assert placed[0].at_stake == pytest.approx(320.0)
    assert placed[0].weighed_by == "homes"


def test_of_two_cells_with_as_many_homes_the_one_the_method_was_less_sure_of_counts_more():
    draft = town(TWO, margins={(0, 3): 8.0, (0, 4): 1.0}, homes=100, wards=WARDS)

    placed = order_of(draft)

    assert [each.item for each in placed] == [area_id("B"), area_id("A")]
    assert placed[0].at_stake == pytest.approx(90.0)
    assert placed[1].at_stake == pytest.approx(20.0)


def test_a_cell_counts_as_one_where_the_gate_gives_no_count_of_homes():
    placed = by_item(order_of(town(TWO, margins={(0, 3): 5.0}, wards=WARDS)))

    assert placed[area_id("A")].weighed_by == "output areas"
    assert placed[area_id("A")].at_stake == pytest.approx(0.5)


def test_one_cell_with_no_count_of_homes_means_every_cell_counts_as_one():
    """Nothing is filled in: a town is never weighed by homes here and by cells there."""
    draft = town(("AABB",), homes={(0, 0): 100, (0, 1): 100, (0, 2): 100})
    cells = dict(draft.cells)
    last = sorted(cells)[-1]
    cells[last] = type(cells[last])(last, cells[last].area, cells[last].borough, homes=None)

    assert Draft(draft.areas, cells, draft.sides).weighed_by == "output areas"


def test_a_cell_that_two_flags_point_at_is_counted_once_at_the_most_unsure():
    draft = town(
        ("AAAAB", "AAAAB"),
        split=3,
        margins={(0, 3): 2.0, (1, 3): 50.0},
        homes=100,
        wards=("PPPPQ", "PPPPQ"),
    )

    placed = by_item(order_of(draft, Rules(least_compact_share=0.0, size_times=10.0)))

    # Two cells are outside the main borough, a half in doubt each. One of them has a
    # margin of 2% too, which is 0.8 in doubt: it is counted once, at 0.8.
    assert placed[area_id("A")].flags == (flags.TWO_BOROUGHS,)
    assert placed[area_id("A")].at_stake == pytest.approx(80.0 + 50.0)


def test_a_flag_of_the_whole_area_puts_a_tenth_of_it_at_stake():
    draft = town(("AAAAAAAAAABC", "AAAAAAAAAABC"), wards=("PPPPPPPPPPQR",) * 2, homes=100)

    placed = by_item(order_of(draft))

    # Alderwick is far larger than the areas beside it, and Brackenhythe far smaller.
    assert placed[area_id("A")].flags == (flags.SIZE,)
    assert placed[area_id("A")].at_stake == pytest.approx(200.0)
    assert placed[area_id("A")].held == pytest.approx(2_000.0)
    assert placed[area_id("B")].at_stake == pytest.approx(20.0)
    assert placed[area_id("C")].at_stake == 0.0


def test_a_flag_about_the_name_puts_nothing_at_stake():
    named = town(TWO, wards=WARDS, publishers={"A": (SURVEY,)}, unreceipted={"A": ("syn",)})

    placed = by_item(order_of(named))

    assert placed[area_id("A")].flags == (flags.ONE_PUBLISHER, flags.NO_RECEIPT)
    assert placed[area_id("A")].about_the_border == ()
    assert placed[area_id("A")].at_stake == 0.0


def test_what_is_at_stake_is_never_more_than_the_area_holds():
    draft = town(
        ("AB",),
        margins={(0, 0): 0.0},
        centres={"A": ("Tallowgate Cross", "Quillhaven Market")},
    )

    placed = by_item(order_of(draft, Rules()))

    assert placed[area_id("A")].at_stake == pytest.approx(placed[area_id("A")].held)


def test_how_sure_the_method_was_is_the_share_of_the_area_that_is_not_in_doubt():
    placed = by_item(order_of(town(TWO, margins={(0, 3): 0.0}, wards=WARDS)))

    assert placed[area_id("A")].sure == pytest.approx(0.75)
    assert placed[area_id("B")].sure == pytest.approx(1.0)


def test_how_sure_the_method_was_is_from_its_margins_and_from_no_flag():
    """A cell across a borough line that the method placed with a wide margin was placed surely."""
    draft = town(("AAAB", "AAAB"), split=2, wards=("PPPQ", "PPPQ"))

    placed = by_item(order_of(draft))

    assert placed[area_id("A")].flags == (flags.TWO_BOROUGHS,)
    assert placed[area_id("A")].sure == pytest.approx(1.0)
    assert placed[area_id("A")].at_stake == pytest.approx(1.0)


def test_how_sure_the_method_was_is_not_known_where_the_draft_gives_no_margin():
    placed = order_of(town(("AAAB", "AAAB"), split=2, no_margin=True))

    assert [each.sure for each in placed] == [None, None]
    assert placed[0].at_stake > 0


def test_a_cell_with_no_margin_had_no_second_choice_and_is_not_in_doubt():
    draft = town(TWO, margins={(0, 3): 5.0}, wards=WARDS)
    cells = dict(draft.cells)
    first = sorted(cells)[0]
    cells[first] = type(cells[first])(first, cells[first].area, cells[first].borough, margin=None)

    placed = by_item(order_of(Draft(draft.areas, cells, draft.sides, draft.boroughs)))

    assert placed[area_id("A")].sure == pytest.approx(1 - 0.5 / 4)


def test_an_area_with_no_flag_is_still_placed_by_its_close_cells():
    draft = town(
        ("AAAAAABBBBBB", "AAAAAABBBBBB", "CCCCCCCCCCCC"),
        wards=("PPPPPPQQQQQQ", "PPPPPPQQQQQQ", "RRRRRRRRRRRR"),
        publishers={"C": (SURVEY,)},
        margins={(0, 5): 1.0},
    )

    placed = order_of(draft)

    # Alderwick has one close cell in twelve, which is too few to flag it. Cindermoor has
    # a flag about its name, which puts nothing at stake and moves it nowhere.
    assert [(each.item, each.flags) for each in placed] == [
        (area_id("A"), ()),
        (area_id("B"), ()),
        (area_id("C"), (flags.ONE_PUBLISHER,)),
    ]
    assert placed[0].at_stake == pytest.approx(0.9)


def test_of_two_areas_with_as_much_at_stake_the_one_with_more_flags_is_first():
    draft = town(
        ("AAAABBBB",), wards=WARDS, seeds={"B": (0, 5), "A": (0, 2)}, margins={(0, 0): 0.0}
    )
    rules = Rules(least_compact_share=0.0, doubt_between_seeds=0.0)

    placed = order_of(draft, rules)

    # Brackenhythe has a flag and nothing at stake. Alderwick has the same flag, and a cell
    # at stake besides.
    assert [(each.item, each.at_stake) for each in placed] == [
        (area_id("A"), 1.0),
        (area_id("B"), 0.0),
    ]


def test_an_area_that_breaks_a_rule_of_the_design_comes_before_every_other():
    """An area is in one piece and on one bank. One that is not is looked at first."""
    draft = town(
        ("AAAAAABBBBBB", "CCCCCCCCCC.C"),
        wards=("PPPPPPQQQQQQ", "RRRRRRRRRR.R"),
        margins={(0, 5): 0.0, (0, 4): 0.0, (0, 3): 0.0},
    )

    placed = order_of(draft, Rules(least_compact_share=0.0, follows_share=0.0))

    assert [(each.item, each.flags) for each in placed][:2] == [
        (area_id("C"), (flags.TWO_PIECES,)),
        (area_id("A"), (flags.MARGIN,)),
    ]
    assert placed[0].at_stake < placed[1].at_stake


def test_an_area_carries_why_it_is_flagged_in_the_order_of_its_flags():
    draft = town(("AAABBA", "AAABBB"), publishers={"A": (SURVEY,)})

    placed = by_item(order_of(draft))[area_id("A")]

    assert placed.flags[:2] == (flags.ONE_PUBLISHER, flags.FOLLOWS_NOTHING)
    assert placed.why[0] == (
        "One publisher writes its name: The Made-up Survey. It does not write it for a "
        "populated place at a point inside the area."
    )
    assert len(placed.why) == len(placed.flags)


def test_a_flag_of_the_names_queue_changes_no_place_in_the_order_of_borders():
    draft = town(TWO, wards=WARDS, unreceipted={"A": ("syn",)})
    names_only = [flag for flag in flags.no_receipt(draft, PLAIN) if flag.queue != BORDERS]

    assert flags_order.areas_in_order(draft, names_only) == flags_order.areas_in_order(draft, [])


def test_a_borough_is_placed_by_the_sum_of_the_areas_whose_main_borough_it_is():
    draft = town(TWO, split=4, margins={(0, 0): 0.0, (0, 5): 0.0, (0, 6): 0.0}, homes=100)

    placed = flags_order.boroughs_in_order(draft, order_of(draft), GROUPS)

    assert [(each.queue, each.item, each.rank) for each in placed] == [
        ("whole", "tallowgate", 1),
        ("whole", "quillhaven", 2),
    ]
    assert placed[0].at_stake == pytest.approx(200.0)
    assert placed[0].sure == pytest.approx(0.5)
    assert placed[0].why == ("1 of its 1 area has a flag about the border.",)


def test_the_same_draft_gives_the_same_order_whatever_order_it_is_held_in():
    draft = town(("AAABBA", "AAABBB"), split=4, margins={(0, 2): 1.0})
    turned = Draft(
        dict(reversed(list(draft.areas.items()))),
        dict(reversed(list(draft.cells.items()))),
        list(reversed(draft.sides)),
        draft.boroughs,
    )

    assert order_of(turned) == order_of(draft)
