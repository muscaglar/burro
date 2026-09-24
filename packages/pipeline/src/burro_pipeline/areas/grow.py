"""How far along the roads a place is from the seeds nearest to it.

An area is grown from a seed: a point that a publisher's file gives for a name.
Near is measured along the roads, never in a straight line, because a railway
or a reservoir that parts two streets is crossed only where a road crosses it
(areas design, section 4). The roads are those of one publisher's file, as
links between nodes, each with its length.

One search is run from every seed at once. It gives each node of the roads the
few seeds nearest to it, with the distance to each. A few and not one, because
what is nearest along the roads is weighed afterwards against what the ward and
the borough say, and the second choice is kept beside the first.

Every length is held in whole millimetres, so that a sum is the same whatever
order its parts are added in. Every list is put in order before it is walked.
So the same roads and the same seeds give the same answer, whatever order a
file lists them in.

Nothing here reads a file. It holds no name and no place.
"""

import heapq
import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from functools import cached_property

# A length along the roads, in whole millimetres.
Millimetres = int
MILLIMETRES_IN_A_METRE = 1000


def millimetres(metres: float) -> Millimetres:
    """A length in metres as whole millimetres. It stops at a length that is no length."""
    if not math.isfinite(metres) or metres < 0:
        raise ValueError("a length is a number that is not below nothing")
    return round(metres * MILLIMETRES_IN_A_METRE)


@dataclass(frozen=True, order=True)
class Link:
    """One stretch of road between two nodes, and how long it is."""

    start: str
    end: str
    metres: float


@dataclass(frozen=True, order=True)
class Near:
    """One seed, and how far along the roads it is from a node."""

    far: Millimetres
    seed: str


@dataclass(frozen=True)
class Roads:
    """The roads as a search walks them: each node, and the nodes one link away."""

    # The id of every node, in order.
    nodes: tuple[str, ...]
    # For each node, in that order: the nodes one link away and how far, in order.
    beside: tuple[tuple[tuple[int, Millimetres], ...], ...]

    @cached_property
    def number_of(self) -> Mapping[str, int]:
        return {node: number for number, node in enumerate(self.nodes)}


def roads_of(links: Iterable[Link]) -> Roads:
    """The roads, from their links in any order.

    A link from a node to itself leads nowhere and is left out. Of two links
    between the same two nodes the shorter is kept.
    """
    shortest: dict[tuple[str, str], Millimetres] = {}
    for link in links:
        if link.start == link.end:
            continue
        ends = (link.start, link.end) if link.start < link.end else (link.end, link.start)
        far = millimetres(link.metres)
        if far < shortest.get(ends, far + 1):
            shortest[ends] = far
    nodes = tuple(sorted({node for ends in shortest for node in ends}))
    number_of = {node: number for number, node in enumerate(nodes)}
    beside: list[list[tuple[int, Millimetres]]] = [[] for _ in nodes]
    for (start, end), far in shortest.items():
        beside[number_of[start]].append((number_of[end], far))
        beside[number_of[end]].append((number_of[start], far))
    return Roads(nodes=nodes, beside=tuple(tuple(sorted(others)) for others in beside))


def pieces_of(roads: Roads) -> tuple[int, ...]:
    """The piece of the roads each node is in, in the order of the nodes.

    A piece is every node that can be reached from one node. Pieces are
    numbered from nought, in the order of their first node.
    """
    piece = [-1] * len(roads.nodes)
    count = 0
    for first in range(len(roads.nodes)):
        if piece[first] >= 0:
            continue
        piece[first] = count
        waiting = [first]
        while waiting:
            for other, _ in roads.beside[waiting.pop()]:
                if piece[other] < 0:
                    piece[other] = count
                    waiting.append(other)
        count += 1
    return tuple(piece)


def nearest_seeds(
    roads: Roads, starts: Mapping[str, tuple[str, Millimetres]], most: int
) -> dict[str, tuple[Near, ...]]:
    """For every node a seed reaches, the seeds nearest to it along the roads, nearest first.

    `starts` gives each seed the node it starts from, and how far the seed is
    from that node. A node holds `most` seeds at most. Of two seeds as far as
    each other, the one whose id sorts first is the nearer. A node no seed
    reaches is not in the answer.
    """
    if most < 1:
        raise ValueError("a node holds one seed or more")
    seeds = sorted(starts)
    found: list[list[tuple[Millimetres, int]]] = [[] for _ in roads.nodes]
    waiting: list[tuple[Millimetres, int, int]] = []
    for order, seed in enumerate(seeds):
        node, far = starts[seed]
        if node not in roads.number_of or far < 0:
            raise ValueError("a seed starts from a node of the roads, at no distance below nothing")
        waiting.append((far, order, roads.number_of[node]))
    heapq.heapify(waiting)
    while waiting:
        far, order, node = heapq.heappop(waiting)
        held = found[node]
        if len(held) >= most or any(order == other for _, other in held):
            continue
        held.append((far, order))
        for other, length in roads.beside[node]:
            there = found[other]
            if len(there) < most and not any(order == seen for _, seen in there):
                heapq.heappush(waiting, (far + length, order, other))
    return {
        roads.nodes[node]: tuple(Near(far, seeds[order]) for far, order in held)
        for node, held in enumerate(found)
        if held
    }


def within(roads: Roads, start: str, limit: Millimetres) -> dict[str, Millimetres]:
    """Every node within a distance of one node along the roads, and how far each is."""
    if start not in roads.number_of:
        raise ValueError("a search starts from a node of the roads")
    found: dict[int, Millimetres] = {}
    waiting: list[tuple[Millimetres, int]] = [(0, roads.number_of[start])]
    while waiting:
        far, node = heapq.heappop(waiting)
        if node in found:
            continue
        found[node] = far
        for other, length in roads.beside[node]:
            if other not in found and far + length <= limit:
                heapq.heappush(waiting, (far + length, other))
    return {roads.nodes[node]: far for node, far in sorted(found.items())}
