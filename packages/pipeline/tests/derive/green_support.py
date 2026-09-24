"""What the tests of the green measures share: made-up sites, in files laid out as the publisher's.

Nothing here is real. The sites stand on the made-up town of the tests of
cells, which is drawn in squares of 100 metres in the North Sea. The town
stands at the corner of four squares of the National Grid, none of which holds
land, so a file for each can be made up:

    TB | TC      the town is in TC, hard against its west and south sides
    ---+---      the island of Tallowgate is in TH
    TG | TH

A file is a zip laid out as the publisher's: a folder named for the product
and the square, with `doc/licence.txt`, `readme.txt` and `data/` with one
document of GML. The document has the publisher's own elements, in its own
namespaces. What it holds is made up.

    columns  0    1    2    3    4    5          10 to 14
    row 3                                       +---------+
    row 2                                       |         |
    row 1  | a1 | a2 | b1 | b2 | c1 | c2 |      |  Great  |
    row 0  | a3 | a4 | b3 | b4 | c3 | c4 |      +---------+

    Long Meadow   a park of 2 hectares, over half of a1, all of a2 and half of b1
    Walled Plot   a garden of 0.25 hectares, inside Long Meadow
    Pocket        a garden of 0.04 hectares, in c3
    Links         a golf course of 2 hectares, over b3 and b4
    Great         a park of 20 hectares, east of the town
"""

import hashlib
import io
import zipfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from burro_pipeline.derive import green_sites
from burro_pipeline.evidence.receipt import How, Period, Receipt
from burro_pipeline.evidence.record import file_id_of
from burro_pipeline.fetch.store import FolderStore
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import (
    CENTRES_COLUMNS,
    EAST,
    FILES,
    LONDON,
    NORTH,
    SIDE,
    contents,
    receipt_of,
    registry,
)

# A string found nowhere else. It stands where a site's name does, which is never read.
CANARY = "Zzyzx Parva"
EDITION = "2026-04"
# When every member of a made-up zip says it was written.
WRITTEN = (2026, 4, 1, 0, 0, 0)
SAID = "Ordnance Survey Crown Copyright 2026"
GRID = "urn:ogc:def:crs:EPSG::27700"
PARK, GOLF, PLAY = "Public Park Or Garden", "Golf Course", "Play Space"
ON_FOOT, BY_CAR, EITHER = "Pedestrian", "Motor Vehicle", "Motor Vehicle And Pedestrian"
OAS = tuple(unit.oa for unit in LONDON)
QUILLHAVEN_1, QUILLHAVEN_2, TALLOWGATE = "lon-ne02999001", "lon-ne02999002", "lon-ne02999003"

Point = tuple[float, float]
Ring = tuple[Point, ...]

ROOT = (
    '<os:FeatureCollection xmlns:gml="http://www.opengis.net/gml/3.2" '
    'xmlns:os="http://namespaces.os.uk/product/1.0" '
    'xmlns:ogsp="http://namespaces.ordnancesurvey.co.uk/Open/Greenspace/1.0" '
    'xmlns:xlink="http://www.w3.org/1999/xlink" gml:id="OSOpenGreenspace">'
)


def box(west: float, south: float, wide: float, high: float) -> Ring:
    """A ring round a box, by its corner nearest the grid's origin, on the grid of the town."""
    x, y = EAST + west, NORTH + south
    return ((x, y), (x + wide, y), (x + wide, y + high), (x, y + high), (x, y))


def at(east: float, north: float) -> Point:
    """A point on the grid of the town, in metres from its corner."""
    return EAST + east, NORTH + north


@dataclass(frozen=True)
class MadeUpSite:
    site_id: str
    kind: str | None
    # Each piece is the ring round it, and then the ring round each hole in it.
    pieces: tuple[tuple[Ring, ...], ...]
    name: str | None = CANARY
    grid: str = GRID


@dataclass(frozen=True)
class MadeUpWay:
    site_id: str | None
    access: str | None
    point: Point | None
    grid: str = GRID


LONG_MEADOW = MadeUpSite("idLONGMEADOW", PARK, ((box(50, 100, 200, 100),),))
WALLED_PLOT = MadeUpSite("idWALLEDPLOT", PARK, ((box(100, 125, 50, 50),),), name=None)
POCKET = MadeUpSite("idPOCKET", PARK, ((box(410, 10, 20, 20),),))
LINKS = MadeUpSite("idLINKS", GOLF, ((box(200, 0, 200, 100),),))
GREAT = MadeUpSite("idGREAT", PARK, ((box(1000, 0, 500, 400),),))
SITES = (LONG_MEADOW, WALLED_PLOT, POCKET, LINKS, GREAT)
WAYS_IN = (
    # Long Meadow has a gate for walkers on its west side, and one for cars alone on its east.
    MadeUpWay("idLONGMEADOW", ON_FOOT, at(50, 150)),
    MadeUpWay("idLONGMEADOW", BY_CAR, at(250, 150)),
    MadeUpWay("idPOCKET", ON_FOOT, at(410, 20)),
    MadeUpWay("idLINKS", EITHER, at(300, 100)),
    MadeUpWay("idGREAT", ON_FOOT, at(1000, 150)),
)
# One small site in each of the other three squares, far from the town, so that each has a file.
ELSEWHERE = {
    "tb": MadeUpSite("idFARWEST", PLAY, ((box(-5_000, 5_000, 10, 10),),)),
    "tg": MadeUpSite("idFARSOUTHWEST", PLAY, ((box(-5_000, -5_000, 10, 10),),)),
    "th": MadeUpSite("idFARSOUTH", PLAY, ((box(5_000, -5_000, 10, 10),),)),
}


def _ring(ring: Ring, side: str) -> str:
    points = " ".join(f"{east:.2f} {north:.2f}" for east, north in ring)
    return (
        f"<gml:{side}><gml:LinearRing><gml:posList>{points}</gml:posList>"
        f"</gml:LinearRing></gml:{side}>"
    )


def _site(site: MadeUpSite) -> str:
    pieces = "".join(
        "<gml:surfaceMember><gml:Surface><gml:patches><gml:PolygonPatch>"
        + _ring(rings[0], "exterior")
        + "".join(_ring(hole, "interior") for hole in rings[1:])
        + "</gml:PolygonPatch></gml:patches></gml:Surface></gml:surfaceMember>"
        for rings in site.pieces
    )
    kind = (
        ""
        if site.kind is None
        else '<ogsp:function codeSpace="http://www.os.uk/xml/codelists/OpenFunctionValue">'
        f"{site.kind}</ogsp:function>"
    )
    name = (
        "" if site.name is None else f"<ogsp:distinctiveName1>{site.name}</ogsp:distinctiveName1>"
    )
    outline = (
        f'<ogsp:geometry><gml:MultiSurface gml:id="{site.site_id}-0" srsName="{site.grid}" '
        f'srsDimension="2">{pieces}</gml:MultiSurface></ogsp:geometry>'
        if site.pieces
        else ""
    )
    return (
        f'<os:featureMember><ogsp:GreenspaceSite gml:id="{site.site_id}">{kind}{name}{outline}'
        "</ogsp:GreenspaceSite></os:featureMember>"
    )


def _way_in(number: int, way: MadeUpWay) -> str:
    access = (
        ""
        if way.access is None
        else '<ogsp:accessType codeSpace="http://www.os.uk/xml/codelists/AccessTypeValue">'
        f"{way.access}</ogsp:accessType>"
    )
    of_site = (
        ""
        if way.site_id is None
        else f"<ogsp:refToGreenspaceSite>{way.site_id}</ogsp:refToGreenspaceSite>"
    )
    place = (
        ""
        if way.point is None
        else f'<ogsp:geometry><gml:Point gml:id="idWAY{number}-0" srsName="{way.grid}" '
        f'srsDimension="2"><gml:pos>{way.point[0]:.2f} {way.point[1]:.2f}</gml:pos></gml:Point>'
        "</ogsp:geometry>"
    )
    return (
        f'<os:featureMember><ogsp:AccessPoint gml:id="idWAY{number}">{access}{of_site}{place}'
        "</ogsp:AccessPoint></os:featureMember>"
    )


def document(
    sites: Sequence[MadeUpSite] = SITES,
    ways_in: Sequence[MadeUpWay] = WAYS_IN,
    *,
    said: str | None = SAID,
    more: str = "",
    before: str = "",
) -> bytes:
    """A document of GML as the publisher writes one. What it holds is made up."""
    whose = "" if said is None else f"<gml:description>{said}</gml:description>"
    inside = "".join(
        [
            whose,
            f'<gml:boundedBy><gml:Envelope srsName="{GRID}" srsDimension="2">'
            "<gml:lowerCorner>0 0</gml:lowerCorner><gml:upperCorner>1 1</gml:upperCorner>"
            "</gml:Envelope></gml:boundedBy>",
            '<os:metadata xlink:href="http://www.os.uk/xml/products/GSO.xml"/>',
            # The ways in stand before the sites, as they do in the publisher's file.
            *(_way_in(number, way) for number, way in enumerate(ways_in, start=1)),
            *(_site(site) for site in sites),
            more,
        ]
    )
    written = (
        f'<?xml version="1.0" encoding="UTF-8"?>\n{before}{ROOT}{inside}</os:FeatureCollection>'
    )
    return written.encode()


def tile(letters: str, held: bytes | None = None, *, member: str | None = None) -> bytes:
    """A file of one square, as the publisher zips it: a licence, a note and the document."""
    folder = f"OS Open Greenspace (GML) {letters.upper()}"
    members = {
        f"{folder}/doc/licence.txt": b"Made up for a test.\n",
        f"{folder}/readme.txt": b"Made up for a test.\n",
        member or f"{folder}/data/OSOpenGreenspace_{letters.upper()}.gml": (
            document() if held is None else held
        ),
    }
    packed = io.BytesIO()
    with zipfile.ZipFile(packed, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in members.items():
            # A zip holds the time each member was written. It is fixed here, so that the
            # same sites are the same bytes, and so the same file, whenever a test makes them.
            archive.writestr(zipfile.ZipInfo(name, date_time=WRITTEN), content)
    return packed.getvalue()


def tiles(town: bytes | None = None) -> dict[str, bytes]:
    """A file for each of the four squares round the town. The town is in `tc`."""
    found = {letters: tile(letters, document([site], [])) for letters, site in ELSEWHERE.items()}
    return {"tc": tile("tc", town), **found}


def green_receipt(letters: str, content: bytes, *, edition: str = EDITION) -> Receipt:
    sha256 = hashlib.sha256(content).hexdigest()
    return Receipt(
        file_id=file_id_of(sha256),
        source_id=green_sites.SOURCE,
        use=Use.SCORING,
        publisher_file=f"opgrsp_gml3_{letters}.zip",
        url=f"https://files.made-up.example/{sha256[:8]}",
        sha256=sha256,
        bytes=len(content),
        retrieved_at="2026-09-23T21:51:19Z",
        how=How.FETCHED,
        edition=edition,
        data_period=Period(as_at=edition),
    )


def centres_in_the_middle(left_out: Sequence[str] = ()) -> bytes:
    """The centre of each output area of the town, in the very middle of its square."""
    lines = [",".join(CENTRES_COLUMNS)]
    for number, unit in enumerate(LONDON, start=1):
        if unit.oa in left_out:
            continue
        column, row = unit.squares[0]
        east, north = EAST + column * SIDE + SIDE / 2, NORTH + row * SIDE + SIDE / 2
        lines.append(
            f"{east:.4f},{north:.4f},{number},{unit.oa},{{made-up-{number}}},{{made-up-{number}-2}}"
        )
    return b"\xef\xbb\xbf" + "".join(f"{line}\n" for line in lines).encode()


def inputs_of(
    folder: Path,
    of_squares: Mapping[str, bytes] | None = None,
    *,
    centres: bytes | None = None,
    given: Registry | None = None,
    edition: str = EDITION,
) -> Inputs:
    """The made-up files of a build in a store of their own, with a receipt for each."""
    files = contents() | {"centres": centres_in_the_middle() if centres is None else centres}
    every = [
        (
            receipt_of(FILES[which][0], FILES[which][1], FILES[which][2], content, FILES[which][3]),
            content,
        )
        for which, content in files.items()
    ]
    squares = tiles() if of_squares is None else of_squares
    every += [
        (green_receipt(letters, content, edition=edition), content)
        for letters, content in squares.items()
    ]
    store = FolderStore(folder / "store")
    for receipt, content in every:
        path = folder / "given" / receipt.file_id / receipt.publisher_file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        store.put(receipt.source_id, receipt.publisher_file, path)
    return Inputs(given or registry(), [receipt for receipt, _ in every], store, folder / "work")


def opened_of(folder: Path, letters: str, content: bytes, *, edition: str = EDITION) -> Opened:
    """One made-up file, handed over as a step of a build is handed one."""
    receipt = green_receipt(letters, content, edition=edition)
    path = folder / "given" / receipt.publisher_file
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    store = FolderStore(folder / "store")
    store.put(receipt.source_id, receipt.publisher_file, path)
    inputs = Inputs(registry(), [receipt], store, folder / "work")
    return inputs.open(green_sites.SOURCE, Use.SCORING)


def file_ids(of_squares: Mapping[str, bytes]) -> dict[str, str]:
    """The id of the file of each square, by its letters."""
    return {
        letters: green_receipt(letters, content).file_id for letters, content in of_squares.items()
    }
