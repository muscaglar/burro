"""What the tests of prices paid share: made-up files of sales, laid out as the publisher's.

Nothing here is real. The sales stand on the made-up town of the tests of
cells, at the made-up postcodes of `tests/cells/postcodes_support.py`. No
postcode here is one that has been given out, no address is an address, and
every price was chosen so that a test can say which sales a figure came from.

    columns  0    1    2    3    4    5        7
    row 1  | a1 | a2 | b1 | b2 | c1 | c2 |   | z1 |     each square is one output area
    row 0  | a3 | a4 | b3 | b4 | c3 | c4 |
             Quillhaven 001  002   Tallowgate 001   outside London

    NORTH_GATE and ENDED stand in Quillhaven 001, MILL_ROW in Quillhaven 002, QUAY in
    Tallowgate 001, and OUTSIDE outside London.

What was sold, over the three years 2023 to 2025:

    area             flats                          terraced houses          detached houses
    Quillhaven 001   11, at 200,000 to 300,000      none                     none
    Quillhaven 002   9, too few for a figure        10, the two middle ones  none
                                                    at 400,000 and 400,001
    Tallowgate 001   50, at 101,000 to 150,000      none                     10, all at 900,000

A file has the publisher's 16 columns and no row of names. Every column that
is never read holds a canary: the number of a sale, every line of an address,
whether the home is freehold, and the status of the record.
"""

import csv
import hashlib
import io
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from burro_pipeline.derive import price_paid
from burro_pipeline.evidence.receipt import How, Period, Receipt
from burro_pipeline.evidence.record import file_id_of
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.postcodes_support import (
    ENDED,
    MILL_ROW,
    NORTH_GATE,
    OUTSIDE,
    QUAY,
    directory_receipt,
    directory_zip,
    of_the_town,
    stored,
)

# A string found nowhere else. It stands in every column that is never read.
CANARY = "Zzyzx Parva"
# A price found nowhere else. It is the price of every sale that must not count.
CANARY_PRICE = 987_654_321
QUILLHAVEN_1, QUILLHAVEN_2, TALLOWGATE = "lon-ne02999001", "lon-ne02999002", "lon-ne02999003"
AREAS = (QUILLHAVEN_1, QUILLHAVEN_2, TALLOWGATE)
YEARS = (2023, 2024, 2025)
EDITION = "{year} file, made up for a test"
FLAT, TERRACED, SEMI, DETACHED, OTHER = "F", "T", "S", "D", "O"


@dataclass(frozen=True)
class MadeUpSale:
    """One made-up row of a file of sales."""

    price: int
    postcode: str
    home: str = FLAT
    year: int = 2024
    day: str = "06-15"
    new: str = "N"
    category: str = "A"


def _flats_of_quillhaven_1() -> list[MadeUpSale]:
    """Eleven, a year after another, at two postcodes of which one has ended."""
    return [
        MadeUpSale(
            200_000 + 10_000 * number,
            (NORTH_GATE if number % 2 else ENDED).postcode,
            year=YEARS[number % 3],
            new="Y" if number < 2 else "N",
        )
        for number in range(11)
    ]


def _of_quillhaven_2() -> list[MadeUpSale]:
    flats = [MadeUpSale(310_000 + 1_000 * number, MILL_ROW.postcode) for number in range(9)]
    # Ten terraced houses: the two in the middle sold for 400,000 and 400,001.
    paid = (350_000, 360_000, 370_000, 380_000, 400_000, 400_001, 420_000, 430_000, 440_000)
    houses = [MadeUpSale(price, MILL_ROW.postcode, TERRACED, year=2023) for price in paid]
    houses.append(MadeUpSale(450_000, MILL_ROW.postcode, TERRACED, year=2025, day="12-31"))
    return [*flats, *houses]


def _of_tallowgate() -> list[MadeUpSale]:
    flats = [
        MadeUpSale(101_000 + 1_000 * number, QUAY.postcode, year=YEARS[number % 3])
        for number in range(50)
    ]
    houses = [MadeUpSale(900_000, QUAY.postcode, DETACHED, year=2025) for _ in range(10)]
    return [*flats, *houses]


# None of these counts. Each is at the canary's price, so a figure that took one in shows it.
NOT_COUNTED = (
    # An additional sale: a repossession, a buy-to-let, a transfer to a company.
    MadeUpSale(CANARY_PRICE, NORTH_GATE.postcode, category="B"),
    MadeUpSale(CANARY_PRICE, QUAY.postcode, DETACHED, category="B"),
    # A sale of no kind of home.
    MadeUpSale(CANARY_PRICE, MILL_ROW.postcode, OTHER, category="B"),
    # A sale outside London, and one with no postcode.
    MadeUpSale(CANARY_PRICE, OUTSIDE.postcode),
    MadeUpSale(CANARY_PRICE, ""),
    # A sale at a postcode the directory does not hold.
    MadeUpSale(CANARY_PRICE, "QX9 9CK"),
)
SALES: tuple[MadeUpSale, ...] = (
    *_flats_of_quillhaven_1(),
    *_of_quillhaven_2(),
    *_of_tallowgate(),
    *NOT_COUNTED,
)


def line_of(sale: MadeUpSale, number: int, *, width: int = price_paid.WIDTH) -> list[str]:
    """One line of a file: what is read as it would be written, and a canary in the rest."""
    line = [CANARY] * max(width, price_paid.WIDTH)
    line[0] = f"{{MADE-UP-{number:06d}-{CANARY}}}"
    line[price_paid.PRICE - 1] = str(sale.price)
    line[price_paid.DAY - 1] = f"{sale.year}-{sale.day} 00:00"
    line[price_paid.POSTCODE - 1] = sale.postcode
    line[price_paid.HOME - 1] = sale.home
    line[price_paid.NEW - 1] = sale.new
    line[price_paid.CATEGORY - 1] = sale.category
    return line[:width]


def file_of(
    year: int, sales: Sequence[MadeUpSale] = SALES, *, width: int = price_paid.WIDTH
) -> bytes:
    """The file of one year, as the publisher writes it: every cell in quotes, no row of names."""
    text = io.StringIO(newline="")
    table = csv.writer(text, quoting=csv.QUOTE_ALL, lineterminator="\n")
    for number, sale in enumerate(sales, start=1):
        if sale.year == year:
            table.writerow(line_of(sale, number, width=width))
    return text.getvalue().encode()


def receipt_of(
    year: int, content: bytes, *, name: str | None = None, period: Period | None = None
) -> Receipt:
    sha256 = hashlib.sha256(content).hexdigest()
    return Receipt(
        file_id=file_id_of(sha256),
        source_id=price_paid.SOURCE,
        use=Use.SCORING,
        publisher_file=name or f"pp-{year}.csv",
        url=f"https://files.made-up.example/{sha256[:8]}",
        sha256=sha256,
        bytes=len(content),
        retrieved_at="2026-09-24T21:35:54Z",
        how=How.FETCHED,
        edition=EDITION.format(year=year),
        data_period=period or Period(start=f"{year}-01-01", end=f"{year}-12-31"),
    )


def files_of(sales: Sequence[MadeUpSale] = SALES) -> list[tuple[Receipt, bytes]]:
    """The file of each of the three years, with its receipt."""
    found: list[tuple[Receipt, bytes]] = []
    for year in YEARS:
        content = file_of(year, sales)
        found.append((receipt_of(year, content), content))
    return found


def inputs_of(
    folder: Path,
    files: Sequence[tuple[Receipt, bytes]] | None = None,
    *,
    directory: bool = True,
    given: Registry | None = None,
) -> Inputs:
    """The made-up town, the made-up directory and the made-up sales in a store of their own."""
    every = [*of_the_town(), *(files_of() if files is None else files)]
    if directory:
        content = directory_zip()
        every.append((directory_receipt(content), content))
    return stored(folder, every, given)
