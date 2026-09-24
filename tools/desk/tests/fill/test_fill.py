"""Filling every queue: what is written, what is said, and what is refused.

Every test runs offline. A draft that names real sources is the made-up city under other
names: it shows that London takes the same path, and it says nothing of any real place.
"""

import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any

import pytest
from desk import fill
from desk.fill import draft, gate
from desk.fill.draft import Draft
from desk.fill.layers import Unfit

from .conftest import REGISTRY, RELEASE, Filled, fill_made_up

# In the order of the work.
QUEUES = (
    "rules",
    "know",
    "kinds",
    "commons",
    "figures",
    "sentences",
    "names",
    "borders",
    "whole",
    "ratings",
    "articles",
    "claims",
)
ITEM = {"id", "rev", "group", "title", "lines", "text", "map", "picks", "flags", "fill", "preset"}
HEADER = {"desk", "queue", "question", "synthetic", "made_on", "made_from", "count"}
DRAWS_A_MAP = ("names", "borders", "whole", "ratings", "know")


def files_of(folder: Path) -> dict[str, str]:
    return {
        str(path.relative_to(folder)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(folder.rglob("*"))
        if path.is_file()
    }


# What is written


def test_every_queue_of_the_design_is_filled_in_the_order_of_the_design(made_up: Filled):
    assert tuple(queue.queue for queue in made_up.report.queues) == QUEUES == tuple(draft.QUEUES)
    assert sorted(path.stem for path in (made_up.data / "items").iterdir()) == sorted(QUEUES)
    assert all(queue.items > 0 and not queue.lacks for queue in made_up.report.queues)
    assert made_up.report.items == 512 and made_up.report.synthetic is True


def test_the_same_release_gives_the_same_files_byte_for_byte(made_up: Filled, tmp_path: Path):
    again = fill_made_up(tmp_path)
    assert files_of(again.data) == files_of(made_up.data)
    assert again.report == made_up.report
    assert len(files_of(again.data)) == 41 + 25 + 12


def test_filling_again_changes_nothing(made_up: Filled, tmp_path: Path):
    first = files_of(fill_made_up(tmp_path).data)
    assert files_of(fill_made_up(tmp_path).data) == first
    assert not list(tmp_path.rglob("*.partial"))


@pytest.mark.parametrize("queue", QUEUES)
def test_a_file_of_items_begins_with_what_it_was_made_from(made_up: Filled, queue: str):
    header = made_up.header(queue)
    assert set(header) == HEADER
    assert (header["desk"], header["queue"], header["synthetic"]) == (1, queue, True)
    assert header["question"] == f"{queue}@1" == draft.questions()[queue].version
    assert header["made_on"] == "2026-09-23"
    for made in header["made_from"]:
        assert set(made) == {"source_id", "file", "sha256"} and gate.is_made_up(made["source_id"])
        held = (made_up.data / "draft" / made["file"]).read_bytes()
        assert hashlib.sha256(held).hexdigest() == made["sha256"]
    assert {made["file"] for made in header["made_from"]} >= set(draft.QUEUES[queue][0])


@pytest.mark.parametrize("queue", QUEUES)
def test_an_item_has_the_fields_of_the_design_and_no_other(made_up: Filled, queue: str):
    names: set[str] = set()
    for item in made_up.items(queue):
        assert set(item) == ITEM
        assert re.fullmatch(r"[0-9a-f]{12}", item["rev"])
        if queue not in draft.DECIDED_ON_THE_GROUND:
            assert item["rev"] == draft.revision(item)
        assert item["id"] and len(item["id"]) <= 200 and item["id"] not in names
        assert item["group"] == draft.slug(item["group"])
        assert all(set(line) == {"label", "value", "source_id"} for line in item["lines"])
        assert all(line["label"] and line["value"] for line in item["lines"])
        assert item["text"] is None or set(item["text"]) == {"before", "body", "after"}
        # A draft may have the desk mark the map of a border: the fourth key.
        drawn = set(item["map"] or ()) - ({"marks"} if queue == "borders" else set())
        assert item["map"] is None or drawn == {"bbox", "focus", "layers"}
        assert isinstance(item["fill"], dict) and isinstance(item["preset"], dict)
        assert (item["map"] is not None) == (queue in DRAWS_A_MAP)
        names.add(item["id"])


@pytest.mark.parametrize("queue", QUEUES)
def test_every_made_up_item_says_that_it_is_made_up(made_up: Filled, queue: str):
    for item in made_up.items(queue):
        assert item["title"].endswith(" (made up)"), item["id"]
        sources = {line["source_id"] for line in item["lines"]} - {""}
        assert all(gate.is_made_up(source) for source in sources), item["id"]


# The queues that are read a part at a time, so that a part is finished: a borough, an
# area, a kind. Each puts its flagged items first within the part, and `test_queues.py`
# holds each to that.
IN_PARTS = ("names", "borders", "articles", "claims", "kinds")


@pytest.mark.parametrize("queue", [queue for queue in QUEUES if queue not in IN_PARTS])
def test_flagged_items_come_first(made_up: Filled, queue: str):
    flagged = [bool(item["flags"]) for item in made_up.items(queue)]
    assert flagged == sorted(flagged, reverse=True)


def test_every_flag_of_an_item_has_its_words_in_the_questions(made_up: Filled):
    held = json.loads(draft.QUESTIONS.read_text(encoding="utf-8"))["queues"]
    words = {queue["id"]: set(queue["flags"]) for queue in held}
    for queue in QUEUES:
        used = {flag for item in made_up.items(queue) for flag in item["flags"]}
        assert used <= words[queue], queue


@pytest.mark.parametrize(
    "words",
    [
        "62% of households rent from the council",
        "popular with young families",
        "most residents are retired",
        "a large student population",
        "Low crime",
        "house prices have risen",
        "people born abroad",
        "the most deprived ward",
        "young professionals",
    ],
)
def test_words_about_who_lives_somewhere_are_known_for_what_they_are(words: str):
    assert draft.about_residents(words)


@pytest.mark.parametrize(
    "words",
    [
        "How much of what you see from the street is trees, hedges and gardens?",
        "its ward is Kindlewharf ward 3",
        "margin 4%, second choice Pellam Cross",
        "Rented bicycles stand by the station",
        "Bornewood Parade",
    ],
)
def test_words_about_streets_and_buildings_are_let_through(words: str):
    assert not draft.about_residents(words)


def test_every_word_a_question_asks_for_is_given_by_the_item(made_up: Filled):
    held = json.loads(draft.QUESTIONS.read_text(encoding="utf-8"))["queues"]
    for queue in held:
        asked = set(re.findall(r"\{([a-z_]+)\}", queue["text"]))
        for item in made_up.items(queue["id"]):
            assert set(item["fill"]) == asked, item["id"]
            assert all(isinstance(word, str) and word for word in item["fill"].values())


def test_no_item_holds_a_field_about_residents(made_up: Filled):
    # The name the design gives this test: section 6. The fill step holds every draft to
    # the same list, and this holds the made-up city to it once more, titles and all.
    assert DRAWS_A_MAP == draft.DRAWS_A_MAP
    for queue in DRAWS_A_MAP:
        for item in made_up.items(queue):
            shown = [item["title"], *(f"{line['label']} {line['value']}" for line in item["lines"])]
            shown += list(item["fill"].values())
            # A name is a fact of its publisher, and one that may say who lives there is
            # flagged for the founder. Nothing else may hold such a word.
            named = queue == "names" and "describes_residents" in item["flags"]
            assert named or not draft.about_residents(" ".join(shown)), item["id"]
            allowed = {"of", "pick", "proposed", "holds", "fits", "leans_on", "area_id", "vibe"}
            assert not set(item["preset"]) - allowed, item["id"]
    flagged = [i["title"] for i in made_up.items("names") if "describes_residents" in i["flags"]]
    assert len(flagged) == 1 and "Pensioners Row" in flagged[0]


def test_a_map_is_drawn_from_layers_the_desk_holds(made_up: Filled):
    for queue in DRAWS_A_MAP:
        for item in made_up.items(queue):
            west, south, east, north = item["map"]["bbox"]
            assert west < east and south < north
            for layer in item["map"]["layers"]:
                group = "all" if layer == "boroughs" else item["group"]
                assert (made_up.data / "layers" / group / f"{layer}.geojson").is_file()


def test_filling_never_touches_the_decisions(tmp_path: Path):
    line = '{"n":1,"reviewer":"r1","queue":"names","item":"n:syn-n0004","answer":"area"}\n'
    kept = tmp_path / "decisions" / "names" / "r1.jsonl"
    kept.parent.mkdir(parents=True)
    kept.write_text(line, encoding="utf-8")
    before = kept.stat()
    fill_made_up(tmp_path)
    fill_made_up(tmp_path)
    assert kept.read_text(encoding="utf-8") == line
    assert (kept.stat().st_mtime_ns, kept.stat().st_ino) == (before.st_mtime_ns, before.st_ino)
    assert files_of(tmp_path / "decisions") == {
        "names/r1.jsonl": hashlib.sha256(line.encode()).hexdigest()
    }


# What reopens an answer


def changed(before: dict[str, str], after: dict[str, str]) -> set[str]:
    return {name for name in before if after.get(name) != before[name]}


def test_a_name_respelt_reopens_no_border_no_borough_and_no_rating(made_up: Filled):
    # One capital letter of one name, which is a spelling the page offers. A border is
    # decided on the ground, and the ground has not moved.
    draft_of = Draft.open(made_up.data / "draft", synthetic=True)
    before = {queue: draft.MAKERS[queue](draft_of) for queue in QUEUES}
    draft_of.areas["syn-n0004"]["name"] = "Dulcimer green"
    for cached in ("neighbours",):
        draft_of.__dict__.pop(cached, None)
    after = {queue: draft.MAKERS[queue](draft_of) for queue in QUEUES}

    def revs_of(items: list[dict[str, Any]]) -> dict[str, str]:
        return {item["id"]: item["rev"] for item in items}

    for queue in draft.DECIDED_ON_THE_GROUND:
        assert changed(revs_of(before[queue]), revs_of(after[queue])) == set(), queue
        titles = {item["title"] for item in after[queue]}
        assert queue == "whole" or any("Dulcimer green" in title for title in titles)
    assert changed(revs_of(before["names"]), revs_of(after["names"])) >= {"n:syn-n0004"}


def test_a_cell_that_changes_area_reopens_the_border_of_both_areas(made_up: Filled):
    draft_of = Draft.open(made_up.data / "draft", synthetic=True)
    before = {item["id"]: item["rev"] for item in draft.borders(draft_of)}
    row = next(row for row in draft_of.table("oa_to_area.csv") if row["area_id"] == "syn-n0007")
    code, there = row["oa21cd"], draft.evidence_of(row)["second"]
    row["area_id"] = there
    draft_of.cells[code]["properties"]["area"] = there  # type: ignore[index]
    for cached in ("membership", "cells_of", "neighbours"):
        draft_of.__dict__.pop(cached, None)
    after = {item["id"]: item["rev"] for item in draft.borders(draft_of)}
    assert changed(before, after) == {"syn-n0007", there}


def test_a_changed_rubric_reopens_the_ratings_of_its_vibe_alone(made_up: Filled):
    draft_of = Draft.open(made_up.data / "draft", synthetic=True)
    before = {item["id"]: item["rev"] for item in draft.ratings(draft_of)}
    row = next(row for row in draft_of.table("rubrics.csv") if row["vibe"] == "leafy")
    row["rubric"] = "How much of what you see from the street is green?"
    after = {item["id"]: item["rev"] for item in draft.ratings(draft_of)}
    reopened = changed(before, after)
    assert reopened and all(name.endswith(":leafy") for name in reopened)
    assert len(reopened) == len(draft_of.areas)


# London takes the same path


def test_a_draft_of_real_sources_takes_the_same_path(made_up: Filled, real_draft: Path):
    data = real_draft.parent
    report = fill.fill(real_draft, data, synthetic=False, made_on="2026-10-06", registry=REGISTRY)
    assert [(queue.queue, queue.items) for queue in report.queues] == [
        (queue.queue, queue.items) for queue in made_up.report.queues
    ]
    real = Filled(data, report)
    for queue in QUEUES:
        header = real.header(queue)
        assert (header["synthetic"], header["made_on"]) == (False, "2026-10-06")
        assert not any(gate.is_made_up(made["source_id"]) for made in header["made_from"])
        if queue == "kinds":
            # A sample is drawn by the ids of its records, so another id draws another.
            continue
        for item, made in zip(real.items(queue), made_up.items(queue), strict=True):
            assert item["id"] == made["id"].replace("syn-", "lon-")
            assert item["title"] == made["title"].removesuffix(" (made up)")
    assert real.layer("quillhaven", "cells")["desk"]["synthetic"] is False
    sources = {made["source_id"] for made in real.header("sentences")["made_from"]}
    assert sources == {"wikimedia-wikipedia-excerpts"}
    assert {made["source_id"] for made in real.header("whole")["made_from"]} >= {"burro"}


def test_two_files_of_one_publisher_are_shown_under_the_name_of_that_publisher(
    real_draft: Path,
):
    report = fill.fill(real_draft, real_draft.parent, synthetic=False, registry=REGISTRY)
    names = Filled(real_draft.parent, report).items("names")
    labels = {
        line["source_id"]: line["label"]
        for item in names
        for line in item["lines"]
        if line["source_id"]
    }
    assert labels["os-open-names"] == "Ordnance Survey, OS Open Names"
    assert labels["os-boundary-line"] == "Ordnance Survey, OS Boundary-Line"
    assert labels["gla-town-centre-boundaries"].startswith("Greater London Authority, ")
    assert not set(labels) & set(labels.values())


def without_a_layer_of_records(folder: Path) -> dict[str, list[float]]:
    """Draw a draft as the areas build draws one: no layer of records, and each record of
    a name as a point of the layer of names, under the record's own id.

    Gives where each record was put, by its id.
    """
    put: dict[str, list[float]] = {}
    for path in sorted(folder.glob("layers/*/records.geojson")):
        names = path.with_name("names.geojson")
        held = json.loads(names.read_text(encoding="utf-8"))
        for record in json.loads(path.read_text(encoding="utf-8"))["features"]:
            if record["properties"]["source_id"] != "os-open-names":
                continue
            put[record["id"]] = record["geometry"]["coordinates"]
            held["features"].append(
                {
                    "type": "Feature",
                    "id": record["id"],
                    "properties": {"name": record["properties"]["as_written"], "kind": "Hamlet"},
                    "geometry": record["geometry"],
                }
            )
        names.write_text(json.dumps(held), encoding="utf-8")
        path.unlink()
    return put


def test_a_name_is_shown_where_its_record_puts_it_in_a_draft_that_draws_no_records(
    real_draft: Path,
):
    # Seen at the desk, on the first draft of London: a smaller place inside an area was
    # asked about, and nothing on the map said where in the area the place is.
    put = without_a_layer_of_records(real_draft)
    report = fill.fill(real_draft, real_draft.parent, synthetic=False, registry=REGISTRY)
    real = Filled(real_draft.parent, report)
    assert "records" not in {
        layer for item in real.items("names") for layer in item["map"]["layers"]
    }
    item = real.item("names", "a:lon-n0007:foxholt-market")
    assert item["map"]["focus"]["area"] == "lon-n0007"
    assert item["map"]["focus"]["at"] in [[round(x, 6), round(y, 6)] for x, y in put.values()]
    west, south, east, north = item["map"]["bbox"]
    x, y = item["map"]["focus"]["at"]
    assert west < x < east and south < y < north
    placed = [item for item in real.items("names") if "at" in item["map"]["focus"]]
    assert len(placed) > 10, "and so is every name that a record of a point writes"


def test_a_real_draft_is_made_on_the_day_it_is_filled(real_draft: Path):
    report = fill.fill(real_draft, real_draft.parent, synthetic=False, registry=REGISTRY)
    made_on = Filled(real_draft.parent, report).header("names")["made_on"]
    assert re.fullmatch(r"20\d\d-\d\d-\d\d", made_on)


# What is refused


def table_with(folder: Path, name: str, old: str, new: str) -> None:
    path = folder / name
    path.write_text(path.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")


@pytest.mark.parametrize(
    ("name", "old", "new", "refusal"),
    [
        ("kinds.csv", "overture-places", "google-places", "'google-places' is banned"),
        ("figures.csv", "defra-pcm-background-air", "ons-census-2021-resident-tables", "gated"),
        ("name_evidence.csv", "os-open-names", "osm-place-nodes", "'osm-place-nodes' is gated"),
        ("claims.jsonl", "wikimedia-wikipedia-excerpts", "wikimedia-wikivoyage-text", "is held"),
        ("kinds.csv", "overture-places", "synthetic", "A real draft names a made-up source"),
        (
            "layers/quillhaven/roads.geojson",
            "ons-output-areas-2021",
            "osm-geofabrik-greater-london",
            "not registered for gazetteer",
        ),
    ],
)
def test_a_source_the_registry_refuses_stops_the_fill_and_nothing_is_written(
    real_draft: Path, name: str, old: str, new: str, refusal: str
):
    table_with(real_draft, name, old, new)
    before = files_of(real_draft.parent)
    with pytest.raises(gate.Refused, match=refusal):
        fill.fill(real_draft, real_draft.parent, synthetic=False, registry=REGISTRY)
    assert files_of(real_draft.parent) == before


def cells_with(folder: Path, change: str, *, every: bool = False) -> None:
    """Add to the evidence of the first cell of a draft, or of every cell."""
    path = folder / "oa_to_area.csv"
    head, *rows = path.read_text(encoding="utf-8").splitlines(keepends=True)
    for at, row in enumerate(rows if every else rows[:1]):
        cells = row.split(",")
        cells[3] = f"{cells[3]};{change}"
        rows[at] = ",".join(cells)
    path.write_text("".join([head, *rows]), encoding="utf-8")


def test_a_name_from_a_source_that_is_gated_is_never_shown_beside_a_border(real_draft: Path):
    # The registry gates the file of MSOA names until its licence is read. The table of
    # cells is Burro's own work, but a name in its evidence is its publisher's.
    cells_with(real_draft, "msoa=A Name From The Gated File")
    before = files_of(real_draft.parent)
    with pytest.raises(gate.Refused, match="'hoc-library-msoa-names' is gated"):
        fill.fill(real_draft, real_draft.parent, synthetic=False, registry=REGISTRY)
    assert files_of(real_draft.parent) == before


def test_each_name_in_the_evidence_of_a_cell_has_a_source_the_gate_is_asked_about():
    named = {key for key in draft.EVIDENCE if key not in ("margin", "second")}
    assert set(draft.EVIDENCE_SOURCE) == named == {"roads", "ward", "msoa", "centre"}
    assert draft.EVIDENCE_SOURCE["msoa"] == "hoc-library-msoa-names"


def test_the_evidence_a_real_draft_may_show_passes_the_gate(real_draft: Path):
    cells_with(real_draft, "roads=A Made-up Settlement;centre=A Made-up Centre", every=True)
    report = fill.fill(real_draft, real_draft.parent, synthetic=False, registry=REGISTRY)
    shown = Filled(real_draft.parent, report).items("borders")
    said = " ".join(line["value"] for item in shown for line in item["lines"])
    assert "its roads say A Made-up Settlement" in said


@pytest.mark.parametrize(
    ("change", "said"),
    [
        ("ward=62% of households rent from the council", "oa_to_area.csv, row 1"),
        ("roads=Where young families live", "oa_to_area.csv, row 1"),
        ("centre=Low crime", "oa_to_area.csv, row 1"),
    ],
)
def test_evidence_about_who_lives_somewhere_stops_the_fill(
    real_draft: Path, change: str, said: str
):
    # Rule 8. Nothing that describes who lives somewhere stands beside a border.
    cells_with(real_draft, change)
    before = files_of(real_draft.parent)
    with pytest.raises(Unfit, match=said) as refusal:
        fill.fill(real_draft, real_draft.parent, synthetic=False, registry=REGISTRY)
    assert "who lives somewhere" in str(refusal.value)
    assert change.split("=")[1] not in str(refusal.value), "the words name the row, never a value"
    assert files_of(real_draft.parent) == before


@pytest.mark.parametrize(
    "rubric",
    [
        "How many young professionals live here?",
        "Is it popular with students?",
        "How many people are on the street at night?",
        "How high are the rents?",
        "How much crime is there?",
    ],
)
def test_a_rubric_about_who_lives_somewhere_stops_the_fill(real_draft: Path, rubric: str):
    # vibes 6.2: a rubric is in words about streets, buildings and places.
    path = real_draft / "rubrics.csv"
    head, first, *rest = path.read_text(encoding="utf-8").splitlines(keepends=True)
    path.write_text("".join([head, first, f'leafy,"{rubric}"\n', *rest]), encoding="utf-8")
    before = files_of(real_draft.parent)
    with pytest.raises(Unfit, match=r"rubrics\.csv, row 2") as refusal:
        fill.fill(real_draft, real_draft.parent, synthetic=False, registry=REGISTRY)
    assert rubric not in str(refusal.value)
    assert files_of(real_draft.parent) == before


def test_a_place_may_be_named_for_a_word_that_a_rubric_may_not_use(real_draft: Path):
    # A name is a fact of its publisher. The founder reads every name, in Names.
    table_with(real_draft, "areas.csv", "Alderwick", "Students Green")
    table_with(real_draft, "name_evidence.csv", "Alderwick", "Students Green")
    report = fill.fill(real_draft, real_draft.parent, synthetic=False, registry=REGISTRY)
    titles = [item["title"] for item in Filled(real_draft.parent, report).items("borders")]
    assert any("Students Green" in title for title in titles)


def test_a_figure_about_who_lives_somewhere_never_reaches_the_desk(real_draft: Path):
    # Rule 8. The census tables are registered for the census table alone, so the gate
    # keeps them out of the queue of figures.
    table_with(
        real_draft, "figures.csv", "defra-pcm-background-air", "ons-census-2021-resident-tables"
    )
    with pytest.raises(gate.Refused, match="ons-census-2021-resident-tables"):
        fill.fill(real_draft, real_draft.parent, synthetic=False, registry=REGISTRY)
    assert not (real_draft.parent / "items").exists()


def test_the_made_up_city_and_london_are_never_filled_into_one_folder(
    made_up: Filled, real_draft: Path, tmp_path: Path
):
    fill.fill(real_draft, real_draft.parent, synthetic=False, registry=REGISTRY)
    before = files_of(real_draft.parent)
    with pytest.raises(Unfit, match="holds the other city"):
        fill.fill(RELEASE, real_draft.parent, synthetic=True)
    assert files_of(real_draft.parent) == before
    other = fill_made_up(tmp_path / "made-up").data
    with pytest.raises(Unfit, match="holds the other city"):
        fill.fill(other / "draft", other, synthetic=False, registry=REGISTRY)


def test_a_draft_of_the_other_city_is_refused(made_up: Filled, tmp_path: Path):
    shutil.copytree(made_up.data / "draft", tmp_path / "draft")
    with pytest.raises(Unfit, match="another layer, of another group or another city"):
        fill.fill(tmp_path / "draft", tmp_path, synthetic=False, registry=REGISTRY)
    assert not (tmp_path / "items").exists() and not (tmp_path / "layers").exists()


def test_a_draft_of_real_files_is_kept_where_a_build_reads_it(real_draft: Path, tmp_path: Path):
    # The step that makes a build's files reads `<data>/draft`. A draft filled from any
    # other folder would be decided on and then never found.
    with pytest.raises(Unfit, match="kept in the folder draft, inside the data folder"):
        fill.fill(real_draft, tmp_path / "elsewhere", synthetic=False, registry=REGISTRY)
    assert not (tmp_path / "elsewhere").exists()


def test_a_flag_the_page_has_no_words_for_stops_the_fill(real_draft: Path):
    with (real_draft / "flags.csv").open("a", encoding="utf-8") as file:
        file.write("borders,lon-n0002,looks_odd\n")
    with pytest.raises(Unfit, match="a flag the page has no words for"):
        fill.fill(real_draft, real_draft.parent, synthetic=False, registry=REGISTRY)
    assert not (real_draft.parent / "items").exists()


@pytest.mark.parametrize(
    ("name", "first", "refusal"),
    [
        ("areas.csv", "area_id,name\n", "areas.csv does not have the columns of the design"),
        (
            "kinds.csv",
            "record_id,source_id,kind,name,category,upstream,age\n",
            "kinds.csv does not",
        ),
        ("oa_to_area.csv", None, "oa_to_area.csv holds a cell twice"),
        (
            "oa_to_area.csv",
            "oa21cd,area_id,basis,evidence,decided_by,decided_on,reason\n"
            "lon-oa0001,lon-n0024,auto,income=low;margin=58,,,\n",
            "oa_to_area.csv gives evidence that is not one of",
        ),
        ("sentences.jsonl", '{"page_id": 1}\n', "sentences.jsonl holds a line without the keys"),
        ("claims.jsonl", "not json\n", "claims.jsonl cannot be read as lines of JSON"),
    ],
)
def test_a_file_that_is_not_as_the_design_gives_it_stops_the_fill(
    real_draft: Path, name: str, first: str | None, refusal: str
):
    held = (real_draft / name).read_text(encoding="utf-8").splitlines(keepends=True)
    (real_draft / name).write_text(first or "".join([*held, held[-1]]), encoding="utf-8")
    before = files_of(real_draft.parent)
    with pytest.raises(Unfit, match=refusal):
        fill.fill(real_draft, real_draft.parent, synthetic=False, registry=REGISTRY)
    assert files_of(real_draft.parent) == before


def test_a_queue_whose_file_the_draft_lacks_is_said_and_not_filled(tmp_path: Path):
    folder = tmp_path / "draft"
    draft.write_table(folder, "rubrics.csv", [{"vibe": "leafy", "rubric": "How leafy?"}])
    draft.write_table(folder, "kinds.csv", [])
    report = fill.fill(folder, tmp_path, synthetic=False, registry=REGISTRY)
    lacks = {queue.queue: queue.lacks for queue in report.queues}
    assert lacks["ratings"] == ("areas.csv",) and lacks["names"] == (
        "areas.csv",
        "name_evidence.csv",
    )
    assert lacks["kinds"] == () and report.items == 0
    assert sorted(path.name for path in (tmp_path / "items").iterdir()) == ["kinds.jsonl"]


def test_a_queue_that_was_filled_before_is_left_when_the_draft_lacks_its_file(real_draft: Path):
    data = real_draft.parent
    first = fill.fill(real_draft, data, synthetic=False, made_on="2026-10-06", registry=REGISTRY)
    before = Filled(data, first).rows("claims")
    (real_draft / "claims.jsonl").unlink()
    again = fill.fill(real_draft, data, synthetic=False, made_on="2026-10-07", registry=REGISTRY)
    assert Filled(data, again).rows("claims") == before
    assert Filled(data, again).header("names")["made_on"] == "2026-10-07"


# What is said


def said(capsys: pytest.CaptureFixture[str]) -> tuple[str, str]:
    captured = capsys.readouterr()
    return captured.out, captured.err


def test_the_run_says_of_each_queue_how_many_items_and_how_long(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    assert fill.run(RELEASE, tmp_path, synthetic=True) == 0
    out, err = said(capsys)
    assert err == ""
    lines = out.splitlines()
    assert lines[0] == "Filled from the made-up city. 25 layers."
    rows = {line.split()[0]: line.split() for line in lines[2:15]}
    assert list(rows) == [*QUEUES, "all"]
    assert rows["names"] == ["names", "37", "6", "45", "s", "an", "item", "28", "min"]
    assert rows["articles"] == ["articles", "30", "3", "20", "s", "an", "item", "10", "min"]
    assert rows["borders"] == ["borders", "24", "8", "8", "min", "an", "item", "3.2", "h"]
    assert rows["sentences"][-6:] == ["12", "min", "an", "article", "36", "min"]
    assert rows["rules"] == ["rules", "5", "0", "2", "min", "an", "item", "10", "min"]
    assert rows["all"] == ["all", "512", "6.5", "h"]
    assert lines[-1] == "The pace is the design's guess. Nobody has timed it."


def test_the_pace_of_each_queue_is_the_pace_of_the_design():
    assert {queue: each for queue, (each, _) in fill.PACE.items()} == {
        "rules": 120,
        "claims": 25,
        "borders": 480,
        "names": 45,
        "whole": 900,
        "sentences": 720,
        "ratings": 10,
        "figures": 15,
        "kinds": 6,
        "know": 5,
        "commons": 60,
        "articles": 20,
    }
    assert [queue for queue, (_, of) in fill.PACE.items() if of == fill.GROUP] == ["sentences"]


def test_the_run_prints_counts_and_no_word_of_a_file(
    made_up: Filled, tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    fill.run(RELEASE, tmp_path, synthetic=True)
    out, _ = said(capsys)
    held: set[str] = set()
    for queue in QUEUES:
        for item in made_up.items(queue):
            held |= {item["id"], item["title"].removesuffix(" (made up)")}
    assert not [word for word in held if word in out]
    assert "syn-" not in out and "Quillhaven" not in out


def test_a_refusal_is_said_in_one_line_and_the_run_ends_with_2(
    real_draft: Path, capsys: pytest.CaptureFixture[str]
):
    table_with(real_draft, "kinds.csv", "overture-places", "google-places")
    assert fill.run(real_draft, real_draft.parent, synthetic=False) == 2
    out, err = said(capsys)
    assert out == "" and err.count("\n") == 1
    assert err.startswith("Not filled. 'google-places' is banned, not approved")


def test_the_fill_step_needs_python_alone_on_the_made_up_city():
    # `make desk` fills the made-up city before anything is installed. Only the gate
    # imports outside the standard library, and only when it is asked about a real file.
    folder = Path(fill.__file__).parent
    allowed = {"desk", *stdlib()}
    for path in sorted(folder.glob("*.py")):
        found = re.findall(r"^\s*(?:from|import) ([a-z_0-9]+)", path.read_text("utf-8"), re.M)
        outside = set(found) - allowed
        assert outside == ({"burro_pipeline"} if path.name == "gate.py" else set()), path.name
    top = re.findall(
        r"^(?:from|import) ([a-z_0-9]+)", (folder / "gate.py").read_text("utf-8"), re.M
    )
    assert "burro_pipeline" not in top


def stdlib() -> frozenset[str]:
    import sys

    return sys.stdlib_module_names
