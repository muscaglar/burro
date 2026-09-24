"""The two measures of recorded incidents, on the police's zip as it was saved.

It is skipped where the store of fetched files is not here, or where the zip
has no receipt. It holds counts, months and the states of figures. It holds no
figure of any area and no name of a place: a count of all London is no fact
about a neighbourhood.
"""

import os
from pathlib import Path

import pytest
from burro_pipeline.cells import land, spine
from burro_pipeline.cells.land import Land
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import incident_antisocial, incident_criminal_damage
from burro_pipeline.derive.incident_criminal_damage import Incidents, for_each_hectare
from burro_pipeline.derive.measures import says_what_core_says
from burro_pipeline.evidence.lock import read_receipts
from burro_pipeline.evidence.receipt import Period
from burro_pipeline.evidence.row import State
from burro_pipeline.fetch.store import FOLDER_VARIABLE, FolderStore
from burro_pipeline.inputs import Inputs

from ..cells.support import REPOSITORY, registry

STORE = os.environ.get(FOLDER_VARIABLE, "")
RECEIPTS = REPOSITORY / "data" / "receipts"


def has_a_receipt() -> bool:
    return RECEIPTS.is_dir() and any(
        receipt.source_id == incident_criminal_damage.SOURCE for receipt in read_receipts(RECEIPTS)
    )


pytestmark = pytest.mark.skipif(
    not (STORE and Path(STORE).is_dir() and has_a_receipt()),
    reason=f"the zip is not here: {FOLDER_VARIABLE} names no folder, or it has no receipt",
)

AREAS, FILES = 1_002, 72
FIRST, LAST = "2023-08", "2026-07"
# The three latest months hold about a twentieth of the criminal damage and arson of any
# month before them, from the larger force and in every borough. So they are not whole.
NOT_WHOLE = ("2026-05", "2026-06", "2026-07")


@pytest.fixture(scope="module")
def real(tmp_path_factory: pytest.TempPathFactory) -> Inputs:
    work = tmp_path_factory.mktemp("incidents")
    return Inputs(registry(), read_receipts(RECEIPTS), FolderStore(Path(STORE)), work)


@pytest.fixture(scope="module")
def found(real: Inputs) -> Spine:
    return spine.build(real)


@pytest.fixture(scope="module")
def measured(real: Inputs, found: Spine) -> Land:
    return land.build(real, found)


@pytest.fixture(scope="module")
def damage(real: Inputs, found: Spine) -> Incidents:
    return incident_criminal_damage.build(real, found)


@pytest.fixture(scope="module")
def antisocial(real: Inputs, found: Spine) -> Incidents:
    return incident_antisocial.build(real, found)


def test_every_row_is_of_the_month_of_its_file_and_the_months_are_the_receipts(
    damage: Incidents, antisocial: Incidents
):
    # `read` stops at a row of another month than its file, so that both were read says it.
    for made in (damage, antisocial):
        assert made.counted.files == FILES
        assert (made.counted.months[0], made.counted.months[-1]) == (FIRST, LAST)
        assert len(made.counted.months) == 36
        (zipped,) = [r for r in made.files if r.source_id == incident_criminal_damage.SOURCE]
        assert zipped.data_period == Period(start=FIRST, end=LAST)


def test_the_three_latest_months_of_criminal_damage_are_not_whole(damage: Incidents):
    assert damage.placed.left_out == NOT_WHOLE
    assert len(damage.placed.whole) == 33
    middle = sorted(damage.counted.of_month(month) for month in damage.counted.months)[18]
    assert all(damage.counted.of_month(month) < middle / 10 for month in NOT_WHOLE)
    assert all(damage.counted.of_month(month) > 0.8 * middle for month in damage.placed.whole)
    assert {one.state for one in damage.worked.values()} == {State.PARTIAL}
    assert {one.weight_covered for one in damage.worked.values()} == {0.916667}


def test_every_month_of_anti_social_behaviour_is_whole(antisocial: Incidents):
    assert antisocial.placed.left_out == ()
    assert {one.state for one in antisocial.worked.values()} == {State.PRESENT}


def test_what_is_counted_and_what_is_in_no_area(damage: Incidents, antisocial: Incidents):
    counted = {
        made.metric.feature_id: (
            sum(made.placed.count(area) for area in made.worked),
            made.placed.outside,
            made.placed.without,
        )
        for made in (damage, antisocial)
    }
    assert counted == {
        "incident_criminal_damage": (151_235, 366, 720),
        "incident_antisocial": (701_377, 308, 102),
    }


def test_every_area_has_a_figure_and_a_record(damage: Incidents, antisocial: Incidents):
    for made in (damage, antisocial):
        assert len(made.worked) == len(made.rows) == AREAS
        assert all(one.value is not None and one.value > 0 for one in made.worked.values())
        assert says_what_core_says(made.metric)


def test_over_land_the_count_follows_how_close_homes_stand(
    damage: Incidents, found: Spine, measured: Land
):
    """Why no build carries the count over land: it says what homes per hectare says."""
    homes = incident_criminal_damage.homes_of(found)
    density = {area: homes[area] / measured.of_area[area] for area in homes}
    over_land = {
        area: one.value or 0.0 for area, one in for_each_hectare(damage.placed, measured).items()
    }
    over_homes = {area: one.value or 0.0 for area, one in damage.worked.items()}
    assert _ranked_alike(over_land, density) > 0.8
    assert abs(_ranked_alike(over_homes, density)) < 0.3


def _ranked_alike(one: dict[str, float], other: dict[str, float]) -> float:
    """The rank correlation of two figures over the same areas. Ties share a rank."""
    import statistics

    def ranks(of: dict[str, float]) -> list[float]:
        order = sorted(of, key=lambda area: (of[area], area))
        rank: dict[str, float] = {}
        at = 0
        while at < len(order):
            to = at
            while to + 1 < len(order) and of[order[to + 1]] == of[order[at]]:
                to += 1
            for area in order[at : to + 1]:
                rank[area] = (at + to) / 2
            at = to + 1
        return [rank[area] for area in sorted(of)]

    return statistics.correlation(ranks(one), ranks(other))
