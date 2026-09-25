"""What the panel shows of a release: an area, a measure and a vibe.

Every test reads the made-up city, which is the committed synthetic release. No name
here is of a real place, and no figure is of one.
"""

from typing import Any

import pytest
from burro_core.catalogue import FEATURES, ROUGH_GUIDE, WHY_A_ROUGH_GUIDE
from burro_core.ids import FeatureId, TagId
from desk import cli
from desk.panel import look
from desk.panel.look import Held

RELEASE = cli.FIXTURE / "syn-2026-09-23-01"
AREA = "syn-n0004"


@pytest.fixture(scope="module")
def held() -> Held:
    return look.open_held(RELEASE)


def of(rows: list[dict[str, Any]], key: str, wanted: str) -> dict[str, Any]:
    return next(row for row in rows if row[key] == wanted)


# What is served


def test_the_panel_says_what_is_served(held: Held):
    served = look.served(held)
    assert served["release_id"] == "syn-2026-09-23-01"
    assert (served["synthetic"], served["preview"]) == (True, False)
    assert served["built_on"] == "2026-09-23"
    assert served["areas"] == 24 and served["measures"] == len(held.release.metrics)
    assert {vibe["id"] for vibe in served["vibes"]} == {v.tag_id for v in held.release.vibes}
    assert all(vibe["held"] <= 100 for vibe in served["vibes"])


def test_a_release_is_read_as_it_is_served(tmp_path: Any):
    # A folder that is no release is refused in words, as `burro-release check` refuses it.
    with pytest.raises(look.NotServed, match=r"manifest\.json"):
        look.open_held(tmp_path)


# An area


def test_an_area_is_found_by_its_name_by_its_borough_and_on_the_map(held: Held):
    listed = look.areas(held)["areas"]
    assert len(listed) == 24
    one = of(listed, "id", AREA)
    assert (one["name"], one["borough"], one["label"]) == (
        "Dulcimer Green",
        "Quillhaven",
        "Quillhaven 004",
    )
    assert one["state"] == "draft"
    assert [round(each, 3) for each in one["centre"]] == [0.034, 0.017]
    outlines = look.outlines(held)
    assert set(outlines["outlines"]) == {each["id"] for each in listed}
    assert outlines["outlines"][AREA]["type"] in ("Polygon", "MultiPolygon")


def test_an_area_that_is_not_in_the_release_is_not_found(held: Held):
    assert look.area(held, "syn-n9999") is None
    assert look.area(held, "../manifest.json") is None


def test_every_figure_of_an_area_says_its_unit_its_source_its_date_and_its_file(held: Held):
    shown = look.area(held, AREA)
    assert shown is not None
    figures = shown["figures"]
    air = of(figures, "measure", "air_no2")
    assert (air["value"], air["unit"]) == (19.7, "µg/m³")
    assert air["label"] == "Modelled annual mean nitrogen dioxide"
    assert air["sources"] == [
        {"id": "synthetic", "name": "Synthetic test data", "publisher": "Burro"}
    ]
    assert air["date"] == "2025"
    assert air["files"] and all(
        set(file) == {"id", "name", "edition", "source", "retrieved_on"} for file in air["files"]
    )
    assert air["state"] == "present" and air["method"].startswith("Made up for testing")
    # Every figure the release holds of the area is there, and no other.
    valued = {
        row.feature_id
        for row in held.release.features
        if row.area_id == AREA and row.value is not None
    }
    assert {row["measure"] for row in figures} == valued
    assert all(row["files"] and row["sources"] and row["date"] for row in figures)


def test_what_a_home_sells_for_is_a_figure_of_the_area_with_its_source(held: Held):
    shown = look.area(held, AREA)
    assert shown is not None
    flat = of(shown["costs"], "key", "buy.flat")
    assert (flat["median"], flat["unit"], flat["date"]) == (400000, "£", "2026-08")
    assert flat["sources"][0]["id"] == "synthetic" and flat["files"]


def test_every_vibe_of_an_area_says_its_band_and_the_share_of_each_part(held: Held):
    shown = look.area(held, AREA)
    assert shown is not None
    leafy = of(shown["vibes"], "vibe", "leafy")
    assert (leafy["label"], leafy["band"], leafy["held"]) == ("Leafy", 4, 100)
    assert [(part["measure"], part["hundredths"], part["read"]) for part in leafy["parts"]] == [
        ("land_gardens", 40, "high"),
        ("land_woodland", 30, "high"),
        ("green_cover", 30, "high"),
    ]
    assert all(part["has_a_figure"] for part in leafy["parts"])
    assert sum(part["hundredths"] for part in leafy["parts"]) == 100
    # A vibe is said as a band. The score it is ranked on is never shown.
    assert "score" not in leafy and "raw" not in leafy


def test_what_an_area_has_no_figure_for_is_listed_with_why(held: Held):
    shown = look.area(held, AREA)
    assert shown is not None
    missing = {row["measure"]: row["why"] for row in shown["missing"]}
    carried = {metric.feature_id for metric in held.release.metrics}
    # A measure that core names and the release does not carry is said to be missing.
    for feature_id in set(FEATURES) - carried:
        assert missing[feature_id] == look.WHY["not_carried"]
    assert FeatureId.CUISINE_VARIETY in missing
    assert not set(missing) & {row["measure"] for row in shown["figures"]}
    assert all(missing.values())


def test_a_vibe_that_cannot_be_placed_says_how_much_of_its_recipe_is_held(held: Held):
    unplaced = [(row.area_id, row.tag_id) for row in held.release.tags if row.band is None]
    assert unplaced, "the made-up city holds an area that a vibe cannot place"
    area_id, tag_id = unplaced[0]
    shown = look.area(held, area_id)
    assert shown is not None
    vibe = of(shown["vibes"], "vibe", tag_id)
    assert vibe["band"] is None
    assert vibe["why"].startswith(f"It rests on {vibe['held']} in 100 of its recipe")


# A measure


def test_a_measure_says_its_spread_and_the_areas_highest_and_lowest(held: Held):
    shown = look.measure(held, "air_no2")
    assert shown is not None
    about, spread = shown["measure"], shown["spread"]
    assert (about["label"], about["unit"]) == ("Modelled annual mean nitrogen dioxide", "µg/m³")
    values = sorted(
        row.value
        for row in held.release.features
        if row.feature_id == "air_no2" and row.value is not None
    )
    assert (spread["least"], spread["most"]) == (values[0], values[-1])
    assert spread["least"] <= spread["lower_quartile"] <= spread["median"]
    assert spread["median"] <= spread["upper_quartile"] <= spread["most"]
    assert spread["with_a_figure"] == len(values)
    assert sum(one["areas"] for one in spread["bins"]) == len(values)
    assert [row["value"] for row in shown["highest"]] == values[::-1][:10]
    assert [row["value"] for row in shown["lowest"]] == values[:10]
    assert all({"id", "name", "borough", "value"} <= set(row) for row in shown["highest"])


def test_a_measure_lists_the_areas_with_no_figure_and_why(held: Held):
    lacking = next(
        row for row in held.release.features if row.value is None and row.area_id.startswith("syn")
    )
    shown = look.measure(held, lacking.feature_id)
    assert shown is not None
    listed = {row["id"]: row["why"] for row in shown["missing"]}
    assert listed.get(lacking.area_id)
    assert shown["spread"]["areas"] == 24
    assert shown["spread"]["with_a_figure"] + len(listed) == 24


def test_a_measure_the_release_does_not_carry_is_not_found(held: Held):
    assert look.measure(held, "cuisine_variety") is None
    assert look.measure(held, "no_such_measure") is None


def test_a_figure_far_from_those_of_the_areas_beside_it_stands_out():
    beside = {"a": ("b", "c", "d"), "b": ("a",), "c": ("a",), "d": ("a",), "e": ()}
    percentiles = {"a": 95.0, "b": 10.0, "c": 20.0, "d": 30.0, "e": 50.0}
    values = {"a": 9.0, "b": 1.0, "c": 2.0, "d": 3.0, "e": 5.0}
    found = look.stands_out(values, percentiles, beside)
    assert found == [{"id": "a", "why": "far_from_the_areas_beside_it", "beside": 3}]


def test_a_figure_at_nought_where_its_neighbours_are_not_stands_out():
    beside = {"a": ("b", "c"), "b": ("a", "c"), "c": ("a", "b")}
    values = {"a": 0.0, "b": 4.0, "c": 5.0}
    percentiles = {"a": 16.7, "b": 50.0, "c": 83.3}
    found = look.stands_out(values, percentiles, beside)
    assert found == [{"id": "a", "why": "nought_where_the_areas_beside_it_are_not", "beside": 2}]


def test_an_area_with_too_few_neighbours_that_have_a_figure_never_stands_out():
    beside = {"a": ("b",), "b": ("a",)}
    assert look.stands_out({"a": 9.0, "b": None}, {"a": 100.0, "b": None}, beside) == []
    assert look.stands_out({"a": 0.0, "b": 9.0}, {"a": 25.0, "b": 75.0}, beside) == []


# A vibe


def test_a_vibe_says_its_recipe_its_bands_and_the_areas_highest_and_lowest(held: Held):
    shown = look.vibe(held, "leafy")
    assert shown is not None
    about = shown["vibe"]
    assert (about["label"], about["shape"], about["low_end"]) == ("Leafy", "one_way", None)
    assert about["cannot_see"][0] == "One street or one home. An area is many streets."
    assert [(part["measure"], part["hundredths"]) for part in about["recipe"]] == [
        ("land_gardens", 40),
        ("land_woodland", 30),
        ("green_cover", 30),
    ]
    assert (about["held"], about["needed"], about["placed"]) == (100, 60, True)
    bands = shown["bands"]
    assert set(bands) == {area.area_id for area in held.release.neighbourhoods}
    assert set(bands.values()) <= {1, 2, 3, 4, 5, None}
    assert sum(shown["counts"].values()) == 24
    assert shown["highest"][0]["band"] == 5 and shown["lowest"][0]["band"] == 1
    assert all({"id", "name", "borough", "band"} == set(row) for row in shown["highest"])


def test_a_vibe_says_how_closely_it_follows_homes_per_hectare_and_the_distance_from_the_centre(
    held: Held,
):
    shown = look.vibe(held, "homes")
    assert shown is not None
    follows = {one["what"]: one for one in shown["follows"]}
    assert set(follows) == {"homes_density", "distance_from_the_centre"}
    # Houses or flats holds homes per hectare at 35 in 100, so it follows it closely.
    assert follows["homes_density"]["rank_correlation"] > 0.5
    assert all(-1 <= one["rank_correlation"] <= 1 for one in follows.values())
    placed = sum(row.tag_id == "homes" and row.raw is not None for row in held.release.tags)
    assert follows["distance_from_the_centre"]["areas"] == placed
    assert 0 < follows["homes_density"]["areas"] <= placed


def test_a_rank_correlation_is_one_where_two_orders_are_one_order():
    assert look.rank_correlation([1, 2, 3, 4], [10, 20, 30, 40]) == 1.0
    assert look.rank_correlation([1, 2, 3, 4], [40, 30, 20, 10]) == -1.0
    assert look.rank_correlation([1, 2, 3, 4], [5, 5, 5, 5]) is None
    assert look.rank_correlation([1], [1]) is None


def test_a_band_that_rests_on_little_of_its_recipe_stands_out(held: Held):
    shown = look.vibe(held, "parks_close_by")
    assert shown is not None
    for row in shown["rests_on_little"]:
        placed = held.release.tag(row["id"], TagId.PARKS_CLOSE_BY)
        assert placed is not None and placed.band is not None
        assert row["held"] == round(placed.coverage * 100) < look.LITTLE
    every = [
        row
        for row in held.release.tags
        if row.tag_id == "parks_close_by"
        and row.band is not None
        and round(row.coverage * 100) < look.LITTLE
    ]
    assert len(shown["rests_on_little"]) == len(every)


def test_a_vibe_that_is_a_rough_guide_says_so_wherever_the_panel_names_it(held: Held):
    """Its label and the sentence that says why are core's, as every client is served them."""
    said = {
        "label": "Rough guide",
        "why": (
            "Of the areas it puts highest, about half read as villages to people, and it "
            "takes some busy main roads and some grand inner streets for villages."
        ),
    }
    assert said == {"label": ROUGH_GUIDE, "why": WHY_A_ROUGH_GUIDE[TagId.VILLAGE_FEEL]}
    # Where every vibe is listed, in the audit of an area, and on the screen of the vibe.
    listed = {vibe["id"]: vibe["rough"] for vibe in look.served(held)["vibes"]}
    found = look.area(held, AREA)
    assert found is not None
    of_the_area = {row["vibe"]: row["rough"] for row in found["vibes"]}
    for rows in (listed, of_the_area):
        assert rows.pop("village_feel") == said
        assert len(rows) == 13 and set(rows.values()) == {None}
    for tag_id, told in (("village_feel", said), ("leafy", None)):
        one = look.vibe(held, tag_id)
        assert one is not None and one["vibe"]["rough"] == told


def test_a_vibe_the_release_does_not_carry_is_not_found(held: Held):
    assert look.vibe(held, "works_warehouses") is None
    assert look.vibe(held, "no_such_vibe") is None


# What is never shown


def test_the_panel_shows_no_census_table_and_no_income(held: Held):
    import ast
    from pathlib import Path

    for path in sorted(Path(look.__file__).parent.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        named = {
            (node.module or "") if isinstance(node, ast.ImportFrom) else alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import | ast.ImportFrom)
            for alias in node.names
        }
        assert not {name for name in named if name.endswith((".census", ".income"))}, path.name
