"""Seeds: the points of a place, where its seed is put, and which of two that lie close gives way.

Every place here is made up. `names_support.py` draws the town.
"""

import math
from dataclasses import replace

import pytest
from burro_pipeline.areas import names_draft, names_wards, seeds
from burro_pipeline.areas.names_candidates import Match
from burro_pipeline.areas.names_shapes import Ground
from burro_pipeline.areas.seeds import Draft, Put, Rules, Seed, Tier, Tried, Weight, Why
from burro_pipeline.areas.seeds_roads import Link, Roads

from .names_support import (
    CENTRE_OF_ALDERWICK,
    CENTRE_OF_WEXMOOR,
    HIGH_STREET,
    OF_TWO_NAMES,
    OSIERHOLM,
    PELLAM,
    RULES,
    drafted,
    held,
    middle,
    node,
    seed,
)

OS, GLA = "Ordnance Survey", "Greater London Authority"


def draft_by(
    rules: Rules = RULES, points: int | None = None, publishers: int | None = None
) -> Draft:
    return names_draft.make(held(), rules, points=points, publishers=publishers).seeds


def named(draft: Draft, name: str, kind: str | None = None) -> Seed:
    (found,) = (
        each for each in draft.seeds if each.name == name and kind in (None, each.place.key.kind)
    )
    return found


# The points


@pytest.mark.parametrize(
    ("name", "kind", "weight", "publishers"),
    [
        # A populated place, 60 roads, its own town centre, and a ward of its name.
        ("Alderwick", None, (3, 2, 3, 1), (GLA, OS)),
        # A populated place, and a town centre of district class 450 m off. Ten roads are
        # too few, and the ward of its name lies elsewhere.
        ("Foxholt", None, (3, 0, 3, 0), (GLA, OS)),
        # A ward that names it beside another name. The centre near it is below district.
        ("Cindermoor", None, (3, 0, 0, 1), (OS,)),
        ("Eskerfold", None, (3, 0, 0, 0), (OS,)),
        ("Farrowmere", "Suburban Area", (3, 0, 0, 0), (OS,)),
        ("Farrowmere", "Village", (3, 0, 3, 0), (GLA, OS)),
        # Its town centre is the same place, 1,150 m off: further than 800 m, and its own.
        ("Wexmoor", None, (3, 0, 3, 0), (GLA, OS)),
        # A name that only a town centre holds has no points for being a populated place.
        ("Osierholm", None, (0, 0, 3, 0), (GLA,)),
        ("Pellam Cross", None, (0, 0, 3, 0), (GLA,)),
        ("Grapnel Dock/ Cindermoor", None, (0, 0, 0, 0), ()),
    ],
)
def test_the_points_of_a_place_are_the_designs(
    name: str, kind: str | None, weight: tuple[int, int, int, int], publishers: tuple[str, ...]
):
    found = seed(name, kind).weight
    assert (found.place, found.roads, found.centre, found.ward) == weight
    assert found.total == sum(weight)
    assert found.publishers == publishers


def test_points_say_which_record_gave_them():
    alderwick = seed("Alderwick").weight
    assert (alderwick.centre_record, alderwick.centre_metres) == (CENTRE_OF_ALDERWICK, 0.0)
    assert alderwick.ward_record == "E05998001"
    foxholt = seed("Foxholt").weight
    assert (foxholt.centre_record, foxholt.centre_metres) == (CENTRE_OF_ALDERWICK, 450.0)
    assert seed("Wexmoor").weight.centre_metres == 1_150.0
    assert seed("Eskerfold").weight.centre_record == ""
    assert seed("Eskerfold").weight.centre_metres is None


def test_the_ward_that_gives_the_point_is_one_that_writes_the_name_where_one_does():
    """A person is shown the wards that write a name as records of it. Where such a ward
    and one that only holds the name among other words both carry it, the point is said
    to come from the first, however near the second lies: the ward a person can see."""
    place = seed("Cindermoor").place
    (writes,) = place.written_by(names_wards.SOURCE)
    assert writes.match is Match.PART
    writes = replace(writes, metres=200.0)
    holds = replace(
        writes,
        candidate=replace(
            writes.candidate, record_id="E05998099", as_written="Cindermoor Park Ward"
        ),
        match=Match.HELD,
        metres=0.0,
    )
    # The nearest first, as the draft of names puts them.
    nearer_first = replace(place, others=(holds, writes))
    found = seeds.weigh(nearer_first, {}, Ground({}), RULES)
    assert (found.ward, found.ward_record) == (1, writes.candidate.record_id)
    # Where no ward writes it, the nearest that holds it gives the point.
    only_held = replace(place, others=(holds, replace(holds, metres=300.0)))
    assert seeds.weigh(only_held, {}, Ground({}), RULES).ward_record == "E05998099"


def test_points_from_a_class_that_was_read_as_district_say_so():
    assert seed("Thrushcombe").weight.centre_record == PELLAM
    assert seed("Thrushcombe").weight.centre_rank_is_read
    assert not seed("Alderwick").weight.centre_rank_is_read


def test_a_town_centre_further_than_800_metres_gives_no_points():
    near = replace(RULES, centre_metres=400.0)
    assert named(draft_by(near), "Foxholt").weight.centre == 0
    assert named(draft_by(near), "Alderwick").weight.centre == 3


def test_every_number_of_the_rules_is_the_designs_first_guess():
    assert Rules() == Rules(
        place=3,
        roads=2,
        roads_needed=50,
        centre=3,
        centre_metres=800.0,
        ward=1,
        points=6,
        publishers=2,
        too_close_metres=600.0,
        least=400,
        most=500,
        wide_over=5,
        wide_hectares=1_750.0,
    )


# Who writes a name


def test_a_name_one_publisher_writes_is_marked_so_whoever_gave_it_points():
    """Foxholt has points from two publishers, and only one of them writes its name."""
    assert seed("Foxholt").weight.publishers == (GLA, OS) and seed("Foxholt").one_publisher
    assert not seed("Alderwick").one_publisher
    assert not seed("Cindermoor").one_publisher
    assert seed("Osierholm").one_publisher


# Where a seed is put


def test_a_seed_is_put_on_the_town_centre_of_its_own_name():
    alderwick = seed("Alderwick")
    assert (alderwick.put, alderwick.own_centre) == (Put.CENTRE, CENTRE_OF_ALDERWICK)
    wexmoor = seed("Wexmoor")
    assert (wexmoor.put, wexmoor.own_centre, wexmoor.at) == (
        Put.CENTRE,
        CENTRE_OF_WEXMOOR,
        middle((5, 0)),
    )
    assert wexmoor.place.at != wexmoor.at


def test_a_seed_is_put_on_a_centre_whose_label_names_it_or_holds_its_name():
    assert seed("Cindermoor").own_centre == OF_TWO_NAMES
    assert seed("Kindlewharf").own_centre == HIGH_STREET


def test_a_seed_is_never_moved_to_a_centre_of_another_name():
    """Two places lie within 800 m of a centre that names neither. Each keeps its point."""
    for name, kind in (("Foxholt", None), ("Farrowmere", "Village"), ("Thrushcombe", None)):
        found = seed(name, kind)
        assert found.weight.centre == 3
        assert (found.put, found.own_centre, found.at) == (Put.PLACE, "", found.place.at)


def test_a_name_that_only_a_town_centre_holds_stands_on_that_centre():
    osierholm = seed("Osierholm")
    assert (osierholm.put, osierholm.own_centre) == (Put.CENTRE, OSIERHOLM)
    # Its own point lies outside its outline, so it stands inside the outline.
    assert osierholm.at == middle((7, 2))


def test_a_centre_is_given_to_one_place_and_to_the_nearest_of_those_it_fits_as_well():
    given = [each.own_centre for each in drafted().seeds.seeds if each.place.record is not None]
    taken = [centre for centre in given if centre]
    assert len(taken) == len(set(taken)) == 4


# Tiers


def test_a_place_with_enough_points_from_two_publishers_is_put_forward_as_an_area():
    found = draft_by(points=6, publishers=2)
    assert sorted(each.name for each in found.areas) == [
        "Alderwick",
        "Farrowmere",
        "Kindlewharf",
        "Thrushcombe",
        "Wexmoor",
    ]
    assert all(each.why is Why.NONE and each.of == () for each in found.areas)


def test_a_place_with_too_few_points_is_put_forward_as_a_name_of_the_nearest_area():
    found = draft_by(points=6, publishers=2)
    eskerfold = named(found, "Eskerfold")
    assert (eskerfold.tier, eskerfold.why) == (Tier.INSIDE, Why.FEW_POINTS)
    assert [named(found, "Thrushcombe").key] == list(eskerfold.of)
    # One link along the roads, and half a link from the seed to the node nearest it.
    assert eskerfold.metres == 750.0 and eskerfold.along_roads


def test_a_place_whose_points_come_from_one_publisher_waits_on_the_founder():
    found = draft_by(points=4, publishers=2)
    cindermoor = named(found, "Cindermoor")
    assert cindermoor.weight.total == 4
    assert (cindermoor.tier, cindermoor.why) == (Tier.INSIDE, Why.ONE_PUBLISHER)
    assert named(draft_by(points=4, publishers=1), "Cindermoor").tier is Tier.AREA


def test_of_two_seeds_too_close_the_one_with_fewer_points_gives_way():
    foxholt = seed("Foxholt")
    assert (foxholt.tier, foxholt.why) == (Tier.INSIDE, Why.TOO_CLOSE)
    assert foxholt.of == (seed("Alderwick").key,)
    assert foxholt.metres == 500.0 and not foxholt.tie
    assert seed("Alderwick").tier is Tier.AREA


def test_two_seeds_further_apart_than_600_metres_along_the_roads_both_stay():
    apart = replace(RULES, too_close_metres=499.0)
    found = draft_by(apart, points=6, publishers=2)
    assert named(found, "Foxholt").tier is Tier.AREA
    assert named(found, "Alderwick").tier is Tier.AREA


def test_a_town_centre_that_gives_way_to_the_place_that_stands_on_it_is_the_same_ground():
    found = draft_by(points=3, publishers=1)
    street = named(found, "Kindlewharf High Street")
    assert (street.tier, street.why) == (Tier.SAME_GROUND, Why.TOO_CLOSE)
    assert street.of == (named(found, "Kindlewharf").key,) and street.metres == 0.0


def test_of_two_seeds_with_as_many_points_the_one_more_publishers_write_stays_and_says_so():
    put = {"tier": Tier.AREA, "why": Why.NONE, "of": (), "metres": None, "tie": False}
    foxholt = replace(seed("Foxholt"), **put)
    alderwick = replace(seed("Alderwick"), weight=foxholt.weight, **put)
    for order in ([foxholt, alderwick], [alderwick, foxholt]):
        kept, gave_way = sorted(
            seeds.thin(order, held().roads, RULES), key=lambda each: each.tier is not Tier.AREA
        )
        assert (kept.name, kept.tier, kept.tie) == ("Alderwick", Tier.AREA, False)
        assert (gave_way.name, gave_way.why, gave_way.tie) == ("Foxholt", Why.TOO_CLOSE, True)


def test_two_seeds_on_one_spot_are_no_distance_apart():
    """Both are put on the same node of the roads, and the step to it is not counted twice."""
    roads = held().roads
    assert roads.within(middle((6, 1)), {"there": middle((6, 1))}, 600.0) == {"there": 0.0}
    here = (middle((6, 1))[0], middle((6, 1))[1] + 200.0)
    assert roads.within(here, {"there": here}, 600.0) == {"there": 0.0}
    assert roads.nearest_of({"start": here}, {"there": here}) == {"there": ("start", 0.0)}


def test_a_city_in_a_box_no_larger_than_five_areas_is_weighed_as_any_other_place():
    """The made-up city's box is 4,800 hectares. With the rule at 4,800, it is no wide name."""
    city = named(draft_by(replace(RULES, wide_hectares=4_800.0), 6, 2), "Quillhaven")
    assert city.place.record is not None and city.place.record.hectares == 4_800.0
    assert (city.tier, city.why) == (Tier.AREA, Why.NONE)
    assert named(draft_by(replace(RULES, wide_hectares=4_799.0)), "Quillhaven").tier is Tier.WIDE
    # A place of another kind is never a wide name, whatever its box.
    tiers = [each.tier for each in draft_by(replace(RULES, wide_hectares=1.0)).seeds]
    assert tiers.count(Tier.WIDE) == 1


def test_a_city_in_a_large_box_is_a_wide_name_and_never_a_seed():
    for points in (1, 6):
        found = draft_by(points=points, publishers=1)
        city = named(found, "Quillhaven")
        assert (city.tier, city.why) == (Tier.WIDE, Why.WIDE_KIND)
        assert 1 <= len(city.of) <= 5 and len(set(city.of)) == len(city.of)
        assert {key for key in city.of} <= {each.key for each in found.areas}
        assert not city.along_roads


def test_every_name_that_is_no_area_is_a_name_of_an_area_that_stands():
    for points in (1, 3, 4, 6, 9):
        found = draft_by(points=points, publishers=1)
        areas = {each.key for each in found.areas}
        for each in found.seeds:
            assert (each.tier is Tier.AREA) == (each.key in areas)
            if each.tier is not Tier.AREA:
                assert each.of and set(each.of) <= areas and each.key not in each.of


# What a person decided


def decided_by(decided: dict[str, Tier | None], rules: Rules = RULES) -> Draft:
    keys = {seed(name).key: tier for name, tier in decided.items()}
    read = held()
    return seeds.draft(drafted().candidates.places, read.centres, read.roads, rules, decided=keys)


def test_a_name_a_person_turned_down_is_never_put_forward_as_an_area():
    found = decided_by({"Thrushcombe": Tier.INSIDE})
    thrushcombe = named(found, "Thrushcombe")
    assert thrushcombe.weight.total == 6
    assert (thrushcombe.tier, thrushcombe.why) == (Tier.INSIDE, Why.DECIDED)
    assert thrushcombe.of and set(thrushcombe.of) <= {each.key for each in found.areas}
    assert "Thrushcombe" not in {each.name for each in found.areas}
    # Every other name stands as it stood.
    assert {each.name for each in found.areas} == {each.name for each in drafted().seeds.areas} - {
        "Thrushcombe"
    }


def test_a_name_a_person_said_is_not_a_name_to_keep_is_in_no_list():
    found = decided_by({"Thrushcombe": None})
    assert "Thrushcombe" not in {each.name for each in found.seeds}
    assert all(seed("Thrushcombe").key not in each.of for each in found.seeds)


def test_a_name_a_person_made_an_area_stands_whatever_its_points_and_never_gives_way():
    found = decided_by({"Foxholt": Tier.AREA, "Eskerfold": Tier.AREA})
    foxholt, eskerfold = named(found, "Foxholt"), named(found, "Eskerfold")
    assert (foxholt.tier, foxholt.why, foxholt.of) == (Tier.AREA, Why.DECIDED, ())
    assert (eskerfold.tier, eskerfold.weight.total) == (Tier.AREA, 3)
    # Alderwick stands 500 m from it, with more points, and stays too.
    assert named(found, "Alderwick").tier is Tier.AREA


def test_a_decision_does_not_move_the_points_the_draft_asks_for():
    """The rule is the one the method lands on. What a person decided is laid over it."""
    rules = Rules(least=5, most=6)
    found = decided_by({"Thrushcombe": Tier.INSIDE, "Wexmoor": None}, rules)
    assert (found.points, found.publishers) == (6, 2)
    assert len(found.areas) == 3 and found.in_range
    assert found.tried == draft_by(rules).tried


# Landing in range


def test_the_designs_rule_stands_where_it_lands_in_range():
    found = draft_by(Rules(least=5, most=6))
    assert (found.points, found.publishers, found.in_range) == (6, 2, True)
    assert len(found.areas) == 5


def test_the_points_are_moved_until_the_count_lands_in_range():
    found = draft_by(Rules(least=1, most=2))
    assert (found.points, found.publishers, found.in_range, len(found.areas)) == (7, 2, True, 1)


def test_where_two_publishers_cannot_land_in_range_one_is_allowed_and_the_draft_says_so():
    found = draft_by(Rules(least=6, most=6))
    assert (found.points, found.publishers, found.in_range, len(found.areas)) == (4, 1, True, 6)
    assert [each.name for each in found.areas if len(each.weight.publishers) < 2] == ["Cindermoor"]


def test_where_nothing_lands_in_range_the_draft_comes_as_near_as_it_can_and_says_so():
    found = draft_by(Rules(least=400, most=500))
    assert not found.in_range
    assert len(found.areas) == max(each.areas for each in found.tried) == 9
    found = draft_by(Rules(least=7, most=8))
    assert not found.in_range and len(found.areas) in (6, 9)


def test_every_rule_that_was_tried_is_kept_with_its_count():
    found = draft_by(Rules(least=5, most=6))
    assert Tried(6, 2, 5) in found.tried and Tried(4, 1, 6) in found.tried
    assert {each.publishers for each in found.tried} == {1, 2}
    assert [each.points for each in found.tried if each.publishers == 2] == list(range(9, 0, -1))


# It repeats


def test_the_order_the_places_come_in_changes_nothing():
    read = held()
    places = list(drafted().candidates.places)
    first = seeds.draft(places, read.centres, read.roads, RULES)
    turned = [*reversed(places[5:]), *places[:5]]
    assert seeds.draft(turned, list(reversed(read.centres)), read.roads, RULES) == first


def test_a_weight_with_nothing_behind_it_is_nothing():
    assert Weight().total == 0 and Weight().publishers == ()


# The roads


def grid(links: list[tuple[str, str, float]], nodes: dict[str, tuple[float, float]]) -> Roads:
    return Roads(nodes, [Link(*link) for link in links])


def test_a_distance_is_along_the_roads_and_not_in_a_straight_line():
    """Two points 100 m apart, with 900 m of road between them."""
    nodes = {"a": (0.0, 0.0), "b": (0.0, 400.0), "c": (100.0, 400.0), "d": (100.0, 0.0)}
    roads = grid([("a", "b", 400.0), ("b", "c", 100.0), ("c", "d", 400.0)], nodes)
    assert roads.within((0.0, 0.0), {"there": (100.0, 0.0)}, 1_000.0) == {"there": 900.0}
    assert roads.within((0.0, 0.0), {"there": (100.0, 0.0)}, 899.0) == {}


def test_the_way_to_a_point_counts_the_step_from_the_point_to_its_node():
    nodes = {"a": (0.0, 0.0), "b": (300.0, 0.0)}
    roads = grid([("a", "b", 300.0)], nodes)
    found = roads.within((0.0, 40.0), {"there": (300.0, -30.0)}, 1_000.0)
    assert found == {"there": 370.0}


def test_a_point_is_put_on_the_largest_piece_of_the_roads():
    read = held()
    assert read.roads.pieces == 2
    assert (read.roads.nodes, read.roads.links) == (33, 50)
    # A point beside the two nodes that stand apart is put on the town's roads all the same.
    nearest = read.roads.nearest(middle((2, 6)))
    assert nearest is not None and nearest[1] == 3 * 500.0
    assert node((2, 3)) != node((2, 6))


def test_the_nearest_of_several_starts_is_found_in_one_search():
    nodes = {name: (index * 100.0, 0.0) for index, name in enumerate("abcdefg")}
    links = [(a, b, 100.0) for a, b in zip("abcdef", "bcdefg", strict=True)]
    roads = grid(links, nodes)
    found = roads.nearest_of(
        {"west": (0.0, 0.0), "east": (600.0, 0.0)},
        {"one": (100.0, 0.0), "two": (500.0, 0.0), "middle": (300.0, 0.0)},
    )
    assert found == {"one": ("west", 100.0), "two": ("east", 100.0), "middle": ("east", 300.0)}


def test_where_there_is_no_road_nothing_is_near():
    roads = Roads({}, [])
    assert roads.nearest((0.0, 0.0)) is None
    assert roads.within((0.0, 0.0), {"there": (1.0, 1.0)}, math.inf) == {}
    assert roads.nearest_of({"here": (0.0, 0.0)}, {"there": (1.0, 1.0)}) == {}
