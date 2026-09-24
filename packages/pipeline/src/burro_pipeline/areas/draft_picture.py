"""A picture of a draft: the areas drawn and coloured, from their outlines alone.

A person should see a draft before deciding on it. This draws one as an SVG,
which any browser opens. It draws what it is handed and nothing else: the
outlines of the areas, and whatever layers are laid over them. It has no
basemap and asks no other host for anything, so nothing can be copied from a
map (ADR 0004, and section 3.2 of the areas design).

| Drawn | As |
|---|---|
| An area | Filled, in one of twelve colours. Two areas side by side differ |
| A borough | A dark line |
| The tidal water | Filled, in blue |
| A main road | A thin grey line |
| A town centre | A dashed line |
| A seed | A dot |
| A label | The words it is handed, at the point it is handed |

Every shape is a GeoJSON geometry in longitude and latitude. The picture is
flat about its own middle: a degree of longitude is drawn as wide as it is on
the ground at that latitude. The same shapes give the same bytes.

Standard library only.
"""

import math
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from html import escape
from typing import Any, cast

# Twelve fills, light enough for a label to be read over them.
COLOURS = (
    *("#a6cee3", "#fdbf6f", "#b2df8a", "#fb9a99", "#cab2d6", "#ffff99"),
    *("#8dd3c7", "#fccde5", "#d9d9d9", "#bc80bd", "#ccebc5", "#ffed6f"),
)
WATER, ROAD, BOROUGH, CENTRE, SEED, INK = (
    "#6baed6",
    "#737373",
    "#252525",
    "#d94801",
    "#000000",
    "#111111",
)
AREA, LINE, WATER_FILL, ROADS, CENTRES, DOTS = "area", "line", "water", "roads", "centres", "dots"
Geometry = Mapping[str, Any]
Point = tuple[float, float]


@dataclass(frozen=True)
class Shape:
    """One thing to draw: what it is drawn as, its geometry, and the colour of an area."""

    drawn_as: str
    geometry: Geometry
    colour: int = 0
    # What the shape is, for whoever reads the file. It is never drawn.
    name: str = ""


@dataclass(frozen=True)
class Label:
    words: str
    at: Point


@dataclass(frozen=True)
class Picture:
    """Everything one picture is drawn from, in the order it is drawn."""

    title: str
    shapes: Sequence[Shape]
    labels: Sequence[Label] = field(default=())
    # What the picture is fitted to. Without it, to every shape.
    fit_to: Sequence[Geometry] = field(default=())
    width: int = 1600


def lines_of(geometry: Geometry) -> Iterator[tuple[list[Point], bool]]:
    """Every line of a geometry as its points, and whether the line is a closed ring."""
    kind, held = geometry["type"], geometry["coordinates"]
    if kind == "Point":
        yield [(float(held[0]), float(held[1]))], False
    elif kind == "LineString":
        yield [(float(x), float(y)) for x, y, *_ in held], False
    elif kind == "MultiLineString":
        for line in held:
            yield [(float(x), float(y)) for x, y, *_ in line], False
    elif kind == "Polygon":
        for ring in held:
            yield [(float(x), float(y)) for x, y, *_ in ring], True
    elif kind == "MultiPolygon":
        for polygon in held:
            for ring in polygon:
                yield [(float(x), float(y)) for x, y, *_ in ring], True
    else:
        raise ValueError("a geometry of a kind that is not drawn")


def box_of(geometries: Sequence[Geometry]) -> tuple[float, float, float, float]:
    """West, south, east and north of some geometries."""
    points = [point for each in geometries for line, _ in lines_of(each) for point in line]
    if not points:
        raise ValueError("there is nothing to draw")
    return (
        min(x for x, _ in points),
        min(y for _, y in points),
        max(x for x, _ in points),
        max(y for _, y in points),
    )


class _Flat:
    """From longitude and latitude to the picture, flat about the middle of what is drawn."""

    def __init__(self, box: tuple[float, float, float, float], width: int, margin: float) -> None:
        west, south, east, north = box
        self.west, self.north = west, north
        self.squeeze = math.cos(math.radians((south + north) / 2))
        wide = max((east - west) * self.squeeze, 1e-9)
        high = max(north - south, 1e-9)
        self.margin = margin
        self.scale = (width - 2 * margin) / wide
        self.width = width
        self.height = math.ceil(high * self.scale + 2 * margin)

    def __call__(self, point: Point) -> str:
        x = (point[0] - self.west) * self.squeeze * self.scale + self.margin
        y = (self.north - point[1]) * self.scale + self.margin
        return f"{x:.1f},{y:.1f}"


def _path(geometry: Geometry, flat: _Flat) -> str:
    parts: list[str] = []
    for line, closed in lines_of(geometry):
        if len(line) > 1:
            parts.append("M" + "L".join(flat(point) for point in line) + ("Z" if closed else ""))
    return "".join(parts)


STYLE: Mapping[str, str] = {
    AREA: 'stroke="#4d4d4d" stroke-width="0.6" fill-rule="evenodd"',
    WATER_FILL: f'fill="{WATER}" stroke="none" fill-rule="evenodd"',
    ROADS: f'fill="none" stroke="{ROAD}" stroke-width="0.6" stroke-opacity="0.7"',
    CENTRES: f'fill="none" stroke="{CENTRE}" stroke-width="1" stroke-dasharray="3 2"',
    LINE: f'fill="none" stroke="{BOROUGH}" stroke-width="2.2"',
}


def svg(picture: Picture) -> str:
    """The picture as an SVG document."""
    fitted = list(picture.fit_to) or [shape.geometry for shape in picture.shapes]
    flat = _Flat(box_of(fitted), picture.width, margin=24.0)
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{flat.width}" height="{flat.height}" '
        f'viewBox="0 0 {flat.width} {flat.height}" font-family="sans-serif">',
        f"<title>{escape(picture.title)}</title>",
        f'<rect width="{flat.width}" height="{flat.height}" fill="#ffffff"/>',
    ]
    for shape in picture.shapes:
        named = f"<title>{escape(shape.name)}</title>" if shape.name else ""
        if shape.drawn_as == DOTS:
            for line, _ in lines_of(shape.geometry):
                x, y = flat(line[0]).split(",")
                out.append(f'<circle cx="{x}" cy="{y}" r="2.2" fill="{SEED}">{named}</circle>')
            continue
        drawn = _path(shape.geometry, flat)
        if not drawn:
            continue
        fill = f'fill="{COLOURS[shape.colour % len(COLOURS)]}" ' if shape.drawn_as == AREA else ""
        out.append(f'<path {fill}{STYLE[shape.drawn_as]} d="{drawn}">{named}</path>')
    for label in picture.labels:
        x, y = flat(label.at).split(",")
        out.append(
            f'<text x="{x}" y="{y}" font-size="11" text-anchor="middle" fill="{INK}" '
            f'stroke="#ffffff" stroke-width="2.5" paint-order="stroke">{escape(label.words)}</text>'
        )
    out.append(
        f'<text x="24" y="16" font-size="12" fill="{INK}">{escape(picture.title)}</text></svg>'
    )
    return "\n".join(out) + "\n"


def features_of(collection: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """The features of a GeoJSON document that have a geometry."""
    found = collection.get("features", [])
    if not isinstance(found, list):
        raise ValueError("not a collection of features")
    return [
        cast(Mapping[str, Any], each)
        for each in cast(list[Any], found)
        if isinstance(each, dict) and cast(dict[str, Any], each).get("geometry")
    ]
