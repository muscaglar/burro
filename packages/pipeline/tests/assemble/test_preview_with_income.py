"""The step `preview` on a build whose list names the workbook of household income.

The town is Quillhaven and Tallowgate, which do not exist, and every figure is
made up: the workbook of the tests of household income.

    area             estimate   lower    upper
    Quillhaven 001   52307      46113    59311
    Quillhaven 002   41009      38001    44017
    Tallowgate 001   no figure

The figures are written to a folder of their own beside the release. The
release holds nothing of them: no measure, no fact, no row of evidence.
"""

import io
import json
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from burro_core.income import INCOME, INCOME_FOLDER, MANIFEST
from burro_core.release import EVIDENCE
from burro_pipeline.derive import household_income
from burro_pipeline.evidence.receipt import Receipt
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.registry.model import Use
from burro_pipeline.release import cli as release_cli
from burro_pipeline.release.income import read_income
from burro_pipeline.release.read import read_release
from public_log import is_public

from ..derive import income_support
from ..derive.income_support import FIGURES
from .support import ONE, PAGE, RELEASE, THREE, TWO, File, Made, made

Printed = pytest.CaptureFixture[str]
ITEM = "income-msoa"
# Every figure of the made-up workbook, as it would be printed.
EVERY = sorted(
    {str(figure) for held in FIGURES.values() for figure in held if figure is not None}
    | {f"{figure:,}" for held in FIGURES.values() for figure in held if isinstance(figure, int)}
)


@dataclass(frozen=True)
class Workbook(File):
    """The made-up workbook of household income, as a file of a build."""

    def receipt(self) -> Receipt:
        made_up = income_support.receipt(self.content)
        return made_up.model_copy(update={"url": self.url})


def workbook(content: bytes | None = None) -> Workbook:
    return Workbook(
        ITEM,
        household_income.SOURCE,
        Use.DISPLAY,
        income_support.NAME,
        income_support.EDITION,
        "2022-04 to 2023-03",
        income_support.book() if content is None else content,
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
            'format = "xlsx"',
            f'page = "{PAGE}"',
            f'url = "{file.url}"',
            "max_bytes = 10_000_000",
            f'edition = "{file.edition}"',
            'data_period = { start = "2022-04", end = "2023-03" }',
            "",
        ]
    )


def with_income(folder: Path, *, receipt: bool = True, content: bytes | None = None) -> Made:
    """The made-up build, with the workbook named in its list and kept in its store."""
    build = made(folder)
    file = workbook(content)
    build.keep(file, receipt=receipt)
    with (folder / "made-up.toml").open("a", encoding="utf-8") as the_list:
        the_list.write(listed(file))
    return build


def quietly(build: Made, *more: str, out: Path | None = None) -> int:
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        return build.run(*more, out=out)


def read(path: Path) -> Any:
    return json.loads(path.read_bytes())


def shown(build: Made) -> Path:
    return build.out / f"{RELEASE}{INCOME_FOLDER}"


@pytest.fixture(scope="module")
def build(tmp_path_factory: pytest.TempPathFactory) -> Made:
    found = with_income(tmp_path_factory.mktemp("shown"))
    assert quietly(found) == 0
    return found


def test_a_build_whose_list_names_the_workbook_says_one_line_of_it(tmp_path: Path, capsys: Printed):
    assert with_income(tmp_path).run() == 0
    said = capsys.readouterr().out.splitlines()
    assert all(is_public(line) for line in said)
    [line] = [line for line in said if line.startswith("step=income ")]
    assert (
        line == f"step=income status=ok source={household_income.SOURCE} areas=3 values=2 files=1"
    )
    assert " findings=0 " in next(line for line in said if line.startswith("step=check"))


def test_what_it_prints_holds_no_figure_of_any_area(tmp_path: Path, capsys: Printed):
    assert with_income(tmp_path).run() == 0
    said = "".join(capsys.readouterr())
    assert not [figure for figure in EVERY if figure in said]


def test_the_figures_stand_in_a_folder_of_their_own_beside_the_release(build: Made):
    assert sorted(entry.name for entry in shown(build).iterdir()) == [INCOME, MANIFEST]
    found = read_income(shown(build), read_release(build.release))
    assert found.synthetic is False and found.source.source_id == household_income.SOURCE
    assert (found.start, found.end) == ("2022-04", "2023-03")
    held = {area.area_id: (area.estimate, area.lower, area.upper) for area in found.areas}
    assert held == {
        ONE: (52_307, 46_113, 59_311),
        TWO: (41_009, 38_001, 44_017),
        THREE: (None, None, None),
    }


def test_the_release_holds_nothing_of_the_figures(build: Made):
    """No measure, no cost, no fact and no row of evidence: nothing ranks on them."""
    release = read_release(build.release)
    assert not [metric for metric in release.metrics if "income" in metric.feature_id]
    assert household_income.SOURCE not in {source.source_id for source in release.manifest.sources}
    written = b"".join(entry.read_bytes() for entry in sorted(build.release.iterdir()))
    assert b"income" not in written.lower()
    assert not [figure for figure in EVERY if figure.encode() in written]
    evidence = Evidence.model_validate_json((build.beside / EVIDENCE).read_bytes())
    assert not [row for row in evidence.rows if "income" in row.fact_id]
    assert household_income.SOURCE not in {receipt.source_id for receipt in evidence.receipts}


def test_the_record_of_the_build_says_it_is_shown_and_never_ranked_on(build: Made):
    record = read(build.beside / "build.json")
    assert record["income"] == {
        "asked": True,
        "source_id": household_income.SOURCE,
        "shown_and_never_ranked_on": True,
        "areas": 3,
        "areas_with_an_estimate": 2,
        "folder": INCOME_FOLDER,
    }
    assert household_income.SOURCE not in {one["source_id"] for one in record["measures_carried"]}
    assert not [figure for figure in EVERY if figure in json.dumps(record)]


def test_the_folder_passes_the_check_of_the_command(build: Made, capsys: Printed):
    asked = ["check", str(build.release), "--income", str(shown(build))]
    assert release_cli.main(asked) == 0
    said = capsys.readouterr().out.splitlines()
    assert said[-1] == f"{RELEASE}-income: 3 areas, 2 with an estimate, real"


def test_a_build_whose_list_does_not_name_the_workbook_writes_no_figures(tmp_path: Path):
    found = made(tmp_path)
    assert quietly(found) == 0
    assert not shown(found).exists()
    assert read(found.beside / "build.json")["income"] == {"asked": False}


def test_a_workbook_with_no_receipt_is_left_out_and_no_figures_are_written(
    tmp_path: Path, capsys: Printed
):
    found = with_income(tmp_path, receipt=False)
    assert found.run() == 0
    assert f"{ITEM} of the list has no receipt" in capsys.readouterr().err
    assert not shown(found).exists()


def test_a_workbook_that_is_not_what_was_described_stops_the_build(tmp_path: Path, capsys: Printed):
    broken = income_support.book(metadata=income_support.METADATA[1:])
    found = with_income(tmp_path, content=broken)
    assert found.run() == 2
    err = capsys.readouterr().err
    assert "it does not say the estimates are from a model" in err
    assert not found.release.exists() and not shown(found).exists()
    assert not [figure for figure in EVERY if figure in err]


def test_a_folder_of_figures_that_is_there_already_stops_the_build(tmp_path: Path):
    found = with_income(tmp_path)
    shown(found).mkdir(parents=True)
    assert quietly(found) == 2
    assert not found.release.exists()
