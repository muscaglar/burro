"""Residents aged 65 and over as a share of all residents, from a made-up table of age.

Every figure here is made up. `census_support.py` draws the town and its counts,
and `test_census_msoa.py` holds the reading that the four census measures share.

    area             all   65-69  70-74  75-79  80-84  85 and over
    Quillhaven 001  1000      40     30     20      7      3     100 of 1000 is 10.0
    Quillhaven 002  2000       5      5      5      5      5      25 of 2000 is  1.3
    Tallowgate 001   800     100    100    100     50     50     400 of  800 is 50.0
"""

from pathlib import Path

from burro_pipeline.derive import census_msoa, residents_aged_65_over
from burro_pipeline.derive.census_msoa import AGE
from burro_pipeline.derive.methods import Worked
from burro_pipeline.evidence.row import State

from .census_support import AGES, MSOA_ONE, ONE, THREE, TWO, built, inputs_with, spine_of, table_csv

MEASURE = residents_aged_65_over.MEASURE


def test_the_share_is_the_five_oldest_bands_added_up_over_all_residents(tmp_path: Path):
    inputs = inputs_with(tmp_path)
    assert residents_aged_65_over.build(inputs, spine_of(inputs)).worked == {
        ONE: Worked(10.0, 1, 1, 1.0, State.PRESENT),
        # 25 of 2000 is 1.25 in 100, and a half is taken upward.
        TWO: Worked(1.3, 1, 1, 1.0, State.PRESENT),
        THREE: Worked(50.0, 1, 1, 1.0, State.PRESENT),
    }


def test_it_counts_the_bands_from_65_upward_and_no_other():
    assert [MEASURE.table.category(key).name for key in MEASURE.counted] == [
        "Aged 65 to 69 years",
        "Aged 70 to 74 years",
        "Aged 75 to 79 years",
        "Aged 80 to 84 years",
        "Aged 85 years and over",
    ]


def test_the_band_below_65_is_part_of_no_figure(tmp_path: Path):
    row = {**AGES[MSOA_ONE], "Aged 60 to 64 years": 300}
    row["Aged 35 to 39 years"] -= 300
    made = built(tmp_path, MEASURE, table_csv(AGE, {**AGES, MSOA_ONE: row}))
    assert made.worked[ONE].value == 10.0


def test_the_name_says_residents_and_the_year_and_asks_for_more():
    assert residents_aged_65_over.KEY == "residents_aged_65_over"
    assert MEASURE.label == "Residents aged 65 and over as a share of all residents, Census 2021"
    assert MEASURE.short_label == "More residents aged 65 and over"
    assert residents_aged_65_over.SOURCE == census_msoa.SOURCE
    assert residents_aged_65_over.is_the_table("census2021-ts007a.zip")


def test_what_it_cannot_see_says_the_day_and_that_a_share_is_of_everyone():
    first, second = residents_aged_65_over.CANNOT_SEE
    assert "on 21 March 2021, during a lockdown" in first
    assert "cannot see who has moved in or out since" in first
    assert "or who lives in a home built since" in first
    assert "cannot tell an area with many older residents from one with few younger" in second
