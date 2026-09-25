"""The numbers a person set by judgement, as core holds them today.

The panel lists them so that a person can see each, with its unit and where it is. None
is changed at the panel yet: each is arithmetic of core, and a change to one is a change
to the code, with its tests. docs/design/panel.md, section 6, says how each would reach
a release.
"""

from typing import Any, Final

from burro_core import estimate
from burro_core.catalogue import (
    NEAREST_WITHIN_M,
    PART_MAX_HUNDREDTHS,
    TAG_MIN_COVERAGE_HUNDREDTHS,
    TRAFFIC_WITHIN_M,
    WITHIN_M,
)
from burro_core.rank import FIRM_BUDGET_MARGIN_PERCENT
from burro_core.release import FEWEST_SALES

from desk.panel import look

CORE: Final = "packages/core/src/burro_core"
IN_CODE: Final = "A change to core, in code, with its tests."
SAYS: Final = (
    "Each number is core's own, and is the same for every release. None is changed at the "
    "panel yet: a change to one is a change to the code, which a person reviews."
)


def _row(
    key: str, says: str, value: float, unit: str, where: str, changed_by: str = IN_CODE
) -> dict[str, Any]:
    return {
        "id": key,
        "says": says,
        "value": value,
        "unit": unit,
        "where": where,
        "changed_by": changed_by,
    }


def listed() -> dict[str, Any]:
    """Every number, in the groups a person thinks of them in."""
    journey = f"in {CORE}/estimate.py"
    return {
        "says": SAYS,
        "groups": [
            {
                "title": "A firm budget",
                "numbers": [
                    _row(
                        "firm_budget_margin",
                        "An area is left out where its middle price is over a firm budget by "
                        "more than this.",
                        FIRM_BUDGET_MARGIN_PERCENT,
                        "%",
                        f"FIRM_BUDGET_MARGIN_PERCENT in {CORE}/rank.py",
                    )
                ],
            },
            {
                "title": "The estimate of a journey",
                "numbers": [
                    _row(
                        "journey_fixed_minutes",
                        "What every journey takes before it covers any ground: the walk to a "
                        "stop, the wait and the walk from one.",
                        estimate.FIXED_MINUTES,
                        "minutes",
                        f"FIXED_MINUTES {journey}",
                    ),
                    _row(
                        "journey_minutes_a_km",
                        "What each kilometre in a straight line takes.",
                        estimate.MINUTES_A_KM,
                        "minutes a km",
                        f"MINUTES_A_KM {journey}",
                    ),
                    _row(
                        "journey_minutes_a_km_near_the_underground",
                        "What each kilometre takes where both ends are near the Underground.",
                        estimate.MINUTES_A_KM_NEAR_THE_UNDERGROUND,
                        "minutes a km",
                        f"MINUTES_A_KM_NEAR_THE_UNDERGROUND {journey}",
                    ),
                    _row(
                        "journey_near_the_underground",
                        "How near a station of the Underground an end of a journey is, to "
                        "count as near it.",
                        estimate.NEAR_THE_UNDERGROUND_M,
                        "m",
                        f"NEAR_THE_UNDERGROUND_M {journey}",
                    ),
                    _row(
                        "journey_within_by",
                        "An estimate is likely within a limit where it is under it by this "
                        "or more.",
                        estimate.WITHIN_BY,
                        "minutes",
                        f"WITHIN_BY {journey}",
                    ),
                    _row(
                        "journey_beyond_by",
                        "An estimate is likely beyond a limit where it is over it by more "
                        "than this.",
                        estimate.BEYOND_BY,
                        "minutes",
                        f"BEYOND_BY {journey}",
                    ),
                ],
            },
            {
                "title": "How near is near",
                "numbers": [
                    _row(
                        "near",
                        "A place is within reach of a home where it is no further than this, "
                        "in a straight line.",
                        WITHIN_M,
                        "m",
                        f"WITHIN_M in {CORE}/catalogue.py, and in the label of every measure "
                        "that counts within it",
                        "A change to the catalogue, in code: the labels say the distance.",
                    ),
                    _row(
                        "nearest",
                        "The nearest place is looked for no further than this.",
                        NEAREST_WITHIN_M,
                        "m",
                        f"NEAREST_WITHIN_M in {CORE}/catalogue.py, and in the label of every "
                        "measure of a distance",
                        "A change to the catalogue, in code: the labels say the distance.",
                    ),
                    _row(
                        "near_a_count_point",
                        "A count point of traffic is near a home where it stands no further "
                        "than this, in a straight line.",
                        TRAFFIC_WITHIN_M,
                        "m",
                        f"TRAFFIC_WITHIN_M in {CORE}/catalogue.py, and in the label of the "
                        "measure of traffic",
                        "A change to the catalogue, in code: the label says the distance.",
                    ),
                ],
            },
            {
                "title": "A price",
                "numbers": [
                    _row(
                        "fewest_sales",
                        "A price rests on no fewer sales than this. Fewer would say what one "
                        "home sold for.",
                        FEWEST_SALES,
                        "sales",
                        f"FEWEST_SALES in {CORE}/release.py",
                        "A change to core, in code, with its tests. It may be made larger, "
                        "and never smaller.",
                    )
                ],
            },
            {
                "title": "A recipe and a band",
                "numbers": [
                    _row(
                        "part_most",
                        "No part of a recipe holds more than this, so that no part places "
                        "an area alone.",
                        PART_MAX_HUNDREDTHS,
                        "in 100",
                        f"PART_MAX_HUNDREDTHS in {CORE}/catalogue.py",
                    ),
                    _row(
                        "band_needs",
                        "An area has a band only where it has a figure for this much of "
                        "the recipe.",
                        TAG_MIN_COVERAGE_HUNDREDTHS,
                        "in 100",
                        f"TAG_MIN_COVERAGE_HUNDREDTHS in {CORE}/catalogue.py",
                    ),
                ],
            },
            {
                "title": "What the panel calls out",
                "numbers": [
                    _row(
                        "rests_on_little",
                        "A band rests on little where the area has a figure for less than "
                        "this much of the recipe.",
                        look.LITTLE,
                        "in 100",
                        "LITTLE in tools/desk/panel/look.py",
                        "A change to the panel, in code. It changes what is called out, and "
                        "nothing that is served.",
                    ),
                    _row(
                        "far_from_beside",
                        "A figure is far from the areas beside it where it stands this far, "
                        "among all areas, from the middle one of theirs.",
                        look.FAR,
                        "points of 100",
                        "FAR in tools/desk/panel/look.py",
                        "A change to the panel, in code. It changes what is called out, and "
                        "nothing that is served.",
                    ),
                ],
            },
        ],
    }
