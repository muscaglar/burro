"""To relabel at the panel: the name of a vibe and of its ends, what it cannot see, and the
label of a measure.

Every test reads the made-up city and asks the panel with no port. Every reason is made up.
"""

import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from burro_core.catalogue import FEATURES, TAGS, tags_of
from burro_core.ids import FeatureId, GrittyVariant, TagId
from burro_pipeline import changes
from desk import cli, fill, records, server
from desk.panel import kept, routes

START = datetime(2026, 10, 6, 21, 14, 9, tzinfo=UTC)
RELEASE = cli.FIXTURE / "syn-2026-09-23-01"
WHY = "It is what people call it."
LEAFY = {"label": "Green and leafy", "low_end": None, "high_end": None}
PACE = {"label": "Pace", "low_end": "Sleepy", "high_end": "Busy"}
NO2 = {
    "label": "Nitrogen dioxide in the air, as a mean over the year",
    "short_label": "Nitrogen dioxide",
}


@pytest.fixture(scope="module")
def filled(tmp_path_factory: pytest.TempPathFactory) -> Path:
    data = tmp_path_factory.mktemp("relabel") / "desk-synthetic"
    fill.fill(cli.FIXTURE, data, synthetic=True)
    return data


@pytest.fixture(scope="module")
def panel() -> routes.Panel:
    return routes.open_panel(RELEASE)


def no_sync(descriptor: int) -> None:
    """Stands in for the wait on the disk, which a test of the records holds to account."""


class Sitting:
    """One reviewer at the panel, asked with no port."""

    def __init__(self, desk: server.Desk, panel: routes.Panel) -> None:
        self.desk, self.panel = desk, panel

    def get(self, route: str, of: str | None = None) -> dict[str, Any]:
        return self.panel.answer(self.desk, route, of, None)

    def post(self, route: str, /, **sent: Any) -> dict[str, Any]:
        return self.panel.answer(self.desk, route, None, sent)

    def keep(self, what: str, of: str, now: Any, why: str = WHY) -> dict[str, Any]:
        seen = self.post("preview", what=what, of=of, now=now)["seen"]
        return self.post("keep", what=what, of=of, now=now, why=why, seen=seen)

    def refused(self, what: str, of: str, now: Any) -> server.Refused:
        with pytest.raises(server.Refused) as caught:
            self.post("preview", what=what, of=of, now=now)
        return caught.value

    @property
    def lines(self) -> tuple[changes.Change, ...]:
        return kept.read(self.desk.data, self.desk.reviewer)


@pytest.fixture
def sitting(
    filled: Path, panel: routes.Panel, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Sitting:
    monkeypatch.setattr(records, "_sync", no_sync)
    data = tmp_path / "desk-synthetic"
    shutil.copytree(filled, data)
    desk = server.open_desk(
        data, cli.PAGE, cli.QUESTIONS, "r1", clock=lambda: START, log=lambda _: None, panel=panel
    )
    return Sitting(desk, panel)


def built(sitting: Sitting) -> dict[TagId, Any]:
    """The vibes as a build would carry them, from the file the panel wrote."""
    return {vibe.tag_id: vibe for vibe in changes.adjusted(tags_of(GrittyVariant.B), sitting.lines)}


def test_the_name_of_a_vibe_is_changed_and_a_build_carries_it(sitting: Sitting):
    looked = sitting.post("preview", what="name", of="leafy", now=LEAFY)
    assert looked["was"] == {"label": "Leafy", "low_end": None, "high_end": None}
    assert looked["now"] == LEAFY and "bands" not in looked
    sitting.keep("name", "leafy", LEAFY)
    adjust = sitting.get("vibe", "leafy")["adjust"]
    assert (adjust["names"], adjust["as_served"]) == (LEAFY, False)
    # What is served is as it was, until a build is made.
    assert sitting.get("vibe", "leafy")["vibe"]["label"] == "Leafy"
    made = built(sitting)[TagId.LEAFY]
    assert (made.label, made.short_label) == ("Green and leafy", "Green and leafy")
    assert made.terms == TAGS[TagId.LEAFY].terms, "a name moves no share"


def test_the_two_ends_of_a_scale_are_named(sitting: Sitting):
    sitting.keep("name", "pace", PACE)
    made = built(sitting)[TagId.PACE]
    assert (made.label, made.low_end, made.high_end) == ("Pace", "Sleepy", "Busy")


def test_what_a_vibe_cannot_see_is_changed_after_the_line_every_vibe_says_first(
    sitting: Sitting,
):
    stands = sitting.get("vibe", "leafy")["adjust"]["cannot_see"]
    assert stands == list(TAGS[TagId.LEAFY].cannot_see[1:])
    now = [*stands, "Whether a garden is kept."]
    sitting.keep("cannot_see", "leafy", now)
    made = built(sitting)[TagId.LEAFY]
    assert made.cannot_see == (TAGS[TagId.LEAFY].cannot_see[0], *now)


def test_the_label_of_a_measure_is_changed_and_a_build_carries_it(sitting: Sitting):
    adjust = sitting.get("measure", "air_no2")["adjust"]
    core = FEATURES[FeatureId.AIR_NO2]
    assert adjust == {
        "labels": {"label": core.label, "short_label": core.short_label},
        "may": True,
        "as_served": True,
    }
    sitting.keep("label", "air_no2", NO2)
    assert sitting.get("measure", "air_no2")["adjust"]["labels"] == NO2
    metrics = changes.relabelled(sitting.panel.held.release.metrics, sitting.lines)
    made = next(metric for metric in metrics if metric.feature_id is FeatureId.AIR_NO2)
    assert (made.label, made.short_label) == (NO2["label"], NO2["short_label"])
    assert [(one["what"], one["of"]) for one in sitting.get("home")["changed"]] == [
        ("label", "air_no2")
    ]


def test_a_measure_that_counts_who_lived_somewhere_keeps_the_name_core_gives_it(
    sitting: Sitting,
):
    counted = "households_dependent_children"
    assert sitting.get("measure", counted)["adjust"]["may"] is False
    now = {"label": "Families with children", "short_label": "Families"}
    refusal = sitting.refused("label", counted, now)
    assert refusal.words == routes.BREAKS["who_is_counted_is_named_by_core"]
    assert not sitting.lines


@pytest.mark.parametrize(
    ("what", "of", "now", "words"),
    [
        # A word that calls a place safe or unsafe, praise, and a word for a group of people.
        ("name", "leafy", {**LEAFY, "label": "Safe and leafy"}, "name_is_plain"),
        ("name", "leafy", {**LEAFY, "label": "The best streets"}, "name_is_plain"),
        ("name", "leafy", {**LEAFY, "label": "Students"}, "name_is_plain"),
        ("name", "pace", {**PACE, "high_end": "Rough"}, "name_is_plain"),
        ("name", "leafy", {**LEAFY, "label": "Leafy 2"}, "name_is_plain"),
        ("name", "leafy", {**LEAFY, "label": "x" * 41}, "name_is_plain"),
        ("name", "leafy", {**LEAFY, "label": "Two\nlines"}, "change_is_of_its_kind"),
        # A vibe of one way has no ends, and a scale has both.
        ("name", "leafy", {**LEAFY, "low_end": "Bare", "high_end": "Leafy"}, "vibe_is_cores"),
        ("name", "pace", {**PACE, "low_end": None}, "vibe_is_cores"),
        ("name", "pace", {"label": "Pace"}, "change_is_of_its_kind"),
        ("name", "pace", "Pace", "change_is_of_its_kind"),
        ("name", "works_warehouses", LEAFY, changes.NOT_CARRIED),
        ("name", "no_such_vibe", LEAFY, changes.NOT_CARRIED),
        ("cannot_see", "leafy", ["Whether it is safe."], "says_what_it_cannot_see"),
        ("cannot_see", "leafy", ["x" * 201], "says_what_it_cannot_see"),
        ("cannot_see", "leafy", ["One."] * 13, "says_what_it_cannot_see"),
        ("cannot_see", "leafy", "Whether a garden is kept.", "change_is_of_its_kind"),
        # A line that names the census is kept.
        ("cannot_see", "family_area", [], "says_what_it_cannot_see"),
        ("label", "air_no2", {**NO2, "short_label": "The best air"}, "name_is_plain"),
        ("label", "air_no2", {**NO2, "label": "x" * 201}, "name_is_plain"),
        ("label", "air_no2", {"label": NO2["label"]}, "change_is_of_its_kind"),
        ("label", "no_such_measure", NO2, changes.NOT_CARRIED),
    ],
)
def test_a_name_that_breaks_a_rule_is_refused_and_nothing_is_written(
    sitting: Sitting, what: str, of: str, now: Any, words: str
):
    refusal = sitting.refused(what, of, now)
    assert refusal.status == 400
    assert refusal.words == routes.BREAKS.get(words, server.WORDS[server.BAD_REQUEST])
    assert not sitting.lines


def test_a_name_is_taken_back_and_core_s_own_stands_again(sitting: Sitting):
    sitting.keep("name", "leafy", LEAFY)
    sitting.post("take-back", n=1, why="People did not call it that.")
    assert sitting.get("vibe", "leafy")["adjust"]["names"]["label"] == "Leafy"
    assert built(sitting)[TagId.LEAFY] == TAGS[TagId.LEAFY]


# A name holds no name of a place, and a label no figure of its own


@pytest.mark.parametrize(
    ("what", "of", "now"),
    [
        ("name", "leafy", {**LEAFY, "label": "Cindermoor feel"}),
        ("name", "leafy", {**LEAFY, "label": "Like quillhaven"}),
        ("name", "pace", {**PACE, "high_end": "As Dulcimer Green"}),
        ("label", "air_no2", {**NO2, "short_label": "Air of Alderwick"}),
        ("cannot_see", "leafy", ["Whether Brackenhythe has trees."]),
    ],
)
def test_a_name_that_holds_the_name_of_a_place_of_the_release_is_refused(
    sitting: Sitting, what: str, of: str, now: Any
):
    names = {area.name for area in sitting.panel.held.release.neighbourhoods}
    assert {"Cindermoor", "Dulcimer Green", "Alderwick", "Brackenhythe"} <= names
    if what == "cannot_see":
        now = [*sitting.get("vibe", of)["adjust"]["cannot_see"], *now]
    refusal = sitting.refused(what, of, now)
    assert refusal.words == routes.BREAKS["names_name_no_place"]
    assert not sitting.lines


@pytest.mark.parametrize(
    "now",
    [
        {"label": "State primary schools within 500 m of home", "short_label": "Schools"},
        {"label": "The 3 nearest state primary schools", "short_label": "Schools"},
        {"label": "State primary schools nearby", "short_label": "Schools within 800 m"},
    ],
)
def test_a_label_says_no_figure_that_the_label_of_core_does_not(
    sitting: Sitting, now: dict[str, str]
):
    refusal = sitting.refused("label", "school_primary_nearby", now)
    assert refusal.words == routes.BREAKS["name_is_plain"]
    again = {
        "label": "State primary schools no further than 800 m from home, in a straight line",
        "short_label": "Schools nearby",
    }
    assert sitting.post("preview", what="label", of="school_primary_nearby", now=again)["seen"]
