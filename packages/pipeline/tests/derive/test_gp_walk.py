"""The nearest GP practice, from the publisher's report to a distance for each area.

Every file here is made up: `by_postcode_support.py` lays out the report as
the publisher's specification says, and says where each practice stands. No
file of the real report has been fetched. No postcode here is one that has
been given out, and no name is a name.
"""

import dataclasses
import re
from pathlib import Path

import pytest
from burro_core.catalogue import FEATURES, NEVER_A_TRADE_OFF
from burro_core.ids import FeatureId, NativeResolution, Polarity
from burro_pipeline.cells import centres, land, postcodes, spine
from burro_pipeline.derive import gp_walk, measures, nearest_by_postcode
from burro_pipeline.derive.gp_walk import Walk
from burro_pipeline.derive.measures import says_what_core_says
from burro_pipeline.derive.methods import Worked
from burro_pipeline.derive.nearest_by_postcode import Placing
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.receipt import Geography
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.postcodes_support import MILL_ROW, NORTH_GATE, OF_NORTHERN_IRELAND, QUAY
from ..cells.support import held, registry
from .by_postcode_support import (
    AREAS,
    AT_A_LONG_ENDED_POSTCODE,
    AT_AN_ENDED_POSTCODE,
    CANARY,
    PRACTICES,
    QUILLHAVEN_1,
    QUILLHAVEN_2,
    TALLOWGATE,
    MadeUpPractice,
    centres_with_the_district,
    inputs_of,
    report,
)


def built(inputs: Inputs) -> Walk:
    return gp_walk.build(inputs, spine.build(inputs))


def of(*practices: MadeUpPractice, folder: Path) -> Walk:
    return built(inputs_of(folder, practices=report(practices)))


def refusal(folder: Path, practices: bytes) -> str:
    with pytest.raises(LockError) as refused:
        built(inputs_of(folder, practices=practices))
    assert refused.value.rule == "input_is_as_described"
    return str(refused.value)


@pytest.fixture(scope="module")
def town(tmp_path_factory: pytest.TempPathFactory) -> Walk:
    return built(inputs_of(tmp_path_factory.mktemp("town")))


# Which practices count


def test_a_practice_counts_where_it_is_active_open_and_of_the_setting_of_a_gp_practice(
    town: Walk,
):
    assert town.report.rows == len(PRACTICES) == 11
    assert town.report.by_status == {"active": 8, "closed": 1, "dormant": 1, "proposed": 1}
    assert town.report.of_a_gp_practice == 9
    # Two that are placed, and three that count and cannot be placed.
    assert len(town.report.postcodes) == 5


@pytest.mark.parametrize(
    "practice",
    [
        MadeUpPractice(MILL_ROW.postcode, status="CLOSED", closed="20190331"),
        MadeUpPractice(MILL_ROW.postcode, status="CLOSED"),
        MadeUpPractice(MILL_ROW.postcode, status="DORMANT"),
        MadeUpPractice(MILL_ROW.postcode, status="PROPOSED"),
        # It is active still, and the day it closes is given.
        MadeUpPractice(MILL_ROW.postcode, closed="20261231"),
        # A walk-in centre, a prison, a hospital service: another setting.
        MadeUpPractice(MILL_ROW.postcode, setting="RO80"),
        MadeUpPractice(MILL_ROW.postcode, setting="RO7"),
        MadeUpPractice(MILL_ROW.postcode, setting="RO760"),
        MadeUpPractice(MILL_ROW.postcode, setting=""),
    ],
)
def test_a_practice_that_is_not_open_or_is_no_gp_practice_does_not_count(
    tmp_path: Path, practice: MadeUpPractice
):
    found = of(MadeUpPractice(NORTH_GATE.postcode), practice, folder=tmp_path)
    assert found.report.postcodes == (NORTH_GATE.postcode,)
    assert found.placing.listed == 1


@pytest.mark.parametrize("status", ["ACTIVE", "Active", "active", " ACTIVE "])
def test_a_status_is_read_whatever_its_case(tmp_path: Path, status: str):
    found = of(MadeUpPractice(MILL_ROW.postcode, status=status), folder=tmp_path)
    assert found.report.by_status == {"active": 1}
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


def test_what_became_of_the_practices_that_count_is_counted(town: Walk):
    assert town.placing == Placing(
        listed=5,
        placed=2,
        at_an_ended_postcode=0,
        not_a_postcode=1,
        not_of_london=1,
        too_coarse=1,
    )


def test_a_practice_at_an_ended_postcode_is_placed_and_one_at_a_long_ended_one_is_not(
    tmp_path: Path,
):
    found = of(
        MadeUpPractice(AT_AN_ENDED_POSTCODE),
        MadeUpPractice(AT_A_LONG_ENDED_POSTCODE),
        folder=tmp_path,
    )
    assert (found.placing.placed, found.placing.at_an_ended_postcode) == (1, 1)
    assert found.placing.too_coarse == 1
    # The one that is placed stands in the middle of the fourth output area.
    assert found.distances.of_oa[spine.build(inputs_of(tmp_path / "again")).cells[3].oa] == 0.0


def test_with_no_practice_in_tallowgate_its_homes_have_no_distance_and_none_is_filled_in(
    tmp_path: Path,
):
    found = of(MadeUpPractice(NORTH_GATE.postcode), folder=tmp_path)
    assert found.worked[TALLOWGATE] == Worked(None, 0, 4, 0.0, State.SOURCE_GAP)
    assert len(found.distances.near_the_edge) == 4
    assert [row.value for row in found.rows] == [100.0, 300.0, None]


def test_no_row_of_northern_ireland_reaches_a_figure(tmp_path: Path, town: Walk):
    """Each of the two is written in the directory as a row of London, at a point in the town.

    A reader that kept either would place a practice there, and a figure would move.
    """
    with_them = of(
        MadeUpPractice(NORTH_GATE.postcode),
        MadeUpPractice(QUAY.postcode),
        *(MadeUpPractice(row.postcode) for row in OF_NORTHERN_IRELAND),
        folder=tmp_path,
    )
    assert with_them.worked == town.worked
    assert [row.value for row in with_them.rows] == [row.value for row in town.rows]
    assert (with_them.placing.listed, with_them.placing.placed) == (4, 2)
    assert with_them.placing.not_of_london == 2
    alone = of(
        *(MadeUpPractice(row.postcode) for row in OF_NORTHERN_IRELAND), folder=tmp_path / "alone"
    )
    assert alone.distances.of_oa == {}
    assert [row.value for row in alone.rows] == [None, None, None]


def test_an_output_area_with_no_centre_has_no_distance(tmp_path: Path):
    first = spine.build(inputs_of(tmp_path / "first")).cells[0].oa
    inputs = inputs_of(tmp_path / "second", centres=centres_with_the_district(left_out=[first]))
    found = built(inputs)
    assert first not in found.distances.of_oa
    # The first output area holds 110 of the area's 500 homes.
    assert found.worked[QUILLHAVEN_1] == Worked(100.0, 3, 4, round(390 / 500, 6), State.PARTIAL)


# What is never read


def test_the_columns_that_may_name_a_person_are_never_read():
    assert gp_walk.READ == {"postcode": 10, "closed": 12, "status": 13, "setting": 26}
    assert gp_walk.NEVER_READ == {"name": (2,), "address": (5, 6, 7, 8, 9), "telephone": (18,)}
    never = {place for places in gp_walk.NEVER_READ.values() for place in places}
    assert not never & set(gp_walk.READ.values())
    assert max(gp_walk.READ.values()) <= gp_walk.WIDTH == 27


def test_nothing_of_a_column_that_is_not_read_is_kept(town: Walk):
    assert CANARY in report().decode()
    kept = repr(dataclasses.asdict(town.report)) + repr(town.rows) + repr(town.metric)
    assert CANARY not in kept
    assert CANARY not in repr(town.placing) + repr(town.distances)


def test_a_report_with_nothing_in_the_columns_that_are_not_read_reads_the_same(
    tmp_path: Path, town: Walk
):
    emptied = report().decode().replace(CANARY, "").encode()
    found = built(inputs_of(tmp_path, practices=emptied))
    assert found.worked == town.worked
    assert found.report.postcodes == town.report.postcodes


def test_what_is_printed_of_the_report_holds_no_postcode(town: Walk):
    said = repr(town.report) + repr(town.placing) + repr(town.rows) + repr(town.metric)
    for practice in PRACTICES:
        assert practice.postcode not in said
    assert repr(town.report) == "Report(rows=11, counted=5)"


# A file that is not as the step expects


@pytest.mark.parametrize("width", [26, 28])
def test_a_line_of_another_width_stops_the_step(tmp_path: Path, width: int):
    said = refusal(tmp_path, report(width=width))
    assert "a line has not the columns of the report" in said


def test_a_report_with_a_row_of_names_stops_the_step(tmp_path: Path):
    names = ",".join(f'"Column {number}"' for number in range(1, 28)).encode() + b"\r\n"
    assert "a status is not one the specification names" in refusal(tmp_path, names + report())


@pytest.mark.parametrize(
    ("practice", "words"),
    [
        (MadeUpPractice("QH1 1CK", status="A"), "a status is not one the specification names"),
        (MadeUpPractice("QH1 1CK", status="INACTIVE"), "a status is not one the specification"),
        (MadeUpPractice("QH1 1CK", status=""), "a status is not one the specification names"),
        (MadeUpPractice("QH1 1CK", closed="31/03/2019"), "a close date is no day"),
        (MadeUpPractice("QH1 1CK", closed="2019"), "a close date is no day"),
        (MadeUpPractice("QH1 1CK", setting="4"), "a prescribing setting is not written as"),
        (MadeUpPractice("QH1 1CK", setting="GP PRACTICE"), "a prescribing setting is not"),
    ],
)
def test_a_row_that_is_not_written_as_the_specification_says_stops_the_step(
    tmp_path: Path, practice: MadeUpPractice, words: str
):
    said = refusal(tmp_path, report([practice]))
    assert words in said
    assert practice.postcode not in said and CANARY not in said


def test_a_report_with_no_row_stops_the_step(tmp_path: Path):
    # The mark at the start of a file, and nothing after it.
    assert "it holds no row" in refusal(tmp_path, b"\xef\xbb\xbf")


def test_a_report_that_is_not_utf8_stops_the_step(tmp_path: Path):
    assert "it could not be read as text" in refusal(tmp_path, report() + b"\xff\xfe\r\n")


# The evidence


def test_every_area_has_a_row_that_holds_its_figure(town: Walk):
    assert [row.fact_id for row in town.rows] == [f"{area}/feature/gp_walk" for area in AREAS]
    assert [row.value for row in town.rows] == [100.0, 200.0, 100.0]
    for row in town.rows:
        assert row.derivation_id == "straight_line_to_nearest_by_postcode@1"
        assert row.retrieved_on == "2026-09-24"
        assert row.data_period is not None
        assert row.data_period.days() == ("2021-03-21", "2026-09-24")


def test_a_row_rests_on_the_report_the_directory_the_centres_the_lookup_and_the_homes(
    town: Walk,
):
    by_source = {receipt.source_id: receipt.file_id for receipt in town.files}
    assert set(by_source) == {
        gp_walk.SOURCE,
        postcodes.SOURCE,
        centres.CENTRES,
        spine.LOOKUP,
        spine.HOMES,
    }
    for row in town.rows:
        assert set(row.inputs) == set(by_source.values())


def test_the_evidence_of_the_measure_has_no_loose_end(town: Walk):
    evidence = Evidence.of("lon-2026-10-02-01", town.files, gp_walk.METHODS, town.rows)
    assert len(evidence.rows) == 3
    assert town.geography is Geography.POSTCODE
    assert gp_walk.METHODS == (nearest_by_postcode.METHOD,)


# The gate and the store


@pytest.mark.parametrize("source", [gp_walk.SOURCE, postcodes.SOURCE, centres.CENTRES])
def test_the_gate_is_asked_about_every_file_before_it_is_read(tmp_path: Path, source: str):
    sources = [
        one.model_copy(update={"uses": (Use.DISPLAY,)}) if one.id == source else one
        for one in registry()
    ]
    inputs = inputs_of(tmp_path, given=Registry(tuple(sources)))
    found = spine.build(inputs)
    with pytest.raises(LockError) as stopped:
        gp_walk.build(inputs, found)
    assert stopped.value.rule == "gate_refuses"
    assert source not in {one.receipt.source_id for one in inputs.opened}


def test_the_report_of_trusts_and_hospitals_is_never_read_in_its_place(tmp_path: Path):
    """The entry for hospital sites allows destination search alone, and is another entry."""
    assert Use.SCORING not in registry().get("nhs-ods").uses
    assert registry().get(gp_walk.SOURCE).uses == (Use.SCORING,)
    assert gp_walk.is_the_report("epraccur.csv")
    for name in (
        "ets.csv",
        "etr.csv",
        "egpcur.csv",
        "epracmem.csv",
        "ebranchs.csv",
        "EPRACCUR.CSV",
    ):
        assert not gp_walk.is_the_report(name)


def test_every_file_behind_a_figure_is_registered_for_scoring(town: Walk):
    assert town.metric.source_ids == (
        "nhs-ods-gp-practices",
        "ons-census-2021-housing-tables",
        "ons-oa-pwc-2021",
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
        "ons-postcode-directory",
    )
    for source_id in town.metric.source_ids:
        assert Use.SCORING in registry().get(source_id).uses


def test_the_three_credits_of_the_directory_stand_with_the_figure(town: Walk):
    assert gp_walk.credits_of(town) == (
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
    """Core's words are held here, so that this fails on the day core names a walk again.

    The measure is on the list of no build yet: `WAITS_ON` says what would bring it in.
    """
    metric, core = town.metric, FEATURES[FeatureId.GP_WALK]
    assert metric.label == (
        "Straight-line distance to the nearest GP practice, placed by its postcode"
    )
    assert "walk" not in metric.label.lower()
    assert (core.label, core.unit) == (metric.label, "m")
    assert core.native_resolution is NativeResolution.POINT
    assert NEVER_A_TRADE_OFF[FeatureId.GP_WALK] == 800
    assert (metric.unit, metric.polarity) == ("m", Polarity.LESS)
    assert metric.native_resolution is NativeResolution.POINT
    assert says_what_core_says(metric)
    assert not says_what_core_says(metric.model_copy(update={"unit": "min"}))
    assert metric.vintage == "2026-09-24"
    # Everything else that core decides of the feature is as core has it.
    for name in ("short_label", "dimension", "polarity", "kind", "describes", "family"):
        assert getattr(metric, name) == getattr(core, name)


def test_the_measure_says_what_it_waits_on_and_none_of_it_is_cores():
    assert len(gp_walk.WAITS_ON) == 3
    assert not any("Core names" in said for said in gp_walk.WAITS_ON)


def test_the_measure_is_called_as_the_list_of_the_measures_of_a_build_calls_each(
    tmp_path: Path, town: Walk
):
    """It is not on the list yet. This is the line that puts it there."""
    assert gp_walk.FEATURE not in {measure.feature for measure in measures.MEASURES}
    measure = measures.Measure(
        gp_walk.FEATURE,
        gp_walk.SOURCE,
        gp_walk.is_the_report,
        gp_walk.METHODS,
        gp_walk.CANNOT_SEE,
        lambda inputs, ground: gp_walk.build(inputs, ground.spine),
        waits_on=gp_walk.WAITS_ON,
    )
    inputs = inputs_of(tmp_path)
    found = spine.build(inputs)
    made = measure.build(inputs, measures.Ground(found, land.build(inputs, found)))
    assert made.worked == town.worked
    assert (made.rows, made.metric, made.geography) == (town.rows, town.metric, town.geography)
    assert [receipt.source_id for receipt in made.files if measure.reads(receipt.publisher_file)]
    assert not measure.in_squares


def test_the_definition_is_one_sentence_that_says_it_is_a_straight_line(town: Walk):
    definition = town.metric.definition
    assert definition == gp_walk.definition_of("2026-09-24")
    assert definition.endswith(".") and not re.search(r"[.!?]\s|\n", definition)
    for words in (
        "in a straight line",
        "the report epraccur of NHS England",
        "lists as active, as at 2026-09-24",
        "ONS Postcode Directory",
        "median",
        "census of 2021",
        "nearest 100 metres",
        "not along any street",
        "the walk is longer",
        "a door of its postcode that may not be its own",
        "a branch surgery is not counted",
        "a practice outside London is not counted",
    ):
        assert words in definition


RESIDENT_WORDS = re.compile(
    r"\b(residents?|people|population|households?|famil(y|ies)|health|ages?|incomes?)\b", re.I
)


def test_no_sentence_of_the_measure_describes_who_lives_somewhere(town: Walk):
    sentences = (town.metric.definition, *gp_walk.CANNOT_SEE, gp_walk.METHOD.sentence)
    assert [sentence for sentence in sentences if RESIDENT_WORDS.search(sentence)] == []


def test_what_it_cannot_see_is_said_in_whole_sentences():
    assert len(gp_walk.CANNOT_SEE) == 6
    for sentence in gp_walk.CANNOT_SEE:
        assert sentence.endswith(".") and not re.search(r"[.!?]\s", sentence)
    assert "not a walk" in gp_walk.CANNOT_SEE[0]
    assert "a branch surgery that is nearer is not counted" in gp_walk.CANNOT_SEE[4]
    assert "Near is not able to register" in gp_walk.CANNOT_SEE[5]
    assert QUAY.postcode not in "".join(gp_walk.CANNOT_SEE)
