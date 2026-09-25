"""The list of the road traffic counts, held to the registry.

Nothing is fetched and no socket is opened. The list, the registry and the
receipt are the repository's own.

The publisher offers several files on one page, from one folder of one host.
One gives the flow of an average day at each count point, and is taken. These
hold the list to that file, and the entry to what it says of a street that
nobody counted.
"""

import json
from functools import cache
from pathlib import Path

import pytest
from burro_pipeline.evidence import Period
from burro_pipeline.fetch.gate import Reason, Refused, ask, host_of, part_of
from burro_pipeline.fetch.sources import LISTS, Listed, load_list
from burro_pipeline.fetch.store import Part
from burro_pipeline.registry import Registry, Use, load

REPOSITORY = Path(__file__).parents[4]
REGISTRY = REPOSITORY / "registry" / "sources"
RECEIPTS = REPOSITORY / "data" / "receipts"
NAME = "m13-road-traffic"
COUNTS = "dft-road-traffic-counts"
FILES_ARE_ON = "storage.googleapis.com"
FOLDER = f"https://{FILES_ARE_ON}/dft-statistics/road-traffic"
# What the publisher offers beside the file that is taken. None is a file of the list.
NEVER_TAKEN = (
    f"{FOLDER}/downloads/data-gov-uk/count_points.zip",
    f"{FOLDER}/downloads/data-gov-uk/dft_traffic_counts_raw_counts.zip",
    f"{FOLDER}/downloads/data-gov-uk/dft_traffic_counts_aadf_by_direction.zip",
    f"{FOLDER}/downloads/data-gov-uk/local_authority_traffic.csv",
    f"{FOLDER}/mrdb-2025.zip",
    f"{FOLDER}/all-traffic-data-metadata.pdf",
)


@cache
def of_the_repository() -> Registry:
    """The repository's own registry, read once for all the tests here. It is frozen."""
    return load(REGISTRY)


@cache
def the_file() -> Listed:
    (file,) = load_list(NAME).files
    return file


def test_the_list_holds_the_one_file_of_the_flow_at_each_count_point():
    file = the_file()
    assert (file.item, file.source_id, file.use) == ("dft-aadf", COUNTS, Use.SCORING)
    assert file.format == "zip" and "Annual average daily flow" in file.what
    assert file.url.endswith("/dft_traffic_counts_aadf.zip")


def test_the_file_passes_the_gate_and_is_for_the_store_of_the_product():
    source = ask(the_file(), of_the_repository())
    assert (source.id, source.status) == (COUNTS, "approved")
    assert part_of(the_file().use, source) is Part.PRODUCT
    assert set(source.uses) == {Use.SCORING, Use.VALIDATION_ONLY}


def test_the_page_is_the_entrys_own_and_the_address_is_the_one_it_names():
    source = of_the_repository().get(COUNTS)
    assert the_file().page == source.url
    assert source.file_urls == (the_file().url,)
    assert host_of(the_file().url) == FILES_ARE_ON
    # The host holds the files of many publishers, so the entry names the file whole.
    assert not any(address.endswith("/") for address in source.file_urls)


def test_the_edition_is_the_day_it_arrived_and_the_period_is_the_years_the_page_states():
    file = the_file()
    assert not file.edition and file.edition_from is not None
    assert (file.edition_from.where, file.edition_from.period_too) == ("retrieved", False)
    assert file.data_period == Period(start="2000", end="2025")
    # A fetch has tried the address, and what arrived is well under the most allowed.
    assert not file.unsure
    assert file.ready_for_a_receipt and not file.by_hand
    assert "never the period of the file" in file.notes


@pytest.mark.parametrize("address", NEVER_TAKEN)
def test_a_file_the_list_does_not_take_is_refused_under_the_same_entry(address: str):
    with pytest.raises(Refused) as refused:
        ask(the_file().model_copy(update={"url": address}), of_the_repository())
    assert refused.value.reason is Reason.NOT_THE_ADDRESS


def test_the_entry_says_that_a_street_nobody_counted_has_no_figure():
    source = of_the_repository().get(COUNTS)
    said = " ".join(source.conditions)
    assert "minor roads are sampled" in said
    assert "has no figure, and none is ever filled in" in said
    assert "never as nought" in said
    assert "a figure is given with the year it is of" in said


def test_the_entry_says_what_the_publisher_asks_of_whoever_shows_a_figure():
    source = of_the_repository().get(COUNTS)
    said = " ".join(source.conditions)
    assert "marked Estimated should be used with caution" in said
    assert "a note of their limitations in any published material" in said
    assert "never added together" in said
    # The pages give no wording of credit, so none is said to have been read.
    assert source.attribution_verified is False


def test_the_note_the_publisher_asks_for_stands_with_its_credit_beside_every_figure():
    """The publisher asks for a note of the limits of its estimates in anything that is
    published. The entry holds it, in the words of the publisher's page, and asks for its
    credit beside every figure, so that a release carries both to every fact."""
    source = of_the_repository().get(COUNTS)
    assert source.attribution_beside_figures is True
    assert source.said_with_attribution == (
        "The Department for Transport says that its estimates of traffic for a road link are "
        "less robust than its figures for a region or for the country, because they are not "
        "always based on up-to-date counts made at the place."
    )
    # The credit is the licence's own wording, and holds none of the note.
    assert "robust" not in source.attribution
    assert not [left for left in source.before_launch if "limitations" in left]


def test_the_entry_says_why_it_was_promoted():
    source = of_the_repository().get(COUNTS)
    assert "Promoted from held on 2026-09-25" in source.status_reason
    assert "a measure now needs it" in source.status_reason
    assert "none was done" in source.status_reason


def test_the_receipt_that_is_kept_is_of_the_file_the_list_names():
    (path,) = sorted((RECEIPTS / COUNTS).glob("*.json"))
    receipt = json.loads(path.read_text(encoding="utf-8"))
    file = the_file()
    assert (receipt["source_id"], receipt["use"]) == (COUNTS, file.use.value)
    # The request was not sent on: the file came from the address the list names.
    assert receipt["listed_url"] == receipt["url"] == file.url
    assert receipt["publisher_file"] == file.url.rsplit("/", 1)[-1]
    assert path.stem == receipt["file_id"] == f"f-{receipt['sha256'][:12]}"
    # The day it was retrieved is its edition, and its period is the list's.
    assert receipt["edition"] == f"retrieved {receipt['retrieved_at'][:10]}"
    assert Period.model_validate(receipt["data_period"]) == file.data_period
    assert 0 < receipt["bytes"] <= file.max_bytes


def test_no_item_and_no_source_of_the_list_is_in_another_list():
    """A build may take several lists, and refuses two that give a file one name."""
    for path in sorted(LISTS.glob("*.toml")):
        if path.stem != NAME:
            others = load_list(path.stem).files
            assert the_file().item not in {file.item for file in others}, path.stem
            assert the_file().source_id not in {file.source_id for file in others}, path.stem


def test_the_header_of_the_list_names_what_it_leaves_out():
    header = (LISTS / f"{NAME}.toml").read_text(encoding="utf-8").split("schema_version")[0]
    said = " ".join(header.replace("#", " ").split())
    for words in ("count points", "raw counts", "by direction", "Major Roads Database"):
        assert words in said, words
    assert "it was not built from a pattern" in said and "2026-09-25" in said
