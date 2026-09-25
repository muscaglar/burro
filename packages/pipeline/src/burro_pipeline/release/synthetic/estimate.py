"""The made-up estimate of household income of each area of the made-up city.

It stands in for the statistics office's estimates until a real one is read,
so that the page that shows one can be built and checked. It reads nothing, as
the rest of the generator reads nothing, and it cites the reserved source
`synthetic` and no other.

It is drawn from noise alone. It follows no trait of an area, so nothing about
a made-up income goes with how leafy, how lively or how dear an area is: no
picture of the made-up city says that any kind of place is well off. Its words
are the made-up words of core, which name no real publisher.

It is drawn from a stream of its own, so that it moves no figure of the release
and none of the made-up count.
"""

from burro_core.ids import SYNTHETIC_SOURCE_ID
from burro_core.income import AreaIncome, Income, IncomeSource
from burro_core.release import SYNTHETIC_ATTRIBUTION, InMemoryRelease

from burro_pipeline.release.synthetic.chart import Draw

# The year the made-up estimates are dated: a financial year, as a real one is.
START, END = "2022-04", "2023-03"
# Which stream of the seed they are drawn from. The release and the count take those below.
STREAM = 11
# The new town that most surveys have not reached: it has no estimate.
NOT_ESTIMATED = "Otterby Fields"
# A made-up estimate lies between these, in pounds a year, and is given to the pound, as a
# real one is. So no figure of the release, which gives a price to the 500, is ever one.
LEAST, MOST = 28_000, 96_000
# How far each limit stands from the estimate, as a share of it.
NEAREST, FURTHEST = 0.06, 0.16


def made_up_income(release: InMemoryRelease, seed: int) -> Income:
    """The made-up estimates of a made-up release. The same release and seed give the same."""
    draw = Draw(seed + STREAM)
    areas: list[AreaIncome] = []
    # In the order of the ids, so that a seed draws the same.
    for found in release.neighbourhoods:
        estimate = round(draw.between(LEAST, MOST))
        spread = draw.between(NEAREST, FURTHEST)
        lower, upper = round(estimate * (1 - spread)), round(estimate * (1 + spread))
        if found.name == NOT_ESTIMATED:
            areas.append(AreaIncome(area_id=found.area_id, estimate=None, lower=None, upper=None))
            continue
        areas.append(AreaIncome(area_id=found.area_id, estimate=estimate, lower=lower, upper=upper))
    return Income(
        release_id=release.manifest.release_id,
        synthetic=True,
        start=START,
        end=END,
        source=IncomeSource(
            source_id=SYNTHETIC_SOURCE_ID,
            name="Synthetic test data",
            publisher="Burro",
            licence="None. Made up for testing",
            attribution=SYNTHETIC_ATTRIBUTION,
            url="",
            retrieved_on=release.manifest.built_at[:10],
        ),
        areas=tuple(sorted(areas, key=lambda area: area.area_id)),
    )
