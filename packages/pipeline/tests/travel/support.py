"""What the tests of travel share: a town small enough to check by hand. Every name is made up.

The town is one street that runs east along the equator, in open sea. Its
stops bear the names of stations of the synthetic release, and stand a whole
number of metres apart, so that a test can say what a journey takes and why.

    Pellam Cross ---- 2,000 m ---- Tallowgate ---- 3,000 m ---- Wexmoor
         |
      1,000 m
         |
    Kindlewharf

The Amber line runs from Pellam Cross to Wexmoor, and the Birch line from
Kindlewharf to Pellam Cross. A point of the street stands every 100 metres.
"""

import io
from collections.abc import Sequence
from datetime import date

from burro_pipeline.travel.feed import WEEKDAYS, Feed, read_feed
from burro_pipeline.travel.write_feed import zipped

# Found nowhere else. A test puts it where a value is, and looks for it in what is said.
CANARY = "zqxcanary7431"
TUESDAY = date(2026, 9, 22)
SATURDAY = date(2026, 9, 26)
SUNDAY = date(2026, 9, 27)

Table = list[list[str]]
# One length for a degree, each way, as the made-up city is drawn.
METRES_PER_DEGREE = 111_320
Lonlat = tuple[float, float]
PELLAM, TALLOWGATE, WEXMOOR, KINDLEWHARF = "syn-s0009", "syn-s0011", "syn-s0012", "syn-s0007"
CORACLE = "syn-s0002"
# Metres east and north of Pellam Cross.
WHERE = {
    PELLAM: (0, 0),
    TALLOWGATE: (2000, 0),
    WEXMOOR: (5000, 0),
    KINDLEWHARF: (0, -1000),
    CORACLE: (300, 0),
}
NAMES = {
    PELLAM: "Pellam Cross",
    TALLOWGATE: "Tallowgate",
    WEXMOOR: "Wexmoor",
    KINDLEWHARF: "Kindlewharf",
    CORACLE: "Coracle Row",
}


def at(east: float, north: float = 0) -> Lonlat:
    """The point so many metres east and north of Pellam Cross."""
    return (east / METRES_PER_DEGREE, north / METRES_PER_DEGREE)


def clock(seconds: int) -> str:
    return f"{seconds // 3600:02d}:{seconds // 60 % 60:02d}:{seconds % 60:02d}"


def hours(hour: int, minute: int = 0, second: int = 0) -> int:
    return hour * 3600 + minute * 60 + second


def trips_of(
    route_id: str,
    stops: Sequence[str],
    ride: Sequence[int],
    first: int,
    last: int,
    every: int,
    service: str = "syn-weekdays",
) -> tuple[Table, Table]:
    """The rows of trips and of calls for one line, one way: a trip every so many seconds."""
    trips: Table = []
    calls: Table = []
    for count, leaves in enumerate(range(first, last + 1, every), start=1):
        trip_id = f"{route_id}-{service[4]}{count:03d}"
        trips.append([route_id, service, trip_id])
        time = leaves
        for place, stop_id in enumerate(stops):
            time += ride[place - 1] if place else 0
            calls.append([trip_id, clock(time), clock(time), stop_id, str(place + 1)])
    return trips, calls


def tables(every: int = 600, birch_ends_at: str = PELLAM) -> dict[str, Table]:
    """The timetable of the small town: the Amber line and the Birch line, each one way.

    The Amber line leaves Pellam Cross on the hour and every `every` seconds
    after, takes 5 minutes to Tallowgate and 20 to Wexmoor. The Birch line
    leaves Kindlewharf at 3 minutes past and every 10 minutes after, and
    takes 4 minutes to Pellam Cross. On a Saturday the Amber line alone runs,
    every half hour.

    A test of a change on foot ends the Birch line at Coracle Row, the second
    station of the centre, 300 metres along the street.
    """
    line = ("syn-r1", [PELLAM, TALLOWGATE, WEXMOOR], [300, 900], hours(5), hours(12))
    amber = trips_of(*line, every)
    birch = trips_of("syn-r2", [KINDLEWHARF, birch_ends_at], [240], hours(5, 3), hours(12), 600)
    saturday = trips_of(*line, 1800, "syn-saturdays")
    return {
        "stops.txt": [
            ["stop_id", "stop_name", "stop_lat", "stop_lon"],
            *(
                [
                    stop_id,
                    f"{NAMES[stop_id]} station",
                    f"{at(*where)[1]:.6f}",
                    f"{at(*where)[0]:.6f}",
                ]
                for stop_id, where in sorted(WHERE.items())
                if stop_id != CORACLE or birch_ends_at == CORACLE
            ),
        ],
        "routes.txt": [
            ["route_id", "route_long_name", "route_type"],
            ["syn-r1", "Amber line", "2"],
            ["syn-r2", "Birch line", "2"],
        ],
        "trips.txt": [["route_id", "service_id", "trip_id"], *amber[0], *birch[0], *saturday[0]],
        "stop_times.txt": [
            ["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"],
            *amber[1],
            *birch[1],
            *saturday[1],
        ],
        "calendar.txt": [
            ["service_id", *WEEKDAYS, "start_date", "end_date"],
            ["syn-weekdays", "1", "1", "1", "1", "1", "0", "0", "20260901", "20261218"],
            ["syn-saturdays", "0", "0", "0", "0", "0", "1", "0", "20260901", "20261218"],
        ],
    }


def zip_of(held: dict[str, Table]) -> io.BytesIO:
    return io.BytesIO(zipped(held))


def feed(every: int = 600, day: date = TUESDAY, birch_ends_at: str = PELLAM) -> Feed:
    return read_feed(zip_of(tables(every, birch_ends_at)), day)


def row_of(held: dict[str, Table], table: str, column: str, value: str) -> int:
    """The place in a table of the first row that holds a value in a column."""
    names = held[table][0]
    return next(n for n, row in enumerate(held[table]) if n and row[names.index(column)] == value)


def put(held: dict[str, Table], table: str, row: int, column: str, value: str) -> None:
    """Change one value of one row. Rows are counted as the table lists them, names first."""
    held[table][row][held[table][0].index(column)] = value
