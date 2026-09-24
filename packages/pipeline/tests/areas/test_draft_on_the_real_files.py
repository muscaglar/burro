"""The whole draft, on the files as their publishers gave them.

Every other test of the draft runs on made-up files. These read the real ones,
and are skipped where the store of fetched files is not. The store is named by
BURRO_STORE_FOLDER.
Each file is read through its receipt, from `data/receipts/`, or from the folder
BURRO_RECEIPTS_FOLDER names where a working copy holds none.

The whole draft is made twice, which takes about three minutes: once as the
method makes it, and once again from answers a person might give at the desk.
It is made as the founder decided on 2026-09-24: the name of an area that one
official publisher writes for a populated place at a point inside it, and that
the draft has no mark on, stands by that rule and is put to nobody. So the
desk is handed the lines of 126 names of areas, and not of 488.
A number here is a count over all of London, and never a row or a name. An id
is one Burro gave its own area. Each was counted on 2026-09-24. Nothing is
written to the store.
"""

import csv
import json
import os
import re
from collections import Counter
from dataclasses import replace
from pathlib import Path

import pytest
from burro_pipeline.areas import draft_run
from burro_pipeline.evidence.lock import read_receipts
from burro_pipeline.fetch.store import FOLDER_VARIABLE, FolderStore
from burro_pipeline.inputs import Inputs

from ..cells.support import REPOSITORY, registry

RECEIPTS_VARIABLE = "BURRO_RECEIPTS_FOLDER"
STORE = os.environ.get(FOLDER_VARIABLE, "")
RECEIPTS = Path(os.environ.get(RECEIPTS_VARIABLE, "") or REPOSITORY / "data" / "receipts")
pytestmark = pytest.mark.skipif(
    not (STORE and Path(STORE).is_dir() and RECEIPTS.is_dir()),
    reason=f"the store of fetched files or its receipts are not here: {FOLDER_VARIABLE} names "
    f"the store, and data/receipts or {RECEIPTS_VARIABLE} the receipts",
)
OUTPUT_AREAS, BOROUGHS = 26_369, 33
LOCATES_IN = ("point_inside", "polygon_overlap")


class Real:
    def __init__(self, out: Path, counted: dict[str, object]) -> None:
        self.out, self.counted = out, counted

    def rows(self, name: str) -> list[dict[str, str]]:
        with (self.out / name).open(encoding="utf-8", newline="") as file:
            return list(csv.DictReader(file))


@pytest.fixture(scope="module")
def real(tmp_path_factory: pytest.TempPathFactory) -> Real:
    folder = tmp_path_factory.mktemp("real-draft")
    inputs = Inputs(registry(), read_receipts(RECEIPTS), FolderStore(Path(STORE)), folder / "work")
    return Real(folder / "out", draft_run.make(inputs, folder / "out"))


def test_the_counts_of_the_whole_draft(real: Real):
    assert real.counted == {
        "output_areas": OUTPUT_AREAS,
        "candidates": 1_661,
        "places": 781,
        "seeds": 516,
        "areas": 488,
        "areas_with_no_name": 1,
        "other_names": 301,
        "evidence_rows": 1_266,
        "relations": 106,
        "areas_flagged_about_the_border": 279,
        "layers": 251,
        "pictures": BOROUGHS + 1,
        # The town centres were the one file with no receipt, until 2026-09-24.
        "no_receipt": 0,
    }


def test_every_output_area_of_london_is_in_exactly_one_area_that_stands(real: Real):
    given = real.rows("oa_to_area.csv")
    assert len(given) == len({row["oa21cd"] for row in given}) == OUTPUT_AREAS
    areas = [row["area_id"] for row in real.rows("areas.csv")]
    assert len(areas) == len(set(areas)) == 488
    assert {row["area_id"] for row in given} == set(areas)


def test_every_name_offered_is_one_a_publishers_record_writes(real: Real):
    """No name is supplied by whoever wrote this, or by a model: each is in a file."""
    written = {row["as_written"] for row in real.rows("made/names/candidates.csv")}
    offered = {row["name"] for row in real.rows("areas.csv") if row["name"]}
    offered |= {row["alias"] for row in real.rows("aliases.csv")}
    assert offered and offered <= written
    sources = {row["source_id"] for row in real.rows("name_evidence.csv")}
    assert sources == {"os-open-names", "gla-town-centre-boundaries", "os-boundary-line"}


def test_every_area_has_one_name_or_none_and_every_name_has_a_record_inside(real: Real):
    areas = real.rows("areas.csv")
    assert sum(not row["name"] for row in areas) == 1
    assert {row["slug"] for row in areas if not row["name"]} == {""}
    slugs = [row["slug"] for row in areas if row["name"]]
    assert len(slugs) == len(set(slugs)) == 487
    inside = {
        (row["area_id"], row["name"])
        for row in real.rows("name_evidence.csv")
        if row["role"] == "primary" and row["locates"] in LOCATES_IN
    }
    assert {(row["area_id"], row["name"]) for row in areas if row["name"]} == inside


def test_the_names_are_counted_by_how_they_came_to_be_offered(real: Real):
    counted = json.loads((real.out / "counts.json").read_bytes())["naming"]
    assert counted["areas_named_for_their_seed"] == 484
    assert counted["areas_named_for_another_name"] == 3
    assert counted["areas_whose_name_two_publishers_write"] == 154
    # For 20 of them the second publisher writes the name with another name beside it, or
    # with its own word for a ward or a centre after it, or with other marks.
    assert counted["areas_whose_name_two_publishers_write_letter_for_letter"] == 134
    assert counted["areas_whose_name_one_publisher_writes"] == 333
    # Four more than the first draft counted: their own point stands on their own edge.
    assert counted["areas_whose_name_a_point_places"] == 463
    # 355 rested on the town centres while that file had no receipt.
    assert counted["areas_that_rest_on_a_file_with_no_receipt"] == 0
    assert counted["areas_whose_main_borough_is_a_tie"] == 1
    assert counted["other_names_by_kind"] == {"inside": 289, "same_ground": 4, "wide": 8}
    assert counted["other_names_that_were_seeds"] == 32
    assert counted["places_offered_nowhere"] == 0
    assert counted["relations_by_kind"] == {
        "grown_from_a_name_in": 4,
        "name_lies_over": 94,
        "same_name": 8,
    }
    assert counted["marks"] == {
        "by_an_outline_alone": 24,
        "heavier_name_inside": 8,
        "not_its_seed": 3,
        "on_the_line": 17,
        "seed_lies_elsewhere": 4,
        "unnamed": 1,
        "was_put_under_another": 29,
    }


def test_every_row_of_every_curated_file_says_it_is_a_draft(real: Real):
    for name in ("areas.csv", "oa_to_area.csv", "aliases.csv", "name_evidence.csv"):
        assert {row["state"] for row in real.rows(name)} == {
            "draft, made by method, checked by nobody"
        }
    held = json.loads((real.out / "snapshots.json").read_bytes())
    assert len(held) == 8
    assert "gla-town-centre-boundaries" in {each["source_id"] for each in held}
    assert [each["source_id"] for each in held if not each["has_receipt"]] == []


def test_there_is_a_picture_of_london_and_of_each_borough(real: Real):
    pictures = sorted(path.name for path in (real.out / "pictures").iterdir())
    assert len(pictures) == BOROUGHS + 1 and "london.svg" in pictures
    assert all(
        b"http://" not in path.read_bytes().replace(b"http://www.w3.org/2000/svg", b"")
        for path in (real.out / "pictures").iterdir()
    )


# What reaches the person who decides


def test_the_one_name_that_may_say_who_lives_there_is_flagged_for_the_founder(real: Real):
    """Section 6 of the areas design. The name is kept as its publisher writes it."""
    flags = Counter((row["queue"], row["flag"]) for row in real.rows("desk/draft/flags.csv"))
    assert flags == {
        # It was 613, while the design asked for two publishers. It is raised only
        # where no official publisher writes the name at a point inside the area.
        ("names", "one_publisher"): 86,
        ("names", "same_name_elsewhere"): 18,
        ("names", "describes_residents"): 1,
        # Every name with a mark to settle is flagged.
        ("names", "look_hard"): 245,
        ("borders", "two_boroughs"): 169,
        ("borders", "margin_under_10"): 73,
        ("borders", "follows_nothing"): 60,
        ("borders", "seeds_close"): 44,
        ("borders", "least_compact"): 25,
        ("borders", "size_unlike_neighbours"): 19,
        ("borders", "seed_outside"): 10,
        ("borders", "two_centres"): 6,
    }
    # Every area the draft flags about its border is flagged at the desk.
    flagged = {
        row["item"] for row in real.rows("desk/draft/flags.csv") if row["queue"] == "borders"
    }
    assert len(flagged) == real.counted["areas_flagged_about_the_border"] == 279
    listed = real.rows("names_to_look_at.csv")
    assert len(listed) == 391
    assert listed[0]["mark"] == "may_describe_residents" and listed[0]["item"].startswith("a:")
    assert len({row["item"] for row in listed if row["grave"] == "true"}) == 245
    # Every grave mark of the draft of names is in the list the founder is told to read.
    grave = {
        (row["area_id"], row["mark"], row["why"])
        for row in real.rows("made/names/hard_look.csv")
        if row["grave"] == "true"
    }
    assert grave == {
        (row["place_id"], row["mark"], row["why"]) for row in listed if row["from"] == "names"
    }


def test_the_desk_is_handed_no_label_of_a_ward_as_a_spelling(real: Real):
    ours = real.rows("name_evidence.csv")
    desk = real.rows("desk/draft/name_evidence.csv")
    assert (len(ours), len(desk)) == (1_266, 946)
    assert sum(row["source_id"] == "os-boundary-line" for row in ours) == 320
    assert not [row for row in desk if row["source_id"] == "os-boundary-line"]
    assert Counter((row["source_id"], row["letter_for_letter"]) for row in ours) == {
        ("os-open-names", "true"): 697,
        ("os-boundary-line", "false"): 320,
        ("gla-town-centre-boundaries", "true"): 230,
        ("gla-town-centre-boundaries", "false"): 19,
    }


def test_every_doubt_of_the_draft_is_a_line_of_the_item_it_is_about(real: Real):
    lines = real.rows("desk/draft/lines.csv")
    labels = Counter(
        (row["queue"], "an output area" if row["label"].startswith("E0") else row["label"])
        for row in lines
    )
    assert labels["borders", "an output area"] == 4_955
    assert labels["borders", "Flagged"] == 406
    assert labels["names", "Look hard"] == 345
    # 362 names of areas stand by the rule on one official publisher, and have no line.
    assert labels["names", "Points"] == 125
    # What a person weighs: who writes the name, the kind of place, the road records and
    # the size of the area.
    assert labels["names", "Publishers"] == 420
    assert labels["names", "Kind of place"] == 420
    assert labels["names", "Road records"] == 329
    assert labels["names", "Size"] == 126
    assert labels["names", "Other names"] == 126
    assert labels["rules", "Every item"] == labels["rules", "Already decided"] == 8
    assert labels["borders", "No receipt"] == 0
    # The border of an area whose name nobody read says so.
    assert labels["borders", "Name"] == 362
    assert labels["names", "Grown from"] + labels["names", "Nearest name"] == 12
    in_doubt = {
        (row["area_id"], row["oa21cd"]) for row in real.rows("made/flags/cells_in_doubt.csv")
    }
    assert in_doubt == {
        (row["item"], row["label"]) for row in lines if row["label"].startswith("E0")
    }
    named = [row for row in lines if row["label"].startswith("E0") and "streets: " in row["value"]]
    assert len(named) >= 4_800
    assert not [row for row in lines if "no place" in row["value"]]
    # Every flag of the draft about a border is said in words, with what it found.
    flagged = {
        (row["item"], row["why"])
        for row in real.rows("made/flags/flagged.csv")
        if row["queue"] == "borders" and row["about"] == "border"
    }
    assert flagged == {(row["item"], row["value"]) for row in lines if row["label"] == "Flagged"}
    assert len({item for item, _ in flagged}) == 279


def test_what_a_name_says_of_its_points_can_be_read_without_an_id(real: Real):
    """A town centre and a ward are named as their files write them, and a distance says
    what it is from. Nothing rests on a file with no receipt: every file has its own."""
    lines = [row for row in real.rows("desk/draft/lines.csv") if row["queue"] == "names"]
    points = [row["value"] for row in lines if row["label"] == "Points"]
    assert len(points) == 125
    assert sum('A town centre of another name, "' in value for value in points) == 36
    assert not [value for value in points if "town centre" in value and '"' not in value]
    carried = [value for value in points if " carries it" in value]
    assert len(carried) == 94
    assert sum("carries it among other words" in value for value in carried) == 27
    listed: dict[str, set[str]] = {}
    for row in lines:
        if row["source_id"] == "os-boundary-line" and "Record " in row["value"]:
            listed.setdefault(row["item"], set()).add(row["value"].split("Record ")[-1][:-1])
    for row in lines:
        if row["label"] == "Points" and " carries it: " in row["value"]:
            record = row["value"].split(" carries it: 1. Record ")[-1].split(".")[0]
            assert record in listed[row["item"]]
    assert not [row for row in lines if " m off" in row["value"] or " km off" in row["value"]]
    assert not [row for row in lines if row["label"] == "No receipt"]
    none = sum(row["value"].startswith("The draft puts no other") for row in lines)
    assert none == 63


def test_the_cells_in_doubt_are_counted_once_and_every_one_is_under_a_reason(real: Real):
    lines = [row for row in real.rows("desk/draft/lines.csv") if row["queue"] == "borders"]
    said = [row["value"] for row in lines if row["label"] == "In doubt"]
    assert len(said) == 474
    for value in said:
        count = int(value.split()[0])
        under = [int(found) for found in re.findall(r"\. (\d+) (?:ha|l|is |are )", value)]
        assert under and max(under) <= count <= sum(under), value
    # No margin of a hundred or more is shown as a percentage.
    shown = [int(found) for row in lines for found in re.findall(r"margin (\d+)%", row["value"])]
    assert shown and max(shown) < 100
    assert sum(" as far" in row["value"] for row in lines) == 328
    assert sum("over 10 times as far" in row["value"] for row in lines) == 11


def test_what_the_desk_marks_on_the_map_of_a_border_is_counted(real: Real):
    marks = real.rows("desk/draft/marks.csv")
    assert Counter((row["flag"], row["kind"]) for row in marks) == {
        ("margin_under_10", "cell"): 3_341,
        ("two_boroughs", "cell"): 1_674,
        ("seeds_close", "cell"): 459,
        ("seeds_close", "seed"): 44,
        ("follows_nothing", "side"): 2_703,
        ("two_centres", "centre"): 12,
    }
    cells = {(row["item"], row["what"]) for row in marks if row["kind"] == "cell"}
    in_doubt = {
        (row["area_id"], row["oa21cd"]) for row in real.rows("made/flags/cells_in_doubt.csv")
    }
    assert cells == in_doubt and len(cells) == 4_955
    flagged = Counter(
        row["flag"] for row in real.rows("desk/draft/flags.csv") if row["queue"] == "borders"
    )
    stretches = {row["item"] for row in marks if row["kind"] == "side"}
    assert len(stretches) == flagged["follows_nothing"] == 60
    assert len({row["item"] for row in marks if row["kind"] == "seed"}) == flagged["seeds_close"]
    assert len({row["item"] for row in marks if row["kind"] == "centre"}) == 6


def test_the_desk_is_handed_the_order_and_the_rules(real: Real):
    order = Counter(row["queue"] for row in real.rows("desk/draft/order.csv"))
    assert order == {"borders": 488, "whole": BOROUGHS}
    rules = real.rows("desk/draft/rules.csv")
    assert len(rules) == 8 and Counter(row["queue"] for row in rules) == {"names": 7, "borders": 1}
    settled = Counter(row["queue"] for row in real.rows("desk/draft/rules_items.csv"))
    # It was 438 names. 240 of them stand by the rule on one official publisher, and 26
    # are names of areas with a mark, which a person reads.
    assert settled == {"names": 172, "borders": 26}
    items = {(row["queue"], row["item"]) for row in real.rows("desk/draft/rules_items.csv")}
    assert len(items) == 198, "an item is settled by one rule alone"
    # The fifth rule leans on the fourth, and lets through another name alone.
    leans = Counter(
        (row["rule"], row["leans_on"])
        for row in real.rows("desk/draft/rules_items.csv")
        if row["leans_on"]
    )
    assert leans == {("a_mark_that_asks_nothing", "a_smaller_place_by_its_own_point"): 21}
    stands = {
        f"n:{row['area_id']}"
        for row in real.rows("named_by_the_rule.csv")
        if row["asked_at_the_desk"] == "false"
    }
    assert len(stands) == 362 and not stands & {item for _, item in items}
    assert not (real.out / "desk" / "draft" / "rules_would_settle.csv").exists()


def test_every_seed_is_drawn_under_the_name_its_own_record_writes(real: Real):
    seeds = {row["area_id"]: row["name"] for row in real.rows("desk/draft/seeds.csv")}
    areas = {row["area_id"]: row["name"] for row in real.rows("areas.csv")}
    drawn = [
        feature["properties"]
        for path in sorted((real.out / "desk" / "draft" / "layers").glob("*/seeds.geojson"))
        for feature in json.loads(path.read_bytes())["features"]
    ]
    assert len(drawn) == 685
    assert all(each["name"] == seeds[each["area"]] for each in drawn)
    assert sorted(area for area in areas if areas[area] != seeds[area]) == [
        "lon-n0019",
        "lon-n0100",
        "lon-n0520",
        "lon-n0538",
    ]


def test_what_each_rule_put_to_the_founder_would_settle_is_counted_and_none_is_adopted(
    real: Real,
):
    counted = json.loads((real.out / "counts.json").read_bytes())
    assert counted["rules_put_to_the_founder"] == {
        # The first three fit only names that stand by the rule on one official publisher.
        "two_publishers_write_it": 0,
        "a_ward_of_its_name": 0,
        "many_roads_name_it": 0,
        "a_smaller_place_by_its_own_point": 109,
        # It was 40, while it let through the name of an area with such a mark.
        "a_mark_that_asks_nothing": 21,
        "named_for_a_built_thing": 19,
        "a_label_of_two_names": 23,
        # The desk shows every flag about a border, so a border that carries another flag
        # is not flagged only for lying in two boroughs. With four flags shown it was 39.
        "a_few_cells_across_a_borough_line": 26,
    }
    already = {rule: count for rule, count in counted["rules_already_decided"].items() if count}
    assert already == {
        "two_publishers_write_it": 104,
        # It fitted 127. In the area of 7 of them lies a heavier name, or the name another
        # area was grown from: each is read by a person.
        "a_ward_of_its_name": 120,
        "many_roads_name_it": 16,
    }
    assert counted["for_the_founder_to_decide"] == {
        "names_put_forward_as_areas": 516,
        "of_them_one_publisher_writes": 360,
        "of_them_with_points_from_a_town_centre_of_another_name": 205,
        "of_them_reaching_the_points_asked_only_through_such_a_centre": 95,
        "of_them_known_by_a_record_in_the_smallest_box": 10,
        "of_them_holding_a_word_for_a_built_thing_in_a_larger_box": 12,
        "of_them_with_a_seed_moved_to_a_label_that_only_holds_the_name": 22,
        "of_them_resting_on_a_file_with_no_receipt": 0,
    }
    assert {row["review_state"] for row in real.rows("areas.csv")} == {"drafted", "named_by_rule"}
    assert {row["chosen_by"] for row in real.rows("name_evidence.csv")} == {""}
    largest = real.rows("largest_areas.csv")
    assert [int(row["output_areas"]) for row in largest][:3] == [208, 184, 164]
    assert sum(row["other_names_inside"] == "0" for row in largest) == 6


def test_what_the_decision_on_one_official_publisher_settled_is_counted(real: Real):
    """The founder decided that a name an official publisher writes for a populated
    place, at a point inside the area, is a name. A name still says who writes it."""
    counted = json.loads((real.out / "counts.json").read_bytes())["one_official_publisher"]
    assert counted == {
        "decided_on": "2026-09-24",
        "record": "0022",
        "areas": 488,
        "areas_the_rule_fits": 463,
        # An outline alone places 24, and one has no name.
        "areas_the_rule_does_not_fit": 25,
        "of_them_one_publisher_writes": 326,
        "areas_named_by_the_rule_alone": 362,
        "of_them_one_publisher_writes_the_name": 257,
        "areas_the_rule_fits_that_are_still_asked_at_the_desk": 101,
        "items_that_leave_the_queue_of_names": 362,
        "hours_they_would_have_taken": 4.5,
        "names_the_rule_fits": 673,
    }
    areas = real.rows("areas.csv")
    stands = {row["area_id"] for row in areas if row["review_state"] == "named_by_rule"}
    assert len(stands) == 362
    listed = real.rows("named_by_the_rule.csv")
    assert {row["area_id"] for row in listed if row["asked_at_the_desk"] == "false"} == stands
    assert Counter(row["why"] for row in listed) == {"": 362, "the draft has a mark on it": 101}
    assert {row["source_id"] for row in listed} == {"os-open-names"}
    # No line, no flag and no rule of a name that stands is handed to the desk.
    for name in ("lines.csv", "flags.csv", "rules_items.csv"):
        items = {row["item"] for row in real.rows(f"desk/draft/{name}") if row["queue"] == "names"}
        assert items and not items & {f"n:{area}" for area in stands}, name
    # Its border is still looked at.
    assert stands <= {row["item"] for row in real.rows("desk/draft/order.csv")}
    # No mark of the draft is on any of them, on its own item or on another that bears on it.
    marked = {row["item"] for row in real.rows("names_to_look_at.csv")}
    assert not marked & {f"n:{area}" for area in stands}
    writing = Counter(len(row["publishers_writing"].split(";")) for row in areas if row["name"])
    assert writing == {1: 333, 2: 154}
    assert Counter(
        len(row["publishers_writing"].split(";")) for row in areas if row["area_id"] in stands
    ) == {1: 257, 2: 105}


# The draft made again from what was decided


# Seven names put forward as areas that hold a word for a street or a building, by the
# ids Burro gave them, and what a person might say of each. They are nobody's decisions.
TURNED_DOWN = {
    "lon-n0052": "inside",
    "lon-n0152": "inside",
    "lon-n0672": "drop",
    "lon-n0673": "inside",
    "lon-n0674": "inside",
    "lon-n0684": "drop",
    "lon-n0685": "same_ground",
}


@pytest.fixture(scope="module")
def again(real: Real, tmp_path_factory: pytest.TempPathFactory) -> Real:
    folder = tmp_path_factory.mktemp("real-draft-again")
    inputs = Inputs(registry(), read_receipts(RECEIPTS), FolderStore(Path(STORE)), folder / "work")
    settings = replace(draft_run.Settings(), decided=TURNED_DOWN)
    ids = real.out / "made" / "names" / "ids.csv"
    return Real(folder / "out", draft_run.make(inputs, folder / "out", ids=ids, settings=settings))


def test_a_draft_made_again_without_seven_names_gives_their_ground_to_their_neighbours(
    real: Real, again: Real
):
    before = {row["oa21cd"]: row["area_id"] for row in real.rows("oa_to_area.csv")}
    after = {row["oa21cd"]: row["area_id"] for row in again.rows("oa_to_area.csv")}
    assert len(after) == OUTPUT_AREAS and set(after) == set(before)
    areas = {row["area_id"] for row in again.rows("areas.csv")}
    assert len(areas) == 481 and set(after.values()) == areas
    assert areas == {row["area_id"] for row in real.rows("areas.csv")} - set(TURNED_DOWN)
    moved = {oa for oa in before if before[oa] != after[oa]}
    assert len(moved) == 290
    assert len({before[oa] for oa in moved} | {after[oa] for oa in moved}) == 31
    assert (again.out / "made" / "names" / "ids.csv").read_bytes() == (
        real.out / "made" / "names" / "ids.csv"
    ).read_bytes()
    assert again.counted["seeds"] == 509 and again.counted["other_names"] == 306
