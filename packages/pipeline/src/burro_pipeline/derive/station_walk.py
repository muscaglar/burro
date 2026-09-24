"""The nearest station: how far it is, in a straight line, from where homes are to a way in.

The ways in come from the Department for Transport's file of London's stops,
which `stops_file.py` reads. Where homes are comes from the centres of output
areas, which `cells/centres.py` reads.

**It is a straight line, in metres, and not a walk.** No network of streets is
built yet, so no walk can be worked out, and a straight line is not turned into
minutes here: a railway, a river or a main road stands between many homes and
the station nearest to them. So the row of the catalogue says a straight line
and metres, as core names the measure. The id says a walk, because an id is
never renamed. Do not name the figure a walk, or give it in minutes, while it
is a straight line.

What counts as a station: every way in that the file gives as `RSE`, a way in
to a railway station, or as `TMU`, a way in to a tram, metro or underground
station, and whose row is active. So a railway station counts whoever runs its
trains, and so do the Underground, the DLR and a tram stop. The file gives the
two ends of the cable car as `TMU`, and they count too: no column tells them
apart, and the measure reads no code for what it stands for. A pier and a stop
of a bus are no station.

How a figure is made:

1. For each output area, the distance from its centre to the nearest way in.
   It is measured to a way in and never to the middle of a station, which the
   file does not give.
2. An area's figure is the median of those distances over its homes: half the
   area's homes are in an output area no further than this from a way in.
3. It is given to the nearest 10 metres. A home may stand a hundred metres
   from the centre of its output area, so a metre would claim too much.

**The edge.** The file holds the stops of London alone. A home near London's
edge may have its nearest station just outside, and that station is in no file
that was read. So the distance of an output area is known only where the
nearest way in that was found is no further than the nearest land outside
London. Land outside London is the outline of every small census area (LSOA)
that the lookup does not give to a London borough. Water is no land: the tidal
Thames is inside no outline, and a home beside it is not at an edge. Where the
distance is not known the output area adds nothing, the coverage of its area
falls by its homes, and below half the homes covered no figure is given. An
area that any such home lies in is listed under `edge`. The national file
closes the edge: `docs/research/data/stations.md` says how.

Nothing is filled in. A distance that is not known is never taken to be the
distance that was found.
"""

import math
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass

from burro_core.facts import fact_id
from burro_core.ids import FactKind, FeatureId, NativeResolution
from burro_core.release import Metric

from burro_pipeline.cells import centres, land, spine
from burro_pipeline.cells.centres import Point
from burro_pipeline.cells.shapes import Shape, read_outlines
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import park_proximity, stops_file
from burro_pipeline.derive.catalogue_row import catalogue_row
from burro_pipeline.derive.methods import Worked, row_of
from burro_pipeline.derive.station_shapes import (
    to_the_nearest_land,
    to_the_nearest_point,
    within,
)
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Method
from burro_pipeline.evidence.receipt import Geography, Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

FEATURE = FeatureId.STATION_WALK
SOURCE = stops_file.SOURCE
# The types of stop that are a way in to a station.
COUNTS = stops_file.STATION_TYPES
# The method is the one the distance to a park is worked out by. It is held once.
METHOD: Method = park_proximity.STRAIGHT_LINE
METHODS: tuple[Method, ...] = (METHOD,)
# The figure is in metres, and never in minutes.
UNIT = "m"
# A figure is given to the nearest so many metres.
NEAREST = park_proximity.NEAREST
# What the ways in are keyed by, as the parser finds them.
KEYED_BY = Geography.POINT
CENSUS = 2021
# What a person reads beside the figure: it is a straight line, and no walk, and it is
# measured to a way in.
LABEL = "Straight-line distance to the nearest way in to a station"
# What the measure is, from whom, for what period, and what it is not.
DEFINITION = (
    "The distance in a straight line, in metres, from the point the statistics office gives as "
    "the centre of each census output area to the nearest way in to a railway station or to a "
    "tram, metro or underground station that {publisher} lists for Greater London in {product} "
    "as the file was saved on {saved}, as the median over the area's homes at the census of "
    "{census} and given to the nearest {nearest} metres with a half taken upward: it is "
    "measured across whatever lies between and not along any street or path, so the walk is "
    "longer, and a home that stands nearer to land outside London than to any way in that was "
    "found is left out, because the file holds no station outside London."
)
# What the product shows beside the figure.
CANNOT_SEE = (
    "This is a straight line from where the homes of each small census area are taken to stand "
    "to the nearest way in to a station, and not a walk, so a railway, a river or a main road "
    "in between makes the real walk longer.",
    "A station is any railway, Underground, DLR or tram station, and either end of the cable "
    "car: the figure does not say which trains call, how often, where they go, or whether a "
    "way in has steps.",
    "The file holds the stations of London alone, so a home near London's edge may have a "
    "nearer station outside it, and such a home is left out of the figure.",
)


@dataclass(frozen=True)
class Edge:
    """Where London's edge is nearer than the nearest way in that was found."""

    # The output areas whose distance is not known for it, in the order of their codes.
    output_areas: tuple[str, ...]
    # The areas that any of them lies in, and those of them that have no figure for it.
    areas: tuple[str, ...]
    without_a_figure: tuple[str, ...]


@dataclass(frozen=True)
class Distances:
    """The distance to the nearest stop of some types, for every area, and what is behind it."""

    # The figure of each area, by its id. An area with no figure is here too, with its state.
    worked: Mapping[str, Worked]
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    # How many stops of the types were read.
    stops: int
    # The distance of each output area whose nearest stop is known, in metres.
    of_oa: Mapping[str, float]
    # The distance that was found for each output area that has a centre, known or not.
    found_of_oa: Mapping[str, float]
    edge: Edge
    # The day the file was saved, as its receipt gives it.
    saved: str


@dataclass(frozen=True)
class Nearest(Distances):
    """The same for the ways in to a station, with its evidence and its row of the catalogue."""

    rows: tuple[EvidenceRow, ...]
    metric: Metric
    geography: Geography


def is_the_file(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the file this measure reads."""
    return stops_file.is_the_file(name)


def outside_london(lookup: Opened) -> frozenset[str]:
    """The code of every small census area the lookup gives to no London borough."""
    found: set[str] = set()
    with lookup.text() as text:
        for row in lookup.rows(text, (spine.LSOA, spine.BOROUGH)):
            if not row[spine.BOROUGH].startswith(spine.LONDON):
                found.add(row[spine.LSOA])
    return frozenset(found)


def known(found: Mapping[str, float], edge: Mapping[str, float]) -> dict[str, float]:
    """The distances that are known: the nearest stop is no further than the land outside."""
    return {oa: far for oa, far in found.items() if math.isfinite(far) and far <= edge[oa]}


def _edge(
    found: Spine, of_oa: Mapping[str, float], placed: Collection[str], worked: Mapping[str, Worked]
) -> Edge:
    unknown = tuple(sorted(oa for oa in placed if oa not in of_oa))
    areas = tuple(sorted({found.area_of[oa] for oa in unknown}))
    return Edge(unknown, areas, tuple(area for area in areas if worked[area].value is None))


def _land_outside(
    inputs: Inputs, points: Sequence[Point], reach: float
) -> tuple[list[Shape], tuple[str, str]]:
    """The land outside London that a home of the build may be nearest to, and its two files."""
    lookup = inputs.open(spine.LOOKUP, Use.SCORING, edition=spine.LOOKUP_EDITION)
    boundaries = inputs.open(land.BOUNDARIES, Use.SCORING, edition=land.BOUNDARIES_EDITION)
    outlines = read_outlines(boundaries, spine.LSOA, outside_london(lookup))
    near = within([outlines[code] for code in sorted(outlines)], points, reach)
    return near, (lookup.file_id, boundaries.file_id)


def distances(
    inputs: Inputs, found: Spine, types: Collection[str], *, edition: str | None = None
) -> Distances:
    """The distance to the nearest stop of some types for every area, with the edge held.

    The gate is asked about every file before it is read. `found` is the spine
    of the same build.
    """
    opened = stops_file.open_the_file(inputs, Use.SCORING, edition=edition)
    placed = inputs.open(centres.CENTRES, Use.SCORING, edition=centres.CENTRES_EDITION)
    stops = stops_file.read(opened, types)
    points = centres.centres_of(placed, found)
    if not points:
        raise LockError("input_is_as_described", placed.file_id, "it holds no centre of the build")
    ordered = sorted(points)
    at = [points[oa] for oa in ordered]
    far = to_the_nearest_point(at, sorted({stop.point for stop in stops}))
    outside, ground = _land_outside(inputs, at, max(far))
    found_of_oa = dict(zip(ordered, far, strict=True))
    edge_of_oa = dict(zip(ordered, to_the_nearest_land(at, outside), strict=True))
    of_oa = known(found_of_oa, edge_of_oa)
    worked = park_proximity.figures(of_oa, found)
    handed = {one.file_id: one.receipt for one in inputs.opened}
    if not set(found.inputs) <= set(handed):
        raise ValueError("the spine is made from files of this build")
    behind = sorted({opened.file_id, placed.file_id, *ground, *found.inputs})
    files = tuple(handed[file_id] for file_id in behind)
    return Distances(
        worked=worked,
        files=files,
        stops=len(stops),
        of_oa=of_oa,
        found_of_oa=found_of_oa,
        edge=_edge(found, of_oa, ordered, worked),
        saved=opened.receipt.data_period.days()[1],
    )


def definition_of(saved: str) -> str:
    """The sentence a methods page prints for the measure."""
    return DEFINITION.format(
        publisher=stops_file.PUBLISHER,
        product=stops_file.PRODUCT,
        saved=saved,
        census=CENSUS,
        nearest=NEAREST,
    )


def metric_of(files: Sequence[Receipt], saved: str) -> Metric:
    """The row of the catalogue: the name, the unit, the period and every source.

    The name and the unit are the ones the figure supports, and core says
    both. It is measured from points, and on no network.
    """
    row = catalogue_row(
        FEATURE,
        method=METHOD,
        label=LABEL,
        native_resolution=NativeResolution.POINT,
        source_ids={receipt.source_id for receipt in files},
        vintage=saved,
        definition=definition_of(saved),
    )
    return row.replace(unit=UNIT)


def build(inputs: Inputs, found: Spine, *, edition: str | None = None) -> Nearest:
    """The distance to the nearest way in to a station for every area, and its evidence.

    A row of evidence names the file of stops, the centres, the lookup, the
    table of homes and the outlines the edge was read from.
    """
    made = distances(inputs, found, COUNTS, edition=edition)
    rows = tuple(
        row_of(fact_id(area, FactKind.FEATURE, FEATURE), made.worked[area], METHOD, made.files)
        for area in sorted(made.worked)
    )
    return Nearest(
        worked=made.worked,
        files=made.files,
        stops=made.stops,
        of_oa=made.of_oa,
        found_of_oa=made.found_of_oa,
        edge=made.edge,
        saved=made.saved,
        rows=rows,
        metric=metric_of(made.files, made.saved),
        geography=KEYED_BY,
    )
