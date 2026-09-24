"""Where the files of the two lists after the first build are, as the registry and the lists
have it.

Nothing is fetched here and no socket is opened. Every address was read on a publisher's
page, through a reader that extracts the text of a page. Where a file has since been
fetched, its receipt is what shows which host it arrived from. The twin of
`test_first_build_addresses.py`, for the lists `m2-places` and `m2-living`.
"""

import re
from functools import cache
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

import pytest
from burro_pipeline.evidence.lock import read_receipts
from burro_pipeline.fetch.gate import ask, host_of, hosts_of
from burro_pipeline.fetch.sources import Listed, load_list
from burro_pipeline.registry import Registry, load
from burro_pipeline.registry.addresses import is_a_file_of

REPOSITORY = Path(__file__).parents[3]
REGISTRY = REPOSITORY / "registry" / "sources"
RECEIPTS = REPOSITORY / "data" / "receipts"
LISTS = ("m2-places", "m2-living")

PORTAL = "open-geography-portalx-ons.hub.arcgis.com"
DOWNLOADS = "api.os.uk"
ASSETS = "assets.publishing.service.gov.uk"
PLATFORM_FILES = "files.planning.data.gov.uk"

# The host a publisher hands its files out from, where that is not the host of its pages.
# Every other file of the two lists is on the host its page is on.
FILES_ARE_ON = {
    "ons-msoa-2021": PORTAL,
    "ons-lsoa-pwc-2021": PORTAL,
    "os-open-names": DOWNLOADS,
    "os-open-roads": DOWNLOADS,
    "os-open-greenspace": DOWNLOADS,
    "os-open-rivers": DOWNLOADS,
    "os-boundary-line": DOWNLOADS,
    "ofsted-state-funded-schools-mi": ASSETS,
    "hmlr-uk-house-price-index": "publicdata.landregistry.gov.uk",
    "nhs-ods": "www.odsdatasearchandexport.nhs.uk",
}

# The sources whose entry names the host of its files under `file_urls` alone, and was made
# to once a person had read the address in a browser. A fetch has tried each address since,
# and the receipt of each file gives the address it arrived from.
NAMED_AND_FETCHED = {
    "mhclg-planning-data-conservation-areas": PLATFORM_FILES,
    "historic-england-listed-buildings": PLATFORM_FILES,
}

# The one source with a file a person saved and a file that is fetched. The stops of London
# were saved from a form on the host of the publisher's pages. The national file is fetched
# from the publisher's API, which the entry names under `file_urls` alone. So the entry names
# two addresses, each whole: the one a file was saved from, and the one a list holds.
SAVED_AND_FETCHED = {"dft-naptan": "naptan.api.dft.gov.uk"}

# The files that have no address in a list and are not saved by a person, each with the host
# its publisher hands it out from. The entry of each names no address on that host, under
# `file_urls` or anywhere else.
HELD_BACK = {
    "price-paid-2025": "price-paid-data.publicdata.landregistry.gov.uk",
    "price-paid-2024": "price-paid-data.publicdata.landregistry.gov.uk",
    "price-paid-2023": "price-paid-data.publicdata.landregistry.gov.uk",
}

# The files a person saved, each with the host the browser recorded that it was saved from.
# The entry of each names that one address, whole. Three of the four hosts are not the host
# of the publisher's pages, and no page that was read names any of the three.
SAVED_FROM = {
    "naptan-london": "beta-naptan.dft.gov.uk",
    "gias-establishments": "ea-edubase-api-prod.azurewebsites.net",
    "police-crime-london": "policeuk-data.s3.amazonaws.com",
    "postcode-directory": "www.arcgis.com",
}

# Where the portal of the statistics office handed a download on to, in the first fetch.
SEEN_IN_THE_FIRST_FETCH = ("services1.arcgis.com", "hub.arcgis.com")


@cache
def of_the_repository() -> Registry:
    """The repository's own registry, read once for all the tests here. It is frozen."""
    return load(REGISTRY)


@cache
def files() -> tuple[Listed, ...]:
    return tuple(file for name in LISTS for file in load_list(name).files)


def with_an_address() -> list[Listed]:
    return [file for file in files() if file.has_an_address]


def saved_by_hand() -> list[Listed]:
    return [file for file in files() if file.by_hand]


def fetched(source_id: str) -> list[str]:
    """The addresses an entry names for its files that are not where a person saved one from.

    The address a file was saved from is held by the tests of a file a person saved. Every
    other address of an entry is held by the tests of a file that is fetched.
    """
    saved_from = {SAVED_FROM[file.item] for file in saved_by_hand() if file.source_id == source_id}
    named = of_the_repository().get(source_id).file_urls
    return [address for address in named if host_of(address) not in saved_from]


# The registry


ELSEWHERE = FILES_ARE_ON | NAMED_AND_FETCHED | SAVED_AND_FETCHED


@pytest.mark.parametrize(("source_id", "files_are_on"), ELSEWHERE.items())
def test_an_entry_names_the_host_its_files_are_on(source_id: str, files_are_on: str):
    assert files_are_on in hosts_of(of_the_repository().get(source_id))


@pytest.mark.parametrize(("source_id", "files_are_on"), FILES_ARE_ON.items())
def test_an_entry_that_names_a_host_for_its_files_says_that_it_is_no_evidence_of_the_licence(
    source_id: str, files_are_on: str
):
    source = of_the_repository().get(source_id)
    assert files_are_on != host_of(source.url)
    assert files_are_on in source.notes
    assert "no evidence of the licence" in source.notes


@pytest.mark.parametrize("source_id", ELSEWHERE)
def test_an_entry_that_names_a_host_for_its_files_is_approved(source_id: str):
    assert of_the_repository().get(source_id).status == "approved"


@pytest.mark.parametrize(("source_id", "files_are_on"), NAMED_AND_FETCHED.items())
def test_a_host_named_under_file_urls_alone_is_the_host_a_fetch_arrived_from(
    source_id: str, files_are_on: str
):
    """The entry names the host nowhere but under `file_urls`, so no address on it passes
    for evidence of the licence. What shows that the address is the file's is a receipt."""
    source = of_the_repository().get(source_id)
    assert files_are_on not in {host_of(held) for held in (source.url, *source.evidence_urls)}
    assert {host_of(held) for held in source.file_urls} == {files_are_on}
    if RECEIPTS.is_dir():
        assert arrived_from(source_id) == {files_are_on}


@pytest.mark.parametrize(("source_id", "files_are_on"), SAVED_AND_FETCHED.items())
def test_an_entry_with_a_saved_file_and_a_fetched_one_names_the_address_of_each_and_no_other(
    source_id: str, files_are_on: str
):
    """The host of the fetched file is named nowhere but under `file_urls`, so no address on
    it passes for evidence of the licence. The entry names one address on it, which a list
    holds letter for letter, and one address a file was saved from. Each file has its
    receipt, which gives the address it arrived from."""
    source = of_the_repository().get(source_id)
    assert files_are_on not in {host_of(held) for held in (source.url, *source.evidence_urls)}
    (saved,) = [file for file in saved_by_hand() if file.source_id == source_id]
    (listed,) = [file for file in with_an_address() if file.source_id == source_id]
    assert fetched(source_id) == [listed.url] and host_of(listed.url) == files_are_on
    assert {host_of(held) for held in source.file_urls} == {files_are_on, SAVED_FROM[saved.item]}
    assert len(source.file_urls) == 2
    if RECEIPTS.is_dir():
        found = [receipt for receipt in read_receipts(RECEIPTS) if receipt.source_id == source_id]
        assert {(receipt.how, host_of(receipt.url)) for receipt in found} == {
            ("by_hand", SAVED_FROM[saved.item]),
            ("fetched", files_are_on),
        }


# The two lists


def test_every_file_passes_the_gate_as_the_registry_stands():
    """The gate itself: the use, the page, the host, and what the file says it is."""
    registry = of_the_repository()
    for file in files():
        assert ask(file, registry).id == file.source_id, file.item


def test_every_file_has_an_address_is_saved_by_hand_or_is_held_back_by_name():
    without = {file.item for file in files() if not file.has_an_address and not file.by_hand}
    assert without == set(HELD_BACK)


def test_a_file_is_held_back_only_while_its_entry_does_not_name_its_host():
    """When an entry comes to name the address, it goes back in the list. Until then the
    notes say which host it is on, because `plan --words` prints no comment of a list."""
    registry = of_the_repository()
    for file in files():
        files_are_on = HELD_BACK.get(file.item)
        if files_are_on:
            source = registry.get(file.source_id)
            assert files_are_on not in hosts_of(source), file.item
            assert not [held for held in source.file_urls if host_of(held) == files_are_on]
            assert files_are_on in file.notes, file.item


def test_every_file_a_person_saves_is_named_with_the_host_it_was_saved_from():
    assert {file.item for file in saved_by_hand()} == set(SAVED_FROM)
    for file in saved_by_hand():
        assert not file.has_an_address, file.item
        assert SAVED_FROM[file.item] in file.notes, file.item


def test_the_entry_of_a_file_a_person_saved_names_one_whole_address_and_no_prefix():
    """A prefix takes in every address under it. The address a file was saved from names
    that file and no other, so the entry is no wider than what a person saved."""
    registry = of_the_repository()
    for file in saved_by_hand():
        source = registry.get(file.source_id)
        # One address on the host it was saved from. Any other the entry names is the
        # address of a file that is fetched, which a list holds letter for letter.
        (named,) = [held for held in source.file_urls if held not in fetched(file.source_id)]
        assert len(source.file_urls) == 1 or file.source_id in SAVED_AND_FETCHED, file.item
        assert host_of(named) == SAVED_FROM[file.item], file.item
        assert not named.endswith("/") and not urlsplit(named).query, file.item
        assert SAVED_FROM[file.item] in source.notes, file.item
        assert "no evidence of the licence" in source.notes, file.item


def test_the_receipt_of_a_file_a_person_saved_holds_the_address_its_entry_names():
    """The receipt is the record. It says `by_hand`, and holds the address with no
    parameter: a browser may be given an address with a key in it."""
    found = read_receipts(RECEIPTS) if RECEIPTS.is_dir() else ()
    registry = of_the_repository()
    for file in saved_by_hand():
        kept = [
            receipt
            for receipt in found
            if (receipt.source_id, receipt.edition) == (file.source_id, file.edition)
        ]
        assert len(kept) == 1, file.item
        (receipt,) = kept
        assert (receipt.how, receipt.use) == ("by_hand", file.use), file.item
        assert receipt.data_period == file.data_period, file.item
        assert receipt.url in registry.get(file.source_id).file_urls, file.item
        assert not urlsplit(receipt.url).query and receipt.listed_url is None, file.item
        assert receipt.bytes <= file.max_bytes, file.item


def test_every_page_is_the_entrys_own_letter_for_letter():
    registry = of_the_repository()
    for file in files():
        source = registry.get(file.source_id)
        assert file.page in (source.url, *source.evidence_urls), file.item


def test_every_address_is_on_the_host_its_publisher_hands_files_out_from():
    registry = of_the_repository()
    assert with_an_address()
    for file in with_an_address():
        files_are_on = ELSEWHERE.get(file.source_id, host_of(file.page))
        assert host_of(file.url) == files_are_on, file.item
        assert host_of(file.url) in hosts_of(registry.get(file.source_id)), file.item


def test_every_address_is_one_that_the_entry_of_its_source_names_for_its_files():
    registry = of_the_repository()
    for file in with_an_address():
        assert is_a_file_of(registry.get(file.source_id), file.url), file.item


def test_an_entry_names_no_address_for_its_files_that_no_list_holds():
    """An address under `file_urls` is one that a list holds, or the prefix of one. So an
    entry is never wider than the files that were read on its publisher's page."""
    registry = of_the_repository()
    listed = [file for name in ("m1", *LISTS) for file in load_list(name).files]
    for source_id in {file.source_id for file in with_an_address()}:
        held = [file.url for file in listed if file.source_id == source_id and file.url]
        assert len(fetched(source_id)) == len(registry.get(source_id).file_urls) - (
            source_id in SAVED_AND_FETCHED
        )
        for named in fetched(source_id):
            if named.endswith("/"):
                assert any(address.startswith(named) for address in held), source_id
            else:
                assert named in held, source_id


def test_a_prefix_is_named_only_where_it_ends_at_an_item_that_the_entry_holds():
    """A prefix takes in every address under it. So one is named only on the portal, where
    the path names the item, and the entry holds the id of that item from another page."""
    registry = of_the_repository()
    sources = [registry.get(source_id) for source_id in {file.source_id for file in files()}]
    prefixes = [
        (source, address)
        for source in sources
        for address in source.file_urls
        if address.endswith("/")
    ]
    assert {source.id for source, _ in prefixes} == {"ons-msoa-2021", "ons-lsoa-pwc-2021"}
    for source, address in prefixes:
        found = re.fullmatch(
            rf"https://{re.escape(PORTAL)}/api/download/v1/items/([0-9a-f]{{32}})/", address
        )
        assert found is not None, source.id
        assert any(f"/content/items/{found[1]}?" in held for held in source.evidence_urls)


def test_the_addresses_of_an_entrys_files_are_on_the_one_host_its_files_are_on():
    for file in with_an_address():
        named = fetched(file.source_id)
        assert {host_of(address) for address in named} == {host_of(file.url)}, file.item


def test_an_address_on_the_portal_names_an_item_that_the_entry_holds():
    """The portal names a file by the id of its item. The entry holds that id from another
    page, read by other people. So the id in an address was not made up."""
    registry = of_the_repository()
    on_the_portal = [file for file in with_an_address() if host_of(file.url) == PORTAL]
    assert len(on_the_portal) == 2
    for file in on_the_portal:
        found = re.fullmatch(
            r"/api/download/v1/items/([0-9a-f]{32})/[A-Za-z]+", urlsplit(file.url).path
        )
        assert found is not None, file.item
        held = registry.get(file.source_id).evidence_urls
        assert any(f"/content/items/{found[1]}?" in address for address in held), file.item


def test_an_address_in_the_download_service_names_the_product_whose_record_the_entry_holds():
    """Ordnance Survey names a file by its product. The entry holds the record of that
    product, so a file of one product is not fetched under the entry of another."""
    registry = of_the_repository()
    in_the_service = [file for file in with_an_address() if host_of(file.url) == DOWNLOADS]
    assert len(in_the_service) == 6
    for file in in_the_service:
        found = re.fullmatch(
            r"(/downloads/v1/products/[A-Za-z]+)/downloads", urlsplit(file.url).path
        )
        assert found is not None, file.item
        held = registry.get(file.source_id).evidence_urls
        assert f"https://{DOWNLOADS}{found[1]}" in held, file.item


def test_no_address_holds_a_login_a_part_of_a_page_or_a_parameter_the_list_does_not_name():
    for file in with_an_address():
        parts = urlsplit(file.url)
        assert parts.username is None and parts.password is None, file.item
        assert parts.fragment == "", file.item
        held = [name for name, _ in parse_qsl(parts.query, keep_blank_values=True)]
        assert sorted(held) == sorted(file.url_parameters), file.item
        # What says where a reader came from is no part of a file's address.
        assert not any(name.startswith("utm_") for name in held), file.item


def arrived_from(source_id: str) -> set[str]:
    """The hosts a fetch of a source ended on, as its receipts have it."""
    found = read_receipts(RECEIPTS) if RECEIPTS.is_dir() else ()
    return {host_of(receipt.url) for receipt in found if receipt.source_id == source_id}


def test_a_host_a_download_is_handed_on_to_is_named_only_where_a_fetch_has_seen_it():
    """Nobody has seen where any other publisher sends a download. A fetch that is sent on
    stops and says so, and a person names the host then. What shows that a fetch saw a host
    is a receipt: it holds the address the file arrived from."""
    for file in files():
        if file.has_an_address and host_of(file.url) == PORTAL:
            assert set(SEEN_IN_THE_FIRST_FETCH) <= set(file.may_redirect_to), file.item
        else:
            assert set(file.may_redirect_to) <= arrived_from(file.source_id), file.item


def test_only_the_download_service_is_seen_to_hand_a_download_on():
    """Beside the portal of the statistics office, which the first fetch met."""
    handed_on = {host_of(file.url) for file in with_an_address() if file.may_redirect_to}
    assert handed_on == {PORTAL, DOWNLOADS}


def test_each_file_says_when_its_address_was_read_and_through_what():
    for file in with_an_address():
        assert re.search(r"Address read on \d{4}-\d{2}-\d{2}", file.notes), file.item
        assert "through a reader that extracts" in file.notes, file.item


def test_what_nobody_has_tried_is_still_marked_as_not_sure():
    """No fetch has tried an address on a host that was named for this change."""
    for file in with_an_address():
        if file.source_id in FILES_ARE_ON:
            assert "url" in file.unsure, file.item
