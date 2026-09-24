"""A name that stands by a rule the founder has decided is put to nobody.

The founder decided that one official publisher is enough for a name. A draft says of
an area whose name stands by that rule alone that it is `named_by_rule`. The desk makes
no item of its name, and asks about its border as before. Every draft here is written by
the test that reads it, and every name in it is made up.
"""

import io
import json
from pathlib import Path
from typing import Any

import pytest
from desk import fill
from desk.fill import draft
from desk.fill.draft import Draft
from desk.fill.layers import Unfit, canonical

from .conftest import REGISTRY, as_if_real
from .test_draft import squares

STANDS, DRAFTED = "named_by_rule", "drafted"


def areas_of(folder: Path, states: dict[str, str], names: dict[str, str] | None = None) -> None:
    """A draft of a row of areas, each one cell, each in the state given."""
    squares(folder, len(states))
    named = [
        {
            "area_id": area_id,
            "name": (names or {}).get(area_id, f"Area {at}"),
            "primary_borough": "Quillhaven",
            "review_state": state,
        }
        for at, (area_id, state) in enumerate(sorted(states.items()), start=1)
    ]
    draft.write_table(folder, "areas.csv", named)
    draft.write_table(folder, "name_evidence.csv", [])


def ids(items: list[dict[str, Any]]) -> list[str]:
    return [item["id"] for item in items]


def test_a_name_that_stands_by_the_rule_is_no_item_and_its_border_is_one(tmp_path: Path):
    areas_of(tmp_path, {"syn-n0001": STANDS, "syn-n0002": DRAFTED, "syn-n0003": STANDS})
    held = Draft.open(tmp_path, synthetic=True)
    assert ids(draft.names(held)) == ["n:syn-n0002"]
    assert ids(draft.borders(held)) == ["syn-n0001", "syn-n0002", "syn-n0003"]
    assert draft.stands(held) == ["syn-n0001", "syn-n0003"]


def test_another_name_of_an_area_that_stands_is_still_asked_about(tmp_path: Path):
    areas_of(tmp_path, {"syn-n0001": STANDS, "syn-n0002": DRAFTED})
    about = {"kind": "inside", "source_id": "synthetic-names", "record_id": "syn-r0001"}
    draft.write_table(
        tmp_path, "aliases.csv", [{**about, "alias": "Pellam", "area_id": "syn-n0001"}]
    )
    held = Draft.open(tmp_path, synthetic=True)
    assert sorted(ids(draft.names(held))) == ["a:syn-n0001:pellam", "n:syn-n0002"]


def test_a_name_the_draft_flags_is_asked_about_whatever_its_state(tmp_path: Path):
    """A flag is a doubt, and no doubt is lost without a word: a draft that says a name
    stands, and flags it, is asked about it."""
    areas_of(tmp_path, {"syn-n0001": STANDS, "syn-n0002": STANDS})
    flags = [{"queue": "names", "item": "n:syn-n0001", "flag": "same_name_elsewhere"}]
    draft.write_table(tmp_path, "flags.csv", flags)
    held = Draft.open(tmp_path, synthetic=True)
    assert ids(draft.names(held)) == ["n:syn-n0001"]
    assert draft.stands(held) == ["syn-n0002"]


def test_a_name_that_may_say_who_lives_there_is_put_to_the_founder_whatever_the_draft_says(
    tmp_path: Path,
):
    """Areas design, section 6: each such name is put to the founder. The desk holds a
    name to its own list of words, so a draft cannot take one out of the founder's hands."""
    names = {"syn-n0001": "Pensioners Rest", "syn-n0002": "Area 2"}
    areas_of(tmp_path, {"syn-n0001": STANDS, "syn-n0002": STANDS}, names)
    held = Draft.open(tmp_path, synthetic=True)
    [item] = draft.names(held)
    assert (item["id"], item["flags"]) == ("n:syn-n0001", ["describes_residents"])
    assert draft.stands(held) == ["syn-n0002"]


def test_an_area_in_any_other_state_is_asked_about(tmp_path: Path):
    states = {"syn-n0001": "", "syn-n0002": "name_checked", "syn-n0003": "by_rule"}
    areas_of(tmp_path, states)
    held = Draft.open(tmp_path, synthetic=True)
    assert ids(draft.names(held)) == ["n:syn-n0001", "n:syn-n0002", "n:syn-n0003"]
    assert draft.stands(held) == []


def test_what_a_draft_says_of_a_name_that_stands_stops_the_fill(tmp_path: Path):
    """A draft says nothing of a name that is put to nobody. Where it does, the two
    disagree, and the fill stops rather than lose what was said."""
    data = tmp_path / "desk-synthetic"
    areas_of(data / "draft", {"syn-n0001": STANDS, "syn-n0002": DRAFTED})
    row = {"queue": "names", "item": "n:syn-n0001", "label": "Size", "value": "4 cells."}
    draft.write_table(data / "draft", "lines.csv", [row])
    held = Draft.open(data / "draft", synthetic=True)
    with pytest.raises(Unfit, match=r"lines\.csv holds a line of an item that names does not"):
        draft.fill(held, "names", "2026-09-24", draft.questions()["names"])


def test_a_rule_that_names_a_name_that_stands_stops_the_fill(tmp_path: Path):
    """What the founder has decided already is settled by no rule."""
    areas_of(tmp_path, {"syn-n0001": STANDS, "syn-n0002": DRAFTED})
    rule = {"rule": "a_made_up_rule", "queue": "names", "gives": "proposed"}
    words = {"says": "Made up.", "goes_wrong": "Made up.", "leans_on": ""}
    draft.write_table(tmp_path, "rules.csv", [{**rule, **words}])
    items = [{"rule": "a_made_up_rule", "queue": "names", "item": "n:syn-n0001", "leans_on": ""}]
    draft.write_table(tmp_path, "rules_items.csv", items)
    with pytest.raises(Unfit, match=r"rules_items\.csv names an item that names does not hold"):
        draft.rules(Draft.open(tmp_path, synthetic=True))


def test_a_rule_with_nothing_left_to_settle_is_shown_and_draws_no_item(tmp_path: Path):
    """The decision on one official publisher names every name that three of the rules
    fit. Each rule is still shown, with what the draft says of it, and settles nothing."""
    areas_of(tmp_path, {"syn-n0001": STANDS, "syn-n0002": DRAFTED})
    rule = {"rule": "a_made_up_rule", "queue": "names", "gives": "proposed"}
    words = {"says": "Made up.", "goes_wrong": "Made up.", "leans_on": ""}
    draft.write_table(tmp_path, "rules.csv", [{**rule, **words}])
    draft.write_table(tmp_path, "rules_items.csv", [])
    said = {"queue": "rules", "item": "a_made_up_rule", "label": "Already decided"}
    draft.write_table(tmp_path, "lines.csv", [{**said, "value": "Made up.", "source_id": ""}])
    [item] = draft.rules(Draft.open(tmp_path, synthetic=True))
    lines = {line["label"]: line["value"] for line in item["lines"]}
    assert lines["Would settle"].startswith("0 of the 1 items of Names.")
    assert lines["Already decided"] == "Made up."
    # It explains what the rule would settle, so it is read straight after it.
    assert list(lines)[:4] == ["The rule", "Would settle", "Already decided", "What could go wrong"]
    assert item["preset"]["drawn"] == []
    assert not [label for label in lines if label.startswith("Drawn at random")]


def test_the_run_says_how_many_names_stand_and_are_not_asked_about(tmp_path: Path):
    data = tmp_path / "desk"
    states = {"syn-n0001": STANDS, "syn-n0002": DRAFTED, "syn-n0003": STANDS}
    areas_of(tmp_path / "made-up", states)
    # The layer as the desk's own step writes one, so that it can be read as London's.
    layer = tmp_path / "made-up" / "layers" / "quillhaven" / "cells.geojson"
    layer.write_text(canonical(json.loads(layer.read_text(encoding="utf-8"))), encoding="utf-8")
    as_if_real(tmp_path / "made-up", data / "draft")
    report = fill.fill(
        data / "draft", data, synthetic=False, made_on="2026-09-24", registry=REGISTRY
    )
    assert report.stands == 2
    names = next(queue for queue in report.queues if queue.queue == "names")
    assert names.items == 1
    out = io.StringIO()
    fill.say(report, out)
    assert (
        "2 names of areas stand by a rule the founder has decided, and are not asked about: "
        "2 min at the pace of names.\n" in out.getvalue()
    )


def test_the_run_says_nothing_of_it_where_no_name_stands(tmp_path: Path):
    data = tmp_path / "walk-synthetic"
    areas_of(data / "draft", {"syn-n0001": DRAFTED})
    held = Draft.open(data / "draft", synthetic=True)
    assert draft.stands(held) == []
    out = io.StringIO()
    fill.say(fill.Report(True, (), 0), out)
    assert "stand by a rule" not in out.getvalue()
