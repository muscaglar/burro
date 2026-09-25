"""A made-up file of places, laid out as the publisher of places lays out its own.

Nothing here is real. Every place is made up, and every name in the file is
the canary, so that a step that reads a name gives itself away.

The layout is the one the publisher's own pages give for release 2026-09-23.0,
as they were read on 2026-09-24: a Parquet file, packed with zstd, of sixteen
columns in the order its catalogue lists them, with the rows in row groups and
the places near each other in the same row group. Each row has a point as
well-known binary, and the box the point fits in as four numbers of four
bytes. The file's own metadata says which columns hold the box, as the
GeoParquet standard has it. No real file was opened to write this, so where
the pages do not give the type of a field, the type here is a guess, and it is
a field that no step reads.

It is written by a Parquet library and by nothing of Burro's, so that what
reads it here is held to a real writer.
"""
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false, reportMissingTypeStubs=false

import json
import struct
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

# A string found nowhere else. It stands in every field that no step may read.
CANARY = "Zzyzx Parva"
# The columns, in the order the publisher's catalogue lists them.
COLUMNS = (
    "id",
    "geometry",
    "confidence",
    "websites",
    "emails",
    "socials",
    "phones",
    "brand",
    "addresses",
    "names",
    "sources",
    "operating_status",
    "basic_category",
    "taxonomy",
    "version",
    "bbox",
)
# The columns a test takes, and the one that says where a row is. Of what the file says of
# where a record came from, the name of the dataset is taken and nothing beside it.
DATASET = "sources.list.element.dataset"
TAKEN = ("geometry", "confidence", DATASET, "operating_status", "taxonomy", "bbox")
BOX_IN = "bbox"
MUSEUM = ("arts_and_entertainment", "museum")


@dataclass(frozen=True)
class Place:
    """One made-up place: where it is, and what the file says it is."""

    longitude: float
    latitude: float
    hierarchy: tuple[str, ...] = MUSEUM
    alternates: tuple[str, ...] = ()
    dataset: str = "meta"
    confidence: float | None = 0.9
    status: str | None = "open"
    # What the file gives as the most particular category. It is the last of the hierarchy
    # unless a test says otherwise.
    primary: str | None = ""
    # What the file gives where the point would stand, in place of one.
    geometry: bytes | None = None
    # The chain the file says the place belongs to: the name it writes the chain by, and
    # the id an encyclopaedia gives it. Both hold the canary unless a test says otherwise.
    # With `None` the file gives the place no brand, as it does for a place of no chain.
    brand: tuple[str | None, str | None] | None = (f"Made-up Brand {CANARY}", CANARY)

    @property
    def most_particular(self) -> str | None:
        if self.primary == "":
            return self.hierarchy[-1] if self.hierarchy else None
        return self.primary


NAMES = pa.struct(
    [
        ("primary", pa.string()),
        ("common", pa.map_(pa.string(), pa.string())),
        ("rules", pa.list_(pa.struct([("variant", pa.string()), ("value", pa.string())]))),
    ]
)
LAYOUT = pa.schema(
    [
        ("id", pa.string()),
        ("geometry", pa.binary()),
        ("confidence", pa.float64()),
        ("websites", pa.list_(pa.string())),
        ("emails", pa.list_(pa.string())),
        ("socials", pa.list_(pa.string())),
        ("phones", pa.list_(pa.string())),
        ("brand", pa.struct([("wikidata", pa.string()), ("names", NAMES)])),
        (
            "addresses",
            pa.list_(
                pa.struct(
                    [
                        ("freeform", pa.string()),
                        ("locality", pa.string()),
                        ("postcode", pa.string()),
                        ("region", pa.string()),
                        ("country", pa.string()),
                    ]
                )
            ),
        ),
        ("names", NAMES),
        (
            "sources",
            pa.list_(
                pa.struct(
                    [
                        ("property", pa.string()),
                        ("dataset", pa.string()),
                        ("license", pa.string()),
                        ("record_id", pa.string()),
                        ("update_time", pa.string()),
                        ("confidence", pa.float64()),
                        ("between", pa.list_(pa.float64())),
                    ]
                )
            ),
        ),
        ("operating_status", pa.string()),
        ("basic_category", pa.string()),
        (
            "taxonomy",
            pa.struct(
                [
                    ("primary", pa.string()),
                    ("hierarchy", pa.list_(pa.string())),
                    ("alternates", pa.list_(pa.string())),
                ]
            ),
        ),
        ("version", pa.int32()),
        (
            "bbox",
            pa.struct(
                [
                    ("xmin", pa.float32()),
                    ("xmax", pa.float32()),
                    ("ymin", pa.float32()),
                    ("ymax", pa.float32()),
                ]
            ),
        ),
    ]
)
# What the file says of itself, as the GeoParquet standard has it.
GEO = {
    "version": "1.1.0",
    "primary_column": "geometry",
    "columns": {
        "geometry": {
            "encoding": "WKB",
            "geometry_types": ["Point"],
            "covering": {
                "bbox": {
                    "xmin": ["bbox", "xmin"],
                    "ymin": ["bbox", "ymin"],
                    "xmax": ["bbox", "xmax"],
                    "ymax": ["bbox", "ymax"],
                }
            },
        }
    },
}


def point(longitude: float, latitude: float) -> bytes:
    """A point as well-known binary writes one: its byte order, its type, and two numbers."""
    return struct.pack("<BIdd", 1, 1, longitude, latitude)


def _four_bytes(value: float) -> tuple[float, float]:
    """The numbers of four bytes just under and just over a number of eight."""
    (near,) = struct.unpack("<f", struct.pack("<f", value))
    (bits,) = struct.unpack("<i", struct.pack("<f", near))
    step = 1 if near >= 0 else -1
    (under,) = struct.unpack("<f", struct.pack("<i", bits - step))
    (over,) = struct.unpack("<f", struct.pack("<i", bits + step))
    return (under if near > value else near), (over if near < value else near)


def row_of(number: int, place: Place) -> dict[str, object]:
    """One row, as the publisher writes one. Every field that no step reads holds the canary."""
    west, east = _four_bytes(place.longitude)
    south, north = _four_bytes(place.latitude)
    said = {"primary": f"Made-up Place {number} {CANARY}", "common": None, "rules": None}
    chain = (
        None
        if place.brand is None
        else {
            "wikidata": place.brand[1],
            "names": {"primary": place.brand[0], "common": {CANARY: CANARY}, "rules": None},
        }
    )
    return {
        "id": f"made-up-{number:08d}-{CANARY}",
        "geometry": (
            point(place.longitude, place.latitude) if place.geometry is None else place.geometry
        ),
        "confidence": place.confidence,
        "websites": [f"https://made-up.example/{CANARY}"],
        "emails": [f"{CANARY}@made-up.example"],
        "socials": [f"https://made-up.example/social/{CANARY}"],
        "phones": [CANARY],
        "brand": chain,
        "addresses": [
            {
                "freeform": f"{number} {CANARY} Row",
                "locality": CANARY,
                "postcode": CANARY,
                "region": CANARY,
                "country": "ZZ",
            }
        ],
        "names": said,
        "sources": [
            {
                "property": "",
                "dataset": place.dataset,
                "license": CANARY,
                "record_id": f"{CANARY}-{number}",
                "update_time": "1999-09-09T00:00:00.000Z",
                "confidence": place.confidence,
                "between": None,
            }
        ],
        "operating_status": place.status,
        "basic_category": place.hierarchy[-1] if place.hierarchy else None,
        "taxonomy": {
            "primary": place.most_particular,
            "hierarchy": list(place.hierarchy) or None,
            "alternates": list(place.alternates) or None,
        },
        "version": 1,
        "bbox": {"xmin": west, "xmax": east, "ymin": south, "ymax": north},
    }


def made_up_places(
    path: Path,
    places: Sequence[Place],
    rows_in_a_group: int = 4,
    *,
    packed: str = "zstd",
    without: Sequence[str] = (),
    statistics: bool = True,
) -> Path:
    """Write a made-up file of places, its rows in the order given, so many to a row group.

    `without` leaves columns out, and `statistics` says whether the writer records the least
    and the most of each column, for a test of a file that is not laid out as expected.
    """
    layout = pa.schema([field for field in LAYOUT if field.name not in without])
    rows = [
        {name: held for name, held in row_of(number, place).items() if name not in without}
        for number, place in enumerate(places, start=1)
    ]
    table = pa.Table.from_pylist(rows, schema=layout).replace_schema_metadata(
        {"geo": json.dumps(GEO)}
    )
    pq.write_table(
        table,
        path,
        row_group_size=rows_in_a_group,
        compression=packed,
        write_statistics=statistics,
        store_schema=False,
    )
    return path


# Where the made-up places stand: in the North Sea, as the made-up town of the other tests.
WEST, LATITUDE, WIDE = 2.0, 53.4, 0.25


def a_town(groups: int = 6, in_a_group: int = 4) -> list[Place]:
    """Made-up places in a row from west to east, a row group to each quarter of a degree.

    The first row group holds the places between 2 and 2.25 degrees east, the second those
    between 2.25 and 2.5, and so on. All stand at one latitude, in open sea.
    """
    return [
        Place(WEST + WIDE * (group + (n + 0.5) / in_a_group), LATITUDE)
        for group in range(groups)
        for n in range(in_a_group)
    ]
