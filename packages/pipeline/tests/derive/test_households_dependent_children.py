"""Households with dependent children as a share of all households, from a made-up table.

Every figure here is made up. `census_support.py` draws the town and its counts,
and `test_census_msoa.py` holds the reading that the four census measures share.

The table gives households with dependent children in four categories, by the
kind of family. They are added up, and no figure is made from one alone.

    area             all   the four categories
    Quillhaven 001   400    40 + 20 + 30 + 10     100 of  400 is 25.0
    Quillhaven 002  1000    10 +  5 +  5 +  5      25 of 1000 is  2.5
    Tallowgate 001   300   100 + 40 + 30 + 10     180 of  300 is 60.0
"""

from itertools import permutations
from pathlib import Path

from burro_pipeline.derive import census_msoa, households_dependent_children
from burro_pipeline.derive.census_msoa import HOUSEHOLDS
from burro_pipeline.derive.methods import Worked
from burro_pipeline.evidence.row import State

from .census_support import (
    HOMES,
    MSOA_THREE,
    ONE,
    THREE,
    TWO,
    WITH_CHILDREN,
    built,
    inputs_with,
    spine_of,
    table_csv,
)

MEASURE = households_dependent_children.MEASURE


def test_the_share_is_the_four_categories_added_up_over_all_households(tmp_path: Path):
    inputs = inputs_with(tmp_path)
    assert households_dependent_children.build(inputs, spine_of(inputs)).worked == {
        ONE: Worked(25.0, 1, 1, 1.0, State.PRESENT),
        TWO: Worked(2.5, 1, 1, 1.0, State.PRESENT),
        THREE: Worked(60.0, 1, 1, 1.0, State.PRESENT),
    }


def test_it_counts_every_category_that_holds_dependent_children_and_no_other():
    counted = [MEASURE.table.category(key).name for key in MEASURE.counted]
    assert counted == list(WITH_CHILDREN)
    assert all("ependent children" in name for name in counted)
    every = [category.name for category in HOUSEHOLDS.categories]
    assert [name for name in every if "ependent children" in name] == counted


def test_which_kind_of_family_a_household_is_changes_nothing(tmp_path: Path):
    """The four are read only to be added up. Moved between them, the same homes give the same."""
    plain = built(tmp_path / "plain", MEASURE).worked
    held = [HOMES[MSOA_THREE][name] for name in WITH_CHILDREN]
    for number, moved in enumerate(list(permutations(held))[1:6]):
        row = {**HOMES[MSOA_THREE], **dict(zip(WITH_CHILDREN, moved, strict=True))}
        table = table_csv(HOUSEHOLDS, {**HOMES, MSOA_THREE: row})
        assert built(tmp_path / str(number), MEASURE, table).worked == plain


def test_no_measure_is_made_from_one_kind_of_family_alone():
    """How a couple is joined was not decided on, and nor were lone parents."""
    from burro_pipeline.derive import households_one_person

    every = (MEASURE, households_one_person.MEASURE)
    apart = set(households_dependent_children.WITH_CHILDREN)
    assert all(not (set(of.counted) & apart) or set(of.counted) == apart for of in every)
    assert "of every kind of family added together" in MEASURE.said


def test_the_name_says_households_and_the_year_and_asks_for_more():
    assert households_dependent_children.KEY == "households_dependent_children"
    assert MEASURE.label == (
        "Households with dependent children as a share of all households, Census 2021"
    )
    assert MEASURE.short_label == "More households with children"
    assert households_dependent_children.SOURCE == census_msoa.SOURCE
    assert households_dependent_children.is_the_table("census2021-ts003.zip")
    assert not households_dependent_children.is_the_table("census2021-ts003-extra.zip")


def test_what_it_cannot_see_says_the_day_and_that_it_counts_no_child():
    first, second = households_dependent_children.CANNOT_SEE
    assert "on 21 March 2021, during a lockdown" in first
    assert "cannot see how many children there are, how old they are" in second
