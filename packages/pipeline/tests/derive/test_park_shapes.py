"""Which outlines hold which: the share of a site's land that lies inside another.

Every shape here is made up: boxes in the North Sea, where the made-up town of
the tests of cells stands.
"""

import pytest
from burro_pipeline.cells.shapes import Shape, outline_of
from burro_pipeline.derive.park_shapes import held_by


def box(west: float, south: float, wide: float, high: float) -> Shape:
    x, y = 700_000 + west, 400_000 + south
    ring = [(x, y), (x + wide, y), (x + wide, y + high), (x, y + high), (x, y)]
    return outline_of([[ring]])


PARKS = {"meadow": box(0, 0, 100, 100), "garden": box(40, 40, 20, 20), "far": box(500, 0, 50, 50)}


@pytest.mark.parametrize(
    ("site", "holders"),
    [
        # Wholly inside one park, and inside the garden that stands in it.
        (box(45, 45, 10, 10), ("garden", "meadow")),
        (box(10, 10, 10, 10), ("meadow",)),
        # Six parts in ten, and exactly half.
        (box(94, 0, 10, 10), ("meadow",)),
        (box(95, 0, 10, 10), ("meadow",)),
        # Four parts in ten.
        (box(96, 0, 10, 10), ()),
        # Against the side of a park, and at its corner.
        (box(100, 0, 10, 10), ()),
        (box(100, 100, 10, 10), ()),
        # Near no park.
        (box(300, 300, 10, 10), ()),
    ],
)
def test_a_site_is_inside_a_park_that_holds_at_least_half_of_its_land(
    site: Shape, holders: tuple[str, ...]
):
    assert held_by({"site": site}, PARKS, 0.5) == {"site": holders}


def test_the_land_of_two_parks_is_never_added_up():
    """A third of the site is in one park and a third in another: it is inside neither."""
    parks = {"west": box(0, 0, 10, 30), "east": box(20, 0, 10, 30)}
    assert held_by({"site": box(0, 0, 30, 30)}, parks, 0.5) == {"site": ()}


def test_every_site_has_an_answer_and_the_order_they_are_given_in_changes_nothing():
    sites = {"b": box(10, 10, 10, 10), "a": box(300, 300, 10, 10), "c": box(510, 10, 10, 10)}
    turned = dict(reversed(list(sites.items())))
    parks = dict(reversed(list(PARKS.items())))
    found = held_by(sites, PARKS, 0.5)
    assert found == held_by(turned, parks, 0.5) == {"a": (), "b": ("meadow",), "c": ("far",)}
    assert list(found) == ["a", "b", "c"]


@pytest.mark.parametrize("share", [0.0, -0.5, 1.5])
def test_a_share_is_more_than_none_and_no_more_than_the_whole(share: float):
    with pytest.raises(ValueError, match="a share"):
        held_by({"site": box(0, 0, 10, 10)}, PARKS, share)
