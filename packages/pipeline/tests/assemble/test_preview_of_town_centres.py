"""The measures of town centres in the whole of a made-up build, on the day core names them.

A build leaves the size and the shape of a centre out while their names are not
core's. These tests stand for the day core and the measures say the same, so
that nothing but the name is seen to keep either out: the release is written,
every fact of it has its evidence, and Village feel is placed where both have
a figure. No real build is made so.

The distance to the nearest centre is another matter. Core names it as it is
built, a distance in metres, so every build made here carries it.

The town is Quillhaven and Tallowgate, which do not exist, and every figure is
made up. The homes of Tallowgate stand nearer to homes beyond London than to
any centre of the file, so Tallowgate has no figure for either measure.
"""

import io
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest
from burro_core.catalogue import TAG_MIN_COVERAGE_HUNDREDTHS, TAGS
from burro_core.ids import FeatureId, TagId
from burro_core.release import TagValue
from burro_pipeline.derive import centre_compact, centre_small
from burro_pipeline.release.read import read_release

from ..derive.centres_support import QUILLHAVEN_1, QUILLHAVEN_2, TALLOWGATE
from .support import Made, made, named_as_core_names_it

SIZE_AND_SHAPE = {FeatureId.CENTRE_SMALL, FeatureId.CENTRE_COMPACT}
ENOUGH = TAG_MIN_COVERAGE_HUNDREDTHS / 100


def test_named_as_core_names_them_the_size_and_the_shape_of_a_centre_are_carried(tmp_path: Path):
    found = made(tmp_path)
    with (
        named_as_core_names_it(centre_small),
        named_as_core_names_it(centre_compact),
        redirect_stdout(io.StringIO()) as said,
        redirect_stderr(io.StringIO()),
    ):
        assert found.run() == 0
    (checked,) = (line for line in said.getvalue().splitlines() if line.startswith("step=check "))
    assert " status=ok " in checked and " findings=0 " in checked
    release = read_release(found.release)
    carried = {metric.feature_id for metric in release.metrics}
    assert carried >= SIZE_AND_SHAPE and FeatureId.HIGHSTREET_ACCESS in carried
    with_a_figure = {
        feature: {
            fact.area_id
            for fact in release.features
            if fact.feature_id == feature and fact.value is not None
        }
        for feature in SIZE_AND_SHAPE
    }
    assert with_a_figure == {feature: {QUILLHAVEN_1, QUILLHAVEN_2} for feature in SIZE_AND_SHAPE}


def test_village_feel_is_placed_where_the_size_and_the_shape_of_a_centre_have_a_figure(
    tmp_path: Path,
):
    """Each is 20 in 100 of the recipe, and homes before 1919 is 20 more."""
    parts = {term.feature_id: term.hundredths for term in TAGS[TagId.VILLAGE_FEEL].terms}
    assert {parts[feature] for feature in SIZE_AND_SHAPE} == {20}
    before = _placed(made(tmp_path / "before"))
    found = made(tmp_path / "after")
    with named_as_core_names_it(centre_small), named_as_core_names_it(centre_compact):
        after = _placed(found)
    for area in (QUILLHAVEN_1, QUILLHAVEN_2):
        assert after[area].coverage == pytest.approx(before[area].coverage + 0.4)
        assert after[area].coverage >= ENOUGH and after[area].score is not None
    # Nothing is put in for the area with no figure: it is placed no more than it was.
    assert after[TALLOWGATE].coverage == before[TALLOWGATE].coverage
    assert (after[TALLOWGATE].score is None) == (before[TALLOWGATE].score is None)


def _placed(found: Made) -> dict[str, TagValue]:
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        assert found.run() == 0
    release = read_release(found.release)
    return {tag.area_id: tag for tag in release.tags if tag.tag_id == TagId.VILLAGE_FEEL}
