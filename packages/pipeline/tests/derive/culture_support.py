"""What the tests of culture share: a made-up file of places, taken in part as fetch takes it.

Nothing here is real. The town is Quillhaven and Tallowgate, two boroughs that
do not exist, which the tests of cells draw in the North Sea. Every place is
made up, and every name in the file is the canary.

The file is written by a Parquet library as the publisher of places lays out
its own: `tests/fetch/parquet_support.py` says how. It is then taken in part
as fetch takes it, from disk and with no connection, and kept in a store with
a receipt that says which part it is. So a step reads here what a fetch would
hand it.

The town is spread out for these tests, so that what is within reach of one
home is not within reach of every home. The centres of its output areas stand
1,000 metres apart in three rows, 5,000 metres apart:

    north 10,000   T1  T2  T3  T4     Tallowgate 001   homes 190, 200, 210, 220
    north  5,000   R1  R2  R3  R4     Quillhaven 002   homes 150, 160, 170, 180
    north      0   Q1  Q2  Q3  Q4     Quillhaven 001   homes 110, 120, 130, 140
            east   0  1,000  2,000  3,000

The one output area outside London stands far to the east, unless a test
brings it near. A place is put so many metres east and north of the first
centre, on the National Grid, and written as longitude and latitude, as the
publisher writes it.
"""

import hashlib
import io
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from burro_pipeline.cells.shapes import longitude_and_latitude
from burro_pipeline.evidence.receipt import How, Period, Receipt, Taken
from burro_pipeline.evidence.record import file_id_of
from burro_pipeline.fetch.store import FolderStore
from burro_pipeline.fetch.take import take, taken_as
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import (
    CENTRES_COLUMNS,
    EAST,
    FILES,
    LONDON,
    NORTH,
    TOWN,
    contents,
    receipt_of,
    registry,
)
from ..fetch.parquet_support import BOX_IN, CANARY, Place, made_up_places

SOURCE = "overture-places"
EDITION, DAY = "2026-09-23.0", "2026-09-23"
NAME = "part-00007-made-up-c000.zstd.parquet"
ONE, TWO, THREE = "lon-ne02999001", "lon-ne02999002", "lon-ne02999003"
OAS = tuple(unit.oa for unit in LONDON)
OUTSIDE = next(unit.oa for unit in TOWN if unit not in LONDON)
# How far apart the centres stand, and the rows they stand in.
APART, ROWS = 1_000, 5_000
FAR_EAST = 50_000
# The columns the list of the build takes, and a box that holds the whole of the town.
COLUMNS = ("geometry", "bbox", "taxonomy", "confidence", "operating_status", "sources")
BOX = (2.0, 53.0, 4.5, 54.0)

ARTS = "arts_and_entertainment"
STAGE = (ARTS, "performing_arts_venue")
MUSEUM = (ARTS, "museum")
ART_MUSEUM = (ARTS, "museum", "art_museum")
GALLERY = (ARTS, "arts_and_crafts_space", "art_gallery")
THEATRE = (*STAGE, "theatre_venue")
CINEMA = (ARTS, "movie_theater")
MUSIC = (*STAGE, "music_venue")
LIBRARY = ("education", "library")
CHOIR = (*STAGE, "music_venue", "choir")
CAFE = ("food_and_drink", "cafe")
SHOP = ("shopping", "bookstore")

Metres = tuple[float, float]


def centre_of(oa: str) -> Metres:
    """Where the centre of an output area of the town stands, from the first centre."""
    number = OAS.index(oa)
    return float(number % 4 * APART), float(number // 4 * ROWS)


def on_the_grid(at: Metres) -> tuple[float, float]:
    return EAST + at[0], NORTH + at[1]


def centres_at(
    outside: Metres = (FAR_EAST, 0.0),
    without: Sequence[str] = (),
    more: Sequence[Metres] = (),
) -> bytes:
    """The centres of the town's output areas, and of the one outside London.

    `more` are centres of further output areas outside London, which no other
    file of the made-up build names.
    """
    lines = [",".join(CENTRES_COLUMNS)]
    placed = [(oa, centre_of(oa)) for oa in OAS if oa not in without]
    placed.append((OUTSIDE, outside))
    placed += [(f"E00998{number:03d}", at) for number, at in enumerate(more, start=1)]
    for number, (oa, at) in enumerate(placed, start=1):
        east, north = on_the_grid(at)
        lines.append(
            f"{east:.4f},{north:.4f},{number},{oa},{{made-up-{number}}},{{made-up-{number}-2}}"
        )
    return b"\xef\xbb\xbf" + "".join(f"{line}\n" for line in lines).encode()


def place(at: Metres, hierarchy: tuple[str, ...] = MUSEUM, **said: object) -> Place:
    """A made-up place so many metres east and north of the first centre of the town."""
    longitude, latitude = longitude_and_latitude(*on_the_grid(at))
    return replace(Place(longitude, latitude, hierarchy), **said)  # pyright: ignore[reportArgumentType]


Q1, Q2, Q3, Q4 = (centre_of(oa) for oa in OAS[:4])
R1, R2, R3, R4 = (centre_of(oa) for oa in OAS[4:8])
T1, T2, T3, T4 = (centre_of(oa) for oa in OAS[8:])


def beside(centre: Metres, east: float = 0.0, north: float = 0.0) -> Metres:
    return centre[0] + east, centre[1] + north


# A shop stands 30 metres south of every centre, so that the file is seen to hold something
# within reach of every home.
BY_EVERY_CENTRE = tuple(place(beside(centre_of(oa), 0, -30), SHOP) for oa in OAS)
# What stands in the town unless a test says otherwise. Every place is put against a centre,
# so that each count can be made by hand.
IN_THE_TOWN = (
    *BY_EVERY_CENTRE,
    # A museum, a gallery and a theatre stand 100 metres from the first centre.
    place(beside(Q1, 100), MUSEUM),
    place(beside(Q1, 0, 100), GALLERY),
    place(beside(Q1, -100), THEATRE),
    # A cinema stands half way between the second centre and the third.
    place(beside(Q2, 500), CINEMA),
    # A library stands 790 metres north of the fourth centre, and a music venue 810.
    place(beside(Q4, 0, 790), LIBRARY),
    place(beside(Q4, 0, 810), MUSIC),
    # What is no venue of culture stands beside the first centre too.
    place(beside(Q1, 10, 10), CAFE),
    place(beside(Q1, 20, 20), SHOP),
    place(beside(Q1, 30, 30), STAGE),
    place(beside(Q1, 40, 40), CHOIR),
    place(beside(Q1, 50, 50), THEATRE, alternates=("drama_school",)),
    place(beside(Q1, 60, 60), MUSEUM, status="permanently_closed"),
    # The second area has one library, beside its first centre.
    place(beside(R1, 0, 50), LIBRARY),
    # Two museums and a gallery beside the first centre of Tallowgate, and nothing else.
    place(beside(T1, 50), ART_MUSEUM),
    place(beside(T1, -50), MUSEUM),
    place(beside(T1, 0, 50), GALLERY),
)


@dataclass(frozen=True)
class Wanted:
    """What a made-up list states of the part to take."""

    box: tuple[float, float, float, float] = BOX
    box_in: str = BOX_IN
    columns: tuple[str, ...] = COLUMNS


class _OnDisk:
    """A file that is asked for a piece at a time, from the bytes of it."""

    def __init__(self, whole: bytes) -> None:
        self._whole = whole

    @property
    def of_bytes(self) -> int:
        return len(self._whole)

    def end(self, count: int) -> bytes:
        return self._whole[-count:]

    def piece(self, first: int, count: int, keep: Callable[[bytes], object]) -> None:
        keep(self._whole[first : first + count])


def whole_file(folder: Path, places: Sequence[Place], **how: object) -> bytes:
    """A made-up file of places, whole, as the publisher would give it."""
    folder.mkdir(parents=True, exist_ok=True)
    path = made_up_places(folder / "whole.parquet", places, **how)  # pyright: ignore[reportArgumentType]
    return path.read_bytes()


def part_of(whole: bytes, wanted: Wanted | None = None) -> tuple[bytes, Taken]:
    """The part of a file that fetch would keep, and what its receipt would say of it."""
    wanted = wanted or Wanted()
    kept = io.BytesIO()
    plan = take(_OnDisk(whole), wanted, kept, len(whole) + 1)
    return kept.getvalue(), taken_as(plan, wanted)


def places_receipt(content: bytes, taken: Taken | None, **changed: object) -> Receipt:
    sha256 = hashlib.sha256(content).hexdigest()
    url = f"https://files.made-up.example/release/{EDITION}/theme=places/type=place/{NAME}"
    fields: dict[str, object] = {
        "file_id": file_id_of(sha256),
        "source_id": SOURCE,
        "use": Use.SCORING,
        "publisher_file": NAME,
        "url": url,
        "listed_url": url,
        "sha256": sha256,
        "bytes": len(content),
        "retrieved_at": "2026-09-24T09:12:31Z",
        "how": How.FETCHED,
        "edition": EDITION,
        "data_period": Period(as_at=DAY),
        "taken": taken,
    } | changed
    return Receipt.model_validate(fields)


def inputs_of(
    folder: Path,
    places: Sequence[Place] | None = IN_THE_TOWN,
    centres: bytes | None = None,
    *,
    wanted: Wanted | None = None,
    whole: bool = False,
    more: Sequence[tuple[Receipt, bytes]] = (),
    given: Registry | None = None,
    **how: object,
) -> Inputs:
    """The made-up files of a build in a store of their own, with a receipt for each.

    With `whole`, the file of places is kept whole, as a fetch that took no
    part of it would keep it. With no places, no file of places is kept.
    """
    files = contents() | {"centres": centres_at() if centres is None else centres}
    every = [
        (
            receipt_of(FILES[which][0], FILES[which][1], FILES[which][2], content, FILES[which][3]),
            content,
        )
        for which, content in files.items()
    ]
    if places is not None:
        written = whole_file(folder / "written", places, **how)
        content, taken = (written, None) if whole else part_of(written, wanted)
        every.append((places_receipt(content, taken), content))
    every += list(more)
    store = FolderStore(folder / "store")
    for receipt, content in every:
        path = folder / "given" / receipt.file_id / receipt.publisher_file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        store.put(receipt.source_id, receipt.publisher_file, path)
    return Inputs(given or registry(), [receipt for receipt, _ in every], store, folder / "work")


def counts(found: Mapping[Any, int]) -> dict[str, int]:
    """Counts by what they count, as plain words, with what counts nothing left out."""
    return {str(key): found[key] for key in sorted(found, key=str) if found[key]}


__all__ = ["CANARY", "THREE", "TWO"]
