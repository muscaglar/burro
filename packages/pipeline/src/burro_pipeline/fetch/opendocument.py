"""Reading the shape of an OpenDocument workbook with the standard library.

An `.ods` file is a zip of XML, and one part of it, `content.xml`, holds every
sheet. It is read once, in a stream, so a large workbook needs little memory.
What is given of each sheet is what is given of a sheet of any workbook: its
name, the names of its columns where a row can be told to be names, and how
many rows hold anything.

A spreadsheet program ends a row with a run of empty cells and a sheet with a
run of empty rows, each written once with a count. A run is counted and never
walked.

No number is kept. A cell that holds a number, a date or a truth value is
kept as the text "0", as the reader of the other kind of workbook keeps one,
so a row of figures is never taken for a row of names and no figure is given.

A workbook says what it is on a cover and in its notes, and over and under
a table. Those are words and no part of its layout, so they are given of one
sheet alone, and only when the sheet is named. What is given is each row of
that sheet that holds words alone, wherever it stands, with the column each
cell stands in. A row that holds a number is never given. So the title over a
table, the rows that name its columns and the notes under it are given, and
no row of its figures. A date is given as the day the cell holds, because a
cover dates its file with one.
"""

import math
import zipfile
import zlib
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from burro_pipeline.fetch.headers import KEPT, Row, find_names
from burro_pipeline.fetch.markup import Limited, MarkupError, read

# The part of the zip that holds every sheet.
CONTENT = "content.xml"
# How much of the part is read once unpacked.
PART_LIMIT = 4 * 1024 * 1024 * 1024
# The most of one cell that is kept.
TEXT_LENGTH = 1000
# The most columns a sheet can hold. A cell that holds something stands in one of them.
MOST_COLUMNS = 16_384
# Stands for a cell that holds a number, a date or a truth value.
NOT_TEXT = "0"
# A row that is repeated is kept this many times at most. Twice is enough to be seen.
AT_MOST = 2
# How many rows of words are given of the one sheet that is named.
WORDS_KEPT = 200
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
# The kinds of cell whose value is a day, as the format names them.
DAYS = ("date",)


class OpenDocumentError(Exception):
    """The workbook could not be read. The message repeats nothing from it."""


@dataclass
class _Sheet:
    name: str
    hidden: bool
    # The first rows that hold anything, each with the number the sheet gives it.
    first: list[tuple[int, Row]] = field(default_factory=list[tuple[int, Row]])
    # The rows that hold words alone, where the sheet is the one that was named.
    said: list[tuple[int, Row]] = field(default_factory=list[tuple[int, Row]])
    rows: int = 0
    widths: Counter[int] = field(default_factory=Counter[int])


@dataclass
class _Walk:
    """Walks every sheet once. It counts the rows of each and keeps the first of them."""

    # The one sheet whose words are kept, or none.
    words_of: str | None = None
    found: list[_Sheet] = field(default_factory=list[_Sheet])
    # The styles of a sheet that say it is not shown.
    _hidden: set[str] = field(default_factory=set[str])
    _style: str | None = None
    _sheet: _Sheet | None = None
    # How deep in tables the walk is. A table inside a cell is not a sheet.
    _tables: int = 0
    _number: int = 0
    _repeated: int = 1
    _row: Row | None = None
    _words: Row | None = None
    _all_words: bool = True
    _column: int = 0
    _across: int = 1
    _kind: str = ""
    _day: str = ""
    _pieces: list[str] | None = None
    _length: int = 0
    _paragraphs: int = 0
    # How deep in a paragraph, and in a note on a cell, the walk is.
    _inside: int = 0
    _notes: int = 0

    def start(self, name: str, given: dict[str, str]) -> None:
        if name == "table":
            self._tables += 1
            if self._tables == 1:
                hidden = given.get("style-name", "") in self._hidden
                self._sheet, self._number = _Sheet(given.get("name", ""), hidden), 0
        elif self._tables == 0:
            self._a_style(name, given)
        elif self._tables != 1:
            return
        elif name == "table-row":
            self._repeated = _count(given.get("number-rows-repeated"))
            self._row, self._words, self._column, self._all_words = {}, {}, 0, True
        elif name in ("table-cell", "covered-table-cell") and self._row is not None:
            self._across = _count(given.get("number-columns-repeated"))
            self._kind = given.get("value-type", "")
            self._day = given.get("date-value", "")
            text = given.get("string-value")
            self._pieces = [] if text is None else [text[:TEXT_LENGTH]]
            self._length = len(text or "")
            # Text written on the cell itself is what the cell holds, and not what it shows.
            self._paragraphs = -1 if text is not None else 0
        elif self._pieces is not None:
            self._inside_a_cell(name, given)

    def _a_style(self, name: str, given: dict[str, str]) -> None:
        if name == "style":
            self._style = given.get("name") if given.get("family") == "table" else None
        elif name == "table-properties" and self._style and given.get("display") == "false":
            self._hidden.add(self._style)

    def _inside_a_cell(self, name: str, given: dict[str, str]) -> None:
        if name == "annotation":
            self._notes += 1
        elif self._notes or self._paragraphs < 0:
            return
        elif name == "p":
            self._inside += 1
            if self._paragraphs:
                self._add("\n")
            self._paragraphs += 1
        elif self._inside and name == "s":
            self._add(" " * min(_count(given.get("c")), TEXT_LENGTH))
        elif self._inside and name in ("tab", "line-break"):
            self._add(" ")

    def _add(self, piece: str) -> None:
        if self._pieces is None or self._length >= TEXT_LENGTH:
            return
        piece = piece[: TEXT_LENGTH - self._length]
        self._length += len(piece)
        self._pieces.append(piece)

    def characters(self, piece: str) -> None:
        if self._inside and not self._notes and self._tables == 1 and self._paragraphs > 0:
            self._add(piece)

    def end(self, name: str) -> None:
        if name == "table":
            self._tables -= 1
            if self._tables == 0 and self._sheet is not None:
                self.found.append(self._sheet)
                self._sheet = None
        elif name == "style":
            self._style = None
        elif self._tables != 1:
            return
        elif name == "annotation":
            self._notes = max(0, self._notes - 1)
        elif name == "p" and not self._notes:
            self._inside = max(0, self._inside - 1)
        elif name in ("table-cell", "covered-table-cell") and self._pieces is not None:
            self._end_of_a_cell()
        elif name == "table-row" and self._row is not None:
            self._end_of_a_row()

    def _end_of_a_cell(self) -> None:
        text = "".join(self._pieces or ()).strip()
        holds_a_value = bool(self._kind) and self._kind != "string"
        held = NOT_TEXT if holds_a_value else text
        a_day = self._kind in DAYS and bool(self._day)
        said = self._day[:TEXT_LENGTH] if a_day else held
        self._pieces, self._inside, self._notes = None, 0, 0
        if held and self._row is not None and self._words is not None:
            self._all_words = self._all_words and (a_day or not holds_a_value)
            if self._column + self._across > MOST_COLUMNS:
                raise OpenDocumentError("a row runs past the last column")
            for column in range(self._column, self._column + self._across):
                self._row[column], self._words[column] = held, said
        self._column += self._across

    def _end_of_a_row(self) -> None:
        sheet, row, words = self._sheet, self._row, self._words
        self._row = self._words = None
        first = self._number + 1
        self._number += self._repeated
        if sheet is None or not row or words is None:
            return
        sheet.rows += self._repeated
        sheet.widths[len(row)] += self._repeated
        for nth in range(min(self._repeated, AT_MOST)):
            if len(sheet.first) < KEPT:
                sheet.first.append((first + nth, row))
        if self._all_words and sheet.name == self.words_of and len(sheet.said) < WORDS_KEPT:
            sheet.said.append((first, words))


def _count(written: str | None) -> int:
    """How many times a cell or a row is repeated. Once, where the file does not say."""
    if written is None:
        return 1
    if not (written.isascii() and written.isdigit() and 0 < int(written) <= 2**31):
        raise OpenDocumentError("a cell or a row is repeated a number of times that is no number")
    return int(written)


def _walked(path: Path, limit: int, words_of: str | None) -> list[_Sheet]:
    walk = _Walk(words_of)
    over = OpenDocumentError("a part of the workbook is over the size limit")
    try:
        with zipfile.ZipFile(path) as archive, archive.open(CONTENT) as source:
            read(Limited(source, limit, over), walk.start, walk.end, walk.characters)
    except KeyError:
        raise OpenDocumentError("a part of the workbook is missing") from None
    except MarkupError as error:
        raise OpenDocumentError(str(error)) from None
    except (zipfile.BadZipFile, zlib.error, OSError, EOFError, NotImplementedError, RuntimeError):
        raise OpenDocumentError("a part of the workbook could not be unpacked") from None
    if not walk.found:
        raise OpenDocumentError("the workbook lists no sheet")
    return walk.found


def sheets(
    path: Path, limit: int = PART_LIMIT, words_of: str | None = None
) -> list[dict[str, object]]:
    """Each sheet of a workbook: its name, its column names if they can be told, its rows.

    With `words_of`, the sheet of that name gives its words too: each row of
    it that holds words alone, with the column each cell stands in.
    """
    found = _walked(path, limit, words_of)
    if words_of is not None and words_of not in {sheet.name for sheet in found}:
        raise OpenDocumentError("it holds no sheet of the name that was given")
    return [_described(sheet, sheet.name == words_of) for sheet in found]


def letters(column: int) -> str:
    """The name a spreadsheet program gives a column, counted from 0: A, B, and AA after Z."""
    found = ""
    number = column + 1
    while number:
        number, last = divmod(number - 1, len(LETTERS))
        found = LETTERS[last] + found
    return found


def _described(sheet: _Sheet, with_words: bool) -> dict[str, object]:
    widest = max(sheet.widths, default=0)
    names = find_names([row for _, row in sheet.first], max(1, math.ceil(widest / 2)))
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
    if with_words:
        found["words"] = [
            {"row": number, "cells": {letters(column): row[column] for column in sorted(row)}}
            for number, row in sheet.said
        ]
    return found
