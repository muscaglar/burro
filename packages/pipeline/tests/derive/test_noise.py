"""Transport noise, from the publisher's workbook to a figure for each area.

Every file here is made up. The workbook is laid out as the publisher lays out
its own, with its own names for sheets and columns. What it holds is made up:
the six LSOAs of the made-up town of the tests of cells, and one outside
London, each with a share chosen so that a figure can be worked out by hand.

    area             LSOA        homes   share
    Quillhaven 001   E01999001     230   0.25
                     E01999002     270   0.75
    Quillhaven 002   E01999003     310   0.332
                     E01999004     350   0.001
    Tallowgate 001   E01999005     390   1.0
                     E01999006     430   0.0

    Quillhaven 001   (230 x 25 + 270 x 75) / 500      = 52.0
    Quillhaven 002   (310 x 33.2 + 350 x 0.1) / 660   = 15.6, from 15.647
    Tallowgate 001   (390 x 100 + 430 x 0) / 820      = 47.6, from 47.561
"""

from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest
from burro_core.catalogue import FEATURES
from burro_core.ids import FeatureId, NativeResolution, Polarity
from burro_pipeline.cells import spine
from burro_pipeline.derive import noise
from burro_pipeline.derive.measures import says_what_core_says
from burro_pipeline.derive.methods import LSOA_VALUE_BY_HOMES
from burro_pipeline.derive.noise import Noise
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind, Method
from burro_pipeline.evidence.receipt import Geography, Period
from burro_pipeline.evidence.row import Flag, State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.inputs import Opened
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import held, registry
from .noise_support import (
    CANARY,
    CANARY_NUMBER,
    LIVING,
    LIVING_COLUMNS,
    NEVER_OPENED,
    NOTES,
    OUTSIDE,
    SAID_OF_NOISE,
    SHARES,
    SOURCE,
    SUPPLIER_OF_NOISE,
    Cell,
    Raw,
    file_8,
    inputs_of,
    living,
    notes,
    receipt,
)

Q1, Q2, T1 = "lon-ne02999001", "lon-ne02999002", "lon-ne02999003"


def built(folder: Path, content: bytes | None = None, period: Period | None = None) -> Noise:
    """The measure, from a made-up build whose workbook is the one given."""
    inputs = inputs_of(folder, file_8() if content is None else content, period=period)
    return noise.build(inputs, spine.build(inputs))


def shares(**changed: Cell) -> dict[str, Cell]:
    """The shares of the made-up town, with those of some LSOAs changed."""
    return {**SHARES, **{f"E01999{number[1:]}": share for number, share in changed.items()}}


def refused(folder: Path, content: bytes, period: Period | None = None) -> LockError:
    """The refusal of a workbook that is not what the step was written to read."""
    inputs = inputs_of(folder, content, period=period)
    found = spine.build(inputs)
    with pytest.raises(LockError) as stopped:
        noise.build(inputs, found)
    assert stopped.value.rule == "input_is_as_described"
    assert stopped.value.subject == receipt(content).file_id
    # A refusal repeats nothing from the file.
    assert CANARY not in str(stopped.value) and str(CANARY_NUMBER) not in str(stopped.value)
    return stopped.value


def values(found: Noise) -> dict[str, float | None]:
    return {area: one.value for area, one in found.worked.items()}


# The parser


def test_the_share_of_every_lsoa_is_read_as_the_publisher_wrote_it(tmp_path: Path):
    sheet = built(tmp_path).sheet
    assert sheet.share == SHARES
    assert (sheet.rows, sheet.without, sheet.year) == (7, (), "2021")


def test_the_rows_are_keyed_by_the_lsoas_of_2021_as_the_column_says(tmp_path: Path):
    assert noise.LSOA_CODE == "LSOA code (2021)"
    assert built(tmp_path).geography is Geography.LSOA21


def test_the_order_of_the_rows_changes_nothing(tmp_path: Path):
    turned = dict(reversed(list(SHARES.items())))
    assert built(tmp_path / "turned", file_8(turned)).worked == built(tmp_path / "as").worked


@pytest.mark.parametrize(
    ("changed", "why"),
    [
        ({"n001": 1.001}, "a share is not a share"),
        ({"n001": -0.001}, "a share is not a share"),
        ({"n001": 25}, "a share is not a share"),
        ({"n001": CANARY}, "a share is not a share"),
        ({"n001": "0.25"}, "a share is not a share"),
        ({"n001": Raw("n", "<v>1e400</v>")}, "neither text nor a number"),
    ],
)
def test_a_share_that_is_not_a_number_from_0_to_1_stops_the_step(
    tmp_path: Path, changed: Mapping[str, Cell], why: str
):
    assert why in str(refused(tmp_path, file_8(shares(**changed))))


@pytest.mark.parametrize("code", ["E02999001", "e01999001", "E0199900", "E019990011", CANARY])
def test_a_code_that_is_no_code_of_an_lsoa_stops_the_step(tmp_path: Path, code: str):
    assert "a code is not a code" in str(refused(tmp_path, file_8({**SHARES, code: 0.5})))


def test_a_row_with_a_share_and_no_code_stops_the_step(tmp_path: Path):
    no_code: list[Cell] = [None if name == noise.LSOA_CODE else 0.5 for name in LIVING_COLUMNS]
    table = [*living(), no_code]
    assert "a code is not a code" in str(refused(tmp_path, file_8(sheets={LIVING: table})))


def test_an_lsoa_that_is_there_twice_stops_the_step(tmp_path: Path):
    table = [*living(), living()[1]]
    assert "an LSOA is there twice" in str(refused(tmp_path, file_8(sheets={LIVING: table})))


@pytest.mark.parametrize("missing", [noise.LSOA_CODE, noise.NOISE])
def test_a_workbook_without_a_column_that_is_read_stops_the_step_and_names_it(
    tmp_path: Path, missing: str
):
    columns = tuple(name for name in LIVING_COLUMNS if name != missing)
    stopped = refused(tmp_path, file_8(columns=columns))
    assert f"the column {missing} is missing" in str(stopped)


def test_a_workbook_whose_codes_are_of_another_census_stops_the_step(tmp_path: Path):
    """The column is named for the census its codes follow. Codes of 2011 are another column."""
    header, *rows = living()
    of_2011 = [["LSOA code (2011)" if name == noise.LSOA_CODE else name for name in header], *rows]
    stopped = refused(tmp_path, file_8(sheets={LIVING: of_2011}))
    assert f"the column {noise.LSOA_CODE} is missing" in str(stopped)


def test_the_step_names_every_sheet_and_column_it_reads_and_they_are_about_no_resident(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Two sheets are asked for: the notes, and the one sheet of figures, for two columns."""
    asked: list[tuple[str, tuple[str, ...]]] = []
    read_sheet = noise.read_sheet

    def watched(opened: Opened, sheet: str, columns: Sequence[str], *, header_at: int = 1):
        asked.append((sheet, tuple(columns)))
        return read_sheet(opened, sheet, columns, header_at=header_at)

    monkeypatch.setattr(noise, "read_sheet", watched)
    built(tmp_path)
    assert asked == [
        (NOTES, ("Indicator", "Data supplier", "Data time point", "Comments")),
        (LIVING, ("LSOA code (2021)", "Noise pollution")),
    ]
    assert not {sheet for sheet, _ in asked} & set(NEVER_OPENED)


def test_a_sheet_with_no_row_under_its_header_stops_the_step(tmp_path: Path):
    assert "no row of an LSOA" in str(refused(tmp_path, file_8({})))


def test_a_sheet_of_somewhere_else_stops_the_step(tmp_path: Path):
    """No LSOA of the spine is in it: it is of another place, or of another census."""
    assert "no row of London" in str(refused(tmp_path, file_8({OUTSIDE: 0.5})))


# The period and the level, read from the notes


def test_the_year_is_read_from_the_notes_of_the_file(tmp_path: Path):
    assert built(tmp_path).sheet.year == "2021"
    later = file_8(noted=notes(year="2022"))
    assert built(tmp_path / "later", later, period=Period(as_at="2022")).sheet.year == "2022"


def test_a_year_kept_as_a_number_is_read_as_the_year(tmp_path: Path):
    assert built(tmp_path, file_8(noted=notes(year=2021))).sheet.year == "2021"


def test_a_receipt_that_states_another_year_than_the_notes_stops_the_step(tmp_path: Path):
    stopped = refused(tmp_path, file_8(noted=notes(year="2022")))
    assert "its receipt gives another period than its notes" in str(stopped)
    stopped = refused(tmp_path / "day", file_8(), period=Period(as_at="2021-03-21"))
    assert "its receipt gives another period than its notes" in str(stopped)


@pytest.mark.parametrize("year", ["2019 to 2023", "March 2021", "21", 2021.5, None, CANARY])
def test_notes_that_give_no_year_stop_the_step(tmp_path: Path, year: Cell):
    assert "its notes give no year" in str(refused(tmp_path, file_8(noted=notes(year=year))))


def test_notes_with_no_row_for_the_indicator_stop_the_step(tmp_path: Path):
    other = file_8(noted=notes(indicator="Noise"))
    assert "do not hold one row for the indicator" in str(refused(tmp_path, other))


def test_notes_with_two_rows_for_the_indicator_stop_the_step(tmp_path: Path):
    twice = file_8(noted=[*notes(), notes()[3]])
    assert "do not hold one row for the indicator" in str(refused(tmp_path, twice))


@pytest.mark.parametrize("said", ["Exposed to 60 dB or more.", "Exposed to 155dB.", None, CANARY])
def test_notes_that_do_not_give_the_level_stop_the_step(tmp_path: Path, said: Cell):
    """The measure is named for 55 dB. A file whose indicator has another level is not it."""
    stopped = refused(tmp_path, file_8(noted=notes(said=said)))
    assert "do not give the level the measure is named for" in str(stopped)


@pytest.mark.parametrize("level", ["55dB Lden", "55 dB Lden", "55 dB(A) Lden"])
def test_the_level_is_found_however_the_notes_space_it(tmp_path: Path, level: str):
    said = (
        f"Made up for a test. The residents exposed to combined transport noise above {level}. "
        "Shrinkage was applied to this indicator."
    )
    assert built(tmp_path, file_8(noted=notes(said=said))).sheet.year == "2021"


@pytest.mark.parametrize(
    ("said", "supplier", "why"),
    [
        (
            SAID_OF_NOISE.replace("population", "homes").replace("residents", "homes"),
            SUPPLIER_OF_NOISE,
            "do not say it counts residents",
        ),
        (
            SAID_OF_NOISE.replace("transport noise", "road noise"),
            SUPPLIER_OF_NOISE,
            "do not say it is transport noise",
        ),
        (
            SAID_OF_NOISE.replace("Lden", "Lnight"),
            SUPPLIER_OF_NOISE,
            "do not name the measure of the level",
        ),
        (
            SAID_OF_NOISE.replace("Shrinkage was applied", "No shrinkage was needed"),
            SUPPLIER_OF_NOISE,
            "do not say shrinkage was applied",
        ),
        (
            SAID_OF_NOISE.replace("exposed to", "living with"),
            SUPPLIER_OF_NOISE,
            "do not say it counts who is exposed",
        ),
        (SAID_OF_NOISE, "A made-up consultancy", "do not name the supplier the measure names"),
        (SAID_OF_NOISE, None, "do not name the supplier the measure names"),
        (SAID_OF_NOISE, CANARY, "do not name the supplier the measure names"),
    ],
)
def test_notes_that_no_longer_say_what_the_measure_claims_stop_the_step(
    tmp_path: Path, said: str, supplier: Cell, why: str
):
    """The label and the sentence say only what the notes say. A file that says less is not it."""
    changed = file_8(noted=notes(said=said, supplier=supplier))
    assert why in str(refused(tmp_path, changed))


def test_the_made_up_notes_say_everything_the_measure_claims():
    """So that each refusal above is for the one thing that was changed."""
    said = {noise.COMMENTS: SAID_OF_NOISE, noise.SUPPLIER: SUPPLIER_OF_NOISE}
    for column, words, _ in noise.CLAIMED:
        assert words.search(said[column])


# The figure


def test_an_areas_figure_is_the_mean_of_the_shares_of_its_lsoas_by_homes(tmp_path: Path):
    found = built(tmp_path)
    assert values(found) == {Q1: 52.0, Q2: 15.6, T1: 47.6}
    for one in found.worked.values():
        assert (one.units_used, one.units_expected, one.weight_covered) == (2, 2, 1.0)
        assert one.state is State.PRESENT


def test_the_file_gives_a_share_and_the_figure_is_a_percentage(tmp_path: Path):
    found = built(tmp_path, file_8(shares(n001=1.0, n002=1.0, n003=0.0, n004=0.0)))
    assert (values(found)[Q1], values(found)[Q2]) == (100.0, 0.0)
    assert noise.metric_of(found.files, "2021").unit == "%"


def test_a_share_of_nought_is_a_share(tmp_path: Path):
    """The last LSOA of the town has a share of nought. It counts, with all its homes."""
    found = built(tmp_path).worked[T1]
    assert (found.value, found.weight_covered, found.state) == (47.6, 1.0, State.PRESENT)


@pytest.mark.parametrize("without", [{"n001": None}, {"n001": Raw("n", "<v></v>")}])
def test_an_lsoa_with_no_share_adds_nothing_and_is_never_nought(
    tmp_path: Path, without: Mapping[str, Cell]
):
    """Were it read as nought the figure would be 40.5. It is the share of the other LSOA."""
    found = built(tmp_path, file_8(shares(**without)))
    one = found.worked[Q1]
    assert (one.value, one.state) == (75.0, State.PARTIAL)
    assert (one.units_used, one.units_expected, one.weight_covered) == (1, 2, 0.54)
    assert found.sheet.without == ("E01999001",)
    assert values(found)[Q2] == 15.6


def test_an_lsoa_with_no_row_is_as_one_with_no_share(tmp_path: Path):
    fewer = {code: share for code, share in SHARES.items() if code != "E01999001"}
    found = built(tmp_path, file_8(fewer))
    assert (found.worked[Q1].value, found.worked[Q1].state) == (75.0, State.PARTIAL)
    assert found.sheet.without == ()


def test_below_half_the_homes_no_figure_is_given(tmp_path: Path):
    one = built(tmp_path, file_8(shares(n002=None))).worked[Q1]
    assert (one.value, one.state) == (None, State.BELOW_THRESHOLD)
    assert (one.units_used, one.units_expected, one.weight_covered) == (1, 2, 0.46)


def test_an_area_with_no_share_at_all_is_a_gap_in_the_source(tmp_path: Path):
    found = built(tmp_path, file_8(shares(n001=None, n002=None)))
    one = found.worked[Q1]
    assert (one.value, one.state, one.weight_covered) == (None, State.SOURCE_GAP, 0.0)
    assert values(found) == {Q1: None, Q2: 15.6, T1: 47.6}


def test_an_lsoa_outside_london_is_part_of_no_figure(tmp_path: Path):
    louder = built(tmp_path / "louder", file_8(shares(n901=1.0)))
    assert louder.worked == built(tmp_path / "as").worked
    assert set(louder.worked) == {Q1, Q2, T1}


def test_a_figure_is_given_to_one_decimal_place(tmp_path: Path):
    found = built(tmp_path, file_8(shares(n001=0.333, n002=0.333)))
    assert values(found)[Q1] == 33.3


def test_a_figure_is_marked_as_rounded_only_when_every_share_is(tmp_path: Path):
    assert built(tmp_path / "as").worked[Q1].flags == (Flag.ROUNDED_IN_SOURCE,)
    finer = built(tmp_path / "finer", file_8(shares(n005=0.12345)))
    assert finer.worked[Q1].flags == ()


# The evidence


def test_every_area_has_a_row_of_evidence_that_names_the_three_files(tmp_path: Path):
    found = built(tmp_path)
    assert [row.fact_id for row in found.rows] == [
        f"{area}/feature/noise_exposure" for area in (Q1, Q2, T1)
    ]
    assert {one.source_id for one in found.files} == {
        SOURCE,
        "ons-census-2021-housing-tables",
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
    }
    for row in found.rows:
        assert row.inputs == tuple(sorted(one.file_id for one in found.files))
        assert row.derivation_id == "lsoa_value_by_homes@1"
        assert (row.units_used, row.units_expected, row.weight_covered) == (2, 2, 1.0)
        assert (row.state, row.flags) == (State.PRESENT, (Flag.ROUNDED_IN_SOURCE,))
        # The span of the three files: the year of the indicator, and the month of the lookup.
        assert row.data_period == Period(start="2021-01-01", end="2021-12-31")
        assert row.retrieved_on == "2026-09-23"


def test_a_figure_that_is_missing_has_a_row_too_and_the_row_says_why(tmp_path: Path):
    found = built(tmp_path, file_8(shares(n001=None, n002=None, n004=None)))
    rows = {row.area_id: row for row in found.rows}
    assert (rows[Q1].state, rows[Q1].units_used, rows[Q1].weight_covered) == (
        State.SOURCE_GAP,
        0,
        0.0,
    )
    assert (rows[Q2].state, rows[Q2].units_used) == (State.BELOW_THRESHOLD, 1)
    assert all(row.inputs for row in rows.values())


def test_the_rows_stand_as_the_evidence_of_a_release(tmp_path: Path):
    found = built(tmp_path, file_8(shares(n001=None, n002=None)))
    evidence = Evidence.of("lon-2026-10-02-01", found.files, noise.METHODS, found.rows)
    row = evidence.row(f"{T1}/feature/noise_exposure")
    assert row is not None
    assert evidence.sources_of(row) == frozenset(found.metric.source_ids)
    assert evidence.method(row.derivation_id or "") == LSOA_VALUE_BY_HOMES
    assert LSOA_VALUE_BY_HOMES.kind is Kind.AVERAGED


# The name and the unit


def test_the_label_says_residents_and_no_homes_and_so_does_the_sentence(tmp_path: Path):
    """The file counts residents, and gives no count of homes.

    So the name says whose share it is, and never says homes. Core lets this one name
    say residents, and no other. The sentence of the measure says residents in full.
    """
    metric = built(tmp_path).metric
    assert metric.label == "Share of residents exposed to 55 dB or more of transport noise"
    assert "homes" not in metric.label.lower()
    assert "residents exposed to combined transport noise" in metric.definition
    assert "not a share of homes" in metric.definition


def test_the_row_names_and_makes_the_measure_as_core_does_so_a_build_carries_it(tmp_path: Path):
    metric, feature = built(tmp_path).metric, FEATURES[FeatureId.NOISE_EXPOSURE]
    assert (metric.label, metric.method) == (feature.label, feature.method)
    assert metric.method.value == "averaged"
    assert says_what_core_says(metric)


def test_core_decides_the_unit_and_which_way_is_more(tmp_path: Path):
    metric, feature = built(tmp_path).metric, FEATURES[FeatureId.NOISE_EXPOSURE]
    assert (metric.feature_id, metric.dimension) == (feature.feature_id, feature.dimension)
    assert (metric.unit, metric.polarity) == ("%", Polarity.LESS)
    assert (metric.unit, metric.polarity) == (feature.unit, feature.polarity)
    assert metric.native_resolution is NativeResolution.LSOA
    assert (feature.higher, feature.lower) == ("noisier", "quieter")


def test_the_row_of_the_catalogue_names_every_source_and_the_year(tmp_path: Path):
    metric = built(tmp_path).metric
    assert metric.source_ids == (
        "mhclg-iod-2025-underlying-indicators",
        "ons-census-2021-housing-tables",
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
    )
    assert (metric.vintage, metric.rankable) == ("2021", True)


def test_the_definition_is_one_sentence_that_states_every_number_it_rests_on(tmp_path: Path):
    """The record of a method refuses a sentence that leaves a parameter out."""
    definition = built(tmp_path).metric.definition
    stated = Method(
        derivation_id="noise_exposure@1",
        sentence=definition,
        kind=Kind.AVERAGED,
        parameters={
            "decibels": noise.DECIBELS,
            "year": 2021,
            "decimal_places": noise.DECIMAL_PLACES,
            "times": noise.TIMES,
            "edition": 2025,
            "decimals": noise.DECIMALS,
        },
        code="burro_pipeline.derive.noise",
    )
    assert stated.sentence == definition
    for said in ("residents", "Defra", "Indices of Deprivation", "shrinkage", "modelled"):
        assert said in definition
    assert "not a share of homes" in definition
    assert "with a half taken upward" in definition


def test_the_definition_says_it_is_a_measure_of_a_place_and_of_nobody(tmp_path: Path):
    """It may be ranked on because it says how loud a place is, and nothing of who lives there."""
    definition = built(tmp_path).metric.definition
    assert "how much of where an area's people live is loud" in definition
    assert "nothing of who they are" in definition


def test_the_definition_names_no_kind_of_transport_because_the_file_names_none(tmp_path: Path):
    said = " ".join([built(tmp_path).metric.definition, noise.LABEL, *noise.CANNOT_SEE]).lower()
    for kind in ("road", "rail", "aircraft", "airport", "flight"):
        assert kind not in said


def test_what_it_cannot_see_is_said_in_two_plain_sentences():
    assert len(noise.CANNOT_SEE) == 2
    for said in noise.CANNOT_SEE:
        assert said.endswith(".") and "!" not in said and len(said) < 250
        # Each is one sentence.
        assert said.count(". ") == 0
    together = " ".join(noise.CANNOT_SEE)
    for word in ("modelled", "2021", "street", "55 dB", "which kinds", "neighbours"):
        assert word in together


# The gate, the receipt and the store


def without_scoring() -> Registry:
    """The repository's registry, with the workbook no longer registered for scoring."""
    sources = [
        source.model_copy(update={"uses": (Use.DISPLAY,)}) if source.id == SOURCE else source
        for source in registry()
    ]
    return Registry(tuple(sources))


def test_the_gate_is_asked_before_the_workbook_is_read(tmp_path: Path):
    inputs = inputs_of(tmp_path, file_8(), using=without_scoring())
    found = spine.build(inputs)
    before = inputs.opened
    with pytest.raises(LockError) as stopped:
        noise.build(inputs, found)
    assert (stopped.value.rule, stopped.value.subject) == ("gate_refuses", SOURCE)
    assert inputs.opened == before
    assert not any((tmp_path / "work").rglob("*.xlsx"))


def test_a_workbook_with_no_receipt_is_not_read(tmp_path: Path):
    """The file is in the store, as one is whose period the list did not state. It is not read."""
    inputs = inputs_of(tmp_path, None)
    found = spine.build(inputs)
    with pytest.raises(LockError) as stopped:
        noise.build(inputs, found)
    assert (stopped.value.rule, stopped.value.subject) == ("input_has_one_receipt", SOURCE)
    assert not any((tmp_path / "work").rglob("*.xlsx"))


def test_another_file_of_the_publisher_is_not_taken_for_the_workbook(tmp_path: Path):
    inputs = inputs_of(tmp_path, file_8(), name="File_7_IoD2025_All_Ranks_Scores.xlsx")
    found = spine.build(inputs)
    with pytest.raises(LockError) as stopped:
        noise.build(inputs, found)
    assert stopped.value.rule == "input_has_one_receipt"


def test_a_spine_of_another_build_is_refused(tmp_path: Path):
    """A row names the files of the spine, so they must be files this build opened."""
    found = spine.build(inputs_of(tmp_path / "other", file_8()))
    with pytest.raises(LockError) as stopped:
        noise.build(inputs_of(tmp_path / "this", file_8()), found)
    assert stopped.value.rule == "input_has_one_receipt"
    assert stopped.value.subject in found.inputs


def test_nothing_is_written_to_the_store(tmp_path: Path):
    inputs = inputs_of(tmp_path, file_8())
    before = held(tmp_path / "store")
    noise.build(inputs, spine.build(inputs))
    assert held(tmp_path / "store") == before
