"""Builds the synthetic release: a made-up city, drawn the same way every time.

There is no `Registry.require` in this package, and that is on purpose. The
licence gate stands in front of data that is read from somewhere. The generator
reads nothing: no file, no dataset, no network. Every figure is worked out from
the plan in `names.py` and a seeded random source, and the only source the
release cites is the reserved id `synthetic`, which `write_release` allows for
a synthetic release and for nothing else.

The figures are shaped so that features go together the way a city's would:
nearer the centre is denser, noisier, dearer and a shorter journey. But no two
vibes go together, or a person could not tell what one adds to another: the
plan in `names.py` says where an area is not what its place on the map would
make it. That is for demos and tests only. It is a claim about nothing.
"""

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from burro_core.catalogue import (
    BANDS,
    CATALOGUE_VERSION,
    FEATURES,
    RANKED_AS,
    band_of,
    percentile_of,
    tag_raw,
    tags_of,
)
from burro_core.ids import (
    BUY_SEGMENTS,
    RENT_SEGMENTS,
    SYNTHETIC_SOURCE_ID,
    City,
    Confidence,
    FeatureId,
    GeometryType,
    GrittyVariant,
    PlaceKind,
    Segment,
    TagId,
    Tenure,
)
from burro_core.release import (
    BEYOND_CUTOFF_CELL,
    NEARBY_STATION_MINUTES,
    SCHEMA_VERSION,
    SYNTHETIC_ATTRIBUTION,
    AreaGeometry,
    CostEstimate,
    Counts,
    Cutoffs,
    Destination,
    FeatureValue,
    Geometry,
    InMemoryRelease,
    Manifest,
    Metric,
    Neighbourhood,
    Origin,
    Place,
    Source,
    StationAccess,
    TagValue,
    TravelTable,
)

from burro_pipeline.release.synthetic.chart import (
    Cell,
    Chart,
    Draw,
    Xy,
    centroid,
    clamp,
    distance,
    draw_chart,
    lon_lat,
    share_near_water,
)
from burro_pipeline.release.synthetic.journeys import (
    Network,
    Spot,
    Station,
    by_bike,
    network_km,
    on_foot,
    whole_minutes,
)
from burro_pipeline.release.synthetic.names import (
    AREAS,
    BOROUGH,
    CENTRE,
    LINES,
    OUT_OF_TOWN_KM,
    PLACES,
    SECOND_STATIONS,
    SOUTH_BANK,
    STEP_FREE_STATIONS,
    AreaPlan,
)

# The committed fixture is built with these. A rebuild with them is byte-identical.
SEED = 20260923
RELEASE_ID = "syn-2026-09-23-01"
BUILT_AT = "2026-09-23T00:00:00Z"
# The committed fixture carries Gritty, the one vibe that counts recorded crime,
# which Works and warehouses is a part of. A release that holds no recorded
# crime carries Works and warehouses in its place. It is built on demand,
# under an id of its own, and is never committed.
GRITTY = GrittyVariant.B
RELEASE_IDS: Mapping[GrittyVariant, str] = {
    GrittyVariant.B: RELEASE_ID,
    GrittyVariant.A: "syn-2026-09-23-02",
}

SOURCES = (SYNTHETIC_SOURCE_ID,)
VINTAGE = "2025"
COST_AS_OF = "2026-08"
TRAVEL_AS_OF = "2026-09"
DEFINITION = "Made up for testing from the invented character of each area. It measures nothing."
CUTOFFS = Cutoffs(pt=90, cycle=60, walk=60)

# An area this far from the middle of the centre is not central at all.
CITY_RADIUS_KM = 7.5
# A station stands within this of the middle of the area it is named for.
STATION_OFFSET_KM = 0.5
# With this much of an area near the river, in per cent, all of its green is
# meadow, and all of its newer homes are flats on the old quays.
MEADOW_FROM = 20
NEW_FLATS_FROM = 30

_F = FeatureId
_CRIME = (_F.CRIME_VIOLENCE_ROBBERY, _F.CRIME_BURGLARY_THEFT)
# A share of homes, or a middle distance over them, which too few homes leave unsteady.
_OF_HOMES = (_F.HOMES_FLATS, _F.HOMES_PRE1919, _F.NOISE_EXPOSURE, _F.HIGHSTREET_ACCESS)
# A rate for each 1,000 homes, which too few homes leave unsteady.
_FOR_EACH_HOME = (_F.VENUE_FOOD_DRINK_PER_HOMES, _F.CULTURE_VENUES_PER_HOMES)
# What a person walks in a minute, in metres. The made-up town has no streets, so a
# straight line there is as long as the walk its station rows hold.
METRES_A_MINUTE = 80
# The features of catalogue version 1, in the order they are drawn. The first
# random stream draws these and nothing else, so that no figure of theirs
# moves when a feature is added.
FIRST = (
    *_CRIME,
    _F.SCHOOL_PRIMARY_NEARBY,
    _F.SCHOOL_PRIMARY_ATTAINMENT,
    _F.SCHOOL_SECONDARY_ATTAINMENT,
    _F.UNIVERSITY_PROXIMITY,
    _F.GREEN_COVER,
    _F.PARK_PROXIMITY,
    _F.PLAY_SPACE_PROXIMITY,
    _F.WATER_ACCESS,
    _F.AIR_NO2,
    _F.NOISE_EXPOSURE,
    _F.VENUE_FOOD_DRINK,
    _F.VENUE_EVENING,
    _F.VENUE_INDEPENDENT,
    _F.CULTURE_VENUES,
    _F.HIGHSTREET_ACCESS,
    _F.HOMES_FLATS,
    _F.HOMES_PRE1919,
    _F.HOMES_DENSITY,
    _F.CONSERVATION_COVER,
    _F.STATION_WALK,
    _F.STATION_LINES,
)
# The parts the vibes of catalogue version 2 are made of. They draw from a
# second stream, after everything the first one draws.
SECOND = (
    _F.INDEPENDENTS_NEARBY,
    _F.CENTRE_SMALL,
    _F.CENTRE_COMPACT,
    _F.LISTED_BUILDINGS,
    _F.HOMES_POST2000,
    _F.ROAD_MAJOR_EXPOSURE,
    _F.EVENING_CLUSTER_EXPOSURE,
    _F.LAND_INDUSTRY,
    _F.LAND_STORAGE,
    _F.LAND_TRANSPORT_OTHER,
    _F.LAND_GARDENS,
    _F.LAND_WOODLAND,
    _F.PARK_LARGE_PROXIMITY,
    _F.PARK_FACILITIES,
    _F.GROCERY_WALK,
    _F.INCIDENT_CRIMINAL_DAMAGE,
    _F.INCIDENT_ANTISOCIAL,
)
# What joined the catalogue after the vibes. Each draws from a stream of its own, after
# everything else, so that one more of them moves no figure of another.
LATER = (_F.VENUE_FOOD_DRINK_PER_HOMES, _F.PRICE_MEDIAN, _F.CULTURE_VENUES_PER_HOMES)
# In core and in no release yet, so three recipes run short, as London would
# today: outdoor space and kinds of food wait on an audit, a GP and a
# pharmacy on a licence.
CARRIED = (*FIRST, *SECOND, *LATER)
_OF_HOMES_TOO = (
    _F.CENTRE_SMALL,
    _F.HOMES_POST2000,
    _F.ROAD_MAJOR_EXPOSURE,
    _F.EVENING_CLUSTER_EXPOSURE,
)
_INCIDENTS = (_F.INCIDENT_CRIMINAL_DAMAGE, _F.INCIDENT_ANTISOCIAL)
# A count that is a mean over an area's homes, and so is no whole number.
_MEANS = (_F.VENUE_FOOD_DRINK, _F.CULTURE_VENUES)

# Gaps left on purpose, so that the code that handles missing data has
# something to handle. Nothing is filled in anywhere downstream.
NOT_MEASURED: Mapping[str, tuple[FeatureId, ...]] = {
    # The new town, which most surveys have not reached. Under the default
    # weights less than half of what is asked for is known, so it is unranked.
    "Otterby Fields": (
        *_CRIME,
        _F.SCHOOL_PRIMARY_ATTAINMENT,
        _F.SCHOOL_SECONDARY_ATTAINMENT,
        _F.PARK_PROXIMITY,
        _F.PLAY_SPACE_PROXIMITY,
        _F.AIR_NO2,
        _F.NOISE_EXPOSURE,
        _F.VENUE_FOOD_DRINK,
        _F.VENUE_EVENING,
        _F.VENUE_INDEPENDENT,
        _F.CULTURE_VENUES,
        _F.HIGHSTREET_ACCESS,
        _F.HOMES_PRE1919,
        _F.CONSERVATION_COVER,
        # It holds none of the newer parts, so it can be placed on Homes alone.
        *SECOND,
        *LATER,
    ),
    # Too few homes for a rate, or a share of homes, to be steady.
    "Grapnel Dock": (
        *_CRIME,
        *_OF_HOMES,
        _F.SCHOOL_PRIMARY_ATTAINMENT,
        *_OF_HOMES_TOO,
        *_INCIDENTS,
        *_FOR_EACH_HOME,
    ),
    "Sedgewater Marsh": (
        *_CRIME,
        *_OF_HOMES,
        _F.SCHOOL_PRIMARY_ATTAINMENT,
        *_OF_HOMES_TOO,
        *_INCIDENTS,
        *_FOR_EACH_HOME,
    ),
    # Where the conservation source has no cover the answer is unknown, not zero.
    "Gorsebeck": (_F.CONSERVATION_COVER,),
    "Marrowfen": (_F.CONSERVATION_COVER, _F.NOISE_EXPOSURE),
    # No primary school within reach, so there are no results to report.
    "Cindermoor": (_F.SCHOOL_PRIMARY_ATTAINMENT,),
    "Alderwick": (_F.AIR_NO2,),
}
# A rankable area with no cost estimate at all.
NO_COST = "Ostrel Vale"
# Every estimate here is modelled: a new town has no history of rents or sales.
MODELLED_COST = "Otterby Fields"
# Areas that hold both ends of a scale, one for each scale that both ways of
# gritty carry. Each is drawn as a range, a band either side of where it sits,
# and never as a point in the middle. No release holds the sub-areas a spread
# would be worked out from, so it is set by hand, and every other spread is
# the band itself.
MIXED = frozenset(
    {
        # A loud high street, and quiet streets a few minutes behind it.
        ("Foxholt", TagId.PACE),
        # Old wharves, and new studios built between them.
        ("Kindlewharf", TagId.BUILT_AGE),
        # New blocks on the water, and streets of houses behind them.
        ("Sable Reach", TagId.HOMES),
    }
)
# Journeys the router never computed: `null` in every matrix, which is not `-1`.
NOT_ROUTED = (
    ("Gorsebeck", "Wexmoor University"),
    ("Gorsebeck", "Kindlewharf School of Art"),
    ("Otterby Fields", "Pellam Infirmary"),
)

RENT_BASE, RENT_RANGE, RENT_UNIT = 900, 1400, 25
PRICE_BASE, PRICE_RANGE, PRICE_UNIT = 180_000, 480_000, 5_000
LOWER_SHARE, UPPER_SHARE = 0.87, 1.15
SEGMENT_MULTIPLE: Mapping[Segment, float] = {
    Segment.ROOM: 0.52,
    Segment.STUDIO: 0.78,
    Segment.BED_1: 1.0,
    Segment.BED_2: 1.32,
    Segment.BED_3: 1.68,
    Segment.BED_4PLUS: 2.25,
    Segment.FLAT: 1.0,
    Segment.TERRACED: 1.4,
    Segment.SEMI_DETACHED: 1.7,
    Segment.DETACHED: 2.4,
}
# Observations behind an estimate: the tiers of the contract, and too few to estimate at all.
HIGH_FROM, MEDIUM_FROM, ESTIMATED_FROM = 50, 10, 3
BUSIEST_MARKET = 95


@dataclass(frozen=True)
class _Area:
    plan: AreaPlan
    area_id: str
    ring: tuple[Xy, ...]
    spot: Spot
    central: float  # 1 at the centre, 0 at the city's edge
    water: float  # per cent of the area near the river

    @property
    def cell(self) -> Cell:
        return (self.plan.row, self.plan.col)


@dataclass(frozen=True)
class _Located:
    place: Place
    spot: Spot


def _areas(chart: Chart) -> tuple[_Area, ...]:
    river = chart.river()
    rings = {plan.name: chart.ring((plan.row, plan.col)) for plan in AREAS}
    middle = centroid(rings[CENTRE])
    found: list[_Area] = []
    for number, plan in enumerate(AREAS, start=1):
        ring = rings[plan.name]
        spot = Spot(centroid(ring), (plan.row, plan.col) in SOUTH_BANK)
        found.append(
            _Area(
                plan=plan,
                area_id=f"syn-n{number:04d}",
                ring=ring,
                spot=spot,
                central=clamp(1 - distance(spot.at, middle) / CITY_RADIUS_KM),
                water=round(share_near_water(ring, river), 1),
            )
        )
    return tuple(found)


def _stations(areas: Sequence[_Area], draw: Draw) -> tuple[Station, ...]:
    """Every station a line stops at, a short walk from the middle of its area."""
    middles = {area.plan.name: area.spot for area in areas}
    found: list[Station] = []
    for number, name in enumerate(sorted({stop for line in LINES for stop in line.stops}), 1):
        area, planned = SECOND_STATIONS.get(name, (name, None))
        # Drawn even where the plan says where, so that a second station moves no other.
        drawn = (draw.around(STATION_OFFSET_KM), draw.around(STATION_OFFSET_KM))
        east, north = planned or drawn
        middle = middles[area]
        found.append(
            Station(
                station_id=f"syn-s{number:04d}",
                name=name,
                spot=Spot((middle.at[0] + east, middle.at[1] + north), middle.south_bank),
                lines=tuple(sorted(line.name for line in LINES if name in line.stops)),
            )
        )
    return tuple(found)


def _station_walks(area: _Area, stations: Sequence[Station]) -> list[tuple[Station, int]]:
    """Every station with the walk to it from the middle of the area, nearest first."""
    walks = [(station, whole_minutes(on_foot(area.spot, station.spot))) for station in stations]
    return sorted(walks, key=lambda pair: (pair[1], pair[0].station_id))


def _neighbours(area: _Area, areas: Sequence[_Area]) -> tuple[str, ...]:
    """The areas that share a side with this one. The river is not a shared side."""
    row, col = area.cell
    beside = {(row + 1, col), (row - 1, col), (row, col + 1), (row, col - 1)}
    return tuple(
        sorted(
            other.area_id
            for other in areas
            if other.cell in beside and other.spot.south_bank == area.spot.south_bank
        )
    )


def _neighbourhoods(areas: Sequence[_Area]) -> tuple[Neighbourhood, ...]:
    return tuple(
        Neighbourhood(
            area_id=area.area_id,
            slug=area.plan.name.lower().replace(" ", "-"),
            name=area.plan.name,
            borough=BOROUGH,
            aliases=area.plan.aliases,
            centroid=lon_lat(area.spot.at),
            rankable=area.plan.rankable,
            neighbours=_neighbours(area, areas),
        )
        for area in areas
    )


def _geometries(areas: Sequence[_Area]) -> tuple[AreaGeometry, ...]:
    return tuple(
        AreaGeometry(
            area_id=area.area_id,
            geometry=Geometry(
                type=GeometryType.POLYGON,
                # A GeoJSON ring ends where it began.
                coordinates=(tuple(lon_lat(p) for p in (*area.ring, area.ring[0])),),
            ),
        )
        for area in areas
    )


def _station_rows(areas: Sequence[_Area], stations: Sequence[Station]) -> tuple[StationAccess, ...]:
    return tuple(
        StationAccess(
            area_id=area.area_id,
            station_id=station.station_id,
            name=station.name,
            walk_minutes=walk,
            lines=station.lines,
            step_free=station.name in STEP_FREE_STATIONS,
            nearest=position == 0,
        )
        for area in areas
        for position, (station, walk) in enumerate(_station_walks(area, stations))
        # The nearest, however far, and any other within a short walk.
        if position == 0 or walk <= NEARBY_STATION_MINUTES
    )


def _places(chart: Chart, stations: Sequence[Station], draw: Draw) -> tuple[_Located, ...]:
    """Every place and where it is. Stations come first, then the places of the plan."""
    cells = {plan.name: (plan.row, plan.col) for plan in AREAS}
    named: list[tuple[str, PlaceKind, tuple[str, ...], Spot, str]] = [
        (s.name, PlaceKind.STATION, (f"{s.name} station",), s.spot, "") for s in stations
    ]
    for plan in PLACES:
        spot = Spot(OUT_OF_TOWN_KM, south_bank=False)
        if plan.area:
            cell = cells[plan.area]
            at = chart.inside(cell, draw.between(0.15, 0.85), draw.between(0.15, 0.85))
            spot = Spot(at, cell in SOUTH_BANK)
        named.append((plan.name, plan.kind, plan.aliases, spot, plan.shares))

    place_ids = {name: f"syn-p{n:04d}" for n, (name, *_) in enumerate(named, start=1)}
    spots = {name: spot for name, _, _, spot, _ in named}
    own = [name for name, *_, shares in named if not shares]
    destination_ids = {name: f"syn-d{n:04d}" for n, name in enumerate(own, start=1)}
    for name, *_, shares in named:
        if shares:
            # Two names for one spot end at one destination, and stand where it stands.
            destination_ids[name] = destination_ids[shares]
            spots[name] = spots[shares]

    coarse = [name for name, kind, *_ in named if kind in (PlaceKind.STATION, PlaceKind.DISTRICT)]

    def stands_in(name: str) -> str:
        """The station or district that takes this place's part in a shared link."""
        if name in coarse:
            return place_ids[name]
        return place_ids[min(coarse, key=lambda c: (distance(spots[c].at, spots[name].at), c))]

    return tuple(
        _Located(
            Place(
                place_id=place_ids[name],
                name=name,
                aliases=aliases,
                kind=kind,
                destination_id=destination_ids[name],
                coarse_place_id=stands_in(name),
                centroid=lon_lat(spots[name].at),
                source_id=SYNTHETIC_SOURCE_ID,
            ),
            spots[name],
        )
        for name, kind, aliases, _, _ in named
    )


def _destinations(places: Sequence[_Located]) -> dict[str, Spot]:
    """Where each destination is, in the order of their ids."""
    return dict(sorted(((p.place.destination_id, p.spot) for p in places), key=lambda d: d[0]))


def _travel(
    areas: Sequence[_Area], places: Sequence[_Located], stations: Sequence[Station]
) -> TravelTable:
    destinations = _destinations(places)
    network = Network(stations)
    by_name = {p.place.name: p.place.destination_id for p in places}
    skipped = {(area, by_name[place]) for area, place in NOT_ROUTED}

    def matrix(
        minutes: Callable[[Spot, Spot], float], cutoff: int
    ) -> tuple[tuple[int | None, ...], ...]:
        def cell(area: _Area, destination_id: str, end: Spot) -> int | None:
            if (area.plan.name, destination_id) in skipped:
                return None
            whole = whole_minutes(minutes(area.spot, end))
            # All the release holds of a longer journey is that it is longer than the cutoff.
            return whole if whole <= cutoff else BEYOND_CUTOFF_CELL

        return tuple(
            tuple(cell(area, destination_id, end) for destination_id, end in destinations.items())
            for area in areas
        )

    return TravelTable(
        source_ids=SOURCES,
        as_of=TRAVEL_AS_OF,
        area_ids=tuple(area.area_id for area in areas),
        destination_ids=tuple(destinations),
        cutoff_minutes=CUTOFFS,
        pt_typical=matrix(lambda a, b: network.minutes(a, b, missed=False), CUTOFFS.pt),
        pt_just_missed=matrix(lambda a, b: network.minutes(a, b, missed=True), CUTOFFS.pt),
        cycle=matrix(by_bike, CUTOFFS.cycle),
        walk=matrix(on_foot, CUTOFFS.walk),
    )


def _figures(
    area: _Area, stations: Sequence[Station], campus_km: float, draw: Draw
) -> dict[FeatureId, float]:
    """One area's figures before tidying, from its character and its place on the map.

    Every figure draws its noise whether or not it is kept, so that leaving a
    gap never changes any other number.
    """
    p, central = area.plan, area.central
    # Going out follows the centre: the same liveliness is busier in the middle of town.
    busy = p.lively * (0.35 + 0.65 * central)
    walks = _station_walks(area, stations)
    nearby = [station for station, walk in walks if walk <= NEARBY_STATION_MINUTES]
    noise = draw.around
    # Homes are flats, and close together, towards the middle of town, but for where the
    # plan says otherwise: terraces beside the centre, estates at the end of a line.
    built_up = central if p.flats is None else p.flats
    # Density climbs steeply with it. A square root, and no other power, because it is
    # the one that gives the same answer to the last digit on every machine.
    crowding = built_up * math.sqrt(built_up)
    # A park is where the green is, but for where the green is gardens and fields.
    parks = p.green if p.parks is None else p.parks
    attainment = 50 + 32 * p.family + 7 * p.green - 6 * p.industry
    loudness = 6 + 40 * central + 26 * p.industry + 12 * p.lively - 12 * p.green
    return {
        _F.CRIME_VIOLENCE_ROBBERY: 6 + 34 * busy + 9 * central + 6 * p.industry + noise(2),
        _F.CRIME_BURGLARY_THEFT: 18 + 55 * central + 22 * busy + noise(5),
        _F.SCHOOL_PRIMARY_NEARBY: 0.6 + 4.6 * p.family + 1.4 * central + noise(0.5),
        _F.SCHOOL_PRIMARY_ATTAINMENT: attainment + noise(2),
        _F.SCHOOL_SECONDARY_ATTAINMENT: 39 + 15 * p.family + 4 * p.green + noise(1.5),
        _F.UNIVERSITY_PROXIMITY: 1000 * campus_km + noise(40),
        _F.GREEN_COVER: 5 + 45 * p.green - 4 * central + noise(2),
        _F.PARK_PROXIMITY: 1250 - 1050 * parks + 120 * central + noise(60),
        _F.PLAY_SPACE_PROXIMITY: 950 - 620 * p.family - 180 * p.green + noise(50),
        _F.WATER_ACCESS: area.water,
        _F.AIR_NO2: 13 + 21 * central + 11 * p.industry - 5 * p.green + noise(1.2),
        _F.NOISE_EXPOSURE: loudness + noise(3),
        _F.VENUE_FOOD_DRINK: 3 + 125 * busy + 22 * p.street * central + noise(4),
        _F.VENUE_EVENING: 0.8 + 52 * busy * p.lively + 4 * p.street * central + noise(1.5),
        _F.VENUE_INDEPENDENT: 24 + 62 * p.indie + noise(3),
        _F.CULTURE_VENUES: 0.2 + 7 * busy + 5 * p.indie * p.old + noise(0.3),
        # A distance to a town centre: the more of a high street, the nearer. It is drawn
        # as the share of homes near one that it once was, so that no area changed places.
        _F.HIGHSTREET_ACCESS: 3000 - 30 * round(18 + 76 * p.street + noise(3), 1),
        _F.HOMES_FLATS: 12 + 70 * built_up + 14 * p.lively - 12 * p.family + noise(3),
        _F.HOMES_PRE1919: 4 + 72 * p.old + noise(3),
        _F.HOMES_DENSITY: 14 + 105 * crowding + 24 * p.lively - 10 * p.green + noise(4),
        _F.CONSERVATION_COVER: 62 * p.old - 9 + noise(3),
        # The same station and the same lines as the station rows hold, in metres.
        _F.STATION_WALK: float(METRES_A_MINUTE * walks[0][1]),
        _F.STATION_LINES: float(len({line for station in nearby for line in station.lines})),
    }


def _newer_figures(area: _Area, draw: Draw) -> dict[FeatureId, float]:
    """One area's figures for the parts of catalogue version 2, before tidying.

    As `_figures`: each is made up from the character of the area, and each
    draws its noise whether or not it is kept. These parts do not all follow
    the centre, so that the vibes made of them find different areas: what is
    independent follows the plan and not how much goes on, gardens follow the
    green and not the schools, and what is recorded follows the night and the
    middle of town more than the works.
    """
    p, central = area.plan, area.central
    busy = p.lively * (0.35 + 0.65 * central)
    noise = draw.around
    # Offices empty in the evening, so the centre goes out less late than it is busy.
    late = p.lively * (1 - 0.45 * p.offices)
    night = late * late * (0.35 + 0.65 * central)
    works = p.industry if p.works is None else p.works
    # A food shop follows a high street, but not one given over to offices or to going out.
    grocers = p.street * (1 - 0.7 * late) * (1 - 0.5 * p.offices)
    # The large parks are the meadows along the river, and the towpath where it is built
    # up. An old village has kept its green.
    parks = p.green if p.parks is None else p.parks
    meadow = clamp(area.water / MEADOW_FROM) * (0.35 + 0.65 * parks)
    meadow = max(meadow, parks * p.indie * p.old)
    # New flats go up along the river, where the quays were, and nothing there is listed.
    quays = (1 - p.old) * clamp(area.water / NEW_FLATS_FROM)
    # Works line the main roads, and so does a high street. Green streets stand back from
    # them. The plan says where a road runs through a green place, or round a busy one.
    roads = 12 + 34 * central + 22 * p.street + 24 * works - 10 * p.green
    if p.roads is not None:
        roads = 12 + 70 * p.roads
    return {
        _F.INDEPENDENTS_NEARBY: 1 + 28 * p.indie + 2 * busy + noise(1.5),
        # A small centre is a high street where not much goes on. The more that does, the
        # larger the centre and the more strung out.
        _F.CENTRE_SMALL: 20 + 110 * p.street * (1 - busy) * (1 - busy) + noise(3),
        _F.CENTRE_COMPACT: 35 + 50 * p.indie * p.street - 60 * busy + noise(3),
        _F.LISTED_BUILDINGS: 0.4 + 38 * p.old * p.old - 2 * quays + noise(1),
        _F.HOMES_POST2000: 3 + 30 * (1 - p.old) * (1 - p.old) + 22 * quays + noise(2.5),
        _F.ROAD_MAJOR_EXPOSURE: roads + noise(3),
        # Where little is open late, few homes are near a cluster, wherever they are.
        _F.EVENING_CLUSTER_EXPOSURE: 0.3 + 58 * night + 8 * late * central + noise(0.3),
        _F.LAND_INDUSTRY: 0.5 + 24 * works + noise(0.8),
        _F.LAND_STORAGE: 0.4 + 17 * works + noise(0.7),
        _F.LAND_TRANSPORT_OTHER: 0.6 + 9 * works + 3 * central + noise(0.5),
        _F.LAND_GARDENS: 6 + 28 * p.green + 4 * p.family - 14 * central + noise(2),
        _F.LAND_WOODLAND: 0.5 + 15 * p.green * p.green + noise(0.8),
        _F.PARK_LARGE_PROXIMITY: 3300 - 1200 * parks - 1800 * meadow + noise(140),
        _F.PARK_FACILITIES: 1 + 3 * parks + 3 * p.family + 3 * meadow + noise(0.6),
        _F.GROCERY_WALK: 15 - 22 * grocers + noise(1),
        # What is recorded follows where people go out late, the middle of town and a
        # high street, and the yards and works less than any. It followed the works most
        # of all until Gritty was given the recipe that was decided, in which works and
        # warehouses and what is recorded are three quarters: drawn as they were, Gritty
        # found the areas that Works and warehouses finds, and nobody could have told
        # what either adds.
        _F.INCIDENT_CRIMINAL_DAMAGE: (
            3 + 10 * night + 4 * central + 4 * works + 3 * p.street + noise(0.8)
        ),
        _F.INCIDENT_ANTISOCIAL: 8 + 22 * night + 8 * central + 4 * works + noise(2),
    }


def _later_figure(feature_id: FeatureId, area: _Area, draw: Draw) -> float:
    """One area's figure for a part that joined after the vibes, before tidying.

    As `_figures`: it is made up from the character of the area, and draws
    its noise whether or not it is kept.
    """
    p, central = area.plan, area.central
    if feature_id is _F.VENUE_FOOD_DRINK_PER_HOMES:
        # The places within reach for the homes within reach. It follows how much goes
        # on, by day and late, and a high street, and falls where homes stand close
        # together: the same places serve more of them. Offices have places to eat and
        # few homes, so they read high. Works and yards have few places to eat, so they
        # read low.
        busy = p.lively * (0.35 + 0.65 * central)
        late = p.lively * (1 - 0.45 * p.offices)
        night = late * late * (0.35 + 0.65 * central)
        built_up = central if p.flats is None else p.flats
        drawn = 5 + 8 * busy + 6 * night + 3 * p.street + 6 * p.offices
        return drawn - 4 * built_up - 5 * p.industry + draw.around(0.4)
    if feature_id is _F.CULTURE_VENUES_PER_HOMES:
        # The venues within reach for the homes within reach. It follows how much goes
        # on and old streets with independent places, as the count does. Offices have
        # venues and few homes, so they read high.
        busy = p.lively * (0.35 + 0.65 * central)
        drawn = 0.5 + 7 * busy + 5 * p.indie * p.old + 1.5 * p.offices
        return drawn + draw.around(0.3)
    if feature_id is _F.PRICE_MEDIAN:
        # What a home of any kind sold for. It follows what makes the made-up costs dear:
        # central, green, old and by the water all cost more, and works cost less. It
        # draws its own noise, so that no cost moves.
        wanted = 0.50 * central + 0.20 * p.green + 0.15 * p.old + 0.08 * p.lively
        by_water = 0.10 * clamp(area.water / 30)
        level = clamp(0.10 + wanted + by_water - 0.30 * p.industry + draw.around(0.03))
        return PRICE_BASE + PRICE_RANGE * level
    raise ValueError(f"no figure is made up for {feature_id}")


def _tidy(feature_id: FeatureId, value: float) -> float:
    """A figure as its source would publish it: in its unit, and never below nothing."""
    unit = FEATURES[feature_id].unit
    if unit == "%":
        return round(clamp(value, 0, 100), 1)
    if unit == "m":
        return float(max(round(value / 10) * 10, 10))
    if unit == "min":
        # No walk in the release is under 2 minutes, as no journey is.
        return float(whole_minutes(value)) if feature_id in SECOND else _whole(value)
    if unit == "£":
        # A median of what was paid is a whole number of pounds, or ends in a half.
        return float(max(round(value / 500) * 500, 500))
    # The places within reach are a mean over an area's homes, so the count is given to one
    # decimal place, as a build of real files gives it.
    if unit == "count" and feature_id not in _MEANS:
        return _whole(value)
    return round(max(value, 0.0), 1)


def _whole(value: float) -> float:
    return float(max(round(value), 0))


def _features(
    areas: Sequence[_Area],
    stations: Sequence[Station],
    places: Sequence[_Located],
    draw: Draw,
    newer: Draw,
    later: Mapping[FeatureId, Draw],
) -> tuple[FeatureValue, ...]:
    campuses = [p.spot for p in places if p.place.kind is PlaceKind.UNIVERSITY]
    values: dict[tuple[str, FeatureId], float | None] = {}
    coverage: dict[tuple[str, FeatureId], float] = {}

    def keep(area: _Area, figures: Mapping[FeatureId, float], stream: Draw) -> None:
        for feature_id in figures:
            # Most of the time a source covers the whole area. Now and then it covers part.
            whole, part = stream.between(0, 1) < 0.85, round(stream.between(0.55, 0.95), 2)
            too_little = round(stream.between(0.0, 0.45), 2)
            known = feature_id not in NOT_MEASURED.get(area.plan.name, ())
            key = (area.area_id, feature_id)
            values[key] = _tidy(feature_id, figures[feature_id]) if known else None
            coverage[key] = (1.0 if whole else part) if known else too_little

    for area in areas:
        campus_km = min(network_km(area.spot, campus) for campus in campuses)
        keep(area, _figures(area, stations, campus_km, draw), draw)
    for area in areas:
        keep(area, _newer_figures(area, newer), newer)
    for feature_id, stream in later.items():
        for area in areas:
            keep(area, {feature_id: _later_figure(feature_id, area, stream)}, stream)

    rankable = [area.plan.rankable for area in areas]
    rows: list[FeatureValue] = []
    for feature_id in CARRIED:
        column = [values[area.area_id, feature_id] for area in areas]
        percentiles = percentile_of(column, rankable)
        rows += [
            FeatureValue(
                area_id=area.area_id,
                feature_id=feature_id,
                value=value,
                percentile=percentile,
                coverage=coverage[area.area_id, feature_id],
            )
            for area, value, percentile in zip(areas, column, percentiles, strict=True)
        ]
    return tuple(rows)


def _spread(area: _Area, tag_id: TagId, band: int | None) -> tuple[int | None, int | None]:
    """The bands the middle half of an area's homes span: the band itself, but for a mixed area."""
    if band is None or (area.plan.name, tag_id) not in MIXED:
        return band, band
    return max(band - 1, 1), min(band + 1, BANDS)


def _tags(
    areas: Sequence[_Area], features: Sequence[FeatureValue], variant: GrittyVariant
) -> tuple[TagValue, ...]:
    percentiles: dict[str, dict[FeatureId, float | None]] = {a.area_id: {} for a in areas}
    for row in features:
        percentiles[row.area_id][row.feature_id] = row.percentile
    rankable = [area.plan.rankable for area in areas]
    rows: list[TagValue] = []
    for vibe in tags_of(variant):
        raws = [tag_raw(vibe.tag_id, percentiles[area.area_id]) for area in areas]
        scores = percentile_of([raw.raw for raw in raws], rankable)
        # Core works out every band. Nothing here has a rule of its own for one.
        bands = band_of([raw.raw for raw in raws], rankable)
        for area, raw, score, band in zip(areas, raws, scores, bands, strict=True):
            low, high = _spread(area, vibe.tag_id, band)
            rows.append(
                TagValue(
                    area_id=area.area_id,
                    tag_id=vibe.tag_id,
                    raw=raw.raw,
                    score=score,
                    coverage=raw.coverage,
                    band=band,
                    spread_low=low,
                    spread_high=high,
                )
            )
    return tuple(rows)


def _price_level(area: _Area, draw: Draw) -> float:
    """How dear an area is, from 0 to 1. Central, green, old and by the water all cost more."""
    p = area.plan
    wanted = 0.50 * area.central + 0.20 * p.green + 0.15 * p.old + 0.08 * p.lively
    by_water = 0.10 * clamp(area.water / 30)
    return clamp(0.10 + wanted + by_water - 0.30 * p.industry + draw.around(0.03))


def _share_of_market(segment: Segment, flats: float, green: float) -> float:
    """How much of an area's market one kind of home is, from the share of its homes in flats."""
    houses = 1 - flats
    return {
        Segment.ROOM: 0.45 + 0.5 * flats,
        Segment.STUDIO: flats,
        Segment.BED_1: 0.3 + 0.7 * flats,
        Segment.BED_2: 0.7,
        Segment.BED_3: 0.15 + 0.85 * houses,
        Segment.BED_4PLUS: houses * houses,
        Segment.FLAT: 0.25 + 0.75 * flats,
        Segment.TERRACED: 0.2 + 0.7 * houses,
        Segment.SEMI_DETACHED: houses,
        Segment.DETACHED: houses * houses * (0.4 + 0.6 * green),
    }[segment]


def _confidence(observations: int) -> Confidence:
    if observations >= HIGH_FROM:
        return Confidence.HIGH
    return Confidence.MEDIUM if observations >= MEDIUM_FROM else Confidence.LOW


def _to_unit(value: float, unit: int) -> int:
    return max(round(value / unit), 1) * unit


def _costs(
    areas: Sequence[_Area], flats: Mapping[str, float], draw: Draw
) -> tuple[CostEstimate, ...]:
    rows: list[CostEstimate] = []
    for area in areas:
        level = _price_level(area, draw)
        estimated = area.plan.rankable and area.plan.name != NO_COST
        for tenure, segments in ((Tenure.RENT, RENT_SEGMENTS), (Tenure.BUY, BUY_SEGMENTS)):
            rent = tenure is Tenure.RENT
            base = RENT_BASE + RENT_RANGE * level if rent else PRICE_BASE + PRICE_RANGE * level
            unit = RENT_UNIT if rent else PRICE_UNIT
            for segment in segments:
                share = _share_of_market(segment, flats[area.area_id], area.plan.green)
                observations = round(BUSIEST_MARKET * share * draw.between(0.6, 1.0))
                median = base * SEGMENT_MULTIPLE[segment] * (1 + draw.around(0.03))
                if not estimated or observations < ESTIMATED_FROM:
                    continue  # no row where there is no estimate
                modelled = area.plan.name == MODELLED_COST
                rows.append(
                    CostEstimate(
                        area_id=area.area_id,
                        tenure=tenure,
                        segment=segment,
                        lower_quartile=_to_unit(median * LOWER_SHARE, unit),
                        median=_to_unit(median, unit),
                        upper_quartile=_to_unit(median * UPPER_SHARE, unit),
                        confidence=Confidence.LOW if modelled else _confidence(observations),
                        as_of=COST_AS_OF,
                        source_ids=SOURCES,
                    )
                )
    return tuple(rows)


def _metrics() -> tuple[Metric, ...]:
    return tuple(
        Metric(
            feature_id=feature.feature_id,
            label=feature.label,
            short_label=feature.short_label,
            dimension=feature.dimension,
            unit=feature.unit,
            polarity=feature.polarity,
            kind=feature.kind,
            describes=feature.describes,
            family=feature.family,
            method=feature.method,
            in_likeness=feature.in_likeness,
            native_resolution=feature.native_resolution,
            source_ids=SOURCES,
            vintage=VINTAGE,
            # What core shows and never ranks on is shown here too, and not ranked on.
            rankable=feature.feature_id not in RANKED_AS,
            definition=DEFINITION,
        )
        for feature in (FEATURES[feature_id] for feature_id in CARRIED)
    )


def _manifest(
    seed: int, release_id: str, built_at: str, counts: Counts, variant: GrittyVariant
) -> Manifest:
    return Manifest(
        release_id=release_id,
        schema_version=SCHEMA_VERSION,
        built_at=built_at,
        catalogue_version=CATALOGUE_VERSION,
        gritty_variant=variant,
        synthetic=True,
        # It is the whole of what it is: every part is there, and every part is made up.
        preview=False,
        city=City.SYN,
        seed=seed,
        sources=(
            Source(
                source_id=SYNTHETIC_SOURCE_ID,
                name="Synthetic test data",
                publisher="Burro",
                licence="None. Made up for testing",
                attribution=SYNTHETIC_ATTRIBUTION,
                url="",
                retrieved_on=built_at[:10],
            ),
        ),
        # `write_release` lists the files: only it sees their bytes.
        files=(),
        counts=counts,
    )


def build_synthetic(
    seed: int = SEED,
    release_id: str = RELEASE_ID,
    built_at: str = BUILT_AT,
    gritty_variant: GrittyVariant | str = GRITTY,
) -> InMemoryRelease:
    """The whole synthetic release. The same four inputs give the same release, byte for byte.

    Nothing is read from the clock, the environment or a file. The seed moves
    the map's corners, the places inside their areas and the noise on every
    figure. It does not move a name, an id or the character of an area.
    `gritty_variant` says which of the two ways gritty was built the release
    carries, and moves no figure.
    """
    variant = GrittyVariant(gritty_variant)
    draw = Draw(seed)
    chart = draw_chart(draw)
    areas = _areas(chart)
    stations = _stations(areas, draw)
    places = _places(chart, stations, draw)
    # The second stream, so that a newer part moves no figure that was drawn before it.
    # And a stream for each part that joined later, the first of them the third.
    later = {feature_id: Draw(seed + 2 + at) for at, feature_id in enumerate(LATER)}
    features = _features(areas, stations, places, draw, Draw(seed + 1), later)
    flats = {
        row.area_id: (row.value or 0.0) / 100
        for row in features
        if row.feature_id is FeatureId.HOMES_FLATS
    }
    destinations = _destinations(places)
    counts = Counts(
        neighbourhoods=len(areas),
        rankable=sum(area.plan.rankable for area in areas),
        destinations=len(destinations),
        places=len(places),
        stations=len(stations),
    )
    return InMemoryRelease(
        manifest=_manifest(seed, release_id, built_at, counts, variant),
        neighbourhoods=_neighbourhoods(areas),
        neighbourhoods_origin=Origin(source_ids=SOURCES, as_of=built_at[:10]),
        travel_table=_travel(areas, places, stations),
        stations_origin=Origin(source_ids=SOURCES, as_of=TRAVEL_AS_OF),
        metrics=_metrics(),
        features=features,
        tags=_tags(areas, features, variant),
        vibes=tags_of(variant),
        costs=_costs(areas, flats, draw),
        destinations=tuple(
            Destination(destination_id=destination_id, centroid=lon_lat(spot.at))
            for destination_id, spot in destinations.items()
        ),
        places=tuple(located.place for located in places),
        station_rows=_station_rows(areas, stations),
        geometries=_geometries(areas),
    )
