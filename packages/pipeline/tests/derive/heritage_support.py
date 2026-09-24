"""What the tests of the heritage measures share: made-up records, in files as the platform's.

Nothing here is real. The records stand on the made-up town of the tests of
cells, which is drawn in squares of 100 metres in the North Sea:

    columns  0    1    2    3    4    5        7
    row 1  | a1 | a2 | b1 | b2 | c1 | c2 |   | z1 |
    row 0  | a3 | a4 | b3 | b4 | c3 | c4 |
             Quillhaven 001  002   Tallowgate 001   outside London

Two output areas side by side are one LSOA of 2 hectares, and an area is two
LSOAs, one above the other. The last LSOA of Tallowgate has an island of 1
hectare more.

A file is a collection of features in GeoJSON, as the planning data platform
writes one: a line for each feature, every property as text, and where a
record is in longitude and latitude to six decimal places. That is about a
tenth of a metre, so a made-up outline is not drawn to the millimetre, and a
test that holds a share of land holds it to the figure as it is given.

    Old Quarter   all of a1 and a2, and out to sea: 2 hectares of Quillhaven 001
    The Copy      Old Quarter again, 10 metres short, as the ministry recorded it
    Inner Court   a quarter of a hectare inside Old Quarter
    Wharf         half of b3: half a hectare of Quillhaven 002
    Long Gone     b1 and b2, ended in 2020
    Marker        a point in b4, and no outline
    Over The Way  z1, outside London
    Far Off       50 kilometres to the north
"""

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from burro_pipeline.cells.shapes import longitude_and_latitude
from burro_pipeline.evidence.receipt import EditionFrom, How, Period, Receipt, Where
from burro_pipeline.evidence.record import file_id_of
from burro_pipeline.fetch.store import FolderStore
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import EAST, FILES, NORTH, contents, receipt_of, registry

# A string found nowhere else. It stands where the name of a record does, which is never read.
CANARY = "Zzyzx Parva"
# The day the made-up files are of, and the day they were retrieved.
DAY = "2026-09-24"
QUILLHAVEN, TALLOWGATE = "E09000901", "E09000902"
QUILLHAVEN_1, QUILLHAVEN_2, TALLOWGATE_1 = "lon-ne02999001", "lon-ne02999002", "lon-ne02999003"
# The platform's numbers for who provided a record. None is a number it has given out.
OF_QUILLHAVEN, OF_TALLOWGATE, THE_MINISTRY, THE_LIST = "90001", "90002", "1", "16"
AUTHORITATIVE, SOME = "authoritative", "some"

Geometry = dict[str, Any]


def at(east: float, north: float) -> list[float]:
    """A point of the town as a file writes it, in metres from the town's corner."""
    return list(longitude_and_latitude(EAST + east, NORTH + north))


def point(east: float, north: float) -> Geometry:
    return {"type": "Point", "coordinates": at(east, north)}


def ring(west: float, south: float, wide: float, high: float) -> list[list[float]]:
    """A ring round a box, by its corner nearest the town's."""
    corners = (
        (west, south),
        (west + wide, south),
        (west + wide, south + high),
        (west, south + high),
        (west, south),
    )
    return [at(east, north) for east, north in corners]


def outline(west: float, south: float, wide: float, high: float) -> Geometry:
    """A box as an outline in one piece."""
    return {"type": "Polygon", "coordinates": [ring(west, south, wide, high)]}


def outlines(*boxes: tuple[float, float, float, float]) -> Geometry:
    """Several boxes as one outline in several pieces."""
    return {"type": "MultiPolygon", "coordinates": [[ring(*box)] for box in boxes]}


@dataclass(frozen=True)
class MadeUp:
    """One made-up record of a dataset."""

    entity: str
    where: Geometry | None
    provider: str = OF_QUILLHAVEN
    quality: str = AUTHORITATIVE
    ended: str = ""
    entered: str = "2024-05-01"
    grade: str | None = None
    # Properties to leave out, and properties to write as they stand, whatever they are.
    without: tuple[str, ...] = ()
    instead: Mapping[str, Any] | None = None


def feature(dataset: str, record: MadeUp) -> dict[str, Any]:
    """A record as the platform writes one: every property as text."""
    properties: dict[str, Any] = {
        "dataset": dataset,
        "end-date": record.ended,
        "entity": record.entity,
        "entry-date": record.entered,
        "name": CANARY,
        "organisation-entity": record.provider,
        "prefix": dataset,
        "quality": record.quality,
        "reference": f"MADE-UP-{record.entity}",
        "start-date": "1990-01-01",
        "typology": "geography",
        "documentation-url": f"https://made-up.example/{record.entity}",
        "notes": CANARY,
    }
    if record.grade is not None:
        properties["listed-building-grade"] = record.grade
    properties |= dict(record.instead or {})
    for name in record.without:
        del properties[name]
    return {"type": "Feature", "properties": properties, "geometry": record.where}


def collection(
    dataset: str,
    records: Sequence[MadeUp],
    *,
    layout: str = "lines",
    named: str | None = None,
) -> bytes:
    """A file of a dataset. What it holds is made up.

    `layout` is how the file breaks its lines: `lines` is the platform's own,
    a line for each feature. `one` writes the whole file on one line, and
    `spread` writes every value on a line of its own.
    """
    features = [feature(dataset, record) for record in records]
    name = dataset if named is None else named
    if layout == "lines":
        rows = ",\n".join(json.dumps(one, ensure_ascii=False) for one in features)
        written = (
            f'{{\n"type": "FeatureCollection",\n"name": {json.dumps(name)},\n'
            f'"features": [\n{rows}\n]\n}}\n'
        )
    else:
        whole = {"type": "FeatureCollection", "name": name, "features": features}
        written = json.dumps(whole, indent=None if layout == "one" else 2)
    return written.encode()


OLD_QUARTER = MadeUp("44000001", outline(-20, 100, 220, 120))
THE_COPY = MadeUp(
    "44000002",
    outline(-20, 100, 210, 120),
    provider=THE_MINISTRY,
    quality=SOME,
    entered="2025-06-01",
)
INNER_COURT = MadeUp("44000003", outline(50, 120, 50, 50))
WHARF = MadeUp("44000004", outline(200, -20, 100, 70))
LONG_GONE = MadeUp("44000005", outline(200, 100, 200, 100), ended="2020-01-01")
MARKER = MadeUp("44000006", point(350, 50))
OVER_THE_WAY = MadeUp("44000007", outline(700, 100, 100, 100))
FAR_OFF = MadeUp("44000008", outline(0, 50_000, 100, 100))
AREAS = (OLD_QUARTER, THE_COPY, INNER_COURT, WHARF, LONG_GONE, MARKER, OVER_THE_WAY, FAR_OFF)
# One conservation area of Tallowgate: all of c2, and out to sea. 1 hectare of Tallowgate 001.
QUAYSIDE = MadeUp("44000009", outline(500, 100, 120, 120), provider=OF_TALLOWGATE)

# Listed buildings. Three in the first LSOA of Quillhaven 001, one in Quillhaven 002, one that
# ended, one in the sea, one outside London and one far off. None in Tallowgate.
ENTRIES = (
    MadeUp("31000001", point(50, 150), provider=THE_LIST, grade="I"),
    MadeUp("31000002", point(60, 150), provider=THE_LIST, grade="II*"),
    MadeUp("31000003", point(150, 190), provider=THE_LIST, grade="II"),
    MadeUp("31000004", point(250, 50), provider=THE_LIST, grade="II"),
    MadeUp(
        "31000005",
        outlines((210, 110, 10, 10), (230, 110, 10, 10)),
        provider=THE_LIST,
        ended="2026-09-23",
    ),
    MadeUp("31000006", point(100, 250), provider=THE_LIST, grade="II"),
    MadeUp("31000007", point(750, 150), provider=THE_LIST, grade="II"),
    MadeUp("31000008", point(0, 50_000), provider=THE_LIST, grade="II"),
)
# One entry of Tallowgate, on its island.
ON_THE_ISLAND = MadeUp("31000009", point(550, -150), provider=THE_LIST, grade="II")

# Each made-up file: its source, the publisher's name for it, and the dataset it holds. The
# tests of each measure hold these to what the measure reads.
CONSERVATION = (
    "mhclg-planning-data-conservation-areas",
    "conservation-area.geojson",
    "conservation-area",
)
LISTED = ("historic-england-listed-buildings", "listed-building.geojson", "listed-building")


def areas_file(records: Sequence[MadeUp] = AREAS, **how: Any) -> bytes:
    return collection(CONSERVATION[2], records, **how)


def entries_file(records: Sequence[MadeUp] = ENTRIES, **how: Any) -> bytes:
    return collection(LISTED[2], records, **how)


def heritage_receipt(source_id: str, name: str, content: bytes, *, day: str = DAY) -> Receipt:
    """The receipt of a made-up file, dated by the day it was retrieved as the real ones are."""
    sha256 = hashlib.sha256(content).hexdigest()
    return Receipt(
        file_id=file_id_of(sha256),
        source_id=source_id,
        use=Use.SCORING,
        publisher_file=name,
        url=f"https://files.made-up.example/{sha256[:8]}",
        sha256=sha256,
        bytes=len(content),
        retrieved_at=f"{day}T08:55:00Z",
        how=How.FETCHED,
        edition=f"retrieved {day}",
        edition_from=EditionFrom(where=Where.RETRIEVED, at="", period_too=True),
        data_period=Period(as_at=day),
    )


def inputs_of(
    folder: Path,
    *,
    areas: bytes | None = None,
    entries: bytes | None = None,
    given: Registry | None = None,
    day: str = DAY,
) -> Inputs:
    """The made-up files of a build in a store of their own, with a receipt for each."""
    every = [
        (
            receipt_of(FILES[which][0], FILES[which][1], FILES[which][2], content, FILES[which][3]),
            content,
        )
        for which, content in contents().items()
    ]
    every.append(_with_receipt(CONSERVATION, areas_file() if areas is None else areas, day))
    every.append(_with_receipt(LISTED, entries_file() if entries is None else entries, day))
    store = FolderStore(folder / "store")
    for receipt, content in every:
        path = folder / "given" / receipt.file_id / receipt.publisher_file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        store.put(receipt.source_id, receipt.publisher_file, path)
    return Inputs(given or registry(), [receipt for receipt, _ in every], store, folder / "work")


def _with_receipt(which: tuple[str, str, str], content: bytes, day: str) -> tuple[Receipt, bytes]:
    return heritage_receipt(which[0], which[1], content, day=day), content


def opened_of(folder: Path, which: tuple[str, str, str], content: bytes) -> Opened:
    """One made-up file, handed over as a step of a build is handed one."""
    receipt = heritage_receipt(which[0], which[1], content)
    path = folder / "given" / receipt.publisher_file
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    store = FolderStore(folder / "store")
    store.put(receipt.source_id, receipt.publisher_file, path)
    inputs = Inputs(registry(), [receipt], store, folder / "work")
    return inputs.open(which[0], Use.SCORING)
