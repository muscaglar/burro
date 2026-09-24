"""What the tests of price share: a made-up workbook, laid out as the publisher lays out its own.

Nothing here is real. The workbook has the publisher's seventeen sheets under
their own names, and a sheet that is read has its own 126 columns under its own
title. What the cells hold is made up: the MSOAs are those of the made-up town
of the tests of cells, with one outside London, and every price was chosen so
that a test can say which cell it came from.

    MSOA        area             any kind   detached   semi      terraced   flat
    E02999001   Quillhaven 001    410000    [x]        525000    450000     300000
    E02999002   Quillhaven 002    655000    1200000    [x]       700500     [x]
    E02999003   Tallowgate 001    287500    no row     no row    [x]        250000
    E02999901   outside London    150000    320000     [x]       140000      95000

Every other year of a row holds a canary, and so does every name. The sheets of
newly built and of existing homes are not well formed. So a reader that opens
one fails, and a reader that takes another column is caught.
"""

from collections.abc import Mapping, Sequence
from pathlib import Path

from burro_pipeline.evidence.receipt import Period, Receipt
from burro_pipeline.fetch.store import FolderStore
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import CANARY, FILES, contents, receipt_of, registry
from .noise_support import NOT_WELL_FORMED, Cell, Table, workbook

SOURCE = "ons-median-house-prices-msoa"
WORKBOOK_NAME = "medianpricepaidformsoa.xlsx"
EDITION = "Year ending March 2026"
YEAR = Period(start="2025-04", end="2026-03")
# A price found nowhere else. It stands in every year of a row that is not read.
CANARY_PRICE = 987_654_321

COVER, CONTENTS = "Cover", "Contents"
READ = ("1a", "1b", "1c", "1d", "1e")
NEVER_OPENED = ("2a", "2b", "2c", "2d", "2e", "3a", "3b", "3c", "3d", "3e")
SHEETS = (COVER, CONTENTS, *READ, *NEVER_OPENED)

FIRST_COLUMNS = ("Local authority code", "Local authority name", "MSOA code", "MSOA name")
QUARTERS = ("Mar", "Jun", "Sep", "Dec")
YEARS = (
    "Year ending Dec 1995",
    *(f"Year ending {month} {year}" for year in range(1996, 2026) for month in QUARTERS),
    "Year ending Mar 2026",
)
COLUMNS = (*FIRST_COLUMNS, *YEARS)
LAST, THE_YEAR_BEFORE = "Year ending Mar 2026", "Year ending Mar 2025"

# What the contents say each sheet holds, between "Median price paid" and "by MSOA".
HOLDS: Mapping[str, str] = {
    "a": "",
    "b": " for detached houses",
    "c": " for semi-detached houses",
    "d": " for terraced houses",
    "e": " for flats/maisonettes",
}
OF: Mapping[str, str] = {"1": "", "2": " (newly built dwellings)", "3": " (existing dwellings)"}
# What the cover says, in the publisher's own turns of phrase. The step holds the cover to the
# unit and to what stands where no figure is given, so each is said here.
SAID_ON_THE_COVER = (
    "Median price paid by Middle layer Super Output Area (MSOA)",
    "Introductory information",
    "Made up for a test. It describes no real place.",
    "Notes",
    "All the figures within these datasets relate to pounds sterling (£)",
    "Where the symbol [x] appears in the tables, no data are available. This is due to there "
    "being no house sales or fewer than five house sales of that particular type in the given "
    "year for the selected geography.",
    "Source: made up for a test.",
)

Q1, Q2, T1, OUTSIDE = "E02999001", "E02999002", "E02999003", "E02999901"
DISTRICTS: Mapping[str, str] = {
    Q1: "E09000901",
    Q2: "E09000901",
    T1: "E09000902",
    OUTSIDE: "E07000901",
}
PRICES: Mapping[str, Mapping[str, Cell]] = {
    "1a": {Q1: 410_000, Q2: 655_000, T1: 287_500, OUTSIDE: 150_000},
    "1b": {Q1: "[x]", Q2: 1_200_000, OUTSIDE: 320_000},
    "1c": {Q1: 525_000, Q2: "[x]", OUTSIDE: "[x]"},
    "1d": {Q1: 450_000, Q2: 700_500, T1: "[x]", OUTSIDE: 140_000},
    "1e": {Q1: 300_000, Q2: "[x]", T1: 250_000, OUTSIDE: 95_000},
}


def described(sheet: str, last: str = "March 2026") -> str:
    """What the contents say of a sheet, and what the sheet says of itself in its first row."""
    return (
        f"Table {sheet} - Median price paid{OF[sheet[0]]}{HOLDS[sheet[1]]} by MSOA, "
        f"England and Wales, year ending December 1995 to year ending {last}"
    )


def listed(last: str = "March 2026", **changed: str) -> list[list[Cell]]:
    """The contents: two rows of words, the row that names the columns, and a row a sheet."""
    every = {sheet: described(sheet, last) for sheet in (*READ, *NEVER_OPENED)} | changed
    return [
        ["Table of contents"],
        ["This worksheet contains one table."],
        ["Sheet name", "Table description"],
        *([sheet, said] for sheet, said in every.items()),
    ]


def sheet_of(
    sheet: str,
    prices: Mapping[str, Cell],
    *,
    columns: Sequence[str] = COLUMNS,
    year: str = LAST,
    districts: Mapping[str, Cell] = DISTRICTS,
) -> list[list[Cell]]:
    """A sheet of figures: its title, its source, its header, and a row for each MSOA."""
    found: list[list[Cell]] = [[described(sheet)], ["Source: made up for a test."], list(columns)]
    for code, price in prices.items():
        row: dict[str, Cell] = dict.fromkeys(COLUMNS, CANARY_PRICE)
        row |= {
            "Local authority code": districts.get(code, "E09000901"),
            "Local authority name": CANARY,
            "MSOA code": code,
            "MSOA name": CANARY,
            year: price,
        }
        found.append([row[name] for name in columns])
    return found


def book(
    prices: Mapping[str, Mapping[str, Cell]] = PRICES,
    *,
    cover: Sequence[Cell] = SAID_ON_THE_COVER,
    contents_of: Table | None = None,
    columns: Sequence[str] = COLUMNS,
    year: str = LAST,
    districts: Mapping[str, Cell] = DISTRICTS,
    sheets: Mapping[str, Table | bytes] | None = None,
    without: Sequence[str] = (),
) -> bytes:
    """The made-up workbook: the cover, the contents, five sheets that are read and ten that
    are never opened."""
    every: dict[str, Table | bytes] = {
        COVER: [[said] for said in cover],
        CONTENTS: listed() if contents_of is None else contents_of,
    }
    for sheet in READ:
        every[sheet] = sheet_of(
            sheet, prices.get(sheet, {}), columns=columns, year=year, districts=districts
        )
    every |= dict.fromkeys(NEVER_OPENED, NOT_WELL_FORMED)
    every |= sheets or {}
    return workbook({name: table for name, table in every.items() if name not in without})


def receipt(
    content: bytes,
    period: Period | None = None,
    name: str = WORKBOOK_NAME,
    use: Use = Use.SCORING,
) -> Receipt:
    """The receipt of a made-up workbook that stands in for a fetched one.

    It is fetched to be ranked on, as the list of a build names it. `use` is
    for a workbook that was fetched for less.
    """
    made = receipt_of(SOURCE, use, name, content, EDITION)
    return made.model_copy(update={"data_period": period or YEAR})


def inputs_of(
    folder: Path,
    content: bytes | None,
    *,
    period: Period | None = None,
    name: str = WORKBOOK_NAME,
    using: Registry | None = None,
) -> Inputs:
    """The files of a made-up build in a store of their own: the spine's two, and the workbook.

    With no content the workbook is in the store and has no receipt.
    """
    store = FolderStore(folder / "store")
    receipts: list[Receipt] = []
    files = {which: contents()[which] for which in ("lookup", "homes")}
    for which, held in files.items():
        source_id, use, file_name, edition = FILES[which]
        given = folder / "given" / file_name
        given.parent.mkdir(parents=True, exist_ok=True)
        given.write_bytes(held)
        store.put(source_id, file_name, given)
        receipts.append(receipt_of(source_id, use, file_name, held, edition))
    given = folder / "given" / name
    given.write_bytes(book() if content is None else content)
    store.put(SOURCE, name, given)
    if content is not None:
        receipts.append(receipt(content, period, name))
    return Inputs(using or registry(), receipts, store, folder / "work")
