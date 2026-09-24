from datetime import date
from functools import cache
from pathlib import Path

import pytest
from burro_pipeline.registry import (
    Registry,
    RegistryError,
    Severity,
    Source,
    Use,
    check,
    find,
    load,
)
from burro_pipeline.registry.cli import main
from burro_pipeline.registry.model import SHOWN_TABLES
from burro_pipeline.release.write import USE_OF

REPO_REGISTRY = Path(__file__).parents[3] / "registry" / "sources"


@cache
def of_the_repository() -> Registry:
    """The repository's own registry, read once for all the tests here. It is frozen."""
    return load(REPO_REGISTRY)


REGISTRY = """
schema_version = 1

[[source]]
id = "hmlr-price-paid"
name = "Price Paid Data"
publisher = "HM Land Registry"
url = "https://www.gov.uk/government/collections/price-paid-data"
dimension = "housing"
licence = "OGL-3.0"
commercial_use = "yes_with_conditions"
share_alike = false
attribution = "Contains HM Land Registry data © Crown copyright and database right."
attribution_verified = true
conditions = ["Never display or export postcode-level rows."]
status = "approved"
uses = ["scoring", "display"]
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = ["https://www.gov.uk/government/publications/about-the-price-paid-data"]

[[source]]
id = "ons-census-2021-ethnicity"
name = "Census 2021 ethnic group"
publisher = "Office for National Statistics"
url = "https://www.nomisweb.co.uk/"
dimension = "audit"
licence = "OGL-3.0"
commercial_use = "yes"
share_alike = false
attribution = "Source: Office for National Statistics licensed under the OGL v3.0."
attribution_verified = true
status = "approved"
uses = ["audit_only"]
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = ["https://www.ons.gov.uk/methodology/geography/licences"]

[[source]]
id = "nr-schedule"
name = "Network Rail schedule"
publisher = "Network Rail"
url = "https://raildata.org.uk/"
dimension = "transport"
licence = "Network-Rail-OGL-based"
commercial_use = "unknown"
share_alike = false
status = "gated"
status_reason = "Marketplace terms must be read and saved first."
uses = ["routing", "validation_only"]
verified_how = "secondary_source"
verified_on = 2026-09-23

[[source]]
id = "google-places"
name = "Google Places"
publisher = "Google"
url = "https://developers.google.com/maps/documentation/places/web-service"
dimension = "places"
licence = "Bespoke-terms"
commercial_use = "no"
share_alike = false
status = "banned"
status_reason = "Terms prohibit storing content and deriving data from it."
verified_how = "primary_source"
verified_on = 2026-09-23
"""


def split_by_dimension(folder: Path) -> Path:
    """Write the example registry as a folder: one file per dimension."""
    header, *entries = REGISTRY.split("[[source]]")
    for entry in entries:
        dimension = entry.split('dimension = "')[1].split('"')[0]
        file = folder / f"{dimension}.toml"
        if not file.exists():
            file.write_text(header)
        file.write_text(file.read_text() + "[[source]]" + entry)
    return folder


@pytest.fixture
def path(tmp_path: Path) -> Path:
    file = tmp_path / "sources.toml"
    file.write_text(REGISTRY)
    return file


@pytest.fixture
def registry(path: Path) -> Registry:
    return load(path)


def test_the_example_registry_is_valid(registry: Registry):
    assert check(registry, date(2026, 9, 23)) == []


def broken(path: Path, old: str, new: str) -> Path:
    assert old in REGISTRY
    path.write_text(REGISTRY.replace(old, new, 1))
    return path


def test_the_gate_refuses_a_registry_that_breaks_a_rule(path: Path):
    broken(path, "share_alike = false", "share_alike = true")
    with pytest.raises(RegistryError, match="breaks the registry rules: hmlr-price-paid"):
        load(path)


def test_a_share_alike_source_registered_for_scoring_never_reaches_the_gate(path: Path):
    text = REGISTRY.replace('licence = "OGL-3.0"', 'licence = "ODbL-1.0"', 1)
    path.write_text(text.replace("share_alike = false", "share_alike = true", 1))
    with pytest.raises(RegistryError, match="share-alike data may not be used for scoring"):
        load(path)


def test_tools_that_report_problems_can_still_read_a_broken_registry(path: Path):
    broken(path, "share_alike = false", "share_alike = true")
    registry = load(path, enforce=False)
    assert {p.rule for p in check(registry, date(2026, 9, 23))} == {
        "share_alike_matches_licence",
        "share_alike_stays_out_of_scoring",
    }


def test_an_id_used_twice_is_refused_even_when_not_enforcing(path: Path):
    broken(path, 'id = "google-places"', 'id = "hmlr-price-paid"')
    with pytest.raises(RegistryError, match="id used more than once: hmlr-price-paid"):
        load(path, enforce=False)


def test_a_ban_cannot_be_shadowed_by_a_second_entry(tmp_path: Path):
    split_by_dimension(tmp_path)
    approved = (tmp_path / "housing.toml").read_text().replace("hmlr-price-paid", "google-places")
    (tmp_path / "housing.toml").write_text(approved)
    with pytest.raises(RegistryError, match="id used more than once: google-places"):
        load(tmp_path)


def test_approved_source_passes_the_gate_for_a_registered_use(registry: Registry):
    assert registry.require("hmlr-price-paid", Use.SCORING).publisher == "HM Land Registry"


def test_approved_source_is_refused_for_an_unregistered_use(registry: Registry):
    with pytest.raises(RegistryError, match="not registered for gazetteer"):
        registry.require("hmlr-price-paid", Use.GAZETTEER)


def test_audit_only_data_can_never_reach_scoring(registry: Registry):
    with pytest.raises(RegistryError, match="not registered for scoring"):
        registry.require("ons-census-2021-ethnicity", Use.SCORING)


# A made-up entry shaped like the real one, approved so that the gate's own answer is tested.
RESIDENTS_ID = "ons-census-2021-resident-tables"
RESIDENTS = """
[[source]]
id = "ons-census-2021-resident-tables"
name = "Census 2021 tables about residents"
publisher = "Office for National Statistics"
url = "https://www.nomisweb.co.uk/sources/census_2021_bulk"
dimension = "residents"
tables = ["TS021", "TS030"]
licence = "OGL-3.0"
commercial_use = "yes"
share_alike = false
attribution = "Source: Office for National Statistics"
attribution_verified = true
status = "approved"
uses = ["census_table"]
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = ["https://www.nomisweb.co.uk/home/copyright.asp"]
"""


@pytest.fixture
def with_residents(tmp_path: Path) -> Registry:
    file = tmp_path / "with-residents.toml"
    file.write_text(REGISTRY + RESIDENTS)
    return load(file)


def test_a_resident_source_passes_the_gate_for_the_census_table(with_residents: Registry):
    assert with_residents.require(RESIDENTS_ID, Use.CENSUS_TABLE).tables == ("TS021", "TS030")


# Over every use there is, so that a use added later is refused without anyone remembering to.
@pytest.mark.parametrize("use", sorted(set(Use) - {Use.CENSUS_TABLE}))
def test_the_gate_refuses_a_resident_source_for_every_other_use(with_residents: Registry, use: Use):
    with pytest.raises(RegistryError, match=f"not registered for {use}. It is registered for: "):
        with_residents.require(RESIDENTS_ID, use)


@pytest.mark.parametrize("file", sorted(USE_OF))
def test_no_file_of_a_release_may_cite_a_resident_source(with_residents: Registry, file: str):
    # `write_release` asks the gate for the use each file needs. None of them is the census
    # table, which is kept in a folder of its own, outside the release.
    assert USE_OF[file] is not Use.CENSUS_TABLE
    with pytest.raises(RegistryError, match="not registered for"):
        with_residents.require(RESIDENTS_ID, USE_OF[file])


@pytest.mark.parametrize("use", ["scoring", "display", "profile_text", "destination_search"])
def test_a_resident_source_given_a_use_in_the_product_never_reaches_the_gate(
    tmp_path: Path, use: str
):
    file = tmp_path / "sources.toml"
    listed = f'uses = ["census_table", "{use}"]'
    file.write_text(REGISTRY + RESIDENTS.replace('uses = ["census_table"]', listed))
    with pytest.raises(RegistryError, match=f"a source about residents may not be used for {use}"):
        load(file)


def test_a_source_elsewhere_given_the_census_table_never_reaches_the_gate(path: Path):
    broken(path, 'uses = ["scoring", "display"]', 'uses = ["scoring", "display", "census_table"]')
    with pytest.raises(RegistryError, match="hmlr-price-paid: only a source under residents"):
        load(path)


def test_a_census_table_about_people_under_housing_never_reaches_the_gate(path: Path):
    broken(path, 'dimension = "housing"', 'dimension = "housing"\ntables = ["TS021"]')
    with pytest.raises(RegistryError, match="hmlr-price-paid: census table TS021"):
        load(path)


def test_the_census_table_is_credited_once_its_source_is_approved(with_residents: Registry):
    assert RESIDENTS_ID in [source.id for source, _ in with_residents.attributions()]


def test_gated_source_is_refused_with_its_reason(registry: Registry):
    with pytest.raises(RegistryError, match="terms must be read and saved"):
        registry.require("nr-schedule", Use.ROUTING)


def test_gated_source_may_be_read_for_an_internal_use_it_lists(registry: Registry):
    assert registry.require("nr-schedule", Use.VALIDATION_ONLY).id == "nr-schedule"


def test_gated_source_is_refused_for_an_internal_use_it_does_not_list(registry: Registry):
    with pytest.raises(RegistryError) as refused:
        registry.require("nr-schedule", Use.PROTOTYPING_ONLY)
    message = str(refused.value)
    assert "is gated, not approved: Marketplace terms must be read" in message
    assert message.endswith("Meanwhile it may be read for: validation_only.")
    assert "routing" not in message


@pytest.mark.parametrize("use", list(Use))
def test_banned_source_is_refused_for_every_use(registry: Registry, use: Use):
    with pytest.raises(RegistryError, match="banned"):
        registry.require("google-places", use)


def test_unregistered_source_is_refused(registry: Registry):
    with pytest.raises(RegistryError, match="not in the licence registry"):
        registry.require("somebodys-scraped-reviews", Use.SCORING)


def test_attributions_cover_only_approved_sources_that_reach_users(registry: Registry):
    assert [source.id for source, _ in registry.attributions()] == ["hmlr-price-paid"]


def test_missing_file_is_a_registry_error(tmp_path: Path):
    with pytest.raises(RegistryError, match="no registry"):
        load(tmp_path / "absent.toml")


def test_an_empty_folder_is_a_registry_error(tmp_path: Path):
    with pytest.raises(RegistryError, match=r"no \.toml files"):
        load(tmp_path)


def test_a_folder_is_read_as_one_file_per_dimension(tmp_path: Path):
    registry = load(split_by_dimension(tmp_path))
    assert sorted(source.id for source in registry) == [
        "google-places",
        "hmlr-price-paid",
        "nr-schedule",
        "ons-census-2021-ethnicity",
    ]


def test_a_source_filed_under_the_wrong_dimension_is_refused(tmp_path: Path):
    split_by_dimension(tmp_path)
    (tmp_path / "housing.toml").rename(tmp_path / "heritage.toml")
    with pytest.raises(RegistryError, match=r"hmlr-price-paid .* belongs in housing\.toml"):
        load(tmp_path)


def test_a_file_not_named_for_a_dimension_is_refused(tmp_path: Path):
    split_by_dimension(tmp_path)
    (tmp_path / "misc.toml").write_text("schema_version = 1\n")
    with pytest.raises(RegistryError, match="'misc' is not a dimension"):
        load(tmp_path)


def test_a_file_with_an_upper_case_name_is_refused_not_skipped(tmp_path: Path):
    split_by_dimension(tmp_path)
    (tmp_path / "housing.toml").rename(tmp_path / "Housing.TOML")
    with pytest.raises(RegistryError, match="in lower case"):
        load(tmp_path)


def test_other_files_and_subfolders_are_left_alone(tmp_path: Path):
    split_by_dimension(tmp_path)
    (tmp_path / "README.md").write_text("notes")
    (tmp_path / "old").mkdir()
    (tmp_path / "old" / "misc.toml").write_text("nonsense")
    assert len(load(tmp_path).sources) == 4


def test_entries_under_a_misspelt_table_are_refused(path: Path):
    path.write_text(REGISTRY.replace("[[source]]", "[[sources]]"))
    with pytest.raises(RegistryError, match=r"unknown top-level key 'sources'.*\[\[source\]\]"):
        load(path)


def test_a_file_that_is_not_utf8_is_a_registry_error(tmp_path: Path):
    file = tmp_path / "sources.toml"
    file.write_bytes(b'schema_version = 1\n[[source]]\nid = "caf\xe9"\n')
    with pytest.raises(RegistryError, match="not UTF-8"):
        load(file)


@pytest.mark.parametrize("sources", ['source = "hmlr-price-paid"', "source = [1, 2]"])
def test_sources_not_written_as_tables_are_a_registry_error(tmp_path: Path, sources: str):
    file = tmp_path / "sources.toml"
    file.write_text(f"schema_version = 1\n{sources}\n")
    with pytest.raises(RegistryError, match=r"\[\[source\]\] tables"):
        load(file)


def test_a_quoted_boolean_is_refused(path: Path):
    path.write_text(REGISTRY.replace("share_alike = false", 'share_alike = "false"', 1))
    with pytest.raises(RegistryError, match="share_alike"):
        load(path)


def test_validation_errors_are_one_readable_line(path: Path):
    path.write_text(REGISTRY.replace('dimension = "housing"', 'dimension = "houses"'))
    with pytest.raises(RegistryError) as raised:
        load(path)
    message = str(raised.value)
    assert "hmlr-price-paid: dimension: Input should be" in message
    assert "\n" not in message
    assert "errors.pydantic.dev" not in message


def test_the_registry_is_found_from_any_folder_inside_the_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    folder = tmp_path / "registry" / "sources"
    folder.mkdir(parents=True)
    split_by_dimension(folder)
    nested = tmp_path / "packages" / "pipeline" / "src"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    assert find() == folder.resolve()
    assert len(load().sources) == 4


def test_a_folder_outside_any_repository_has_no_registry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(RegistryError, match="or any folder above it"):
        find()


def test_invalid_toml_is_a_registry_error(tmp_path: Path):
    file = tmp_path / "sources.toml"
    file.write_text("schema_version = ")
    with pytest.raises(RegistryError, match="not valid TOML"):
        load(file)


def test_wrong_schema_version_is_refused(tmp_path: Path):
    file = tmp_path / "sources.toml"
    file.write_text("schema_version = 2\n")
    with pytest.raises(RegistryError, match="schema_version"):
        load(file)


def test_invalid_entry_names_the_source(path: Path):
    path.write_text(REGISTRY.replace('licence = "Bespoke-terms"', 'licence = "Whatever"'))
    with pytest.raises(RegistryError, match="google-places"):
        load(path)


def test_cli_check_passes_on_a_valid_registry(path: Path, capsys: pytest.CaptureFixture[str]):
    assert main(["--path", str(path), "check"]) == 0
    assert "4 sources (2 approved, 1 banned, 1 gated); 0 failing" in capsys.readouterr().out


def test_cli_check_on_an_empty_registry(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    file = tmp_path / "sources.toml"
    file.write_text("schema_version = 1\n")
    assert main(["--path", str(file), "check"]) == 0
    assert capsys.readouterr().out == "0 sources; 0 failing\n"


def test_cli_check_fails_on_an_error(path: Path, capsys: pytest.CaptureFixture[str]):
    path.write_text(REGISTRY.replace("share_alike = false", "share_alike = true", 1))
    assert main(["--path", str(path), "check"]) == 1
    assert "share_alike_matches_licence" in capsys.readouterr().err


def test_something_to_settle_before_launch_passes_check_but_fails_strict(
    path: Path, capsys: pytest.CaptureFixture[str]
):
    path.write_text(
        REGISTRY.replace(
            'uses = ["scoring", "display"]',
            'uses = ["scoring", "display"]\nbefore_launch = ["Written reply from the publisher."]',
        )
    )
    assert load(path).require("hmlr-price-paid", Use.SCORING)
    assert main(["--path", str(path), "check"]) == 0
    quiet = capsys.readouterr()
    assert quiet.err == ""
    assert quiet.out.endswith("0 failing; 1 to settle before launch (--strict lists them)\n")
    assert main(["--path", str(path), "check", "--strict"]) == 1
    strict = capsys.readouterr()
    assert "to settle before launch: Written reply" in strict.err
    assert strict.out.endswith("; 1 failing\n")


def test_cli_strict_fails_on_a_warning(path: Path):
    path.write_text(
        REGISTRY.replace("attribution_verified = true", "attribution_verified = false", 1)
    )
    assert main(["--path", str(path), "check"]) == 0
    assert main(["--path", str(path), "check", "--strict"]) == 1


def test_cli_reports_an_unreadable_registry(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    assert main(["--path", str(tmp_path / "absent.toml"), "check"]) == 2
    assert "no registry" in capsys.readouterr().err


def test_cli_will_not_print_attributions_from_a_broken_registry(
    path: Path, capsys: pytest.CaptureFixture[str]
):
    broken(path, "share_alike = false", "share_alike = true")
    assert main(["--path", str(path), "list"]) == 0
    assert main(["--path", str(path), "attributions"]) == 2
    assert "breaks the registry rules" in capsys.readouterr().err


def test_cli_lists_and_prints_attributions(path: Path, capsys: pytest.CaptureFixture[str]):
    assert main(["--path", str(path), "list"]) == 0
    assert "banned" in capsys.readouterr().out
    assert main(["--path", str(path), "attributions"]) == 0
    assert "HM Land Registry data" in capsys.readouterr().out


def test_the_real_registry_has_no_errors():
    problems = check(load(REPO_REGISTRY, enforce=False), date.today())
    assert [str(p) for p in problems if p.severity is Severity.ERROR] == []


# These are gated until the thing that keeps them contained exists: the isolated audit
# store for the census tables, the lineage test for the OpenStreetMap comparisons, and
# for the census table on an area's page a saved licence page and the fences around the
# artefact that holds it. Giving one a use belongs in the same change as that containment.
CONTAINED = [
    "ons-census-2021-protected-characteristics",
    "ons-census-2021-resident-tables",
    "osm-place-nodes",
    "openstreetmap-points-of-interest",
]


@pytest.mark.parametrize("source_id", CONTAINED)
@pytest.mark.parametrize("use", list(Use))
def test_contained_sources_are_refused_for_every_use(source_id: str, use: Use):
    with pytest.raises(RegistryError, match="not approved"):
        of_the_repository().require(source_id, use)


# What the first five real measures are worked out from: flats, homes built before 1919,
# homes per hectare, transport noise and nitrogen dioxide. A catalogue row names every
# source behind its figure, the geography included, and `write_release` asks the gate
# for the use of the file that names it. See ADR 0016.
GEOGRAPHY_BEHIND_A_MEASURE = [
    "ons-lsoa-2021",
    "ons-oa-pwc-2021",
    "ons-oa21-lsoa21-msoa21-lad22-lookup",
]
BEHIND_THE_FIRST_MEASURES = [
    "defra-pcm-background-air",
    "mhclg-iod-2025-underlying-indicators",
    "ons-census-2021-housing-tables",
    "voa-council-tax-stock-of-properties",
    *GEOGRAPHY_BEHIND_A_MEASURE,
]


@pytest.mark.parametrize("source_id", BEHIND_THE_FIRST_MEASURES)
def test_every_source_behind_the_first_real_measures_passes_the_gate(source_id: str):
    assert of_the_repository().require(source_id, USE_OF["catalogue.json"]).id == source_id


@pytest.mark.parametrize("source_id", GEOGRAPHY_BEHIND_A_MEASURE)
def test_geography_behind_a_measure_rests_on_the_publishers_own_licence_page(source_id: str):
    source = of_the_repository().get(source_id)
    assert "https://www.ons.gov.uk/methodology/geography/licences" in source.evidence_urls
    assert source.verified_how == "primary_source"
    assert source.licence == "OGL-3.0"


def test_the_real_registry_keeps_resident_sources_under_residents():
    registry = of_the_repository()
    shown = [source for source in registry if Use.CENSUS_TABLE in source.uses]
    assert [source.id for source in shown] == ["ons-census-2021-resident-tables"]
    assert [source.id for source in registry if source.dimension == "residents"] == [
        "ons-census-2021-resident-tables"
    ]
    assert set(shown[0].tables) == SHOWN_TABLES
    assert shown[0].uses == (Use.CENSUS_TABLE,)


def test_the_real_census_entry_cannot_be_approved_by_changing_its_status_alone():
    # Nobody has read its licence pages by eye. Approving it takes a person who has.
    entry = of_the_repository().get("ons-census-2021-resident-tables")
    approved = Source.model_validate(entry.model_dump() | {"status": "approved"})
    assert {problem.rule for problem in check([approved], date.today())} == {
        "approved_is_proven",
        "attribution_wording_is_confirmed",
    }


def test_the_real_audit_entry_has_no_use_that_reaches_a_page():
    audit = of_the_repository().get("ons-census-2021-protected-characteristics")
    assert audit.dimension == "audit"
    assert audit.uses == ()
