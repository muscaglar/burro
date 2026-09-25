"""A high street in a conservation area: how much of the nearest high street lies inside one.

The outlines of high streets come from the Greater London Authority's file of
high street boundaries, which `high_streets.py` reads. The conservation areas
come from the planning data platform, kept as `conservation_cover.py` keeps
them: each once. Where homes are comes from the centres of output areas, and
the land of each authority from the boundaries of LSOAs. It is a figure about
land and buildings. It says nothing of who lives anywhere.

**It is of the high street, and not of the area.** Conservation cover says how
much of an area's own land lies inside a conservation area. This says how much
of the high street its homes are nearest to does. The two differ where an old
high street stands among newer homes, and where old homes stand round a centre
that was built again.

**Why it is measured.** Village feel was first tried on the size and the shape
of a town centre, with independent places and old homes, and did not find
villages. Of all that was worked out on that first try, one figure read like a
list of them: how much of a centre's own outline lies inside a conservation
area. `docs/research/data/high-streets.md` says what the second try found
with it. It did not reach the founder's bar, and the founder chose on
2026-09-25 to serve it all the same, as a rough guide.

The licence registry puts conditions on the conservation areas, and
`conservation_cover.py` lists them. Each is kept here by asking that module:
a conservation area recorded twice is one area, an authority that sent none is
not known to hold none, and no vibe rests on this source alone.

How a figure is made:

1. **The conservation land.** The conservation areas of London, each once, as
   `conservation_cover.held_for_london` keeps them. They are joined before
   anything is measured, so land inside two of them is counted once.
2. **The ground that is known.** The land of every authority that the file
   holds a conservation area of: `COVERED` in `conservation_cover.py` is the
   rule. Land is what the outline of an LSOA encloses, cut at the mean high
   water mark, so the tidal river is no land, and nor is anything beyond
   London.
3. **The share of each high street.** The land of the high street that lies
   inside the conservation land, over the land of the high street that lies on
   the ground that is known, times 100, to one decimal place. A high street
   with under half of what its outline encloses on that ground has no share:
   what stands on the rest is not known, and is never taken to be nought.
4. **The high street of each output area.** The nearest, in a straight line
   from the centre of population to the nearest edge of an outline, where it
   is within 800 metres and no nearer one may stand beyond London. An output
   area whose nearest high street has no share has none either.
5. **The figure.** The mean of those shares over the area's homes, to one
   decimal place. Below half the area's homes with a share, no figure is
   given.

Nought is a figure: the authority sent its conservation areas, and none
touches the high street.

**Core holds the measure, and a build carries it.** Core decides the name, the
unit and which way is more, and the row of the catalogue that is made here
says the same. No likeness between areas counts it.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace

from burro_core.facts import fact_id
from burro_core.ids import FactKind, FeatureId
from burro_core.release import Metric

from burro_pipeline.cells import land
from burro_pipeline.cells.shapes import Shape, hectares, hectares_inside, joined
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import conservation_cover, high_streets, planning_data, town_centres
from burro_pipeline.derive.catalogue_row import catalogue_row
from burro_pipeline.derive.heritage_shapes import box_round, in_degrees, land_shared
from burro_pipeline.derive.methods import Worked, lsoa_value_by_homes, row_of, to_places
from burro_pipeline.derive.town_centres import Found
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind, Method
from burro_pipeline.evidence.receipt import Geography, Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

FEATURE = FeatureId.HIGHSTREET_CONSERVED
SOURCE = high_streets.SOURCE
CONSERVATION = conservation_cover.SOURCE
REACH = high_streets.REACH
# A high street has a share where this much of what its outline encloses lies on the ground
# that is known, in 100.
KNOWN_IN_100 = 50
TIMES = 100
# A share and a figure are given to this many decimal places.
DECIMALS = 1
# What the rows of the file of high streets are keyed by, as the parser finds them.
KEYED_BY = Geography.POLYGON
CODE = "burro_pipeline.derive.highstreet_conserved"

METHOD = Method(
    derivation_id="nearest_outline_inside_conservation_areas@1",
    sentence="The land of the nearest of the outlines that count that lies inside a conservation "
    "area, as a percentage of the land of that outline in an authority the file holds a "
    "conservation area of, with land inside two conservation areas counted once, for each census "
    "output area whose centre of population is within 800 metres of that outline in a straight "
    "line, as the mean over the area's homes at the census, and not given where under 50 in 100 "
    "of the area's homes are in such an output area.",
    kind=Kind.MEASURED,
    parameters={"metres": REACH, "known_in_100": KNOWN_IN_100, "enough_in_100": 50},
    code=CODE,
)
METHODS: tuple[Method, ...] = (
    METHOD,
    land.MEASURED,
    conservation_cover.ONE_OF_EACH,
    conservation_cover.COVERED,
)
# What the measure is, from whom, for what period, and what it is not.
DEFINITION = (
    "The land of the nearest high street that lies inside the conservation areas that the "
    "{platform} of the {ministry} held as at {areas}, as a percentage of the land of that high "
    "street in an authority that sent a conservation area, for the homes whose census output "
    "area has its centre within {metres} metres, in a straight line, of the nearest high street "
    "that {publisher} draws in its {product} as at {streets}, as the mean over the area's homes "
    "at the census of {census} and given to {decimals} decimal place with a half taken upward: a "
    "conservation area recorded twice is counted once, land inside two is counted once, the "
    "tidal river is no land, the outlines are the publisher's own and are no border, and a home "
    "with no high street of the file within {metres} metres, or nearer to homes beyond London "
    "than to any high street of the file, is not counted."
)
# What the product shows beside the figure.
CANNOT_SEE = (
    "It counts the land inside a line a planning authority drew, so it cannot see what the "
    "buildings of the high street are like, which shops stand on it, or how much traffic runs "
    "along it: a trunk road through a conservation area reads as a village street does.",
    "It reads the high streets the Greater London Authority draws, so a centre that its file "
    "does not draw is not counted, and a home is given the high street nearest to it in a "
    "straight line, which may be a parade of shops and not the centre a person would name.",
    "The publisher of the conservation areas says its data may be incomplete, so where an "
    "authority sent only some of its conservation areas the figure is too low, and where it "
    "sent none there is no figure.",
)


@dataclass(frozen=True)
class Conserved:
    """The measure for every area of the spine, with what stands behind it."""

    # The figure of each area, by its id. An area with no figure is here too, with its state.
    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    metric: Metric
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    geography: Geography
    # The share of each high street that has one, in 100, by the id of the high street.
    shares: Mapping[str, float]
    # The share of the nearest high street, for each output area that has one within reach.
    of_oa: Mapping[str, float]
    found: Found
    # How many conservation areas were kept, each once.
    conservation_areas: int


def is_the_file(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the file of high streets."""
    return high_streets.is_the_file(name)


def shares_of(
    outlines: Mapping[str, Shape], conserved: Sequence[Shape], ground: Shape
) -> dict[str, float]:
    """How much of each outline lies inside a conservation area, in 100, where it is known.

    `conserved` is the conservation areas, each once, and `ground` the land
    that is known. An outline with under half of what it encloses on that
    ground is not here. It is asked of high streets, and may be asked of any
    outlines on the National Grid.
    """
    known: dict[str, Shape] = {}
    for name in sorted(outlines):
        part = land_shared(outlines[name], ground)
        if part is not None and TIMES * hectares(part) >= KNOWN_IN_100 * hectares(outlines[name]):
            known[name] = part
    inside = hectares_inside(known, conserved)
    return {
        name: to_places(min(float(TIMES), TIMES * inside[name] / hectares(known[name])), DECIMALS)
        for name in sorted(known)
    }


def values(found: Found, shares: Mapping[str, float]) -> dict[str, float]:
    """The share of the nearest high street, for each output area with one within reach."""
    return {
        oa: shares[one.centre]
        for oa, one in sorted(town_centres.within_reach(found).items())
        if one.centre in shares
    }


def figures(of_oa: Mapping[str, float], spine: Spine) -> dict[str, Worked]:
    """The figure of every area of the spine, to one decimal place, or why it has none.

    It is the mean over the area's homes, which `lsoa_value_by_homes` works
    out with each output area as a unit of its own.
    """
    worked = lsoa_value_by_homes(of_oa, {oa: oa for oa in spine.area_of}, spine.weights)
    return {
        area: one if one.value is None else replace(one, value=to_places(one.value, DECIMALS))
        for area, one in worked.items()
    }


def metric_of(files: Sequence[Receipt], streets: str, areas: str) -> Metric:
    """The row of the catalogue: the name, the unit, the days and every source.

    Core decides the name, the unit and which way is more, and the figure is
    what core's name says: a share of the nearest high street. The period is
    the day the conservation areas are of, as conservation cover gives it.
    """
    return catalogue_row(
        FEATURE,
        method=METHOD,
        source_ids={receipt.source_id for receipt in files},
        vintage=areas,
        definition=DEFINITION.format(
            platform=conservation_cover.PLATFORM,
            ministry=conservation_cover.PUBLISHER,
            areas=areas,
            metres=REACH,
            publisher=high_streets.PUBLISHER,
            product=high_streets.PRODUCT,
            streets=streets,
            census=high_streets.CENSUS,
            decimals=DECIMALS,
        ),
    )


def build(inputs: Inputs, spine: Spine, *, edition: str | None = None) -> Conserved:
    """The figure of every area and its evidence, from the files of the build.

    The gate is asked about each file before it is read: the high streets,
    the centres of population, the conservation areas and the boundaries.
    `spine` is the spine of the same build. `edition` says which file of
    conservation areas is meant where the folder of receipts holds more than
    one. A row of evidence names the two files, the boundaries, the centres,
    the lookup and the table of homes.
    """
    found = high_streets.build(inputs, spine)
    opened = inputs.open(
        CONSERVATION, Use.SCORING, edition=edition, named=conservation_cover.is_the_file
    )
    boundaries = inputs.open(land.BOUNDARIES, Use.SCORING, edition=land.BOUNDARIES_EDITION)
    outlines = land.read(boundaries, spine)
    if any(lsoa not in outlines for lsoa in spine.lsoas):
        raise LockError("input_is_as_described", boundaries.file_id, "an LSOA has no outline")
    day = opened.receipt.data_period.days()[1]
    read = planning_data.read(
        opened,
        conservation_cover.DATASET,
        in_degrees(box_round(outlines), conservation_cover.MARGIN),
    )
    authorities = conservation_cover.outlines_of_authorities(outlines, spine)
    try:
        held = conservation_cover.held_for_london(read, day, authorities)
    except ValueError:
        raise LockError(
            "input_is_as_described", opened.file_id, "an outline could not be read"
        ) from None
    covered = [authorities[code] for code in sorted(authorities) if held.authorities[code].covered]
    shares = (
        shares_of(
            {name: one.shape for name, one in found.centres.items()},
            [outlined.shape for outlined in held.kept],
            joined(covered),
        )
        if covered
        else {}
    )
    of_oa = values(found, shares)
    worked = figures(of_oa, spine)
    handed = {one.file_id: one.receipt for one in inputs.opened}
    behind = sorted(
        {opened.file_id, boundaries.file_id, *(receipt.file_id for receipt in found.files)}
    )
    files = tuple(handed[file_id] for file_id in behind)
    rows = tuple(
        row_of(fact_id(area, FactKind.FEATURE, FEATURE), worked[area], METHOD, files)
        for area in sorted(worked)
    )
    period = opened.receipt.data_period
    return Conserved(
        worked=worked,
        rows=rows,
        metric=metric_of(files, found.as_at, period.as_at or f"{period.start} to {period.end}"),
        files=files,
        geography=KEYED_BY,
        shares=shares,
        of_oa=of_oa,
        found=found,
        conservation_areas=len(held.kept),
    )
