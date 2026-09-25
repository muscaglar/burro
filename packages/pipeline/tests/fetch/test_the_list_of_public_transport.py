"""The list of the accessibility grid and of the bus stops and routes, held to the registry.

Nothing is fetched and no socket is opened. The list and the registry are the
repository's own.

Each file is old, and says how old: the levels are of 2015, and the files of buses are of
3 October 2025. Each publisher links other files beside the one that is taken, and some
of those may never be: an example that is not updated, and a file under terms that grant
no reuse. These hold the list to the files it names, and the entries to what they say of
each.
"""

import re
from functools import cache
from pathlib import Path

import pytest
from burro_pipeline.evidence import Period
from burro_pipeline.fetch.gate import Reason, Refused, ask, host_of, part_of
from burro_pipeline.fetch.sources import LISTS, Listed, load_list
from burro_pipeline.fetch.store import Part
from burro_pipeline.registry import Registry, Use, load

REGISTRY = Path(__file__).parents[4] / "registry" / "sources"
NAME = "m12-public-transport"
LEVELS = "tfl-ptal-2015"
BUSES = "tfl-bus-stops-and-routes"
# The host each publisher hands its files out from.
FILES_ARE_ON = {LEVELS: "data.london.gov.uk", BUSES: "bus.data.tfl.gov.uk"}
DATASTORE = "https://data.london.gov.uk/download/24rz6"
STORE = "https://bus.data.tfl.gov.uk/stops-sequences"
# What each publisher links or keeps beside the file that is taken, by the source it would
# be asked for under. None is a file of its entry.
NEVER_TAKEN = {
    # The means of the areas of another census, as the page of the dataset lists two.
    LEVELS: (
        f"{DATASTORE}/77d9b319-931e-4090-bf8e-f578938bd352/LSOA2011%20AvPTAI2015.csv",
        f"{DATASTORE}/ca17d14f-379e-469e-917c-ff1f21c5e3d4/COA2011%20AvPTAI2015.csv",
    ),
    # The two examples the open data page links, and a file of an earlier day.
    BUSES: (
        "https://tfl.gov.uk/cdn/static/cms/documents/bus-stops-example.csv",
        "https://tfl.gov.uk/cdn/static/cms/documents/stop-sequences-example.csv",
        f"{STORE}/Archived/Data_3rdParties_bus-sequences-20240714.csv",
        f"{STORE}/Data_3rdParties_bus-sequences-20240714.csv",
    ),
}


@cache
def of_the_repository() -> Registry:
    """The repository's own registry, read once for all the tests here. It is frozen."""
    return load(REGISTRY)


@cache
def files() -> tuple[Listed, ...]:
    return load_list(NAME).files


def of_the_source(source_id: str) -> list[Listed]:
    return [file for file in files() if file.source_id == source_id]


def test_the_list_holds_the_grid_and_the_two_files_of_buses():
    assert [(file.item, file.source_id, file.use) for file in files()] == [
        ("ptal-grid-2015", LEVELS, Use.SCORING),
        ("bus-sequences", BUSES, Use.SCORING),
        ("bus-stops", BUSES, Use.SCORING),
    ]


def test_every_file_passes_the_gate_and_is_for_the_store_of_the_product():
    registry = of_the_repository()
    for file in files():
        source = ask(file, registry)
        assert (source.id, source.status) == (file.source_id, "approved"), file.item
        assert part_of(file.use, source) is Part.PRODUCT, file.item


def test_every_page_is_the_entrys_own_and_every_address_is_one_it_names():
    registry = of_the_repository()
    for file in files():
        source = registry.get(file.source_id)
        assert file.page == source.url, file.item
        assert file.url in source.file_urls, file.item
        assert host_of(file.url) == FILES_ARE_ON[file.source_id], file.item


def test_an_entry_names_the_files_the_list_holds_and_no_other():
    """An address under `file_urls` is one the list holds, whole and never as a prefix. So
    an entry is no wider than the files that were read of its publisher."""
    registry = of_the_repository()
    for source_id in (LEVELS, BUSES):
        named = registry.get(source_id).file_urls
        assert sorted(named) == sorted(file.url for file in of_the_source(source_id))
        assert not [address for address in named if address.endswith("/")]


def test_each_file_states_its_edition_and_its_period_and_is_unsure_of_its_address_alone():
    for file in files():
        assert set(file.unsure) == {"url"}, file.item
        assert file.edition and file.data_period is not None, file.item
        assert file.ready_for_a_receipt, file.item
        assert not file.by_hand and file.edition_from is None, file.item
        assert not file.may_redirect_to, file.item


def test_the_levels_are_of_2015_and_every_word_of_the_item_says_so():
    (file,) = of_the_source(LEVELS)
    assert (file.edition, file.data_period) == ("2015", Period(as_at="2015"))
    assert "2015" in file.what and "2015" in file.url
    assert "every figure says that it is of 2015" in file.notes


def test_the_day_of_a_file_of_buses_is_the_day_in_its_name():
    """The publisher's guide says the day of the data is in the name of the file. So the
    edition is that day as the name writes it, and the period is the same day."""
    for file in of_the_source(BUSES):
        found = re.fullmatch(r".*-(\d{4})(\d{2})(\d{2})\.csv", file.url)
        assert found is not None, file.item
        assert file.edition == "".join(found.groups()), file.item
        assert file.data_period == Period(as_at="-".join(found.groups())), file.item
        assert "The date is presented in the file name" in " ".join(
            (file.notes, of_the_repository().get(BUSES).notes)
        )


@pytest.mark.parametrize(
    ("source_id", "address"),
    [(source_id, address) for source_id, held in NEVER_TAKEN.items() for address in held],
)
def test_a_file_the_list_does_not_take_is_refused_under_the_same_entry(
    source_id: str, address: str
):
    for file in of_the_source(source_id):
        with pytest.raises(Refused) as refused:
            ask(file.model_copy(update={"url": address}), of_the_repository())
        assert refused.value.reason is Reason.NOT_THE_ADDRESS


def test_a_file_of_one_source_is_refused_under_the_entry_of_the_other():
    """An address is of one entry. The grid is no file of the buses, and the other way."""
    (levels,), (sequences, _) = of_the_source(LEVELS), of_the_source(BUSES)
    for file, address in ((levels, sequences.url), (sequences, levels.url)):
        with pytest.raises(Refused) as refused:
            ask(file.model_copy(update={"url": address}), of_the_repository())
        assert refused.value.reason in (Reason.NOT_THE_HOST, Reason.NOT_THE_ADDRESS)


def test_the_entry_of_the_levels_says_what_is_never_taken_and_how_old_a_figure_is():
    source = of_the_repository().get(LEVELS)
    said = " ".join(source.conditions)
    assert "Never take PTAL data from Transport for London's own pages or from WebCAT" in said
    assert "should no longer be used" in said
    assert "say beside every figure that it is of 2015" in said
    assert "No area is ranked on it until the founder has said" in said
    assert any("ranked on a figure of 2015" in item for item in source.before_launch)


def test_the_entry_of_the_buses_says_what_a_figure_must_show_and_never_count():
    source = of_the_repository().get(BUSES)
    said = " ".join(source.conditions)
    assert "Register on the TfL API portal before the first download" in said
    assert "Count no virtual bus stop as a stop" in said
    assert "Show beside every figure the day its file is of" in said
    assert "Never take either" in said
    assert any("older than the two weeks" in item for item in source.before_launch)


def test_each_file_says_when_its_address_was_read_and_through_what():
    for file in files():
        assert re.search(r"Address read on \d{4}-\d{2}-\d{2}", file.notes), file.item
        assert "through a reader that extracts" in file.notes, file.item
        assert "No fetch has tried it" in file.notes or "Open it once" in file.notes, file.item


def test_no_item_and_no_source_of_the_list_is_in_another_list():
    """A build may take several lists, and refuses two that give a file one name."""
    items = {file.item for file in files()}
    sources = {file.source_id for file in files()}
    for path in sorted(LISTS.glob("*.toml")):
        if path.stem != NAME:
            others = load_list(path.stem).files
            assert not items & {file.item for file in others}, path.stem
            assert not sources & {file.source_id for file in others}, path.stem


def test_the_header_of_the_list_names_what_it_leaves_out():
    header = (LISTS / f"{NAME}.toml").read_text(encoding="utf-8").split("schema_version")[0]
    for words in ("WebCAT", "bus-stops-example.csv", "stop-sequences-example.csv", "Archived"):
        assert words in header, words
    assert "m5-journeys" in header and "m2-living" in header
