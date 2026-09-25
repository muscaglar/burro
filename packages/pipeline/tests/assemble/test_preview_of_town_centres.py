"""The measures of town centres in the whole of a made-up build, on the day core names them.

A build leaves the size and the shape of a centre out while their names are not
core's. This test stands for the day core and the measures say the same, so
that nothing but the name is seen to keep either out: the release is written,
and every fact of it has its evidence. No real build is made so. Neither is a
part of any recipe since 2026-09-25, when Village feel came to be made of the
high street nearest a home: `test_preview_of_high_streets.py` holds that.

The distance to the nearest centre is another matter. Core names it as it is
built, a distance in metres, so every build made here carries it.

The town is Quillhaven and Tallowgate, which do not exist, and every figure is
made up. The homes of Tallowgate stand nearer to homes beyond London than to
any centre of the file, so Tallowgate has no figure for either measure.
"""

import io
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from burro_core.catalogue import TAGS
from burro_core.ids import FeatureId
from burro_pipeline.derive import centre_compact, centre_small
from burro_pipeline.release.read import read_release

from ..derive.centres_support import QUILLHAVEN_1, QUILLHAVEN_2
from .support import made, named_as_core_names_it

SIZE_AND_SHAPE = {FeatureId.CENTRE_SMALL, FeatureId.CENTRE_COMPACT}


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
    # Neither is a part of any recipe, so neither places an area on a vibe.
    assert not SIZE_AND_SHAPE & {term.feature_id for tag in TAGS.values() for term in tag.terms}
