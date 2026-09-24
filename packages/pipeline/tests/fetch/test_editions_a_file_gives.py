"""The files whose publisher's page names no edition, as the two lists say of them.

Forty files of the lists `m2-places` and `m2-living` have no edition on their
publisher's page: the food hygiene register of each of London's 33 authorities, the town
centre boundaries, two reports of NHS organisations, the street extract, the two files
of the planning data platform, which are conservation areas and listed buildings, and the
national file of stops. A list
cannot state the edition of a file that its publisher replaces under one address. So each
says where the file states its own, and fetch reads it in what arrives. These hold the
lists to that.

Nothing is fetched here, and no file of a publisher is opened. How fetch reads a file is
held on made-up files, by `test_the_day_a_file_gives.py`.
"""

import re
from functools import cache

from burro_pipeline.evidence import Where
from burro_pipeline.fetch.sources import Listed, load_list

LISTS = ("m2-places", "m2-living")
FOOD = "fsa-food-hygiene-ratings"
TOWN_CENTRES = "gla-town-centre-boundaries"
REPORTS = "nhs-ods"
STREETS = "osm-geofabrik-greater-london"
CONSERVATION = "mhclg-planning-data-conservation-areas"
LISTED = "historic-england-listed-buildings"
STOPS = "dft-naptan"

# Where each file states its own edition: the place, the words a receipt writes before the
# day, and whether the day is the period of the data too.
STATED_AT = {
    FOOD: (Where.XML_HEADER, "Header/ExtractDate", "extract of", True),
    # The day a GeoPackage was last changed is about the file. Fetch never takes it for the
    # period: the list states one.
    TOWN_CENTRES: (Where.GEOPACKAGE, "gpkg_contents.last_change", "last changed", False),
    # The time the publisher says the data runs to, written as the publisher writes it.
    STREETS: (Where.STREET_EXTRACT, "OSMHeader.osmosis_replication_timestamp", "", True),
    # The file holds no date. Its edition is the day it was retrieved, written so.
    REPORTS: (Where.RETRIEVED, "", "retrieved", True),
    # Each record holds the day it was entered, and nothing dates the file as a whole.
    CONSERVATION: (Where.RETRIEVED, "", "retrieved", True),
    LISTED: (Where.RETRIEVED, "", "retrieved", True),
}
# A source of two files, of which one is dated by its file, is told by the item. The stops of
# London were saved by a person, and the list states their edition. The national file is
# made again each day under one address, and holds no date of the file as a whole.
NATIONAL_STOPS = "naptan-national"
STATED_AT_OF_AN_ITEM = {NATIONAL_STOPS: (Where.RETRIEVED, "", "retrieved", True)}
A_DAY = r"(\d{4}-\d{2}-\d{2})"
THE_FILE_READ = re.compile(rf"in the file kept in the store on {A_DAY}, (f-[0-9a-f]{{12}})\b")


def stated_at(file: Listed) -> tuple[Where, str, str, bool] | None:
    """Where a file states its own edition, or nothing where its page names one."""
    return STATED_AT_OF_AN_ITEM.get(file.item, STATED_AT.get(file.source_id))


@cache
def dated_here() -> tuple[Listed, ...]:
    """The files whose page names no edition, of both lists."""
    return tuple(
        file for name in LISTS for file in load_list(name).files if stated_at(file) is not None
    )


def test_every_file_whose_page_names_no_edition_says_where_the_file_states_its_own():
    by_source = {source: 0 for source in (*STATED_AT, STOPS)}
    for file in dated_here():
        assert file.edition_from is not None, file.item
        by_source[file.source_id] += 1
    assert by_source == {
        STREETS: 1,
        FOOD: 33,
        TOWN_CENTRES: 1,
        REPORTS: 2,
        CONSERVATION: 1,
        LISTED: 1,
        STOPS: 1,
    }


def test_no_other_file_of_the_two_lists_is_dated_by_its_file():
    """Every other file has an edition on its publisher's page, and the list states it."""
    for name in LISTS:
        for file in load_list(name).files:
            if stated_at(file) is None:
                assert file.edition_from is None, file.item


def test_the_stops_a_person_saved_are_not_dated_by_their_file():
    """One source, two files: the list states the edition of the one a person saved."""
    of_the_source = [
        file for name in LISTS for file in load_list(name).files if file.source_id == STOPS
    ]
    assert {file.item: file.edition_from is not None for file in of_the_source} == {
        "naptan-london": False,
        NATIONAL_STOPS: True,
    }


def test_each_kind_of_file_is_read_in_the_place_that_was_found_in_it():
    for file in dated_here():
        there = file.edition_from
        assert there is not None
        found = (there.where, there.at, there.words, there.period_too)
        assert found == stated_at(file), file.item


def test_no_list_states_the_edition_of_a_file_that_is_replaced_under_its_address():
    """What a list states is written on whatever arrives. So the list states none."""
    for file in dated_here():
        assert file.edition == "", file.item
        assert "edition" not in file.unsure, file.item


def test_an_edition_says_which_kind_of_day_it_is():
    """A receipt holds the edition and no notes. So the edition itself says what it is."""
    written = {
        file.source_id: file.edition_from.written("2026-09-16")
        for file in dated_here()
        if file.edition_from is not None
    }
    assert written == {
        FOOD: "extract of 2026-09-16",
        TOWN_CENTRES: "last changed 2026-09-16",
        REPORTS: "retrieved 2026-09-16",
        CONSERVATION: "retrieved 2026-09-16",
        LISTED: "retrieved 2026-09-16",
        STOPS: "retrieved 2026-09-16",
        # The street extract gives a time, written as its publisher writes it. No words
        # stand before it: it is the publisher's own label, and is taken for nothing else.
        STREETS: "2026-09-16",
    }


def test_a_file_that_gives_its_period_is_ready_before_it_is_fetched():
    for file in dated_here():
        if file.source_id != TOWN_CENTRES:
            assert file.data_period is None, file.item
            assert file.ready_for_a_receipt, file.item


def test_the_period_of_the_town_centres_is_the_lists_and_its_notes_say_why():
    """Fetch takes no period from the file. The list states one, and says what stands behind it."""
    (file,) = (file for file in dated_here() if file.source_id == TOWN_CENTRES)
    assert file.edition_from is not None and not file.edition_from.period_too
    assert file.data_period is not None and "data_period" not in file.unsure
    assert file.ready_for_a_receipt
    # The period is the day the file was last changed, and the notes give the day and the reason.
    assert file.data_period.as_at is not None
    assert f"its edition is last changed {file.data_period.as_at}" in file.notes
    assert "fetch never takes it for the period of the data" in file.notes
    assert "a boundary is as the file holds it" in file.notes
    # What the period does not say, and that no person has confirmed it.
    assert "never that a centre was designated on it" in file.notes
    assert "no person has" in file.notes


def test_the_notes_name_the_one_file_that_was_read_for_each():
    """So a person can see, in the line of a fetch, whether the file that was read arrived."""
    seen: set[str] = set()
    for file in dated_here():
        found = THE_FILE_READ.findall(file.notes)
        assert len(found) == 1, file.item
        seen.add(found[0][1])
    assert len(seen) == len(dated_here())


def test_the_notes_of_a_report_say_why_the_day_it_was_retrieved_is_its_period():
    for file in dated_here():
        if file.source_id == REPORTS:
            assert "written as such" in file.notes, file.item
            assert "updated each night" in file.notes, file.item


def test_the_notes_of_a_register_made_again_each_day_say_why_that_day_is_its_period():
    for file in dated_here():
        if file.source_id in (CONSERVATION, LISTED) or file.item == NATIONAL_STOPS:
            assert "written as such" in file.notes, file.item
            assert "made again each day" in file.notes, file.item
            assert "when it was asked for" in file.notes, file.item


def test_the_street_extract_is_listed_for_routing_and_for_nothing_else():
    (file,) = (file for file in dated_here() if file.source_id == STREETS)
    assert file.use == "routing"
    assert "For routing only" in file.notes
