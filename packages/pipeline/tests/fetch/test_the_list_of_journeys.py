"""The files a journey time is worked out from, as the lists and the registry have them.

Nothing is fetched here and no socket is opened. The list `m5-journeys` holds the one
file of a journey that no other list holds: the timetables of Transport for London. The
streets, the stops and the points a journey starts from are in the lists of the second
milestone, and a file is listed once. The stops are two files of one source. The rail
schedule is in no list while its entry is gated.

The made-up part of these tests is one address, on a host that is no publisher's. The
rest read the repository's own lists, its own registry and its own design, and no file of
any publisher.
"""

import re
from functools import cache
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

import pytest
from burro_pipeline.evidence.receipt import SECRET_NAME, Period
from burro_pipeline.fetch.gate import Reason, Refused, ask, host_of
from burro_pipeline.fetch.sources import LISTS, Listed, load_list
from burro_pipeline.registry import Registry, RegistryError, load
from burro_pipeline.registry.addresses import is_a_file_of
from burro_pipeline.registry.model import Use

REPOSITORY = Path(__file__).parents[4]
DESIGN = REPOSITORY / "docs" / "design" / "london-data-timetables.md"
LIST = "m5-journeys"
TIMETABLES = "tfl-journey-planner-timetables"
# The zip the publisher's page links. The page says it is not updated and is for
# demonstration only, so no entry names it and no list takes it.
EXAMPLE = "https://tfl.gov.uk/cdn/static/cms/documents/journey-planner-timetables.zip"

# Where every other file of a journey is listed, by the id of its source.
ELSEWHERE = {
    "osm-geofabrik-greater-london": "m2-living",
    "dft-naptan": "m2-living",
    "ons-lsoa-pwc-2021": "m2-places",
}
# The stops are two files of one source: London's, which a person saved, and the national
# file. Each is listed for scoring, which is what it is first put to. A step that routes asks
# the gate for routing when it opens a file, and the entry allows it.
STOPS = "dft-naptan"
ITEMS_OF_THE_STOPS = ("naptan-london", "naptan-national")

# What a journey by train waits on, and a second source of each timetable. None is
# approved, so none is in a list: one refusal stops every file of a list.
HELD_BACK = (
    "network-rail-nwr-schedule",
    "rdg-timetable-feed",
    "planarnetwork-gb-transit-rail-gtfs",
    "dft-bods-london-gtfs",
    "traveline-tnds",
)


@cache
def of_the_repository() -> Registry:
    """The repository's own registry, read once for all the tests here. It is frozen."""
    return load(REPOSITORY / "registry" / "sources")


@cache
def files() -> tuple[Listed, ...]:
    return load_list(LIST).files


def every_list() -> list[str]:
    return sorted(path.stem for path in LISTS.glob("*.toml"))


def holds_a_key(address: str) -> bool:
    """Whether an address names a parameter that is taken for a key."""
    asked = parse_qsl(urlsplit(address).query, keep_blank_values=True)
    return any(SECRET_NAME.search(name) for name, _ in asked)


def step(number: int) -> str:
    """One of the founder's steps, as the design's table has it."""
    rows = [
        line
        for line in DESIGN.read_text(encoding="utf-8").splitlines()
        if line.startswith(f"| {number} | ")
    ]
    (row,) = rows
    return row


def test_the_list_holds_the_timetables_of_transport_for_london():
    assert [file.source_id for file in files()] == [TIMETABLES]


def test_every_file_passes_the_gate_as_the_registry_stands():
    registry = of_the_repository()
    for file in files():
        assert ask(file, registry).id == file.source_id, file.item


def test_every_file_is_asked_for_as_a_part_of_a_journey():
    assert {file.use for file in files()} == {Use.ROUTING}


def test_every_page_is_the_entrys_own_letter_for_letter():
    registry = of_the_repository()
    for file in files():
        source = registry.get(file.source_id)
        assert file.page in (source.url, *source.evidence_urls), file.item


def test_a_file_has_an_address_only_where_its_entry_names_one():
    """The page of the timetables names no address of the file that is kept up to date. The
    list held none until 2026-09-24, when the entry came to name the address the
    publisher's staff wrote on its own forum. The two change together, or this fails."""
    registry = of_the_repository()
    for file in files():
        source = registry.get(file.source_id)
        assert file.has_an_address == bool(source.file_urls), file.item
        if file.has_an_address:
            assert is_a_file_of(source, file.url), file.item


def test_the_address_is_on_the_publishers_own_host_and_its_notes_say_where_it_was_read():
    """The address was read on the publisher's forum and on no page the entry holds. So the
    notes say where, and that a fetch has since taken the file from it, with no key."""
    registry = of_the_repository()
    for file in files():
        if file.has_an_address:
            source = registry.get(file.source_id)
            assert host_of(file.url) == host_of(source.url), file.item
            assert "url" not in file.unsure, file.item
            assert "techforum.tfl.gov.uk" in file.notes, file.item
            assert "A fetch took the file from it on 2026-09-24" in file.notes, file.item
            assert "the file asks for no key of an account" in file.notes, file.item


def test_every_address_the_entry_names_is_of_the_one_zip():
    """A request for the address in the list may be sent on. The entry names where it may
    end, which is the same file by its name, on the same host."""
    source = of_the_repository().get(TIMETABLES)
    assert source.file_urls
    for named in source.file_urls:
        assert host_of(named) == host_of(source.url), named
        assert named.endswith("/journey-planner-timetables.zip"), named
    assert [file.url for file in files()] == [source.file_urls[0]]


def test_the_example_the_page_links_is_never_taken():
    """The page says of it that it is not updated. A time worked out from it would rest on
    a timetable of no known date, so the gate refuses it as a file of the entry."""
    registry = of_the_repository()
    assert not is_a_file_of(registry.get(TIMETABLES), EXAMPLE)
    for file in files():
        with pytest.raises(Refused) as refused:
            ask(file.model_copy(update={"url": EXAMPLE}), registry)
        assert refused.value.reason is Reason.NOT_THE_ADDRESS
        assert "not taken" in file.notes, file.item


def test_a_file_with_no_address_says_in_its_notes_where_one_was_read():
    """`plan --words` prints no comment of a list, so what a person needs is in the notes."""
    for file in files():
        if not file.has_an_address:
            assert "url" in file.unsure, file.item
            assert "techforum.tfl.gov.uk" in file.notes, file.item
            assert "register" in file.notes, file.item


def test_an_address_that_holds_the_key_of_an_account_is_known_for_one():
    """The portal asks for its key as a part of the address, so an address that a person
    copies from a browser may hold one."""
    assert holds_a_key("https://files.example/timetables.zip?app_key=made-up")
    assert holds_a_key("https://files.example/timetables.zip?day=monday&Subscription-Key=made-up")
    assert not holds_a_key("https://files.example/timetables.zip")
    assert not holds_a_key("https://files.example/timetables.zip?day=monday")


def test_no_address_the_registry_holds_names_a_key():
    """The registry is published. Its own rule on the addresses of files lets a parameter
    through, so this holds every address of every entry, and every one written in its notes."""
    for source in of_the_repository().sources:
        written = re.findall(r"https://[^\s'\"<>]+", source.notes)
        held = (source.url, source.licence_url, *source.evidence_urls, *source.file_urls)
        for address in (*held, *written):
            assert not holds_a_key(address), source.id


def test_a_file_with_no_address_says_to_write_it_down_with_no_key_in_it():
    """Whoever finds the address writes it in two published files, the list and the
    registry. So the notes of each say how it is written."""
    for file in files():
        if not file.has_an_address:
            assert "with no key in it" in file.notes, file.item
    assert "with no key in it" in of_the_repository().get(TIMETABLES).notes


def test_the_step_that_finds_the_address_says_to_leave_the_key_out():
    assert "with no key in it" in step(3)


def test_the_steps_that_save_a_copy_keep_a_name_and_a_key_out_of_the_repository():
    """`registry/evidence` takes nothing that holds personal data or the details of an
    account. An agreement as executed names whoever signed it."""
    assert "registry/evidence" in step(4)
    assert "signed out" in step(4)
    assert "names whoever signed it" in step(5)
    assert "stays with whoever signed it" in step(5)


def test_the_list_states_the_edition_and_the_period_as_the_file_gives_them():
    """The page states neither. The edition is the day in the names of the zips the file
    holds, written as they write it. The period is the days its timetables say they run on,
    and never the day the file was fetched. A program read both, and no person has."""
    (file,) = files()
    assert file.unsure == () and file.ready_for_a_receipt
    assert file.edition_from is None
    assert file.edition == "21092026"
    assert file.data_period == Period(start="2026-09-19", end="2026-12-23")
    for words in (
        "with `describe --inside`, by a program and by no person",
        "The edition: the name of each of the six zips ends in 21092026",
        "The period: every service states the day it runs from and the day it runs to",
        "never the day the file was fetched",
    ):
        assert words in file.notes, words


def test_the_notes_say_that_the_next_issue_is_another_file():
    """The file is replaced under one address, and what a list states is written on whatever
    arrives. So the notes say to read the next issue before a fetch that would take it."""
    (file,) = files()
    for words in (
        "The file is replaced under one address",
        "state both again before that fetch",
        "new=0",
    ):
        assert words in file.notes, words


def test_the_notes_say_what_the_page_does_not_name_and_the_file_holds():
    """The page names six kinds of service. The file holds a zip of buses that run in place of
    a train, and whether a step reads it is to be decided before one does."""
    (file,) = files()
    assert "The sixth zip is not on the page" in file.notes
    assert "Whether a step reads the sixth zip is to be decided before one does" in file.notes
    assert "named for the London Overground or for the Elizabeth line" in file.notes


def test_no_file_is_saved_by_hand():
    """A file saved by hand is held to an address of its entry as any other. Until the
    entry names one, saving it by hand would be refused too."""
    assert not [file.item for file in files() if file.by_hand]


def test_no_item_is_named_in_another_list():
    """A build may take several lists, and refuses two that give a file one name."""
    ours = {file.item for file in files()}
    for name in every_list():
        if name != LIST:
            assert not ours & {file.item for file in load_list(name).files}, name


def test_no_source_of_the_list_is_in_another_list():
    ours = {file.source_id for file in files()}
    for name in every_list():
        if name != LIST:
            assert not ours & {file.source_id for file in load_list(name).files}, name


@pytest.mark.parametrize(("source_id", "listed_in"), ELSEWHERE.items())
def test_every_other_file_of_a_journey_is_in_one_list_and_is_allowed_for_routing(
    source_id: str, listed_in: str
):
    found = [
        (name, file)
        for name in every_list()
        for file in load_list(name).files
        if file.source_id == source_id
    ]
    assert {name for name, _ in found} == {listed_in}
    items = sorted(file.item for _, file in found)
    if source_id == STOPS:
        assert items == sorted(ITEMS_OF_THE_STOPS)
        assert {file.use for _, file in found} == {Use.SCORING}
    else:
        # Listed once, and for routing.
        ((_, file),) = found
        assert file.use is Use.ROUTING
    for _, file in found:
        assert ask(file, of_the_repository()).status == "approved"
    # Whatever use the list states, the entry allows the source for a journey.
    of_the_repository().require(source_id, Use.ROUTING)


@pytest.mark.parametrize("source_id", HELD_BACK)
def test_a_source_that_is_held_back_is_in_no_list_and_is_refused_for_a_journey(source_id: str):
    registry = of_the_repository()
    assert registry.get(source_id).status in ("gated", "held")
    for name in every_list():
        assert source_id not in {file.source_id for file in load_list(name).files}, name
    with pytest.raises(RegistryError, match=source_id):
        registry.require(source_id, Use.ROUTING)


def test_the_header_of_the_list_names_every_source_it_leaves_to_another_list_or_holds_back():
    header = (LISTS / f"{LIST}.toml").read_text(encoding="utf-8").split("schema_version")[0]
    for source_id in (*ELSEWHERE, *HELD_BACK):
        assert source_id in header, source_id
