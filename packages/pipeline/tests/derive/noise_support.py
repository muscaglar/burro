"""What the tests of noise share: a made-up workbook, laid out as the publisher lays out its own.

Nothing here is real. The workbook has the publisher's eight sheets under their
own names, and the sheet that is read has its own fourteen columns. The notes
are a table whose header is the eleventh row, in columns C to H, as the
publisher's is. What the cells hold is made up: the LSOAs are those of the
made-up town of the tests of cells, and every share was chosen so that a
figure can be worked out by hand.

A sheet that may never be opened holds a canary, and is not well formed. So a
reader that opens one fails, and a reader that repeats what one holds is
caught.

A number is written as a workbook writes it, to 17 digits: 0.332 is
`0.33200000000000002`. Text is kept in the table of text, which every sheet
points into.
"""

import io
import zipfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

from burro_pipeline.evidence.receipt import Period, Receipt
from burro_pipeline.fetch.store import FolderStore
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import FILES, LONDON, contents, receipt_of, registry

SOURCE = "mhclg-iod-2025-underlying-indicators"
WORKBOOK_NAME = "File_8_IoD2025_Underlying_Indicators.xlsx"
EDITION, YEAR = "2025", "2021"
# A string found nowhere else. It stands where the step never reads.
CANARY = "Zzyzx Parva"
# A number found nowhere else. It stands in every column of figures that is not read.
CANARY_NUMBER = 0.987654321

NOTES, LIVING = "Notes", "IoD25 Living Env Domain"
NEVER_OPENED = (
    "IoD25 Income Domain",
    "IoD25 Employment Domain",
    "IoD25 Education Domain",
    "IoD25 Health Domain",
    "IoD25 Crime Domain",
    "IoD25 Barriers Domain",
)
SHEETS = (NOTES, *NEVER_OPENED, LIVING)
LIVING_COLUMNS = (
    "LSOA code (2021)",
    "LSOA name (2021)",
    "Local Authority District code (2024)",
    "Local Authority District name (2024)",
    "Housing in poor condition indicator",
    "Housing energy performance deprivation Score",
    "Housing lacking private outdoor space deprivation score",
    "Noise pollution",
    "Road traffic casualties involving injury to pedestrians and cyclists",
    "Sulphur dioxide (component of air quality indicator)",
    "Nitrogen dioxide (component of air quality indicator)",
    "Benzene (component of air quality indicator)",
    "Particulates (component of air quality indicator)",
    "Air quality indicator",
)
NOTES_COLUMNS = (
    "Domain",
    "Indicator",
    "Data supplier",
    "Data time point",
    "Published",
    "Comments",
)
# The notes stand in columns C to H, under ten rows that hold no cell.
NOTES_FIRST_COLUMN, NOTES_HEADER_AT = 2, 11
# What the notes say of the indicator, in the publisher's own turns of phrase. The step holds
# the notes to the level, to who is counted, to the kind of noise, to the measure of the level
# and to the shrinkage, so each is said here.
SAID_OF_NOISE = (
    "Made up for a test. The percentage of the population of each LSOA exposed to noise "
    "pollution greater than or equal to 55dB Lden. The numerator is the number of residents in "
    "each LSOA exposed to combined transport noise above 55 dB Lden. Shrinkage was applied to "
    "this indicator."
)
# The supplier, as the publisher names it. The apostrophe is the publisher's, and is curled.
SUPPLIER_OF_NOISE = "Defra\u2019s Noise Modelling System, as made up for a test"

# The LSOAs of the made-up town, in the order of their codes, and the share each is given.
LSOAS = tuple(sorted({unit.lsoa for unit in LONDON}))
OUTSIDE = "E01999901"
SHARES: Mapping[str, float] = {
    "E01999001": 0.25,
    "E01999002": 0.75,
    "E01999003": 0.332,
    "E01999004": 0.001,
    "E01999005": 1.0,
    "E01999006": 0.0,
    OUTSIDE: 0.5,
}


@dataclass(frozen=True)
class Raw:
    """A cell written as the test says: how it is typed, and the markup inside it."""

    kind: str
    inside: str


Cell = str | float | int | Raw | None
Table = Sequence[Sequence[Cell]]
NOT_WELL_FORMED = b"<worksheet><sheetData><row><c><v>" + CANARY.encode()


def letters(column: int) -> str:
    """The letters of a column, counted from 0: A, B, and AA after Z."""
    found = ""
    number = column + 1
    while number:
        number, last = divmod(number - 1, 26)
        found = chr(ord("A") + last) + found
    return found


def as_written(number: float) -> str:
    """A number as a workbook writes it: to 17 digits, so 0.332 is 0.33200000000000002."""
    return format(number, ".17g")


class _Texts:
    def __init__(self) -> None:
        self.held: list[str] = []

    def place_of(self, text: str) -> int:
        if text not in self.held:
            self.held.append(text)
        return self.held.index(text)

    def part(self) -> bytes:
        main = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
        written = "".join(f"<si><t>{escape(text)}</t></si>" for text in self.held)
        return f'<?xml version="1.0" encoding="UTF-8"?><sst xmlns="{main}">{written}</sst>'.encode()


def _sheet(
    table: Table, texts: _Texts, first_column: int, first_row: int, merged: Sequence[str] = ()
) -> bytes:
    main = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    # A workbook lists the cells it merges under the rows, each as `V1:Z1`.
    merges = "".join(f'<mergeCell ref="{escape(one)}"/>' for one in merged)
    merges = f'<mergeCells count="{len(merged)}">{merges}</mergeCells>' if merged else ""
    rows: list[str] = []
    for number, row in enumerate(table, start=first_row):
        cells: list[str] = []
        for column, cell in enumerate(row, start=first_column):
            at = f"{letters(column)}{number}"
            if isinstance(cell, Raw):
                cells.append(f'<c r="{at}" t="{cell.kind}">{cell.inside}</c>')
            elif isinstance(cell, str):
                cells.append(f'<c r="{at}" t="s"><v>{texts.place_of(cell)}</v></c>')
            elif cell is not None:
                cells.append(f'<c r="{at}"><v>{as_written(cell)}</v></c>')
        rows.append(f'<row r="{number}">{"".join(cells)}</row>')
    return (
        f'<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="{main}">'
        f"<sheetData>{''.join(rows)}</sheetData>{merges}</worksheet>"
    ).encode()


def workbook(
    sheets: Mapping[str, Table | bytes],
    *,
    starts: Mapping[str, tuple[int, int]] | None = None,
    parts: Mapping[str, bytes] | None = None,
    merged: Mapping[str, Sequence[str]] | None = None,
) -> bytes:
    """A workbook, as a zip of XML. A sheet given as bytes is written as it is given.

    `starts` says where the table of a sheet begins, by column from 0 and by
    row from 1. `parts` takes the place of any part of the zip. `merged` names
    the cells a sheet merges, each as a workbook writes it: `V1:Z1`.
    """
    main = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    related = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    package = "http://schemas.openxmlformats.org/package/2006/relationships"
    texts = _Texts()
    members: dict[str, bytes] = {}
    listed: list[str] = []
    relations: list[str] = []
    for number, (name, table) in enumerate(sheets.items(), start=1):
        column, row = (starts or {}).get(name, (0, 1))
        members[f"xl/worksheets/sheet{number}.xml"] = (
            table
            if isinstance(table, bytes)
            else _sheet(table, texts, column, row, (merged or {}).get(name, ()))
        )
        listed.append(f'<sheet name="{escape(name)}" sheetId="{number}" r:id="rId{number}"/>')
        relations.append(
            f'<Relationship Id="rId{number}" Type="{related}/worksheet" '
            f'Target="worksheets/sheet{number}.xml"/>'
        )
    members["xl/workbook.xml"] = (
        f'<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="{main}" '
        f'xmlns:r="{related}"><sheets>{"".join(listed)}</sheets></workbook>'
    ).encode()
    members["xl/_rels/workbook.xml.rels"] = (
        f'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="{package}">'
        f"{''.join(relations)}</Relationships>"
    ).encode()
    members["xl/sharedStrings.xml"] = texts.part()
    members["[Content_Types].xml"] = b'<?xml version="1.0" encoding="UTF-8"?><Types/>'
    members |= parts or {}
    packed = io.BytesIO()
    with zipfile.ZipFile(packed, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(members):
            # A fixed date, so that the same sheets make the same bytes.
            archive.writestr(zipfile.ZipInfo(name, (2026, 9, 23, 0, 0, 0)), members[name])
    return packed.getvalue()


def notes(
    year: Cell = YEAR,
    said: Cell = SAID_OF_NOISE,
    indicator: str = "Noise pollution",
    supplier: Cell = SUPPLIER_OF_NOISE,
) -> list[list[Cell]]:
    """The table of notes: its header, a row about residents, and the row of the indicator."""
    living = "Living Environment Deprivation Domain"
    return [
        list(NOTES_COLUMNS),
        ["Income Deprivation Domain", CANARY, CANARY, "March 2024", "No", CANARY],
        [living, "Housing in poor condition", CANARY, "2023", "Yes", CANARY],
        [None, indicator, supplier, year, "Yes", said],
        [None, "Air quality indicator", CANARY, "2023", "Yes", CANARY],
    ]


def living(
    shares: Mapping[str, Cell] = SHARES, columns: Sequence[str] = LIVING_COLUMNS
) -> list[list[Cell]]:
    """The sheet that is read: its header, and a row for each LSOA that is given a share."""
    found: list[list[Cell]] = [list(columns)]
    for code, share in shares.items():
        row: dict[str, Cell] = dict.fromkeys(LIVING_COLUMNS, CANARY_NUMBER)
        row |= {
            "LSOA code (2021)": code,
            "LSOA name (2021)": CANARY,
            "Local Authority District code (2024)": "E09999901",
            "Local Authority District name (2024)": CANARY,
            "Noise pollution": share,
        }
        found.append([row[name] for name in columns])
    return found


def file_8(
    shares: Mapping[str, Cell] = SHARES,
    *,
    columns: Sequence[str] = LIVING_COLUMNS,
    noted: Table | None = None,
    sheets: Mapping[str, Table | bytes] | None = None,
) -> bytes:
    """The made-up workbook: the notes, six sheets that are never opened, and the one read."""
    every: dict[str, Table | bytes] = {NOTES: notes() if noted is None else noted}
    every |= dict.fromkeys(NEVER_OPENED, NOT_WELL_FORMED)
    every[LIVING] = living(shares, columns)
    every |= sheets or {}
    return workbook(every, starts={NOTES: (NOTES_FIRST_COLUMN, NOTES_HEADER_AT)})


def receipt(content: bytes, period: Period | None = None, name: str = WORKBOOK_NAME) -> Receipt:
    """The receipt of a made-up workbook that stands in for a fetched one."""
    made = receipt_of(SOURCE, Use.SCORING, name, content, EDITION)
    return made.model_copy(update={"data_period": period or Period(as_at=YEAR)})


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
    """The files of a made-up build in a store of their own: the spine's two, and the workbook.

    With no content the workbook is in the store and has no receipt, as a file
    is whose period the list did not state when it was fetched.
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
    given.write_bytes(file_8() if content is None else content)
    store.put(SOURCE, name, given)
    if content is not None:
        receipts.append(receipt(content, period, name))
    return Inputs(using or registry(), receipts, store, folder / "work")
