"""What the tests of the traffic near homes share: made-up count points.

Nothing here is real. The count points stand on the made-up town of the tests
of cells, spread out as `culture_support.py` spreads it: the centres of its
output areas stand 1,000 metres apart in three rows, 5,000 metres apart. A
count point is put so many metres east and north of a centre, so each distance
can be worked out by hand.

    north 10,000   T1  T2  T3  T4     Tallowgate 001   homes 190, 200, 210, 220
    north  5,000   R1  R2  R3  R4     Quillhaven 002   homes 150, 160, 170, 180
    north      0   Q1  Q2  Q3  Q4     Quillhaven 001   homes 110, 120, 130, 140

The file is a zip of one CSV, with the 34 columns the publisher's file has,
under the same names. It holds a row for each count point and year. What it
holds is made up. The name of every road, junction, region and authority is a
string found nowhere else, because none is ever read.

    Count point   Stands                       Years         Latest flow
    1             100 metres east of Q1        2019, 2023    12,000, estimated
    2             300 metres north of Q1       2024          15,000, counted
    3             400 metres west of Q2        2025          7,000, counted
    4             200 metres south of Q3       2010          4,000, counted
    5             100 metres east of R1        2025          30,000, estimated
    6             far from every home          2025          50, counted

So the homes of Q1 read 15,000, those of Q2 read 7,000, those of Q3 read 4,000
of 2010, and those of Q4 have no count point and no figure. The homes of R1
read 30,000, which is under half the homes of Quillhaven 002. No count point
stands in Tallowgate 001.
"""

import csv
import hashlib
import io
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from burro_pipeline.evidence.receipt import EditionFrom, How, Period, Receipt, Where
from burro_pipeline.evidence.record import file_id_of
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import CANARY, zip_of
from . import culture_support
from .culture_support import Q1, Q2, Q3, R1, Metres, beside, on_the_grid

SOURCE = "dft-road-traffic-counts"
FILE = "dft_traffic_counts_aadf.zip"
MEMBER = "dft_traffic_counts_aadf.csv"
# The years the made-up receipt says the file covers, as the real one does.
PERIOD = Period(start="2000", end="2025")
RETRIEVED = "2026-09-25"
# Every column of the publisher's file, in the file's order.
COLUMNS: tuple[str, ...] = (
    "count_point_id",
    "year",
    "region_id",
    "region_name",
    "region_ons_code",
    "local_authority_id",
    "local_authority_name",
    "local_authority_code",
    "road_name",
    "road_category",
    "road_type",
    "start_junction_road_name",
    "end_junction_road_name",
    "easting",
    "northing",
    "latitude",
    "longitude",
    "link_length_km",
    "link_length_miles",
    "estimation_method",
    "estimation_method_detailed",
    "pedal_cycles",
    "two_wheeled_motor_vehicles",
    "cars_and_taxis",
    "buses_and_coaches",
    "LGVs",
    "HGVs_2_rigid_axle",
    "HGVs_3_rigid_axle",
    "HGVs_4_or_more_rigid_axle",
    "HGVs_3_or_4_articulated_axle",
    "HGVs_5_articulated_axle",
    "HGVs_6_articulated_axle",
    "all_HGVs",
    "all_motor_vehicles",
)
COUNTED, ESTIMATED = "Counted", "Estimated"


@dataclass(frozen=True)
class MadeUpCount:
    """One made-up row: the flow at one count point on an average day of one year."""

    point: int
    year: int
    # Where it stands, in metres east and north of the first centre of the town.
    at: Metres
    flow: int | str
    how: str = COUNTED
    category: str = "PA"


BY_Q1 = (
    MadeUpCount(1, 2019, beside(Q1, 100), 9_000),
    MadeUpCount(1, 2023, beside(Q1, 100), 12_000, ESTIMATED),
)
NORTH_OF_Q1 = MadeUpCount(2, 2024, beside(Q1, 0, 300), 15_000)
WEST_OF_Q2 = MadeUpCount(3, 2025, beside(Q2, -400), 7_000)
SOUTH_OF_Q3 = MadeUpCount(4, 2010, beside(Q3, 0, -200), 4_000, category="MCU")
BY_R1 = MadeUpCount(5, 2025, beside(R1, 100), 30_000, ESTIMATED, "TM")
ELSEWHERE = MadeUpCount(6, 2025, (40_000.0, 40_000.0), 50, category="MB")
COUNTS: tuple[MadeUpCount, ...] = (
    *BY_Q1,
    NORTH_OF_Q1,
    WEST_OF_Q2,
    SOUTH_OF_Q3,
    BY_R1,
    ELSEWHERE,
)


# The count points of the whole of a made-up build, which `tests/assemble/support.py` puts
# together. Its homes are taken to stand by the middles of four squares of a kilometre, and
# a road runs by each. A count point stands on each road, under 100 metres from the homes,
# so that every home of the build has a figure. Each is of the one year the receipt of that
# build states.
BY_THE_ROADS: tuple[MadeUpCount, ...] = (
    MadeUpCount(21, 2025, (450.0, 500.0), 21_000),
    MadeUpCount(22, 2025, (1_500.0, 400.0), 3_000, ESTIMATED, "MCU"),
    MadeUpCount(23, 2025, (1_500.0, 1_400.0), 2_000, category="MCU"),
    MadeUpCount(24, 2025, (5_500.0, 400.0), 6_000, category="MB"),
)


def counts_csv(rows: Sequence[MadeUpCount] = COUNTS, columns: Sequence[str] = COLUMNS) -> str:
    """The table of flows, as the publisher writes it. What it holds is made up."""
    text = io.StringIO(newline="")
    table = csv.DictWriter(text, columns, extrasaction="ignore", lineterminator="\n")
    table.writeheader()
    for row in rows:
        east, north = on_the_grid(row.at)
        every: dict[str, object] = dict.fromkeys(COLUMNS, 7) | {
            "count_point_id": row.point,
            "year": row.year,
            "region_name": CANARY,
            "region_ons_code": "E12999999",
            "local_authority_name": CANARY,
            "local_authority_code": "E09000901",
            "road_name": CANARY,
            "road_category": row.category,
            "road_type": "Major" if row.category in ("PA", "TA", "PM", "TM") else "Minor",
            "start_junction_road_name": CANARY,
            "end_junction_road_name": CANARY,
            "easting": _whole(east),
            "northing": _whole(north),
            "latitude": 53.0,
            "longitude": 2.0,
            "link_length_km": 0.5,
            "link_length_miles": 0.31,
            "estimation_method": row.how,
            "estimation_method_detailed": CANARY,
            "all_motor_vehicles": row.flow,
        }
        table.writerow(every)
    return text.getvalue()


def _whole(metres: float) -> object:
    """A place as the file writes one: in whole metres, where it is a whole number of them."""
    return int(metres) if float(metres).is_integer() else metres


def counts_zip(rows: Sequence[MadeUpCount] = COUNTS, columns: Sequence[str] = COLUMNS) -> bytes:
    """The zip the publisher hands out: the one table inside it."""
    return zip_of({MEMBER: counts_csv(rows, columns)})


def counts_receipt(content: bytes, *, period: Period = PERIOD, name: str = FILE) -> Receipt:
    """The receipt a fetch would write of the made-up file."""
    sha256 = hashlib.sha256(content).hexdigest()
    return Receipt(
        file_id=file_id_of(sha256),
        source_id=SOURCE,
        use=Use.SCORING,
        publisher_file=name,
        url=f"https://files.made-up.example/{sha256[:8]}",
        sha256=sha256,
        bytes=len(content),
        retrieved_at=f"{RETRIEVED}T06:13:59Z",
        how=How.FETCHED,
        edition=f"retrieved {RETRIEVED}",
        edition_from=EditionFrom(where=Where.RETRIEVED, at="", period_too=False),
        data_period=period,
    )


def inputs_of(
    folder: Path,
    packed: bytes | None = None,
    *,
    centres: bytes | None = None,
    period: Period = PERIOD,
    given: Registry | None = None,
    with_a_receipt: bool = True,
) -> Inputs:
    """The made-up files of a build in a store of their own, the count points among them."""
    content = counts_zip() if packed is None else packed
    receipt = counts_receipt(content, period=period)
    town = culture_support.inputs_of(folder, None, centres, more=[(receipt, content)], given=given)
    if with_a_receipt:
        return town
    receipts = [one for one in town.receipts if one.file_id != receipt.file_id]
    return Inputs(town.registry, receipts, town.store, town.work)
