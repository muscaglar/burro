"""Brands nearby, from the part of the file that holds the brand to a figure for each area.

Every file here is made up, and says so: `culture_support.py` draws the town
and writes its places. No shop here exists. A made-up place bears the brand of
a chain of the table, written as the real file writes it, so that the table is
read as a build reads it. The centres stand 1,000 metres apart, so that a home
is within reach of what stands by its own centre and of little else, and every
figure can be made by hand:

    Quillhaven 001   Q1  a premium grocer 100 metres east, and its bank beside it
                     Q2  a value grocer on the centre, and a mid-range coffee place 50 metres north
                     Q3  a mid-range gym 300 metres north
                     Q4  nothing of a tier
    Quillhaven 002   R1  three places to eat: one of a chain, two of none
    Tallowgate 001   nothing but the shop that stands by every centre

A shop of no chain stands 30 metres south of every centre, so that the file is
seen to hold something within reach of every home.
"""

from pathlib import Path

import pytest
from burro_core.catalogue import FEATURES, SHOWN_BESIDE_THE_MIX
from burro_core.ids import FeatureId, NativeResolution
from burro_pipeline.cells import spine
from burro_pipeline.derive import brands_nearby, measures
from burro_pipeline.derive.brand_table import Kind, Tier, the_table
from burro_pipeline.derive.brands_nearby import (
    EVERY,
    INDEPENDENT,
    MIX,
    NEAREST_WITHIN,
    OF_A_CHAIN,
    OF_NO_CHAIN,
    WITHIN,
    Brands,
    LeftOut,
    slot_of,
)
from burro_pipeline.derive.measures import says_what_core_says
from burro_pipeline.derive.methods import Worked
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.row import State

from ..fetch.parquet_support import Place
from .culture_support import (
    CANARY,
    COLUMNS,
    DAY,
    EDITION,
    OAS,
    ONE,
    Q1,
    Q2,
    Q3,
    Q4,
    R1,
    SHOP,
    SOURCE,
    THREE,
    TWO,
    Wanted,
    beside,
    centre_of,
    inputs_of,
    place,
)

WITH_THE_BRAND = Wanted(columns=(*COLUMNS, "brand"))
GROCERY = ("shopping", "food_and_beverage_store", "grocery_store")
CONVENIENCE = ("shopping", "convenience_store")
ATM = ("services_and_business", "financial_service", "atm")
GYM = ("sports_and_recreation", "sport_or_fitness_facility", "gym")
COFFEE = ("food_and_drink", "non_alcoholic_beverage_venue", "coffee_shop")
BAKERY = ("food_and_drink", "casual_eatery", "bakery")
RESTAURANT = ("food_and_drink", "restaurant")
PUB = ("food_and_drink", "alcoholic_beverage_venue", "bar", "pub")
# The brand of a chain of the table, as the real file writes it, and the brand of a chain
# that is on no row.
WAITROSE, LIDL = ("Waitrose & Partners", None), ("Lidl", "Q151954")
STARBUCKS, NUFFIELD = ("Starbucks", None), ("Nuffield Health", None)
OFF_THE_TABLE = ("Gildcrest", None)
OA_Q1, OA_Q2, OA_Q3, OA_Q4 = OAS[:4]
OA_R1 = OAS[4]
PREMIUM_GROCER = slot_of(Kind.GROCER, Tier.PREMIUM)
VALUE_GROCER = slot_of(Kind.GROCER, Tier.VALUE)
MID_COFFEE = slot_of(Kind.COFFEE, Tier.MID)
MID_GYM = slot_of(Kind.GYM, Tier.MID)


def shop(at: tuple[float, float], path: tuple[str, ...], brand: object = None, **said: object):
    return place(at, path, brand=brand, **said)


# A shop of no chain stands by every centre, so that the file is seen to hold something.
BY_EVERY_CENTRE = tuple(shop(beside(centre_of(oa), 0, -30), SHOP) for oa in OAS)
IN_THE_TOWN = (
    *BY_EVERY_CENTRE,
    shop(beside(Q1, 100), GROCERY, WAITROSE),
    shop(beside(Q1, 110), ATM, WAITROSE),
    shop(Q2, GROCERY, LIDL),
    shop(beside(Q2, 0, 50), COFFEE, STARBUCKS),
    shop(beside(Q3, 0, 300), GYM, NUFFIELD),
    shop(beside(R1, 0, 100), RESTAURANT, OFF_THE_TABLE),
    shop(beside(R1, 100), RESTAURANT),
    shop(beside(R1, -100), PUB),
)


def built(folder: Path, *places: Place, centres: bytes | None = None, **how: object) -> Brands:
    given = places if places else IN_THE_TOWN
    inputs = inputs_of(folder, given, centres, wanted=WITH_THE_BRAND, **how)  # pyright: ignore[reportArgumentType]
    return brands_nearby.build(inputs, spine.build(inputs))


@pytest.fixture
def town(tmp_path: Path) -> Brands:
    return built(tmp_path)


def value_of(worked: Worked) -> float:
    assert worked.value is not None
    return worked.value


def figure(made: Brands, feature: FeatureId, area: str = ONE) -> float:
    return value_of(made.worked[feature][area])


# Which place counts


def test_the_two_distances_are_those_the_names_of_the_measures_state():
    assert (WITHIN, NEAREST_WITHIN) == (800, 2_000)
    assert "within 800 m" in FEATURES[FeatureId.GROCER_PREMIUM_NEARBY].label
    assert "within 2,000 m" in FEATURES[FeatureId.GROCER_PREMIUM_DISTANCE].label
    assert "within 2,000 m" in FEATURES[FeatureId.BRAND_WAITROSE].label
    assert "within 800 m" in FEATURES[MIX].label and "within 800 m" in FEATURES[INDEPENDENT].label


def test_a_place_of_a_chain_of_the_table_is_counted_in_the_tier_of_the_chain(town: Brands):
    assert town.within[OA_Q1][PREMIUM_GROCER] == 1
    assert town.within[OA_Q2][VALUE_GROCER] == 1 and town.within[OA_Q2][MID_COFFEE] == 1
    assert town.within[OA_Q3][MID_GYM] == 1
    assert sum(town.within[OA_Q4][:OF_NO_CHAIN]) == 0
    assert town.held.counted["waitrose"] == 1 and town.held.counted["lidl"] == 1


def test_a_bank_of_a_chain_of_grocers_is_no_grocer(town: Brands):
    """It bears the brand, and the file gives it no category of a grocer."""
    assert town.held.written["waitrose"] == {"Waitrose & Partners": 2}
    assert town.held.left_out["waitrose"] == {LeftOut.NOT_OF_ITS_KIND: 1}
    assert town.within[OA_Q1][PREMIUM_GROCER] == 1


def test_a_place_of_a_chain_that_is_on_no_row_has_no_tier(town: Brands):
    assert sum(town.within[OA_R1][:OF_NO_CHAIN]) == 0
    assert town.within[OA_R1][OF_A_CHAIN] == 1


def test_a_place_that_has_closed_for_good_or_has_no_point_is_left_out(tmp_path: Path):
    nowhere = b"\x01\x01\x00\x00\x00" + b"\x00\x00\x00\x00\x00\x00\xf8\x7f" * 2
    made = built(
        tmp_path,
        *BY_EVERY_CENTRE,
        shop(beside(Q1, 100), GROCERY, WAITROSE, status="permanently_closed"),
        shop(beside(Q1, 200), GROCERY, WAITROSE, status="temporarily_closed"),
        shop(beside(Q1, 300), GROCERY, WAITROSE, geometry=nowhere),
        shop(beside(Q1, 400), GROCERY, WAITROSE, status=None),
    )
    assert made.held.left_out["waitrose"] == {LeftOut.CLOSED: 1, LeftOut.NO_POINT: 1}
    assert made.within[OA_Q1][PREMIUM_GROCER] == 2


def test_places_of_one_chain_within_25_metres_are_one_place(tmp_path: Path):
    made = built(
        tmp_path,
        *BY_EVERY_CENTRE,
        shop(beside(Q1, 100), GROCERY, WAITROSE),
        shop(beside(Q1, 120), CONVENIENCE, ("Little Waitrose", "Q771734")),
        shop(beside(Q1, 130), GROCERY, WAITROSE),
        # A place of another chain of the same tier beside them is a place of its own.
        shop(beside(Q1, 110), GROCERY, ("Marks and Spencer", None)),
    )
    assert made.held.left_out["waitrose"] == {LeftOut.COUNTED_ALREADY: 1}
    assert made.held.counted["waitrose"] == 2 and made.held.counted["mands"] == 1
    assert made.within[OA_Q1][PREMIUM_GROCER] == 3


# The places of a tier, and the nearest


def test_the_places_of_a_tier_are_the_mean_over_the_homes_of_an_area(town: Brands):
    assert figure(town, FeatureId.GROCER_PREMIUM_NEARBY) == round(110 / 500, 1) == 0.2
    assert figure(town, FeatureId.GROCER_VALUE_NEARBY) == round(120 / 500, 1) == 0.2
    assert figure(town, FeatureId.COFFEE_MID_NEARBY) == 0.2
    assert figure(town, FeatureId.GYM_MID_NEARBY) == round(130 / 500, 1) == 0.3
    assert figure(town, FeatureId.GYM_PREMIUM_NEARBY) == 0.0
    assert figure(town, FeatureId.GROCER_PREMIUM_NEARBY, TWO) == 0.0


def test_the_nearest_of_a_tier_is_the_median_over_the_homes_that_have_one(town: Brands):
    """The premium grocer is 100 metres from Q1, 900 from Q2, 1,900 from Q3 and 2,900 from Q4.

    So three of the four have one within 2,000 metres, with 360 of the area's
    500 homes. Half of 360 is 180: Q1 holds 110 and Q2 brings them to 230, so
    the median is Q2's.
    """
    found = town.worked[FeatureId.GROCER_PREMIUM_DISTANCE][ONE]
    assert found.value == 900.0 and found.state is State.PARTIAL
    assert found.weight_covered == round(360 / 500, 6)
    # A distance on the ground is a little under the distance on the grid.
    assert [round(far, -1) for far in _far(town, PREMIUM_GROCER)] == [100, 900, 1900]


def _far(made: Brands, slot: int) -> list[float]:
    found = (made.nearest_of_a_tier[oa][slot] for oa in (OA_Q1, OA_Q2, OA_Q3, OA_Q4))
    return [far for far in found if far is not None]


def test_a_place_further_than_2000_metres_is_not_known_to_be_the_nearest(town: Brands):
    assert town.nearest_of_a_tier[OA_Q4][PREMIUM_GROCER] is None
    # No home of the second area or of the third has one within 2,000 metres.
    for area in (TWO, THREE):
        found = town.worked[FeatureId.GROCER_PREMIUM_DISTANCE][area]
        assert (found.value, found.state) == (None, State.SOURCE_GAP)


def test_a_distance_is_given_to_the_nearest_10_metres(tmp_path: Path):
    """A gym 344 metres north of Q2 is 1,057 metres from Q1 and from Q3, and out of reach of Q4.

    Half of the 360 homes that have one is 180. Q2 holds 120 and Q1 brings
    them to 230, so the median is the 1,057 metres of Q1.
    """
    made = built(tmp_path, *BY_EVERY_CENTRE, shop(beside(Q2, 0, 344), GYM, NUFFIELD))
    near, far = (made.nearest_of_a_tier[oa][MID_GYM] for oa in (OA_Q2, OA_Q1))
    assert near is not None and 343 < near < 344
    assert far is not None and 1_056 < far < 1_058
    assert made.worked[FeatureId.GYM_MID_DISTANCE][ONE].value == 1_060.0
    assert made.worked[FeatureId.BRAND_NUFFIELD][ONE].value == 1_060.0


def test_the_nearest_of_a_chain_is_measured_to_the_places_of_that_chain_alone(tmp_path: Path):
    made = built(
        tmp_path,
        *BY_EVERY_CENTRE,
        shop(beside(Q1, 0, 200), GROCERY, WAITROSE),
        shop(beside(Q1, 0, 100), GROCERY, ("Marks and Spencer", None)),
        shop(beside(Q2, 0, 100), GROCERY, ("Whole Foods Market", None)),
        shop(beside(Q3, 0, 100), GROCERY, ("Marks & Spencer", "Q714491")),
        shop(beside(Q4, 0, 100), GROCERY, ("Marks and Spencer", None)),
    )
    # Every home has a premium grocer 100 metres off, and an M&S is that near to three in four.
    assert figure(made, FeatureId.GROCER_PREMIUM_DISTANCE) == 100.0
    assert figure(made, FeatureId.BRAND_MANDS) == 100.0
    # The one Waitrose is 200 metres from Q1, and about 1,020, 2,010 and 3,007 from the rest.
    found = made.worked[FeatureId.BRAND_WAITROSE][ONE]
    assert (found.value, found.state) == (None, State.BELOW_THRESHOLD)
    assert made.worked[FeatureId.BRAND_TESCO][ONE].state is State.SOURCE_GAP


def test_a_chain_the_file_holds_no_place_of_has_a_distance_nowhere(town: Brands):
    for feature in (FeatureId.BRAND_THIRD_SPACE, FeatureId.BRAND_GYMBOX, FeatureId.BRAND_ASDA):
        assert {one.value for one in town.worked[feature].values()} == {None}


# The mix


def test_the_mix_is_the_share_that_are_premium_with_a_mid_range_place_counted_as_half(
    town: Brands,
):
    """Added up over homes: Q1 has one premium. Q2 has one value and one mid. Q3 has one mid.

    So the top is 110 + 120 / 2 + 130 / 2 and the bottom is 110 + 2 * 120 + 130.
    """
    assert figure(town, MIX) == round(100 * (110 + 60 + 65) / (110 + 240 + 130), 1) == 49.0


@pytest.mark.parametrize(
    ("brand", "path", "mix"),
    [(WAITROSE, GROCERY, 100.0), (STARBUCKS, COFFEE, 50.0), (LIDL, GROCERY, 0.0)],
)
def test_the_mix_runs_from_nought_where_all_is_value_to_a_hundred_where_all_is_premium(
    tmp_path: Path, brand: tuple[str, str | None], path: tuple[str, ...], mix: float
):
    made = built(tmp_path, *BY_EVERY_CENTRE, shop(Q1, path, brand), shop(Q3, path, brand))
    assert figure(made, MIX) == mix


def test_an_area_with_no_place_of_a_tier_within_reach_has_no_mix(town: Brands):
    """It is not in the middle, and it is not nought: there is nothing to take a share of."""
    for area in (TWO, THREE):
        assert town.worked[MIX][area].value is None


# Independent places


def test_independent_places_are_the_share_of_the_places_to_eat_and_drink_of_no_chain(
    town: Brands,
):
    assert town.within[OA_R1][OF_NO_CHAIN] == 2 and town.within[OA_R1][OF_A_CHAIN] == 1
    assert figure(town, INDEPENDENT, TWO) == round(100 * 2 / 3, 1) == 66.7
    # The one place to eat or drink of the first area is a coffee place of a chain.
    assert figure(town, INDEPENDENT, ONE) == 0.0
    assert town.worked[INDEPENDENT][THREE].value is None


def test_a_place_that_no_source_that_names_chains_gave_is_counted_on_neither_side(
    tmp_path: Path,
):
    """The file gives a brand only to places that some of its sources gave."""
    made = built(
        tmp_path,
        *BY_EVERY_CENTRE,
        shop(beside(R1, 0, 100), RESTAURANT, OFF_THE_TABLE, dataset="meta"),
        shop(beside(R1, 100), RESTAURANT, dataset="meta"),
        shop(beside(R1, -100), RESTAURANT, dataset="made-up-source"),
        shop(beside(R1, 0, -100), BAKERY, dataset="made-up-source"),
    )
    assert made.held.name_chains == ("meta",)
    assert made.held.eating_of_no_such_source == 2
    assert figure(made, INDEPENDENT, TWO) == 50.0


def test_a_shop_is_no_place_to_eat_or_drink(town: Brands):
    assert town.within[OA_Q1][OF_NO_CHAIN] == 0
    assert town.within[OA_Q1][EVERY] == 3


# When nought is a count, and the edge


def test_nought_is_a_count_only_where_the_file_holds_something_within_reach(tmp_path: Path):
    made = built(tmp_path, *BY_EVERY_CENTRE[:4], shop(beside(Q1, 100), GROCERY, WAITROSE))
    assert made.worked[FeatureId.GROCER_VALUE_NEARBY][ONE].value == 0.0
    assert made.worked[FeatureId.GROCER_VALUE_NEARBY][TWO].value is None
    assert set(made.nothing_seen) == set(OAS[4:])


def test_the_same_places_in_any_order_give_the_same_figures(tmp_path: Path):
    one = built(tmp_path / "a", *IN_THE_TOWN)
    other = built(tmp_path / "b", *reversed(IN_THE_TOWN), rows_in_a_group=3)
    assert one.worked == other.worked and one.held.places == other.held.places


def test_what_is_worked_out_is_kept_for_the_next_measure_that_asks(tmp_path: Path):
    inputs = inputs_of(tmp_path, IN_THE_TOWN, wanted=WITH_THE_BRAND)
    found = spine.build(inputs)
    assert brands_nearby.build(inputs, found) is brands_nearby.build(inputs, found)


# What stands behind a figure


def test_no_name_of_a_place_is_held(town: Brands):
    assert CANARY not in repr(town.held) and CANARY not in repr(town.worked)


@pytest.mark.parametrize("feature", brands_nearby.FEATURES, ids=str)
def test_every_measure_says_what_core_says_and_names_its_method(town: Brands, feature: FeatureId):
    one = town.one(feature)
    assert says_what_core_says(one.metric)
    assert one.metric.rankable is (feature not in SHOWN_BESIDE_THE_MIX)
    assert one.metric.native_resolution is NativeResolution.POINT
    assert SOURCE in one.metric.source_ids and one.metric.vintage == DAY
    assert set(one.metric.source_ids) == {file.source_id for file in town.files}
    assert [row.fact_id for row in one.rows] == [
        f"{area}/feature/{feature.value}" for area in sorted(one.worked)
    ]
    method = brands_nearby.method_of(feature)
    assert {row.derivation_id for row in one.rows} == {method.derivation_id}
    assert all(row.value == one.worked[row.area_id].value for row in one.rows)
    said = one.metric.definition
    assert said.endswith(".") and "\n" not in said and CANARY not in said
    assert f"release {EDITION} of Overture Maps Places" in said and DAY in said


def test_a_row_of_evidence_rests_on_the_part_that_holds_the_brand(town: Brands):
    part = [file for file in town.files if file.source_id == SOURCE]
    assert len(part) == 1 and part[0].taken is not None and "brand" in part[0].taken.columns
    row = town.one(MIX).rows[0]
    assert set(row.inputs) == {file.file_id for file in town.files}


def test_a_measure_of_a_tier_says_which_chains_the_table_gives_it(town: Brands):
    said = town.one(FeatureId.GROCER_PREMIUM_NEARBY).metric.definition
    assert "Waitrose, M&S or Whole Foods" in said
    assert "which is a judgement and no finding" in said
    assert "within 800 metres in a straight line" in said and "within 25 metres" in said
    said = town.one(FeatureId.GYM_VALUE_DISTANCE).metric.definition
    assert "PureGym or The Gym Group" in said and "within 2,000 metres" in said
    assert "to the nearest 10 metres" in said
    mix = town.one(MIX).metric.definition
    assert "a mid-range place counted as 0.5 of one" in mix
    assert "premium are Waitrose, M&S, Whole Foods, Equinox, Third Space, Barry's" in mix


def test_every_chain_the_table_holds_is_in_the_sentence_of_the_mix(town: Brands):
    mix = town.one(MIX).metric.definition
    assert all(chain.name in mix for chain in the_table().chains)


def test_what_a_figure_cannot_see_says_that_it_counts_shops_and_not_who_shops():
    for feature in brands_nearby.FEATURES:
        said = brands_nearby.cannot_see(feature)
        assert all(line.endswith(".") and "\n" not in line for line in said)
        assert len(set(said)) == len(said)
        if feature is not INDEPENDENT:
            assert brands_nearby.PLACES_NOT_PEOPLE in said
    assert brands_nearby.A_JUDGEMENT in brands_nearby.cannot_see(MIX)
    assert brands_nearby.FEW_PLACES in brands_nearby.cannot_see(MIX)
    assert brands_nearby.NOT_EVERY_SOURCE in brands_nearby.cannot_see(INDEPENDENT)


def test_every_measure_of_brands_is_on_the_list_of_the_measures_of_a_build():
    listed = {measure.feature: measure for measure in measures.MEASURES}
    assert set(brands_nearby.FEATURES) <= set(listed)
    assert len(brands_nearby.FEATURES) == 9 + 9 + 1 + 29 + 1
    for feature in brands_nearby.FEATURES:
        measure = listed[feature]
        assert measure.source == SOURCE and measure.reads("part-00007-made-up.zstd.parquet")
        assert measure.methods == (brands_nearby.method_of(feature),)
        assert measure.cannot_see == brands_nearby.cannot_see(feature)
        assert not measure.waits_on and not measure.held_back
    assert [m.feature.value for m in measures.MEASURES] == sorted(
        m.feature.value for m in measures.MEASURES
    )


def test_a_measure_is_worked_out_as_the_list_of_measures_calls_it(tmp_path: Path):
    from burro_pipeline.cells.land import Land

    inputs = inputs_of(tmp_path, IN_THE_TOWN, wanted=WITH_THE_BRAND)
    ground = measures.Ground(spine.build(inputs), Land({}, {}, "f-000000000000"))
    listed = {measure.feature: measure for measure in measures.MEASURES}
    made = listed[MIX].build(inputs, ground)
    assert value_of(made.worked[ONE]) == 49.0 and made.metric.feature_id is MIX


def test_a_build_with_no_part_that_holds_the_brand_works_no_measure_of_brands_out(
    tmp_path: Path,
):
    """The part that culture reads holds no brand, and is not read in its place."""
    inputs = inputs_of(tmp_path, IN_THE_TOWN)
    with pytest.raises(LockError) as stopped:
        brands_nearby.build(inputs, spine.build(inputs))
    assert stopped.value.rule == "input_has_one_receipt"
