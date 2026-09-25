"""Homes near a cluster of pubs and bars: the share with three or more within 150 metres.

Quiet streets holds it at 30 in 100 of its recipe, read from its low end: the
fewer of an area's homes stand among pubs and bars, the quieter its streets
are taken to be. It is a nuisance, so its one direction is less.

The pubs and bars are those of `venues_nearby.py`: the places that the file of
Overture Maps Places gives a category of a pub or a bar, by the table in
`venue_kinds.py`, with records within 25 metres of the first of them counted
as one place. No name is read. What the licence registry asks of the file is
at the head of `culture_file.py`.

How a figure is made:

1. A home is placed at the point the statistics office gives as the centre of
   population of its output area.
2. An output area is near a cluster where three or more pubs or bars stand
   within 150 metres of that point, in a straight line.
3. An area's figure is the homes of its output areas that are near a cluster,
   over the homes of its output areas that have a verdict, as a percentage.
   That is `homes_within`. It is given to one decimal place.
4. An output area has a verdict where it has a centre, and the file holds a
   record of any kind within 800 metres of it. So nought is a figure only
   where the file is seen to hold something.

**The edge of London leaves out no home.** The part of the file that is
fetched reaches 2,000 metres beyond the homes of London, and the figure
counts no home outside London. So an output area at the edge has its verdict.

**Three, and 150 metres, are choices and not findings.** Core's catalogue
gives the distance. Three is the fewest that a person would call a cluster,
and it is the founder's to change: it is one line here, and stands in the
name of the measure. On the part of release 2026-09-23.0, 6 in 100 of
London's homes stand so, and 660 of the 1,002 areas read nought.

**It cannot say how late a place is open.** The file gives no hours. A pub
that shuts at ten counts as one that shuts at two, and a nightclub is not
counted at all.
"""

from collections.abc import Mapping
from dataclasses import dataclass, replace

from burro_core.facts import fact_id
from burro_core.ids import FactKind, FeatureId, NativeResolution
from burro_core.release import Metric

from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import culture_reach, venues_nearby
from burro_pipeline.derive.catalogue_row import catalogue_row
from burro_pipeline.derive.culture_reach import ground_of, reach_at
from burro_pipeline.derive.culture_venues import ONE_VENUE, SEEN
from burro_pipeline.derive.methods import Worked, homes_within, homes_within_at, row_of, to_places
from burro_pipeline.derive.venue_kinds import Kind
from burro_pipeline.derive.venues_nearby import (
    A_STRAIGHT_LINE,
    AS_AT_THE_CENSUS,
    BY_CATEGORY,
    GATHERED,
    HOW_SURE,
    NO_NIGHTCLUB,
    OF_THE_RELEASE,
    ON_THE_FILE,
    PUBLISHER,
    THIN_AT_THE_EDGE,
    Found,
)
from burro_pipeline.evidence.method import Method
from burro_pipeline.evidence.receipt import Geography, Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.inputs import Inputs

FEATURE = FeatureId.EVENING_CLUSTER_EXPOSURE
SOURCE = venues_nearby.SOURCE
KEYED_BY = venues_nearby.KEYED_BY
CENSUS = 2021
# How near a pub or a bar stands to count, in a straight line, in whole metres.
METRES = 150
# How many pubs or bars within that distance are a cluster.
FEWEST = 3
# How far the file is looked in to see that it holds something, in whole metres.
SEEN_WITHIN = culture_reach.METRES
DECIMALS = 1
LABEL = f"Share of homes with three or more pubs or bars within {METRES} m, in a straight line"
METHOD = homes_within_at(METRES)
METHODS: tuple[Method, ...] = (METHOD,)
DEFINITION = (
    "The share of the area's homes whose census output area has {fewest} or more pubs or bars "
    "within {metres} metres, in a straight line, of the point the statistics office gives as "
    "its centre, from the records that release {release} of Overture Maps Places, of the "
    "{publisher}, as at {as_at}, gives a category of a pub or a bar, leaving out a record that "
    "its file says has closed for good, and counting records within {one_venue} metres of the "
    "first of them as one place, each output area weighed by its homes at the census of "
    "{census}, with a verdict only where the file holds a record of any kind within {seen} "
    "metres, and given to {decimals} decimal place with a half taken upward: it is measured "
    "across whatever lies between and not along any street, a place the file does not hold is "
    "not counted, and nothing says how late a place is open."
)
A_CLUSTER = (
    "Three or more pubs or bars within 150 metres are taken for a cluster, so a home beside "
    "one loud pub, or two, counts as a home beside none."
)
ONE_PLACE = venues_nearby.ONE_PLACE
NOUGHT = (
    "Nought means that the file lists fewer than three pubs or bars within reach of every "
    "home that was counted, which is not the same as there being fewer."
)
# What the product shows beside the figure.
CANNOT_SEE = (
    A_CLUSTER,
    NO_NIGHTCLUB,
    OF_THE_RELEASE,
    ON_THE_FILE,
    GATHERED,
    BY_CATEGORY,
    ONE_PLACE,
    HOW_SURE,
    A_STRAIGHT_LINE,
    NOUGHT,
    THIN_AT_THE_EDGE,
    AS_AT_THE_CENSUS,
)


@dataclass(frozen=True)
class Exposure:
    """The measure for every area of the spine, with what stands behind it."""

    # The figure of each area, by its id. An area with no figure is here too, with its state.
    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    metric: Metric
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    # For each output area with a verdict: how many pubs or bars stand within 150 metres.
    within: Mapping[str, int]
    # The output areas with no verdict: the file holds nothing at all within reach.
    nothing_seen: tuple[str, ...]
    geography: Geography


def is_the_file(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the file this measure reads."""
    return venues_nearby.is_the_file(name)


def metric_of(files: tuple[Receipt, ...], made: Found) -> Metric:
    """The row of the catalogue: what core decides of the feature, and what the build found."""
    return catalogue_row(
        FEATURE,
        method=METHOD,
        label=LABEL,
        native_resolution=NativeResolution.OA,
        source_ids={receipt.source_id for receipt in files},
        vintage=made.held.as_at,
        definition=DEFINITION.format(
            fewest="three",
            metres=METRES,
            release=made.held.file.edition,
            publisher=PUBLISHER,
            as_at=made.held.as_at,
            one_venue=ONE_VENUE,
            census=CENSUS,
            seen=SEEN_WITHIN,
            decimals=DECIMALS,
        ),
    )


def build(inputs: Inputs, found: Spine, *, edition: str | None = None) -> Exposure:
    """The figure of every area and its evidence, from the files of the build.

    The gate is asked about the places and about the centres before either is
    read. `found` is the spine of the same build.
    """
    made = venues_nearby.found_of(inputs, found, edition=edition)
    ground = ground_of(inputs, found)
    handed = {one.file_id: one.receipt for one in inputs.opened}
    if not set(found.inputs) <= set(handed):
        raise ValueError("the spine is made from files of this build")
    centred = tuple((oa, ground.at[oa], found.homes[oa]) for oa in sorted(ground.at))
    pubs = [(one.longitude, one.latitude, 0, 1) for one in made.of_kind(Kind.PUB)]
    about = [(longitude, latitude, 0, 1) for longitude, latitude in made.held.every]
    near = reach_at(pubs, 1, centred, (), METRES).within
    seen = reach_at(about, 1, centred, (), SEEN_WITHIN).within
    within = {oa: held[0] for oa, held in near.items() if seen[oa][0] >= SEEN}
    share = homes_within(
        {oa: count >= FEWEST for oa, count in within.items()}, found.weights, times=100
    )
    worked = {
        area: one if one.value is None else replace(one, value=to_places(one.value, DECIMALS))
        for area, one in share.items()
    }
    behind = sorted({made.held.file.file_id, ground.placed.file_id, *found.inputs})
    files = tuple(handed[file_id] for file_id in behind)
    return Exposure(
        worked=worked,
        rows=tuple(
            row_of(fact_id(area, FactKind.FEATURE, FEATURE), worked[area], METHOD, files)
            for area in sorted(worked)
        ),
        metric=metric_of(files, made),
        files=files,
        within=within,
        nothing_seen=tuple(sorted(set(near) - set(within))),
        geography=KEYED_BY,
    )
