"""Counts a publisher rounds to 10, and what its own rows say of a dash.

The council tax tables of the Valuation Office Agency give every count as a
whole number of tens. They write `0` for nought, and `-` for a count they do
not give. Neither the table nor the notes beside it says what `-` means, or
how a count is rounded. So the reading is held to the file's own rows, and not
only reasoned.

The reading:

| The file writes | It is read as |
|---|---|
| `0` | Nothing was counted |
| `-` | 1 to 4 were counted: a count too small to round to 10 |
| A whole number of tens | A count within 5 of it |

The table holds a row for each LSOA and a row for each MSOA, which is made of
whole LSOAs. If the reading is right then, for every count of every MSOA:

1. Where every LSOA has `0`, the MSOA has `0`.
2. Where any LSOA has `-` or a number, the MSOA does not have `0`.
3. Where the MSOA has `-`, no LSOA has a number, and at most four have `-`.
4. Where the MSOA has a number, it is within 5 of the sum of its LSOAs for
   each LSOA and 5 for itself, with `-` read as nothing.

`disagrees` says which of these a row breaks. A measure asks it about every
area of the build before it gives a figure, and stops if any row does. On the
tables of 31 March 2025 no row of England breaks one.
"""

from collections.abc import Sequence

# Every count in the file is a whole number of these.
ROUNDED_TO = 10
# How far rounding can move one count: a count is within this of what the file writes.
ROUNDING = ROUNDED_TO // 2
# What the file writes for a count that is not nought and that it does not give.
TOO_SMALL = "-"
# The most a dash can hide. Five would be rounded to 10 and written.
MOST_HIDDEN = ROUNDING - 1

# A count as the file gives it. It is `None` where the file writes a dash.
Count = int | None


def disagrees(own: Count, parts: Sequence[Count]) -> str | None:
    """How an area's own count is not what the counts of its parts allow, or `None`.

    `own` is the publisher's count for the area and `parts` its counts for the
    smaller areas that make the area up. What is given back is a few fixed
    words, which repeat nothing from the file.
    """
    dashes = sum(part is None for part in parts)
    numbers = [part for part in parts if part]
    if not dashes and not numbers:
        return None if own == 0 else "an area holds a count and no part of it does"
    if own == 0:
        return "an area holds nought and a part of it does not"
    if own is None:
        if numbers or dashes > MOST_HIDDEN:
            return "a dash hides more than a small count"
        return None
    if abs(own - sum(numbers)) > ROUNDING * (len(parts) + 1):
        return "an area's count is not within rounding of its parts"
    return None
