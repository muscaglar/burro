"""Where the files of the first real build are, as the registry and the list have it.

Nothing is fetched here and no socket is opened. No file has been fetched at all: every
address was read on a publisher's page, through a reader that extracts the text of a page.
"""

import re
from functools import cache
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from burro_pipeline.fetch.sources import Listed, load_list
from burro_pipeline.registry import Registry, Source, load
from burro_pipeline.registry.addresses import is_a_file_of

REPOSITORY = Path(__file__).parents[3]
REGISTRY = REPOSITORY / "registry" / "sources"


@cache
def of_the_repository() -> Registry:
    """The repository's own registry, read once for all the tests here. It is frozen."""
    return load(REGISTRY)


PORTAL = "open-geography-portalx-ons.hub.arcgis.com"
ASSETS = "assets.publishing.service.gov.uk"

# The host each publisher hands its files out from, as its own page lists them.
FILES_ARE_ON = {
    "ons-oa21-lsoa21-msoa21-lad22-lookup": PORTAL,
    "ons-output-areas-2021": PORTAL,
    "ons-oa-pwc-2021": PORTAL,
    "ons-lsoa-2021": PORTAL,
    "ons-census-2021-housing-tables": "www.nomisweb.co.uk",
    "voa-council-tax-stock-of-properties": ASSETS,
    "mhclg-iod-2025-underlying-indicators": ASSETS,
    "defra-pcm-background-air": "uk-air.defra.gov.uk",
}


def host(address: str) -> str:
    return (urlsplit(address).hostname or "").lower()


def hosts_named_by(source: Source) -> set[str]:
    """The hosts of an entry's own page and of its evidence. Its licence's host is not one."""
    return {host(address) for address in (source.url, *source.evidence_urls)}


@pytest.mark.parametrize(("source_id", "files_are_on"), FILES_ARE_ON.items())
def test_an_entry_behind_the_first_build_names_the_host_its_files_are_on(
    source_id: str, files_are_on: str
):
    source = of_the_repository().get(source_id)
    assert files_are_on in hosts_named_by(source)


@pytest.mark.parametrize(("source_id", "files_are_on"), FILES_ARE_ON.items())
def test_an_entry_that_names_a_host_for_its_files_says_that_it_is_no_evidence_of_the_licence(
    source_id: str, files_are_on: str
):
    source = of_the_repository().get(source_id)
    if files_are_on == host(source.url):
        return
    assert files_are_on in source.notes
    assert "no evidence of the licence" in source.notes


# The list of the first build


def files() -> tuple[Listed, ...]:
    return load_list("m1").files


def test_every_file_of_the_first_build_has_an_address_or_is_saved_by_hand():
    assert [file.item for file in files() if not file.has_an_address and not file.by_hand] == []


def test_every_page_of_the_first_build_is_the_entrys_own_letter_for_letter():
    registry = of_the_repository()
    for file in files():
        source = registry.get(file.source_id)
        assert file.page in (source.url, *source.evidence_urls), file.item


def test_every_address_is_on_a_host_that_the_entry_of_its_source_names():
    registry = of_the_repository()
    for file in files():
        assert host(file.url) == FILES_ARE_ON[file.source_id], file.item
        assert host(file.url) in hosts_named_by(registry.get(file.source_id)), file.item


def test_every_address_is_one_that_the_entry_of_its_source_names_for_its_files():
    registry = of_the_repository()
    for file in files():
        assert is_a_file_of(registry.get(file.source_id), file.url), file.item


def test_a_prefix_is_named_only_where_it_ends_at_an_item_that_the_entry_holds():
    """A prefix takes in every address under it. So one is named only on the portal, where
    the path names the item, and the entry holds the id of that item from another page."""
    registry = of_the_repository()
    prefixes = [
        (source, address)
        for source in (registry.get(source_id) for source_id in FILES_ARE_ON)
        for address in source.file_urls
        if address.endswith("/")
    ]
    assert prefixes
    for source, address in prefixes:
        found = re.fullmatch(
            rf"https://{re.escape(PORTAL)}/api/download/v1/items/([0-9a-f]{{32}})/", address
        )
        assert found is not None, source.id
        assert any(f"/content/items/{found[1]}?" in held for held in source.evidence_urls)


def test_a_folder_that_holds_other_datasets_is_named_by_no_prefix():
    registry = of_the_repository()
    for source_id, files_are_on in FILES_ARE_ON.items():
        named = registry.get(source_id).file_urls
        assert named, source_id
        assert {host(address) for address in named} == {files_are_on}, source_id
        if files_are_on != PORTAL:
            assert not [address for address in named if address.endswith("/")], source_id


def test_an_address_on_the_portal_names_an_item_that_the_entry_holds():
    """The portal names a file by the id of its item. The entry holds that id from another
    page, read by other people. So the id in an address was not made up."""
    registry = of_the_repository()
    on_the_portal = [file for file in files() if host(file.url) == PORTAL]
    assert on_the_portal
    for file in on_the_portal:
        found = re.fullmatch(
            r"/api/download/v1/items/([0-9a-f]{32})/[A-Za-z]+", urlsplit(file.url).path
        )
        assert found is not None, file.item
        held = registry.get(file.source_id).evidence_urls
        assert any(f"/content/items/{found[1]}?" in address for address in held), file.item


def test_no_address_holds_a_login_a_key_or_a_part_of_a_page():
    for file in files():
        parts = urlsplit(file.url)
        assert parts.username is None and parts.password is None, file.item
        assert parts.query in ("", "layers=0"), file.item
        assert parts.fragment == "", file.item


def test_each_file_says_when_its_address_was_read_and_through_what():
    for file in files():
        assert re.search(r"Address read on \d{4}-\d{2}-\d{2}", file.notes), file.item
        assert "through a reader that extracts" in file.notes, file.item
