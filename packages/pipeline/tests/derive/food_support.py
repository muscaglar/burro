"""What the tests of the food register share: a made-up register, laid out as the real one is.

Nothing here is real. The town is Quillhaven and Tallowgate, two boroughs that
do not exist, which the tests of cells draw in the North Sea. Each has a file
of a made-up register, and every business in it has a made-up name. A file
says that it is made up, in a comment above its root.

A file is laid out as the publisher lays out its own: a declaration, the root
`FHRSEstablishment`, a header of three elements, and one `EstablishmentDetail`
for each business, all on one line. Every element the real file holds is here.
The elements that no step may read hold the canary, so a step that reads one
gives itself away.

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
register writes it.
"""

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

from burro_pipeline.cells.shapes import longitude_and_latitude
from burro_pipeline.evidence.receipt import EditionFrom, How, Period, Receipt, Where
from burro_pipeline.evidence.record import file_id_of
from burro_pipeline.fetch.store import FolderStore
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

SOURCE = "fsa-food-hygiene-ratings"
# A string found nowhere else. It stands in every element that no step may read.
CANARY = "Zzyzx Parva"
SAID = "<!-- Made up for a test. It describes no real place and no real business. -->"
DAY, LATER = "2026-09-16", "2026-09-17"
# The register's own numbers for two authorities that do not exist.
QUILLHAVEN, TALLOWGATE = "901", "902"
ONE, TWO, THREE = "lon-ne02999001", "lon-ne02999002", "lon-ne02999003"
OAS = tuple(unit.oa for unit in LONDON)
OUTSIDE = next(unit.oa for unit in TOWN if unit not in LONDON)
# How far apart the centres stand, and the rows they stand in.
APART, ROWS = 1_000, 5_000
FAR_EAST = 50_000

# The kinds of business, as the register writes them, each with its number.
EAT = ("Restaurant/Cafe/Canteen", "1")
PUB = ("Pub/bar/nightclub", "7843")
TAKEAWAY = ("Takeaway/sandwich shop", "7844")
SHOP = ("Retailers - other", "4613")
SUPERMARKET = ("Retailers - supermarkets/hypermarkets", "7840")
SCHOOL = ("School/college/university", "7845")
CARING = ("Hospitals/Childcare/Caring Premises", "5")
CATERER = ("Other catering premises", "7841")
VAN = ("Mobile caterer", "7846")
HOTEL = ("Hotel/bed & breakfast/guest house", "7842")
MAKER = ("Manufacturers/packers", "7839")
CARRIER = ("Distributors/Transporters", "7")
IMPORTER = ("Importers/Exporters", "14")
FARMER = ("Farmers/growers", "7838")
EVERY_KIND = (
    EAT,
    PUB,
    TAKEAWAY,
    SHOP,
    SUPERMARKET,
    SCHOOL,
    CARING,
    CATERER,
    VAN,
    HOTEL,
    MAKER,
    CARRIER,
    IMPORTER,
    FARMER,
)

Metres = tuple[float, float]


@dataclass(frozen=True)
class Business:
    """One made-up business: its kind, and where it is, if the register says where."""

    kind: tuple[str, str]
    # So many metres east and north of the first centre of the town. None is no point.
    at: Metres | None
    # What the register writes where the point would stand, in place of `at`.
    point: str | None = None
    authority: str | None = None


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
    moved: Mapping[str, Metres] | None = None,
) -> bytes:
    """The centres of the town's output areas, and of the one outside London.

    `more` are centres of further output areas outside London, which no other
    file of the made-up build names. `moved` puts a centre of the town
    somewhere else.
    """
    lines = [",".join(CENTRES_COLUMNS)]
    placed = [(oa, (moved or {}).get(oa, centre_of(oa))) for oa in OAS if oa not in without]
    placed.append((OUTSIDE, outside))
    placed += [(f"E00998{number:03d}", at) for number, at in enumerate(more, start=1)]
    for number, (oa, at) in enumerate(placed, start=1):
        east, north = on_the_grid(at)
        lines.append(
            f"{east:.4f},{north:.4f},{number},{oa},{{made-up-{number}}},{{made-up-{number}-2}}"
        )
    return b"\xef\xbb\xbf" + "".join(f"{line}\n" for line in lines).encode()


def written(at: Metres) -> str:
    """A point as the register writes one: a longitude and a latitude, each an element."""
    longitude, latitude = longitude_and_latitude(*on_the_grid(at))
    return f"<Longitude>{longitude}</Longitude><Latitude>{latitude}</Latitude>"


def detail(business: Business, authority: str, number: int, **changed: str) -> str:
    """One business, as the register writes it. Every name in it is made up."""
    if business.point is not None:
        point = f"<Geocode>{business.point}</Geocode>"
    else:
        point = (
            "<Geocode />" if business.at is None else f"<Geocode>{written(business.at)}</Geocode>"
        )
    kind, kind_id = business.kind
    elements = {
        "FHRSID": str(900_000 + number),
        "LocalAuthorityBusinessID": f"MADE-UP-{number}",
        "BusinessName": f"Made-up Business {number} {CANARY}",
        "BusinessType": escape(kind),
        "BusinessTypeID": kind_id,
        "AddressLine1": f"{number} {CANARY} Row",
        "AddressLine2": CANARY,
        "PostCode": CANARY,
        "RatingValue": CANARY,
        "RatingKey": CANARY,
        "RatingDate": "1999-09-09",
        "LocalAuthorityCode": business.authority or authority,
        "LocalAuthorityName": f"Made-up Authority {CANARY}",
        "LocalAuthorityWebSite": "https://made-up.example/",
        "LocalAuthorityEmailAddress": "made-up@made-up.example",
        "Scores": f"<Hygiene>{CANARY}</Hygiene><Structural>{CANARY}</Structural>"
        f"<ConfidenceInManagement>{CANARY}</ConfidenceInManagement>",
        "SchemeType": "FHRS",
        "NewRatingPending": CANARY,
    } | changed
    inside = "".join(f"<{name}>{held}</{name}>" for name, held in elements.items() if held != "")
    return f"<EstablishmentDetail>{inside}{point}</EstablishmentDetail>"


def header_of(
    day: str | None = DAY, items: int | str | None = 0, code: str | None = "Success"
) -> str:
    parts = (("ExtractDate", day), ("ItemCount", items), ("ReturnCode", code))
    return "<Header>" + "".join(f"<{n}>{v}</{n}>" for n, v in parts if v is not None) + "</Header>"


def register_xml(
    businesses: Sequence[Business],
    authority: str = QUILLHAVEN,
    *,
    day: str = DAY,
    header: str | None = None,
    root: str = "FHRSEstablishment",
    rows: Sequence[str] | None = None,
    before: str = SAID,
) -> bytes:
    """One file of the made-up register, on one line, as the publisher writes its own."""
    details = (
        [detail(business, authority, number) for number, business in enumerate(businesses, 1)]
        if rows is None
        else list(rows)
    )
    head = header_of(day, len(details)) if header is None else header
    return (
        f'<?xml version="1.0"?>{before}'
        f'<{root} xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">{head}'
        f"<EstablishmentCollection>{''.join(details)}</EstablishmentCollection></{root}>"
    ).encode()


def name_of(authority: str) -> str:
    """The publisher's name for the file of an authority."""
    return f"FHRS{authority}en-GB.xml"


def register_receipt(content: bytes, authority: str = QUILLHAVEN, day: str = DAY) -> Receipt:
    sha256 = hashlib.sha256(content).hexdigest()
    url = f"https://files.made-up.example/register/{name_of(authority)}"
    return Receipt(
        file_id=file_id_of(sha256),
        source_id=SOURCE,
        use=Use.SCORING,
        publisher_file=name_of(authority),
        url=url,
        listed_url=url,
        sha256=sha256,
        bytes=len(content),
        retrieved_at="2026-09-23T21:09:21Z",
        how=How.FETCHED,
        edition=f"extract of {day}",
        edition_from=EditionFrom(where=Where.XML_HEADER, at="Header/ExtractDate", period_too=True),
        data_period=Period(as_at=day),
    )


# What stands in the town unless a test says otherwise. Every place is put against a centre,
# so that each count can be made by hand.
Q1, Q2, Q3, Q4 = (centre_of(oa) for oa in OAS[:4])
R1, R2, R3, R4 = (centre_of(oa) for oa in OAS[4:8])
T1, T2, T3, T4 = (centre_of(oa) for oa in OAS[8:])


def beside(centre: Metres, east: float = 0.0, north: float = 0.0) -> Metres:
    return centre[0] + east, centre[1] + north


IN_QUILLHAVEN = (
    # Three places to eat, a pub and a takeaway stand 100 metres from the first centre.
    Business(EAT, beside(Q1, 100)),
    Business(EAT, beside(Q1, 0, 100)),
    Business(EAT, beside(Q1, -100)),
    Business(PUB, beside(Q1, 0, -100)),
    Business(TAKEAWAY, beside(Q1, 60, 80)),
    # One place to eat stands half way between the second centre and the third.
    Business(EAT, beside(Q2, 500)),
    # A pub stands 790 metres north of the fourth centre, and a takeaway 810.
    Business(PUB, beside(Q4, 0, 790)),
    Business(TAKEAWAY, beside(Q4, 0, 810)),
    # What is no place to eat or drink stands beside the first centre too.
    Business(SHOP, beside(Q1, 10, 10)),
    Business(SCHOOL, beside(Q1, 20, 20)),
    Business(CATERER, beside(Q1, 30, 30)),
    Business(VAN, beside(Q1, 40, 40)),
    Business(HOTEL, beside(Q1, 50, 50)),
    # Two places to eat have no point. They are counted, and are within reach of nobody.
    Business(EAT, None),
    Business(EAT, None),
    # The second area has one takeaway, beside its first centre.
    Business(TAKEAWAY, beside(R1, 0, 50)),
)
IN_TALLOWGATE = (
    # Two places to eat and a pub beside the first centre of Tallowgate, and nothing else.
    Business(EAT, beside(T1, 50)),
    Business(EAT, beside(T1, -50)),
    Business(PUB, beside(T1, 0, 50)),
    Business(CARING, beside(T2, 10)),
    Business(PUB, None),
)
TOWNS = {QUILLHAVEN: IN_QUILLHAVEN, TALLOWGATE: IN_TALLOWGATE}


def inputs_of(
    folder: Path,
    registers: Mapping[str, bytes] | None = None,
    centres: bytes | None = None,
    *,
    day: str = DAY,
    more: Sequence[tuple[Receipt, bytes]] = (),
    given: Registry | None = None,
) -> Inputs:
    """The made-up files of a build in a store of their own, with a receipt for each."""
    if registers is None:
        registers = {code: register_xml(held, code) for code, held in TOWNS.items()}
    files = contents() | {"centres": centres_at() if centres is None else centres}
    every = [
        (
            receipt_of(FILES[which][0], FILES[which][1], FILES[which][2], content, FILES[which][3]),
            content,
        )
        for which, content in files.items()
    ]
    every += [
        (register_receipt(content, code, day), content) for code, content in registers.items()
    ]
    every += list(more)
    store = FolderStore(folder / "store")
    for receipt, content in every:
        path = folder / "given" / receipt.file_id / receipt.publisher_file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        store.put(receipt.source_id, receipt.publisher_file, path)
    return Inputs(given or registry(), [receipt for receipt, _ in every], store, folder / "work")
