"""An entry names the addresses of its files, and an address is of one entry.

A publisher serves many datasets from one host: the statistics office, the
London Datastore and the government's file host each do. So a host says
nothing of what a file is. An entry names the addresses of its files under
`file_urls`: a whole address, or a prefix that ends in `/` and at the dataset.
An address passes only under the entry that names it. Every address here is
made up, but for those of the repository's own registry, and nothing is asked
of any of them.
"""

import json
from datetime import date
from functools import cache
from itertools import permutations
from pathlib import Path
from typing import Any

import pytest
from burro_pipeline.registry import Registry, RegistryError, Severity, Source, check, load
from burro_pipeline.registry.addresses import holds, is_a_file_of, names

TODAY = date(2026, 9, 23)
REPOSITORY = Path(__file__).parents[3]
HOST = "https://files.made-up.example"
WHOLE = f"{HOST}/media/0123456789abcdef/made-up-homes.zip"
PREFIX = f"{HOST}/api/download/items/0123456789abcdef/"

WITH_A_LOGIN = "https://made-up:made-up@files.made-up.example/homes.zip"  # public-only: allow
# Made-up addresses that hold the host where a login stands, and a login before the host.
HOST_AS_A_LOGIN = "https://files.made-up.example@elsewhere.example"  # public-only: allow
LOGIN_AND_HOST = "https://made-up@files.made-up.example"  # public-only: allow
HOST_AND_A_SLASH = "https://files.made-up.example\\@elsewhere.example"  # public-only: allow

PLAIN = "file_urls_are_written_plainly"
OF_ONE_ENTRY = "no_address_is_held_by_two_entries"

HOMES: dict[str, Any] = {
    "id": "made-up-homes",
    "name": "Made-up homes",
    "publisher": "Made-up Office",
    "url": "https://made-up.example/homes",
    "dimension": "housing",
    "licence": "OGL-3.0",
    "commercial_use": "yes",
    "share_alike": False,
    "attribution": "Contains made-up data.",
    "attribution_verified": True,
    "status": "approved",
    "uses": ["scoring"],
    "verified_how": "primary_source",
    "verified_on": TODAY,
    "evidence_urls": ["https://made-up.example/licence"],
    "file_urls": [WHOLE, PREFIX],
}

# Read for the audit alone, from the same host.
AUDIT: dict[str, Any] = HOMES | {
    "id": "made-up-classification",
    "name": "Made-up classification of residents",
    "url": f"{HOST}/datasets/made-up-classification",
    "dimension": "audit",
    "status": "held",
    "status_reason": "Made up. It is read for the audit and for nothing else.",
    "uses": ["audit_only"],
    "file_urls": [f"{HOST}/media/fedcba9876543210/made-up-classification.zip"],
}


def source(base: dict[str, Any] = HOMES, **changes: Any) -> Source:
    return Source.model_validate(base | changes)


def rules_broken(*sources: Source) -> set[str]:
    return {p.rule for p in check(sources, TODAY) if p.severity is Severity.ERROR}


# A whole address


def test_a_whole_address_names_itself():
    assert names(WHOLE, WHOLE)
    assert is_a_file_of(source(), WHOLE)


@pytest.mark.parametrize(
    "address",
    [
        f"{HOST}/media/0123456789abcdef/made-up-homes.csv",
        f"{HOST}/media/0123456789abcdef/",
        f"{HOST}/media/0123456789abcdef/made-up-homes.zip/more",
        f"{HOST}/media/0123456789abcdef/made-up-homes.zip?table=other",
        f"{HOST}/media/0123456789abcdef/MADE-UP-HOMES.zip",
        f"{HOST}/media/0123456789abcdef/made-up-homes%2Ezip",
        f"{HOST}/media/fedcba9876543210/made-up-classification.zip",
        f"{HOST}/media/0123456789abcdef/../fedcba9876543210/made-up-classification.zip",
        f"{HOST}/",
        HOST,
        "",
        "made-up-homes.zip",
    ],
)
def test_a_whole_address_names_no_other(address: str):
    assert not names(WHOLE, address)


def test_a_parameter_is_part_of_a_whole_address():
    held = f"{HOST}/download?id=1"
    assert names(held, held)
    for other in (f"{HOST}/download?id=2", f"{HOST}/download", f"{HOST}/download?id=1&id=2"):
        assert not names(held, other)


# A prefix


@pytest.mark.parametrize(
    "address",
    [
        f"{PREFIX}csv",
        f"{PREFIX}csv?layers=0",
        f"{PREFIX}geoPackage?layers=0",
        f"{PREFIX}2021/made-up%20homes.csv",
        # What stands after `#` is never sent to a server.
        f"{PREFIX}csv#part",
        # A letter outside ASCII is left to the download, which asks nothing of such an address.
        f"{PREFIX}caf\u00e9.csv",
    ],
)
def test_a_prefix_names_every_address_under_it(address: str):
    assert names(PREFIX, address)
    assert is_a_file_of(source(), address)


@pytest.mark.parametrize(
    "address",
    [
        # Beside it, above it, or under a name that only starts as it does.
        f"{HOST}/api/download/items/fedcba9876543210/csv",
        f"{HOST}/api/download/items/",
        f"{HOST}/api/download/items/0123456789abcdef",
        f"{HOST}/api/download/items/0123456789abcdef0/csv",
        f"{HOST}/api/download/items/0123456789ABCDEF/csv",
        # Under it as it is written, and elsewhere as a server reads it.
        f"{PREFIX}../fedcba9876543210/csv",
        f"{PREFIX}x/../../fedcba9876543210/csv",
        f"{PREFIX}%2e%2e/fedcba9876543210/csv",
        f"{PREFIX}%2E%2E%2Ffedcba9876543210/csv",
        f"{PREFIX}%252e%252e/fedcba9876543210/csv",
        f"{PREFIX}%25252e%25252e/fedcba9876543210/csv",
        f"{PREFIX}%2525252e%2525252e/fedcba9876543210/csv",
        f"{PREFIX}..%5Cfedcba9876543210/csv",
        f"{PREFIX}..\\fedcba9876543210\\csv",
        f"{PREFIX}./csv",
        f"{PREFIX}/csv",
        f"{PREFIX}x//csv",
        f"{PREFIX}csv\n",
        f"{PREFIX}c sv",
        # Signs of another width, and a sign encoded wrongly, that a server may read as plain.
        f"{PREFIX}\uff0e\uff0e/fedcba9876543210/csv",
        f"{PREFIX}%EF%BC%8E%EF%BC%8E/fedcba9876543210/csv",
        f"{PREFIX}%c0%ae%c0%ae/fedcba9876543210/csv",
    ],
)
def test_a_prefix_names_nothing_beside_it_above_it_or_written_to_leave_it(address: str):
    assert not names(PREFIX, address)


# The host, the port and the scheme


@pytest.mark.parametrize(
    "address",
    [
        "https://FILES.made-up.example/media/0123456789abcdef/made-up-homes.zip",
        "https://files.made-up.example:443/media/0123456789abcdef/made-up-homes.zip",
        "https://files.made-up.example./media/0123456789abcdef/made-up-homes.zip",
        "HTTPS://files.made-up.example/media/0123456789abcdef/made-up-homes.zip",
    ],
)
def test_a_host_is_the_same_host_however_it_is_written(address: str):
    assert names(WHOLE, address)


@pytest.mark.parametrize(
    "address",
    [
        "http://files.made-up.example/media/0123456789abcdef/made-up-homes.zip",
        "https://files.made-up.example:8443/media/0123456789abcdef/made-up-homes.zip",
        "https://made-up.example/media/0123456789abcdef/made-up-homes.zip",
        "https://more.files.made-up.example/media/0123456789abcdef/made-up-homes.zip",
        "https://files.made-up.example.elsewhere.example/media/0123456789abcdef/made-up-homes.zip",
        f"{HOST_AS_A_LOGIN}/media/0123456789abcdef/made-up-homes.zip",
        f"{LOGIN_AND_HOST}/media/0123456789abcdef/made-up-homes.zip",
        "https://elsewhere.example/files.made-up.example/media/0123456789abcdef/made-up-homes.zip",
        f"{HOST_AND_A_SLASH}/media/0123456789abcdef/made-up-homes.zip",
        "https://files.made-up.example:port/media/0123456789abcdef/made-up-homes.zip",
    ],
)
def test_an_address_on_another_host_port_or_scheme_is_not_named(address: str):
    assert not names(WHOLE, address)
    assert not is_a_file_of(source(), address)


def test_an_entry_that_names_no_address_has_no_file():
    assert not is_a_file_of(source(file_urls=[]), WHOLE)
    # Its own page and its evidence are pages. They are not the addresses of its files.
    assert not is_a_file_of(source(file_urls=[]), "https://made-up.example/homes")
    assert not is_a_file_of(source(file_urls=[]), "https://made-up.example/licence")


# What an entry may write under `file_urls`


def test_an_entry_with_a_whole_address_and_a_prefix_has_no_problems():
    assert check([source()], TODAY) == []
    assert check([source(file_urls=[])], TODAY) == []


@pytest.mark.parametrize(
    "address",
    [
        # A prefix that does not end at a dataset: the whole of a host.
        f"{HOST}/",
        HOST,
        # A prefix holds no parameter, and no address holds a part of a page.
        f"{PREFIX}?layers=0",
        f"{WHOLE}#sheet",
        # Not written plainly.
        f"{HOST}/media/../media/made-up-homes.zip",
        f"{HOST}/media/%2e%2e/made-up-homes.zip",
        f"{HOST}/media//made-up-homes.zip",
        f"{HOST}/media/made-up homes.zip",
        f"{HOST}\\media\\made-up-homes.zip",
        f"{HOST}/media/caf\u00e9.zip",
        "http://files.made-up.example/media/made-up-homes.zip",
        WITH_A_LOGIN,
        "files.made-up.example/media/made-up-homes.zip",
        "",
    ],
)
def test_an_address_of_a_file_is_written_plainly(address: str):
    assert PLAIN in rules_broken(source(file_urls=[address]))


def test_an_address_is_written_once_under_an_entry():
    assert PLAIN in rules_broken(source(file_urls=[WHOLE, WHOLE]))
    assert PLAIN in rules_broken(source(file_urls=[PREFIX, f"{PREFIX}csv"]))


def test_a_census_table_is_read_in_the_address_of_a_file_too():
    named = source(file_urls=[f"{HOST}/output/census/2021/census2021-ts021.zip"])
    assert "resident_tables_sit_under_residents_or_audit" in rules_broken(named)


# No address of one entry passes under another


def test_two_entries_on_one_host_that_each_name_their_own_files_have_no_problems():
    assert check([source(), source(AUDIT)], TODAY) == []


@pytest.mark.parametrize(
    "widened",
    [
        # The file of the other entry, its page, and a prefix that takes either in.
        [f"{HOST}/media/fedcba9876543210/made-up-classification.zip"],
        [f"{HOST}/media/FEDCBA9876543210/Made-Up-Classification.zip"],
        [f"{HOST}/media/fedcba9876543210/made-up-classification%2Ezip"],
        [f"{HOST}/media/fedcba9876543210/"],
        [f"{HOST}/media/"],
        [f"{HOST}/datasets/made-up-classification"],
        [f"{HOST}/datasets/"],
    ],
)
def test_an_entry_may_not_name_an_address_that_another_entry_holds(widened: list[str]):
    assert OF_ONE_ENTRY in rules_broken(source(file_urls=widened), source(AUDIT))
    assert OF_ONE_ENTRY in rules_broken(source(AUDIT), source(file_urls=widened))


def test_a_prefix_may_not_take_in_the_evidence_of_another_entry():
    other = source(AUDIT, evidence_urls=[f"{HOST}/api/download/items/0123456789abcdef/about"])
    assert OF_ONE_ENTRY in rules_broken(source(), other)


def test_two_prefixes_may_not_stand_one_inside_the_other():
    inner = source(AUDIT, file_urls=[f"{PREFIX}audit/"])
    assert OF_ONE_ENTRY in rules_broken(source(), inner)
    assert OF_ONE_ENTRY in rules_broken(inner, source())


def test_entries_may_share_a_page_that_is_no_file_of_either():
    licence = "https://made-up.example/licence"
    assert check([source(), source(AUDIT, evidence_urls=[licence])], TODAY) == []


def test_an_entry_may_hold_its_own_file_as_evidence_too():
    assert check([source(evidence_urls=[WHOLE, "https://made-up.example/licence"])], TODAY) == []


# The repository's own registry


@cache
def of_the_repository() -> Registry:
    return load(REPOSITORY / "registry" / "sources")


def test_the_repositorys_registry_breaks_no_rule_on_addresses():
    found = [p for p in check(of_the_repository(), TODAY) if p.rule in (PLAIN, OF_ONE_ENTRY)]
    assert found == []


def test_no_address_that_one_entry_holds_passes_under_another():
    """Every address every entry holds, its pages and its files, asked of every other entry."""
    registry = of_the_repository()
    with_files = [entry for entry in registry if entry.file_urls]
    assert with_files, "some entry of the repository names the addresses of its files"
    passed = [
        (other.id, entry.id)
        for entry in with_files
        for other in registry
        if other.id != entry.id
        for address in (other.url, *other.evidence_urls, *other.file_urls)
        if is_a_file_of(entry, address)
    ]
    assert passed == []


def test_no_file_of_one_entry_is_a_file_of_another():
    registry = of_the_repository()
    for one, other in permutations(registry, 2):
        for address in one.file_urls:
            # Under a prefix, a made-up name stands for every file there.
            asked = f"{address}made-up" if address.endswith("/") else address
            assert is_a_file_of(one, asked), one.id
            assert not is_a_file_of(other, asked), (one.id, other.id)


def test_the_gate_never_answers_from_a_registry_where_an_address_is_of_two_entries(tmp_path: Path):
    path = tmp_path / "registry.toml"
    path.write_text(_as_toml(source(), source(AUDIT)), encoding="utf-8")
    assert len(load(path).sources) == 2
    path.write_text(_as_toml(source(), source(AUDIT, file_urls=[WHOLE])), encoding="utf-8")
    with pytest.raises(RegistryError, match="made-up-classification"):
        load(path)


# An address that an entry holds, as a page or as a file


def test_an_entry_holds_its_pages_and_its_files():
    entry = source()
    for address in (WHOLE, f"{PREFIX}csv", "https://made-up.example/homes"):
        assert holds(entry, address)
    assert holds(entry, "https://made-up.example/licence#terms")
    assert holds(entry, "https://MADE-UP.example/Licence")
    for address in (f"{HOST}/media/fedcba9876543210/made-up-classification.zip", f"{HOST}/"):
        assert not holds(entry, address)


def _as_toml(*sources: Source) -> str:
    """Made-up entries as a registry file. A list of words is written in TOML as it is in JSON."""
    lines = ["schema_version = 1", ""]
    for entry in sources:
        lines.append("[[source]]")
        for name, value in entry.model_dump(mode="json", exclude_defaults=True).items():
            written = str(value) if name == "verified_on" else json.dumps(value)
            lines.append(f"{name} = {written}")
        lines.append("")
    return "\n".join(lines)
