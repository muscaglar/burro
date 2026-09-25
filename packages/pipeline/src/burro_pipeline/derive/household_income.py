"""Household income, as the statistics office estimates it: read to be shown, and never ranked on.

The Office for National Statistics publishes one workbook of "model-based small
area income estimates": for each middle layer super output area, four kinds of
annual household income, each with the two limits of its confidence interval.
This reads the first kind, total annual household income, for the areas of a
build, and hands it on to be written to a folder of its own beside the
release. **It is no measure.** It is on no list of measures, it makes no row of
a catalogue and no row of evidence of a release, and nothing here gives it a
percentile, a band or a place in any order.

Why it is kept so. The figure describes residents: what the households of an
area are estimated to have. Decision record 0006 keeps such a figure out of
every score, tag, vibe and filter, and the licence registry holds the source
for `display` and for `validation_only` and for nothing else, so the gate
refuses this file for a feature or a cost. It is opened here for `display`.

What is read, and what is never read:

    sheet                    what is read
    Notes                    that the year is 1 April to 31 March, and the census of the codes
    Metadata                 that the estimates are model-based, and the name of the kind
    Terms and Conditions     the credit the publisher asks for
    Total annual income      the code of the area and of its local authority, the estimate,
                             and its lower and upper confidence limits

The three sheets of disposable income are never opened. Nor is the name of any
area, the region, or the width of the interval, which the limits already give.

What the publisher says of a figure, which is why it is shown as it is:

- It is a mean and never a median, and is of one area: nothing is added up,
  averaged or shared out. While an area of a build is one MSOA, the figure of
  an area is the publisher's own row.
- Areas are to be compared only with the confidence intervals in mind. Burro
  compares none.
- The method "is optimised for point-in-time estimates and not for estimating
  change", so one year is read and no change is shown.
"""

import re
from collections.abc import Mapping
from dataclasses import dataclass

from burro_core.income import AreaIncome, Income, IncomeSource

from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive.noise_sheet import Value, read_sheet
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.receipt import Receipt
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

SOURCE = "ons-income-estimates-small-areas"
# What the file is opened for. The registry allows nothing that ranks.
USE = Use.DISPLAY
# The publisher's name for the file.
WORKBOOK = "datasetfinal.xlsx"
# The sheets that are read, and the row of each that names its columns.
NOTES, METADATA, TERMS, FIGURES = (
    "Notes",
    "Metadata",
    "Terms and Conditions",
    "Total annual income",
)
NOTE_AT, FIGURES_AT = 3, 4
NOTE_TEXT = "Note text"
CODE, DISTRICT = "MSOA code", "Local authority code"
ESTIMATE = "Total annual income (£)"
UPPER, LOWER = "Upper confidence limit (£)", "Lower confidence limit (£)"
COLUMNS = (CODE, DISTRICT, ESTIMATE, UPPER, LOWER)
AN_MSOA = re.compile(r"[EW]02[0-9]{6}")
A_DISTRICT = re.compile(r"[EW]0[6-9][0-9]{6}")

# What the workbook must say of itself for the words of the page to be its own. Each is a
# part of a sentence of the publisher's, and the page quotes the sentence it is part of.
SAID_OF_THE_YEAR = "refers to the period between 1st April {start} to 31st March {end}"
SAID_OF_THE_CODES = "MSOA codes used by ONS from Census 2021"
SAID_OF_THE_MODEL = "model-based small area income estimates for financial year ending {end}"
SAID_OF_THE_KIND = "Total annual household income is the sum of the gross income"
SAID_OF_THE_CREDIT = "Source: Office for National Statistics"
FIRST_MONTH, LAST_MONTH = "04", "03"


@dataclass(frozen=True)
class Estimate:
    """The publisher's figure of one MSOA, in whole pounds a year."""

    estimate: int
    lower: int
    upper: int

    def __repr__(self) -> str:
        # A figure is of residents. Nothing prints one by accident.
        return "Estimate()"


@dataclass(frozen=True)
class Estimated:
    """The figure of every area of a build, and what stands behind it. It names no figure."""

    # The figure of each area, by its id. An area the publisher gives none for is not here.
    of: Mapping[str, Estimate]
    # Every area of the build, in the order of its id.
    areas: tuple[str, ...]
    receipt: Receipt
    # How many rows of an MSOA the sheet holds, those outside the build too.
    rows: int

    @property
    def given(self) -> int:
        return len(self.of)


def is_the_workbook(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the file that is read."""
    return name == WORKBOOK


def _refused(opened: Opened, words: str) -> LockError:
    return LockError("input_is_as_described", opened.file_id, words)


def _said(opened: Opened, sheet: str, heading: str, header_at: int = 1) -> list[str]:
    """Every line of words of one column of a sheet of words."""
    rows = read_sheet(opened, sheet, (heading,), header_at=header_at)
    return [held for row in rows if isinstance(held := row[heading], str)]


def hold_the_words(opened: Opened) -> None:
    """Stop unless the workbook says of itself what the page will say of it.

    The year is the one the receipt gives, the estimates are said to be from a
    model, the codes are those of the census of 2021, the kind of income is
    defined as the page defines it, and the credit is the one the page gives.
    Nothing of the workbook is repeated in a refusal.
    """
    period = opened.receipt.data_period
    start, end = str(period.start or ""), str(period.end or "")
    if not (start.endswith(f"-{FIRST_MONTH}") and end.endswith(f"-{LAST_MONTH}")):
        raise _refused(opened, "its receipt is not of a financial year")
    if int(end[:4]) - int(start[:4]) != 1:
        raise _refused(opened, "its receipt is not of a financial year")
    notes = _said(opened, NOTES, NOTE_TEXT, NOTE_AT)
    of_the_year = SAID_OF_THE_YEAR.format(start=start[:4], end=end[:4])
    if not any(of_the_year in note for note in notes):
        raise _refused(opened, "its notes do not give the year its receipt gives")
    if not any(SAID_OF_THE_CODES in note for note in notes):
        raise _refused(opened, "its notes do not say its codes are of the census of 2021")
    about = _said(opened, METADATA, METADATA)
    if not any(SAID_OF_THE_MODEL.format(end=end[:4]) in line for line in about):
        raise _refused(opened, "it does not say the estimates are from a model")
    if not any(line.startswith(f"1. {SAID_OF_THE_KIND}") for line in about):
        raise _refused(opened, "it does not define the kind of income that is read")
    if not any(SAID_OF_THE_CREDIT in line for line in _said(opened, TERMS, TERMS)):
        raise _refused(opened, "it does not ask for the credit that is given")


def _pounds(opened: Opened, cell: Value) -> int | None:
    """A figure in whole pounds, or none where the cell is empty."""
    if cell is None:
        return None
    if not (isinstance(cell, float) and cell.is_integer() and cell > 0):
        raise _refused(opened, "a figure is not a figure")
    return int(cell)


def read(opened: Opened) -> tuple[dict[str, Estimate], dict[str, str], int]:
    """The figure of every MSOA the sheet gives one for, its local authority, and the rows.

    It stops at a column that is missing, a code that is no code, an MSOA
    that is there twice, a cell that is no figure, and an estimate that does
    not stand with both its limits and between them.
    """
    hold_the_words(opened)
    rows = read_sheet(opened, FIGURES, COLUMNS, header_at=FIGURES_AT)
    found: dict[str, Estimate] = {}
    district: dict[str, str] = {}
    for row in rows:
        code, within = row[CODE], row[DISTRICT]
        if not (isinstance(code, str) and AN_MSOA.fullmatch(code)):
            raise _refused(opened, "a code is not a code")
        if not (isinstance(within, str) and A_DISTRICT.fullmatch(within)):
            raise _refused(opened, "a code is not a code")
        if code in district:
            raise _refused(opened, "an MSOA is there twice")
        district[code] = within
        held = tuple(_pounds(opened, row[name]) for name in (LOWER, ESTIMATE, UPPER))
        lower, estimate, upper = held
        if lower is None and estimate is None and upper is None:
            continue
        if lower is None or estimate is None or upper is None:
            raise _refused(opened, "an estimate stands without both its limits")
        if not lower <= estimate <= upper:
            raise _refused(opened, "an estimate does not stand between its limits")
        found[code] = Estimate(estimate=estimate, lower=lower, upper=upper)
    if not district:
        raise _refused(opened, "it holds no row of an MSOA")
    return found, district, len(rows)


def build(inputs: Inputs, found: Spine) -> Estimated:
    """The publisher's figure of every area of the build, from the files of the build.

    The gate is asked about the workbook before it is read, for `display`.
    `found` is the spine of the same build. An area has a figure only where it
    is one MSOA and the sheet gives that MSOA one: nothing is worked out.
    """
    opened = inputs.open(SOURCE, USE, named=is_the_workbook)
    figures, district, rows = read(opened)
    if any(area.code not in district for area in found.areas):
        raise _refused(opened, "an MSOA of the census of 2021 has no row")
    if any(district[area.code] != area.borough_code for area in found.areas):
        raise _refused(opened, "an MSOA is in another borough than the lookup gives")
    return Estimated(
        of={area.area_id: figures[area.code] for area in found.areas if area.code in figures},
        areas=tuple(sorted(area.area_id for area in found.areas)),
        receipt=opened.receipt,
        rows=rows,
    )


def income_of(release_id: str, estimated: Estimated, registry: Registry) -> Income:
    """What is written beside a release: every area of it, with the figure of each that has one.

    The source is as the licence registry gives it, which is asked once more,
    for `display`, before anything is put together.
    """
    entry = registry.require(SOURCE, USE)
    period = estimated.receipt.data_period
    areas = tuple(
        AreaIncome(
            area_id=area_id,
            estimate=held.estimate if held else None,
            lower=held.lower if held else None,
            upper=held.upper if held else None,
        )
        for area_id in estimated.areas
        for held in (estimated.of.get(area_id),)
    )
    return Income(
        release_id=release_id,
        synthetic=False,
        start=str(period.start),
        end=str(period.end),
        source=IncomeSource(
            source_id=SOURCE,
            name=entry.name,
            publisher=entry.publisher,
            licence=entry.licence,
            attribution=entry.attribution,
            url=entry.url,
            retrieved_on=estimated.receipt.retrieved_at[:10],
        ),
        areas=areas,
    )
