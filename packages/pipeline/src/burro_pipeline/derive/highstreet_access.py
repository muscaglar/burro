"""The nearest town centre: how far it is, in a straight line, from where homes are.

The outlines come from the Greater London Authority's file of town centre
boundaries, which `town_centres.py` reads. Where homes are comes from the
centres of output areas, which `cells/centres.py` reads.

**It is a town centre, and not a high street.** The id of the measure says a
high street, because an id is never renamed. The file holds town centres:
London's larger centres, of every class the file writes. A high street is
another thing, and the authority publishes boundaries of high streets in
another file, which no measure reads. So the row of the catalogue says a town
centre, as core names the measure, and says nothing of a high street.

**It is a straight line, and not a walk.** No network of streets is built yet,
so no walk can be worked out. The figure is the distance across whatever lies
between, in metres, and the row of the catalogue says so in its name and in its
unit, as core does. Less is nearer, so each recipe that weighs the measure
reads it from its near end. Do not name it a walk while it is a straight line.

How a figure is made:

1. For each output area, the distance from its centre of population to the
   nearest edge of the nearest town centre. It is nothing where the outline of
   a centre holds the point.
2. An area's figure is the median of those distances over its homes: half the
   area's homes are in an output area no further than this from a centre.
3. It is given to the nearest 10 metres. A home may stand a hundred metres
   from the centre of its output area, so a metre would claim too much.

Nothing is filled in. A home nearer to homes beyond London than to any centre
of the file may have a nearer centre there, which the file does not hold. Its
distance is not known, it adds nothing, and the coverage of its area falls by
its homes. Below half the homes covered no figure is given.

The median over homes is worked out by `median_by_homes` in
`derive/park_proximity.py`, which the distance to a park uses too.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace

from burro_core.ids import FeatureId, NativeResolution, Polarity
from burro_core.release import Metric

from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import town_centres
from burro_pipeline.derive.catalogue_row import catalogue_row
from burro_pipeline.derive.methods import Worked, to_places
from burro_pipeline.derive.park_proximity import median_by_homes
from burro_pipeline.derive.town_centres import Found
from burro_pipeline.evidence.method import Kind, Method
from burro_pipeline.evidence.receipt import Geography, Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.inputs import Inputs

FEATURE = FeatureId.HIGHSTREET_ACCESS
SOURCE = town_centres.SOURCE
# A figure is given to the nearest so many metres, which is this many decimal places.
NEAREST, DECIMALS = 10, -1
# The unit of the figure, and which way is better: less is nearer.
UNIT, BETTER = "m", Polarity.LESS

METHOD = Method(
    derivation_id="straight_line_to_nearest_outline@1",
    sentence="The distance in a straight line from the point where the homes of each census "
    "output area are taken to stand to the nearest edge of the nearest of the outlines that "
    "count, which is nothing where an outline holds the point, as the median over the area's "
    "homes at the census, which is the mean of the two middle distances where the homes divide "
    "exactly in half between them, and not given where under 50 in 100 of the area's homes are "
    "in an output area whose nearest outline is known.",
    kind=Kind.MEASURED,
    parameters={"enough_in_100": 50},
    code="burro_pipeline.derive.highstreet_access",
)
METHODS: tuple[Method, ...] = (METHOD,)
# What a person reads beside the figure: a straight line, to a town centre, and no walk.
LABEL = "Straight-line distance to the nearest town centre boundary"
# What the measure is, from whom, for what period, and what it is not.
DEFINITION = (
    "The distance in a straight line, in metres, from the point the statistics office gives as "
    "the centre of each census output area to the nearest edge of the nearest town centre that "
    "{publisher} draws in its {product} as at {as_at}, and nothing where the outline of a centre "
    "holds the point, as the median over the area's homes at the census of {census} and given to "
    "the nearest {nearest} metres with a half taken upward: it is measured across whatever lies "
    "between and not along any street, so the walk is longer, the outlines are the publisher's "
    "guide to where a centre is and are no border, a centre that the file does not hold is not "
    "counted, and a home nearer to homes beyond London than to any centre of the file has no "
    "distance."
)
# What the product shows beside the figure.
CANNOT_SEE = (
    "This is a straight line from where the homes of each small census area are taken to stand "
    "to the edge of the nearest town centre, and not a walk, so a railway, a river or a main "
    "road in between makes the real walk longer.",
    "It counts the town centres the Greater London Authority draws, which are London's larger "
    "centres, so a parade of shops or a village centre that is not among them is not counted, "
    "and nor is any centre beyond London.",
)


@dataclass(frozen=True)
class Access:
    """The distance to the nearest town centre for every area, with what stands behind each."""

    # The figure of each area, by its id. An area with no figure is here too, with its state.
    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    geography: Geography
    metric: Metric
    # The distance of each output area whose nearest centre is known, in metres.
    of_oa: Mapping[str, float]
    found: Found


def is_the_file(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the file this measure reads."""
    return town_centres.is_the_file(name)


def distances(found: Found) -> dict[str, float]:
    """The distance from each output area to the nearest town centre, where it is known."""
    return {oa: found.nearest[oa].metres for oa in sorted(found.nearest)}


def figures(of_oa: Mapping[str, float], spine: Spine) -> dict[str, Worked]:
    """The figure of every area of the spine, to the nearest 10 metres, or why it has none."""
    worked = median_by_homes(of_oa, spine.weights)
    return {
        area: one if one.value is None else replace(one, value=to_places(one.value, DECIMALS))
        for area, one in worked.items()
    }


def metric_of(files: Sequence[Receipt], as_at: str) -> Metric:
    """The row of the catalogue: the name, the unit, the period and every source.

    The name, the unit and the way that is better are the figure's own, and
    core says each: a distance in metres, where less is nearer.
    """
    row = catalogue_row(
        FEATURE,
        method=METHOD,
        label=LABEL,
        native_resolution=NativeResolution.POLYGON,
        source_ids={receipt.source_id for receipt in files},
        vintage=as_at,
        definition=DEFINITION.format(
            publisher=town_centres.PUBLISHER,
            product=town_centres.PRODUCT,
            as_at=as_at,
            census=town_centres.CENSUS,
            nearest=NEAREST,
        ),
    )
    return row.model_copy(update={"unit": UNIT, "polarity": BETTER})


def build(inputs: Inputs, spine: Spine, *, edition: str | None = None) -> Access:
    """The distance to the nearest town centre for every area, and its evidence.

    The gate is asked about the town centres and about the centres of
    population before either is read. `spine` is the spine of the same build.
    A row of evidence names the file of town centres, the centres of
    population, the lookup and the table of homes.
    """
    found = town_centres.build(inputs, spine, edition=edition)
    of_oa = distances(found)
    worked = figures(of_oa, spine)
    return Access(
        worked=worked,
        rows=town_centres.rows_of(found, worked, FEATURE, METHOD),
        files=found.files,
        geography=found.geography,
        metric=metric_of(found.files, found.as_at),
        of_oa=of_oa,
        found=found,
    )
