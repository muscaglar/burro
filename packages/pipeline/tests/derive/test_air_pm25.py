"""Fine particles, from the publisher's grid to a figure for each area.

Every file here is made up. The grid is laid out as the publisher lays out its
own: four rows of notes, of which the first is `pm2.5`, an empty row, the
header `gridcode,x,y,pm252024g`, plain ASCII, and lines that end CR LF. What it
holds is made up. The squares, the town and its centres are those of the tests
of nitrogen dioxide, with other values. The square far to the west has no
value, as in the real file.

             x: 700500   701500
    y: 401500     9.25   MISSING
    y: 400500      8.0      8.5

The parser and the reading at homes are those of nitrogen dioxide, and its
tests hold them. These hold what differs: what the file calls itself, the name
of its column, the file it is told from, and what is said of the measure.
"""

import re
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest
from burro_core.catalogue import FEATURES
from burro_core.ids import Dimension, FeatureId, NativeResolution, Polarity
from burro_pipeline.cells import centres, spine
from burro_pipeline.derive import air_no2, air_pm25, measures
from burro_pipeline.derive.air_pm25 import Air
from burro_pipeline.derive.methods import GRID_AT_HOMES, Worked
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind
from burro_pipeline.evidence.receipt import Geography
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import held, registry
from . import test_air_no2 as no2
from .test_air_no2 import CANARY, FAR_WEST, OFF_THE_GRID, PLACED, A, B, C, D, Middle, on

GRID_NAME = "mappm252024g.csv"
NOTES = ("pm2.5", "2024", "annual mean", "ug m-3")
HEADER = ("gridcode", "x", "y", "pm252024g")
SQUARES = (
    ("900001", *A, "8.0"),
    ("900002", *B, "8.5"),
    ("900003", *C, "9.25"),
    ("900004", *D, "MISSING"),
    ("900005", *FAR_WEST, "MISSING"),
)
QUILLHAVEN_1, QUILLHAVEN_2, TALLOWGATE = no2.QUILLHAVEN_1, no2.QUILLHAVEN_2, no2.TALLOWGATE


def grid_csv(
    squares: Sequence[Sequence[object]] = SQUARES,
    notes: Sequence[str] = NOTES,
    header: Sequence[str] = HEADER,
) -> bytes:
    """A grid of fine particles as the publisher writes one. What it holds is made up."""
    return no2.grid_csv(squares, notes, header)


def inputs_of(
    folder: Path,
    grid: bytes | None = None,
    placed: Mapping[str, Middle] = PLACED,
    *,
    name: str = GRID_NAME,
    year: str = "2024",
    given: Registry | None = None,
) -> Inputs:
    """The made-up files of a build. The grid of nitrogen dioxide is among them, as in the store."""
    grid = grid_csv() if grid is None else grid
    more = [(no2.grid_receipt(grid, name=name, year=year), grid)]
    return no2.inputs_of(folder, placed=placed, more=more, given=given)


def built(folder: Path, grid: bytes | None = None, placed: Mapping[str, Middle] = PLACED) -> Air:
    inputs = inputs_of(folder, grid, placed)
    return air_pm25.build(inputs, spine.build(inputs))


def refused(folder: Path, grid: bytes) -> LockError:
    """The refusal of a grid, which names a rule and repeats nothing the file holds."""
    inputs = inputs_of(folder, grid)
    with pytest.raises(LockError) as stopped:
        air_pm25.build(inputs, spine.build(inputs))
    assert stopped.value.rule == "input_is_as_described"
    assert CANARY not in str(stopped.value)
    assert str(folder) not in str(stopped.value)
    return stopped.value


def value_of(worked: Worked) -> float:
    assert worked.value is not None
    return worked.value


# The parser


def test_the_grid_is_read_from_under_its_notes_by_the_column_the_file_really_has(tmp_path: Path):
    grid = built(tmp_path).grid
    assert (grid.year, grid.rows, grid.without_a_value) == (2024, 5, 2)
    assert grid.values == {
        (700_000, 400_000): 8.0,
        (701_000, 400_000): 8.5,
        (700_000, 401_000): 9.25,
    }


def test_a_square_the_publisher_gives_no_value_for_is_counted_and_never_nought(tmp_path: Path):
    grid = built(tmp_path).grid
    assert (701_000, 401_000) not in grid.values and (-1_000, 5_000) not in grid.values
    assert grid.without_a_value == 2
    assert 0 not in grid.values.values()


@pytest.mark.parametrize("missing", HEADER)
def test_a_grid_without_a_column_is_refused_and_the_column_is_named(tmp_path: Path, missing: str):
    header = [CANARY if name == missing else name for name in HEADER]
    stopped = refused(tmp_path, grid_csv(header=header))
    assert f"the column {missing} is missing" in str(stopped)


@pytest.mark.parametrize("written", ["pm252024", "pm2.52024g", "pm2.52024", "pm102024g"])
def test_the_column_of_values_is_named_as_the_file_names_it_and_no_other_way(
    tmp_path: Path, written: str
):
    """The note has a point and the column has none, and the column ends in a letter."""
    stopped = refused(tmp_path, grid_csv(header=(*HEADER[:3], written)))
    assert "the column pm252024g is missing" in str(stopped)


@pytest.mark.parametrize("note", ["no2", "pm25", "pm10", "PM2.5", CANARY])
def test_a_grid_that_is_not_of_fine_particles_is_refused(tmp_path: Path, note: str):
    stopped = refused(tmp_path, grid_csv(notes=(note, *NOTES[1:])))
    assert "it is not a map of fine particles (PM2.5)" in str(stopped)


@pytest.mark.parametrize(
    ("notes", "words"),
    [
        (("pm2.5", CANARY, "annual mean", "ug m-3"), "the year it states is no year"),
        (("pm2.5", "2024", "daily mean", "ug m-3"), "not an annual mean"),
        (("pm2.5", "2024", "annual mean", "ng m-3"), "not in micrograms a cubic metre"),
    ],
)
def test_a_grid_whose_notes_say_something_else_is_refused(
    tmp_path: Path, notes: tuple[str, ...], words: str
):
    assert words in str(refused(tmp_path, grid_csv(notes=notes)))


def test_a_grid_of_another_year_than_its_receipt_says_is_refused(tmp_path: Path):
    grid = grid_csv(notes=("pm2.5", "2023", *NOTES[2:]), header=(*HEADER[:3], "pm252023g"))
    assert "not the year of its receipt" in str(refused(tmp_path, grid))


# The gate, the receipt and the store


def test_the_gate_is_asked_before_the_grid_is_read(tmp_path: Path):
    inputs = inputs_of(tmp_path, given=no2.without_scoring())
    found = spine.build(inputs)
    before = inputs.opened
    with pytest.raises(LockError) as stopped:
        air_pm25.build(inputs, found)
    assert stopped.value.rule == "gate_refuses"
    assert inputs.opened == before


def test_the_grid_is_told_from_the_nitrogen_dioxide_of_its_source(tmp_path: Path):
    """The store holds a file of each. Each measure opens its own and not the other."""
    inputs = inputs_of(tmp_path)
    found = spine.build(inputs)
    fine = air_pm25.build(inputs, found)
    opened = [one.receipt for one in inputs.opened if one.receipt.source_id == air_pm25.SOURCE]
    assert [one.publisher_file for one in opened] == [GRID_NAME]
    assert fine.grid.file_id == no2.grid_receipt(grid_csv(), name=GRID_NAME).file_id
    assert air_no2.build(inputs, found).grid.file_id != fine.grid.file_id
    assert not air_pm25.is_the_grid(no2.GRID_NAME) and not air_no2.is_the_grid(GRID_NAME)
    assert not air_pm25.is_the_grid("mappm102024g.csv")


def test_a_file_with_no_receipt_is_not_read(tmp_path: Path):
    inputs = no2.inputs_of(tmp_path)
    with pytest.raises(LockError) as stopped:
        air_pm25.build(inputs, spine.build(inputs))
    assert stopped.value.rule == "input_has_one_receipt"


def test_nothing_is_written_to_the_store(tmp_path: Path):
    inputs = inputs_of(tmp_path)
    before = held(tmp_path / "store")
    air_pm25.build(inputs, spine.build(inputs))
    assert held(tmp_path / "store") == before


# The figure


def test_an_area_is_given_the_mean_of_the_squares_its_homes_stand_on(tmp_path: Path):
    found = built(tmp_path).worked[QUILLHAVEN_1]
    # 230 homes stand on the square at 8.0 and 270 on the square at 8.5.
    assert (230 * 8.0 + 270 * 8.5) / 500 == 8.27
    assert found == Worked(8.3, 4, 4, 1.0, State.PRESENT)


def test_a_figure_is_given_to_one_decimal_place_with_a_half_taken_upward(tmp_path: Path):
    found = built(tmp_path, placed=on(*[C] * 4, *[A] * 8)).worked[QUILLHAVEN_1]
    assert found == Worked(9.3, 4, 4, 1.0, State.PRESENT)


def test_an_output_area_on_a_square_with_no_value_adds_nothing(tmp_path: Path):
    found = built(tmp_path).worked[QUILLHAVEN_2]
    # 180 of the area's 660 homes stand on the square the publisher gives no value for.
    assert found == Worked(8.0, 3, 4, round(480 / 660, 6), State.PARTIAL)


def test_below_half_the_homes_no_figure_is_given(tmp_path: Path):
    found = built(tmp_path).worked[TALLOWGATE]
    assert found == Worked(None, 1, 4, round(190 / 820, 6), State.BELOW_THRESHOLD)


def test_an_area_with_no_home_on_a_square_with_a_value_is_a_gap_and_never_nought(tmp_path: Path):
    placed = on(*[OFF_THE_GRID] * 4, *[D] * 4, *[A] * 4)
    found = built(tmp_path, placed=placed).worked
    assert found[QUILLHAVEN_1] == Worked(None, 0, 4, 0.0, State.SOURCE_GAP)
    assert found[QUILLHAVEN_2] == Worked(None, 0, 4, 0.0, State.SOURCE_GAP)
    assert found[TALLOWGATE] == Worked(8.0, 4, 4, 1.0, State.PRESENT)


# The evidence


def test_every_area_has_a_row_of_evidence_whether_or_not_it_has_a_figure(tmp_path: Path):
    found = built(tmp_path)
    assert [row.fact_id for row in found.rows] == [
        f"{area}/feature/air_pm25" for area in (QUILLHAVEN_1, QUILLHAVEN_2, TALLOWGATE)
    ]
    assert [row.state for row in found.rows] == [
        State.PRESENT,
        State.PARTIAL,
        State.BELOW_THRESHOLD,
    ]
    assert [row.value for row in found.rows] == [8.3, 8.0, None]
    assert [(row.units_used, row.units_expected) for row in found.rows] == [(4, 4), (3, 4), (1, 4)]


def test_a_row_names_the_grid_the_centres_the_lookup_and_the_homes(tmp_path: Path):
    found = built(tmp_path)
    by_source = {receipt.source_id: receipt.file_id for receipt in found.files}
    assert sorted(by_source) == sorted(
        [air_pm25.SOURCE, centres.CENTRES, spine.LOOKUP, spine.HOMES]
    )
    assert by_source[air_pm25.SOURCE] == found.grid.file_id
    for row in found.rows:
        assert row.inputs == tuple(sorted(by_source.values()))
        assert row.derivation_id == GRID_AT_HOMES.derivation_id
        assert row.retrieved_on == "2026-09-23"
        # From the day of the census, which the weights are of, to the end of the grid's year.
        assert row.data_period is not None
        assert row.data_period.days() == ("2021-03-21", "2024-12-31")


def test_the_figures_are_marked_as_modelled_and_keyed_by_squares_of_a_grid(tmp_path: Path):
    assert air_pm25.METHODS == (GRID_AT_HOMES,)
    assert air_pm25.METHOD.kind is Kind.MODELLED
    assert built(tmp_path).geography is Geography.GRID_1KM


def test_the_evidence_of_the_measure_has_no_loose_end(tmp_path: Path):
    found = built(tmp_path)
    evidence = Evidence.of("lon-2026-10-02-01", found.files, air_pm25.METHODS, found.rows)
    assert len(evidence.rows) == 3


# The name, the unit and the sentences


def test_core_holds_no_measure_of_fine_particles_so_no_build_carries_one():
    """When core gains the feature, add the measure to `derive/measures.py` and turn this round."""
    assert not air_pm25.core_holds_it()
    assert air_pm25.KEY not in {feature.value for feature in FeatureId}
    assert all(measure.reads is not air_pm25.is_the_grid for measure in measures.MEASURES)


def test_what_the_row_of_the_catalogue_would_say_is_said_as_for_nitrogen_dioxide(tmp_path: Path):
    proposed = built(tmp_path).proposed
    beside = FEATURES[FeatureId.AIR_NO2]
    assert (proposed.key, proposed.label) == (
        "air_pm25",
        "Modelled annual mean fine particles (PM2.5)",
    )
    assert (proposed.unit, proposed.dimension) == ("µg/m³", Dimension.AIR_NOISE)
    assert (proposed.unit, proposed.dimension) == (beside.unit, beside.dimension)
    # Less of it is better, and it is held on a grid.
    assert proposed.polarity is Polarity.LESS
    assert proposed.native_resolution is NativeResolution.GRID_1KM
    assert proposed.vintage == "2024"
    assert proposed.source_ids == tuple(sorted(proposed.source_ids))
    assert len(proposed.source_ids) == 4
    for source_id in proposed.source_ids:
        assert Use.SCORING in registry().get(source_id).uses


def test_the_measure_is_put_forward_as_shown_and_not_ranked_on(tmp_path: Path):
    assert built(tmp_path).proposed.rankable is False


def test_the_definition_is_one_sentence_that_says_what_the_figure_is_and_is_not(tmp_path: Path):
    definition = built(tmp_path).proposed.definition
    assert definition.endswith(".") and not re.search(r"[.!?]\s|\n", definition)
    for words in ("Defra", "modelled", "annual mean", "background", "for 2024", "1000 metres"):
        assert words in definition
    assert "fine particles (PM2.5)" in definition and "nitrogen dioxide" not in definition
    assert "to 1 decimal place" in definition
    assert "not a reading" in definition
    # It claims nothing the file does not say: not how the particles were weighed.
    assert "gravimetric" not in definition


def test_no_sentence_of_the_measure_describes_who_lives_somewhere(tmp_path: Path):
    sentences = (built(tmp_path).proposed.definition, *air_pm25.CANNOT_SEE)
    assert [sentence for sentence in sentences if no2.RESIDENT_WORDS.search(sentence)] == []


def test_what_it_cannot_see_is_said_in_two_sentences_with_no_figure_in_them():
    assert len(air_pm25.CANNOT_SEE) == 2
    for sentence in air_pm25.CANNOT_SEE:
        assert sentence.endswith(".") and not re.search(r"[.!?]\s|\d", sentence)
    assert "not a reading" in air_pm25.CANNOT_SEE[0]
    assert "differs little" in air_pm25.CANNOT_SEE[1]
