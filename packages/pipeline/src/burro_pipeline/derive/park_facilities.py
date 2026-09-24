"""What a park offers: the kinds of play and sports site inside the parks within reach of homes.

The sites and the ways into them come from OS Open Greenspace, which
`green_sites.py` reads. Where homes are comes from the centres of output
areas, which `cells/centres.py` reads.

**It counts kinds of site that the publisher maps, inside parks, within a
straight line.** Core names the measure kinds of thing to do in parks within a
15-minute walk. No network of streets is built, and the file holds sites and
not things to do. So the row of the catalogue that is made here carries a name
of its own, which says what is counted. That name is not core's, so a build
leaves the measure out until core says the same. Do not give it core's name
while it is a straight line.

What is counted, and why. The publisher gives every site one of ten kinds. The
file names the kinds and defines none of them, and no page of the publisher
was opened for this. So the choice rests on the names alone:

| Kind | Read as | Why |
|---|---|---|
| Public Park Or Garden | A park | It is the one kind the publisher names a park |
| Play Space | A kind a park may offer | Play |
| Playing Field | A kind a park may offer | Pitches |
| Tennis Court | A kind a park may offer | Courts |
| Bowling Green | A kind a park may offer | Greens |
| Other Sports Facility | A kind a park may offer | The file does not say which sport |
| Allotments Or Community Growing Spaces | Never counted | A plot is let to one holder |
| Cemetery | Never counted | The design says it never counts |
| Golf Course | Never counted | The design says it never counts |
| Religious Grounds | Never counted | Not a thing to do in a park |

A site of the last four kinds is green and is no park that a person walks in.
It is never read as a park, and never as a kind that a park offers, whether it
stands inside a park or not.

Which parks, and which sites:

- **A park** is a site of any size that the publisher maps as a public park or
  garden, with a way in that is for a person on foot. The nearest park asks 2
  hectares of a park. Nothing is asked here: a small park with a play space
  offers play.
- **Within reach** is a way in on foot within 1,200 metres of where homes are
  taken to stand, in a straight line. It is what a person walks in 15 minutes
  at 80 metres a minute, if the way were straight. The walk is longer.
- **Inside a park** is a site with at least half of its land inside the
  outline of the park. The publisher draws some sites inside a park and some
  beside it. A site that only lies against a park is not counted: the file
  does not say that it is part of the park, and it may be a school's or a
  club's.
- A kind is counted once, however many sites of it the parks hold. A site is
  counted wherever it lies in a park that is within reach, however far into
  the park it is.

How a figure is made:

1. For each output area, the parks with a way in on foot within reach of its
   centre, and the kinds of site inside them: none to five.
2. For each kind, the share of the area's homes that have it within reach.
   That is `homes_within`, which the pipeline design names.
3. An area's figure is the sum of the five shares, which is the mean number of
   kinds over its homes. It is given to one decimal place.

Nothing is filled in. The files are cut to squares of the National Grid, and
each holds every site of its square, inside London or not. So a park outside
London is counted where it is within reach. An output area whose reach takes
in land that no file was read for has no count: a park may lie there. Nor has
one within reach of a park whose outline lies on such land: what the park
offers is not all known. Its homes add nothing, and the coverage of its area
falls by them. Below half the homes covered no figure is given. An output area
whose reach the files cover, with no park in it or with parks that offer
nothing, counts none, and nought is what it adds.

The design asks that 20 named commons, heaths and forests are looked for in
the file before any figure of parks is shown. That check has not been made:
the list is the founder's to give.
"""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace

from burro_core.facts import fact_id
from burro_core.ids import FactKind, FeatureId, NativeResolution
from burro_core.release import Metric

from burro_pipeline.cells import centres
from burro_pipeline.cells.centres import Point
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import green_sites, park_proximity
from burro_pipeline.derive.catalogue_row import catalogue_row
from burro_pipeline.derive.green_sites import Greenspace
from burro_pipeline.derive.methods import (
    Worked,
    cell_of,
    homes_within,
    homes_within_at,
    row_of,
    to_places,
)
from burro_pipeline.derive.park_proximity import Parks
from burro_pipeline.derive.park_shapes import held_by
from burro_pipeline.evidence.method import Kind, Method
from burro_pipeline.evidence.receipt import Geography, Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

FEATURE = FeatureId.PARK_FACILITIES
SOURCE = green_sites.SOURCE
# The one kind of site that is a park, of any size.
PARK, LEAST = green_sites.PARK, 0
# The kinds of site a park may offer, as the publisher writes them.
KINDS = (
    "Bowling Green",
    "Other Sports Facility",
    "Play Space",
    "Playing Field",
    "Tennis Court",
)
# The kinds that are never a park and never a kind a park offers.
NEVER = (
    "Allotments Or Community Growing Spaces",
    "Cemetery",
    "Golf Course",
    "Religious Grounds",
)
# How far a way into a park may be from where homes stand, in metres, in a straight line.
REACH = 1_200
# The least share of a site's land that lies inside a park, for the site to be inside it.
INSIDE, INSIDE_IN_100 = 0.5, 50
# The ways in are kept by squares this wide while those within reach are looked for, in metres.
KEPT_BY = 1_000
# A figure is given to this many decimal places.
DECIMALS = 1
# What the sites are keyed by, as the parser finds them. No receipt says it yet.
KEYED_BY = Geography.POINT
PUBLISHER, PRODUCT = green_sites.PUBLISHER, park_proximity.PRODUCT
CENSUS = park_proximity.CENSUS

METHOD = Method(
    derivation_id=f"kinds_in_parks_within_{REACH}m@1",
    sentence=f"The number of kinds of site, of {len(KINDS)} that are counted, that lie inside "
    f"the parks with a way in on foot within {REACH} metres, in a straight line, of the point "
    "where the homes of each census output area are taken to stand, a site being inside a park "
    f"where at least {INSIDE_IN_100} in 100 of its land lies inside the outline of the park, as "
    "the mean over the area's homes at the census, which is the sum over the kinds of the share "
    "of homes that have the kind within reach, and not given where under 50 in 100 of the "
    "area's homes are in an output area whose reach the files cover.",
    kind=Kind.MEASURED,
    parameters={
        "metres": REACH,
        "kinds": len(KINDS),
        "inside_in_100": INSIDE_IN_100,
        "enough_in_100": 50,
    },
    code="burro_pipeline.derive.park_facilities",
)
# The arithmetic, and the share of homes it is a sum of. The first is the one a row names.
METHODS: tuple[Method, ...] = (METHOD, homes_within_at(REACH))
# What a person reads beside the figure: what is counted, where, and that it is a straight line.
LABEL = "Kinds of play and sports site in parks within 1,200 m in a straight line"
# What the measure is, from whom, for what period, and what it is not.
DEFINITION = (
    "The number of kinds of site, of the {count} kinds {kinds}, that {publisher} maps in "
    "{product} as at {sites} with at least half of their land inside the outline of a site of "
    "any size that it maps as {park}, where that site has a way in on foot within {reach} "
    "metres in a straight line of the point the statistics office gives as the centre of each "
    "census output area, inside London or outside it, as the mean over the area's homes at the "
    "census of {census} and given to {decimals} decimal place with a half taken upward: a kind "
    "is counted once however many sites of it there are, the reach is measured across whatever "
    "lies between and not along any street or path, so the walk is longer, and a cemetery, a "
    "golf course, an allotment and religious grounds are never counted as a park or as a kind."
)
# What keeps the measure out of a release, and whose it is to settle.
WAITS_ON = (
    "Core names the measure kinds of thing to do in parks within a 15-minute walk, and the "
    "figure counts kinds of play and sports site inside parks with a marked way in within "
    "1,200 metres in a straight line. A name in core that says what is counted settles it, or "
    "a walk worked out on a network of streets.",
)
# What the product shows beside the figure.
CANNOT_SEE = (
    "This counts kinds of site and not how many there are or how good, so one small play space "
    "counts as much as several, and it cannot tell whether a court or a pitch is free to use, "
    "needs booking or is open to all.",
    "It counts only what its publisher maps as a site of its own inside a site it maps as a "
    "public park or garden, so a play space or a court on a playing field that is mapped as no "
    "park is not counted, nor is a pitch marked out on the grass, a path to run on, a cafe or a "
    "lake, nor a site drawn beside a park, and the reach is a straight line and not a walk.",
)


@dataclass(frozen=True)
class Counted:
    """How many sites of one kind the files hold, and how many of them lie inside a park."""

    sites: int
    inside_a_park: int


@dataclass(frozen=True)
class Offers:
    """What each park offers, and what was counted on the way."""

    # The parks, of any size, and the ways into them on foot.
    parks: Parks
    # The way in on foot and the park it is into, for every such way in.
    ways_in: tuple[tuple[Point, str], ...]
    # The kinds of site inside each park that holds any, in the order of `KINDS`.
    of_park: Mapping[str, tuple[str, ...]]
    # The sites of each kind that may be counted, and of each kind that never is.
    counted: Mapping[str, Counted]
    never: Mapping[str, Counted]


@dataclass(frozen=True)
class Within:
    """What is within reach of each output area whose reach the files cover."""

    # The kinds of site in the parks within reach, in the order of `KINDS`.
    kinds: Mapping[str, tuple[str, ...]]
    # The parks within reach.
    parks: Mapping[str, tuple[str, ...]]


@dataclass(frozen=True)
class Facilities:
    """What parks offer within reach of the homes of every area, with what stands behind it."""

    # The figure of each area, by its id. An area with no figure is here too, with its state.
    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    metric: Metric
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    geography: Geography
    offers: Offers
    within: Within
    # For each kind, the share of each area's homes with the kind within reach.
    shares: Mapping[str, Mapping[str, Worked]]


def is_a_tile(name: str) -> bool:
    """Whether a publisher's name for a file is the name of a file this measure reads."""
    return green_sites.is_a_tile(name)


def offers_of(green: Greenspace) -> Offers:
    """What each park offers: the kinds of site with at least half their land inside it.

    A park with no way in on foot is no park here, as it is none for the
    nearest park: the file does not say how a person gets in.
    """
    parks = park_proximity.sites_of(green, PARK, LEAST)
    ways_in = sorted(
        (way.point, way.site_id)
        for way in green.ways_in
        if way.on_foot and green.sites[way.site_id].kind == PARK
    )
    reached = {site_id for _, site_id in ways_in}
    every = {site_id: site.shape for site_id, site in green.sites.items() if site.kind == PARK}
    others = {
        site_id: site.shape
        for site_id, site in green.sites.items()
        if site.kind in KINDS or site.kind in NEVER
    }
    inside = held_by(others, every, INSIDE)
    of_park: dict[str, set[str]] = {}
    for site_id in sorted(inside):
        kind = green.sites[site_id].kind
        for park in inside[site_id]:
            if kind in KINDS and park in reached:
                of_park.setdefault(park, set()).add(kind)

    def counted(kind: str) -> Counted:
        of_kind = [site_id for site_id in inside if green.sites[site_id].kind == kind]
        return Counted(len(of_kind), sum(bool(inside[site_id]) for site_id in of_kind))

    return Offers(
        parks=parks,
        ways_in=tuple(ways_in),
        of_park={
            park: tuple(kind for kind in KINDS if kind in of_park[park]) for park in sorted(of_park)
        },
        counted={kind: counted(kind) for kind in KINDS},
        never={kind: counted(kind) for kind in NEVER},
    )


class _Kept:
    """Ways in, kept by the square each stands on, so that those within reach are found near."""

    def __init__(self, ways_in: Sequence[tuple[Point, str]]) -> None:
        self._on: dict[tuple[int, int], list[tuple[Point, str]]] = {}
        for point, park in ways_in:
            self._on.setdefault(cell_of(*point, KEPT_BY), []).append((point, park))

    def parks_within(self, point: Point, metres: int) -> tuple[str, ...]:
        """The parks with a way in no further than so many metres from a point."""
        low = cell_of(point[0] - metres, point[1] - metres, KEPT_BY)
        high = cell_of(point[0] + metres, point[1] + metres, KEPT_BY)
        found: set[str] = set()
        for across in range(low[0], high[0] + KEPT_BY, KEPT_BY):
            for up in range(low[1], high[1] + KEPT_BY, KEPT_BY):
                for other, park in self._on.get((across, up), ()):
                    if math.hypot(other[0] - point[0], other[1] - point[1]) <= metres:
                        found.add(park)
        return tuple(sorted(found))


def within_reach(green: Greenspace, offers: Offers, points: Mapping[str, Point]) -> Within:
    """The parks within reach of each output area, and the kinds of site inside them.

    An output area is left out where it has no centre, where its reach takes
    in land that no file was read for, and where a park within its reach lies
    on such land: what is within its reach is then not all known.
    """
    kept = _Kept(offers.ways_in)
    kinds: dict[str, tuple[str, ...]] = {}
    parks: dict[str, tuple[str, ...]] = {}
    for oa in sorted(points):
        if green.beyond(points[oa]) <= REACH:
            continue
        near = kept.parks_within(points[oa], REACH)
        if any(green.files_under(green.sites[park].shape) is None for park in near):
            continue
        offered = {kind for park in near for kind in offers.of_park.get(park, ())}
        parks[oa] = near
        kinds[oa] = tuple(kind for kind in KINDS if kind in offered)
    return Within(kinds=kinds, parks=parks)


def shares_of(within: Within, found: Spine) -> dict[str, dict[str, Worked]]:
    """For each kind, the share of each area's homes that have the kind within reach."""
    return {
        kind: homes_within({oa: kind in kinds for oa, kinds in within.kinds.items()}, found.weights)
        for kind in KINDS
    }


def figures(shares: Mapping[str, Mapping[str, Worked]], found: Spine) -> dict[str, Worked]:
    """The figure of every area: the sum of the five shares, to one decimal place.

    The five shares of an area are of the same homes, so they are covered
    alike and have a value or none together.
    """
    worked: dict[str, Worked] = {}
    for area in found.weights.areas:
        each = [shares[kind][area] for kind in KINDS]
        values = [one.value for one in each if one.value is not None]
        if len({(one.weight_covered, one.state, one.units_used) for one in each}) != 1:
            raise ValueError("the shares of an area are of the same homes")
        worked[area] = replace(
            each[0],
            value=to_places(math.fsum(values), DECIMALS) if len(values) == len(each) else None,
        )
    return worked


def definition_of(as_at: str) -> str:
    """The sentence a methods page prints for the measure."""
    return DEFINITION.format(
        count="five",
        kinds=", ".join(KINDS[:-1]) + " and " + KINDS[-1],
        publisher=PUBLISHER,
        product=PRODUCT,
        sites=as_at,
        park=PARK,
        reach=f"{REACH:,}",
        census=CENSUS,
        decimals="one",
    )


def metric_of(files: Sequence[Receipt], as_at: str) -> Metric:
    """The row of the catalogue: the name, the unit, the period and every source.

    Core decides the unit and which way is more. The name is `LABEL`: the one
    the figure supports, which is not core's. It is measured from points, and
    on no network.
    """
    return catalogue_row(
        FEATURE,
        method=METHOD,
        label=LABEL,
        native_resolution=NativeResolution.POINT,
        source_ids={receipt.source_id for receipt in files},
        vintage=as_at,
        definition=definition_of(as_at),
    )


def _files_of(
    green: Greenspace, within: Within, points: Mapping[str, Point], found: Spine
) -> dict[str, tuple[str, ...]]:
    """For each area, the files of sites its figure rests on.

    A count rests on the file of every square that lies within reach of the
    home, and of every square that a park within reach lies on. An area with
    no count rests on every file that was read.
    """
    every = tuple(receipt.file_id for receipt in green.files)
    behind: dict[str, set[str]] = {area.area_id: set() for area in found.areas}
    for oa in sorted(within.kinds):
        rests_on = set(green.files_within(points[oa], REACH))
        for park in within.parks[oa]:
            rests_on |= set(green.files_under(green.sites[park].shape) or ())
        behind[found.area_of[oa]] |= rests_on
    return {area: tuple(sorted(files)) or every for area, files in behind.items()}


def build(inputs: Inputs, found: Spine, *, edition: str | None = None) -> Facilities:
    """What parks offer within reach of the homes of every area, and its evidence.

    The gate is asked about the sites and about the centres before either is
    read. `found` is the spine of the same build. A row of evidence names the
    files of sites its figure rests on, the centres, the lookup and the table
    of homes.
    """
    green = green_sites.build(inputs, edition=edition)
    placed = inputs.open(centres.CENTRES, Use.SCORING, edition=centres.CENTRES_EDITION)
    handed = {one.file_id: one.receipt for one in inputs.opened}
    if not set(found.inputs) <= set(handed):
        raise ValueError("the spine is made from files of this build")
    points = centres.centres_of(placed, found)
    offers = offers_of(green)
    within = within_reach(green, offers, points)
    shares = shares_of(within, found)
    worked = figures(shares, found)
    ground = sorted({placed.file_id, *found.inputs})
    of_sites = _files_of(green, within, points, found)
    rows = tuple(
        row_of(
            fact_id(area, FactKind.FEATURE, FEATURE),
            worked[area],
            METHOD,
            [handed[file_id] for file_id in sorted({*of_sites[area], *ground})],
        )
        for area in sorted(worked)
    )
    behind = sorted({receipt.file_id for receipt in green.files} | set(ground))
    files = tuple(handed[file_id] for file_id in behind)
    return Facilities(
        worked=worked,
        rows=rows,
        metric=metric_of(files, green.as_at),
        files=files,
        geography=KEYED_BY,
        offers=offers,
        within=within,
        shares=shares,
    )
