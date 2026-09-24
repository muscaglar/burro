"""Places to eat and drink, worked out from the files their publishers gave.

Every other test of the measure runs on a made-up register. These read the 33
real files, and are skipped where the store of fetched files is not. The store
is named by BURRO_STORE_FOLDER, and each file is read through its receipt in
`data/receipts/`.

The four measures of the register are held here together: places to eat and
drink, pubs and bars, places to eat, and takeaways. They are counted from the
same files in one pass, so one module reads the files once.

They hold counts and a few figures, so that a file that changes is noticed. A
figure here is London's lowest, its middle, or the figure that nine areas in
ten do not pass. The highest is not held: one area of London is a borough on
its own, and it leads some of these, so its figure would be the figure of a
named place. None is said of a named area or of a named borough, and no
business is named. Each was worked out on 2026-09-24, from the extracts of
2026-09-09 to 2026-09-16. A second program, written apart from the first,
came to the same figures, and no person has checked one.

Contains public sector information licensed under the Open Government Licence
v3.0. Source: Food Standards Agency. Source: Office for National Statistics
licensed under the Open Government Licence v.3.0. Contains OS data © Crown
copyright and database right [year].

Nothing is written to the store. A file is copied out of it to be read.
"""

import statistics
from collections import Counter
from collections.abc import Mapping
from pathlib import Path

import pytest
from burro_pipeline.cells import centres, spine
from burro_pipeline.cells.shapes import longitude_and_latitude
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import (
    culture_reach,
    measures,
    venue_eat,
    venue_evening,
    venue_food_drink,
    venue_takeaway,
)
from burro_pipeline.derive.food_register import Group
from burro_pipeline.derive.methods import Worked
from burro_pipeline.derive.venue_food_drink import COUNTED, METRES, AtHomes, Venues
from burro_pipeline.evidence.receipt import Period
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

from ..cells.support import registry
from .food_real_files import SKIPPED, STORE, listing, real_inputs

pytestmark = SKIPPED


@pytest.fixture(scope="module")
def before() -> dict[str, tuple[int, int]]:
    return listing()


@pytest.fixture(scope="module")
def real(tmp_path_factory: pytest.TempPathFactory, before: dict[str, tuple[int, int]]) -> Inputs:
    return real_inputs(tmp_path_factory.mktemp("real"))


@pytest.fixture(scope="module")
def found(real: Inputs) -> Spine:
    return spine.build(real)


@pytest.fixture(scope="module")
def made(real: Inputs, found: Spine) -> Venues:
    return venue_food_drink.build(real, found)


@pytest.fixture(scope="module")
def others(real: Inputs, found: Spine) -> dict[str, AtHomes]:
    """The three other measures of the register, each by the id its rows are written under."""
    return {
        "venue_evening": venue_evening.build(real, found),
        "venue_eat": venue_eat.build(real, found),
        "venue_takeaway": venue_takeaway.build(real, found),
    }


def three_of(worked: Mapping[str, Worked]) -> tuple[float, float, float]:
    """London's lowest and middle figure, and the figure nine areas in ten do not pass.

    The middle of two is given to two places. The highest is never held: it may be the
    figure of the one area that is a borough on its own.
    """
    values = sorted(one.value for one in worked.values() if one.value is not None)
    return values[0], round(statistics.median(values), 2), values[(9 * len(values)) // 10]


# The register is held to London


def test_every_borough_of_london_has_its_file_and_each_file_is_of_one_borough(
    made: Venues, found: Spine
):
    """It is how nought is known to be a count. A borough with no file stops the build."""
    boroughs = {cell.borough for cell in found.cells}
    assert len(made.register.extracts) == len(boroughs) == 33
    assert set(made.reach.borough_of) == {one.authority for one in made.register.extracts}
    assert set(made.reach.borough_of.values()) == boroughs


def test_so_many_places_that_count_have_a_point_and_so_many_have_none(made: Venues):
    counted = venue_food_drink.COUNTED
    listed = sum(made.register.listed(group) for group in counted)
    placed = sum(made.register.placed(group) for group in counted)
    assert (listed, placed, listed - placed) == (40_558, 37_013, 3_545)
    assert made.register.listed(Group.EAT) == 27_262


# What is within reach


def test_the_homes_near_the_edge_of_london_have_no_verdict(made: Venues, found: Spine):
    """A home outside London is within 800 metres, so a place outside London may be."""
    near = made.reach.near_the_edge
    assert (len(near), len(made.reach.places)) == (311, 26_058)
    assert len(near) + len(made.reach.places) == len(found.cells) == 26_369
    assert sum(found.homes[oa] for oa in near) == 40_373
    assert sum(found.homes.values()) == 3_423_767


def test_the_sum_is_the_same_counted_from_the_homes_and_from_the_places(
    real: Inputs, made: Venues, found: Spine
):
    """Every pair of a centre and a place within reach of it, counted both ways.

    A distance is measured at the latitude of the home, so a pair within a few
    centimetres of 800 metres can fall either way. Fewer than 1 in 100,000 do.
    """
    from_homes = sum(sum(held) for held in made.reach.places.values())
    by_group = [sum(held[n] for held in made.reach.places.values()) for n in range(3)]
    assert (from_homes, by_group) == (2_185_994, [1_482_308, 199_357, 504_329])
    at = centres.build(real, found)
    with_a_verdict = culture_reach.kept(
        (*longitude_and_latitude(*at[oa]), 0, 1) for oa in made.reach.places
    )
    from_places = sum(
        culture_reach.within(with_a_verdict, (place.longitude, place.latitude), METRES, 1)[0]
        for place in made.register.places
        if place.group in COUNTED
    )
    assert abs(from_places - from_homes) == 15


def test_few_homes_have_no_place_to_eat_or_drink_within_reach(made: Venues):
    none = sum(1 for held in made.reach.places.values() if sum(held) == 0)
    no_pub = sum(1 for held in made.reach.places.values() if held[1] == 0)
    assert (none, no_pub) == (60, 2_072)


# The figures


def test_all_but_ten_areas_have_a_figure_and_thirty_have_one_for_part_of_their_homes(
    made: Venues,
):
    assert len(made.worked) == 1_002
    states = {State.PRESENT: 962, State.PARTIAL: 30, State.BELOW_THRESHOLD: 10}
    assert Counter(one.state for one in made.worked.values()) == states
    assert Counter(one.state for one in made.rate.values()) == states
    part = sorted(one.weight_covered for one in made.worked.values() if one.value is not None)
    assert part[0] == 0.552832
    assert {one.flags for one in made.worked.values()} == {()}


def test_the_lowest_the_middle_and_the_ninth_in_ten_are_what_was_worked_out(made: Venues):
    assert three_of(made.worked) == (3.1, 51.5, 163.2)
    assert three_of(made.rate) == (1.2, 8.2, 15.9)


def test_no_area_reads_nought(made: Venues):
    assert sum(one.value == 0 for one in made.worked.values()) == 0


# The three other measures


def test_each_kind_alone_comes_to_what_it_came_to(others: dict[str, AtHomes]):
    """For each: London's lowest, middle and ninth in ten, of the count and then for 1,000 homes."""
    found = {key: (three_of(one.worked), three_of(one.rate)) for key, one in others.items()}
    assert found == {
        "venue_evening": ((0.0, 4.5, 15.7), (0.0, 0.7, 1.7)),
        "venue_eat": ((0.6, 30.05, 113.2), (0.2, 4.9, 11.3)),
        "venue_takeaway": ((0.2, 13.65, 36.8), (0.1, 2.1, 4.3)),
    }


def test_each_kind_alone_has_a_figure_where_the_three_together_have_one(
    made: Venues, others: dict[str, AtHomes]
):
    for one in others.values():
        assert len(one.rows) == len(one.rows_of_the_rate) == 1_002
        assert {area: held.state for area, held in one.worked.items()} == {
            area: held.state for area, held in made.worked.items()
        }
        assert one.files == made.files and one.reach == made.reach


def test_a_few_areas_read_nought_for_pubs_and_none_for_the_other_kinds(
    others: dict[str, AtHomes], found: Spine
):
    """Nought to one decimal place. In three of the five no home has a pub within reach."""
    nought = {
        key: sum(held.value == 0 for held in one.worked.values()) for key, one in others.items()
    }
    assert nought == {"venue_evening": 5, "venue_eat": 0, "venue_takeaway": 0}
    pubs = others["venue_evening"]
    within = pubs.reach.of(pubs.counted.groups)
    none_at_all = sum(
        pubs.worked[area].value is not None and all(within[oa] == 0 for oa in oas if oa in within)
        for area, oas in found.weights.of_area.items()
    )
    assert none_at_all == 3


# The evidence


def test_every_figure_rests_on_the_33_files_the_centres_the_lookup_and_the_homes(made: Venues):
    assert len(made.rows) == len(made.rows_of_the_rate) == 1_002
    by_source = Counter(receipt.source_id for receipt in made.files)
    assert by_source == {
        "fsa-food-hygiene-ratings": 33,
        "ons-census-2021-housing-tables": 1,
        "ons-oa-pwc-2021": 1,
        "ons-oa21-lsoa21-msoa21-lad22-lookup": 1,
    }
    every = tuple(sorted(receipt.file_id for receipt in made.files))
    assert {row.inputs for row in (*made.rows, *made.rows_of_the_rate)} == {every}
    assert {row.derivation_id for row in made.rows} == {"places_within_800m_at_homes@1"}
    # From the day of the census, which the weights are of, to the day of the newest extract.
    span = Period(start="2021-03-21", end="2026-09-16")
    assert all(row.data_period == span for row in made.rows)
    rows = (*made.rows, *made.rows_of_the_rate)
    assert Evidence.of("lon-2026-10-02-01", made.files, venue_food_drink.METHODS, rows)


def test_the_row_of_the_catalogue_carries_the_days_of_the_extracts_and_is_cores(
    made: Venues,
):
    assert made.metric.vintage == "2026-09-09 to 2026-09-16"
    assert "as at 2026-09-09 to 2026-09-16" in made.metric.definition
    assert measures.says_what_core_says(made.metric)
    assert (made.metric.unit, made.metric.rankable) == ("count", False)
    for source_id in made.metric.source_ids:
        assert Use.SCORING in registry().get(source_id).uses


def test_the_files_are_read_from_copies_and_the_store_is_as_it_was(
    real: Inputs, made: Venues, before: dict[str, tuple[int, int]]
):
    assert len(real.opened) == 36
    assert Path(STORE).resolve() not in real.work.resolve().parents
    # Other steps may add a file to the store while this runs. None that was there has changed.
    after = listing()
    assert {name: after.get(name) for name in before} == before
