"""Where every area stands on every measure is worked out once, as a release is made.

The facts of an area ask for the band and the standing of each of its figures.
Each was worked out over every area again for every figure of every area asked
about, so a page of reasons took seconds on a city of a thousand areas. A
release now holds both, and what it holds is what `band_of` and a sorted list
give: these tests hold it to that.
"""

import dataclasses

from burro_core.catalogue import band_of
from burro_core.ids import FeatureId
from burro_core.release import InMemoryRelease

from .support import build_worked_release


def figures(release: InMemoryRelease, feature_id: FeatureId) -> list[float | None]:
    rows = (release.feature(area.area_id, feature_id) for area in release.neighbourhoods)
    return [None if row is None else row.value for row in rows]


def carried(release: InMemoryRelease) -> list[FeatureId]:
    return sorted({row.feature_id for row in release.features})


def test_the_band_a_release_holds_is_the_band_that_is_worked_out_from_its_figures():
    release = build_worked_release()
    rankable = [area.rankable for area in release.neighbourhoods]

    assert carried(release)
    for feature_id in carried(release):
        bands = band_of(figures(release, feature_id), rankable)
        for area, band in zip(release.neighbourhoods, bands, strict=True):
            assert release.band(area.area_id, feature_id) == band


def test_the_figures_a_standing_is_taken_among_are_those_of_the_rankable_areas_from_the_least():
    release = build_worked_release()

    for feature_id in carried(release):
        among = sorted(
            figure
            for area, figure in zip(
                release.neighbourhoods, figures(release, feature_id), strict=True
            )
            if area.rankable and figure is not None
        )
        assert list(release.population(feature_id)) == among


def test_an_area_that_cannot_be_ranked_is_banded_and_is_not_among_the_figures():
    worked = build_worked_release()
    first = worked.neighbourhoods[0]
    release = dataclasses.replace(
        worked,
        neighbourhoods=(
            first.model_copy(update={"rankable": False}),
            *worked.neighbourhoods[1:],
        ),
    )
    feature_id = next(f for f in carried(release) if release.feature(first.area_id, f) is not None)
    row = release.feature(first.area_id, feature_id)
    assert row is not None

    assert len(release.population(feature_id)) == len(worked.population(feature_id)) - 1
    assert release.band(first.area_id, feature_id) is not None


def test_a_measure_the_release_does_not_carry_has_no_figures_and_no_band():
    release = build_worked_release()
    missing = next(f for f in FeatureId if f not in carried(release))

    assert release.population(missing) == ()
    assert release.band(release.neighbourhoods[0].area_id, missing) is None


def test_an_area_the_release_does_not_hold_has_no_band():
    release = build_worked_release()

    assert release.band("no-such-area", carried(release)[0]) is None


def test_a_release_made_from_another_holds_its_own_figures_and_not_the_others():
    worked = build_worked_release()
    feature_id = carried(worked)[0]
    fewer = dataclasses.replace(
        worked, features=tuple(row for row in worked.features if row.feature_id != feature_id)
    )

    assert worked.population(feature_id) != ()
    assert fewer.population(feature_id) == ()
