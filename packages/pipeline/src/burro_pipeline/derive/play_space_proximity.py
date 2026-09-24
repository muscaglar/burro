"""The nearest play space: how far it is, in a straight line, from where homes are to a way in.

The sites and the ways into them come from OS Open Greenspace, which
`green_sites.py` reads. Where homes are comes from the centres of output
areas, which `cells/centres.py` reads. The arithmetic is the nearest park's,
and is in `park_proximity.py`: this module says which sites count and what the
figure is called, and holds no arithmetic of its own.

**It is a straight line, and not a walk.** No network of streets is built, so
the figure is the distance across whatever lies between, and the row of the
catalogue says so in its name, as core names the measure. Do not name it a walk
while it is a straight line.

What counts as a play space, and why:

- A site that the publisher maps as `Play Space`. The file names the kind and
  does not define it, and no page of the publisher was opened for this. It
  does not say what a site holds, or whether it is open to all.
- Of any size. A play space is small: no least size is asked of one.
- With a way in that is for a person on foot. A play space with no such way in
  marked is not counted: the file does not say how a person gets in. Many of
  those stand inside a park and are reached by the park's own gate, which the
  file does not tie to them.
- Whether it stands in a park or not. A play space on a housing estate counts
  as one in a park does.

What never counts: a playing field, a tennis court, a bowling green, a sports
facility, a park with no play space mapped in it, an allotment, a cemetery, a
golf course and religious grounds.

How a figure is made is said in `park_proximity.py`: the distance from the
centre of each output area to the nearest way in, as the median over the
area's homes, to the nearest 10 metres.

Nothing is filled in. The files are cut to squares of the National Grid, and
each holds every site of its square, inside London or not. So a play space
outside London is measured to where it is the nearest. A home nearer to a
square that was not read than to any way in that was found has no distance,
and the coverage of its area falls by its homes.
"""

from collections.abc import Sequence

from burro_core.ids import FeatureId, NativeResolution
from burro_core.release import Metric

from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import green_sites, park_proximity
from burro_pipeline.derive.catalogue_row import catalogue_row
from burro_pipeline.derive.green_sites import Greenspace
from burro_pipeline.derive.park_proximity import Parks, Proximity
from burro_pipeline.evidence.method import Method
from burro_pipeline.evidence.receipt import Geography, Receipt
from burro_pipeline.inputs import Inputs

FEATURE = FeatureId.PLAY_SPACE_PROXIMITY
SOURCE = green_sites.SOURCE
# The one kind of site that counts, as the publisher writes it.
COUNTS = "Play Space"
# No least size is asked of a play space.
LEAST = 0
KEYED_BY = Geography.POINT
PUBLISHER, PRODUCT = green_sites.PUBLISHER, park_proximity.PRODUCT
CENSUS, NEAREST = park_proximity.CENSUS, park_proximity.NEAREST

# The arithmetic is the nearest park's, and the rows name the same record.
METHOD = park_proximity.STRAIGHT_LINE
METHODS: tuple[Method, ...] = (METHOD,)
# What a person reads beside the figure: it is a straight line, and no walk.
LABEL = "Straight-line distance to the nearest marked way into a play space"
# What the measure is, from whom, for what period, and what it is not.
DEFINITION = (
    "The distance in a straight line, in metres, from the point the statistics office gives as "
    "the centre of each census output area to the nearest way in on foot to a site of any size "
    "that {publisher} maps as {counts} in {product} as at {sites}, inside London or outside it, "
    "as the median over the area's homes at the census of {census} and given to the nearest "
    "{nearest} metres with a half taken upward: it is measured across whatever lies between and "
    "not along any street or path, so the walk is longer, and a site with no way in on foot "
    "marked is not counted."
)
# What the product shows beside the figure.
CANNOT_SEE = (
    "This is a straight line from where the homes of each small census area are taken to stand "
    "to the nearest marked way into a play space, and not a walk, so a railway, a river or a "
    "main road in between makes the real walk longer.",
    "A play space is a site its publisher maps as one, so the figure cannot tell what a play "
    "space holds, what state it is in or whether it is open to all, and a play space with no "
    "way in marked is not counted.",
)


def is_a_tile(name: str) -> bool:
    """Whether a publisher's name for a file is the name of a file this measure reads."""
    return green_sites.is_a_tile(name)


def play_spaces_of(green: Greenspace) -> Parks:
    """The play spaces, and every way into one on foot."""
    return park_proximity.sites_of(green, COUNTS, LEAST)


def definition_of(as_at: str) -> str:
    """The sentence a methods page prints for the measure."""
    return DEFINITION.format(
        publisher=PUBLISHER,
        counts=COUNTS,
        product=PRODUCT,
        sites=as_at,
        census=CENSUS,
        nearest=NEAREST,
    )


def metric_of(files: Sequence[Receipt], as_at: str) -> Metric:
    """The row of the catalogue: the name, the unit, the period and every source.

    Core decides the unit and which way is more. The name is `LABEL`: the one
    the figure supports, which is core's too. It is measured from points, and
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


def build(inputs: Inputs, found: Spine, *, edition: str | None = None) -> Proximity:
    """The distance to the nearest play space for every area, and its evidence.

    The gate is asked about the sites and about the centres before either is
    read. `found` is the spine of the same build. A row of evidence names the
    files of sites its figure rests on, the centres, the lookup and the table
    of homes.
    """
    made, green = park_proximity.to_the_nearest(inputs, found, FEATURE, play_spaces_of, edition)
    return Proximity(
        worked=made.worked,
        rows=made.rows,
        files=made.files,
        geography=made.geography,
        parks=made.parks,
        of_oa=made.of_oa,
        metric=metric_of(made.files, green.as_at),
    )
