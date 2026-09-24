"""The made-up count: who lived in each area of the made-up city, on a day nobody was counted.

It stands in for a census until a real one is read, so that the page that shows
one can be built and checked. It reads nothing, as the rest of the generator
reads nothing, and it cites the reserved source `synthetic` and no other.

It is unmistakably made up, in three ways that a test holds:

- Its three tables of groups name groups, countries and beliefs that do not
  exist. No heading of a real table of ethnic group, religion or country of
  birth is in it, so no picture of the made-up city can show a made-up share
  of real people.
- Those three tables are drawn from noise alone. They follow no trait of an
  area, so nothing about a made-up group goes with how leafy, how lively or
  how dear an area is.
- Its words are the made-up words of core, which name no real census.

Age and households follow the plan of the city a little, so that the tables
differ from area to area as real ones do. That is a claim about nothing.

It is drawn from a stream of its own, so that it moves no figure of the release.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from burro_core.census import (
    FLOOR,
    AreaCensus,
    Census,
    CensusKind,
    CensusLeftOut,
    CensusSource,
    Counted,
    Row,
    Table,
    Unit,
    Whole,
    is_small,
)
from burro_core.ids import SYNTHETIC_SOURCE_ID
from burro_core.release import SYNTHETIC_ATTRIBUTION, InMemoryRelease

from burro_pipeline.release.synthetic.chart import Draw
from burro_pipeline.release.synthetic.names import AREAS, BOROUGH, AreaPlan

# The day the made-up count is dated. It is the day of no count.
TAKEN_ON = "2021-03-21"
# Which stream of the seed the count is drawn from: the release takes the first two.
STREAM = 2
# The new town that most surveys have not reached: the count holds nothing for it.
NOT_COUNTED = "Otterby Fields"
# How many people a made-up small area holds, more or less.
PEOPLE_IN_A_SMALL_AREA = 310

PEOPLE = "usual residents"
HOUSEHOLDS = "households"


@dataclass(frozen=True)
class _Leaf:
    """A row that is counted, under the rows it stands beneath, with how much of it there is.

    `weight` is its share across the city, before an area moves it. `family`
    and `lively` say how far the traits of an area move it, and are nought
    for every table of made-up groups.
    """

    path: tuple[str, ...]
    weight: float
    family: float = 0.0
    lively: float = 0.0


def _bands() -> tuple[_Leaf, ...]:
    edges = [(low, low + 4) for low in range(5, 85, 5)]
    labels = ["Aged 4 and under", *(f"Aged {low} to {high}" for low, high in edges)]
    labels.append("Aged 85 and over")
    weights = (6, 6, 6, 5, 7, 9, 9, 8, 7, 7, 6, 6, 5, 4, 3, 3, 2, 1)
    # Children and the adults who raise them follow the schools. Those in their twenties
    # follow the places to go out.
    family = (1, 1, 1, 0.5, -0.5, -0.5, 0.5, 1, 1, 0.5, 0, 0, 0, 0, 0, 0, 0, 0)
    lively = (-0.5, -0.5, -0.5, 0.5, 1.5, 1.5, 0.5, 0, 0, 0, 0, 0, -0.5, -0.5, -0.5, 0, 0, 0)
    return tuple(
        _Leaf((label,), weight, by_family, by_lively)
        for label, weight, by_family, by_lively in zip(labels, weights, family, lively, strict=True)
    )


_ALONE = "One person living alone"
_FAMILY = "One family"
_MARRIED = "A married couple or civil partners"
_TOGETHER = "A couple living together"
_PARENT = "One parent"
_OTHER = "Other households"
_DEPEND = "Children who depend on them"
_GROWN = "Grown-up children only"

_HOUSEHOLDS = (
    _Leaf((_ALONE, "Aged 66 or over"), 12),
    _Leaf((_ALONE, "Under 66"), 18, -1, 1),
    _Leaf((_FAMILY, "Everyone aged 66 or over"), 6),
    _Leaf((_FAMILY, _MARRIED, "No children"), 9),
    _Leaf((_FAMILY, _MARRIED, _DEPEND), 14, 1.5, -0.5),
    _Leaf((_FAMILY, _MARRIED, _GROWN), 5),
    _Leaf((_FAMILY, _TOGETHER, "No children"), 7, -0.5, 1),
    _Leaf((_FAMILY, _TOGETHER, _DEPEND), 4, 1),
    _Leaf((_FAMILY, _TOGETHER, _GROWN), 0.4),
    _Leaf((_FAMILY, _PARENT, _DEPEND), 7, 1),
    _Leaf((_FAMILY, _PARENT, _GROWN), 4),
    _Leaf((_FAMILY, "Any other family"), 1.2),
    _Leaf((_OTHER, "With children who depend on them"), 4, 0.5),
    _Leaf(
        (
            _OTHER,
            "Any other, which takes in every household of students and every household "
            "where all are aged 66 or over",
        ),
        8.4,
        -1,
        1.5,
    ),
)

_NEAR = "Made-up countries nearby"
_FAR = "Made-up countries far away"

_BORN = (
    _Leaf(("The made-up home country",), 61),
    _Leaf((_NEAR, "Made-up country N1"), 9),
    _Leaf((_NEAR, "Made-up country N2"), 5),
    _Leaf((_NEAR, "Made-up country N3"), 2),
    _Leaf((_NEAR, "Any other made-up country nearby"), 0.6),
    _Leaf((_FAR, "Made-up country F1"), 11),
    _Leaf((_FAR, "Made-up country F2"), 7),
    _Leaf((_FAR, "Made-up country F3"), 3),
    _Leaf((_FAR, "Made-up country F4"), 0.9),
    _Leaf((_FAR, "Any other made-up country far away"), 0.5),
)

_GROUP_B = "Made-up group B, with a name as long as the longest that a publisher prints"

_GROUPS = (
    _Leaf(("Made-up group A", "First part"), 9),
    _Leaf(("Made-up group A", "Second part"), 3),
    _Leaf(("Made-up group A", "Third part"), 6),
    _Leaf(("Made-up group A", "Fourth part"), 2),
    _Leaf(("Made-up group A", "Any other part"), 4),
    _Leaf((_GROUP_B, "First part"), 7),
    _Leaf((_GROUP_B, "Second part"), 4),
    _Leaf((_GROUP_B, "Any other part"), 2),
    _Leaf(("Made-up group C", "First part"), 1.5),
    _Leaf(("Made-up group C", "Second part"), 0.8),
    _Leaf(("Made-up group C", "Third part"), 1.4),
    _Leaf(("Made-up group C", "Any other part"), 1.6),
    _Leaf(("Made-up group D", "First part"), 36),
    _Leaf(("Made-up group D", "Second part"), 2),
    _Leaf(("Made-up group D", "Third part"), 0.1),
    _Leaf(("Made-up group D", "Fourth part"), 0.4),
    _Leaf(("Made-up group D", "Any other part"), 14),
    _Leaf(("Any other made-up group", "First part"), 1.6),
    _Leaf(("Any other made-up group", "Any other part"), 2.6),
)

_BELIEFS = (
    _Leaf(("None of the made-up beliefs",), 27),
    _Leaf(("Made-up belief A",), 40),
    _Leaf(("Made-up belief B",), 1),
    _Leaf(("Made-up belief C",), 5),
    _Leaf(("Made-up belief D",), 1.7),
    _Leaf(("Made-up belief E",), 15),
    _Leaf(("Made-up belief F",), 1.6),
    _Leaf(("Any other made-up belief",), 0.9),
    _Leaf(("Gave no answer",), 7),
)


@dataclass(frozen=True)
class _Plan:
    code: str
    kind: CensusKind
    title: str
    variable: str
    unit: Unit
    definition: str
    leaves: tuple[_Leaf, ...]
    # How far an area's share of a row may stray from the city's, as a share of itself.
    noise: float


PLANS = (
    _Plan(
        "SYN-HH",
        CensusKind.HOUSEHOLDS,
        "Households, made up",
        "Household",
        Unit.HOUSEHOLDS,
        "Who shares a home, by how they are related. Made up for testing: it counts nobody.",
        _HOUSEHOLDS,
        0.25,
    ),
    _Plan(
        "SYN-BORN",
        CensusKind.COUNTRY_OF_BIRTH,
        "Made-up countries, in place of country of birth",
        "Made-up country",
        Unit.PEOPLE,
        "The made-up country a person was born in. Made up for testing: it counts nobody.",
        _BORN,
        0.6,
    ),
    _Plan(
        "SYN-AGE",
        CensusKind.AGE,
        "Age, made up",
        "Age",
        Unit.PEOPLE,
        "A person's age on the day of the made-up count. Made up for testing: it counts nobody.",
        _bands(),
        0.2,
    ),
    _Plan(
        "SYN-GRP",
        CensusKind.ETHNIC_GROUP,
        "Made-up groups, in place of ethnic group",
        "Made-up group",
        Unit.PEOPLE,
        "The made-up group a person would say they belong to. Made up for testing: it counts "
        "nobody.",
        _GROUPS,
        0.6,
    ),
    _Plan(
        "SYN-BLF",
        CensusKind.RELIGION,
        "Made-up beliefs, in place of religion",
        "Made-up belief",
        Unit.PEOPLE,
        "The made-up belief a person would name, or none. Made up for testing: it counts nobody.",
        _BELIEFS,
        0.6,
    ),
)


def _paths(plan: _Plan) -> tuple[tuple[str, ...], ...]:
    """Every row of a table in the order it is printed: a group, and then what stands under it."""
    found: list[tuple[str, ...]] = []
    for leaf in plan.leaves:
        for depth in range(1, len(leaf.path) + 1):
            if leaf.path[:depth] not in found:
                found.append(leaf.path[:depth])
    return tuple(found)


def _code(plan: _Plan, position: int) -> str:
    return f"{plan.code.casefold()}-{position + 1:02d}"


def _table(plan: _Plan) -> Table:
    return Table(
        table_code=plan.code,
        kind=plan.kind,
        title=plan.title,
        variable=plan.variable,
        universe=HOUSEHOLDS if plan.unit is Unit.HOUSEHOLDS else PEOPLE,
        unit=plan.unit,
        definition=plan.definition,
        source_id=SYNTHETIC_SOURCE_ID,
        url="",
        rows=tuple(
            Row(
                code=_code(plan, position),
                heading=": ".join(path),
                label=path[-1],
                depth=len(path) - 1,
            )
            for position, path in enumerate(_paths(plan))
        ),
    )


def _shared_out(total: int, weights: Sequence[float]) -> list[int]:
    """`total` shared out by `weights` in whole numbers that add up to it."""
    whole = sum(weights)
    exact = [total * weight / whole for weight in weights]
    counts = [int(each) for each in exact]
    # What is left over goes to the rows that lost most by being cut down.
    by_loss = sorted(range(len(exact)), key=lambda at: (counts[at] - exact[at], at))
    for at in by_loss[: total - sum(counts)]:
        counts[at] += 1
    return counts


def _leaf_counts(plan: _Plan, area: AreaPlan, base: int, draw: Draw) -> list[int]:
    weights = [
        max(
            leaf.weight
            * (1 + leaf.family * (area.family - 0.4) + leaf.lively * (area.lively - 0.3))
            * (1 + draw.around(plan.noise)),
            leaf.weight / 20,
        )
        for leaf in plan.leaves
    ]
    return _shared_out(base, weights)


def _row_counts(plan: _Plan, leaves: Sequence[int]) -> list[int]:
    """A count for every row. A group's is the sum of what stands under it."""
    return [
        sum(
            count
            for leaf, count in zip(plan.leaves, leaves, strict=True)
            if leaf.path[: len(path)] == path
        )
        for path in _paths(plan)
    ]


def _held(code: str, base: int, counts: Sequence[int]) -> Counted:
    """The figures as the count holds them: no count that is under 1 in 100 of the base."""
    if base < FLOOR:
        return Counted(table_code=code, base=None, counts=(), reason=CensusLeftOut.TOO_FEW)
    kept = tuple(None if is_small(count, base) else count for count in counts)
    return Counted(table_code=code, base=base, counts=kept, reason=None)


def _not_held(code: str) -> Counted:
    return Counted(table_code=code, base=None, counts=(), reason=CensusLeftOut.NOT_HELD)


def _people(area: AreaPlan, draw: Draw) -> int:
    if not area.rankable:
        # Docks and marsh: too few live there for a share to be steady.
        return round(draw.between(240, 720))
    flats = area.flats if area.flats is not None else area.lively
    return round(4_200 + 7_000 * flats + draw.between(0, 2_400))


def made_up_census(release: InMemoryRelease, seed: int) -> Census:
    """The made-up count of a made-up release. The same release and seed give the same count."""
    draw = Draw(seed + STREAM)
    plans = {plan.name: plan for plan in AREAS}
    totals = {plan.code: [0] * len(_paths(plan)) for plan in PLANS}
    bases = {plan.code: 0 for plan in PLANS}
    areas: list[AreaCensus] = []
    # In the order of the plan, which is the order of the ids, so that a seed draws the same.
    for found in release.neighbourhoods:
        area = plans[found.name]
        people = _people(area, draw)
        households = round(people / (2.0 + 0.9 * area.family))
        tables: list[Counted] = []
        for plan in PLANS:
            base = households if plan.unit is Unit.HOUSEHOLDS else people
            counts = _row_counts(plan, _leaf_counts(plan, area, base, draw))
            if area.name == NOT_COUNTED:
                tables.append(_not_held(plan.code))
                continue
            tables.append(_held(plan.code, base, counts))
            # The whole city is every area that was counted, the smallest among them.
            bases[plan.code] += base
            totals[plan.code] = [a + b for a, b in zip(totals[plan.code], counts, strict=True)]
        areas.append(
            AreaCensus(
                area_id=found.area_id,
                output_areas=max(1, round(people / PEOPLE_IN_A_SMALL_AREA)),
                tables=tuple(tables),
            )
        )

    built_on = release.manifest.built_at[:10]
    source = CensusSource(
        source_id=SYNTHETIC_SOURCE_ID,
        name="Synthetic test data",
        publisher="Burro",
        licence="None. Made up for testing",
        attribution=SYNTHETIC_ATTRIBUTION,
        url="",
        retrieved_on=built_on,
    )
    return Census(
        release_id=release.manifest.release_id,
        synthetic=True,
        taken_on=TAKEN_ON,
        retrieved_on=built_on,
        sources=(source,),
        tables=tuple(_table(plan) for plan in PLANS),
        whole=Whole(
            name=BOROUGH,
            tables=tuple(_held(plan.code, bases[plan.code], totals[plan.code]) for plan in PLANS),
        ),
        areas=tuple(areas),
    )
