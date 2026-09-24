"""The list of the two census tables that may feed a score, held to the registry as it stands.

Nothing is fetched and no socket is opened. The list names two files and no
other: the table of age by five-year bands and the table of household
composition. No file of any other table about residents is in any list.
"""

from pathlib import Path

import pytest
from burro_pipeline.fetch.gate import Reason, Refused, ask, hold_what_arrived, part_of
from burro_pipeline.fetch.sources import LISTS, load_list
from burro_pipeline.fetch.store import Part
from burro_pipeline.registry import Registry, Source, Use, load
from burro_pipeline.registry.model import HOUSING_TABLES, SCORED_TABLES
from burro_pipeline.registry.rules import census_tables_read_one_way

REPOSITORY = Path(__file__).parents[4]
REGISTRY = REPOSITORY / "registry" / "sources"
NAME = "m11-age-and-households"
SOURCE = "ons-census-2021-age-and-household-tables"
NEVER_SCORED = "ons-census-2021-resident-tables"


def test_the_list_holds_the_two_tables_and_no_other():
    files = load_list(NAME).files
    assert [(file.item, file.source_id, file.use) for file in files] == [
        ("census-ts007a", SOURCE, Use.SCORING),
        ("census-ts003", SOURCE, Use.SCORING),
    ]
    named = set[str]()
    for file in files:
        named |= census_tables_read_one_way(f"{file.item} {file.what} {file.edition} {file.url}")
    assert named == SCORED_TABLES


def test_every_file_of_it_passes_the_gate_and_is_for_the_store_of_the_product():
    registry = load(REGISTRY)
    for file in load_list(NAME).files:
        source = ask(file, registry)
        assert source.id == SOURCE
        assert part_of(file.use, source) is Part.PRODUCT


def test_every_page_and_address_of_it_is_one_the_registry_entry_holds():
    source = load(REGISTRY).get(SOURCE)
    for file in load_list(NAME).files:
        assert file.page in {source.url, *source.evidence_urls}, file.item
        assert file.url in source.file_urls, file.item


def test_it_says_what_nobody_has_checked_and_states_the_day_of_the_census():
    for file in load_list(NAME).files:
        assert set(file.unsure) == {"url", "max_bytes"}
        assert file.data_period is not None and file.data_period.as_at == "2021-03-21"


def test_the_same_files_are_refused_under_the_entry_that_is_never_scored():
    """The address of a file is of one entry. The entry that is shown alone names none."""
    registry = load(REGISTRY)
    for file in load_list(NAME).files:
        for use in (Use.SCORING, Use.CENSUS_TABLE):
            moved = file.model_copy(update={"source_id": NEVER_SCORED, "use": use})
            try:
                ask(moved, registry)
            except Refused as refused:
                assert refused.reason is Reason.GATE
            else:
                raise AssertionError("a file was let through under the entry that is shown alone")


def test_no_list_names_a_file_of_any_other_table_about_residents():
    """Age by single year, TS007, is no table of any list: the bands of five years are."""
    allowed = SCORED_TABLES | HOUSING_TABLES
    for path in sorted(LISTS.glob("*.toml")):
        for file in load_list(path.stem).files:
            named = census_tables_read_one_way(f"{file.item} {file.what} {file.edition} {file.url}")
            assert named <= allowed, (path.stem, file.item)
            if named & SCORED_TABLES:
                assert file.source_id == SOURCE, (path.stem, file.item)


# Another table, under the entry that may be scored

BULK = "https://www.nomisweb.co.uk/output/census/2021"
OTHERS = ("ts021", "ts030", "ts004", "ts007", "ts024", "ts038", "ts077")


def _naming(*addresses: str) -> Registry:
    """The registry as it would stand if the entry named more addresses. It breaks a rule."""
    real = load(REGISTRY)
    entry = real.get(SOURCE)
    wider = entry.model_dump() | {"file_urls": [*entry.file_urls, *addresses]}
    changed = Source.model_validate(wider)
    return Registry(tuple(changed if source.id == SOURCE else source for source in real))


@pytest.mark.parametrize("other", OTHERS)
def test_the_address_of_another_table_is_refused_under_the_entry_that_is_scored(other: str):
    """A list that names the allowed source and the address of a table that is not."""
    address = f"{BULK}/census2021-{other}.zip"
    for file in load_list(NAME).files:
        moved = file.model_copy(update={"url": address})
        with pytest.raises(Refused) as refused:
            ask(moved, load(REGISTRY))
        assert refused.value.reason in (Reason.NOT_THE_ADDRESS, Reason.RESIDENT_TABLE)
        # Where a registry names the address, against its own rule, the fence keeps the
        # whole entry apart: no file of it is for the store of the product.
        with pytest.raises(Refused) as refused:
            ask(moved, _naming(address))
        assert refused.value.reason is Reason.NOT_THE_STORE
        with pytest.raises(Refused) as refused:
            ask(file, _naming(address))
        assert refused.value.reason is Reason.NOT_THE_STORE


@pytest.mark.parametrize(
    "changed",
    [
        {"item": "census-ts021"},
        {"what": "Census 2021 table TS021, ethnic group"},
        {"edition": "Census 2021 TS030"},
        {"what": "Census 2021 table TS007, age by single year"},
    ],
    ids=lambda changed: next(iter(changed)),
)
def test_a_file_of_it_that_is_said_to_be_another_table_is_refused(changed: dict[str, str]):
    for file in load_list(NAME).files:
        with pytest.raises(Refused) as refused:
            ask(file.model_copy(update=changed), load(REGISTRY))
        assert refused.value.reason is Reason.RESIDENT_TABLE


def test_what_arrives_for_it_holds_its_own_table_and_no_other():
    source = load(REGISTRY).get(SOURCE)
    for code in ("ts003", "ts007a"):
        hold_what_arrived(
            source,
            f"{BULK}/census2021-{code}.zip",
            f"census2021-{code}.zip",
            f"census2021-{code}-msoa.csv",
            f"census2021-{code}-oa.csv",
            f"metadata/{code}-2021-1.txt",
        )
    for named in (
        "census2021-ts021-msoa.csv",
        "census2021-ts007-msoa.csv",
        "TS030 religion.xlsx",
        "t%53004.csv",
        "TS_021_oa.csv",
    ):
        with pytest.raises(Refused) as refused:
            hold_what_arrived(source, f"{BULK}/census2021-ts003.zip", "census2021-ts003.zip", named)
        assert refused.value.reason is Reason.RESIDENT_TABLE
