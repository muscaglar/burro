"""The nearest GP practice: how far it is, in a straight line, from where homes are.

NHS England's Organisation Data Service publishes a report of every
prescribing cost centre of England and Wales, of which GP practices are a
part. It gives a practice by its postcode and by no point. `cells/postcodes.py`
gives the postcode a point, and `nearest_by_postcode.py` measures to it.

**This was written before any file of the report was fetched.** It rests on
the publisher's specification of the report, which was read on 2026-09-24
through a reader that extracts, three times, in different words. What the
specification says, and what it does not:

| The specification says | So here |
|---|---|
| 27 columns, and of none that it is a row of names | A line of another width stops the step |
| Column 10 is the postcode | It is read, to place the practice |
| Column 12 is the close date, of up to 8 characters | It is read: 8 digits, or nothing |
| Column 13 is the status, once a letter and now in full | It is read: one of four names |
| Column 26 is the prescribing setting, as a role | It is read. `RO76` is a GP practice |
| Column 2 is a name, 5 to 9 an address, 18 a telephone number | Never read |

It does not say how a status is spelled in full, in capitals or not, or what
a date looks like. The two reports of the same service that were fetched
write a date as 8 digits, and hold no status. So a status is read whatever
its case, and one that is none of the four names stops the step.

**The first file was fetched on 2026-09-24, and the step stops at it.** It
holds no row of names and 27 columns to a line, and writes a date as 8 digits,
as the step expects. It writes a status as `ACTIVE`, `INACTIVE` or `DORMANT`,
and the step names no `INACTIVE`. In a few lines it writes two prescribing
settings in one cell, with a bar between them, where the step holds a cell to
one. `docs/research/data/postcodes.md` holds the counts. When the step is put
right, put its counts in a test on the real files.

**What counts as a GP practice.** A row whose status is active, whose close
date is empty, and whose prescribing setting is that of a GP practice. The
report holds walk-in centres, hospital services, prisons and more beside
them, each under a setting of its own, and none of those counts.

**What is never read.** The name of a practice is often a doctor's. So the
name, every line of the address and the telephone number are never read. A
row that is handed on holds the four columns that are read and no other.

It is a straight line, and not a walk, and it is given to the nearest 100
metres: `nearest_by_postcode.py` says why. The row of the catalogue says a
straight line in metres, as core names the measure. It is on the list of no
build yet: `WAITS_ON` says what would bring it in.

Branch surgeries are not read. The publisher gives them in a report of their
own, which the licence registry does not cover.
"""

import csv
import re
from collections import Counter
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass

from burro_core.catalogue import FEATURES
from burro_core.ids import FeatureId, NativeResolution
from burro_core.ids import Method as MadeBy
from burro_core.release import Metric

from burro_pipeline.cells import postcodes
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import nearest_by_postcode
from burro_pipeline.derive.methods import Worked
from burro_pipeline.derive.nearest_by_postcode import Distances, Placing
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Method
from burro_pipeline.evidence.receipt import Geography, Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

FEATURE = FeatureId.GP_WALK
SOURCE = "nhs-ods-gp-practices"
PUBLISHER, REPORT = "NHS England", "epraccur"
USE = Use.SCORING
# The publisher's name for the file of the report.
FILE = "epraccur.csv"
# How many columns a line holds, and the place of each that is read, counted from 1 as the
# specification counts them.
WIDTH = 27
POSTCODE, CLOSED, STATUS, SETTING = 10, 12, 13, 26
READ: Mapping[str, int] = {
    "postcode": POSTCODE,
    "closed": CLOSED,
    "status": STATUS,
    "setting": SETTING,
}
# The columns that may say who a person is, by their place. None is ever read.
NEVER_READ: Mapping[str, tuple[int, ...]] = {
    "name": (2,),
    "address": (5, 6, 7, 8, 9),
    "telephone": (18,),
}
# The four names the specification gives for a status. One counts.
ACTIVE = "active"
STATUSES = frozenset({ACTIVE, "closed", "dormant", "proposed"})
# The prescribing setting of a GP practice, as the specification gives it.
GP_PRACTICE = "RO76"
A_SETTING = re.compile(r"RO[0-9]{1,4}")
A_DAY = re.compile(r"[0-9]{8}")
UNIT = "m"

METHOD = nearest_by_postcode.METHOD
METHODS: tuple[Method, ...] = (METHOD,)
# What a person reads beside the figure: it is a straight line, and no walk, and a practice
# is put where its postcode is.
LABEL = "Straight-line distance to the nearest GP practice, placed by its postcode"
# What the measure is, from whom, for what period, and what it is not.
DEFINITION = (
    "The distance in a straight line, in metres, from the point the statistics office gives as "
    "the centre of each census output area to the nearest GP practice that the report "
    "{report} of {publisher} lists as active, as at {as_at}, each practice put at the point "
    "the {directory} gives for its postcode, as the median over the area's homes at the "
    "census of {census} and given to the nearest {nearest} metres with a half taken upward: it "
    "is measured across whatever lies between and not along any street, so the walk is longer, "
    "a practice is put at a door of its postcode that may not be its own, a branch surgery is "
    "not counted, and a practice outside London is not counted."
)
# What keeps the measure out of a release, and whose it is to settle.
OF_THE_FILE = (
    "The step was written from the publisher's specification, before a file of the report was "
    "fetched. The first file writes a status the specification did not name, and two "
    "prescribing settings in one cell in a few lines, so the step stops at it until it is put "
    "right.",
    "The plan lists GP access as out of the first version, and the design of the London data "
    "recommends that the walk comes in. Which stands is the founder's to say.",
    "A practice outside London is placed nowhere, because the licence registry keeps London's "
    "rows of the postcode directory alone. So the homes near the edge of London are left out "
    "of the figure. The rows of the districts that border London would close it, and whether "
    "they are kept is the founder's to say.",
)
WAITS_ON = OF_THE_FILE
# What the product shows beside the figure.
NOT_A_BRANCH = (
    "It measures to the main address of a practice, so a branch surgery that is nearer is not "
    "counted, and the figure reads further than the nearest place a GP is seen."
)
NOT_ABLE_TO_REGISTER = (
    "Near is not able to register: nothing here says whether a practice takes new patients, "
    "when it is open, or how long a person waits to be seen."
)
CANNOT_SEE = (*nearest_by_postcode.OF_EVERY_MEASURE, NOT_A_BRANCH, NOT_ABLE_TO_REGISTER)


@dataclass(frozen=True)
class Report:
    """What the report holds, as counts, and the postcode of each practice that counts."""

    file_id: str
    # Every line of the file.
    rows: int
    # The rows by their status, in small letters, and how many have the setting of a GP practice.
    by_status: Mapping[str, int]
    of_a_gp_practice: int
    # The postcode of each practice that counts, as the file writes it. It stays inside the
    # build: what is printed of the report is counts.
    postcodes: tuple[str, ...]

    def __repr__(self) -> str:
        """Counts alone, so that a line that prints the report prints no postcode."""
        return f"Report(rows={self.rows}, counted={len(self.postcodes)})"


@dataclass(frozen=True)
class Walk:
    """The distance to the nearest GP practice for every area, with what stands behind it."""

    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    files: tuple[Receipt, ...]
    geography: Geography
    metric: Metric
    report: Report
    placing: Placing
    distances: Distances


def is_the_report(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the file this measure reads."""
    return name == FILE


def _not_as_described(opened: Opened, words: str) -> LockError:
    return LockError("input_is_as_described", opened.file_id, words)


def _read(opened: Opened) -> Iterator[dict[str, str]]:
    """The rows of the report, each with the four columns that are read and no other."""
    with opened.text() as text:
        try:
            for line in csv.reader(text):
                if len(line) != WIDTH:
                    raise _not_as_described(opened, "a line has not the columns of the report")
                yield {name: line[place - 1].strip() for name, place in READ.items()}
        except csv.Error:
            raise _not_as_described(opened, "a row is broken") from None


def read(opened: Opened) -> Report:
    """The report: what it holds as counts, and the postcode of each practice that counts.

    It stops at a line that is not 27 columns wide, at a status that is none
    of the four the specification names, at a close date that is no day, and
    at a prescribing setting that is not written as a role. What it says of a
    refusal repeats nothing the file holds.
    """
    by_status: Counter[str] = Counter()
    rows = practices = 0
    counted: list[str] = []
    for row in _read(opened):
        rows += 1
        status = row["status"].casefold()
        if status not in STATUSES:
            raise _not_as_described(opened, "a status is not one the specification names")
        if row["closed"] and A_DAY.fullmatch(row["closed"]) is None:
            raise _not_as_described(opened, "a close date is no day")
        if row["setting"] and A_SETTING.fullmatch(row["setting"]) is None:
            raise _not_as_described(opened, "a prescribing setting is not written as a role")
        by_status[status] += 1
        if row["setting"] != GP_PRACTICE:
            continue
        practices += 1
        if status == ACTIVE and not row["closed"]:
            counted.append(row["postcode"])
    if not rows:
        raise _not_as_described(opened, "it holds no row")
    return Report(
        file_id=opened.file_id,
        rows=rows,
        by_status=dict(sorted(by_status.items())),
        of_a_gp_practice=practices,
        postcodes=tuple(sorted(counted)),
    )


def definition_of(as_at: str) -> str:
    """The sentence a methods page prints for the measure."""
    return DEFINITION.format(
        report=REPORT,
        publisher=PUBLISHER,
        as_at=as_at,
        directory="ONS Postcode Directory",
        census=nearest_by_postcode.CENSUS,
        nearest=nearest_by_postcode.NEAREST,
    )


def metric_of(files: Sequence[Receipt], as_at: str) -> Metric:
    """The row of the catalogue: the name, the unit, the period and every source.

    Core decides which way is more, what kind of thing the measure is and
    where it is shown. The name and the unit are the ones the figure supports:
    a straight line, in metres, which is what core says too. The sources name
    the postcode directory, so that its three credits are shown wherever the
    figure is.
    """
    core = FEATURES[FEATURE]
    return Metric(
        feature_id=core.feature_id,
        label=LABEL,
        short_label=core.short_label,
        dimension=core.dimension,
        unit=UNIT,
        polarity=core.polarity,
        kind=core.kind,
        describes=core.describes,
        family=core.family,
        method=MadeBy(METHOD.kind.value),
        in_likeness=core.in_likeness,
        native_resolution=NativeResolution.POINT,
        source_ids=tuple(sorted({receipt.source_id for receipt in files})),
        vintage=as_at,
        rankable=True,
        definition=definition_of(as_at),
    )


def build(
    inputs: Inputs, found: Spine, *, edition: str | None = None, directory: str | None = None
) -> Walk:
    """The distance to the nearest GP practice for every area, and its evidence.

    The gate is asked about the report, the directory and the centres before
    any is read. `found` is the spine of the same build. `edition` is the
    edition of the report, and `directory` that of the postcode directory,
    where a build holds more than one of either.
    """
    listed = inputs.open(SOURCE, USE, edition=edition, named=is_the_report)
    report = read(listed)
    made = nearest_by_postcode.build(
        inputs, found, listed, report.postcodes, FEATURE, directory=directory
    )
    first, last = listed.receipt.data_period.days()
    as_at = first if first == last else f"{first} to {last}"
    return Walk(
        worked=made.worked,
        rows=made.rows,
        files=made.files,
        geography=made.geography,
        metric=metric_of(made.files, as_at),
        report=report,
        placing=made.placing,
        distances=made,
    )


def credits_of(walk: Walk) -> tuple[str, ...]:
    """The three credits of the postcode directory, which stand wherever the figure does."""
    (directory,) = [receipt for receipt in walk.files if receipt.source_id == postcodes.SOURCE]
    return postcodes.credits_of(directory)
