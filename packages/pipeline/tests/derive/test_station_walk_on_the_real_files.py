"""The nearest station, worked out from the files their publishers gave.

Every other test of the measure runs on made-up stops. These read the real
file, and are skipped where the store of fetched files is not. The store is
named by BURRO_STORE_FOLDER, and each file is read through its receipt in
`data/receipts/`.

They hold the counts of the file, the count of areas with a figure, and three
figures: London's lowest, middle and highest. None is said of a named area or
of a borough. Each was worked out on 2026-09-24, from the file a person saved
that day.

One name is held: the station the publisher's own guide takes for its example
of a station. The name of a station is the name of a place.

Nothing is written to the store. A file is copied out of it to be read.
"""

import math
import statistics
from collections import Counter
from pathlib import Path

import pytest
from burro_pipeline.cells import spine
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import station_walk, stops_file
from burro_pipeline.derive.measures import says_what_core_says
from burro_pipeline.derive.station_walk import Nearest
from burro_pipeline.derive.stops_file import Station, Stop
from burro_pipeline.evidence.receipt import How, Period
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

from .real_files import SKIPPED, STORE, real_inputs

pytestmark = SKIPPED
# The stops, the centres, the lookup, the outlines of LSOAs and the table of homes, by the
# ids of their receipts.
STOPS, CENTRES, LOOKUP, OUTLINES, HOMES = (
    "f-ed03193db0d8",
    "f-00e1d0532798",
    "f-49321b95f212",
    "f-9f549e33f46b",
    "f-af7b512615ea",
)
# The station the publisher's guide takes for its example, in its section 9.9.
EXAMPLE = "Bank"


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
def ways_in(real: Inputs) -> tuple[Stop, ...]:
    opened = stops_file.open_the_file(real, Use.SCORING)
    return stops_file.read(opened, stops_file.STATION_TYPES, names=True)


@pytest.fixture(scope="module")
def stations(ways_in: tuple[Stop, ...]) -> tuple[Station, ...]:
    return stops_file.stations_of(ways_in)


@pytest.fixture(scope="module")
def made(real: Inputs, found: Spine) -> Nearest:
    return station_walk.build(real, found)


# The file


def test_the_file_is_the_one_a_person_saved_and_its_receipt_says_so(real: Inputs):
    receipt = stops_file.open_the_file(real, Use.SCORING).receipt
    assert (receipt.file_id, receipt.publisher_file) == (STOPS, "490Stops.csv")
    assert (receipt.how, receipt.edition) == (How.BY_HAND, "saved 2026-09-24")
    assert receipt.data_period == Period(as_at="2026-09-24")


def test_it_holds_ways_in_of_two_kinds_and_one_of_them_is_not_active(ways_in: tuple[Stop, ...]):
    """550 rows are a way in to a railway station, and one of them is not active."""
    assert Counter(way.type for way in ways_in) == {"RSE": 549, "TMU": 642}
    assert all(way.code.startswith("4900") for way in ways_in)


def test_it_holds_the_stops_of_buses(real: Inputs):
    opened = stops_file.open_the_file(real, Use.SCORING)
    found = stops_file.read(opened, stops_file.BUS_TYPES)
    assert Counter(stop.type for stop in found) == {"BCT": 20_023, "BCS": 28}


# One station is many rows


def test_the_ways_in_gather_into_641_stations(stations: tuple[Station, ...]):
    assert Counter(station.type for station in stations) == {"RSE": 340, "TMU": 301}
    ways = Counter(len(station.ways_in) for station in stations)
    assert (ways[1], ways[2], max(ways)) == (328, 212, 13)


def test_no_name_is_two_stations_and_no_station_is_wider_than_512_metres(
    stations: tuple[Station, ...],
):
    """So the distance that tells two stations of one name apart decides nothing here."""
    assert len({(station.type, station.name) for station in stations}) == len(stations)
    assert round(max(station.wide for station in stations)) == 512 < stops_file.APART


def test_sixteen_names_are_a_station_of_each_kind(stations: tuple[Station, ...]):
    names = Counter(station.name for station in stations)
    assert Counter(names.values()) == {1: 609, 2: 16}


def test_six_pairs_of_names_of_one_kind_have_ways_in_within_100_metres(
    stations: tuple[Station, ...],
):
    """Each is two stations that stand side by side, and the file names them apart."""
    side_by_side = [
        (one.type, one.name, other.name)
        for one in stations
        for other in stations
        if one.type == other.type
        and one.name < other.name
        and any(math.dist(a.point, b.point) <= 100 for a in one.ways_in for b in other.ways_in)
    ]
    assert Counter(kind for kind, _, _ in side_by_side) == {"RSE": 3, "TMU": 3}


def test_the_letters_of_the_codes_split_the_second_kind_and_leave_six_stations_out(
    stations: tuple[Station, ...],
):
    """The guide defines no letters. They are counted as a hint, and no figure turns on them."""
    letters = Counter((station.type, station.letters) for station in stations)
    assert letters == {
        ("RSE", None): 339,
        ("RSE", "DL"): 1,
        ("TMU", "LU"): 215,
        ("TMU", "DL"): 41,
        ("TMU", "CR"): 37,
        ("TMU", "AL"): 2,
        ("TMU", "BP"): 1,
        ("TMU", "NE"): 1,
        ("TMU", None): 4,
    }


def test_the_station_the_guide_takes_for_its_example_is_in_the_file(
    stations: tuple[Station, ...],
):
    (found,) = [station for station in stations if station.name == EXAMPLE]
    assert (found.type, found.letters, len(found.ways_in)) == ("TMU", "LU", 13)


# The figure


def test_970_of_the_1002_areas_have_a_figure(made: Nearest, found: Spine):
    assert len(made.worked) == len(found.areas) == 1_002
    assert Counter(one.state for one in made.worked.values()) == {
        State.PRESENT: 905,
        State.PARTIAL: 65,
        State.BELOW_THRESHOLD: 25,
        State.SOURCE_GAP: 7,
    }
    assert made.stops == 1_191


def test_the_lowest_the_middle_and_the_highest_of_london(made: Nearest):
    values = sorted(one.value for one in made.worked.values() if one.value is not None)
    assert (values[0], statistics.median(values), values[-1]) == (170.0, 570.0, 2_800.0)
    assert len(set(values)) == 159


def test_the_distance_of_25375_output_areas_is_known(made: Nearest, found: Spine):
    assert (len(made.found_of_oa), len(made.of_oa)) == (26_369, 25_375)
    assert len(found.cells) == 26_369
    known = sorted(made.of_oa.values())
    assert (round(known[0]), round(statistics.median(known)), round(known[-1])) == (3, 564, 3_152)


# The edge of London


def test_the_edge_touches_97_areas_and_leaves_32_with_no_figure(made: Nearest, found: Spine):
    edge = made.edge
    assert (len(edge.output_areas), len(edge.areas), len(edge.without_a_figure)) == (994, 97, 32)
    assert sum(found.homes[oa] for oa in edge.output_areas) == 127_165
    without = {area for area, one in made.worked.items() if one.value is None}
    assert without == set(edge.without_a_figure)
    partial = {area for area, one in made.worked.items() if one.state is State.PARTIAL}
    assert partial <= set(edge.areas)


def test_every_area_the_edge_touches_is_in_an_outer_borough(made: Nearest, found: Spine):
    borough = {area.area_id: area.borough for area in found.areas}
    assert len({borough[area] for area in made.edge.areas}) == 14
    assert len({borough[area] for area in made.edge.without_a_figure}) == 13


# The evidence, and the row of the catalogue


def test_a_row_names_the_five_files_and_holds_the_figure(made: Nearest):
    ids = tuple(sorted((STOPS, CENTRES, LOOKUP, OUTLINES, HOMES)))
    assert tuple(sorted(receipt.file_id for receipt in made.files)) == ids
    assert all(row.inputs == ids for row in made.rows)
    assert [row.value for row in made.rows] == [
        made.worked[row.fact_id.split("/")[0]].value for row in made.rows
    ]
    evidence = Evidence(
        release_id="lon-2026-09-24-01",
        methods=station_walk.METHODS,
        receipts=made.files,
        rows=made.rows,
    )
    assert len(evidence.rows) == 1_002


def test_the_row_of_the_catalogue_is_cores_and_says_when_the_file_was_saved(made: Nearest):
    assert says_what_core_says(made.metric)
    assert (made.metric.unit, made.metric.vintage) == ("m", "2026-09-24")
    assert "saved on 2026-09-24" in made.metric.definition


def test_nothing_was_written_to_the_store(made: Nearest, before: dict[str, tuple[int, int]]):
    assert made.worked and listing() == before
