"""A small town centre, from the publisher's outlines to a share of homes for each area.

Every file here is made up. `centres_support.py` says where the centres stand
and where the town's homes stand. The figures the tests hold, worked out by
hand from that:

    Green, 4 hectares, is small. Road, 20 hectares, is not.

    Quillhaven 001   every home is nearest to Green                     500 of 500 homes
    Quillhaven 002   every home is nearest to Green                     660 of 660
    Tallowgate 001   the 400 homes of column 4 are given to Green,
                     and the 420 of column 5 are nearest to Road        400 of 820
"""

import re
from pathlib import Path

import pytest
from burro_core.catalogue import FEATURES
from burro_core.ids import FeatureId, NativeResolution, Polarity
from burro_pipeline.cells import centres, spine
from burro_pipeline.derive import centre_small, measures, town_centres
from burro_pipeline.derive.centre_small import Small
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


def built(folder: Path, packed: bytes | None = None, homes: bytes | None = None) -> Small:
    inputs = inputs_of(folder, packed, homes=homes)
    return centre_small.build(inputs, spine.build(inputs))


@pytest.fixture(scope="module")
def town(tmp_path_factory: pytest.TempPathFactory) -> Small:
    return built(tmp_path_factory.mktemp("town"))


# What is small


def test_a_centre_is_small_under_10_hectares_and_not_at_10(tmp_path: Path):
    under = MadeUpCentre("TCB00000011", (box(-1100, 0, 999, 100),))
    found = built(tmp_path / "under", centres_gpkg([under]))
    assert found.found.centres["TCB00000011"].hectares == 9.99
    assert found.of_oa[OAS[0]] is True
    at = MadeUpCentre("TCB00000011", (box(-1101, 0, 1000, 100),))
    found = built(tmp_path / "at", centres_gpkg([at]))
    assert found.found.centres["TCB00000011"].hectares == 10.0
    assert found.of_oa[OAS[0]] is False
    assert centre_small.SMALL_UNDER == 10


def test_the_class_of_a_centre_makes_it_neither_small_nor_large(tmp_path: Path):
    """A centre of a high class that covers little ground is small, and the other way round."""
    little = MadeUpCentre("TCB00000001", GREEN.pieces, rank="Metropolitan")
    long = MadeUpCentre("TCB00000002", ROAD.pieces, rank="Local Centre")
    found = built(tmp_path, centres_gpkg([little, long]))
    assert found.of_oa[OAS[0]] is True and found.of_oa[OAS[9]] is False


# The figure


def test_each_output_area_has_the_verdict_of_its_nearest_centre(town: Small):
    small = {0: True, 1: True, 2: True, 3: True, 4: True, 5: False}
    columns = [unit.squares[0][0] for unit in TOWN if unit.oa in OAS]
    assert [town.of_oa[oa] for oa in OAS] == [small[column] for column in columns]


def test_an_area_is_given_the_share_of_its_homes_whose_nearest_centre_is_small(town: Small):
    assert town.worked == {
        QUILLHAVEN_1: Worked(100.0, 4, 4, 1.0, State.PRESENT),
        QUILLHAVEN_2: Worked(100.0, 4, 4, 1.0, State.PRESENT),
        # 400 of 820 is 48.78.
        TALLOWGATE: Worked(48.8, 4, 4, 1.0, State.PRESENT),
    }
    assert centre_small.DECIMALS == 1


def test_an_area_whose_homes_all_have_a_larger_centre_nearest_is_at_nought(tmp_path: Path):
    """Nought is a figure: each home has a town centre near, and it is not a small one."""
    found = built(tmp_path, centres_gpkg([ROAD]))
    assert found.worked[TALLOWGATE] == Worked(0.0, 4, 4, 1.0, State.PRESENT)
    assert found.worked[QUILLHAVEN_2] == Worked(0.0, 4, 4, 1.0, State.PRESENT)


# What is not known


def test_a_home_with_no_centre_within_800_metres_is_never_counted_as_having_none(
    tmp_path: Path,
):
    """With Road alone, the homes of Quillhaven 001 stand 850 and 950 metres from a centre.

    The file holds few local centres, so whether they have a small one near is
    not known. The area has no figure, and it is not nought.
    """
    found = built(tmp_path, centres_gpkg([ROAD]))
    assert not set(OAS[:4]) & set(found.of_oa)
    assert found.worked[QUILLHAVEN_1] == Worked(None, 0, 4, 0.0, State.SOURCE_GAP)


def test_an_area_with_over_half_its_homes_near_a_centre_is_given_a_figure_and_its_share(
    tmp_path: Path,
):
    """A centre 750 metres from the homes of column 1, and 850 from those of column 0."""
    east = MadeUpCentre("TCB00000012", (box(900, 0, 100, 200),))
    found = built(tmp_path, centres_gpkg([east]))
    # The 260 homes of column 1 have a verdict, of 500.
    assert found.worked[QUILLHAVEN_1] == Worked(100.0, 2, 4, 0.52, State.PARTIAL)


def test_below_half_the_homes_near_a_centre_no_figure_is_given(tmp_path: Path):
    """A centre 750 metres from the homes of column 0, and 850 from those of column 1."""
    west = MadeUpCentre("TCB00000013", (box(-800, 0, 100, 200),))
    found = built(tmp_path, centres_gpkg([west]))
    # The 240 homes of column 0 have a verdict, of 500.
    assert found.worked[QUILLHAVEN_1] == Worked(None, 2, 4, 0.48, State.BELOW_THRESHOLD)
    assert found.worked[QUILLHAVEN_2] == Worked(None, 0, 4, 0.0, State.SOURCE_GAP)


def test_a_home_nearer_to_homes_beyond_london_than_to_any_centre_has_no_verdict(tmp_path: Path):
    """With Green alone, the homes of columns 3, 4 and 5 may have a nearer centre beyond London."""
    found = built(tmp_path, centres_gpkg([GREEN]), homes_in_the_middle(TOWN))
    assert found.worked == {
        QUILLHAVEN_1: Worked(100.0, 4, 4, 1.0, State.PRESENT),
        QUILLHAVEN_2: Worked(None, 2, 4, 0.484848, State.BELOW_THRESHOLD),
        TALLOWGATE: Worked(None, 0, 4, 0.0, State.SOURCE_GAP),
    }


def test_a_file_with_no_receipt_stops_the_measure_by_the_rule_a_build_leaves_it_out_for(
    tmp_path: Path,
):
    inputs = inputs_of(tmp_path, with_a_receipt=False)
    with pytest.raises(LockError) as refused:
        centre_small.build(inputs, spine.build(inputs))
    assert refused.value.rule == "input_has_one_receipt"


def test_the_order_of_the_rows_changes_nothing(town: Small, tmp_path: Path):
    turned = built(tmp_path, centres_gpkg([ROAD, GREEN]))
    assert turned.worked == town.worked and turned.of_oa == town.of_oa


# The evidence


def test_every_area_has_a_row_of_evidence_that_holds_its_figure(town: Small):
    assert [row.fact_id for row in town.rows] == [f"{area}/feature/centre_small" for area in AREAS]
    assert [row.value for row in town.rows] == [100.0, 100.0, 48.8]
    assert {row.state for row in town.rows} == {State.PRESENT}


def test_a_row_names_the_town_centres_the_centres_the_lookup_and_the_homes(town: Small):
    by_source = {receipt.source_id: receipt.file_id for receipt in town.files}
    assert sorted(by_source) == sorted(
        [town_centres.SOURCE, centres.CENTRES, spine.LOOKUP, spine.HOMES]
    )
    for row in town.rows:
        assert row.inputs == tuple(sorted(by_source.values()))
        assert row.derivation_id == "homes_whose_nearest_outline_is_small@1"


def test_the_method_states_the_reach_and_the_size_a_centre_is_small_under():
    method = centre_small.METHOD
    assert (method,) == centre_small.METHODS
    assert method.kind is Kind.MEASURED
    assert method.parameters == {"metres": 800, "hectares": 10, "enough_in_100": 50}
    assert "within 800 metres" in method.sentence and "under 10 hectares" in method.sentence


def test_the_evidence_of_the_measure_has_no_loose_end(town: Small):
    evidence = Evidence.of("lon-2026-10-09-01", town.files, centre_small.METHODS, town.rows)
    assert len(evidence.rows) == 3


def test_the_measure_gives_what_the_list_of_measures_asks_of_one(town: Small):
    measured: measures.Measured = town
    assert measured.metric.feature_id is FeatureId.CENTRE_SMALL


# The name, the unit and the sentences


def test_the_row_of_the_catalogue_counts_the_homes_with_a_centre_near_where_core_counts_all(
    town: Small,
):
    """Core's label is held here, so that this fails on the day core changes it.

    On that day the two are brought together: either core says which homes
    are counted and what small is, and the measure is carried, or the figure
    is made what core says.
    """
    core = FEATURES[FeatureId.CENTRE_SMALL]
    assert core.label == "Share of homes whose nearest town centre is a small one"
    assert town.metric.label == (
        "Share of homes within 800 m of a town centre whose nearest town centre is under 10 ha"
    )
    assert not measures.says_what_core_says(town.metric)
    assert len(centre_small.WAITS_ON) == 2


def test_the_unit_and_which_way_is_more_are_cores(town: Small):
    metric, core = town.metric, FEATURES[FeatureId.CENTRE_SMALL]
    for name in ("short_label", "dimension", "unit", "polarity", "kind", "describes", "family"):
        assert getattr(metric, name) == getattr(core, name)
    assert (metric.unit, metric.polarity) == ("%", Polarity.MORE)
    assert metric.native_resolution is NativeResolution.POLYGON
    assert metric.vintage == AS_AT


def test_the_definition_is_one_sentence_that_says_what_the_figure_is_and_is_not(town: Small):
    definition = town.metric.definition
    assert definition.endswith(".") and not re.search(r"[.!?]\s|\n", definition)
    for words in (
        f"the Greater London Authority draws in its Town Centre Boundaries as at {AS_AT}",
        "within 800 metres, in a straight line",
        "encloses under 10 hectares",
        "census of 2021",
        "to 1 decimal place",
        "not by its class or its shops",
        "are no border",
        "is not counted above or below the line",
    ):
        assert words in definition


def test_no_sentence_of_the_measure_describes_who_lives_somewhere(town: Small):
    sentences = (town.metric.label, town.metric.definition, *centre_small.CANNOT_SEE)
    assert [sentence for sentence in sentences if RESIDENT_WORDS.search(sentence)] == []


def test_what_it_cannot_see_is_said_in_two_sentences_with_no_figure_in_them():
    assert len(centre_small.CANNOT_SEE) == 2
    for sentence in centre_small.CANNOT_SEE:
        assert sentence.endswith(".") and not re.search(r"[.!?]\s|\d", sentence)


def test_it_never_says_that_a_place_is_a_village():
    """The figure is the size of an outline. What a place feels like is no part of it."""
    said = " ".join((centre_small.LABEL, centre_small.METHOD.sentence)).lower()
    assert "village" not in said
    assert "cannot tell a quiet village centre from a short parade" in centre_small.CANNOT_SEE[0]
