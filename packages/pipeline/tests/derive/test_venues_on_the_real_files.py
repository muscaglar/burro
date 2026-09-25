"""Cafes, gyms and pubs nearby, held to the file its publisher gave.

Every other test of the measures runs on made-up places. These read the real
part of the file of places, and are skipped where the store of fetched files
is not. The store is named by BURRO_STORE_FOLDER, and each file is read
through its receipt in `data/receipts/`.

They hold what must be so of any file of places, and the counts that the part
of release 2026-09-23.0 gave when it was first read. A figure here is of the
part, of London as a whole, or of a borough that is not named. None is said of
a named area, and no place is named. The highest figure of a measure is not
held: one area of London is a borough on its own, and it leads some of these.

The last tests hold the pubs and bars of the file against the pubs of the food
hygiene register, which was the first source of them. They are why pubs and
bars are counted from the file: `venues_nearby.PUBS_ARE_FROM_THE_FILE`.

Credit: Overture Maps Foundation, overturemaps.org. Contains public sector
information licensed under the Open Government Licence v3.0. Source: Food
Standards Agency. Source: Office for National Statistics licensed under the
Open Government Licence v.3.0.

Nothing is written to the store. A file is copied out of it to be read.
"""

import statistics
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import pytest
from burro_core.catalogue import RANKED_AS
from burro_core.ids import FeatureId
from burro_pipeline.cells import land, spine
from burro_pipeline.cells.shapes import holding, on_the_grid
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import (
    culture_file,
    evening_cluster_exposure,
    homes_density,
    venue_pub,
    venues_nearby,
)
from burro_pipeline.derive.culture_check import (
    distance_from_the_middle,
    held_against,
    rank_correlation,
)
from burro_pipeline.derive.culture_reach import Point, figures, ground_of, kept, within
from burro_pipeline.derive.evening_cluster_exposure import Exposure
from burro_pipeline.derive.food_register import Group
from burro_pipeline.derive.methods import Worked
from burro_pipeline.derive.venue_kinds import IS, IS_NOT, KINDS, PARENTS, Kind, LeftOut
from burro_pipeline.derive.venues_nearby import EVERY, Found, Nearby
from burro_pipeline.evidence.row import State
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

from .food_real_files import RECEIPTS, SKIPPED, real_inputs

FETCHED = (RECEIPTS / culture_file.SOURCE).is_dir()
pytestmark = [
    SKIPPED,
    pytest.mark.skipif(not FETCHED, reason="the part of the file of places has not been fetched"),
]
COUNTS = tuple(feature for feature, of in venues_nearby.MEASURES.items() if not of.rate)
RATES = tuple(RANKED_AS[feature] for feature in COUNTS)


@pytest.fixture(scope="module")
def real(tmp_path_factory: pytest.TempPathFactory) -> Inputs:
    return real_inputs(tmp_path_factory.mktemp("real"), "m2-culture")


@pytest.fixture(scope="module")
def found(real: Inputs) -> Spine:
    return spine.build(real)


@pytest.fixture(scope="module")
def made(real: Inputs, found: Spine) -> Found:
    return venues_nearby.found_of(real, found)


@pytest.fixture(scope="module")
def built(real: Inputs, found: Spine) -> dict[FeatureId, Nearby]:
    return {
        feature: venues_nearby.build(feature, real, found) for feature in venues_nearby.MEASURES
    }


@pytest.fixture(scope="module")
def cluster(real: Inputs, found: Spine) -> Exposure:
    return evening_cluster_exposure.build(real, found)


def values_of(worked: Mapping[str, Worked]) -> dict[str, float | None]:
    return {area: one.value for area, one in worked.items()}


def three_of(worked: Mapping[str, Worked]) -> tuple[float, float, float]:
    """London's lowest and middle figure, and the figure nine areas in ten do not pass."""
    have = sorted(one.value for one in worked.values() if one.value is not None)
    return have[0], statistics.median(have), have[(9 * len(have)) // 10]


# The part, and the table of kinds


def test_every_row_of_the_part_is_read_and_every_row_is_counted_once(made: Found):
    held = made.held
    assert held.file.taken is not None and held.rows == held.file.taken.rows == 683_409
    assert held.rows == len(held.records) + sum(held.left_out.values())
    assert sum(held.counted_as.values()) == len(held.records)
    assert len(made.places) + sum(made.records_of_one_place.values()) == len(held.records)


def test_the_part_holds_the_records_it_held_when_it_was_first_read(made: Found):
    """Of 683,409 rows, 33,349 are of a kind, and they are 28,446 places."""
    assert made.held.by_kind == {"cafe": 12_649, "gym": 8_510, "pub": 12_190}
    assert dict(made.held.left_out) == {
        LeftOut.NO_CATEGORY: 51_966,
        LeftOut.NOT_A_KIND: 20_307,
        LeftOut.NOT_OF_THE_TABLE: 577_787,
    }
    assert {kind: len(made.of_kind(kind)) for kind in KINDS} == {
        Kind.CAFE: 10_699,
        Kind.GYM: 7_696,
        Kind.PUB: 10_051,
    }
    assert dict(made.records_of_one_place) == {Kind.CAFE: 1_950, Kind.GYM: 814, Kind.PUB: 2_139}


def test_every_category_of_a_branch_that_is_read_is_on_the_table(made: Found):
    """A record of a branch that is read is counted or is left out by the name of its
    category. One that is neither stops the build, so that the part was read says the rest."""
    held = made.held
    assert set(held.counted_as) <= set(IS)
    assert set(held.left_out_as) <= set(IS_NOT) | PARENTS
    assert (len(held.counted_as), len(held.left_out_as)) == (33, 97)
    # No record of the part says no more than a parent of the cafes or of the bars.
    assert not set(held.left_out_as) & PARENTS
    # One category of the table is in no record of the part: a fitness studio that says no
    # more. Every studio of the part says which kind it is.
    assert set(IS) - set(held.counted_as) == {"fitness_studio"}
    # Six that are left out are held only as the parent of another.
    assert set(IS_NOT) - set(held.left_out_as) == {
        "adventure_sport",
        "diving_instruction",
        "fishing",
        "sport_court",
        "sport_field",
        "water_sport",
    }


def test_the_categories_that_count_most_are_the_ones_a_person_would_name(made: Found):
    counted = made.held.counted_as
    assert {name: counted[name] for name in ("cafe", "coffee_shop", "tea_room")} == {
        "cafe": 7_159,
        "coffee_shop": 5_037,
        "tea_room": 449,
    }
    assert {name: counted[name] for name in ("gym", "yoga_studio", "pilates_studio")} == {
        "gym": 5_306,
        "yoga_studio": 1_232,
        "pilates_studio": 902,
    }
    assert counted["sport_or_fitness_facility"] == 793
    assert {name: counted[name] for name in ("pub", "bar", "cocktail_bar", "gastropub")} == {
        "pub": 5_978,
        "bar": 2_873,
        "cocktail_bar": 1_079,
        "gastropub": 722,
    }
    left_out = made.held.left_out_as
    assert left_out["fitness_trainer"] == 1_039 and left_out["gymnastics_center"] == 230
    assert left_out["bakery"] == 3_207 and left_out["lounge"] == 417


def test_every_record_of_a_kind_names_a_source_the_registry_has_read_the_licence_of(
    made: Found,
):
    """A source that is met here for the first time fails this test, so that a person reads
    its licence before a record of it is counted."""
    found = made.held.by_dataset
    assert found["Overture"] == len(made.held.records)
    assert set(found) == {
        "AllThePlaces",
        "Foursquare",
        "Microsoft",
        "Overture",
        "Overture-signals",
        "PinMeTo",
        "meta",
    }
    assert found["meta"] == 24_668 and found["Overture-signals"] == 1


# The figures


def test_the_file_holds_something_within_reach_of_every_home_of_london(
    made: Found, built: dict[FeatureId, Nearby]
):
    assert len(made.reach.near_the_edge) == 311 and len(made.seen) == 26_058
    assert len(made.seen) == len(made.reach.within)
    for one in built.values():
        given = [worked.value is not None for worked in one.worked.values()]
        assert (sum(given), len(given)) == (992, 1_002)


def test_every_area_has_a_row_and_no_figure_stands_on_under_half_its_homes(
    built: dict[FeatureId, Nearby], found: Spine
):
    for feature, one in built.items():
        assert set(one.worked) == set(found.weights.areas)
        assert [row.fact_id.split("/", 1)[1] for row in one.rows] == [f"feature/{feature}"] * 1_002
        for worked in one.worked.values():
            assert (worked.value is None) == (worked.state not in (State.PRESENT, State.PARTIAL))
            assert worked.value is None or (worked.weight_covered >= 0.5 and worked.value >= 0)
        assert one.metric.rankable is (feature not in RANKED_AS)
        assert len(one.files) == 4


def test_the_lowest_the_middle_and_the_ninth_in_ten_are_what_was_worked_out(
    built: dict[FeatureId, Nearby],
):
    assert {str(feature): three_of(one.worked) for feature, one in built.items()} == {
        "venue_cafe": (0.1, 10.1, 33.6),
        "venue_cafe_per_homes": (0.0, 1.6, 3.2),
        "venue_gym": (0.0, 6.35, 21.4),
        "venue_gym_per_homes": (0.0, 1.1, 2.2),
        "venue_evening": (0.0, 7.0, 34.6),
        "venue_evening_per_homes": (0.0, 1.2, 3.1),
    }


def test_a_figure_for_each_1000_homes_takes_few_values(built: dict[FeatureId, Nearby]):
    """It is given to one decimal place, as every figure of venues is, so many areas tie."""
    distinct = {
        str(feature): len({one.value for one in built[feature].worked.values()} - {None})
        for feature in RATES
    }
    assert distinct == {
        "venue_cafe_per_homes": 79,
        "venue_gym_per_homes": 50,
        "venue_evening_per_homes": 78,
    }


def test_each_count_is_mostly_a_map_of_the_centre_and_each_rate_less_so(
    real: Inputs, made: Found, built: dict[FeatureId, Nearby], found: Spine
):
    """What each figure stands in the order of, across the 992 areas that have it: homes
    per hectare, the distance from the middle of London's homes, and a count of every
    record of the file within the same reach."""
    density = values_of(homes_density.build(real, found, land.build(real, found)).worked)
    far: dict[str, float | None] = dict(distance_from_the_middle(found, ground_of(real, found).at))
    seen = {oa: float(made.reach.within[oa][EVERY]) for oa in made.seen}
    every = values_of(figures(seen, found))
    held = [
        held_against(str(feature), values_of(one.worked), density, far, every)
        for feature, one in built.items()
    ]
    assert [
        (one.figure, one.areas, *(round(each or 0, 2) for each in against))
        for one in held
        for against in [(one.with_density, one.with_distance, one.with_every)]
    ] == [
        ("venue_cafe", 992, 0.79, -0.79, 0.93),
        ("venue_cafe_per_homes", 992, 0.46, -0.52, 0.74),
        ("venue_gym", 992, 0.73, -0.77, 0.86),
        ("venue_gym_per_homes", 992, 0.32, -0.44, 0.55),
        ("venue_evening", 992, 0.76, -0.78, 0.89),
        ("venue_evening_per_homes", 992, 0.50, -0.57, 0.71),
    ]
    # The count of cafes follows the centre, by the rule of the check of culture, and no
    # rate does. So the count is shown, and the rate is what is ranked on.
    assert [one.figure for one in held if one.follows_the_centre] == ["venue_cafe"]


# Homes near a cluster of pubs and bars


def test_few_homes_stand_among_three_or_more_pubs_and_most_areas_read_nought(
    cluster: Exposure, found: Spine
):
    assert (len(cluster.within), cluster.nothing_seen) == (26_369, ())
    given = [one.value for one in cluster.worked.values() if one.value is not None]
    assert (len(given), sum(value == 0 for value in given)) == (1_002, 660)
    assert three_of(cluster.worked) == (0.0, 0.0, 18.8)
    homes = sum(found.homes[oa] for oa in cluster.within)
    near = sum(found.homes[oa] for oa, count in cluster.within.items() if count >= 3)
    assert round(100 * near / homes, 1) == 6.1
    assert cluster.metric.rankable and cluster.metric.unit == "%"


# The pubs of the register, against the pubs and bars of the file


@dataclass(frozen=True)
class Both:
    """The pubs of the two sources, each with the borough it stands in, or none."""

    register: venue_pub.Places
    pubs: tuple[Point, ...]
    pubs_in: tuple[str | None, ...]
    # What the register lists as a place to eat or as a takeaway.
    to_eat: tuple[Point, ...]
    of_the_file: tuple[Point, ...]
    of_the_file_in: tuple[str | None, ...]


def boroughs_of(real: Inputs, found: Spine, points: Sequence[Point]) -> tuple[str | None, ...]:
    """The borough each point stands in, by the outlines of London's LSOAs, or none."""
    opened = real.open(land.BOUNDARIES, Use.SCORING, edition=land.BOUNDARIES_EDITION)
    borough_of = {cell.lsoa: cell.borough for cell in found.cells}
    held = holding(land.read(opened, found), on_the_grid(list(points)))
    return tuple(None if lsoa is None else borough_of[lsoa] for lsoa in held)


def near(points: Sequence[Point], others: Sequence[Point], metres: int) -> list[bool]:
    """Whether each point has one of the others within so many metres."""
    of_others = kept((one[0], one[1], 0, 1) for one in others)
    return [within(of_others, point, metres, 1)[0] > 0 for point in points]


@pytest.fixture(scope="module")
def both(real: Inputs, found: Spine, made: Found) -> Both:
    register = venue_pub.build(real, found)
    places = register.register.places
    pubs = tuple((one.longitude, one.latitude) for one in places if one.group is Group.PUB)
    to_eat = tuple(
        (one.longitude, one.latitude) for one in places if one.group in (Group.EAT, Group.TAKEAWAY)
    )
    of_the_file = tuple((one.longitude, one.latitude) for one in made.of_kind(Kind.PUB))
    return Both(
        register=register,
        pubs=pubs,
        pubs_in=boroughs_of(real, found, pubs),
        to_eat=to_eat,
        of_the_file=of_the_file,
        of_the_file_in=boroughs_of(real, found, of_the_file),
    )


def test_the_file_holds_nearly_twice_the_pubs_and_bars_that_the_register_gives_a_point_for(
    both: Both,
):
    assert sum(one is not None for one in both.pubs_in) == 3_562
    assert sum(one is not None for one in both.of_the_file_in) == 6_559


def test_the_two_counts_of_pubs_stand_in_nearly_one_order_across_the_areas(
    both: Both, built: dict[FeatureId, Nearby]
):
    found: dict[str, tuple[int, float]] = {}
    for name, mine, theirs in (
        ("count", built[FeatureId.VENUE_EVENING].worked, both.register.worked),
        ("rate", built[FeatureId.VENUE_EVENING_PER_HOMES].worked, both.register.rate),
    ):
        areas = [
            area
            for area in sorted(mine)
            if mine[area].value is not None and theirs[area].value is not None
        ]
        together = rank_correlation(
            [mine[area].value or 0.0 for area in areas],
            [theirs[area].value or 0.0 for area in areas],
        )
        found[name] = (len(areas), round(together or 0, 2))
    assert found == {"count": (992, 0.90), "rate": (992, 0.79)}


def test_the_register_is_short_where_a_council_lists_few_of_its_places_as_pubs(both: Both):
    """Borough by borough, the file holds from 0.95 to 5.67 pubs and bars for each pub the
    register gives a point for. It holds most where the council lists fewest as pubs."""
    listed, held = Counter(both.pubs_in), Counter(both.of_the_file_in)
    boroughs = sorted(one for one in listed if one is not None)
    assert len(boroughs) == 33
    for_each = {borough: held[borough] / listed[borough] for borough in boroughs}
    assert (round(min(for_each.values()), 2), round(max(for_each.values()), 2)) == (0.95, 5.67)
    assert sum(one >= 1.5 for one in for_each.values()) == 22
    # The share of its places to eat and drink that each council lists as a pub.
    share = {
        one.authority: one.of(Group.PUB)
        / (one.of(Group.PUB) + one.of(Group.EAT) + one.of(Group.TAKEAWAY))
        for one in both.register.register.extracts
    }
    assert (round(min(share.values()), 2), round(max(share.values()), 2)) == (0.04, 0.18)
    fewest = min(share, key=lambda authority: share[authority])
    borough = both.register.reach.borough_of[fewest]
    assert (listed[borough], held[borough]) == (147, 834)
    assert for_each[borough] == max(for_each.values())


def test_most_pubs_of_the_register_have_a_pub_or_a_bar_of_the_file_beside_them(both: Both):
    shares = {
        metres: round(sum(near(both.pubs, both.of_the_file, metres)) / len(both.pubs), 2)
        for metres in (50, 100, 200)
    }
    assert shares == {50: 0.69, 100: 0.81, 200: 0.88}


def test_the_file_is_thin_toward_the_edge_of_london(both: Both):
    """In the boroughs where the file holds fewest pubs and bars for each pub of the
    register, which are at the edge, many pubs of the register have none of the file
    near. So the figure of an area far from the middle reads low."""
    beside = near(both.pubs, both.of_the_file, 200)
    listed = Counter(one for one in both.pubs_in if one is not None)
    found = Counter(one for one, by in zip(both.pubs_in, beside, strict=True) if one and by)
    share = sorted(round(found[borough] / listed[borough], 2) for borough in listed)
    assert share[:3] == [0.48, 0.52, 0.57] and share[-3:] == [1.0, 1.0, 1.0]
    assert sum(one < 0.75 for one in share) == 9


def test_one_in_three_pubs_and_bars_of_the_file_is_a_place_to_eat_to_the_register(both: Both):
    """It stands within 50 metres of a place the register lists as a place to eat or as a
    takeaway, and of no pub of the register. One in four has nothing of the three near."""
    in_london = [
        one for one, borough in zip(both.of_the_file, both.of_the_file_in, strict=True) if borough
    ]
    by_a_pub, by_a_place = near(in_london, both.pubs, 50), near(in_london, both.to_eat, 50)
    shares = Counter(
        "a pub" if pub else "a place to eat" if place else "neither"
        for pub, place in zip(by_a_pub, by_a_place, strict=True)
    )
    assert {what: round(count / len(in_london), 2) for what, count in shares.items()} == {
        "a pub": 0.42,
        "a place to eat": 0.33,
        "neither": 0.25,
    }
