"""The list of the one workbook of household income, held to the licence registry.

Nothing is fetched and no socket is opened. The list and the registry are the
repository's own.

The workbook says what the households of an area are estimated to have as income, so it
describes residents. The founder decided on 24 September 2026 that it is fetched, shown
on an area's page and used to check another measure, and that no area is ranked on it
(ADR 0006 keeps income out of every score). These hold the list and the entry to that.
"""

from functools import cache
from pathlib import Path

import pytest
from burro_pipeline.evidence import Period
from burro_pipeline.fetch.gate import Reason, Refused, ask, part_of
from burro_pipeline.fetch.sources import LISTS, Listed, load_list
from burro_pipeline.fetch.store import Part
from burro_pipeline.registry import Registry, RegistryError, Use, load

REGISTRY = Path(__file__).parents[4] / "registry" / "sources"
NAME = "m12-household-income"
SOURCE = "ons-income-estimates-small-areas"
# What the founder decided the workbook is for, and nothing beside.
SHOWN_AND_CHECKED = frozenset({Use.DISPLAY, Use.VALIDATION_ONLY})
# An earlier edition, as the publisher's page lists it. The entry covers the newest alone.
EARLIER = (
    "https://www.ons.gov.uk/file?uri=/employmentandlabourmarket/peopleinwork/"
    "earningsandworkinghours/datasets/"
    "smallareaincomeestimatesformiddlelayersuperoutputareasenglandandwales/"
    "financialyearending2020/saiefy1920finalqaddownload280923.xlsx"
)


@cache
def of_the_repository() -> Registry:
    """The repository's own registry, read once for all the tests here. It is frozen."""
    return load(REGISTRY)


def the_file() -> Listed:
    (file,) = load_list(NAME).files
    return file


def test_the_list_holds_the_one_workbook_and_lists_it_to_be_shown():
    file = the_file()
    assert (file.item, file.source_id, file.use) == ("income-msoa-fye-2023", SOURCE, Use.DISPLAY)


def test_the_file_passes_the_gate_and_is_for_the_store_of_the_product():
    source = ask(the_file(), of_the_repository())
    assert (source.id, source.status) == (SOURCE, "approved")
    assert part_of(the_file().use, source) is Part.PRODUCT


def test_the_page_and_the_address_are_ones_the_registry_entry_holds():
    source = of_the_repository().get(SOURCE)
    assert the_file().page == source.url
    assert source.file_urls == (the_file().url,)
    assert the_file().url_parameters == ("uri",)


def test_the_entry_lets_a_figure_be_shown_and_checked_against_and_nothing_else():
    """No area is ranked on it. A use that is not listed is refused by the gate, so a
    feature, a tag or a cost that rests on the workbook is named by the check of a release."""
    registry = of_the_repository()
    assert frozenset(registry.get(SOURCE).uses) == SHOWN_AND_CHECKED
    for use in Use:
        if use in SHOWN_AND_CHECKED:
            assert registry.require(SOURCE, use).id == SOURCE
        else:
            with pytest.raises(RegistryError, match=SOURCE):
                registry.require(SOURCE, use)


@pytest.mark.parametrize("use", sorted(set(Use) - SHOWN_AND_CHECKED))
def test_the_same_file_listed_for_any_other_use_is_refused(use: Use):
    with pytest.raises(Refused) as refused:
        ask(the_file().model_copy(update={"use": use}), of_the_repository())
    assert refused.value.reason is Reason.GATE


def test_the_entry_says_that_it_describes_residents_and_which_record_applies():
    said = " ".join(of_the_repository().get(SOURCE).conditions)
    assert "It describes residents" in said
    assert "decision record 0006" in said
    assert "no area is ranked on it" in said
    # What the publisher says its model cannot give is a condition, in its own words.
    assert "does not support the disaggregation of incomes below MSOA level" in said
    assert "A figure is a mean and never a median" in said


def test_it_states_its_edition_and_its_period_and_is_unsure_of_its_address_alone():
    file = the_file()
    assert set(file.unsure) == {"url"}
    assert file.edition == "Financial year ending 2023"
    assert file.data_period == Period(start="2022-04", end="2023-03")
    assert file.ready_for_a_receipt
    # No page writes the first month of the year, and the notes say how it was worked out.
    assert "financial year ending March 2023" in file.notes
    assert "No page that was read writes the first month" in file.notes


def test_an_earlier_edition_of_the_same_page_is_refused():
    with pytest.raises(Refused) as refused:
        ask(the_file().model_copy(update={"url": EARLIER}), of_the_repository())
    assert refused.value.reason is Reason.NOT_THE_ADDRESS


def test_it_says_when_its_address_was_read_and_through_what():
    assert "Address read on 2026-09-24" in the_file().notes
    assert "through a reader that extracts" in the_file().notes


def test_no_other_list_names_the_source_or_the_item():
    """The workbook stands in a list of its own: no file that is ranked on shares a list
    with it, and a build that does not name the list does not take it."""
    for path in sorted(LISTS.glob("*.toml")):
        if path.stem != NAME:
            for file in load_list(path.stem).files:
                assert file.source_id != SOURCE, (path.stem, file.item)
                assert file.item != the_file().item, path.stem
