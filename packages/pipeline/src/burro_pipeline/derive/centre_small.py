"""A small town centre: of the homes with a town centre near, the share whose nearest is small.

The outlines come from the Greater London Authority's file of town centre
boundaries, which `town_centres.py` reads. Where homes are comes from the
centres of output areas, which `cells/centres.py` reads.

**Small is the ground a centre covers, and not its class.** The file writes a
class for each centre, which says what part the centre plays among London's
centres. It does not say how large the centre is on the ground: a centre of
the district class may run for a mile along a road. So a centre is small where
its outline encloses under 10 hectares. That is close to the middle of the
centres of the file that was described, so about half of them are small. The
number is a first guess, and is the founder's to change.

**Only a home with a town centre near is counted.** A home has a centre of its
own where one is within 800 metres, in a straight line. The file holds
London's larger centres and few of its local ones, so where it holds none
within 800 metres of a home, whether that home has a small centre near is not
known. Such a home adds nothing, above or below the line, and the coverage of
its area falls by its homes. It is never counted as a home with no small
centre. Core names the measure the share of all homes whose nearest town
centre is a small one, however far that centre is. So the row of the catalogue
that is made here carries a name of its own, and a build leaves the measure
out until core says the same.

How a figure is made:

1. For each output area, the nearest town centre and how far its outline is
   from the centre of population, in a straight line.
2. An output area has a verdict where that centre is within 800 metres, and
   no nearer centre may stand beyond London. The verdict is whether the
   centre's outline encloses under 10 hectares.
3. An area's figure is the homes of its output areas whose verdict is yes,
   over the homes of its output areas that have a verdict, as a percentage.
   It is given to one decimal place.
4. Below half the area's homes with a verdict, no figure is given.

Nought is a figure: every home of the area that has a town centre near has a
larger one nearest. The share is worked out by `homes_within` in
`derive/methods.py`.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace

from burro_core.ids import FeatureId, NativeResolution
from burro_core.release import Metric

from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import town_centres
from burro_pipeline.derive.catalogue_row import catalogue_row
from burro_pipeline.derive.methods import Worked, homes_within, to_places
from burro_pipeline.derive.town_centres import REACH, Found
from burro_pipeline.evidence.method import Kind, Method
from burro_pipeline.evidence.receipt import Geography, Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.inputs import Inputs

FEATURE = FeatureId.CENTRE_SMALL
SOURCE = town_centres.SOURCE
# A centre is small where its outline encloses under so many hectares.
SMALL_UNDER = 10
# A figure is given to so many decimal places.
DECIMALS = 1

METHOD = Method(
    derivation_id="homes_whose_nearest_outline_is_small@1",
    sentence="Of the area's homes whose census output area has its centre of population within "
    "800 metres, in a straight line, of the nearest of the outlines that count, the share whose "
    "nearest outline encloses under 10 hectares, each output area weighed by its homes at the "
    "census, and not given where under 50 in 100 of the area's homes are in such an output "
    "area.",
    kind=Kind.MEASURED,
    parameters={"metres": REACH, "hectares": SMALL_UNDER, "enough_in_100": 50},
    code="burro_pipeline.derive.centre_small",
)
METHODS: tuple[Method, ...] = (METHOD,)
# What a person reads beside the figure: which homes are counted, and what small is.
LABEL = "Share of homes within 800 m of a town centre whose nearest town centre is under 10 ha"
# What the measure is, from whom, for what period, and what it is not.
DEFINITION = (
    "Of the homes whose census output area has its centre within {metres} metres, in a straight "
    "line, of the nearest town centre that {publisher} draws in its {product} as at {as_at}, the "
    "percentage whose nearest town centre has an outline that encloses under {hectares} "
    "hectares, each output area weighed by its homes at the census of {census} and the figure "
    "given to {decimals} decimal place with a half taken upward: a centre is small by the ground "
    "its outline covers and not by its class or its shops, the outlines are the publisher's "
    "guide to where a centre is and are no border, and a home with no centre of the file within "
    "{metres} metres, or nearer to homes beyond London than to any centre of the file, is not "
    "counted above or below the line."
)
# What keeps the measure out of a release, and whose it is to settle.
WAITS_ON = (
    "Core names the measure the share of homes whose nearest town centre is a small one, "
    "however far that centre is. The figure counts only the homes with a town centre within 800 "
    "metres, and calls a centre small where it covers under 10 hectares. Core's row needs this "
    "name.",
    "Whether 10 hectares and 800 metres are the right numbers is the founder's to say, once "
    "the figures have been looked at on a map.",
)
# What the product shows beside the figure.
CANNOT_SEE = (
    "A centre is small by the ground its outline covers, so it cannot tell a quiet village "
    "centre from a short parade on a main road, and it says nothing of which shops are there.",
    "It counts the town centres the Greater London Authority draws, which are London's larger "
    "centres, so a home whose only centre is a local parade or a village centre that is not "
    "among them is left out of the count.",
)


@dataclass(frozen=True)
class Small:
    """The share of homes whose nearest centre is small, for every area, with its evidence."""

    # The figure of each area, by its id. An area with no figure is here too, with its state.
    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    geography: Geography
    metric: Metric
    # Whether the nearest centre is small, for each output area with a centre within reach.
    of_oa: Mapping[str, bool]
    found: Found


def is_the_file(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the file this measure reads."""
    return town_centres.is_the_file(name)


def verdicts(found: Found) -> dict[str, bool]:
    """Whether the nearest centre is small, for each output area with one within reach."""
    return {
        oa: found.centres[one.centre].hectares < SMALL_UNDER
        for oa, one in sorted(town_centres.within_reach(found).items())
    }


def figures(of_oa: Mapping[str, bool], spine: Spine) -> dict[str, Worked]:
    """The figure of every area of the spine, to one decimal place, or why it has none."""
    worked = homes_within(of_oa, spine.weights, times=100.0)
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
            hectares=SMALL_UNDER,
            census=town_centres.CENSUS,
            decimals=DECIMALS,
        ),
    )


def build(inputs: Inputs, spine: Spine, *, edition: str | None = None) -> Small:
    """The share of homes whose nearest centre is small, for every area, and its evidence.

    The gate is asked about the town centres and about the centres of
    population before either is read. `spine` is the spine of the same build.
    """
    found = town_centres.build(inputs, spine, edition=edition)
    of_oa = verdicts(found)
    worked = figures(of_oa, spine)
    return Small(
        worked=worked,
        rows=town_centres.rows_of(found, worked, FEATURE, METHOD),
        files=found.files,
        geography=found.geography,
        metric=metric_of(found.files, found.as_at),
        of_oa=of_oa,
        found=found,
    )
