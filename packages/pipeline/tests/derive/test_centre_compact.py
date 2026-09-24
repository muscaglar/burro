"""A compact town centre, from the publisher's outlines to a figure for each area.

Every file here is made up. `centres_support.py` says where the centres stand
and where the town's homes stand. The figures the tests hold, worked out by
hand from that:

    Green, a square, fills 63.66 in 100 of the circle round it. Road, a strip five times
    as long as it is wide, fills 24.49.

    Quillhaven 001   every home is nearest to Green                          63.7
    Quillhaven 002   every home is nearest to Green                          63.7
    Tallowgate 001   400 homes are given to Green and 420 are nearest to
                     Road: half of the 820 have a centre that fills 24.49    24.5
"""

import re
from pathlib import Path

import pytest
from burro_core.catalogue import FEATURES
from burro_core.ids import FeatureId, NativeResolution, Polarity
from burro_pipeline.cells import centres, spine
from burro_pipeline.derive import centre_compact, measures, town_centres
from burro_pipeline.derive.centre_compact import Compact
from burro_pipeline.derive.methods import Worked
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence

from ..cells.support import TOWN
from .centres_support import (
    AREAS,
    AS_AT,
    GREEN,
    GREEN_FILLS,
    OAS,
    QUILLHAVEN_1,
    QUILLHAVEN_2,
    ROAD,
    ROAD_FILLS,
    TALLOWGATE,
    MadeUpCentre,
    box,
    centres_gpkg,
    homes_in_the_middle,
    inputs_of,
)

RESIDENT_WORDS = re.compile(
    r"\b(residents?|people|population|households?|famil(y|ies)|health|ages?|incomes?)\b", re.I
)


def built(folder: Path, packed: bytes | None = None, homes: bytes | None = None) -> Compact:
    inputs = inputs_of(folder, packed, homes=homes)
    return centre_compact.build(inputs, spine.build(inputs))


@pytest.fixture(scope="module")
def town(tmp_path_factory: pytest.TempPathFactory) -> Compact:
    return built(tmp_path_factory.mktemp("town"))


# What is compact


def test_a_centre_round_a_green_fills_more_of_its_circle_than_one_along_a_road(town: Compact):
    assert town.of_oa[OAS[0]] == pytest.approx(GREEN_FILLS)
    assert town.of_oa[OAS[9]] == pytest.approx(ROAD_FILLS)
    assert pytest.approx(63.66, abs=0.01) == GREEN_FILLS
    assert pytest.approx(24.49, abs=0.01) == ROAD_FILLS


def test_a_large_centre_is_as_compact_as_a_small_one_of_the_same_shape(tmp_path: Path):
    """The measure of a small centre says how large a centre is. This one says its shape."""
    large = MadeUpCentre("TCB00000014", (box(-1100, -400, 1000, 1000),))
    found = built(tmp_path, centres_gpkg([large]))
    assert found.found.centres["TCB00000014"].hectares == 100.0
    assert found.of_oa[OAS[0]] == pytest.approx(GREEN_FILLS)


# The figure


def test_each_output_area_has_the_value_of_its_nearest_centre(town: Compact):
    fills = {0: GREEN_FILLS, 1: GREEN_FILLS, 2: GREEN_FILLS, 3: GREEN_FILLS}
    fills |= {4: GREEN_FILLS, 5: ROAD_FILLS}
    columns = [unit.squares[0][0] for unit in TOWN if unit.oa in OAS]
    assert [town.of_oa[oa] for oa in OAS] == pytest.approx([fills[column] for column in columns])


def test_an_area_is_given_the_median_over_its_homes_to_one_decimal_place(town: Compact):
    assert town.worked == {
        QUILLHAVEN_1: Worked(63.7, 4, 4, 1.0, State.PRESENT),
        QUILLHAVEN_2: Worked(63.7, 4, 4, 1.0, State.PRESENT),
        TALLOWGATE: Worked(24.5, 4, 4, 1.0, State.PRESENT),
    }
    assert centre_compact.DECIMALS == 1


def test_an_area_whose_homes_look_to_one_centre_is_given_that_centres_own_figure(
    tmp_path: Path,
):
    found = built(tmp_path, centres_gpkg([ROAD]))
    assert found.worked[TALLOWGATE].value == 24.5
    assert found.worked[QUILLHAVEN_2].value == 24.5


# What is not known


def test_a_home_with_no_centre_within_800_metres_has_no_value(tmp_path: Path):
    """With Road alone, the homes of Quillhaven 001 stand 850 and 950 metres from a centre."""
    found = built(tmp_path, centres_gpkg([ROAD]))
    assert not set(OAS[:4]) & set(found.of_oa)
    assert found.worked[QUILLHAVEN_1] == Worked(None, 0, 4, 0.0, State.SOURCE_GAP)


def test_an_area_with_over_half_its_homes_near_a_centre_is_given_a_figure_and_its_share(
    tmp_path: Path,
):
    east = MadeUpCentre("TCB00000012", (box(900, 0, 200, 200),))
    found = built(tmp_path, centres_gpkg([east]))
    assert found.worked[QUILLHAVEN_1] == Worked(63.7, 2, 4, 0.52, State.PARTIAL)


def test_below_half_the_homes_near_a_centre_no_figure_is_given(tmp_path: Path):
    west = MadeUpCentre("TCB00000013", (box(-900, 0, 200, 200),))
    found = built(tmp_path, centres_gpkg([west]))
    assert found.worked[QUILLHAVEN_1] == Worked(None, 2, 4, 0.48, State.BELOW_THRESHOLD)


def test_a_home_nearer_to_homes_beyond_london_than_to_any_centre_has_no_value(tmp_path: Path):
    found = built(tmp_path, centres_gpkg([GREEN]), homes_in_the_middle(TOWN))
    assert found.worked == {
        QUILLHAVEN_1: Worked(63.7, 4, 4, 1.0, State.PRESENT),
        QUILLHAVEN_2: Worked(None, 2, 4, 0.484848, State.BELOW_THRESHOLD),
        TALLOWGATE: Worked(None, 0, 4, 0.0, State.SOURCE_GAP),
    }


def test_a_file_with_no_receipt_stops_the_measure_by_the_rule_a_build_leaves_it_out_for(
    tmp_path: Path,
):
    inputs = inputs_of(tmp_path, with_a_receipt=False)
    with pytest.raises(LockError) as refused:
        centre_compact.build(inputs, spine.build(inputs))
    assert refused.value.rule == "input_has_one_receipt"


def test_the_order_of_the_rows_changes_nothing(town: Compact, tmp_path: Path):
    turned = built(tmp_path, centres_gpkg([ROAD, GREEN]))
    assert turned.worked == town.worked and turned.of_oa == town.of_oa


# The evidence


def test_every_area_has_a_row_of_evidence_that_holds_its_figure(town: Compact):
    assert [row.fact_id for row in town.rows] == [
        f"{area}/feature/centre_compact" for area in AREAS
    ]
    assert [row.value for row in town.rows] == [63.7, 63.7, 24.5]
    assert {row.state for row in town.rows} == {State.PRESENT}


def test_a_row_names_the_town_centres_the_centres_the_lookup_and_the_homes(town: Compact):
    by_source = {receipt.source_id: receipt.file_id for receipt in town.files}
    assert sorted(by_source) == sorted(
        [town_centres.SOURCE, centres.CENTRES, spine.LOOKUP, spine.HOMES]
    )
    for row in town.rows:
        assert row.inputs == tuple(sorted(by_source.values()))
        assert row.derivation_id == "circle_filled_by_nearest_outline@1"


def test_the_method_states_the_reach():
    method = centre_compact.METHOD
    assert (method,) == centre_compact.METHODS
    assert method.kind is Kind.MEASURED
    assert method.parameters == {"metres": 800, "enough_in_100": 50}
    assert "within 800 metres" in method.sentence


def test_the_evidence_of_the_measure_has_no_loose_end(town: Compact):
    evidence = Evidence.of("lon-2026-10-09-01", town.files, centre_compact.METHODS, town.rows)
    assert len(evidence.rows) == 3


def test_the_measure_gives_what_the_list_of_measures_asks_of_one(town: Compact):
    measured: measures.Measured = town
    assert measured.metric.feature_id is FeatureId.CENTRE_COMPACT


# The name, the unit and the sentences


def test_the_row_of_the_catalogue_is_the_shape_of_a_centre_where_core_gives_its_reach(
    town: Compact,
):
    """Core's label is held here, so that this fails on the day core changes it.

    On that day the two are brought together: either core says the circle
    round a centre, and the measure is carried, or the figure is made what
    core says.
    """
    core = FEATURES[FeatureId.CENTRE_COMPACT]
    assert core.label == "Share of the nearest town centre within 200 m of its middle"
    assert town.metric.label == (
        "Share of the smallest circle round the nearest town centre that the centre fills, "
        "for homes within 800 m of one"
    )
    assert not measures.says_what_core_says(town.metric)
    assert len(centre_compact.WAITS_ON) == 2


def test_the_unit_and_which_way_is_more_are_cores(town: Compact):
    metric, core = town.metric, FEATURES[FeatureId.CENTRE_COMPACT]
    for name in ("short_label", "dimension", "unit", "polarity", "kind", "describes", "family"):
        assert getattr(metric, name) == getattr(core, name)
    assert (metric.unit, metric.polarity) == ("%", Polarity.MORE)
    assert metric.native_resolution is NativeResolution.POLYGON
    assert metric.vintage == AS_AT


def test_the_definition_is_one_sentence_that_says_what_the_figure_is_and_is_not(town: Compact):
    definition = town.metric.definition
    assert definition.endswith(".") and not re.search(r"[.!?]\s|\n", definition)
    for words in (
        f"the Greater London Authority draws in its Town Centre Boundaries as at {AS_AT}",
        "within 800 metres, in a straight line",
        "the smallest circle that holds all of that outline",
        "census of 2021",
        "to 1 decimal place",
        "the shape of the outline and not its size",
        "are no border",
        "is not counted",
    ):
        assert words in definition


def test_no_sentence_of_the_measure_describes_who_lives_somewhere(town: Compact):
    sentences = (town.metric.label, town.metric.definition, *centre_compact.CANNOT_SEE)
    assert [sentence for sentence in sentences if RESIDENT_WORDS.search(sentence)] == []


def test_what_it_cannot_see_is_said_in_two_sentences_with_no_figure_in_them():
    assert len(centre_compact.CANNOT_SEE) == 2
    for sentence in centre_compact.CANNOT_SEE:
        assert sentence.endswith(".") and not re.search(r"[.!?]\s|\d", sentence)


def test_it_says_that_it_reads_the_outline_a_planner_drew():
    assert "the shape of the outline a planner drew" in centre_compact.CANNOT_SEE[0]
    assert "village" not in centre_compact.LABEL.lower()
