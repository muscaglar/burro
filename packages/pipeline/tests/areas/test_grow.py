"""The search along the roads, on a made-up town. Nothing here is real, and no file is read."""

import random

import pytest
from burro_pipeline.areas.grow import (
    Link,
    Near,
    millimetres,
    nearest_seeds,
    pieces_of,
    roads_of,
    within,
)


def node(square: tuple[int, int]) -> str:
    return f"syn-node-{square[1]:02d}-{square[0]:02d}"


def grid(columns: int, rows: int) -> list[Link]:
    """A node at every crossing of a grid, 100 metres from the ones beside it."""
    return [
        Link(node((column, row)), node(other), 100.0)
        for row in range(rows)
        for column in range(columns)
        for other in ((column + 1, row), (column, row + 1))
        if other[0] < columns and other[1] < rows
    ]


# A row of five nodes, 100 metres apart, and one node that no link reaches.
ROW = [Link(node((column, 0)), node((column + 1, 0)), 100.0) for column in range(4)]
WEST, MIDDLE, EAST = node((0, 0)), node((2, 0)), node((4, 0))


def test_each_node_holds_its_nearest_seeds_with_the_nearest_first():
    found = nearest_seeds(roads_of(ROW), {"syn-a": (WEST, 0), "syn-b": (EAST, 0)}, most=2)
    assert found[node((1, 0))] == (Near(100_000, "syn-a"), Near(300_000, "syn-b"))
    assert found[node((3, 0))] == (Near(100_000, "syn-b"), Near(300_000, "syn-a"))


def test_a_node_holds_no_more_seeds_than_it_is_asked_to():
    starts = {"syn-a": (WEST, 0), "syn-b": (MIDDLE, 0), "syn-c": (EAST, 0)}
    found = nearest_seeds(roads_of(ROW), starts, most=2)
    assert all(len(near) == 2 for near in found.values())
    assert [each.seed for each in found[WEST]] == ["syn-a", "syn-b"]


def test_of_two_seeds_as_far_as_each_other_the_one_whose_id_sorts_first_is_nearer():
    found = nearest_seeds(roads_of(ROW), {"syn-b": (WEST, 0), "syn-a": (EAST, 0)}, most=2)
    assert found[MIDDLE] == (Near(200_000, "syn-a"), Near(200_000, "syn-b"))


def test_how_far_a_seed_is_from_its_node_is_added_to_every_distance():
    found = nearest_seeds(roads_of(ROW), {"syn-a": (WEST, 25_000)}, most=1)
    assert found[WEST] == (Near(25_000, "syn-a"),)
    assert found[EAST] == (Near(425_000, "syn-a"),)


def test_a_node_no_seed_reaches_is_not_in_the_answer():
    apart = [*ROW, Link("syn-node-far-a", "syn-node-far-b", 50.0)]
    found = nearest_seeds(roads_of(apart), {"syn-a": (WEST, 0)}, most=3)
    assert len(found) == 5
    assert "syn-node-far-a" not in found


def test_a_link_to_itself_is_left_out_and_of_two_links_the_shorter_is_kept():
    roads = roads_of(
        [Link(WEST, WEST, 10.0), Link(WEST, MIDDLE, 300.0), Link(MIDDLE, WEST, 200.0004)]
    )
    assert roads.nodes == (WEST, MIDDLE)
    assert roads.beside == (((1, 200_000),), ((0, 200_000),))


def test_a_length_that_is_no_length_stops_the_roads():
    for wrong in (float("nan"), float("inf"), -1.0):
        with pytest.raises(ValueError, match="a length"):
            millimetres(wrong)


def test_a_seed_that_starts_from_no_node_of_the_roads_stops_the_search():
    with pytest.raises(ValueError, match="a seed starts"):
        nearest_seeds(roads_of(ROW), {"syn-a": ("syn-node-nowhere", 0)}, most=1)


def test_every_node_within_a_distance_is_found_and_none_beyond_it():
    found = within(roads_of(ROW), MIDDLE, 100_000)
    assert found == {node((1, 0)): 100_000, MIDDLE: 0, node((3, 0)): 100_000}


def test_the_same_roads_in_another_order_give_the_same_answer():
    made = grid(columns=9, rows=7)
    starts = {
        "syn-a": (node((1, 1)), 0),
        "syn-b": (node((7, 5)), 12_000),
        "syn-c": (node((4, 3)), 0),
    }
    first = nearest_seeds(roads_of(made), starts, most=3)
    assert len(first) == 63 and all(len(near) == 3 for near in first.values())
    drawn = random.Random(7)  # noqa: S311
    for _ in range(3):
        links = [Link(link.end, link.start, link.metres) for link in made]
        drawn.shuffle(links)
        turned = dict(drawn.sample(sorted(starts.items()), len(starts)))
        assert nearest_seeds(roads_of(links), turned, most=3) == first


def test_the_roads_fall_into_the_pieces_that_no_link_joins():
    apart = [*ROW, Link("syn-node-far-a", "syn-node-far-b", 50.0)]
    roads = roads_of(apart)
    assert dict(zip(roads.nodes, pieces_of(roads), strict=True)) == {
        **{node((column, 0)): 0 for column in range(5)},
        "syn-node-far-a": 1,
        "syn-node-far-b": 1,
    }
