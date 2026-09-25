"""The step `preview` on a build whose list names the file of high streets.

The town is Quillhaven and Tallowgate, which do not exist, and every outline is
made up. The high streets are those of the tests of the measure, laid out as
their publisher lays out its own, and the conservation areas are those the
made-up build holds already.

How much of the nearest high street lies in a conservation area is on the
table of measures, and nothing holds it back. So a build that holds the file
works it out and carries it, and a build that holds no file of it leaves it
out for that. No likeness between areas counts it.

It is 45 in 100 of Village feel, which the founder chose on 2026-09-25 to
serve as a rough guide. So an area has a band of Village feel only where its
high street has a figure, and a build that holds no file of high streets places
no area on it.

The homes of the made-up build stand where the tests of the air put them, a
kilometre apart. Those on the first square of the grid stand 332 metres from
Far Side, half of which lies inside Quayside. Every other home stands beyond
800 metres of any high street, and has none. So one area has a figure, and two
have too few homes with a high street to have one.
"""

import io
import json
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any

import pytest
from burro_core.catalogue import FEATURES, PLACED_ONLY_WITH, TAGS
from burro_core.ids import FeatureId, Sureness, TagId
from burro_core.likeness import similar
from burro_core.release import FeatureValue
from burro_pipeline.assemble import release as release_rows
from burro_pipeline.derive import conservation_cover, high_streets, highstreet_conserved
from burro_pipeline.derive.measures import MEASURES
from burro_pipeline.evidence.lock import read_lock
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.registry.model import Use
from burro_pipeline.release.read import read_release
from public_log import is_public

from ..derive import high_streets_support as streets
from .support import ONE, PAGE, THREE, TWO, File, Made, files, made

Printed = pytest.CaptureFixture[str]
FEATURE = FeatureId.HIGHSTREET_CONSERVED
NO_RECEIPT = "input_has_one_receipt"
# What the made-up outlines give: a share for the one area most of whose homes have a high
# street within reach, and none for the two where under half of the homes have one.
FIGURES = {ONE: None, TWO: 50.0, THREE: None}


def the_streets() -> File:
    return File(
        "high-streets",
        high_streets.SOURCE,
        Use.SCORING,
        high_streets.FILE,
        streets.EDITION,
        streets.AS_AT,
        streets.streets_gpkg(),
    )


def listed(file: File) -> str:
    return "\n".join(
        [
            "",
            "[[file]]",
            f'item = "{file.item}"',
            f'source_id = "{file.source_id}"',
            f'use = "{file.use}"',
            'what = "Made up for a test"',
            'format = "other"',
            f'page = "{PAGE}"',
            f'url = "{file.url}"',
            "max_bytes = 10_000_000",
            f'edition = "{file.edition}"',
            f'data_period = {{ as_at = "{file.period}" }}',
            "",
        ]
    )


def with_high_streets(folder: Path, **how: Any) -> Made:
    """The made-up build, with the file of high streets named in its list and in its store."""
    build = made(folder, **how)
    build.keep(the_streets())
    with (folder / "made-up.toml").open("a", encoding="utf-8") as the_list:
        the_list.write(listed(the_streets()))
    return build


def read(path: Path) -> Any:
    return json.loads(path.read_bytes())


def said_of(said: list[str], status: str) -> dict[str, list[str]]:
    """What each line of `derive` with one status says, by the measure it is of."""
    lines = [line.split() for line in said if f" status={status} " in line]
    return {line[2].removeprefix("feature="): line[3:] for line in lines if "feature=" in line[2]}


@pytest.fixture(scope="module")
def build(tmp_path_factory: pytest.TempPathFactory) -> tuple[Made, list[str], str]:
    found = with_high_streets(tmp_path_factory.mktemp("built"))
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        assert found.run() == 0
    return found, out.getvalue().splitlines(), err.getvalue()


def test_the_build_works_the_measure_out_and_carries_it(build: tuple[Made, list[str], str]):
    _, said, words = build
    assert all(is_public(line) for line in said)
    assert said_of(said, "ok")[FEATURE] == [
        f"source={high_streets.SOURCE}",
        "areas=3",
        "values=1",
        "files=6",
    ]
    assert FEATURE not in said_of(said, "skipped")
    assert f"{FEATURE} is left out of the release" not in words
    assert " findings=0 " in said[-2]
    # No name of a high street is read, so none can be printed.
    assert streets.CANARY not in "".join(said) + words


def test_its_row_of_the_catalogue_is_what_core_says(build: tuple[Made, list[str], str]):
    found, _, _ = build
    (measure,) = [one for one in MEASURES if one.feature is FEATURE]
    assert (measure.held_back, measure.waits_on) == ((), ())
    release = read_release(found.release)
    (metric,) = [one for one in release.metrics if one.feature_id == FEATURE]
    core = FEATURES[FEATURE]
    assert (metric.label, metric.short_label, metric.unit) == (core.label, core.short_label, "%")
    assert (metric.rankable, metric.in_likeness) == (True, False)
    # The day the conservation areas are of, as conservation cover gives it.
    (cover,) = [one for one in release.metrics if one.feature_id == conservation_cover.FEATURE]
    assert metric.vintage == cover.vintage
    assert set(metric.source_ids) >= {high_streets.SOURCE, conservation_cover.SOURCE}
    for area, figure in FIGURES.items():
        held = release.feature(area, FEATURE)
        assert (None if held is None else held.value) == figure


def test_an_area_with_too_few_homes_near_a_high_street_has_no_figure_and_never_nought(
    build: tuple[Made, list[str], str],
):
    found, _, _ = build
    evidence = Evidence.model_validate_json((found.beside / "evidence.json").read_bytes())
    behind = {the_streets().receipt().file_id, files()["conservation-areas"].receipt().file_id}
    for area, figure in FIGURES.items():
        row = evidence.row(f"{area}/feature/{FEATURE}")
        assert row is not None and behind <= set(row.inputs) and len(row.inputs) == 6
        assert row.derivation_id == highstreet_conserved.METHOD.derivation_id
        assert (row.state, row.value) == (
            (State.BELOW_THRESHOLD, None) if figure is None else (State.PARTIAL, figure)
        )


def test_the_build_lists_the_measure_as_carried_and_says_what_it_cannot_see(
    build: tuple[Made, list[str], str],
):
    found, _, _ = build
    record = read(found.beside / "build.json")
    assert FEATURE not in {one["feature_id"] for one in record["measures_left_out"]}
    (carried,) = [one for one in record["measures_carried"] if one["feature_id"] == FEATURE]
    assert carried["cannot_see"] == list(highstreet_conserved.CANNOT_SEE)
    assert "trunk road" in carried["cannot_see"][0]


def test_the_lock_names_the_file_which_the_build_read(build: tuple[Made, list[str], str]):
    found, _, _ = build
    assert read_lock(found.beside / "lock.json").holds(the_streets().receipt().file_id)


def test_no_likeness_between_areas_counts_it(build: tuple[Made, list[str], str], tmp_path: Path):
    """The areas most like an area are those they were before the measure was carried."""
    found, _, _ = build
    without = made(tmp_path)
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        assert without.run() == 0
    before, after = read_release(without.release), read_release(found.release)
    assert FEATURE not in {metric.feature_id for metric in before.metrics}
    for area in FIGURES:
        assert similar(after, area) == similar(before, area)


def test_a_build_that_names_no_file_of_high_streets_leaves_the_measure_out_for_that(
    tmp_path: Path, capsys: Printed
):
    found = made(tmp_path)
    assert found.run() == 0
    said = capsys.readouterr().out.splitlines()
    assert said_of(said, "skipped")[FEATURE] == [f"source={high_streets.SOURCE}", f"{NO_RECEIPT}=1"]
    release = read_release(found.release)
    assert FEATURE not in {metric.feature_id for metric in release.metrics}


def test_a_build_with_no_receipt_of_the_conservation_areas_leaves_the_measure_out(
    tmp_path: Path, capsys: Printed
):
    """A share is of the land inside a conservation area. With no file of them, none is made."""
    found = with_high_streets(tmp_path, without_a_receipt=["conservation-areas"])
    assert found.run() == 0
    said = capsys.readouterr().out.splitlines()
    assert said_of(said, "skipped")[FEATURE] == [f"source={high_streets.SOURCE}", f"{NO_RECEIPT}=1"]
    release = read_release(found.release)
    carried = {metric.feature_id for metric in release.metrics}
    assert not carried & {FEATURE, conservation_cover.FEATURE}


# Village feel, which is made of it


def test_village_feel_is_placed_where_the_high_street_has_a_figure_and_nowhere_else(
    build: tuple[Made, list[str], str],
):
    """The other three parts are 55 in 100 of it, which is under what a band needs."""
    found, _, _ = build
    release = read_release(found.release)
    (village,) = [vibe for vibe in release.vibes if vibe.tag_id is TagId.VILLAGE_FEEL]
    assert village == TAGS[TagId.VILLAGE_FEEL] and village.sureness is Sureness.ROUGH_GUIDE
    rows = {tag.area_id: tag for tag in release.tags if tag.tag_id is TagId.VILLAGE_FEEL}
    assert {area: (tag.coverage, tag.band is None) for area, tag in rows.items()} == {
        ONE: (0.55, True),
        TWO: (1.0, False),
        THREE: (0.55, True),
    }
    assert release.placed(TagId.VILLAGE_FEEL)


def test_a_build_with_no_file_of_high_streets_places_no_area_on_village_feel(tmp_path: Path):
    found = made(tmp_path)
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        assert found.run() == 0
    release = read_release(found.release)
    rows = [tag for tag in release.tags if tag.tag_id is TagId.VILLAGE_FEEL]
    assert {(tag.coverage, tag.raw, tag.band) for tag in rows} == {(0.55, None, None)}
    assert release.placed(TagId.VILLAGE_FEEL) is False


def test_no_rule_holds_village_feel_off_and_its_own_shares_do():
    """It was held off by name until 2026-09-25. Its high street is 45 in 100 of it, so no
    area has 60 in 100 without one, and nothing else need hold it off."""
    assert TagId.VILLAGE_FEEL not in PLACED_ONLY_WITH
    areas = ("lon-n0001", "lon-n0002", "lon-n0003")
    rest = (FeatureId.HOMES_DENSITY, FeatureId.HOMES_PRE1919, FeatureId.CONSERVATION_COVER)
    features = [
        FeatureValue(
            area_id=area, feature_id=feature, value=value, percentile=percentile, coverage=1.0
        )
        for feature in rest
        for area, value, percentile in zip(areas, (1.0, 2.0, 3.0), (16.7, 50.0, 83.3), strict=True)
    ]
    rows = release_rows.tags_of(features, areas, [TAGS[TagId.VILLAGE_FEEL]])
    assert [row.coverage for row in rows] == [0.55, 0.55, 0.55]
    assert {(row.raw, row.score, row.band) for row in rows} == {(None, None, None)}
    street = [
        FeatureValue(
            area_id=area,
            feature_id=FeatureId.HIGHSTREET_CONSERVED,
            value=value,
            percentile=percentile,
            coverage=1.0,
        )
        for area, value, percentile in zip(areas, (1.0, 2.0, 3.0), (16.7, 50.0, 83.3), strict=True)
    ]
    with_it = release_rows.tags_of([*features, *street], areas, [TAGS[TagId.VILLAGE_FEEL]])
    assert [row.coverage for row in with_it] == [1.0, 1.0, 1.0]
    assert all(row.band is not None for row in with_it)
