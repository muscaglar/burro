"""The nearest food shop: how far it is, in a straight line, from where homes are.

The shops come from one file of Overture Maps Places, which `culture_file.py`
reads: the kind and the point of each record, and nothing else of it. Which
category is a food shop is in `food_shop_kinds.py`: a grocer or supermarket,
and a convenience store. Where homes are comes from the centres of output
areas, which `cells/centres.py` reads.

**It is a straight line, in metres, and not a walk.** No network of streets is
built, so no walk can be worked out, and a straight line is not turned into
minutes here. The row of the catalogue says a straight line and metres, as
core names the measure. The id says a walk, because an id is never renamed.
Do not name the figure a walk, or give it in minutes, while it is a straight
line.

How a figure is made, which is how the distance to a station is made:

1. For each output area, the distance from its centre to the nearest shop
   that counts. A shop is a point, as its file gives it, put on the National
   Grid by the pipeline's one fixed operation, which is good to 2 metres.
2. An area's figure is the median of those distances over its homes: half the
   area's homes are in an output area no further than this from a food shop.
3. It is given to the nearest 10 metres.

**What is not read, and what is not left out.** No name is read, and no brand:
the list takes no column that names a business. A record that its file says
has closed for good is left out, and a record with no point is put nowhere.
No record is left out for how sure its publisher is that the place exists.
Two records of one shop are one distance, so nothing is made of how near two
records stand.

**The edge of what was taken.** Fetch takes the part of the file that lies in
a box round London, which reaches at least 2,000 metres beyond London's homes.
A shop beyond the box may not be in the part. So the distance of an output
area is known only where the nearest shop that was found is no further than
the nearest side of the box: no shop beyond it could be nearer. Where it is
not known the output area adds nothing, the coverage of its area falls by its
homes, and below half the homes covered no figure is given. A file that was
kept whole has no edge.

**What the figure follows.** `test_grocery_walk_on_the_real_files.py` holds
the figures of London. A food shop is nearer where homes stand closer
together, so the figure stands mostly in the order of how built up an area
is. `CANNOT_SEE` says what else it cannot tell.

Nothing is filled in. A distance that is not known is never taken to be the
distance that was found.
"""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from burro_core.facts import fact_id
from burro_core.ids import FactKind, FeatureId, NativeResolution
from burro_core.release import Metric

from burro_pipeline.cells import centres
from burro_pipeline.cells.centres import Point
from burro_pipeline.cells.shapes import longitude_and_latitude, on_the_grid
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import culture_file, park_proximity, places_counted
from burro_pipeline.derive.catalogue_row import catalogue_row
from burro_pipeline.derive.culture_file import Record
from burro_pipeline.derive.culture_reach import metres_to_a_degree
from burro_pipeline.derive.culture_venues import AS_AT_THE_CENSUS, HOW_SURE, OF_THE_RELEASE
from burro_pipeline.derive.food_shop_kinds import KINDS, SAID, Kind, LeftOut, kind_of
from burro_pipeline.derive.methods import Worked, row_of
from burro_pipeline.derive.places_counted import Held
from burro_pipeline.derive.station_shapes import to_the_nearest_point
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Method
from burro_pipeline.evidence.receipt import Geography, Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

FEATURE = FeatureId.GROCERY_WALK
SOURCE = culture_file.SOURCE
PUBLISHER = culture_file.PUBLISHER
# The method is the one the distance to a park and to a station is worked out by.
METHOD: Method = park_proximity.STRAIGHT_LINE
METHODS: tuple[Method, ...] = (METHOD,)
# The figure is in metres, and never in minutes.
UNIT = "m"
# A figure is given to the nearest so many metres.
NEAREST = park_proximity.NEAREST
# What the shops are keyed by, as the parser finds them.
KEYED_BY = Geography.POINT
CENSUS = 2021
# The reasons for a record that is no record of a food shop, which is most of any file.
PASSED_BY = (LeftOut.NOT_A_FOOD_SHOP, LeftOut.NO_CATEGORY)
# The sides of a box, in the order a receipt writes them.
WEST, SOUTH, EAST, NORTH = range(4)
# What a person reads beside the figure: it is a straight line, and no walk.
LABEL = "Straight-line distance to the nearest food shop"
# What the measure is, from whom, for what period, and what it is not.
DEFINITION = (
    "The distance in a straight line, in metres, from the point the statistics office gives as "
    "the centre of each census output area to the nearest place that release {release} of "
    "Overture Maps Places, of the {publisher}, as at {as_at}, gives a category of {kinds}, "
    "leaving out a record that its file says has closed for good, as the median over the "
    "area's homes at the census of {census} and given to the nearest {nearest} metres with a "
    "half taken upward: it is measured across whatever lies between and not along any street, "
    "so the walk is longer, a shop the file does not hold is not seen, nothing says how large "
    "a shop is or what it sells, and a home whose nearest shop that was found is further off "
    "than the edge of the part of the file that was taken is left out, because a nearer shop "
    "may stand beyond it."
)
# What the product shows beside the figure. Each line has a name, so that it is taken by
# what it says and never by where it stands.
A_STRAIGHT_LINE = (
    "This is a straight line from where the homes of each small census area are taken to stand "
    "to the nearest food shop, and not a walk, so a railway, a river or a main road in between "
    "makes the real walk longer."
)
WHAT_COUNTS = (
    "A food shop is a place its file gives as a grocer, a supermarket or a convenience store, "
    "so a butcher, a baker, a greengrocer and a market are not counted, and nothing is decided "
    "from a name."
)
HOW_LARGE = (
    "Nothing says how large a shop is, what it sells, what it costs or when it is open, so a "
    "corner shop counts as a supermarket does."
)
GATHERED = (
    "The file is gathered from what businesses and others have put on the web and not from a "
    "register, so a shop the file does not hold is not seen, and the figure then reads further "
    "than the nearest shop is."
)
ON_THE_FILE = (
    "A shop that has closed is counted unless the file says it has closed for good, which it "
    "says of almost none, so the figure may read nearer than the nearest shop that trades."
)
AT_THE_EDGE = (
    "The file was taken for a box round London, so a home whose nearest shop that was found is "
    "further off than the edge of that box is left out of the figure, because a nearer shop "
    "may stand beyond it."
)
CANNOT_SEE = (
    A_STRAIGHT_LINE,
    WHAT_COUNTS,
    HOW_LARGE,
    GATHERED,
    ON_THE_FILE,
    HOW_SURE,
    OF_THE_RELEASE,
    AT_THE_EDGE,
    AS_AT_THE_CENSUS,
)


@dataclass(frozen=True)
class Nearest:
    """The distance to the nearest food shop for every area, with what stands behind it."""

    # The figure of each area, by its id. An area with no figure is here too, with its state.
    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    metric: Metric
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    geography: Geography
    # What the file holds of food shops, record by record. No name of a place is here.
    held: Held
    # The distance that was found for each output area that has a centre, known or not.
    found_of_oa: Mapping[str, float]
    # The distance of each output area whose nearest shop is known, in metres.
    of_oa: Mapping[str, float]
    # The output areas whose distance is not known: the shop that was found is further off
    # than the edge of what was taken.
    beyond_the_edge: tuple[str, ...]


def is_the_file(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the file this measure reads."""
    return culture_file.is_the_file(name)


def decide(record: Record) -> Kind | LeftOut:
    """What a record is, by the table of kinds of food shop."""
    return kind_of(record.primary, record.hierarchy)


def to_the_edge_of(box: Sequence[float], at: Point) -> float:
    """How far a point stands inside a box, in metres on the ground: to its nearest side.

    The point and the box are in degrees: a longitude and a latitude, and
    west, south, east and north. A point outside the box stands no distance
    inside it.
    """
    across, up = metres_to_a_degree(at[1])
    inside = min(
        (at[0] - box[WEST]) * across,
        (box[EAST] - at[0]) * across,
        (at[1] - box[SOUTH]) * up,
        (box[NORTH] - at[1]) * up,
    )
    return max(inside, 0.0)


def known(
    found: Mapping[str, float], points: Mapping[str, Point], box: Sequence[float] | None
) -> dict[str, float]:
    """The distances that are known: the shop that was found is no further than the edge.

    `points` are the centres on the National Grid, and `box` what was taken of
    the file, in degrees. With no box the file was kept whole, and every
    distance that was found is known. With no shop at all nothing was found.
    """
    return {
        oa: far
        for oa, far in found.items()
        if math.isfinite(far)
        and (box is None or far <= to_the_edge_of(box, longitude_and_latitude(*points[oa])))
    }


def definition_of(held: Held) -> str:
    """The sentence a methods page prints: what is counted, from whom, as at when, and what not."""
    return DEFINITION.format(
        release=held.file.edition,
        publisher=PUBLISHER,
        as_at=held.as_at,
        kinds=SAID,
        census=CENSUS,
        nearest=NEAREST,
    )


def metric_of(files: Sequence[Receipt], held: Held) -> Metric:
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
        vintage=held.as_at,
        definition=definition_of(held),
    )
    return row.replace(unit=UNIT)


def build(inputs: Inputs, found: Spine, *, edition: str | None = None) -> Nearest:
    """The distance to the nearest food shop for every area, and its evidence.

    The gate is asked about the places and about the centres before either is
    read. `found` is the spine of the same build. `edition` is the release of
    the places, as its receipt gives it. A row of evidence names the file of
    places, the centres, the lookup and the table of homes.
    """
    opened = culture_file.opened_of(inputs, edition=edition)
    held = places_counted.read(opened, decide, KINDS, PASSED_BY)
    placed = inputs.open(centres.CENTRES, Use.SCORING, edition=centres.CENTRES_EDITION)
    handed = {one.file_id: one.receipt for one in inputs.opened}
    if not set(found.inputs) <= set(handed):
        raise ValueError("the spine is made from files of this build")
    points = centres.centres_of(placed, found)
    if not points:
        raise LockError("input_is_as_described", placed.file_id, "it holds no centre of the build")
    ordered = sorted(points)
    shops = on_the_grid(sorted({(one.longitude, one.latitude) for one in held.records}))
    far = to_the_nearest_point([points[oa] for oa in ordered], shops)
    found_of_oa = dict(zip(ordered, far, strict=True))
    taken = opened.receipt.taken
    of_oa = known(found_of_oa, points, None if taken is None else taken.box)
    worked = park_proximity.figures(of_oa, found)
    behind = sorted({opened.file_id, placed.file_id, *found.inputs})
    files = tuple(handed[file_id] for file_id in behind)
    rows = tuple(
        row_of(fact_id(area, FactKind.FEATURE, FEATURE), worked[area], METHOD, files)
        for area in sorted(worked)
    )
    return Nearest(
        worked=worked,
        rows=rows,
        metric=metric_of(files, held),
        files=files,
        geography=KEYED_BY,
        held=held,
        found_of_oa=found_of_oa,
        of_oa=of_oa,
        beyond_the_edge=tuple(sorted(set(found_of_oa) - set(of_oa))),
    )
