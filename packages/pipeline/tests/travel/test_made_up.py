"""The made-up town: it is unmistakably made up, it reads nothing, and it is the same every time."""

import ast
import io
import itertools
import zipfile
from pathlib import Path

import pytest
from burro_core.ids import PlaceKind
from burro_pipeline.release.synthetic import build_synthetic
from burro_pipeline.release.synthetic.names import LINES
from burro_pipeline.travel import made_up
from burro_pipeline.travel.feed import FeedError, read_feed
from burro_pipeline.travel.made_up import DAY, HOLIDAY, RELEASE_ID, SUNDAY, town
from burro_pipeline.travel.plain import METRES_PER_DEGREE, SNAP_LIMIT, PlainRouter, metres_between

# The box the synthetic release is drawn in, which is open sea: section 2.9 of the contract.
LON, LAT = 0.20, 0.15


def tables_of(feed: bytes) -> dict[str, list[list[str]]]:
    with zipfile.ZipFile(io.BytesIO(feed)) as held:
        return {
            name: [line.split(",") for line in held.read(name).decode().splitlines()]
            for name in held.namelist()
        }


def test_the_same_seed_makes_the_same_town_byte_for_byte():
    first, second = town(), town()

    assert first == second
    assert first.feed == second.feed
    assert town(seed=7).feed != first.feed


def test_the_town_moves_nothing_of_the_synthetic_release():
    """It draws from a stream of its own, and the city it stands on is the committed one."""
    made = town()
    committed = build_synthetic()

    assert made.release.manifest.release_id == RELEASE_ID != committed.manifest.release_id
    assert made.release.travel_table == committed.travel_table
    assert made.release.places == committed.places
    assert made.release.features == committed.features


def test_every_name_of_the_timetable_is_one_the_synthetic_release_holds():
    made = town()
    held = tables_of(made.feed)
    stations = {p.name for p in made.release.places if p.kind is PlaceKind.STATION}

    stop_names = {row[1] for row in held["stops.txt"][1:]}
    line_names = {row[3] for row in held["routes.txt"][1:]}

    assert stop_names == {f"{name} station" for name in stations}
    assert line_names == {line.name for line in LINES}
    assert all("made up" in row[1] for row in held["agency.txt"][1:])
    assert all("made up" in row[0] for row in held["feed_info.txt"][1:])


def test_every_id_begins_syn_and_a_stop_bears_the_id_of_its_station():
    made = town()
    held = tables_of(made.feed)
    of_station = {row.name: row.station_id for row in made.release.station_rows}

    for table, column in (("stops.txt", 0), ("routes.txt", 0), ("trips.txt", 2), ("trips.txt", 1)):
        assert all(row[column].startswith("syn-") for row in held[table][1:]), table
    assert all(node.startswith("syn-k") for node in made.streets.nodes)
    assert all(home.point.point_id.startswith(f"{home.area_id}-") for home in made.homes)
    for stop_id, name, *_ in held["stops.txt"][1:]:
        station = name.removesuffix(" station")
        assert of_station.get(station, stop_id) == stop_id


def test_the_town_is_in_open_sea():
    made = town()
    points = [
        *(at for at in made.streets.nodes.values()),
        *(home.point.at for home in made.homes),
    ]
    stops = [(float(row[3]), float(row[2])) for row in tables_of(made.feed)["stops.txt"][1:]]

    # The streets reach a little past the city, and one road leads out to the airfield.
    assert all(abs(lon) <= LON and abs(lat) <= LAT for lon, lat in [*stops, *points])


def test_every_area_has_three_home_points_inside_it_each_with_a_count_of_homes():
    made = town()
    by_area: dict[str, list[int]] = {}
    for home in made.homes:
        by_area.setdefault(home.area_id, []).append(home.weight)

    assert set(by_area) == {area.area_id for area in made.release.neighbourhoods}
    assert all(len(weights) == 3 for weights in by_area.values())
    assert all(100 <= weight < 900 for weights in by_area.values() for weight in weights)
    assert len({home.point.at for home in made.homes}) == len(made.homes)


def test_every_point_a_journey_starts_or_ends_at_is_on_the_streets():
    made = town()
    nodes = list(made.streets.nodes.values())

    for at in [*(home.point.at for home in made.homes), *(end.at for end in made.destinations)]:
        assert min(metres_between(at, node) for node in nodes) <= SNAP_LIMIT


def test_the_river_is_crossed_at_a_bridge_and_the_streets_are_one_town():
    made = town()
    grid = [link for link in made.streets.links if link[2] == made_up.GRID_METRES]
    nodes = len(made.streets.nodes)
    router = PlainRouter(read_feed(io.BytesIO(made.feed), DAY), made.streets)

    # A grid with every link has two for each point, less those of its edges.
    assert 0 < 2 * nodes - len(grid) - 200 < 120
    # Every point of the streets can be walked to from any other.
    start = min(made.streets.nodes)
    assert len(router._spread(start)) == nodes  # pyright: ignore[reportPrivateUsage]


def test_the_timetable_runs_each_line_both_ways_at_its_headway():
    made = town()
    feed = read_feed(io.BytesIO(made.feed), DAY)
    names = {row[0]: row[1].removesuffix(" station") for row in tables_of(made.feed)["stops.txt"]}

    for number, line in enumerate(LINES, start=1):
        out = [
            trip
            for trip in feed.trips
            if trip.route_id == f"syn-r{number}" and names[trip.stops[0]] == line.stops[0]
        ]
        back = [trip for trip in feed.trips if trip.route_id == f"syn-r{number}"]
        gaps = {b.departs[0] - a.departs[0] for a, b in itertools.pairwise(out)}
        assert gaps == {60 * line.headway}, line.name
        assert len(back) == 2 * len(out)
        assert [names[stop] for stop in out[0].stops] == list(line.stops)


def test_nothing_runs_on_a_sunday():
    with pytest.raises(FeedError) as stopped:
        read_feed(io.BytesIO(town().feed), SUNDAY)

    assert stopped.value.rule == "calendar_covers_the_day"


def test_the_town_reads_nothing():
    """No file, no dataset, no network: so it has no gate to ask."""
    source = Path(made_up.__file__)
    tree = ast.parse(source.read_text(encoding="utf-8"))
    imported = {
        node.module if isinstance(node, ast.ImportFrom) else alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import | ast.ImportFrom)
        for alias in node.names
    }
    calls = {
        node.func.id if isinstance(node.func, ast.Name) else node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name | ast.Attribute)
    }

    assert imported <= {
        "math",
        "collections.abc",
        "dataclasses",
        "datetime",
        "itertools",
        "burro_core.ids",
        "burro_core.release",
        "burro_pipeline.release.synthetic.build",
        "burro_pipeline.release.synthetic.chart",
        "burro_pipeline.release.synthetic.journeys",
        "burro_pipeline.release.synthetic.names",
        "burro_pipeline.travel.engine",
        "burro_pipeline.travel.feed",
        "burro_pipeline.travel.plain",
        "burro_pipeline.travel.roll_up",
        "burro_pipeline.travel.write_feed",
    }
    assert not calls & {"open", "read_text", "read_bytes", "require", "getenv"}
    assert METRES_PER_DEGREE == 111_320


def test_the_timetable_of_the_made_up_town_keeps_every_rule():
    made = town()

    weekday = read_feed(io.BytesIO(made.feed), DAY)
    holiday = read_feed(io.BytesIO(made.feed), HOLIDAY)

    assert (weekday.counted.stops, weekday.counted.routes) == (16, 4)
    assert weekday.counted.trips == weekday.counted.running + holiday.counted.running
    # On the holiday the Saturday trips run, at twice the headway.
    assert 0 < holiday.counted.running < weekday.counted.running
    # Every call but the first and the last of a trip stands for the time of a dwell.
    trip = weekday.trips[0]
    assert all(
        leaves - arrives == 42
        for arrives, leaves in zip(trip.arrives[1:-1], trip.departs[1:-1], strict=True)
    )
