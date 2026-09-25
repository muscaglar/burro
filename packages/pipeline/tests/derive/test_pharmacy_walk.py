"""The nearest pharmacy, from the publisher's list to a distance for each area.

Every file here is made up: `by_postcode_support.py` lays out the list under
the names of the fields the publisher's page gives, and says where each
contractor stands. No file of the real list has been fetched. No postcode here
is one that has been given out, and no name is a name.
"""

import dataclasses
import re
from pathlib import Path

import pytest
from burro_core.catalogue import FEATURES, NEVER_A_TRADE_OFF
from burro_core.ids import FeatureId, NativeResolution, Polarity
from burro_pipeline.cells import centres, land, postcodes, spine
from burro_pipeline.derive import measures, nearest_by_postcode, pharmacy_walk
from burro_pipeline.derive.measures import says_what_core_says
from burro_pipeline.derive.methods import Worked
from burro_pipeline.derive.nearest_by_postcode import Placing
from burro_pipeline.derive.pharmacy_walk import Walk
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.receipt import Geography
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.postcodes_support import MILL_ROW, NORTH_GATE, QUAY
from ..cells.support import held, registry
from .by_postcode_support import (
    AREAS,
    AT_AN_ENDED_POSTCODE,
    CANARY,
    CONTRACTORS,
    QUILLHAVEN_1,
    QUILLHAVEN_2,
    TALLOWGATE,
    MadeUpContractor,
    inputs_of,
    pharmacy_list,
)


def built(inputs: Inputs) -> Walk:
    return pharmacy_walk.build(inputs, spine.build(inputs))


def of(*contractors: MadeUpContractor, folder: Path) -> Walk:
    return built(inputs_of(folder, contractors=pharmacy_list(contractors)))


def refusal(folder: Path, contractors: bytes) -> str:
    with pytest.raises(LockError) as refused:
        built(inputs_of(folder, contractors=contractors))
    assert refused.value.rule == "input_is_as_described"
    return str(refused.value)


@pytest.fixture(scope="module")
def town(tmp_path_factory: pytest.TempPathFactory) -> Walk:
    return built(inputs_of(tmp_path_factory.mktemp("town")))


# Which contractors count


def test_a_pharmacy_and_a_local_services_contractor_count_and_an_appliance_contractor_does_not(
    town: Walk,
):
    assert town.listed.rows == len(CONTRACTORS) == 6
    assert town.listed.by_type == {"community": 4, "dac": 1, "lps": 1}
    # Two that are placed, and three that count and cannot be placed.
    assert len(town.listed.postcodes) == 5
    assert pharmacy_walk.COUNTS == {"community": True, "lps": True, "dac": False}


def test_an_appliance_contractor_that_is_nearer_changes_no_figure(tmp_path: Path):
    with_one = of(
        MadeUpContractor(NORTH_GATE.postcode),
        MadeUpContractor(MILL_ROW.postcode, contract="DAC"),
        folder=tmp_path / "with",
    )
    without = of(MadeUpContractor(NORTH_GATE.postcode), folder=tmp_path / "without")
    assert with_one.worked == without.worked
    assert with_one.listed.postcodes == (NORTH_GATE.postcode,)


@pytest.mark.parametrize("contract", ["Community", "COMMUNITY", "community", " LPS ", "lps"])
def test_a_type_of_contract_is_read_whatever_its_case(tmp_path: Path, contract: str):
    found = of(MadeUpContractor(MILL_ROW.postcode, contract=contract), folder=tmp_path)
    assert found.placing.placed == 1


# The figure


def test_an_area_is_given_the_median_over_its_homes_to_the_nearest_hundred_metres(town: Walk):
    assert town.worked == {
        # 110 homes at 0 and 250 at 100: half of the 500 are no further than 100.
        QUILLHAVEN_1: Worked(100.0, 4, 4, 1.0, State.PRESENT),
        # 330 homes at 200 and 330 at 224: the homes divide in half, and the mean is 212.
        QUILLHAVEN_2: Worked(200.0, 4, 4, 1.0, State.PRESENT),
        # 220 homes at 0 and 410 at 100: half of the 820 are no further than 100.
        TALLOWGATE: Worked(100.0, 4, 4, 1.0, State.PRESENT),
    }


def test_what_became_of_the_contractors_that_count_is_counted(town: Walk):
    assert town.placing == Placing(
        listed=5,
        placed=2,
        at_an_ended_postcode=0,
        not_a_postcode=1,
        not_of_london=1,
        too_coarse=1,
    )


def test_a_pharmacy_at_an_ended_postcode_is_placed_where_the_postcode_last_stood(
    tmp_path: Path,
):
    found = of(MadeUpContractor(AT_AN_ENDED_POSTCODE), folder=tmp_path)
    assert (found.placing.placed, found.placing.at_an_ended_postcode) == (1, 1)


def test_with_no_pharmacy_in_tallowgate_its_homes_have_no_distance_and_none_is_filled_in(
    tmp_path: Path,
):
    found = of(MadeUpContractor(NORTH_GATE.postcode), folder=tmp_path)
    assert found.worked[TALLOWGATE] == Worked(None, 0, 4, 0.0, State.SOURCE_GAP)
    assert len(found.distances.near_the_edge) == 4
    assert [row.value for row in found.rows] == [100.0, 300.0, None]


# What is never read


def test_the_fields_that_may_name_a_person_are_never_read():
    assert pharmacy_walk.READ == ("POST_CODE", "CONTRACT_TYPE")
    assert not set(pharmacy_walk.NEVER_READ) & set(pharmacy_walk.READ)
    assert "ORGANISATION_NAME" in pharmacy_walk.NEVER_READ
    assert set(pharmacy_walk.READ) | set(pharmacy_walk.NEVER_READ) <= set(pharmacy_walk.HELD)
    assert len(pharmacy_walk.HELD) == 25
    assert (pharmacy_walk.HELD[8], pharmacy_walk.HELD[-1]) == ("POST_CODE", "CONTRACT_TYPE")


def test_nothing_of_a_field_that_is_not_read_is_kept(town: Walk):
    assert CANARY in pharmacy_list().decode()
    kept = repr(dataclasses.asdict(town.listed)) + repr(town.rows) + repr(town.metric)
    assert CANARY not in kept
    assert CANARY not in repr(town.placing) + repr(town.distances)


def test_a_list_with_the_two_fields_alone_reads_the_same(tmp_path: Path, town: Walk):
    found = built(inputs_of(tmp_path, contractors=pharmacy_list(columns=pharmacy_walk.READ)))
    assert found.worked == town.worked
    assert found.listed == dataclasses.replace(town.listed, file_id=found.listed.file_id)


def test_what_is_printed_of_the_list_holds_no_postcode(town: Walk):
    said = repr(town.listed) + repr(town.placing) + repr(town.rows) + repr(town.metric)
    for contractor in CONTRACTORS:
        assert contractor.postcode not in said
    assert repr(town.listed) == "Listed(rows=6, counted=5)"


# A file that is not as the step expects


@pytest.mark.parametrize("column", pharmacy_walk.READ)
def test_a_list_that_lacks_a_field_that_is_read_stops_the_step(tmp_path: Path, column: str):
    columns = [name for name in pharmacy_walk.HELD if name != column]
    assert "a column is missing" in refusal(tmp_path, pharmacy_list(columns=columns))


@pytest.mark.parametrize("contract", ["", "Pharmacy", "Distance Selling", "C"])
def test_a_type_of_contract_the_page_does_not_name_stops_the_step(tmp_path: Path, contract: str):
    said = refusal(tmp_path, pharmacy_list([MadeUpContractor("QH1 1CK", contract=contract)]))
    assert "a type of contract is not one the page names" in said
    assert "QH1 1CK" not in said and CANARY not in said
    assert not contract or contract not in said


def test_a_list_with_no_row_stops_the_step(tmp_path: Path):
    assert "it holds no row" in refusal(tmp_path, pharmacy_list([]))


def test_a_list_that_is_not_utf8_stops_the_step(tmp_path: Path):
    assert "it could not be read as text" in refusal(tmp_path, pharmacy_list() + b"\xff\xfe\r\n")


@pytest.mark.parametrize(
    ("name", "is_one"),
    [
        ("consol_pharmacy_list_202606q1.csv", True),
        ("consol_pharmacy_list_202526q4.csv", True),
        ("consol_pharmacy_list_202526q3final.csv", True),
        ("consol_pharmacy_list_202526q5.csv", False),
        ("consol_pharmacy_list.csv", False),
        ("contractor_details_202606.csv", False),
        ("edispensary.csv", False),
    ],
)
def test_a_file_of_the_list_is_known_by_its_name(name: str, is_one: bool):
    assert pharmacy_walk.is_the_list(name) is is_one


# The evidence


def test_every_area_has_a_row_that_holds_its_figure(town: Walk):
    assert [row.fact_id for row in town.rows] == [f"{area}/feature/pharmacy_walk" for area in AREAS]
    assert [row.value for row in town.rows] == [100.0, 200.0, 100.0]
    for row in town.rows:
        assert row.derivation_id == "straight_line_to_nearest_by_postcode@1"
        assert row.retrieved_on == "2026-09-24"
        assert row.data_period is not None
        assert row.data_period.days() == ("2021-03-21", "2026-08-31")


def test_a_row_rests_on_the_list_the_directory_the_centres_the_lookup_and_the_homes(
    town: Walk,
):
    by_source = {receipt.source_id: receipt.file_id for receipt in town.files}
    assert set(by_source) == {
        pharmacy_walk.SOURCE,
        postcodes.SOURCE,
        centres.CENTRES,
        spine.LOOKUP,
        spine.HOMES,
    }
    for row in town.rows:
        assert set(row.inputs) == set(by_source.values())


def test_the_evidence_of_the_measure_has_no_loose_end(town: Walk):
    evidence = Evidence.of("lon-2026-10-02-01", town.files, pharmacy_walk.METHODS, town.rows)
    assert len(evidence.rows) == 3
    assert town.geography is Geography.POSTCODE
    assert pharmacy_walk.METHODS == (nearest_by_postcode.METHOD,)


# The gate and the store


@pytest.mark.parametrize("source", [pharmacy_walk.SOURCE, postcodes.SOURCE, centres.CENTRES])
def test_the_gate_is_asked_about_every_file_before_it_is_read(tmp_path: Path, source: str):
    sources = [
        one.model_copy(update={"uses": (Use.DISPLAY,)}) if one.id == source else one
        for one in registry()
    ]
    inputs = inputs_of(tmp_path, given=Registry(tuple(sources)))
    found = spine.build(inputs)
    with pytest.raises(LockError) as stopped:
        pharmacy_walk.build(inputs, found)
    assert stopped.value.rule == "gate_refuses"
    assert source not in {one.receipt.source_id for one in inputs.opened}


def test_every_file_behind_a_figure_is_registered_for_scoring(town: Walk):
    assert town.metric.source_ids == (
        "nhsbsa-consolidated-pharmaceutical-list",
        "ons-census-2021-housing-tables",
        "ons-oa-pwc-2021",
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
        "ons-postcode-directory",
    )
    for source_id in town.metric.source_ids:
        assert Use.SCORING in registry().get(source_id).uses


def test_the_three_credits_of_the_directory_stand_with_the_figure(town: Walk):
    assert pharmacy_walk.credits_of(town) == (
        "Contains OS data © Crown copyright and database right 2026",
        "Contains Royal Mail data © Royal Mail copyright and database right 2026",
        "Source: Office for National Statistics licensed under the Open Government Licence v.3.0",
    )


def test_nothing_is_written_to_the_store(tmp_path: Path):
    inputs = inputs_of(tmp_path)
    before = held(tmp_path / "store")
    built(inputs)
    assert held(tmp_path / "store") == before


# The name, the unit and the sentences


def test_the_name_says_it_is_a_straight_line_and_core_says_the_same(town: Walk):
    """Core's words are held here, so that this fails on the day core names a walk again."""
    metric, core = town.metric, FEATURES[FeatureId.PHARMACY_WALK]
    assert metric.label == "Straight-line distance to the nearest pharmacy, placed by its postcode"
    assert "walk" not in metric.label.lower()
    assert (core.label, core.unit) == (metric.label, "m")
    assert core.native_resolution is NativeResolution.POINT
    assert NEVER_A_TRADE_OFF[FeatureId.PHARMACY_WALK] == 800
    assert (metric.unit, metric.polarity) == ("m", Polarity.LESS)
    assert metric.native_resolution is NativeResolution.POINT
    assert says_what_core_says(metric)
    assert not says_what_core_says(metric.model_copy(update={"unit": "min"}))
    assert metric.vintage == "2026-04-01 to 2026-06-30"
    # Everything else that core decides of the feature is as core has it.
    for name in ("short_label", "dimension", "polarity", "kind", "describes", "family"):
        assert getattr(metric, name) == getattr(core, name)


def test_the_measure_is_carried_and_waits_on_nothing():
    assert pharmacy_walk.WAITS_ON == ()


def test_the_measure_is_on_the_list_and_is_called_as_the_list_calls_each(
    tmp_path: Path, town: Walk
):
    (measure,) = [one for one in measures.MEASURES if one.feature is pharmacy_walk.FEATURE]
    assert (measure.source, measure.methods) == (pharmacy_walk.SOURCE, pharmacy_walk.METHODS)
    assert measure.cannot_see == pharmacy_walk.CANNOT_SEE
    assert (measure.waits_on, measure.held_back) == ((), ())
    assert measure.reads("consol_pharmacy_list_202606q1.csv")
    assert not measure.reads("epraccur.csv")
    inputs = inputs_of(tmp_path)
    found = spine.build(inputs)
    made = measure.build(inputs, measures.Ground(found, land.build(inputs, found)))
    assert made.worked == town.worked
    assert (made.rows, made.metric, made.geography) == (town.rows, town.metric, town.geography)
    assert [receipt.source_id for receipt in made.files if measure.reads(receipt.publisher_file)]
    assert not measure.in_squares


def test_the_definition_is_one_sentence_that_says_it_is_a_straight_line(town: Walk):
    definition = town.metric.definition
    assert definition == pharmacy_walk.definition_of("2026-04-01", "2026-06-30")
    assert definition.endswith(".") and not re.search(r"[.!?]\s|\n", definition)
    # The list is of a quarter, and nothing says what day it is as at.
    assert "as at" not in definition
    assert "as at 2026-06-30" in pharmacy_walk.definition_of("2026-06-30", "2026-06-30")
    for words in (
        "in a straight line",
        "Consolidated Pharmaceutical List of the NHS Business Services Authority",
        "for the period from 2026-04-01 to 2026-06-30",
        "ONS Postcode Directory",
        "median",
        "census of 2021",
        "nearest 100 metres",
        "not along any street",
        "the walk is longer",
        "a door of its postcode that may not be its own",
        "a pharmacy that serves by post alone is counted",
        "a pharmacy outside London is not counted",
    ):
        assert words in definition


RESIDENT_WORDS = re.compile(
    r"\b(residents?|people|population|households?|famil(y|ies)|health|ages?|incomes?)\b", re.I
)


def test_no_sentence_of_the_measure_describes_who_lives_somewhere(town: Walk):
    sentences = (town.metric.definition, *pharmacy_walk.CANNOT_SEE, pharmacy_walk.METHOD.sentence)
    assert [sentence for sentence in sentences if RESIDENT_WORDS.search(sentence)] == []


def test_what_it_cannot_see_is_said_in_whole_sentences():
    assert len(pharmacy_walk.CANNOT_SEE) == 6
    for sentence in pharmacy_walk.CANNOT_SEE:
        assert sentence.endswith(".") and not re.search(r"[.!?]\s", sentence)
    assert "not a walk" in pharmacy_walk.CANNOT_SEE[0]
    assert "serve by post alone" in pharmacy_walk.CANNOT_SEE[4]
    assert QUAY.postcode not in "".join(pharmacy_walk.CANNOT_SEE)
