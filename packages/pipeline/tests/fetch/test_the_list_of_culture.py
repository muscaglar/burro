"""The list that takes London's part of one file of places, held to the licence registry.

The list takes the part twice: as culture reads it, and again with the brand
of a place that belongs to a chain. Nothing is fetched and no socket is
opened. The list and the registry are the repository's own.
"""

from pathlib import Path

import pytest
from burro_pipeline.evidence import Period
from burro_pipeline.evidence.lock import read_receipts
from burro_pipeline.fetch import gate
from burro_pipeline.fetch.download import may_be_asked
from burro_pipeline.fetch.sources import Format, Listed, load_list
from burro_pipeline.registry import Use, load

REGISTRY = Path(__file__).parents[4] / "registry" / "sources"
RECEIPTS = Path(__file__).parents[4] / "data" / "receipts"
# The columns of a place that say who or where a business is, by the publisher's own names.
NEVER_TAKEN = {"id", "names", "addresses", "phones", "websites", "socials", "emails"}
# The one column that says which chain a place belongs to. It names no place, and the
# second item of the list alone takes it.
BRAND = "brand"
# The furthest a measure of venues reaches from a home, in degrees of latitude and a little
# more: 800 metres is under 0.0073 degrees north, and under 0.0117 degrees east at London.
REACH_NORTH, REACH_EAST = 0.0073, 0.0117

FILES = load_list("m2-culture").files
EACH = pytest.mark.parametrize("file", FILES, ids=[file.item for file in FILES])


def test_the_list_holds_the_part_twice_and_the_second_takes_the_brand():
    first, second = FILES
    assert (first.item, second.item) == ("overture-places-london", "overture-places-london-brands")
    assert first.take is not None and second.take is not None
    assert (second.url, second.edition, second.data_period) == (
        first.url,
        first.edition,
        first.data_period,
    )
    assert (second.take.box, second.take.box_in) == (first.take.box, first.take.box_in)
    assert set(second.take.columns) - set(first.take.columns) == {BRAND}
    assert set(first.take.columns) <= set(second.take.columns)


@EACH
def test_the_gate_lets_each_file_through(file: Listed):
    source = gate.ask(file, load(REGISTRY))
    assert (source.id, file.use, file.format) == ("overture-places", Use.SCORING, Format.PARQUET)
    may_be_asked(file.url)


@EACH
def test_the_file_is_one_file_of_the_release_the_list_states(file: Listed):
    assert f"/release/{file.edition}/theme=places/type=place/" in file.url
    assert file.url.endswith(".parquet") and "*" not in file.url
    (named,) = load(REGISTRY).get("overture-places").file_urls
    assert named == file.url


@EACH
def test_part_of_the_file_is_taken_and_never_the_whole(file: Listed):
    assert file.take is not None
    assert file.max_bytes < 728_373_349


@EACH
def test_no_column_that_names_a_business_or_says_where_to_reach_it_is_taken(file: Listed):
    assert file.take is not None
    assert not {column.split(".")[0] for column in file.take.columns} & NEVER_TAKEN


def test_the_part_that_culture_reads_holds_no_brand():
    first = FILES[0]
    assert first.take is not None
    assert BRAND not in {column.split(".")[0] for column in first.take.columns}


@EACH
def test_the_box_is_wider_than_the_homes_of_london_by_more_than_a_measure_reaches(file: Listed):
    """The span of the centres is the one the list's own notes give, from the first build."""
    assert file.take is not None
    west, south, east, north = file.take.box
    assert west + 2 * REACH_EAST < -0.497233 and east - 2 * REACH_EAST > 0.295567
    assert south + 2 * REACH_NORTH < 51.298417 and north - 2 * REACH_NORTH > 51.681978


@EACH
def test_the_period_is_the_day_of_the_release_and_the_list_says_who_stated_it(file: Listed):
    """The file states no period. The founder stated one on 2026-09-24: the day of the
    publisher's release, with a note that many records are years older. So nothing of the
    item is unsure, and the notes say who stated the period, when, and what it is not.
    """
    assert file.unsure == () and file.ready_for_a_receipt
    assert file.data_period == Period(as_at="2026-09-23")
    assert file.edition.startswith("2026-09-23")
    assert "The period was stated by the founder on 2026-09-24" in file.notes
    assert "many records are years older" in file.notes
    assert "not of each record" in file.notes


def test_each_receipt_of_the_part_holds_what_the_list_states_of_one_item():
    """A figure is cited to the receipt, so it says what the list says and no other day.

    The two items are one file at one address, so a receipt is of the item
    whose columns it took. The part that culture reads has its receipt.
    """
    by_columns = {tuple(sorted(file.take.columns)): file for file in FILES if file.take}
    receipts = [one for one in read_receipts(RECEIPTS) if one.source_id == FILES[0].source_id]
    items: list[str] = []
    for receipt in receipts:
        assert receipt.taken is not None
        file = by_columns[receipt.taken.columns]
        assert file.take is not None
        items.append(file.item)
        assert (receipt.edition, receipt.data_period) == (file.edition, file.data_period)
        assert (receipt.listed_url, receipt.use) == (file.url, file.use)
        assert (receipt.taken.box, receipt.taken.box_in) == (file.take.box, file.take.box_in)
        assert receipt.bytes <= file.max_bytes
    assert len(set(items)) == len(items) and FILES[0].item in items
