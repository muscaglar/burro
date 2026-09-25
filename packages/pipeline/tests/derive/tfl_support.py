"""A made-up file of the stations of a transport authority, as the publisher's zip is laid out.

Every station, line and point here is made up. The zip holds the four tables
that are read, with columns beside them that are not, and the table of names,
which is never opened: a name that is read fails a test by the word it holds.
"""

import csv
import hashlib
import io
import zipfile
from collections.abc import Sequence
from dataclasses import dataclass

from burro_pipeline.cells.shapes import longitude_and_latitude
from burro_pipeline.derive import tfl_stations
from burro_pipeline.evidence.receipt import How, Period, Receipt
from burro_pipeline.evidence.record import file_id_of
from burro_pipeline.registry.model import Use

from ..cells.support import CANARY

RETRIEVED = "2026-09-24"
# The lines of the made-up file, each with the mode the publisher gives it.
LINES = (
    ("overground", "weaver"),
    ("elizabeth-line", "elizabeth"),
    ("nationalRail", "national-rail"),
    ("tube", "central"),
    ("tram", "tram"),
    ("dlr", "dlr"),
    ("cableCar", "london-cable-car"),
)
# A day early in its first member, so that the same stations are the same bytes.
WRITTEN = (2026, 9, 24, 0, 0, 0)


@dataclass(frozen=True)
class MadeUpStation:
    """One station: its id, the lines that call at it, and its points on the grid of the town."""

    station_id: str
    lines: tuple[str, ...]
    points: tuple[tuple[float, float], ...]
    name: str = CANARY


def _csv(columns: Sequence[str], rows: Sequence[Sequence[object]]) -> bytes:
    text = io.StringIO(newline="")
    table = csv.writer(text, lineterminator="\r\n")
    table.writerow(columns)
    table.writerows(rows)
    return text.getvalue().encode("utf-8")


def tables_of(
    stations: Sequence[MadeUpStation], lines: Sequence[tuple[str, str]] = LINES
) -> dict[str, bytes]:
    """The tables of the zip, by their names."""
    platforms = [
        (f"{station.station_id}-Plat{at:02d}", station.station_id, line)
        for station in stations
        for at, line in enumerate(station.lines, start=1)
    ]
    points = [
        (
            f"{station.station_id}-{at}",
            station.station_id,
            *reversed(longitude_and_latitude(*point)),
        )
        for station in stations
        for at, point in enumerate(station.points, start=1)
    ]
    return {
        "ModesAndLines.csv": _csv(("Mode", "Name"), lines),
        "Platforms.csv": _csv(
            ("UniqueId", "StationUniqueId", "PlatformNumber", "FriendlyName"),
            [(platform, station, "1", CANARY) for platform, station, _ in platforms],
        ),
        "PlatformServices.csv": _csv(
            ("PlatformUniqueId", "StopAreaNaptanCode", "Line", "DirectionTowards"),
            [(platform, station, line, CANARY) for platform, station, line in platforms],
        ),
        "StationPoints.csv": _csv(
            ("UniqueId", "StationUniqueId", "AreaName", "Lat", "Lon", "FriendlyName"),
            [(point, station, "Entr", lat, lon, CANARY) for point, station, lat, lon in points],
        ),
        # Never opened: it holds the names.
        "Stations.csv": _csv(
            ("UniqueId", "Name", "FareZones"),
            [(station.station_id, station.name, "2") for station in stations],
        ),
    }


def zipped(tables: dict[str, bytes]) -> bytes:
    held = io.BytesIO()
    with zipfile.ZipFile(held, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(tables):
            archive.writestr(zipfile.ZipInfo(name, WRITTEN), tables[name])
    return held.getvalue()


def stations_zip(stations: Sequence[MadeUpStation]) -> bytes:
    """The made-up file of stations, as the publisher zips it."""
    return zipped(tables_of(stations))


def stations_receipt(content: bytes, name: str = tfl_stations.FILE) -> Receipt:
    """The receipt of a made-up file of stations, as `fetch` writes one."""
    sha256 = hashlib.sha256(content).hexdigest()
    return Receipt(
        file_id=file_id_of(sha256),
        source_id=tfl_stations.SOURCE,
        use=Use.SCORING,
        publisher_file=name,
        url=f"https://files.made-up.example/{sha256[:8]}",
        sha256=sha256,
        bytes=len(content),
        retrieved_at=f"{RETRIEVED}T00:00:00Z",
        how=How.FETCHED,
        edition=f"retrieved {RETRIEVED}",
        data_period=Period(as_at=RETRIEVED),
    )


def given(stations: Sequence[MadeUpStation]) -> tuple[Receipt, bytes]:
    """The file and its receipt, to hand to a build beside its other files."""
    content = stations_zip(stations)
    return stations_receipt(content), content
