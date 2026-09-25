"""The panel's own code, run against the desk's own server.

`test_panel_server.py` asks the desk as the panel would, in words written by hand. This
runs the panel itself: `page/test/support/panel-at-the-desk.mjs` starts the desk on the
loopback address, as `make desk` does, hands the panel a stand-in for the browser and
presses what a person would. Here what came on the screen is read, and then the file of
changes on the disk. So a change to the panel's page or to its server that the other
does not follow is caught.

It needs Node, as `make desk-check` does, and is left out where there is none. No browser
is opened, so nothing here says how the panel looks.
"""

import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from burro_pipeline import changes
from desk import cli, fill, server
from desk.panel import kept, routes

NODE = shutil.which("node")
DRIVER = cli.PAGE / "test" / "support" / "panel-at-the-desk.mjs"
MADE_UP = "MADE-UP CITY. Nothing here is a real place."
REASON = "A made-up reason, from the panel"
VIBE = "family_amenities"

pytestmark = pytest.mark.skipif(NODE is None, reason="Node is not on the PATH")


@dataclass(frozen=True)
class Sat:
    data: Path
    # What came on the screen, as the driver wrote it down.
    seen: dict[str, Any]

    @property
    def lines(self) -> tuple[changes.Change, ...]:
        return kept.read(self.data, "r1")


@pytest.fixture(scope="module")
def sat(tmp_path_factory: pytest.TempPathFactory) -> Sat:
    data = tmp_path_factory.mktemp("panel-page") / "desk-synthetic"
    fill.fill(cli.FIXTURE, data, synthetic=True)
    assert NODE is not None
    ran = subprocess.run(
        [NODE, str(DRIVER), sys.executable, str(cli.ROOT / "tools"), str(data)],
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
        cwd=cli.ROOT,
    )
    assert ran.returncode == 0, ran.stderr[-2000:]
    return Sat(data, json.loads(ran.stdout))


def test_the_panel_opens_on_what_is_served_and_says_the_city_is_made_up(sat: Sat):
    first = sat.seen["first"]
    assert (first["banner"], first["trouble"]) == (MADE_UP, "")
    assert first["tab"] == "What is served - The panel - Burro review desk"
    assert "Release syn-2026-09-23-01, built on 2026-09-23. The made-up city." in first["main"]
    assert "24 areas." in first["main"] and "Nothing was changed." in first["main"]
    assert "Names" in first["main"] and "Borders" in first["main"]


def test_an_area_is_found_by_its_name_and_shown_with_every_figure(sat: Sat):
    assert "24 of 24 areas." in sat.seen["areas"]["main"]
    assert "1 of 24 areas." in sat.seen["found"]["main"]
    area = sat.seen["area"]
    assert area["tab"].startswith("Dulcimer Green - ")
    for words in (
        "Dulcimer Green, Quillhaven",
        "Modelled annual mean nitrogen dioxide",
        "19.7 µg/m³",
        "Leafy",
        "4 of 5",
        "40 in 100: Land that is residential garden, read from its high end. It has a figure.",
        "No figure for:",
        "This build does not work the measure out.",
    ):
        assert words in area["main"], words


def test_a_measure_and_a_vibe_are_shown_and_the_map_of_a_vibe_is_drawn(sat: Sat):
    assert re.search(r"\d+ of 24 areas have a figure", sat.seen["measure"]["main"])
    vibe = sat.seen["vibe"]["main"]
    assert "Its five bands" in vibe and "What it follows" in vibe
    assert "Homes per hectare:" in vibe
    assert {"beginPath", "lineTo", "fill", "stroke"} <= set(sat.seen["drawn"])
    assert "Going out" in sat.seen["vibes"]["main"]
    assert "Homes per hectare" in sat.seen["measures"]["main"]


def test_what_moved_says_how_to_name_the_release_to_hold_this_one_against(sat: Sat):
    moved = sat.seen["moved"]
    assert moved["tab"] == "What moved - The panel - Burro review desk"
    assert (moved["trouble"], moved["banner"]) == ("", MADE_UP)
    # The heading, and then the one line: a page holds no space between two of its nodes.
    assert moved["main"] == f"What moved{routes.NO_OTHER}"


def test_a_figure_is_flagged_in_one_press_with_a_note_and_the_line_is_on_the_disk(sat: Sat):
    assert sat.seen["asked_why"] == {
        "open": True,
        "of": "Modelled annual mean nitrogen dioxide, of Dulcimer Green",
    }
    flagged = sat.seen["flagged"]
    assert (flagged["open"], flagged["trouble"]) == (False, "")
    assert flagged["said"].startswith("Flagged: Modelled annual mean nitrogen dioxide")
    assert "Flagged here" in flagged["main"] and REASON in flagged["main"]
    first = sat.lines[0]
    assert (first.n, first.by, first.what, first.of, first.why) == (
        1,
        "r1",
        changes.What.FLAG,
        "figure/syn-n0004/air_no2",
        REASON,
    )
    assert "Flagged: 1" in sat.seen["listed"]["main"]
    assert "1 flagged" in sat.seen["home"]["main"]


def test_the_flag_is_taken_back_from_the_history_which_is_itself_a_line(sat: Sat):
    assert REASON in sat.seen["history"]["main"]
    back = sat.seen["taken_back"]
    assert (back["open"], back["trouble"]) == (False, "")
    assert "Taken back by line 2" in back["main"]
    assert "Nothing is flagged." in sat.seen["after"]["main"]
    assert [(line.n, line.what, line.takes_back) for line in sat.lines[:2]] == [
        (1, changes.What.FLAG, None),
        (2, changes.What.TAKE_BACK, 1),
    ]


def test_a_share_is_moved_by_a_slider_and_the_shares_still_come_to_100(sat: Sat):
    assert (sat.seen["recipe"]["shares"], sat.seen["recipe"]["can_look"]) == ([40, 35, 25], False)
    slid = sat.seen["slid"]
    assert slid == {"shares": [20, 47, 33], "can_look": True, "can_keep": False}


def test_what_would_move_is_shown_before_anything_is_kept(sat: Sat):
    looked = sat.seen["looked"]
    assert looked["can_keep"] is True and looked["trouble"] == ""
    assert re.search(r"\d+ of 24 areas change band: \d+ go up, and \d+ go down\.", looked["main"])
    for words in (
        "The areas that rise most",
        "The areas that fall most",
        "The first ten areas of three searches, before and after",
        "The founder's own sentence",
        "A family, buying a house",
        "Nights out, and well connected",
        "The release names no place for the journey of this search. It is left out.",
    ):
        assert words in looked["main"], words
    # Nothing was written by looking.
    assert [line.what for line in sat.lines][:2] == [changes.What.FLAG, changes.What.TAKE_BACK]


def test_the_shares_that_were_kept_are_a_line_of_the_file_and_nothing_served_has_changed(
    sat: Sat,
):
    kept_as = sat.seen["kept"]
    assert kept_as["said"].startswith("Kept: the shares of Family amenities. It is line 3 of")
    line = sat.lines[2]
    assert (line.n, line.by, line.what, line.of) == (3, "r1", changes.What.RECIPE, VIBE)
    assert line.was == {
        "school_primary_nearby": 40,
        "play_space_proximity": 35,
        "park_proximity": 25,
    }
    assert line.now == {
        "school_primary_nearby": 20,
        "play_space_proximity": 47,
        "park_proximity": 33,
    }
    assert line.why == "A made-up reason to move a share"
    # The sliders start from what was kept, and the release is served as it was.
    assert kept_as["shares"] == [20, 47, 33]
    assert "You have kept a change of this vibe that is not yet built." in kept_as["main"]
    assert "A made-up reason to move a share" in sat.seen["changed"]["main"]


def test_the_shares_are_taken_back_from_the_history_and_stand_as_they_did(sat: Sat):
    back = sat.seen["recipe_back"]
    assert (back["open"], back["trouble"]) == (False, "")
    assert [(line.n, line.what, line.takes_back) for line in sat.lines[2:4]] == [
        (3, changes.What.RECIPE, None),
        (4, changes.What.TAKE_BACK, 3),
    ]
    assert "Nothing was changed." in sat.seen["unchanged"]["main"]
    assert sat.seen["recipe_after"]["shares"] == [40, 35, 25]


def test_a_chain_is_moved_to_another_tier_at_the_table_of_brands(sat: Sat):
    assert "Lidl" in sat.seen["brands"]["main"] and "Add a chain" in sat.seen["brands"]["main"]
    looked = sat.seen["brand_looked"]
    assert (looked["open"], looked["title"]) == (True, "Keep")
    assert "tier value" in looked["more"] and "tier premium" in looked["more"]
    assert "A build works these measures out again:" in looked["more"]
    kept_as = sat.seen["brand_kept"]
    assert (kept_as["open"], kept_as["trouble"]) == (False, "")
    assert kept_as["said"].startswith("Kept: Lidl: to another tier. It is line 5 of")
    assert "Premium, which you changed" in kept_as["main"]
    line = sat.lines[4]
    assert (line.what, line.of, line.now["tier"], line.was["tier"]) == (
        changes.What.BRAND,
        "lidl",
        "premium",
        "value",
    )


def test_a_vibe_is_given_another_name_and_a_measure_another_label(sat: Sat):
    looked = sat.seen["name_looked"]
    assert looked["open"] is True
    assert "label Leafy" in looked["more"] and "label Green and leafy" in looked["more"]
    assert sat.seen["name_kept"]["said"].startswith("Kept: Leafy: its name. It is line 6 of")
    refused = sat.seen["name_refused"]
    assert refused["open"] is False
    assert refused["trouble"].startswith("A name is one line of plain words")
    assert sat.seen["label_kept"]["said"].startswith("Kept: ")
    name, label = sat.lines[5], sat.lines[6]
    assert (name.what, name.of, name.now) == (
        changes.What.NAME,
        "leafy",
        {"label": "Green and leafy", "low_end": None, "high_end": None},
    )
    assert (label.what, label.of) == (changes.What.LABEL, "air_no2")
    assert label.now["short_label"] == "Nitrogen dioxide"


def test_a_screen_the_desk_does_not_hold_says_so(sat: Sat):
    nowhere = sat.seen["nowhere"]
    assert nowhere["trouble"] == server.WORDS[server.NOT_FOUND]
    assert "Dulcimer Green" not in nowhere["main"]


def test_the_panel_asks_the_desk_by_a_path_and_nothing_else(sat: Sat):
    routes = (
        r"state|panel/(home|areas|outlines|measures|flags|history|brands|moved)"
        r"|panel/(flag|take-back|preview|keep)"
        r"|panel/(area|measure|vibe)/[a-z0-9_-]+"
    )
    assert len(sat.seen["asked"]) > 10
    for line in sat.seen["asked"]:
        assert re.fullmatch(rf"(GET|POST) /api/({routes})", line), "a path the desk does not know"


def test_the_desk_prints_nothing_of_what_the_panel_asked_or_sent(sat: Sat):
    printed = sat.seen["printed"].replace("/syn-2026-09-23-01.", "")
    assert "A made-up" not in printed and "syn-" not in printed and "air_no2" not in printed
    assert "POST /api/panel/flag 200" in printed and "GET /api/panel/area/{id} 200" in printed
