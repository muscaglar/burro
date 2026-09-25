"""The table of tiers with what a person decided at the panel laid over it.

Every file here is made up, as in `test_brands_nearby.py`, whose town this is. No shop
here exists. The name of a chain is the name a chain of the table bears, written as the
real file writes it, so that the table is read as a build reads it.
"""

from pathlib import Path
from typing import Any

import pytest
from burro_core.ids import FeatureId
from burro_pipeline import changes
from burro_pipeline.cells import spine
from burro_pipeline.changes import Change, ChangesError
from burro_pipeline.derive import brand_table, brands_nearby
from burro_pipeline.derive.brand_table import Kind, Tier, the_table
from burro_pipeline.derive.brands_nearby import MIX, Brands

from .culture_support import ONE, Q1, Q3, R1, TWO, beside, inputs_of
from .test_brands_nearby import (
    GROCERY,
    IN_THE_TOWN,
    OFF_THE_TABLE,
    RESTAURANT,
    WITH_THE_BRAND,
    figure,
    shop,
)


def row_of(key: str, **changed: Any) -> dict[str, Any]:
    """A row of the table as a line of the file of changes holds it."""
    return {**changes.row_of(the_table().by_key[key]), **changed}


def a_line(n: int, of: str, was: object, now: object) -> Change:
    return Change(
        n=n,
        on="2026-09-25",
        by="r1",
        what=changes.What.BRAND,
        of=of,
        was=was,
        now=now,
        why="A made-up reason.",
        takes_back=None,
    )


def moved(n: int, key: str, tier: str) -> Change:
    return a_line(n, key, row_of(key), row_of(key, tier=tier))


GILDCREST = {
    "name": "Gildcrest",
    "kind": "coffee",
    "tier": "premium",
    "wikidata": [],
    "spellings": ["Gildcrest"],
}


def named_as(name: str) -> dict[str, Any]:
    """A chain that is added under a name, which is how the file of places writes it."""
    return {**GILDCREST, "name": name, "spellings": [name]}


def built(folder: Path, *lines: Change) -> Brands:
    inputs = inputs_of(folder, IN_THE_TOWN, None, wanted=WITH_THE_BRAND)
    with brand_table.using(changes.table_with(the_table(), lines)):
        return brands_nearby.build(inputs, spine.build(inputs))


def refused(*lines: Change) -> tuple[int, str]:
    with pytest.raises(ChangesError) as caught:
        changes.table_with(the_table(), lines)
    return caught.value.line, caught.value.rule


def test_with_no_change_the_table_is_the_table_of_the_file():
    assert changes.table_with(the_table(), ()) is the_table()
    flag = Change(
        n=1,
        on="2026-09-25",
        by="r1",
        what=changes.What.FLAG,
        of="figure/syn-n0004/brand_mix",
        was=None,
        now=None,
        why="A made-up reason.",
        takes_back=None,
    )
    assert changes.table_with(the_table(), (flag,)) is the_table()


def test_a_chain_is_moved_from_one_tier_to_another(tmp_path: Path):
    before = built(tmp_path / "before")
    after = built(tmp_path / "after", moved(1, "lidl", "premium"))
    assert after.table.by_key["lidl"].tier is Tier.PREMIUM
    assert after.table.by_key["lidl"].on_the_founders_table is True
    # The grocer on the centre was a value one, and is a premium one.
    assert figure(after, FeatureId.GROCER_PREMIUM_NEARBY) > figure(
        before, FeatureId.GROCER_PREMIUM_NEARBY
    )
    assert figure(after, FeatureId.GROCER_VALUE_NEARBY) < figure(
        before, FeatureId.GROCER_VALUE_NEARBY
    )
    assert figure(after, MIX) > figure(before, MIX)
    # Every other row of the table is as it was, in the order of the table.
    assert [chain.key for chain in after.table.chains] == [c.key for c in the_table().chains]
    others = [chain for chain in after.table.chains if chain.key != "lidl"]
    assert others == [chain for chain in the_table().chains if chain.key != "lidl"]


def test_a_chain_is_added_and_counted_in_its_tier_though_core_names_no_measure_of_it(
    tmp_path: Path,
):
    before = built(tmp_path / "before")
    after = built(tmp_path / "after", a_line(1, "gildcrest", None, GILDCREST))
    added = after.table.by_key["gildcrest"]
    assert (added.kind, added.tier, added.spellings) == (Kind.COFFEE, Tier.PREMIUM, ("Gildcrest",))
    assert after.table.chains[-1] == added, "a chain that is added is the last row"
    assert figure(after, FeatureId.COFFEE_PREMIUM_NEARBY, TWO) > 0
    assert before.worked[FeatureId.COFFEE_PREMIUM_NEARBY][TWO].value in (None, 0.0)
    assert "brand_gildcrest" not in FeatureId
    assert "Gildcrest" in after.one(FeatureId.COFFEE_PREMIUM_NEARBY).metric.definition


def test_a_chain_is_taken_out_and_its_places_are_of_no_tier(tmp_path: Path):
    before = built(tmp_path / "before")
    after = built(tmp_path / "after", a_line(1, "waitrose", row_of("waitrose"), None))
    assert "waitrose" not in after.table.by_key
    assert figure(before, FeatureId.GROCER_PREMIUM_NEARBY) > 0
    assert figure(after, FeatureId.GROCER_PREMIUM_NEARBY) == 0
    # Core still names the measure of the chain, and no area has a figure for it.
    assert all(worked.value is None for worked in after.worked[FeatureId.BRAND_WAITROSE].values())
    assert "Waitrose" not in after.one(FeatureId.GROCER_PREMIUM_NEARBY).metric.definition
    assert figure(before, FeatureId.BRAND_WAITROSE, ONE) > 0


def test_a_change_that_was_taken_back_changes_nothing():
    back = Change(
        n=2,
        on="2026-09-25",
        by="r1",
        what=changes.What.TAKE_BACK,
        of="lidl",
        was=None,
        now=None,
        why="A made-up reason.",
        takes_back=1,
    )
    assert changes.table_with(the_table(), (moved(1, "lidl", "premium"), back)) is the_table()


def test_a_second_change_of_a_chain_is_made_of_what_the_first_made():
    first = moved(1, "lidl", "mid")
    second = a_line(2, "lidl", row_of("lidl", tier="mid"), row_of("lidl", tier="premium"))
    assert changes.table_with(the_table(), (first, second)).by_key["lidl"].tier is Tier.PREMIUM


@pytest.mark.parametrize(
    ("line", "rule"),
    [
        # It was made of a row that is not the table's, and that no line made.
        (a_line(1, "lidl", row_of("lidl", tier="mid"), row_of("lidl", tier="premium")), "stale"),
        (a_line(1, "gildcrest", GILDCREST, {**GILDCREST, "tier": "mid"}), "stale"),
        (a_line(1, "lidl", None, row_of("lidl")), "stale"),
        (a_line(1, "lidl", row_of("lidl"), row_of("lidl", tier="luxury")), "row"),
        # A chain of the table is moved by its tier alone: nothing else of its row changes.
        (a_line(1, "lidl", row_of("lidl"), row_of("lidl", kind="gym")), "moved"),
        (a_line(1, "lidl", row_of("lidl"), row_of("lidl", name="Gildcrest")), "moved"),
        (a_line(1, "lidl", row_of("lidl"), row_of("lidl", wikidata=[])), "moved"),
        (a_line(1, "lidl", row_of("lidl"), row_of("lidl", spellings=["Lidl", "Aldi"])), "moved"),
        # A chain that is added is named as the file of places writes it.
        (a_line(1, "gildcrest", None, {**GILDCREST, "name": "Gild Crest"}), "named"),
        (a_line(1, "gildcrest", None, {**GILDCREST, "spellings": []}), "named"),
        (a_line(1, "gildcrest", None, {**GILDCREST, "name": "Ada Quillfeather"}), "named"),
        # Two rows may not claim one place.
        (a_line(1, "gildcrest", None, named_as("Starbucks")), "row"),
        (a_line(1, "gildcrest", None, {**GILDCREST, "wikidata": ["Q151954"]}), "row"),
        (a_line(1, "gildcrest", None, {**GILDCREST, "kind": "bank"}), "row"),
        (a_line(1, "gildcrest", None, {**GILDCREST, "wikidata": ["151954"]}), "row"),
        (a_line(1, "gildcrest", None, named_as(" Gildcrest")), "name"),
        # A name says nothing of who lives somewhere.
        (a_line(1, "gildcrest", None, named_as("Students")), "name"),
        (a_line(1, "gildcrest", None, named_as("x" * 41)), "name"),
        # A chain that is on the table is not added again.
        (a_line(1, "lidl", None, row_of("lidl")), "stale"),
    ],
)
def test_a_change_of_the_table_that_cannot_be_built_is_refused_by_its_line(line: Change, rule: str):
    rules = {
        "stale": changes.STALE,
        "row": "row_is_a_row_of_the_table",
        "name": "name_is_plain",
        "moved": "chain_moves_by_its_tier_alone",
        "named": "chain_is_named_as_it_is_written",
    }
    assert refused(line) == (1, rules[rule])


def test_the_table_that_is_used_is_put_back_when_the_build_is_over():
    changed = changes.table_with(the_table(), (moved(1, "lidl", "premium"),))
    with brand_table.using(changed):
        assert brand_table.the_table() is changed
        with pytest.raises(RuntimeError), brand_table.using(changed):
            pass
    assert brand_table.the_table().by_key["lidl"].tier is Tier.VALUE
    with pytest.raises(ZeroDivisionError), brand_table.using(changed):
        raise ZeroDivisionError
    assert brand_table.the_table().by_key["lidl"].tier is Tier.VALUE


# Whether a name is that of a chain


def seen(made: Brands, line: Change) -> bool:
    return changes.seen_to_be_a_chain(line, made.held.written, made.held.counted)


def places_of(
    *at: tuple[float, float],
    brand: tuple[str, str | None] = OFF_THE_TABLE,
    path: tuple[str, ...] = RESTAURANT,
) -> Any:
    return (*IN_THE_TOWN, *(shop(where, path, brand) for where in at))


def with_places(folder: Path, places: Any, *lines: Change) -> Brands:
    inputs = inputs_of(folder, places, None, wanted=WITH_THE_BRAND)
    with brand_table.using(changes.table_with(the_table(), lines)):
        return brands_nearby.build(inputs, spine.build(inputs))


def test_a_name_the_file_gives_to_one_place_is_not_seen_to_be_a_chain(tmp_path: Path):
    # The town holds one place that bears the brand: a shop, and no chain.
    line = a_line(1, "gildcrest", None, GILDCREST)
    made = with_places(tmp_path, IN_THE_TOWN, line)
    assert made.held.counted["gildcrest"] == 1
    assert seen(made, line) is False


def test_a_name_the_file_gives_to_two_places_that_stand_apart_is_seen_to_be_a_chain(
    tmp_path: Path,
):
    line = a_line(1, "gildcrest", None, GILDCREST)
    made = with_places(tmp_path, places_of(beside(Q1, 0, 200)), line)
    assert made.held.counted["gildcrest"] == 2
    assert seen(made, line) is True


def test_two_records_of_one_shop_are_one_place_and_no_chain(tmp_path: Path):
    line = a_line(1, "gildcrest", None, GILDCREST)
    made = with_places(tmp_path, places_of(beside(R1, 0, 105)), line)
    assert made.held.written["gildcrest"] == {"Gildcrest": 2}
    assert made.held.counted["gildcrest"] == 1
    assert seen(made, line) is False


def test_a_name_the_file_gives_to_no_place_is_not_seen_to_be_a_chain(tmp_path: Path):
    line = a_line(1, "ada", None, named_as("Ada Quillfeather"))
    made = with_places(tmp_path, IN_THE_TOWN, line)
    assert made.held.counted["ada"] == 0
    assert seen(made, line) is False
    # Nor is it where nothing was read of the file at all.
    assert changes.seen_to_be_a_chain(line, {}, {}) is False


def test_a_name_is_not_seen_to_be_a_chain_by_the_places_of_another_name(tmp_path: Path):
    # The row finds the places of a chain by the id an encyclopaedia gives the chain, and
    # says a name of its own choosing. The file writes that name for no place.
    lidl = ("Lidl", "Q151954")
    places = places_of(beside(Q1, 0, 200), beside(Q3, 0, 200), brand=lidl, path=GROCERY)
    gone = a_line(1, "lidl", row_of("lidl"), None)
    line = a_line(
        2, "ada", None, {**named_as("Ada Quillfeather"), "kind": "grocer", "wikidata": ["Q151954"]}
    )
    made = with_places(tmp_path, places, gone, line)
    assert made.held.counted["ada"] >= 2, "the places of the chain are counted as the row's"
    assert seen(made, line) is False, "and the name is that of none of them"


def test_only_a_chain_that_a_line_adds_is_asked_to_be_seen(tmp_path: Path):
    table = the_table()
    assert changes.added(table, (moved(1, "lidl", "premium"),)) == ()
    assert changes.added(table, (a_line(1, "waitrose", row_of("waitrose"), None),)) == ()
    line = a_line(1, "gildcrest", None, GILDCREST)
    assert changes.added(table, (line,)) == (line,)
    back = Change(
        n=2,
        on="2026-09-25",
        by="r1",
        what=changes.What.TAKE_BACK,
        of="gildcrest",
        was=None,
        now=None,
        why="A made-up reason.",
        takes_back=1,
    )
    assert changes.added(table, (line, back)) == ()
