"""Recorded criminal damage and arson is counted from points, and from the crime files alone.

Nothing here is real. The zip and the town are made up: `incident_support.py`
says how. Every figure is worked out by hand beside the test that holds it.
"""

import zipfile
from pathlib import Path
from typing import Any

import pytest
from burro_core.catalogue import FEATURES
from burro_pipeline.cells import land, spine
from burro_pipeline.cells.shapes import holding, on_the_grid
from burro_pipeline.derive import incident_criminal_damage as damage
from burro_pipeline.derive.measures import says_what_core_says
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.receipt import Geography, Period
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.registry.model import Use

from ..cells.support import CANARY, EAST, NORTH, SIDE
from .incident_support import (
    ANTISOCIAL,
    AT_SEA,
    DAMAGE,
    EVERY_MONTH,
    IN_ONE,
    IN_TWO,
    MONTHS,
    ONE,
    THREE,
    TWO,
    Record,
    at,
    inputs_with,
    members,
)


def built(folder: Path, held: dict[str, str | bytes] | None = None) -> damage.Incidents:
    inputs = inputs_with(folder, held)
    return damage.build(inputs, spine.build(inputs))


def refusal(folder: Path, held: dict[str, str | bytes]) -> str:
    with pytest.raises(LockError) as refused:
        built(folder, held)
    assert refused.value.rule == "input_is_as_described"
    assert CANARY not in str(refused.value)
    return str(refused.value)


def test_a_record_is_counted_in_the_area_its_point_lies_on(tmp_path: Path):
    made = built(tmp_path)
    assert {area: made.placed.count(area) for area in (ONE, TWO, THREE)} == {
        ONE: 4 * 36,
        TWO: 2 * 36,
        THREE: 0,
    }
    # 144 records in three years is 48 a year. Over 500 homes that is 96 for each 1,000.
    # 72 in three years is 24 a year. Over 660 homes that is 36.36, given as 36.4.
    assert {area: one.value for area, one in made.worked.items()} == {
        ONE: 96.0,
        TWO: 36.4,
        THREE: 0.0,
    }
    assert {one.state for one in made.worked.values()} == {State.PRESENT}
    assert {(one.units_used, one.units_expected) for one in made.worked.values()} == {(36, 36)}
    assert made.geography is Geography.POINT


def test_an_area_with_no_record_has_a_figure_of_nought_and_is_not_a_gap(tmp_path: Path):
    made = built(tmp_path)
    assert made.worked[THREE].value == 0.0
    assert made.worked[THREE].state is State.PRESENT


def test_no_other_kind_is_counted(tmp_path: Path):
    made = built(tmp_path)
    assert sum(sum(month.values()) for month in made.counted.at.values()) == 6 * 36


def test_only_a_crime_file_is_opened_and_nothing_of_a_column_that_is_not_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    seen: list[str] = []
    really_open = zipfile.ZipFile.open

    def watched(self: zipfile.ZipFile, name: Any, *args: Any, **kwargs: Any) -> Any:
        if (args[0] if args else kwargs.get("mode", "r")) == "r" and "made-up.zip" in str(
            self.filename
        ):
            seen.append(name.filename if isinstance(name, zipfile.ZipInfo) else str(name))
        return really_open(self, name, *args, **kwargs)

    inputs = inputs_with(tmp_path)
    found = spine.build(inputs)
    monkeypatch.setattr(zipfile.ZipFile, "open", watched)
    made = damage.build(inputs, found)
    assert len(set(seen)) == 72
    assert all(name.endswith("-street.csv") for name in seen)
    assert CANARY not in repr(made.counted) + repr(made.rows) + repr(made.metric)
    assert damage.COLUMNS == ("Month", "Crime type", "Longitude", "Latitude")


def test_a_record_with_no_point_and_one_at_sea_are_in_no_area(tmp_path: Path):
    held = members({MONTHS[0]: (*EVERY_MONTH, Record(DAMAGE, None), Record(DAMAGE, AT_SEA))})
    made = built(tmp_path, held)
    assert (made.placed.without, made.placed.outside) == (1, 1)
    assert made.placed.count(ONE) == 4 * 36


def test_a_month_under_half_the_middle_month_is_left_out_for_every_area(tmp_path: Path):
    # The last month holds two records of the kind, where the middle month holds six.
    short = (Record(DAMAGE, IN_ONE), Record(DAMAGE, IN_TWO))
    made = built(tmp_path, members({MONTHS[-1]: short}))
    assert made.placed.left_out == (MONTHS[-1],)
    assert made.placed.count(ONE) == 4 * 35
    # 140 records in 35 months is 48 a year, as it is over 36: nothing stands in for the
    # month, and the figure is a count a year over the months that are left.
    assert made.worked[ONE].value == 96.0
    assert made.worked[ONE].state is State.PARTIAL
    assert (made.worked[ONE].units_used, made.worked[ONE].weight_covered) == (35, 0.972222)
    assert made.metric.vintage == f"{MONTHS[0]} to {MONTHS[-2]}"
    assert "35 whole months" in made.metric.definition


def test_a_month_of_half_the_middle_month_is_whole(tmp_path: Path):
    half = tuple(Record(DAMAGE, IN_ONE) for _ in range(3))
    made = built(tmp_path, members({MONTHS[5]: half}))
    assert made.placed.left_out == ()
    assert made.placed.count(ONE) == 4 * 35 + 3


def test_a_zip_of_fewer_months_than_are_counted_stops_the_step(tmp_path: Path):
    assert "fewer months" in refusal(tmp_path, members(months=MONTHS[1:]))


def test_a_month_that_is_missing_between_two_others_stops_the_step(tmp_path: Path):
    before = ("2023-06", "2023-07", *MONTHS[:17], *MONTHS[18:])
    assert "between two others" in refusal(tmp_path, members(months=before))


def test_a_force_with_no_file_of_a_month_stops_the_step(tmp_path: Path):
    held = members()
    del held[f"{MONTHS[3]}/{MONTHS[3]}-city-of-london-street.csv"]
    assert "a force has no file" in refusal(tmp_path, held)


def test_a_row_of_another_month_than_its_file_stops_the_step(tmp_path: Path):
    held = members({MONTHS[2]: (Record(DAMAGE, IN_ONE, month=MONTHS[3]),)})
    assert "another month" in refusal(tmp_path, held)


def test_a_point_that_is_no_point_stops_the_step(tmp_path: Path):
    held = members()
    name = f"{MONTHS[0]}/{MONTHS[0]}-metropolitan-street.csv"
    held[name] = str(held[name]).replace(at(IN_ONE)[0], "not a number", 1)
    assert "a point is not a point" in refusal(tmp_path, held)


def test_the_latest_36_months_are_counted_of_a_zip_that_holds_more(tmp_path: Path):
    earlier = ("2023-06", "2023-07", *MONTHS)
    made = built(tmp_path, members(months=earlier))
    assert made.counted.months == MONTHS


def test_a_receipt_that_does_not_take_in_the_months_counted_stops_the_step(tmp_path: Path):
    inputs = inputs_with(tmp_path, period=Period(start=MONTHS[1], end=MONTHS[-1]))
    with pytest.raises(LockError) as refused:
        damage.build(inputs, spine.build(inputs))
    assert "its receipt gives another period" in str(refused.value)


def test_a_row_of_evidence_names_the_zip_the_outlines_the_lookup_and_the_homes(tmp_path: Path):
    inputs = inputs_with(tmp_path)
    made = damage.build(inputs, spine.build(inputs))
    assert sorted(receipt.source_id for receipt in made.files) == [
        "ons-census-2021-housing-tables",
        "ons-lsoa-2021",
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
        "police-uk-street-level-crime",
    ]
    assert len(made.rows) == 3
    assert {row.derivation_id for row in made.rows} == {damage.COUNTED.derivation_id}
    assert {row.inputs for row in made.rows} == {
        tuple(sorted(receipt.file_id for receipt in made.files))
    }
    # The months that were counted, with the day of the census and of the outlines.
    stated = Period(start="2021-03-21", end="2026-07-31")
    assert all(row.data_period == stated for row in made.rows)
    assert len(Evidence.of("lon-2026-10-02-01", made.files, damage.METHODS, made.rows).rows) == 3


def test_the_gate_is_asked_about_the_zip_for_scoring(tmp_path: Path):
    inputs = inputs_with(tmp_path)
    damage.build(inputs, spine.build(inputs))
    assert {(one.receipt.source_id, one.receipt.use) for one in inputs.opened} >= {
        (damage.SOURCE, Use.SCORING),
        (land.BOUNDARIES, Use.SCORING),
    }


def test_the_row_is_cores_so_a_build_carries_the_measure(tmp_path: Path):
    made = built(tmp_path)
    core = FEATURES[damage.FEATURE]
    # The name says arson, which the file counts with criminal damage, and the unit says
    # homes. It fails on the day core counts the measure for each resident again.
    assert made.metric.unit == core.unit == "per 1,000 homes a year"
    assert made.metric.label == core.label == "Recorded criminal damage and arson"
    assert made.metric.method.value == "measured"
    assert says_what_core_says(made.metric)
    for_each_resident = made.metric.model_copy(update={"unit": "per 1,000 residents a year"})
    assert not says_what_core_says(for_each_resident)


def test_no_word_of_the_measure_says_a_place_is_safe_or_who_lives_there():
    said = " ".join((*damage.CANNOT_SEE, damage.MADE_SO, damage.UNIT)).lower()
    for word in ("safe", "dangerous", "deprived", "resident", "rough"):
        assert word not in said


def test_the_same_count_over_land_is_for_each_hectare(tmp_path: Path):
    inputs = inputs_with(tmp_path)
    found = spine.build(inputs)
    made = damage.build(inputs, found)
    over_land = damage.for_each_hectare(made.placed, land.build(inputs, found))
    # Each area of the town is four squares of 100 metres: four hectares. 48 a year over 4.
    assert over_land[ONE].value == 12.0
    assert over_land[TWO].value == 6.0


def test_a_point_on_a_line_two_outlines_share_is_counted_once_and_the_same_way():
    from shapely import box

    outlines = {"b": box(0, 0, 10, 10), "a": box(10, 0, 20, 10)}
    assert holding(outlines, [(10.0, 5.0), (5.0, 5.0), (15.0, 5.0), (25.0, 5.0)]) == [
        "a",
        "b",
        "a",
        None,
    ]
    assert holding(outlines, []) == []


def test_a_point_is_put_on_the_grid_within_a_metre_of_where_it_was_taken_from():
    easting, northing = EAST + 1.5 * SIDE, NORTH + 0.5 * SIDE
    written = at((1, 0))
    ((x, y),) = on_the_grid([(float(written[0]), float(written[1]))])
    assert abs(x - easting) < 1 and abs(y - northing) < 1


def test_anti_social_behaviour_is_no_part_of_the_count():
    assert damage.CRIMINAL_DAMAGE.kind == DAMAGE != ANTISOCIAL
    assert IN_TWO != IN_ONE
