"""Households of one person as a share of all households, from a made-up table.

Every figure here is made up. `census_support.py` draws the town and its counts,
and `test_census_msoa.py` holds the reading that the four census measures share.

    area             all   of one person
    Quillhaven 001   400       100     100 of  400 is 25.0
    Quillhaven 002  1000       555     555 of 1000 is 55.5
    Tallowgate 001   300        30      30 of  300 is 10.0
"""

from pathlib import Path

from burro_pipeline.derive import census_msoa, households_one_person
from burro_pipeline.derive.census_msoa import HOUSEHOLDS
from burro_pipeline.derive.methods import Worked
from burro_pipeline.evidence.row import State

from .census_support import (
    HOMES,
    KINDS,
    MSOA_ONE,
    ONE,
    THREE,
    TWO,
    built,
    inputs_with,
    spine_of,
    table_csv,
)

MEASURE = households_one_person.MEASURE


def test_the_share_is_the_households_of_one_person_over_all_households(tmp_path: Path):
    inputs = inputs_with(tmp_path)
    assert households_one_person.build(inputs, spine_of(inputs)).worked == {
        ONE: Worked(25.0, 1, 1, 1.0, State.PRESENT),
        TWO: Worked(55.5, 1, 1, 1.0, State.PRESENT),
        THREE: Worked(10.0, 1, 1, 1.0, State.PRESENT),
    }


def test_it_counts_the_one_category_and_not_its_split_by_age():
    assert MEASURE.counted == ("one_person",)
    assert MEASURE.table.category("one_person").name == "One-person household"
    read = {category.name for category in HOUSEHOLDS.categories}
    assert not read & {KINDS[1], KINDS[2]}
    assert (KINDS[1], KINDS[2]) == (
        "One-person household: Aged 66 years and over",
        "One-person household: Other",
    )


def test_how_old_a_person_who_lives_alone_is_changes_nothing(tmp_path: Path):
    plain = built(tmp_path / "plain", MEASURE).worked
    row = {**HOMES[MSOA_ONE], KINDS[1]: 99, KINDS[2]: 1}
    table = table_csv(HOUSEHOLDS, {**HOMES, MSOA_ONE: row})
    assert built(tmp_path / "moved", MEASURE, table).worked == plain


def test_the_name_says_households_and_the_year_and_asks_for_more():
    assert households_one_person.KEY == "households_one_person"
    assert MEASURE.label == "Households of one person as a share of all households, Census 2021"
    assert MEASURE.short_label == "More households of one person"
    assert households_one_person.SOURCE == census_msoa.SOURCE
    assert households_one_person.is_the_table("census2021-ts003.zip")


def test_what_it_cannot_see_says_it_cannot_tell_young_from_old():
    first, second = households_one_person.CANNOT_SEE
    assert "on 21 March 2021, during a lockdown" in first
    assert "cannot tell a young person who lives alone from an old one" in second
