"""A made-up workbook of household income, laid out as the publisher lays out its own.

Every figure here is made up. The town is the made-up town of the tests of
cells: three areas, each an MSOA. The workbook has the publisher's sheets, the
rows of words its cover, notes and terms hold, the title over each table, and
the columns of the table that is read. What it holds is made up.

    MSOA        area             estimate   lower    upper
    E02999001   Quillhaven 001   52307      46113    59311
    E02999002   Quillhaven 002   41009      38001    44017
    E02999003   Tallowgate 001   no figure
    E02999901   outside London   77777      70007    80008

The three sheets of disposable income are not well formed. So a reader that
opens one fails.
"""

from collections.abc import Mapping, Sequence
from pathlib import Path

from burro_pipeline.derive import household_income
from burro_pipeline.evidence.receipt import Period, Receipt
from burro_pipeline.fetch.store import FolderStore
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import CANARY, FILES, contents, receipt_of, registry
from .noise_support import NOT_WELL_FORMED, Cell, Table, workbook

SOURCE = household_income.SOURCE
NAME = household_income.WORKBOOK
EDITION = "Financial year ending 2023"
YEAR = Period(start="2022-04", end="2023-03")
Q1, Q2, T1, OUTSIDE = "E02999001", "E02999002", "E02999003", "E02999901"
# The estimate, its lower limit and its upper limit. A figure found nowhere else.
Held = tuple[Cell, Cell, Cell]
FIGURES: Mapping[str, Held] = {
    Q1: (52_307, 46_113, 59_311),
    Q2: (41_009, 38_001, 44_017),
    T1: (None, None, None),
    OUTSIDE: (77_777, 70_007, 80_008),
}
DISTRICTS: Mapping[str, str] = {
    Q1: "E09000901",
    Q2: "E09000901",
    T1: "E09000902",
    OUTSIDE: "E06000901",
}
COLUMNS = (
    "MSOA code",
    "MSOA name",
    "Local authority code",
    "Local authority name",
    "Region code",
    "Region name",
    "Total annual income (£)",
    "Upper confidence limit (£)",
    "Lower confidence limit (£)",
    "Confidence interval (£)",
)
NOTES: Sequence[str] = (
    "Financial year ending (FYE) 2023 refers to the period between 1st April 2022 to 31st "
    "March 2023.",
    "This workbook uses MSOA codes used by ONS from Census 2021. These are made up of "
    "unchanged 2011 MSOAs and new 2021 MSOAs.",
    "Caution should be applied when interpreting trends over time.",
)
METADATA: Sequence[str] = (
    "These reference tables contain statistics of model-based small area income estimates "
    "for financial year ending 2023, made up for a test.",
    "1. Total annual household income",
    "1. Total annual household income is the sum of the gross income of every member of the "
    "household plus any income from benefits such as Working Families Tax Credit.",
)
TERMS: Sequence[str] = (
    "Made up for a test.",
    "Users should include a source accreditation to ONS - Source: Office for National Statistics.",
)
NEVER_OPENED = (
    "Net annual income",
    "Net annual income (equivalised) before housing costs",
    "Net annual income (equivalised) after housing costs",
)


def table_of(
    figures: Mapping[str, Held] = FIGURES,
    columns: Sequence[str] = COLUMNS,
    districts: Mapping[str, str] = DISTRICTS,
) -> Table:
    """The sheet that is read: three rows of words, the names of its columns, and its rows."""
    found: list[list[Cell]] = [
        ["Total annual household income by middle layer super output area, made up"],
        ["This worksheet contains one table."],
        ["Link back to Contents"],
        list(columns),
    ]
    for code, (estimate, lower, upper) in figures.items():
        row: dict[str, Cell] = {
            "MSOA code": code,
            "MSOA name": CANARY,
            "Local authority code": districts.get(code, "E09000901"),
            "Local authority name": CANARY,
            "Region code": "E12000007",
            "Region name": CANARY,
            "Total annual income (£)": estimate,
            "Upper confidence limit (£)": upper,
            "Lower confidence limit (£)": lower,
            "Confidence interval (£)": 987_654_321,
        }
        found.append([row[name] for name in columns])
    return found


def book(
    figures: Mapping[str, Held] = FIGURES,
    *,
    notes: Sequence[str] = NOTES,
    metadata: Sequence[str] = METADATA,
    terms: Sequence[str] = TERMS,
    columns: Sequence[str] = COLUMNS,
    districts: Mapping[str, str] = DISTRICTS,
    without: Sequence[str] = (),
) -> bytes:
    """The made-up workbook: its sheets of words, the sheet that is read, and three that are not."""
    every: dict[str, Table | bytes] = {
        "Cover Sheet": [["Income estimates for small areas, made up"], [CANARY]],
        "Notes": [
            ["Notes related to the data in this spreadsheet"],
            ["This worksheet contains one table."],
            ["Note number", "Note text"],
            *([str(at), note] for at, note in enumerate(notes, start=1)),
        ],
        "Metadata": [["Metadata"], *([line] for line in metadata)],
        "Terms and Conditions": [["Terms and Conditions"], *([line] for line in terms)],
        "Total annual income": table_of(figures, columns, districts),
    }
    every |= dict.fromkeys(NEVER_OPENED, NOT_WELL_FORMED)
    return workbook({name: table for name, table in every.items() if name not in without})


def receipt(content: bytes, period: Period | None = None, use: Use = Use.DISPLAY) -> Receipt:
    """The receipt of a made-up workbook that stands in for a fetched one: fetched to be shown."""
    made = receipt_of(SOURCE, use, NAME, content, EDITION)
    return made.model_copy(update={"data_period": period or YEAR})


def inputs_of(
    folder: Path,
    content: bytes | None = None,
    *,
    period: Period | None = None,
    use: Use = Use.DISPLAY,
    using: Registry | None = None,
) -> Inputs:
    """The files of a made-up build in a store of their own: the spine's two, and the workbook."""
    store = FolderStore(folder / "store")
    receipts: list[Receipt] = []
    files = {which: contents()[which] for which in ("lookup", "homes")}
    for which, held in files.items():
        source_id, asked, file_name, edition = FILES[which]
        given = folder / "given" / file_name
        given.parent.mkdir(parents=True, exist_ok=True)
        given.write_bytes(held)
        store.put(source_id, file_name, given)
        receipts.append(receipt_of(source_id, asked, file_name, held, edition))
    held = book() if content is None else content
    given = folder / "given" / NAME
    given.write_bytes(held)
    store.put(SOURCE, NAME, given)
    receipts.append(receipt(held, period, use))
    return Inputs(using or registry(), receipts, store, folder / "work")
