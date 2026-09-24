"""The geometry behind a flag and behind a layer: what is near, what overlaps, what is drawn.

`cells/shapes.py` joins and measures outlines, and `assign_shapes.py` reads a
named layer of a file and says which outline holds most of another. A flag and
a layer need a little more: how much of one shape lies over each of many, how
much of a straight side runs beside a line, the part of a shape that lies in
an outline, an outline drawn with fewer points, and a line or a point as a map
draws it. They are here while the parts of the areas are built side by side,
and belong in `cells/shapes.py` once those parts are joined. Like that module,
this one tells the type checker not to ask what the geometry library returns.

Every coordinate is on the National Grid, in metres, until it is written for a
map. It is turned to longitude and latitude by the one fixed operation of
`cells/shapes.py`, and by nothing else.

Nothing here reads a name. It is handed shapes, and gives back shapes and numbers.
"""
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false, reportUnknownParameterType=false
# pyright: reportMissingTypeStubs=false, reportAttributeAccessIssue=false

import math
from collections.abc import Mapping, Sequence

import shapely

from burro_pipeline.cells.shapes import Point, Shape, as_geojson, longitude_and_latitude

# A straight side of an outline: its two ends.
Straight = tuple[Point, Point]

POLYGONS = ("Polygon", "MultiPolygon")
LINES = ("LineString", "MultiLineString")


# Measuring


def grown(shape: Shape, metres: float) -> Shape:
    """A shape, and the ground within so many metres of it."""
    return shapely.buffer(shape, metres, quad_segs=4)


def within_reach(shapes: Sequence[Shape], of: Shape) -> list[int]:
    """Which of some shapes meet another shape: the place of each in the list, in order."""
    if not shapes:
        return []
    found = shapely.STRtree(list(shapes)).query(of, predicate="intersects")
    return sorted(int(index) for index in found.tolist())


def cut_to(shape: Shape, to: Shape) -> Shape | None:
    """The part of a line or of an outline that lies in an outline. Nothing where none does.

    What is left of a line is lines, and of an outline outlines: where a line
    only touches the edge, the point it touches at is not kept.
    """
    kinds = LINES if shape.geom_type in LINES else POLYGONS
    part = shapely.intersection(shape, to)
    if part.is_empty:
        return None
    if part.geom_type in kinds:
        return part
    kept = [each for each in getattr(part, "geoms", ()) if each.geom_type in kinds]
    return shapely.union_all(kept) if kept else None


def overlaps(
    shapes: Mapping[str, Shape], ground: Mapping[str, Shape]
) -> list[tuple[str, str, float]]:
    """Each shape with each outline of the ground it lies over, and the share of it that does."""
    names, codes = sorted(shapes), sorted(ground)
    if not names or not codes:
        return []
    asked = [shapes[name] for name in names]
    held = [ground[code] for code in codes]
    tree = shapely.STRtree(held)
    pairs = tree.query(asked, predicate="intersects")
    if pairs.shape[1] == 0:
        return []
    mine = [asked[int(at)] for at in pairs[0].tolist()]
    theirs = [held[int(over)] for over in pairs[1].tolist()]
    common = shapely.area(shapely.intersection(mine, theirs)).tolist()
    whole = shapely.area(mine).tolist()
    found = [
        (names[int(at)], codes[int(over)], float(part) / float(all_of_it))
        for at, over, part, all_of_it in zip(
            pairs[0].tolist(), pairs[1].tolist(), common, whole, strict=True
        )
        if all_of_it > 0 and part > 0
    ]
    return sorted(found)


def metres_in(lines: Sequence[Shape], ground: Mapping[str, Shape]) -> dict[str, dict[int, float]]:
    """For each outline of the ground, the lines that run in it and for how many metres.

    A line is known by its place in the list. One that only touches the edge
    of an outline runs for no length in it, and is left out.
    """
    found: dict[str, dict[int, float]] = {code: {} for code in sorted(ground)}
    if not lines or not ground:
        return found
    held = list(lines)
    tree = shapely.STRtree(held)
    for code in sorted(ground):
        near = sorted(int(at) for at in tree.query(ground[code], predicate="intersects").tolist())
        if not near:
            continue
        inside = shapely.length(
            shapely.intersection([held[at] for at in near], ground[code])
        ).tolist()
        found[code] = {at: float(metres) for at, metres in zip(near, inside, strict=True) if metres}
    return found


def metres_beside(
    sides: Sequence[Straight], lines: Sequence[Shape], within: float, step: float
) -> list[float]:
    """For each straight side, how many of its metres run within so far of any of the lines.

    A side is walked in steps, and each step counts if its middle is within
    the distance of a line. So a side that crosses a road counts for the step
    that crosses it, and a side that runs along one counts whole.
    """
    if not sides:
        return []
    if not lines:
        return [0.0] * len(sides)
    tree = shapely.STRtree(list(lines))
    xs: list[float] = []
    ys: list[float] = []
    owner: list[int] = []
    weigh: list[float] = []
    for at, ((ax, ay), (bx, by)) in enumerate(sides):
        length = math.hypot(bx - ax, by - ay)
        steps = max(1, math.ceil(length / step))
        for number in range(steps):
            along = (number + 0.5) / steps
            xs.append(ax + (bx - ax) * along)
            ys.append(ay + (by - ay) * along)
            owner.append(at)
            weigh.append(length / steps)
    middles = shapely.points(xs, ys)
    near = tree.query(middles, predicate="dwithin", distance=within)
    counted = [0.0] * len(sides)
    for index in sorted(set(near[0].tolist())):
        counted[owner[int(index)]] += weigh[int(index)]
    return counted


# Making a shape fit for a page


def fewer_points(shapes: Sequence[Shape], metres: float) -> list[Shape]:
    """Outlines that tile, each drawn with fewer points, and still sharing their sides.

    A corner is left out where the triangle it makes with the corners each
    side of it is smaller than a square of the distance given, so a line moves
    by about that distance at most. A side that two outlines share is thinned
    once, for both, so no gap opens between them. Outlines that lie over each
    other do not tile, and are thinned one by one.
    """
    held = list(shapes)
    if not held:
        return []
    if bool(shapely.coverage_is_valid(held)):
        thinned = shapely.coverage_simplify(held, metres)
    else:
        thinned = shapely.simplify(held, metres, preserve_topology=True)
    return [shapely.make_valid(each) if not shapely.is_valid(each) else each for each in thinned]


def fewer_points_of_a_line(shape: Shape, metres: float) -> Shape:
    return shapely.simplify(shape, metres, preserve_topology=True)


def joined_lines(lines: Sequence[Shape]) -> Shape:
    """Lines that meet end to end as one line, or as few as they can be."""
    return shapely.line_merge(shapely.union_all(list(lines)))


def polygons_of(shape: Shape) -> Shape | None:
    """What of a shape is ground: its polygons, as one outline. Nothing where it has none."""
    if shape.geom_type in POLYGONS:
        return shape
    parts = [each for each in getattr(shape, "geoms", ()) if each.geom_type in POLYGONS]
    if not parts:
        return None
    return shapely.union_all(parts)


# Writing a shape for a map


def _line(line: Shape) -> list[list[float]]:
    return [list(longitude_and_latitude(x, y)) for x, y in shapely.get_coordinates(line).tolist()]


def drawn(shape: Shape) -> dict[str, object]:
    """A shape as a GeoJSON geometry, in longitude and latitude, to six decimal places.

    An outline is written by `cells/shapes.py`. A line is put in the library's
    fixed form first, so that the same line is always the same bytes.
    """
    if shape.geom_type in POLYGONS:
        return as_geojson(shape)
    if shape.geom_type == "Point":
        return {"type": "Point", "coordinates": list(longitude_and_latitude(shape.x, shape.y))}
    fixed = shapely.normalize(shape)
    if fixed.geom_type == "LineString":
        return {"type": "LineString", "coordinates": _line(fixed)}
    if fixed.geom_type == "MultiLineString":
        return {"type": "MultiLineString", "coordinates": [_line(each) for each in fixed.geoms]}
    raise ValueError("a shape a map draws is an outline, a line or a point")


# Making a shape from points


def point(at: Point) -> Shape:
    return shapely.Point(at)


def line(points: Sequence[Point]) -> Shape:
    return shapely.LineString(list(points))


def outline(points: Sequence[Point]) -> Shape:
    """The outline that runs through some points and back to the first."""
    return shapely.Polygon(list(points))
