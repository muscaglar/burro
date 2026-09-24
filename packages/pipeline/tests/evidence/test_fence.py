"""Which source about residents is part of the product, and which is kept apart.

A table about residents is kept apart from the product: it is read by the
audit, or shown as the census table, and no figure rests on it. One exception
was decided on 24 September 2026. A source whose every table is of age or of
household composition may feed a score, so a file of it is part of the product.
Nothing else about residents is, however an entry is written.

Every source here is made up but the two of the repository's own registry,
which are read as they stand. No file is opened.
"""

from pathlib import Path
from typing import Any

import pytest
from burro_pipeline.evidence import fence
from burro_pipeline.evidence.receipt import How, Period, Receipt
from burro_pipeline.evidence.record import file_id_of
from burro_pipeline.fetch.gate import part_of
from burro_pipeline.fetch.store import Part
from burro_pipeline.registry import Registry, Source, Use, load
from burro_pipeline.registry.model import SCORED_TABLES, SHOWN_TABLES

REPOSITORY = Path(__file__).parents[4]
AGE_AND_HOUSEHOLDS = "ons-census-2021-age-and-household-tables"
SHOWN_AND_NEVER_SCORED = "ons-census-2021-resident-tables"
SHA256 = "a" * 64


def about_residents(*uses: str, tables: tuple[str, ...], **changed: Any) -> Source:
    """A made-up entry about residents. It is not held to the rules: a registry may not be."""
    fields: dict[str, Any] = {
        "id": "made-up-census",
        "name": "Made-up census tables",
        "publisher": "Made-up Office",
        "url": "https://made-up.example/census",
        "dimension": "residents",
        "tables": list(tables),
        "licence": "OGL-3.0",
        "commercial_use": "yes",
        "share_alike": False,
        "attribution": "Contains made-up data.",
        "attribution_verified": True,
        "status": "approved",
        "uses": list(uses),
        "verified_how": "primary_source",
        "verified_on": "2026-09-24",
        "evidence_urls": ["https://made-up.example/licence"],
    }
    return Source.model_validate(fields | changed)


def receipt(source_id: str, use: Use) -> Receipt:
    return Receipt(
        file_id=file_id_of(SHA256),
        source_id=source_id,
        use=use,
        publisher_file="made-up.zip",
        url="https://files.made-up.example/made-up.zip",
        sha256=SHA256,
        bytes=1,
        retrieved_at="2026-09-24T09:00:00Z",
        how=How.FETCHED,
        edition="made up",
        data_period=Period(as_at="2021-03-21"),
    )


@pytest.mark.parametrize("tables", [("TS003", "TS007A"), ("TS003",), ("TS007A",)])
@pytest.mark.parametrize("uses", [("scoring",), ("scoring", "census_table")])
def test_age_and_household_composition_held_for_scoring_are_part_of_the_product(
    tables: tuple[str, ...], uses: tuple[str, ...]
):
    source = about_residents(*uses, tables=tables)
    assert not fence.source_is_kept_apart(source)
    assert part_of(Use.SCORING, source) is Part.PRODUCT
    held = Registry((source,))
    assert not fence.is_kept_apart(receipt(source.id, Use.SCORING), held)
    assert not fence.names_a_source_kept_apart(source.id, held)


def test_a_file_of_them_that_was_fetched_for_the_census_table_is_still_kept_apart():
    source = about_residents("scoring", "census_table", tables=("TS003", "TS007A"))
    assert fence.is_kept_apart(receipt(source.id, Use.CENSUS_TABLE), Registry((source,)))
    assert part_of(Use.CENSUS_TABLE, source) is Part.RESIDENTS


def test_they_are_kept_apart_while_the_registry_holds_them_for_the_census_table_alone():
    source = about_residents("census_table", tables=("TS003", "TS007A"))
    assert fence.source_is_kept_apart(source)
    for use in Use:
        assert part_of(use, source) is Part.RESIDENTS


# Over every other table an area's page may show, and some that it may not.
@pytest.mark.parametrize(
    "table", [*sorted(SHOWN_TABLES - SCORED_TABLES), "TS007", "TS024", "TS038", "TS077", "TS078"]
)
def test_no_other_table_about_residents_is_part_of_the_product_whatever_its_entry_lists(
    table: str,
):
    """What an entry lists is not enough. The rule on tables is asked too."""
    for tables in ((table,), ("TS003", "TS007A", table)):
        source = about_residents("scoring", "census_table", tables=tables)
        assert fence.source_is_kept_apart(source)
        assert part_of(Use.SCORING, source) is Part.RESIDENTS
        assert fence.is_kept_apart(receipt(source.id, Use.SCORING), Registry((source,)))


def test_a_source_about_residents_that_names_no_table_is_kept_apart():
    assert fence.source_is_kept_apart(about_residents("scoring", tables=()))


@pytest.mark.parametrize("heading", ["audit", "housing", "safety"])
def test_the_tables_of_age_are_part_of_the_product_under_no_other_heading(heading: str):
    """Under the audit they are the audit's. Under any other heading the registry refuses them."""
    source = about_residents("scoring", "audit_only", tables=("TS007A",), dimension=heading)
    assert fence.source_is_kept_apart(source)
    assert part_of(Use.SCORING, source) is Part.AUDIT


def test_the_real_entry_of_age_and_household_composition_is_part_of_the_product():
    registry = load(REPOSITORY / "registry" / "sources")
    entry = registry.get(AGE_AND_HOUSEHOLDS)
    assert set(entry.tables) == SCORED_TABLES
    assert not fence.source_is_kept_apart(entry)
    assert part_of(Use.SCORING, entry) is Part.PRODUCT
    assert not fence.is_kept_apart(receipt(entry.id, Use.SCORING), registry)


def test_the_real_entry_of_ethnic_group_religion_and_country_of_birth_is_kept_apart():
    registry = load(REPOSITORY / "registry" / "sources")
    entry = registry.get(SHOWN_AND_NEVER_SCORED)
    assert set(entry.tables) == {"TS004", "TS021", "TS030"}
    assert fence.source_is_kept_apart(entry)
    for use in Use:
        assert part_of(use, entry) is Part.RESIDENTS
        assert fence.is_kept_apart(receipt(entry.id, use), registry)


@pytest.mark.parametrize(
    "changed",
    [
        {"file_urls": ["https://files.made-up.example/census2021-ts021.zip"]},
        {"file_urls": ["https://files.made-up.example/census2021-ts007.zip"]},
        {"url": "https://made-up.example/datasets/c2021ts030"},
        {"name": "Made-up census tables, and TS004 country of birth"},
    ],
    ids=lambda changed: next(iter(changed)),
)
def test_a_source_that_names_another_table_in_an_address_is_kept_apart(changed: dict[str, Any]):
    """`tables` is what an entry says of itself. What it names elsewhere is asked too."""
    source = about_residents("scoring", "census_table", tables=("TS003", "TS007A"), **changed)
    assert fence.source_is_kept_apart(source)
    assert part_of(Use.SCORING, source) is Part.RESIDENTS
    assert fence.is_kept_apart(receipt(source.id, Use.SCORING), Registry((source,)))
