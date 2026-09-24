"""The nearest park: how far it is, in a straight line, from where homes are to a way in.

The sites and the ways into them come from OS Open Greenspace, which
`green_sites.py` reads. Where homes are comes from the centres of output
areas, which `cells/centres.py` reads.

**It is a straight line, and not a walk.** The pipeline design works a walk out
on a network of streets, and no such network is built yet. So the figure is
the distance across whatever lies between, and the row of the catalogue that
is made here says so in its name. Core names the measure the same, so a build
carries it. Do not give it a name that says a walk while it is a straight
line.

What counts as a park, and why:

- A site that the publisher maps as `Public Park Or Garden`. It is the one
  kind of the ten that the publisher names a park. The file names the kinds
  and defines none of them, and no page of the publisher was opened for this.
- Of at least 2 hectares, as the publisher draws the site. For a large park,
  of at least 20. Both sizes are the design's. A park that the publisher draws
  as several sites is as many parks, each of its own size.
- With a way in that is for a person on foot. The publisher marks each way in
  as for walkers, for motor vehicles, or for both. A way in for motor vehicles
  alone is not counted, and a park with no way in on foot is not counted at
  all: the file does not say how a person gets in.

How a figure is made:

1. For each output area, the distance from its centre to the nearest way in
   that counts.
2. An area's figure is the median of those distances over its homes: half the
   area's homes are in an output area no further than this from a way in.
3. It is given to the nearest 10 metres. A home may stand a hundred metres
   from the centre of its output area, so a metre would claim too much.

Nothing is filled in. The files are cut to squares of the National Grid, and
each holds the ways in that lie on its square. A home nearer to a square that
was not read than to any way in that was found may have a nearer park there.
Its distance is not known, it adds nothing, and the coverage of its area falls
by its homes. Below half the homes covered no figure is given.

The large park is a measure of its own in core's catalogue. It is made here
the same way, to a park of 20 hectares or more, and a build carries both.

The design asks that 20 named commons, heaths and forests are looked for in
the file before any figure of parks is shown. That check has not been made:
the list is the founder's to give.
"""

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace

from burro_core.facts import fact_id
from burro_core.ids import FactKind, FeatureId, NativeResolution
from burro_core.release import Metric

from burro_pipeline.cells import centres
from burro_pipeline.cells.centres import Point
from burro_pipeline.cells.spine import Homes, Spine
from burro_pipeline.derive import green_sites
from burro_pipeline.derive.catalogue_row import catalogue_row
from burro_pipeline.derive.green_sites import Greenspace
from burro_pipeline.derive.methods import DECIMALS as SHARE_DECIMALS
from burro_pipeline.derive.methods import ENOUGH, Worked, cell_of, row_of, to_places
from burro_pipeline.evidence.method import Kind, Method
from burro_pipeline.evidence.receipt import Geography, Receipt
from burro_pipeline.evidence.row import EvidenceRow, State, state_of
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

FEATURE = FeatureId.PARK_PROXIMITY
# The same distance, to a large park.
LARGE = FeatureId.PARK_LARGE_PROXIMITY
SOURCE = green_sites.SOURCE
# The one kind of site that counts.
COUNTS = green_sites.PARK
# The least a park may be, in hectares, and the least a large park may be.
LEAST, LEAST_LARGE = 2, 20
# A figure is given to the nearest so many metres, which is this many decimal places.
NEAREST, DECIMALS = 10, -1
# The ways in are kept by squares this wide while the nearest is looked for, in metres.
KEPT_BY = 1_000
# What the ways in are keyed by, as the parser finds them. No receipt says it yet.
KEYED_BY = Geography.POINT
PUBLISHER, PRODUCT = green_sites.PUBLISHER, "OS Open Greenspace"
CENSUS = 2021

STRAIGHT_LINE = Method(
    derivation_id="straight_line_to_nearest@1",
    sentence="The distance in a straight line from the point where the homes of each census "
    "output area are taken to stand to the nearest of the points that count, as the median over "
    "the area's homes at the census, which is the mean of the two middle distances where the "
    "homes divide exactly in half between them, and not given where under 50 in 100 of the "
    "area's homes are in an output area whose nearest point is known.",
    kind=Kind.MEASURED,
    parameters={"enough_in_100": 50},
    code="burro_pipeline.derive.park_proximity",
)
METHOD = STRAIGHT_LINE
METHODS: tuple[Method, ...] = (METHOD,)
# What a person reads beside the figure: it is a straight line, and no walk. It is measured
# to a way in that the publisher marks, and not to the edge of the park, so the name says a
# way in. It is core's name for the measure too.
LABEL = "Straight-line distance to the nearest marked way into a park of {least} ha or more"
# What the measure is, from whom, for what period, and what it is not.
DEFINITION = (
    "The distance in a straight line, in metres, from the point the statistics office gives as "
    "the centre of each census output area to the nearest way in on foot to a site of {least} "
    "hectares or more that {publisher} maps as {counts} in {product} as at {sites}, as the "
    "median over the area's homes at the census of {census} and given to the nearest {nearest} "
    "metres with a half taken upward: it is measured across whatever lies between and not "
    "along any street or path, so the walk is longer, a site is as large as its publisher "
    "draws it, and a site with no way in on foot marked is not counted."
)
# What the product shows beside the figure.
CANNOT_SEE = (
    "This is a straight line from where the homes of each small census area are taken to stand "
    "to the nearest marked way into a park, and not a walk, so a railway, a river or a main "
    "road in between makes the real walk longer.",
    "A park is a site its publisher maps as a public park or garden, so a common or a wood "
    "counts only where it is mapped as one, and a park drawn as several smaller sites may fall "
    "under the size asked for.",
)


@dataclass(frozen=True)
class Parks:
    """The parks that count, and the ways into them that a person on foot may take."""

    # The least a park may be, in hectares.
    least: int
    ways_in: tuple[Point, ...]
    # How many parks are of that size, and how many of them have no way in on foot.
    parks: int
    without_a_way_in: int


@dataclass(frozen=True)
class Distances:
    """The distance to the nearest park for every area, with what stands behind each figure."""

    # The figure of each area, by its id. An area with no figure is here too, with its state.
    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    geography: Geography
    parks: Parks
    # The distance of each output area whose nearest way in is known, in metres.
    of_oa: Mapping[str, float]


@dataclass(frozen=True)
class Proximity(Distances):
    """The same, with the row of the catalogue of the measure."""

    metric: Metric


def is_a_tile(name: str) -> bool:
    """Whether a publisher's name for a file is the name of a file this measure reads."""
    return green_sites.is_a_tile(name)


def sites_of(green: Greenspace, kind: str, least: int) -> Parks:
    """The sites of one kind of at least so many hectares, and every way into one on foot.

    It is what is measured to, whatever the kind. A measure of another kind of
    site hands the kind over, and is worked out as the nearest park is.
    """
    of_size = {
        site_id
        for site_id, site in green.sites.items()
        if site.kind == kind and site.hectares >= least
    }
    ways_in = [way for way in green.ways_in if way.site_id in of_size and way.on_foot]
    reached = {way.site_id for way in ways_in}
    return Parks(
        least=least,
        ways_in=tuple(sorted({way.point for way in ways_in})),
        parks=len(of_size),
        without_a_way_in=len(of_size - reached),
    )


def parks_of(green: Greenspace, least: int) -> Parks:
    """The parks of at least so many hectares, and every way into one on foot."""
    return sites_of(green, COUNTS, least)


class _Near:
    """Points, kept by the square each stands on, so that the nearest is found by looking near."""

    def __init__(self, points: Sequence[Point]) -> None:
        self._on: dict[tuple[int, int], list[Point]] = {}
        for point in points:
            self._on.setdefault(cell_of(*point, KEPT_BY), []).append(point)
        across = [corner[0] for corner in self._on]
        up = [corner[1] for corner in self._on]
        self._box = (min(across), min(up), max(across), max(up)) if self._on else None

    def nearest(self, point: Point) -> float | None:
        """How far a point is from the nearest of the points, or none if there is no point."""
        if self._box is None:
            return None
        own = cell_of(*point, KEPT_BY)
        west, south, east, north = self._box
        furthest = max(
            abs(own[0] - west), abs(own[0] - east), abs(own[1] - south), abs(north - own[1])
        )
        best, ring = math.inf, 0
        # A point on a square so many squares away is at least one square fewer away.
        while (ring - 1) * KEPT_BY < best and ring * KEPT_BY <= furthest:
            for corner in _round(own, ring):
                for other in self._on.get(corner, ()):
                    best = min(best, math.hypot(other[0] - point[0], other[1] - point[1]))
            ring += 1
        return best


def _round(own: tuple[int, int], ring: int) -> list[tuple[int, int]]:
    """The squares that stand so many squares from a square, in a ring round it."""
    if ring == 0:
        return [own]
    reach = range(-ring, ring + 1)
    return [
        (own[0] + across * KEPT_BY, own[1] + up * KEPT_BY)
        for across in reach
        for up in reach
        if max(abs(across), abs(up)) == ring
    ]


def distances(green: Greenspace, parks: Parks, points: Mapping[str, Point]) -> dict[str, float]:
    """The distance from each output area to the nearest way in, where it is known.

    It is not known where an output area has no centre, where no way in was
    found, and where land that no file was read for is nearer than the
    nearest way in that was found: a nearer way in may lie there.
    """
    near = _Near(parks.ways_in)
    found: dict[str, float] = {}
    for oa in sorted(points):
        nearest = near.nearest(points[oa])
        if nearest is not None and nearest <= green.beyond(points[oa]):
            found[oa] = nearest
    return found


def _median(weighed: Sequence[tuple[float, float]]) -> float:
    """The median of some distances, each with its weight: half the weight is no further.

    Where the weight divides exactly in half between two distances, it is the
    mean of the two, as the median of an even count is.
    """
    ordered = sorted(one for one in weighed if one[1] > 0)
    half = math.fsum(weight for _, weight in ordered) / 2
    reached = 0.0
    for at, (distance, weight) in enumerate(ordered):
        reached += weight
        if reached > half:
            return distance
        if reached == half:
            return (distance + ordered[at + 1][0]) / 2
    raise ValueError("a median is of distances that weigh something")


def median_by_homes(of_oa: Mapping[str, float], homes: Homes) -> dict[str, Worked]:
    """The median distance over each area's homes, or why an area has no figure.

    `of_oa` holds the output areas whose distance is known. One whose
    distance is not known adds nothing, and the area's coverage falls by its
    homes. Below half the homes covered no figure is given. An area with no
    homes at all is weighed by how many of its output areas have a distance.
    """
    found: dict[str, Worked] = {}
    for area in homes.areas:
        every = homes.of_area[area]
        used = [oa for oa in every if oa in of_oa]
        by_count = homes.weight(every, by_count=False) == 0
        whole = homes.weight(every, by_count)
        covered = to_places(homes.weight(used, by_count) / whole, SHARE_DECIMALS) if whole else 0.0
        if covered == 0:
            found[area] = Worked(None, 0, len(every), 0.0, State.SOURCE_GAP)
        elif covered < ENOUGH:
            found[area] = Worked(None, len(used), len(every), covered, State.BELOW_THRESHOLD)
        else:
            value = _median([(of_oa[oa], homes.weight([oa], by_count)) for oa in used])
            found[area] = Worked(value, len(used), len(every), covered, state_of(True, covered))
    return found


def figures(of_oa: Mapping[str, float], found: Spine) -> dict[str, Worked]:
    """The figure of every area of the spine, to the nearest 10 metres, or why it has none."""
    worked = median_by_homes(of_oa, found.weights)
    return {
        area: one if one.value is None else replace(one, value=to_places(one.value, DECIMALS))
        for area, one in worked.items()
    }


def definition_of(as_at: str, least: int) -> str:
    """The sentence a methods page prints for the measure, for a park of at least so large."""
    return DEFINITION.format(
        least=least,
        publisher=PUBLISHER,
        counts=COUNTS,
        product=PRODUCT,
        sites=as_at,
        census=CENSUS,
        nearest=NEAREST,
    )


def metric_of(
    files: Sequence[Receipt], as_at: str, feature: FeatureId = FEATURE, least: int = LEAST
) -> Metric:
    """The row of the catalogue: the name, the unit, the period and every source.

    Core decides the unit and which way is more. The name is `LABEL`: the one
    the figure supports, which core gives it too. It is measured from points,
    and on no network.
    """
    return catalogue_row(
        feature,
        method=METHOD,
        label=LABEL.format(least=least),
        native_resolution=NativeResolution.POINT,
        source_ids={receipt.source_id for receipt in files},
        vintage=as_at,
        definition=definition_of(as_at, least),
    )


def _files_of(
    green: Greenspace, of_oa: Mapping[str, float], points: Mapping[str, Point], found: Spine
) -> dict[str, tuple[str, ...]]:
    """For each area, the files of sites its figure rests on.

    A distance rests on the file of every square that lies no further from
    the home than the way in that was found: a nearer way in could lie on no
    other. An area with no distance rests on every file that was read.
    """
    every = tuple(receipt.file_id for receipt in green.files)
    within: dict[str, set[str]] = {area.area_id: set() for area in found.areas}
    for oa in sorted(of_oa):
        within[found.area_of[oa]] |= set(green.files_within(points[oa], of_oa[oa]))
    return {area: tuple(sorted(files)) or every for area, files in within.items()}


def to_the_nearest(
    inputs: Inputs,
    found: Spine,
    key: str,
    counts: Callable[[Greenspace], Parks],
    edition: str | None,
) -> tuple[Distances, Greenspace]:
    """The distance from where homes are to the nearest site that counts, for every area.

    `counts` says which sites count, and gives the ways into them. `key` is
    the id of the measure the rows of evidence are of. The gate is asked about
    the sites and about the centres before either is read.
    """
    green = green_sites.build(inputs, edition=edition)
    placed = inputs.open(centres.CENTRES, Use.SCORING, edition=centres.CENTRES_EDITION)
    handed = {one.file_id: one.receipt for one in inputs.opened}
    if not set(found.inputs) <= set(handed):
        raise ValueError("the spine is made from files of this build")
    points = centres.centres_of(placed, found)
    parks = counts(green)
    of_oa = distances(green, parks, points)
    worked = figures(of_oa, found)
    ground = sorted({placed.file_id, *found.inputs})
    of_sites = _files_of(green, of_oa, points, found)
    rows = tuple(
        row_of(
            fact_id(area, FactKind.FEATURE, key),
            worked[area],
            METHOD,
            [handed[file_id] for file_id in sorted({*of_sites[area], *ground})],
        )
        for area in sorted(worked)
    )
    behind = sorted({receipt.file_id for receipt in green.files} | set(ground))
    files = tuple(handed[file_id] for file_id in behind)
    return Distances(worked, rows, files, KEYED_BY, parks, of_oa), green


def _proximity(
    inputs: Inputs, found: Spine, feature: FeatureId, least: int, edition: str | None
) -> Proximity:
    made, green = to_the_nearest(
        inputs, found, feature, lambda green: parks_of(green, least), edition
    )
    return Proximity(
        worked=made.worked,
        rows=made.rows,
        files=made.files,
        geography=made.geography,
        parks=made.parks,
        of_oa=made.of_oa,
        metric=metric_of(made.files, green.as_at, feature, least),
    )


def build(inputs: Inputs, found: Spine, *, edition: str | None = None) -> Proximity:
    """The distance to the nearest park for every area, and its evidence.

    The gate is asked about the sites and about the centres before either is
    read. `found` is the spine of the same build. A row of evidence names the
    files of sites its figure rests on, the centres, the lookup and the table
    of homes.
    """
    return _proximity(inputs, found, FEATURE, LEAST, edition)


def build_large(inputs: Inputs, found: Spine, *, edition: str | None = None) -> Proximity:
    """The same, to the nearest park of 20 hectares or more."""
    return _proximity(inputs, found, LARGE, LEAST_LARGE, edition)
