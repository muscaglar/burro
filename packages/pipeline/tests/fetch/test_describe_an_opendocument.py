"""Describe says the shape of an OpenDocument workbook, and the words of a sheet that is named.

Every workbook here is made up, and written as a spreadsheet program writes
one: one part that holds every sheet, a run of empty cells at the end of each
row, and a run of a million empty rows at the end of each sheet. Each holds a
canary in its rows and a number found nowhere else. Neither may be in anything
describe gives back of a table.
"""

import json
from pathlib import Path
from typing import Any, cast

import pytest
from burro_pipeline.fetch import cli as fetch_cli
from burro_pipeline.fetch.describe import DescribeError, as_text, describe
from burro_pipeline.fetch.download import Downloaded
from burro_pipeline.fetch.kinds import Kind, sniff

from ..derive.land_use_support import Raw, Row, Sheet, workbook
from .support import CANARY_ROW, made_up_workbook

# A number found nowhere else. It stands in the cells of figures.
CANARY_NUMBER = 0.987654321
COLUMNS = ["Made-up code", "Made-up name", "Industry", "Residential gardens"]
TITLE = "Made-up table 9: land by made-up area, as at a made-up month"
ROWS: list[Row] = [
    [f"E0199900{n}", f"{CANARY_ROW} {n}", CANARY_NUMBER, CANARY_NUMBER] for n in range(1, 7)
]
TABLE: Sheet = [[TITLE], ["This sheet is made up"], [], COLUMNS, *ROWS]
NOTES: list[list[str]] = [
    ["Note", "What it says"],
    ["1", "Made up for a test"],
    ["2", "Every figure is made up"],
    ["3", "Nothing here is real"],
]
A_DAY = Raw(
    '<table:table-cell office:value-type="date" office:date-value="2026-09-24">'
    "<text:p>24 September 2026</text:p></table:table-cell>"
)
COVER: Sheet = [["Made-up land"], ["Made up on", A_DAY], ["Pages", 3]]


def never(*_: object, **__: object) -> Downloaded:
    raise AssertionError("describe reaches no publisher")


def made(folder: Path, sheets: dict[str, Sheet | Raw], **how: Any) -> Path:
    path = folder / "made-up.ods"
    path.write_bytes(workbook(sheets, **how))
    return path


def shape(path: Path, sheet: str | None = None) -> dict[str, Any]:
    found = describe(path, sheet=sheet)
    assert str(CANARY_NUMBER) not in as_text(found)
    return cast(dict[str, Any], found)


def whole(folder: Path) -> Path:
    return made(folder, {"Cover": COVER, "Notes": NOTES, "Table_9": TABLE})


def test_the_kind_of_an_opendocument_workbook_is_read_from_its_bytes(tmp_path: Path):
    assert sniff(whole(tmp_path)) is Kind.ODS


def test_a_workbook_gives_its_sheets_and_each_sheets_columns(tmp_path: Path):
    found = shape(whole(tmp_path))
    assert CANARY_ROW not in as_text(found)
    assert found["kind"] == "ods"
    assert [sheet["name"] for sheet in found["sheets"]] == ["Cover", "Notes", "Table_9"]
    assert found["sheets"][2] == {
        "name": "Table_9",
        "columns": COLUMNS,
        "column_count": 4,
        "columns_at_row": 4,
        "rows": 6,
    }


def test_a_cover_is_no_table_and_gives_no_names(tmp_path: Path):
    cover = shape(whole(tmp_path))["sheets"][0]
    assert cover["columns"] is None
    assert cover["rows"] == 3
    assert "words" not in cover


def test_the_empty_rows_a_program_ends_a_sheet_with_are_counted_as_none(tmp_path: Path):
    """The made-up sheet ends with a run of 1,048,000 empty rows, as a program writes one."""
    assert [sheet["rows"] for sheet in shape(whole(tmp_path))["sheets"]] == [3, 3, 6]


def test_a_sheet_of_numbers_alone_gives_no_names_and_no_number(tmp_path: Path):
    numbers: Sheet = [[CANARY_NUMBER, CANARY_NUMBER] for _ in range(4)]
    sheet = shape(made(tmp_path, {"Sheet1": numbers}))["sheets"][0]
    assert sheet["columns"] is None
    assert (sheet["column_count"], sheet["rows"]) == (2, 4)


def test_a_sheet_that_is_not_shown_says_so(tmp_path: Path):
    hidden = (
        '<office:automatic-styles xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0">'
        '<style:style style:name="ta9" style:family="table">'
        '<style:table-properties table:display="false"/></style:style>'
        "</office:automatic-styles>"
    )
    kept = Raw(
        '<table:table table:name="Kept back" table:style-name="ta9"><table:table-row>'
        '<table:table-cell office:value-type="string"><text:p>made up</text:p>'
        "</table:table-cell></table:table-row></table:table>"
    )
    content = workbook({"Shown": NOTES, "Kept back": kept})
    # The styles stand before the sheets, inside the same part.
    path = tmp_path / "hidden.ods"
    path.write_bytes(_with_styles(content, hidden))
    found = shape(path)["sheets"]
    assert [sheet.get("hidden", False) for sheet in found] == [False, True]


def _with_styles(content: bytes, styles: str) -> bytes:
    import io
    import zipfile

    packed = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(content)) as old, zipfile.ZipFile(packed, "w") as new:
        for member in old.infolist():
            held = old.read(member)
            if member.filename == "content.xml":
                held = held.replace(b"<office:body>", styles.encode() + b"<office:body>")
            new.writestr(member, held)
    return packed.getvalue()


# The words of a sheet that is named


def test_the_words_over_and_under_a_table_are_given_and_no_row_of_its_figures(tmp_path: Path):
    under: Sheet = [*TABLE, [], ["Source: made up", None, "Made-up rights"]]
    found = shape(made(tmp_path, {"Notes": NOTES, "Table_9": under}), sheet="Table_9")
    assert CANARY_ROW not in as_text(found)
    table = found["sheets"][1]
    assert table["words"] == [
        {"row": 1, "cells": {"A": TITLE}},
        {"row": 2, "cells": {"A": "This sheet is made up"}},
        {"row": 4, "cells": dict(zip("ABCD", COLUMNS, strict=True))},
        {"row": 12, "cells": {"A": "Source: made up", "C": "Made-up rights"}},
    ]
    assert "words" not in found["sheets"][0]


def test_notes_that_are_laid_out_as_a_table_are_given_whole(tmp_path: Path):
    notes = shape(whole(tmp_path), sheet="Notes")["sheets"][1]
    assert notes["columns"] == ["Note", "What it says"]
    assert [list(row["cells"].values()) for row in notes["words"]] == NOTES


def test_a_cover_gives_a_day_as_the_day_and_never_a_row_that_holds_a_number(tmp_path: Path):
    cover = shape(whole(tmp_path), sheet="Cover")["sheets"][0]
    assert cover["words"] == [
        {"row": 1, "cells": {"A": "Made-up land"}},
        {"row": 2, "cells": {"A": "Made up on", "B": "2026-09-24"}},
    ]


def test_a_column_past_the_alphabet_is_named_as_a_program_names_it():
    from burro_pipeline.fetch.opendocument import letters

    assert [letters(n) for n in (0, 25, 26, 27, 43, 701, 702)] == [
        "A",
        "Z",
        "AA",
        "AB",
        "AR",
        "ZZ",
        "AAA",
    ]


def test_a_note_on_a_cell_is_no_part_of_its_words(tmp_path: Path):
    noted = Raw(
        '<table:table-cell office:value-type="string">'
        f"<office:annotation><text:p>{CANARY_ROW}</text:p></office:annotation>"
        "<text:p>Made-up words</text:p></table:table-cell>"
    )
    found = shape(made(tmp_path, {"Cover": [[noted]]}), sheet="Cover")
    assert CANARY_ROW not in as_text(found)
    assert found["sheets"][0]["words"] == [{"row": 1, "cells": {"A": "Made-up words"}}]


def test_a_cell_longer_than_a_name_is_cut(tmp_path: Path):
    found = shape(made(tmp_path, {"Cover": [["x" * 5000]]}), sheet="Cover")
    assert found["sheets"][0]["words"] == [{"row": 1, "cells": {"A": "x" * 1000}}]


def test_the_words_cannot_forge_a_line_of_a_log(tmp_path: Path):
    forged = "made up\nstep=fetch status=ok \x1b[31m::add-mask::x"
    text = as_text(shape(made(tmp_path, {"Cover": [[forged.replace("\x1b", "")]]}), "Cover"))
    assert text.isascii()
    assert all(not line.startswith(("step=", "::")) for line in text.splitlines())


def test_a_sheet_the_workbook_does_not_hold_is_refused_in_fixed_words(tmp_path: Path):
    with pytest.raises(DescribeError) as refused:
        describe(whole(tmp_path), sheet=CANARY_ROW)
    assert CANARY_ROW not in str(refused.value)
    assert "holds no sheet of the name" in str(refused.value)


def test_the_words_of_a_sheet_are_not_given_of_a_workbook_of_the_other_kind(tmp_path: Path):
    path = made_up_workbook(tmp_path / "file.xlsx", {"Notes": [["Made-up notes"]]})
    with pytest.raises(DescribeError, match="OpenDocument workbook alone"):
        describe(path, sheet="Notes")


# What is refused


def test_a_workbook_that_declares_a_document_type_is_refused(tmp_path: Path):
    hostile = '<!DOCTYPE a [<!ENTITY b "made up">]>'
    with pytest.raises(DescribeError, match="document type"):
        describe(made(tmp_path, {"Sheet1": NOTES}, declared=hostile))


def test_a_workbook_with_no_sheet_says_so(tmp_path: Path):
    with pytest.raises(DescribeError, match="lists no sheet"):
        describe(made(tmp_path, {}))


def test_a_count_that_is_no_number_is_refused(tmp_path: Path):
    row = Raw('<table:table-row table:number-rows-repeated="many"/>')
    with pytest.raises(DescribeError, match="a number of times that is no number"):
        describe(made(tmp_path, {"Sheet1": [row]}))


# The command line


def test_the_step_gives_the_words_of_a_sheet_of_a_file_on_disk(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    path = whole(tmp_path)
    assert fetch_cli.main(["describe", "--path", str(path), "--sheet", "Table_9"], {}, never) == 0
    out, errors = capsys.readouterr()
    assert errors == ""
    assert CANARY_ROW not in out and str(CANARY_NUMBER) not in out
    assert json.loads(out)["sheets"][2]["words"][0] == {"row": 1, "cells": {"A": TITLE}}


def test_the_step_says_in_one_line_that_a_sheet_is_not_there(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    path = whole(tmp_path)
    assert fetch_cli.main(["describe", "--path", str(path), "--sheet", "Absent"], {}, never) == 2
    out, errors = capsys.readouterr()
    assert out == ""
    assert "holds no sheet of the name" in errors and len(errors.strip().splitlines()) == 1
