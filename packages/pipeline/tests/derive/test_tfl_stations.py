"""The reader of the station data of a transport authority, on a made-up zip.

Every station, line and point here is made up. The reader is held to what it
reads: four tables, the columns it names, and no name of a station.
"""

from pathlib import Path

import pytest
from burro_pipeline.derive import tfl_stations
from burro_pipeline.derive.tfl_stations import Station
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.inputs import Opened
from burro_pipeline.registry.model import Use

from ..cells.support import CANARY
from . import tfl_support
from .stops_support import at, inputs_of
from .tfl_support import LINES, MadeUpStation, stations_receipt, tables_of, zipped

PELLAM = MadeUpStation("910GPELLAMX", ("weaver",), (at(60, 150), at(50, 60)))
TALLOW = MadeUpStation("910GTALLOWG", ("elizabeth", "national-rail"), (at(250, 170),))
UNDER = MadeUpStation("940GZZLUTLG", ("central",), (at(350, 150),))
STATIONS = (PELLAM, TALLOW, UNDER)


def opened(folder: Path, content: bytes) -> Opened:
    inputs = inputs_of(folder, more=[(stations_receipt(content), content)])
    return tfl_stations.open_the_file(inputs, Use.SCORING)


def read(folder: Path, content: bytes) -> tuple[Station, ...]:
    return tfl_stations.read(opened(folder, content))


def test_a_mode_calls_at_a_station_where_a_line_of_it_calls_at_a_platform(tmp_path: Path):
    found = {s.station_id: s for s in read(tmp_path, tfl_support.stations_zip(STATIONS))}
    assert {station: sorted(found[station].modes) for station in found} == {
        "910GPELLAMX": ["overground"],
        "910GTALLOWG": ["elizabeth-line", "nationalRail"],
        "940GZZLUTLG": ["tube"],
    }
    assert found["910GTALLOWG"].is_served_by(tfl_stations.OF_A_RAILWAY)
    assert not found["940GZZLUTLG"].is_served_by(tfl_stations.OF_A_RAILWAY)


def test_the_points_of_a_station_are_put_on_the_national_grid(tmp_path: Path):
    """They are given as longitude and latitude, to six places, which is within a metre."""
    (pellam, _, _) = read(tmp_path, tfl_support.stations_zip(STATIONS))
    assert len(pellam.points) == 2
    for found, meant in zip(pellam.points, sorted(PELLAM.points), strict=True):
        assert found == pytest.approx(meant, abs=1.0)


def test_the_file_is_known_by_the_publishers_name_for_it_and_is_read_through_the_gate(
    tmp_path: Path,
):
    assert tfl_stations.is_the_file("tfl-stationdata-detailed.zip")
    assert not tfl_stations.is_the_file("tfl-stationdata-gtfs.zip")
    assert tfl_stations.SOURCE == "tfl-step-free-station-topology"
    with pytest.raises(LockError) as refused:
        tfl_stations.open_the_file(inputs_of(tmp_path), Use.SCORING)
    assert refused.value.rule == "input_has_one_receipt"
    content = tfl_support.stations_zip(STATIONS)
    inputs = inputs_of(tmp_path / "held", more=[(stations_receipt(content), content)])
    with pytest.raises(LockError) as refused:
        # The registry allows scoring and display, and no search for a journey's end.
        tfl_stations.open_the_file(inputs, Use.DESTINATION_SEARCH)
    assert refused.value.rule == "gate_refuses"


def test_no_name_is_read_and_the_table_of_names_is_never_opened(tmp_path: Path):
    content = tfl_support.stations_zip(STATIONS)
    assert CANARY.encode() in b"".join(tables_of(STATIONS).values())
    assert CANARY not in repr(read(tmp_path, content))
    # With the table of names gone, and those of lifts never there, it reads the same.
    tables = tables_of(STATIONS)
    del tables["Stations.csv"]
    without = zipped(tables)
    assert read(tmp_path / "without", without) == read(tmp_path / "with", content)


POINTS = "StationPoints.csv"
# A table as it should not be, by its name, with what the reader says of it. `None` is a
# table that is not there.
BROKEN: tuple[tuple[str, bytes | None, str], ...] = (
    ("PlatformServices.csv", None, "it does not hold the one file that is read"),
    (POINTS, b"UniqueId,StationUniqueId,Lat\r\nx,y,1\r\n", "a column is missing"),
    ("ModesAndLines.csv", b"Mode,Name\r\nhovercraft,weaver\r\n", "a mode is none the step knows"),
    (
        "ModesAndLines.csv",
        b"Mode,Name\r\noverground,weaver\r\n",
        "a service is of a line the file does not name",
    ),
    (
        "Platforms.csv",
        b"UniqueId,StationUniqueId\r\nx,y\r\n",
        "a service is at a platform the file does not name",
    ),
    (
        POINTS,
        b"StationUniqueId,Lat,Lon\r\n910GPELLAMX,91.0,0.1\r\n910GTALLOWG,51.5,0.1\r\n"
        b"940GZZLUTLG,51.5,0.1\r\n",
        "a point is no point",
    ),
    (POINTS, b"StationUniqueId,Lat,Lon\r\n910GPELLAMX,north,0.1\r\n", "a point is no point"),
    (POINTS, b"StationUniqueId,Lat,Lon\r\n910GPELLAMX,51.5,0.1\r\n", "a station has no point"),
)


@pytest.mark.parametrize(("table", "content", "why"), BROKEN)
def test_a_file_that_is_not_as_the_reader_was_written_to_read_stops_the_build(
    tmp_path: Path, table: str, content: bytes | None, why: str
):
    tables = tables_of(STATIONS)
    if content is None:
        del tables[table]
    else:
        tables[table] = content
    with pytest.raises(LockError, match=why) as refused:
        read(tmp_path, zipped(tables))
    assert refused.value.rule == "input_is_as_described"


def test_the_modes_are_the_publishers_seven():
    assert {mode for mode, _ in LINES} == tfl_stations.MODES
    assert {"overground", "elizabeth-line", "nationalRail"} == tfl_stations.OF_A_RAILWAY
