"""What the tests of a rent of a wider place share: a release that holds some, and a renter.

A publisher gives the rents of a city for its postcode districts and for its
boroughs, and for nothing smaller. So an area is given the figure of the place
it lies in, and the row says which place that is.

Every name and figure here is made up. No postcode begins with a Q, so no
district here is a district.
"""

import dataclasses

from burro_core.ids import CostOfKind, Provenance, Segment, Strictness, Tenure
from burro_core.release import CostEstimate, CostOf, InMemoryRelease, confidence_of
from burro_core.spec import Budget, PreferenceSpec, default_spec

from .support import BOROUGHS, SYNTHETIC, area_id, small_release

ONE, TWO, THREE, FOUR, FIVE = (area_id(n) for n in range(1, 6))
# The months the rents were recorded in, the first and the last.
SINCE, UNTIL = "2025-04", "2026-03"
# Two districts and a borough, and how many rents were recorded in each.
DISTRICT, NEXT_DISTRICT = "QH1", "QH2"
QUILLHAVEN, OSTREL_VALE = BOROUGHS
MANY, FEW = 170, 10
BUDGET = 1_700
# The most a middle rent may be and not be left out by a firm budget of 1,700: a quarter over.
AT_THE_LINE = 2_125

IN_THE_DISTRICT = CostOf(kind=CostOfKind.POSTCODE_DISTRICT, name=DISTRICT)
IN_THE_NEXT = CostOf(kind=CostOfKind.POSTCODE_DISTRICT, name=NEXT_DISTRICT)
IN_QUILLHAVEN = CostOf(kind=CostOfKind.BOROUGH, name=QUILLHAVEN)


def let(
    area: str,
    middle: int,
    of: CostOf = IN_THE_DISTRICT,
    rents: int = MANY,
    *,
    lower: int | None = None,
    upper: int | None = None,
    segment: Segment = Segment.BED_1,
) -> CostEstimate:
    """The rent of one kind of home, as a publisher gives it for the place an area lies in."""
    return CostEstimate(
        area_id=area,
        tenure=Tenure.RENT,
        segment=segment,
        lower_quartile=middle - 250 if lower is None else lower,
        median=middle,
        upper_quartile=middle + 310 if upper is None else upper,
        confidence=confidence_of(rents),
        as_of=UNTIL,
        since=SINCE,
        rents=rents,
        of=of,
        source_ids=SYNTHETIC,
    )


# The rent of a home of one bedroom in each area, and the place each is of. The first and
# the third lie in one district, so they show one figure. The fifth has its borough's.
RENTS = (
    let(ONE, 1_600),
    let(TWO, 1_900, IN_THE_NEXT, FEW),
    let(THREE, 1_600),
    let(FIVE, 2_200, IN_QUILLHAVEN, 520),
)


def recorded(*rows: CostEstimate) -> InMemoryRelease:
    """The small release, with the rents a publisher gives for wider places and no other cost.

    The fourth area has no rent. With rows given, it holds those and no other.
    """
    return dataclasses.replace(small_release(), costs=rows or RENTS)


def renter(strictness: Strictness, amount: int = BUDGET) -> PreferenceSpec:
    """A renter with a budget for a home of one bedroom, who asks for nothing else."""
    spec = default_spec(Tenure.RENT)
    return spec.replace(
        weights=(),
        tags=(),
        budget=Budget(
            amount=amount,
            segment=Segment.BED_1,
            strictness=strictness,
            weight=0.80,
            provenance=Provenance.STATED,
        ),
    )
