"""The nearest food shop, from the file of places to a distance for each area.

Every file here is made up, and says so: the shops stand in the town that
`culture_support.py` draws, whose centres stand 1,000 metres apart in three
rows, 5,000 metres apart. Every place is made up, and every name in the file
is the canary.

    north 10,000   T1  T2  T3  T4     Tallowgate 001   homes 190, 200, 210, 220
    north  5,000   R1  R2  R3  R4     Quillhaven 002   homes 150, 160, 170, 180
    north      0   Q1  Q2  Q3  Q4     Quillhaven 001   homes 110, 120, 130, 140
            east   0  1,000  2,000  3,000

A grocer stands 100 metres east of Q1 and a convenience store 300 metres
north of Q3. A grocer of one cuisine stands 50 metres south of R2, and a
convenience store on T4. What is no food shop stands beside Q4, where it
would change every figure of the first area if it were counted.
"""

import math
import re
from pathlib import Path

import pytest
from burro_core.catalogue import FEATURES, NEVER_A_TRADE_OFF, TAGS
from burro_core.ids import FeatureId, NativeResolution, Polarity, TagId
from burro_core.release import DECIDED_BY_CORE
from burro_pipeline.cells import centres, land, spine
from burro_pipeline.cells.shapes import longitude_and_latitude
from burro_pipeline.derive import culture_file, grocery_walk, measures, park_proximity
from burro_pipeline.derive.culture_reach import metres_to_a_degree
from burro_pipeline.derive.food_shop_kinds import Kind
from burro_pipeline.derive.grocery_walk import Nearest, to_the_edge_of
from burro_pipeline.derive.measures import says_what_core_says
from burro_pipeline.derive.methods import Worked
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind as MadeBy
from burro_pipeline.evidence.receipt import Geography
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import held, registry
from ..fetch.parquet_support import Place
from .culture_support import (
    BOX,
    CANARY,
    DAY,
    EDITION,
    OAS,
    ONE,
    Q1,
    Q3,
    Q4,
    R2,
    SOURCE,
    T4,
    THREE,
    TWO,
    Wanted,
    beside,
    centres_at,
    inputs_of,
    on_the_grid,
    place,
)

SHOPS = ("shopping", "food_and_beverage_store")
GROCER = (*SHOPS, "grocery_store")
OF_ONE_CUISINE = (*GROCER, "international_grocery_store")
CONVENIENCE = ("shopping", "convenience_store")
BUTCHER = (*SHOPS, "butcher_shop")
GREENGROCER = (*SHOPS, "specialty_foods_store", "produce_store")
OFF_LICENCE = (*SHOPS, "liquor_store")
BAKER = ("food_and_drink", "casual_eatery", "bakery")
MARKET = ("shopping", "market", "farmers_market")
BOOKSHOP = ("shopping", "bookstore")

# A point as well-known binary writes one, which is nowhere on the earth: no number twice.
NOWHERE = b"\x01\x01\x00\x00\x00" + b"\x00\x00\x00\x00\x00\x00\xf8\x7f" * 2

COUNTED = (
    place(beside(Q1, 100), GROCER),
    place(beside(Q3, 0, 300), CONVENIENCE),
    place(beside(R2, 0, -50), OF_ONE_CUISINE),
    place(T4, CONVENIENCE),
)
# None of these counts. Each stands 10 metres from Q4, or nearer.
NOT_COUNTED = (
    place(beside(Q4, 10), BUTCHER),
    place(beside(Q4, -10), GREENGROCER),
    place(beside(Q4, 0, 10), OFF_LICENCE),
    place(beside(Q4, 0, -10), BAKER),
    place(beside(Q4, 5, 5), MARKET),
    place(beside(Q4, -5, -5), BOOKSHOP),
    place(beside(Q4, 5, -5), SHOPS),
    place(Q4, GROCER, status="permanently_closed"),
    place(Q4, CONVENIENCE, geometry=NOWHERE),
    place(Q4, hierarchy=(), primary=None),
)
IN_THE_TOWN = (*COUNTED, *NOT_COUNTED)
OA_Q1, OA_Q2, OA_Q3, OA_Q4 = OAS[:4]


def built(folder: Path, *places: Place, **how: object) -> Nearest:
    given = places if places else IN_THE_TOWN
    inputs = inputs_of(folder, given, **how)  # pyright: ignore[reportArgumentType]
    return grocery_walk.build(inputs, spine.build(inputs))


@pytest.fixture(scope="module")
def town(tmp_path_factory: pytest.TempPathFactory) -> Nearest:
    return built(tmp_path_factory.mktemp("town"))


# Which shops count


def test_a_grocer_and_a_convenience_store_count_and_nothing_else_does(town: Nearest):
    assert town.held.rows == len(IN_THE_TOWN) == 14
    assert town.held.by_kind == {"convenience_store": 2, "grocer": 2}
    assert town.held.counted_as == {
        "convenience_store": 2,
        "grocery_store": 1,
        "international_grocery_store": 1,
    }
    assert town.held.left_out == {
        "closed": 1,
        "no_category": 1,
        "no_point": 1,
        "not_a_food_shop": 3,
        "not_a_kind": 3,
        "parent_alone": 1,
    }
    assert town.held.left_out_as == {
        "butcher_shop": 1,
        "convenience_store": 1,
        "food_and_beverage_store": 1,
        "grocery_store": 1,
        "liquor_store": 1,
        "produce_store": 1,
    }


def test_each_kind_is_a_kind_of_the_table(town: Nearest):
    assert {one.kind for one in town.held.records} == {kind.value for kind in Kind}


def test_a_category_of_the_branch_that_the_table_does_not_hold_stops_the_build(tmp_path: Path):
    with pytest.raises(LockError) as refused:
        built(tmp_path, *COUNTED, place(Q4, (*SHOPS, "egg_store")))
    assert refused.value.rule == "input_is_as_described"
    assert "egg_store" not in str(refused.value) and CANARY not in str(refused.value)


# The figure


def test_an_output_area_is_as_far_from_a_shop_as_the_nearest_that_counts(town: Nearest):
    """A shop is written as a longitude and a latitude, so a distance is good to a metre."""
    near = [town.of_oa[oa] for oa in OAS]
    assert near[:4] == pytest.approx([100, 900, 300, math.hypot(1000, 300)], abs=0.5)
    far = math.hypot(1000, 50)
    assert near[4:8] == pytest.approx([far, 50, far, math.hypot(2000, 50)], abs=0.5)
    assert near[8:] == pytest.approx([3000, 2000, 1000, 0], abs=0.5)
    assert town.found_of_oa == town.of_oa and town.beyond_the_edge == ()


def test_an_area_is_given_the_median_over_its_homes_to_the_nearest_ten_metres(town: Nearest):
    assert town.worked == {
        # 110 homes at 100 and 130 at 300 are 240 of 500: the 120 at 900 hold the middle.
        ONE: Worked(900.0, 4, 4, 1.0, State.PRESENT),
        # 160 homes at 50, and 150 at 1,001 are 310 of 660: the 170 at 1,001 hold the middle.
        TWO: Worked(1000.0, 4, 4, 1.0, State.PRESENT),
        # 220 homes at 0 and 210 at 1,000 are 430 of 820.
        THREE: Worked(1000.0, 4, 4, 1.0, State.PRESENT),
    }


def test_what_is_no_food_shop_moves_no_figure(tmp_path: Path, town: Nearest):
    alone = built(tmp_path, *COUNTED)
    assert alone.worked == town.worked and alone.of_oa == town.of_oa


def test_two_records_of_one_shop_are_one_distance(tmp_path: Path, town: Nearest):
    twice = built(tmp_path, *COUNTED, *COUNTED, place(beside(Q1, 100), CONVENIENCE))
    assert twice.worked == town.worked
    assert len(twice.held.records) == 9


def test_the_same_shops_in_any_order_give_the_same_figures(tmp_path: Path, town: Nearest):
    turned = built(tmp_path, *reversed(IN_THE_TOWN))
    assert (turned.worked, turned.of_oa) == (town.worked, town.of_oa)
    assert [row.value for row in turned.rows] == [row.value for row in town.rows]


def test_no_record_is_left_out_for_how_sure_its_publisher_is(tmp_path: Path):
    unsure = place(beside(Q1, 100), GROCER, confidence=0.05)
    assert built(tmp_path, *COUNTED[1:], unsure).of_oa[OA_Q1] == pytest.approx(100, abs=0.5)
    unsaid = place(beside(Q1, 100), GROCER, confidence=None)
    found = built(tmp_path / "unsaid", *COUNTED[1:], unsaid)
    assert found.of_oa[OA_Q1] == pytest.approx(100, abs=0.5)


def test_with_no_food_shop_at_all_no_area_has_a_figure_and_none_is_filled_in(tmp_path: Path):
    found = built(tmp_path, *NOT_COUNTED)
    assert found.of_oa == {} and len(found.beyond_the_edge) == 12
    assert set(found.worked.values()) == {Worked(None, 0, 4, 0.0, State.SOURCE_GAP)}
    assert [row.value for row in found.rows] == [None, None, None]


def test_an_output_area_with_no_centre_has_no_distance(tmp_path: Path):
    found = built(tmp_path, centres=centres_at(without=[OA_Q1]))
    assert OA_Q1 not in found.found_of_oa and OA_Q1 not in found.of_oa
    # The first output area holds 110 of the area's 500 homes.
    assert found.worked[ONE] == Worked(900.0, 3, 4, round(390 / 500, 6), State.PARTIAL)


# The edge of what was taken


def at(metres: tuple[float, float]) -> tuple[float, float]:
    return longitude_and_latitude(*on_the_grid(metres))


def test_a_point_stands_as_far_inside_a_box_as_its_nearest_side():
    """At London a degree east is about 69 kilometres, and a degree north about 111."""
    box = (-0.5, 51.3, 0.3, 51.7)
    across, up = metres_to_a_degree(51.5)
    assert (round(across, -2), round(up, -2)) == (69_400, 111_300)
    # The east side is the nearest, at three tenths of a degree.
    assert to_the_edge_of(box, (0.0, 51.5)) == pytest.approx(0.3 * across)
    # A tenth of a degree from the south side, which is nearer than any other.
    assert to_the_edge_of(box, (-0.1, 51.4)) == pytest.approx(0.1 * metres_to_a_degree(51.4)[1])
    assert to_the_edge_of(box, (-0.49, 51.5)) == pytest.approx(0.01 * across)


@pytest.mark.parametrize(
    "point", [(-0.5, 51.5), (0.3, 51.5), (0.0, 51.7), (-0.6, 51.5), (0.0, 52.0)]
)
def test_a_point_on_a_side_of_the_box_or_beyond_it_stands_no_distance_inside(
    point: tuple[float, float],
):
    assert to_the_edge_of((-0.5, 51.3, 0.3, 51.7), point) == pytest.approx(0.0, abs=1e-6)


def test_a_home_whose_nearest_shop_found_is_beyond_the_edge_has_no_distance(tmp_path: Path):
    """The box ends 500 metres east of Q4, and the one shop stands by Q1.

    A shop beyond the box may not be in the part, and may be nearer than the
    one that was found.
    """
    east = round(at(beside(Q4, 500))[0], 6)
    narrow = Wanted(box=(BOX[0], BOX[1], east, BOX[3]))
    found = built(tmp_path, place(beside(Q1, 100), GROCER), wanted=narrow)
    assert round(found.found_of_oa[OA_Q4]) == 2_900 and round(found.found_of_oa[OA_Q3]) == 1_900
    # Q2 stands some 2,500 metres inside the box and 900 from the shop. Q3 stands 1,500
    # inside it and 1,900 from the shop, and Q4 500 inside it and 2,900 from the shop.
    assert {OA_Q3, OA_Q4} <= set(found.beyond_the_edge)
    assert {OA_Q1, OA_Q2} <= set(found.of_oa)
    # 230 of the 500 homes of the first area have a distance, which is under half.
    assert found.worked[ONE] == Worked(None, 2, 4, 0.46, State.BELOW_THRESHOLD)


def test_a_file_that_was_kept_whole_has_no_edge(tmp_path: Path, town: Nearest):
    whole = built(tmp_path, whole=True)
    assert whole.held.file.taken is None
    assert (whole.worked, whole.beyond_the_edge) == (town.worked, ())


# What is never read


def test_no_name_of_a_place_is_read_or_kept(town: Nearest):
    said = f"{town.worked} {town.rows} {town.metric} {town.held}"
    assert CANARY not in said
    assert set(culture_file.READ) == {
        "geometry",
        "taxonomy",
        "operating_status",
        "sources",
        "confidence",
    }


def test_the_store_is_never_written_to(tmp_path: Path):
    inputs = inputs_of(tmp_path, IN_THE_TOWN)
    before = held(tmp_path / "store")
    grocery_walk.build(inputs, spine.build(inputs))
    assert held(tmp_path / "store") == before


# The evidence


def test_every_area_has_a_row_that_holds_its_figure(town: Nearest):
    assert [row.fact_id for row in town.rows] == [
        f"{area}/feature/grocery_walk" for area in (ONE, TWO, THREE)
    ]
    assert [row.value for row in town.rows] == [900.0, 1000.0, 1000.0]
    for row in town.rows:
        assert row.derivation_id == "straight_line_to_nearest@1"
        assert row.data_period is not None
        assert row.data_period.days() == ("2021-03-21", DAY)


def test_a_row_names_the_places_the_centres_the_lookup_and_the_homes(town: Nearest):
    sources = sorted(receipt.source_id for receipt in town.files)
    assert sources == sorted([SOURCE, centres.CENTRES, spine.LOOKUP, spine.HOMES])
    ids = tuple(sorted(receipt.file_id for receipt in town.files))
    assert all(row.inputs == ids for row in town.rows)


def test_the_rows_are_evidence_a_release_can_hold(town: Nearest):
    evidence = Evidence(
        release_id="lon-2026-09-24-01",
        methods=grocery_walk.METHODS,
        receipts=town.files,
        rows=town.rows,
    )
    assert len(evidence.rows) == 3
    assert town.geography is Geography.POINT


def test_the_method_is_the_one_the_distance_to_a_station_is_worked_out_by():
    assert grocery_walk.METHOD is park_proximity.STRAIGHT_LINE
    assert grocery_walk.METHOD.kind is MadeBy.MEASURED
    assert "straight line" in grocery_walk.METHOD.sentence


# The gate


@pytest.mark.parametrize("source", [SOURCE, centres.CENTRES])
def test_the_gate_is_asked_about_every_file_before_it_is_read(tmp_path: Path, source: str):
    sources = [
        one.model_copy(update={"uses": (Use.DISPLAY,)}) if one.id == source else one
        for one in registry()
    ]
    inputs = inputs_of(tmp_path, IN_THE_TOWN, given=Registry(tuple(sources)))
    found = spine.build(inputs)
    with pytest.raises(LockError) as stopped:
        grocery_walk.build(inputs, found)
    assert stopped.value.rule == "gate_refuses"
    assert source not in {one.receipt.source_id for one in inputs.opened}


def test_a_build_with_no_file_of_places_leaves_the_measure_out(tmp_path: Path):
    inputs = inputs_of(tmp_path, None)
    with pytest.raises(LockError) as refused:
        grocery_walk.build(inputs, spine.build(inputs))
    assert refused.value.rule == "input_has_one_receipt"


# The name, the unit and the sentences


def test_the_row_says_a_straight_line_in_metres_and_names_every_source(town: Nearest):
    metric = town.metric
    assert metric.feature_id is FeatureId.GROCERY_WALK
    assert metric.label == "Straight-line distance to the nearest food shop"
    assert (metric.unit, metric.polarity) == ("m", Polarity.LESS)
    assert metric.native_resolution is NativeResolution.POINT
    assert metric.vintage == DAY
    assert metric.source_ids == tuple(sorted(receipt.source_id for receipt in town.files))
    assert metric.rankable


def test_the_row_is_cores_so_a_build_carries_the_measure(town: Nearest):
    assert says_what_core_says(town.metric)
    core = FEATURES[FeatureId.GROCERY_WALK]
    differs = {
        name for name in DECIDED_BY_CORE if getattr(town.metric, name) != getattr(core, name)
    }
    assert differs == set()
    assert not says_what_core_says(town.metric.model_copy(update={"unit": "min"}))
    assert (core.label, core.unit) == (grocery_walk.LABEL, grocery_walk.UNIT)
    assert NEVER_A_TRADE_OFF[FeatureId.GROCERY_WALK] == 800


def test_the_sentence_of_the_measure_says_what_it_is_and_what_it_is_not(town: Nearest):
    said = town.metric.definition
    assert said == grocery_walk.definition_of(town.held)
    assert said.endswith(".") and not re.search(r"[.!?]\s|\n", said.replace(f"{EDITION} ", ""))
    for words in (
        "in a straight line, in metres",
        f"release {EDITION} of Overture Maps Places, of the Overture Maps Foundation",
        f"as at {DAY}",
        "gives a category of a grocer, a supermarket or a convenience store",
        "leaving out a record that its file says has closed for good",
        "the median over the area's homes at the census of 2021",
        "to the nearest 10 metres with a half taken upward",
        "not along any street, so the walk is longer",
        "a shop the file does not hold is not seen",
        "nothing says how large a shop is or what it sells",
        "further off than the edge of the part of the file that was taken",
    ):
        assert words in said


def test_nothing_said_of_the_figure_calls_it_a_walk_or_gives_it_in_minutes():
    said = (grocery_walk.LABEL, grocery_walk.DEFINITION, *grocery_walk.CANNOT_SEE)
    for words in said:
        assert "minute" not in words
        assert "walk" not in words or "not a walk" in words or "the walk is longer" in words
    assert "walk" not in grocery_walk.LABEL.lower()


def test_what_the_measure_cannot_see_is_said_in_whole_sentences():
    assert len(grocery_walk.CANNOT_SEE) == len(set(grocery_walk.CANNOT_SEE)) == 9
    for said in grocery_walk.CANNOT_SEE:
        assert said.endswith(".") and "!" not in said and "\n" not in said and "|" not in said
        assert not re.search(r"[.!?]\s", said)
    assert "not a walk" in grocery_walk.A_STRAIGHT_LINE
    assert "a corner shop counts as a supermarket does" in grocery_walk.HOW_LARGE
    assert "a butcher, a baker, a greengrocer and a market are not counted" in (
        grocery_walk.WHAT_COUNTS
    )
    assert grocery_walk.CANNOT_SEE[0] is grocery_walk.A_STRAIGHT_LINE


RESIDENT_WORDS = re.compile(
    r"\b(residents?|people|population|households?|famil(y|ies)|health|ages?|incomes?)\b", re.I
)


def test_no_sentence_of_the_measure_describes_who_lives_somewhere(town: Nearest):
    sentences = (town.metric.definition, *grocery_walk.CANNOT_SEE, grocery_walk.METHOD.sentence)
    assert [sentence for sentence in sentences if RESIDENT_WORDS.search(sentence)] == []


def test_the_vibe_that_holds_it_says_the_same_of_a_shop():
    """Core says it of Everyday on foot, where the measure is a quarter of the recipe."""
    vibe = TAGS[TagId.EVERYDAY_ON_FOOT]
    assert {term.feature_id: term.hundredths for term in vibe.terms}[FeatureId.GROCERY_WALK] == 25
    assert "How large a food shop is, and what it sells." in vibe.cannot_see
    assert "How long the walk is: each distance is a straight line." in vibe.cannot_see


# The list of the measures of a build


def test_the_measure_is_on_the_list_and_is_called_as_the_list_calls_each(
    tmp_path: Path, town: Nearest
):
    (measure,) = [one for one in measures.MEASURES if one.feature is FeatureId.GROCERY_WALK]
    assert (measure.source, measure.methods) == (SOURCE, grocery_walk.METHODS)
    assert measure.cannot_see == grocery_walk.CANNOT_SEE
    assert (measure.waits_on, measure.held_back) == ((), ())
    assert not measure.in_squares and not measure.in_parts
    inputs = inputs_of(tmp_path, IN_THE_TOWN)
    found = spine.build(inputs)
    made = measure.build(inputs, measures.Ground(found, land.build(inputs, found)))
    assert made.worked == town.worked
    assert (made.rows, made.metric, made.geography) == (town.rows, town.metric, town.geography)
    assert [receipt for receipt in made.files if measure.reads(receipt.publisher_file)]
    assert grocery_walk.is_the_file("part-00007-made-up-c000.zstd.parquet")
    assert not grocery_walk.is_the_file("places.csv")
