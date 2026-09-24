"""What is drawn behind a border for a reviewer, and what may not be.

A reviewer who moves a border to match a line on a map has taken that line
from the map. The registered basemap is made from OpenStreetMap, which may
only be displayed (ADR 0004). So the review desk shows no basemap and no tile.
It draws layers made here, each from a source the licence registry gives the
use `gazetteer`: sections 3.2, 9 and 13 of the areas design, and section 6 of
the desk's. The gate is asked about every source of every layer before the
layer is made, and a layer it refuses is not made from anything else.

| Layer | Drawn as | From | The desk |
|---|---|---|---|
| `boroughs` | Outlines, in the group `all` | Output areas joined by borough | Draws it |
| `wards` | Thin outlines | Boundary-Line | Draws it |
| `centres` | Hatched outlines | The town centre boundaries | Draws it |
| `roads` | Lines by class | OS Open Roads: main and minor roads | Draws it |
| `names` | Names as text | OS Open Names: places, stations, water, woods | Draws it |
| `water` | The tidal river, filled | Boundary-Line, less the output areas | Has no such layer yet |

Three more layers are the draft itself, and are made once there is one:

| Layer | Drawn as | From |
|---|---|---|
| `cells` | Filled, in the colour of its area | The output areas, and the draft's area for each |
| `areas` | Outlines, as drafted | The output areas of each area joined |
| `seeds` | Points | Where the draft puts each area's seed |

What the design wants and the gate refuses is in `WANTED`, each with what the
desk can show in its place and what the founder decides.

A layer is a GeoJSON FeatureCollection in longitude and latitude, to six
decimal places, with a member `desk` that names the layer, its group and its
sources. A feature holds the properties the desk's design gives its layer and
no other, so nothing about who lives anywhere can ride in on a layer. A name
is written exactly as its publisher writes it.

A borough's group holds what lies within 500 m of the borough. An outline is
thinned to be small enough for a page: no point moves by more than a few
metres, and outlines that share a side still share it.

This module is handed shapes and names, and reads no file.
"""

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from burro_pipeline.areas import assign_shapes, context_shapes
from burro_pipeline.cells import shapes
from burro_pipeline.cells.shapes import Shape
from burro_pipeline.registry import Registry, RegistryError
from burro_pipeline.registry.model import Use

USE = Use.GAZETTEER
ALL = "all"
# How far beyond a borough its layers reach, in metres (desk design, section 6).
MARGIN = 500.0

OUTLINES = "ons-output-areas-2021"
LOOKUP = "ons-oa21-lsoa21-msoa21-lad22-lookup"
BOUNDARY_LINE = "os-boundary-line"
TOWN_CENTRES = "gla-town-centre-boundaries"
OPEN_ROADS = "os-open-roads"
OPEN_NAMES = "os-open-names"
GREENSPACE, RIVERS, STATIONS = "os-open-greenspace", "os-open-rivers", "dft-naptan"

# How many colours the desk fills cells with.
COLOURS = 12

type Feature = dict[str, object]
type Collection = dict[str, object]


@dataclass(frozen=True)
class Layer:
    """One layer that may be drawn, if the gate gives every source of it."""

    name: str
    sources: tuple[str, ...]
    # The properties a feature of it may hold, as the desk's design gives them.
    properties: tuple[str, ...]
    # Whether the desk has a layer of this name. One it has none for is kept apart.
    desk_draws_it: bool = True
    # How far a point of it may be moved to make it smaller, in metres. None moves none.
    thinned_by: float | None = None
    # Whether a thing of it is cut to the ground of each borough. A road and a river run
    # through many boroughs, and are not drawn whole for each.
    cut: bool = False


LAYERS: tuple[Layer, ...] = (
    Layer("boroughs", (OUTLINES, LOOKUP), ("name",)),
    Layer("wards", (BOUNDARY_LINE,), ("name",), thinned_by=5.0),
    Layer("centres", (TOWN_CENTRES,), ("name", "class"), thinned_by=2.0),
    Layer("roads", (OPEN_ROADS,), ("class", "name"), thinned_by=5.0, cut=True),
    Layer("names", (OPEN_NAMES,), ("name", "kind")),
    Layer("cells", (OUTLINES, LOOKUP), ("area", "colour", "borough")),
    Layer("areas", (OUTLINES, LOOKUP), ("name",)),
    Layer("seeds", (OPEN_NAMES, TOWN_CENTRES), ("area", "name")),
    Layer(
        "water",
        (BOUNDARY_LINE, OUTLINES),
        ("name",),
        desk_draws_it=False,
        thinned_by=5.0,
        cut=True,
    ),
)


@dataclass(frozen=True)
class Wanted:
    """One thing a reviewer finds their way by, from a source the design names for it."""

    what: str
    source: str
    # What the desk can show in its place, from a source the gate gives.
    in_its_place: str
    # What the founder, or the registry's owner, must decide.
    to_decide: str


WANTED: tuple[Wanted, ...] = (
    Wanted(
        "parks",
        GREENSPACE,
        "The layer `names`: the woods and green spaces OS Open Names holds, each a name at a "
        "point. No outline of a park is drawn.",
        "Whether os-open-greenspace is given the use gazetteer, as section 13 of the areas "
        "design asks. A border moved to the edge of a park is then a border taken from that "
        "file, which is under the Open Government Licence.",
    ),
    Wanted(
        "rivers",
        RIVERS,
        "The tidal river needs no layer: no output area covers it, so it shows as ground with "
        "no cell. The layer `water` fills it, once the desk draws such a layer. Named water "
        "is in the layer `names`, each a name at a point. Above the tide no river is drawn.",
        "Whether os-open-rivers is given the use gazetteer, as section 13 of the areas design "
        "asks. Until then a reviewer cannot see the river west of the tidal limit.",
    ),
    Wanted(
        "stations",
        STATIONS,
        "The layer `names`: the railway stations OS Open Names holds, each a name at a point.",
        "Whether dft-naptan is given the use gazetteer, and who saves London's file by hand.",
    ),
)


@dataclass(frozen=True)
class Answer:
    """What the gate said of one source, for the use a layer needs."""

    source: str
    given: bool
    # The gate's own words where it refused.
    words: str = ""


def ask(registry: Registry, sources: Sequence[str]) -> dict[str, Answer]:
    """Ask the gate about every source, for `gazetteer`. Every one is asked, refused or not."""
    found: dict[str, Answer] = {}
    for source in sorted(set(sources)):
        try:
            registry.require(source, USE)
        except RegistryError as error:
            found[source] = Answer(source, False, str(error))
        else:
            found[source] = Answer(source, True)
    return found


def may_be_made(layer: Layer, answers: Mapping[str, Answer]) -> bool:
    """Whether the gate gave every source of a layer. A source it was not asked of is refused."""
    return all(source in answers and answers[source].given for source in layer.sources)


def layer_named(name: str) -> Layer:
    return next(layer for layer in LAYERS if layer.name == name)


def group_of(borough: str) -> str:
    """The name of a borough's group: its name in lower case with hyphens, as the desk makes it."""
    return re.sub(r"[^a-z0-9]+", "-", borough.casefold()).strip("-")


def canonical(document: object) -> str:
    """The one way a layer is written, which is the desk's: the same data, the same bytes."""
    return json.dumps(
        document, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )


@dataclass(frozen=True)
class Drawn:
    """One thing to draw: its id, what is said of it, and its shape on the National Grid."""

    record_id: str
    # Every property is text, but the colour of a cell, which is a whole number.
    properties: Mapping[str, str | int]
    shape: Shape


def feature(layer: Layer, drawn: Drawn) -> Feature:
    """A feature as the desk reads it. It stops at a property the layer may not hold."""
    if not drawn.record_id or not set(drawn.properties) <= set(layer.properties):
        raise ValueError("a feature has an id, and the properties of its layer and no other")
    return {
        "type": "Feature",
        "id": drawn.record_id,
        "properties": dict(sorted(drawn.properties.items())),
        "geometry": context_shapes.drawn(drawn.shape),
    }


def collection(
    layer: Layer, group: str, things: Sequence[Drawn], *, synthetic: bool = False
) -> Collection:
    """A layer of one group, its features in the order of their ids. An id is there once."""
    if len({each.record_id for each in things}) != len(things):
        raise ValueError("an id is held twice in one layer")
    return {
        "type": "FeatureCollection",
        "desk": {
            "layer": layer.name,
            "group": group,
            "source_ids": sorted(layer.sources),
            "synthetic": synthetic,
        },
        "features": [
            feature(layer, each) for each in sorted(things, key=lambda each: each.record_id)
        ],
    }


# The draft itself


def colours_of(beside: Mapping[str, Sequence[str]]) -> dict[str, int]:
    """A colour for each area, from 0 to 11, that no area beside it has where that can be.

    Areas are taken in the order of their ids, and each is given the first
    colour that no area beside it has yet. Where every colour is taken, it is
    given the one that fewest beside it have.
    """
    given: dict[str, int] = {}
    for area_id in sorted(beside):
        taken = [given[other] for other in beside[area_id] if other in given]
        free = [colour for colour in range(COLOURS) if colour not in taken]
        given[area_id] = (
            free[0]
            if free
            else min(range(COLOURS), key=lambda colour: (taken.count(colour), colour))
        )
    return given


def cells_drawn(
    outlines: Mapping[str, Shape],
    area_of: Mapping[str, str],
    borough_of: Mapping[str, str],
    colours: Mapping[str, int],
) -> list[Drawn]:
    """Every output area of the draft, with its area, its area's colour and its borough's name."""
    return [
        Drawn(
            oa,
            {"area": area_of[oa], "colour": colours[area_of[oa]], "borough": borough_of[oa]},
            outlines[oa],
        )
        for oa in sorted(area_of)
    ]


def areas_drawn(
    outlines: Mapping[str, Shape], area_of: Mapping[str, str], names: Mapping[str, str]
) -> list[Drawn]:
    """Every area of the draft as its output areas joined, so that its line is its cells' line."""
    parts: dict[str, list[Shape]] = {}
    for oa in sorted(area_of):
        parts.setdefault(area_of[oa], []).append(outlines[oa])
    return [
        Drawn(area_id, {"name": names[area_id]}, shapes.joined(cells))
        for area_id, cells in sorted(parts.items())
    ]


# The shapes of each layer


def borough_outlines(
    outlines: Mapping[str, Shape], borough_of: Mapping[str, str]
) -> dict[str, Shape]:
    """Each borough as its output areas joined, by the borough's code.

    So a borough's line is the line of its outermost cells, to the point, and
    the tidal river is in no borough.
    """
    parts: dict[str, list[Shape]] = {}
    for oa in sorted(outlines):
        parts.setdefault(borough_of[oa], []).append(outlines[oa])
    return {code: shapes.joined(cells) for code, cells in sorted(parts.items())}


def thinned(layer: Layer, things: Sequence[Drawn]) -> list[Drawn]:
    """The same things, each drawn with fewer points where its layer allows."""
    if layer.thinned_by is None or not things:
        return list(things)
    held = [each.shape for each in things]
    if all(shape.geom_type in context_shapes.POLYGONS for shape in held):
        fewer = context_shapes.fewer_points(held, layer.thinned_by)
        kept = [context_shapes.polygons_of(shape) for shape in fewer]
    else:
        kept = [context_shapes.fewer_points_of_a_line(shape, layer.thinned_by) for shape in held]
    return [
        Drawn(each.record_id, each.properties, shape)
        for each, shape in zip(things, kept, strict=True)
        if shape is not None and not shape.is_empty
    ]


def by_borough(
    layer: Layer, things: Sequence[Drawn], boroughs: Mapping[str, Shape], names: Mapping[str, str]
) -> dict[str, list[Drawn]]:
    """What of a layer is drawn for each borough: what lies within 500 m of it.

    A road or a river is cut to that ground, so that it is not drawn whole for
    every borough it passes. A ward or a centre at the edge is drawn whole.
    """
    held = [each.shape for each in things]
    found: dict[str, list[Drawn]] = {}
    for code in sorted(boroughs):
        ground = context_shapes.grown(boroughs[code], MARGIN)
        near: list[Drawn] = []
        for index in context_shapes.within_reach(held, ground):
            each = things[index]
            part = context_shapes.cut_to(each.shape, ground) if layer.cut else each.shape
            if part is not None:
                near.append(Drawn(each.record_id, each.properties, part))
        found[group_of(names[code])] = near
    return found


def tidal_water(boroughs_to_the_river: Sequence[Shape], land: Sequence[Shape]) -> Shape | None:
    """The tidal river: the boroughs as drawn to its middle, less the land.

    Boundary-Line draws a borough to the middle of tidal water, and an output
    area stops at the mean high water mark. What lies between is water. Only
    the largest piece is: every other is a sliver where two publishers draw
    one line a little apart. It is worked out as the draft of areas works it
    out, so the water a reviewer sees is the water the draft kept to.
    """
    return assign_shapes.water_between(boroughs_to_the_river, land)


# The boroughs, for the desk to ask a reviewer about


@dataclass(frozen=True, order=True)
class Borough:
    """One borough, as the desk asks how well a reviewer knows it."""

    # The name, as the lookup writes it.
    name: str
    code: str
    # The item of the desk's queue, and the group of the borough's layers.
    group: str
    output_areas: int
    hectares: float


def boroughs_to_ask(
    outlines: Mapping[str, Shape], borough_of: Mapping[str, str], names: Mapping[str, str]
) -> list[Borough]:
    """Every borough the files hold, by name. It stops where two would share a group."""
    cells: dict[str, list[str]] = {}
    for oa in sorted(borough_of):
        cells.setdefault(borough_of[oa], []).append(oa)
    found = sorted(
        Borough(
            name=names[code],
            code=code,
            group=group_of(names[code]),
            output_areas=len(oas),
            hectares=round(sum(shapes.hectares(outlines[oa]) for oa in oas), 1),
        )
        for code, oas in cells.items()
    )
    if len({borough.group for borough in found}) != len(found) or any(
        not borough.group or borough.group == ALL for borough in found
    ):
        raise ValueError("two boroughs would share a group, or one would have none")
    return found
