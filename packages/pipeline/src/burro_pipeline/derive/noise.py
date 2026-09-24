"""Transport noise: the share of residents exposed to 55 dB or more, for each area.

The figure comes from File 8 of the English Indices of Deprivation 2025, the
underlying indicators. One column of one sheet is read, `Noise pollution`, with
the code of the LSOA beside it. Every other sheet of figures in the workbook
is about residents and is never opened, and no other column of this sheet is
read.

What the file says of the column, on its sheet of notes:

- It is the share of the population of each LSOA exposed to combined transport
  noise of 55 dB or more, on the day, evening and night measure, which is an
  average over the year. It is written as a share from 0 to 1, to 3 decimal
  places.
- Its supplier is Defra's noise modelling system, and it describes 2021.
- Its top is the residents of the LSOA who are exposed, and its bottom is the
  population of the LSOA in 2021. Neither is in the file.
- Shrinkage was applied to it. The file does not say what that did.

What the file does not say, so that nothing here claims it:

- Which kinds of transport were counted. The notes say "combined transport
  noise" and name no road, railway or airport.
- How a resident is placed in the noise: at a home, at a postcode or otherwise.
- Whether the level is at 55 dB or above it. One sentence of the notes says
  "greater than or equal to" and the next says "above". The label follows the
  first, which is the one that says what the indicator is.

Is it a measure of a place? It is. The noise is a model's, of whatever
transport the model took in, and the residents are how the places of an LSOA
are weighed: a loud place where nobody lives counts for nothing, and a loud
place where many live counts for much. It says how much of where an area's
people live is loud. It says nothing of who they are: no age, no income, no
health, no origin. So it may be ranked on (ADR 0006), and the sentence of the
measure says so.

It is a share of residents, and not of homes. So the name of the measure says
residents, and never homes. Core lets no word for who lives somewhere stand in
the name of a thing a person can rank on, and lets this one name through,
whole: it says whose share the figure is, and nothing of who they are. It was
decided on 2026-09-24 (ADR 0006). The sentence of the measure says in full
what is counted. `LABEL` is that name, and it is core's. While the two are the
same a build carries the measure.

How a figure is made. No top and no bottom are published, so no sum can be
taken, and the file holds no row for an area larger than an LSOA. An area's
figure is the mean of its LSOAs' shares, weighted by their homes at the census
of 2021: the method `lsoa_value_by_homes`, which is marked as averaged. The
weight is homes and the share is of residents, so the mean is near the area's
own share and is not the same as it.

Nothing is filled in. An LSOA with no row, or with a row and no share, adds
nothing, and the area's coverage falls by its homes. A share outside 0 to 1
stops the step.

What is read from the file and never assumed:

| What | Where it is read |
|---|---|
| The census the codes follow | The name of the column, `LSOA code (2021)` |
| The year the indicator describes | Its row on the sheet of notes |
| The level the measure is named for | The same row |
| That it counts residents, and transport noise | The same row |
| The measure of the level, the supplier, and that shrinkage was applied | The same row |

The step stops if the receipt states another year than the notes, and if the
notes no longer say any one of the things the label or the sentence claims.
"""

import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace

from burro_core.facts import fact_id
from burro_core.ids import FactKind, FeatureId
from burro_core.release import Metric

from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive.catalogue_row import catalogue_row
from burro_pipeline.derive.methods import (
    LSOA_VALUE_BY_HOMES,
    Worked,
    lsoa_value_by_homes,
    row_of,
    to_places,
)
from burro_pipeline.derive.noise_sheet import Row, read_sheet
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Method
from burro_pipeline.evidence.receipt import Geography, Period, Receipt
from burro_pipeline.evidence.row import EvidenceRow, Flag
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

FEATURE = FeatureId.NOISE_EXPOSURE
SOURCE = "mhclg-iod-2025-underlying-indicators"
EDITION = "2025"
# The publisher's name for the file starts so. The entry of its source covers File 8 alone.
FILE_STARTS = "File_8"

# The one sheet of figures that is opened, and the two columns of it that are read.
SHEET = "IoD25 Living Env Domain"
LSOA_CODE, NOISE = "LSOA code (2021)", "Noise pollution"
# The sheet of notes. The row that names its columns is the eleventh.
NOTES, NOTES_HEADER_AT = "Notes", 11
INDICATOR, SUPPLIER = "Indicator", "Data supplier"
TIME_POINT, COMMENTS = "Data time point", "Comments"
# What the rows of the sheet are keyed by, as the name of the column says.
KEYED_BY = Geography.LSOA21

# The level the measure is named for, in decibels. The notes must give it.
DECIBELS = 55
# The publisher writes a share to this many decimal places.
DECIMAL_PLACES = 3
# A share is written from 0 to 1, and is shown as a percentage.
TIMES = 100
# A figure is given to this many decimal places. The publisher writes a share to a tenth of
# a point, so a second place would say nothing.
DECIMALS = 1

AN_LSOA = re.compile(r"E01[0-9]{6}")
A_YEAR = re.compile(r"(19|20)[0-9]{2}")
THE_LEVEL = re.compile(rf"\b{DECIBELS} ?dB\b")
# What the notes must say of the indicator, beside its level and its year, for the label and
# the sentence of the measure to say it: where it is looked for, the words that say it, and
# the fixed words of the refusal where they are not there.
CLAIMED: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        COMMENTS,
        re.compile(r"\b(population|residents)\b"),
        "its notes do not say it counts residents",
    ),
    (COMMENTS, re.compile(r"\bexposed to\b"), "its notes do not say it counts who is exposed"),
    (COMMENTS, re.compile(r"\btransport noise\b"), "its notes do not say it is transport noise"),
    (COMMENTS, re.compile(r"\bLden\b"), "its notes do not name the measure of the level"),
    (
        COMMENTS,
        re.compile(r"\b[Ss]hrinkage was applied\b"),
        "its notes do not say shrinkage was applied",
    ),
    (SUPPLIER, re.compile(r"\bDefra\b"), "its notes do not name the supplier the measure names"),
)

# The arithmetic: what a methods page prints beside the measure.
METHODS: tuple[Method, ...] = (LSOA_VALUE_BY_HOMES,)
# What a person reads beside the figure. The file counts residents and no homes, so the name
# says residents and never homes. It says whose share it is and nothing of who they are.
LABEL = "Share of residents exposed to 55 dB or more of transport noise"
# What the measure is, from whom, for what period, and what it is not.
DEFINITION = (
    "The share of each small census area's residents exposed to combined transport noise of "
    "{decibels} dB or more on the day, evening and night measure, which is an average over the "
    "year, as Defra's noise modelling system gives it for {year} and the English Indices of "
    "Deprivation 2025 publish it to {places} decimal places with shrinkage applied, times "
    "{times}, averaged over the area's small census areas by their homes at the census of 2021 "
    "and given to {decimals} decimal place with a half taken upward, so it says how much of "
    "where an area's people live is loud and nothing of who they are, and it is a modelled "
    "share of residents and not a share of homes, a reading taken in any street or a level in "
    "decibels."
)
# What the product shows beside the figure.
CANNOT_SEE = (
    "This is modelled transport noise for 2021, averaged over the year and over the area, so "
    "it cannot tell a loud street from a quiet one nearby, or a level just over 55 dB from one "
    "far above it.",
    "It gives one figure for all transport noise and does not say which kinds of transport were "
    "counted, and it counts no noise from neighbours, venues or building works.",
)


def is_the_workbook(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the workbook this measure reads."""
    return name.startswith(FILE_STARTS)


@dataclass(frozen=True)
class Sheet:
    """What the file holds of noise: the share of each LSOA, as its publisher wrote it."""

    # The share of each LSOA that has one, from 0 to 1.
    share: Mapping[str, float]
    # The rows under the header, for all of England.
    rows: int
    # The LSOAs with a row and no share. Nothing stands in for one.
    without: tuple[str, ...]
    # The year the notes say the indicator describes.
    year: str
    file_id: str


@dataclass(frozen=True)
class Noise:
    """The figure of every area, in percent, with what stands behind each."""

    # The figure of each area, by its id. An area with no figure is here too, with its state.
    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    metric: Metric
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    sheet: Sheet
    geography: Geography


def _refused(opened: Opened, words: str) -> LockError:
    return LockError("input_is_as_described", opened.file_id, words)


def year_in_the_notes(opened: Opened) -> str:
    """The year the indicator describes, as the notes of the file give it.

    The notes hold one row for the indicator. It must say what the label and
    the sentence of the measure say of it: the level, that residents are
    counted, that the noise is of transport, the measure of the level, the
    supplier, and that shrinkage was applied. So a file whose indicator has
    changed is noticed, and nothing is claimed that the file does not say.
    """
    notes = read_sheet(
        opened, NOTES, (INDICATOR, SUPPLIER, TIME_POINT, COMMENTS), header_at=NOTES_HEADER_AT
    )
    found = [row for row in notes if row[INDICATOR] == NOISE]
    if len(found) != 1:
        raise _refused(opened, "its notes do not hold one row for the indicator")
    year, said = found[0][TIME_POINT], found[0][COMMENTS]
    if isinstance(year, float) and year.is_integer():
        year = str(int(year))
    if not (isinstance(year, str) and A_YEAR.fullmatch(year)):
        raise _refused(opened, "its notes give no year for the indicator")
    if not (isinstance(said, str) and THE_LEVEL.search(said)):
        raise _refused(opened, "its notes do not give the level the measure is named for")
    for column, words, refusal in CLAIMED:
        held = found[0][column]
        if not (isinstance(held, str) and words.search(held)):
            raise _refused(opened, refusal)
    return year


def _share_of(opened: Opened, row: Row) -> tuple[str, float | None]:
    code, share = row[LSOA_CODE], row[NOISE]
    if not (isinstance(code, str) and AN_LSOA.fullmatch(code)):
        raise _refused(opened, "a code is not a code")
    if share is None:
        return code, None
    if not (isinstance(share, float) and math.isfinite(share) and 0.0 <= share <= 1.0):
        raise _refused(opened, "a share is not a share")
    return code, share


def read(opened: Opened) -> Sheet:
    """The share of every LSOA in the file, held to what a share can be.

    It stops at a sheet or a column that is missing, a code that is no code, an
    LSOA that is there twice, and a share that is not a number from 0 to 1.
    """
    year = year_in_the_notes(opened)
    rows = read_sheet(opened, SHEET, (LSOA_CODE, NOISE))
    share: dict[str, float] = {}
    without: set[str] = set()
    for row in rows:
        code, found = _share_of(opened, row)
        if code in share or code in without:
            raise _refused(opened, "an LSOA is there twice")
        if found is None:
            without.add(code)
        else:
            share[code] = found
    if not rows:
        raise _refused(opened, "it holds no row of an LSOA")
    return Sheet(
        share=share,
        rows=len(rows),
        without=tuple(sorted(without)),
        year=year,
        file_id=opened.file_id,
    )


def is_rounded(sheet: Sheet) -> bool:
    """Whether every share is written to the decimal places the publisher says it is."""
    return all(
        math.isclose(share, round(share, DECIMAL_PLACES), abs_tol=1e-12)
        for share in sheet.share.values()
    )


def figures(sheet: Sheet, found: Spine) -> dict[str, Worked]:
    """The figure of every area, in percent, or why an area has no figure.

    It is the mean of the shares of the area's LSOAs, weighted by their homes.
    An LSOA with no share adds nothing, and the area's coverage falls by its
    homes. It stops if the sheet holds no LSOA of the spine at all: it is then
    a sheet of somewhere else, or of another census.
    """
    if not any(lsoa in sheet.share or lsoa in sheet.without for lsoa in found.lsoas):
        raise LockError("input_is_as_described", sheet.file_id, "it holds no row of London")
    percent = {lsoa: TIMES * sheet.share[lsoa] for lsoa in found.lsoas if lsoa in sheet.share}
    flags = [Flag.ROUNDED_IN_SOURCE] if is_rounded(sheet) else []
    worked = lsoa_value_by_homes(percent, found.lsoa_of, found.weights, flags=flags)
    return {
        area: one if one.value is None else replace(one, value=to_places(one.value, DECIMALS))
        for area, one in worked.items()
    }


def metric_of(files: Sequence[Receipt], year: str) -> Metric:
    """The row of the catalogue: the name, the unit, the period and every source.

    Core decides the unit and which way is more. The name is `LABEL`: the one
    the file supports, which core gives it too. The period is the year the
    notes give.
    """
    return catalogue_row(
        FEATURE,
        method=LSOA_VALUE_BY_HOMES,
        label=LABEL,
        source_ids={receipt.source_id for receipt in files},
        vintage=year,
        definition=DEFINITION.format(
            decibels=DECIBELS,
            year=year,
            places=DECIMAL_PLACES,
            times=TIMES,
            decimals=DECIMALS,
        ),
    )


def build(inputs: Inputs, found: Spine) -> Noise:
    """The figure of every area and its evidence, from the files of the build.

    The gate is asked about the workbook before it is read. `found` is the
    spine of the same build: a row of evidence names its files beside the
    workbook, so they must be files this build opened.
    """
    opened = inputs.open(SOURCE, Use.SCORING, edition=EDITION, named=is_the_workbook)
    sheet = read(opened)
    if opened.receipt.data_period != Period(as_at=sheet.year):
        raise _refused(opened, "its receipt gives another period than its notes")
    handed = {one.file_id: one.receipt for one in inputs.opened}
    behind = sorted({opened.file_id, *found.inputs})
    for file_id in behind:
        if file_id not in handed:
            raise LockError("input_has_one_receipt", file_id)
    files = tuple(handed[file_id] for file_id in behind)
    worked = figures(sheet, found)
    rows = tuple(
        row_of(fact_id(area, FactKind.FEATURE, FEATURE), worked[area], LSOA_VALUE_BY_HOMES, files)
        for area in sorted(worked)
    )
    return Noise(
        worked=worked,
        rows=rows,
        metric=metric_of(files, sheet.year),
        files=files,
        sheet=sheet,
        geography=KEYED_BY,
    )
