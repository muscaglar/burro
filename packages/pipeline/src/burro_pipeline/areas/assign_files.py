"""The ground a draft is made on, read from the publishers' files through the licence gate.

Every file is asked for under the use `gazetteer`, and the gate is asked before
the file is looked for. A source the gate refuses for that use is not read,
however useful it would be. So three things the design counts on are not here:

| The design uses | The gate says | So |
|---|---|---|
| Homes in each output area | Not for `gazetteer` | An area's size is counted in output areas |
| The river | `os-open-rivers` is not for `gazetteer` | Only the tidal water is a barrier |
| MSOA names | The source is gated | No distance is cut for one |

| Read | From | For |
|---|---|---|
| London's output areas and their boroughs | The lookup | The list of what must be given |
| Where the homes of each stand | The centres of population | Where a distance is measured from |
| The generalised outlines | `ons-output-areas-2021`, BGC V2 | Sides, land, and what is drawn |
| The full outlines | The same source, BFC V8 | The output area a seed lies in, and the water |
| Boroughs and wards | Boundary-Line | The water, and the ward of each output area |
| Links and nodes | OS Open Roads | Distance along the roads |
| Records of roads | OS Open Names | The settlement the roads of an output area name |

**The tidal water.** Boundary-Line draws a borough to the middle of the tidal
river, and an output area stops at the mean high water mark. What lies between
is the water. No file the gate gives draws the river west of where the tide
ends, so there the river is no barrier and no output area has a bank.

**The banks.** Output areas on the two banks share no side, because the water
lies between them. So the output areas that lie wholly east of the western end
of the water fall into two pieces, and each piece is a bank. The one further
north is the north bank. Nothing is taken from memory.

**A link is taken up** where it lies over the water, unless both its ends are
on one bank: a road over a creek stays, and a bridge or a tunnel between the
banks goes. So no distance is measured across the river.

Nothing is written to the store. A GeoPackage inside a zip is taken out beside
the checked copy of the zip, because SQLite cannot read inside one.
"""

import math
import re
import shutil
import zipfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from burro_pipeline.areas import assign_settlements
from burro_pipeline.areas import assign_shapes as geometry
from burro_pipeline.areas.assign import NORTH, NOT_DRAWN, ROADS, SOUTH, WARD, Cell, Said, Seed
from burro_pipeline.areas.assign_settlements import Settlement
from burro_pipeline.areas.grow import Link, Roads, millimetres, pieces_of, roads_of
from burro_pipeline.cells.shapes import Point, Shape, read_outlines
from burro_pipeline.cells.spine import (
    BOROUGH,
    BOROUGH_NAME,
    LOOKUP,
    LOOKUP_EDITION,
    OA,
    read_lookup,
)
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

USE = Use.GAZETTEER
CENTRES, CENTRES_EDITION = "ons-oa-pwc-2021", "V4"
EASTING, NORTHING = "X", "Y"
BOUNDARIES = "ons-output-areas-2021"
TO_DRAW, TO_PLACE = "BGC V2", "BFC V8"
BOUNDARY_LINE, BOUNDARY_LINE_INSIDE = "os-boundary-line", "bdline_gb.gpkg"
BOROUGHS_AND_WARDS = ("district_borough_unitary", "district_borough_unitary_ward")
KIND, CODE, NAME = "Area_Code", "Census_Code", "Name"
A_BOROUGH, A_WARD = "LBO", "LBW"
# What Boundary-Line writes after the name of every ward.
WARD_ENDS = " Ward"
OPEN_ROADS, ROADS_INSIDE = "os-open-roads", "oproad_gb.gpkg"
LINKS, NODES = "road_link", "road_node"
LINK_FIELDS = ("start_node", "end_node", "length")
PIECE = 16 * 1024 * 1024
# The apostrophe as a typesetter writes it.
CURLED = "\N{RIGHT SINGLE QUOTATION MARK}"


@dataclass(frozen=True)
class Reading:
    """Every number the reading of the ground turns on."""

    # How far beyond London the roads are read, in metres, so that a way may leave
    # London and come back.
    margin: float = 2_000.0
    # The least ground, in hectares, that is taken for the tidal water. The slivers
    # where two publishers' lines differ are under one hectare each.
    least_water: float = 100.0
    # The fewest nodes in a piece of the roads that a seed may start from. A yard or a
    # private road that joins nothing is a piece of a few nodes. The largest piece is
    # always one a seed may start from, however small it is.
    least_piece: int = 50


@dataclass(frozen=True)
class SeedPoint:
    """One seed as a file gives it: a point with a weight, and the name it stands for."""

    seed_id: str
    point: Point
    weight: float
    # The name as its publisher writes it. Empty where the file of seeds gives none.
    name: str = ""
    # The id of the publisher's record the seed was read from. Empty where none is given.
    record: str = ""


@dataclass(frozen=True)
class Ward:
    """The ward that holds most of an output area, and the share of it that it holds."""

    code: str
    # The name as Boundary-Line writes it, less the word it puts after every ward.
    name: str
    share: float


@dataclass(frozen=True)
class Ground:
    """All that a draft is made on, as plain values, and what was read to make it."""

    cells: tuple[Cell, ...]
    seeds: tuple[Seed, ...]
    roads: Roads
    beside: Mapping[str, Mapping[str, float]]
    # The generalised outline of each output area, on the National Grid.
    outlines: Mapping[str, Shape]
    # The length of each of those outlines, in metres.
    around: Mapping[str, float]
    # The name of each borough by its code, as the lookup writes it.
    boroughs: Mapping[str, str]
    wards: Mapping[str, Ward]
    # The settlement most of the roads of each output area name. None for one with no road.
    settlements: Mapping[str, Settlement]
    # The seeds whose point lies in no output area of London. They are not grown from.
    outside: tuple[str, ...]
    # What was counted on the way, held to no number.
    counted: Mapping[str, int | float]
    # The files that were read, by id.
    inputs: tuple[str, ...] = field(default=())


def taken_out(opened: Opened, ends_with: str) -> Path:
    """The one file inside a zip whose name ends so, taken out beside the zip.

    The copy is kept, and is taken for whole when it is the size the zip gives.
    """
    try:
        with zipfile.ZipFile(opened.path) as archive:
            found = [each for each in archive.infolist() if each.filename.endswith(ends_with)]
            if len(found) != 1:
                raise LockError(
                    "input_is_as_described", opened.file_id, "it does not hold the one file"
                )
            to = opened.path.parent / Path(found[0].filename).name
            if not (to.is_file() and to.stat().st_size == found[0].file_size):
                part = to.with_name(f".part-{to.name}")
                with archive.open(found[0]) as packed, part.open("wb") as unpacked:
                    shutil.copyfileobj(packed, unpacked, PIECE)
                part.replace(to)
            return to
    except (zipfile.BadZipFile, OSError):
        raise LockError("input_is_as_described", opened.file_id, "it is not a zip") from None


def fold(text: str) -> str:
    """A name in lower case, with `&` as a word and every mark as a space, to compare by words."""
    plain = text.casefold().replace("&", " and ").replace("'", "").replace(CURLED, "")
    return " ".join(re.findall(r"[a-z0-9]+", plain))


def holds(label: str, name: str) -> bool:
    """Whether a label holds a name as whole words, in order."""
    wanted = fold(name)
    return bool(wanted) and f" {wanted} " in f" {fold(label)} "


def read_centres(opened: Opened, wanted: frozenset[str]) -> dict[str, Point]:
    """The centre of population of each output area that is wanted, on the National Grid."""
    found: dict[str, Point] = {}
    with opened.text() as text:
        for row in opened.rows(text, (OA, EASTING, NORTHING)):
            if row[OA] not in wanted:
                continue
            try:
                point = float(row[EASTING]), float(row[NORTHING])
            except ValueError:
                point = math.nan, math.nan
            if row[OA] in found or not all(math.isfinite(part) for part in point):
                raise LockError("input_is_as_described", opened.file_id, "a point is no point")
            found[row[OA]] = point
    if frozenset(found) != wanted:
        raise LockError("input_is_as_described", opened.file_id, "an output area has no centre")
    return found


def banks_of(
    outlines: Mapping[str, Shape],
    centres: Mapping[str, Point],
    beside: Mapping[str, Mapping[str, float]],
    water: Shape | None,
) -> dict[str, str]:
    """The bank of each output area: north, south, or none where no file draws the river.

    The output areas wholly east of the western end of the water fall into
    pieces, by the sides they share. The two largest are the banks. An output
    area in neither has no bank.
    """
    found = dict.fromkeys(sorted(outlines), NOT_DRAWN)
    if water is None:
        return found
    west = geometry.west_of(water)
    east_of = {oa for oa in found if geometry.west_of(outlines[oa]) >= west}
    piece_of: dict[str, int] = {}
    pieces: list[list[str]] = []
    for first in sorted(east_of):
        if first in piece_of:
            continue
        piece_of[first] = len(pieces)
        piece, waiting = [first], [first]
        while waiting:
            for other in beside.get(waiting.pop(), {}):
                if other in east_of and other not in piece_of:
                    piece_of[other] = len(pieces)
                    piece.append(other)
                    waiting.append(other)
        pieces.append(sorted(piece))
    largest = sorted(pieces, key=lambda piece: (-len(piece), piece))[:2]
    if len(largest) < 2:
        return found
    northing = [math.fsum(centres[oa][1] for oa in piece) / len(piece) for piece in largest]
    north, south = (largest[0], largest[1]) if northing[0] >= northing[1] else largest[::-1]
    found.update(dict.fromkeys(north, NORTH))
    found.update(dict.fromkeys(south, SOUTH))
    return found


def _snapped(
    points: Mapping[str, Point], banks: Mapping[str, str], nodes: Mapping[str, tuple[Point, str]]
) -> dict[str, tuple[str, float]]:
    """The node nearest each point, among the nodes on a bank the point may be on.

    `nodes` gives each node its point and its bank. A point on a bank is put on
    a node of that bank, or on one that has no bank. A point with no bank is
    put on the nearest node of any.
    """
    found: dict[str, tuple[str, float]] = {}
    for bank in (NORTH, SOUTH, NOT_DRAWN):
        asked = sorted(name for name in points if banks[name] == bank)
        fit = {
            node: point
            for node, (point, side) in nodes.items()
            if bank == NOT_DRAWN or side in (bank, NOT_DRAWN)
        }
        if asked and fit:
            near = geometry.Points(fit).nearest([points[name] for name in asked])
            found.update(zip(asked, near, strict=True))
    return found


@dataclass(frozen=True)
class _Network:
    """The roads once the links over the water are taken up, and where each node is."""

    roads: Roads
    # Each node of the roads: its point, and the bank of the output area it lies in.
    nodes: Mapping[str, tuple[Point, str]]
    # How many nodes are in the piece of the roads each node is in, and which piece.
    piece: Mapping[str, int]
    size: Mapping[int, int]
    counted: Mapping[str, int]


def _network(
    path: Path,
    file_id: str,
    box: geometry.Box,
    water: Shape | None,
    cells: geometry.Outlines,
    banks: Mapping[str, str],
) -> _Network:
    """The links and nodes of the roads in a box, less the links that join the two banks."""
    read = geometry.read_layer(path, file_id, NODES, ("id",), box=box)
    points = {str(name): geometry.at(shape) for (name,), shape in read}
    names = sorted(points)
    inside = cells.holding([points[name] for name in names])
    bank_of = {
        name: banks[oa] if oa is not None else NOT_DRAWN
        for name, oa in zip(names, inside, strict=True)
    }
    links = geometry.read_layer(path, file_id, LINKS, LINK_FIELDS, box=box)
    over: set[int] = set()
    if water is not None:
        over = set(geometry.crossing([shape for _, shape in links], water))
    kept: list[Link] = []
    counted = {"links_read": len(links), "links_over_the_water": len(over)}
    taken_up = beyond = 0
    for number, ((start, end, length), _) in enumerate(links):
        if start not in points or end not in points or not isinstance(length, int | float):
            beyond += 1
            continue
        same_bank = bank_of[str(start)] != NOT_DRAWN and bank_of[str(start)] == bank_of[str(end)]
        if number in over and not same_bank:
            taken_up += 1
            continue
        kept.append(Link(str(start), str(end), float(length)))
    roads = roads_of(kept)
    piece = pieces_of(roads)
    size: dict[int, int] = {}
    for label in piece:
        size[label] = size.get(label, 0) + 1
    counted |= {
        "links_taken_up": taken_up,
        "links_with_an_end_beyond_the_box": beyond,
        "links": len(kept),
        "nodes": len(roads.nodes),
        "pieces_of_the_roads": len(size),
        "nodes_off_the_largest_piece": len(roads.nodes) - max(size.values(), default=0),
    }
    return _Network(
        roads=roads,
        nodes={name: (points[name], bank_of[name]) for name in roads.nodes},
        piece=dict(zip(roads.nodes, piece, strict=True)),
        size=size,
        counted=counted,
    )


def _wards(path: Path, file_id: str, outlines: Mapping[str, Shape]) -> tuple[dict[str, Ward], int]:
    """The ward that holds most of each output area, and how many wards were read."""
    read = geometry.read_layer(
        path, file_id, BOROUGHS_AND_WARDS[1], (CODE, NAME), where=(KIND, A_WARD)
    )
    shapes = {str(code): shape for (code, _), shape in read}
    names = {str(code): str(name).removesuffix(WARD_ENDS) for (code, name), _ in read}
    if len(shapes) != len(read) or not geometry.are_shapes(list(shapes.values())):
        raise LockError("input_is_as_described", file_id, "a ward is there twice, or is no shape")
    held = geometry.held_most_by(outlines, shapes)
    wards = {oa: Ward(code, names[code], share) for oa, (code, share) in held.items()}
    return wards, len({ward.code for ward in wards.values()})


class _Saying:
    """What a ward and a settlement say, each worked out once and kept."""

    def __init__(self, seeds: Sequence[SeedPoint]) -> None:
        self.names = {seed.seed_id: fold(seed.name) for seed in seeds if fold(seed.name)}
        self.records = {seed.seed_id: seed.record for seed in seeds}
        self.of_ward: dict[str, Said] = {}
        self.of_settlement: dict[str, Said] = {}

    def ward(self, ward: Ward) -> Said:
        """A ward's name, and the seeds whose name it holds as whole words."""
        if ward.code not in self.of_ward:
            label = f" {fold(ward.name)} "
            favours = frozenset(seed for seed, name in self.names.items() if f" {name} " in label)
            self.of_ward[ward.code] = Said(WARD, ward.name, favours)
        return self.of_ward[ward.code]

    def settlement(self, settlement: Settlement) -> Said:
        """A settlement's name, and the seeds that were read from its record."""
        if settlement.key not in self.of_settlement:
            favours = assign_settlements.favoured(settlement, self.records)
            self.of_settlement[settlement.key] = Said(ROADS, settlement.name, favours)
        said = self.of_settlement[settlement.key]
        # The roads of two output areas may write one settlement's name in two ways.
        return (
            said
            if said.as_written == settlement.name
            else Said(ROADS, settlement.name, said.favours)
        )

    def of(self, ward: Ward | None, settlement: Settlement | None) -> tuple[Said, ...]:
        """What the roads and the ward of an output area say, the roads first."""
        found: list[Said] = []
        if settlement is not None:
            found.append(self.settlement(settlement))
        if ward is not None:
            found.append(self.ward(ward))
        return tuple(found)


def read_ground(
    inputs: Inputs, seeds: Sequence[SeedPoint], reading: Reading | None = None
) -> Ground:
    """The ground of London and the seeds put on it, from the files of the build.

    It stops when a file is not laid out as it is read, when an output area
    of the lookup has no outline or no centre, and when no seed lies in London.
    """
    reading = reading or Reading()
    if len({seed.seed_id for seed in seeds}) != len(seeds):
        raise ValueError("a seed is there twice")
    rows = read_lookup(inputs.open(LOOKUP, USE, edition=LOOKUP_EDITION))
    borough_of = {row[OA]: row[BOROUGH] for row in rows}
    wanted = frozenset(borough_of)
    centres = read_centres(inputs.open(CENTRES, USE, edition=CENTRES_EDITION), wanted)
    drawn = inputs.open(BOUNDARIES, USE, edition=TO_DRAW)
    outlines = read_outlines(drawn, OA, wanted)
    placed = inputs.open(BOUNDARIES, USE, edition=TO_PLACE)
    full = read_outlines(placed, OA, wanted)
    for opened, held in ((drawn, outlines), (placed, full)):
        if frozenset(held) != wanted:
            raise LockError(
                "input_is_as_described", opened.file_id, "an output area has no outline"
            )
    beside = geometry.shared_metres(outlines)

    lines = inputs.open(BOUNDARY_LINE, USE)
    boundary_line = taken_out(lines, BOUNDARY_LINE_INSIDE)
    boroughs = [
        shape
        for (code,), shape in geometry.read_layer(
            boundary_line, lines.file_id, BOROUGHS_AND_WARDS[0], (CODE,), where=(KIND, A_BOROUGH)
        )
        if code in set(borough_of.values())
    ]
    water = geometry.water_between(boroughs, list(full.values()))
    if water is not None and geometry.ground_of(water) < reading.least_water:
        water = None
    banks = banks_of(outlines, centres, beside, water)
    wards, wards_used = _wards(boundary_line, lines.file_id, outlines)

    settlements = assign_settlements.read(
        inputs.open(assign_settlements.SOURCE, USE),
        geometry.Outlines(full),
        geometry.box_of(list(full.values())),
    )

    ways = inputs.open(OPEN_ROADS, USE)
    network = _network(
        taken_out(ways, ROADS_INSIDE),
        ways.file_id,
        geometry.box_of(list(outlines.values()), reading.margin),
        water,
        geometry.Outlines(outlines),
        banks,
    )

    names = sorted(seed.seed_id for seed in seeds)
    by_id = {seed.seed_id: seed for seed in seeds}
    lies_in = dict(
        zip(
            names,
            geometry.Outlines(full).holding([by_id[name].point for name in names]),
            strict=True,
        )
    )
    inside = {name: oa for name, oa in lies_in.items() if oa is not None}
    if not inside:
        raise ValueError("no seed lies in an output area of London")
    enough = min(reading.least_piece, max(network.size.values(), default=0))
    may_start = {
        node: at
        for node, at in network.nodes.items()
        if network.size[network.piece[node]] >= enough
    }
    seed_at = _snapped(
        {name: by_id[name].point for name in inside},
        {name: banks[oa] for name, oa in inside.items()},
        may_start,
    )
    if len(seed_at) != len(inside):
        raise LockError("input_is_as_described", ways.file_id, "it holds no road to start from")
    reached = {network.piece[node] for node, _ in seed_at.values()}
    cell_at = _snapped(
        centres,
        banks,
        {node: at for node, at in network.nodes.items() if network.piece[node] in reached},
    )
    saying = _Saying(seeds)
    cells = tuple(
        Cell(
            oa=oa,
            borough=borough_of[oa],
            centre=centres[oa],
            bank=banks[oa],
            node=cell_at[oa][0] if oa in cell_at else "",
            to_node=millimetres(cell_at[oa][1]) if oa in cell_at else 0,
            hectares=geometry.ground_of(outlines[oa]),
            said=saying.of(wards.get(oa), settlements.get(oa)),
        )
        for oa in sorted(wanted)
    )
    put = tuple(
        Seed(
            seed_id=name,
            point=by_id[name].point,
            weight=by_id[name].weight,
            oa=inside[name],
            node=seed_at[name][0],
            to_node=millimetres(seed_at[name][1]),
        )
        for name in sorted(seed_at)
    )
    counted: dict[str, int | float] = {
        "output_areas": len(cells),
        "boroughs": len(set(borough_of.values())),
        "seeds_read": len(seeds),
        "seeds_in_london": len(put),
        "water_hectares": round(geometry.ground_of(water), 1) if water is not None else 0.0,
        "on_the_north_bank": sum(cell.bank == NORTH for cell in cells),
        "on_the_south_bank": sum(cell.bank == SOUTH for cell in cells),
        "with_no_bank": sum(cell.bank == NOT_DRAWN for cell in cells),
        "boroughs_on_both_banks": sum(
            {NORTH, SOUTH} <= {cell.bank for cell in cells if cell.borough == borough}
            for borough in set(borough_of.values())
        ),
        "wards": wards_used,
        "output_areas_with_a_ward": len(wards),
        "output_areas_whose_roads_name_a_settlement": len(settlements),
        "output_areas_whose_roads_name_a_seed": sum(
            any(said.kind == ROADS and said.favours for said in cell.said) for cell in cells
        ),
        "output_areas_whose_ward_names_a_seed": sum(
            any(said.kind == WARD and said.favours for said in cell.said) for cell in cells
        ),
        "output_areas_at_no_node": sum(not cell.node for cell in cells),
        **network.counted,
    }
    return Ground(
        cells=cells,
        seeds=put,
        roads=network.roads,
        beside=beside,
        outlines=outlines,
        around={oa: geometry.metres_round(outlines[oa]) for oa in sorted(outlines)},
        boroughs={row[BOROUGH]: row[BOROUGH_NAME] for row in rows},
        wards=wards,
        settlements=settlements,
        outside=tuple(sorted(name for name, oa in lies_in.items() if oa is None)),
        counted=counted,
        inputs=tuple(opened.file_id for opened in inputs.opened),
    )
