"""Homes built before 1919, from a made-up table laid out as the publisher lays out its own.

Every figure here is made up. The town is the made-up town of the tests of
cells: three areas, each an MSOA of two LSOAs. The table of homes by build
period has the publisher's own 35 columns, its mark at the start, its row for
each larger area and for each council tax band, and its three ways of writing
a cell. What it holds is made up.

A figure is read from the row of the MSOA, which is the area's own. The rows
of its LSOAs are what that row is held to.

    area             row         before 1900  1900 to 1918  no period  all homes
    Quillhaven 001   E02999001       130           70           0         500
                       E01999001     100           50           0         300
                       E01999002      30           20           0         200
                                     200 of 500 homes is 40 in 100
    Quillhaven 002   E02999002        10            -           -         500
                       E01999003       -            0           0         400
                       E01999004      10            -           -         100
                                     10 of 500 homes is 2 in 100, and marked
    Tallowgate 001   E02999003       200          100         100        1000
                       E01999005     200          100         100         500
                       E01999006       0            0           0         500
                                     300 of the 900 homes with a period is 33.3 in 100,
                                     and 900 of 1,000 homes are covered
"""

import csv
import io
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest
from burro_core.catalogue import FEATURES
from burro_core.ids import FeatureId
from burro_pipeline.cells import spine
from burro_pipeline.derive import homes_pre1919
from burro_pipeline.derive.homes_pre1919 import Counted, Pre1919
from burro_pipeline.derive.methods import AREA_ROW_RATIO, Worked
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind, Method
from burro_pipeline.evidence.receipt import Geography, Period
from burro_pipeline.evidence.row import Flag, State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import CANARY, contents, held, inputs_of, receipt_of, registry, zip_of

NAME = "CTSOP4.1.zip"
TABLE = "CTSOP4.1/CTSOP4_1_2025_03_31.csv"
NOTES = "CTSOP4.1/CTSOP4_1_CSV_table_notes.xlsx"
# The columns of the publisher's table, in its order.
YEARS = tuple(f"bp_{year}" for year in range(2009, 2026))
COLUMNS = (
    "geography",
    "ba_code",
    "ecode",
    "area_name",
    "band",
    "bp_pre_1900",
    "bp_1900_1918",
    "bp_1919_1929",
    "bp_1930_1939",
    "bp_1945_1954",
    "bp_1955_1964",
    "bp_1965_1972",
    "bp_1973_1982",
    "bp_1983_1992",
    "bp_1993_1999",
    "bp_2000_2008",
    *YEARS,
    "bp_unkw",
    "all_properties",
)
ONE, TWO, THREE = "lon-ne02999001", "lon-ne02999002", "lon-ne02999003"
# For each row: before 1900, 1900 to 1918, of no known period, and all homes.
Cells = tuple[str, str, str, str]
LSOAS: Mapping[str, Cells] = {
    "E01999001": ("100", "50", "0", "300"),
    "E01999002": ("30", "20", "0", "200"),
    "E01999003": ("-", "0", "0", "400"),
    "E01999004": ("10", "-", "-", "100"),
    "E01999005": ("200", "100", "100", "500"),
    "E01999006": ("0", "0", "0", "500"),
    # Outside London, and in Wales. Neither is part of any area.
    "E01999901": ("700", "0", "0", "700"),
    "W01999001": ("90", "0", "0", "90"),
}
# The publisher's own row for each MSOA, each count rounded once. A figure is read from it.
MSOAS: Mapping[str, Cells] = {
    "E02999001": ("130", "70", "0", "500"),
    "E02999002": ("10", "-", "-", "500"),
    "E02999003": ("200", "100", "100", "1000"),
    "E02999901": ("700", "0", "0", "700"),
}
# Rows for larger areas, which the table holds beside those for LSOAs and MSOAs. 9990 is
# no count of any LSOA, so a figure made from one of these rows would show.
LARGER = (
    ("ENGWAL", "K04999999"),
    ("NATL", "E92999999"),
    ("REGL", "E12999901"),
    ("CTYMET", "E11999901"),
    ("LAUA", "E09000901"),
    ("UNMD", "UNMATCHED"),
)
BANDS = ("A", "B", "C", "D", "E", "F", "G", "H")
ROUNDED = (Flag.ROUNDED_IN_SOURCE,)
MARKED = (Flag.ROUNDED_IN_SOURCE, Flag.SUPPRESSED_IN_SOURCE)


def table_of(
    lsoas: Mapping[str, Cells] = LSOAS,
    msoas: Mapping[str, Cells] = MSOAS,
    columns: Sequence[str] = COLUMNS,
    twice: Sequence[str] = (),
) -> bytes:
    """The table of homes by build period, as the publisher writes it: a mark, and LF."""
    text = io.StringIO(newline="")
    table = csv.DictWriter(text, columns, extrasaction="ignore", lineterminator="\n")
    table.writeheader()
    rows = [(kind, code, ("9990", "9990", "9990", "9990")) for kind, code in LARGER]
    rows += [("MSOA", code, cells) for code, cells in msoas.items()]
    rows += [("LSOA", code, cells) for code, cells in lsoas.items()]
    rows += [("LSOA", code, lsoas[code]) for code in twice]
    for kind, code, cells in rows:
        bands = ("All", *BANDS, "I") if code.startswith("W") else ("All", *BANDS)
        for band in bands:
            # The row of one band holds 990 for every period: no figure is made from one.
            old, later, unknown, homes = cells if band == "All" else ("990", "990", "990", "990")
            table.writerow(
                dict.fromkeys(COLUMNS, "10")
                | {"geography": kind, "ecode": code, "area_name": CANARY, "band": band}
                | {"ba_code": "9901" if kind == "LAUA" else "N/A"}
                | {"bp_pre_1900": old, "bp_1900_1918": later}
                | {"bp_unkw": unknown, "all_properties": homes}
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
    given.store.put(homes_pre1919.SOURCE, NAME, path)
    receipt = receipt_of(homes_pre1919.SOURCE, Use.SCORING, NAME, content, "2025").model_copy(
        update={"data_period": Period(as_at=as_at)}
    )
    return Inputs(given.registry, [*given.receipts, receipt], given.store, given.work)


def built(
    folder: Path, lsoas: Mapping[str, Cells] = LSOAS, msoas: Mapping[str, Cells] = MSOAS
) -> Pre1919:
    inputs = inputs_with(folder, zipped(table_of(lsoas, msoas)))
    return homes_pre1919.build(inputs, spine.build(inputs))


def refused(folder: Path, table: bytes, as_at: str = "2025-03-31") -> LockError:
    """The refusal of a table, which repeats nothing the table holds."""
    inputs = inputs_with(folder, table, as_at)
    found = spine.build(inputs)
    with pytest.raises(LockError) as stopped:
        homes_pre1919.build(inputs, found)
    assert stopped.value.rule == "input_is_as_described"
    assert CANARY not in str(stopped.value)
    assert str(folder) not in str(stopped.value)
    return stopped.value


# The figure


def test_the_share_is_the_old_homes_of_an_area_over_its_homes_that_have_a_period(tmp_path: Path):
    found = built(tmp_path).worked
    assert found == {
        ONE: Worked(40.0, 1, 1, 1.0, State.PRESENT, ROUNDED),
        TWO: Worked(2.0, 1, 1, 1.0, State.PRESENT, MARKED),
        THREE: Worked(33.3, 1, 1, 0.9, State.PARTIAL, ROUNDED),
    }


def test_the_figure_is_read_from_the_areas_own_row_and_not_added_up_from_its_lsoas(
    tmp_path: Path,
):
    """The LSOAs of Quillhaven 001 add up to 210 old homes of 500, which is 42 in 100.

    The publisher's own row for the area holds 130 and 70 of 500. Rounding
    lets the two differ, and the row is the one a reader finds in the table.
    """
    more = {**LSOAS, "E01999001": ("100", "60", "0", "300")}
    assert built(tmp_path, more).worked[ONE].value == 40.0


def test_the_two_periods_before_1919_are_added_and_no_later_one_is(tmp_path: Path):
    """Every later period of the made-up table holds 10 homes, and none is counted."""
    found = built(tmp_path).stock.of_msoa["E02999001"]
    assert found == Counted(before_1900=130, from_1900=70, not_known=0, homes=500)
    assert found.before_1919 == 200


def test_a_share_is_given_to_one_decimal_place(tmp_path: Path):
    assert built(tmp_path).worked[THREE].value == 33.3


def test_a_share_that_stands_on_a_half_is_rounded_upward(tmp_path: Path):
    """10 old homes of 800 is 1.25 in 100, which a person who rounds by hand gives as 1.3."""
    half = {
        **LSOAS,
        "E01999001": ("10", "0", "0", "400"),
        "E01999002": ("0", "0", "0", "400"),
    }
    found = built(tmp_path, half, {**MSOAS, "E02999001": ("10", "0", "0", "800")})
    assert found.worked[ONE].value == 1.3


def test_a_count_of_nought_is_a_count(tmp_path: Path):
    none = {**LSOAS, "E01999001": ("0", "0", "0", "300"), "E01999002": ("0", "0", "0", "200")}
    found = built(tmp_path, none, {**MSOAS, "E02999001": ("0", "0", "0", "500")}).worked[ONE]
    assert found == Worked(0.0, 1, 1, 1.0, State.PRESENT, ROUNDED)


def test_only_the_rows_for_all_bands_of_an_msoa_and_an_lsoa_are_read(tmp_path: Path):
    """A row of one band holds 990, and a row of a larger area 9990. Neither is counted."""
    found = built(tmp_path)
    assert set(found.stock.of_lsoa) == set(LSOAS)
    assert set(found.stock.of_msoa) == set(MSOAS)
    # 6 larger areas, 4 MSOAs and 7 English LSOAs have 9 rows each, and the Welsh LSOA has 10.
    assert found.stock.rows == 9 * (6 + 4 + 7) + 10
    assert all(one.homes != 990 for one in found.stock.of_lsoa.values())
    assert all(one.homes not in (990, 9990) for one in found.stock.of_msoa.values())


# A count too small to round


def test_a_dash_beside_a_count_adds_nothing_and_marks_the_figure(tmp_path: Path):
    found = built(tmp_path)
    assert found.stock.of_msoa["E02999002"].from_1900 is None
    assert found.stock.of_msoa["E02999002"].old_withheld
    assert found.worked[TWO] == Worked(2.0, 1, 1, 1.0, State.PRESENT, MARKED)


@pytest.mark.parametrize(
    ("own", "parts"),
    [
        # A dash for both periods: the area has 2 to 8 old homes.
        (("-", "-", "0", "500"), (("-", "-", "0", "400"), ("0", "0", "0", "100"))),
        # A dash for one period and nought for the other: the area has 1 to 4.
        (("-", "0", "0", "500"), (("-", "0", "0", "400"), ("-", "0", "0", "100"))),
        (("0", "-", "0", "500"), (("0", "0", "0", "400"), ("0", "-", "0", "100"))),
    ],
)
def test_old_homes_that_are_all_too_small_to_round_are_never_said_to_be_nought(
    tmp_path: Path, own: Cells, parts: tuple[Cells, Cells]
):
    """The share is above nought and the file does not say what it is, so none is given."""
    lsoas = {**LSOAS, "E01999003": parts[0], "E01999004": parts[1]}
    found = built(tmp_path, lsoas, {**MSOAS, "E02999002": own})
    assert found.worked[TWO] == Worked(None, 0, 1, 0.0, State.SUPPRESSED, MARKED)
    row = next(row for row in found.rows if row.area_id == TWO)
    assert (row.state, row.has_a_value, row.flags) == (State.SUPPRESSED, False, MARKED)


def test_an_area_with_no_old_home_at_all_is_said_to_have_none_and_is_not_marked(
    tmp_path: Path,
):
    lsoas = {
        **LSOAS,
        "E01999003": ("0", "0", "0", "400"),
        "E01999004": ("0", "0", "0", "100"),
    }
    found = built(tmp_path, lsoas, {**MSOAS, "E02999002": ("0", "0", "0", "500")})
    assert found.worked[TWO] == Worked(0.0, 1, 1, 1.0, State.PRESENT, ROUNDED)


def test_a_dash_for_homes_of_no_known_period_does_not_mark_the_figure(tmp_path: Path):
    """It moves the bottom by at most 4 homes, which is less than rounding does."""
    lsoas = {**LSOAS, "E01999002": ("30", "20", "-", "200")}
    found = built(tmp_path, lsoas, {**MSOAS, "E02999001": ("130", "70", "-", "500")})
    assert found.worked[ONE] == Worked(40.0, 1, 1, 1.0, State.PRESENT, ROUNDED)


def test_a_dash_in_the_row_of_an_lsoa_does_not_mark_a_figure_read_from_its_msoa(
    tmp_path: Path,
):
    lsoas = {**LSOAS, "E01999002": ("30", "-", "0", "200")}
    found = built(tmp_path, lsoas, {**MSOAS, "E02999001": ("130", "50", "0", "500")})
    assert found.worked[ONE] == Worked(36.0, 1, 1, 1.0, State.PRESENT, ROUNDED)


# The row of an area is held to the rows of its LSOAs


def test_the_row_of_every_area_is_held_to_the_rows_of_its_lsoas(tmp_path: Path):
    assert built(tmp_path).rows_held == 3


@pytest.mark.parametrize(
    ("own", "words"),
    [
        # The MSOA holds 50 homes of before 1900, and its LSOAs hold a dash and 10.
        (("50", "-", "-", "500"), "an area's count is not within rounding of its parts"),
        # The MSOA holds a dash, and one of its LSOAs a number.
        (("-", "-", "-", "500"), "a dash hides more than a small count"),
        # The MSOA holds nought, and one of its LSOAs a dash.
        (("10", "0", "-", "500"), "an area holds nought and a part of it does not"),
        (("10", "-", "-", "700"), "an area's count is not within rounding of its parts"),
    ],
)
def test_a_row_that_is_not_what_the_rows_of_its_lsoas_allow_stops_the_build(
    tmp_path: Path, own: Cells, words: str
):
    table = zipped(table_of(msoas={**MSOAS, "E02999002": own}))
    assert words in str(refused(tmp_path, table))


def test_a_count_where_no_lsoa_holds_one_stops_the_build(tmp_path: Path):
    table = zipped(table_of(msoas={**MSOAS, "E02999001": ("130", "70", "10", "500")}))
    assert "an area holds a count and no part of it does" in str(refused(tmp_path, table))


def test_an_area_with_no_row_of_its_own_stops_the_build(tmp_path: Path):
    fewer = {code: cells for code, cells in MSOAS.items() if code != "E02999002"}
    error = refused(tmp_path, zipped(table_of(msoas=fewer)))
    assert "an MSOA of the census of 2021 has no row" in str(error)


# Homes of no known period


def test_a_home_of_no_known_period_is_left_out_and_lowers_the_coverage(tmp_path: Path):
    """Counted as not old, the 100 homes of no period would make the share 30 in 100."""
    found = built(tmp_path).worked[THREE]
    assert found == Worked(33.3, 1, 1, 0.9, State.PARTIAL, ROUNDED)


def test_with_under_half_the_homes_of_known_period_no_figure_is_given(tmp_path: Path):
    unknown = {
        **LSOAS,
        "E01999005": ("200", "0", "300", "500"),
        "E01999006": ("0", "0", "300", "500"),
    }
    found = built(tmp_path, unknown, {**MSOAS, "E02999003": ("200", "0", "600", "1000")})
    assert found.worked[THREE] == Worked(None, 1, 1, 0.4, State.BELOW_THRESHOLD, ROUNDED)
    row = next(row for row in found.rows if row.area_id == THREE)
    assert (row.state, row.weight_covered) == (State.BELOW_THRESHOLD, 0.4)


def test_an_area_where_no_home_has_a_period_has_no_figure_and_none_is_made_up(tmp_path: Path):
    unknown = {
        **LSOAS,
        "E01999005": ("0", "0", "500", "500"),
        "E01999006": ("0", "0", "500", "500"),
    }
    found = built(tmp_path, unknown, {**MSOAS, "E02999003": ("0", "0", "1000", "1000")})
    assert found.worked[THREE] == Worked(None, 0, 1, 0.0, State.SOURCE_GAP, ROUNDED)


# An area with no count of its homes


def test_an_area_with_no_count_of_all_its_homes_is_said_to_be_withheld(tmp_path: Path):
    none = {**LSOAS, "E01999001": ("0", "0", "0", "-"), "E01999002": ("0", "0", "0", "-")}
    found = built(tmp_path, none, {**MSOAS, "E02999001": ("0", "0", "0", "-")}).worked[ONE]
    assert found == Worked(None, 0, 1, 0.0, State.SUPPRESSED, MARKED)


def test_an_area_with_no_home_has_no_figure_and_is_never_nought(tmp_path: Path):
    none = {**LSOAS, "E01999001": ("0", "0", "0", "0"), "E01999002": ("0", "0", "0", "0")}
    found = built(tmp_path, none, {**MSOAS, "E02999001": ("0", "0", "0", "0")}).worked[ONE]
    assert found == Worked(None, 0, 1, 0.0, State.SOURCE_GAP, ROUNDED)


def test_a_share_that_is_more_than_the_whole_stops_the_build(tmp_path: Path):
    """Each count is rounded by itself. No figure is cut to fit."""
    over = {
        **LSOAS,
        "E01999001": ("300", "10", "0", "300"),
        "E01999002": ("200", "0", "0", "200"),
    }
    table = zipped(table_of(over, {**MSOAS, "E02999001": ("500", "10", "0", "500")}))
    assert "more than the whole" in str(refused(tmp_path, table))


# Which census the codes follow


def test_the_rows_a_figure_is_read_from_are_found_to_be_on_the_msoas_of_2021(tmp_path: Path):
    assert built(tmp_path).geography is Geography.MSOA21


def test_a_table_that_lacks_an_lsoa_of_the_spine_stops_the_build(tmp_path: Path):
    """A table on the codes of another census lacks every LSOA that was drawn again."""
    fewer = {code: cells for code, cells in LSOAS.items() if code != "E01999004"}
    error = refused(tmp_path, zipped(table_of(fewer)))
    assert "an LSOA of the census of 2021 has no row" in str(error)


def test_an_area_outside_london_is_read_and_is_part_of_no_figure(tmp_path: Path):
    found = built(tmp_path)
    assert found.stock.of_lsoa["E01999901"].homes == 700
    assert found.stock.of_msoa["E02999901"].homes == 700
    assert set(found.worked) == {ONE, TWO, THREE}


# What stops the build


@pytest.mark.parametrize("missing", homes_pre1919.COLUMNS)
def test_a_table_that_lacks_a_column_stops_the_build_and_says_which(tmp_path: Path, missing: str):
    columns = [name for name in COLUMNS if name != missing]
    error = refused(tmp_path, zipped(table_of(columns=columns)))
    assert f"the column {missing} is missing" in str(error)


def test_a_table_needs_no_column_that_is_not_read(tmp_path: Path):
    """A year that is gone, or one more, changes no figure: no year is before 1919."""
    fewer = [name for name in COLUMNS if name not in ("bp_2024", "area_name", "ba_code")]
    more = [*COLUMNS[:-2], "bp_2026", *COLUMNS[-2:]]
    whole = built(tmp_path / "whole").worked
    for case, columns in (("fewer", fewer), ("more", more)):
        inputs = inputs_with(tmp_path / case, zipped(table_of(columns=columns)))
        assert homes_pre1919.build(inputs, spine.build(inputs)).worked == whole


@pytest.mark.parametrize(
    "change",
    [
        {"bp_1919_1929": "bp_1910_1929"},
        {"bp_1930_1939": "bp_1850_1899"},
        {"bp_2000_2008": "bp_2000_2009"},
    ],
)
def test_a_build_period_the_step_does_not_know_stops_the_build(
    tmp_path: Path, change: Mapping[str, str]
):
    """A period that is new may end before 1919, and the two that are added would miss it."""
    columns = [change.get(name, name) for name in COLUMNS]
    error = refused(tmp_path, zipped(table_of(columns=columns)))
    assert "a build period is not one the step knows" in str(error)


@pytest.mark.parametrize(
    ("cells", "words"),
    [
        ((CANARY, "0", "0", "300"), "a count is not a count"),
        (("100", "", "0", "300"), "a count is not a count"),
        (("100", "50", "..", "300"), "a count is not a count"),
        (("100", "50", "0", "-300"), "a count is not a count"),
        (("100", "50", "0", "3e2"), "a count is not a count"),
        (("100", "50", "0", "304"), "a count is not rounded to 10"),
        (("104", "50", "0", "300"), "a count is not rounded to 10"),
    ],
)
def test_a_cell_that_cannot_be_read_stops_the_build(tmp_path: Path, cells: Cells, words: str):
    error = refused(tmp_path, zipped(table_of({**LSOAS, "E01999001": cells})))
    assert words in str(error)


@pytest.mark.parametrize("cells", [(CANARY, "0", "0", "500"), ("130", "70", "0", "504")])
def test_a_cell_of_the_row_of_an_msoa_that_cannot_be_read_stops_the_build(
    tmp_path: Path, cells: Cells
):
    error = refused(tmp_path, zipped(table_of(msoas={**MSOAS, "E02999001": cells})))
    assert "a count is not" in str(error)


def test_a_code_that_is_not_a_code_stops_the_build(tmp_path: Path):
    error = refused(tmp_path, zipped(table_of({**LSOAS, "Zzyzx-001": ("0", "0", "0", "10")})))
    assert "a code is not a code" in str(error)
    assert "Zzyzx" not in str(error)


def test_an_lsoa_that_is_there_twice_stops_the_build(tmp_path: Path):
    assert "twice" in str(refused(tmp_path, zipped(table_of(twice=["E01999002"]))))


def test_a_table_with_no_row_of_an_lsoa_stops_the_build(tmp_path: Path):
    assert "no row of an LSOA" in str(refused(tmp_path, zipped(table_of({}))))


def test_a_table_with_no_row_of_an_msoa_stops_the_build(tmp_path: Path):
    assert "no row of an MSOA" in str(refused(tmp_path, zipped(table_of(msoas={}))))


@pytest.mark.parametrize(
    "name", ["CTSOP4.1/CTSOP4_1.csv", "CTSOP4.1/CTSOP4_1_2025_13_31.csv", "CTSOP4.1/homes.csv"]
)
def test_a_table_that_is_not_named_for_a_day_stops_the_build(tmp_path: Path, name: str):
    assert "not named for a day" in str(refused(tmp_path, zipped(table_of(), name)))


def test_a_table_of_another_day_than_its_receipt_gives_stops_the_build(tmp_path: Path):
    error = refused(tmp_path, zipped(table_of()), as_at="2024-03-31")
    assert "not of the day its receipt gives" in str(error)


def test_a_zip_with_two_tables_stops_the_build(tmp_path: Path):
    two = zip_of({TABLE: table_of(), "CTSOP4.1/CTSOP4_1_2024_03_31.csv": table_of()})
    assert "the one file" in str(refused(tmp_path, two))


# The gate, and what is read


def without_scoring() -> Registry:
    """The repository's registry, with the table of homes no longer registered for scoring."""
    sources = [
        source.model_copy(update={"uses": (Use.DISPLAY,)})
        if source.id == homes_pre1919.SOURCE
        else source
        for source in registry()
    ]
    return Registry(tuple(sources))


def test_the_gate_is_asked_before_the_table_is_read(tmp_path: Path):
    inputs = inputs_with(tmp_path, registry=without_scoring())
    found = spine.build(inputs)
    with pytest.raises(LockError) as stopped:
        homes_pre1919.build(inputs, found)
    assert stopped.value.rule == "gate_refuses"
    assert all(one.receipt.source_id != homes_pre1919.SOURCE for one in inputs.opened)


def test_the_table_is_registered_for_scoring_in_the_repositorys_registry():
    source = registry().get(homes_pre1919.SOURCE)
    assert Use.SCORING in source.uses
    assert source.dimension == "housing"


def test_a_table_of_another_name_is_not_taken_for_this_one(tmp_path: Path):
    """The source has three tables. The one read is the one by build period."""
    given = inputs_with(tmp_path)
    other = [
        receipt.model_copy(update={"publisher_file": "CTSOP3.1.zip"})
        if receipt.source_id == homes_pre1919.SOURCE
        else receipt
        for receipt in given.receipts
    ]
    inputs = Inputs(given.registry, other, given.store, given.work)
    with pytest.raises(LockError) as stopped:
        homes_pre1919.build(inputs, spine.build(inputs))
    assert stopped.value.rule == "input_has_one_receipt"


def test_nothing_is_written_to_the_store(tmp_path: Path):
    inputs = inputs_with(tmp_path)
    before = held(tmp_path / "store")
    homes_pre1919.build(inputs, spine.build(inputs))
    assert held(tmp_path / "store") == before


def test_the_same_files_give_the_same_figures(tmp_path: Path):
    first, second = built(tmp_path / "a"), built(tmp_path / "b")
    assert (first.worked, first.rows, first.metric) == (second.worked, second.rows, second.metric)


def test_a_spine_of_another_build_is_refused(tmp_path: Path):
    other = spine.build(inputs_of(tmp_path / "other", contents()))
    inputs = inputs_with(tmp_path / "this")
    with pytest.raises(ValueError, match="files of this build"):
        homes_pre1919.build(inputs, other)


# The evidence


def test_every_area_has_a_row_of_evidence_whether_or_not_it_has_a_figure(tmp_path: Path):
    none = {**LSOAS, "E01999001": ("0", "0", "0", "-"), "E01999002": ("0", "0", "0", "-")}
    found = built(tmp_path, none, {**MSOAS, "E02999001": ("0", "0", "0", "-")})
    assert [row.fact_id for row in found.rows] == [
        f"{area}/feature/homes_pre1919" for area in (ONE, TWO, THREE)
    ]
    assert [row.state for row in found.rows] == [
        State.SUPPRESSED,
        State.PRESENT,
        State.PARTIAL,
    ]
    assert [row.has_a_value for row in found.rows] == [False, True, True]


def test_a_row_names_the_table_and_the_lookup_and_not_the_census(tmp_path: Path):
    """Nothing is shared out by homes while the figure is the area's own row."""
    inputs = inputs_with(tmp_path)
    found = homes_pre1919.build(inputs, spine.build(inputs))
    sources = {receipt.source_id: receipt.file_id for receipt in found.files}
    assert set(sources) == {homes_pre1919.SOURCE, spine.LOOKUP}
    lookup = next(receipt for receipt in found.files if receipt.source_id == spine.LOOKUP)
    for row in found.rows:
        assert set(row.inputs) == set(sources.values())
        assert row.derivation_id == AREA_ROW_RATIO.derivation_id
        assert (row.units_used, row.units_expected) == (1, 1)
        assert row.retrieved_on == "2026-09-23"
        # From the lookup, which says which MSOA an area is, to the day the table is of.
        assert row.data_period == Period(start=lookup.data_period.days()[0], end="2025-03-31")
    assert found.stock.file_id == sources[homes_pre1919.SOURCE]


def test_a_row_carries_the_coverage_the_state_and_the_flags_of_its_figure(tmp_path: Path):
    rows = {row.area_id: row for row in built(tmp_path).rows}
    assert (rows[TWO].state, rows[TWO].weight_covered, rows[TWO].flags) == (
        State.PRESENT,
        1.0,
        MARKED,
    )
    assert (rows[THREE].state, rows[THREE].weight_covered, rows[THREE].flags) == (
        State.PARTIAL,
        0.9,
        ROUNDED,
    )


def test_the_evidence_of_the_measure_has_no_loose_end(tmp_path: Path):
    found = built(tmp_path)
    evidence = Evidence.of("lon-2026-09-23-01", found.files, homes_pre1919.METHODS, found.rows)
    assert len(evidence.rows) == 3
    assert evidence.sources_of(evidence.rows[0]) == {receipt.source_id for receipt in found.files}
    method = evidence.method(found.rows[0].derivation_id or "")
    assert method is not None and method.kind is Kind.MEASURED


# The name, the unit and the period


def test_the_name_the_unit_and_which_way_is_more_are_core_s(tmp_path: Path):
    metric = built(tmp_path).metric
    feature = FEATURES[FeatureId.HOMES_PRE1919]
    assert (metric.label, metric.unit) == ("Homes built before 1919", "%")
    assert (metric.label, metric.unit, metric.polarity, metric.dimension) == (
        feature.label,
        feature.unit,
        feature.polarity,
        feature.dimension,
    )
    assert (feature.higher, feature.lower) == ("more", "fewer")
    assert metric.native_resolution == "lsoa"


def test_the_period_is_the_day_the_table_is_of(tmp_path: Path):
    found = built(tmp_path)
    assert found.stock.as_at == found.metric.vintage == "2025-03-31"


def test_the_measure_names_every_source_a_figure_rests_on(tmp_path: Path):
    assert built(tmp_path).metric.source_ids == (spine.LOOKUP, homes_pre1919.SOURCE)


def test_the_definition_is_one_sentence_that_states_what_it_is_made_with(tmp_path: Path):
    """It is held to the rule of a method's sentence: one sentence, every number in it."""
    definition = built(tmp_path).metric.definition
    stated = Method(
        derivation_id="homes_pre1919@1",
        sentence=definition,
        kind=Kind.MEASURED,
        parameters={"built_before": 1919, "rounded_to": 10, "decimal_places": 1},
        code="burro_pipeline.derive.homes_pre1919",
    )
    assert stated.sentence == definition
    for words in ("Valuation Office Agency", "2025-03-31", "no recorded build period", "not"):
        assert words in definition
    # What the share is a share of: the two counts that are taken from each other.
    assert "its count of all homes less its count of homes of no recorded build period" in (
        definition
    )


def test_the_definition_makes_plain_that_the_count_is_the_publishers_own_for_the_area(
    tmp_path: Path,
):
    """So that a reader who opens the publisher's table for the area finds the same counts."""
    definition = built(tmp_path).metric.definition
    for words in (
        "the publisher's own for the area",
        "not added up from smaller areas",
        "with a half taken upward",
        "no figure is given",
    ):
        assert words in definition


def test_what_it_cannot_see_is_two_sentences_that_name_no_place():
    assert len(homes_pre1919.CANNOT_SEE) == 2
    for line in homes_pre1919.CANNOT_SEE:
        assert line.endswith(".") and line.count(". ") == 0
        assert "London" not in line


# The made-up table


def test_the_made_up_table_has_the_columns_the_publishers_has():
    header = table_of().splitlines()[0]
    assert header == b"\xef\xbb\xbf" + ",".join(COLUMNS).encode()
    assert len(COLUMNS) == 35
    assert set(homes_pre1919.COLUMNS) <= set(COLUMNS)
    assert tuple(name for name in COLUMNS[5:16]) == homes_pre1919.PERIODS
