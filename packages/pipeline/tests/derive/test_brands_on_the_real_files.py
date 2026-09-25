"""The chains of grocers, gyms and coffee, held to the file their publisher gave.

Every other test of the measures runs on made-up places and made-up chains.
These read the real file, and are skipped where the store of fetched files is
not, or where the part that was taken with the brand has no receipt. The
store is named by BURRO_STORE_FOLDER, and the file is read through its
receipt in `data/receipts/`.

They hold what must be so of any file of places, and the counts that the part
of release 2026-09-23.0 gave when it was first read. A count is of the part,
or of London as a whole. None is said of a named area, and no name of a place
is read. The name of a chain is no secret: the table of tiers names each.

Nothing is written to the store. A file is copied out of it to be read.
"""

import os
from pathlib import Path

import pytest
from burro_core.catalogue import CHAINS
from burro_core.ids import FeatureId
from burro_pipeline.cells import land, spine
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import brands_nearby, culture_file, homes_density, price_median
from burro_pipeline.derive.brand_table import folded
from burro_pipeline.derive.brands_nearby import Brands, LeftOut
from burro_pipeline.derive.culture_check import distance_from_the_middle, rank_correlation
from burro_pipeline.derive.culture_reach import ground_of
from burro_pipeline.evidence.lock import read_receipts
from burro_pipeline.evidence.row import State
from burro_pipeline.fetch.sources import load_list
from burro_pipeline.fetch.store import FOLDER_VARIABLE, FolderStore
from burro_pipeline.inputs import Inputs

from ..cells.support import REPOSITORY, registry

STORE = os.environ.get(FOLDER_VARIABLE, "")
RECEIPTS = REPOSITORY / "data" / "receipts"
FETCHED = STORE and any(
    culture_file.takes_the_brand(receipt)
    for receipt in (read_receipts(RECEIPTS) if RECEIPTS.is_dir() else ())
    if receipt.source_id == culture_file.SOURCE
)
pytestmark = pytest.mark.skipif(
    not (STORE and Path(STORE).is_dir() and FETCHED),
    reason=f"the part of the file of places with its brands is not here: {FOLDER_VARIABLE}",
)

# The places counted of each chain, in the part, when it was first read.
COUNTED = {
    "waitrose": 147,
    "mands": 253,
    "whole_foods": 5,
    "sainsburys": 471,
    "tesco": 676,
    "coop": 449,
    "morrisons": 76,
    "asda": 71,
    "aldi": 101,
    "lidl": 132,
    "iceland": 147,
    "equinox": 2,
    "barrys": 7,
    "virgin_active": 23,
    "nuffield": 48,
    "david_lloyd": 47,
    "anytime_fitness": 102,
    "puregym": 135,
    "the_gym_group": 109,
    "gails": 65,
    "ole_and_steen": 1,
    "pret": 281,
    "nero": 222,
    "starbucks": 279,
    "costa": 656,
    "blank_street": 9,
    "greggs": 343,
}
# The two chains of the founder's table that the file gives no place the brand of.
NOT_HELD = ("third_space", "gymbox")


@pytest.fixture(scope="module")
def real(tmp_path_factory: pytest.TempPathFactory) -> Inputs:
    work = tmp_path_factory.mktemp("real")
    return Inputs(registry(), read_receipts(RECEIPTS), FolderStore(Path(STORE)), work)


@pytest.fixture(scope="module")
def found(real: Inputs) -> Spine:
    return spine.build(real)


@pytest.fixture(scope="module")
def made(real: Inputs, found: Spine) -> Brands:
    return brands_nearby.build(real, found)


def figures(made: Brands, feature: FeatureId) -> dict[str, float]:
    return {area: one.value for area, one in made.worked[feature].items() if one.value is not None}


def test_the_part_that_is_read_is_the_one_the_list_takes_with_the_brand(real: Inputs):
    wanted = [file for file in load_list("m2-culture").files if file.take is not None]
    (with_brand,) = [file for file in wanted if "brand" in file.take.columns]  # pyright: ignore[reportOptionalMemberAccess]
    opened = culture_file.opened_with_the_brand(real)
    taken = opened.receipt.taken
    assert taken is not None and with_brand.take is not None
    assert taken.columns == tuple(sorted(with_brand.take.columns))
    assert (taken.box, opened.receipt.edition) == (with_brand.take.box, with_brand.edition)
    # No column that names a place was taken.
    assert not {name.split(".")[0] for name in taken.columns} & {"names", "addresses", "phones"}


def test_the_part_holds_the_brands_it_held_when_it_was_first_read(made: Brands):
    held = made.held
    assert (held.rows, held.branded, held.of_the_table) == (683_409, 58_882, 5_579)
    assert len(held.places) == sum(held.counted.values()) == 4_857
    assert {key: count for key, count in held.counted.items() if count} == COUNTED
    # A place is counted once: what is left out is left out for a reason that is said.
    left_out = {reason: 0 for reason in LeftOut}
    for reasons in held.left_out.values():
        for reason, count in reasons.items():
            left_out[reason] += count
    assert left_out == {
        LeftOut.NOT_OF_ITS_KIND: 654,
        LeftOut.CLOSED: 0,
        LeftOut.NO_POINT: 0,
        LeftOut.COUNTED_ALREADY: 68,
    }
    assert held.of_the_table == len(held.places) + sum(left_out.values())


def test_the_file_holds_no_place_of_two_chains_of_the_founders_table(made: Brands):
    """Nothing is filled in: each is on the table, and no release carries a figure for it."""
    for key in NOT_HELD:
        assert not made.held.written.get(key) and not made.held.counted.get(key)
        assert figures(made, FeatureId(f"brand_{key}")) == {}
    assert {key for key in made.table.by_key if not made.held.counted.get(key)} == set(NOT_HELD)


def test_every_spelling_of_the_table_is_one_the_file_writes(made: Brands):
    """A spelling the file does not write finds nothing, and nothing says so. This does."""
    for chain in made.table.chains:
        written = {folded(name) for name in made.held.written.get(chain.key, {})}
        assert {folded(name) for name in chain.spellings} == written, chain.key


def test_a_brand_is_given_by_two_sources_and_by_no_other(made: Brands):
    """The licence registry says which source is under which licence. A source that names a
    chain here for the first time fails this test, so that a person reads its licence first."""
    assert set(made.held.name_chains) == {"AllThePlaces", "Overture-signals", "meta"}
    assert all(
        set(place.datasets) <= {"AllThePlaces", "Overture", "meta"} for place in made.held.places
    )
    assert (len(made.held.eating), made.held.eating_of_no_such_source) == (52_099, 19_571)


def test_every_measure_has_a_row_for_every_area_and_no_figure_stands_on_under_half_its_homes(
    made: Brands, found: Spine
):
    assert set(made.worked) == set(brands_nearby.FEATURES)
    for worked in made.worked.values():
        assert set(worked) == set(found.weights.areas)
        for one in worked.values():
            assert (one.value is None) == (one.state not in (State.PRESENT, State.PARTIAL))
            assert one.value is None or (one.weight_covered >= 0.5 and one.value >= 0)
    assert made.nothing_seen == ()


def test_the_mix_and_the_share_of_independent_places_are_shares(made: Brands):
    mix = figures(made, FeatureId.BRAND_MIX)
    independent = figures(made, FeatureId.INDEPENDENTS_NEARBY)
    assert (len(mix), len(independent)) == (990, 992)
    assert all(0 <= value <= 100 for value in (*mix.values(), *independent.values()))
    # The mix is spread across the scale. Independent places run in a narrow band at the top.
    assert (min(mix.values()), max(mix.values())) == (3.7, 84.5)
    assert (min(independent.values()), max(independent.values())) == (58.1, 100.0)


def test_a_distance_is_in_whole_tens_of_metres_and_never_beyond_how_far_it_is_looked_for(
    made: Brands,
):
    of_a_chain = {feature: figures(made, feature) for feature in CHAINS}
    assert sum(1 for held in of_a_chain.values() if held) == len(CHAINS) - len(NOT_HELD)
    for held in of_a_chain.values():
        assert all(0 <= value <= 2_000 and value == round(value, -1) for value in held.values())
    assert len(of_a_chain[FeatureId.BRAND_TESCO]) == 971
    assert len(of_a_chain[FeatureId.BRAND_WAITROSE]) == 442


def test_what_the_mix_follows_is_what_the_row_of_the_proxy_audit_says(
    real: Inputs, made: Brands, found: Spine
):
    """The row was written before the mix was served. It quotes these, to two places."""
    density = homes_density.build(real, found, land.build(real, found)).worked
    price = price_median.build(real, found).worked
    against = {
        "homes per hectare": {area: one.value for area, one in density.items()},
        "distance from the middle": distance_from_the_middle(found, ground_of(real, found).at),
        "what homes sell for": {area: one.value for area, one in price.items()},
    }

    def follows(feature: FeatureId) -> dict[str, float | None]:
        held = figures(made, feature)
        said: dict[str, float | None] = {}
        for name, other in against.items():
            both = [area for area in sorted(held) if other.get(area) is not None]
            stands = rank_correlation(
                [held[area] for area in both], [float(other[area] or 0) for area in both]
            )
            said[name] = None if stands is None else round(stands, 2)
        return said

    assert follows(FeatureId.BRAND_MIX) == {
        "homes per hectare": 0.04,
        "distance from the middle": -0.21,
        "what homes sell for": 0.48,
    }
    assert follows(FeatureId.INDEPENDENTS_NEARBY) == {
        "homes per hectare": 0.01,
        "distance from the middle": -0.07,
        "what homes sell for": -0.10,
    }
