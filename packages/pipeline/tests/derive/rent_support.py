"""What the tests of rents share: a made-up workbook and a made-up directory of postcodes.

Nothing here is real. The workbook is laid out as the statistics office lays
out its workbook of the rents of London: a cover, the contents, the notes, and
three tables, of which the second is by borough and the third by postcode
district. The places are those of the made-up town of the tests of cells. No
postcode begins with a Q, so no district here is a district, and every figure
was chosen so that a test can say which row it came from.

    columns  0    1    2    3    4    5        7
    row 1  | a1 | a2 | b1 | b2 | c1 | c2 |   | z1 |     each square is one output area
    row 0  | a3 | a4 | b3 | b4 | c3 | c4 |
             Quillhaven 001  002   Tallowgate 001   outside London

Where the homes of each area stand, by the postcodes in use of its output areas:

    area             homes   its output areas stand in                   so it takes the figure of
    Quillhaven 001   500     QH1, all four                               the district QH1
    Quillhaven 002   660     QH1, QH2 and QH3, one each, and one in none the borough: no district
                                                                         holds half of its homes
    Tallowgate 001   820     QT1, two of 390 homes, and QT2, two of 430  the district QT2

What the workbook gives, as the count of rents and the lower quartile, the
median and the upper quartile. `..` is not available, and `-` was withheld.

    place        room          studio          one bedroom         two bedrooms
    Quillhaven   ..            10 .. 1100 ..   520 1250 1500 1800  630 1600 1900 2300
    Tallowgate   30 700 800    50 1000 1200    240 1100 1300 1450  470 1400 1650 1800
                 900           1400
    QH1          ..            20 1026 1075    170 1300 1400 1450  230 1500 1650 1800
                               1119
    QT2          10 .. 650 ..  ..              60 1150 1275 1400   10 .. 1500 ..

    place        three bedrooms        four or more bedrooms
    Quillhaven   320 2000 2400 2900    100 2600 3300 4100
    Tallowgate   250 1700 1950 2100    - - - -
    QH1          100 1800 2000 2213    30 2500 2850 3500
    QT2          - - - -               ..

Every other district holds a canary in every cell, so that a figure taken from a
district an area does not lie in is seen.
"""

from collections.abc import Mapping, Sequence
from pathlib import Path

from burro_pipeline.evidence.receipt import Period, Receipt
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.postcodes_support import (
    MadeUpPostcode,
    directory_receipt,
    directory_zip,
    of_the_town,
    stored,
)
from ..cells.support import receipt_of
from .noise_support import Cell, Table, workbook

SOURCE = "ons-private-rental-market-london-postcode-district"
WORKBOOK_NAME = "londonrentalstatsaccessibleq12026.xlsx"
EDITION = "3389"
MONTHS = Period(start="2025-04", end="2026-03")
SAID_OF_THE_MONTHS = "April 2025 to March 2026"
# A rent found nowhere else. It stands in every row that no area may take.
CANARY_RENT = 9_876

COVER, CONTENTS, NOTES = "Cover sheet", "Contents", "Notes"
OF_LONDON, OF_BOROUGHS, OF_DISTRICTS = "1", "2", "3"
KINDS = (
    "Room",
    "Studio",
    "One Bedroom",
    "Two Bedrooms",
    "Three Bedrooms",
    "Four or More Bedrooms",
)
FIGURES = ("Count of rents", "Mean", "Lower quartile", "Median", "Upper quartile")
NONE, WITHHELD = "..", "-"
Row = tuple[Cell, Cell, Cell, Cell]
NOT_AVAILABLE: Row = (NONE, NONE, NONE, NONE)
SUPPRESSED: Row = (WITHHELD, WITHHELD, WITHHELD, WITHHELD)
A_CANARY: Row = (60, CANARY_RENT, CANARY_RENT, CANARY_RENT)

QUILLHAVEN, TALLOWGATE = "Quillhaven", "Tallowgate"
QH1, QH2, QH3, QT1, QT2, NO_AREA_LIES_IN = "QH1", "QH2", "QH3", "QT1", "QT2", "QZ9"
Q1, Q2, T1 = "lon-ne02999001", "lon-ne02999002", "lon-ne02999003"
AREAS = (Q1, Q2, T1)

# The count of rents, the lower quartile, the median and the upper quartile of each kind of
# home, in the order of `KINDS`.
BOROUGHS: Mapping[str, Sequence[Row]] = {
    QUILLHAVEN: (
        NOT_AVAILABLE,
        (10, NONE, 1_100, NONE),
        (520, 1_250, 1_500, 1_800),
        (630, 1_600, 1_900, 2_300),
        (320, 2_000, 2_400, 2_900),
        (100, 2_600, 3_300, 4_100),
    ),
    TALLOWGATE: (
        (30, 700, 800, 900),
        (50, 1_000, 1_200, 1_400),
        (240, 1_100, 1_300, 1_450),
        (470, 1_400, 1_650, 1_800),
        (250, 1_700, 1_950, 2_100),
        SUPPRESSED,
    ),
}
DISTRICTS: Mapping[str, Sequence[Row]] = {
    QH1: (
        NOT_AVAILABLE,
        (20, 1_026, 1_075, 1_119),
        (170, 1_300, 1_400, 1_450),
        (230, 1_500, 1_650, 1_800),
        (100, 1_800, 2_000, 2_213),
        (30, 2_500, 2_850, 3_500),
    ),
    QH2: (A_CANARY,) * 6,
    QH3: (A_CANARY,) * 6,
    QT1: (A_CANARY,) * 6,
    QT2: (
        (10, NONE, 650, NONE),
        NOT_AVAILABLE,
        (60, 1_150, 1_275, 1_400),
        (10, NONE, 1_500, NONE),
        SUPPRESSED,
        NOT_AVAILABLE,
    ),
    NO_AREA_LIES_IN: (A_CANARY,) * 6,
}

# The postcodes in use of the made-up town, each in the output area its point stands in.
IN_USE = (
    MadeUpPostcode("QH1 1CK", (50, 150)),
    MadeUpPostcode("QH1 2CK", (150, 150)),
    MadeUpPostcode("QH1 3CK", (50, 50)),
    MadeUpPostcode("QH1 4CK", (150, 50)),
    MadeUpPostcode("QH1 5CK", (250, 150)),
    MadeUpPostcode("QH2 1CK", (350, 150)),
    MadeUpPostcode("QH3 1CK", (250, 50)),
    MadeUpPostcode("QT1 1CK", (450, 150)),
    MadeUpPostcode("QT1 2CK", (550, 150)),
    MadeUpPostcode("QT2 1CK", (450, 50)),
    # An output area with postcodes of two districts stands in the district of most of them.
    MadeUpPostcode("QT1 3CK", (550, 50)),
    MadeUpPostcode("QT2 2CK", (560, 60)),
    MadeUpPostcode("QT2 3CK", (570, 70)),
)
# A postcode that has ended counts towards no district: the fourth output area of
# Quillhaven 002 holds this one alone.
ENDED = MadeUpPostcode("QH2 9CK", (350, 50), ended="201903")
OUTSIDE = MadeUpPostcode("QZ9 1CK", (750, 150))
DIRECTORY = (*IN_USE, ENDED, OUTSIDE)

# What the cover and the notes say, in the publisher's own words. The step holds the
# workbook to each sentence that a page of Burro rests on.
SAID_ON_THE_COVER = (
    f"Private Rental Market in London: {SAID_OF_THE_MONTHS}",
    "These statistics are not comparable with the Office for National Statistics' Official "
    "Statistics releases on the private rental market. Both use the Valuation Office Agency's "
    "data collected by Rent Officers from landlords and letting agents, however, the sample "
    "and methodology used to produce the figures is not the same.\n\nThe data in this "
    "worksheet have been published in response to an ad-hoc request. It must be noted that no "
    "attempt has been made to account for the change in quality or composition of rented "
    "property in these statistics, so should be interpreted with caution. ",
    "Publication dates",
    "Made up for a test. It describes no real place.",
    "Source",
    "The main sources of data used in this worksheet is from VOA's administrative database.",
)
SAID_IN_THE_NOTES: Mapping[str, str] = {
    "note 1": "All averages and measures are expressed in £ values and rounded to the nearest £1.",
    "note 2": "Counts are rounded to the nearest 10.",
    "note 3": "Private rents data are collected by Rent Officers as part of their "
    "responsibilities to administer functions relating to Housing Benefit and Universal "
    "Credit. Rent Officers collect rental prices from letting agents and landlords who are "
    "willing to provide data. The sample is purposive, but Rent Officers use Census data to "
    "set collection aims that are representative of the private rental market.\n \nDue to the "
    "sampling approach being purposive, data collection may not be consistent over time and "
    "these statistics should not be compared across time periods or between areas.\n \nThese "
    "statistics are not comparable with the average monthly private rent prices for England "
    "which are published within the Office for National Statistics' Price Index of Private "
    "Rents. This is because, although they both use the Valuation Office Agency's data, the "
    "methodologies used to produce the statistics are different.",
    "note 4": "Housing Benefit claimants are not included in the sample.",
    "note 5": "Statistics derived from fewer than five observations have been suppressed and "
    "denoted by '-'.",
    "note 6": "Values denoted by '.'  are not applicable.",
    "note 7": "Values denoted by '..' are not available.",
}


def described(of: str, months: str = SAID_OF_THE_MONTHS) -> str:
    """What the contents say of a table, and what the table says of itself in its first row."""
    return f"Summary of monthly rents recorded between {months} by {of} for London"


HOLDS: Mapping[str, str] = {
    OF_LONDON: "bedroom category",
    OF_BOROUGHS: "borough and bedroom category",
    OF_DISTRICTS: "postcode district and bedroom category",
}


def listed(months: str = SAID_OF_THE_MONTHS, **changed: str) -> list[list[Cell]]:
    """The contents: two rows of words, the row that names the columns, and a row a table."""
    every = {sheet: described(of, months) for sheet, of in HOLDS.items()} | changed
    return [
        ["Table of contents"],
        ["This worksheet contains one table."],
        ["Worksheet Number", "Worksheet Title"],
        *([f"Worksheet {sheet}", said] for sheet, said in every.items()),
    ]


def noted(notes: Mapping[str, str] = SAID_IN_THE_NOTES) -> list[list[Cell]]:
    return [
        ["Notes"],
        ["This worksheet contains one table."],
        ["Note number", "Note text"],
        *([number, said] for number, said in notes.items()),
    ]


def table_of(
    sheet: str,
    places: Mapping[str, Sequence[Row]],
    *,
    named: str,
    kinds: Sequence[str] = KINDS,
    columns: Sequence[str] | None = None,
) -> list[list[Cell]]:
    """A table of figures: its title, a line of words, its header, and a row for each place
    and kind of home. The mean is never read, and holds a canary."""
    header: list[Cell] = list(columns or (named, "Bedroom Category", *FIGURES))
    found: list[list[Cell]] = [
        [f"{described(HOLDS[sheet])} [note 1, 2, 3, 4, 5, 6, 7]"],
        ["This worksheet contains one table. Some cells refer to notes."],
        header,
    ]
    for place, rows in places.items():
        for kind, (count, lower, median, upper) in zip(kinds, rows, strict=True):
            found.append([place, kind, count, CANARY_RENT, lower, median, upper])
    return found


def of_london(kind: str) -> list[Cell]:
    """One row of the table of London as a whole, which is never read: a canary in each cell."""
    return [kind, 60, CANARY_RENT, CANARY_RENT, CANARY_RENT, CANARY_RENT]


def book(
    boroughs: Mapping[str, Sequence[Row]] = BOROUGHS,
    districts: Mapping[str, Sequence[Row]] = DISTRICTS,
    *,
    cover: Sequence[Cell] = SAID_ON_THE_COVER,
    contents_of: Table | None = None,
    notes: Mapping[str, str] = SAID_IN_THE_NOTES,
    kinds: Sequence[str] = KINDS,
    sheets: Mapping[str, Table | bytes] | None = None,
    without: Sequence[str] = (),
) -> bytes:
    """The made-up workbook: the cover, the contents, the notes and the three tables."""
    every: dict[str, Table | bytes] = {
        COVER: [[said] for said in cover],
        CONTENTS: listed() if contents_of is None else contents_of,
        NOTES: noted(notes),
        OF_LONDON: [
            [described(HOLDS[OF_LONDON])],
            ["This worksheet contains one table."],
            ["Bedroom Category", *FIGURES],
            *(of_london(kind) for kind in KINDS),
        ],
        OF_BOROUGHS: table_of(OF_BOROUGHS, boroughs, named="Borough", kinds=kinds),
        OF_DISTRICTS: table_of(OF_DISTRICTS, districts, named="Postcode District", kinds=kinds),
    }
    every |= sheets or {}
    return workbook({name: table for name, table in every.items() if name not in without})


def receipt(
    content: bytes,
    period: Period | None = None,
    name: str = WORKBOOK_NAME,
    use: Use = Use.SCORING,
) -> Receipt:
    """The receipt of a made-up workbook that stands in for a fetched one."""
    made = receipt_of(SOURCE, use, name, content, EDITION)
    return made.model_copy(update={"data_period": period or MONTHS})


def inputs_of(
    folder: Path,
    content: bytes | None = None,
    *,
    directory: Sequence[MadeUpPostcode] | None = DIRECTORY,
    period: Period | None = None,
    name: str = WORKBOOK_NAME,
    given: Registry | None = None,
    with_a_receipt: bool = True,
) -> Inputs:
    """The made-up town, the made-up directory and the made-up workbook in a store of their own.

    With no directory the directory has no receipt, and with `with_a_receipt`
    false the workbook has none.
    """
    every = [*of_the_town()]
    if with_a_receipt:
        held = book() if content is None else content
        every.append((receipt(held, period, name), held))
    if directory is not None:
        zipped = directory_zip(directory)
        every.append((directory_receipt(zipped), zipped))
    return stored(folder, every, given)
