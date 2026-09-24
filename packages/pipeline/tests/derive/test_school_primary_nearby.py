"""Primary schools close by, from the register to a count for each area.

Every file here is made up: `schools_support.py` makes the register, and the
tests of cells draw the town it stands beside. The centre of each output area
is put where each count can be worked out by hand.

    A and B   on one point, at (700000, 400000)
    C         1,000 metres east of them
    D         1,000 metres east of C, and past the edge of London

    Quillhaven 001   homes 110, 120, 130, 140   2, 2, 0 and 3 within 800 metres: 1.76
    Quillhaven 002   homes 150, 160, 170, 180   1, 2, 1 and 0: 0.97
    Tallowgate 001   homes 190, 200, 210, 220   none: 0
"""

import re
from dataclasses import replace
from pathlib import Path

import pytest
from burro_core.catalogue import FEATURES, NEVER_A_TRADE_OFF
from burro_core.ids import Dimension, FeatureId, NativeResolution, Polarity
from burro_pipeline.cells import centres, spine
from burro_pipeline.cells.spine import Homes
from burro_pipeline.derive import measures, park_proximity, school_primary_nearby, schools_file
from burro_pipeline.derive.measures import says_what_core_says
from burro_pipeline.derive.school_primary_nearby import (
    CANNOT_SEE,
    COUNTS,
    KINDS,
    LABEL,
    METHOD,
    PHASES,
    REACH,
    STATUSES,
    Nearby,
    figures,
)
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind
from burro_pipeline.evidence.receipt import Geography
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import held, registry
from .schools_support import (
    CANARY,
    COUNTED,
    DAY,
    DO_NOT_COUNT,
    FAR_AWAY,
    NAMELESS,
    OAS,
    PLACED,
    QUILLHAVEN_1,
    QUILLHAVEN_2,
    REGISTER,
    TALLOWGATE,
    MadeUpSchool,
    at,
    inputs_of,
    on,
    register_csv,
    with_one,
    zipped,
)

AREAS = (QUILLHAVEN_1, QUILLHAVEN_2, TALLOWGATE)


def built(inputs: Inputs) -> Nearby:
    return school_primary_nearby.build(inputs, spine.build(inputs))


def values_of(made: Nearby) -> list[float | None]:
    return [made.worked[area].value for area in AREAS]


def stopped(inputs: Inputs) -> LockError:
    with pytest.raises(LockError) as refused:
        built(inputs)
    assert refused.value.rule == "input_is_as_described"
    # A refusal repeats nothing of the file.
    assert CANARY not in str(refused.value) and NAMELESS not in str(refused.value)
    return refused.value


@pytest.fixture(scope="module")
def town(tmp_path_factory: pytest.TempPathFactory) -> Nearby:
    return built(inputs_of(tmp_path_factory.mktemp("town")))


# What is read


def test_the_measure_asks_for_the_seven_columns_that_may_be_read_and_for_no_other():
    assert set(school_primary_nearby.COLUMNS) == schools_file.MAY_BE_READ
    assert not set(school_primary_nearby.COLUMNS) & schools_file.FORBIDDEN
    assert len(school_primary_nearby.COLUMNS) == 7


# Which schools count


def test_a_school_counts_where_it_is_open_state_funded_and_primary(town: Nearby):
    found = town.schools
    assert found.england.rows == len(REGISTER) == 110
    assert found.england.counted == len(COUNTED) + len(FAR_AWAY) == 104
    assert found.england.counted_by_kind == {
        "Academy converter": 1,
        "Community school": 101,
        "Free schools": 1,
        "Voluntary aided school": 1,
    }
    assert len(found.points) == 104 and found.day == DAY


def test_each_school_that_does_not_count_is_dropped_by_the_first_column_that_says_so(
    town: Nearby,
):
    found = town.schools.england
    assert found.dropped_by_status == {"Closed": 1, "Proposed to open": 1}
    assert found.open_rows == 108
    assert found.dropped_by_kind == {
        "Community special school": 1,
        "Local authority nursery school": 1,
        "Other independent school": 1,
    }
    assert found.dropped_by_phase == {"Secondary": 1}
    dropped = (
        sum(found.dropped_by_status.values())
        + sum(found.dropped_by_kind.values())
        + sum(found.dropped_by_phase.values())
    )
    assert dropped == len(DO_NOT_COUNT) and dropped + found.counted == found.rows


def test_the_schools_of_london_are_counted_apart_by_the_region_the_register_gives(town: Nearby):
    found = town.schools.london
    assert (found.rows, found.open_rows, found.counted) == (9, 7, 3)
    # The special school has no point. It is open, and it does not count.
    assert (found.open_without_a_point, found.without_a_point) == (1, 0)


def test_the_seven_types_that_count_are_the_ones_the_state_funds_and_any_child_may_go_to():
    assert COUNTS == (
        "Academy converter",
        "Academy sponsor led",
        "Community school",
        "Foundation school",
        "Free schools",
        "Voluntary aided school",
        "Voluntary controlled school",
    )
    assert [kind for kind, counts in KINDS.items() if counts] == list(COUNTS)
    assert len(KINDS) == 39
    assert [phase for phase, counts in PHASES.items() if counts] == [
        "Primary",
        "Middle deemed primary",
        "All-through",
    ]
    assert [status for status, counts in STATUSES.items() if counts] == [
        "Open",
        "Open, but proposed to close",
    ]


@pytest.mark.parametrize("kind", ["special", "independent", "nursery", "referral", "16"])
def test_no_type_that_counts_is_a_special_a_fee_paying_or_a_nursery_school(kind: str):
    assert not [name for name in COUNTS if kind in name.lower()]


@pytest.mark.parametrize(
    ("school", "words"),
    [
        (at(700_000, 400_000, status="Open for now"), "a status is not known"),
        (at(700_000, 400_000, kind="A new type of school"), "a type of school is not known"),
        (at(700_000, 400_000, phase="Upper primary"), "a phase is not known"),
        # A closed school of a type that is not known stops the build too.
        (at(700_000, 400_000, status="Closed", kind="A new type"), "a type of school"),
    ],
)
def test_a_value_the_measure_has_not_met_stops_the_build(
    tmp_path: Path, school: MadeUpSchool, words: str
):
    """A school under a new name would otherwise be counted as none."""
    assert words in str(stopped(inputs_of(tmp_path, with_one(school))))


def test_a_school_that_is_there_twice_stops_the_build(tmp_path: Path):
    again = replace(COUNTED[0], urn="900001")
    assert "there twice" in str(stopped(inputs_of(tmp_path, with_one(again))))


# Where a school stands


def test_two_schools_on_one_point_are_two_schools(town: Nearby):
    assert (town.schools.shared_points, town.schools.on_a_shared_point) == (1, 2)
    assert town.within[OAS[0]] == 2


@pytest.mark.parametrize(("east", "north"), [("", ""), ("0", "0"), ("", "0")])
def test_a_school_with_no_point_is_placed_nowhere_and_is_said(
    tmp_path: Path, east: str, north: str
):
    found = built(inputs_of(tmp_path, with_one(MadeUpSchool(east=east, north=north))))
    assert (found.schools.england.counted, found.schools.england.without_a_point) == (105, 1)
    assert (found.schools.london.counted, found.schools.london.without_a_point) == (4, 1)
    assert len(found.schools.points) == 104
    assert values_of(found) == [1.8, 1.0, 0.0]


@pytest.mark.parametrize(
    ("east", "north"),
    [("700000", ""), ("", "400000"), ("700000", "0"), ("7e5", "4e5"), ("700000.5", "400000")],
)
def test_a_point_that_is_no_point_stops_the_build(tmp_path: Path, east: str, north: str):
    school = MadeUpSchool(east=east, north=north)
    assert "a point is no point" in str(stopped(inputs_of(tmp_path, with_one(school))))


def test_the_build_stops_where_more_than_1_in_100_schools_have_no_point(tmp_path: Path):
    """A count would then be a gap read as a figure."""
    register = register_csv((*COUNTED, MadeUpSchool()))
    assert "have no point" in str(stopped(inputs_of(tmp_path, zipped(register))))


def test_the_build_stops_where_the_register_holds_no_school_round_the_homes(tmp_path: Path):
    far_away = zipped(register_csv(FAR_AWAY))
    assert "do not reach the homes" in str(stopped(inputs_of(tmp_path, far_away)))


def test_a_register_with_no_school_that_counts_stops_the_build(tmp_path: Path):
    none = zipped(register_csv(DO_NOT_COUNT))
    assert "no school that counts" in str(stopped(inputs_of(tmp_path, none)))


# The count


def test_each_output_area_counts_the_schools_within_800_metres_in_a_straight_line(town: Nearby):
    assert [town.within[oa] for oa in OAS] == [2, 2, 0, 3, 1, 2, 1, 0, 0, 0, 0, 0]


def test_a_school_at_800_metres_exactly_is_within_reach_and_half_a_metre_more_is_not(
    town: Nearby,
):
    assert PLACED[1] == (700_000, 400_800) and town.within[OAS[1]] == 2
    assert PLACED[2] == (700_000, 400_800.5) and town.within[OAS[2]] == 0


def test_the_reach_is_the_one_at_which_the_nearest_park_is_never_a_trade_off():
    assert REACH == NEVER_A_TRADE_OFF[FeatureId.PARK_PROXIMITY] == 800
    assert METHOD.parameters == {"metres": 800, "enough_in_100": 50}


def test_an_area_is_given_the_mean_over_its_homes_to_one_decimal_place(town: Nearby):
    # 880 over 500, 640 over 660, and none.
    assert values_of(town) == [1.8, 1.0, 0.0]
    assert {one.state for one in town.worked.values()} == {State.PRESENT}
    assert {one.weight_covered for one in town.worked.values()} == {1.0}
    assert [(one.units_used, one.units_expected) for one in town.worked.values()] == [(4, 4)] * 3


def test_nought_is_a_figure_where_the_register_covers_and_no_school_is_near(town: Nearby):
    assert town.worked[TALLOWGATE].value == 0.0
    assert town.worked[TALLOWGATE].state is State.PRESENT


def test_a_figure_is_rounded_with_a_half_taken_upward():
    homes = Homes(area_of=dict.fromkeys(OAS[:2], QUILLHAVEN_1), homes={OAS[0]: 1, OAS[1]: 3})
    # A quarter. The language's own rounding gives 0.2.
    assert figures({OAS[0]: 1, OAS[1]: 0}, homes)[QUILLHAVEN_1].value == 0.3
    assert round(0.25, 1) == 0.2


def test_an_area_with_no_homes_has_no_figure():
    homes = Homes(area_of=dict.fromkeys(OAS[:2], QUILLHAVEN_1), homes={OAS[0]: 0, OAS[1]: 0})
    found = figures({OAS[0]: 1, OAS[1]: 3}, homes)[QUILLHAVEN_1]
    assert (found.value, found.state) == (None, State.SOURCE_GAP)


def test_the_order_of_the_rows_of_the_register_changes_nothing(tmp_path: Path, town: Nearby):
    turned = zipped(register_csv(tuple(reversed(REGISTER))))
    found = built(inputs_of(tmp_path, turned))
    assert found.worked == town.worked and found.schools.points == town.schools.points


# The edge of London


def test_a_school_past_the_edge_of_london_counts_for_a_home_it_is_near(town: Nearby):
    """The register is of England. The fourth school is of another region."""
    assert len(town.schools.past_the_edge) == 1 + len(FAR_AWAY)
    assert (town.reached, town.reached_past_the_edge) == (4, 1)
    # The seventh output area has that school within reach, and no other.
    assert town.within[OAS[6]] == 1


def test_without_the_school_past_the_edge_the_area_beside_it_reads_lower(tmp_path: Path):
    inside = zipped(register_csv((*COUNTED[:3], *DO_NOT_COUNT, *FAR_AWAY)))
    # 150 and 160 over 660.
    assert values_of(built(inputs_of(tmp_path, inside))) == [1.8, 0.5, 0.0]


# What is missing


def test_an_output_area_with_no_centre_adds_nothing_and_lowers_the_coverage(tmp_path: Path):
    placed = dict(on(*PLACED))
    del placed[OAS[3]]
    found = built(inputs_of(tmp_path, placed=placed))
    one = found.worked[QUILLHAVEN_1]
    # 460 over 360, with 360 of 500 homes covered.
    assert (one.value, one.state, one.weight_covered) == (1.3, State.PARTIAL, 0.72)
    assert (one.units_used, one.units_expected) == (3, 4)
    assert OAS[3] not in found.within and OAS[3] not in found.metres


def test_below_half_the_homes_covered_no_figure_is_given(tmp_path: Path):
    placed = {oa: point for oa, point in on(*PLACED).items() if oa not in OAS[1:4]}
    one = built(inputs_of(tmp_path, placed=placed)).worked[QUILLHAVEN_1]
    assert (one.value, one.state, one.weight_covered) == (None, State.BELOW_THRESHOLD, 0.22)


def test_an_area_with_no_centre_at_all_is_a_gap_and_nothing_is_filled_in(tmp_path: Path):
    placed = {oa: point for oa, point in on(*PLACED).items() if oa not in OAS[:4]}
    one = built(inputs_of(tmp_path, placed=placed)).worked[QUILLHAVEN_1]
    assert (one.value, one.state, one.weight_covered) == (None, State.SOURCE_GAP, 0.0)


# The distance to the nearest


def test_the_distance_to_the_nearest_school_is_worked_out_as_the_nearest_park_is(town: Nearby):
    assert [round(town.metres[oa], 1) for oa in OAS[:8]] == [
        0.0,
        800.0,
        800.5,
        500.0,
        0.0,
        400.0,
        600.0,
        3000.0,
    ]
    # The median over homes, to the nearest 10 metres: half way between 500 and 800.
    assert [town.nearest[area].value for area in AREAS] == [650.0, 600.0, 4000.0]
    assert school_primary_nearby.NEAREST is park_proximity.STRAIGHT_LINE


def test_the_nearest_school_may_be_one_past_the_edge(town: Nearby):
    assert town.metres[OAS[8]] == 3_000.0


def test_core_holds_no_measure_of_the_distance_to_the_nearest_school():
    """It is worked out to be compared. On the day core gains one, it needs rows of its own."""
    of_schools = {one.feature_id for one in FEATURES.values() if one.dimension is Dimension.SCHOOLS}
    assert of_schools == {
        FeatureId.SCHOOL_PRIMARY_NEARBY,
        FeatureId.SCHOOL_PRIMARY_ATTAINMENT,
        FeatureId.SCHOOL_SECONDARY_ATTAINMENT,
        FeatureId.UNIVERSITY_PROXIMITY,
    }


# The evidence


def test_every_area_has_a_row_that_holds_its_figure(town: Nearby):
    assert [row.fact_id for row in town.rows] == [
        f"{area}/feature/school_primary_nearby" for area in AREAS
    ]
    assert [row.value for row in town.rows] == [1.8, 1.0, 0.0]
    for row in town.rows:
        assert row.derivation_id == "points_within_800m_by_homes@1"
        assert row.retrieved_on == DAY
        assert row.data_period is not None
        # From the day of the census, which the weights are of, to the day of the register.
        assert row.data_period.days() == ("2021-03-21", DAY)


def test_a_row_rests_on_the_register_the_centres_the_lookup_and_the_homes(town: Nearby):
    by_source = {receipt.source_id: receipt.file_id for receipt in town.files}
    assert sorted(by_source) == sorted(
        [school_primary_nearby.SOURCE, centres.CENTRES, spine.LOOKUP, spine.HOMES]
    )
    assert {row.inputs for row in town.rows} == {tuple(sorted(by_source.values()))}


def test_the_evidence_has_no_loose_end(town: Nearby):
    evidence = Evidence.of(
        "lon-2026-10-02-01", town.files, school_primary_nearby.METHODS, town.rows
    )
    assert len(evidence.rows) == 3
    assert town.geography is Geography.POINT
    assert METHOD.kind is Kind.MEASURED
    assert METHOD.code == "burro_pipeline.derive.school_primary_nearby"


def test_nothing_of_a_column_that_is_never_read_is_in_what_the_build_gives(town: Nearby):
    assert (repr(town).count(CANARY), repr(town).count(NAMELESS)) == (0, 0)


# The gate and the store


def test_the_gate_is_asked_before_the_register_is_read(tmp_path: Path):
    sources = [
        source.model_copy(update={"uses": (Use.DISPLAY,)})
        if source.id == school_primary_nearby.SOURCE
        else source
        for source in registry()
    ]
    inputs = inputs_of(tmp_path, given=Registry(tuple(sources)))
    found = spine.build(inputs)
    before = inputs.opened
    with pytest.raises(LockError) as refused:
        school_primary_nearby.build(inputs, found)
    assert refused.value.rule == "gate_refuses"
    assert inputs.opened == before


def test_every_file_behind_a_figure_is_registered_for_scoring(town: Nearby):
    assert town.metric.source_ids == (
        "dfe-gias",
        "ons-census-2021-housing-tables",
        "ons-oa-pwc-2021",
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
    )
    for source_id in town.metric.source_ids:
        assert Use.SCORING in registry().get(source_id).uses


def test_nothing_is_written_to_the_store(tmp_path: Path):
    inputs = inputs_of(tmp_path)
    before = held(tmp_path / "store")
    built(inputs)
    assert held(tmp_path / "store") == before


# The name, the unit and the sentences


def test_the_name_says_a_straight_line_and_core_says_the_same(town: Nearby):
    """Core's words are held here, so that this fails on the day core names a walk again.

    Until the count is made along a network of streets, no release carries it under a
    name that says a walk.
    """
    metric, feature = town.metric, FEATURES[FeatureId.SCHOOL_PRIMARY_NEARBY]
    assert metric.label == LABEL == "State primary schools within 800 m in a straight line"
    assert feature.label == metric.label and "walk" not in metric.label.lower()
    assert says_what_core_says(metric)
    assert not says_what_core_says(
        metric.model_copy(update={"label": "State primary schools within a short walk"})
    )
    assert (metric.unit, metric.polarity) == (feature.unit, feature.polarity)
    assert (metric.unit, metric.polarity) == ("count", Polarity.MORE)
    assert metric.native_resolution is feature.native_resolution is NativeResolution.POINT
    assert metric.vintage == DAY


def test_the_measure_is_on_the_list_of_a_build_and_waits_on_nothing():
    listed = {measure.feature: measure for measure in measures.MEASURES}
    measure = listed[FeatureId.SCHOOL_PRIMARY_NEARBY]
    assert (measure.waits_on, measure.held_back) == ((), ())
    # An infant school and a junior school on one site are counted as two, and it is said.
    assert any("counted as two" in said for said in CANNOT_SEE)
    assert (measure.source, measure.in_squares) == ("dfe-gias", False)
    assert measure.reads("extract.zip") and not measure.reads("edubasealldata20260924.csv")
    assert measure.cannot_see == CANNOT_SEE


def test_the_definition_is_one_sentence_that_says_what_is_counted_and_what_is_not(town: Nearby):
    definition = town.metric.definition
    assert definition == school_primary_nearby.definition_of(DAY)
    assert definition.endswith(".") and not re.search(r"[.!?]\s|\n", definition)
    for words in (
        "within 800 metres, in a straight line",
        "Get Information About Schools",
        "Department for Education",
        "as at 2026-09-24",
        "gives it as open",
        "one of the 7 types",
        "primary, middle deemed primary or all-through",
        "census of 2021",
        "past the edge of London",
        "the mean over the area's homes",
        "1 decimal place",
        "not along any street",
        "how good a school is",
        "whether it has a place",
    ):
        assert words in definition
    assert "straight line" in METHOD.sentence


RESIDENT_WORDS = re.compile(
    r"\b(residents?|people|population|households?|famil(y|ies)|health|ages?|incomes?|faith"
    r"|religio\w*)\b",
    re.IGNORECASE,
)


def test_no_sentence_of_the_measure_describes_who_lives_somewhere_or_names_a_faith(
    town: Nearby,
):
    sentences = (town.metric.definition, LABEL, *CANNOT_SEE, METHOD.sentence)
    assert [sentence for sentence in sentences if RESIDENT_WORDS.search(sentence)] == []


def test_no_sentence_of_the_measure_claims_a_catchment_or_a_place():
    """The registry entry asks it: a school nearby is not a place at it."""
    said = " ".join((LABEL, school_primary_nearby.DEFINITION, METHOD.sentence)).lower()
    assert "catchment" not in said and "admission" not in said
    assert "not a place at it" in CANNOT_SEE[1]


def test_what_it_cannot_see_is_said_in_two_sentences_with_no_figure_in_them():
    assert len(CANNOT_SEE) == 2
    for sentence in CANNOT_SEE:
        assert sentence.endswith(".") and not re.search(r"[.!?]\s|\d", sentence)
    assert "not within a walk" in CANNOT_SEE[0]
    for words in ("how good a school is", "whether it has a place", "counted as two"):
        assert words in CANNOT_SEE[1]
