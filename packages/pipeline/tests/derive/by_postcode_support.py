"""What the tests of the two walks share: a made-up report and a made-up list, as the publishers'.

Nothing here is real. The places stand on the made-up town of the tests of
cells, at the made-up postcodes of `tests/cells/postcodes_support.py`. No
postcode here is one that has been given out, and no name is a name.

    columns  0    1    2    3    4    5        7
    row 1  | a1 | a2 | b1 | b2 | c1 | c2 |   | z1 |     each square is one output area
    row 0  | a3 | a4 | b3 | b4 | c3 | c4 |
             Quillhaven 001  002   Tallowgate 001   outside London

The centre of each output area is put in the very middle of its square, so
each distance can be worked out by hand. The output area outside London has a
centre too, at (750, 150): a home there may be nearer than a place in London.

Two places count and are placed: one at NORTH_GATE, in the middle of a1, and
one at QUAY, in the middle of c4.

    Quillhaven 001   homes 110, 120, 130, 140   at 0, 100, 100 and 141 metres
    Quillhaven 002   homes 150, 160, 170, 180   at 200, 224, 224 and 200
    Tallowgate 001   homes 190, 200, 210, 220   at 141, 100, 100 and 0

The report of practices is laid out as the publisher's specification says,
and as the first real file was found to be: 27 columns, no row of names, a
status in capitals, and in a few lines two prescribing settings in one cell
with a bar between them. The list of pharmacies has the 25 fields the
publisher's page names, under a row of names. A column that is never read
holds `CANARY`.
"""

import csv
import hashlib
import io
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from burro_pipeline.derive import gp_walk, pharmacy_walk
from burro_pipeline.evidence.receipt import How, Period, Receipt
from burro_pipeline.evidence.record import file_id_of
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.postcodes_support import (
    A_BOX,
    ENDED,
    LONG_ENDED,
    MILL_ROW,
    NORTH_GATE,
    OUTSIDE,
    QUAY,
    directory_receipt,
    directory_zip,
    of_the_town,
    stored,
)
from ..cells.support import CENTRES_COLUMNS, EAST, NORTH, SIDE, TOWN

# A string found nowhere else. It stands in every column that is never read.
CANARY = "Zzyzx Parva"
QUILLHAVEN_1, QUILLHAVEN_2, TALLOWGATE = "lon-ne02999001", "lon-ne02999002", "lon-ne02999003"
AREAS = (QUILLHAVEN_1, QUILLHAVEN_2, TALLOWGATE)
RETRIEVED = "2026-09-24"
QUARTER = "2026-27 Quarter 1"
LIST_NAME = "consol_pharmacy_list_202606q1.csv"
# Text that has not the shape of a postcode.
NO_POSTCODE = "not known"


@dataclass(frozen=True)
class MadeUpPractice:
    """One made-up row of the report of practices."""

    postcode: str
    status: str = "ACTIVE"
    setting: str = gp_walk.GP_PRACTICE
    closed: str = ""


@dataclass(frozen=True)
class MadeUpContractor:
    """One made-up row of the list of pharmacies."""

    postcode: str
    contract: str = "Community"


PRACTICES = (
    MadeUpPractice(NORTH_GATE.postcode),
    MadeUpPractice(QUAY.postcode),
    # None of these counts: each stands where it would change every figure if it did.
    MadeUpPractice(MILL_ROW.postcode, status="CLOSED", closed="20190331"),
    MadeUpPractice(MILL_ROW.postcode, status="DORMANT"),
    MadeUpPractice(MILL_ROW.postcode, status="PROPOSED"),
    MadeUpPractice(MILL_ROW.postcode, closed="20261231"),
    MadeUpPractice(MILL_ROW.postcode, setting="RO80"),
    MadeUpPractice(MILL_ROW.postcode, setting=""),
    # As the first real file writes a practice that has closed, and one of two settings.
    MadeUpPractice(MILL_ROW.postcode, status="INACTIVE", closed="20190331"),
    MadeUpPractice(MILL_ROW.postcode, setting="RO80|RO87"),
    # These count, and are placed nowhere.
    MadeUpPractice(OUTSIDE.postcode),
    MadeUpPractice(A_BOX.postcode),
    MadeUpPractice(NO_POSTCODE),
)
CONTRACTORS = (
    MadeUpContractor(NORTH_GATE.postcode),
    MadeUpContractor(QUAY.postcode, contract="LPS"),
    # An appliance contractor does not count.
    MadeUpContractor(MILL_ROW.postcode, contract="DAC"),
    # These count, and are placed nowhere.
    MadeUpContractor(OUTSIDE.postcode),
    MadeUpContractor(A_BOX.postcode),
    MadeUpContractor(NO_POSTCODE),
)
# A place at a postcode that has ended, and one at a postcode that ended before November 2000.
AT_AN_ENDED_POSTCODE, AT_A_LONG_ENDED_POSTCODE = ENDED.postcode, LONG_ENDED.postcode


def report(practices: Sequence[MadeUpPractice] = PRACTICES, *, width: int = gp_walk.WIDTH) -> bytes:
    """The report of practices, as the publisher's specification lays it out."""
    text = io.StringIO(newline="")
    table = csv.writer(text, quoting=csv.QUOTE_ALL, lineterminator="\r\n")
    for number, practice in enumerate(practices, start=1):
        line = [CANARY] * max(width, gp_walk.SETTING)
        line[0] = f"Q{number:05d}"
        line[gp_walk.POSTCODE - 1] = practice.postcode
        line[10] = "19740401"
        line[gp_walk.CLOSED - 1] = practice.closed
        line[gp_walk.STATUS - 1] = practice.status
        line[gp_walk.SETTING - 1] = practice.setting
        table.writerow(line[:width])
    return text.getvalue().encode()


def pharmacy_list(
    contractors: Sequence[MadeUpContractor] = CONTRACTORS,
    *,
    columns: Sequence[str] = pharmacy_walk.HELD,
) -> bytes:
    """The list of pharmacies, under the names of the fields the publisher's page gives."""
    text = io.StringIO(newline="")
    table = csv.DictWriter(text, columns, extrasaction="ignore", lineterminator="\r\n")
    table.writeheader()
    for number, contractor in enumerate(contractors, start=1):
        row = dict.fromkeys(pharmacy_walk.HELD, CANARY) | {
            "PHARMACY_ODS_CODE_F_CODE": f"FQ{number:03d}",
            pharmacy_walk.POSTCODE: contractor.postcode,
            pharmacy_walk.CONTRACT: contractor.contract,
        }
        table.writerow(row)
    return text.getvalue().encode()


def centres_with_the_district(left_out: Sequence[str] = ()) -> bytes:
    """The centre of every output area of the town, in the middle of its square.

    The output area outside London has its centre too, as the publisher's
    file has one for every output area of England and Wales.
    """
    lines = [",".join(CENTRES_COLUMNS)]
    for number, unit in enumerate(TOWN, start=1):
        if unit.oa in left_out:
            continue
        column, row = unit.squares[0]
        east, north = EAST + column * SIDE + SIDE / 2, NORTH + row * SIDE + SIDE / 2
        lines.append(
            f"{east:.4f},{north:.4f},{number},{unit.oa},{{made-up-{number}}},{{made-up-{number}-2}}"
        )
    return b"\xef\xbb\xbf" + "".join(f"{line}\n" for line in lines).encode()


def _receipt(source_id: str, name: str, content: bytes, edition: str, period: Period) -> Receipt:
    sha256 = hashlib.sha256(content).hexdigest()
    return Receipt(
        file_id=file_id_of(sha256),
        source_id=source_id,
        use=Use.SCORING,
        publisher_file=name,
        url=f"https://files.made-up.example/{sha256[:8]}",
        sha256=sha256,
        bytes=len(content),
        retrieved_at=f"{RETRIEVED}T00:00:00Z",
        how=How.FETCHED,
        edition=edition,
        data_period=period,
    )


def report_receipt(content: bytes, *, name: str = gp_walk.FILE) -> Receipt:
    return _receipt(
        gp_walk.SOURCE, name, content, f"retrieved {RETRIEVED}", Period(as_at=RETRIEVED)
    )


def list_receipt(content: bytes, *, name: str = LIST_NAME) -> Receipt:
    period = Period(start="2026-04-01", end="2026-06-30")
    return _receipt(pharmacy_walk.SOURCE, name, content, QUARTER, period)


def inputs_of(
    folder: Path,
    *,
    practices: bytes | None = None,
    contractors: bytes | None = None,
    directory: bytes | None = None,
    centres: bytes | None = None,
    given: Registry | None = None,
) -> Inputs:
    """The made-up town, directory, report and list in a store of their own."""
    held = directory_zip() if directory is None else directory
    of_practices = report() if practices is None else practices
    of_contractors = pharmacy_list() if contractors is None else contractors
    every = [
        *of_the_town(centres_with_the_district() if centres is None else centres),
        (directory_receipt(held), held),
        (report_receipt(of_practices), of_practices),
        (list_receipt(of_contractors), of_contractors),
    ]
    return stored(folder, every, given)
