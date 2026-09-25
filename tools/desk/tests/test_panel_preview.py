"""To adjust the shares of a recipe: what would move is shown before anything is kept.

Every test reads the made-up city, which is the committed synthetic release, and asks
the panel with no port. No name here is of a real place, and every reason is made up.
"""

import dataclasses
import hashlib
import json
import shutil
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from burro_core import catalogue
from burro_core.catalogue import COUNTS_RESIDENTS, PLACED_ONLY_WITH, TAGS, tags_of
from burro_core.ids import FeatureId, GrittyVariant, TagId
from burro_pipeline import changes
from desk import cli, fill, records, server
from desk.panel import kept, preview, routes

START = datetime(2026, 10, 6, 21, 14, 9, tzinfo=UTC)
RELEASE = cli.FIXTURE / "syn-2026-09-23-01"
VIBE = "family_amenities"
WAS = {"school_primary_nearby": 40, "play_space_proximity": 35, "park_proximity": 25}
NOW = {"school_primary_nearby": 20, "play_space_proximity": 47, "park_proximity": 33}
WHY = "A park says more of a family's week than the count of schools."
# A reason no other test writes. If an answer or a log repeats what was sent, it shows.
CANARY = "Zzyzx Parva canary reason"


@pytest.fixture(scope="module")
def filled(tmp_path_factory: pytest.TempPathFactory) -> Path:
    data = tmp_path_factory.mktemp("preview") / "desk-synthetic"
    fill.fill(cli.FIXTURE, data, synthetic=True)
    return data


@pytest.fixture(scope="module")
def panel() -> routes.Panel:
    return routes.open_panel(RELEASE)


def no_sync(descriptor: int) -> None:
    """Stands in for the wait on the disk, which a test of the records holds to account."""


class Sitting:
    """One reviewer at the panel, asked with no port."""

    def __init__(self, desk: server.Desk, panel: routes.Panel, log: list[str]) -> None:
        self.desk, self.panel, self.log = desk, panel, log

    def get(self, route: str, of: str | None = None) -> dict[str, Any]:
        return self.panel.answer(self.desk, route, of, None)

    def post(self, route: str, /, **sent: Any) -> dict[str, Any]:
        return self.panel.answer(self.desk, route, None, sent)

    def preview(self, now: dict[str, int] = NOW, of: str = VIBE) -> dict[str, Any]:
        return self.post("preview", what="recipe", of=of, now=now)

    def keep(self, now: dict[str, int] = NOW, why: str = WHY, of: str = VIBE) -> dict[str, Any]:
        seen = self.preview(now, of)["seen"]
        return self.post("keep", what="recipe", of=of, now=now, why=why, seen=seen)

    def refused(self, route: str, /, **sent: Any) -> server.Refused:
        with pytest.raises(server.Refused) as caught:
            self.post(route, **sent)
        return caught.value

    @property
    def lines(self) -> tuple[changes.Change, ...]:
        return kept.read(self.desk.data, self.desk.reviewer)


Opener = Callable[..., Sitting]


@pytest.fixture
def opener(
    filled: Path, panel: routes.Panel, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Opener:
    monkeypatch.setattr(records, "_sync", no_sync)
    data = tmp_path / "desk-synthetic"
    shutil.copytree(filled, data)

    def start(reviewer: str = "r1") -> Sitting:
        log: list[str] = []
        desk = server.open_desk(
            data,
            cli.PAGE,
            cli.QUESTIONS,
            reviewer,
            clock=lambda: START,
            log=log.append,
            panel=panel,
        )
        return Sitting(desk, panel, log)

    return start


@pytest.fixture
def sitting(opener: Opener) -> Sitting:
    return opener()


# The three searches


def test_the_panel_ranks_three_searches_and_the_first_is_the_founders_own_sentence(
    panel: routes.Panel,
):
    assert [search.id for search in panel.searches] == [
        "the_founders_sentence",
        "a_family_buying_a_house",
        "nights_out_well_connected",
    ]
    cases = (cli.ROOT / "evals" / "reader" / "cases" / "whole_searches.jsonl").read_text("utf-8")
    case = next(json.loads(row) for row in cases.splitlines() if '"whole-035"' in row)
    assert panel.searches[0].says == case["text"]


def test_the_file_of_searches_holds_no_words_of_anybodys_search_and_names_no_place():
    held = json.loads(preview.SEARCHES.read_text(encoding="utf-8"))
    first, *others = held["searches"]
    # The founder's sentence is in the evaluation set, by their consent, and nowhere else.
    assert first["case"] == "whole-035" and "says" not in first
    for journey in first["journeys"]:
        assert set(journey) == {"words", "minutes", "firm"}
        assert all(type(at) is int for at in journey["words"])
    assert all(search["journeys"] == [] for search in others)
    assert all(set(vibe) == {"vibe", "toward"} for one in held["searches"] for vibe in one["vibes"])


def test_the_place_of_the_founders_journey_is_where_its_words_stand_in_the_sentence(
    panel: routes.Panel,
):
    founder = panel.searches[0]
    ((start, end),) = [journey["words"] for journey in founder.journeys]
    assert founder.says[:start].endswith("commute from ")
    assert founder.says[start:end].istitle() is False and founder.says[start].isupper()
    assert founder.says[end] == "."


def test_a_search_asks_for_no_part_that_counts_who_lives_somewhere_by_a_slider_of_the_panel(
    panel: routes.Panel,
):
    # The searches are the website's own edits. None weighs a census figure by itself.
    for search in panel.searches:
        assert not {feature_id for feature_id, _ in search.measures} & COUNTS_RESIDENTS


def test_a_journey_to_a_place_the_release_does_not_hold_is_left_out_and_said(
    panel: routes.Panel,
):
    found = preview.first_of(panel.searches[0], panel.held.release)
    assert preview.NO_PLACE in found["notes"]
    assert 0 < len(found["first"]) <= preview.FIRST
    assert found["ranked"] + found["left_out"] <= 24
    assert all(set(one) == {"id", "name", "borough"} for one in found["first"])


def test_a_vibe_the_release_places_no_area_on_is_left_out_of_a_search_and_said(
    panel: routes.Panel,
):
    unplaced = [
        vibe for vibe in panel.held.release.vibes if not panel.held.release.placed(vibe.tag_id)
    ]
    found = [preview.first_of(search, panel.held.release) for search in panel.searches]
    asked = {tag_id for search in panel.searches for tag_id, _ in search.vibes}
    for vibe in unplaced:
        if vibe.tag_id in asked:
            said = preview.NOT_IN_IT.format(label=TAGS[vibe.tag_id].label)
            assert any(said in one["notes"] for one in found)
    assert all(one["ranked"] > 0 for one in found)


# What would move


def test_what_a_slider_starts_from_is_what_stands_and_how_far_it_may_go(sitting: Sitting):
    adjust = sitting.get("vibe", VIBE)["adjust"]
    assert {part["measure"]: part["hundredths"] for part in adjust["shares"]} == WAS
    assert (adjust["least"], adjust["most"], adjust["as_served"]) == (1, 59, True)
    # Beside a part that counts who lived there, no part is over 40.
    assert sitting.get("vibe", "family_area")["adjust"]["most"] == 40
    assert [
        part["counts_residents"] for part in sitting.get("vibe", "family_area")["adjust"]["shares"]
    ] == [
        True,
        False,
        False,
        False,
    ]


def test_the_preview_says_how_many_areas_change_band_and_which_rise_and_fall_most(
    sitting: Sitting, panel: routes.Panel
):
    found = sitting.preview()
    assert (found["what"], found["of"], found["was"], found["now"]) == ("recipe", VIBE, WAS, NOW)
    bands = found["bands"]
    assert bands["areas"] == 24
    assert bands["change_band"] == sum(step["areas"] for step in bands["steps"]) > 0
    assert bands["up"] + bands["down"] <= bands["change_band"]
    assert 0 < len(bands["rise"]) <= 10 and 0 < len(bands["fall"]) <= 10
    assert all(
        set(one) == {"id", "name", "borough", "from", "to"}
        for one in (*bands["rise"], *bands["fall"])
    )
    # An area is said by its band, and never by the score it is ranked on.
    assert "score" not in json.dumps(found) and "raw" not in json.dumps(found["bands"])
    # Every band is the one core gives for the shares that are proposed.
    after = preview.with_vibes(
        panel.held.release,
        [
            vibe
            if vibe.tag_id != VIBE
            else vibe.replace(
                terms=tuple(term.replace(hundredths=NOW[term.feature_id]) for term in vibe.terms)
            )
            for vibe in panel.held.release.vibes
        ],
    )
    now = {row.area_id: row.band for row in after.tags if row.tag_id == VIBE}
    assert all(one["to"] == now[one["id"]] for one in (*bands["rise"], *bands["fall"]))


def test_the_preview_gives_the_first_ten_areas_of_each_search_before_and_after(
    sitting: Sitting,
):
    found = sitting.preview()["searches"]
    assert [one["id"] for one in found] == [
        "the_founders_sentence",
        "a_family_buying_a_house",
        "nights_out_well_connected",
    ]
    for one in found:
        assert 0 < len(one["before"]["first"]) == len(one["after"]["first"]) <= 10
        assert one["same"] is (one["before"]["first"] == one["after"]["first"])
    # The search that asks for the vibe moves, and one that does not ask for it does not.
    by_id = {one["id"]: one for one in found}
    assert by_id["a_family_buying_a_house"]["same"] is False
    assert by_id["nights_out_well_connected"]["same"] is True


def test_a_preview_of_what_stands_already_moves_nothing(sitting: Sitting):
    found = sitting.preview(WAS)
    assert found["bands"]["change_band"] == 0
    assert found["bands"]["rise"] == found["bands"]["fall"] == []
    assert all(one["same"] for one in found["searches"])


def test_a_preview_writes_nothing(sitting: Sitting):
    sitting.preview()
    assert not (sitting.desk.data / "decisions" / "changes").exists()


@pytest.mark.parametrize(
    ("of", "now", "words"),
    [
        # It does not come to 100.
        (VIBE, {**NOW, "school_primary_nearby": 30}, "recipe_keeps_its_rules"),
        # One part could place an area alone.
        (
            VIBE,
            {"school_primary_nearby": 60, "play_space_proximity": 20, "park_proximity": 20},
            "recipe_keeps_its_rules",
        ),
        # A part holds nothing.
        (
            VIBE,
            {"school_primary_nearby": 0, "play_space_proximity": 50, "park_proximity": 50},
            "recipe_keeps_its_rules",
        ),
        # Beside a part that counts who lived there, no part is over 40.
        (
            "family_area",
            {
                "households_dependent_children": 45,
                "school_primary_nearby": 25,
                "play_space_proximity": 15,
                "park_proximity": 15,
            },
            "recipe_keeps_its_rules",
        ),
        # No part is added, and none is taken out.
        (VIBE, {**NOW, "play_space_proximity": 37, "air_no2": 10}, "change_is_of_its_kind"),
        (VIBE, {"school_primary_nearby": 50, "play_space_proximity": 50}, "change_is_of_its_kind"),
        # No slider takes a census figure that the recipe does not hold.
        (
            VIBE,
            {**NOW, "play_space_proximity": 37, "households_dependent_children": 10},
            "change_is_of_its_kind",
        ),
        # A vibe the release does not carry.
        (
            "works_warehouses",
            {"land_industry": 50, "land_storage": 30, "land_transport_other": 20},
            changes.NOT_CARRIED,
        ),
    ],
)
def test_a_recipe_that_breaks_a_rule_is_refused_before_anything_is_worked_out(
    sitting: Sitting, of: str, now: dict[str, int], words: str
):
    refusal = sitting.refused("preview", what="recipe", of=of, now=now)
    assert (refusal.status, refusal.error) == (400, "bad_request")
    assert refusal.words == routes.BREAKS[words]
    seen = preview.seen("recipe", of, changes.recipe_of(TAGS[TagId(of)]), now)
    assert sitting.refused("keep", what="recipe", of=of, now=now, why=WHY, seen=seen).status == 400
    assert not (sitting.desk.data / "decisions" / "changes").exists()


@pytest.mark.parametrize(
    "sent",
    [
        {"what": "recipe", "of": VIBE},
        {"what": "recipe", "of": VIBE, "now": NOW, "value": 41.5},
        {"what": "recipe", "of": "no_such_vibe", "now": NOW},
        {"what": "recipe", "of": VIBE, "now": {"school_primary_nearby": "20"}},
        {"what": "recipe", "of": VIBE, "now": {"school_primary_nearby": 20.5}},
        {"what": "recipe", "of": VIBE, "now": [20, 47, 33]},
        {"what": "recipe", "of": VIBE, "now": {}},
        {"what": "figure", "of": "syn-n0004", "now": {"air_no2": 40}},
        {"what": "reading", "of": VIBE, "now": {"school_primary_nearby": "low"}},
    ],
)
def test_what_is_sent_to_be_looked_at_is_a_recipe_and_nothing_else(
    sitting: Sitting, sent: dict[str, Any]
):
    assert sitting.refused("preview", **sent).status == 400


# To keep


def test_a_kept_recipe_is_a_line_with_what_stood_before_what_stands_now_and_why(
    sitting: Sitting,
):
    answer = sitting.keep()
    assert answer["line"] == {
        "n": 1,
        "on": "2026-10-06",
        "by": "r1",
        "what": "recipe",
        "of": VIBE,
        "was": WAS,
        "now": NOW,
        "why": WHY,
        "takes_back": None,
    }
    assert [(line.n, line.was, line.now, line.why) for line in sitting.lines] == [
        (1, WAS, NOW, WHY)
    ]


def test_nothing_is_kept_that_was_not_looked_at_as_it_stands(sitting: Sitting):
    for seen in ("", "000000000000", preview.seen("recipe", VIBE, WAS, WAS)):
        refusal = sitting.refused("keep", what="recipe", of=VIBE, now=NOW, why=WHY, seen=seen)
        assert refusal.words == routes.NOT_LOOKED_AT
    assert not sitting.lines


def test_a_change_is_kept_with_its_reason_and_never_without(sitting: Sitting):
    seen = sitting.preview()["seen"]
    for why in ("", "   ", "x" * 501, "two\nlines"):
        refusal = sitting.refused("keep", what="recipe", of=VIBE, now=NOW, why=why, seen=seen)
        assert refusal.words == routes.NO_REASON
    assert not sitting.lines


def test_what_stands_already_is_not_kept_again(sitting: Sitting):
    seen = sitting.preview(WAS)["seen"]
    refusal = sitting.refused("keep", what="recipe", of=VIBE, now=WAS, why=WHY, seen=seen)
    assert refusal.words == routes.NOTHING_CHANGED
    assert not sitting.lines


def test_a_second_change_is_made_of_what_the_first_made(sitting: Sitting):
    sitting.keep()
    adjust = sitting.get("vibe", VIBE)["adjust"]
    assert {part["measure"]: part["hundredths"] for part in adjust["shares"]} == NOW
    assert adjust["as_served"] is False
    later = {"school_primary_nearby": 30, "play_space_proximity": 40, "park_proximity": 30}
    found = sitting.preview(later)
    assert found["was"] == NOW
    sitting.keep(later, why="Schools count for more than that.")
    assert [(line.was, line.now) for line in sitting.lines] == [(WAS, NOW), (NOW, later)]
    # A mark of a preview made before the first change was kept is of no use after it.
    stale = preview.seen("recipe", VIBE, WAS, later)
    assert sitting.refused("keep", what="recipe", of=VIBE, now=later, why=WHY, seen=stale)


def test_a_build_reads_what_the_panel_kept(sitting: Sitting):
    sitting.keep()
    sitting.post("flag", of="figure/syn-n0004/air_no2", why="Too low.", leave_out=False)
    written = kept.path_of(sitting.desk.data, "r1").read_bytes()
    lines = changes.read(written)
    built = {vibe.tag_id: vibe for vibe in changes.adjusted(tags_of(GrittyVariant.B), lines)}
    assert changes.recipe_of(built[TagId(VIBE)]) == NOW
    assert all(built[tag_id] == TAGS[tag_id] for tag_id in built if tag_id != VIBE)
    assert changes.applied(lines, changes.OF_THE_CATALOGUE) == [
        {"n": 1, "what": "recipe", "of": VIBE, "by": "r1", "on": "2026-10-06"}
    ]


def test_what_was_kept_and_not_yet_built_is_said_on_the_first_screen(sitting: Sitting):
    sitting.keep()
    home = sitting.get("home")
    assert [(one["n"], one["what"], one["of"], one["why"]) for one in home["changed"]] == [
        (1, "recipe", VIBE, WHY)
    ]
    # The release that is served is as it was: nothing a person does here changes it.
    served = sitting.get("vibe", VIBE)["vibe"]["recipe"]
    assert {part["measure"]: part["hundredths"] for part in served} == WAS


def test_a_kept_change_is_taken_back_and_the_file_says_so(sitting: Sitting):
    sitting.keep()
    sitting.post("take-back", n=1, why="It put the centre of town first.")
    assert [(line.n, line.what.value, line.takes_back) for line in sitting.lines] == [
        (1, "recipe", None),
        (2, "take_back", 1),
    ]
    assert sitting.get("home")["changed"] == []
    adjust = sitting.get("vibe", VIBE)["adjust"]
    assert {part["measure"]: part["hundredths"] for part in adjust["shares"]} == WAS
    assert changes.adjusted(tags_of(GrittyVariant.B), sitting.lines) == tags_of(GrittyVariant.B)


def test_a_second_reviewers_change_is_a_proposal_shown_beside_the_founders_and_never_built(
    opener: Opener,
):
    founder, second = opener("r1"), opener("r2")
    founder.keep()
    theirs = {"school_primary_nearby": 50, "play_space_proximity": 30, "park_proximity": 20}
    second.keep(theirs, why="Schools are what a family asks about first.")
    # Each writes a file of their own, and each was made of core's own.
    assert [line.was for line in second.lines] == [WAS]
    differ = founder.get("history")["differ"]
    assert [(one["what"], one["of"], one["built"]) for one in differ] == [("recipe", VIBE, "r1")]
    assert [(line["by"], line["now"]) for line in differ[0]["said"]] == [
        ("r1", NOW),
        ("r2", theirs),
    ]
    # The first screen says what would be built, which is the founder's.
    assert [(one["by"], one["now"]) for one in second.get("home")["changed"]] == [("r1", NOW)]


def test_what_the_panel_prints_and_what_it_refuses_never_repeat_a_reason(sitting: Sitting):
    seen = sitting.preview()["seen"]
    refusal = sitting.refused("keep", what="recipe", of=VIBE, now=NOW, why=CANARY + "\n", seen=seen)
    assert "Zzyzx" not in refusal.words
    sitting.keep(why=CANARY)
    assert not any("Zzyzx" in line for line in sitting.log)


# What a release was built with


def lines_of(*made: tuple[str, Any]) -> bytes:
    rows: list[dict[str, Any]] = []
    for n, (what, more) in enumerate(made, start=1):
        held = {"n": n, "on": "2026-10-06", "by": "r1", "what": what, "of": VIBE, "was": None}
        rows.append({**held, "now": None, "why": WHY, "takes_back": None, **more})
    return "".join(json.dumps(row) + "\n" for row in rows).encode()


def test_a_release_was_built_with_the_start_of_the_file_as_it_stands():
    first = lines_of(("recipe", {"was": WAS, "now": NOW}))
    whole = lines_of(("recipe", {"was": WAS, "now": NOW}), ("take_back", {"takes_back": 1}))
    built = (hashlib.sha256(first).hexdigest(), len(first))
    assert routes.built_of(None, whole) == 0
    assert routes.built_of(built, first) == 1
    assert routes.built_of(built, whole) == 1
    # A file that does not begin as the file the release was built with is another file.
    assert routes.built_of(built, whole.replace(b"2026-10-06", b"2026-10-07")) is None
    assert routes.built_of(built, b"") is None


def test_what_was_changed_and_what_was_taken_back_since_the_build_are_both_not_yet_built():
    later = {"school_primary_nearby": 30, "play_space_proximity": 40, "park_proximity": 30}
    lines = changes.read(
        lines_of(
            ("recipe", {"was": WAS, "now": NOW}),
            ("recipe", {"was": NOW, "now": later}),
            ("take_back", {"takes_back": 2}),
        )
    )
    assert [line.n for line in routes.not_yet_built(lines, 0)] == [1]
    assert [line.n for line in routes.not_yet_built(lines, 1)] == []
    assert [line.n for line in routes.not_yet_built(lines, 2)] == [1]
    assert [line.n for line in routes.not_yet_built(lines, 3)] == []
    gone = changes.read(
        lines_of(("recipe", {"was": WAS, "now": NOW}), ("take_back", {"takes_back": 1}))
    )
    # The release carries a change that was taken back since: a build would put it right.
    assert [line.n for line in routes.not_yet_built(gone, 1)] == [2]
    assert routes.not_yet_built(gone, 2) == []


# A vibe that is held off


def without(panel: routes.Panel, *parts: str) -> routes.Panel:
    """The panel on the made-up release with no figure for some measures: every band is
    worked out again, by core's own recipes, as a build would have."""
    release = panel.held.release
    bare = dataclasses.replace(
        release,
        features=tuple(
            row.replace(value=None, percentile=None, coverage=0.0)
            if row.feature_id in parts
            else row
            for row in release.features
        ),
    )
    rows = {
        (row.area_id, row.tag_id): row
        for vibe in release.vibes
        for row in preview.rows_of(bare, vibe)
    }
    again = dataclasses.replace(
        bare, tags=tuple(rows[row.area_id, row.tag_id] for row in release.tags)
    )
    return dataclasses.replace(panel, held=dataclasses.replace(panel.held, release=again))


def sat_at(panel: routes.Panel, data: Path) -> Sitting:
    desk = server.open_desk(
        data, cli.PAGE, cli.QUESTIONS, "r1", clock=lambda: START, log=lambda _: None, panel=panel
    )
    return Sitting(desk, panel, [])


def test_a_vibe_the_release_places_no_area_on_is_placed_by_no_change_to_its_shares(
    sitting: Sitting, panel: routes.Panel
):
    # Two parts of Going out have no figure, so 35 in 100 of its recipe is there.
    bare = without(panel, "venue_evening_per_homes", "venue_food_drink_per_homes")
    assert bare.held.release.placed(TagId.PACE) is False
    there = sat_at(bare, sitting.desk.data)
    to_what_is_left = dict(zip(changes.recipe_of(TAGS[TagId.PACE]), (1, 1, 58, 40), strict=True))
    refusal = there.refused("preview", what="recipe", of="pace", now=to_what_is_left)
    assert refusal.words == routes.BREAKS["held_off_stays_held_off"]
    seen = preview.seen("recipe", "pace", changes.recipe_of(TAGS[TagId.PACE]), to_what_is_left)
    refusal = there.refused(
        "keep", what="recipe", of="pace", now=to_what_is_left, why=WHY, seen=seen
    )
    assert refusal.words == routes.BREAKS["held_off_stays_held_off"]
    assert not there.lines
    # A change that places no area is looked at as any other.
    within: dict[str, int] = dict(
        zip(changes.recipe_of(TAGS[TagId.PACE]), (40, 30, 15, 15), strict=True)
    )
    assert there.preview(within, of="pace")["bands"]["placed_after"] == 0


def test_a_vibe_that_is_held_off_is_placed_by_no_change_to_its_shares(
    sitting: Sitting, panel: routes.Panel, monkeypatch: pytest.MonkeyPatch
):
    """For a while, Leafy places an area only where woodland has a figure.

    No vibe is held off today. Village feel was, until the founder chose on 2026-09-25 to
    serve it on another recipe, as a rough guide. What holding a vibe off does is kept for
    any vibe that is held off in future, and is held here on a vibe that is not.
    """
    assert dict(PLACED_ONLY_WITH) == {}
    held_off = {TagId.LEAFY: frozenset({FeatureId.LAND_WOODLAND})}
    monkeypatch.setattr(catalogue, "PLACED_ONLY_WITH", held_off)
    bare = without(panel, "land_woodland")
    assert bare.held.release.placed(TagId.LEAFY) is False
    there = sat_at(bare, sitting.desk.data)
    held = changes.recipe_of(TAGS[TagId.LEAFY])
    looked = there.preview(dict(zip(held, (58, 1, 41), strict=True)), of="leafy")
    assert looked["bands"]["placed_before"] == looked["bands"]["placed_after"] == 0
    assert looked["bands"]["change_band"] == 0
