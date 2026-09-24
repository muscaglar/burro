"""One table of an OpenDocument workbook, found by the names of its columns.

Every workbook here is made up, and written as a spreadsheet program writes
one. The reader is told no name of a sheet and no place of a row or a column.
It is told the names of the columns and the shape of a code, and finds the
rest. Where a workbook names a column over a total, or holds its table in two
units, the reader is told the name over the total and the word for the unit.
"""

import re
import time
import zipfile
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest
from burro_pipeline.derive.land_use_sheet import Table, read_table
from burro_pipeline.evidence.lock import LockError

from .land_use_support import (
    BY_LSOA,
    BY_MSOA,
    CANARY,
    CANARY_NUMBER,
    CODE,
    COLUMNS,
    GARDENS,
    HEADER_AT,
    INDUSTRY,
    NAME,
    OUTSIDE,
    USED,
    Raw,
    Row,
    Sheet,
    by_lsoa,
    by_msoa,
    cell,
    figures,
    opened,
    table_p405,
    workbook,
)

AN_LSOA = re.compile(r"E01[0-9]{6}")
# The names the step asks by, each with the ways the publisher is known to spell it.
ASKED: Mapping[str, Sequence[str]] = {
    "industry": ("Industry",),
    "gardens": ("Residential gardens",),
}


def read(folder: Path, content: bytes, asked: Mapping[str, Sequence[str]] = ASKED) -> Table:
    return read_table(opened(folder, content), asked, AN_LSOA)


def refused(
    folder: Path, content: bytes, asked: Mapping[str, Sequence[str]] = ASKED, within: int = 30
) -> LockError:
    """The refusal of a workbook that is not what the step was written to read."""
    given = opened(folder, content)
    with pytest.raises(LockError) as stopped:
        read_table(given, asked, AN_LSOA, within=within)
    assert (stopped.value.rule, stopped.value.subject) == ("input_is_as_described", given.file_id)
    # A refusal repeats nothing from the file.
    assert CANARY not in str(stopped.value) and str(CANARY_NUMBER) not in str(stopped.value)
    return stopped.value


def one_sheet(table: Sheet | Raw) -> bytes:
    return workbook({BY_LSOA: table})


def small(*rows: Row) -> bytes:
    """A workbook of one sheet: the two columns asked for and a code, and the rows given."""
    return one_sheet([[CODE, "Industry", "Residential gardens"], *rows])


# What is read


def test_a_row_holds_its_code_and_the_columns_that_are_named_and_no_other(tmp_path: Path):
    table = read(tmp_path, table_p405())
    assert [row.code for row in table.rows] == list(USED)
    assert [dict(row.held) for row in table.rows] == [
        {"industry": USED[code].get(INDUSTRY, 0.0), "gardens": USED[code].get(GARDENS, 0.0)}
        for code in USED
    ]
    assert CANARY not in repr(table) and str(CANARY_NUMBER) not in repr(table)


def test_the_table_is_found_whatever_its_sheet_is_called_and_wherever_it_stands(tmp_path: Path):
    """No page says what the sheets are called. The reader is never told."""
    as_made = read(tmp_path / "as", table_p405())
    renamed = workbook({CANARY: [[CANARY]], "P405": by_lsoa()})
    assert read(tmp_path / "renamed", renamed).rows == as_made.rows


def test_the_names_of_the_columns_are_found_in_whichever_of_the_first_rows_holds_them(
    tmp_path: Path,
):
    as_made = read(tmp_path / "as", table_p405())
    assert as_made.header_at == HEADER_AT == 4
    at_the_top = read(tmp_path / "top", table_p405(over=()))
    assert at_the_top.header_at == 1
    assert at_the_top.rows == as_made.rows


def test_the_columns_are_found_by_their_names_wherever_they_stand(tmp_path: Path):
    turned = tuple(reversed(COLUMNS))
    assert read(tmp_path / "turned", table_p405(columns=turned)).rows == (
        read(tmp_path / "as", table_p405()).rows
    )


def test_a_name_is_compared_without_its_case_and_its_spacing(tmp_path: Path):
    written = one_sheet([[CODE, "  INDUSTRY ", "Residential\n gardens"], ["E01999001", 0.5, 0.4]])
    (row,) = read(tmp_path, written).rows
    assert dict(row.held) == {"industry": 0.5, "gardens": 0.4}


def test_a_column_is_found_under_any_of_the_spellings_the_step_gives(tmp_path: Path):
    asked = {"woodland": ("Forestry and woodland", "Forestry/Woodland")}
    for number, spelt in enumerate(asked["woodland"]):
        written = one_sheet([[CODE, spelt], ["E01999001", 0.25]])
        (row,) = read(tmp_path / str(number), written, asked).rows
        assert dict(row.held) == {"woodland": 0.25}


def test_a_name_that_only_holds_a_name_that_is_asked_for_is_another_column(tmp_path: Path):
    """The group is called industry and commerce. It is not the category industry."""
    written = one_sheet(
        [
            [CODE, "Industry and commerce", "Industry", "Residential gardens"],
            ["E01999001", CANARY_NUMBER, 0.5, 0.4],
        ]
    )
    (row,) = read(tmp_path, written).rows
    assert dict(row.held) == {"industry": 0.5, "gardens": 0.4}


def test_the_column_of_codes_is_found_by_the_shape_of_a_code(tmp_path: Path):
    """No page says what the column of codes is called, so it is found by what it holds."""
    written = one_sheet(
        [
            ["Industry", CANARY, "Residential gardens", CANARY],
            [0.5, CANARY, 0.4, "E01999001"],
            [0.1, "E01999002", 0.8, "E01999002"],
        ]
    )
    table = read(tmp_path, written)
    # The column is the one the first code stands in. The second row holds no code there.
    assert [row.code for row in table.rows] == ["E01999001", "E01999002"]
    assert table.others == 0


def test_a_row_under_the_names_that_holds_no_code_is_passed_over_and_counted(tmp_path: Path):
    """A row of units, a row for a larger area and a row of notes are part of no figure."""
    written = small(
        [None, "hectares", "hectares"],
        ["E02999001", CANARY_NUMBER, CANARY_NUMBER],
        ["E01999001", 0.5, 0.4],
        [CANARY, CANARY_NUMBER, CANARY_NUMBER],
        ["e01999002", CANARY_NUMBER, CANARY_NUMBER],
        ["E019990021", CANARY_NUMBER, CANARY_NUMBER],
    )
    table = read(tmp_path, written)
    assert [row.code for row in table.rows] == ["E01999001"]
    assert table.others == 5


def test_a_sheet_of_the_same_columns_with_no_code_of_the_shape_is_not_the_table(tmp_path: Path):
    """The workbook holds the table by MSOA under the same names. No row of it is read."""
    table = read(tmp_path, table_p405())
    assert len(table.rows) == 7
    only_msoas = workbook({BY_MSOA: by_msoa()})
    assert "holds a code" in str(refused(tmp_path / "msoa", only_msoas))


# A column that is named over a total, and the word for the unit

# Made up, so that the name over the total is no name the row of names could hold.
OVER = {"gardens": ("Gardens of homes",)}
GROUPED: Sheet = [
    ["Made up", CANARY],
    [None, None, None, "Hectares"],
    [None, "Industry and commerce", None, "Gardens of homes"],
    [CODE, "Industry", "Total", "Total"],
    ["E01999001", 0.5, CANARY_NUMBER, 0.4],
    ["E01999002", 0.1, CANARY_NUMBER, 0.8],
]


def grouped(folder: Path, sheet: Sheet = GROUPED, **told: object) -> Table:
    given = opened(folder, one_sheet(sheet))
    return read_table(given, ASKED, AN_LSOA, over=OVER, **told)  # type: ignore[arg-type]


def test_a_column_is_found_by_the_name_that_stands_over_its_total(tmp_path: Path):
    table = grouped(tmp_path)
    assert table.header_at == 4
    assert [dict(row.held) for row in table.rows] == [
        {"industry": 0.5, "gardens": 0.4},
        {"industry": 0.1, "gardens": 0.8},
    ]
    assert str(CANARY_NUMBER) not in repr(table)


def test_a_name_over_a_column_that_is_not_called_a_total_names_no_column(tmp_path: Path):
    sheet: Sheet = [GROUPED[2], [CODE, "Industry", "Total", CANARY], *GROUPED[4:]]
    given = opened(tmp_path, one_sheet(sheet))
    with pytest.raises(LockError) as stopped:
        read_table(given, ASKED, AN_LSOA, over=OVER)
    assert "the column gardens is missing" in str(stopped.value)


def test_a_total_is_called_what_the_step_says_it_is_called(tmp_path: Path):
    sheet: Sheet = [GROUPED[2], [CODE, "Industry", "All", "All"], *GROUPED[4:]]
    assert len(grouped(tmp_path, sheet, total=" all ").rows) == 2


def test_a_column_named_in_the_row_of_names_and_over_a_total_is_there_twice(tmp_path: Path):
    sheet: Sheet = [
        [None, None, None, "Gardens of homes"],
        [CODE, "Industry", "Residential gardens", "Total"],
        ["E01999001", 0.5, 0.4, CANARY_NUMBER],
    ]
    given = opened(tmp_path, one_sheet(sheet))
    with pytest.raises(LockError) as stopped:
        read_table(given, ASKED, AN_LSOA, over=OVER)
    assert "the column gardens is there twice" in str(stopped.value)


def test_a_name_over_a_total_is_looked_for_only_where_the_step_gives_one(tmp_path: Path):
    """Told no name over a total, the reader reads the row of names and no row above it."""
    assert "the column gardens is missing" in str(refused(tmp_path, one_sheet(GROUPED)))


def test_a_column_that_is_named_over_a_total_is_a_column_that_is_read(tmp_path: Path):
    given = opened(tmp_path, one_sheet(GROUPED))
    with pytest.raises(ValueError, match="is a column that is read"):
        read_table(given, ASKED, AN_LSOA, over={"woodland": ("Forestry and woodland",)})


def test_of_two_sheets_of_one_table_the_one_that_says_the_unit_is_read(tmp_path: Path):
    per_cent: Sheet = [
        GROUPED[0],
        [None, None, None, "Per cent"],
        *GROUPED[2:4],
        ["E01999001", CANARY_NUMBER, CANARY_NUMBER, CANARY_NUMBER],
    ]
    written = workbook({"One": per_cent, "Two": GROUPED})
    table = read_table(
        opened(tmp_path, written), ASKED, AN_LSOA, over=OVER, unit=("hectares", "ha")
    )
    assert [row.code for row in table.rows] == ["E01999001", "E01999002"]
    assert str(CANARY_NUMBER) not in repr(table)


def test_a_table_that_does_not_say_the_unit_stops_the_step(tmp_path: Path):
    given = opened(tmp_path, one_sheet(GROUPED))
    with pytest.raises(LockError) as stopped:
        read_table(given, ASKED, AN_LSOA, over=OVER, unit=("Acres",))
    assert "no sheet that holds the table says its unit" in str(stopped.value)
    assert CANARY not in str(stopped.value)


def test_a_cell_that_only_holds_the_word_for_the_unit_does_not_say_it(tmp_path: Path):
    sheet: Sheet = [["Made up, in hectares"], *GROUPED[2:]]
    given = opened(tmp_path, one_sheet(sheet))
    with pytest.raises(LockError) as stopped:
        read_table(given, ASKED, AN_LSOA, over=OVER, unit=("Hectares",))
    assert "no sheet that holds the table says its unit" in str(stopped.value)


# How a cell is read


def test_a_number_is_read_from_its_value_and_never_from_how_it_is_shown(tmp_path: Path):
    shown = Raw(
        '<table:table-cell office:value-type="float" office:value="0.123456">'
        "<text:p>0.12</text:p></table:table-cell>"
    )
    (row,) = read(tmp_path, small(["E01999001", shown, 0.4])).rows
    assert row.held["industry"] == 0.123456


@pytest.mark.parametrize("kind", ["float", "percentage", "currency"])
def test_every_kind_of_number_is_a_number(tmp_path: Path, kind: str):
    held = Raw(f'<table:table-cell office:value-type="{kind}" office:value="0.5"/>')
    (row,) = read(tmp_path, small(["E01999001", held, 0.4])).rows
    assert row.held["industry"] == 0.5


def test_an_empty_cell_is_none_and_never_nought(tmp_path: Path):
    rows = read(tmp_path, small(["E01999001", None, 0.0], ["E01999002", 0.5, None])).rows
    assert [dict(row.held) for row in rows] == [
        {"industry": None, "gardens": 0.0},
        {"industry": 0.5, "gardens": None},
    ]


def test_text_in_a_column_of_figures_is_given_as_text_for_the_step_to_refuse(tmp_path: Path):
    (row,) = read(tmp_path, small(["E01999001", "[x]", 0.4])).rows
    assert row.held["industry"] == "[x]"


def test_text_in_pieces_is_joined_and_a_note_on_a_cell_is_left_out(tmp_path: Path):
    in_pieces = Raw(
        '<table:table-cell office:value-type="string">'
        f"<office:annotation><text:p>{CANARY}</text:p></office:annotation>"
        "<text:p>E01<text:span>999</text:span><text:a>001</text:a></text:p>"
        "</table:table-cell>"
    )
    named = Raw(
        '<table:table-cell office:value-type="string">'
        '<text:p>Residential<text:s text:c="2"/>gardens</text:p></table:table-cell>'
    )
    written = one_sheet([[CODE, "Industry", named], [in_pieces, 0.5, 0.4]])
    (row,) = read(tmp_path, written).rows
    assert (row.code, dict(row.held)) == ("E01999001", {"industry": 0.5, "gardens": 0.4})


def test_a_cell_that_is_repeated_stands_in_every_column_it_is_repeated_over(tmp_path: Path):
    twice = Raw(
        '<table:table-cell table:number-columns-repeated="2" office:value-type="float" '
        'office:value="0.25"><text:p>0.25</text:p></table:table-cell>'
    )
    (row,) = read(tmp_path, small(["E01999001", twice])).rows
    assert dict(row.held) == {"industry": 0.25, "gardens": 0.25}


def test_empty_cells_that_are_repeated_move_the_columns_along(tmp_path: Path):
    gap = Raw('<table:table-cell table:number-columns-repeated="3"/>')
    merged = Raw("<table:covered-table-cell/>")
    written = one_sheet(
        [
            [CODE, gap, "Industry", merged, "Residential gardens"],
            ["E01999001", None, None, None, 0.5, None, 0.4],
        ]
    )
    (row,) = read(tmp_path, written).rows
    assert dict(row.held) == {"industry": 0.5, "gardens": 0.4}


def test_rows_that_are_repeated_are_counted_and_empty_ones_are_not_walked(tmp_path: Path):
    """A sheet ends in a run of a million empty rows. Reading it takes no longer for them."""
    empty = Raw(
        '<table:table-row table:number-rows-repeated="1000000">'
        '<table:table-cell table:number-columns-repeated="16384"/></table:table-row>'
    )
    written = one_sheet(
        [
            Raw(
                '<table:table-row table:number-rows-repeated="3">'
                "<table:table-cell/></table:table-row>"
            ),
            [CODE, "Industry", "Residential gardens"],
            empty,
            ["E01999001", 0.5, 0.4],
        ]
    )
    started = time.monotonic()
    table = read(tmp_path, written)
    assert time.monotonic() - started < 5
    # Three empty rows stand over the names, and are counted.
    assert (table.header_at, [row.code for row in table.rows]) == (4, ["E01999001"])


def test_a_row_of_figures_that_is_repeated_is_there_twice(tmp_path: Path):
    repeated = Raw(
        '<table:table-row table:number-rows-repeated="2">'
        f"{cell('E01999001')}{cell(0.5)}{cell(0.4)}</table:table-row>"
    )
    table = read(tmp_path, small(repeated))
    assert [row.code for row in table.rows] == ["E01999001", "E01999001"]


def test_a_table_inside_a_cell_is_not_read(tmp_path: Path):
    inside = Raw(
        "<table:table-cell><table:table table:name='inside'><table:table-row>"
        f"{cell('E01999002')}{cell(CANARY_NUMBER)}{cell(CANARY_NUMBER)}"
        "</table:table-row></table:table></table:table-cell>"
    )
    table = read(tmp_path, small(["E01999001", 0.5, 0.4, inside]))
    assert [row.code for row in table.rows] == ["E01999001"]


def test_rows_in_a_group_and_under_a_header_that_repeats_are_read(tmp_path: Path):
    sheet = Raw(
        f"<table:table table:name='{BY_LSOA}'><table:table-header-rows><table:table-row>"
        f"{cell(CODE)}{cell('Industry')}{cell('Residential gardens')}</table:table-row>"
        "</table:table-header-rows><table:table-row-group><table:table-row>"
        f"{cell('E01999001')}{cell(0.5)}{cell(0.4)}</table:table-row></table:table-row-group>"
        "</table:table>"
    )
    table = read(tmp_path, workbook({BY_LSOA: sheet}))
    assert (table.header_at, [row.code for row in table.rows]) == (1, ["E01999001"])


def test_text_written_on_the_cell_itself_is_what_the_cell_holds(tmp_path: Path):
    """A cell may hold its text as a value, and show other text. The value is read."""
    held = Raw(
        '<table:table-cell office:value-type="string" office:string-value="E01999001">'
        f"<text:p>{CANARY}</text:p></table:table-cell>"
    )
    (row,) = read(tmp_path, small([held, 0.5, 0.4])).rows
    assert row.code == "E01999001"


def test_what_a_spreadsheet_program_adds_to_a_sheet_changes_nothing(tmp_path: Path):
    """A drawing over the sheet, a day, a truth, and marks of another program on a cell."""
    drawn = (
        '<table:shapes xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0">'
        f"<draw:frame><draw:text-box><text:p>{CANARY}</text:p></draw:text-box></draw:frame>"
        "</table:shapes>"
    )
    marked = (
        '<table:table-cell xmlns:calcext="urn:org:documentfoundation:names:experimental:'
        'calc:xmlns:calcext:1.0" table:style-name="ce1" office:value-type="float" '
        'calcext:value-type="float" office:value="0.5"><text:p>0.50</text:p></table:table-cell>'
    )
    a_day = (
        '<table:table-cell office:value-type="date" office:date-value="2022-04-01">'
        "<text:p>1 April 2022</text:p></table:table-cell>"
    )
    a_truth = (
        '<table:table-cell office:value-type="boolean" office:boolean-value="true">'
        "<text:p>TRUE</text:p></table:table-cell>"
    )
    sheet = Raw(
        f"<table:table table:name='{BY_LSOA}'>{drawn}<table:table-column-group>"
        '<table:table-column table:number-columns-repeated="5"/></table:table-column-group>'
        f"<table:table-row>{cell(CODE)}{cell('Industry')}{cell('Residential gardens')}"
        f"{cell(CANARY)}{cell(CANARY)}</table:table-row>"
        f"<table:table-row>{cell('E01999001')}{marked}{cell(0.4)}{a_day}{a_truth}"
        "</table:table-row></table:table>"
    )
    (row,) = read(tmp_path, workbook({BY_LSOA: sheet})).rows
    assert (row.code, dict(row.held)) == ("E01999001", {"industry": 0.5, "gardens": 0.4})


# What stops the step


@pytest.mark.parametrize("missing", ["Industry", "Residential gardens"])
def test_a_table_without_a_column_that_is_read_stops_the_step_and_names_it(
    tmp_path: Path, missing: str
):
    columns = tuple(name for name in COLUMNS if name != missing)
    asked_as = {"Industry": "industry", "Residential gardens": "gardens"}[missing]
    stopped = refused(tmp_path, table_p405(columns=columns))
    assert f"the column {asked_as} is missing" in str(stopped)


def test_a_workbook_in_which_no_row_names_a_column_stops_the_step(tmp_path: Path):
    stopped = refused(tmp_path, workbook({BY_LSOA: [[CANARY, CANARY], ["E01999001", 0.5]]}))
    assert "no row names the columns" in str(stopped)


def test_names_that_stand_below_the_first_rows_are_not_looked_for(tmp_path: Path):
    stopped = refused(tmp_path, table_p405(), within=HEADER_AT - 1)
    assert "no row names the columns" in str(stopped)


def test_a_column_that_is_there_twice_stops_the_step_and_names_it(tmp_path: Path):
    """As it is where a table gives hectares and a share under the same names."""
    stopped = refused(tmp_path, table_p405(columns=(*COLUMNS, INDUSTRY)))
    assert "the column industry is there twice" in str(stopped)


def test_two_sheets_that_hold_the_table_stop_the_step(tmp_path: Path):
    twice = workbook({"One": by_lsoa(), "Two": by_lsoa()})
    assert "more than one sheet holds the table" in str(refused(tmp_path, twice))


def test_names_with_no_row_of_a_code_under_them_stop_the_step(tmp_path: Path):
    assert "holds a code" in str(refused(tmp_path, small()))
    assert "holds a code" in str(refused(tmp_path / "other", small([CANARY, 0.5, 0.4])))


@pytest.mark.parametrize(
    "held",
    [
        '<table:table-cell office:value-type="float" office:value="1e400"/>',
        '<table:table-cell office:value-type="float" office:value="nan"/>',
        '<table:table-cell office:value-type="float" office:value="Zzyzx"/>',
        '<table:table-cell office:value-type="float"><text:p>0.5</text:p></table:table-cell>',
    ],
)
def test_a_number_that_is_no_number_stops_the_step(tmp_path: Path, held: str):
    stopped = refused(tmp_path, small(["E01999001", Raw(held), 0.4]))
    assert "a cell holds a number that is no number" in str(stopped)


def test_a_cell_that_holds_more_than_a_cell_can_stops_the_step(tmp_path: Path):
    stopped = refused(tmp_path, small(["E01999001", "x" * 40_000, 0.4]))
    assert "a cell holds more than a cell can" in str(stopped)


def test_a_row_that_runs_past_the_last_column_stops_the_step(tmp_path: Path):
    wide = Raw(
        '<table:table-cell table:number-columns-repeated="20000" office:value-type="float" '
        'office:value="0.5"/>'
    )
    stopped = refused(tmp_path, small(["E01999001", wide]))
    assert "a row runs past the last column" in str(stopped)


def test_a_file_that_is_no_workbook_stops_the_step(tmp_path: Path):
    assert "it is not a workbook" in str(refused(tmp_path, CANARY.encode()))


def test_a_workbook_without_the_part_that_holds_its_sheets_stops_the_step(tmp_path: Path):
    without = workbook({BY_LSOA: by_lsoa()}, parts={"content.xml": None})
    assert "a part of it is missing" in str(refused(tmp_path, without))


def test_a_part_that_is_not_well_formed_stops_the_step(tmp_path: Path):
    broken = workbook({}, parts={"content.xml": f"<a><b>{CANARY}</a>".encode()})
    assert "a part of it is not well formed" in str(refused(tmp_path, broken))


def test_a_part_that_declares_an_entity_is_not_read(tmp_path: Path):
    declared = f'<!DOCTYPE a [<!ENTITY e "{CANARY}">]>'
    written = workbook({BY_LSOA: by_lsoa()}, declared=declared)
    assert "a part of it is not well formed" in str(refused(tmp_path, written))


def test_a_part_that_cannot_be_unpacked_stops_the_step(tmp_path: Path):
    """The part that holds the sheets is marked as locked, so it cannot be unpacked."""
    content = bytearray(workbook({BY_LSOA: by_lsoa()}))
    # The list of members at the end of a zip holds a mark for each: its first bit locks it.
    listed = content.rindex(b"PK\x01\x02", 0, content.rindex(b"content.xml"))
    content[listed + 8] |= 1
    with zipfile.ZipFile(opened(tmp_path / "locked", bytes(content)).path) as archive:
        assert archive.getinfo("content.xml").flag_bits & 1
    assert "could not be unpacked" in str(refused(tmp_path, bytes(content)))


# What it costs


def test_the_whole_of_a_made_up_workbook_is_read_once(tmp_path: Path):
    table = read(tmp_path, table_p405(figures(n001={INDUSTRY: 1.5})))
    assert table.rows[0].held["industry"] == 1.5
    assert (len(table.rows), table.others, table.header_at) == (7, 0, HEADER_AT)
    assert table.rows[-1].code == OUTSIDE


def test_an_lsoa_named_beside_its_code_is_never_kept(tmp_path: Path):
    table = read(tmp_path, table_p405())
    assert NAME not in repr(table)
    assert all(set(row.held) == set(ASKED) for row in table.rows)
