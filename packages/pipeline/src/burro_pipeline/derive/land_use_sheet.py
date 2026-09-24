"""One table of an OpenDocument workbook, found by the names of its columns.

The land use statistics are published as an OpenDocument spreadsheet. It is a
zip, and one part of it, `content.xml`, holds every sheet. No page of the
publisher says what the sheets are called, which row names the columns, or
what the column of codes is called. So the reader is told none of them. It is
told what follows, and finds the table by it:

- The names of the columns that are read, each with the ways its publisher
  spells it. The row that names the columns is the first row of a sheet, among
  its first rows, that holds every one of them.
- The names that stand over a total. A workbook that groups its columns gives
  a group of one column no name in the row of names: it calls the column a
  total there, and names the group in a row above. Such a column is found by
  the name over it, and only in a column the row of names calls a total.
- The shape of a code. The column of codes is the first column in which a row
  under the names holds a code of that shape, and a row of the table is a row
  that holds one there.
- The word for the unit, where the step gives one. A workbook may hold the
  same table twice, in two units. The table is the sheet that holds the word
  alone in a cell above the names of its columns.

A sheet that names the columns and holds no code of that shape is not the
table: the workbook holds the same columns for larger areas. Two sheets that
both hold the table stop the step, because nothing here may pick one.

What is kept and what is not:

- A row holds its code and the columns that are named, and no other, so that a
  step cannot use a column it did not name.
- A name is compared without its case and its spacing, and whole: a column
  named for a group is not the column of a category whose name it starts with.
- A number is read from the value the cell holds, and never from how the cell
  shows it. An empty cell is nothing, and is never nought.
- A note on a cell is no part of what the cell holds.

It is read with the standard library, once, a piece at a time. A spreadsheet
program ends a row with a run of empty cells and a sheet with a run of empty
rows, each written once with a count. A run is counted and never walked, so a
sheet of a million empty rows costs nothing.

A workbook that is not laid out as the step expects stops the step, in a few
fixed words that repeat nothing from the file. A column the table lacks is
named, by the name the step asked for it by.
"""

import math
import re
import zipfile
import zlib
from collections.abc import Collection, Mapping
from dataclasses import dataclass, field

from burro_pipeline.evidence.lock import LockError
from burro_pipeline.fetch.markup import Limited, MarkupError, read
from burro_pipeline.inputs import Opened

# The part of the zip that holds every sheet.
CONTENT = "content.xml"
# How much of the part is read once unpacked.
PART_LIMIT = 4 * 1024 * 1024 * 1024
# The longest text a cell of a spreadsheet can hold.
TEXT_LENGTH = 32_767
# The most columns a sheet can hold. A cell that holds something stands in one of them.
MOST_COLUMNS = 16_384
# The names of the columns are looked for in this many of the first rows of each sheet.
WITHIN = 30
# The kinds of cell that hold a number, as the format names them.
NUMBERS = ("float", "percentage", "currency")
# A row that is repeated is given this many times at most. Twice is enough to be seen.
AT_MOST = 2

# What a cell of a named column holds: text, a number, or nothing.
Value = str | float | None


class _Refused(Exception):
    """The workbook is not as the step expects. It holds the fixed words that say how."""


@dataclass(frozen=True)
class Row:
    """One row of the table: its code, and what it holds in the columns that were named."""

    code: str
    held: Mapping[str, Value]


@dataclass(frozen=True)
class Table:
    """The rows of the one table the workbook holds, and where its columns were named."""

    rows: tuple[Row, ...]
    # The row that names the columns, as the sheet numbers its rows, from 1.
    header_at: int
    # The rows under the names that hold no code: a row of units, of a larger area, of notes.
    others: int


def fold(text: str) -> str:
    """A name as it is compared: without its case, and with one space between its words."""
    return " ".join(text.split()).casefold()


@dataclass
class _Sheet:
    """What was found in one sheet."""

    # The name each column is asked for by, by the place of the column, from 0.
    header: dict[int, str] | None = None
    header_at: int = 0
    key_at: int | None = None
    rows: list[Row] = field(default_factory=list[Row])
    others: int = 0
    # The rows that stand above the names of the columns.
    above: list[Mapping[int, Value]] = field(default_factory=list[Mapping[int, Value]])
    # Whether a cell above the names holds the word for the unit, where one was given.
    says_the_unit: bool = True


@dataclass
class _Walk:
    """Walks every sheet once, and keeps the rows of each sheet that names the columns."""

    # The name a column is asked for by, by each way it is spelt, folded.
    spelt: Mapping[str, str]
    asked: tuple[str, ...]
    key: re.Pattern[str]
    within: int
    # The name a column is asked for by, by each way it is spelt over a total, folded.
    over: Mapping[str, str] = field(default_factory=dict[str, str])
    # What the row of names calls a total, folded.
    total: str = ""
    # The ways the word for the unit is spelt, folded. With none, no sheet is asked for one.
    unit: frozenset[str] = frozenset()
    found: list[_Sheet] = field(default_factory=list[_Sheet])
    # The most of the names that any one row held, where no row held them all.
    nearest: frozenset[str] = frozenset()
    _sheet: _Sheet | None = None
    # How deep in tables the walk is. A table inside a cell is not a sheet.
    _tables: int = 0
    _number: int = 0
    _repeated: int = 1
    _row: dict[int, Value] | None = None
    _column: int = 0
    _across: int = 1
    _kind: str = ""
    _value: str | None = None
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
                self._sheet, self._number = _Sheet(), 0
        elif self._tables != 1:
            return
        elif name == "table-row":
            self._repeated = _count(given.get("number-rows-repeated"))
            self._row, self._column = {}, 0
        elif name in ("table-cell", "covered-table-cell") and self._row is not None:
            self._across = _count(given.get("number-columns-repeated"))
            self._kind = given.get("value-type", "")
            self._value = given.get("value")
            text = given.get("string-value")
            self._pieces = [] if text is None else [text]
            self._length = len(text or "")
            # Text written on the cell itself is what the cell holds, and not what it shows.
            self._paragraphs = -1 if text is not None else 0
        elif self._pieces is not None:
            self._inside_a_cell(name, given)

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
            self._add(" " * min(_count(given.get("c")), TEXT_LENGTH + 1))
        elif self._inside and name in ("tab", "line-break"):
            self._add(" ")

    def _add(self, piece: str) -> None:
        if self._pieces is None:
            return
        self._length += len(piece)
        if self._length > TEXT_LENGTH:
            raise _Refused("a cell holds more than a cell can")
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
        elif self._tables != 1:
            return
        elif name == "annotation":
            self._notes = max(0, self._notes - 1)
        elif name == "p" and not self._notes:
            self._inside = max(0, self._inside - 1)
        elif name in ("table-cell", "covered-table-cell") and self._pieces is not None:
            self._end_of_a_cell()
        elif name == "table-row" and self._row is not None:
            row, self._row = self._row, None
            first = self._number + 1
            self._number += self._repeated
            if row:
                for nth in range(min(self._repeated, AT_MOST)):
                    self._take(first + nth, row)

    def _end_of_a_cell(self) -> None:
        held = self._held()
        self._pieces, self._inside, self._notes = None, 0, 0
        if held is not None and self._row is not None:
            if self._column + self._across > MOST_COLUMNS:
                raise _Refused("a row runs past the last column")
            for column in range(self._column, self._column + self._across):
                self._row[column] = held
        self._column += self._across

    def _held(self) -> Value:
        """What the cell that has just ended holds."""
        if self._kind in NUMBERS:
            try:
                number = float(self._value or "")
            except ValueError:
                number = math.nan
            if not math.isfinite(number):
                raise _Refused("a cell holds a number that is no number")
            return number
        return "".join(self._pieces or ()).strip() or None

    def _take(self, number: int, row: Mapping[int, Value]) -> None:
        sheet = self._sheet
        if sheet is None:
            return
        if sheet.header is None:
            if number <= self.within:
                self._look_for_the_names(sheet, number, row)
            return
        if sheet.key_at is None:
            sheet.key_at = next(
                (column for column in sorted(row) if self._is_a_code(row[column])), None
            )
        code = None if sheet.key_at is None else row.get(sheet.key_at)
        if not (isinstance(code, str) and self.key.fullmatch(code)):
            sheet.others += 1
            return
        held = {name: row.get(column) for column, name in sheet.header.items()}
        sheet.rows.append(Row(code, {name: held[name] for name in self.asked}))

    def _is_a_code(self, held: Value) -> bool:
        return isinstance(held, str) and self.key.fullmatch(held) is not None

    def _look_for_the_names(self, sheet: _Sheet, number: int, row: Mapping[int, Value]) -> None:
        at: dict[str, list[int]] = {}
        for column in sorted(row):
            held = row[column]
            name = self.spelt.get(fold(held)) if isinstance(held, str) else None
            if name is not None:
                at.setdefault(name, []).append(column)
        for name, column in self._over_a_total(sheet, row):
            at.setdefault(name, []).append(column)
        if len(at) < len(self.asked):
            if len(at) > len(self.nearest):
                self.nearest = frozenset(at)
            sheet.above.append(row)
            return
        for name in self.asked:
            if len(at[name]) > 1:
                # The name is the one the step asked for, so it is the code's and not the file's.
                raise _Refused(f"the column {name} is there twice")
        sheet.header = {columns[0]: name for name, columns in at.items()}
        sheet.header_at = number
        sheet.says_the_unit = not self.unit or any(
            isinstance(held, str) and fold(held) in self.unit
            for above in sheet.above
            for held in above.values()
        )

    def _over_a_total(self, sheet: _Sheet, row: Mapping[int, Value]) -> list[tuple[str, int]]:
        """The columns this row calls a total that a row above names, each with its name."""
        found: list[tuple[str, int]] = []
        if not self.over:
            return found
        totals = [
            column
            for column in sorted(row)
            if isinstance(held := row[column], str) and fold(held) == self.total
        ]
        for column in totals:
            for above in sheet.above:
                held = above.get(column)
                name = self.over.get(fold(held)) if isinstance(held, str) else None
                if name is not None:
                    found.append((name, column))
        return found


def _count(written: str | None) -> int:
    """How many times a cell or a row is repeated. Once, where the file does not say."""
    if written is None:
        return 1
    if not (written.isascii() and written.isdigit() and 0 < int(written) <= 2**31):
        raise _Refused("a cell or a row is repeated a number of times that is no number")
    return int(written)


def _spelt(columns: Mapping[str, Collection[str]], whole: bool = True) -> dict[str, str]:
    found: dict[str, str] = {}
    for name, spellings in columns.items():
        for spelling in spellings:
            if found.setdefault(fold(spelling), name) != name:
                raise ValueError("a spelling is given for one column and no other")
    if whole and (not found or any(not spellings for spellings in columns.values())):
        raise ValueError("every column that is read is given a spelling")
    return found


def _the_table(walk: _Walk) -> Table:
    """The one sheet that names the columns and holds a code, or the words that say why not."""
    named = [sheet for sheet in walk.found if sheet.header is not None]
    coded = [sheet for sheet in named if sheet.rows]
    tables = [sheet for sheet in coded if sheet.says_the_unit]
    if len(tables) > 1:
        raise _Refused("more than one sheet holds the table")
    if tables:
        return Table(tuple(tables[0].rows), tables[0].header_at, tables[0].others)
    if coded:
        raise _Refused("no sheet that holds the table says its unit")
    if named:
        raise _Refused("no row under the names of the columns holds a code")
    if walk.nearest:
        missing = next(name for name in walk.asked if name not in walk.nearest)
        raise _Refused(f"the column {missing} is missing")
    raise _Refused("no row names the columns")


def _read(archive: zipfile.ZipFile, walk: _Walk) -> Table:
    over = _Refused("a part of it is larger than a workbook's is")
    try:
        with archive.open(CONTENT) as source:
            read(Limited(source, PART_LIMIT, over), walk.start, walk.end, walk.characters)
    except KeyError:
        raise _Refused("a part of it is missing") from None
    except MarkupError:
        raise _Refused("a part of it is not well formed") from None
    except (zipfile.BadZipFile, zlib.error, OSError, EOFError, NotImplementedError, RuntimeError):
        raise _Refused("a part of it could not be unpacked") from None
    return _the_table(walk)


def read_table(
    opened: Opened,
    columns: Mapping[str, Collection[str]],
    key: re.Pattern[str],
    *,
    within: int = WITHIN,
    over: Mapping[str, Collection[str]] | None = None,
    total: str = "Total",
    unit: Collection[str] = (),
) -> Table:
    """The rows of the one table that names every column given and holds a code.

    `columns` gives each column by the name the step asks for it by, with the
    ways its publisher spells it. `key` is the shape of a code. The names are
    looked for in the first `within` rows of each sheet. A cell that is empty
    is given as None, and a cell of text with no space round it.

    `over` gives the ways a column is spelt in a row above the names, where
    the row of names calls the column `total`. `unit` gives the ways the unit
    is spelt: with one, the table is the sheet that holds it alone in a cell
    above the names.
    """
    if over is not None and not set(over) <= set(columns):
        raise ValueError("a column that is named over a total is a column that is read")
    walk = _Walk(
        _spelt(columns),
        tuple(columns),
        key,
        within,
        over=_spelt(over or {}, whole=False),
        total=fold(total),
        unit=frozenset(fold(word) for word in unit),
    )
    try:
        with zipfile.ZipFile(opened.path) as archive:
            return _read(archive, walk)
    except (zipfile.BadZipFile, OSError):
        raise LockError("input_is_as_described", opened.file_id, "it is not a workbook") from None
    except _Refused as refused:
        raise LockError("input_is_as_described", opened.file_id, str(refused)) from None
