"""The guide to adding a city, held to the code, the registry and the receipts it speaks of.

A guide goes stale without a sound. Each test here reads docs/adding-a-city.md beside what
it describes, and fails when the two part: a place where London was written that is no
longer as the guide says, a source that gained a receipt and has no row, a recipe of core
that no longer comes to what the guide says a second city holds of it.
"""

import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "packages" / "pipeline" / "src" / "burro_pipeline"
ADDING = (ROOT / "docs" / "adding-a-city.md").read_text(encoding="utf-8")
# A row of a table of places: where, what is written there, and what it does.
PLACE = re.compile(r"^\| `(?P<path>[^`:]+):(?P<line>\d+)` \| `(?P<words>.+?)` \| ", re.MULTILINE)
REACHES = (
    "London alone",
    "England",
    "England and Wales",
    "Great Britain",
    "United Kingdom",
    "The world",
    "Not said in the registry",
)


def section(guide: str, heading: str) -> str:
    """What stands under a heading of a guide, up to the next heading of its kind."""
    marks = "#" * (len(heading) - len(heading.lstrip("#")))
    after = guide.split(f"\n{heading}", 1)[1]
    return re.split(rf"\n{marks} ", after, maxsplit=1)[0]


def cells(row: str) -> list[str]:
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", row.strip().strip("|"))]


# Adding a city: the places


def test_every_place_the_guide_names_holds_the_words_it_gives():
    places = [
        (found["path"], found["words"].replace("\\|", "|"))
        for found in PLACE.finditer(section(ADDING, "## 8. The places, one by one"))
    ]
    assert len(places) > 150
    gone: list[str] = []
    for path, words in places:
        file = next((at for at in (PIPELINE / path, ROOT / path) if at.is_file()), None)
        if file is None or words not in file.read_text(encoding="utf-8"):
            gone.append(f"{path}: {words}")
    assert gone == [], "a place the guide names is no longer as it says"


def test_the_places_of_each_kind_come_to_what_the_guide_counts():
    counted = {
        int(found[1]): int(found[2])
        for found in re.finditer(
            r"^\| (\d+)\. [^|]+ \| (\d+) \|", section(ADDING, "## 2. What does"), re.MULTILINE
        )
    }
    assert sorted(counted) == list(range(1, 11))
    assert sum(counted.values()) == 250
    assert f"| {sum(counted.values())} places, of ten kinds |" in ADDING
    listed = section(ADDING, "## 8. The places, one by one")
    for kind, places in counted.items():
        # What stands under the heading, after the line of the heading itself.
        under = section(listed, f"### Kind {kind}:").split("\n", 1)[1].strip()
        if places == 0:
            assert under.startswith("No place.")
            continue
        assert under.startswith(f"{places} places."), kind
        rows = [cells(row) for row in under.splitlines() if row.startswith("| `")]
        # A row stands for one place, but for the one that says how many it stands for.
        stood_for = sum(33 if "33 files of the food register" in row[2] else 1 for row in rows)
        assert stood_for == places, kind


# Adding a city: the sources


def sources() -> dict[str, list[str]]:
    rows = section(ADDING, "## 9. The sources, one row for each that holds a receipt")
    found = [cells(row) for row in rows.splitlines() if row.startswith("| `")]
    return {row[0].strip("`"): row[1:] for row in found}


def test_every_source_that_holds_a_receipt_has_its_row_and_no_other_has():
    held = {path.name for path in (ROOT / "data" / "receipts").iterdir() if path.is_dir()}
    assert set(sources()) == held
    assert len(held) == 43 or "43" not in section(ADDING, "## 0. In short")


def test_the_reach_of_the_sources_comes_to_what_the_guide_counts():
    def reach(said: str) -> str:
        found = [one for one in REACHES if said.startswith(one)]
        assert found, said
        return max(found, key=len)

    counted = Counter(reach(row[0]) for row in sources().values())
    assert counted == {
        "London alone": 7,
        "England": 7,
        "England and Wales": 13,
        "Great Britain": 7,
        "United Kingdom": 4,
        "The world": 1,
        "Not said in the registry": 4,
    }
    said = (
        "7 London alone, 7 England, 13 England and Wales, 7 Great Britain, 4 the United "
        "Kingdom, 1 the world. Of 4 the repository does not say"
    )
    assert said in section(ADDING, "## 0. In short")


def test_every_substitute_the_guide_names_is_in_the_registry():
    """The guide names no dataset the registry does not hold."""
    from burro_pipeline.registry import load

    registered = {source.id for source in load(ROOT / "registry" / "sources", enforce=False)}
    named = set(re.findall(r"`([a-z0-9]+(?:-[a-z0-9]+)+)`", section(ADDING, "## 3. The sources")))
    named |= {
        name
        for row in sources().values()
        for name in re.findall(r"`([a-z0-9]+(?:-[a-z0-9]+)+)`", row[2])
    }
    assert named and named <= registered, sorted(named - registered)


# Adding a city: the measures and the vibes


def test_the_measures_of_day_one_come_to_the_measures_london_carries():
    # The first table of the section: a row says how many measures, and then which.
    first = section(ADDING, "## 4.").split("| Vibe |", 1)[0]
    counted = [int(found) for found in re.findall(r"^\| [A-Z][^|]+ \| (\d+) \| ", first, re.M)]
    assert counted == [90, 4, 4, 2] and sum(counted) == 100
    assert "90 of London's 100 measures, and 9 of its 14 vibes" in ADDING


def test_the_vibes_of_day_one_are_held_to_cores_recipes():
    """A vibe places an area on day one where 60 in 100 of its recipe is of a measure the
    guide says a second city has, and no rule of core holds it off."""
    from burro_core.catalogue import PLACED_ONLY_WITH, TAG_MIN_COVERAGE_HUNDREDTHS, tags_of
    from burro_core.ids import GrittyVariant

    waits = {"highstreet_access", "highstreet_conserved", "bus_routes_nearby", "rail_proximity"}
    never = {"underground_proximity", "overground_proximity"}
    if_given = {
        "venue_food_drink",
        "venue_food_drink_per_homes",
        "incident_criminal_damage",
        "incident_antisocial",
    }
    # What no build of London carries, so no build of a second city would.
    not_built = {"centre_small", "centre_compact", "park_facilities", "cuisine_variety"}
    held: dict[str, tuple[int, int]] = {}
    for vibe in tags_of(GrittyVariant.B):
        parts = {term.feature_id.value: term.hundredths for term in vibe.terms}
        sure = sum(n for part, n in parts.items() if part not in waits | never | not_built)
        held[vibe.label] = (
            sure - sum(n for part, n in parts.items() if part in if_given),
            sure,
        )
    assert TAG_MIN_COVERAGE_HUNDREDTHS == 60
    # No vibe is held off by name. Village feel was, until 2026-09-25.
    assert dict(PLACED_ONLY_WITH) == {}
    assert held == {
        "Leafy": (100, 100),
        "Village feel": (55, 55),
        "Going out": (50, 80),
        "Quiet streets": (100, 100),
        "Age of buildings": (100, 100),
        "Everyday on foot": (75, 75),
        "Parks close by": (70, 70),
        "Houses or flats": (100, 100),
        "Food and drink": (40, 80),
        "Family amenities": (100, 100),
        "Well connected": (0, 0),
        "Gritty": (55, 100),
        "Family area": (100, 100),
        "Young professionals": (80, 100),
    }
    table = section(ADDING, "## 4.")
    for label in held:
        assert label in table, label
