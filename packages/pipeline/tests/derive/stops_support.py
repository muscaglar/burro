"""What the tests of the nearest station share: made-up stops, in a file like the publisher's.

Nothing here is real. The stops stand on the made-up town of the tests of
cells, which is drawn in squares of 100 metres in the North Sea. Every name of
a station is one the synthetic release already holds, with the closing words
the publisher's file writes. The file has the publisher's 43 columns, in the
publisher's order, with no mark at its start and lines that end LF.

    columns  0    1    2    3    4    5        7
    row 2                            T
    row 1  | a1 | a2 | b1 | b2 | c1 | c2 |   | z1 |    z1 is land outside London
    row 0  | a3 | a4 | b3 | b4 | c3 | c4 |

    Pellam Cross Station   a railway station, with a way in at the middle of a1 and of a3,
                           and a third at the middle of a2 that is not active
    Tallowgate             an underground station, with one way in between b2 and b4
    Sable Reach Tram Stop  T: a tram stop, 100 metres north of the middle of c2
    A pier                 at the middle of b3. It is no station
    A stop of a bus        at the middle of a4, and a bay at the middle of c4. Neither is one

Every column that no step reads holds `CANARY`, a string found nowhere else.
"""

import csv
import hashlib
import io
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from burro_pipeline.derive import stops_file
from burro_pipeline.evidence.receipt import How, Period, Receipt
from burro_pipeline.evidence.record import file_id_of
from burro_pipeline.fetch.store import FolderStore
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import EAST, FILES, LONDON, NORTH, contents, receipt_of, registry
from .green_support import centres_in_the_middle

# A string found nowhere else. It stands in every column that is never read.
CANARY = "Zzyzx Parva"
NAME = "490Stops.csv"
EDITION, SAVED = "saved 2026-09-24", "2026-09-24"
OAS = tuple(unit.oa for unit in LONDON)
QUILLHAVEN_1, QUILLHAVEN_2, TALLOWGATE = "lon-ne02999001", "lon-ne02999002", "lon-ne02999003"
AREAS = (QUILLHAVEN_1, QUILLHAVEN_2, TALLOWGATE)
# The columns of the publisher's file, in its order.
COLUMNS = (
    "ATCOCode",
    "NaptanCode",
    "PlateCode",
    "CleardownCode",
    "CommonName",
    "CommonNameLang",
    "ShortCommonName",
    "ShortCommonNameLang",
    "Landmark",
    "LandmarkLang",
    "Street",
    "StreetLang",
    "Crossing",
    "CrossingLang",
    "Indicator",
    "IndicatorLang",
    "Bearing",
    "NptgLocalityCode",
    "LocalityName",
    "ParentLocalityName",
    "GrandParentLocalityName",
    "Town",
    "TownLang",
    "Suburb",
    "SuburbLang",
    "LocalityCentre",
    "GridType",
    "Easting",
    "Northing",
    "Longitude",
    "Latitude",
    "StopType",
    "BusStopType",
    "TimingStatus",
    "DefaultWaitTime",
    "Notes",
    "NotesLang",
    "AdministrativeAreaCode",
    "CreationDateTime",
    "ModificationDateTime",
    "RevisionNumber",
    "Modification",
    "Status",
)

Point = tuple[float, float]


def at(east: float, north: float) -> Point:
    """A point on the grid of the town, in metres from its corner."""
    return float(EAST + east), float(NORTH + north)


@dataclass(frozen=True)
class MadeUpStop:
    code: str
    name: str
    type: str
    point: tuple[object, object]
    status: str = "active"
    grid: str = "UKOS"


PELLAM, TALLOW, SABLE = "Pellam Cross Station", "Tallowgate", "Sable Reach Tram Stop"
WAY_1 = MadeUpStop("4900PELLAMX1", PELLAM, "RSE", at(50, 150))
WAY_2 = MadeUpStop("4900PELLAMX2", PELLAM, "RSE", at(50, 50))
# It would put the homes of a2 at its door, if a row that is not active counted.
SHUT = MadeUpStop("4900PELLAMX3", PELLAM, "RSE", at(150, 150), status="inactive")
UNDER = MadeUpStop("4900ZZLUTLG1", TALLOW, "TMU", at(350, 100))
TRAM = MadeUpStop("4900ZZCRSBR1", SABLE, "TMU", at(550, 250))
PIER = MadeUpStop("4900SBR0", "Sable Reach Pier", "FTD", at(250, 50))
BUS = MadeUpStop("490000001A", "Coracle Row", "BCT", at(150, 50))
BAY = MadeUpStop("490000002B", "Lantern Yard", "BCS", at(550, 50))
STOPS = (WAY_1, WAY_2, SHUT, UNDER, TRAM, PIER, BUS, BAY)


def stops_csv(stops: Sequence[MadeUpStop] = STOPS, columns: Sequence[str] = COLUMNS) -> bytes:
    """The file of stops, as the publisher writes it, with a canary in all that is never read."""
    text = io.StringIO(newline="")
    table = csv.DictWriter(text, columns, extrasaction="ignore", lineterminator="\n")
    table.writeheader()
    for stop in stops:
        east, north = stop.point
        table.writerow(
            dict.fromkeys(COLUMNS, CANARY)
            | {
                "ATCOCode": stop.code,
                "CommonName": stop.name,
                "GridType": stop.grid,
                "Easting": f"{east:.0f}" if isinstance(east, float) else east,
                "Northing": f"{north:.0f}" if isinstance(north, float) else north,
                "StopType": stop.type,
                "Status": stop.status,
            }
        )
    return text.getvalue().encode()


def stops_receipt(content: bytes, name: str = NAME, edition: str = EDITION) -> Receipt:
    """The receipt of a made-up file of stops, as `by-hand` writes one."""
    sha256 = hashlib.sha256(content).hexdigest()
    return Receipt(
        file_id=file_id_of(sha256),
        source_id=stops_file.SOURCE,
        use=Use.SCORING,
        publisher_file=name,
        url=f"https://files.made-up.example/{sha256[:8]}",
        sha256=sha256,
        bytes=len(content),
        retrieved_at="2026-09-24T00:00:00Z",
        how=How.BY_HAND,
        edition=edition,
        data_period=Period(as_at=SAVED),
    )


def inputs_of(
    folder: Path,
    stops: bytes | None = None,
    *,
    ground: Mapping[str, bytes] | None = None,
    given: Registry | None = None,
    name: str = NAME,
) -> Inputs:
    """The made-up files of a build in a store of their own, with a receipt for each.

    `ground` changes a file of the geography: the lookup, the outlines or the
    centres, by the name the tests of cells give it.
    """
    files = contents() | {"centres": centres_in_the_middle()} | dict(ground or {})
    every = [
        (
            receipt_of(FILES[which][0], FILES[which][1], FILES[which][2], content, FILES[which][3]),
            content,
        )
        for which, content in files.items()
    ]
    held = stops_csv() if stops is None else stops
    every.append((stops_receipt(held, name), held))
    store = FolderStore(folder / "store")
    for receipt, content in every:
        path = folder / "given" / receipt.file_id / receipt.publisher_file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        store.put(receipt.source_id, receipt.publisher_file, path)
    return Inputs(given or registry(), [receipt for receipt, _ in every], store, folder / "work")
