"""What an engine is asked and gives back: the settings, the rule of a percentile, the matrices."""

from typing import Any

import pytest
from burro_pipeline.travel import engine
from burro_pipeline.travel.engine import (
    MEANING,
    Fine,
    Reached,
    RoutingError,
    Settings,
    percentile_of,
)


def window(*times: int | None) -> list[int | None]:
    return list(times)


def test_a_percentile_is_a_time_that_some_departure_minute_has():
    # Ten minutes of a window: the time at 50 is the fifth shortest, and at 90 the ninth.
    times = window(21, 30, 29, 28, 27, 26, 25, 24, 23, 22)

    assert [percentile_of(times, percent) for percent in (10, 50, 90, 100)] == [21, 25, 29, 30]
    # Between two times nothing is made up: at 55 it is the sixth, and never 25.5.
    assert percentile_of(times, 51) == percentile_of(times, 60) == 26


def test_the_design_s_own_example_comes_out_as_the_design_says():
    """One service every 10 minutes and a ride of 20: typical is 25 and just missed is 29."""
    times = [wait + 20 for wait in range(1, 11)] * 12

    assert len(times) == 120
    assert (percentile_of(times, 50), percentile_of(times, 90), max(times)) == (25, 29, 30)


def test_a_minute_with_no_journey_counts_as_longer_than_any_other():
    half = window(*([20] * 60), *([None] * 60))

    assert percentile_of(half, 50) == 20
    assert percentile_of(half, 51) is None
    assert percentile_of(window(None, None), 1) is None
    assert percentile_of(window(7), 1) == percentile_of(window(7), 100) == 7


@pytest.mark.parametrize("percent", [0, -1, 101])
def test_a_percentile_is_from_1_to_100(percent: int):
    with pytest.raises(ValueError, match="from 1 to 100"):
        percentile_of([1, 2], percent)
    with pytest.raises(ValueError, match="from 1 to 100"):
        percentile_of([], 50)


def test_just_missed_is_never_shorter_than_typical():
    for times in (window(3, 9, None), window(5, 5, 5), window(None, None), window(1, 2, 3, 4)):
        typical, missed = percentile_of(times, 50), percentile_of(times, 90)
        assert missed is None or (typical is not None and typical <= missed)


def test_the_settings_are_the_designs():
    """Section 4 of the travel design, as numbers."""
    settings = Settings()

    assert (settings.window_start, settings.departures) == (7 * 3600, 120)
    assert (settings.typical, settings.just_missed) == (50, 90)
    assert settings.percentiles == (10, 25, 50, 75, 90)
    assert (settings.cutoff_pt, settings.cutoff_cycle, settings.cutoff_walk) == (120, 60, 60)
    assert (settings.walk_speed, settings.cycle_speed) == (4800, 15000)
    assert (settings.most_rides, settings.floor) == (4, 2)


@pytest.mark.parametrize(
    "changed",
    [
        {"cutoff_pt": 254},
        {"cutoff_walk": 0},
        {"departures": 0},
        {"window_start": 24 * 3600},
        {"percentiles": (50, 50, 90)},
        {"percentiles": (90, 50)},
        {"percentiles": (0, 50, 90)},
        {"percentiles": (10, 90)},
        {"typical": 90, "just_missed": 50},
        {"walk_speed": 0},
        {"most_rides": 0},
        {"board_slack": -1},
        {"longest_walk": -1},
        {"floor": -1},
    ],
)
def test_settings_that_make_no_sense_are_refused(changed: dict[str, Any]):
    with pytest.raises(ValueError, match=r"\w"):
        Settings(**changed)


def reached(origin_id: str, width: int = 2) -> Reached:
    row = tuple(range(width))
    return Reached(origin_id, {50: row, 90: row}, row, row)


def test_the_fine_matrices_hold_each_origin_once_and_in_order():
    Fine(("syn-d0001", "syn-d0002"), (reached("a"), reached("b")))

    for given in ([reached("b"), reached("a")], [reached("a"), reached("a")]):
        with pytest.raises(RoutingError) as stopped:
            Fine(("syn-d0001", "syn-d0002"), tuple(given))
        assert stopped.value.rule == "origins_are_given_once"


def test_an_answer_for_too_few_destinations_is_refused():
    with pytest.raises(RoutingError) as stopped:
        Fine(("syn-d0001", "syn-d0002", "syn-d0003"), (reached("a"),))

    assert stopped.value.rule == "answers_are_whole"


def test_a_refusal_names_a_rule_and_nothing_else():
    for rule, words in MEANING.items():
        assert str(RoutingError(rule)) == f"{words} [{rule}]"


def test_the_module_names_the_engine_and_imports_none():
    said = engine.__doc__ or ""

    assert "R5" in said and "No module here" in said
