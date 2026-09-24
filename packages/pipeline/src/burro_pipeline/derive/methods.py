"""The methods: from a publisher's figure at one geography to a figure for an area.

Section 5 of the pipeline design names them, and the plan adds the mean by
homes. Each is here once, for every measure to use. The first build needs six:

| Method | From | The area's figure is |
|---|---|---|
| `oa_sum` | A count by output area | The sum over its output areas |
| `lsoa_to_area_by_homes` | A count by LSOA or MSOA | The sum, a split unit shared out by homes |
| `lsoa_ratio_by_homes` | Two counts by unit | One sum over the other, never a mean of rates |
| `lsoa_value_by_homes` | A rate with no top and bottom | The mean over the area's homes |
| `grid_at_homes` | A value by square of a grid | The value at each centre, averaged by homes |
| `area_row_ratio` | Two counts the publisher gives for the area itself | One over the other |

An area is a set of output areas, and every method but the last goes through
them. So a boundary that moves needs no new arithmetic, and a unit that lies
in two areas is shared out between them by where its homes are.

`area_row_ratio` is for the case where the publisher's file holds a row for
the area itself. While an area is an MSOA the council tax tables do. A
publisher that rounds its counts rounds the area's own count once, and a sum
of the rows of smaller areas takes in one rounding for each. So the area's own
row is the better count, and it is the one a reader finds who opens the
publisher's table. When areas are drawn by hand no file holds a row for one,
and a measure goes back to `lsoa_ratio_by_homes`.

A seventh is for a file of lines or of outlines: `homes_within`, the share of
an area's homes whose output area has its centre within a distance of what is
measured. Its record is made for one distance by `homes_within_at`, and the
distance is part of its id: the evidence of a release holds one record under
one id, and two measures may use two distances.

Every method gives one `Worked` for every area: a value or none, how much of
the area stood behind it, and the state that leaves the figure in. Nothing is
filled in:

- A unit the publisher holds no figure for adds nothing, and the area's
  coverage falls by that unit's homes.
- Below half the area's homes covered, the value is not given.
- With nothing covered the area is a gap in the source, or withheld if the
  publisher withheld every unit of it.

Coverage is a share of homes. A home is a household at the census of 2021, so
an output area that has gained homes since weighs what it did then.

The arithmetic repeats: every loop is over a sorted list and every sum is
`math.fsum`. A method does not round a figure. A measure rounds its figure
with `to_places`, which takes a half upward, as a person does who rounds by
hand. The share of homes covered is kept to six decimal places the same way.
`to_places` is in `burro_pipeline.rounding`, and is handed on from here.
"""

import math
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass

from burro_pipeline.cells.spine import Homes
from burro_pipeline.evidence.method import Kind, Method
from burro_pipeline.evidence.receipt import Receipt
from burro_pipeline.evidence.row import FULLY_COVERED, EvidenceRow, Flag, State
from burro_pipeline.inputs import period_of, retrieved_on
from burro_pipeline.rounding import to_places

# Below this share of an area's homes, a figure is not given (contract, section 2).
ENOUGH = 0.5
# A share is held to this many decimal places, as a row of evidence holds it.
DECIMALS = 6
# The width of a square of the grid the first build reads, in metres.
SQUARE = 1000
CODE = "burro_pipeline.derive.methods"
_NOT_GIVEN = "and not given where under 50 in 100 of the area's homes are in {where} with {what}."

OA_SUM = Method(
    derivation_id="oa_sum@1",
    sentence="The sum over the area's census output areas, "
    + _NOT_GIVEN.format(where="an output area", what="a count"),
    kind=Kind.MEASURED,
    parameters={"enough_in_100": 50},
    code=CODE,
)
LSOA_TO_AREA_BY_HOMES = Method(
    derivation_id="lsoa_to_area_by_homes@1",
    sentence="The sum of the counts of the small census areas the area takes in, each shared "
    "out by where its homes were at the census, "
    + _NOT_GIVEN.format(where="a small area", what="a count"),
    kind=Kind.MEASURED,
    parameters={"enough_in_100": 50},
    code=CODE,
)
LSOA_RATIO_BY_HOMES = Method(
    derivation_id="lsoa_ratio_by_homes@1",
    sentence="One sum over another, each added up over the small census areas the area takes "
    "in and shared out by where their homes were at the census, "
    + _NOT_GIVEN.format(where="a small area", what="both counts"),
    kind=Kind.MEASURED,
    parameters={"enough_in_100": 50},
    code=CODE,
)
LSOA_VALUE_BY_HOMES = Method(
    derivation_id="lsoa_value_by_homes@1",
    sentence="The mean of the values of the small census areas the area takes in, weighted by "
    "their homes at the census, " + _NOT_GIVEN.format(where="a small area", what="a value"),
    kind=Kind.AVERAGED,
    parameters={"enough_in_100": 50},
    code=CODE,
)
GRID_AT_HOMES = Method(
    derivation_id="grid_at_homes@1",
    sentence="A modelled value on a grid of squares 1000 metres wide, read at the centre of "
    "population of each census output area and averaged by homes at the census, "
    + _NOT_GIVEN.format(where="an output area on a square", what="a value"),
    kind=Kind.MODELLED,
    parameters={"square_metres": SQUARE, "enough_in_100": 50},
    code=CODE,
)
AREA_ROW_RATIO = Method(
    derivation_id="area_row_ratio@1",
    sentence="One count over another, each taken from the publisher's own row for the area and "
    "never added up from the rows of smaller areas, and not given where the row gives no count "
    "or where under 50 in 100 of the area's homes are counted in the bottom.",
    kind=Kind.MEASURED,
    parameters={"enough_in_100": 50},
    code=CODE,
)
METHODS = (
    OA_SUM,
    LSOA_TO_AREA_BY_HOMES,
    LSOA_RATIO_BY_HOMES,
    LSOA_VALUE_BY_HOMES,
    GRID_AT_HOMES,
    AREA_ROW_RATIO,
)


@dataclass(frozen=True)
class Worked:
    """One figure for one area, and how much of the area stood behind it."""

    value: float | None
    # How many of the source's units the area takes in, and how many had a figure.
    units_used: int
    units_expected: int
    # The share of the area's homes that had a figure.
    weight_covered: float
    state: State
    flags: tuple[Flag, ...] = ()


def cell_of(easting: float, northing: float, square: int = SQUARE) -> tuple[int, int]:
    """The square of a grid a point stands on, by the corner nearest the grid's origin.

    A square takes in its west and south sides and not its east and north, so
    a point on a line between two squares is on one square and never on two.
    """
    return math.floor(easting / square) * square, math.floor(northing / square) * square


def _worked(
    value: float | None,
    used: int,
    expected: int,
    covered: float,
    withheld: bool,
    flags: Collection[Flag],
) -> Worked:
    """The figure as it is given, with the state its coverage leaves it in."""
    covered = to_places(min(max(covered, 0.0), 1.0), DECIMALS)
    marks: set[Flag] = set(flags) | ({Flag.SUPPRESSED_IN_SOURCE} if withheld else set())
    if covered == 0 or used == 0 or (value is None and covered >= ENOUGH):
        # Nothing to go on. A sum over nothing is no sum, and nor is a share of no homes.
        state = State.SUPPRESSED if withheld else State.SOURCE_GAP
        return Worked(None, 0, expected, 0.0, state, tuple(sorted(marks)))
    if covered < ENOUGH:
        return Worked(None, used, expected, covered, State.BELOW_THRESHOLD, tuple(sorted(marks)))
    state = State.PRESENT if covered >= FULLY_COVERED else State.PARTIAL
    return Worked(value, used, expected, covered, state, tuple(sorted(marks)))


@dataclass(frozen=True)
class _Part:
    """The part of one unit that lies in one area."""

    unit: str
    oas: tuple[str, ...]
    # The share of the unit's homes that are in the area.
    share: float
    # Whether the unit lies in another area too.
    split: bool


def _parts(homes: Homes, unit_of: Mapping[str, str]) -> dict[str, list[_Part]]:
    """For each area, the units it takes in, and how much of each."""
    if not set(homes.area_of) <= set(unit_of):
        raise ValueError("every output area is part of a unit")
    of_unit: dict[str, list[str]] = {}
    for oa in sorted(homes.area_of):
        of_unit.setdefault(unit_of[oa], []).append(oa)
    found: dict[str, list[_Part]] = {area: [] for area in homes.areas}
    for unit in sorted(of_unit):
        oas = of_unit[unit]
        # A unit with no homes is shared out by how many of its output areas each area has.
        by_count = homes.weight(oas, by_count=False) == 0
        whole = homes.weight(oas, by_count)
        within: dict[str, list[str]] = {}
        for oa in oas:
            within.setdefault(homes.area_of[oa], []).append(oa)
        for area in sorted(within):
            share = homes.weight(within[area], by_count) / whole
            found[area].append(_Part(unit, tuple(within[area]), share, len(within) > 1))
    return found


def _covered(homes: Homes, area: str, with_a_figure: Sequence[str]) -> float:
    """The share of an area's homes that are in the output areas given."""
    every = homes.of_area[area]
    by_count = homes.weight(every, by_count=False) == 0
    whole = homes.weight(every, by_count)
    return homes.weight(with_a_figure, by_count) / whole if whole else 0.0


def oa_sum(
    counts: Mapping[str, float],
    homes: Homes,
    *,
    withheld: Collection[str] = (),
    flags: Collection[Flag] = (),
) -> dict[str, Worked]:
    """The sum of a count over each area's output areas.

    `counts` holds the output areas the publisher gives a count for, and
    `withheld` those it withheld the count of.
    """
    found: dict[str, Worked] = {}
    for area in homes.areas:
        every = homes.of_area[area]
        used = [oa for oa in every if oa in counts]
        total = math.fsum(counts[oa] for oa in used) if used else None
        hidden = any(oa in withheld for oa in every)
        covered = _covered(homes, area, used)
        found[area] = _worked(total, len(used), len(every), covered, hidden, flags)
    return found


def lsoa_ratio_by_homes(
    top: Mapping[str, float],
    bottom: Mapping[str, float],
    unit_of: Mapping[str, str],
    homes: Homes,
    *,
    times: float = 1.0,
    withheld: Collection[str] = (),
    flags: Collection[Flag] = (),
) -> dict[str, Worked]:
    """One sum over another, for each area: a share, a rate or a density.

    The top and the bottom are each shared out between the areas a unit lies
    in, by where its homes are, and added up. Then one is divided by the
    other. Only a unit with both a top and a bottom is added to either. With
    `times` at 100 the figure is a percentage. An area whose bottom adds up to
    nothing has no figure, and is given as a gap in the source.
    """
    found: dict[str, Worked] = {}
    for area, parts in _parts(homes, unit_of).items():
        used = [part for part in parts if part.unit in top and part.unit in bottom]
        above = math.fsum(part.share * top[part.unit] for part in used)
        below = math.fsum(part.share * bottom[part.unit] for part in used)
        value = times * above / below if below > 0 else None
        found[area] = _of_parts(homes, area, parts, used, value, withheld, flags)
    return found


def area_row_ratio(
    top: Mapping[str, float],
    bottom: Mapping[str, float],
    homes: Homes,
    *,
    times: float = 1.0,
    covered: Mapping[str, float] | None = None,
    withheld: Collection[str] = (),
    flags: Collection[Flag] = (),
) -> dict[str, Worked]:
    """One count of the area's own row over another: a share, a rate or a density.

    `top` and `bottom` hold a count for each area whose row gives one, by the
    id of the area. Nothing is added up and nothing is shared out: the row is
    the publisher's count for the area. An area with no top or no bottom has
    no figure. `withheld` names the areas whose row withholds a count of the
    top: with no top such an area is said to be withheld, and with one its
    figure is marked. `covered` is the share of an area's homes that its
    bottom counts, where that is not all of them. With `times` at 100 the
    figure is a percentage.
    """
    if not set(top) | set(bottom) | set(withheld) | set(covered or ()) <= set(homes.areas):
        raise ValueError("every row is the row of an area of the build")
    found: dict[str, Worked] = {}
    for area in homes.areas:
        used = int(area in top and area in bottom)
        value = times * top[area] / bottom[area] if used and bottom[area] > 0 else None
        share = (1.0 if covered is None else covered.get(area, 0.0)) if used else 0.0
        found[area] = _worked(value, used, 1, share, area in withheld, flags)
    return found


def lsoa_to_area_by_homes(
    counts: Mapping[str, float],
    unit_of: Mapping[str, str],
    homes: Homes,
    *,
    withheld: Collection[str] = (),
    flags: Collection[Flag] = (),
) -> dict[str, Worked]:
    """The sum of a count over the units each area takes in, a split unit shared out by homes."""
    found: dict[str, Worked] = {}
    for area, parts in _parts(homes, unit_of).items():
        used = [part for part in parts if part.unit in counts]
        value = math.fsum(part.share * counts[part.unit] for part in used) if used else None
        found[area] = _of_parts(homes, area, parts, used, value, withheld, flags)
    return found


def lsoa_value_by_homes(
    values: Mapping[str, float],
    unit_of: Mapping[str, str],
    homes: Homes,
    *,
    withheld: Collection[str] = (),
    flags: Collection[Flag] = (),
) -> dict[str, Worked]:
    """The mean of a unit's value over each area's homes.

    It is for a rate or a share that the publisher gives with no top and no
    bottom, so that no sum can be taken. Every home of an output area is given
    the value of the unit it is in. The figure is marked as averaged.
    """
    found: dict[str, Worked] = {}
    for area, parts in _parts(homes, unit_of).items():
        used = [part for part in parts if part.unit in values]
        by_count = homes.weight(homes.of_area[area], by_count=False) == 0
        weights = [homes.weight(part.oas, by_count) for part in used]
        whole = math.fsum(weights)
        value = (
            math.fsum(
                weight * values[part.unit] for weight, part in zip(weights, used, strict=True)
            )
            / whole
            if whole > 0
            else None
        )
        found[area] = _of_parts(homes, area, parts, used, value, withheld, flags)
    return found


def _of_parts(
    homes: Homes,
    area: str,
    parts: Sequence[_Part],
    used: Sequence[_Part],
    value: float | None,
    withheld: Collection[str],
    flags: Collection[Flag],
) -> Worked:
    covered = _covered(homes, area, [oa for part in used for oa in part.oas])
    hidden = any(part.unit in withheld for part in parts)
    split = {Flag.UNIT_SPLIT} if any(part.split for part in used) else set[Flag]()
    return _worked(value, len(used), len(parts), covered, hidden, set(flags) | split)


def grid_at_homes(
    grid: Mapping[tuple[int, int], float],
    centres: Mapping[str, tuple[float, float]],
    homes: Homes,
    *,
    square: int = SQUARE,
    flags: Collection[Flag] = (),
) -> dict[str, Worked]:
    """The value of a grid where each area's homes are, averaged by homes.

    `grid` holds the value of each square, by the corner `cell_of` gives.
    `centres` holds the point where an output area's homes are taken to
    stand, on the same grid as the squares. An output area with no centre,
    or on a square with no value, adds nothing. The figure is marked as
    modelled.
    """
    found: dict[str, Worked] = {}
    for area in homes.areas:
        every = homes.of_area[area]
        read = {
            oa: grid[cell_of(*centres[oa], square)]
            for oa in every
            if oa in centres and cell_of(*centres[oa], square) in grid
        }
        used = sorted(read)
        by_count = homes.weight(every, by_count=False) == 0
        whole = homes.weight(used, by_count)
        value = (
            math.fsum(homes.weight([oa], by_count) * read[oa] for oa in used) / whole
            if whole > 0
            else None
        )
        covered = _covered(homes, area, used)
        found[area] = _worked(value, len(used), len(every), covered, False, flags)
    return found


def homes_within_at(metres: int) -> Method:
    """The record of `homes_within` for one distance, in whole metres.

    The distance is part of the id, so that two measures that use two
    distances name two records, and two that use one distance name the same.
    The sentence does not say what is measured: the measure's own does.
    """
    if metres < 1:
        raise ValueError("a distance is a whole number of metres, and more than none")
    return Method(
        derivation_id=f"homes_within_{metres}m@1",
        sentence=f"The share of the area's homes whose census output area has its centre of "
        f"population within {metres} metres of what is measured, in a straight line, each output "
        "area weighed by its homes at the census, "
        + _NOT_GIVEN.format(where="an output area", what="a centre that the source covers"),
        kind=Kind.MEASURED,
        parameters={"metres": metres, "enough_in_100": 50},
        code=CODE,
    )


def homes_within(
    near: Mapping[str, bool],
    homes: Homes,
    *,
    times: float = 1.0,
    flags: Collection[Flag] = (),
) -> dict[str, Worked]:
    """The share of each area's homes that are in an output area near what is measured.

    `near` holds a verdict for each output area the source covers: whether
    its centre is within the distance. Every home of an output area takes the
    verdict of its centre. An output area with no verdict adds nothing, to
    the top or to the bottom, and the area's coverage falls by its homes. It
    is never taken to be far. With `times` at 100 the figure is a percentage.
    """
    if not set(near) <= set(homes.area_of):
        raise ValueError("every verdict is of an output area of the build")
    found: dict[str, Worked] = {}
    for area in homes.areas:
        every = homes.of_area[area]
        used = [oa for oa in every if oa in near]
        by_count = homes.weight(every, by_count=False) == 0
        whole = homes.weight(used, by_count)
        close = homes.weight([oa for oa in used if near[oa]], by_count)
        value = times * close / whole if whole > 0 else None
        covered = _covered(homes, area, used)
        found[area] = _worked(value, len(used), len(every), covered, False, flags)
    return found


def row_of(fact_id: str, worked: Worked, method: Method, files: Sequence[Receipt]) -> EvidenceRow:
    """The row of evidence behind one figure, or behind one figure that is missing.

    `files` are the receipts of every file the figure was worked out from: the
    publisher's table, the lookup, the homes, and any boundary or centre.
    """
    return EvidenceRow(
        fact_id=fact_id,
        derivation_id=method.derivation_id,
        inputs=tuple(sorted({receipt.file_id for receipt in files})),
        data_period=period_of(files),
        retrieved_on=retrieved_on(files),
        units_used=worked.units_used,
        units_expected=worked.units_expected,
        weight_covered=worked.weight_covered,
        state=worked.state,
        flags=worked.flags,
        value=worked.value,
    )
