"""The draft, on a made-up town. Nothing here is real, and no file is read.

Each test holds one promise of section 4 of the areas design: every output
area in exactly one area, every area in one piece and on one bank, and the
same draft from the same ground.
"""

import random
from dataclasses import replace

import pytest
from burro_pipeline.areas.assign import (
    BOTH_BANKS,
    IN_PIECES,
    JOINED,
    NO_OUTPUT_AREA,
    NORTH,
    NOT_DRAWN,
    ROADS,
    SEED_OUTSIDE,
    SMALL,
    SOUTH,
    STRAY,
    TOO_CLOSE,
    UNDER_SMALLEST,
    WARD,
    Draft,
    Rules,
    Said,
    Seed,
    draft,
)
from burro_pipeline.areas.grow import Link

from .assign_support import QUILLHAVEN, TALLOWGATE, Town, node, town

# No area is too small, and no two seeds are too close, unless a test says so.
PLAIN = Rules(smallest=1, too_close=0.0)
A, B, C = "syn-n0001", "syn-n0002", "syn-n0003"


def areas_of(found: Draft) -> dict[str, str]:
    return {oa: given.area for oa, given in found.given.items()}


def drafted(made: Town, seeds: list[Seed], rules: Rules = PLAIN) -> Draft:
    return draft(made.cells, seeds, made.roads, made.beside, rules)


# Every output area in exactly one area


def test_every_output_area_is_in_exactly_one_area():
    made = town()
    found = drafted(made, [made.seed(1, 1, 1), made.seed(2, 4, 2)])
    assert sorted(found.given) == sorted(cell.oa for cell in made.cells)
    assert {given.area for given in found.given.values()} == set(found.drawn) == {A, B}
    assert sum(len(each.cells) for each in found.drawn.values()) == len(made.cells)


def test_every_row_names_an_area_that_exists():
    made = town()
    found = drafted(made, [made.seed(1, 0, 0), made.seed(2, 5, 3), made.seed(3, 2, 2)])
    assert all(given.oa in found.drawn[given.area].cells for given in found.given.values())
    assert all(given.second in {"", *found.drawn} for given in found.given.values())


def test_an_output_area_goes_to_the_seed_nearest_along_the_roads():
    """A wall parts two columns. What is beside the wall goes round it, and not through it."""
    made = town(columns=4, rows=3)
    wall = [((1, row), (2, row)) for row in (0, 1)]
    walled = made.without_links(wall)
    found = drafted(walled, [made.seed(1, 2, 0), made.seed(2, 0, 2)])
    # One square west of the wall is 100 m from the first seed in a straight line, and
    # 500 m by road. The second seed is 300 m away by road.
    assert found.given[made.oa(1, 0)].area == B
    assert found.given[made.oa(1, 0)].choices[0].far == 300_000
    assert drafted(made, [made.seed(1, 2, 0), made.seed(2, 0, 2)]).given[made.oa(1, 0)].area == A


def test_an_output_area_with_no_homes_beside_a_road_is_still_given():
    made = town(columns=3, rows=1)
    far = {made.oa(2, 0): replace(made.cells[2], to_node=40_000)}
    found = drafted(made.with_cells(far), [made.seed(1, 0, 0)])
    assert found.given[made.oa(2, 0)].choices[0].far == 240_000


# What a border may not cross


def test_no_output_area_goes_to_a_seed_on_the_other_bank():
    """The seed north of the bridge is the nearest to every square south of it. None goes."""
    made = town(river_above_row=1, bridges=(2,))
    north, south = made.seed(1, 2, 2), made.seed(2, 5, 0)
    found = drafted(made, [north, south])
    assert {found.given[made.oa(column, row)].area for column in range(6) for row in (0, 1)} == {B}
    assert {found.given[made.oa(column, row)].area for column in range(6) for row in (2, 3)} == {A}
    assert not [each for each in found.listed if each.what == BOTH_BANKS]
    assert found.drawn[A].banks == (NORTH,) and found.drawn[B].banks == (SOUTH,)


def test_a_bank_with_no_seed_of_its_own_is_listed_and_not_left_out():
    """Where a whole bank has no seed, its output areas still go somewhere, and it is said."""
    made = town(river_above_row=1, bridges=(2,))
    found = drafted(made, [made.seed(1, 2, 2)])
    assert set(areas_of(found).values()) == {A}
    assert found.given[made.oa(0, 0)].how == JOINED
    assert [each.what for each in found.listed] == [IN_PIECES, BOTH_BANKS]


def test_a_seed_with_no_bank_is_put_on_the_bank_most_of_what_it_is_nearest_to_is_on():
    """The water ends two columns from the west. A seed beyond its end is nearest to both banks."""
    made = town(columns=6, rows=4, river_above_row=1)
    west = {
        cell.oa: replace(cell, bank=NOT_DRAWN)
        for cell in made.cells
        if cell.oa in {made.oa(column, row) for column in (0, 1) for row in range(4)}
    }
    links = [
        *made.links,
        *(Link(node((column, 1)), node((column, 2)), 100.0) for column in (0, 1)),
    ]
    beside = {oa: dict(others) for oa, others in made.beside.items()}
    for column in (0, 1):
        beside[made.oa(column, 1)][made.oa(column, 2)] = 100.0
        beside[made.oa(column, 2)][made.oa(column, 1)] = 100.0
    round_the_end = replace(made.with_cells(west), links=tuple(links), beside=beside)
    found = drafted(round_the_end, [made.seed(1, 1, 2), made.seed(2, 5, 0), made.seed(3, 5, 3)])
    # The seed in the west is nearest to four squares of the north bank and three of the
    # south. It is put on the north bank, and the three go to the seed of their own bank.
    assert found.drawn[A].banks == (NOT_DRAWN, NORTH)
    assert {found.given[made.oa(column, row)].area for column in (2, 3) for row in (0, 1)} == {B}
    assert not [each for each in found.listed if each.what == BOTH_BANKS]
    assert all(NORTH not in each.banks or SOUTH not in each.banks for each in found.drawn.values())


def test_a_distance_is_raised_across_a_borough_line():
    """A square halfway between two seeds goes to the seed of its own borough."""
    made = town(columns=5, rows=1, borough_from_column=3)
    found = drafted(made, [made.seed(1, 0, 0), made.seed(2, 4, 0)])
    middle = found.given[made.oa(2, 0)]
    assert middle.area == A
    assert [(each.seed, each.far, each.across) for each in middle.choices] == [
        (A, 200_000, False),
        (B, 200_000, True),
    ]
    assert middle.choices[1].weighed == pytest.approx(220_000.0)
    assert middle.margin == 10 and middle.second == B


def test_an_area_may_lie_in_two_boroughs_and_the_share_of_each_is_kept():
    made = town(columns=5, rows=1, borough_from_column=3)
    found = drafted(made, [made.seed(1, 2, 0)])
    assert found.drawn[A].boroughs == {QUILLHAVEN: 3, TALLOWGATE: 2}
    assert found.drawn[A].primary_borough == QUILLHAVEN
    assert found.counts()["areas_in_two_boroughs"] == 1


def test_a_ward_that_holds_the_name_of_a_seed_cuts_the_distance_to_it():
    made = town(columns=5, rows=1)
    named = Said(WARD, "Dulcimer Green Ward", frozenset({B}))
    middle = made.cells[2]
    told = made.with_cells({middle.oa: replace(middle, said=(named,))})
    found = drafted(told, [made.seed(1, 0, 0), made.seed(2, 4, 0)])
    assert found.given[middle.oa].area == B
    assert found.given[middle.oa].choices[0].favoured_by == (WARD,)
    assert found.given[middle.oa].choices[0].weighed == pytest.approx(190_000.0)
    assert drafted(made, [made.seed(1, 0, 0), made.seed(2, 4, 0)]).given[middle.oa].area == A


def test_the_roads_that_name_a_seed_cut_the_distance_to_it_by_more_than_a_ward_does():
    made = town(columns=7, rows=1)
    middle = made.cells[3]
    told = (Said(ROADS, "Cindermoor", frozenset({A})), Said(WARD, "Eskerfold", frozenset({B})))
    found = drafted(
        made.with_cells({middle.oa: replace(middle, said=told)}),
        [made.seed(1, 0, 0), made.seed(2, 6, 0)],
    )
    assert [(each.seed, each.favoured_by) for each in found.given[middle.oa].choices] == [
        (A, (ROADS,)),
        (B, (WARD,)),
    ]
    assert [each.weighed for each in found.given[middle.oa].choices] == pytest.approx(
        [255_000.0, 285_000.0]
    )


# How sure the method was


def test_the_margin_is_how_much_further_the_second_choice_is_in_hundredths():
    made = town(columns=6, rows=1)
    found = drafted(made, [made.seed(1, 0, 0), made.seed(2, 5, 0)])
    assert [found.given[made.oa(column, 0)].margin for column in range(6)] == [
        999,
        300,
        50,
        50,
        300,
        999,
    ]
    assert found.given[made.oa(2, 0)].second == B


def test_an_output_area_with_one_seed_in_reach_has_no_margin_and_none_is_made_up():
    made = town(columns=3, rows=1)
    found = drafted(made, [made.seed(1, 0, 0)])
    assert {(given.margin, given.second) for given in found.given.values()} == {(None, "")}


# Repair


def test_an_output_area_no_seed_reaches_joins_the_area_it_shares_most_border_with():
    made = town(columns=4, rows=2)
    cut = made.cells[3]
    alone = made.with_cells({cut.oa: replace(cut, node="")})
    beside = {oa: dict(others) for oa, others in made.beside.items()}
    beside[cut.oa][made.oa(3, 1)] = beside[made.oa(3, 1)][cut.oa] = 250.0
    found = drafted(replace(alone, beside=beside), [made.seed(1, 0, 0), made.seed(2, 3, 1)])
    assert (found.given[cut.oa].area, found.given[cut.oa].how) == (B, JOINED)
    assert (found.given[cut.oa].margin, found.given[cut.oa].second) == (0, "")
    assert found.counts()["no_seed_reached"] == 1


def test_a_part_cut_off_from_its_area_joins_the_area_it_shares_most_border_with():
    """A road runs from the first seed into the far corner, which no side joins to it."""
    made = town(columns=5, rows=1)
    links = [*made.links, Link(node((0, 0)), node((4, 0)), 10.0)]
    found = drafted(replace(made, links=tuple(links)), [made.seed(1, 0, 0), made.seed(2, 3, 0)])
    corner = found.given[made.oa(4, 0)]
    assert corner.choices[0].seed == A
    assert (corner.area, corner.how, corner.margin, corner.second) == (B, STRAY, 0, A)
    assert not found.listed
    assert all(len(each.pieces) == 1 for each in found.drawn.values())


@pytest.mark.parametrize("turn", range(4))
def test_every_area_is_one_piece(turn: int):
    """Fast roads run between far corners of the town, so parts of an area are cut off."""
    made = town(columns=12, rows=9, borough_from_column=6)
    drawn = random.Random(turn)  # noqa: S311
    fast = [Link(node(drawn.choice(SQUARES)), node(drawn.choice(SQUARES)), 50.0) for _ in range(10)]
    quick = replace(made, links=(*made.links, *fast))
    seeds = [made.seed(number, *drawn.choice(SQUARES)) for number in range(1, 9)]
    found = drafted(quick, list({seed.oa: seed for seed in seeds}.values()))
    assert found.counts()["cut_off_and_joined"] > 0
    assert sorted(found.given) == sorted(cell.oa for cell in made.cells)
    assert all(len(each.pieces) == 1 for each in found.drawn.values())
    assert not [each for each in found.listed if each.what == IN_PIECES]


SQUARES = [(column, row) for column in range(12) for row in range(9)]


def test_a_part_with_no_other_area_beside_it_is_listed_and_stays():
    """An island is reached by a road and shares no side. It stays, and the area is listed."""
    made = town(columns=4, rows=1)
    island = (3, 0)
    apart = made.without_sides([((2, 0), island)])
    found = drafted(apart, [made.seed(1, 0, 0)])
    assert found.given[made.oa(*island)].area == A
    assert [(each.area, each.what, each.cells) for each in found.listed] == [
        (A, IN_PIECES, (made.oa(*island),))
    ]


def test_an_area_under_the_least_size_becomes_part_of_the_area_beside_it():
    made = town(columns=6, rows=1)
    seeds = [made.seed(1, 1, 0), made.seed(2, 5, 0)]
    found = drafted(made, seeds, Rules(smallest=3, too_close=0.0))
    assert set(areas_of(found).values()) == {A}
    assert [
        (each.seed, each.into, each.why, each.lies_in, each.held) for each in found.absorbed
    ] == [(B, A, UNDER_SMALLEST, A, 2)]
    assert found.given[made.oa(5, 0)].how == SMALL
    # What was its own seed now stands as the area it became part of, so nothing is in doubt.
    assert found.given[made.oa(5, 0)].margin is None


def test_an_area_on_the_kept_list_stays_however_small():
    made = town(columns=6, rows=1)
    seeds = [made.seed(1, 1, 0), made.seed(2, 5, 0)]
    found = drafted(made, seeds, Rules(smallest=3, too_close=0.0, kept=frozenset({B})))
    assert len(found.drawn[B].cells) == 2 and not found.absorbed


def test_the_smallest_area_is_taken_in_first():
    made = town(columns=9, rows=1)
    seeds = [made.seed(1, 0, 0), made.seed(2, 3, 0), made.seed(3, 8, 0)]
    found = drafted(made, seeds, Rules(smallest=3, too_close=0.0))
    # The first seed holds two squares, the second four and the third three. Only the
    # first is under three.
    assert [(each.seed, each.into) for each in found.absorbed] == [(A, B)]
    assert sorted(len(each.cells) for each in found.drawn.values()) == [3, 6]


def test_two_seeds_too_close_are_one_place_and_the_heavier_stands():
    made = town(columns=8, rows=1)
    seeds = [made.seed(1, 1, 0, weight=6), made.seed(2, 3, 0, weight=9), made.seed(3, 7, 0)]
    found = drafted(made, seeds, Rules(smallest=1, too_close=250.0))
    assert [(each.seed, each.into, each.why, each.far) for each in found.absorbed] == [
        (A, B, TOO_CLOSE, 200_000)
    ]
    assert set(areas_of(found).values()) == {B, C}


def test_of_two_seeds_as_heavy_and_too_close_the_one_whose_id_sorts_first_stands():
    made = town(columns=4, rows=1)
    found = drafted(made, [made.seed(2, 1, 0), made.seed(1, 2, 0)], Rules(1, 100.0, 1))
    assert [(each.seed, each.into) for each in found.absorbed] == [(B, A)]


def test_a_chain_of_seeds_is_not_all_taken_in_by_the_first():
    """Each seed is 200 m from the next. The middle one goes, and the far one stands."""
    made = town(columns=6, rows=1)
    seeds = [made.seed(1, 0, 0, 9), made.seed(2, 2, 0, 8), made.seed(3, 4, 0, 7)]
    found = drafted(made, seeds, Rules(smallest=1, too_close=250.0))
    assert [(each.seed, each.into) for each in found.absorbed] == [(B, A)]
    assert set(found.drawn) == {A, C}


def test_a_seed_that_is_given_no_output_area_becomes_part_of_the_area_it_lies_in():
    """Two seeds in one output area, further apart by road than is too close."""
    made = town(columns=3, rows=1)
    first = made.seed(1, 1, 0, weight=9)
    second = replace(made.seed(2, 1, 0, weight=6), node=first.node, to_node=90_000)
    found = drafted(made, [first, second], Rules(smallest=1, too_close=50.0))
    assert [(each.seed, each.into, each.why) for each in found.absorbed] == [(B, A, NO_OUTPUT_AREA)]


def test_a_seed_whose_own_output_area_went_elsewhere_is_listed():
    made = town(columns=5, rows=1)
    away = replace(made.seed(2, 1, 0), node=made.seed(9, 4, 0).node)
    found = drafted(made, [made.seed(1, 0, 0), away])
    assert [(each.area, each.what) for each in found.listed] == [(B, SEED_OUTSIDE)]


# The same areas for the same files


def test_the_same_ground_in_another_order_gives_the_same_draft():
    made = town(columns=10, rows=8, river_above_row=3, bridges=(2, 7), borough_from_column=5)
    seeds = [
        made.seed(1, 1, 1),
        made.seed(2, 8, 1, weight=7),
        made.seed(3, 2, 6),
        made.seed(4, 7, 6, weight=9),
        made.seed(5, 7, 5),
        made.seed(6, 4, 0, weight=3),
    ]
    rules = Rules(smallest=6, too_close=150.0)
    first = drafted(made, seeds, rules)
    assert first.absorbed and len(first.drawn) > 2
    drawn = random.Random(11)  # noqa: S311
    for turn in range(3):
        again = made.shuffled(turn)
        mixed = drawn.sample(seeds, len(seeds))
        assert drafted(again, mixed, rules) == first


# What stops a draft


def test_a_draft_stops_where_the_ground_does_not_fit_together():
    made = town(columns=3, rows=1)
    seed = made.seed(1, 0, 0)
    with pytest.raises(ValueError, match="there twice"):
        draft([*made.cells, made.cells[0]], [seed], made.roads, made.beside)
    with pytest.raises(ValueError, match="there twice"):
        draft(made.cells, [seed, seed], made.roads, made.beside)
    with pytest.raises(ValueError, match="no seed"):
        draft(made.cells, [], made.roads, made.beside)
    with pytest.raises(ValueError, match="lies in no output area"):
        draft(made.cells, [replace(seed, oa="E00999999")], made.roads, made.beside)
    with pytest.raises(ValueError, match="shared by both"):
        draft(made.cells, [seed], made.roads, {made.oa(0, 0): {made.oa(1, 0): 100.0}})
