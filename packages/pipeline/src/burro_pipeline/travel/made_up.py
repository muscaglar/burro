"""The made-up town as a timetable, streets and homes. It describes no real place.

The synthetic release already holds a made-up city: its areas, its stations,
its four lines and the places a person may name. This module writes the same
city as the inputs the travel step takes, so that the step can be driven from
a timetable to a release with no publisher's file and no engine.

- The timetable is a feed in the open format, as a zip. Its stops are the
  stations of the city, its routes are the four lines of `names.LINES`, and
  each line runs both ways at its headway, every trip with its own times.
- The streets are a grid of points 250 metres apart, with a link between
  neighbours. The river is crossed at a bridge, about one in four of the
  links that would cross it. One road leads out of town to the airfield.
- The homes of each area are three points inside it, each with a count of
  homes.

It reads nothing: no file, no dataset, no network. Every name is one the
synthetic release already holds, every id begins `syn-`, and the map is in
open sea. It draws only from `Random(seed).random()`, from a stream of its
own, so that nothing of the synthetic release moves.
"""

import itertools
import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from burro_core.ids import PlaceKind
from burro_core.release import InMemoryRelease

from burro_pipeline.release.synthetic.build import BUILT_AT, GRITTY, SEED, build_synthetic
from burro_pipeline.release.synthetic.chart import Chart, Draw, Xy, draw_chart, lon_lat
from burro_pipeline.release.synthetic.journeys import RAIL_DWELL_MIN, RAIL_MIN_PER_KM
from burro_pipeline.release.synthetic.names import AREAS, LINES, OUT_OF_TOWN_KM
from burro_pipeline.travel.engine import Lonlat, Point
from burro_pipeline.travel.feed import WEEKDAYS as WEEK
from burro_pipeline.travel.plain import METRES_PER_DEGREE, Streets
from burro_pipeline.travel.roll_up import Home
from burro_pipeline.travel.write_feed import Table, zipped

# The release whose journeys are worked out from the timetable. It is built on demand, as
# the other way of gritty is, and is never committed.
RELEASE_ID = "syn-2026-09-24-07"
# The day that is modelled: a Tuesday the timetable covers.
DAY = date(2026, 9, 22)
# A Monday on which the weekday trips do not run and the Saturday trips do.
HOLIDAY = date(2026, 10, 26)
SUNDAY = date(2026, 9, 27)
COVERS = (date(2026, 9, 1), date(2026, 12, 18))
WEEKDAYS, SATURDAYS = "syn-weekdays", "syn-saturdays"
# The first and the last trip of a line leave its first stop at these seconds of the day.
FIRST_TRIP, LAST_TRIP = 5 * 3600, 11 * 3600 + 1800
GRID_METRES = 250
MARGIN_KM = 0.5
HOMES_TO_AN_AREA = 3
# A link that would cross the river is a bridge if it is one in this many.
ONE_BRIDGE_IN = 4


@dataclass(frozen=True)
class Town:
    """All that the travel step takes, for the made-up town."""

    # The made-up city, with the journeys it was first drawn with.
    release: InMemoryRelease
    # The timetable, as the zip a publisher would give.
    feed: bytes
    streets: Streets
    homes: tuple[Home, ...]
    destinations: tuple[Point, ...]
    day: date


def _clock(seconds: int) -> str:
    return f"{seconds // 3600:02d}:{seconds // 60 % 60:02d}:{seconds % 60:02d}"


def _day(day: date) -> str:
    return day.strftime("%Y%m%d")


def _km(a: Lonlat, b: Lonlat) -> float:
    east, north = (a[0] - b[0]) * METRES_PER_DEGREE, (a[1] - b[1]) * METRES_PER_DEGREE
    return math.sqrt(east * east + north * north) / 1000


def _stations(release: InMemoryRelease) -> dict[str, tuple[str, Lonlat]]:
    """Each station by name: its id, as the release numbers the stations, and where it is."""
    places = sorted(
        (place for place in release.places if place.kind is PlaceKind.STATION),
        key=lambda place: place.name,
    )
    return {
        place.name: (f"syn-s{number:04d}", place.centroid)
        for number, place in enumerate(places, start=1)
    }


def timetable(release: InMemoryRelease) -> dict[str, Table]:
    """The tables of the made-up timetable: four lines, each way, every trip with its times."""
    stations = _stations(release)
    stops: list[Sequence[str]] = [("stop_id", "stop_name", "stop_lat", "stop_lon")]
    stops += [
        (stop_id, f"{name} station", f"{at[1]:.6f}", f"{at[0]:.6f}")
        for name, (stop_id, at) in stations.items()
    ]
    routes: list[Sequence[str]] = [
        ("route_id", "agency_id", "route_short_name", "route_long_name", "route_type")
    ]
    trips: list[Sequence[str]] = [("route_id", "service_id", "trip_id")]
    calls: list[Sequence[str]] = [
        ("trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence")
    ]
    for number, line in enumerate(LINES, start=1):
        route_id = f"syn-r{number}"
        routes.append((route_id, "syn-a1", line.name.split()[0], line.name, "2"))
        for way, names in enumerate((line.stops, line.stops[::-1]), start=1):
            runs = [
                round(60 * RAIL_MIN_PER_KM * _km(stations[a][1], stations[b][1]))
                for a, b in itertools.pairwise(names)
            ]
            for service, every in ((WEEKDAYS, line.headway), (SATURDAYS, 2 * line.headway)):
                # Each line and each way leaves a little after the last, so that no two
                # trains of the town stand at one platform at one time.
                leaves = FIRST_TRIP + 60 * (number - 1) + 120 * (way - 1)
                for count, first in enumerate(range(leaves, LAST_TRIP + 1, 60 * every), 1):
                    trip_id = f"{route_id}-{way}-{service[4]}{count:03d}"
                    trips.append((route_id, service, trip_id))
                    calls += _calls(trip_id, [stations[name][0] for name in names], runs, first)
    calendar: list[Sequence[str]] = [
        ("service_id", *WEEK, "start_date", "end_date"),
        (WEEKDAYS, "1", "1", "1", "1", "1", "0", "0", *map(_day, COVERS)),
        (SATURDAYS, "0", "0", "0", "0", "0", "1", "0", *map(_day, COVERS)),
    ]
    return {
        "agency.txt": [
            ("agency_id", "agency_name", "agency_timezone"),
            ("syn-a1", "Quillhaven Transit (made up)", "Etc/UTC"),
        ],
        "calendar.txt": calendar,
        "calendar_dates.txt": [
            ("service_id", "date", "exception_type"),
            (WEEKDAYS, _day(HOLIDAY), "2"),
            (SATURDAYS, _day(HOLIDAY), "1"),
        ],
        "feed_info.txt": [
            ("feed_publisher_name", "feed_lang", "feed_start_date", "feed_end_date"),
            ("Burro (made up)", "en", *map(_day, COVERS)),
        ],
        "routes.txt": routes,
        "stop_times.txt": calls,
        "stops.txt": stops,
        "trips.txt": trips,
    }


def _calls(
    trip_id: str, stops: Sequence[str], runs: Sequence[int], first: int
) -> list[Sequence[str]]:
    """The calls of one trip: it stands at each stop between its ends for the time of a dwell."""
    dwell = round(60 * RAIL_DWELL_MIN)
    found: list[Sequence[str]] = []
    arrives = leaves = first
    for place, stop_id in enumerate(stops):
        if place:
            arrives = leaves + runs[place - 1]
            leaves = arrives if place == len(stops) - 1 else arrives + dwell
        found.append((trip_id, _clock(arrives), _clock(leaves), stop_id, str(place + 1)))
    return found


def _crosses(a: Xy, b: Xy, c: Xy, d: Xy) -> bool:
    """Whether the stretch from a to b crosses the stretch from c to d."""

    def side(p: Xy, q: Xy, r: Xy) -> float:
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    return (side(a, b, c) > 0) != (side(a, b, d) > 0) and (side(c, d, a) > 0) != (side(c, d, b) > 0)


def streets(chart: Chart) -> Streets:
    """The streets of the made-up town: a grid, the bridges, and the road to the airfield."""
    xs = [point[0] for point in chart.points.values()]
    ys = [point[1] for point in chart.points.values()]
    step = GRID_METRES / 1000
    west, south = min(xs) - MARGIN_KM, min(ys) - MARGIN_KM
    columns = int((max(xs) + MARGIN_KM - west) / step) + 2
    rows = int((max(ys) + MARGIN_KM - south) / step) + 2
    at = {
        (row, col): (west + col * step, south + row * step)
        for row in range(rows)
        for col in range(columns)
    }
    ids = {cell: f"syn-k{number:05d}" for number, cell in enumerate(sorted(at), start=1)}
    river = chart.river()
    banks = list(itertools.pairwise(river))

    links: list[tuple[str, str, int]] = []
    crossings = 0
    for row, col in sorted(at):
        for to in ((row, col + 1), (row + 1, col)):
            if to not in at:
                continue
            if any(_crosses(at[row, col], at[to], a, b) for a, b in banks):
                crossings += 1
                if crossings % ONE_BRIDGE_IN != 1:
                    continue
            links.append((ids[row, col], ids[to], GRID_METRES))

    # The road out of town, from the corner of the grid to the airfield.
    nodes = {ids[cell]: lon_lat(point) for cell, point in at.items()}
    corner = at[rows - 1, columns - 1]
    east, north = OUT_OF_TOWN_KM[0] - corner[0], OUT_OF_TOWN_KM[1] - corner[1]
    stretches = int(math.sqrt(east * east + north * north) / step) + 1
    last = ids[rows - 1, columns - 1]
    for count in range(1, stretches + 1):
        node = f"syn-k{len(at) + count:05d}"
        point = (corner[0] + east * count / stretches, corner[1] + north * count / stretches)
        nodes[node] = lon_lat(point)
        links.append((last, node, _whole_metres(nodes[last], nodes[node])))
        last = node
    return Streets(nodes=nodes, links=tuple(sorted(links)))


def _whole_metres(a: Lonlat, b: Lonlat) -> int:
    return max(1, int(1000 * _km(a, b) + 0.5))


def homes(release: InMemoryRelease, chart: Chart, draw: Draw) -> tuple[Home, ...]:
    """Three points inside each area, each with a count of homes."""
    cells = {plan.name: (plan.row, plan.col) for plan in AREAS}
    found: list[Home] = []
    for area in release.neighbourhoods:
        for letter in "abc"[:HOMES_TO_AN_AREA]:
            point = chart.inside(cells[area.name], draw.between(0.2, 0.8), draw.between(0.2, 0.8))
            found.append(
                Home(
                    point=Point(f"{area.area_id}-{letter}", lon_lat(point)),
                    area_id=area.area_id,
                    weight=int(draw.between(100, 900)),
                )
            )
    return tuple(found)


def town(seed: int = SEED, release_id: str = RELEASE_ID, built_at: str = BUILT_AT) -> Town:
    """The made-up town. The same three inputs give the same town, byte for byte."""
    release = build_synthetic(seed, release_id, built_at, GRITTY)
    # The chart is the first thing the city draws, so the same seed draws the same chart.
    chart = draw_chart(Draw(seed))
    return Town(
        release=release,
        feed=zipped(timetable(release)),
        streets=streets(chart),
        # A stream of its own: the city draws from `seed` and from `seed + 1`.
        homes=homes(release, chart, Draw(seed + 2)),
        destinations=tuple(Point(end.destination_id, end.centroid) for end in release.destinations),
        day=DAY,
    )
