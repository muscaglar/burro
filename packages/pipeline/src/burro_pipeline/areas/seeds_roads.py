"""How far one seed is from another along the roads, from OS Open Roads.

The design measures how close two seeds lie in metres along the roads, and
never in a straight line: a railway or a river between two places is felt on
the ground, and a road crosses one only where there is a bridge. Never
OpenStreetMap (ADR 0004).

The file is a zip that holds one GeoPackage. Two layers are read: the links,
each with the nodes it runs between and its length in metres, and the nodes,
each a point. Only the links whose box meets the ground that is asked about
are read, by the layer's own index.

The roads are in several pieces, and nearly every node is in the largest. A
point is put on the nearest node of the largest piece, so that a search from it
can reach the rest. The way from a point to another is the way between their
nodes, and the straight line from each point to its node. Two points that are
put on the same node are as far apart as the straight line between them.

It holds roads for vehicles. It holds no footpath and no footbridge, so a way
on foot may be shorter than the way found here.
"""

import heapq
import math
import sqlite3
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from burro_pipeline.areas import names_shapes
from burro_pipeline.areas.names_files import File, taken_out
from burro_pipeline.cells.shapes import Point
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.fetch.kinds import read_only

SOURCE = "os-open-roads"
MEMBER = "oproad_gb.gpkg"
# How far beyond the ground the roads are read, so that a way may leave it and come back.
MARGIN = 2_000.0
# The side of a square of the grid that nodes are looked for in.
SQUARE = 250.0
LINKS = (
    "SELECT l.start_node, l.end_node, l.length FROM road_link AS l "
    "JOIN rtree_road_link_geometry AS r ON r.id = l.fid "
    "WHERE r.maxx >= ? AND r.minx <= ? AND r.maxy >= ? AND r.miny <= ?"
)
NODES = (
    "SELECT n.id, n.geometry FROM road_node AS n "
    "JOIN rtree_road_node_geometry AS r ON r.id = n.fid "
    "WHERE r.maxx >= ? AND r.minx <= ? AND r.maxy >= ? AND r.miny <= ?"
)

Box = tuple[float, float, float, float]


@dataclass(frozen=True)
class Link:
    """One stretch of road between two nodes, and its length in metres."""

    start: str
    end: str
    metres: float


def _straight(a: Point, b: Point) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _root(parent: list[int], node: int) -> int:
    while parent[node] != node:
        parent[node] = parent[parent[node]]
        node = parent[node]
    return node


class Roads:
    """The roads of a ground, as nodes and the ways between them."""

    def __init__(self, nodes: Mapping[str, Point], links: Sequence[Link]) -> None:
        ids = sorted(nodes)
        number = {node: index for index, node in enumerate(ids)}
        self._at: list[Point] = [nodes[node] for node in ids]
        self._beside: list[list[tuple[int, float]]] = [[] for _ in ids]
        parent = list(range(len(ids)))
        for link in sorted(links, key=lambda each: (each.start, each.end, each.metres)):
            if link.start not in number or link.end not in number:
                continue
            a, b = number[link.start], number[link.end]
            self._beside[a].append((b, link.metres))
            self._beside[b].append((a, link.metres))
            parent[_root(parent, a)] = _root(parent, b)
        sizes: dict[int, int] = {}
        for node in range(len(ids)):
            root = _root(parent, node)
            sizes[root] = sizes.get(root, 0) + 1
        self.pieces = len(sizes)
        largest = max(sorted(sizes), key=lambda root: sizes[root]) if sizes else -1
        self._main = [_root(parent, node) == largest for node in range(len(ids))]
        self.nodes = len(ids)
        self.links = sum(len(beside) for beside in self._beside) // 2
        self._squares: dict[tuple[int, int], list[int]] = {}
        for node, (x, y) in enumerate(self._at):
            if self._main[node]:
                self._squares.setdefault(self._square(x, y), []).append(node)

    @staticmethod
    def _square(x: float, y: float) -> tuple[int, int]:
        return math.floor(x / SQUARE), math.floor(y / SQUARE)

    def nearest(self, at: Point) -> tuple[int, float] | None:
        """The nearest node of the largest piece to a point, and how far off it is."""
        if not self._squares:
            return None
        column, row = self._square(*at)
        best: tuple[float, int] | None = None
        ring = 0
        # A node in a ring of squares is at least as far off as the ring before it is wide.
        while best is None or best[0] > (ring - 1) * SQUARE:
            for across in range(column - ring, column + ring + 1):
                for up in range(row - ring, row + ring + 1):
                    if max(abs(across - column), abs(up - row)) != ring:
                        continue
                    for node in self._squares.get((across, up), ()):
                        x, y = self._at[node]
                        found = (math.hypot(x - at[0], y - at[1]), node)
                        if best is None or found < best:
                            best = found
            ring += 1
            if ring > 4_000:
                return None
        return best[1], best[0]

    def _search(
        self, starts: Mapping[int, tuple[float, str]], most: float
    ) -> dict[int, tuple[float, str]]:
        """The shortest way to each node from the nearest of several starts, within a length."""
        found: dict[int, tuple[float, str]] = {}
        heap = [(metres, name, node) for node, (metres, name) in sorted(starts.items())]
        heapq.heapify(heap)
        while heap:
            metres, name, node = heapq.heappop(heap)
            if node in found or metres > most:
                continue
            found[node] = (metres, name)
            for other, length in self._beside[node]:
                if other not in found and metres + length <= most:
                    heapq.heappush(heap, (metres + length, name, other))
        return found

    def within(self, at: Point, points: Mapping[str, Point], most: float) -> dict[str, float]:
        """How far each of some named points is from a point along the roads, if within a length.

        A point that lies further off, or that the roads do not reach, is left out.
        """
        start = self.nearest(at)
        if start is None:
            return {}
        reached = self._search({start[0]: (start[1], "")}, most)
        found: dict[str, float] = {}
        for name in sorted(points):
            end = self.nearest(points[name])
            if end is None:
                continue
            if end[0] == start[0]:
                metres = _straight(at, points[name])
            elif end[0] in reached:
                metres = reached[end[0]][0] + end[1]
            else:
                continue
            if metres <= most:
                found[name] = metres
        return found

    def nearest_of(
        self, starts: Mapping[str, Point], points: Mapping[str, Point]
    ) -> dict[str, tuple[str, float]]:
        """For each of some named points, the nearest start along the roads and how far it is.

        One search is made, from every start at once. Of two starts as near, the
        one whose name sorts first is taken. A point the roads do not reach is
        left out.
        """
        began: dict[int, tuple[float, str]] = {}
        on: dict[int, list[str]] = {}
        for name in sorted(starts):
            node = self.nearest(starts[name])
            if node is None:
                continue
            on.setdefault(node[0], []).append(name)
            if node[0] not in began or (node[1], name) < began[node[0]]:
                began[node[0]] = (node[1], name)
        reached = self._search(began, math.inf)
        found: dict[str, tuple[str, float]] = {}
        for name in sorted(points):
            end = self.nearest(points[name])
            if end is None or end[0] not in reached:
                continue
            if end[0] in on:
                metres, start = min(
                    (_straight(starts[each], points[name]), each) for each in on[end[0]]
                )
                found[name] = (start, metres)
            else:
                metres, start = reached[end[0]]
                found[name] = (start, metres + end[1])
        return found


def read(file: File, ground: Box) -> Roads:
    """The roads whose box meets a ground, and a margin round it."""
    path = taken_out(file, MEMBER)
    west, south, east, north = ground
    box = (west - MARGIN, east + MARGIN, south - MARGIN, north + MARGIN)
    try:
        database = read_only(path)
        try:
            links = [
                Link(str(start), str(end), float(metres))
                for start, end, metres in database.execute(LINKS, box)
            ]
            wanted = {link.start for link in links} | {link.end for link in links}
            nodes = {
                str(node): names_shapes.at(names_shapes.geometry_of(bytes(blob)))
                for node, blob in database.execute(NODES, box)
                if str(node) in wanted
            }
        finally:
            database.close()
    except (sqlite3.Error, ValueError, TypeError, AttributeError):
        raise LockError(
            "input_is_as_described", file.file_id, "the roads could not be read"
        ) from None
    if not links or not nodes or any(link.metres < 0 for link in links):
        raise LockError("input_is_as_described", file.file_id, "it holds no road of the ground")
    return Roads(nodes, links)
