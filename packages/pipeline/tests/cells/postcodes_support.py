"""What the tests of the postcode lookup share: a made-up directory, laid out as the publisher's.

Nothing here is real. The postcodes stand on the made-up town of the tests of
cells, which is drawn in squares of 100 metres in the North Sea.

**No postcode here is a postcode.** Each is made up twice over, so that none
can be one that Royal Mail has given out:

- Its area begins with `Q`. The zip of August 2026 holds the file of 124
  postcode areas, and the name of none begins with `Q`: a test on the real file
  holds that.
- Its last two letters are from `C`, `I`, `K`, `M`, `O` and `V`. No row of
  London in the directory of August 2026 ends in a letter of those six: a test
  on the real file holds that too. The rows of Northern Ireland here begin
  `BT`, as they must to be dropped, and end the same way.

The zip is laid out as the publisher's: the whole directory under `Data/`,
once as a CSV and once as text, the file of each postcode area under
`Data/multi_csv/`, and a guide. Each table has the 55 columns of August 2026,
in their order. A column that is never read holds `CANARY`, so that a test can
see that nothing of it is kept.

    columns  0    1    2    3    4    5        7
    row 1  | a1 | a2 | b1 | b2 | c1 | c2 |   | z1 |     each square is one output area
    row 0  | a3 | a4 | b3 | b4 | c3 | c4 |
             Quillhaven 001  002   Tallowgate 001   outside London

    NORTH_GATE    in a1, at (50, 150): the very middle of the square
    MILL_ROW      in b1, at (250, 150)
    QUAY          in c4, at (550, 50)
    ENDED         in a4, at (150, 50). It ended in March 2019
    LONG_ENDED    in a2, at (130, 150). It ended in June 1999, and its point is of mark 8
    A_BOX         in b4, at (350, 50). Its point is the middle of its sector, mark 6
    OUTSIDE       in z1, outside London
    NO_POINT      has no point, and so no authority
"""

import csv
import hashlib
import io
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from burro_pipeline.cells import postcodes
from burro_pipeline.evidence.receipt import How, Period, Receipt
from burro_pipeline.evidence.record import file_id_of
from burro_pipeline.fetch.store import FolderStore
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from .support import (
    EAST,
    FILES,
    NORTH,
    SIDE,
    TOWN,
    MadeUp,
    contents,
    receipt_of,
    registry,
    zip_of,
)

# A string found nowhere else. It stands in every column that is never read.
CANARY = "Zzyzx Parva"
EDITION, PERIOD = "August 2026", "2026-08"
NAME = "ONSPD_AUG_2026.zip"
STEM = "ONSPD_AUG_2026_UK"
# The letters a made-up postcode ends in. No postcode that is in use ends in one of them.
NEVER_LAST = "CIKMOV"


@dataclass(frozen=True)
class MadeUpPostcode:
    """One made-up row of the directory."""

    postcode: str
    # Where it stands, in metres from the corner of the town. None is a row with no point.
    at: tuple[int, int] | None
    quality: int = 1
    # The month it ended, as the directory writes one, or nothing while it is in use.
    ended: str = ""
    # The file it is written in, where that is not the file of its own area.
    file: str | None = None

    @property
    def area(self) -> str:
        return self.file or "".join(letter for letter in self.postcode[:2] if letter.isalpha())


NORTH_GATE = MadeUpPostcode("QH1 1CK", (50, 150))
MILL_ROW = MadeUpPostcode("QH2 1CK", (250, 150))
QUAY = MadeUpPostcode("QT1 1CK", (550, 50))
ENDED = MadeUpPostcode("QH1 9CK", (150, 50), ended="201903")
LONG_ENDED = MadeUpPostcode("QH1 8CK", (130, 150), quality=8, ended="199906")
A_BOX = MadeUpPostcode("QH9 9CK", (350, 50), quality=6)
OUTSIDE = MadeUpPostcode("QZ1 1CK", (750, 150))
NO_POINT = MadeUpPostcode("QH3 1CK", None, quality=9)
# Two rows of Northern Ireland, each written as a row of London so that a reader that kept
# either would show it: one in the file of its own area, and one in the file of another.
IN_ITS_OWN_FILE = MadeUpPostcode("BT1 1CK", (50, 50))
IN_ANOTHER_FILE = MadeUpPostcode("BT2 1CK", (450, 150), file="QT")
OF_LONDON = (NORTH_GATE, MILL_ROW, QUAY, ENDED, LONG_ENDED, A_BOX)
OF_NORTHERN_IRELAND = (IN_ITS_OWN_FILE, IN_ANOTHER_FILE)
DIRECTORY = (*OF_LONDON, OUTSIDE, NO_POINT, *OF_NORTHERN_IRELAND)


def unit_at(at: tuple[int, int]) -> MadeUp:
    """The made-up output area a point stands in."""
    square = (at[0] // SIDE, at[1] // SIDE)
    (found,) = [unit for unit in TOWN if square in unit.squares]
    return found


def point_of(row: MadeUpPostcode) -> tuple[float, float]:
    """Where a made-up postcode stands on the National Grid."""
    assert row.at is not None
    return float(EAST + row.at[0]), float(NORTH + row.at[1])


def _cells(row: MadeUpPostcode) -> dict[str, str]:
    """One row of the table: what is read as it would be written, and a canary in the rest."""
    found: dict[str, str] = dict.fromkeys(postcodes.HELD, CANARY)
    outward, inward = row.postcode.split(" ")
    found |= {
        "pcd7": f"{outward:<4}{inward}",
        "pcd8": f"{outward:<4} {inward}",
        postcodes.POSTCODE: row.postcode,
        "dointr": "198001",
        postcodes.ENDED: row.ended,
        "usrtypind": "0",
        postcodes.QUALITY_MARK: str(row.quality),
    }
    if row.at is None:
        # The directory gives a postcode with no point no authority and no area.
        return found | dict.fromkeys(
            (
                postcodes.AUTHORITY,
                postcodes.EASTING,
                postcodes.NORTHING,
                postcodes.OA,
                postcodes.LSOA,
                postcodes.MSOA,
            ),
            "",
        )
    unit = unit_at(row.at)
    return found | {
        postcodes.AUTHORITY: unit.borough,
        postcodes.EASTING: str(EAST + row.at[0]),
        postcodes.NORTHING: str(NORTH + row.at[1]),
        postcodes.OA: unit.oa,
        postcodes.LSOA: unit.lsoa,
        postcodes.MSOA: unit.msoa,
    }


def table(rows: Sequence[Mapping[str, str]], columns: Sequence[str] = postcodes.HELD) -> str:
    """A table as the directory writes one: the names of the columns, and a row to a line."""
    text = io.StringIO(newline="")
    written = csv.DictWriter(text, columns, extrasaction="ignore", lineterminator="\r\n")
    written.writeheader()
    written.writerows(rows)
    return text.getvalue()


def members_of(
    directory: Sequence[MadeUpPostcode] = DIRECTORY,
    *,
    columns: Sequence[str] = postcodes.HELD,
    changed: Mapping[str, Mapping[str, str]] | None = None,
) -> dict[str, str | bytes]:
    """The members of the zip. `changed` writes other values in the row of a postcode."""
    other = changed or {}
    rows = {row.postcode: _cells(row) | dict(other.get(row.postcode, {})) for row in directory}
    areas = sorted({row.area for row in directory})
    whole = table([rows[row.postcode] for row in directory], columns)
    found: dict[str, str | bytes] = {
        f"Data/{STEM}.csv": whole,
        f"Data/{STEM}.txt": whole,
    }
    for area in areas:
        of_area = [rows[row.postcode] for row in directory if row.area == area]
        found[f"Data/multi_csv/{STEM}_{area}.csv"] = table(of_area, columns)
    found["Documents/Made up names and codes.csv"] = f"{CANARY}\r\n"
    found["User Guide/Made up guide.odt"] = b"Made up for a test.\n"
    return found


def directory_zip(
    directory: Sequence[MadeUpPostcode] = DIRECTORY,
    *,
    columns: Sequence[str] = postcodes.HELD,
    changed: Mapping[str, Mapping[str, str]] | None = None,
) -> bytes:
    """The zip of the directory, as the publisher lays it out. What it holds is made up."""
    return zip_of(members_of(directory, columns=columns, changed=changed))


def directory_receipt(content: bytes, *, name: str = NAME, edition: str = EDITION) -> Receipt:
    sha256 = hashlib.sha256(content).hexdigest()
    return Receipt(
        file_id=file_id_of(sha256),
        source_id=postcodes.SOURCE,
        use=Use.CELLS,
        publisher_file=name,
        url=f"https://files.made-up.example/{sha256[:8]}",
        sha256=sha256,
        bytes=len(content),
        retrieved_at="2026-09-24T00:00:00Z",
        how=How.BY_HAND,
        edition=edition,
        data_period=Period(as_at=PERIOD),
    )


def stored(folder: Path, every: Sequence[tuple[Receipt, bytes]], given: Registry | None) -> Inputs:
    """Some made-up files in a store of their own, with a receipt for each."""
    store = FolderStore(folder / "store")
    for receipt, content in every:
        path = folder / "given" / receipt.file_id / receipt.publisher_file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        store.put(receipt.source_id, receipt.publisher_file, path)
    return Inputs(given or registry(), [receipt for receipt, _ in every], store, folder / "work")


def of_the_town(centres: bytes | None = None) -> list[tuple[Receipt, bytes]]:
    """The files of the made-up town, each with its receipt."""
    files = contents() | ({} if centres is None else {"centres": centres})
    return [
        (
            receipt_of(FILES[which][0], FILES[which][1], FILES[which][2], content, FILES[which][3]),
            content,
        )
        for which, content in files.items()
    ]


def inputs_of(
    folder: Path,
    directory: bytes | None = None,
    *,
    given: Registry | None = None,
    name: str = NAME,
) -> Inputs:
    """The made-up town and the made-up directory in a store of their own."""
    content = directory_zip() if directory is None else directory
    every = [*of_the_town(), (directory_receipt(content, name=name), content)]
    return stored(folder, every, given)


def opened_of(folder: Path, directory: bytes | None = None, *, name: str = NAME) -> Opened:
    """The made-up directory, handed over as a step of a build is handed it."""
    return inputs_of(folder, directory, name=name).open(postcodes.SOURCE, postcodes.USE)
