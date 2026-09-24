"""One sheet of a workbook, read by its name, for the columns that are named.

Every workbook here is made up. It is laid out as the publisher lays out its
own: eight sheets under their own names, text in a table that every sheet
points into, and numbers written to 17 digits. Six of its sheets are not well
formed and hold a canary, so a reader that opens one fails.
"""

import zipfile
from pathlib import Path

import pytest
from burro_pipeline.derive.noise_sheet import Under, read_sheet
from burro_pipeline.evidence.lock import LockError

from .noise_support import (
    CANARY,
    CANARY_NUMBER,
    LIVING,
    LIVING_COLUMNS,
    NEVER_OPENED,
    NOTES,
    NOTES_COLUMNS,
    NOTES_FIRST_COLUMN,
    NOTES_HEADER_AT,
    SHARES,
    Raw,
    Table,
    file_8,
    living,
    opened,
    workbook,
)

CODE, NOISE = "LSOA code (2021)", "Noise pollution"


def refused(folder: Path, content: bytes, sheet: str = LIVING, header_at: int = 1) -> LockError:
    """The refusal of a workbook that is not what the step was written to read."""
    given = opened(folder, content)
    with pytest.raises(LockError) as stopped:
        read_sheet(given, sheet, (CODE, NOISE), header_at=header_at)
    assert (stopped.value.rule, stopped.value.subject) == ("input_is_as_described", given.file_id)
    # A refusal repeats nothing from the file.
    assert CANARY not in str(stopped.value) and str(CANARY_NUMBER) not in str(stopped.value)
    return stopped.value


def one_sheet(table: Table) -> bytes:
    return workbook({LIVING: table})


# What is read


def test_a_row_holds_the_columns_that_are_named_and_no_other(tmp_path: Path):
    rows = read_sheet(opened(tmp_path, file_8()), LIVING, (CODE, NOISE))
    assert [(row[CODE], row[NOISE]) for row in rows] == list(SHARES.items())
    assert all(set(row) == {CODE, NOISE} for row in rows)
    assert CANARY not in repr(rows) and str(CANARY_NUMBER) not in repr(rows)


def test_a_number_written_to_17_digits_is_the_number_it_stands_for(tmp_path: Path):
    written = one_sheet([[CODE, NOISE], ["E01999003", Raw("n", "<v>0.33200000000000002</v>")]])
    assert read_sheet(opened(tmp_path, written), LIVING, (CODE, NOISE)) == [
        {CODE: "E01999003", NOISE: 0.332}
    ]


def test_the_columns_are_found_by_their_names_wherever_they_stand(tmp_path: Path):
    turned = tuple(reversed(LIVING_COLUMNS))
    rows = read_sheet(opened(tmp_path, file_8(columns=turned)), LIVING, (CODE, NOISE))
    assert [(row[CODE], row[NOISE]) for row in rows] == list(SHARES.items())


def test_a_table_is_read_under_the_row_that_names_its_columns(tmp_path: Path):
    """The notes of the publisher's workbook start at the eleventh row, in the third column."""
    rows = read_sheet(
        opened(tmp_path, file_8()),
        NOTES,
        ("Indicator", "Data time point"),
        header_at=NOTES_HEADER_AT,
    )
    assert {"Indicator": "Noise pollution", "Data time point": "2021"} in rows
    assert len(rows) == 4


def test_an_empty_cell_is_none_and_never_nought(tmp_path: Path):
    rows = read_sheet(
        opened(tmp_path, file_8({"E01999001": None, "E01999002": 0.0})), LIVING, (CODE, NOISE)
    )
    assert rows == [{CODE: "E01999001", NOISE: None}, {CODE: "E01999002", NOISE: 0.0}]


def test_a_row_with_nothing_in_the_named_columns_is_left_out(tmp_path: Path):
    table = [[CODE, "LSOA name (2021)", NOISE], [None, CANARY, None], ["E01999001", CANARY, 0.5]]
    assert read_sheet(opened(tmp_path, one_sheet(table)), LIVING, (CODE, NOISE)) == [
        {CODE: "E01999001", NOISE: 0.5}
    ]


@pytest.mark.parametrize(
    ("cell", "read"),
    [
        (Raw("inlineStr", "<is><t>E01999001</t></is>"), "E01999001"),
        (Raw("str", "<f>A1</f><v>E01999001</v>"), "E01999001"),
        (Raw("n", "<f>1/4</f><v>0.25</v>"), 0.25),
        (Raw("s", "<v> 0 </v>"), CODE),
    ],
)
def test_text_is_read_where_a_workbook_may_keep_it(tmp_path: Path, cell: Raw, read: object):
    written = one_sheet([[CODE, NOISE], [cell, 0.5]])
    assert read_sheet(opened(tmp_path, written), LIVING, (CODE, NOISE))[0][CODE] == read


def test_text_in_pieces_is_joined_and_how_it_is_said_aloud_is_left_out(tmp_path: Path):
    main = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    texts = (
        f'<sst xmlns="{main}"><si><t>{CODE}</t></si><si><t>{NOISE}</t></si>'
        f"<si><r><t>E0199</t></r><r><t>9001</t></r><rPh><t>{CANARY}</t></rPh></si></sst>"
    ).encode()
    table = [[Raw("s", "<v>0</v>"), Raw("s", "<v>1</v>")], [Raw("s", "<v>2</v>"), 0.5]]
    written = workbook({LIVING: table}, parts={"xl/sharedStrings.xml": texts})
    assert read_sheet(opened(tmp_path, written), LIVING, (CODE, NOISE)) == [
        {CODE: "E01999001", NOISE: 0.5}
    ]


# What is never opened


def test_no_other_sheet_is_unpacked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Six sheets of the made-up workbook are about residents. None is opened."""
    given = opened(tmp_path, file_8())
    unpacked: list[str] = []
    unpack = zipfile.ZipFile.open

    def watched(archive: zipfile.ZipFile, name: str, mode: str = "r"):
        unpacked.append(name)
        return unpack(archive, name, "r" if mode == "r" else "w")

    monkeypatch.setattr(zipfile.ZipFile, "open", watched)
    read_sheet(given, LIVING, (CODE, NOISE))
    assert set(unpacked) == {
        "xl/workbook.xml",
        "xl/_rels/workbook.xml.rels",
        "xl/sharedStrings.xml",
        f"xl/worksheets/sheet{len(NEVER_OPENED) + 2}.xml",
    }


def test_a_sheet_is_found_by_its_name_and_not_by_its_place(tmp_path: Path):
    """The sheet that is read stands first here, and a sheet about residents stands last."""
    moved = workbook({LIVING: living(), NEVER_OPENED[0]: [[CODE, NOISE], ["E01999001", 0.9]]})
    rows = read_sheet(opened(tmp_path, moved), LIVING, (CODE, NOISE))
    assert [(row[CODE], row[NOISE]) for row in rows] == list(SHARES.items())


def test_only_the_text_a_named_column_points_at_is_kept(tmp_path: Path):
    """The table of text holds the text of every sheet. A canary in it is never read."""
    table = [[CODE, "LSOA name (2021)", NOISE], ["E01999001", CANARY, 0.5]]
    given = opened(tmp_path, one_sheet(table))
    with zipfile.ZipFile(given.path) as archive:
        assert CANARY.encode() in archive.read("xl/sharedStrings.xml")
    assert CANARY not in repr(read_sheet(given, LIVING, (CODE, NOISE)))


# What stops the step


def test_a_file_that_is_no_workbook_is_refused(tmp_path: Path):
    assert "it is not a workbook" in str(refused(tmp_path, CANARY.encode()))


def test_a_workbook_without_the_sheet_is_refused(tmp_path: Path):
    lacking = workbook({NEVER_OPENED[0]: living()})
    assert "does not hold the one sheet" in str(refused(tmp_path, lacking))


def test_a_workbook_that_names_the_sheet_twice_is_refused(tmp_path: Path):
    main = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    twice = (
        f'<workbook xmlns="{main}" xmlns:r="made-up"><sheets>'
        f'<sheet name="{LIVING}" sheetId="1" r:id="rId1"/>'
        f'<sheet name="{LIVING}" sheetId="2" r:id="rId1"/></sheets></workbook>'
    ).encode()
    written = workbook({LIVING: living()}, parts={"xl/workbook.xml": twice})
    assert "does not hold the one sheet" in str(refused(tmp_path, written))


def test_a_sheet_that_points_outside_the_workbook_is_refused(tmp_path: Path):
    package = "http://schemas.openxmlformats.org/package/2006/relationships"
    outside = (
        f'<Relationships xmlns="{package}"><Relationship Id="rId1" Type="made-up" '
        f'Target="../../{CANARY}.xml"/></Relationships>'
    ).encode()
    written = workbook({LIVING: living()}, parts={"xl/_rels/workbook.xml.rels": outside})
    assert "does not hold the one sheet" in str(refused(tmp_path, written))


@pytest.mark.parametrize("missing", [CODE, NOISE])
def test_a_sheet_without_a_column_that_is_read_is_refused_and_the_column_is_named(
    tmp_path: Path, missing: str
):
    columns = tuple(name for name in LIVING_COLUMNS if name != missing)
    stopped = refused(tmp_path, file_8(columns=columns))
    assert f"the column {missing} is missing" in str(stopped)
    # Only the column that is missing is named, and no column that was never asked for.
    assert all(name not in str(stopped) for name in LIVING_COLUMNS if name != missing)


def test_a_column_under_another_name_is_a_column_that_is_missing(tmp_path: Path):
    """A publisher that renames the column has made another file. Its name is not repeated."""
    header, *rows = living()
    renamed = [[CANARY if name == NOISE else name for name in header], *rows]
    stopped = refused(tmp_path, file_8(sheets={LIVING: renamed}))
    assert f"the column {NOISE} is missing" in str(stopped)


def test_a_column_that_is_named_twice_is_refused(tmp_path: Path):
    table = [[CODE, NOISE, NOISE], ["E01999001", 0.1, 0.9]]
    assert f"the column {NOISE} is there twice" in str(refused(tmp_path, one_sheet(table)))


def test_a_header_that_is_not_where_the_step_looks_is_refused(tmp_path: Path):
    """The notes are read from the eleventh row. A sheet whose names stand elsewhere is not."""
    table = [list(NOTES_COLUMNS), [CANARY] * len(NOTES_COLUMNS)]
    written = workbook({NOTES: table}, starts={NOTES: (NOTES_FIRST_COLUMN, 1)})
    given = opened(tmp_path, written)
    with pytest.raises(LockError) as stopped:
        read_sheet(given, NOTES, ("Indicator",), header_at=NOTES_HEADER_AT)
    assert "the row that names the columns is empty" in str(stopped.value)
    assert CANARY not in str(stopped.value)


@pytest.mark.parametrize(
    "cell",
    [
        Raw("e", "<v>#DIV/0!</v>"),
        Raw("b", "<v>1</v>"),
        Raw("d", "<v>2021-03-21</v>"),
        Raw("n", f"<v>{CANARY}</v>"),
        Raw("n", "<v>inf</v>"),
        Raw("n", "<v>nan</v>"),
    ],
)
def test_a_cell_that_is_neither_text_nor_a_number_is_refused(tmp_path: Path, cell: Raw):
    written = one_sheet([[CODE, NOISE], ["E01999001", cell]])
    assert "neither text nor a number" in str(refused(tmp_path, written))


@pytest.mark.parametrize("place", ["7", CANARY, "-1", "1.5"])
def test_a_cell_that_points_at_no_text_is_refused(tmp_path: Path, place: str):
    written = one_sheet([[CODE, NOISE], [Raw("s", f"<v>{place}</v>"), 0.5]])
    assert "a cell points at no text" in str(refused(tmp_path, written))


def test_a_cell_that_is_there_twice_is_refused(tmp_path: Path):
    main = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    sheet = (
        f'<worksheet xmlns="{main}"><sheetData>'
        '<row r="1"><c r="A1" t="inlineStr"><is><t>LSOA code (2021)</t></is></c>'
        '<c r="B1" t="inlineStr"><is><t>Noise pollution</t></is></c></row>'
        '<row r="2"><c r="A2" t="inlineStr"><is><t>E01999001</t></is></c>'
        '<c r="B2"><v>0.1</v></c><c r="B2"><v>0.9</v></c></row>'
        "</sheetData></worksheet>"
    ).encode()
    assert "a cell is there twice" in str(refused(tmp_path, workbook({LIVING: sheet})))


def test_a_sheet_that_is_not_well_formed_is_refused(tmp_path: Path):
    broken = workbook({LIVING: b"<worksheet><sheetData><row>" + CANARY.encode()})
    assert "not well formed" in str(refused(tmp_path, broken))


def test_a_sheet_that_declares_an_entity_is_refused(tmp_path: Path):
    """An entity is how a small file is made to unpack without end. None is read."""
    grows = (
        b'<?xml version="1.0"?><!DOCTYPE made [<!ENTITY up "up">]>'
        b"<worksheet><sheetData/></worksheet>"
    )
    assert "not well formed" in str(refused(tmp_path, workbook({LIVING: grows})))


def test_a_workbook_with_a_part_missing_is_refused(tmp_path: Path):
    given = opened(tmp_path, one_sheet(living()))
    with zipfile.ZipFile(given.path) as whole:
        kept = {name: whole.read(name) for name in whole.namelist() if "sharedStrings" not in name}
    with zipfile.ZipFile(given.path, "w") as less:
        for name, content in kept.items():
            less.writestr(name, content)
    with pytest.raises(LockError) as stopped:
        read_sheet(given, LIVING, (CODE, NOISE))
    assert "a part of it is missing" in str(stopped.value)


def test_a_cell_that_holds_more_than_a_cell_can_is_refused(tmp_path: Path):
    long = Raw("inlineStr", f"<is><t>{'x' * 40_000}</t></is>")
    written = one_sheet([[CODE, NOISE], [long, 0.5]])
    assert "more than a cell can" in str(refused(tmp_path, written))


# Columns that are named under a heading

# A sheet that counts one thing three ways: the names of the second row are the same
# under each heading of the first, and a heading stands over the columns the sheet merges.
WAYS, COUNT, PART = ("Of one kind", "Of another", "Of both"), "Count", "Part of it"
GROUPED: Table = [
    [CODE, WAYS[0], None, WAYS[1], None, WAYS[2], None],
    [None, COUNT, PART, COUNT, PART, COUNT, PART],
    ["E01999001", CANARY_NUMBER, CANARY_NUMBER, CANARY_NUMBER, CANARY_NUMBER, 50, 20],
    ["E01999002", CANARY_NUMBER, CANARY_NUMBER, CANARY_NUMBER, CANARY_NUMBER, 30, None],
    # A line under the table, in a column that is not read.
    [None, CANARY],
]
MERGED = ("A1:A2", "B1:C1", "D1:E1", "F1:G1")
BOTH = Under(WAYS[2], (COUNT, PART))


def grouped(table: Table = GROUPED, merged: tuple[str, ...] = MERGED) -> bytes:
    return workbook({LIVING: table}, merged={LIVING: merged})


def refused_under(folder: Path, content: bytes, under: Under = BOTH) -> LockError:
    given = opened(folder, content)
    with pytest.raises(LockError) as stopped:
        read_sheet(given, LIVING, (CODE,), under=under)
    assert (stopped.value.rule, stopped.value.subject) == ("input_is_as_described", given.file_id)
    assert CANARY not in str(stopped.value) and str(CANARY_NUMBER) not in str(stopped.value)
    return stopped.value


def test_a_column_is_read_under_the_heading_that_stands_over_it(tmp_path: Path):
    rows = read_sheet(opened(tmp_path, grouped()), LIVING, (CODE,), under=BOTH)
    assert rows == [
        {CODE: "E01999001", COUNT: 50.0, PART: 20.0},
        {CODE: "E01999002", COUNT: 30.0, PART: None},
    ]


def test_a_column_of_the_same_name_under_another_heading_is_never_read(tmp_path: Path):
    given = opened(tmp_path, grouped())
    rows = read_sheet(given, LIVING, (CODE,), under=Under(WAYS[1], (COUNT,)))
    assert [row[COUNT] for row in rows] == [CANARY_NUMBER, CANARY_NUMBER]
    assert str(CANARY_NUMBER) not in repr(read_sheet(given, LIVING, (CODE,), under=BOTH))


def test_the_rows_begin_below_both_rows_of_names(tmp_path: Path):
    """The row of names under the headings is no row of the table."""
    rows = read_sheet(opened(tmp_path, grouped()), LIVING, (CODE,), under=BOTH)
    assert COUNT not in [row[COUNT] for row in rows] and len(rows) == 2


def test_a_heading_stands_over_the_columns_the_sheet_merges_and_no_other(tmp_path: Path):
    """Where the next heading begins says nothing. A heading the sheet merges with nothing
    stands over no column, and no column is taken to be under it."""
    alone = tuple(one for one in MERGED if not one.startswith("F1"))
    assert "a heading stands over no columns" in str(refused_under(tmp_path, grouped(merged=alone)))
    narrow = (*alone, "F1:F1")
    stopped = refused_under(tmp_path / "narrow", grouped(merged=narrow))
    assert f"the column {PART} is missing" in str(stopped)


def test_a_heading_that_is_merged_down_the_sheet_is_refused(tmp_path: Path):
    down = (*(one for one in MERGED if not one.startswith("F1")), "F1:G2")
    assert "more than one row" in str(refused_under(tmp_path, grouped(merged=down)))


@pytest.mark.parametrize("written", ["F1", "F1:", "F1:G", "1:2", CANARY])
def test_a_merged_cell_that_is_not_as_a_workbook_writes_one_is_refused(
    tmp_path: Path, written: str
):
    stopped = refused_under(tmp_path, grouped(merged=(*MERGED, written)))
    assert "a merged cell is not as a workbook writes one" in str(stopped)


def test_a_heading_that_is_missing_or_there_twice_is_refused_and_is_named(tmp_path: Path):
    top, *rest = GROUPED
    gone = [[CANARY if cell == WAYS[2] else cell for cell in top], *rest]
    assert f"the heading {WAYS[2]} is missing" in str(refused_under(tmp_path, grouped(gone)))
    twice = [[WAYS[2] if cell == WAYS[1] else cell for cell in top], *rest]
    stopped = refused_under(tmp_path / "twice", grouped(twice))
    assert f"the heading {WAYS[2]} is there twice" in str(stopped)


def test_a_name_that_is_missing_or_there_twice_under_the_heading_is_refused(tmp_path: Path):
    top, names, *rest = GROUPED
    gone = [top, [*names[:6], CANARY], *rest]
    assert f"the column {PART} is missing" in str(refused_under(tmp_path, grouped(gone)))
    twice = [top, [*names[:6], COUNT], *rest]
    stopped = refused_under(tmp_path / "twice", grouped(twice), Under(WAYS[2], (COUNT,)))
    assert f"the column {COUNT} is there twice" in str(stopped)


def test_a_sheet_with_no_row_of_names_under_the_headings_is_refused(tmp_path: Path):
    top, _, *rest = GROUPED
    stopped = refused_under(tmp_path, grouped([top, [], *rest]))
    assert f"the column {COUNT} is missing" in str(stopped)


def test_a_column_is_asked_for_once(tmp_path: Path):
    with pytest.raises(ValueError, match="asked for once"):
        read_sheet(opened(tmp_path, grouped()), LIVING, (CODE,), under=Under(WAYS[2], (CODE,)))
