"""The nearest town centre, from the publisher's outlines to a distance for each area.

Every file here is made up. `centres_support.py` says where the centres stand
and where the town's homes stand. The figures the tests hold, worked out by
hand from that:

    Quillhaven 001   homes 110, 120, 130, 140   at 150, 250, 150 and 250 metres from Green
    Quillhaven 002   homes 150, 160, 170, 180   at 350, 450, 350 and 450 from Green
    Tallowgate 001   homes 190, 200, 210, 220   at 550 from either, and 450 from Road
"""

import re
from pathlib import Path

import pytest
from burro_core.catalogue import FEATURES
from burro_core.ids import FeatureId, NativeResolution, Polarity
from burro_pipeline.cells import centres, spine
from burro_pipeline.derive import highstreet_access, measures, town_centres
from burro_pipeline.derive.highstreet_access import Access
from burro_pipeline.derive.methods import Worked
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind
from burro_pipeline.evidence.receipt import Geography
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence

from ..cells.support import TOWN, registry
from .centres_support import (
    AREAS,
    AS_AT,
    GREEN,
    OAS,
    QUILLHAVEN_1,
    QUILLHAVEN_2,
    ROAD,
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


def built(folder: Path, packed: bytes | None = None, homes: bytes | None = None) -> Access:
    inputs = inputs_of(folder, packed, homes=homes)
    return highstreet_access.build(inputs, spine.build(inputs))


@pytest.fixture(scope="module")
def town(tmp_path_factory: pytest.TempPathFactory) -> Access:
    return built(tmp_path_factory.mktemp("town"))


# The figure


def test_each_output_area_is_as_far_as_its_centre_is_from_the_nearest_outline(town: Access):
    by_column = {0: 150.0, 1: 250.0, 2: 350.0, 3: 450.0, 4: 550.0, 5: 450.0}
    columns = [unit.squares[0][0] for unit in TOWN if unit.oa in OAS]
    assert [town.of_oa[oa] for oa in OAS] == [by_column[column] for column in columns]


def test_an_area_is_given_the_median_over_its_homes_to_the_nearest_ten_metres(town: Access):
    assert town.worked == {
        # 240 homes at 150 and 260 at 250: half of the 500 are no further than 250.
        QUILLHAVEN_1: Worked(250.0, 4, 4, 1.0, State.PRESENT),
        # 320 at 350 and 340 at 450: half of the 660 are no further than 450.
        QUILLHAVEN_2: Worked(450.0, 4, 4, 1.0, State.PRESENT),
        # 420 at 450 and 400 at 550: half of the 820 are no further than 450.
        TALLOWGATE: Worked(450.0, 4, 4, 1.0, State.PRESENT),
    }


def test_a_figure_is_given_to_the_nearest_ten_metres_with_a_half_taken_upward(tmp_path: Path):
    near = MadeUpCentre("TCB00000007", (box(-205, 0, 100, 200),))
    found = built(tmp_path, centres_gpkg([near]))
    # The homes of column 1 stand 255 metres from the outline.
    assert found.of_oa[OAS[1]] == 255.0
    assert found.worked[QUILLHAVEN_1].value == 260.0
    assert (highstreet_access.NEAREST, highstreet_access.DECIMALS) == (10, -1)


def test_an_area_whose_homes_stand_in_a_town_centre_is_at_nought_and_nought_is_a_figure(
    tmp_path: Path,
):
    over = MadeUpCentre("TCB00000003", (box(0, 0, 200, 200),))
    found = built(tmp_path, centres_gpkg([over]))
    assert found.worked[QUILLHAVEN_1] == Worked(0.0, 4, 4, 1.0, State.PRESENT)


def test_a_far_centre_is_still_the_nearest_and_the_distance_is_given(tmp_path: Path):
    """No reach cuts the distance short: how far the nearest centre is, is the figure."""
    far = MadeUpCentre("TCB00000008", (box(-5_000, 0, 100, 200),))
    found = built(tmp_path, centres_gpkg([far]))
    assert found.worked[QUILLHAVEN_1].value == 5_050.0


# What is not known


def test_a_home_nearer_to_homes_beyond_london_than_to_any_centre_adds_nothing(tmp_path: Path):
    """With Green alone, the homes of columns 3, 4 and 5 may have a nearer centre beyond London."""
    found = built(tmp_path, centres_gpkg([GREEN]), homes_in_the_middle(TOWN))
    assert found.worked == {
        QUILLHAVEN_1: Worked(250.0, 4, 4, 1.0, State.PRESENT),
        # The 320 homes of column 2 alone are known, of 660.
        QUILLHAVEN_2: Worked(None, 2, 4, 0.484848, State.BELOW_THRESHOLD),
        TALLOWGATE: Worked(None, 0, 4, 0.0, State.SOURCE_GAP),
    }


def test_an_area_with_over_half_its_homes_known_is_given_a_figure_and_its_share(tmp_path: Path):
    """The homes of column 3 are 400 metres from the homes beyond London, and 50 from a centre."""
    near = MadeUpCentre("TCB00000010", (box(300, 300, 100, 100),))
    found = built(tmp_path, centres_gpkg([GREEN, near]), homes_in_the_middle(TOWN))
    worked = found.worked[QUILLHAVEN_2]
    assert worked.state is State.PARTIAL or worked.state is State.PRESENT
    assert worked.value is not None and worked.weight_covered >= 0.5


def test_an_output_area_with_no_centre_of_population_is_never_taken_to_be_far(tmp_path: Path):
    found = built(tmp_path, homes=homes_in_the_middle(left_out=[OAS[0]]))
    assert OAS[0] not in found.of_oa
    assert found.worked[QUILLHAVEN_1] == Worked(250.0, 3, 4, 0.78, State.PARTIAL)


def test_a_file_with_no_receipt_stops_the_measure_by_the_rule_a_build_leaves_it_out_for(
    tmp_path: Path,
):
    inputs = inputs_of(tmp_path, with_a_receipt=False)
    with pytest.raises(LockError) as refused:
        highstreet_access.build(inputs, spine.build(inputs))
    assert refused.value.rule == "input_has_one_receipt"


def test_the_order_of_the_rows_changes_nothing(town: Access, tmp_path: Path):
    turned = built(tmp_path, centres_gpkg([ROAD, GREEN]))
    assert turned.worked == town.worked and turned.of_oa == town.of_oa


# The evidence


def test_every_area_has_a_row_of_evidence_that_holds_its_figure(town: Access):
    assert [row.fact_id for row in town.rows] == [
        f"{area}/feature/highstreet_access" for area in AREAS
    ]
    assert [row.value for row in town.rows] == [250.0, 450.0, 450.0]
    assert [(row.units_used, row.units_expected) for row in town.rows] == [(4, 4)] * 3
    assert {row.state for row in town.rows} == {State.PRESENT}


def test_a_row_names_the_town_centres_the_centres_the_lookup_and_the_homes(town: Access):
    by_source = {receipt.source_id: receipt.file_id for receipt in town.files}
    assert sorted(by_source) == sorted(
        [town_centres.SOURCE, centres.CENTRES, spine.LOOKUP, spine.HOMES]
    )
    for row in town.rows:
        assert row.inputs == tuple(sorted(by_source.values()))
        assert row.derivation_id == "straight_line_to_nearest_outline@1"
        # From the day of the census, which the weights are of, to the day of the town centres.
        assert row.data_period is not None
        assert row.data_period.days() == ("2021-03-21", AS_AT)


def test_the_figures_are_marked_as_measured_by_a_method_of_the_measures_own():
    assert highstreet_access.METHODS == (highstreet_access.METHOD,)
    assert highstreet_access.METHOD.name == "straight_line_to_nearest_outline"
    assert highstreet_access.METHOD.kind is Kind.MEASURED
    assert highstreet_access.METHOD.code == "burro_pipeline.derive.highstreet_access"


def test_the_evidence_of_the_measure_has_no_loose_end(town: Access):
    """Every row names a method and files that the evidence of a release would hold."""
    evidence = Evidence.of("lon-2026-10-09-01", town.files, highstreet_access.METHODS, town.rows)
    assert len(evidence.rows) == 3


def test_the_measure_gives_what_the_list_of_measures_asks_of_one(town: Access):
    measured: measures.Measured = town
    assert measured.metric.feature_id is FeatureId.HIGHSTREET_ACCESS
    assert measured.geography is Geography.POLYGON


# The name, the unit and the sentences


def test_the_row_of_the_catalogue_is_a_distance_in_metres_and_core_says_the_same(town: Access):
    """Core's row is held here, so that this fails on the day core names a walk again."""
    core = FEATURES[FeatureId.HIGHSTREET_ACCESS]
    assert core.label == "Straight-line distance to the nearest town centre boundary"
    assert (core.unit, core.polarity) == ("m", Polarity.LESS)
    assert town.metric.label == core.label
    assert (town.metric.unit, town.metric.polarity) == ("m", Polarity.LESS)
    assert town.metric.native_resolution is NativeResolution.POLYGON
    assert measures.says_what_core_says(town.metric)
    as_a_share = town.metric.model_copy(update={"unit": "%", "polarity": Polarity.MORE})
    assert not measures.says_what_core_says(as_a_share)
    listed = {measure.feature: measure for measure in measures.MEASURES}
    assert listed[FeatureId.HIGHSTREET_ACCESS].waits_on == ()


def test_everything_else_of_the_row_is_cores(town: Access):
    metric, core = town.metric, FEATURES[FeatureId.HIGHSTREET_ACCESS]
    for name in ("short_label", "dimension", "kind", "describes", "family", "in_likeness"):
        assert getattr(metric, name) == getattr(core, name)
    assert metric.vintage == AS_AT
    assert metric.source_ids == tuple(sorted(metric.source_ids))


def test_the_definition_is_one_sentence_that_says_what_the_figure_is_and_is_not(town: Access):
    definition = town.metric.definition
    assert definition.endswith(".") and not re.search(r"[.!?]\s|\n", definition)
    for words in (
        f"the Greater London Authority draws in its Town Centre Boundaries as at {AS_AT}",
        "in a straight line",
        "nearest edge of the nearest town centre",
        "census of 2021",
        "to the nearest 10 metres",
        "not along any street",
        "are no border",
        "beyond London",
    ):
        assert words in definition


def test_no_sentence_of_the_measure_describes_who_lives_somewhere(town: Access):
    sentences = (town.metric.label, town.metric.definition, *highstreet_access.CANNOT_SEE)
    assert [sentence for sentence in sentences if RESIDENT_WORDS.search(sentence)] == []


def test_what_it_cannot_see_is_said_in_two_sentences_with_no_figure_in_them():
    assert len(highstreet_access.CANNOT_SEE) == 2
    for sentence in highstreet_access.CANNOT_SEE:
        assert sentence.endswith(".") and not re.search(r"[.!?]\s|\d", sentence)


def test_it_says_a_straight_line_and_a_town_centre_and_never_a_walk_or_a_high_street():
    said = " ".join((highstreet_access.LABEL, highstreet_access.METHOD.sentence)).lower()
    assert "straight" in said and "walk" not in said and "high street" not in said
    assert "and not a walk" in highstreet_access.CANNOT_SEE[0]


def test_the_outlines_are_never_said_to_be_a_border(town: Access):
    """The licence registry asks that the boundaries are never presented as definitive."""
    conditions = " ".join(registry().get(town_centres.SOURCE).conditions)
    assert "Never present them as definitive" in conditions
    assert "are no border" in town.metric.definition
