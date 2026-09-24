"""The spine: London's output areas, what each is part of, and how many homes each holds.

London is the rows of the statistics office's lookup whose local authority
code starts `E09`: the 32 boroughs and the City. Every row is one output area
of the census of 2021, with the LSOA, the MSOA and the borough it is part of.

A home is a household at the census of 2021, from the table of accommodation
type. It is the weight behind every figure that is shared out or averaged "by
homes". The total of the table is read, and no other column of it.

An area is a set of output areas. No named neighbourhood exists yet: a person
has still to curate them. Until then an area is an MSOA, under the statistics
office's own label for it, which is its borough and a number. The label claims
no name. The names the House of Commons Library gives to MSOAs are not used:
their source is gated.

Nothing is counted against a number the code expects. `counts` says what the
files hold, and a test that reads the real files holds the numbers.
"""

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import cached_property

from burro_core.ids import AREA_ID_PATTERN, SLUG_PATTERN

from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind, Method
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

LOOKUP = "ons-oa21-lsoa21-msoa21-lad22-lookup"
# The registry asks that the version of the lookup is pinned.
LOOKUP_EDITION = "V2"
HOMES = "ons-census-2021-housing-tables"
# The code of every London borough, and of the City, starts so.
LONDON = "E09"
# The columns of the lookup that are read. It holds others, which are not.
OA, LSOA, LSOA_NAME, MSOA, MSOA_NAME = "OA21CD", "LSOA21CD", "LSOA21NM", "MSOA21CD", "MSOA21NM"
BOROUGH, BOROUGH_NAME = "LAD22CD", "LAD22NM"
OF_THE_LOOKUP = (OA, LSOA, LSOA_NAME, MSOA, MSOA_NAME, BOROUGH, BOROUGH_NAME)
# The table of accommodation type, by output area: the file inside the zip, and its columns.
HOMES_TABLE, HOMES_MEMBER = "ts044", "-ts044-oa.csv"
HOMES_CODE, HOMES_TOTAL = "geography code", "Accommodation type: Total: All households"
CODE = re.compile(r"E0[0-9][0-9]{6}")
# An MSOA's label is its borough and a number of three digits.
LABEL = re.compile(r"(?P<borough>.+) (?P<number>[0-9]{3})")

LABELLED = Method(
    derivation_id="published_label@1",
    sentence="The statistics office's own label for a census area, which is the name of its "
    "borough and a number, as its lookup of output areas gives it.",
    kind=Kind.MEASURED,
    code="burro_pipeline.cells.spine",
)


@dataclass(frozen=True, order=True)
class Cell:
    """One output area of London, what it is part of, and the homes it holds."""

    oa: str
    lsoa: str
    msoa: str
    borough: str
    # Households at the census of 2021.
    homes: int


@dataclass(frozen=True, order=True)
class Area:
    """One area of the first build: an MSOA, under the statistics office's own label."""

    area_id: str
    # The code of the MSOA the area is.
    code: str
    # The label, as the lookup gives it: the borough and a number.
    name: str
    slug: str
    borough: str
    borough_code: str


@dataclass(frozen=True)
class Homes:
    """Which area each output area is in, and how many homes it holds.

    Every output area of an area is here, with its homes. An output area with
    no homes weighs nothing. An area with no homes at all is covered by how
    many of its output areas have a figure.
    """

    area_of: Mapping[str, str]
    homes: Mapping[str, int]

    def __post_init__(self) -> None:
        if set(self.area_of) != set(self.homes):
            raise ValueError("every output area has an area and a count of homes")
        if any(count < 0 for count in self.homes.values()):
            raise ValueError("a count of homes is not below nothing")

    @cached_property
    def areas(self) -> tuple[str, ...]:
        return tuple(sorted(set(self.area_of.values())))

    @cached_property
    def of_area(self) -> Mapping[str, tuple[str, ...]]:
        """The output areas of each area, in the order of their codes."""
        found: dict[str, list[str]] = {area: [] for area in self.areas}
        for oa in sorted(self.area_of):
            found[self.area_of[oa]].append(oa)
        return {area: tuple(oas) for area, oas in found.items()}

    def weight(self, oas: Sequence[str], by_count: bool) -> float:
        """What some output areas weigh: their homes, or how many they are."""
        return float(len(oas)) if by_count else float(sum(self.homes[oa] for oa in oas))


def area_id_of(msoa: str) -> str:
    """The id of the area an MSOA is. It holds the MSOA's code, so it never moves."""
    return f"lon-n{msoa.lower()}"


def slug_of(name: str) -> str:
    return "-".join(re.findall(r"[a-z0-9]+", name.lower()))


@dataclass(frozen=True)
class Spine:
    """London as output areas, and the areas of the first build."""

    cells: tuple[Cell, ...]
    areas: tuple[Area, ...]
    # The files the spine was read from, by id.
    inputs: tuple[str, ...]

    @cached_property
    def area_of(self) -> Mapping[str, str]:
        """The area each output area is in."""
        return {cell.oa: area_id_of(cell.msoa) for cell in self.cells}

    @cached_property
    def lsoa_of(self) -> Mapping[str, str]:
        return {cell.oa: cell.lsoa for cell in self.cells}

    @cached_property
    def msoa_of(self) -> Mapping[str, str]:
        return {cell.oa: cell.msoa for cell in self.cells}

    @cached_property
    def homes(self) -> Mapping[str, int]:
        """The homes of each output area."""
        return {cell.oa: cell.homes for cell in self.cells}

    @cached_property
    def weights(self) -> Homes:
        """The areas and the homes, as a method that shares out by homes takes them."""
        return Homes(area_of=self.area_of, homes=self.homes)

    @cached_property
    def lsoas(self) -> tuple[str, ...]:
        return tuple(sorted({cell.lsoa for cell in self.cells}))

    @cached_property
    def area_of_lsoa(self) -> Mapping[str, str]:
        """The area each LSOA is in. An LSOA is part of one MSOA, so of one area."""
        return {cell.lsoa: area_id_of(cell.msoa) for cell in self.cells}

    def counts(self) -> dict[str, int]:
        """What the spine holds, counted and held to no number."""
        return {
            "output_areas": len(self.cells),
            "lsoas": len(self.lsoas),
            "msoas": len({cell.msoa for cell in self.cells}),
            "boroughs": len({cell.borough for cell in self.cells}),
            "areas": len(self.areas),
            "homes": sum(cell.homes for cell in self.cells),
        }


def read_lookup(opened: Opened) -> list[dict[str, str]]:
    """The rows of the lookup that are London's, each held to the shape of its codes."""
    found: list[dict[str, str]] = []
    with opened.text() as text:
        for row in opened.rows(text, OF_THE_LOOKUP):
            if not row[BOROUGH].startswith(LONDON):
                continue
            if not all(CODE.fullmatch(row[name]) for name in (OA, LSOA, MSOA, BOROUGH)):
                raise LockError("input_is_as_described", opened.file_id, "a code is not a code")
            found.append(row)
    return found


def read_homes(opened: Opened) -> dict[str, int]:
    """The households of every output area in the table, by its code."""
    found: dict[str, int] = {}
    with opened.text(HOMES_MEMBER) as text:
        for row in opened.rows(text, (HOMES_CODE, HOMES_TOTAL)):
            count = row[HOMES_TOTAL]
            if not (count.isascii() and count.isdigit()) or row[HOMES_CODE] in found:
                raise LockError("input_is_as_described", opened.file_id, "a count is not a count")
            found[row[HOMES_CODE]] = int(count)
    return found


def _nested(rows: Sequence[Mapping[str, str]], inner: str, outer: str) -> bool:
    """Whether every inner unit is part of one outer unit."""
    part_of: dict[str, str] = {}
    return all(part_of.setdefault(row[inner], row[outer]) == row[outer] for row in rows)


def _areas(rows: Sequence[Mapping[str, str]], file_id: str) -> tuple[Area, ...]:
    found: dict[str, Area] = {}
    for row in rows:
        label = LABEL.fullmatch(row[MSOA_NAME])
        if label is None or label["borough"] != row[BOROUGH_NAME]:
            raise LockError(
                "input_is_as_described", file_id, "a label is not a borough and a number"
            )
        area = Area(
            area_id=area_id_of(row[MSOA]),
            code=row[MSOA],
            name=row[MSOA_NAME],
            slug=slug_of(row[MSOA_NAME]),
            borough=row[BOROUGH_NAME],
            borough_code=row[BOROUGH],
        )
        if not re.fullmatch(AREA_ID_PATTERN, area.area_id) or not re.fullmatch(
            SLUG_PATTERN, area.slug
        ):
            raise LockError("input_is_as_described", file_id, "a label makes no id")
        found[area.area_id] = area
    areas = tuple(sorted(found.values()))
    if len({area.slug for area in areas}) != len(areas):
        raise LockError("input_is_as_described", file_id, "two areas share a label")
    return areas


def spine_of(lookup: Opened, homes: Opened) -> Spine:
    """The spine, from the lookup and the table of homes. It stops where the two do not fit.

    It stops when an output area is listed twice, when a unit is part of two
    larger ones, and when an output area has no count of homes: a figure shared
    out by homes cannot be worked out round a hole in the weights.
    """
    rows = read_lookup(lookup)
    if not rows:
        raise LockError("input_is_as_described", lookup.file_id, "it holds no row of London")
    if len({row[OA] for row in rows}) != len(rows):
        raise LockError("input_is_as_described", lookup.file_id, "an output area is there twice")
    if not (_nested(rows, LSOA, MSOA) and _nested(rows, MSOA, BOROUGH)):
        raise LockError("input_is_as_described", lookup.file_id, "a unit is part of two others")
    counted = read_homes(homes)
    if any(row[OA] not in counted for row in rows):
        raise LockError("input_is_as_described", homes.file_id, "an output area has no count")
    cells = tuple(
        sorted(Cell(row[OA], row[LSOA], row[MSOA], row[BOROUGH], counted[row[OA]]) for row in rows)
    )
    inputs = tuple(sorted({lookup.file_id, homes.file_id}))
    return Spine(cells=cells, areas=_areas(rows, lookup.file_id), inputs=inputs)


def build(inputs: Inputs) -> Spine:
    """The spine, from the files of the build. The gate is asked about each before it is read."""
    lookup = inputs.open(LOOKUP, Use.SCORING, edition=LOOKUP_EDITION)
    homes = inputs.open(HOMES, Use.SCORING, named=lambda name: HOMES_TABLE in name.lower())
    return spine_of(lookup, homes)
