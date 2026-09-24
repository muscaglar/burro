"""Whether a figure of culture says something that how central an area is does not.

Every number here is made up. The check is handed figures and reads no file.
"""

from pathlib import Path

import pytest
from burro_pipeline.cells import spine
from burro_pipeline.derive import culture_check, culture_venues
from burro_pipeline.derive.culture_check import (
    FOLLOWS,
    Held,
    check,
    distance_from_the_middle,
    held_against,
    middle_of,
    put_forward,
    rank_correlation,
    ranks,
)
from burro_pipeline.derive.culture_reach import ground_of, metres_between
from burro_pipeline.derive.culture_venues import KEY, KEY_OF_THE_KINDS, KEY_OF_THE_RATE

from .culture_support import IN_THE_TOWN, ONE, THREE, TWO, inputs_of

# The order of things


def test_a_rank_is_a_place_in_the_order_and_a_tie_shares_the_middle_of_its_places():
    assert ranks([10.0, 30.0, 20.0]) == [1.0, 3.0, 2.0]
    assert ranks([5.0, 5.0, 1.0, 9.0]) == [2.5, 2.5, 1.0, 4.0]
    assert ranks([7.0, 7.0, 7.0]) == [2.0, 2.0, 2.0]
    assert ranks([]) == []


def test_two_lists_in_one_order_correlate_at_one_and_in_the_other_order_at_minus_one():
    up = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert rank_correlation(up, [10.0, 20.0, 30.0, 40.0, 500.0]) == 1.0
    assert rank_correlation(up, [5.0, 4.0, 3.0, 2.0, 1.0]) == -1.0


def test_a_rank_correlation_is_the_one_a_textbook_gives():
    """Ten made-up pairs, worked by hand: 1 - 6 x 8 / (10 x 99)."""
    one = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    other = [2.0, 1.0, 4.0, 3.0, 6.0, 5.0, 8.0, 7.0, 10.0, 12.0]
    squared = sum((a - b) ** 2 for a, b in zip(ranks(one), ranks(other), strict=True))
    assert squared == 8.0
    assert rank_correlation(one, other) == pytest.approx(1 - 6 * 8 / (10 * 99))


def test_ties_are_counted_as_the_order_of_the_ranks_has_them():
    one, other = [1.0, 1.0, 2.0, 3.0], [1.0, 2.0, 2.0, 3.0]
    found = rank_correlation(one, other)
    assert found is not None and 0.8 < found < 1.0


@pytest.mark.parametrize(
    ("one", "other"),
    [([], []), ([1.0], [2.0]), ([1.0, 2.0], [2.0, 1.0]), ([1.0, 1.0, 1.0], [1.0, 2.0, 3.0])],
)
def test_too_few_areas_or_no_spread_gives_no_correlation_and_never_nought(
    one: list[float], other: list[float]
):
    assert rank_correlation(one, other) is None


def test_two_lists_of_two_lengths_are_refused():
    with pytest.raises(ValueError, match="as many"):
        rank_correlation([1.0, 2.0, 3.0], [1.0, 2.0])


# What is put forward


def held(figure: str, every: float | None, distance: float | None = -0.5) -> Held:
    return Held(figure, 900, with_density=0.6, with_distance=distance, with_every=every)


def test_the_rate_is_put_forward_where_the_count_follows_the_centre_and_the_rate_does_not():
    assert FOLLOWS == 0.9
    chosen, why = put_forward(held(KEY, 0.96), held(KEY_OF_THE_RATE, 0.7))
    assert chosen == KEY_OF_THE_RATE
    assert "0.9" in why and why.endswith(".")


def test_a_figure_follows_the_centre_by_either_sign_and_by_either_measure_of_it():
    assert held(KEY, 0.9).follows_the_centre and held(KEY, -0.93).follows_the_centre
    assert held(KEY, 0.2, distance=-0.91).follows_the_centre
    assert not held(KEY, 0.89, distance=-0.89).follows_the_centre
    assert not held(KEY, None, distance=None).follows_the_centre


@pytest.mark.parametrize(
    ("count", "rate"),
    [(0.5, 0.4), (0.95, 0.92), (0.5, 0.95), (None, 0.3)],
    ids=["neither follows", "both follow", "the rate alone follows", "the count is not known"],
)
def test_in_every_other_case_nothing_is_put_forward_and_a_person_decides(
    count: float | None, rate: float | None
):
    chosen, why = put_forward(held(KEY, count, distance=None), held(KEY_OF_THE_RATE, rate))
    assert chosen is None
    assert "person" in why and why.endswith(".")


# The middle of the homes


def test_the_middle_is_where_the_homes_are_and_not_where_the_land_is(tmp_path: Path):
    inputs = inputs_of(tmp_path)
    found = spine.build(inputs)
    ground = ground_of(inputs, found)
    middle = middle_of(found, ground.at)
    longitudes = [point[0] for point in ground.at.values()]
    latitudes = [point[1] for point in ground.at.values()]
    # More homes stand in the north and the east of the made-up town than in its south-west.
    assert sum(longitudes) / 12 < middle[0] < max(longitudes)
    assert sum(latitudes) / 12 < middle[1] < max(latitudes)


def test_how_far_an_area_is_from_the_middle_is_the_mean_over_its_homes(tmp_path: Path):
    inputs = inputs_of(tmp_path)
    found = spine.build(inputs)
    ground = ground_of(inputs, found)
    far = distance_from_the_middle(found, ground.at)
    middle = middle_of(found, ground.at)
    assert set(far) == {ONE, TWO, THREE}
    assert far[TWO] < far[ONE] and far[TWO] < far[THREE]
    oas = found.weights.of_area[ONE]
    by_hand = sum(found.homes[oa] * metres_between(middle, ground.at[oa]) for oa in oas) / sum(
        found.homes[oa] for oa in oas
    )
    assert far[ONE] == pytest.approx(by_hand)


# A figure held against the three


def test_a_figure_is_held_against_the_areas_that_have_every_number():
    figure = {"a": 1.0, "b": 2.0, "c": 3.0, "d": 4.0, "e": None, "f": 6.0}
    density = {"a": 10.0, "b": 20.0, "c": 30.0, "d": 40.0, "e": 50.0}
    distance = {"a": 4.0, "b": 3.0, "c": 2.0, "d": 1.0, "e": 0.5, "f": 0.1}
    every = {"a": 1.0, "b": 3.0, "c": 2.0, "d": 4.0, "e": 9.0, "f": 9.0}
    found = held_against("made_up", figure, density, distance, every)
    assert found.areas == 4
    assert (found.with_density, found.with_distance) == (1.0, -1.0)
    assert found.with_every == pytest.approx(0.8)


def test_the_check_holds_each_of_the_three_figures_against_the_same_three(tmp_path: Path):
    inputs = inputs_of(tmp_path, IN_THE_TOWN)
    found = spine.build(inputs)
    culture = culture_venues.build(inputs, found)
    density = {ONE: 30.0, TWO: 20.0, THREE: 10.0}
    result = check(culture, found, density, ground_of(inputs, found))
    assert [one.figure for one in result.held] == [KEY, KEY_OF_THE_RATE, KEY_OF_THE_KINDS]
    assert {one.areas for one in result.held} == {3}
    assert result.put_forward is None and "person" in result.why
    for line in result.lines():
        assert culture_check.is_a_line_of_numbers(line), line


def test_what_the_check_prints_holds_numbers_and_no_name_of_an_area(tmp_path: Path):
    inputs = inputs_of(tmp_path, IN_THE_TOWN)
    found = spine.build(inputs)
    culture = culture_venues.build(inputs, found)
    result = check(culture, found, {ONE: 1.0, TWO: 2.0, THREE: 3.0}, ground_of(inputs, found))
    said = "\n".join(result.lines())
    assert "lon-" not in said and "Quillhaven" not in said and "Tallowgate" not in said
