"""What a publisher's own rows say of a dash. Every count here is made up."""

import pytest
from burro_pipeline.derive.rounded_counts import MOST_HIDDEN, ROUNDING, Count, disagrees


@pytest.mark.parametrize(
    ("own", "parts"),
    [
        (0, [0, 0, 0]),
        (None, [None, 0, 0]),
        (None, [None, None, None, None]),
        # Four dashes may hide 16, which the publisher rounds to 20.
        (20, [None, None, None, None]),
        (10, [None, 0]),
        (130, [100, 30]),
        # 64 and 74 are written 60 and 70, and their sum of 138 is written 140.
        (140, [60, 70]),
        # 55 and 65 are written 60 and 70, and their sum of 120 is written 120.
        (120, [60, 70]),
        (10, [10, None, 0]),
    ],
)
def test_an_area_whose_count_is_what_its_parts_allow_is_let_through(own: Count, parts: list[Count]):
    assert disagrees(own, parts) is None


@pytest.mark.parametrize(
    ("own", "parts", "words"),
    [
        (10, [0, 0], "an area holds a count and no part of it does"),
        (None, [0, 0], "an area holds a count and no part of it does"),
        (0, [None, 0], "an area holds nought and a part of it does not"),
        (0, [10, 0], "an area holds nought and a part of it does not"),
        (None, [10, 0], "a dash hides more than a small count"),
        (None, [None] * 5, "a dash hides more than a small count"),
        (50, [10, None], "an area's count is not within rounding of its parts"),
        (150, [60, 70], "an area's count is not within rounding of its parts"),
        (110, [60, 70], "an area's count is not within rounding of its parts"),
    ],
)
def test_an_area_whose_count_is_not_what_its_parts_allow_is_named(
    own: Count, parts: list[Count], words: str
):
    assert disagrees(own, parts) == words


def test_a_dash_hides_at_most_four_and_a_count_is_within_five_of_what_was_counted():
    assert (MOST_HIDDEN, ROUNDING) == (4, 5)
