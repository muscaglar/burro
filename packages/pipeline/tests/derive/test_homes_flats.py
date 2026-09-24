"""Flats as a share of homes, from a made-up table laid out as the publisher lays out its own.

Every figure here is made up. The town is the made-up town of the tests of
cells: three areas, each an MSOA of two LSOAs. The table of homes by kind has
the publisher's own 49 columns, its mark at the start, its rows for larger
areas and for single bands, and its three ways of writing a cell. What it
holds is made up.

A figure is read from the row of the MSOA, which is the area's own. The rows
of its LSOAs are what that row is held to.

    area             row           flats   no kind   homes
    Quillhaven 001   E02999001        80      -        200    80 of 200 is 40
                       E01999001      60      0        120
                       E01999002      20      -         80
    Quillhaven 002   E02999002        30     10        600    30 of 600 is 5
                       E01999003      30     10         60
                       E01999004       -      0        540
    Tallowgate 001   E02999003       300      0        400    300 of 400 is 75
                       E01999005     300      0        300
                       E01999006       0      0        100
"""

import csv
import io
import re
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest
from burro_core.catalogue import FEATURES
from burro_core.ids import FeatureId
from burro_pipeline.cells import spine
from burro_pipeline.derive import homes_flats
from burro_pipeline.derive.homes_flats import Counted, Flats, Stock
from burro_pipeline.derive.methods import Worked, to_places
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.receipt import Geography, Period
from burro_pipeline.evidence.row import Flag, State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import CANARY, contents, held, inputs_of, receipt_of, registry, zip_of

NAME = "CTSOP3.1.zip"
TABLE = "CTSOP3.1/CTSOP3_1_2025_03_31.csv"
NOTES = "CTSOP3.1/CTSOP3_1_CSV_table_notes.xlsx"
KINDS = ("bungalow", "flat_mais", "house_terraced", "house_semi", "house_detached")
SIZES = ("1", "2", "3", "4", "5", "6", "unkw", "total")
# The columns of the publisher's table, in its order.
COLUMNS = (
    "geography",
    "ba_code",
    "ecode",
    "area_name",
    "band",
    *(f"{kind}_{size}" for kind in KINDS for size in SIZES),
    "annexe",
    "caravan_houseboat_mobilehome",
    "unknown",
    "all_properties",
)
BANDS = ("All", "A", "B", "C", "D", "E", "F", "G", "H")
ONE, TWO, THREE = "lon-ne02999001", "lon-ne02999002", "lon-ne02999003"
# No count of any row that is read. A figure made from a cell that is not read would show it.
NEVER = "9990"

# For each row: its flats, its homes of no known kind, and all its homes.
Cells = tuple[str, str, str]
HOMES: Mapping[str, Cells] = {
    "E01999001": ("60", "0", "120"),
    "E01999002": ("20", "-", "80"),
    "E01999003": ("30", "10", "60"),
    "E01999004": ("-", "0", "540"),
    "E01999005": ("300", "0", "300"),
    "E01999006": ("0", "0", "100"),
    # Outside London, and in Wales. Neither is part of any area.
    "E01999901": ("700", "0", "700"),
    "W01999001": ("90", "0", "90"),
}
# The publisher's own row for each MSOA, each count rounded once. A figure is read from it.
OF_MSOAS: Mapping[str, Cells] = {
    "E02999001": ("80", "-", "200"),
    "E02999002": ("30", "10", "600"),
    "E02999003": ("300", "0", "400"),
    "E02999901": ("700", "0", "700"),
}
# Rows for larger areas, which the table holds beside those for LSOAs and MSOAs.
LARGER = (
    ("ENGWAL", "K04999999"),
    ("NATL", "E92999999"),
    ("REGL", "E12999901"),
    ("CTYMET", "E11999901"),
    ("LAUA", "E09000901"),
    ("UNMD", "UNMATCHED"),
)


def table_of(
    homes: Mapping[str, Cells] = HOMES,
    of_msoas: Mapping[str, Cells] = OF_MSOAS,
    columns: Sequence[str] = COLUMNS,
    twice: Sequence[str] = (),
    turned: bool = False,
) -> bytes:
    """The table of homes by kind, as the publisher writes it: a mark at the start, and LF."""
    text = io.StringIO(newline="")
    table = csv.DictWriter(text, columns, extrasaction="ignore", lineterminator="\n")
    table.writeheader()
    rows = [(kind, code, (NEVER, NEVER, NEVER)) for kind, code in LARGER]
    rows += [("MSOA", code, cells) for code, cells in of_msoas.items()]
    rows += [("LSOA", code, cells) for code, cells in homes.items()]
    rows += [("LSOA", code, homes[code]) for code in twice if code in homes]
    rows += [("MSOA", code, of_msoas[code]) for code in twice if code in of_msoas]
    for kind, code, (flats, not_known, every) in reversed(rows) if turned else rows:
        for band in BANDS:
            # A row for one band holds what is never read. So does every other kind of home.
            read = band == "All"
            table.writerow(
                dict.fromkeys(COLUMNS[5:], NEVER)
                | {"geography": kind, "ba_code": "N/A", "ecode": code, "area_name": CANARY}
                | {"band": band, "flat_mais_total": flats if read else NEVER}
                | {"unknown": not_known if read else NEVER}
                | {"all_properties": every if read else NEVER}
            )
    return b"\xef\xbb\xbf" + text.getvalue().encode()


def zipped(table: bytes, name: str = TABLE) -> bytes:
    # The notes are a workbook. No step opens them, so these are not one.
    return zip_of({name: table, NOTES: CANARY})


def inputs_with(
    folder: Path,
    table: bytes | None = None,
    as_at: str = "2025-03-31",
    **changes: Registry,
) -> Inputs:
    """The made-up build of the tests of cells, and the table of homes by kind beside it."""
    given = inputs_of(folder, contents(), **changes)
    content = zipped(table_of()) if table is None else table
    path = folder / "given" / NAME
    path.write_bytes(content)
    given.store.put(homes_flats.SOURCE, NAME, path)
    receipt = receipt_of(homes_flats.SOURCE, Use.SCORING, NAME, content, "2025").model_copy(
        update={"data_period": Period(as_at=as_at)}
    )
    return Inputs(given.registry, [*given.receipts, receipt], given.store, given.work)


def built(
    folder: Path, homes: Mapping[str, Cells] = HOMES, of_msoas: Mapping[str, Cells] = OF_MSOAS
) -> Flats:
    inputs = inputs_with(folder, zipped(table_of(homes, of_msoas)))
    return homes_flats.build(inputs, spine.build(inputs))


def refused(folder: Path, table: bytes, as_at: str = "2025-03-31") -> LockError:
    """The refusal of a table, which repeats nothing the table holds."""
    inputs = inputs_with(folder, table, as_at)
    found = spine.build(inputs)
    with pytest.raises(LockError) as stopped:
        homes_flats.build(inputs, found)
    assert stopped.value.rule == "input_is_as_described"
    assert CANARY not in str(stopped.value)
    assert NEVER not in str(stopped.value)
    assert str(folder) not in str(stopped.value)
    return stopped.value


def with_cell(code: str, which: int, cell: str) -> dict[str, Cells]:
    """The made-up counts, with one cell of one LSOA written another way."""
    cells = list(HOMES.get(code, ("10", "0", "10")))
    cells[which] = cell
    return {**HOMES, code: (cells[0], cells[1], cells[2])}


def with_row(code: str, flats: str, not_known: str, homes: str) -> dict[str, Cells]:
    """The made-up rows of the MSOAs, with the row of one written another way."""
    return {**OF_MSOAS, code: (flats, not_known, homes)}


FLATS, NOT_KNOWN, EVERY = 0, 1, 2
ROUNDED = (Flag.ROUNDED_IN_SOURCE,)
TOO_SMALL = (Flag.ROUNDED_IN_SOURCE, Flag.SUPPRESSED_IN_SOURCE)


# The figure


def test_the_share_is_the_flats_of_an_area_over_all_its_homes(tmp_path: Path):
    assert built(tmp_path).worked == {
        ONE: Worked(40.0, 1, 1, 1.0, State.PRESENT, ROUNDED),
        TWO: Worked(5.0, 1, 1, 1.0, State.PRESENT, ROUNDED),
        THREE: Worked(75.0, 1, 1, 1.0, State.PRESENT, ROUNDED),
    }


def test_the_figure_is_read_from_the_areas_own_row_and_not_added_up_from_its_lsoas(
    tmp_path: Path,
):
    """The LSOAs of Quillhaven 001 add up to 90 flats of 200 homes, which is 45 in 100.

    The publisher's own row for the area holds 80 of 200. Rounding lets the
    two differ, and the row is the one a reader finds in the table.
    """
    more = with_cell("E01999001", FLATS, "70")
    assert built(tmp_path, more).worked[ONE].value == 40.0


def test_a_count_of_nought_is_a_count(tmp_path: Path):
    none = with_cell("E01999005", FLATS, "0")
    found = built(tmp_path, none, with_row("E02999003", "0", "0", "400")).worked[THREE]
    assert found == Worked(0.0, 1, 1, 1.0, State.PRESENT, ROUNDED)


def test_every_home_may_be_a_flat(tmp_path: Path):
    every = with_cell("E01999006", FLATS, "100")
    found = built(tmp_path, every, with_row("E02999003", "400", "0", "400")).worked[THREE]
    assert found == Worked(100.0, 1, 1, 1.0, State.PRESENT, ROUNDED)


def test_a_figure_is_given_to_one_decimal_place(tmp_path: Path):
    """A count is rounded to 10 by its publisher, so a second decimal place would say nothing."""
    homes = {**HOMES, "E01999001": ("10", "0", "20"), "E01999002": ("0", "0", "10")}
    # 10 flats of 30 homes, which is 33.333333.
    assert built(tmp_path, homes, with_row("E02999001", "10", "0", "30")).worked[ONE].value == 33.3


def test_a_share_that_stands_on_a_half_is_rounded_upward(tmp_path: Path):
    """10 flats of 800 homes is 1.25 in 100, which a person who rounds by hand gives as 1.3."""
    homes = {**HOMES, "E01999001": ("10", "0", "400"), "E01999002": ("0", "0", "400")}
    assert built(tmp_path, homes, with_row("E02999001", "10", "0", "800")).worked[ONE].value == 1.3


def test_the_order_of_the_rows_changes_nothing(tmp_path: Path):
    inputs = inputs_with(tmp_path, zipped(table_of(turned=True)))
    turned = homes_flats.build(inputs, spine.build(inputs))
    assert turned.worked == built(tmp_path / "plain").worked


def test_a_share_that_is_more_than_the_whole_stops_the_build(tmp_path: Path):
    """No figure is cut to fit. More flats than homes is a table a person must look at."""
    homes = {**HOMES, "E01999001": ("200", "0", "120"), "E01999002": ("100", "0", "80")}
    stopped = refused(tmp_path, zipped(table_of(homes, with_row("E02999001", "300", "0", "200"))))
    assert "a share is more than the whole" in str(stopped)


# A dash: a count too small to round


@pytest.mark.parametrize("other", ["-", "0"])
def test_flats_that_are_too_small_to_round_are_never_said_to_be_nought(tmp_path: Path, other: str):
    """A dash is a count that is not nought. So an area whose row holds one has flats.

    The share is above nought and the file does not say what it is, so none is given.
    """
    homes = {**HOMES, "E01999003": (other, "10", "60")}
    made = built(tmp_path, homes, with_row("E02999002", "-", "10", "600"))
    assert made.worked[TWO] == Worked(None, 0, 1, 0.0, State.SUPPRESSED, TOO_SMALL)
    (row,) = [row for row in made.rows if row.area_id == TWO]
    assert (row.state, row.has_a_value, row.flags) == (State.SUPPRESSED, False, TOO_SMALL)


def test_an_area_with_no_flat_at_all_is_said_to_have_none(tmp_path: Path):
    """A count of nought is a count."""
    homes = {**HOMES, "E01999003": ("0", "10", "60"), "E01999004": ("0", "0", "540")}
    made = built(tmp_path, homes, with_row("E02999002", "0", "10", "600"))
    assert made.worked[TWO] == Worked(0.0, 1, 1, 1.0, State.PRESENT, ROUNDED)


def test_a_dash_in_the_row_of_an_lsoa_does_not_mark_a_figure_read_from_its_msoa(
    tmp_path: Path,
):
    """The second LSOA of Quillhaven 002 holds a dash for its flats. The area's own row holds 30."""
    made = built(tmp_path)
    assert made.stock.of_lsoa["E01999004"].too_small
    assert made.worked[TWO] == Worked(5.0, 1, 1, 1.0, State.PRESENT, ROUNDED)
    assert all(Flag.SUPPRESSED_IN_SOURCE not in row.flags for row in made.rows)


def test_a_dash_for_homes_of_no_known_kind_is_part_of_no_figure(tmp_path: Path):
    homes = {code: (flats, "-", every) for code, (flats, _, every) in HOMES.items()}
    of_msoas = {code: (flats, "-", every) for code, (flats, _, every) in OF_MSOAS.items()}
    made = built(tmp_path, homes, of_msoas)
    assert made.worked == built(tmp_path / "plain").worked
    assert {one.not_known for one in made.stock.of_msoa.values()} == {None}


# The row of an area is held to the rows of its LSOAs


def test_the_row_of_every_area_is_held_to_the_rows_of_its_lsoas(tmp_path: Path):
    assert built(tmp_path).rows_held == 3


@pytest.mark.parametrize("own", ["20", "30", "40"])
def test_a_row_is_let_through_while_it_is_within_rounding_of_its_lsoas(tmp_path: Path, own: str):
    """Two LSOAs and the MSOA are each within 5 of what is written: 15 in all, round 30."""
    made = built(tmp_path, of_msoas=with_row("E02999002", own, "10", "600"))
    assert made.worked[TWO].value == to_places(100 * int(own) / 600, 1)


@pytest.mark.parametrize(
    ("own", "words"),
    [
        ("-", "a dash hides more than a small count"),
        ("0", "an area holds nought and a part of it does not"),
        ("10", "an area's count is not within rounding of its parts"),
        ("50", "an area's count is not within rounding of its parts"),
        ("570", "an area's count is not within rounding of its parts"),
    ],
)
def test_a_row_that_is_not_what_the_rows_of_its_lsoas_allow_stops_the_build(
    tmp_path: Path, own: str, words: str
):
    table = zipped(table_of(of_msoas=with_row("E02999002", own, "10", "600")))
    assert words in str(refused(tmp_path, table))


def test_a_count_where_no_lsoa_holds_one_stops_the_build(tmp_path: Path):
    table = zipped(table_of(of_msoas=with_row("E02999003", "300", "10", "400")))
    assert "an area holds a count and no part of it does" in str(refused(tmp_path, table))


def test_an_area_with_no_row_of_its_own_stops_the_build(tmp_path: Path):
    of_msoas = {code: cells for code, cells in OF_MSOAS.items() if code != "E02999002"}
    stopped = refused(tmp_path, zipped(table_of(of_msoas=of_msoas)))
    assert "an MSOA of the census of 2021 has no row" in str(stopped)


# What the table leaves out


def test_an_area_with_no_count_of_its_homes_is_said_to_be_withheld(tmp_path: Path):
    homes = {**HOMES, "E01999001": ("60", "0", "-"), "E01999002": ("20", "-", "-")}
    found = built(tmp_path, homes, with_row("E02999001", "80", "-", "-")).worked[ONE]
    assert found == Worked(None, 0, 1, 0.0, State.SUPPRESSED, TOO_SMALL)


def test_an_area_with_no_home_has_no_figure_and_is_never_nought(tmp_path: Path):
    homes = {**HOMES, "E01999001": ("0", "0", "0"), "E01999002": ("0", "0", "0")}
    made = built(tmp_path, homes, with_row("E02999001", "0", "0", "0"))
    assert made.worked[ONE] == Worked(None, 0, 1, 0.0, State.SOURCE_GAP, ROUNDED)
    (row,) = [row for row in made.rows if row.area_id == ONE]
    assert (row.state, row.has_a_value, row.units_used) == (State.SOURCE_GAP, False, 0)


def test_a_table_that_lacks_an_lsoa_of_the_spine_is_not_on_its_codes(tmp_path: Path):
    """The table names no census. One on the codes of 2011 would lack an LSOA drawn since."""
    homes = {code: cells for code, cells in HOMES.items() if code != "E01999005"}
    stopped = refused(tmp_path, zipped(table_of(homes)))
    assert "an LSOA of the census of 2021 has no row" in str(stopped)


def test_the_rows_a_figure_is_read_from_are_keyed_by_the_msoas_of_2021(tmp_path: Path):
    assert built(tmp_path).geography is Geography.MSOA21


def test_an_area_the_table_lacks_would_have_no_figure(tmp_path: Path):
    """The build stops before this. The figures are still never made round a hole."""
    inputs = inputs_with(tmp_path)
    found = spine.build(inputs)
    stock = Stock(
        of_lsoa={},
        of_msoa={"E02999001": Counted(80, None, 200)},
        as_at="2025-03-31",
        rows=1,
        file_id="f-000000000000",
    )
    assert homes_flats.figures(stock, found) == {
        ONE: Worked(40.0, 1, 1, 1.0, State.PRESENT, ROUNDED),
        TWO: Worked(None, 0, 1, 0.0, State.SOURCE_GAP, ROUNDED),
        THREE: Worked(None, 0, 1, 0.0, State.SOURCE_GAP, ROUNDED),
    }


# The parser


def test_only_the_rows_for_all_bands_of_an_msoa_and_an_lsoa_are_read(tmp_path: Path):
    stock = built(tmp_path).stock
    assert stock.rows == len(BANDS) * (len(LARGER) + len(OF_MSOAS) + len(HOMES))
    assert stock.of_lsoa == {
        "E01999001": Counted(60, 0, 120),
        "E01999002": Counted(20, None, 80),
        "E01999003": Counted(30, 10, 60),
        "E01999004": Counted(None, 0, 540),
        "E01999005": Counted(300, 0, 300),
        "E01999006": Counted(0, 0, 100),
        "E01999901": Counted(700, 0, 700),
        "W01999001": Counted(90, 0, 90),
    }
    assert stock.of_msoa == {
        "E02999001": Counted(80, None, 200),
        "E02999002": Counted(30, 10, 600),
        "E02999003": Counted(300, 0, 400),
        "E02999901": Counted(700, 0, 700),
    }


def test_no_other_kind_of_home_and_no_bedroom_is_read(tmp_path: Path):
    assert set(homes_flats.COLUMNS) == {
        "geography",
        "ecode",
        "band",
        "flat_mais_total",
        "unknown",
        "all_properties",
    }
    inputs = inputs_with(tmp_path, zipped(table_of(columns=homes_flats.COLUMNS)))
    made = homes_flats.build(inputs, spine.build(inputs))
    assert made.worked == built(tmp_path / "plain").worked


def test_the_made_up_table_has_the_columns_the_publishers_has():
    header = table_of().splitlines()[0].removeprefix(b"\xef\xbb\xbf").decode().split(",")
    assert len(header) == 49
    assert header[:5] == ["geography", "ba_code", "ecode", "area_name", "band"]
    assert header[-4:] == ["annexe", "caravan_houseboat_mobilehome", "unknown", "all_properties"]
    assert header[13:21] == [f"flat_mais_{size}" for size in SIZES]


@pytest.mark.parametrize("missing", homes_flats.COLUMNS)
def test_a_table_without_a_column_that_is_read_is_refused_and_the_column_is_named(
    tmp_path: Path, missing: str
):
    table = table_of(columns=[name for name in COLUMNS if name != missing])
    assert f"the column {missing} is missing" in str(refused(tmp_path, zipped(table)))


def test_a_table_whose_columns_have_other_names_is_refused(tmp_path: Path):
    table = table_of().replace(b"flat_mais_total", b"Flats and maisonettes")
    assert "the column flat_mais_total is missing" in str(refused(tmp_path, zipped(table)))


@pytest.mark.parametrize("cell", ["", "..", "12a", "-5", "1,200", "12.5", " 120", "c", "١٢٠"])
def test_a_cell_that_is_no_count_stops_the_build(tmp_path: Path, cell: str):
    stopped = refused(tmp_path, zipped(table_of(with_cell("E01999901", FLATS, cell))))
    assert "a count is not a count" in str(stopped)


@pytest.mark.parametrize("which", [NOT_KNOWN, EVERY])
def test_every_cell_that_is_read_is_held_to_be_a_count(tmp_path: Path, which: int):
    stopped = refused(tmp_path, zipped(table_of(with_cell("E01999901", which, ".."))))
    assert "a count is not a count" in str(stopped)


def test_a_count_that_is_not_rounded_to_ten_stops_the_build(tmp_path: Path):
    """The figure is said to be rounded by its publisher. A table that is not must be looked at."""
    stopped = refused(tmp_path, zipped(table_of(with_cell("E01999002", FLATS, "24"))))
    assert "a count is not rounded to 10" in str(stopped)


def test_an_lsoa_that_is_there_twice_stops_the_build(tmp_path: Path):
    stopped = refused(tmp_path, zipped(table_of(twice=["E01999003"])))
    assert "an LSOA is there twice" in str(stopped)


def test_an_msoa_that_is_there_twice_stops_the_build(tmp_path: Path):
    stopped = refused(tmp_path, zipped(table_of(twice=["E02999002"])))
    assert "an MSOA is there twice" in str(stopped)


@pytest.mark.parametrize("code", ["E02999001", "e01999001", "E0199900", "E019990011", ""])
def test_a_row_for_an_lsoa_whose_code_is_not_one_stops_the_build(tmp_path: Path, code: str):
    homes = {**HOMES, code: ("10", "0", "10")}
    assert "a code is not a code" in str(refused(tmp_path, zipped(table_of(homes))))


def test_a_row_for_an_msoa_whose_code_is_not_one_stops_the_build(tmp_path: Path):
    of_msoas = with_row("E01999001", "10", "0", "10")
    assert "a code is not a code" in str(refused(tmp_path, zipped(table_of(of_msoas=of_msoas))))


def test_a_table_with_no_row_of_an_lsoa_is_refused(tmp_path: Path):
    assert "it holds no row of an LSOA" in str(refused(tmp_path, zipped(table_of({}))))


def test_a_table_with_no_row_of_an_msoa_is_refused(tmp_path: Path):
    assert "it holds no row of an MSOA" in str(refused(tmp_path, zipped(table_of(of_msoas={}))))


@pytest.mark.parametrize("cells", [("..", "0", "200"), ("80", "0", "204")])
def test_a_cell_of_the_row_of_an_msoa_that_cannot_be_read_stops_the_build(
    tmp_path: Path, cells: Cells
):
    stopped = refused(tmp_path, zipped(table_of(of_msoas={**OF_MSOAS, "E02999001": cells})))
    assert "a count is not" in str(stopped)


def test_a_zip_without_the_one_table_is_refused(tmp_path: Path):
    stopped = refused(tmp_path, zipped(table_of(), name="CTSOP3.1/CTSOP3_1_2025_03_31.txt"))
    assert "it does not hold the one file that is read" in str(stopped)


@pytest.mark.parametrize(
    "name", ["CTSOP3.1/made-up.csv", "CTSOP3_1_2025_13_31.csv", "CTSOP4_1_2025_03_31.csv"]
)
def test_a_table_that_is_not_named_for_a_day_is_refused(tmp_path: Path, name: str):
    stopped = refused(tmp_path, zipped(table_of(), name=name))
    assert "the table is not named for a day" in str(stopped)


def test_a_table_of_another_day_than_its_receipt_gives_is_refused(tmp_path: Path):
    stopped = refused(tmp_path, zipped(table_of()), as_at="2024-03-31")
    assert "the table is not of the day its receipt gives" in str(stopped)


def test_the_table_is_told_from_the_other_tables_of_its_source(tmp_path: Path):
    """The source has three tables. The one of homes by kind is asked for by its name."""
    inputs = inputs_with(tmp_path)
    others = list(inputs.receipts)
    for name in ("CTSOP1.1.zip", "CTSOP4.1.zip"):
        other = zipped(table_of(with_cell("E01999001", FLATS, "0")), name=f"{name[:8]}/made-up.csv")
        path = tmp_path / "given" / name
        path.write_bytes(other)
        inputs.store.put(homes_flats.SOURCE, name, path)
        others.append(receipt_of(homes_flats.SOURCE, Use.SCORING, name, other, "2025"))
    every = Inputs(inputs.registry, others, inputs.store, inputs.work)
    made = homes_flats.build(every, spine.build(every))
    assert made.worked[ONE].value == 40.0
    (read,) = [receipt for receipt in made.files if receipt.source_id == homes_flats.SOURCE]
    assert read.publisher_file == NAME


# The gate, the receipt and the store


def without_scoring() -> Registry:
    """The repository's registry, with the table of homes no longer allowed to score."""
    return Registry(
        tuple(
            source.model_copy(update={"uses": (Use.DISPLAY,)})
            if source.id == homes_flats.SOURCE
            else source
            for source in registry()
        )
    )


def test_the_gate_is_asked_before_the_table_is_read(tmp_path: Path):
    inputs = inputs_with(tmp_path, registry=without_scoring())
    found = spine.build(inputs)
    before = inputs.opened
    with pytest.raises(LockError) as stopped:
        homes_flats.build(inputs, found)
    assert (stopped.value.rule, stopped.value.subject) == ("gate_refuses", homes_flats.SOURCE)
    assert inputs.opened == before
    assert not list((tmp_path / "work").rglob(NAME))


def test_a_table_with_no_receipt_is_not_read(tmp_path: Path):
    inputs = inputs_of(tmp_path, contents())
    with pytest.raises(LockError) as stopped:
        homes_flats.build(inputs, spine.build(inputs))
    assert stopped.value.rule == "input_has_one_receipt"


def test_every_source_behind_the_figure_is_registered_for_scoring():
    for source_id in (homes_flats.SOURCE, spine.LOOKUP):
        assert Use.SCORING in registry().get(source_id).uses
    assert registry().get(homes_flats.SOURCE).publisher == homes_flats.PUBLISHER


def test_nothing_is_written_to_the_store(tmp_path: Path):
    inputs = inputs_with(tmp_path)
    before = held(tmp_path / "store")
    homes_flats.build(inputs, spine.build(inputs))
    assert held(tmp_path / "store") == before


# The evidence


def test_every_area_has_a_row_of_evidence_that_names_the_table_and_the_lookup(tmp_path: Path):
    """It does not name the census: nothing is shared out by homes while the row is the area's."""
    made = built(tmp_path)
    assert [row.fact_id for row in made.rows] == [
        f"{area}/feature/homes_flats" for area in (ONE, TWO, THREE)
    ]
    behind = {receipt.source_id: receipt for receipt in made.files}
    assert set(behind) == {homes_flats.SOURCE, spine.LOOKUP}
    assert made.stock.file_id == behind[homes_flats.SOURCE].file_id
    for row in made.rows:
        assert row.inputs == tuple(sorted(receipt.file_id for receipt in behind.values()))
        assert row.derivation_id == "area_row_ratio@1"
        assert (row.units_used, row.units_expected, row.weight_covered) == (1, 1, 1.0)
        assert row.state is State.PRESENT
        assert row.flags == ROUNDED
        # From the lookup, which says which MSOA an area is, to the day of the table.
        assert row.data_period == Period(
            start=behind[spine.LOOKUP].data_period.days()[0], end="2025-03-31"
        )
        assert row.retrieved_on == "2026-09-23"


def test_a_figure_that_is_missing_has_a_row_too(tmp_path: Path):
    homes = {**HOMES, "E01999003": ("-", "10", "60")}
    made = built(tmp_path, homes, with_row("E02999002", "-", "10", "600"))
    (row,) = [row for row in made.rows if row.area_id == TWO]
    assert (row.state, row.has_a_value) == (State.SUPPRESSED, False)
    assert (row.units_used, row.units_expected, row.weight_covered) == (0, 1, 0.0)


def test_the_rows_name_no_file_the_figure_does_not_rest_on(tmp_path: Path):
    """A build opens the outlines of output areas too, to draw with. No figure rests on them."""
    inputs = inputs_with(tmp_path)
    found = spine.build(inputs)
    drawn = inputs.open("ons-output-areas-2021", Use.CELLS, edition="BGC V2")
    made = homes_flats.build(inputs, found)
    assert drawn.file_id in {one.file_id for one in inputs.opened}
    assert all(drawn.file_id not in row.inputs for row in made.rows)


def test_the_evidence_of_a_release_takes_the_rows_with_no_loose_end(tmp_path: Path):
    made = built(tmp_path)
    evidence = Evidence.of("lon-2026-10-02-01", made.files, homes_flats.METHODS, made.rows)
    assert len(evidence.rows) == 3
    assert [method.derivation_id for method in evidence.methods] == ["area_row_ratio@1"]
    assert all(method.kind == "measured" for method in evidence.methods)


def test_a_spine_made_from_the_files_of_another_build_is_not_taken(tmp_path: Path):
    found = spine.build(inputs_of(tmp_path / "other", contents()))
    with pytest.raises(ValueError, match="files of this build"):
        homes_flats.build(inputs_with(tmp_path / "this"), found)


# The name, the unit and the period


def test_the_name_the_unit_and_which_way_is_more_are_the_ones_core_gives(tmp_path: Path):
    metric = built(tmp_path).metric
    feature = FEATURES[FeatureId.HOMES_FLATS]
    assert (metric.feature_id, metric.label, metric.unit) == (
        "homes_flats",
        "Flats as a share of homes",
        "%",
    )
    assert (feature.higher, feature.lower) == ("more", "fewer")
    assert (metric.polarity, metric.native_resolution, metric.dimension) == (
        feature.polarity,
        feature.native_resolution,
        feature.dimension,
    )
    assert metric.rankable


def test_the_period_is_the_day_the_table_is_as_at(tmp_path: Path):
    metric = built(tmp_path).metric
    assert metric.vintage == "2025-03-31"
    assert metric.source_ids == (
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
        "voa-council-tax-stock-of-properties",
    )


def test_the_definition_says_what_it_is_from_whom_for_when_and_what_it_is_not(tmp_path: Path):
    said = built(tmp_path).metric.definition
    assert said == (
        "Flats and maisonettes, as a percentage of all the properties on the council tax "
        "valuation lists of the Valuation Office Agency as at 2025-03-31: both counts are the "
        "publisher's own for the area, which it rounds to 10, and are not added up from smaller "
        "areas; the share is given to 1 decimal place, with a half taken upward; where the "
        "publisher gives no count of flats but a dash, which is a count too small to round, no "
        "figure is given; a property of no recorded kind counts as a home and not as a flat; so "
        "it is the share of homes recorded as flats, and says nothing of the size of a flat, "
        "the height of a block or whether a home is lived in."
    )
    # One sentence, as a methods page prints it.
    assert said.endswith(".") and not re.search(r"[.!?]\s|\n|[{}]", said)


RESIDENT_WORDS = re.compile(
    r"\b(residents?|people|population|households?|famil(y|ies)|tenants?|owners?|renters?)\b", re.I
)


def test_no_sentence_of_the_measure_describes_who_lives_somewhere(tmp_path: Path):
    sentences = (built(tmp_path).metric.definition, *homes_flats.CANNOT_SEE)
    assert [sentence for sentence in sentences if RESIDENT_WORDS.search(sentence)] == []


def test_what_it_cannot_see_is_said_in_two_sentences_with_no_figure_in_them():
    assert len(homes_flats.CANNOT_SEE) == 2
    for sentence in homes_flats.CANNOT_SEE:
        assert sentence.endswith(".") and not re.search(r"[.!?]\s|\d", sentence)
