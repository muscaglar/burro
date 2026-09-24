"""Takeaways, from the register to a figure for each area.

Every file here is made up, and says so. `food_support.py` draws the town and
writes its register, and `test_venue_food_drink.py` holds the counting, the
edge of London and the evidence. These hold what differs: which kind is
counted, and what is said of the measure.

    Quillhaven 001   one by the first centre. One 810 metres from the last is out of reach
    Quillhaven 002   one by the first centre
    Tallowgate 001   none
"""

import re
from pathlib import Path

from burro_core.ids import Dimension, FeatureId, NativeResolution, Polarity
from burro_pipeline.cells import spine
from burro_pipeline.derive import measures, venue_food_drink, venue_takeaway
from burro_pipeline.derive.food_register import Group
from burro_pipeline.derive.methods import Worked
from burro_pipeline.derive.venue_takeaway import Places
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence

from .food_support import DAY, ONE, THREE, TWO, inputs_of


def built(folder: Path) -> Places:
    inputs = inputs_of(folder)
    return venue_takeaway.build(inputs, spine.build(inputs))


def test_the_one_kind_that_counts_is_the_registers_own():
    assert venue_takeaway.WHAT.groups == (Group.TAKEAWAY,)
    assert venue_takeaway.WHAT.kinds == ("Takeaway/sandwich shop",)
    assert venue_takeaway.WHAT.key == venue_takeaway.KEY == "venue_takeaway"


def test_an_area_is_given_the_takeaways_within_reach_of_its_typical_home(tmp_path: Path):
    found = built(tmp_path)
    # Of 500 homes, 110 have a takeaway within reach. Of 660, 150 have one.
    assert found.worked[ONE] == Worked(0.2, 4, 4, 1.0, State.PRESENT)
    assert found.worked[TWO] == Worked(0.2, 4, 4, 1.0, State.PRESENT)
    assert found.worked[THREE] == Worked(0.0, 4, 4, 1.0, State.PRESENT)
    assert (found.register.listed(Group.TAKEAWAY), found.register.placed(Group.TAKEAWAY)) == (
        3,
        3,
    )


def test_the_second_figure_is_for_each_thousand_homes_within_the_same_reach(tmp_path: Path):
    found = built(tmp_path)
    bottom = 110 * 110 + 120 * 120 + 130 * 130 + 140 * 140
    assert round(1000 * 110 / bottom, 4) == 1.746
    assert found.rate[ONE] == Worked(1.7, 4, 4, 1.0, State.PRESENT)


def test_core_holds_no_measure_of_it_so_no_build_carries_one():
    assert not venue_takeaway.core_holds_it()
    assert venue_takeaway.KEY not in {feature.value for feature in FeatureId}
    assert venue_takeaway.KEY not in {measure.feature for measure in measures.MEASURES}
    assert not hasattr(venue_takeaway, "FEATURE")


def test_the_rows_are_written_under_the_id_the_catalogue_would_need(tmp_path: Path):
    found = built(tmp_path)
    assert [row.fact_id.split("/", 1)[1] for row in found.rows] == ["feature/venue_takeaway"] * 3
    assert [row.fact_id.split("/", 1)[1] for row in found.rows_of_the_rate] == [
        "feature/venue_takeaway_per_homes"
    ] * 3
    rows = (*found.rows, *found.rows_of_the_rate)
    assert Evidence.of("lon-2026-10-02-01", found.files, venue_takeaway.METHODS, rows)
    assert venue_takeaway.METHODS == venue_food_drink.METHODS


def test_what_the_row_of_the_catalogue_would_say_is_said(tmp_path: Path):
    proposed = built(tmp_path).proposed
    assert proposed.key == "venue_takeaway"
    assert proposed.label == "Takeaways and sandwich shops within 800 m of home, in a straight line"
    assert (proposed.unit, proposed.dimension) == ("count", Dimension.VENUES_CULTURE)
    assert (proposed.polarity, proposed.rankable) == (Polarity.EITHER, True)
    assert proposed.native_resolution is NativeResolution.POINT
    assert proposed.vintage == DAY and len(proposed.source_ids) == 4
    assert proposed.definition.endswith(".")
    assert not re.search(r"[.!?]\s|\n", proposed.definition)
    assert "lists as Takeaway/sandwich shop, as at" in proposed.definition


def test_the_second_figure_is_put_forward_as_shown_and_not_ranked_on(tmp_path: Path):
    """It reads highest where few homes are, so an area of offices would lead."""
    proposed = built(tmp_path).proposed_rate
    assert proposed.key == "venue_takeaway_per_homes"
    assert (
        proposed.label
        == "Takeaways and sandwich shops for each 1,000 homes within 800 m, in a straight line"
    )
    assert (proposed.unit, proposed.rankable) == ("per 1,000 homes", False)
    assert "for each 1,000 homes" in proposed.definition


def test_the_kind_is_worked_out_and_is_not_put_forward_to_be_shown_on_its_own():
    """A check found places listed as a place to eat that read as a takeaway, and canteens."""
    said = venue_takeaway.NOT_ALONE
    assert said == venue_food_drink.NOT_ALONE
    assert "do not part a place to eat from a takeaway well" in said
    assert "not shown apart on a screen" in said and "three kinds together" in said
    assert said.endswith(".") and not re.search(r"[!|\n]|\d", said)
    assert not venue_takeaway.core_holds_it()


def test_what_it_cannot_see_is_what_a_register_cannot():
    said = " ".join(venue_takeaway.CANNOT_SEE)
    assert "has closed and is still listed" in said and "trades and is not registered" in said
    assert len(venue_takeaway.CANNOT_SEE) == 10 and "councils do not give kinds alike" in said
    assert len(set(venue_takeaway.CANNOT_SEE)) == 10
    for line in (*venue_food_drink.OF_EVERY_KIND, venue_food_drink.AS_AT_THE_CENSUS):
        assert line in venue_takeaway.CANNOT_SEE
    assert venue_food_drink.ONE_KIND_FOLLOWS_DENSITY in venue_takeaway.CANNOT_SEE
    assert venue_food_drink.AT_THE_EDGE in venue_takeaway.CANNOT_SEE
    for sentence in venue_takeaway.CANNOT_SEE:
        assert sentence.endswith(".") and not re.search(r"[.!?]\s|\d", sentence)
