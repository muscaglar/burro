"""One sheet of a workbook, read by its name, for the columns that are named.

The workbook the noise figure comes from holds eight sheets, and seven of them
hold figures about residents. So a sheet is never read by its place in the
workbook, and a workbook is never read whole:

- A workbook is a zip of XML, with one part for each sheet. The part of the
  sheet that is named is unpacked, and the part of no other sheet is.
- A row holds the columns that are named and no other, so that a step cannot
  use a column it did not name.
- Text is kept once in a workbook, in a table that every sheet points into.
  The table is walked, and only the text that a cell of a named column points
  at is kept.

A publisher that counts one thing several ways may name the columns of each
way alike, and say which way in a heading that stands over them, in the row
above. `Under` names such a heading and the columns under it. What a heading
stands over is what the sheet itself says: the columns of the cell it merges
from the heading. It is never taken from where the next heading begins.

It is read with the standard library, a piece at a time, so a sheet of 20 MB
needs little memory. A workbook that is not laid out as the step expects stops
the step, in a few fixed words that repeat nothing from the file. A column the
sheet lacks is named, by the name the step asked for it by.
"""

import math
import posixpath
import re
import zipfile
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass, field

from burro_pipeline.evidence.lock import LockError
from burro_pipeline.fetch.markup import (
    End,
    Finished,
    Limited,
    MarkupError,
    Start,
    Text,
    read,
)
from burro_pipeline.inputs import Opened

WORKBOOK = "xl/workbook.xml"
RELATIONSHIPS = "xl/_rels/workbook.xml.rels"
STRINGS = "xl/sharedStrings.xml"
# How much of one part is read once unpacked. The sheet that is read unpacks to 22 MB.
PART_LIMIT = 1024 * 1024 * 1024
# The longest text a cell of a workbook can hold.
TEXT_LENGTH = 32_767
REFERENCE = re.compile(r"([A-Z]{1,3})([0-9]{1,7})")
# How a workbook marks what a cell holds: text in the table of text, text in the cell, a number.
IN_TABLE, IN_CELL, NUMBER = "s", ("str", "inlineStr"), "n"

# What a cell of a named column holds: text, a number, or nothing.
Value = str | float | None
Row = dict[str, Value]


class _Refused(Exception):
    """The workbook is not as the step expects. It holds the fixed words that say how."""


@dataclass(frozen=True)
class Under:
    """Columns that are named in the row below a heading that stands over them.

    The heading is in the row that names the other columns, and the names are
    in the row below it. The rows of figures begin below both.
    """

    heading: str
    columns: Sequence[str]


@dataclass
class _Cell:
    kind: str
    held: str


@dataclass
class _Rows:
    """Walks one sheet, and keeps the cells of the rows and the columns it was asked for."""

    # The first row that is kept and the last, as the workbook numbers them.
    first: int
    last: int | None
    # The columns that are kept, counted from 0. None keeps every column.
    columns: Collection[int] | None
    found: list[dict[int, _Cell]] = field(default_factory=list[dict[int, _Cell]])
    # The number of each row that was kept, as the workbook numbers them.
    numbers: list[int] = field(default_factory=list[int])
    _row: dict[int, _Cell] = field(default_factory=dict[int, _Cell])
    _number: int = 0
    _column: int = -1
    _cell: _Cell | None = None
    _inside: bool = False

    def start(self, name: str, given: dict[str, str]) -> None:
        if name == "row":
            stated = given.get("r", "")
            self._number = int(stated) if stated.isdigit() else self._number + 1
            self._row, self._column = {}, -1
            if self.last is not None and self._number > self.last:
                raise Finished
        elif name == "c":
            at = REFERENCE.fullmatch(given.get("r", ""))
            self._column = _column_of(at[1]) if at else self._column + 1
            kept = self._number >= self.first and (
                self.columns is None or self._column in self.columns
            )
            self._cell = _Cell(given.get("t", NUMBER), "") if kept else None
        elif name in ("v", "t"):
            self._inside = True

    def characters(self, piece: str) -> None:
        if self._inside and self._cell is not None:
            if len(self._cell.held) + len(piece) > TEXT_LENGTH:
                raise _Refused("a cell holds more than a cell can")
            self._cell.held += piece

    def end(self, name: str) -> None:
        if name in ("v", "t"):
            self._inside = False
        elif name == "c":
            if self._cell is not None and self._cell.held.strip():
                if self._column in self._row:
                    raise _Refused("a cell is there twice")
                self._row[self._column] = self._cell
            self._cell = None
        elif name == "row" and self._row:
            self.found.append(self._row)
            self.numbers.append(self._number)


@dataclass
class _Texts:
    """Walks the table of text, and keeps the text at the places asked for."""

    wanted: Collection[int]
    found: dict[int, str] = field(default_factory=dict[int, str])
    _at: int = -1
    _inside: bool = False
    # How a word is said aloud, in some scripts. It is not part of the text.
    _spoken: int = 0

    def start(self, name: str, _: dict[str, str]) -> None:
        if name == "si":
            self._at += 1
            if self._at in self.wanted:
                self.found[self._at] = ""
        elif name == "rPh":
            self._spoken += 1
        elif name == "t":
            self._inside = True

    def characters(self, piece: str) -> None:
        if self._inside and not self._spoken and self._at in self.found:
            if len(self.found[self._at]) + len(piece) > TEXT_LENGTH:
                raise _Refused("a cell holds more than a cell can")
            self.found[self._at] += piece

    def end(self, name: str) -> None:
        if name == "t":
            self._inside = False
        elif name == "rPh":
            self._spoken -= 1
        elif name == "si" and len(self.found) == len(self.wanted):
            raise Finished


def _column_of(letters: str) -> int:
    """The column a cell stands in, from the letters of a reference such as `AB12`. From 0."""
    number = 0
    for letter in letters:
        number = number * 26 + ord(letter) - ord("A") + 1
    return number - 1


def _walk(
    archive: zipfile.ZipFile,
    part: str,
    start: Start | None = None,
    end: End | None = None,
    text: Text | None = None,
) -> None:
    """Walk one part of the workbook once. A part that cannot be read stops the step."""
    over = _Refused("a part of it is larger than a workbook's is")
    try:
        with archive.open(part) as source:
            read(Limited(source, PART_LIMIT, over), start, end, text)
    except KeyError:
        raise _Refused("a part of it is missing") from None
    except MarkupError:
        raise _Refused("a part of it is not well formed") from None
    except (zipfile.BadZipFile, OSError, EOFError, NotImplementedError, RuntimeError):
        raise _Refused("a part of it could not be unpacked") from None


def _part_of(archive: zipfile.ZipFile, sheet: str) -> str:
    """The part of the zip that holds the sheet of this name."""
    targets: dict[str, str] = {}
    relations: list[str] = []

    def a_sheet(name: str, given: dict[str, str]) -> None:
        if name == "sheet" and given.get("name") == sheet:
            relations.append(given.get("id", ""))

    def a_relationship(name: str, given: dict[str, str]) -> None:
        if name == "Relationship" and "Id" in given and "Target" in given:
            targets[given["Id"]] = given["Target"]

    _walk(archive, WORKBOOK, start=a_sheet)
    if len(relations) != 1:
        raise _Refused("it does not hold the one sheet that is read")
    _walk(archive, RELATIONSHIPS, start=a_relationship)
    target = targets.get(relations[0], "")
    part = posixpath.normpath(
        target.lstrip("/") if target.startswith("/") else posixpath.join("xl", target)
    )
    if not target or part.startswith(".."):
        raise _Refused("it does not hold the one sheet that is read")
    return part


def _texts(archive: zipfile.ZipFile, rows: Sequence[dict[int, _Cell]]) -> dict[int, str]:
    """The text that the cells of some rows point at, from the table of text."""
    places = [cell.held.strip() for row in rows for cell in row.values() if cell.kind == IN_TABLE]
    if not all(place.isascii() and place.isdigit() for place in places):
        raise _Refused("a cell points at no text")
    wanted = {int(place) for place in places}
    if not wanted:
        return {}
    texts = _Texts(wanted)
    _walk(archive, STRINGS, texts.start, texts.end, texts.characters)
    if len(texts.found) != len(wanted):
        raise _Refused("a cell points at no text")
    return texts.found


def _value_of(cell: _Cell, texts: dict[int, str]) -> Value:
    if cell.kind == IN_TABLE:
        return texts[int(cell.held.strip())].strip() or None
    if cell.kind in IN_CELL:
        return cell.held.strip() or None
    if cell.kind != NUMBER:
        raise _Refused("a cell holds neither text nor a number")
    try:
        number = float(cell.held.strip())
    except ValueError:
        number = math.nan
    if not math.isfinite(number):
        raise _Refused("a cell holds neither text nor a number")
    return number


def _named(names: Mapping[int, Value], wanted: Sequence[str], what: str) -> dict[int, str]:
    """Where each name stands among the cells of a row. Each is there once."""
    at: dict[int, str] = {}
    for name in wanted:
        found = [column for column, held in names.items() if held == name]
        # The name is the one the step asked for, so it is the code's and not the file's.
        if not found:
            raise _Refused(f"the {what} {name} is missing")
        if len(found) > 1:
            raise _Refused(f"the {what} {name} is there twice")
        at[found[0]] = name
    return at


def _stands_over(archive: zipfile.ZipFile, part: str, column: int, row: int) -> range:
    """The columns a heading stands over: those of the cell the sheet merges from it."""
    found: list[range] = []

    def a_merge(name: str, given: dict[str, str]) -> None:
        if name != "mergeCell":
            return
        start, _, end = given.get("ref", "").partition(":")
        first, last = REFERENCE.fullmatch(start), REFERENCE.fullmatch(end)
        if first is None or last is None:
            raise _Refused("a merged cell is not as a workbook writes one")
        if (_column_of(first[1]), int(first[2])) == (column, row):
            if int(last[2]) != row:
                raise _Refused("a heading stands over more than one row")
            found.append(range(column, _column_of(last[1]) + 1))

    _walk(archive, part, start=a_merge)
    if len(found) != 1:
        raise _Refused("a heading stands over no columns")
    return found[0]


def _read(
    archive: zipfile.ZipFile,
    sheet: str,
    columns: Sequence[str],
    header_at: int,
    under: Under | None,
) -> list[Row]:
    part = _part_of(archive, sheet)
    below = header_at + (0 if under is None else 1)
    header = _Rows(first=header_at, last=below, columns=None)
    _walk(archive, part, header.start, header.end, header.characters)
    named = _texts(archive, header.found)
    rows_of_names = {
        number: {column: _value_of(cell, named) for column, cell in row.items()}
        for number, row in zip(header.numbers, header.found, strict=True)
    }
    if header_at not in rows_of_names:
        raise _Refused("the row that names the columns is empty")
    at = _named(rows_of_names[header_at], columns, "column")
    if under is not None:
        ((over, _),) = _named(rows_of_names[header_at], (under.heading,), "heading").items()
        span = _stands_over(archive, part, over, header_at)
        beneath = {
            column: held for column, held in rows_of_names.get(below, {}).items() if column in span
        }
        at |= _named(beneath, under.columns, "column")
        columns = (*columns, *under.columns)
    rows = _Rows(first=below + 1, last=None, columns=frozenset(at))
    _walk(archive, part, rows.start, rows.end, rows.characters)
    texts = _texts(archive, rows.found)
    empty: Row = dict.fromkeys(columns)
    return [
        empty | {at[column]: _value_of(cell, texts) for column, cell in row.items()}
        for row in rows.found
    ]


def read_sheet(
    opened: Opened,
    sheet: str,
    columns: Sequence[str],
    *,
    header_at: int = 1,
    under: Under | None = None,
) -> list[Row]:
    """The rows of one sheet, under the row that names its columns.

    `header_at` is the row that names the columns, as the workbook numbers its
    rows, from 1. Each row holds the columns asked for and no other. A cell
    that is empty is given as None, and a row in which every named column is
    empty is left out. A cell of text is given with no space round it.

    `under` names a heading of that row, and columns that are named in the row
    below it, among the columns the heading stands over. A row then holds
    those columns too, and the rows begin below both rows of names.
    """
    if under is not None and len({*columns, *under.columns}) != len(columns) + len(under.columns):
        raise ValueError("a column is asked for once, under a heading or not")
    try:
        with zipfile.ZipFile(opened.path) as archive:
            return _read(archive, sheet, columns, header_at, under)
    except (zipfile.BadZipFile, OSError):
        raise LockError("input_is_as_described", opened.file_id, "it is not a workbook") from None
    except _Refused as refused:
        raise LockError("input_is_as_described", opened.file_id, str(refused)) from None
