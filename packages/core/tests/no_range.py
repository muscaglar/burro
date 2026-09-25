"""What the tests of a price with no range share: a release that holds some, and a buyer.

Every name and figure here is made up.
"""

import dataclasses

from burro_core.ids import Confidence, Provenance, Segment, Strictness, Tenure
from burro_core.release import CostEstimate, InMemoryRelease, confidence_of
from burro_core.spec import Budget, PreferenceSpec, default_spec

from .support import AS_OF, SYNTHETIC, area_id, small_release

ONE, TWO, THREE, FOUR = (area_id(n) for n in range(1, 5))
# What the flats of each area sold for, in the middle. The fourth has no figure.
FLATS = {ONE: 385_000, TWO: 400_000, THREE: 437_500}
BUDGET = 400_000


def median(area: str, paid: int, segment: Segment = Segment.FLAT) -> CostEstimate:
    """A publisher's median for one kind of home, with no range and no count."""
    return CostEstimate(
        area_id=area,
        tenure=Tenure.BUY,
        segment=segment,
        lower_quartile=None,
        median=paid,
        upper_quartile=None,
        confidence=Confidence.UNSTATED,
        as_of=AS_OF,
        source_ids=SYNTHETIC,
    )


def priced() -> InMemoryRelease:
    """The small release, with a median for flats in three areas and no other price."""
    rents = tuple(row for row in small_release().costs if row.tenure is Tenure.RENT)
    flats = tuple(median(area, paid) for area, paid in FLATS.items())
    return dataclasses.replace(small_release(), costs=(*rents, *flats))


# The first month of the sales a counted median rests on, and how many sales stand behind
# the median of each area.
SINCE = "2023-09"
SALES = {ONE: 1_204, TWO: 50, THREE: 10}


def counted(
    area: str, paid: int, sales: int, segment: Segment = Segment.FLAT, since: str = SINCE
) -> CostEstimate:
    """A median worked out from sales that were counted, with no range."""
    return CostEstimate(
        area_id=area,
        tenure=Tenure.BUY,
        segment=segment,
        lower_quartile=None,
        median=paid,
        upper_quartile=None,
        confidence=confidence_of(sales),
        as_of=AS_OF,
        since=since,
        sales=sales,
        source_ids=SYNTHETIC,
    )


def sold() -> InMemoryRelease:
    """The small release, with a counted median for flats in three areas and no other price."""
    rents = tuple(row for row in small_release().costs if row.tenure is Tenure.RENT)
    flats = tuple(counted(area, paid, SALES[area]) for area, paid in FLATS.items())
    return dataclasses.replace(small_release(), costs=(*rents, *flats))


def buyer(strictness: Strictness, amount: int = BUDGET) -> PreferenceSpec:
    """A buyer with a budget for a flat, who asks for nothing else."""
    spec = default_spec(Tenure.BUY)
    return spec.replace(
        weights=(),
        tags=(),
        budget=Budget(
            amount=amount,
            segment=Segment.FLAT,
            strictness=strictness,
            weight=0.80,
            provenance=Provenance.STATED,
        ),
    )
