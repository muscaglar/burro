"""The numbers a person set by judgement, as the panel lists them.

They are read from core, where they are, and none is changed at the panel yet.
"""

from typing import Any

import pytest
from burro_core import estimate
from burro_core.catalogue import NEAREST_WITHIN_M, PART_MAX_HUNDREDTHS, WITHIN_M
from burro_core.rank import FIRM_BUDGET_MARGIN_PERCENT
from burro_core.release import FEWEST_SALES
from desk import cli, fill, server
from desk.panel import look, routes


@pytest.fixture(scope="module")
def numbers(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    data = tmp_path_factory.mktemp("numbers") / "desk-synthetic"
    fill.fill(cli.FIXTURE, data, synthetic=True)
    panel = routes.open_panel(cli.FIXTURE / "syn-2026-09-23-01")
    desk = server.open_desk(data, cli.PAGE, cli.QUESTIONS, "r1", log=lambda _: None, panel=panel)
    return panel.answer(desk, "numbers", None, None)


def of(numbers: dict[str, Any]) -> dict[str, Any]:
    return {row["id"]: row for group in numbers["groups"] for row in group["numbers"]}


def test_every_number_the_founder_named_is_listed_with_what_it_is_today(
    numbers: dict[str, Any],
):
    held = {key: row["value"] for key, row in of(numbers).items()}
    assert held == {
        "firm_budget_margin": FIRM_BUDGET_MARGIN_PERCENT,
        "journey_fixed_minutes": estimate.FIXED_MINUTES,
        "journey_minutes_a_km": estimate.MINUTES_A_KM,
        "journey_minutes_a_km_near_the_underground": estimate.MINUTES_A_KM_NEAR_THE_UNDERGROUND,
        "journey_near_the_underground": estimate.NEAR_THE_UNDERGROUND_M,
        "journey_within_by": estimate.WITHIN_BY,
        "journey_beyond_by": estimate.BEYOND_BY,
        "near": WITHIN_M,
        "nearest": NEAREST_WITHIN_M,
        "fewest_sales": FEWEST_SALES,
        "part_most": PART_MAX_HUNDREDTHS,
        "band_needs": 60,
        "rests_on_little": look.LITTLE,
        "far_from_beside": look.FAR,
    }
    assert [group["title"] for group in numbers["groups"]] == [
        "A firm budget",
        "The estimate of a journey",
        "How near is near",
        "A price",
        "A recipe and a band",
        "What the panel calls out",
    ]


def test_each_number_says_its_unit_where_it_is_and_how_it_is_changed(numbers: dict[str, Any]):
    for row in of(numbers).values():
        assert set(row) == {"id", "says", "value", "unit", "where", "changed_by"}
        assert row["says"].endswith(".") and row["where"] and row["changed_by"].endswith(".")
        assert type(row["value"]) in (int, float)
    assert (
        of(numbers)["fewest_sales"]["where"]
        == "FEWEST_SALES in packages/core/src/burro_core/release.py"
    )


def test_no_number_is_changed_at_the_panel_yet_and_the_panel_says_so(numbers: dict[str, Any]):
    assert numbers["says"] == routes.NUMBERS_ARE_CORES
    panel = routes.open_panel(cli.FIXTURE / "syn-2026-09-23-01")
    assert "number" not in {what.value for what in routes.STANDS}
    assert panel.searches
