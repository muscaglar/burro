"""How near stops are: three parts of Well connected and the stops of buses, from the files
of stops and of stations.

The stops come from the Department for Transport's national file, which
`stops_file.py` reads. Which trains call at a railway station comes from the
station data of Transport for London, which `tfl_stations.py` reads. Where
homes are comes from the centres of output areas, which `cells/centres.py`
reads.

| Measure | What is measured |
|---|---|
| `underground_proximity` | How far the nearest station of the Underground or the DLR is |
| `overground_proximity` | How far the nearest station of the Overground or the Elizabeth line is |
| `rail_proximity` | How far the nearest National Rail station or tram stop is |
| `bus_stops_nearby` | How many stops of a bus stand within 400 metres |

The fourth part of Well connected is how many routes of a bus stop near, which
`bus_routes.py` works out from another file. The stops of buses are shown, and
no area is ranked on them: a stop on each side of a road is two stops, and a
stop says nothing of how many buses call at it.

**Each counts how near stops are, and nothing more.** No timetable is held. So
no figure says how often anything runs, where it goes, or how long a journey
takes. A station where one train calls an hour counts as one where thirty do.

**Each is a straight line, and not a walk.** No network of streets is built. So
the name of each measure says a straight line, as core names it. Do not name
one a walk while it is a straight line.

**Why the national file.** The file of London holds the ways in to a station
and no station, and holds nothing past London's edge. One station in eight of
the Underground and the DLR has no way in of its own in either file: where it
shares a building with a railway station, its way in is the railway's. So a
distance is measured to the nearest point the file gives for a station of the
kind: a way in, or the station itself. And the file holds the stops of every
authority round London, so a home at London's edge is measured to a stop
outside it where that is nearest, and no home is left out.

**What says which kind a stop is.** The type of a row, and two letters that the
code of most rows holds after `ZZ`. The publisher's guide names the types and
defines no letters, so the letters are what they were seen to stand for in the
file as it was fetched on 2026-09-24.

| Kind | Rows that count |
|---|---|
| The Underground or the DLR | `TMU` or `MET`, with the letters `LU`, `DL`, `BP` or `NE` |
| A railway station | `RSE` or `RLY`, whatever its code |
| A tram stop | `TMU` or `MET`, with the letters `CR` |
| A stop of a bus | `BCT`: a stop on a street |

`BP` and `NE` are the two stations of the Underground that opened in 2021,
whose codes hold letters of their own. The two ends of the cable car and a
miniature railway in a park hold letters of their own and count as none. A bay
of a bus station is not counted: it is one stand of several in one place. A
stretch of road where a bus stops on request is a row of `BCT`, and counts as
a stop.

**Which trains call at a railway station.** The national file does not say: a
railway station is one kind in it, whoever runs its trains. The station data of
Transport for London names the modes that call at each station it serves. The
two files are joined by where a station stands, and by no code: a row of the
national file that is a railway station, or a way in to one, is of the station
of the other file whose nearest point is no further off than 200 metres, and
is of none where none is that near. On the files of 2026-09-24 the nearest
railway station that did not join stood 375 metres from a station of the other
file, and the furthest that did stood under 200.

| A row of the national file is joined to | It counts as |
|---|---|
| A station where the Overground or the Elizabeth line calls | One of theirs |
| A station where National Rail calls | National Rail |
| A station where both call | Both |
| No station | National Rail: a railway station the other file does not hold |

So a station at which no more than the Overground or the Elizabeth line calls
is no National Rail station here. That a station is in neither list of the
other file says nothing of it: the file holds the stations its publisher
serves.

How a figure is made:

1. The national file is read within a box round the homes of the build, 25
   kilometres wide of them. The step stops if any home is further than that
   from the nearest stop of a kind, so that no stop outside the box could be
   nearer.
2. For each output area, the distance from its centre to the nearest point
   that counts, or the stops of a bus within 400 metres of it.
3. A distance is the median over the area's homes, to the nearest 10 metres.
   A count is the mean over the area's homes, to one decimal place.

Nothing is filled in. An output area with no centre adds nothing, and the
coverage of its area falls by its homes.

**A count of stops follows how built up a place is.** It says that buses stop
near, and not that they are good. So it is shown, and is never ranked on.
"""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from burro_core.catalogue import RANKED_AS
from burro_core.facts import fact_id
from burro_core.ids import FactKind, FeatureId, NativeResolution
from burro_core.release import Metric

from burro_pipeline.cells import centres
from burro_pipeline.cells.centres import Point
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import (
    park_proximity,
    school_primary_nearby,
    stops_file,
    tfl_stations,
)
from burro_pipeline.derive.catalogue_row import catalogue_row
from burro_pipeline.derive.methods import Worked, row_of
from burro_pipeline.derive.station_shapes import (
    how_many_within,
    nearest_within,
    to_the_nearest_point,
)
from burro_pipeline.derive.stops_file import Box, Stop
from burro_pipeline.derive.tfl_stations import Station
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind, Method
from burro_pipeline.evidence.receipt import Geography, Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

UNDERGROUND, OVERGROUND, RAIL, BUS = (
    FeatureId.UNDERGROUND_PROXIMITY,
    FeatureId.OVERGROUND_PROXIMITY,
    FeatureId.RAIL_PROXIMITY,
    FeatureId.BUS_STOPS_NEARBY,
)
SOURCE = stops_file.SOURCE
STATIONS = tfl_stations.SOURCE
PUBLISHER, PRODUCT = stops_file.PUBLISHER, stops_file.PRODUCT
# The types of row that are a way in to a station or the station itself, of each kind.
OF_A_METRO = (stops_file.METRO, stops_file.METRO_STATION)
OF_A_RAILWAY = (stops_file.RAIL, stops_file.RAILWAY_STATION)
# The letters a code holds after `ZZ`, as they were seen to stand in the file that was
# fetched on 2026-09-24. The guide defines none of them. The last two of the first are the
# stations of the Underground that opened in 2021, whose codes hold letters of their own.
UNDERGROUND_OR_DLR = ("LU", "DL", "BP", "NE")
TRAM = ("CR",)
# Every type that is read.
TYPES = (*OF_A_METRO, *OF_A_RAILWAY, stops_file.ON_STREET)
# The modes of the other file that make a station one of the Overground or the Elizabeth
# line, and the mode that makes it one of National Rail.
OVERGROUND_OR_ELIZABETH = (tfl_stations.OVERGROUND, tfl_stations.ELIZABETH)
NATIONAL_RAIL = (tfl_stations.NATIONAL_RAIL,)
# A row of the national file is of a station of the other file that stands no further off
# than this many metres.
JOINED_WITHIN = 200
# A stop of a bus is within reach of a home within this many metres, in a straight line.
REACH = 400
# The file is read this far from the homes of the build, in metres, and no home may stand
# further than this from the nearest stop of a kind.
MARGIN = 25_000
# What the rows of the file are keyed by, as the parser finds them.
KEYED_BY = Geography.POINT
CENSUS = 2021

# The arithmetic of a distance is the nearest park's. It is held once.
NEAREST: Method = park_proximity.STRAIGHT_LINE
WITHIN = Method(
    derivation_id=f"points_within_{REACH}m_by_homes@1",
    sentence=f"The number of the points that count within {REACH} metres, in a straight line, "
    "of the point where the homes of each census output area are taken to stand, added up over "
    "the area's homes at the census and divided by those homes, and not given where under 50 in "
    "100 of the area's homes are in an output area that has such a point.",
    kind=Kind.MEASURED,
    parameters={"metres": REACH, "enough_in_100": 50},
    code="burro_pipeline.derive.connected",
)

_TO_A_POINT = (
    "The distance in a straight line, in metres, from the point the statistics office gives as "
    "the centre of each census output area to the nearest point that {publisher} gives in "
    "{product} for {what}, as the file was retrieved on {day}, as the median over the area's "
    "homes at the census of {census} and given to the nearest {nearest} metres with a half "
    "taken upward: a point is a way in to a station or the station itself, whichever is "
    "nearer, {kinds}, a stop past the edge of London counts where it is nearest, and it is "
    "measured across whatever lies between and not along any street or path, so the walk is "
    "longer, and it says nothing of how often a train runs or of where it goes."
)
_BY_THE_OTHER_FILE = (
    "which trains call at a railway station is read from the station data of {stations}, as "
    "it was retrieved on {stations_day}, joined to the station by where it stands, within "
    "{joined} metres"
)
_STRAIGHT = (
    "This is a straight line from where the homes of each small census area are taken to stand, "
    "and not a walk, so a railway, a river or a main road in between makes the real walk longer."
)
_NO_TIMETABLE = (
    "It counts how near a stop is, and not how often anything runs, where it goes or how long "
    "a journey takes: no timetable is held."
)
_JOINED_BY_PLACE = (
    "Which trains call at a station is as Transport for London gives it for the stations it "
    "serves, joined to the station by where it stands. A station that did not join is "
    "counted as National Rail."
)


@dataclass(frozen=True)
class Of:
    """One of the measures: what it is called, and how it is worked out."""

    feature: FeatureId
    # What a person reads beside the figure. It is core's name for the measure too.
    label: str
    method: Method
    # Whether the file of Transport for London is read for it.
    joined: bool
    # The sentence a methods page prints, with gaps for the day and the rest.
    definition: str
    # What the product shows beside the figure.
    cannot_see: tuple[str, ...]


def _letters(stop: Stop) -> str:
    return stops_file.letters_of(stop.code) or ""


def is_underground_or_dlr(stop: Stop) -> bool:
    """Whether a row is a way in to a station of the Underground or the DLR, or the station."""
    return stop.type in OF_A_METRO and _letters(stop) in UNDERGROUND_OR_DLR


def is_a_railway_station(stop: Stop) -> bool:
    """Whether a row is a way in to a railway station, or the station, whoever runs its trains."""
    return stop.type in OF_A_RAILWAY


def is_a_tram_stop(stop: Stop) -> bool:
    """Whether a row is a way in to a tram stop, or the stop."""
    return stop.type in OF_A_METRO and _letters(stop) in TRAM


def is_a_bus_stop(stop: Stop) -> bool:
    """Whether a row is a stop of a bus on a street."""
    return stop.type == stops_file.ON_STREET


MEASURES: Mapping[FeatureId, Of] = {
    UNDERGROUND: Of(
        UNDERGROUND,
        "Straight-line distance to the nearest Underground or DLR station",
        NEAREST,
        False,
        _TO_A_POINT.replace("{what}", "a station of the Underground or the DLR").replace(
            "{kinds}",
            "a station is of the Underground or the DLR by the letters its code holds, which "
            "the publisher's guide does not define",
        ),
        (
            _STRAIGHT,
            _NO_TIMETABLE,
            "Which station is the Underground's or the DLR's is read from letters in its code "
            "that the publisher does not define, so one whose code holds other letters is "
            "missed, and neither end of the cable car counts.",
        ),
    ),
    OVERGROUND: Of(
        OVERGROUND,
        "Straight-line distance to the nearest Overground or Elizabeth line station",
        NEAREST,
        True,
        _TO_A_POINT.replace(
            "{what}", "a railway station at which the Overground or the Elizabeth line calls"
        ).replace("{kinds}", _BY_THE_OTHER_FILE),
        (_STRAIGHT, _NO_TIMETABLE, _JOINED_BY_PLACE),
    ),
    RAIL: Of(
        RAIL,
        "Straight-line distance to the nearest National Rail station or tram stop",
        NEAREST,
        True,
        _TO_A_POINT.replace(
            "{what}", "a railway station at which National Rail calls, or a tram stop"
        ).replace(
            "{kinds}",
            _BY_THE_OTHER_FILE + ", a railway station at which no more than the Overground or "
            "the Elizabeth line calls is not counted, and one that the other file does not "
            "hold is",
        ),
        (_STRAIGHT, _NO_TIMETABLE, _JOINED_BY_PLACE),
    ),
    BUS: Of(
        BUS,
        f"Bus stops within {REACH} m of home, in a straight line",
        WITHIN,
        False,
        "The number of stops of a bus or a coach on a street that {publisher} gives in {product} "
        "as active, as the file was retrieved on {day}, within {reach} metres, in a straight "
        "line, of where homes stand: each home is placed at the point the statistics office "
        "gives as the centre of its census output area, homes are counted as they stood at the "
        "census of {census}, a stop past the edge of London counts where it is within the "
        "distance, and the figure is the mean over the area's homes, given to 1 decimal place "
        "with a half taken upward, so it is measured across whatever lies between and not along "
        "any street, a stop on each side of a road is two stops, a bay of a bus station is not "
        "counted, and it says nothing of how many buses call at a stop or of where they go.",
        (
            "This counts stops within a straight line of where the homes of each small census "
            "area are taken to stand, and not within a walk.",
            "It counts stops, and not buses: it cannot see how many routes call at a stop, how "
            "often, or where they go. A stop on each side of a road is two stops.",
            "A count of stops follows how built up a place is.",
        ),
    ),
}
METHODS: Mapping[FeatureId, tuple[Method, ...]] = {
    feature: (of.method,) for feature, of in MEASURES.items()
}


@dataclass(frozen=True)
class Stops:
    """The stops of the national file that stand round the homes of a build."""

    stops: tuple[Stop, ...]
    # The day the file was retrieved, as its receipt gives it.
    day: str
    file_id: str


@dataclass(frozen=True)
class Joined:
    """The railway rows of the national file, each with the station of the other file it is of."""

    # Each row that is a railway station or a way in to one, with its station, or none.
    rows: tuple[tuple[Stop, Station | None], ...]
    # The day the file of stations was retrieved, as its receipt gives it.
    day: str
    file_id: str

    @property
    def stations(self) -> int:
        """How many stations of the other file a row joined to."""
        return len({station.station_id for _, station in self.rows if station is not None})


@dataclass(frozen=True)
class Connected:
    """One measure for every area of the spine, with what stands behind it."""

    # The figure of each area, by its id. An area with no figure is here too, with its state.
    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    metric: Metric
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    geography: Geography
    # How many points of the file count, and the figure of each output area that has a centre.
    points: int
    of_oa: Mapping[str, float]


def is_the_file(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the file these measures read."""
    return stops_file.is_the_national_file(name)


def box_round(points: Sequence[Point], margin: float = MARGIN) -> Box:
    """The box the file is read within: round the homes of the build, and so much wider."""
    across, up = [point[0] for point in points], [point[1] for point in points]
    return (min(across) - margin, min(up) - margin, max(across) + margin, max(up) + margin)


# What was read of a file is kept for the next measure of the same build that asks. A file is
# known by its hash, and what is read of the national file by the box it was read within.
_READ: dict[tuple[str, Box], tuple[Stop, ...]] = {}
_STATIONS: dict[str, tuple[Station, ...]] = {}


def stops_round(inputs: Inputs, points: Sequence[Point], *, edition: str | None = None) -> Stops:
    """The stops of the national file round the homes of a build. The gate is asked first."""
    opened = stops_file.open_the_national_file(inputs, Use.SCORING, edition=edition)
    key = (opened.receipt.sha256, box_round(points))
    if key not in _READ:
        _READ.clear()
        _READ[key] = stops_file.read(opened, TYPES, within=key[1])
    return Stops(_READ[key], opened.receipt.data_period.days()[1], opened.file_id)


def stations_of(opened: Opened) -> tuple[Station, ...]:
    """The stations of the other file at which a train of a railway calls."""
    key = opened.receipt.sha256
    if key not in _STATIONS:
        _STATIONS.clear()
        _STATIONS[key] = tuple(
            station
            for station in tfl_stations.read(opened)
            if station.is_served_by(tfl_stations.OF_A_RAILWAY)
        )
    return _STATIONS[key]


def join(stops: Stops, stations: Sequence[Station], opened: Opened) -> Joined:
    """Each railway row of the national file, with the station of the other file it is of.

    A row is of the station whose nearest point is nearest to it, where that
    is no further off than `JOINED_WITHIN`, and is of none where none is.
    """
    rows = [stop for stop in stops.stops if is_a_railway_station(stop)]
    of = [(station, point) for station in stations for point in station.points]
    nearest = nearest_within([row.point for row in rows], [point for _, point in of], JOINED_WITHIN)
    return Joined(
        tuple(
            (row, None if at is None else of[at][0]) for row, at in zip(rows, nearest, strict=True)
        ),
        opened.receipt.data_period.days()[1],
        opened.file_id,
    )


def points_of(feature: FeatureId, stops: Stops, joined: Joined | None) -> tuple[Point, ...]:
    """The point of every row that counts for a measure, in order. Two rows on one spot are two."""
    if feature is UNDERGROUND:
        return tuple(sorted(stop.point for stop in stops.stops if is_underground_or_dlr(stop)))
    if feature is BUS:
        return tuple(sorted(stop.point for stop in stops.stops if is_a_bus_stop(stop)))
    if joined is None:
        raise ValueError(f"{feature} is worked out from the file of stations too")
    if feature is OVERGROUND:
        return tuple(
            sorted(
                stop.point
                for stop, station in joined.rows
                if station is not None and station.is_served_by(OVERGROUND_OR_ELIZABETH)
            )
        )
    # National Rail: a railway station that the other file does not hold, or one at which
    # it says National Rail calls. And the trams, which the national file tells by itself.
    return tuple(
        sorted(
            [
                stop.point
                for stop, station in joined.rows
                if station is None or station.is_served_by(NATIONAL_RAIL)
            ]
            + [stop.point for stop in stops.stops if is_a_tram_stop(stop)]
        )
    )


def to_the_nearest(
    file_id: str, among: Sequence[Point], points: Mapping[str, Point]
) -> dict[str, float]:
    """The distance from each output area that has a centre to the nearest point that counts.

    It stops where a home stands further from the nearest than the file was
    read: a nearer stop could then lie outside the box.
    """
    ordered = sorted(points)
    far = to_the_nearest_point([points[oa] for oa in ordered], sorted(set(among)))
    if any(distance > MARGIN for distance in far):
        raise LockError(
            "input_is_as_described", file_id, "its stops do not reach the homes of the build"
        )
    return dict(zip(ordered, far, strict=True))


def within_reach(among: Sequence[Point], points: Mapping[str, Point]) -> dict[str, float]:
    """The stops that count within reach of each output area that has a centre."""
    ordered = sorted(points)
    found = how_many_within([points[oa] for oa in ordered], among, REACH)
    return {oa: float(count) for oa, count in zip(ordered, found, strict=True)}


def definition_of(of: Of, day: str, stations_day: str | None = None) -> str:
    """The sentence a methods page prints for a measure."""
    return of.definition.format(
        publisher=PUBLISHER,
        product=PRODUCT,
        day=day,
        census=CENSUS,
        nearest=park_proximity.NEAREST,
        reach=REACH,
        stations=tfl_stations.PUBLISHER,
        stations_day=stations_day,
        joined=JOINED_WITHIN,
    )


def metric_of(of: Of, files: Sequence[Receipt], day: str, stations_day: str | None) -> Metric:
    """The row of the catalogue: the name, the unit, the period and every source.

    Core decides the unit and which way is more. The name is the one the
    figure supports, which is core's too. It is measured from points, and on
    no network. Its period is the later of the days its files are of.
    """
    return catalogue_row(
        of.feature,
        method=of.method,
        label=of.label,
        native_resolution=NativeResolution.POINT,
        source_ids={receipt.source_id for receipt in files},
        vintage=max(day, stations_day or day),
        definition=definition_of(of, day, stations_day),
        # The stops of buses are shown, and a wish for buses is ranked on the routes.
        rankable=of.feature not in RANKED_AS,
    )


def build(
    feature: FeatureId, inputs: Inputs, found: Spine, *, edition: str | None = None
) -> Connected:
    """One measure for every area, and its evidence, from the files of the build.

    The gate is asked about each file before it is read. `found` is the spine
    of the same build. A row of evidence names the file of stops, the file of
    stations where the measure reads it, the centres, the lookup and the
    table of homes.
    """
    if feature not in MEASURES:
        raise ValueError(f"{feature} is no measure of how near stops are")
    of = MEASURES[feature]
    placed = inputs.open(centres.CENTRES, Use.SCORING, edition=centres.CENTRES_EDITION)
    # Whether the file of stations is held is asked before the national file is read: a
    # measure that cannot be worked out reads nothing.
    served = tfl_stations.open_the_file(inputs, Use.SCORING) if of.joined else None
    points = centres.centres_of(placed, found)
    if not points:
        raise LockError("input_is_as_described", placed.file_id, "it holds no centre of the build")
    stops = stops_round(inputs, [points[oa] for oa in sorted(points)], edition=edition)
    joined = None if served is None else join(stops, stations_of(served), served)
    counted = points_of(feature, stops, joined)
    if not counted:
        raise LockError("input_is_as_described", stops.file_id, "it holds no stop that counts")
    if of.method is NEAREST:
        of_oa = to_the_nearest(stops.file_id, counted, points)
        worked = park_proximity.figures(of_oa, found)
    else:
        of_oa = within_reach(counted, points)
        worked = school_primary_nearby.figures(
            {oa: int(count) for oa, count in of_oa.items()}, found.weights
        )
    handed = {one.file_id: one.receipt for one in inputs.opened}
    read = {stops.file_id, placed.file_id, *([] if joined is None else [joined.file_id])}
    behind = sorted({*read, *found.inputs})
    if not all(file_id in handed for file_id in behind):
        raise ValueError("the spine is made from files of this build")
    files = tuple(handed[file_id] for file_id in behind)
    rows = tuple(
        row_of(fact_id(area, FactKind.FEATURE, feature), worked[area], of.method, files)
        for area in sorted(worked)
    )
    return Connected(
        worked=worked,
        rows=rows,
        metric=metric_of(of, files, stops.day, None if joined is None else joined.day),
        files=files,
        geography=KEYED_BY,
        points=len(set(counted)),
        of_oa=of_oa,
    )


def builder(feature: FeatureId) -> Callable[[Inputs, Spine], Connected]:
    """One measure, called as the list of the measures of a build calls each."""
    if feature not in MEASURES:
        raise ValueError(f"{feature} is no measure of how near stops are")
    return lambda inputs, found: build(feature, inputs, found)
