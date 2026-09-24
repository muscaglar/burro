"""What a draft has the desk mark on the map of a border, in `marks.csv`.

A draft says which cells are in doubt and why, which stretch of a border follows no line,
which seed stands close, and which town centres a flag names. The fill puts them in the
item's map, for the page to draw. Every draft here is the made-up city under other
names, and every mark in it is made up.
"""

import csv
from pathlib import Path

import pytest
from desk import fill
from desk.fill.layers import Unfit

from .conftest import REGISTRY, Filled

COLUMNS = ("queue", "item", "flag", "kind", "what")
BORDER, BESIDE = "lon-n0007", "lon-n0012"


def rows_of(folder: Path, name: str) -> list[dict[str, str]]:
    with (folder / name).open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def cells_of(real_draft: Path, area: str) -> list[str]:
    given = rows_of(real_draft, "oa_to_area.csv")
    return sorted(row["oa21cd"] for row in given if row["area_id"] == area)


def write_marks(folder: Path, rows: list[tuple[str, ...]]) -> None:
    with (folder / "marks.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerows([COLUMNS, *rows])


def filled(real_draft: Path) -> Filled:
    data = real_draft.parent
    return Filled(data, fill.fill(real_draft, data, synthetic=False, registry=REGISTRY))


def test_what_the_draft_marks_is_in_the_map_of_the_border_by_kind(real_draft: Path):
    own, other = cells_of(real_draft, BORDER), cells_of(real_draft, BESIDE)
    write_marks(
        real_draft,
        [
            ("borders", BORDER, "two_boroughs", "cell", own[1]),
            ("borders", BORDER, "margin_under_10", "cell", own[1]),
            ("borders", BORDER, "margin_under_10", "cell", own[0]),
            ("borders", BORDER, "follows_nothing", "side", f"{own[0]} {other[0]}"),
            ("borders", BORDER, "seeds_close", "seed", BESIDE),
            ("borders", BORDER, "two_centres", "centre", "Tallowgate Parade"),
        ],
    )
    held = filled(real_draft)
    assert held.item("borders", BORDER)["map"]["marks"] == {
        "cells": {own[0]: ["margin_under_10"], own[1]: ["two_boroughs", "margin_under_10"]},
        "sides": [[own[0], other[0]]],
        "seeds": [BESIDE],
        "centres": ["Tallowgate Parade"],
    }
    # A border the draft marks nothing on has no marks, and no other queue has any.
    assert "marks" not in held.item("borders", BESIDE)["map"]
    for queue in ("names", "whole", "know"):
        assert not [item for item in held.items(queue) if "marks" in (item["map"] or {})]


def test_a_mark_opens_no_answer_about_a_border_again(real_draft: Path):
    """A border is decided on the ground. What is marked on its map is how it is shown."""
    before = filled(real_draft).item("borders", BORDER)
    write_marks(real_draft, [("borders", BORDER, "seeds_close", "seed", BESIDE)])
    after = filled(real_draft).item("borders", BORDER)
    assert after["map"] != before["map"] and after["rev"] == before["rev"]


@pytest.mark.parametrize(
    ("row", "refusal"),
    [
        (("names", "n:lon-n0007", "margin_under_10", "cell", "{own}"), "a queue that marks"),
        (("borders", "lon-n9999", "two_centres", "centre", "Osierholm"), "an item that borders"),
        (("borders", BORDER, "margin_under_10", "dot", "{own}"), "a kind of mark"),
        (("borders", BORDER, "margin_under_10", "cell", "{other}"), "a cell of another area"),
        (("borders", BORDER, "margin_under_10", "cell", ""), "a cell of another area"),
        (("borders", BORDER, "follows_nothing", "side", "{own}"), "a side that is not"),
        (("borders", BORDER, "follows_nothing", "side", "{other} {own}"), "a side that is not"),
        (("borders", BORDER, "follows_nothing", "side", "{own} {own}"), "a side that is not"),
        (("borders", BORDER, "seeds_close", "seed", BORDER), "the seed of no other area"),
        (("borders", BORDER, "seeds_close", "seed", "lon-n9999"), "the seed of no other area"),
        (("borders", BORDER, "two_centres", "centre", " "), "a town centre with no name"),
        (("borders", BORDER, "no_such_flag", "cell", "{own}"), "a flag the page has no words"),
    ],
)
def test_a_mark_that_is_not_as_the_design_gives_it_stops_the_fill(
    real_draft: Path, row: tuple[str, ...], refusal: str
):
    own, other = cells_of(real_draft, BORDER)[0], cells_of(real_draft, BESIDE)[0]
    write_marks(real_draft, [tuple(each.format(own=own, other=other) for each in row)])
    with pytest.raises(Unfit, match=refusal) as refused:
        fill.fill(real_draft, real_draft.parent, synthetic=False, registry=REGISTRY)
    assert own not in str(refused.value), "a refusal names the file and never a value"
    assert not (real_draft.parent / "items").exists()


def test_the_made_up_city_marks_the_cells_in_doubt_and_the_town_centres_a_flag_names(
    made_up: Filled,
):
    marked = {
        item["id"]: item["map"]["marks"]
        for item in made_up.items("borders")
        if "marks" in item["map"]
    }
    flagged: dict[str, set[str]] = {}
    for item in made_up.items("borders"):
        flagged[item["id"]] = set(item["flags"])
    assert marked
    for name, marks in marked.items():
        under = {flag for flags in marks["cells"].values() for flag in flags}
        assert under <= {"margin_under_10", "two_boroughs"}
        # A cell with a margin under 10% is marked whether or not its area is flagged for it.
        assert under - {"margin_under_10"} <= flagged[name]
    two = [name for name, flags in flagged.items() if "two_centres" in flags]
    assert two and all(len(marked[name]["centres"]) == 2 for name in two)
    assert "Tallowgate Parade" in marked["syn-n0021"]["centres"]
