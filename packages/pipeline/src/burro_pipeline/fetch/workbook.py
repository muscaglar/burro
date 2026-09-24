"""Reading the shape of a workbook with the standard library.

An `.xlsx` file is a zip of XML. To say which sheets it holds and what their
columns are called, three of its parts are enough: the list of sheets, each
sheet, and the table of text that cells point into. Each is read once, in a
stream, so a large workbook needs little memory. No cell's value is kept but
the text of the first rows, which is where the column names are looked for.
"""

import math
import posixpath
import re
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from burro_pipeline.fetch.headers import KEPT, Row, find_names
from burro_pipeline.fetch.markup import End, Finished, Limited, MarkupError, Start, Text, read

WORKBOOK = "xl/workbook.xml"
RELATIONSHIPS = "xl/_rels/workbook.xml.rels"
STRINGS = "xl/sharedStrings.xml"
CELL = re.compile(r"([A-Z]{1,3})(\d{1,7})")
TEXT_LENGTH = 1000
# How much of one part is read once unpacked. A sheet of a million rows is about 100 MB.
PART_LIMIT = 4 * 1024 * 1024 * 1024
# Stands for a cell that holds a number, a date or a truth value.
NOT_TEXT = "0"

# What a cell of the first rows holds: text found in the table of text, by its
# place there; text written in the cell; or something that is not text.
IN_TABLE, IN_CELL, OTHER = "s", "t", "n"
Cell = tuple[str, str]


class WorkbookError(Exception):
    """The workbook could not be read. The message repeats nothing from it."""


def _walk(
    archive: zipfile.ZipFile,
    part: str,
    limit: int,
    start: Start | None = None,
    end: End | None = None,
    text: Text | None = None,
) -> None:
    try:
        with archive.open(part) as source:
            over = WorkbookError("a part of the workbook is over the size limit")
            read(Limited(source, limit, over), start, end, text)
    except KeyError:
        raise WorkbookError("a part of the workbook is missing") from None
    except MarkupError as error:
        raise WorkbookError(str(error)) from None
    except (zipfile.BadZipFile, OSError, EOFError, NotImplementedError, RuntimeError):
        raise WorkbookError("a part of the workbook could not be unpacked") from None


def _column(reference: str, otherwise: int) -> int:
    """The column a cell stands in, from a reference such as `AB12`. Counted from 0."""
    match = CELL.fullmatch(reference)
    if match is None:
        return otherwise
    number = 0
    for letter in match[1]:
        number = number * 26 + ord(letter) - ord("A") + 1
    return number - 1


@dataclass
class _Sheet:
    name: str
    part: str
    hidden: bool
    # The first rows that hold anything, each with the number the workbook gives it.
    first: list[tuple[int, dict[int, Cell]]] = field(
        default_factory=list[tuple[int, dict[int, Cell]]]
    )
    rows: int = 0
    widths: Counter[int] = field(default_factory=Counter[int])


def _listed(archive: zipfile.ZipFile, limit: int) -> list[_Sheet]:
    targets: dict[str, str] = {}
    sheets: list[tuple[str, str, bool]] = []

    def relationship(name: str, given: dict[str, str]) -> None:
        if name == "Relationship" and "Id" in given and "Target" in given:
            targets[given["Id"]] = given["Target"]

    def sheet(name: str, given: dict[str, str]) -> None:
        if name == "sheet" and "name" in given:
            hidden = given.get("state", "visible") != "visible"
            sheets.append((given["name"], given.get("id", ""), hidden))

    _walk(archive, WORKBOOK, limit, start=sheet)
    _walk(archive, RELATIONSHIPS, limit, start=relationship)
    found: list[_Sheet] = []
    for name, relation, hidden in sheets:
        target = targets.get(relation, "")
        part = posixpath.normpath(
            target.lstrip("/") if target.startswith("/") else posixpath.join("xl", target)
        )
        if not target or part.startswith(".."):
            raise WorkbookError("the workbook names a sheet it does not hold")
        found.append(_Sheet(name, part, hidden))
    if not found:
        raise WorkbookError("the workbook lists no sheet")
    return found


class _SheetReader:
    """Counts the rows of a sheet as they go by, and keeps the first of them."""

    def __init__(self, sheet: _Sheet) -> None:
        self.sheet = sheet
        self.row: dict[int, Cell] = {}
        self.number = 0
        self.column = 0
        self.kind = OTHER
        self.inside = False
        self.text = ""

    def start(self, name: str, given: dict[str, str]) -> None:
        if name == "row":
            self.row = {}
            stated = given.get("r", "")
            self.number = int(stated) if stated.isdigit() else self.number + 1
            self.column = 0
        elif name == "c":
            self.column = _column(given.get("r", ""), self.column)
            self.kind, self.text = given.get("t", OTHER), ""
        elif name in ("v", "t"):
            self.inside = True

    def characters(self, piece: str) -> None:
        if self.inside and len(self.text) < TEXT_LENGTH:
            self.text += piece

    def end(self, name: str) -> None:
        if name in ("v", "t"):
            self.inside = False
        elif name == "c":
            held = self.text.strip()
            if held:
                if self.kind == "s" and held.isdigit():
                    self.row[self.column] = (IN_TABLE, held)
                elif self.kind in ("str", "inlineStr"):
                    self.row[self.column] = (IN_CELL, held)
                else:
                    self.row[self.column] = (OTHER, "")
            self.column += 1
        elif name == "row" and self.row:
            self.sheet.rows += 1
            self.sheet.widths[len(self.row)] += 1
            if len(self.sheet.first) < KEPT:
                self.sheet.first.append((self.number, self.row))


class _TextReader:
    """Walks the table of text and keeps only the text at the places asked for."""

    def __init__(self, wanted: set[int]) -> None:
        self.wanted = wanted
        self.last = max(wanted)
        self.found: dict[int, str] = {}
        self.at = -1
        self.inside = False
        # How a word is said aloud, in some scripts. It is not part of the text.
        self.spoken = 0
        self.text = ""

    def start(self, name: str, _: dict[str, str]) -> None:
        if name == "si":
            self.at += 1
            self.text = ""
        elif name == "rPh":
            self.spoken += 1
        elif name == "t":
            self.inside = True

    def characters(self, piece: str) -> None:
        wanted = self.inside and not self.spoken and self.at in self.wanted
        if wanted and len(self.text) < TEXT_LENGTH:
            self.text += piece

    def end(self, name: str) -> None:
        if name == "t":
            self.inside = False
        elif name == "rPh":
            self.spoken -= 1
        elif name == "si" and self.at in self.wanted:
            self.found[self.at] = self.text
            if self.at >= self.last:
                raise Finished


def _texts(archive: zipfile.ZipFile, wanted: set[int], limit: int) -> dict[int, str]:
    if not wanted or STRINGS not in archive.namelist():
        return {}
    reader = _TextReader(wanted)
    _walk(archive, STRINGS, limit, reader.start, reader.end, reader.characters)
    return reader.found


def sheets(path: Path, limit: int = PART_LIMIT) -> list[dict[str, object]]:
    """Each sheet of a workbook: its name, its column names if they can be told, its rows."""
    try:
        archive = zipfile.ZipFile(path)
    except (zipfile.BadZipFile, OSError):
        raise WorkbookError("the workbook could not be opened") from None
    with archive:
        listed = _listed(archive, limit)
        for sheet in listed:
            reader = _SheetReader(sheet)
            _walk(archive, sheet.part, limit, reader.start, reader.end, reader.characters)
        wanted = {
            int(held)
            for sheet in listed
            for _, row in sheet.first
            for kind, held in row.values()
            if kind == IN_TABLE
        }
        texts = _texts(archive, wanted, limit)
    return [_described(sheet, texts) for sheet in listed]


def _text_of(cell: Cell, texts: dict[int, str]) -> str:
    kind, held = cell
    if kind == IN_TABLE:
        return texts.get(int(held), "")
    return held if kind == IN_CELL else NOT_TEXT


def _described(sheet: _Sheet, texts: dict[int, str]) -> dict[str, object]:
    rows: list[Row] = [
        {column: _text_of(cell, texts) for column, cell in row.items()} for _, row in sheet.first
    ]
    widest = max(sheet.widths, default=0)
    names = find_names(rows, max(1, math.ceil(widest / 2)))
    found: dict[str, object] = {
        "name": sheet.name,
        "columns": None if names.columns is None else list(names.columns),
        "column_count": widest,
    }
    if names.columns is not None and names.at is not None:
        found["column_count"] = len(names.columns)
        found["columns_at_row"] = sheet.first[names.at][0]
        found["rows"] = sheet.rows - (names.at + 1)
    else:
        found["rows"] = sheet.rows
        found["why_no_columns"] = names.why
    if sheet.hidden:
        found["hidden"] = True
    return found
