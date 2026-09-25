"""What the tests of the names of a build share: a made-up draft of names, as three tables.

Nothing here is real. The town is the one the tests of cells draw, Quillhaven
and Tallowgate, in the North Sea: three census areas of four output areas each.
Every name is one the made-up city of the synthetic release already holds, so
none was coined here. The draft gives the town's twelve output areas to
neighbourhoods of those names, as a draft of London gives London's.

    columns  0    1    2    3    4    5
    row 1  | 1  | 2  | 5  | 6  | 9  | 10 |     each square is one output area
    row 0  | 3  | 4  | 7  | 8  | 11 | 12 |
             Quillhaven 001  002   Tallowgate 001
"""

import csv
import hashlib
import io
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from burro_pipeline.assemble import names
from burro_pipeline.cells.spine import Area, area_id_of
from burro_pipeline.evidence.receipt import Receipt
from burro_pipeline.registry.model import Use

from ..areas import names_support as town
from ..cells.support import LONDON, receipt_of

PLACES, CENTRES, WARDS = "os-open-names", "gla-town-centre-boundaries", "os-boundary-line"
# The made-up files that write the names: the names of places, and the town centres.
NAMES_FILE, CENTRES_FILE = town.names_zip(), town.centres_gpkg()
FOUNDER = "founder"
ALDERWICK, FOXHOLT, ESKERFOLD, NO_NAME = "lon-n0001", "lon-n0002", "lon-n0003", "lon-n0004"


def oa(number: int) -> str:
    """The code of an output area of the town, by its number."""
    return f"E00999{number:03d}"


def sha256_of(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def receipts() -> list[Receipt]:
    """The receipt of each made-up file that writes a name."""
    return [
        receipt_of(PLACES, Use.GAZETTEER, "opname_csv_gb.zip", NAMES_FILE, "2026-07"),
        receipt_of(CENTRES, Use.SCORING, "Town_Centres_Boundaries.gpkg", CENTRES_FILE, "made up"),
    ]


# The hash of the file of each source that a row of evidence says it was read from.
READ_FROM = {PLACES: sha256_of(NAMES_FILE), CENTRES: sha256_of(CENTRES_FILE)}


@dataclass(frozen=True)
class Wrote:
    """One row of evidence: a record of a source beside the name of a neighbourhood."""

    place_id: str
    source_id: str
    as_written: str
    chosen_by: str = ""
    role: str = names.PRIMARY


def table(columns: Sequence[str], rows: Sequence[Mapping[str, str]]) -> bytes:
    text = io.StringIO(newline="")
    written = csv.DictWriter(text, columns, lineterminator="\n")
    written.writeheader()
    written.writerows(rows)
    return text.getvalue().encode("utf-8")


# The neighbourhoods of the made-up draft. The last has no name: no record lies in it.
NEIGHBOURHOODS = {ALDERWICK: "Alderwick", FOXHOLT: "Foxholt", ESKERFOLD: "Eskerfold", NO_NAME: ""}
# The neighbourhood each output area is given to. Alderwick holds all of the first area and
# half of the second, so two areas of one borough bear its name.
GIVEN = {
    **dict.fromkeys((1, 2, 3, 4, 5, 7), ALDERWICK),
    **dict.fromkeys((6,), FOXHOLT),
    **dict.fromkeys((8,), NO_NAME),
    **dict.fromkeys((9, 10, 11), ESKERFOLD),
    **dict.fromkeys((12,), FOXHOLT),
}
# Who writes each name. A ward's label holds a name among other words, and writes another.
EVIDENCE = (
    Wrote(ALDERWICK, PLACES, "Alderwick"),
    Wrote(ALDERWICK, CENTRES, "Alderwick"),
    Wrote(ALDERWICK, WARDS, "Alderwick Ward"),
    Wrote(FOXHOLT, PLACES, "Foxholt"),
    Wrote(ESKERFOLD, PLACES, "Eskerfold"),
    Wrote(ESKERFOLD, PLACES, "Eskerfold Green", role="alias"),
)


def files(
    neighbourhoods: Mapping[str, str] = NEIGHBOURHOODS,
    given: Mapping[int, str] = GIVEN,
    evidence: Sequence[Wrote] = EVIDENCE,
    read_from: Mapping[str, str] = READ_FROM,
) -> dict[str, bytes]:
    """The three files of a draft that a build reads, with columns the build does not read.

    `read_from` gives the hash of the file of each source, as the draft says it read it.
    A source it does not hold is said to have been read from the file of names.
    """
    return {
        names.AREAS: table(
            ("area_id", "slug", "name", "primary_borough", "review_state", "state"),
            [
                {
                    "area_id": place,
                    "slug": name.lower(),
                    "name": name,
                    "primary_borough": "Quillhaven",
                    "review_state": "drafted",
                    "state": "draft, made by method, checked by nobody",
                }
                for place, name in neighbourhoods.items()
            ],
        ),
        names.GIVEN: table(
            ("oa21cd", "area_id", "basis"),
            [
                {"oa21cd": oa(number), "area_id": place, "basis": "auto"}
                for number, place in sorted(given.items())
            ],
        ),
        names.EVIDENCE: table(
            (
                *("area_id", "name", "role", "source_id", "record_id", "as_written"),
                *("locates", "snapshot_sha256", "chosen_by", "chosen_on"),
            ),
            [
                {
                    "area_id": row.place_id,
                    "name": neighbourhoods.get(row.place_id, ""),
                    "role": row.role,
                    "source_id": row.source_id,
                    "record_id": f"made-up-{number}",
                    "as_written": row.as_written,
                    "locates": "point_inside",
                    "snapshot_sha256": read_from.get(row.source_id, read_from[PLACES]),
                    "chosen_by": row.chosen_by,
                    "chosen_on": "2026-09-24" if row.chosen_by else "",
                }
                for number, row in enumerate(evidence, start=1)
            ],
        ),
    }


def areas() -> tuple[Area, ...]:
    """The three census areas of the town, as the spine of a build holds them."""
    found = {
        unit.msoa: Area(
            area_id=area_id_of(unit.msoa),
            code=unit.msoa,
            name=unit.msoa_name,
            slug=unit.msoa_name.lower().replace(" ", "-"),
            borough=unit.borough_name,
            borough_code=unit.borough,
        )
        for unit in LONDON
    }
    return tuple(sorted(found.values()))


def cells() -> dict[str, tuple[str, ...]]:
    """The output areas of each area of the town."""
    found: dict[str, list[str]] = {}
    for unit in LONDON:
        found.setdefault(area_id_of(unit.msoa), []).append(unit.oa)
    return {area: tuple(sorted(held)) for area, held in found.items()}


# A point inside each area, as longitude and latitude: the three stand west to east.
CENTRES_OF = {
    "lon-ne02999001": (2.001, 53.4),
    "lon-ne02999002": (2.004, 53.4),
    "lon-ne02999003": (2.007, 53.4),
}
