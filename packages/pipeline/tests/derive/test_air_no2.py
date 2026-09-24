"""Nitrogen dioxide, from the publisher's grid to a figure for each area.

Every file here is made up. The grid is laid out as the publisher lays out its
own: four rows of notes, an empty row, the header `gridcode,x,y,no22024`, plain
ASCII, and lines that end CR LF. What it holds is made up: four squares in the
North Sea, where the made-up town of the tests of cells stands, and one far to
the west with an easting below nought, as the real file has.

             x: 700500   701500
    y: 401500     40.0   MISSING
    y: 400500     10.0     20.0

The town is twelve output areas in three areas. Each test puts their centres on
the squares it needs, so that each figure can be worked out by hand.

    Quillhaven 001   homes 110, 120, 130, 140   500 in all
    Quillhaven 002   homes 150, 160, 170, 180   660 in all
    Tallowgate 001   homes 190, 200, 210, 220   820 in all
"""

import hashlib
import re
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest
from burro_core.catalogue import FEATURES
from burro_core.ids import FeatureId, NativeResolution, Polarity
from burro_pipeline.cells import centres, spine
from burro_pipeline.derive import air_no2
from burro_pipeline.derive.air_no2 import Air
from burro_pipeline.derive.methods import GRID_AT_HOMES, Worked
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind
from burro_pipeline.evidence.receipt import Geography, How, Period, Receipt
from burro_pipeline.evidence.record import file_id_of
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.fetch.store import FolderStore
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import CENTRES_COLUMNS, FILES, LONDON, contents, held, receipt_of, registry

# A string found nowhere else. If a refusal repeats what a file holds, this shows up in it.
CANARY = "Zzyzx Parva"
GRID_NAME = "mapno22024.csv"
NOTES = ("no2", "2024", "annual mean", "ug m-3")
HEADER = ("gridcode", "x", "y", "no22024")
# The squares of the made-up grid, each by its number, its middle and its value.
A, B, C, D = (700_500, 400_500), (701_500, 400_500), (700_500, 401_500), (701_500, 401_500)
FAR_WEST = (-500, 5_500)
SQUARES = (
    ("900001", *A, "10.0"),
    ("900002", *B, "20.0"),
    ("900003", *C, "40.0"),
    ("900004", *D, "MISSING"),
    ("900005", *FAR_WEST, "1.5"),
)
# A square the made-up grid does not hold at all.
OFF_THE_GRID = (705_500, 400_500)
QUILLHAVEN_1, QUILLHAVEN_2, TALLOWGATE = "lon-ne02999001", "lon-ne02999002", "lon-ne02999003"
OAS = tuple(unit.oa for unit in LONDON)

Middle = tuple[int, int]


def grid_csv(
    squares: Sequence[Sequence[object]] = SQUARES,
    notes: Sequence[str] = NOTES,
    header: Sequence[str] = HEADER,
    gap: str = ",,,",
) -> bytes:
    """A grid as the publisher writes one. What it holds is made up."""
    lines = [
        *(f"{note},,," for note in notes),
        gap,
        ",".join(header),
        *(",".join(str(cell) for cell in square) for square in squares),
    ]
    return "".join(f"{line}\r\n" for line in lines).encode("ascii")


def centres_at(middles: Mapping[str, Middle]) -> bytes:
    """The centres of the town's output areas, each a little off the middle of a square."""
    lines = [",".join(CENTRES_COLUMNS)]
    for number, unit in enumerate(LONDON, start=1):
        if unit.oa not in middles:
            continue
        east, north = middles[unit.oa]
        lines.append(
            f"{east + 12.3456:.4f},{north - 7.8901:.4f},{number},{unit.oa},"
            f"{{made-up-{number}}},{{made-up-{number}-2}}"
        )
    return b"\xef\xbb\xbf" + "".join(f"{line}\n" for line in lines).encode()


def on(*middles: Middle) -> dict[str, Middle]:
    """Twelve centres, one for each output area of the town, in the order of their codes."""
    assert len(middles) == len(OAS)
    return dict(zip(OAS, middles, strict=True))


# The first area stands half on A and half on B. The second has one output area on the
# square with no value. The third has three of its four off the grid.
PLACED = on(A, A, B, B, A, A, A, D, A, OFF_THE_GRID, OFF_THE_GRID, OFF_THE_GRID)


def grid_receipt(content: bytes, name: str = GRID_NAME, year: str = "2024") -> Receipt:
    sha256 = hashlib.sha256(content).hexdigest()
    return Receipt(
        file_id=file_id_of(sha256),
        source_id=air_no2.SOURCE,
        use=Use.SCORING,
        publisher_file=name,
        url=f"https://files.made-up.example/{sha256[:8]}",
        sha256=sha256,
        bytes=len(content),
        retrieved_at="2026-09-23T21:09:21Z",
        how=How.FETCHED,
        edition=year,
        data_period=Period(as_at=year),
    )


def inputs_of(
    folder: Path,
    grid: bytes | None = None,
    placed: Mapping[str, Middle] = PLACED,
    *,
    more: Sequence[tuple[Receipt, bytes]] = (),
    year: str = "2024",
    given: Registry | None = None,
) -> Inputs:
    """The made-up files of a build in a store of their own, with a receipt for each."""
    grid = grid_csv() if grid is None else grid
    files = contents() | {"centres": centres_at(placed)}
    receipts = [
        (receipt_of(FILES[which][0], FILES[which][1], FILES[which][2], content, FILES[which][3]))
        for which, content in files.items()
    ]
    every = [
        *zip(receipts, files.values(), strict=True),
        (grid_receipt(grid, year=year), grid),
        *more,
    ]
    store = FolderStore(folder / "store")
    for receipt, content in every:
        path = folder / "given" / receipt.file_id / receipt.publisher_file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        store.put(receipt.source_id, receipt.publisher_file, path)
    return Inputs(given or registry(), [receipt for receipt, _ in every], store, folder / "work")


def built(folder: Path, grid: bytes | None = None, placed: Mapping[str, Middle] = PLACED) -> Air:
    inputs = inputs_of(folder, grid, placed)
    return air_no2.build(inputs, spine.build(inputs))


def refused(folder: Path, grid: bytes, year: str = "2024") -> LockError:
    """The refusal of a grid, which names a rule and repeats nothing the file holds."""
    inputs = inputs_of(folder, grid, year=year)
    with pytest.raises(LockError) as stopped:
        air_no2.build(inputs, spine.build(inputs))
    assert stopped.value.rule == "input_is_as_described"
    assert CANARY not in str(stopped.value)
    assert str(folder) not in str(stopped.value)
    return stopped.value


# The parser


def test_the_grid_is_read_from_under_four_notes_an_empty_row_and_the_header(tmp_path: Path):
    grid = built(tmp_path).grid
    assert (grid.year, grid.rows, grid.without_a_value) == (2024, 5, 1)
    # A square is kept by its corner, which is its middle less 500 metres each way.
    assert grid.values == {
        (700_000, 400_000): 10.0,
        (701_000, 400_000): 20.0,
        (700_000, 401_000): 40.0,
        (-1_000, 5_000): 1.5,
    }


def test_a_square_the_publisher_gives_no_value_for_is_counted_and_never_nought(tmp_path: Path):
    grid = built(tmp_path).grid
    assert (701_000, 401_000) not in grid.values
    assert grid.without_a_value == 1
    assert 0 not in grid.values.values()


def test_the_grid_names_the_file_it_was_read_from(tmp_path: Path):
    inputs = inputs_of(tmp_path)
    found = air_no2.build(inputs, spine.build(inputs))
    assert found.grid.file_id == grid_receipt(grid_csv()).file_id


@pytest.mark.parametrize("missing", HEADER)
def test_a_grid_without_a_column_is_refused_and_the_column_is_named(tmp_path: Path, missing: str):
    header = [CANARY if name == missing else name for name in HEADER]
    stopped = refused(tmp_path, grid_csv(header=header))
    assert f"the column {missing} is missing" in str(stopped)


@pytest.mark.parametrize(
    ("notes", "words"),
    [
        (("pm25", "2024", "annual mean", "ug m-3"), "not a map of nitrogen dioxide"),
        ((CANARY, "2024", "annual mean", "ug m-3"), "not a map of nitrogen dioxide"),
        (("no2", CANARY, "annual mean", "ug m-3"), "the year it states is no year"),
        (("no2", "2024", "hourly maximum", "ug m-3"), "not an annual mean"),
        (("no2", "2024", "annual mean", "ppb"), "not in micrograms a cubic metre"),
    ],
)
def test_a_grid_whose_notes_say_something_else_is_refused(
    tmp_path: Path, notes: tuple[str, ...], words: str
):
    assert words in str(refused(tmp_path, grid_csv(notes=notes)))


def test_a_grid_of_another_year_than_its_receipt_says_is_refused(tmp_path: Path):
    """The year a figure is shown with is the receipt's, so the file must say the same."""
    grid = grid_csv(notes=("no2", "2023", "annual mean", "ug m-3"), header=(*HEADER[:3], "no22023"))
    assert "not the year of its receipt" in str(refused(tmp_path, grid))
    assert built(tmp_path / "same", grid_csv()).grid.year == 2024


def test_a_grid_whose_header_is_not_on_the_sixth_row_is_refused(tmp_path: Path):
    assert "sixth row" in str(refused(tmp_path, grid_csv(gap=",".join(HEADER))))


def test_a_file_that_is_no_grid_is_refused(tmp_path: Path):
    assert "nitrogen dioxide" in str(refused(tmp_path, f"{CANARY}\r\n".encode()))
    assert "holds no square" in str(refused(tmp_path / "bare", grid_csv(squares=())))


@pytest.mark.parametrize("value", ["-1.5", "nan", "inf", "1e3", "", " 12.5", "12,5", CANARY])
def test_a_value_that_is_no_number_is_refused(tmp_path: Path, value: str):
    squares = (*SQUARES[:4], ("900005", *FAR_WEST, f'"{value}"'))
    assert "a value is no value" in str(refused(tmp_path, grid_csv(squares)))


@pytest.mark.parametrize("middle", [("700000", "400500"), ("700500.5", "400500"), ("", "400500")])
def test_a_square_that_is_not_named_by_its_middle_is_refused(
    tmp_path: Path, middle: tuple[str, str]
):
    squares = (*SQUARES, ("900006", *middle, "12.5"))
    assert "not named by its middle" in str(refused(tmp_path, grid_csv(squares)))


def test_a_square_that_is_there_twice_is_refused(tmp_path: Path):
    squares = (*SQUARES, ("900006", *A, "12.5"))
    assert "a square is there twice" in str(refused(tmp_path, grid_csv(squares)))


def test_a_row_that_is_short_is_refused(tmp_path: Path):
    squares = (*SQUARES, ("900006", "702500"))
    assert "a row is short" in str(refused(tmp_path, grid_csv(squares)))


def test_a_column_the_measure_does_not_read_is_never_used(tmp_path: Path):
    """A column beside the four changes nothing, whatever it holds."""
    squares = [(*square, CANARY) for square in SQUARES]
    wider = built(tmp_path, grid_csv(squares, header=(*HEADER, "made_up_note")))
    assert wider.worked == built(tmp_path / "plain").worked


# The gate, the receipt and the store


def without_scoring() -> Registry:
    """The repository's registry, with the grid no longer registered for scoring."""
    sources = [
        source.model_copy(update={"uses": (Use.DISPLAY,)})
        if source.id == air_no2.SOURCE
        else source
        for source in registry()
    ]
    return Registry(tuple(sources))


def test_the_gate_is_asked_before_the_grid_is_read(tmp_path: Path):
    inputs = inputs_of(tmp_path, given=without_scoring())
    found = spine.build(inputs)
    before = inputs.opened
    with pytest.raises(LockError) as stopped:
        air_no2.build(inputs, found)
    assert stopped.value.rule == "gate_refuses"
    # Nothing more was handed over: not the grid, and not the centres it would be read at.
    assert inputs.opened == before
    assert not (tmp_path / "work" / grid_receipt(grid_csv()).file_id).exists()


def test_the_grid_is_registered_for_scoring_and_so_is_every_file_behind_a_figure(tmp_path: Path):
    found = built(tmp_path)
    for source_id in found.metric.source_ids:
        assert Use.SCORING in registry().get(source_id).uses


def test_the_grid_is_told_from_the_other_pollutant_of_its_source(tmp_path: Path):
    """The source holds a file for each pollutant and year, and the store holds two today."""
    other = grid_csv(
        [(number, x, y, "99.0") for number, x, y, _ in SQUARES],
        notes=("pm25", "2024", "annual mean", "ug m-3"),
        header=(*HEADER[:3], "pm252024g"),
    )
    inputs = inputs_of(tmp_path, more=[(grid_receipt(other, name="mappm252024g.csv"), other)])
    found = air_no2.build(inputs, spine.build(inputs))
    assert found.grid.file_id == grid_receipt(grid_csv()).file_id
    assert value_of(found.worked[QUILLHAVEN_1]) == 15.4


def test_two_years_of_the_grid_are_told_apart_by_the_year_that_is_asked_for(tmp_path: Path):
    earlier = grid_csv(
        notes=("no2", "2023", "annual mean", "ug m-3"), header=(*HEADER[:3], "no22023")
    )
    more = [(grid_receipt(earlier, name="mapno22023.csv", year="2023"), earlier)]
    inputs = inputs_of(tmp_path, more=more)
    found = spine.build(inputs)
    with pytest.raises(LockError) as stopped:
        air_no2.build(inputs, found)
    assert stopped.value.rule == "input_has_one_receipt"
    assert air_no2.build(inputs, found, edition="2023").metric.vintage == "2023"
    assert air_no2.build(inputs, found, edition="2024").metric.vintage == "2024"


def test_nothing_is_written_to_the_store(tmp_path: Path):
    inputs = inputs_of(tmp_path)
    before = held(tmp_path / "store")
    air_no2.build(inputs, spine.build(inputs))
    assert held(tmp_path / "store") == before


# The figure


def value_of(worked: Worked) -> float:
    assert worked.value is not None
    return worked.value


def test_an_area_is_given_the_mean_of_the_squares_its_homes_stand_on(tmp_path: Path):
    found = built(tmp_path).worked[QUILLHAVEN_1]
    # 230 homes stand on the square at 10 and 270 on the square at 20.
    assert (230 * 10 + 270 * 20) / 500 == 15.4
    assert found == Worked(15.4, 4, 4, 1.0, State.PRESENT)


def test_a_figure_is_given_to_one_decimal_place(tmp_path: Path):
    found = built(tmp_path, placed=on(*[A] * 4, A, B, B, B, *[A] * 4)).worked[QUILLHAVEN_2]
    # 150 homes stand on the square at 10 and 510 on the square at 20: 17.7272 and so on.
    assert round((150 * 10 + 510 * 20) / 660, 4) == 17.7273
    assert found == Worked(17.7, 4, 4, 1.0, State.PRESENT)


def test_an_output_area_on_a_square_with_no_value_adds_nothing(tmp_path: Path):
    found = built(tmp_path).worked[QUILLHAVEN_2]
    # 180 of the area's 660 homes stand on the square the publisher gives no value for.
    assert found == Worked(10.0, 3, 4, round(480 / 660, 6), State.PARTIAL)


def test_below_half_the_homes_no_figure_is_given(tmp_path: Path):
    found = built(tmp_path).worked[TALLOWGATE]
    assert found == Worked(None, 1, 4, round(190 / 820, 6), State.BELOW_THRESHOLD)


def test_an_area_with_no_home_on_the_grid_is_a_gap_and_has_no_figure(tmp_path: Path):
    placed = on(*[OFF_THE_GRID] * 4, *[D] * 4, *[A] * 4)
    found = built(tmp_path, placed=placed).worked
    assert found[QUILLHAVEN_1] == Worked(None, 0, 4, 0.0, State.SOURCE_GAP)
    assert found[QUILLHAVEN_2] == Worked(None, 0, 4, 0.0, State.SOURCE_GAP)
    assert found[TALLOWGATE] == Worked(10.0, 4, 4, 1.0, State.PRESENT)


def test_an_output_area_with_no_centre_is_not_given_the_value_of_a_neighbour(tmp_path: Path):
    placed = {oa: middle for oa, middle in on(*[A] * 4, *[B] * 8).items() if oa != OAS[0]}
    found = built(tmp_path, placed=placed).worked[QUILLHAVEN_1]
    # The first output area holds 110 of the area's 500 homes.
    assert found == Worked(10.0, 3, 4, round(390 / 500, 6), State.PARTIAL)


def test_a_centre_is_read_on_the_square_it_stands_on_and_no_other(tmp_path: Path):
    """The centres stand 12 metres east and 8 south of a middle, so each is inside its square."""
    found = built(tmp_path, placed=on(*[C] * 4, *[B] * 4, *[A] * 4))
    assert [value_of(found.worked[area]) for area in sorted(found.worked)] == [40.0, 20.0, 10.0]
    assert found.squares_read == 3


def test_the_order_of_the_rows_changes_nothing(tmp_path: Path):
    turned = built(tmp_path, grid_csv(tuple(reversed(SQUARES))))
    assert turned.worked == built(tmp_path / "as-written").worked


# The evidence


def test_every_area_has_a_row_of_evidence_whether_or_not_it_has_a_figure(tmp_path: Path):
    found = built(tmp_path)
    assert [row.fact_id for row in found.rows] == [
        f"{area}/feature/air_no2" for area in (QUILLHAVEN_1, QUILLHAVEN_2, TALLOWGATE)
    ]
    assert [row.state for row in found.rows] == [
        State.PRESENT,
        State.PARTIAL,
        State.BELOW_THRESHOLD,
    ]
    assert [(row.units_used, row.units_expected) for row in found.rows] == [(4, 4), (3, 4), (1, 4)]
    assert [row.has_a_value for row in found.rows] == [
        found.worked[row.area_id].value is not None for row in found.rows
    ]


def test_a_row_names_the_grid_the_centres_the_lookup_and_the_homes(tmp_path: Path):
    inputs = inputs_of(tmp_path)
    found = air_no2.build(inputs, spine.build(inputs))
    by_source = {receipt.source_id: receipt.file_id for receipt in found.files}
    assert sorted(by_source) == sorted(
        [air_no2.SOURCE, centres.CENTRES, spine.LOOKUP, spine.HOMES],
    )
    for row in found.rows:
        assert row.inputs == tuple(sorted(by_source.values()))
        assert row.derivation_id == GRID_AT_HOMES.derivation_id
        assert row.retrieved_on == "2026-09-23"
        # From the day of the census, which the weights are of, to the end of the grid's year.
        assert row.data_period is not None
        assert row.data_period.days() == ("2021-03-21", "2024-12-31")


def test_the_figures_are_marked_as_modelled():
    assert air_no2.METHODS == (GRID_AT_HOMES,)
    assert air_no2.METHOD.kind is Kind.MODELLED


def test_the_measure_says_that_the_file_is_keyed_by_squares_of_a_grid(tmp_path: Path):
    assert built(tmp_path).geography is Geography.GRID_1KM


def test_the_evidence_of_the_measure_has_no_loose_end(tmp_path: Path):
    """Every row names a method and files that the evidence of a release would hold."""
    found = built(tmp_path)
    evidence = Evidence.of("lon-2026-10-02-01", found.files, air_no2.METHODS, found.rows)
    assert len(evidence.rows) == 3


# The name, the unit and the sentences


def test_the_row_of_the_catalogue_says_what_core_says_of_the_measure(tmp_path: Path):
    metric = built(tmp_path).metric
    feature = FEATURES[FeatureId.AIR_NO2]
    assert (metric.label, metric.unit) == (feature.label, feature.unit)
    assert (metric.label, metric.unit) == ("Modelled annual mean nitrogen dioxide", "µg/m³")
    # Less of it is better, and it is held on a grid.
    assert metric.polarity is Polarity.LESS
    assert metric.native_resolution is NativeResolution.GRID_1KM
    assert metric.vintage == "2024"
    assert metric.source_ids == tuple(sorted(metric.source_ids))
    assert len(metric.source_ids) == 4


def test_the_definition_is_one_sentence_that_says_what_the_figure_is_and_is_not(tmp_path: Path):
    definition = built(tmp_path).metric.definition
    assert definition.endswith(".") and not re.search(r"[.!?]\s|\n", definition)
    for words in ("Defra", "modelled", "annual mean", "background", "for 2024", "1000 metres"):
        assert words in definition
    assert "to 1 decimal place" in definition
    assert "not a reading" in definition
    # Every parameter of the method stands in it, as it stands in the method's own sentence.
    assert str(air_no2.METHOD.parameters["square_metres"]) in definition


RESIDENT_WORDS = re.compile(
    r"\b(residents?|people|population|households?|famil(y|ies)|health|ages?|incomes?)\b", re.I
)


def test_no_sentence_of_the_measure_describes_who_lives_somewhere(tmp_path: Path):
    sentences = (built(tmp_path).metric.definition, *air_no2.CANNOT_SEE)
    assert [sentence for sentence in sentences if RESIDENT_WORDS.search(sentence)] == []


def test_what_it_cannot_see_is_said_in_three_sentences_with_no_figure_in_them():
    assert len(air_no2.CANNOT_SEE) == 3
    for sentence in air_no2.CANNOT_SEE:
        assert sentence.endswith(".") and not re.search(r"[.!?]\s|\d", sentence)


def test_it_says_that_homes_are_weighed_as_they_stood_at_the_census():
    """The weights are households of 2021. Where homes were built since, they are not there."""
    assert any("as they stood at the last census" in line for line in air_no2.CANNOT_SEE)
