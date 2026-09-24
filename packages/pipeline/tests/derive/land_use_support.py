"""What the tests of land use share: a made-up workbook of land use by LSOA.

No figure here is real, and no figure of the publisher's file was read to
write it. It is made two ways.

`published` lays a workbook out as the publisher's is laid out, which the step
`describe` gave: two sheets of the same columns, one in per cent and one in
hectares, three rows that name the columns, a column for the total of each
group, columns that hold nothing, a row for England and for a region above the
rows of the LSOAs, a dash where a figure would be nought, and two notes under
the table. The names of the sheets and of the columns are the publisher's.
Every code, every name of a place and every figure is made up.

`table_p405` lays one out another way, with one row of names and no total that
is read. The reader of a sheet is told no layout, and its tests move each part
about with it.

What is the publisher's in both: the names of the 28 categories of land, as
the technical notes of the land use statistics for England give them.

The workbook is written as a spreadsheet program writes an OpenDocument file:
a zip whose first member names its kind, one part that holds every sheet, a
run of empty cells at the end of each row, and a run of empty rows at the end
of each sheet.

The LSOAs are those of the made-up town of the tests of cells, where an output
area is a square of one hectare. Every figure was chosen so that a share can
be worked out by hand.

    area             LSOA        hectares   industry  storage  transport  gardens  woodland
    Quillhaven 001   E01999001   2          0.5       0.2      0.1        0.4      0
                     E01999002   2          0.1       0        0.3        0.8      0.2
    Quillhaven 002   E01999003   2          0         0        0          1.2      0.4
                     E01999004   2          0.25      0.05     0          0.3      0
    Tallowgate 001   E01999005   2          1.0       0.5      0.25       0        0
                     E01999006   3          0.5       0.25     0.75       0.15     0.3
"""

import io
import zipfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

from burro_pipeline.evidence.receipt import Period, Receipt
from burro_pipeline.fetch.store import FolderStore
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import FILES, contents, receipt_of, registry

SOURCE = "mhclg-land-use-statistics-2022"
WORKBOOK_NAME = "Live_Tables_-_Land_Use_Stock_2022_-_LSOA.ods"
# The edition and the period, as the title of each sheet of the workbook gives them.
EDITION, AS_AT = "2022", "2022"
# A string found nowhere else. It stands where the step never reads.
CANARY = "Zzyzx Parva"
# A number found nowhere else. It stands in every cell of figures that is part of no figure.
CANARY_NUMBER = 0.987654321

# The 28 categories, by the name the technical notes give each in their table of groups.
CATEGORIES: tuple[str, ...] = (
    "Community buildings",
    "Leisure (indoor)",
    "Defence buildings",
    "Industry",
    "Offices",
    "Retail",
    "Storage and warehousing",
    "Minerals and mining",
    "Landfill and waste disposal",
    "Unidentified building",
    "Unidentified general manmade surface",
    "Unidentified structure",
    "Unknown surface type with no classification",
    "Communal accommodation",
    "Residential",
    "Highways and roads",
    "Transport (other)",
    "Utilities",
    "Agricultural land",
    "Agricultural buildings",
    "Forestry and woodland",
    "Rough grassland",
    "Natural land",
    "Water",
    "Outdoor recreation",
    "Residential gardens",
    "Undeveloped land",
    "Vacant land",
)
INDUSTRY, STORAGE, TRANSPORT = "Industry", "Storage and warehousing", "Transport (other)"
GARDENS, WOODLAND = "Residential gardens", "Forestry and woodland"
RESIDENTIAL, ROADS = "Residential", "Highways and roads"
# As the workbook names the columns of codes and names, and its grand total. The step is
# told none of the first two.
CODE, NAME, TOTAL = "LSOA code", "LSOA name", "Grand Total"
COLUMNS = (CODE, NAME, *CATEGORIES, TOTAL)
# Made up: the names of the sheets, and the rows that stand over the names of the columns.
COVER, NOTES, BY_LSOA, BY_MSOA = "Cover", "Notes", "Table_1", "Table_2"
OVER_THE_HEADER = (
    ("Made up for a test", CANARY),
    (),
    ("This table is made up", None, CANARY),
)
HEADER_AT = len(OVER_THE_HEADER) + 1

OUTSIDE = "E01999901"
# The hectares of five categories in each LSOA. What is left of its land is homes and roads.
LAND: Mapping[str, float] = {
    "E01999001": 2.0,
    "E01999002": 2.0,
    "E01999003": 2.0,
    "E01999004": 2.0,
    "E01999005": 2.0,
    "E01999006": 3.0,
    OUTSIDE: 1.0,
}
USED: Mapping[str, Mapping[str, float]] = {
    "E01999001": {INDUSTRY: 0.5, STORAGE: 0.2, TRANSPORT: 0.1, GARDENS: 0.4},
    "E01999002": {INDUSTRY: 0.1, TRANSPORT: 0.3, GARDENS: 0.8, WOODLAND: 0.2},
    "E01999003": {GARDENS: 1.2, WOODLAND: 0.4},
    "E01999004": {INDUSTRY: 0.25, STORAGE: 0.05, GARDENS: 0.3},
    "E01999005": {INDUSTRY: 1.0, STORAGE: 0.5, TRANSPORT: 0.25},
    "E01999006": {INDUSTRY: 0.5, STORAGE: 0.25, TRANSPORT: 0.75, GARDENS: 0.15, WOODLAND: 0.3},
    OUTSIDE: {INDUSTRY: 0.9},
}
MSOAS = ("E02999001", "E02999002", "E02999003")

OFFICE = "urn:oasis:names:tc:opendocument:xmlns:office:1.0"
TABLE = "urn:oasis:names:tc:opendocument:xmlns:table:1.0"
TEXT = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
KIND = "application/vnd.oasis.opendocument.spreadsheet"
# What a spreadsheet program writes after the last cell of a row, and the last row of a sheet.
REST_OF_A_ROW = '<table:table-cell table:number-columns-repeated="16350"/>'
REST_OF_A_SHEET = (
    '<table:table-row table:number-rows-repeated="1048000">'
    '<table:table-cell table:number-columns-repeated="16384"/></table:table-row>'
)


@dataclass(frozen=True)
class Raw:
    """A cell, or a row, written as the test says: the markup itself."""

    markup: str


Cell = str | float | int | Raw | None
Row = Sequence[Cell] | Raw
Sheet = Sequence[Row]
Figures = Mapping[str, Mapping[str, Cell]]


def cell(held: Cell) -> str:
    """One cell, as a spreadsheet program writes it."""
    if isinstance(held, Raw):
        return held.markup
    if held is None:
        return "<table:table-cell/>"
    if isinstance(held, str):
        return (
            '<table:table-cell office:value-type="string">'
            f"<text:p>{escape(held)}</text:p></table:table-cell>"
        )
    written = format(held, ".15g")
    return (
        f'<table:table-cell office:value-type="float" office:value="{written}">'
        f"<text:p>{written}</text:p></table:table-cell>"
    )


def _row(row: Row) -> str:
    if isinstance(row, Raw):
        return row.markup
    return (
        f"<table:table-row>{''.join(cell(held) for held in row)}{REST_OF_A_ROW}</table:table-row>"
    )


def content_of(sheets: Mapping[str, Sheet | Raw], declared: str = "") -> bytes:
    """The one part of the workbook that holds every sheet."""
    tables = "".join(
        sheet.markup
        if isinstance(sheet, Raw)
        else f"<table:table table:name={quoteattr(name)}>"
        f'<table:table-column table:number-columns-repeated="16384"/>'
        f"{''.join(_row(row) for row in sheet)}{REST_OF_A_SHEET}</table:table>"
        for name, sheet in sheets.items()
    )
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>{declared}'
        f'<office:document-content xmlns:office="{OFFICE}" xmlns:table="{TABLE}" '
        f'xmlns:text="{TEXT}" office:version="1.2"><office:body><office:spreadsheet>'
        f"{tables}</office:spreadsheet></office:body></office:document-content>"
    ).encode()


def workbook(
    sheets: Mapping[str, Sheet | Raw],
    *,
    parts: Mapping[str, bytes | None] | None = None,
    declared: str = "",
) -> bytes:
    """A workbook, as a zip. `parts` takes the place of a part of it, or with None takes it out."""
    members: dict[str, bytes | None] = {
        "mimetype": KIND.encode(),
        "content.xml": content_of(sheets, declared),
        "styles.xml": b'<?xml version="1.0" encoding="UTF-8"?><styles/>',
        "META-INF/manifest.xml": b'<?xml version="1.0" encoding="UTF-8"?><manifest/>',
    }
    members |= parts or {}
    packed = io.BytesIO()
    with zipfile.ZipFile(packed, "w") as archive:
        for name, held in members.items():
            if held is None:
                continue
            # A fixed date, so that the same sheets make the same bytes. The first member is
            # kept as it is, and the rest are packed.
            how = zipfile.ZIP_STORED if name == "mimetype" else zipfile.ZIP_DEFLATED
            archive.writestr(zipfile.ZipInfo(name, (2026, 9, 24, 0, 0, 0)), held, how)
    return packed.getvalue()


def figures(**changed: Mapping[str, Cell]) -> dict[str, dict[str, Cell]]:
    """The hectares of every category in every LSOA, with those of some LSOAs changed.

    An LSOA is named by the end of its code, as `n001`. What is left of its
    land after the five categories is half homes and half roads, so that every
    row adds up to its land.
    """
    found: dict[str, dict[str, Cell]] = {}
    for code, used in USED.items():
        left = LAND[code] - sum(used.values())
        row: dict[str, Cell] = dict.fromkeys(CATEGORIES, 0.0)
        row |= {RESIDENTIAL: left / 2, ROADS: left / 2} | dict(used)
        found[code] = row
    for number, cells in changed.items():
        found[f"E01999{number[1:]}"] |= cells
    return found


def rows_of(held: Figures, columns: Sequence[str] = COLUMNS) -> list[list[Cell]]:
    """A row for each LSOA, under the columns given."""
    found: list[list[Cell]] = []
    for code, cells in held.items():
        row: dict[str, Cell] = {CODE: code, NAME: CANARY, TOTAL: CANARY_NUMBER} | dict(cells)
        found.append([row.get(name) for name in columns])
    return found


def by_lsoa(
    held: Figures | None = None,
    columns: Sequence[str] = COLUMNS,
    over: Sequence[Row] = OVER_THE_HEADER,
) -> list[Row]:
    """The sheet that is read: what stands over the header, the header, and a row for each LSOA."""
    return [*over, list(columns), *rows_of(figures() if held is None else held, columns)]


def by_msoa(columns: Sequence[str] = COLUMNS) -> list[Row]:
    """A sheet of the same columns, with a row for each MSOA. No figure is read from it."""
    rows: list[Row] = [
        [{CODE: code, NAME: CANARY}.get(name, CANARY_NUMBER) for name in columns] for code in MSOAS
    ]
    return [*OVER_THE_HEADER, list(columns), *rows]


def table_p405(
    held: Figures | None = None,
    *,
    columns: Sequence[str] = COLUMNS,
    over: Sequence[Row] = OVER_THE_HEADER,
    sheets: Mapping[str, Sheet | Raw] | None = None,
) -> bytes:
    """The made-up workbook: a cover, notes, the table by LSOA and the table by MSOA."""
    every: dict[str, Sheet | Raw] = {
        COVER: [[CANARY], [CANARY, CANARY_NUMBER]],
        NOTES: [["Note", "What it says"], ["1", CANARY]],
        BY_LSOA: by_lsoa(held, columns, over),
        BY_MSOA: by_msoa(columns),
    }
    every |= sheets or {}
    return workbook(every)


def receipt(content: bytes, period: Period | None = None, name: str = WORKBOOK_NAME) -> Receipt:
    """The receipt of a made-up workbook that stands in for a fetched one."""
    made = receipt_of(SOURCE, Use.SCORING, name, content, EDITION)
    return made.model_copy(update={"data_period": period or Period(as_at=AS_AT)})


def opened(folder: Path, content: bytes) -> Opened:
    """A made-up workbook as a step is handed one: a copy of it, and its receipt."""
    path = folder / "handed" / WORKBOOK_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return Opened(receipt(content), path)


def inputs_of(
    folder: Path,
    content: bytes | None,
    *,
    period: Period | None = None,
    name: str = WORKBOOK_NAME,
    using: Registry | None = None,
) -> Inputs:
    """The files of a made-up build in a store of their own: the spine's, the land's, the table.

    With no content the workbook is in the store and has no receipt, as a file
    is whose period the list was not sure of when it was fetched.
    """
    store = FolderStore(folder / "store")
    receipts: list[Receipt] = []
    files = {which: contents()[which] for which in ("lookup", "homes", "lsoa_outlines")}
    for which, held in files.items():
        source_id, use, file_name, edition = FILES[which]
        given = folder / "given" / file_name
        given.parent.mkdir(parents=True, exist_ok=True)
        given.write_bytes(held)
        store.put(source_id, file_name, given)
        receipts.append(receipt_of(source_id, use, file_name, held, edition))
    given = folder / "given" / name
    given.write_bytes(published() if content is None else content)
    store.put(SOURCE, name, given)
    if content is not None:
        receipts.append(receipt(content, period, name))
    return Inputs(using or registry(), receipts, store, folder / "work")


# The workbook as it is published

# The names of its two sheets, and how each says its unit, alone in a cell of row 3.
PER_CENT, HECTARES = "P404a", "P404b"
UNITS: Mapping[str, str] = {PER_CENT: "Per cent", HECTARES: "Hectares"}
MSOA_CODE, MSOA_NAME = "MSOA code", "MSOA name"
OTHER_NAME = "House of Commons Library \nMSOA Names"
# A column that holds nothing, and the mark of the total of a group of several categories.
GAP, OF_A_GROUP = "", "="
# What stands where a figure would be nought.
DASH = "-"
# The rows that name the columns, as the sheet numbers them, and the row of the unit.
UNIT_AT, NAMES_AT = 3, 6
ENGLAND, A_REGION, ANOTHER_REGION = "E92000001", "E12000007", "E12000008"
NOTES_UNDER = (
    f"1 Made up: the rows are of made-up areas. {CANARY}",
    f"2 Made up: the grand total is every category added up. {CANARY}",
)


def _group(name: str) -> tuple[str, tuple[str | None, str | None, str]]:
    return f"{OF_A_GROUP}{name}", (None, name, "Total")


# Every column of the workbook, in its order, by the name a test names it by: a category as
# the technical notes name it, or the total of a group. With each, what rows 4, 5 and 6 hold
# in its column.
LAID_OUT: tuple[tuple[str, tuple[str | None, str | None, str | None]], ...] = (
    (CODE, (None, None, CODE)),
    (NAME, (None, None, NAME)),
    (MSOA_CODE, (None, None, MSOA_CODE)),
    (MSOA_NAME, (None, None, MSOA_NAME)),
    (OTHER_NAME, (None, None, OTHER_NAME)),
    ("Community buildings", ("Developed use", None, "Community buildings")),
    ("Leisure (indoor)", (None, None, "Leisure and recreational buildings")),
    _group("Community service"),
    ("Defence buildings", (None, "Defence", "Total")),
    ("Industry", (None, None, "Industry")),
    ("Offices", (None, None, "Offices")),
    ("Retail", (None, None, "Retail")),
    ("Storage and warehousing", (None, None, "Storage and warehousing")),
    _group("Industry and commerce"),
    ("Landfill and waste disposal", (None, None, "Landfill and waste disposal")),
    ("Minerals and mining", (None, None, "Minerals and mining")),
    _group("Minerals and landfill"),
    ("Communal accommodation", (None, None, "Institutional and communal accommo-dations")),
    ("Residential", (None, None, "Residential")),
    _group("Residential"),
    ("Highways and roads", (None, None, "Highways and road transport")),
    ("Transport (other)", (None, None, "Transport (other)")),
    ("Utilities", (None, None, "Utilities")),
    _group("Transport and utilities"),
    ("Unidentified building", (None, None, "Unidentified building")),
    ("Unidentified general manmade surface", (None, None, "Unidentified general manmade surface")),
    ("Unidentified structure", (None, None, "Unidentified structure")),
    ("Unknown surface type with no classification", (None, None, "Unknown")),
    _group("Unknown developed use"),
    (GAP, (None, None, None)),
    _group("Developed use"),
    (GAP, (None, None, None)),
    ("Agricultural buildings", ("Non-developed use", None, "Agricultural buildings")),
    ("Agricultural land", (None, None, "Agricultural land")),
    _group("Agriculture"),
    ("Forestry and woodland", (None, None, "Forestry and woodland")),
    ("Natural land", (None, None, "Natural land")),
    ("Rough grassland", (None, None, "Rough grassland")),
    ("Water", (None, None, "Water")),
    _group("Forest, open land and water"),
    ("Outdoor recreation", (None, "Outdoor recreation", "Total")),
    ("Residential gardens", (None, "Residential gardens", "Total")),
    ("Undeveloped land", (None, "Undeveloped land", "Total")),
    (GAP, (None, None, None)),
    _group("Non-developed"),
    (GAP, (None, None, None)),
    ("Vacant land", ("Vacant", None, "Total")),
    (GAP, (None, None, None)),
    (TOTAL, ("Grand Total", None, "Total")),
)
AS_PUBLISHED: tuple[str, ...] = tuple(name for name, _ in LAID_OUT)
_NAMED: Mapping[str, tuple[str | None, str | None, str | None]] = {
    name: rows for name, rows in LAID_OUT if name != GAP
}
# The columns of text beside the code, which no step reads.
_WORDS = (NAME, MSOA_NAME, OTHER_NAME)


def all_of(cells: Mapping[str, Cell]) -> float:
    """All the land of a row: every figure of it added up, but for its own total."""
    return sum(
        float(held)
        for name, held in cells.items()
        if name != TOTAL and isinstance(held, float | int)
    )


def _names(columns: Sequence[str], unit: str) -> list[Row]:
    """Rows 3 to 6: the unit over the last column, and the three rows that name the columns."""
    over = [_NAMED.get(name, (None, None, name or None)) for name in columns]
    return [
        [*([None] * (len(columns) - 1)), unit],
        *([rows[at] for rows in over] for at in range(3)),
    ]


def _row_of(code: str, cells: Mapping[str, Cell], columns: Sequence[str], dashed: bool) -> Row:
    held: dict[str, Cell] = {TOTAL: all_of(cells)} | dict(cells)
    found: list[Cell] = []
    for name in columns:
        if name == CODE:
            found.append(code)
        elif name == MSOA_CODE:
            found.append(f"E02{code[3:]}")
        elif name in _WORDS:
            found.append(CANARY)
        elif name == GAP:
            found.append(None)
        elif name.startswith(OF_A_GROUP):
            found.append(CANARY_NUMBER)
        else:
            one = held.get(name)
            found.append(DASH if dashed and one == 0 and name != TOTAL else one)
    return found


def _of_a_larger_area(code: str, columns: Sequence[str]) -> Row:
    """The row of England or of a region. Every figure of it is part of no figure."""
    return [
        code
        if name == CODE
        else CANARY
        if name == NAME
        else None
        if name in (GAP, MSOA_CODE, MSOA_NAME, OTHER_NAME)
        else CANARY_NUMBER
        for name in columns
    ]


def sheet_as_published(
    held: Figures | None = None,
    *,
    columns: Sequence[str] = AS_PUBLISHED,
    unit: str = UNITS[HECTARES],
    dashed: bool = True,
    larger: Sequence[str] = (ENGLAND, A_REGION, ANOTHER_REGION),
    under: Sequence[str] = NOTES_UNDER,
) -> list[Row]:
    """One sheet, laid out as the publisher lays one out."""
    rows = figures() if held is None else held
    return [
        [f"Made-up table: land by made-up area, 2022. {CANARY}"],
        [],
        *_names(columns, unit),
        [],
        *(_of_a_larger_area(code, columns) for code in larger[:1]),
        [],
        *(_of_a_larger_area(code, columns) for code in larger[1:]),
        *(_row_of(code, cells, columns, dashed) for code, cells in rows.items()),
        [],
        *([words] for words in under),
    ]


def shares_of(held: Figures) -> dict[str, dict[str, Cell]]:
    """The same rows in per cent: each figure over all the land of its row."""
    return {
        code: {
            name: 100 * float(one) / (all_of(cells) or 1.0) if isinstance(one, float | int) else one
            for name, one in cells.items()
        }
        for code, cells in held.items()
    }


def published(
    held: Figures | None = None,
    *,
    columns: Sequence[str] = AS_PUBLISHED,
    dashed: bool = True,
    sheets: Mapping[str, Sheet | Raw] | None = None,
) -> bytes:
    """The made-up workbook as the publisher lays it out: a sheet in per cent, one in hectares."""
    rows = figures() if held is None else held
    every: dict[str, Sheet | Raw] = {
        PER_CENT: sheet_as_published(
            shares_of(rows), columns=columns, unit=UNITS[PER_CENT], dashed=dashed
        ),
        HECTARES: sheet_as_published(rows, columns=columns, dashed=dashed),
    }
    every |= sheets or {}
    return workbook(every)
