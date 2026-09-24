from datetime import date
from typing import Any

import pytest
from burro_pipeline.registry import Dimension, Severity, Source, Use, check
from burro_pipeline.registry.model import HOUSING_TABLES, SHOWN_TABLES

TODAY = date(2026, 9, 23)

APPROVED: dict[str, Any] = {
    "id": "ons-output-areas-2021",
    "name": "Output Areas (December 2021) boundaries",
    "publisher": "Office for National Statistics",
    "url": "https://geoportal.statistics.gov.uk/",
    "dimension": "geography",
    "licence": "OGL-3.0",
    "licence_url": "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
    "commercial_use": "yes",
    "share_alike": False,
    "attribution": "Source: Office for National Statistics licensed under the OGL v3.0.",
    "attribution_verified": True,
    "status": "approved",
    "uses": ["cells", "gazetteer"],
    "verified_how": "primary_source",
    "verified_on": TODAY,
    "evidence_urls": ["https://www.ons.gov.uk/methodology/geography/licences"],
}

OSM: dict[str, Any] = APPROVED | {
    "id": "osm-greater-london",
    "licence": "ODbL-1.0",
    "share_alike": True,
    "uses": ["routing", "basemap"],
}

# Census tables about residents: shown as the statistics office's own table on an
# area's page, and used for nothing else. See ADR 0014.
RESIDENTS: dict[str, Any] = APPROVED | {
    "id": "ons-census-2021-resident-tables",
    "name": "Census 2021 tables about residents",
    "url": "https://www.nomisweb.co.uk/sources/census_2021_bulk",
    "dimension": "residents",
    "tables": ["TS003", "TS021"],
    "uses": ["census_table"],
}

FEEDS_NOTHING_ELSE = "resident_sources_feed_the_census_table_and_nothing_else"
ONLY_RESIDENTS = "only_resident_sources_feed_the_census_table"
UNDER_RESIDENTS = "resident_tables_sit_under_residents_or_audit"


def source(base: dict[str, Any] = APPROVED, **changes: Any) -> Source:
    return Source.model_validate(base | changes)


def rules_broken(*sources: Source, severity: Severity = Severity.ERROR) -> set[str]:
    return {p.rule for p in check(sources, TODAY) if p.severity is severity}


def test_a_well_formed_approved_source_has_no_problems():
    assert check([source()], TODAY) == []


def test_share_alike_source_used_for_routing_and_basemap_has_no_problems():
    assert check([source(OSM)], TODAY) == []


@pytest.mark.parametrize(
    ("changes", "rule"),
    [
        ({"url": "http://example.test/"}, "https_only"),
        ({"evidence_urls": ["ftp://example.test/terms"]}, "https_only"),
        ({"licence_url": "https://user:secret@example.test/"}, "https_only"),  # public-only: allow
        ({"share_alike": True}, "share_alike_matches_licence"),
        ({"additional_licences": ["CC-BY-SA-4.0"]}, "share_alike_matches_licence"),
        ({"dimension": "audit"}, "audit_data_stays_internal"),
        ({"uses": ["audit_only", "scoring"]}, "audit_data_stays_internal"),
        ({"licence": "None-stated"}, "approved_is_proven"),
        ({"attribution": "   "}, "approved_is_proven"),
        ({"commercial_use": "unknown"}, "approved_is_proven"),
        ({"verified_how": "secondary_source"}, "approved_is_proven"),
        ({"evidence_urls": []}, "approved_is_proven"),
        ({"uses": []}, "approved_is_proven"),
        ({"attribution": ""}, "approved_is_proven"),
        ({"commercial_use": "yes_with_conditions"}, "approved_is_proven"),
        ({"status": "gated"}, "unapproved_says_why"),
        ({"status": "held", "status_reason": "  "}, "unapproved_says_why"),
        ({"status": "banned", "status_reason": "terms forbid it"}, "unapproved_stays_internal"),
        ({"status": "held", "status_reason": "later"}, "unapproved_stays_internal"),
        (
            {"status": "gated", "status_reason": "ask", "before_launch": ["A reply."]},
            "launch_items_belong_to_approved_sources",
        ),
        ({"commercial_use": "no"}, "non_commercial_is_not_usable"),
        (
            {"commercial_use": "no", "status": "gated", "status_reason": "ask"},
            "non_commercial_is_not_usable",
        ),
        ({"verified_on": date(2026, 9, 24)}, "verified_on_is_not_in_the_future"),
    ],
)
def test_each_rule_catches_its_violation(changes: dict[str, Any], rule: str):
    assert rule in rules_broken(source(**changes))


@pytest.mark.parametrize("use", ["gazetteer", "cells", "destination_search", "scoring"])
def test_share_alike_data_is_kept_out_of_gazetteer_and_scoring(use: str):
    assert "share_alike_stays_out_of_scoring" in rules_broken(source(OSM, uses=[use]))


def test_audit_data_with_internal_uses_only_is_fine():
    audit = source(dimension="audit", uses=["audit_only", "validation_only"])
    assert check([audit], TODAY) == []


def test_validation_may_sit_beside_uses_that_reach_users():
    assert check([source(uses=["scoring", "validation_only"])], TODAY) == []


def test_a_resident_source_that_feeds_only_the_census_table_has_no_problems():
    assert check([source(RESIDENTS)], TODAY) == []


# Over every use there is, so that a use added later is refused until someone allows it.
@pytest.mark.parametrize("use", sorted(set(Use) - {Use.CENSUS_TABLE}))
def test_a_resident_source_may_feed_the_census_table_and_nothing_else(use: Use):
    assert FEEDS_NOTHING_ELSE in rules_broken(source(RESIDENTS, uses=["census_table", use]))
    assert FEEDS_NOTHING_ELSE in rules_broken(source(RESIDENTS, uses=[use]))


@pytest.mark.parametrize("status", ["gated", "held"])
def test_a_resident_source_that_is_not_approved_cannot_be_opened_to_look(status: str):
    # An internal use would let a file about residents be fetched before its licence page
    # is saved and before the fences around the census table exist.
    waiting = {"status": status, "status_reason": "Its licence page has not been saved."}
    for use in ("prototyping_only", "validation_only", "audit_only"):
        assert FEEDS_NOTHING_ELSE in rules_broken(source(RESIDENTS, uses=[use], **waiting))


def test_a_resident_source_must_name_its_tables():
    assert FEEDS_NOTHING_ELSE in rules_broken(source(RESIDENTS, tables=[]))


# Main language is published for boroughs only. The rest are never shown. See ADR 0014.
@pytest.mark.parametrize("table", ["TS024", "TS077", "TS078", "TS044"])
def test_a_resident_source_may_name_only_a_table_an_areas_page_may_show(table: str):
    assert table not in SHOWN_TABLES
    assert FEEDS_NOTHING_ELSE in rules_broken(source(RESIDENTS, tables=["TS021", table]))


def test_an_areas_page_may_show_five_census_tables():
    assert {"TS003", "TS004", "TS007A", "TS021", "TS030"} == SHOWN_TABLES
    assert check([source(RESIDENTS, tables=sorted(SHOWN_TABLES))], TODAY) == []


@pytest.mark.parametrize("dimension", sorted(set(Dimension) - {Dimension.RESIDENTS}))
def test_only_a_source_under_residents_may_feed_the_census_table(dimension: Dimension):
    for uses in (["census_table"], ["scoring", "census_table"]):
        assert ONLY_RESIDENTS in rules_broken(source(dimension=dimension, uses=uses))


@pytest.mark.parametrize(
    "named",
    [
        {"tables": ["TS021"]},
        {"tables": ["TS044", "TS003"]},
        {"id": "ons-census-2021-ts007a-age"},
        {"name": "Census 2021 table TS030: religion"},
        {"url": "https://www.nomisweb.co.uk/datasets/c2021ts004"},
        {"url": "https://www.nomisweb.co.uk/output/census/2021/census2021-ts021.zip"},
        {"evidence_urls": ["https://www.ons.gov.uk/datasets/TS021/editions/2021/versions/3"]},
        # A table nobody has listed anywhere is fenced too: it is not a housing table.
        {"tables": ["TS999"]},
        # A code is read however it is written: with a sign in it, joined to a word,
        # with letters after it, and in letters and digits of another width.
        {"name": "Census 2021 table TS 021: ethnic group"},
        {"name": "Census 2021 table TS-021"},
        {"name": "Census 2021 table TS_021"},
        {"name": "Census 2021 table TS.021"},
        {"name": "Census 2021 table TS/021"},
        {"name": "Census 2021 table TS:021"},
        {"name": "Census 2021 table T S021"},
        {"name": "Census 2021 table TS0 21"},
        {"name": "Census 2021 table t-s-0-2-1"},
        {"name": "censusTS021"},
        {"name": "Table xTS021 of the census"},
        {"name": "Census 2021 table TS021EW"},
        {"name": "Census 2021 table ts021oa"},
        {"name": "Census 2021 table ts021ab"},
        {"name": "Census 2021 table \uff34\uff33\uff10\uff12\uff11"},
        {"id": "ons-census-2021-ts-021"},
        {"url": "https://www.nomisweb.co.uk/output/census/2021/census2021-ts-021.zip"},
        {"url": "https://www.nomisweb.co.uk/output/census/2021/census2021-ts_021.zip"},
        {"url": "https://www.nomisweb.co.uk/output/censusts021.zip"},
        {"url": "https://www.nomisweb.co.uk/output/bulkTS021.csv"},
        {"url": "https://www.nomisweb.co.uk/output/ts021oa.csv"},
        # A housing table's code with a letter after it is the code of another table.
        {"name": "Census 2021 table TS044A"},
        {"url": "https://www.nomisweb.co.uk/output/ts044oa.csv"},
    ],
)
@pytest.mark.parametrize("dimension", ["housing", "geography", "places", "text"])
def test_a_census_table_about_people_cannot_be_registered_under_another_heading(
    dimension: str, named: dict[str, Any]
):
    assert UNDER_RESIDENTS in rules_broken(source(dimension=dimension, uses=["scoring"], **named))


def test_the_housing_tables_may_stay_under_housing():
    assert {"TS044", "TS050", "TS054"} == HOUSING_TABLES
    housing = source(
        id="ons-census-2021-tenure-ts054",
        name="Census 2021 housing tables: TS044 accommodation type, TS050 number of bedrooms",
        url="https://www.nomisweb.co.uk/datasets/c2021ts044",
        dimension="housing",
        tables=sorted(HOUSING_TABLES),
        uses=["scoring"],
    )
    assert check([housing], TODAY) == []


def test_no_table_an_areas_page_may_show_is_a_housing_table():
    assert not SHOWN_TABLES & HOUSING_TABLES


def test_the_audit_may_name_any_census_table_and_still_has_internal_uses_only():
    audit = source(dimension="audit", tables=["TS021", "TS077"], uses=["audit_only"])
    assert check([audit], TODAY) == []
    assert "audit_data_stays_internal" in rules_broken(
        source(dimension="audit", tables=["TS021"], uses=["census_table"])
    )


def test_a_year_after_a_word_is_no_table_code():
    """A code has three digits and a year has four."""
    plain = source(
        name="Made-up rents 2025, counts 2021 and results-2024",
        url="https://example.test/datasets2021/assets-2025",
        evidence_urls=["https://example.test/posts2021/charts1000"],
    )
    assert check([plain], TODAY) == []


def test_a_word_that_ends_as_a_table_code_does_is_taken_for_one():
    """The rule cannot tell `charts100` from a table's code joined to a word. It refuses both."""
    for address in ("https://example.test/datasets123", "https://example.test/charts100"):
        assert UNDER_RESIDENTS in rules_broken(source(url=address))


@pytest.mark.parametrize("code", ["ts021", "TS21", "TS0211", "21", "TS021 "])
def test_a_table_code_is_written_as_the_statistics_office_writes_it(code: str):
    with pytest.raises(ValueError, match="tables"):
        source(RESIDENTS, tables=[code])


def test_cc0_needs_no_attribution():
    assert check([source(licence="CC0-1.0", attribution="")], TODAY) == []


def test_conditions_satisfy_conditional_commercial_use():
    conditional = source(commercial_use="yes_with_conditions", conditions=["Never show rows."])
    assert check([conditional], TODAY) == []


def test_held_source_may_be_used_for_prototyping():
    held = source(status="held", status_reason="terms unread", uses=["prototyping_only"])
    assert check([held], TODAY) == []


def test_banned_source_with_a_reason_and_no_uses_is_fine():
    banned = source(status="banned", status_reason="terms forbid storing", uses=[])
    assert check([banned], TODAY) == []


def test_duplicate_ids_are_caught():
    assert "unique_ids" in rules_broken(source(), source())


def test_unconfirmed_attribution_wording_is_a_warning_not_an_error():
    unconfirmed = source(attribution_verified=False)
    assert rules_broken(unconfirmed) == set()
    assert rules_broken(unconfirmed, severity=Severity.WARNING) == {
        "attribution_wording_is_confirmed"
    }


def test_verification_older_than_a_year_is_a_warning():
    stale = source(verified_on=date(2025, 9, 1))
    assert rules_broken(stale, severity=Severity.WARNING) == {"verification_is_fresh"}


def test_unknown_field_is_rejected():
    with pytest.raises(ValueError, match="licence_name"):
        source(licence_name="OGL")


def test_unknown_licence_is_rejected():
    with pytest.raises(ValueError, match="licence"):
        source(licence="Public-Domain-ish")


@pytest.mark.parametrize("bad_id", ["ONS-areas", "ons_areas", "ons--areas", "-ons", "ons areas"])
def test_ids_are_kebab_case(bad_id: str):
    with pytest.raises(ValueError, match="id"):
        source(id=bad_id)
