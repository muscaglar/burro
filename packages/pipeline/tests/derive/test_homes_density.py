"""Homes per hectare, from a made-up table of homes laid out as the publisher lays out its own.

Every figure here is made up. The town is the made-up town of the tests of
cells: three areas, each an MSOA of two LSOAs, in squares of one hectare. The
table of homes has the publisher's own columns, its mark at the start, its
quotes round every cell, its row for each larger area, and its ways of writing
a cell. What it holds is made up.

The homes of an area are read from the row of the MSOA, which is the area's
own. The rows of its LSOAs are what that row is held to.

    area               row           hectares   homes in the table
    Quillhaven 001     E02999001     4          200     200 over 4 is 50
                         E01999001   2          120
                         E01999002   2           80
    Quillhaven 002     E02999002     4           40      40 over 4 is 10
                         E01999003   2           40
                         E01999004   2            0
    Tallowgate 001     E02999003     5          500     500 over 5 is 100
                         E01999005   2          250
                         E01999006   3          250
"""

import csv
import io
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest
from burro_core.catalogue import FEATURES
from burro_core.ids import FeatureId
from burro_pipeline.cells import land, spine
from burro_pipeline.derive import homes_density
from burro_pipeline.derive.homes_density import Density, Stock
from burro_pipeline.derive.methods import Worked, to_places
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.receipt import Geography, Period
from burro_pipeline.evidence.row import Flag, State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import CANARY, contents, inputs_of, receipt_of, registry, zip_of

NAME = "CTSOP1.1.zip"
TABLE = "CTSOP1.1/CTSOP1_1_2025_03_31.csv"
NOTES = "CTSOP1.1/CTSOP1_1_CSV_table_notes.xlsx"
# The columns of the publisher's table, in its order.
COLUMNS = (
    "geography",
    "ba_code",
    "ecode",
    "area_name",
    "band_a",
    "band_b",
    "band_c",
    "band_d",
    "band_e",
    "band_f",
    "band_g",
    "band_h",
    "band_i",
    "all_properties",
)
ONE, TWO, THREE = "lon-ne02999001", "lon-ne02999002", "lon-ne02999003"
HOMES: Mapping[str, str] = {
    "E01999001": "120",
    "E01999002": "80",
    "E01999003": "40",
    "E01999004": "0",
    "E01999005": "250",
    "E01999006": "250",
    # Outside London, and in Wales. Neither is part of any area.
    "E01999901": "700",
    "W01999001": "90",
}
# The publisher's own count for each MSOA, rounded once. A figure is read from it.
OF_MSOAS: Mapping[str, str] = {
    "E02999001": "200",
    "E02999002": "40",
    "E02999003": "500",
    "E02999901": "700",
}
# Rows for larger areas, which the table holds beside those for LSOAs and MSOAs. 9990 is
# no count of any row that is read, so a figure made from one of these rows would show.
LARGER = (
    ("ENGWAL", "E92999999"),
    ("NATL", "E92999998"),
    ("REGL", "E12999901"),
    ("CTYMET", "E11999901"),
    ("LAUA", "E09000901"),
    ("UNMD", "E01999001"),
)


def table_of(
    homes: Mapping[str, str] = HOMES,
    of_msoas: Mapping[str, str] = OF_MSOAS,
    columns: Sequence[str] = COLUMNS,
    twice: Sequence[str] = (),
) -> bytes:
    """The table of homes by band, as the publisher writes it.

    It has a mark at the start, quotes round every cell, and lines that end LF.
    """
    text = io.StringIO(newline="")
    table = csv.DictWriter(
        text, columns, extrasaction="ignore", lineterminator="\n", quoting=csv.QUOTE_ALL
    )
    table.writeheader()
    rows = [*((kind, code, "9990") for kind, code in LARGER)]
    rows += [("MSOA", code, count) for code, count in of_msoas.items()]
    rows += [("LSOA", code, count) for code, count in homes.items()]
    rows += [("LSOA", code, homes[code]) for code in twice if code in homes]
    rows += [("MSOA", code, of_msoas[code]) for code in twice if code in of_msoas]
    for kind, code, count in rows:
        # A band may have a dash where the total has a count. No band is read.
        bands = dict.fromkeys(COLUMNS[4:11], "10") | {"band_h": "-"}
        # Band I is for Wales alone. For an English row the table writes two dots.
        table.writerow(
            {"geography": kind, "ba_code": "n/a", "ecode": code, "area_name": CANARY}
            | bands
            | {"band_i": "10" if code.startswith("W") else "..", "all_properties": count}
        )
    return b"\xef\xbb\xbf" + text.getvalue().encode()


def zipped(table: bytes, name: str = TABLE) -> bytes:
    # The notes are a workbook. No step opens them, so these are not one.
    return zip_of({name: table, NOTES: CANARY})


def inputs_with(
    folder: Path, table: bytes | None = None, as_at: str = "2025-03-31", **changes: Registry
) -> Inputs:
    """The made-up build of the tests of cells, and the table of homes beside it."""
    given = inputs_of(folder, contents(), **changes)
    content = zipped(table_of()) if table is None else table
    path = folder / "given" / NAME
    path.write_bytes(content)
    given.store.put(homes_density.SOURCE, NAME, path)
    receipt = receipt_of(homes_density.SOURCE, Use.SCORING, NAME, content, "2025").model_copy(
        update={"data_period": Period(as_at=as_at)}
    )
    return Inputs(given.registry, [*given.receipts, receipt], given.store, given.work)


def built(
    folder: Path, homes: Mapping[str, str] = HOMES, of_msoas: Mapping[str, str] = OF_MSOAS
) -> Density:
    inputs = inputs_with(folder, zipped(table_of(homes, of_msoas)))
    found = spine.build(inputs)
    return homes_density.build(inputs, found, land.build(inputs, found))


def refused(folder: Path, table: bytes, as_at: str = "2025-03-31") -> LockError:
    """The refusal of a table, which repeats nothing the table holds."""
    inputs = inputs_with(folder, table, as_at)
    found = spine.build(inputs)
    measured = land.build(inputs, found)
    with pytest.raises(LockError) as stopped:
        homes_density.build(inputs, found, measured)
    assert stopped.value.rule == "input_is_as_described"
    assert CANARY not in str(stopped.value)
    assert str(folder) not in str(stopped.value)
    return stopped.value


ROUNDED = (Flag.ROUNDED_IN_SOURCE,)
WITHHELD = (Flag.ROUNDED_IN_SOURCE, Flag.SUPPRESSED_IN_SOURCE)


# The figure


def test_homes_per_hectare_is_the_homes_of_an_area_over_all_its_land(tmp_path: Path):
    found = built(tmp_path).worked
    assert found == {
        ONE: Worked(50.0, 1, 1, 1.0, State.PRESENT, ROUNDED),
        TWO: Worked(10.0, 1, 1, 1.0, State.PRESENT, ROUNDED),
        THREE: Worked(100.0, 1, 1, 1.0, State.PRESENT, ROUNDED),
    }


def test_the_homes_are_read_from_the_areas_own_row_and_not_added_up_from_its_lsoas(
    tmp_path: Path,
):
    """The LSOAs of Quillhaven 001 add up to 210 homes, which over 4 hectares is 52.5.

    The publisher's own row for the area holds 200. Rounding lets the two
    differ, and the row is the one a reader finds in the table.
    """
    assert built(tmp_path, {**HOMES, "E01999001": "130"}).worked[ONE].value == 50.0


def test_the_land_is_all_the_land_of_the_area_and_never_a_mean_of_densities(tmp_path: Path):
    # 250 homes on 2 hectares and 250 on 3. The mean of 125 and 83.3 would be 104.2.
    assert built(tmp_path).worked[THREE].value == 100.0


def test_a_count_of_nought_is_a_count(tmp_path: Path):
    found = built(tmp_path, {**HOMES, "E01999003": "0"}, {**OF_MSOAS, "E02999002": "0"})
    assert found.worked[TWO] == Worked(0.0, 1, 1, 1.0, State.PRESENT, ROUNDED)


def test_a_figure_is_given_to_one_decimal_place(tmp_path: Path):
    """A count is rounded to 10 by its publisher, so a second decimal place would say nothing."""
    # 110 homes on 4 hectares.
    homes = {**HOMES, "E01999001": "110", "E01999002": "0"}
    assert built(tmp_path, homes, {**OF_MSOAS, "E02999001": "110"}).worked[ONE].value == 27.5
    # 70 homes on 5 hectares is 14, and 70 on 4 is 17.5.
    homes = {**HOMES, "E01999005": "0", "E01999006": "70"}
    found = built(tmp_path / "long", homes, {**OF_MSOAS, "E02999003": "70"}).worked[THREE]
    assert (found.value, found.state) == (14.0, State.PRESENT)


def test_a_figure_that_stands_on_a_half_is_rounded_upward(tmp_path: Path):
    """90 homes on 4 hectares is 22.5, and 50 on 4 is 12.5. At no decimal place both go up."""
    homes = {**HOMES, "E01999001": "50", "E01999002": "0"}
    found = built(tmp_path, homes, {**OF_MSOAS, "E02999001": "50"}).worked[ONE]
    assert found.value == 12.5
    assert to_places(12.5, 0) == 13.0 and to_places(22.5, 0) == 23.0


# What the table leaves out


def test_an_area_whose_row_holds_a_dash_has_no_figure_and_is_never_nought(tmp_path: Path):
    """A dash is a count of 1 to 4. The area has homes, and the file does not say how many."""
    homes = {**HOMES, "E01999003": "-", "E01999004": "0"}
    found = built(tmp_path, homes, {**OF_MSOAS, "E02999002": "-"}).worked[TWO]
    assert found == Worked(None, 0, 1, 0.0, State.SUPPRESSED, WITHHELD)


def test_a_dash_in_the_row_of_an_lsoa_does_not_mark_a_figure_read_from_its_msoa(
    tmp_path: Path,
):
    found = built(tmp_path, {**HOMES, "E01999004": "-"}).worked[TWO]
    assert found == Worked(10.0, 1, 1, 1.0, State.PRESENT, ROUNDED)


def test_an_area_with_no_row_at_all_is_a_gap_and_never_a_nought(tmp_path: Path):
    """The build stops before this. The figures are still never made round a hole."""
    inputs = inputs_with(tmp_path)
    found = spine.build(inputs)
    stock = Stock(
        homes={},
        withheld=frozenset(),
        of_msoa={"E02999001": 200},
        as_at="2025-03-31",
        rows=1,
        file_id="f-000000000000",
    )
    worked = homes_density.figures(stock, land.build(inputs, found), found)
    assert worked[ONE].value == 50.0
    assert worked[THREE] == Worked(None, 0, 1, 0.0, State.SOURCE_GAP, ROUNDED)


# The row of an area is held to the rows of its LSOAs


def test_the_row_of_every_area_is_held_to_the_rows_of_its_lsoas(tmp_path: Path):
    assert built(tmp_path).rows_held == 3


@pytest.mark.parametrize(
    ("own", "words"),
    [
        ("-", "a dash hides more than a small count"),
        ("0", "an area holds nought and a part of it does not"),
        ("60", "an area's count is not within rounding of its parts"),
        ("400", "an area's count is not within rounding of its parts"),
    ],
)
def test_a_row_that_is_not_what_the_rows_of_its_lsoas_allow_stops_the_build(
    tmp_path: Path, own: str, words: str
):
    table = zipped(table_of(of_msoas={**OF_MSOAS, "E02999002": own}))
    assert words in str(refused(tmp_path, table))


def test_an_area_with_no_row_of_its_own_stops_the_build(tmp_path: Path):
    of_msoas = {code: count for code, count in OF_MSOAS.items() if code != "E02999002"}
    stopped = refused(tmp_path, zipped(table_of(of_msoas=of_msoas)))
    assert "an MSOA of the census of 2021 has no row" in str(stopped)


# Which census, and which day


def test_the_rows_a_figure_is_read_from_are_keyed_by_the_msoas_of_2021(tmp_path: Path):
    assert built(tmp_path).geography is Geography.MSOA21


@pytest.mark.parametrize("left_out", ["E01999001", "E01999006"])
def test_a_table_that_lacks_an_lsoa_of_the_spine_stops_the_build(tmp_path: Path, left_out: str):
    """A table on the codes of another census lacks every LSOA that was drawn again."""
    homes = {code: count for code, count in HOMES.items() if code != left_out}
    stopped = refused(tmp_path, zipped(table_of(homes)))
    assert "an LSOA of the census of 2021 has no row" in str(stopped)


def test_the_day_of_the_counts_is_read_from_the_name_of_the_table(tmp_path: Path):
    made = built(tmp_path)
    assert made.stock.as_at == "2025-03-31"
    assert made.metric.vintage == "2025-03-31"


@pytest.mark.parametrize(
    "name", ["CTSOP1_1.csv", "CTSOP1_1_2025_13_31.csv", "CTSOP3_1_2025_03_31.csv", "made-up.csv"]
)
def test_a_table_that_is_not_named_for_a_day_is_refused(tmp_path: Path, name: str):
    stopped = refused(tmp_path, zipped(table_of(), name=f"CTSOP1.1/{name}"))
    assert "the table is not named for a day" in str(stopped)


def test_a_table_of_another_day_than_its_receipt_gives_is_refused(tmp_path: Path):
    stopped = refused(tmp_path, zipped(table_of()), as_at="2024-03-31")
    assert "the table is not of the day its receipt gives" in str(stopped)


# The parser


def test_only_the_rows_of_an_msoa_and_an_lsoa_are_read_and_every_row_is_counted(
    tmp_path: Path,
):
    stock = built(tmp_path).stock
    assert stock.rows == len(LARGER) + len(OF_MSOAS) + len(HOMES)
    assert stock.homes == {code: int(count) for code, count in HOMES.items()}
    assert stock.of_msoa == {code: int(count) for code, count in OF_MSOAS.items()}
    assert stock.withheld == frozenset()
    assert 9990 not in stock.homes.values() and 9990 not in stock.of_msoa.values()


def test_no_band_is_read(tmp_path: Path):
    """A band is a value of 1991. The table is read for its total and for nothing else."""
    assert set(homes_density.COLUMNS) == {"geography", "ecode", "all_properties"}
    columns = [name for name in COLUMNS if not name.startswith("band_")]
    table = table_of(columns=columns)
    inputs = inputs_with(tmp_path, zipped(table))
    found = spine.build(inputs)
    made = homes_density.build(inputs, found, land.build(inputs, found))
    assert made.worked[ONE].value == 50.0


@pytest.mark.parametrize("missing", homes_density.COLUMNS)
def test_a_table_without_a_column_that_is_read_is_refused_and_the_column_is_named(
    tmp_path: Path, missing: str
):
    table = table_of(columns=[name for name in COLUMNS if name != missing])
    assert f"the column {missing} is missing" in str(refused(tmp_path, zipped(table)))


def test_a_table_whose_columns_have_other_names_is_refused(tmp_path: Path):
    table = table_of().replace(b'"all_properties"', b'"All properties"')
    assert "the column all_properties is missing" in str(refused(tmp_path, zipped(table)))


@pytest.mark.parametrize("cell", ["", "..", "12a", "-5", "1,200", "12.5", " 120", "c", "١٢٠"])
def test_a_cell_that_is_no_count_stops_the_build(tmp_path: Path, cell: str):
    stopped = refused(tmp_path, zipped(table_of({**HOMES, "E01999901": cell})))
    assert "a count is not a count" in str(stopped)


def test_a_count_that_is_not_rounded_to_ten_stops_the_build(tmp_path: Path):
    """The figure is said to be rounded by its publisher. A table that is not must be looked at."""
    stopped = refused(tmp_path, zipped(table_of({**HOMES, "E01999002": "84"})))
    assert "a count is not rounded to 10" in str(stopped)


def test_an_lsoa_that_is_there_twice_stops_the_build(tmp_path: Path):
    stopped = refused(tmp_path, zipped(table_of(twice=["E01999003"])))
    assert "an LSOA is there twice" in str(stopped)


def test_an_msoa_that_is_there_twice_stops_the_build(tmp_path: Path):
    stopped = refused(tmp_path, zipped(table_of(twice=["E02999002"])))
    assert "an MSOA is there twice" in str(stopped)


def test_a_row_for_an_msoa_whose_code_is_not_one_stops_the_build(tmp_path: Path):
    table = zipped(table_of(of_msoas={**OF_MSOAS, "E01999001": "10"}))
    assert "a code is not a code" in str(refused(tmp_path, table))


def test_a_table_with_no_row_of_an_msoa_is_refused(tmp_path: Path):
    assert "it holds no row of an MSOA" in str(refused(tmp_path, zipped(table_of(of_msoas={}))))


@pytest.mark.parametrize("code", ["E02999001", "e01999001", "E0199900", "E019990011", ""])
def test_a_row_for_an_lsoa_whose_code_is_not_one_stops_the_build(tmp_path: Path, code: str):
    stopped = refused(tmp_path, zipped(table_of({**HOMES, code: "10"})))
    assert "a code is not a code" in str(stopped)


def test_a_table_with_no_row_of_an_lsoa_is_refused(tmp_path: Path):
    assert "it holds no row of an LSOA" in str(refused(tmp_path, zipped(table_of({}))))


def test_a_zip_without_the_one_table_is_refused(tmp_path: Path):
    stopped = refused(tmp_path, zipped(table_of(), name="CTSOP1.1/CTSOP1_1_2025_03_31.txt"))
    assert "it does not hold the one file that is read" in str(stopped)


def test_the_table_is_told_from_the_other_tables_of_its_source(tmp_path: Path):
    """The source has three tables. The one of homes by band is asked for by its name."""
    inputs = inputs_with(tmp_path)
    other = zipped(
        table_of(of_msoas={**OF_MSOAS, "E02999001": "9990"}), name="CTSOP3.1/made-up.csv"
    )
    path = tmp_path / "given" / "CTSOP3.1.zip"
    path.write_bytes(other)
    inputs.store.put(homes_density.SOURCE, "CTSOP3.1.zip", path)
    receipt = receipt_of(homes_density.SOURCE, Use.SCORING, "CTSOP3.1.zip", other, "2025")
    both = Inputs(inputs.registry, [*inputs.receipts, receipt], inputs.store, inputs.work)
    found = spine.build(both)
    made = homes_density.build(both, found, land.build(both, found))
    assert made.worked[ONE].value == 50.0
    assert made.stock.file_id != receipt.file_id


# The gate


def without_scoring() -> Registry:
    """The repository's registry, with the table of homes no longer allowed to score."""
    return Registry(
        tuple(
            source.model_copy(update={"uses": (Use.DISPLAY,)})
            if source.id == homes_density.SOURCE
            else source
            for source in registry()
        )
    )


def test_the_gate_is_asked_before_the_table_is_read(tmp_path: Path):
    inputs = inputs_with(tmp_path, registry=without_scoring())
    found = spine.build(inputs)
    measured = land.build(inputs, found)
    before = inputs.opened
    with pytest.raises(LockError) as stopped:
        homes_density.build(inputs, found, measured)
    assert (stopped.value.rule, stopped.value.subject) == ("gate_refuses", homes_density.SOURCE)
    assert inputs.opened == before
    assert not list((tmp_path / "work").rglob(NAME))


def test_a_table_with_no_receipt_is_not_read(tmp_path: Path):
    inputs = inputs_of(tmp_path, contents())
    found = spine.build(inputs)
    with pytest.raises(LockError) as stopped:
        homes_density.build(inputs, found, land.build(inputs, found))
    assert stopped.value.rule == "input_has_one_receipt"


def test_every_source_behind_the_figure_is_registered_for_scoring():
    for source_id in (homes_density.SOURCE, land.BOUNDARIES, spine.LOOKUP):
        assert Use.SCORING in registry().get(source_id).uses
    assert registry().get(homes_density.SOURCE).publisher == homes_density.PUBLISHER
    assert registry().get(land.BOUNDARIES).publisher == homes_density.OF_THE_LAND


# The evidence


def test_every_area_has_a_row_of_evidence_that_names_every_file_behind_it(tmp_path: Path):
    """The table, the boundaries and the lookup. Not the census: nothing is shared out by homes."""
    inputs = inputs_with(tmp_path)
    found = spine.build(inputs)
    made = homes_density.build(inputs, found, land.build(inputs, found))
    assert [row.fact_id for row in made.rows] == [
        f"{area}/feature/homes_density" for area in (ONE, TWO, THREE)
    ]
    behind = {receipt.source_id: receipt for receipt in made.files}
    assert set(behind) == {homes_density.SOURCE, land.BOUNDARIES, spine.LOOKUP}
    first = min(receipt.data_period.days()[0] for receipt in behind.values())
    for row in made.rows:
        assert row.inputs == tuple(sorted(receipt.file_id for receipt in behind.values()))
        assert row.derivation_id == "area_row_ratio@1"
        assert (row.units_used, row.units_expected, row.weight_covered) == (1, 1, 1.0)
        assert (row.state, row.flags) == (State.PRESENT, ROUNDED)
        # From the boundaries the land is measured on to the day of the table.
        assert row.data_period == Period(start=first, end="2025-03-31")
        assert row.retrieved_on == "2026-09-23"


def test_the_rows_name_no_file_the_figure_does_not_rest_on(tmp_path: Path):
    """A build opens the outlines of output areas too, to draw with. No figure rests on them."""
    inputs = inputs_with(tmp_path)
    found = spine.build(inputs)
    drawn = inputs.open("ons-output-areas-2021", Use.CELLS, edition="BGC V2")
    made = homes_density.build(inputs, found, land.build(inputs, found))
    assert drawn.file_id in {one.file_id for one in inputs.opened}
    assert all(drawn.file_id not in row.inputs for row in made.rows)


def test_the_evidence_of_a_release_takes_the_rows_with_no_loose_end(tmp_path: Path):
    made = built(tmp_path)
    evidence = Evidence.of("lon-2026-10-02-01", made.files, homes_density.METHODS, made.rows)
    assert len(evidence.rows) == 3
    assert {method.derivation_id for method in evidence.methods} == {
        "area_row_ratio@1",
        "land_inside_outline@1",
    }
    assert all(method.kind == "measured" for method in evidence.methods)


def test_a_spine_made_from_the_files_of_another_build_is_not_taken(tmp_path: Path):
    other = inputs_of(tmp_path / "other", contents())
    found = spine.build(other)
    measured = land.build(other, found)
    with pytest.raises(ValueError, match="files of this build"):
        homes_density.build(inputs_with(tmp_path / "this"), found, measured)


# The name, the unit and the period


def test_the_name_the_unit_and_which_way_is_more_are_the_ones_core_gives(tmp_path: Path):
    metric = built(tmp_path).metric
    feature = FEATURES[FeatureId.HOMES_DENSITY]
    assert (metric.label, metric.unit) == ("Homes per hectare", "per ha")
    assert (feature.higher, feature.lower) == ("denser", "less dense")
    assert (metric.polarity, metric.native_resolution) == (
        feature.polarity,
        feature.native_resolution,
    )
    assert metric.rankable


def test_every_source_behind_the_figure_is_named_beside_it(tmp_path: Path):
    metric = built(tmp_path).metric
    assert metric.source_ids == (
        "ons-lsoa-2021",
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
        "voa-council-tax-stock-of-properties",
    )


def test_the_definition_says_what_it_is_from_whom_for_when_and_what_it_is_not(tmp_path: Path):
    said = built(tmp_path).metric.definition
    assert said == (
        "Properties on the council tax valuation lists as at 2025-03-31, as the Valuation "
        "Office Agency counts them for the area itself and rounds to 10, not added up from "
        "smaller areas, over the hectares inside the boundaries of the area's small census "
        "areas as at 2021-12, which the Office for National Statistics generalised and cut at "
        "the mean high water mark: the figure is given to 1 decimal place, with a half taken "
        "upward, and every kind of land inside the line is counted, so it is not the density of "
        "the land that homes stand on."
    )
    assert "{" not in said


def test_what_it_cannot_see_is_said_in_one_or_two_sentences():
    assert 1 <= len(homes_density.CANNOT_SEE) <= 2
    for sentence in homes_density.CANNOT_SEE:
        assert sentence.endswith(".") and sentence.count(". ") == 0 and "!" not in sentence
