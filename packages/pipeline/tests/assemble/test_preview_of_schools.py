"""What a build does with primary schools close by, and what it would do under another name.

Nothing here is real. The build is the made-up build of `support.py`, which
holds a made-up register of schools beside its other files.

The figure counts schools within a straight line, and core names the measure
so. So a build carries it, the release passes every check, and Family
amenities is placed on 65 in 100 of its recipe. Named schools within a short
walk, as core named it once, the figure is worked out and left out.
"""

import json
from pathlib import Path
from typing import Any

import pytest
from burro_core.catalogue import TAGS
from burro_core.ids import FeatureId, TagId
from burro_pipeline.derive import school_primary_nearby
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.release import read_release

from .support import ONE, THREE, TWO, Made, made

Printed = pytest.CaptureFixture[str]
FEATURE = FeatureId.SCHOOL_PRIMARY_NEARBY
AREAS = (ONE, TWO, THREE)
A_WALK = "State primary schools within a short walk"


def named_a_walk(found: Made) -> None:
    """Run the build with the measure named as core named it once: a walk."""
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(school_primary_nearby, "LABEL", A_WALK)
        assert found.run() == 0


def read(path: Path) -> Any:
    return json.loads(path.read_bytes())


def placed(folder: Path) -> dict[str, float]:
    """The vibes a release places, each with the share of its recipe that has a figure."""
    release = read_release(folder)
    return {tag.tag_id: tag.coverage for tag in release.tags if tag.score is not None}


def test_the_recipe_of_family_amenities_gives_primary_schools_40_in_100():
    recipe = {term.feature_id: term.hundredths for term in TAGS[TagId.FAMILY_AMENITIES].terms}
    assert recipe == {
        FeatureId.SCHOOL_PRIMARY_NEARBY: 40,
        FeatureId.PLAY_SPACE_PROXIMITY: 35,
        FeatureId.PARK_PROXIMITY: 25,
    }


def test_named_a_walk_a_build_works_the_schools_out_and_leaves_them_out_by_the_rule(
    tmp_path: Path, capsys: Printed
):
    found = made(tmp_path)
    named_a_walk(found)
    said = capsys.readouterr().out.splitlines()
    assert [line for line in said if f"feature={FEATURE}" in line] == [
        f"step=derive status=skipped feature={FEATURE} source=dfe-gias measure_is_as_core_says=1"
    ]
    release = read_release(found.release)
    assert FEATURE not in {metric.feature_id for metric in release.metrics}
    assert all(release.feature(area, FEATURE) is None for area in AREAS)
    assert TagId.FAMILY_AMENITIES not in placed(found.release)
    (left_out,) = [
        one
        for one in read(found.beside / "build.json")["measures_left_out"]
        if one["feature_id"] == FEATURE
    ]
    assert left_out["rule"] == "measure_is_as_core_says"


def test_a_figure_that_is_left_out_has_a_row_that_says_so_and_names_no_file(tmp_path: Path):
    found = made(tmp_path)
    named_a_walk(found)
    evidence = Evidence.model_validate_json((found.beside / "evidence.json").read_bytes())
    for area in AREAS:
        row = evidence.row(f"{area}/feature/{FEATURE}")
        assert row is not None
        assert (row.state, row.inputs, row.value) == (State.NOT_CARRIED, (), None)


def test_a_build_carries_the_schools_and_passes_every_check(tmp_path: Path, capsys: Printed):
    """Core names a straight line, as the figure is."""
    found = made(tmp_path)
    assert found.run() == 0
    said = capsys.readouterr().out.splitlines()
    assert f"feature={FEATURE}" in [
        line.split()[2] for line in said if line.startswith("step=derive status=ok")
    ]
    assert " findings=0 " in said[-2]
    release = read_release(found.release)
    (metric,) = [one for one in release.metrics if one.feature_id == FEATURE]
    assert (metric.unit, metric.vintage, metric.source_ids[0]) == (
        "count",
        "2026-09-24",
        "dfe-gias",
    )
    figures = [release.feature(area, FEATURE) for area in AREAS]
    assert all(figure is not None and figure.value is not None for figure in figures)
    evidence = Evidence.model_validate_json((found.beside / "evidence.json").read_bytes())
    for area in AREAS:
        row = evidence.row(f"{area}/feature/{FEATURE}")
        assert row is not None and row.state is State.PRESENT
        assert row.derivation_id == "points_within_800m_by_homes@1" and len(row.inputs) == 4


def test_family_amenities_is_placed_on_65_in_100_of_its_recipe(tmp_path: Path):
    """Schools are 40 and the nearest park is 25. The nearest play space is not in this build."""
    found = made(tmp_path)
    assert found.run() == 0
    assert placed(found.release)[TagId.FAMILY_AMENITIES] == 0.65
    record = read(found.beside / "build.json")
    (carried,) = [one for one in record["measures_carried"] if one["feature_id"] == FEATURE]
    assert carried["cannot_see"] == list(school_primary_nearby.CANNOT_SEE)
    assert carried["keyed_by"] == "point"
