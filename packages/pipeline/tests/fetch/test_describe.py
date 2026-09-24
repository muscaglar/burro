"""Describe says the shape of a file, and prints no row that it can tell from a row of names.

Every file here is made up, and shaped like a publisher's. Each holds a canary
in its rows: a string found nowhere else, which must be in nothing describe
gives back. No socket is opened: the run blocks them, and describe refuses them too.

Describe cannot always tell. One test here shows the row it prints, and one holds
every place that speaks of describe to saying so.
"""

import json
import sqlite3
import zipfile
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest
from burro_pipeline import cli
from burro_pipeline.fetch import cli as fetch_cli
from burro_pipeline.fetch import describe as describe_module
from burro_pipeline.fetch.describe import DescribeError, as_text, describe
from burro_pipeline.fetch.kinds import Kind, sniff

from .support import (
    CANARY_ROW,
    made_up_csv,
    made_up_geopackage,
    made_up_workbook,
    made_up_zip,
)

ROWS = [f"E0000000{n},E0100000{n},{CANARY_ROW} {n},1{n}" for n in range(1, 8)]
HEADER = "OA21CD,LSOA21CD,LSOA21NM,homes"
REPOSITORY = Path(__file__).parents[4]
# What was once said of describe, and is not so.
NOT_SO = ("no value from", "never a value", "never prints a value", "a log that anyone reads")


def shape(path: Path, inside: bool = False) -> dict[str, Any]:
    found = describe(path, inside=inside)
    assert CANARY_ROW not in as_text(found)
    assert CANARY_ROW.lower() not in json.dumps(found).lower()
    return cast(dict[str, Any], found)


def test_a_csv_gives_its_columns_and_its_row_count(tmp_path: Path):
    found = shape(made_up_csv(tmp_path / "lookup.csv", HEADER, ROWS))
    assert found == {
        "kind": "csv",
        "bytes": (tmp_path / "lookup.csv").stat().st_size,
        "encoding": "utf-8",
        "separator": "comma",
        "columns": ["OA21CD", "LSOA21CD", "LSOA21NM", "homes"],
        "column_count": 4,
        "columns_at_row": 1,
        "rows": 7,
    }


def test_a_csv_with_notes_above_its_columns_is_read_below_them(tmp_path: Path):
    notes = ["Made-up annual mean 2024", f"{CANARY_ROW}", "", "units,made up", ""]
    rows = [f"{n},5{n}0500,18{n}500,1{n}.25" for n in range(1, 6)]
    found = shape(made_up_csv(tmp_path / "grid.csv", "gridcode,x,y,no22024", rows, before=notes))
    assert found["columns"] == ["gridcode", "x", "y", "no22024"]
    assert found["columns_at_row"] == 6
    assert found["rows"] == 5


def test_a_csv_with_no_header_gives_no_names(tmp_path: Path):
    """Shaped like the sales file: a row is a sale, and the first row is one too."""
    rows = [
        f'"{{made-up-{n}}}","25{n}000","2026-01-0{n} 00:00","ZZ9 {n}ZZ","F","N","L","{n}","",'
        f'"{CANARY_ROW}","MADE UP TOWN","A","A"'
        for n in range(1, 6)
    ]
    found = shape(made_up_csv(tmp_path / "sales.csv", None, rows))
    assert found["columns"] is None
    assert found["column_count"] == 13
    assert found["rows"] == 5
    assert found["why_no_columns"] == "the first full row holds a number, a date or an empty cell"


def test_a_csv_of_text_alone_with_no_header_gives_no_names(tmp_path: Path):
    rows = [f"E0000000{n},E0100000{n},{CANARY_ROW} 00{n}A" for n in range(1, 6)]
    found = shape(made_up_csv(tmp_path / "lookup.csv", None, rows))
    assert found["columns"] is None
    assert found["why_no_columns"] == "the first full row is shaped like the rows under it"


@pytest.mark.parametrize("under", [0, 1])
def test_a_first_row_with_too_little_under_it_cannot_be_told_from_data(tmp_path: Path, under: int):
    """One row of a file with no header would otherwise be printed as its names."""
    rows = [f"E{n},{CANARY_ROW}" for n in range(2, 2 + under)]
    found = shape(made_up_csv(tmp_path / "short.csv", f"code,{CANARY_ROW}", rows))
    assert found["columns"] is None
    assert found["why_no_columns"] == "too few rows stand under the first full row"


def test_rows_of_names_and_streets_are_never_taken_for_a_header(tmp_path: Path):
    """No column here keeps one shape, so nothing marks the first row out as names."""
    rows = [
        f"{CANARY_ROW} Ann Jones,3 Made-up Road",
        f"{CANARY_ROW},12 Made-up High Street",
        f"{CANARY_ROW} Smith,Flat 2 Made-up Court",
        f"{CANARY_ROW} Lee,The Made-up House",
    ]
    found = shape(made_up_csv(tmp_path / "people.csv", None, rows))
    assert found["columns"] is None
    assert found["why_no_columns"] == "the first full row is shaped like the rows under it"


def test_a_first_row_of_text_that_alone_breaks_a_shape_is_printed_though_it_is_data(
    tmp_path: Path,
):
    """The limit of the rule. No cell here is a number or a date, and one column keeps a
    shape under the first row that the first row does not have. Nothing marks the first
    row out as data, so it is printed as names."""
    rows = [
        "Made-up Person,Flat A",
        "Made-up Other,12 Made-up Road",
        "Made-up Third,14 Made-up Road",
        "Made-up Fourth,16 Made-up Road",
    ]
    found = describe(made_up_csv(tmp_path / "people.csv", None, rows))
    assert found["columns"] == ["Made-up Person", "Flat A"]


def _spoken_of_describe() -> dict[str, str]:
    """Every place a person reads of describe before they run it."""
    step = cli.STEPS["describe"]
    make = (REPOSITORY / "Makefile").read_text(encoding="utf-8").splitlines()
    rules = (REPOSITORY / "packages/pipeline/AGENTS.md").read_text(encoding="utf-8").splitlines()
    return {
        "the summary of the step": step.summary,
        "the help of the step": step.about,
        "the head of fetch/describe.py": describe_module.__doc__ or "",
        "the head of fetch/cli.py": fetch_cli.__doc__ or "",
        "the Makefile": "\n".join(line for line in make if line.startswith("describe:")),
        "packages/pipeline/AGENTS.md": "\n".join(line for line in rules if "`describe`" in line),
    }


@pytest.mark.parametrize("where", sorted(_spoken_of_describe()))
def test_nothing_says_that_describe_prints_no_value_from_a_row(where: str):
    said = " ".join(_spoken_of_describe()[where].split()).lower()
    assert said, "nothing was found to read"
    assert [words for words in NOT_SO if words in said] == []


def test_the_help_of_describe_says_what_the_guide_says():
    """docs/data-builds.md, section 7: for your own machine, and no workflow runs it."""
    said = " ".join(cli.STEPS["describe"].about.split())
    assert "for a machine of your own, and never for a public log" in said
    assert "Where a table has no header, that row is data" in said
    assert "treat all it prints as if it held a row" in said
    assert "No workflow runs it" in said
    rules = " ".join(_spoken_of_describe()["packages/pipeline/AGENTS.md"].split())
    assert "no workflow runs it" in rules


def test_one_column_alone_gives_no_name(tmp_path: Path):
    rows = ["ZZ9 1ZZ", "ZZ99 2ZZ", f"{CANARY_ROW}", "ZZ9 4ZZ"]
    found = shape(made_up_csv(tmp_path / "one.csv", None, rows))
    assert found["columns"] is None
    assert found["why_no_columns"] == "one column alone cannot be told from a row"


def test_a_name_used_twice_is_not_taken_for_a_header(tmp_path: Path):
    rows = [f"{CANARY_ROW},1", f"{CANARY_ROW},2", f"{CANARY_ROW},3"]
    found = shape(made_up_csv(tmp_path / "twice.csv", "made,made", rows))
    assert found["columns"] is None
    assert found["why_no_columns"] == "the first full row holds the same name twice"


@pytest.mark.parametrize(
    ("separator", "word"), [("\t", "tab"), (";", "semicolon"), ("|", "bar"), (",", "comma")]
)
def test_the_separator_is_found_and_named(tmp_path: Path, separator: str, word: str):
    rows = [row.replace(",", separator) for row in ROWS]
    path = made_up_csv(tmp_path / "file.csv", HEADER.replace(",", separator), rows)
    found = shape(path)
    assert found["separator"] == word
    assert found["column_count"] == 4


def test_a_cell_may_hold_a_line_break_and_is_still_one_row(tmp_path: Path):
    rows = [f'E00000001,E01000001,"{CANARY_ROW}\nsecond line",10', ROWS[1]]
    assert shape(made_up_csv(tmp_path / "file.csv", HEADER, rows))["rows"] == 2


def test_a_file_that_is_not_utf8_is_read_and_says_so(tmp_path: Path):
    path = tmp_path / "latin.csv"
    path.write_bytes("code,café\nE1,10\nE2,20\nE3,30\n".encode("cp1252"))
    found = shape(path)
    assert found["encoding"] == "cp1252"
    assert found["columns"] == ["code", "café"]


def test_a_mark_at_the_start_of_the_file_is_not_part_of_the_first_name(tmp_path: Path):
    path = tmp_path / "bom.csv"
    path.write_bytes(b"\xef\xbb\xbfcode,homes\nE1,10\nE2,20\nE3,30\n")
    assert shape(path)["columns"] == ["code", "homes"]


def test_a_name_cannot_forge_a_line_of_a_log(tmp_path: Path):
    forged = '"code\nstep=fetch status=ok","\x1b[31mhomes","::add-mask::x"'
    path = made_up_csv(tmp_path / "forged.csv", forged, ["E1,10,3", "E2,20,4", "E3,30,5"])
    text = as_text(describe(path))
    assert "\x1b" not in text
    assert all(not line.startswith(("step=", "::")) for line in text.splitlines())
    assert text.isascii()
    assert json.loads(text)["columns"] == [
        "code\nstep=fetch status=ok",
        "\x1b[31mhomes",
        "::add-mask::x",
    ]


def test_a_name_too_long_to_be_a_name_is_not_printed(tmp_path: Path):
    path = made_up_csv(tmp_path / "long.csv", f"code,{'x' * 201}", ["E1,10", "E2,20", "E3,30"])
    assert shape(path)["columns"] is None


def test_a_csv_that_cannot_be_read_says_where_and_not_what(tmp_path: Path):
    """A quote that never closes makes one cell of the rest of the file."""
    path = tmp_path / "broken.csv"
    rest = f"{CANARY_ROW}," * 20_000
    path.write_bytes(f'code,name\nE1,made up\nE2,"{rest}\n'.encode())
    with pytest.raises(DescribeError) as refused:
        describe(path, cell_limit=100_000)
    assert str(refused.value) == "a cell is over the size limit, at or after row 3"
    assert refused.value.__cause__ is None
    assert refused.value.__context__ is None or refused.value.__suppress_context__


def test_a_zip_gives_the_names_and_sizes_inside(tmp_path: Path):
    inside = ("\n".join([HEADER, *ROWS]) + "\n").encode()
    path = made_up_zip(
        tmp_path / "census.zip", {"made-up-oa.csv": inside, "notes/made-up.txt": b"made up"}
    )
    found = shape(path)
    assert found["kind"] == "zip"
    assert [(member["name"], member["bytes"]) for member in found["members"]] == [
        ("made-up-oa.csv", len(inside)),
        ("notes/made-up.txt", 7),
    ]
    assert 0 < found["members"][0]["packed_bytes"] < len(inside)
    assert "inside" not in found["members"][0]


def test_a_zip_can_be_read_one_level_down(tmp_path: Path):
    inside = ("\n".join([HEADER, *ROWS]) + "\n").encode()
    path = made_up_zip(tmp_path / "census.zip", {"made-up-oa.csv": inside, "made-up.txt": b"x"})
    found = shape(path, inside=True)
    assert found["members"][0]["inside"]["columns"] == ["OA21CD", "LSOA21CD", "LSOA21NM", "homes"]
    assert found["members"][0]["inside"]["rows"] == 7
    assert found["members"][1]["inside"]["kind"] == "csv"
    assert found["members"][1]["inside"]["columns"] is None
    assert list(tmp_path.iterdir()) == [path]


def test_a_member_is_never_written_where_its_name_says(tmp_path: Path):
    path = tmp_path / "slip.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("../../made-up-escape.csv", "code,homes\nE1,10\nE2,20\nE3,30\n")
    found = shape(path, inside=True)
    assert found["members"][0]["name"] == "../../made-up-escape.csv"
    assert found["members"][0]["inside"]["columns"] == ["code", "homes"]
    assert not list(tmp_path.parent.rglob("made-up-escape.csv"))


def test_a_member_that_unpacks_to_more_than_the_limit_is_not_read(tmp_path: Path):
    path = made_up_zip(tmp_path / "bomb.zip", {"zeros.csv": b"0" * 5_000_000})
    found = cast(dict[str, Any], describe(path, inside=True, member_limit=1_000_000))
    assert found["members"][0]["inside"] == {"kind": "not_read", "why": "over the size limit"}


def test_a_workbook_gives_its_sheets_and_each_sheets_columns(tmp_path: Path):
    path = made_up_workbook(
        tmp_path / "file8.xlsx",
        {
            "Notes": [["Made-up notes"], [CANARY_ROW]],
            "Made-up indicators": [
                ["LSOA code (2021)", "LSOA name (2021)", "Made-up noise indicator"],
                *[[f"E0100000{n}", f"{CANARY_ROW} 00{n}A", n / 10] for n in range(1, 10)],
            ],
        },
    )
    found = shape(path)
    assert found["kind"] == "workbook"
    assert [sheet["name"] for sheet in found["sheets"]] == ["Notes", "Made-up indicators"]
    assert found["sheets"][1] == {
        "name": "Made-up indicators",
        "columns": ["LSOA code (2021)", "LSOA name (2021)", "Made-up noise indicator"],
        "column_count": 3,
        "columns_at_row": 1,
        "rows": 9,
    }
    assert found["sheets"][0] == {
        "name": "Notes",
        "columns": None,
        "column_count": 1,
        "rows": 2,
        "why_no_columns": "one column alone cannot be told from a row",
    }


def test_a_sheet_with_a_title_above_its_columns_is_read_below_it(tmp_path: Path):
    path = made_up_workbook(
        tmp_path / "titled.xlsx",
        {
            "Table 1": [
                ["Made-up table 1: homes by made-up area"],
                [CANARY_ROW],
                [None],
                ["Area code", "Area name", "Flats", "Houses"],
                *[[f"E0100000{n}", f"{CANARY_ROW} {n}", n * 10, n * 20] for n in range(1, 5)],
            ]
        },
    )
    sheet = shape(path)["sheets"][0]
    assert sheet["columns"] == ["Area code", "Area name", "Flats", "Houses"]
    assert sheet["columns_at_row"] == 4
    assert sheet["rows"] == 4


def test_a_sheet_of_numbers_alone_gives_no_names(tmp_path: Path):
    path = made_up_workbook(tmp_path / "numbers.xlsx", {"Sheet1": [[1, 2], [3, 4], [5, 6]]})
    sheet = shape(path)["sheets"][0]
    assert sheet["columns"] is None
    assert sheet["column_count"] == 2
    assert sheet["rows"] == 3


def test_a_workbook_that_declares_a_document_type_is_refused(tmp_path: Path):
    hostile = '<!DOCTYPE a [<!ENTITY b "made up">]>'
    path = made_up_workbook(tmp_path / "hostile.xlsx", {"Sheet1": [["a", "b"]]}, prologue=hostile)
    with pytest.raises(DescribeError, match="document type"):
        describe(path)


def test_a_workbook_with_a_part_missing_says_so(tmp_path: Path):
    path = made_up_zip(tmp_path / "half.xlsx", {"xl/workbook.xml": b"<workbook/>"})
    with pytest.raises(DescribeError, match="workbook"):
        describe(path)


def test_a_geopackage_gives_its_layers_fields_and_feature_counts(tmp_path: Path):
    path = made_up_geopackage(
        tmp_path / "areas.gpkg",
        {
            "made_up_areas": ([("OA21CD", "TEXT"), ("GlobalID", "TEXT"), ("hectares", "REAL")], 12),
            "made_up_empty": ([("code", "TEXT")], 0),
        },
    )
    found = shape(path)
    assert found["kind"] == "geopackage"
    assert found["layers"] == [
        {
            "name": "made_up_areas",
            "data": "features",
            "geometry": "MULTIPOLYGON",
            "srs_id": 27700,
            "fields": [
                {"name": "fid", "type": "INTEGER"},
                {"name": "geom", "type": "BLOB"},
                {"name": "OA21CD", "type": "TEXT"},
                {"name": "GlobalID", "type": "TEXT"},
                {"name": "hectares", "type": "REAL"},
            ],
            "features": 12,
        },
        {
            "name": "made_up_empty",
            "data": "features",
            "geometry": "MULTIPOLYGON",
            "srs_id": 27700,
            "fields": [
                {"name": "fid", "type": "INTEGER"},
                {"name": "geom", "type": "BLOB"},
                {"name": "code", "type": "TEXT"},
            ],
            "features": 0,
        },
    ]


def dated(path: Path, changes: dict[str, object]) -> Path:
    """A made-up GeoPackage whose record of its contents says when each layer was last changed."""
    made_up_geopackage(path, {layer: ([("code", "TEXT")], 2) for layer in changes})
    database = sqlite3.connect(path)
    try:
        database.execute("ALTER TABLE gpkg_contents ADD COLUMN last_change DATETIME")
        for layer, change in changes.items():
            database.execute(
                "UPDATE gpkg_contents SET last_change = ? WHERE table_name = ?", (change, layer)
            )
        database.commit()
    finally:
        database.close()
    return path


def test_a_geopackage_gives_the_day_each_layer_says_it_was_last_changed(tmp_path: Path):
    """It is what a list states as the period of boundaries that state no other day."""
    path = dated(
        tmp_path / "areas.gpkg",
        {"made_up_first": "2025-12-22T16:37:50.337Z", "made_up_second": "2024-02-29"},
    )
    found = {layer["name"]: layer.get("last_changed") for layer in shape(path)["layers"]}
    assert found == {"made_up_first": "2025-12-22", "made_up_second": "2024-02-29"}


@pytest.mark.parametrize(
    "change", [CANARY_ROW, f"2025-12-22 {CANARY_ROW}", "2025-13-40", "22/12/2025", 20251222, None]
)
def test_a_last_change_that_is_no_day_is_not_given(tmp_path: Path, change: object):
    path = dated(tmp_path / "areas.gpkg", {"made_up": change})
    (layer,) = shape(path)["layers"]
    assert "last_changed" not in layer
    assert (layer["name"], layer["features"]) == ("made_up", 2)


def test_a_geopackage_that_keeps_no_last_change_gives_none(tmp_path: Path):
    path = made_up_geopackage(tmp_path / "areas.gpkg", {"made_up": ([("code", "TEXT")], 2)})
    (layer,) = shape(path)["layers"]
    assert "last_changed" not in layer


def test_a_layer_name_cannot_run_a_query_of_its_own(tmp_path: Path):
    hostile = 'areas"; DROP TABLE gpkg_contents; --'
    path = made_up_geopackage(tmp_path / "hostile.gpkg", {hostile: ([("code", "TEXT")], 3)})
    before = path.read_bytes()
    found = shape(path)
    assert found["layers"][0]["name"] == hostile
    assert found["layers"][0]["features"] == 3
    assert path.read_bytes() == before


def test_a_layer_that_is_a_view_is_never_run(tmp_path: Path):
    path = made_up_geopackage(tmp_path / "view.gpkg", {"made_up": ([("code", "TEXT")], 2)})
    database = sqlite3.connect(path)
    database.execute("CREATE VIEW sly AS SELECT * FROM made_up")
    database.execute("INSERT INTO gpkg_contents VALUES ('sly', 'features', 'sly', '', 27700)")
    database.commit()
    database.close()
    layers = shape(path)["layers"]
    assert layers[1] == {"name": "sly", "data": "features", "why": "not a table, so not read"}


def test_a_geopackage_is_opened_to_read_and_is_left_as_it_was(tmp_path: Path):
    path = made_up_geopackage(tmp_path / "areas.gpkg", {"made_up": ([("code", "TEXT")], 2)})
    before = path.read_bytes()
    shape(path)
    assert path.read_bytes() == before
    assert sorted(item.name for item in tmp_path.iterdir()) == ["areas.gpkg"]


def test_an_sqlite_file_that_is_no_geopackage_is_not_read(tmp_path: Path):
    path = tmp_path / "other.sqlite"
    database = sqlite3.connect(path)
    database.execute("CREATE TABLE made_up (name TEXT)")
    database.execute("INSERT INTO made_up VALUES (?)", (CANARY_ROW,))
    database.commit()
    database.close()
    assert shape(path) == {
        "kind": "not_read",
        "bytes": path.stat().st_size,
        "looks_like": "sqlite",
    }


@pytest.mark.parametrize(
    ("content", "looks_like"),
    [
        (b"<!DOCTYPE html><html><body>Sign in to continue</body></html>", "html"),
        (b"\n  <HTML><head><title>Error</title></head></HTML>", "html"),
        (b'<?xml version="1.0"?><made-up/>', "xml"),
        (b'{"made": "up"}', "json"),
        (b"%PDF-1.7 made up", "pdf"),
        (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1 made up", "xls"),
        (b"\x1f\x8b\x08 made up", "gzip"),
        (b"\x00\x01\x02\x03 made up", "unknown"),
        (b"", "empty"),
    ],
)
def test_a_file_describe_does_not_read_says_only_what_it_looks_like(
    tmp_path: Path, content: bytes, looks_like: str
):
    path = tmp_path / "file"
    path.write_bytes(content + CANARY_ROW.encode())
    if not content:
        path.write_bytes(b"")
    assert shape(path) == {
        "kind": "not_read",
        "bytes": path.stat().st_size,
        "looks_like": looks_like,
    }


@pytest.mark.parametrize(
    ("name", "kind"),
    [("csv", Kind.CSV), ("zip", Kind.ZIP), ("xlsx", Kind.WORKBOOK), ("gpkg", Kind.GEOPACKAGE)],
)
def test_the_kind_of_a_file_is_read_from_its_bytes_and_not_its_name(
    tmp_path: Path, name: str, kind: Kind
):
    made: dict[str, Callable[[Path], Path]] = {
        "csv": lambda path: made_up_csv(path, HEADER, ROWS),
        "zip": lambda path: made_up_zip(path, {"a.txt": b"made up"}),
        "xlsx": lambda path: made_up_workbook(path, {"Sheet1": [["a", "b"], [1, 2]]}),
        "gpkg": lambda path: made_up_geopackage(path, {"made_up": ([("code", "TEXT")], 1)}),
    }
    assert sniff(made[name](tmp_path / "file.bin")) is kind


def test_describe_opens_no_socket_even_if_something_it_calls_tries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    import socket

    from burro_pipeline.fetch import describe as module
    from burro_pipeline.fetch.offline import NetworkRefused

    def reaches_out(path: Path) -> Kind:
        socket.socket()
        return Kind.CSV

    monkeypatch.setattr(module, "sniff", reaches_out)
    with pytest.raises(NetworkRefused):
        describe(made_up_csv(tmp_path / "file.csv", HEADER, ROWS))
