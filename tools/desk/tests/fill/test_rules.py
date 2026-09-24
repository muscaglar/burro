"""The rules put to the founder, as a queue of their own.

A draft may put rules that would settle items without a person: each with what it would
settle and what could go wrong. None is adopted until the founder says yes at the desk.
The fill makes an item of each rule, and says on each item a rule fits which rule that is.
Every rule here is made up, and so is every name.
"""

import csv
import json
from pathlib import Path
from typing import Any

import pytest
from desk import fill
from desk.fill import draft, synthetic
from desk.fill.layers import Unfit

from .conftest import REGISTRY, Filled, fill_made_up

QUESTIONS = json.loads(draft.QUESTIONS.read_text(encoding="utf-8"))["queues"]
RULES = next(queue for queue in QUESTIONS if queue["id"] == "rules")


def shown(item: dict[str, Any]) -> list[tuple[str, str]]:
    return [(line["label"], line["value"]) for line in item["lines"]]


def rows_of(folder: Path, name: str) -> list[dict[str, str]]:
    with (folder / name).open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def fits(made_up: Filled, rule: str) -> list[tuple[str, dict[str, Any]]]:
    """Every item that a rule fits, with its queue, in the order of the queues."""
    return [
        (queue, item)
        for queue in ("names", "borders")
        for item in made_up.items(queue)
        if item["preset"].get("fits") == rule
    ]


# The question


def test_the_rules_are_the_first_queue_and_the_founders_alone():
    assert QUESTIONS[0] is RULES
    assert (RULES["open_to"], RULES["public"], RULES["view"]) == ("founder", True, "text")
    assert [answer["code"] for answer in RULES["answers"]] == ["yes", "no"]
    assert RULES["after"] == []
    # Names are read once the rules are decided, and borders once the names are.
    after = {queue["id"]: queue["after"] for queue in QUESTIONS}
    assert after["names"] == ["rules"]
    assert after["borders"] == after["whole"] == ["rules", "names"]


def test_the_rule_of_the_queue_says_that_none_is_adopted_until_the_founder_says_yes():
    said = RULES["rule"]
    assert "None is adopted until you say yes" in said
    assert "No changes nothing" in said and said.endswith("Undo takes it back.")


# The items


def test_each_rule_the_draft_puts_is_an_item_in_the_order_the_draft_puts_them(made_up: Filled):
    put = rows_of(made_up.data / "draft", "rules.csv")
    assert made_up.ids("rules") == [row["rule"] for row in put]
    assert len(put) == len(synthetic.RULES_PUT) >= 5
    for item, row in zip(made_up.items("rules"), put, strict=True):
        about = {"rule": row["rule"], "queue": row["queue"], "gives": row["gives"]}
        leans = {"leans_on": row["leans_on"].split()} if row["leans_on"] else {}
        held = {"settles": item["preset"]["settles"], "drawn": item["preset"]["drawn"]}
        assert item["preset"] == {**about, **held, **leans}
        settles = [[each["id"], each["rev"]] for _, each in fits(made_up, row["rule"])]
        assert item["preset"]["settles"] == draft.revision({"settles": settles})
        assert (item["group"], item["flags"], item["picks"]) == (row["queue"], [], None)
        assert item["map"] is None and item["text"] is None, "its lines are what is read"


def test_a_rule_is_shown_in_words_with_how_much_it_would_settle_and_what_could_go_wrong(
    made_up: Filled,
):
    put = {row["rule"]: row for row in rows_of(made_up.data / "draft", "rules.csv")}
    for item in made_up.items("rules"):
        row, said = put[item["id"]], shown(item)
        settles = fits(made_up, item["id"])
        assert said[0] == ("The rule", row["says"])
        assert said[1][0] == "Would settle"
        assert said[1][1].startswith(f"{len(settles)} ")
        # A rule that leans on others says so before what could go wrong.
        assert said[3 if row["leans_on"] else 2] == ("What could go wrong", row["goes_wrong"])
        assert item["title"] == f"{draft.in_words(item['id']).capitalize()} (made up)"
    item = made_up.item("rules", "two_made_up_publishers_write_it")
    assert dict(shown(item))["Would settle"] == (
        "17 of the 37 items of Names. 13 min at the pace of the design, which nobody has timed."
    )


def test_a_rule_shows_ten_of_the_items_it_would_settle_drawn_at_random(made_up: Filled):
    item = made_up.item("rules", "a_made_up_smaller_place")
    drawn = [value for label, value in shown(item) if label.startswith("Drawn at random")]
    settles = {each["title"].removesuffix(" (made up)") for _, each in fits(made_up, item["id"])}
    assert len(settles) < 10 and len(drawn) == len(settles)
    assert {value.split(". ")[0] for value in drawn} == settles
    assert all(value.endswith("Accepted as proposed: A smaller place inside.") for value in drawn)
    many = made_up.item("rules", "every_made_up_border")
    drawn = [value for label, value in shown(many) if label.startswith("Drawn at random")]
    assert len(drawn) == 10 < len(fits(made_up, many["id"]))
    assert len(set(drawn)) == 10
    assert all(value.endswith("Left as drafted, and offered to nobody.") for value in drawn)


def test_each_item_that_is_drawn_can_be_found_by_the_page_to_open_it(made_up: Filled):
    """The page opens an item that is drawn from the rule, and comes back to the rule.
    So the rule holds the id of each, in the order of its lines."""
    for rule in made_up.items("rules"):
        drawn = [line for line in rule["lines"] if line["label"].startswith("Drawn at random")]
        ids = rule["preset"]["drawn"]
        assert len(ids) == len(drawn) == len(set(ids))
        held = {item["id"]: item for item in made_up.items(rule["preset"]["queue"])}
        for at, (name, line) in enumerate(zip(ids, drawn, strict=True), start=1):
            assert held[name]["preset"]["fits"] == rule["id"]
            assert line["label"] == f"Drawn at random, {at} of {len(drawn)}"
            assert line["value"].startswith(held[name]["title"].removesuffix(" (made up)"))


def test_the_same_ten_are_drawn_whenever_the_queues_are_filled(made_up: Filled, tmp_path: Path):
    again = fill_made_up(tmp_path / "desk-synthetic")
    assert again.rows("rules") == made_up.rows("rules")


def test_a_rule_that_would_drop_the_name_of_an_area_with_ground_says_that_the_answer_waits(
    made_up: Filled,
):
    item = made_up.item("rules", "named_for_a_made_up_building")
    areas = [each for _, each in fits(made_up, item["id"]) if each["preset"].get("holds")]
    assert areas, "the made-up rule would drop an area that has ground"
    said = dict(shown(item))["Waits for a new draft"]
    assert said.startswith(f"{len(areas)} of these ")
    assert "set aside until the draft is made again" in said
    other = made_up.item("rules", "two_made_up_publishers_write_it")
    assert "Waits for a new draft" not in dict(shown(other))


def test_an_item_a_rule_fits_says_which_rule_and_what_it_would_be(made_up: Filled):
    fitted = {
        queue: [item for item in made_up.items(queue) if "fits" in item["preset"]]
        for queue in ("names", "borders")
    }
    assert len(fitted["names"]) > 10 and len(fitted["borders"]) > 10
    put = {row["rule"]: row for row in rows_of(made_up.data / "draft", "rules.csv")}
    for queue, items in fitted.items():
        for item in items:
            rule = put[item["preset"]["fits"]]
            assert rule["queue"] == queue
            label, value = shown(item)[-1]
            assert label == "A rule fits"
            assert value.startswith(f"{draft.in_words(rule['rule']).capitalize()}. ")
    name = made_up.item("names", "n:syn-n0001")
    assert shown(name)[-1] == (
        "A rule fits",
        "Two made up publishers write it. If you adopt it in Rules, this is accepted "
        "as proposed: An area.",
    )


def test_a_rule_that_leans_on_others_says_which_and_how_many_of_its_items_lean_on_each(
    made_up: Filled,
):
    item = made_up.item("rules", synthetic.LEANS)
    assert item["preset"]["leans_on"] == list(synthetic.LEANS_ON)
    assert dict(shown(item))["Leans on"] == (
        "This rule settles an item only where the rule the item leans on is adopted too. "
        "Of the 1 item it fits, those that lean on each rule: 0 on Two made up publishers "
        "write it, 1 on A made up smaller place."
    )
    others = [each for each in made_up.items("rules") if each["id"] != synthetic.LEANS]
    assert not [each for each in others if "leans_on" in each["preset"]]
    assert not [each for each in others if "Leans on" in dict(shown(each))]


def test_an_item_of_a_rule_that_leans_names_the_rule_it_leans_on(made_up: Filled):
    ((queue, item),) = fits(made_up, synthetic.LEANS)
    assert (queue, item["preset"]["leans_on"]) == ("names", "a_made_up_smaller_place")
    assert set(item["flags"]) <= synthetic.ASKS_NOTHING, "but for its flags, that rule fits"
    assert shown(item)[-1] == (
        "A rule fits",
        "A made up flag that asks nothing. It leans on the rule A made up smaller place. "
        "If you adopt both in Rules, this is accepted as proposed: A smaller place inside.",
    )
    for queue in ("names", "borders"):
        for other in made_up.items(queue):
            leans = other["preset"].get("fits") == synthetic.LEANS
            assert ("leans_on" in other["preset"]) == leans


def test_what_the_draft_says_of_a_rule_is_shown_before_the_items_that_are_drawn(
    real_draft: Path,
):
    """The draft names on a rule the table that lists every item the rule would settle."""
    said = "rules,every_made_up_border,Every item,Made up for testing: every_item.csv.,\n"
    path = real_draft / "lines.csv"
    head = "" if path.exists() else "queue,item,label,value,source_id\n"
    with path.open("a", encoding="utf-8") as file:
        file.write(head + said)
    report = fill.fill(real_draft, real_draft.parent, synthetic=False, registry=REGISTRY)
    item = Filled(real_draft.parent, report).item("rules", "every_made_up_border")
    labels = [label for label, _ in shown(item)]
    assert labels[:4] == ["The rule", "Would settle", "What could go wrong", "Every item"]
    assert set(labels[4:]) == {f"Drawn at random, {at} of 10" for at in range(1, 11)}
    assert dict(shown(item))["Every item"] == "Made up for testing: every_item.csv."


def test_an_item_no_rule_fits_says_nothing_of_rules(made_up: Filled):
    flagged = made_up.item("names", "n:syn-n0020")
    assert "fits" not in flagged["preset"]
    assert "A rule fits" not in dict(shown(flagged))
    for queue in ("know", "whole", "ratings", "kinds"):
        assert not [item for item in made_up.items(queue) if "fits" in item["preset"]]


def test_an_item_is_settled_by_one_rule_alone(made_up: Filled):
    ruled = rows_of(made_up.data / "draft", "rules_items.csv")
    assert len({(row["queue"], row["item"]) for row in ruled}) == len(ruled)
    assert sum(len(fits(made_up, item["id"])) for item in made_up.items("rules")) == len(ruled)


def test_a_rule_is_open_again_when_what_it_would_settle_has_changed(
    made_up: Filled, real_draft: Path
):
    def revs() -> dict[str, str]:
        report = fill.fill(real_draft, real_draft.parent, synthetic=False, registry=REGISTRY)
        return {
            item["id"]: item["rev"] for item in Filled(real_draft.parent, report).items("rules")
        }

    before = revs()
    # One item fewer: the founder said yes to another list than this one.
    path = real_draft / "rules_items.csv"
    held = path.read_text(encoding="utf-8").splitlines(keepends=True)
    gone = next(row for row in held if row.startswith("a_made_up_smaller_place,"))
    path.write_text("".join(row for row in held if row != gone), encoding="utf-8")
    after = revs()
    assert after["a_made_up_smaller_place"] != before["a_made_up_smaller_place"]
    same = set(before) - {"a_made_up_smaller_place"}
    assert {rule: after[rule] for rule in same} == {rule: before[rule] for rule in same}


def test_a_draft_that_puts_no_rule_has_no_queue_of_rules(real_draft: Path):
    (real_draft / "rules.csv").unlink()
    (real_draft / "rules_items.csv").unlink()
    report = fill.fill(real_draft, real_draft.parent, synthetic=False, registry=REGISTRY)
    rules = next(queue for queue in report.queues if queue.queue == "rules")
    assert rules.lacks == ("rules.csv", "rules_items.csv") and rules.items == 0
    names = Filled(real_draft.parent, report).items("names")
    assert not [item for item in names if "fits" in item["preset"]]


# What is refused


@pytest.mark.parametrize(
    ("name", "row", "refusal"),
    [
        (
            "rules_items.csv",
            "a_made_up_smaller_place,names,n:lon-n9999,\n",
            "rules_items.csv names an item that names does not hold",
        ),
        (
            "rules_items.csv",
            "no_such_rule,names,n:lon-n0001,\n",
            "rules_items.csv names a rule that rules.csv does not hold",
        ),
        (
            "rules_items.csv",
            "a_made_up_smaller_place,names,n:lon-n0001,\n",
            "rules_items.csv gives an item to two rules",
        ),
        (
            "rules_items.csv",
            "every_made_up_border,names,n:lon-n0020,\n",
            "rules_items.csv gives a rule an item of another queue than its own",
        ),
        (
            "rules.csv",
            "one_more,kinds,yes,Made up.,Made up.,\n",
            "rules.csv puts a rule to a queue that no rule may settle",
        ),
        (
            "rules.csv",
            "one_more,names,right,Made up.,Made up.,\n",
            "rules.csv gives an answer that is none of the queue's",
        ),
        (
            "rules.csv",
            "one_more,borders,right,Made up.,Made up.,\n",
            "rules.csv gives an answer to a border. A rule may only leave one as drafted",
        ),
        (
            "rules.csv",
            "one_more,names,area,Made up.,,\n",
            "rules.csv puts a rule with no words, or without what could go wrong",
        ),
        (
            "rules.csv",
            "two_made_up_publishers_write_it,names,proposed,Made up.,Made up.,\n",
            "rules.csv puts a rule twice",
        ),
        (
            "rules.csv",
            "one_more,names,proposed,Made up.,Made up.,no_such_rule\n",
            "rules.csv has a rule lean on one that is not put before it",
        ),
        (
            "rules.csv",
            "one_more,names,proposed,Made up.,Made up.,every_made_up_border\n",
            "rules.csv has a rule lean on one that is not put before it for the same queue",
        ),
        (
            "rules.csv",
            "one_more,names,proposed,Made up.,Made up.,a_made_up_flag_that_asks_nothing\n",
            "rules.csv has a rule lean on one .* that leans on another",
        ),
        (
            "rules_items.csv",
            "a_made_up_flag_that_asks_nothing,names,n:lon-n0020,\n",
            "rules_items.csv holds an item that .* names none where its rule leans on others",
        ),
        (
            "rules_items.csv",
            "a_made_up_flag_that_asks_nothing,names,n:lon-n0020,every_made_up_border\n",
            "rules_items.csv holds an item that leans on a rule its own rule does not lean on",
        ),
        (
            "rules_items.csv",
            "a_made_up_smaller_place,names,n:lon-n0020,two_made_up_publishers_write_it\n",
            "rules_items.csv holds an item that leans on a rule its own rule does not lean on",
        ),
    ],
)
def test_rules_that_are_not_as_the_design_gives_them_stop_the_fill(
    real_draft: Path, name: str, row: str, refusal: str
):
    with (real_draft / name).open("a", encoding="utf-8") as file:
        file.write(row)
    with pytest.raises(Unfit, match=refusal):
        fill.fill(real_draft, real_draft.parent, synthetic=False, registry=REGISTRY)
    assert not (real_draft.parent / "items").exists()


def test_a_rule_may_accept_only_what_the_draft_proposes(real_draft: Path):
    # An item with nothing proposed has no answer for a rule to give.
    path = real_draft / "aliases.csv"
    held = path.read_text(encoding="utf-8").replace(",inside,", ",nearby,")
    path.write_text(held, encoding="utf-8")
    with pytest.raises(
        Unfit, match="gives what the draft proposes to an item with nothing proposed"
    ):
        fill.fill(real_draft, real_draft.parent, synthetic=False, registry=REGISTRY)
