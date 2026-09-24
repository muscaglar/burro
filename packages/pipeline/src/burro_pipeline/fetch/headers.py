"""Telling the row that names the columns from a row of data.

Describe prints column names and nothing else from a file. Some files have no
header: their first row is a sale, a person or a place. So a row is printed as
names only when all of this holds:

1. It is a full row, and it has at least two cells.
2. Every cell could be a name: it has a letter, it is not a number or a date,
   it is not empty and not long, and no name is there twice.
3. At least two rows stand under it.
4. Some column keeps one shape in the rows under it, such as a code or a
   number, and the cell above that column does not have that shape.

When any of these fails, no name is printed, and the reason is given in fixed
words. The rule errs towards printing nothing. What is left is a file with no
header whose cells are all text, where the first row alone breaks the shape of
a column under it: that row would be printed.
"""

import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

NAME_LENGTH = 200
KEPT = 60
UNDER = 20
FEWEST_UNDER = 2

A_DATE = re.compile(
    r"\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}([ T]\d{1,2}:\d{2}.*)?"
    r"|\d{1,2}(st|nd|rd|th)? [A-Za-z]{3,9},? \d{2,4}"
    r"|[A-Za-z]{3,9} \d{1,2},? \d{4}",
)

NOT_A_NAME = "the first full row holds a number, a date or an empty cell"
TWICE = "the first full row holds the same name twice"
ONE_COLUMN = "one column alone cannot be told from a row"
TOO_FEW = "too few rows stand under the first full row"
SAME_SHAPE = "the first full row is shaped like the rows under it"
NO_ROWS = "no row holds anything"

# A row as describe sees it: the text of each cell that holds something, by column.
# A cell that holds a number, a date or a truth value is given as the text "0".
Row = dict[int, str]


@dataclass(frozen=True)
class Names:
    """The column names of a table, or why none is given."""

    columns: tuple[str, ...] | None
    # Which of the rows handed over holds the names, counted from 0.
    at: int | None
    why: str | None


def is_number(text: str) -> bool:
    try:
        float(text.replace(",", ""))
    except ValueError:
        return False
    return True


def is_name(cell: str) -> bool:
    text = cell.strip()
    return (
        0 < len(text) <= NAME_LENGTH
        and any(sign.isalpha() for sign in text)
        and not is_number(text)
        and A_DATE.fullmatch(text) is None
    )


def shape(cell: str) -> str:
    """A cell with its letters and digits taken out: `E01000001` and `W01000002` are both `a9`."""
    text = cell.strip()
    if not text:
        return ""
    if is_number(text):
        return "9"
    found: list[str] = []
    for sign in text:
        kind = "a" if sign.isalpha() else "9" if sign.isdigit() else sign
        if not found or found[-1] != kind:
            found.append(kind)
    return "".join(found)


def _breaks_a_shape(first: Row, under: Sequence[Row]) -> bool:
    for column, cell in first.items():
        shapes = {shape(row[column]) for row in under if row.get(column, "").strip()}
        if len(shapes) == 1 and shapes != {shape(cell)}:
            seen = sum(1 for row in under if row.get(column, "").strip())
            if seen >= FEWEST_UNDER:
                return True
    return False


def find_names(rows: Sequence[Row], full: int) -> Names:
    """The names of a table's columns, from its first rows.

    `rows` are the first rows that hold anything, in order. `full` is how many
    cells a full row has: a row with fewer is a title or a note above the table.
    """
    at = next((index for index, row in enumerate(rows) if len(row) >= full), None)
    if at is None:
        return Names(None, None, NO_ROWS)
    first = rows[at]
    if len(first) < 2:
        return Names(None, None, ONE_COLUMN)
    if not all(is_name(cell) for cell in first.values()):
        return Names(None, None, NOT_A_NAME)
    names = tuple(first[column].strip() for column in sorted(first))
    if len(set(names)) != len(names):
        return Names(None, None, TWICE)
    under = [row for row in rows[at + 1 : at + 1 + UNDER] if row]
    if len(under) < FEWEST_UNDER:
        return Names(None, None, TOO_FEW)
    if not _breaks_a_shape(first, under):
        return Names(None, None, SAME_SHAPE)
    return Names(names, at, None)


def most_common_width(widths: Counter[int]) -> int:
    """How many cells a full row has: the width most rows have, and the wider on a tie."""
    return max(widths, key=lambda width: (widths[width], width)) if widths else 0
