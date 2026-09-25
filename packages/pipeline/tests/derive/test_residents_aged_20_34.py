"""Residents aged 20 to 34 as a share of all residents, from a made-up table of age.

Every figure here is made up. `census_support.py` draws the town and its counts,
and `test_census_msoa.py` holds the reading that the four census measures share.

    area             all   20-24  25-29  30-34
    Quillhaven 001  1000     100    150     50     300 of 1000 is 30.0
    Quillhaven 002  2000     200    300    400     900 of 2000 is 45.0
    Tallowgate 001   800       8      8      8      24 of  800 is  3.0
"""

from pathlib import Path

import pytest
from burro_pipeline.derive import census_msoa, residents_aged_20_34
from burro_pipeline.derive.census_msoa import AGE
from burro_pipeline.derive.methods import Worked
from burro_pipeline.evidence.row import State

from .census_support import AGES, MSOA_ONE, ONE, THREE, TWO, inputs_with, spine_of, table_csv
from .census_support import built as built_of

MEASURE = residents_aged_20_34.MEASURE


def test_the_share_is_the_three_bands_added_up_over_all_residents(tmp_path: Path):
    inputs = inputs_with(tmp_path)
    assert residents_aged_20_34.build(inputs, spine_of(inputs)).worked == {
        ONE: Worked(30.0, 1, 1, 1.0, State.PRESENT),
        TWO: Worked(45.0, 1, 1, 1.0, State.PRESENT),
        THREE: Worked(3.0, 1, 1, 1.0, State.PRESENT),
    }


def test_it_counts_the_bands_from_20_to_34_and_no_other():
    assert MEASURE.counted == ("aged_20_24", "aged_25_29", "aged_30_34")
    assert [MEASURE.table.category(key).name for key in MEASURE.counted] == [
        "Aged 20 to 24 years",
        "Aged 25 to 29 years",
        "Aged 30 to 34 years",
    ]


@pytest.mark.parametrize("band", ["Aged 15 to 19 years", "Aged 50 to 54 years"])
def test_a_band_on_either_side_is_part_of_no_figure(tmp_path: Path, band: str):
    """Residents moved between two bands that are not counted move no figure."""
    row = {**AGES[MSOA_ONE], band: 200}
    row["Aged 35 to 39 years"] -= 200
    made = built_of(tmp_path, MEASURE, table_csv(AGE, {**AGES, MSOA_ONE: row}))
    assert made.worked[ONE].value == 30.0


def test_a_figure_is_given_to_one_decimal_place_with_a_half_taken_upward(tmp_path: Path):
    """25 of 2000 is 1.25 in 100, which a person who rounds by hand gives as 1.3."""
    row = {**AGES["E02999002"]} | {
        "Aged 20 to 24 years": 25,
        "Aged 25 to 29 years": 0,
        "Aged 30 to 34 years": 0,
    }
    # The 875 who are in the three bands no longer are in a band that is not counted.
    row["Aged 50 to 54 years"] = 875
    made = built_of(tmp_path, MEASURE, table_csv(AGE, {**AGES, "E02999002": row}))
    assert made.worked[TWO].value == 1.3


def test_the_name_says_residents_and_the_year_and_asks_for_more():
    assert residents_aged_20_34.KEY == "residents_aged_20_34"
    assert MEASURE.label == "Residents aged 20 to 34 as a share of all residents, Census 2021"
    assert MEASURE.short_label == "More young adults"
    assert residents_aged_20_34.SOURCE == census_msoa.SOURCE
    assert residents_aged_20_34.is_the_table("census2021-ts007a.zip")
    assert not residents_aged_20_34.is_the_table("census2021-ts003.zip")


def test_what_it_cannot_see_says_the_lockdown_bears_on_young_adults():
    first, second = residents_aged_20_34.CANNOT_SEE
    assert "on 21 March 2021, during a lockdown" in first
    assert "students" in first and "may read lower than it would in another year" in first
    assert "cannot see who has moved in or out since" in second


def test_what_it_cannot_see_says_nothing_of_who_rents():
    """No page of the publisher's ties the lockdown to who rents, and tenure was not decided on."""
    said = " ".join(residents_aged_20_34.CANNOT_SEE).lower()
    assert "rent" not in said and "tenan" not in said and "owner" not in said
