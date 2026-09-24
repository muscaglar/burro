"""What a build does with the two measures of play and parks.

Every file here is made up. Core names the nearest play space as it is built, a straight
line, so a build carries it wherever an area has a figure. What a park offers keeps core's
name, which says a walk, so a build leaves it out: one test stands for the day the names
agree, so that nothing but the name is seen to keep it out.

The made-up town holds parks and no site inside one, and no play space with a way in.
One test gives it a play space with a gate for walkers, so that the nearest play space has
a figure to carry.
"""

from dataclasses import replace
from pathlib import Path

import pytest
from burro_core.ids import FeatureId, TagId
from burro_pipeline.derive import park_facilities, play_space_proximity
from burro_pipeline.release.read import read_release

from ..derive.green_support import (
    ON_FOOT,
    PLAY,
    SITES,
    WAYS_IN,
    MadeUpSite,
    MadeUpWay,
    at,
    box,
    document,
    tile,
)
from .support import Made, files, made, named_as_core_names_it

Printed = pytest.CaptureFixture[str]


def lines_of(capsys: Printed) -> list[list[str]]:
    return [line.split() for line in capsys.readouterr().out.splitlines()]


def with_a_play_space(folder: Path) -> Made:
    """The made-up build, with a play space in the town that has a gate for walkers."""
    swings = MadeUpSite("idSWINGS", PLAY, ((box(40, 40, 20, 20),),))
    gate = MadeUpWay("idSWINGS", ON_FOOT, at(40, 50))
    town = tile("tc", document((*SITES, swings), (*WAYS_IN, gate)))
    return made(folder, changed={"sites-tc": replace(files()["sites-tc"], content=town)})


def test_what_a_park_offers_is_carried_once_it_says_what_core_says(tmp_path: Path, capsys: Printed):
    """The release is checked before it is written, so every row of the measure was held.

    No park of the town holds a site, so every area counts none, and nought is a figure.
    Parks close by then rests on the whole of its recipe, where it rested on 70 in 100.
    """
    found = made(tmp_path)
    with named_as_core_names_it(park_facilities):
        assert found.run() == 0
    said = lines_of(capsys)
    carried = [line[2] for line in said if line[:2] == ["step=derive", "status=ok"]]
    assert "feature=park_facilities" in carried
    (checked,) = [line for line in said if line[0] == "step=check"]
    assert "findings=0" in checked
    release = read_release(found.release)
    assert FeatureId.PARK_FACILITIES in {metric.feature_id for metric in release.metrics}
    figures = {
        release.feature(area.area_id, FeatureId.PARK_FACILITIES).value  # pyright: ignore[reportOptionalMemberAccess]
        for area in release.neighbourhoods
    }
    assert figures == {0.0}
    parks = [tag for tag in release.tags if tag.tag_id is TagId.PARKS_CLOSE_BY]
    assert {tag.coverage for tag in parks} == {1.0}
    assert all(tag.band is not None for tag in parks)


def test_the_nearest_play_space_is_left_out_where_no_area_has_a_figure(
    tmp_path: Path, capsys: Printed
):
    """A name does not bring a measure in: a measure with no figure is never carried.

    So Family amenities rests on the primary schools and the nearest park, 65 in 100.
    """
    found = made(tmp_path)
    assert found.run() == 0
    skipped = [line for line in lines_of(capsys) if line[:2] == ["step=derive", "status=skipped"]]
    play = [line[2:] for line in skipped if line[2] == "feature=play_space_proximity"]
    assert play == [
        ["feature=play_space_proximity", "source=os-open-greenspace", "measure_has_a_figure=1"]
    ]
    release = read_release(found.release)
    assert FeatureId.PLAY_SPACE_PROXIMITY not in {metric.feature_id for metric in release.metrics}
    family = [tag for tag in release.tags if tag.tag_id is TagId.FAMILY_AMENITIES]
    assert {tag.coverage for tag in family} == {0.65}
    assert all(tag.band is not None for tag in family)


def test_the_nearest_play_space_is_carried_where_it_has_a_figure(tmp_path: Path, capsys: Printed):
    """The release is checked before it is written, so every row of the measure was held.

    Family amenities then rests on the whole of its recipe: the primary schools, the play
    space and the nearest park. Every area is placed on it.
    """
    found = with_a_play_space(tmp_path)
    assert found.run() == 0
    said = lines_of(capsys)
    carried = [line[2] for line in said if line[:2] == ["step=derive", "status=ok"]]
    assert "feature=play_space_proximity" in carried
    (checked,) = [line for line in said if line[0] == "step=check"]
    assert "findings=0" in checked
    release = read_release(found.release)
    assert FeatureId.PLAY_SPACE_PROXIMITY in {metric.feature_id for metric in release.metrics}
    figures = [
        release.feature(area.area_id, FeatureId.PLAY_SPACE_PROXIMITY).value  # pyright: ignore[reportOptionalMemberAccess]
        for area in release.neighbourhoods
    ]
    assert all(figure is not None and figure > 0 and figure % 10 == 0 for figure in figures)
    family = [tag for tag in release.tags if tag.tag_id is TagId.FAMILY_AMENITIES]
    assert {tag.coverage for tag in family} == {1.0}
    assert all(tag.band is not None for tag in family)


def test_a_play_space_that_is_named_a_walk_is_left_out_though_it_has_a_figure(
    tmp_path: Path, capsys: Printed
):
    """With a figure for every area and a name that says a walk, it is left out."""
    found = with_a_play_space(tmp_path)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(play_space_proximity, "LABEL", "Walk to the nearest play space")
        assert found.run() == 0
    skipped = [line for line in lines_of(capsys) if line[:2] == ["step=derive", "status=skipped"]]
    play = [line[2:] for line in skipped if line[2] == "feature=play_space_proximity"]
    assert play == [
        ["feature=play_space_proximity", "source=os-open-greenspace", "measure_is_as_core_says=1"]
    ]
    release = read_release(found.release)
    assert FeatureId.PLAY_SPACE_PROXIMITY not in {metric.feature_id for metric in release.metrics}
    family = [tag for tag in release.tags if tag.tag_id is TagId.FAMILY_AMENITIES]
    assert {tag.coverage for tag in family} == {0.65}
