"""Rules put to the founder: what each would settle, and that none is applied.

Nothing here is real. `draft_support.py` makes the whole draft of the made-up
town, and a border is flagged on a town of plain values.

The founder has decided that one official publisher is enough for a name. A name
that stands by that decision is no item, and no rule settles it. `every` is the
draft in which every name is still put to a person: there the first three rules
settle what they did before the decision.
"""

import json

import pytest
from burro_pipeline.areas import draft_rules
from burro_pipeline.areas.draft_decided import BEAR_ON_THE_AREA
from burro_pipeline.areas.flags import Area, Cell, Draft, Flag, Rules, Side, flags_of

from .draft_support import Made, made, made_with_every_name_read
from .test_draft_marks import two_names


@pytest.fixture(scope="module")
def draft() -> Made:
    return made()


@pytest.fixture(scope="module")
def every() -> Made:
    return made_with_every_name_read()


def test_every_rule_is_said_in_words_with_what_could_go_wrong_and_names_no_place(draft: Made):
    rows = draft.rows("rules_put_to_the_founder.csv")
    assert draft.columns("rules_put_to_the_founder.csv") == draft_rules.COLUMNS
    assert [row["rule"] for row in rows] == [rule.code for rule in draft_rules.RULES]
    names = {row["name"] for row in draft.rows("area_names.csv") if row["name"]}
    for row in rows:
        assert row["says"].endswith(".") and row["what_could_go_wrong"].endswith(".")
        assert not [name for name in names if name in row["says"] + row["what_could_go_wrong"]]
        assert float(row["hours"]) == pytest.approx(
            int(row["would_settle"]) * (480 if row["queue"] == "borders" else 45) / 3600, abs=0.05
        )


def test_a_name_whose_records_agree_and_that_has_no_mark_is_what_a_rule_would_settle(
    every: Made,
):
    settled = {row["item"]: row for row in every.rows("rules_would_settle.csv")}
    # Ordnance Survey writes it at a point inside, and the town centres write it over it.
    assert settled["n:lon-n0001"]["rule"] == "two_publishers_write_it"
    assert settled["n:lon-n0001"]["would_be"] == "accepted as proposed"
    # A name only a town centre holds, in a label of two names.
    assert settled["a:lon-n0009:grapnel-dock-cindermoor"]["rule"] == "a_label_of_two_names"
    assert settled["a:lon-n0009:grapnel-dock-cindermoor"]["would_be"] == "not kept"
    # A name with a mark to settle is left to the person.
    marked = {row["item"] for row in every.rows("names_to_look_at.csv") if row["grave"] == "true"}
    assert marked and not (set(settled) - {"a:lon-n0009:grapnel-dock-cindermoor"}) & marked
    # One publisher writes Thrushcombe, with no ward, no town centre and few roads of its
    # name: no rule fits it, and it is read.
    assert "n:lon-n0010" not in settled


def test_a_name_that_stands_by_the_founders_decision_is_settled_by_no_rule(draft: Made):
    """The first three rules ask that Ordnance Survey write the name at a point inside
    the area, and then ask for more. The decision names every name they fit."""
    settled = {row["item"]: row for row in draft.rows("rules_would_settle.csv")}
    assert set(settled) == {"a:lon-n0009:grapnel-dock-cindermoor"}
    put = {row["rule"]: row for row in draft.rows("rules_put_to_the_founder.csv")}
    first = put["two_publishers_write_it"]
    assert (first["would_settle"], first["already_decided"], first["hours"]) == ("0", "1", "0.0")
    assert {row["already_decided"] for rule, row in put.items() if rule != first["rule"]} == {"0"}
    counted = json.loads((draft.out / "counts.json").read_bytes())
    assert counted["rules_already_decided"]["two_publishers_write_it"] == 1
    assert sum(counted["rules_already_decided"].values()) == 1
    # Thrushcombe stands by the decision too, and was of no rule.
    assert counted["one_official_publisher"]["areas_named_by_the_rule_alone"] == 2


def test_every_rule_says_on_its_own_screen_what_the_founder_has_decided_already(draft: Made):
    """So that the founder is not asked twice. A rule with nothing left to settle says
    that no answer is needed."""
    lines = {
        row["item"]: row["value"]
        for row in draft.rows("desk/draft/lines.csv")
        if (row["queue"], row["label"]) == ("rules", "Already decided")
    }
    assert list(lines) == [rule.code for rule in draft_rules.RULES]
    for said in lines.values():
        assert said.startswith(
            "By the founder's decision of 2026-09-24 that one official publisher is enough, "
            "decision record 0022."
        )
    assert lines["two_publishers_write_it"].endswith(
        "Of the 1 name this rule fits, 1 stands by the decision and is not asked about. "
        "Nothing is left for this rule to settle. Either answer takes it off the queue, and "
        "changes nothing. Each is listed in the file named_by_the_rule.csv of the folder the "
        "draft was written to."
    )
    assert "It was the one rule that said it waited on the decision." in lines["a_ward_of_its_name"]
    for code in ("a_ward_of_its_name", "a_smaller_place_by_its_own_point", "a_label_of_two_names"):
        assert lines[code].endswith(
            "None of the 2 names that stand by the decision is of this rule."
        )
    assert lines["a_few_cells_across_a_borough_line"].endswith(
        "offered as before: that of an area whose name stands by the decision too."
    )
    names = {row["name"] for row in draft.rows("area_names.csv") if row["name"]}
    assert not [name for name in names if any(name in said for said in lines.values())]
    put = {row["rule"]: row for row in draft.rows("rules_put_to_the_founder.csv")}
    for code, said in lines.items():
        assert said.startswith(put[code]["what_the_decision_settled"])


def test_what_is_said_of_a_rule_counts_what_is_left_for_it():
    ward = draft_rules.BY_CODE["a_ward_of_its_name"]
    said = draft_rules.already_decided(ward, fitted=127, already=120, stands=373)
    assert said.endswith(
        "Of the 127 names this rule fits, 120 stand by the decision and are not asked about. "
        "7 are left for this rule to settle."
    )
    # With every name read, nothing stands by the decision, and nothing is counted.
    assert draft_rules.already_decided(ward, fitted=127, already=0, stands=0).endswith(
        "It was the one rule that said it waited on the decision."
    )
    assert "needs the founder's decision" not in ward.goes_wrong
    assert "The founder has decided that one official publisher is enough" in ward.goes_wrong


def test_the_counts_add_up_and_an_item_is_settled_by_one_rule_alone(draft: Made):
    settled = draft.rows("rules_would_settle.csv")
    assert len({(row["queue"], row["item"]) for row in settled}) == len(settled)
    counted = {
        row["rule"]: int(row["would_settle"]) for row in draft.rows("rules_put_to_the_founder.csv")
    }
    assert sum(counted.values()) == len(settled)
    assert (
        json.loads((draft.out / "counts.json").read_bytes())["rules_put_to_the_founder"] == counted
    )


def test_no_rule_is_adopted_and_every_item_is_still_put_to_the_person(every: Made, draft: Made):
    """A rule changes what the design promises, so it is the founder's to adopt."""
    settled = {row["item"] for row in every.rows("rules_would_settle.csv")}
    areas = {f"n:{row['area_id']}" for row in every.rows("desk/draft/areas.csv")}
    others = {row["alias"] for row in every.rows("desk/draft/aliases.csv")}
    assert "n:lon-n0001" in settled & areas
    assert "Grapnel Dock/ Cindermoor" in others
    assert {row["chosen_by"] for row in every.rows("name_evidence.csv")} == {""}
    assert {row["review_state"] for row in every.rows("areas.csv")} == {"drafted"}
    # What the founder has decided is no rule that was adopted: it is said of the area,
    # and what a rule would settle is of names that are still items.
    states = {f"n:{row['area_id']}": row["review_state"] for row in draft.rows("areas.csv")}
    left = {row["item"] for row in draft.rows("rules_would_settle.csv")}
    assert not [item for item in left if states.get(item) == "named_by_rule"]
    assert {row["chosen_by"] for row in draft.rows("name_evidence.csv")} == {""}


def test_the_desk_is_handed_every_rule_and_every_item_it_would_settle(draft: Made):
    """The desk puts each rule to the founder, as a queue of its own. It adopts none."""
    rules = draft.rows("desk/draft/rules.csv")
    assert draft.columns("desk/draft/rules.csv") == draft_rules.DESK_COLUMNS
    assert [row["rule"] for row in rules] == [rule.code for rule in draft_rules.RULES]
    put = {row["rule"]: row for row in draft.rows("rules_put_to_the_founder.csv")}
    for row in rules:
        assert (row["says"], row["goes_wrong"]) == (
            put[row["rule"]]["says"],
            put[row["rule"]]["what_could_go_wrong"],
        )
        assert row["queue"] == put[row["rule"]]["queue"]
    # What a rule gives an item it settles: the answer the draft proposes, the answer
    # that keeps no name, or none of the desk's answers, for a border left as drafted.
    assert {row["rule"]: row["gives"] for row in rules} == {
        "two_publishers_write_it": "proposed",
        "a_ward_of_its_name": "proposed",
        "many_roads_name_it": "proposed",
        "a_smaller_place_by_its_own_point": "proposed",
        "a_mark_that_asks_nothing": "proposed",
        "named_for_a_built_thing": "drop",
        "a_label_of_two_names": "drop",
        "a_few_cells_across_a_borough_line": "",
    }
    items = draft.rows("desk/draft/rules_items.csv")
    assert draft.columns("desk/draft/rules_items.csv") == draft_rules.DESK_ITEM_COLUMNS
    assert [(row["rule"], row["queue"], row["item"]) for row in items] == [
        (row["rule"], row["queue"], row["item"]) for row in draft.rows("rules_would_settle.csv")
    ]
    assert items and not [row for row in items if "name" in row]


def test_a_rule_that_leans_on_others_names_them_and_the_desk_is_told_which():
    """A rule that lets a name through to another rule settles nothing of its own. The
    desk holds it to the rule each item leans on, so the draft says which that is."""
    fifth = draft_rules.BY_CODE["a_mark_that_asks_nothing"]
    # It leant on the first three rules too, while they settled names. The decision on
    # one official publisher overtook them, and the name of an area with a mark is read.
    assert fifth.leans_on == ("a_smaller_place_by_its_own_point",)
    codes = [rule.code for rule in draft_rules.RULES]
    assert all(codes.index(code) < codes.index(fifth.code) for code in fifth.leans_on)
    assert [rule.code for rule in draft_rules.RULES if rule.leans_on] == [fifth.code]
    # Each rule is a screen of its own at the desk, so the words name each rule leant on.
    assert "above" not in fifth.says
    for code in fifth.leans_on:
        assert code.replace("_", " ").capitalize() in fifth.says
    rules, _ = draft_rules.for_the_desk([])
    assert {row["rule"]: row["leans_on"] for row in rules if row["leans_on"]} == {
        fifth.code: " ".join(fifth.leans_on)
    }


def test_a_name_held_back_only_by_a_mark_that_asks_nothing_leans_on_the_rule_its_records_fit():
    fifth = draft_rules.BY_CODE["a_mark_that_asks_nothing"]
    smaller = draft_rules.BY_CODE["a_smaller_place_by_its_own_point"]
    station, under = sorted(draft_rules.ASKS_NOTHING)
    assert draft_rules.rule_for(smaller, set()) == (smaller, "")
    assert draft_rules.rule_for(smaller, {station}) == (fifth, smaller.code)
    assert draft_rules.rule_for(smaller, {station, under}) == (fifth, smaller.code)
    # Any other mark leaves the name to the person, and so does a name no rule fits.
    assert draft_rules.rule_for(smaller, {station, "may_be_a_built_thing"}) == (None, "")
    assert draft_rules.rule_for(None, {station}) == (None, "")
    assert draft_rules.rule_for(None, set()) == (None, "")
    item = "a:lon-n0001:foxholt"
    settled = draft_rules.Settled(fifth.code, "names", item, "Foxholt", "", smaller.code)
    _, items = draft_rules.for_the_desk([settled])
    assert items == [{"rule": fifth.code, "queue": "names", "item": item, "leans_on": smaller.code}]
    assert settled.row()["leans_on"] == smaller.code


@pytest.mark.parametrize(
    "code", ["two_publishers_write_it", "a_ward_of_its_name", "many_roads_name_it"]
)
def test_the_name_of_an_area_with_any_mark_is_read_by_a_person(code: str):
    """A mark is a doubt the decision on one publisher did not settle. A station of the
    name that stands elsewhere may mean that the seed stands in the wrong place."""
    agrees = draft_rules.BY_CODE[code]
    station, under = sorted(draft_rules.ASKS_NOTHING)
    assert draft_rules.rule_for(agrees, set()) == (agrees, "")
    assert draft_rules.rule_for(agrees, {station}) == (None, "")
    assert draft_rules.rule_for(agrees, {under}) == (None, "")


def test_an_item_the_founder_has_decided_already_is_handed_to_the_desk_under_no_rule():
    first = draft_rules.BY_CODE["two_publishers_write_it"]
    stands = draft_rules.Settled(
        first.code, "names", "n:lon-n0001", "Alderwick", first.would_be, already=True
    )
    open_ = draft_rules.Settled(first.code, "names", "n:lon-n0002", "Wexmoor", first.would_be)
    assert draft_rules.left([stands, open_]) == [open_]
    _, items = draft_rules.for_the_desk([stands, open_])
    assert [row["item"] for row in items] == ["n:lon-n0002"]
    put = {row["rule"]: row for row in draft_rules.put_to_the_founder([stands, open_])}
    assert (put[first.code]["would_settle"], put[first.code]["already_decided"]) == ("1", "1")


def test_only_an_item_of_a_rule_that_leans_says_which_rule_it_leans_on(draft: Made):
    leaning = {rule.code for rule in draft_rules.RULES if rule.leans_on}
    for name in ("desk/draft/rules_items.csv", "rules_would_settle.csv"):
        for row in draft.rows(name):
            assert bool(row["leans_on"]) == (row["rule"] in leaning)


def test_every_rule_names_on_its_item_the_table_that_lists_what_it_would_settle(draft: Made):
    """The desk shows ten of the items a rule would settle. The rest are in a table of
    the draft, which the item names, so that the founder can skim them all."""
    every = [row for row in draft.rows("desk/draft/lines.csv") if row["queue"] == "rules"]
    lines = [row for row in every if row["label"] == "Every item"]
    assert [row["item"] for row in lines] == [rule.code for rule in draft_rules.RULES]
    assert {(row["label"], row["source_id"]) for row in every} == {
        ("Already decided", ""),
        ("Every item", ""),
    }
    assert all("the file rules_would_settle.csv" in row["value"] for row in lines)
    assert (draft.out / "rules_would_settle.csv").is_file()
    counted = json.loads((draft.out / "counts.json").read_bytes())["lines_for_the_desk"]
    assert counted["rules"] == 2 * len(draft_rules.RULES)


def test_what_each_decision_of_the_founder_turns_on_is_counted_and_nothing_is_decided(
    draft: Made,
):
    counted = json.loads((draft.out / "counts.json").read_bytes())["for_the_founder_to_decide"]
    assert counted == {
        "names_put_forward_as_areas": 5,
        "of_them_one_publisher_writes": 3,
        # Farrowmere and Thrushcombe have 3 of their 6 points from a centre of another name.
        "of_them_with_points_from_a_town_centre_of_another_name": 2,
        "of_them_reaching_the_points_asked_only_through_such_a_centre": 2,
        "of_them_known_by_a_record_in_the_smallest_box": 2,
        "of_them_holding_a_word_for_a_built_thing_in_a_larger_box": 0,
        "of_them_with_a_seed_moved_to_a_label_that_only_holds_the_name": 1,
        "of_them_resting_on_a_file_with_no_receipt": 5,
    }
    assert len(draft.rows("areas.csv")) == 5


# A border flagged for a few cells across a borough line


def town(outside: int, cells: int = 20, margin: float | None = None) -> Draft:
    held = {
        f"a{number:02d}": Cell(
            f"a{number:02d}",
            "lon-n0001",
            "E09000902" if number < outside else "E09000901",
            margin=margin,
        )
        for number in range(cells)
    }
    areas = {"lon-n0001": Area("lon-n0001", "Alderwick", publishers=("a", "b"))}
    # Each output area is beside the next, so that the area is in one piece.
    sides = [Side(f"a{number:02d}", f"a{number + 1:02d}", 100.0) for number in range(cells - 1)]
    return Draft(areas, held, sides, {"E09000901": "Quillhaven", "E09000902": "Tallowgate"})


def eighth(found: Draft, flags: list[Flag] | None = None) -> list[str]:
    raised = flags_of(found, Rules()) if flags is None else flags
    return [each.item for each in draft_rules.of_borders(found, raised)]


def test_a_border_flagged_only_for_a_few_cells_across_a_borough_line_would_not_be_offered():
    assert eighth(town(outside=1)) == ["lon-n0001"]
    assert eighth(town(outside=1, cells=11)) == ["lon-n0001"]
    # Five output areas, or a tenth of the area, is not a few.
    assert eighth(town(outside=5, cells=80)) == []
    assert eighth(town(outside=1, cells=10)) == []
    assert eighth(town(outside=0)) == []


def test_a_border_with_another_flag_about_the_border_is_still_offered_as_flagged():
    assert eighth(town(outside=1, margin=2.0)) == []
    # The desk shows every flag about the border, so each holds the rule back.
    found = town(outside=1)
    more = [*flags_of(found, Rules()), Flag("borders", "lon-n0001", "lon-n0001", "seeds_close", "")]
    assert eighth(found, more) == []
    # A flag about the name is raised where names are read, and holds nothing back here.
    named = [*flags_of(found, Rules()), Flag("borders", "lon-n0001", "lon-n0001", "no_receipt", "")]
    assert eighth(found, named) == ["lon-n0001"]


def test_no_rule_settles_the_name_of_an_area_in_which_a_heavier_name_lies():
    """The mark is listed on the heavier name, which is another item. It says that the
    area may be better named for that one, so the area's own name is read by a person:
    the decision on one official publisher holds such a name back, and so does a rule."""
    drafted, naming, _ = two_names()
    written = {
        "area_id": "lon-n0001",
        "name": "Alderwick",
        "role": "primary",
        "match": "same",
        "letter_for_letter": "true",
    }
    rows: dict[str, list[dict[str, str]]] = {
        "name_evidence.csv": [
            {**written, "source_id": "os-open-names", "locates": "point_inside"},
            {**written, "source_id": "gla-town-centre-boundaries", "locates": "polygon_overlap"},
        ],
        "names_to_look_at.csv": [],
    }
    settled = {each.item: each.rule for each in draft_rules.of_names(rows, drafted, naming)}
    assert settled["n:lon-n0001"] == "two_publishers_write_it"
    for mark in sorted(BEAR_ON_THE_AREA):
        rows["names_to_look_at.csv"] = [
            {"item": "a:lon-n0001:foxholt", "mark": mark, "area_id": "lon-n0001"}
        ]
        found = {each.item for each in draft_rules.of_names(rows, drafted, naming)}
        assert "n:lon-n0001" not in found
    # A mark on another name of the area that says nothing of the area's own holds
    # nothing back.
    rows["names_to_look_at.csv"] = [
        {"item": "a:lon-n0001:foxholt", "mark": "may_be_a_built_thing", "area_id": "lon-n0001"}
    ]
    assert "n:lon-n0001" in {each.item for each in draft_rules.of_names(rows, drafted, naming)}
