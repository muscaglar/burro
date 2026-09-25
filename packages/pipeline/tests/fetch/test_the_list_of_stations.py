"""The list of the station data of Transport for London, held to the registry.

Nothing is fetched and no socket is opened. The list, the registry and the
receipt are the repository's own.

The publisher hands out two files of its stations. One names the modes and the
lines at each station, and is taken. The other holds the ways through a station
and no mode, and is not. These hold the list to the file it names, and the entry
to what it says of it.
"""

import json
from functools import cache
from pathlib import Path

import pytest
from burro_pipeline.derive import tfl_stations
from burro_pipeline.evidence import Period
from burro_pipeline.fetch.gate import Reason, Refused, ask, host_of, part_of
from burro_pipeline.fetch.sources import LISTS, Listed, load_list
from burro_pipeline.fetch.store import Part
from burro_pipeline.registry import Registry, Use, load

REPOSITORY = Path(__file__).parents[4]
REGISTRY = REPOSITORY / "registry" / "sources"
RECEIPTS = REPOSITORY / "data" / "receipts"
NAME = "m2-stations"
STATIONS = "tfl-step-free-station-topology"
FILES_ARE_ON = "api.tfl.gov.uk"
# What the publisher hands out beside the file that is taken. It is no file of the list.
NEVER_TAKEN = (
    "https://api.tfl.gov.uk/stationdata/tfl-stationdata-gtfs.zip",
    "https://api.tfl.gov.uk/stationdata/tfl-stationdata-detailed-2025.zip",
    "https://tfl.gov.uk/cdn/static/cms/documents/tfl-stationdata-detailed.zip",
)


@cache
def of_the_repository() -> Registry:
    """The repository's own registry, read once for all the tests here. It is frozen."""
    return load(REGISTRY)


@cache
def the_file() -> Listed:
    (file,) = load_list(NAME).files
    return file


def test_the_list_holds_the_one_file_that_names_the_modes_at_each_station():
    file = the_file()
    assert (file.item, file.source_id, file.use) == ("tfl-station-data", STATIONS, Use.SCORING)
    assert file.format == "zip" and "modes and lines" in file.what
    # It is the file the reader of stations is written to read, by the publisher's name.
    assert tfl_stations.is_the_file(file.url.rsplit("/", 1)[-1])
    assert tfl_stations.SOURCE == STATIONS


def test_the_file_passes_the_gate_and_is_for_the_store_of_the_product():
    source = ask(the_file(), of_the_repository())
    assert (source.id, source.status) == (STATIONS, "approved")
    assert part_of(the_file().use, source) is Part.PRODUCT
    assert set(source.uses) == {Use.SCORING, Use.DISPLAY}


def test_the_page_is_the_entrys_own_and_the_address_is_the_one_it_names():
    source = of_the_repository().get(STATIONS)
    assert the_file().page == source.url
    assert source.file_urls == (the_file().url,)
    assert host_of(the_file().url) == FILES_ARE_ON
    assert not the_file().url.endswith("/")


def test_the_file_bears_no_edition_so_its_edition_and_its_period_are_the_day_it_arrived():
    file = the_file()
    assert not file.edition and file.data_period is None
    assert file.edition_from is not None
    assert (file.edition_from.where, file.edition_from.period_too) == ("retrieved", True)
    assert set(file.unsure) == {"max_bytes"}
    assert file.ready_for_a_receipt and not file.by_hand
    assert "its edition and its period are the day it was retrieved" in file.notes


@pytest.mark.parametrize("address", NEVER_TAKEN)
def test_a_file_the_list_does_not_take_is_refused_under_the_same_entry(address: str):
    with pytest.raises(Refused) as refused:
        ask(the_file().model_copy(update={"url": address}), of_the_repository())
    assert refused.value.reason in (Reason.NOT_THE_ADDRESS, Reason.NOT_THE_HOST)


def test_the_entry_says_what_is_asked_of_whoever_shows_a_figure_made_from_it():
    source = of_the_repository().get(STATIONS)
    said = " ".join(source.conditions)
    assert "Register on the TfL API portal first" in said
    assert "wherever a station fact from this data is shown" in said
    assert "Do not present absence as a fact about a station" in said
    # So the statement of credit goes with every fact that cites the source.
    assert source.attribution_beside_figures is True
    assert source.attribution.startswith("Powered by TfL Open Data")


def test_the_receipt_that_is_kept_is_of_the_file_the_list_names():
    (path,) = sorted((RECEIPTS / STATIONS).glob("*.json"))
    receipt = json.loads(path.read_text(encoding="utf-8"))
    file = the_file()
    assert (receipt["source_id"], receipt["use"]) == (STATIONS, file.use.value)
    assert receipt["listed_url"] == receipt["url"] == file.url
    assert receipt["publisher_file"] == tfl_stations.FILE
    assert path.stem == receipt["file_id"] == f"f-{receipt['sha256'][:12]}"
    # The day it was retrieved is its edition and its period, as the list says.
    day = receipt["retrieved_at"][:10]
    assert receipt["edition"] == f"retrieved {day}"
    assert Period.model_validate(receipt["data_period"]) == Period(as_at=day)
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
    for words in ("tfl-stationdata-gtfs.zip", "m5-journeys", "m2-living"):
        assert words in header, words
    assert "registered on" in header and "2026-09-24" in header
