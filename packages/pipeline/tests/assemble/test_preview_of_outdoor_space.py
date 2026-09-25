"""The step `preview` on a build whose list names the workbook of private outdoor space.

The town is Quillhaven and Tallowgate, which do not exist, and every count is
made up. The workbook and the lookup between the areas of two censuses are
those of the tests of the measure, each laid out as its publisher lays out its
own.

The measure is on the table of measures, and nothing holds it back. It was held
back for want of a row of the proxy audit until 2026-09-25, when the founder
dropped the audit (ADR 0006, as amended that day). So a build that holds its
files works it out and carries it, and Houses or flats rests on its whole
recipe wherever an area has a figure. A build that holds no file of it leaves
it out for that, and Houses or flats rests on 75 in 100 as it did.
"""

import io
import json
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any

import pytest
from burro_core.catalogue import TAGS
from burro_core.ids import FeatureId, TagId
from burro_pipeline.derive import areas_of_2011
from burro_pipeline.derive import private_outdoor_space as outdoor
from burro_pipeline.derive.measures import MEASURES, says_what_core_says
from burro_pipeline.evidence.lock import read_lock
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.registry.model import Use
from burro_pipeline.release.read import read_release
from public_log import is_public

from ..derive import areas_of_2011_support as lookup_support
from ..derive import test_private_outdoor_space as workbook_support
from .support import ONE, PAGE, THREE, TWO, File, Made, made

Printed = pytest.CaptureFixture[str]
FEATURE = FeatureId.PRIVATE_OUTDOOR_SPACE
HELD_BACK, NO_RECEIPT = "measure_is_not_held_back", "input_has_one_receipt"
# Every count of the made-up workbook, as a run of digits. None may be printed.
COUNTS = ("500", "400", "300", "100", "200", "150")
# What the made-up workbook gives: a share for the two areas that kept their outline, and
# none for the third, which was made by joining two areas of 2011.
FIGURES = {ONE: 80.0, TWO: 33.3, THREE: None}


def workbook() -> File:
    return File(
        "outdoor-space",
        outdoor.SOURCE,
        Use.SCORING,
        outdoor.FILE_NAME,
        outdoor.EDITION,
        "2020-04",
        workbook_support.made_up(),
    )


def lookup() -> File:
    """The lookup, fetched for `cells` as its list states, and read for `scoring`."""
    return File(
        "areas-of-2011",
        areas_of_2011.SOURCE,
        Use.CELLS,
        lookup_support.NAME,
        areas_of_2011.EDITION,
        "2022-12",
        lookup_support.lookup_csv(),
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


def with_outdoor_space(folder: Path, *, lookup_has_a_receipt: bool = True) -> Made:
    """The made-up build, with the workbook and the lookup named in its list and in its store."""
    build = made(folder)
    build.keep(workbook())
    build.keep(lookup(), receipt=lookup_has_a_receipt)
    with (folder / "made-up.toml").open("a", encoding="utf-8") as the_list:
        the_list.write(listed(workbook()) + listed(lookup()))
    return build


def read(path: Path) -> Any:
    return json.loads(path.read_bytes())


def said_of(said: list[str], status: str) -> dict[str, list[str]]:
    """What each line of `derive` with one status says, by the measure it is of."""
    lines = [line.split() for line in said if f" status={status} " in line]
    return {line[2].removeprefix("feature="): line[3:] for line in lines if "feature=" in line[2]}


@pytest.fixture(scope="module")
def build(tmp_path_factory: pytest.TempPathFactory) -> tuple[Made, list[str], str]:
    found = with_outdoor_space(tmp_path_factory.mktemp("built"))
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        assert found.run() == 0
    return found, out.getvalue().splitlines(), err.getvalue()


def test_the_build_works_the_measure_out_and_carries_it(build: tuple[Made, list[str], str]):
    _, said, words = build
    assert all(is_public(line) for line in said)
    assert FEATURE in said_of(said, "ok")
    assert FEATURE not in said_of(said, "skipped")
    assert f"{FEATURE} is left out of the release" not in words
    assert " findings=0 " in said[-2]
    assert not [count for count in COUNTS if any(f"={count} " in f"{line} " for line in said)]


def test_nothing_holds_the_measure_back_and_its_row_is_what_core_says(
    build: tuple[Made, list[str], str],
):
    """Core names it as it is built, and no check holds it, so the release carries it."""
    found, _, _ = build
    (measure,) = [one for one in MEASURES if one.feature is FEATURE]
    assert (measure.held_back, measure.waits_on) == ((), ())
    behind = [workbook().receipt(), lookup().receipt()]
    assert says_what_core_says(outdoor.metric_of(behind, "2020-04"))
    release = read_release(found.release)
    (metric,) = [one for one in release.metrics if one.feature_id == FEATURE]
    assert (metric.label, metric.unit, metric.vintage) == (outdoor.LABEL, "%", "2020-04")
    assert metric.rankable
    for area, figure in FIGURES.items():
        held = release.feature(area, FEATURE)
        assert (None if held is None else held.value) == figure


def test_houses_or_flats_rests_on_its_whole_recipe_where_an_area_has_a_figure(
    build: tuple[Made, list[str], str],
):
    """The measure is 25 in 100 of the recipe. An area with no figure for it rests on the
    other 75, and has a band all the same: nothing is filled in for it."""
    found, _, _ = build
    assert {term.feature_id: term.hundredths for term in TAGS[TagId.HOMES].terms}[FEATURE] == 25
    release = read_release(found.release)
    homes = {tag.area_id: tag for tag in release.tags if tag.tag_id is TagId.HOMES}
    assert {area: tag.coverage for area, tag in homes.items()} == {ONE: 1.0, TWO: 1.0, THREE: 0.75}
    assert all(tag.band is not None for tag in homes.values())


def test_the_build_lists_the_measure_as_carried_and_says_what_it_cannot_see(
    build: tuple[Made, list[str], str],
):
    found, _, _ = build
    record = read(found.beside / "build.json")
    assert FEATURE not in {one["feature_id"] for one in record["measures_left_out"]}
    (carried,) = [one for one in record["measures_carried"] if one["feature_id"] == FEATURE]
    assert carried["cannot_see"] == list(outdoor.CANNOT_SEE)
    report = (found.beside / "coverage.md").read_text(encoding="utf-8")
    section = report.split("## Worked out and left out")[1].split("## Gaps")[0]
    assert f"| feature/{FEATURE} |" not in section
    assert HELD_BACK not in section


def test_a_row_of_evidence_rests_on_the_workbook_and_both_lookups(
    build: tuple[Made, list[str], str],
):
    """An area with a figure has a row that holds it. The area that was made by joining two
    has a row that says its source holds none, and no figure."""
    found, _, _ = build
    evidence = Evidence.model_validate_json((found.beside / "evidence.json").read_bytes())
    behind = {workbook().receipt().file_id, lookup().receipt().file_id}
    for area, figure in FIGURES.items():
        row = evidence.row(f"{area}/feature/{FEATURE}")
        assert row is not None and behind <= set(row.inputs) and len(row.inputs) == 3
        assert (row.state, row.value) == (
            (State.SOURCE_GAP, None) if figure is None else (State.PRESENT, figure)
        )


def test_the_lock_names_both_files_which_the_build_read(build: tuple[Made, list[str], str]):
    found, _, _ = build
    lock = read_lock(found.beside / "lock.json")
    assert lock.holds(workbook().receipt().file_id)
    assert lock.holds(lookup().receipt().file_id)


def test_a_build_with_no_receipt_of_the_lookup_makes_no_figure_and_goes_on(
    tmp_path: Path, capsys: Printed
):
    """A figure is held to the lookup or is not made. The build leaves the measure out."""
    found = with_outdoor_space(tmp_path, lookup_has_a_receipt=False)
    assert found.run() == 0
    said = capsys.readouterr().out.splitlines()
    assert said_of(said, "skipped")[FEATURE] == [f"source={outdoor.SOURCE}", f"{NO_RECEIPT}=1"]
    release = read_release(found.release)
    assert FEATURE not in {metric.feature_id for metric in release.metrics}
    assert {tag.coverage for tag in release.tags if tag.tag_id is TagId.HOMES} == {0.75}


def test_a_build_that_names_neither_file_leaves_the_measure_out_for_that(
    tmp_path: Path, capsys: Printed
):
    found = made(tmp_path)
    assert found.run() == 0
    said = capsys.readouterr().out.splitlines()
    assert said_of(said, "skipped")[FEATURE] == [f"source={outdoor.SOURCE}", f"{NO_RECEIPT}=1"]
    release = read_release(found.release)
    assert {tag.coverage for tag in release.tags if tag.tag_id is TagId.HOMES} == {0.75}
