"""How near stops are, worked out from the files of stops and of stations as they were fetched.

Every other test of the four measures runs on made-up files. These read the
real ones, and are skipped where the store of fetched files is not. The store
is named by BURRO_STORE_FOLDER, and each file is read through its receipt in
`data/receipts/`.

They hold the counts of the files round London, how the two joined, the count
of areas with a figure, and three figures of each measure: London's lowest,
middle and highest. None is said of a named area or of a borough. Each was
worked out on 2026-09-24, from the files that were fetched that day.

Nothing is written to the store. A file is copied out of it to be read.
"""

import statistics
from collections import Counter
from pathlib import Path

import pytest
from burro_core.ids import FeatureId
from burro_pipeline.cells import centres, spine
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import connected, stops_file, tfl_stations
from burro_pipeline.derive.connected import (
    BUS,
    NATIONAL_RAIL,
    OVERGROUND,
    OVERGROUND_OR_ELIZABETH,
    RAIL,
    UNDERGROUND,
    Connected,
    Joined,
)
from burro_pipeline.derive.measures import says_what_core_says
from burro_pipeline.evidence.receipt import How, Period
from burro_pipeline.evidence.row import State
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

from .real_files import SKIPPED, STORE, real_inputs

pytestmark = SKIPPED
# The national file of stops and the file of stations, each by the id of its receipt.
STOPS, STATIONS = "f-7fbe1ec6aaff", "f-19c50772febd"


def listing() -> dict[str, tuple[int, int]]:
    """Every file of the store, with its size and when it was last written."""
    return {
        path.relative_to(STORE).as_posix(): (path.stat().st_size, path.stat().st_mtime_ns)
        for path in sorted(Path(STORE).rglob("*"))
        if path.is_file()
    }


@pytest.fixture(scope="module")
def before() -> dict[str, tuple[int, int]]:
    return listing()


@pytest.fixture(scope="module")
def real(tmp_path_factory: pytest.TempPathFactory, before: dict[str, tuple[int, int]]) -> Inputs:
    return real_inputs(tmp_path_factory.mktemp("real"))


@pytest.fixture(scope="module")
def found(real: Inputs) -> Spine:
    return spine.build(real)


@pytest.fixture(scope="module")
def made(real: Inputs, found: Spine) -> dict[FeatureId, Connected]:
    return {feature: connected.build(feature, real, found) for feature in connected.MEASURES}


def spread(one: Connected) -> tuple[float, float, float]:
    values = sorted(worked.value for worked in one.worked.values() if worked.value is not None)
    return values[0], statistics.median(values), values[-1]


def test_the_file_is_the_national_one_and_its_receipt_says_when_it_was_retrieved(real: Inputs):
    receipt = stops_file.open_the_national_file(real, Use.SCORING).receipt
    assert (receipt.file_id, receipt.publisher_file) == (STOPS, "Stops.csv")
    assert (receipt.how, receipt.edition) == (How.FETCHED, "retrieved 2026-09-24")
    assert receipt.data_period == Period(as_at="2026-09-24")


def test_round_london_it_holds_the_stations_and_the_ways_in_of_every_authority(
    real: Inputs, found: Spine, made: dict[FeatureId, Connected]
):
    """Read 25 kilometres wide of London's homes. No row near London names no grid."""
    assert made  # The file is read by then, within the box of the build.
    (read,) = connected._READ.values()  # pyright: ignore[reportPrivateUsage]
    kinds = Counter(
        (stop.type, stops_file.letters_of(stop.code) or "") for stop in read if stop.type != "BCT"
    )
    assert sum(1 for stop in read if stop.type == "BCT") == 46_320
    # Railway stations, whoever runs their trains: ways in, and the stations themselves.
    by_type = Counter(stop.type for stop in read)
    assert (by_type["RSE"], by_type["RLY"]) == (978, 649)
    # The Underground and the DLR: ways in, and the stations themselves.
    assert (kinds["TMU", "LU"], kinds["MET", "LU"]) == (516, 281)
    assert (kinds["TMU", "DL"], kinds["MET", "DL"]) == (77, 45)
    # The two stations that opened in 2021, whose codes hold letters of their own.
    assert (kinds["TMU", "BP"], kinds["MET", "BP"], kinds["TMU", "NE"], kinds["MET", "NE"]) == (
        1,
        1,
        1,
        1,
    )
    # Trams, and what counts as neither kind: the cable car and a miniature railway.
    assert (kinds["TMU", "CR"], kinds["MET", "CR"]) == (45, 39)
    assert (kinds["TMU", "AL"], kinds["MET", "AL"], kinds["MET", "RL"]) == (2, 2, 3)


@pytest.fixture(scope="module")
def joined(real: Inputs, found: Spine) -> Joined:
    points = centres.build(real, found)
    stops = connected.stops_round(real, [points[oa] for oa in sorted(points)])
    served = tfl_stations.open_the_file(real, Use.SCORING)
    return connected.join(stops, connected.stations_of(served), served)


def test_the_file_of_stations_says_which_modes_call_at_each_of_509(real: Inputs):
    served = tfl_stations.open_the_file(real, Use.SCORING)
    assert (served.file_id, served.receipt.publisher_file) == (STATIONS, tfl_stations.FILE)
    assert served.receipt.data_period == Period(as_at="2026-09-24")
    every = tfl_stations.read(served)
    assert len(every) == 509
    assert Counter(mode for station in every for mode in station.modes) == {
        "tube": 270,
        "nationalRail": 138,
        "overground": 112,
        "dlr": 45,
        "elizabeth-line": 41,
        "tram": 39,
        "cableCar": 2,
    }
    rail = connected.stations_of(served)
    assert len(rail) == 232
    assert sum(1 for one in rail if one.is_served_by(OVERGROUND_OR_ELIZABETH)) == 149
    assert sum(1 for one in rail if one.is_served_by(NATIONAL_RAIL)) == 138


def test_the_two_files_are_joined_by_where_a_station_stands(joined: Joined):
    """Two in five of the railway rows round London are of a station of the other file.

    All but two of its 232 stations are joined to: those two stand further
    from London than the national file was read.
    """
    assert Counter(stop.type for stop, _ in joined.rows) == {"RSE": 978, "RLY": 649}
    of_a_station = Counter(stop.type for stop, station in joined.rows if station is not None)
    assert of_a_station == {"RSE": 400, "RLY": 259}
    assert joined.stations == 230
    kinds = Counter(
        (
            station.is_served_by(OVERGROUND_OR_ELIZABETH),
            station.is_served_by(NATIONAL_RAIL),
        )
        for _, station in joined.rows
        if station is not None
    )
    assert kinds == {(True, True): 172, (True, False): 236, (False, True): 251}


def test_every_one_of_the_1002_areas_has_a_figure_for_each(
    made: dict[FeatureId, Connected], found: Spine
):
    for one in made.values():
        assert len(one.worked) == len(found.areas) == 1_002
        assert Counter(worked.state for worked in one.worked.values()) == {State.PRESENT: 1_002}
        assert len(one.of_oa) == len(found.cells) == 26_369


def test_the_lowest_the_middle_and_the_highest_of_london(made: dict[FeatureId, Connected]):
    found = {feature: (one.points, spread(one)) for feature, one in made.items()}
    assert found == {
        UNDERGROUND: (922, (170.0, 1_155.0, 17_420.0)),
        OVERGROUND: (407, (170.0, 1_625.0, 13_030.0)),
        RAIL: (1_470, (180.0, 990.0, 5_270.0)),
        BUS: (46_302, (2.2, 8.7, 22.9)),
    }


def test_two_areas_in_five_are_within_800_metres_of_the_underground_or_the_dlr(
    made: dict[FeatureId, Connected],
):
    near = {
        feature: sum(1 for w in made[feature].worked.values() if (w.value or 0) <= 800)
        for feature in (UNDERGROUND, OVERGROUND, RAIL)
    }
    assert near == {UNDERGROUND: 398, OVERGROUND: 248, RAIL: 394}
    # No home of London is further from a station than the file was read.
    assert max(made[UNDERGROUND].of_oa.values()) < 19_100 < connected.MARGIN


def test_each_row_of_the_catalogue_is_cores_and_says_when_the_file_was_retrieved(
    made: dict[FeatureId, Connected],
):
    for one in made.values():
        assert says_what_core_says(one.metric)
        assert one.metric.vintage == "2026-09-24"
        assert "retrieved on 2026-09-24" in one.metric.definition
        assert [r.file_id for r in one.files if r.source_id == connected.SOURCE] == [STOPS]
    for feature in (OVERGROUND, RAIL):
        cited = [r.file_id for r in made[feature].files if r.source_id == connected.STATIONS]
        assert cited == [STATIONS]
        assert connected.STATIONS in made[feature].metric.source_ids


def test_nothing_was_written_to_the_store(
    made: dict[FeatureId, Connected], before: dict[str, tuple[int, int]]
):
    assert made and listing() == before
