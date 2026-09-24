"""What a draft says beside an item, in `lines.csv`, reaches the item when the queues are
filled.

A draft writes a plain sentence for every doubt it has. The fill reads them itself, so
that no second step has to be remembered after a fill. Every draft here is the made-up
city under other names, and every line in it is made up.
"""

import csv
from pathlib import Path
from typing import Any

import pytest
from desk import fill
from desk.fill import draft, gate
from desk.fill.layers import Unfit

from .conftest import REGISTRY, Filled

COLUMNS = ("queue", "item", "label", "value", "source_id")
NAME, BORDER = "n:lon-n0004", "lon-n0007"
# What a draft might say of a name and of a border. The cell is one the border holds.
LINES = (
    ("names", NAME, "Look hard", "A station of this name stands 1,200 m off.", ""),
    (
        "names",
        NAME,
        "The Made-up Survey, Names",
        "Dulcimer Green. A point inside this area. Record lon-r0007.",
        "os-open-names",
    ),
    ("names", NAME, "Points", "6 points, where 4 are asked.", ""),
    ("borders", BORDER, "Flagged", "Its seed is 410 m from the seed of Lantern Yard.", ""),
    ("borders", BORDER, "In doubt", "2 output areas are in doubt.", ""),
    ("borders", BORDER, "lon-oa0250", "margin 3%, streets: Tanner Row", "os-open-roads"),
)


def write_lines(folder: Path, rows: tuple[tuple[str, ...], ...] = LINES) -> None:
    with (folder / "lines.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerows([COLUMNS, *rows])


def filled(real_draft: Path) -> Filled:
    data = real_draft.parent
    return Filled(data, fill.fill(real_draft, data, synthetic=False, registry=REGISTRY))


def items_of(real_draft: Path) -> dict[str, dict[str, dict[str, Any]]]:
    """Every item of the four queues of the areas as a fill writes them now, by queue
    and id, in the order of the file. A second fill writes over the files of the first."""
    held = filled(real_draft)
    return {
        queue: {item["id"]: item for item in held.items(queue)}
        for queue in ("names", "borders", "whole", "know")
    }


def shown(item: dict[str, Any]) -> list[tuple[str, str, str]]:
    return [(line["label"], line["value"], line["source_id"]) for line in item["lines"]]


def test_the_lines_of_the_draft_stand_under_the_first_line_of_the_desk(real_draft: Path):
    before = items_of(real_draft)
    write_lines(real_draft)
    after = items_of(real_draft)
    name, border = after["names"][NAME], after["borders"][BORDER]
    assert shown(name) == [("Proposed as", "An area", ""), *(row[2:] for row in LINES[:3])]
    assert shown(border)[0] == shown(before["borders"][BORDER])[0]
    assert shown(border)[0][0] == "Cells"
    assert shown(border)[1:] == [row[2:] for row in LINES[3:]]
    assert shown(border) != shown(before["borders"][BORDER])


def test_an_item_the_draft_says_nothing_of_shows_the_lines_of_the_desk(real_draft: Path):
    before = items_of(real_draft)
    write_lines(real_draft)
    after = items_of(real_draft)
    for queue, held in after.items():
        for name, now in held.items():
            if name not in (NAME, BORDER):
                assert now == before[queue][name], name
    assert len(after["names"]) > 30 and len(after["borders"]) > 20


def test_nothing_of_an_item_is_changed_but_its_lines_and_the_revision_of_a_name(
    real_draft: Path,
):
    before = items_of(real_draft)
    write_lines(real_draft)
    after = items_of(real_draft)
    for queue, name in (("names", NAME), ("borders", BORDER)):
        was, now = before[queue][name], after[queue][name]
        assert {key for key in now if now[key] != was[key]} <= {"lines", "rev"}
    # A name is decided on what is shown. A border is decided on the ground, and a line
    # that is said another way opens no answer about it again.
    assert after["names"][NAME]["rev"] != before["names"][NAME]["rev"]
    assert after["names"][NAME]["rev"] == draft.revision(after["names"][NAME])
    assert after["borders"][BORDER]["rev"] == before["borders"][BORDER]["rev"]


def test_the_order_of_the_items_is_the_desks_whatever_the_draft_says(real_draft: Path):
    before = items_of(real_draft)
    write_lines(real_draft)
    after = items_of(real_draft)
    for queue in ("names", "borders"):
        assert list(after[queue]) == list(before[queue])


def test_a_border_shows_every_cell_the_draft_has_in_doubt(real_draft: Path):
    # The desk's own lines stop at six cells. A draft lists every one, and the page rings
    # each cell that a line is labelled with.
    cells = [f"lon-oa{at:04d}" for at in range(240, 252)]
    rows = tuple(("borders", BORDER, cell, "margin 3%", "") for cell in cells)
    write_lines(real_draft, rows)
    item = filled(real_draft).item("borders", BORDER)
    assert [line["label"] for line in item["lines"][1:]] == cells


def test_a_file_of_items_says_it_was_made_from_the_lines_too(real_draft: Path):
    write_lines(real_draft)
    after = filled(real_draft)
    for queue in ("names", "borders"):
        made = [each for each in after.header(queue)["made_from"] if each["file"] == "lines.csv"]
        # A line with no source is Burro's own work, and says so.
        assert {each["source_id"] for each in made} == {"burro", "os-open-names", "os-open-roads"}
        assert len({each["sha256"] for each in made}) == 1
    assert not [each for each in after.header("know")["made_from"] if each["file"] == "lines.csv"]


def test_filling_again_gives_the_same_items_with_no_step_between(real_draft: Path):
    write_lines(real_draft)
    once = filled(real_draft)
    held = {queue: once.rows(queue) for queue in ("names", "borders")}
    again = filled(real_draft)
    assert {queue: again.rows(queue) for queue in held} == held


@pytest.mark.parametrize(
    ("source", "refusal"),
    [
        ("osm-place-nodes", "'osm-place-nodes' is gated"),
        ("hoc-library-msoa-names", "'hoc-library-msoa-names' is gated"),
        ("google-places", "'google-places' is banned"),
        ("synthetic-names", "A real draft names a made-up source"),
    ],
)
def test_a_line_from_a_source_the_registry_refuses_stops_the_fill(
    real_draft: Path, source: str, refusal: str
):
    write_lines(real_draft, (*LINES, ("names", NAME, "A publisher", "A name.", source)))
    with pytest.raises(gate.Refused, match=refusal):
        filled(real_draft)
    assert not (real_draft.parent / "items").exists()


def test_a_line_of_an_item_the_queue_does_not_hold_stops_the_fill(real_draft: Path):
    # A doubt that reaches no item would be lost without a word.
    write_lines(real_draft, (*LINES, ("names", "n:lon-n9999", "Look hard", "A doubt.", "")))
    with pytest.raises(Unfit, match=r"lines\.csv holds a line of an item that names does not"):
        filled(real_draft)
    assert not (real_draft.parent / "items").exists()


def test_a_line_of_a_queue_the_desk_does_not_have_stops_the_fill(real_draft: Path):
    write_lines(real_draft, (("streets", "lon-n0004", "Look hard", "A doubt.", ""),))
    with pytest.raises(Unfit, match=r"lines\.csv names a queue the desk does not have"):
        filled(real_draft)


@pytest.mark.parametrize("label", ["Residents", "Household income", "Crime"])
def test_a_label_about_who_lives_somewhere_stops_the_fill(real_draft: Path, label: str):
    write_lines(real_draft, (("borders", BORDER, label, "A figure.", ""),))
    with pytest.raises(Unfit, match="would show words about who lives somewhere"):
        filled(real_draft)
    assert not (real_draft.parent / "items").exists()


def test_a_file_of_lines_that_is_not_as_the_design_gives_it_stops_the_fill(real_draft: Path):
    (real_draft / "lines.csv").write_text("queue,item,label\nnames,n:lon-n0004,A\n", "utf-8")
    with pytest.raises(Unfit, match=r"lines\.csv does not have the columns of the design"):
        filled(real_draft)


def test_a_line_with_no_label_or_no_words_stops_the_fill(real_draft: Path):
    write_lines(real_draft, (("names", NAME, "", "A doubt.", ""),))
    with pytest.raises(Unfit, match=r"lines\.csv holds a line with no label or no words"):
        filled(real_draft)


def test_the_made_up_city_needs_no_lines(made_up: Filled):
    assert not (made_up.data / "draft" / "lines.csv").exists()
    assert made_up.item("names", "n:syn-n0004")["lines"][0]["label"] == "Proposed as"


def test_the_first_line_of_a_border_counts_no_cell_in_doubt(made_up: Filled):
    """The desk counted the cells on a border with a margin under 10%, and the draft every
    cell in doubt. Two counts stood side by side and differed. The draft's is the one."""
    for item in made_up.items("borders"):
        label, value = item["lines"][0]["label"], item["lines"][0]["value"]
        assert label == "Cells" and "under" not in value and "%" not in value
        cells, edge = (int(part.split()[0]) for part in value.split(", "))
        assert value == f"{cells} cells, {edge} on a border" and 0 < edge <= cells


def test_a_margin_of_a_hundred_or_more_is_said_in_words_by_the_desk_too():
    said = draft.placed_by({"margin": "240", "second": "Foxholt"})
    assert said == "second choice Foxholt, which is 3.4 times as far"
    assert draft.placed_by({"margin": "999"}) == "its second choice is over 10 times as far"
    assert draft.placed_by({"margin": "100", "ward": "Alderwick"}) == (
        "its second choice is twice as far, its ward is Alderwick"
    )
    assert draft.placed_by({"margin": "7", "second": "Foxholt"}) == (
        "margin 7%, second choice Foxholt"
    )
    assert draft.placed_by({}) == "No evidence is given"
