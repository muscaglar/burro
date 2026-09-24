"""A compact town centre: how much of the circle round it the nearest town centre fills.

The outlines come from the Greater London Authority's file of town centre
boundaries, which `town_centres.py` reads. Where homes are comes from the
centres of output areas, which `cells/centres.py` reads.

**Compact is the shape of a centre, and not its size.** A centre is compact
where its outline fills much of the smallest circle that can be drawn round
all of it. A centre gathered round a green or a crossroads fills much of its
circle. A centre strung along a main road fills little: a strip ten times as
long as it is wide fills 13 in 100. A centre drawn in several pieces that
stand apart fills little too.

Why this, and not what core names. Core names the measure the share of the
nearest town centre within 200 metres of its middle. That reads high for any
centre that is small, whatever its shape, and low for any that is large. The
measure of a small centre says how large a centre is already, and the recipe
that weighs both would count size twice. How much of its circle an outline
fills does not change with its size, so it tells a long high road from a
centre round a green where both are small. It was chosen over the outline's
edge against its area, which falls wherever an outline is drawn with many
corners and says more of the pen than of the centre.

**Only a home with a town centre near is counted**, as for the measure of a
small centre, and for the same reason: `centre_small.py` says it. So the row of
the catalogue that is made here carries a name of its own, and a build leaves
the measure out until core says the same.

How a figure is made:

1. For each output area, the nearest town centre and how far its outline is
   from the centre of population, in a straight line.
2. An output area has a value where that centre is within 800 metres, and no
   nearer centre may stand beyond London. The value is what the centre's
   outline encloses, as a percentage of the smallest circle that holds all of
   the outline.
3. An area's figure is the median of those values over its homes: half the
   area's homes have a nearest centre at least this compact. Where an area's
   homes look to one centre, the figure is that centre's own.
4. It is given to one decimal place. Below half the area's homes with a
   value, no figure is given.

The median over homes is worked out by `median_by_homes` in
`derive/park_proximity.py`, which the distance to a park uses too.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace

from burro_core.ids import FeatureId, NativeResolution
from burro_core.release import Metric

from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import town_centres
from burro_pipeline.derive.catalogue_row import catalogue_row
from burro_pipeline.derive.methods import Worked, to_places
from burro_pipeline.derive.park_proximity import median_by_homes
from burro_pipeline.derive.town_centres import REACH, Found
from burro_pipeline.evidence.method import Kind, Method
from burro_pipeline.evidence.receipt import Geography, Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.inputs import Inputs

FEATURE = FeatureId.CENTRE_COMPACT
SOURCE = town_centres.SOURCE
# A figure is given to so many decimal places.
DECIMALS = 1

METHOD = Method(
    derivation_id="circle_filled_by_nearest_outline@1",
    sentence="What the nearest of the outlines that count encloses, as a percentage of the "
    "smallest circle that holds all of it, for each census output area whose centre of "
    "population is within 800 metres of that outline in a straight line, as the median over the "
    "area's homes at the census, which is the mean of the two middle values where the homes "
    "divide exactly in half between them, and not given where under 50 in 100 of the area's "
    "homes are in such an output area.",
    kind=Kind.MEASURED,
    parameters={"metres": REACH, "enough_in_100": 50},
    code="burro_pipeline.derive.centre_compact",
)
METHODS: tuple[Method, ...] = (METHOD,)
# What a person reads beside the figure: what is measured, and of which homes.
LABEL = (
    "Share of the smallest circle round the nearest town centre that the centre fills, "
    "for homes within 800 m of one"
)
# What the measure is, from whom, for what period, and what it is not.
DEFINITION = (
    "What the outline of the nearest town centre encloses, as a percentage of the smallest "
    "circle that holds all of that outline, for the homes whose census output area has its "
    "centre within {metres} metres, in a straight line, of the nearest town centre that "
    "{publisher} draws in its {product} as at {as_at}, as the median over the area's homes at "
    "the census of {census} and given to {decimals} decimal place with a half taken upward: it "
    "is the shape of the outline and not its size, the outlines are the publisher's guide to "
    "where a centre is and are no border, and a home with no centre of the file within {metres} "
    "metres, or nearer to homes beyond London than to any centre of the file, is not counted."
)
# What keeps the measure out of a release, and whose it is to settle.
WAITS_ON = (
    "Core names the measure the share of the nearest town centre within 200 metres of its "
    "middle, which reads high for any small centre whatever its shape. The figure is how much "
    "of the smallest circle round it the nearest centre fills, for the homes with a town centre "
    "within 800 metres. Core's row needs this name.",
    "Whether the shape of an outline tells a village centre from a high road is the founder's "
    "to say, once the figures have been looked at on a map.",
)
# What the product shows beside the figure.
CANNOT_SEE = (
    "It reads the shape of the outline a planner drew, so a centre drawn tightly round a long "
    "road reads as strung out and one drawn wide reads as compact, whatever it is like to "
    "walk through.",
    "It counts the town centres the Greater London Authority draws, which are London's larger "
    "centres, so a home whose only centre is a local parade or a village centre that is not "
    "among them is left out of the count.",
)


@dataclass(frozen=True)
class Compact:
    """How compact the nearest centre is, for every area, with what stands behind each figure."""

    # The figure of each area, by its id. An area with no figure is here too, with its state.
    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    geography: Geography
    metric: Metric
    # How much of its circle the nearest centre fills, in 100, for each output area with a
    # centre within reach.
    of_oa: Mapping[str, float]
    found: Found


def is_the_file(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the file this measure reads."""
    return town_centres.is_the_file(name)


def values(found: Found) -> dict[str, float]:
    """How much of its circle the nearest centre fills, for each output area with one in reach."""
    return {
        oa: 100.0 * found.centres[one.centre].fills
        for oa, one in sorted(town_centres.within_reach(found).items())
    }


def figures(of_oa: Mapping[str, float], spine: Spine) -> dict[str, Worked]:
    """The figure of every area of the spine, to one decimal place, or why it has none."""
    worked = median_by_homes(of_oa, spine.weights)
    return {
        area: one if one.value is None else replace(one, value=to_places(one.value, DECIMALS))
        for area, one in worked.items()
    }


def metric_of(files: Sequence[Receipt], as_at: str) -> Metric:
    """The row of the catalogue: the name, the unit, the period and every source.

    Core decides the unit and which way is more. The name is `LABEL`: the one
    the figure supports.
    """
    return catalogue_row(
        FEATURE,
        method=METHOD,
        label=LABEL,
        native_resolution=NativeResolution.POLYGON,
        source_ids={receipt.source_id for receipt in files},
        vintage=as_at,
        definition=DEFINITION.format(
            metres=REACH,
            publisher=town_centres.PUBLISHER,
            product=town_centres.PRODUCT,
            as_at=as_at,
            census=town_centres.CENSUS,
            decimals=DECIMALS,
        ),
    )


def build(inputs: Inputs, spine: Spine, *, edition: str | None = None) -> Compact:
    """How compact the nearest centre is, for every area, and its evidence.

    The gate is asked about the town centres and about the centres of
    population before either is read. `spine` is the spine of the same build.
    """
    found = town_centres.build(inputs, spine, edition=edition)
    of_oa = values(found)
    worked = figures(of_oa, spine)
    return Compact(
        worked=worked,
        rows=town_centres.rows_of(found, worked, FEATURE, METHOD),
        files=found.files,
        geography=found.geography,
        metric=metric_of(found.files, found.as_at),
        of_oa=of_oa,
        found=found,
    )
