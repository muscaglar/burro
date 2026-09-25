"""The nearest pharmacy: how far it is, in a straight line, from where homes are.

The NHS Business Services Authority publishes, each quarter, one list of
every contractor on the pharmaceutical lists of England: NHS pharmacies,
appliance contractors and local pharmaceutical services contractors. It gives
a contractor by its postcode and by no point. `cells/postcodes.py` gives the
postcode a point, and `nearest_by_postcode.py` measures to it.

**It was written before any file of the list was fetched, and the first file
is as it expects.** It rests on the list of fields on the publisher's page of
the file for quarter 1 of 2026-27, which was read on 2026-09-24 through a
reader that extracts, twice, in different words, and on the file that was
fetched that day. The page names 25 fields. Two are read:

| Field | What the page says it is | Read |
|---|---|---|
| `POST_CODE` | Post code | Yes, to place the contractor |
| `CONTRACT_TYPE` | Type of contractor: Community, DAC or LPS | Yes, to say which count |
| `ORGANISATION_NAME` | The name of whoever is included in a pharmaceutical list | Never |
| `PHARMACY_TRADING_NAME` | Trading name of contractor | Never |
| `ADDRESS_FIELD_1` to `ADDRESS_FIELD_4` | The lines of an address | Never |
| `PHARMACY_ODS_CODE_F_CODE` | The code of the contractor | Never: nothing needs it |
| `HEALTH_AND_WELLBEING_BOARD` | The board whose list it is on | Never: nothing needs it |
| The 15 fields of opening hours | The hours of each day, and their totals | Never |

What the page says of `ORGANISATION_NAME` was read two ways, and the registry
entry has both. By either it may be the name of a person.

The page does not say how the file is encoded, or whether a contract type is
written in capitals. So a type is read whatever its case, and one that is
none of the three stops the step. The first file is a CSV in UTF-8 of 10,507
rows, under one row of names, which are the 25 fields the page lists, in
their order. It writes the three types the page names and no other, so the
step read it to its end as it was written.
`test_pharmacy_walk_on_the_real_files.py` holds the counts of the file, and
`docs/research/data/postcodes.md` says what it was found to hold.

**The list is of a quarter, and says no day.** No field is a day, and no page
says what day the list is as at. The list `m10-health` states the period of
the file as the quarter its publisher's title names, and says what that rests
on. So the sentence of the measure says the period, and never "as at".

**What counts as a pharmacy.** A contractor whose type is Community or LPS.
As the reader gave the page, Community is a person who provides
pharmaceutical services by the provision of drugs, LPS is a chemist in a
local pharmaceutical services scheme, and DAC is a dispensing appliance
contractor. An appliance contractor is no pharmacy, and does not count.

**What it cannot tell.** The list has no field that says a pharmacy serves by
post alone and takes no callers. Such a pharmacy is on the list as any other,
so it is counted, and `CANNOT_SEE` says so.

It is a straight line, and not a walk, and it is given to the nearest 100
metres: `nearest_by_postcode.py` says why. The row of the catalogue says a
straight line in metres, as core names the measure, so a build that names the
list of health files and the list of the postcode directory carries it. It is
on the table of a build because Everyday on foot rests on it for 15 in 100.
A pharmacy outside London is placed nowhere, so the homes near the edge of
London are left out of the figure: whether the rows of the districts that
border London are kept is the founder's to say.
"""

import re
from collections import Counter
from collections.abc import Mapping, Sequence
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

FEATURE = FeatureId.PHARMACY_WALK
SOURCE = "nhsbsa-consolidated-pharmaceutical-list"
PUBLISHER, LIST = "NHS Business Services Authority", "Consolidated Pharmaceutical List"
USE = Use.SCORING
# The publisher's name for a file of the list: the quarter, and sometimes that it is final.
FILE = re.compile(r"consol_pharmacy_list_[0-9]{6}q[1-4](final)?\.csv")
POSTCODE, CONTRACT = "POST_CODE", "CONTRACT_TYPE"
# The columns that are read, and no other.
READ = (POSTCODE, CONTRACT)
# Every field of the file, in its order, as the publisher's page names them.
HELD = (
    "PHARMACY_ODS_CODE_F_CODE",
    "HEALTH_AND_WELLBEING_BOARD",
    "PHARMACY_TRADING_NAME",
    "ORGANISATION_NAME",
    "ADDRESS_FIELD_1",
    "ADDRESS_FIELD_2",
    "ADDRESS_FIELD_3",
    "ADDRESS_FIELD_4",
    "POST_CODE",
    "PHARMACY_OPENING_HOURS_MONDAY",
    "MON_TOTAL",
    "PHARMACY_OPENING_HOURS_TUESDAY",
    "TUES_TOTAL",
    "PHARMACY_OPENING_HOURS_WEDNESDAY",
    "WED_TOTAL",
    "PHARMACY_OPENING_HOURS_THURSDAY",
    "THURS_TOTAL",
    "PHARMACY_OPENING_HOURS_FRIDAY",
    "FRI_TOTAL",
    "PHARMACY_OPENING_HOURS_SATURDAY",
    "SAT_TOTAL",
    "PHARMACY_OPENING_HOURS_SUNDAY",
    "SUN_TOTAL",
    "WEEKLY_TOTAL",
    "CONTRACT_TYPE",
)
# The fields that may say who a person is. None is ever read.
NEVER_READ = (
    "ORGANISATION_NAME",
    "PHARMACY_TRADING_NAME",
    "ADDRESS_FIELD_1",
    "ADDRESS_FIELD_2",
    "ADDRESS_FIELD_3",
    "ADDRESS_FIELD_4",
)
# The three types of contract the page gives, in small letters, and whether each counts.
COUNTS: Mapping[str, bool] = {"community": True, "lps": True, "dac": False}
UNIT = "m"

METHOD = nearest_by_postcode.METHOD
METHODS: tuple[Method, ...] = (METHOD,)
# What a person reads beside the figure: it is a straight line, and no walk, and a pharmacy
# is put where its postcode is.
LABEL = "Straight-line distance to the nearest pharmacy, placed by its postcode"
# What the measure is, from whom, for what period, and what it is not.
DEFINITION = (
    "The distance in a straight line, in metres, from the point the statistics office gives as "
    "the centre of each census output area to the nearest contractor that the {list} of the "
    "{publisher} lists as a pharmacy or as a local pharmaceutical services contractor, "
    "{when}, each put at the point the {directory} gives for its postcode, as the median "
    "over the area's homes at the census of {census} and given to the nearest {nearest} metres "
    "with a half taken upward: it is measured across whatever lies between and not along any "
    "street, so the walk is longer, a pharmacy is put at a door of its postcode that may not "
    "be its own, a pharmacy that serves by post alone is counted, and a pharmacy outside "
    "London is not counted."
)
# Nothing keeps the measure out of a release: its file has its receipt, its step reads the
# file, and core names it as it is built.
WAITS_ON: tuple[str, ...] = ()
# What the product shows beside the figure.
BY_POST = (
    "The list does not say which pharmacies serve by post alone and take no callers, so such a "
    "pharmacy is counted as any other, and the figure may read nearer than the nearest counter."
)
NOT_WHEN_OPEN = (
    "Nothing here says when a pharmacy is open, what it stocks, or whether it is on the list "
    "still: the list is made once a quarter."
)
CANNOT_SEE = (*nearest_by_postcode.OF_EVERY_MEASURE, BY_POST, NOT_WHEN_OPEN)


@dataclass(frozen=True)
class Listed:
    """What the list holds, as counts, and the postcode of each contractor that counts."""

    file_id: str
    # Every row of the file.
    rows: int
    # The rows by their type of contract, in small letters.
    by_type: Mapping[str, int]
    # The postcode of each contractor that counts, as the file writes it. It stays inside the
    # build: what is printed of the list is counts.
    postcodes: tuple[str, ...]

    def __repr__(self) -> str:
        """Counts alone, so that a line that prints the list prints no postcode."""
        return f"Listed(rows={self.rows}, counted={len(self.postcodes)})"


@dataclass(frozen=True)
class Walk:
    """The distance to the nearest pharmacy for every area, with what stands behind it."""

    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    files: tuple[Receipt, ...]
    geography: Geography
    metric: Metric
    listed: Listed
    placing: Placing
    distances: Distances


def is_the_list(name: str) -> bool:
    """Whether a publisher's name for a file is the name of a file this measure reads."""
    return FILE.fullmatch(name) is not None


def _not_as_described(opened: Opened, words: str) -> LockError:
    return LockError("input_is_as_described", opened.file_id, words)


def read(opened: Opened) -> Listed:
    """The list: what it holds as counts, and the postcode of each contractor that counts.

    It stops at a file that lacks a column that is read, and at a type of
    contract that is none of the three the publisher's page names. What it
    says of a refusal repeats nothing the file holds.
    """
    by_type: Counter[str] = Counter()
    counted: list[str] = []
    with opened.text() as text:
        for row in opened.rows(text, READ):
            kind = row[CONTRACT].strip().casefold()
            if kind not in COUNTS:
                raise _not_as_described(opened, "a type of contract is not one the page names")
            by_type[kind] += 1
            if COUNTS[kind]:
                counted.append(row[POSTCODE])
    if not by_type:
        raise _not_as_described(opened, "it holds no row")
    return Listed(
        file_id=opened.file_id,
        rows=sum(by_type.values()),
        by_type=dict(sorted(by_type.items())),
        postcodes=tuple(sorted(counted)),
    )


def definition_of(first: str, last: str) -> str:
    """The sentence a methods page prints for the measure, of a list of some period.

    A list of a quarter says its period and no day: nothing says what day
    within it the list is as at.
    """
    when = f"as at {first}" if first == last else f"for the period from {first} to {last}"
    return DEFINITION.format(
        list=LIST,
        publisher=PUBLISHER,
        when=when,
        directory="ONS Postcode Directory",
        census=nearest_by_postcode.CENSUS,
        nearest=nearest_by_postcode.NEAREST,
    )


def metric_of(files: Sequence[Receipt], first: str, last: str) -> Metric:
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
        vintage=first if first == last else f"{first} to {last}",
        rankable=True,
        definition=definition_of(first, last),
    )


def build(
    inputs: Inputs, found: Spine, *, edition: str | None = None, directory: str | None = None
) -> Walk:
    """The distance to the nearest pharmacy for every area, and its evidence.

    The gate is asked about the list, the directory and the centres before any
    is read. `found` is the spine of the same build. `edition` is the edition
    of the list, and `directory` that of the postcode directory, where a build
    holds more than one of either.
    """
    opened = inputs.open(SOURCE, USE, edition=edition, named=is_the_list)
    listed = read(opened)
    made = nearest_by_postcode.build(
        inputs, found, opened, listed.postcodes, FEATURE, directory=directory
    )
    first, last = opened.receipt.data_period.days()
    return Walk(
        worked=made.worked,
        rows=made.rows,
        files=made.files,
        geography=made.geography,
        metric=metric_of(made.files, first, last),
        listed=listed,
        placing=made.placing,
        distances=made,
    )


def credits_of(walk: Walk) -> tuple[str, ...]:
    """The three credits of the postcode directory, which stand wherever the figure does."""
    (directory,) = [receipt for receipt in walk.files if receipt.source_id == postcodes.SOURCE]
    return postcodes.credits_of(directory)
