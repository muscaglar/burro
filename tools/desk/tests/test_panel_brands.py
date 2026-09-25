"""The table of brands at the panel: a chain is moved to another tier, added or taken out.

The table names chains of shops, as the founder's own table does, and no place. Every
test reads the made-up city and asks the panel with no port. Every reason is made up.
"""

import shutil
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from burro_pipeline import changes
from burro_pipeline.derive.brand_table import Tier, the_table
from desk import cli, fill, records, server
from desk.panel import kept, routes

START = datetime(2026, 10, 6, 21, 14, 9, tzinfo=UTC)
RELEASE = cli.FIXTURE / "syn-2026-09-23-01"
WHY = "It charges what the premium grocers charge."
GILDCREST = {
    "name": "Gildcrest",
    "kind": "coffee",
    "tier": "premium",
    "wikidata": [],
    "spellings": ["Gildcrest"],
}


@pytest.fixture(scope="module")
def filled(tmp_path_factory: pytest.TempPathFactory) -> Path:
    data = tmp_path_factory.mktemp("brands") / "desk-synthetic"
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

    def get(self, route: str) -> dict[str, Any]:
        return self.panel.answer(self.desk, route, None, None)

    def post(self, route: str, /, **sent: Any) -> dict[str, Any]:
        return self.panel.answer(self.desk, route, None, sent)

    def keep(self, of: str, now: Any, why: str = WHY) -> dict[str, Any]:
        seen = self.post("preview", what="brand", of=of, now=now)["seen"]
        return self.post("keep", what="brand", of=of, now=now, why=why, seen=seen)

    def refused(self, route: str, /, **sent: Any) -> server.Refused:
        with pytest.raises(server.Refused) as caught:
            self.post(route, **sent)
        return caught.value

    def chain(self, key: str) -> dict[str, Any]:
        return next(one for one in self.get("brands")["chains"] if one["key"] == key)

    @property
    def lines(self) -> tuple[changes.Change, ...]:
        return kept.read(self.desk.data, self.desk.reviewer)


Opener = Callable[..., Sitting]


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


def row_of(key: str, **changed: Any) -> dict[str, Any]:
    return {**changes.row_of(the_table().by_key[key]), **changed}


def test_the_table_is_shown_as_the_file_holds_it_by_kind_and_tier(sitting: Sitting):
    found = sitting.get("brands")
    assert [kind["id"] for kind in found["kinds"]] == ["grocer", "gym", "coffee"]
    assert [tier["id"] for tier in found["tiers"]] == ["premium", "mid", "value"]
    assert [one["key"] for one in found["chains"]] == [chain.key for chain in the_table().chains]
    lidl = sitting.chain("lidl")
    assert (lidl["name"], lidl["kind"], lidl["tier"]) == ("Lidl", "grocer", "value")
    assert (lidl["named_by_core"], lidl["changed"], lidl["on_the_founders_table"]) == (
        True,
        False,
        True,
    )
    assert found["taken_out"] == [] and found["read_in"] == the_table().read_in
    # It names chains of shops, and no place and no figure of one.
    assert set(lidl) == {
        *("key", "name", "kind", "tier", "wikidata", "spellings"),
        *("on_the_founders_table", "named_by_core", "changed"),
    }


def test_a_chain_is_moved_to_another_tier_and_the_panel_says_which_measures_a_build_works_out(
    sitting: Sitting,
):
    looked = sitting.post("preview", what="brand", of="lidl", now=row_of("lidl", tier="premium"))
    assert (looked["was"], looked["now"]) == (row_of("lidl"), row_of("lidl", tier="premium"))
    assert looked["worked_out_again"] == [
        "Straight-line distance to the nearest Lidl within 2,000 m of home",
        "Share of the chain grocers, gyms and coffee places within 800 m of home that are "
        "premium, with a mid-range one counted as half, by Burro's table of tiers",
        "Straight-line distance to the nearest premium grocer within 2,000 m of home, by "
        "Burro's table of tiers",
        "Premium grocers within 800 m of home, in a straight line, by Burro's table of tiers",
        "Straight-line distance to the nearest value grocer within 2,000 m of home, by "
        "Burro's table of tiers",
        "Value grocers within 800 m of home, in a straight line, by Burro's table of tiers",
    ]
    answer = sitting.keep("lidl", row_of("lidl", tier="premium"))
    assert answer["line"]["n"] == 1 and answer["line"]["what"] == "brand"
    assert (sitting.chain("lidl")["tier"], sitting.chain("lidl")["changed"]) == ("premium", True)
    # A build reads the line, and lays it over the table.
    assert changes.table_with(the_table(), sitting.lines).by_key["lidl"].tier is Tier.PREMIUM
    assert [(one["what"], one["of"]) for one in sitting.get("home")["changed"]] == [
        ("brand", "lidl")
    ]


def test_a_chain_is_added_and_the_panel_says_that_core_names_no_measure_of_it(
    sitting: Sitting,
):
    sitting.keep("gildcrest", GILDCREST, "It is on every high street of the made-up city.")
    added = sitting.chain("gildcrest")
    assert (added["name"], added["tier"], added["named_by_core"], added["changed"]) == (
        "Gildcrest",
        "premium",
        False,
        True,
    )
    assert sitting.get("brands")["chains"][-1]["key"] == "gildcrest"
    assert [(line.was, line.now) for line in sitting.lines] == [(None, GILDCREST)]


def test_a_chain_is_taken_out_and_can_be_put_back(sitting: Sitting):
    sitting.keep("waitrose", None, "The file of places holds too few of them.")
    found = sitting.get("brands")
    assert "waitrose" not in [one["key"] for one in found["chains"]]
    assert [one["key"] for one in found["taken_out"]] == ["waitrose"]
    sitting.post("take-back", n=1, why="It holds enough after all.")
    assert sitting.chain("waitrose")["changed"] is False
    assert sitting.get("brands")["taken_out"] == []
    assert changes.table_with(the_table(), sitting.lines) is the_table()


def test_what_the_table_moves_is_said_to_be_known_only_once_it_is_built(sitting: Sitting):
    assert sitting.get("brands")["says"] == routes.ONLY_ONCE_BUILT
    looked = sitting.post("preview", what="brand", of="lidl", now=row_of("lidl", tier="mid"))
    assert "bands" not in looked and "searches" not in looked


@pytest.mark.parametrize(
    ("of", "now", "words"),
    [
        ("lidl", row_of("lidl", tier="luxury"), "row_is_a_row_of_the_table"),
        # A chain of the table is moved by its tier alone.
        ("lidl", row_of("lidl", kind="gym"), "chain_moves_by_its_tier_alone"),
        ("lidl", row_of("lidl", name="Ada Quillfeather"), "chain_moves_by_its_tier_alone"),
        ("lidl", row_of("lidl", spellings=["Lidl", "Aldi"]), "chain_moves_by_its_tier_alone"),
        # A chain that is added is named as the file of places writes it.
        ("gildcrest", {**GILDCREST, "name": "Ada Quillfeather"}, "chain_is_named_as_it_is_written"),
        ("gildcrest", {**GILDCREST, "spellings": ["Starbucks"]}, "chain_is_named_as_it_is_written"),
        (
            "gildcrest",
            {**GILDCREST, "name": "Starbucks", "spellings": ["Starbucks"]},
            "row_is_a_row_of_the_table",
        ),
        (
            "gildcrest",
            {**GILDCREST, "name": "Students", "spellings": ["Students"]},
            "name_is_plain",
        ),
        ("gildcrest", {**GILDCREST, "name": ""}, "change_is_of_its_kind"),
        ("gildcrest", {**GILDCREST, "price": 4.5}, "change_is_of_its_kind"),
        ("gildcrest", {"name": "Gildcrest"}, "change_is_of_its_kind"),
        ("gildcrest", None, "change_is_of_its_kind"),
        ("Gild Crest", GILDCREST, "change_names_what_it_changes"),
        ("../lidl", row_of("lidl"), "change_names_what_it_changes"),
    ],
)
def test_a_row_that_is_no_row_of_the_table_is_refused_and_nothing_is_written(
    sitting: Sitting, of: str, now: Any, words: str
):
    refusal = sitting.refused("preview", what="brand", of=of, now=now)
    assert refusal.status == 400
    assert refusal.words == routes.BREAKS.get(words, server.WORDS[server.BAD_REQUEST])
    assert not sitting.lines


def test_the_panel_says_that_a_build_adds_a_chain_only_where_the_file_of_places_shows_it(
    sitting: Sitting,
):
    looked = sitting.post("preview", what="brand", of="gildcrest", now=GILDCREST)
    assert looked["needs"] == routes.A_CHAIN_IS_SEEN
    moved = sitting.post("preview", what="brand", of="lidl", now=row_of("lidl", tier="mid"))
    assert "needs" not in moved
