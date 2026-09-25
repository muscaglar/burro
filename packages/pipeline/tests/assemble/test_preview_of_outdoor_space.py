"""The step `preview` on a build whose list names the workbook of private outdoor space.

The town is Quillhaven and Tallowgate, which do not exist, and every count is
made up. The workbook and the lookup between the areas of two censuses are
those of the tests of the measure, each laid out as its publisher lays out its
own.

The measure is on the table of measures and is held back: its row of the proxy
audit is not written. So a build that holds its files works it out, leaves it
out and says why, and Houses or flats rests on 75 in 100 of its recipe as it
did. A build that holds no file of it leaves it out for that.
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


def skipped(said: list[str]) -> dict[str, list[str]]:
    lines = [line.split() for line in said if " status=skipped " in line]
    return {line[2].removeprefix("feature="): line[3:] for line in lines}


@pytest.fixture(scope="module")
def build(tmp_path_factory: pytest.TempPathFactory) -> tuple[Made, list[str], str]:
    found = with_outdoor_space(tmp_path_factory.mktemp("built"))
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        assert found.run() == 0
    return found, out.getvalue().splitlines(), err.getvalue()


def test_the_build_works_the_measure_out_and_leaves_it_out_by_the_name_of_the_rule(
    build: tuple[Made, list[str], str],
):
    _, said, words = build
    assert all(is_public(line) for line in said)
    assert skipped(said)[FEATURE] == [f"source={outdoor.SOURCE}", f"{HELD_BACK}=1"]
    assert f"{FEATURE} is left out of the release" in words
    assert not [count for count in COUNTS if any(f"={count} " in f"{line} " for line in said)]


def test_the_release_does_not_carry_it_though_core_names_it_as_it_is_built(
    build: tuple[Made, list[str], str],
):
    """Nothing but the hold keeps it out: its row of the catalogue is what core says."""
    found, _, _ = build
    (measure,) = [one for one in MEASURES if one.feature is FEATURE]
    assert measure.held_back == outdoor.HELD_BACK and measure.waits_on == ()
    behind = [workbook().receipt(), lookup().receipt()]
    assert says_what_core_says(outdoor.metric_of(behind, "2020-04"))
    release = read_release(found.release)
    assert FEATURE not in {metric.feature_id for metric in release.metrics}
    assert all(release.feature(area, FEATURE) is None for area in (ONE, TWO, THREE))


def test_houses_or_flats_rests_on_what_it_rested_on(build: tuple[Made, list[str], str]):
    """The measure is 25 in 100 of the recipe, and no part of any band until it is carried."""
    found, _, _ = build
    assert {term.feature_id: term.hundredths for term in TAGS[TagId.HOMES].terms}[FEATURE] == 25
    release = read_release(found.release)
    homes = [tag for tag in release.tags if tag.tag_id is TagId.HOMES]
    assert len(homes) == 3
    assert {tag.coverage for tag in homes} == {0.75}
    assert all(tag.band is not None for tag in homes)


def test_the_build_says_what_the_measure_waits_on_and_whose_it_is_to_settle(
    build: tuple[Made, list[str], str],
):
    found, _, _ = build
    left_out = {
        one["feature_id"]: one for one in read(found.beside / "build.json")["measures_left_out"]
    }
    said = left_out[FEATURE]
    assert said["rule"] == HELD_BACK
    assert said["waits_on"] == list(outdoor.HELD_BACK)
    assert said["why"].startswith("It is held back: ")
    assert "a check that is asked for before it is served has not been made" in said["why"]
    report = (found.beside / "coverage.md").read_text(encoding="utf-8")
    section = report.split("## Worked out and left out")[1].split("## Gaps")[0]
    assert section.count(f"| feature/{FEATURE} | {HELD_BACK} | ") == 1
    assert all(line in section for line in outdoor.HELD_BACK)


def test_no_row_of_evidence_rests_on_a_file_of_a_measure_that_is_left_out(
    build: tuple[Made, list[str], str],
):
    found, _, _ = build
    evidence = Evidence.model_validate_json((found.beside / "evidence.json").read_bytes())
    for area in (ONE, TWO, THREE):
        row = evidence.row(f"{area}/feature/{FEATURE}")
        assert row is not None
        assert (row.state, row.inputs, row.value) == (State.NOT_CARRIED, (), None)


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
    assert skipped(said)[FEATURE] == [f"source={outdoor.SOURCE}", f"{NO_RECEIPT}=1"]
    assert FEATURE not in {metric.feature_id for metric in read_release(found.release).metrics}


def test_a_build_that_names_neither_file_leaves_the_measure_out_for_that(
    tmp_path: Path, capsys: Printed
):
    found = made(tmp_path)
    assert found.run() == 0
    said = capsys.readouterr().out.splitlines()
    assert skipped(said)[FEATURE] == [f"source={outdoor.SOURCE}", f"{NO_RECEIPT}=1"]
