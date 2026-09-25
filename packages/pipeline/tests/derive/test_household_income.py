"""Household income, read to be shown and never ranked on, from a made-up workbook.

Every figure here is made up: the workbook of `income_support.py`.

    MSOA        area             estimate   lower    upper
    E02999001   Quillhaven 001   52307      46113    59311
    E02999002   Quillhaven 002   41009      38001    44017
    E02999003   Tallowgate 001   no figure
"""

import ast
from pathlib import Path

import burro_pipeline
import pytest
from burro_core.catalogue import FEATURES, TAGS
from burro_core.ids import FeatureId, Segment, TagId
from burro_core.income import ONS, AreaIncome
from burro_pipeline.cells import spine
from burro_pipeline.derive import household_income, measures
from burro_pipeline.derive.household_income import Estimated
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.receipt import Period
from burro_pipeline.registry import RegistryError
from burro_pipeline.registry.model import INTERNAL_USES, Use

from ..cells.support import CANARY, registry
from .income_support import (
    COLUMNS,
    DISTRICTS,
    FIGURES,
    METADATA,
    NOTES,
    Q1,
    SOURCE,
    T1,
    TERMS,
    Held,
    book,
    inputs_of,
)

A1, A2, A3 = "lon-ne02999001", "lon-ne02999002", "lon-ne02999003"
SRC = Path(burro_pipeline.__file__).parent
# Figures that stand in a column or a row that is never read.
NEVER_READ = ("987654321", "77777", "70007", "80008")


def built(folder: Path, content: bytes | None = None) -> Estimated:
    inputs = inputs_of(folder, content)
    return household_income.build(inputs, spine.build(inputs))


def refusal(folder: Path, content: bytes, period: Period | None = None) -> str:
    inputs = inputs_of(folder, content, period=period)
    with pytest.raises(LockError) as refused:
        household_income.build(inputs, spine.build(inputs))
    assert refused.value.rule == "input_is_as_described"
    said = str(refused.value)
    assert CANARY not in said
    assert not [figure for held in FIGURES.values() for figure in held if str(figure) in said]
    return said


# What it is, and what it may be put to


def test_the_registry_holds_it_to_be_shown_and_checked_against_and_never_ranked_on():
    assert household_income.USE is Use.DISPLAY
    entry = registry().require(SOURCE, Use.DISPLAY)
    assert set(entry.uses) == {Use.DISPLAY, Use.VALIDATION_ONLY}
    registry().require(SOURCE, Use.VALIDATION_ONLY)
    for never in (Use.SCORING, Use.PROFILE_TEXT, Use.GAZETTEER, Use.CELLS, Use.ROUTING):
        with pytest.raises(RegistryError):
            registry().require(SOURCE, never)
    assert Use.DISPLAY not in INTERNAL_USES


def test_no_step_can_open_the_workbook_to_rank_on_it(tmp_path: Path):
    inputs = inputs_of(tmp_path)
    with pytest.raises((RegistryError, LockError)):
        inputs.open(SOURCE, Use.SCORING, named=household_income.is_the_workbook)
    assert not inputs.opened


def test_it_is_no_measure_no_vibe_and_no_cost():
    """It is on no list of measures, and core holds no name that could carry it."""
    assert SOURCE not in {measure.source for measure in measures.MEASURES}
    for vocabulary in (FeatureId, TagId, Segment):
        assert not [each for each in vocabulary if "income" in each.value]
    assert not [feature for feature in FEATURES.values() if "income" in feature.label.lower()]
    assert not [tag for tag in TAGS.values() if "income" in tag.label.lower()]


def test_no_other_module_of_the_pipeline_names_the_source():
    """One module opens the workbook, and it opens it to be shown."""
    named = sorted(
        path.relative_to(SRC).as_posix()
        for path in SRC.rglob("*.py")
        if SOURCE in path.read_text(encoding="utf-8")
    )
    assert named == ["derive/household_income.py"]


def test_the_module_works_out_no_place_in_any_order():
    """It imports nothing that ranks, bands or compares, and defines nothing that could."""
    tree = ast.parse((SRC / "derive" / "household_income.py").read_text(encoding="utf-8"))
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    assert not imported & {"percentile_of", "band_of", "catalogue_row", "row_of", "Worked"}
    defined = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    assert not [name for name in defined if "rank" in name or "percentile" in name]


# The figures


def test_the_figure_of_an_area_is_the_publishers_own_row_with_both_its_limits(tmp_path: Path):
    found = built(tmp_path)
    assert found.areas == (A1, A2, A3)
    assert {area: (held.estimate, held.lower, held.upper) for area, held in found.of.items()} == {
        A1: (52_307, 46_113, 59_311),
        A2: (41_009, 38_001, 44_017),
    }
    # The publisher gives none for the third, and nothing stands in for it.
    assert A3 not in found.of and found.given == 2
    assert found.rows == 4


def test_nothing_prints_a_figure_by_accident(tmp_path: Path):
    found = built(tmp_path)
    for said in (repr(found.of[A1]), repr(found), str(found.of)):
        assert "52307" not in said and "46113" not in said


def test_no_column_and_no_row_is_read_but_those_of_the_figures_of_the_build(tmp_path: Path):
    found = built(tmp_path)
    held = "".join(
        str(figure) for one in found.of.values() for figure in (one.estimate, one.lower, one.upper)
    )
    assert not [never for never in NEVER_READ if never in held]


def test_what_is_written_holds_every_area_and_the_source_as_the_registry_gives_it(
    tmp_path: Path,
):
    inputs = inputs_of(tmp_path)
    found = household_income.build(inputs, spine.build(inputs))
    income = household_income.income_of("lon-2026-09-25-01", found, registry())
    assert income.synthetic is False and (income.start, income.end) == ("2022-04", "2023-03")
    assert income.areas == (
        AreaIncome(area_id=A1, estimate=52_307, lower=46_113, upper=59_311),
        AreaIncome(area_id=A2, estimate=41_009, lower=38_001, upper=44_017),
        AreaIncome(area_id=A3, estimate=None, lower=None, upper=None),
    )
    entry = registry().require(SOURCE, Use.DISPLAY)
    assert income.source.source_id == SOURCE and income.source.publisher == entry.publisher
    assert income.source.attribution == entry.attribution and income.source.url == entry.url
    assert income.source.retrieved_on == found.receipt.retrieved_at[:10]


# The workbook is held to the words the page says of it


def test_the_words_of_the_page_are_words_the_workbook_is_held_to():
    """What core quotes of the publisher is what a build finds in the workbook, or it stops."""
    assert household_income.SAID_OF_THE_KIND in ONS.definition
    assert ONS.kind in household_income.SAID_OF_THE_KIND
    assert "model-based small area income estimates" in household_income.SAID_OF_THE_MODEL
    assert "model-based small area income estimates" in ONS.modelled
    assert household_income.SAID_OF_THE_CREDIT in ONS.source_line


@pytest.mark.parametrize(
    ("content", "words"),
    [
        (book(notes=NOTES[1:]), "its notes do not give the year its receipt gives"),
        (book(notes=NOTES[:1]), "its notes do not say its codes are of the census of 2021"),
        (book(metadata=METADATA[1:]), "it does not say the estimates are from a model"),
        (book(metadata=METADATA[:2]), "it does not define the kind of income that is read"),
        (book(terms=TERMS[:1]), "it does not ask for the credit that is given"),
    ],
    ids=["year", "codes", "model", "kind", "credit"],
)
def test_a_workbook_that_does_not_say_what_the_page_says_stops_the_build(
    tmp_path: Path, content: bytes, words: str
):
    assert words in refusal(tmp_path, content)


def test_a_workbook_of_another_year_than_its_receipt_stops_the_build(tmp_path: Path):
    other = Period(start="2019-04", end="2020-03")
    assert "its notes do not give the year" in refusal(tmp_path, book(), other)
    whole_year = Period(start="2022-01", end="2022-12")
    assert "its receipt is not of a financial year" in refusal(tmp_path, book(), whole_year)


@pytest.mark.parametrize(
    "sheet", ["Notes", "Metadata", "Terms and Conditions", "Total annual income"]
)
def test_a_sheet_that_is_missing_stops_the_build(tmp_path: Path, sheet: str):
    refusal(tmp_path, book(without=[sheet]))


def test_a_column_that_is_missing_is_named_by_the_name_the_step_asked_for(tmp_path: Path):
    without = [name for name in COLUMNS if name != "Lower confidence limit (£)"]
    said = refusal(tmp_path, book(columns=without))
    assert "the column Lower confidence limit (£) is missing" in said


def changed(code: str, held: Held) -> dict[str, Held]:
    return {**FIGURES, code: held}


@pytest.mark.parametrize(
    ("held", "words"),
    [
        ((52_307, 46_113, None), "an estimate stands without both its limits"),
        ((None, 46_113, 59_311), "an estimate stands without both its limits"),
        ((52_307, 53_000, 59_311), "an estimate does not stand between its limits"),
        ((52_307, 46_113, 50_000), "an estimate does not stand between its limits"),
        ((52_307.5, 46_113, 59_311), "a figure is not a figure"),
        ((-1, -2, 5), "a figure is not a figure"),
        (("[x]", 46_113, 59_311), "a figure is not a figure"),
    ],
)
def test_a_row_that_is_no_estimate_between_its_limits_stops_the_build(
    tmp_path: Path, held: Held, words: str
):
    assert words in refusal(tmp_path, book(changed(Q1, held)))


def test_an_area_with_no_row_or_a_row_in_another_borough_stops_the_build(tmp_path: Path):
    without = {code: held for code, held in FIGURES.items() if code != T1}
    assert "an MSOA of the census of 2021 has no row" in refusal(tmp_path, book(without))
    elsewhere = {**DISTRICTS, Q1: "E09000902"}
    said = refusal(tmp_path / "b", book(districts=elsewhere))
    assert "an MSOA is in another borough than the lookup gives" in said
