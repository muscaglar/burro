"""The names and seeds of London, from the files as their publishers gave them.

Every other test of names and seeds runs on made-up files. These read the real
ones, and are skipped where the store of fetched files is not. The store is named by
BURRO_STORE_FOLDER.

Each file is read through its receipt. The receipts are those of
`data/receipts/`. A working copy that holds no such folder reads the copies
that the store keeps beside its files, which fetch writes for that purpose.
The file of town centres has its receipt since 2026-09-24, so no file is read
as a draft reads one that has none.

They hold counts, so that a publisher's file that changes is noticed, and a
rule that changes is seen for what it does. A number here is a count over all
of London. No test holds a name, a row or a place. Each was counted on
2026-09-23.

Nothing is written to the store. A file is copied out of it to be read.
"""

import os
import tempfile
from collections import Counter
from pathlib import Path

import pytest
from burro_pipeline.areas import names_centres, names_draft, names_places, names_wards
from burro_pipeline.areas.names_candidates import Match
from burro_pipeline.areas.names_draft import Drafted, Read
from burro_pipeline.areas.names_look import Mark
from burro_pipeline.areas.seeds import Put, Tier, Tried, Why
from burro_pipeline.evidence.lock import read_receipts
from burro_pipeline.evidence.receipt import Receipt
from burro_pipeline.fetch.store import FOLDER_VARIABLE, FolderStore
from burro_pipeline.inputs import Inputs

from ..cells.support import REPOSITORY, registry

STORE = os.environ.get(FOLDER_VARIABLE, "")
RECEIPTS = REPOSITORY / "data" / "receipts"
pytestmark = pytest.mark.skipif(
    not (STORE and Path(STORE).is_dir()),
    reason=f"the store of fetched files is not here: {FOLDER_VARIABLE} names no folder",
)


def receipts(store: FolderStore) -> tuple[Receipt, ...]:
    if RECEIPTS.is_dir():
        return read_receipts(RECEIPTS)
    kept = store.receipts()
    return tuple(Receipt.model_validate_json(kept[key]) for key in sorted(kept))


@pytest.fixture(scope="module")
def read() -> Read:
    """Everything a draft reads. The copies of the files are removed as soon as they are read:
    they come to seven gigabytes, and a folder of a test is kept for three runs."""
    store = FolderStore(Path(STORE))
    with tempfile.TemporaryDirectory(prefix="burro-real-names-") as work:
        inputs = Inputs(registry(), receipts(store), store, Path(work))
        return names_draft.read(inputs, draft=True)


@pytest.fixture(scope="module")
def drafted(read: Read) -> Drafted:
    return names_draft.make(read)


# The files


def test_the_files_hold_as_many_records_as_were_counted(read: Read):
    assert (read.names.tables, read.names.rows) == (819, 3_047_173)
    assert len(read.centres) == 234
    assert (len(read.wards), len(read.boroughs)) == (704, 33)
    assert len(read.london.ground) == 26_369
    assert names_centres.SOURCE in read.files
    assert {file.has_receipt for file in read.files.values()} == {True}


def test_the_roads_of_london_are_as_many_as_were_counted(read: Read):
    """With 2 km round London, so that a way may leave it and come back."""
    assert (read.roads.nodes, read.roads.links, read.roads.pieces) == (227_286, 280_321, 102)


def test_the_town_centres_are_of_the_classes_that_were_counted(read: Read):
    assert Counter(centre.rank for centre in read.centres) == {
        "International": 2,
        "Metropolitan": 13,
        "Major": 36,
        "District": 152,
        "District Centre": 2,
        "Local Centre": 7,
        "CAZ retail cluster": 20,
        "Unclassified": 2,
    }
    assert sum(centre.counts for centre in read.centres) == 205
    assert sum(centre.rank_is_read for centre in read.centres) == 2
    assert sum(centre.point_is_inside for centre in read.centres) == 200


# The candidates


def test_london_holds_as_many_candidates_of_each_kind_as_were_counted(drafted: Drafted):
    found = Counter((each.source_id, each.kind) for each in drafted.candidates.records)
    assert {
        kind: count for (source, kind), count in found.items() if source == "os-open-names"
    } == {
        "City": 3,
        "Village": 24,
        "Hamlet": 9,
        "Other Settlement": 128,
        "Suburban Area": 526,
    }
    assert found[(names_wards.SOURCE, "London Borough Ward")] == 704
    assert found[(names_wards.SOURCE, "London Borough")] == 33
    assert (
        sum(count for (source, _), count in found.items() if source == names_centres.SOURCE) == 234
    )
    assert len(drafted.candidates.records) == 1_661
    assert len(drafted.candidates.stations) == 575
    assert len(drafted.borough_names) == 33


def test_what_lies_in_londons_box_and_not_in_london_is_left_out(drafted: Drafted):
    assert drafted.candidates.outside == {
        "os-open-names:populatedPlace": 326,
        "os-open-names:Railway Station": 83,
        names_centres.SOURCE: 0,
    }


def test_every_record_is_in_an_output_area_of_london_and_in_its_borough(
    read: Read, drafted: Drafted
):
    for record in (*drafted.candidates.records, *drafted.candidates.stations):
        assert read.london.borough_of[record.cell] == record.borough


def test_no_name_holds_a_letter_outside_the_ones_the_fold_reads(drafted: Drafted):
    """The files were counted to hold no name with a letter outside ASCII. A new one is seen."""
    assert all(record.as_written.isascii() for record in drafted.candidates.records)


# What is one place


def test_as_many_town_centres_are_joined_to_a_populated_place_as_were_counted(drafted: Drafted):
    joined = [
        other
        for place in drafted.candidates.places
        for other in place.written_by(names_centres.SOURCE)
        if other.match is Match.SAME
    ]
    assert len(joined) == 143
    assert sum(other.beyond for other in joined) == 6
    assert len({other.candidate.record_id for other in joined}) == 143
    alone = [place for place in drafted.candidates.places if place.centre is not None]
    assert len(alone) == 234 - 143
    assert len(drafted.candidates.places) == 690 + 91


def test_as_many_names_rest_on_two_publishers_as_were_counted(drafted: Drafted):
    places = drafted.candidates.places
    assert sum(len(place.publishers) > 1 for place in places) == 169
    assert sum(len(place.publishers) > 1 for place in places if place.record is not None) == 157
    assert {publisher for place in places for publisher in place.publishers} == {
        "Ordnance Survey",
        "Greater London Authority",
    }


# The points


def test_the_points_are_given_to_as_many_places_as_were_counted(drafted: Drafted):
    """Of the 688 populated places that are no wide name. One of them is a city."""
    counts = names_draft.counts_of(drafted)
    assert counts["populated_places_by_what_gave_points"] == {
        "roads": 92,
        "town_centre": 385,
        "ward": 390,
    }
    assert counts["places_by_points"] == {
        "0": 5,
        "1": 1,
        "3": 223,
        "4": 151,
        "5": 3,
        "6": 140,
        "7": 178,
        "8": 14,
        "9": 66,
    }


def test_no_road_names_a_suburban_area_as_its_settlement(drafted: Drafted):
    named = Counter(
        place.record.kind
        for place in drafted.candidates.places
        if place.record is not None and place.roads
    )
    assert "Suburban Area" not in named
    assert named == {"City": 3, "Other Settlement": 93, "Village": 24, "Hamlet": 9}


# The seeds


def test_the_designs_rule_gives_fewer_areas_than_the_design_asks_for(drafted: Drafted):
    assert Tried(6, 2, 363) in drafted.seeds.tried


def test_no_number_of_points_lands_in_range_and_the_draft_says_so(drafted: Drafted):
    assert list(drafted.seeds.tried) == [
        Tried(9, 2, 66),
        Tried(8, 2, 78),
        Tried(7, 2, 252),
        Tried(6, 2, 363),
        Tried(5, 2, 363),
        Tried(4, 2, 369),
        Tried(3, 2, 369),
        Tried(2, 2, 369),
        Tried(1, 2, 369),
        Tried(9, 1, 66),
        Tried(8, 1, 78),
        Tried(7, 1, 252),
        Tried(6, 1, 374),
        Tried(5, 1, 377),
        Tried(4, 1, 516),
        Tried(3, 1, 676),
        Tried(2, 1, 676),
        Tried(1, 1, 677),
    ]
    assert (drafted.seeds.points, drafted.seeds.publishers) == (4, 1)
    assert not drafted.seeds.in_range and len(drafted.seeds.areas) == 516


def test_the_draft_puts_forward_as_many_of_each_tier_as_were_counted(drafted: Drafted):
    assert Counter((seed.tier, seed.why) for seed in drafted.seeds.seeds) == {
        (Tier.AREA, Why.NONE): 516,
        (Tier.INSIDE, Why.FEW_POINTS): 229,
        (Tier.INSIDE, Why.TOO_CLOSE): 31,
        (Tier.SAME_GROUND, Why.TOO_CLOSE): 3,
        (Tier.WIDE, Why.WIDE_KIND): 2,
    }
    areas = drafted.seeds.areas
    assert sum(seed.put is Put.CENTRE for seed in areas) == 175
    assert sum(seed.one_publisher for seed in areas) == 360
    assert sum(len(seed.weight.publishers) < 2 for seed in areas) == 147
    assert sum(seed.place.centre is not None for seed in areas) == 6


def test_every_name_that_is_no_area_is_a_name_of_an_area_that_stands(drafted: Drafted):
    areas = {seed.key for seed in drafted.seeds.areas}
    for seed in drafted.seeds.seeds:
        if seed.tier is not Tier.AREA:
            assert seed.of and set(seed.of) <= areas
    assert all(seed.along_roads for seed in drafted.seeds.seeds if seed.tier is Tier.INSIDE)


def test_every_borough_has_an_area_and_one_city_is_no_wide_name(read: Read, drafted: Drafted):
    with_an_area = {seed.place.key.borough for seed in drafted.seeds.areas}
    assert with_an_area == set(read.london.borough_names)
    cities = [
        seed
        for seed in drafted.seeds.seeds
        if seed.place.record is not None and seed.place.record.kind == names_places.CITY
    ]
    assert sorted(seed.tier for seed in cities) == [Tier.AREA, Tier.WIDE, Tier.WIDE]


def test_every_seed_stands_in_an_output_area_of_london(read: Read, drafted: Drafted):
    outside = [seed for seed in drafted.seeds.areas if read.london.cell_of(seed.at) is None]
    assert outside == []


# The marks


def test_as_many_names_carry_each_mark_as_were_counted(drafted: Drafted):
    marked: dict[Mark, set[tuple[str, str, str]]] = {}
    for look in drafted.looks:
        marked.setdefault(look.mark, set()).add(look.key)
    assert {mark.value: len(keys) for mark, keys in marked.items()} == {
        "may_describe_residents": 1,
        "same_name_elsewhere": 18,
        "two_names_one_place": 71,
        "joined_beyond_1km": 6,
        "may_be_a_built_thing": 99,
        "also_a_borough": 24,
        "also_a_station": 306,
        "also_a_ward": 247,
        "as_many_points": 12,
        "seed_far_from_place": 19,
        # Every seed moved to a label that is not its name, and not only the three that
        # lost their name by the move.
        "seed_on_a_label_that_holds_it": 22,
        "class_was_read": 5,
        # No name carries the mark `no_receipt`: 482 did, until the town centres had theirs.
        "one_publisher": 612,
    }
    grave = {look.key for look in drafted.looks if look.grave}
    assert len(grave) == 226
    assert len(grave & {seed.key for seed in drafted.seeds.areas}) == 105


# What is written


def test_every_area_has_a_row_that_puts_its_name_on_the_map(drafted: Drafted):
    located = {
        row.area_id
        for row in drafted.rows
        if row.role == "primary" and row.writes and row.locates != "label_only"
    }
    assert located == {drafted.area_ids[seed.key] for seed in drafted.seeds.areas}
    assert len(drafted.rows) == 1_518
    assert sum(row.writes for row in drafted.rows) == 1_268


def test_the_draft_is_written_and_is_the_same_bytes_when_it_is_made_again(
    read: Read, drafted: Drafted, tmp_path: Path
):
    names_draft.write(tmp_path, drafted)
    assert {path.name for path in tmp_path.iterdir()} == {
        *("candidates.csv", "places.csv", "seeds.csv", "name_records.csv", "hard_look.csv"),
        *("stations.csv", "ids.csv", "decided.csv", "counts.json", "draft"),
    }
    assert names_draft.written(names_draft.make(read)) == names_draft.written(drafted)
    assert names_places.POSTCODE.encode() not in (tmp_path / "candidates.csv").read_bytes()
