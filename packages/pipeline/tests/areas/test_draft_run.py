"""The whole draft in one command: what it writes, what it refuses, and that it repeats.

Nothing here is real, and nothing reaches a network or a store of fetched
files. `draft_support.py` puts every file of the made-up town in one store.
"""

import ast
import hashlib
import json
import re
import socket
from dataclasses import replace
from pathlib import Path
from xml.etree import ElementTree

import burro_pipeline.areas
import pytest
from burro_pipeline.areas import assign, draft_picture, draft_run
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.fetch.offline import NetworkRefused
from burro_pipeline.fetch.store import FOLDER_VARIABLE
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import SHARE_ALIKE_LICENCES, Status, Use

from ..cells.support import CANARY, registry
from . import names_support as town
from .draft_support import CENTRES, SETTINGS, given, made, make, receipts_folder

AREAS = Path(burro_pipeline.areas.__file__).parent
MODULES = sorted(AREAS.glob("draft*.py"))
# Every source the whole draft reads.
READ = (town.NAMES, town.CENTRES, town.LINE, town.ROADS, town.OUTLINES, town.LOOKUP, CENTRES)
# Sources that would be useful and that the gate does not give for a gazetteer.
REFUSED = (
    "hoc-library-msoa-names",
    "gla-high-street-boundaries",
    "ons-census-2021-housing-tables",
    "os-open-rivers",
    "os-open-greenspace",
    "dft-naptan",
    "osm-geofabrik-greater-london",
)
CURATED = (
    *("areas.csv", "oa_to_area.csv", "aliases.csv", "name_evidence.csv", "relations.csv"),
    "snapshots.json",
)


def every_file(folder: Path) -> dict[str, str]:
    """Every file under a folder, by where it is, with the hash of what it holds."""
    return {
        path.relative_to(folder).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(folder.rglob("*"))
        if path.is_file()
    }


def run(folder: Path, out: Path, *more: str, store: bool = True, receipts: bool = True) -> int:
    """The command, as it is typed, on the made-up town in a store of its own."""
    found = given(folder)
    held = receipts_folder(folder / "receipts", found.receipts) if receipts else folder / "none"
    return draft_run.main(
        ["--out", str(out), "--receipts", str(held), *more],
        {FOLDER_VARIABLE: str(found.store)} if store else {},
    )


# What a run makes


def test_one_run_makes_every_part_of_the_draft():
    out = made().out
    assert sorted(path.name for path in out.iterdir()) == sorted(
        [
            *CURATED,
            *("about.txt", "area_names.csv", "counts.json", "names_to_look_at.csv"),
            *("rules_put_to_the_founder.csv", "rules_would_settle.csv", "largest_areas.csv"),
            *("named_by_the_rule.csv", "desk", "made", "pictures"),
        ]
    )
    assert sorted(path.name for path in (out / "made").iterdir()) == [
        "areas",
        "context",
        "draft",
        "flags",
        "names",
    ]
    for part, file in (
        ("names", "candidates.csv"),
        ("names", "seeds.csv"),
        ("areas", "oa_to_area.csv"),
        ("areas", "outlines.geojson"),
        ("flags", "flags.csv"),
        ("flags", "order.csv"),
        ("context", "layers.json"),
    ):
        assert (out / "made" / part / file).is_file(), file
    desk = out / "desk" / "draft"
    assert {"areas.csv", "oa_to_area.csv", "aliases.csv", "name_evidence.csv", "flags.csv"} <= {
        path.name for path in desk.iterdir()
    }
    assert (desk / "layers" / "all" / "boroughs.geojson").is_file()
    assert every_file(desk / "layers") == every_file(out / "made" / "context" / "layers")


def test_the_desk_is_handed_the_order_to_look_at_the_areas_and_the_boroughs_in():
    """The desk reads names and borders borough by borough, the most at stake first."""
    draft = made()
    assert draft.columns("desk/draft/order.csv") == ("queue", "item", "rank")
    handed = [
        (row["queue"], row["item"], row["rank"]) for row in draft.rows("desk/draft/order.csv")
    ]
    whole = [(row["queue"], row["item"], row["rank"]) for row in draft.rows("made/flags/order.csv")]
    assert handed == whole
    areas = {row["area_id"] for row in draft.rows("desk/draft/areas.csv")}
    assert {item for queue, item, _ in handed if queue == "borders"} == areas
    # A borough is named as the desk names the group of its items.
    groups = {
        re.sub(r"[^a-z0-9]+", "-", row["primary_borough"].casefold()).strip("-")
        for row in draft.rows("desk/draft/areas.csv")
    }
    assert {item for queue, item, _ in handed if queue == "whole"} == groups
    for queue in ("borders", "whole"):
        ranks = [int(rank) for held, _, rank in handed if held == queue]
        assert ranks == list(range(1, len(ranks) + 1))


def test_the_seeds_grow_into_the_areas_and_the_areas_are_what_is_flagged():
    """The three parts fit: every area is grown from a seed, named, flagged and drawn."""
    draft = made()
    seeds = {row["area_id"] for row in draft.rows("made/names/seeds.csv")}
    areas = {row["area_id"] for row in draft.rows("areas.csv")}
    taken_in = {row["seed_id"] for row in draft.rows("made/areas/absorbed.csv")}
    assert areas == seeds - taken_in and areas
    assert {row["area_id"] for row in draft.rows("oa_to_area.csv")} == areas
    order = [row for row in draft.rows("made/flags/order.csv") if row["queue"] == "borders"]
    assert {row["item"] for row in order} == areas
    assert [int(row["rank"]) for row in order] == list(range(1, len(areas) + 1))
    assert draft.counted["areas"] == len(areas)
    assert draft.counted["seeds"] == len(seeds)
    assert draft.counted["output_areas"] == len(town.LONDON)


def test_the_same_files_give_the_same_bytes(tmp_path: Path):
    first, second = make(tmp_path / "one"), make(tmp_path / "two")
    assert every_file(first.out) == every_file(second.out) == every_file(made().out)
    assert first.counted == second.counted


def test_a_run_prints_counts_alone(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    # The rules are the real ones, so the small town is one area.
    assert run(tmp_path, tmp_path / "out") == 0
    printed = capsys.readouterr()
    assert printed.err == ""
    assert printed.out.startswith("step=areas-draft status=ok output_areas=31 ")
    assert printed.out.count("\n") == 1
    assert all(pair.split("=")[1].isdigit() for pair in printed.out.split()[2:])
    for word in ("Alderwick", "Quillhaven", "E00", "osgb", str(tmp_path), CANARY):
        assert word not in printed.out
    assert (tmp_path / "out" / "areas.csv").is_file()


def test_the_note_beside_a_draft_says_what_it_is_and_names_no_place():
    about = (made().out / "about.txt").read_text(encoding="utf-8")
    assert "nobody has checked" in about and "No name and no border" in about
    assert not any(record.name in about for record in town.PLACES)
    for name in CURATED:
        assert name in about


SVG = "{http://www.w3.org/2000/svg}"


def _read(drawn: bytes) -> ElementTree.Element:
    """A picture as a document. It was drawn by the code under test, from made-up files."""
    return ElementTree.fromstring(drawn)  # noqa: S314


def test_a_run_draws_the_whole_of_the_town_and_each_of_its_boroughs():
    pictures = made().out / "pictures"
    assert sorted(path.name for path in pictures.iterdir()) == [
        "borough-quillhaven.svg",
        "borough-tallowgate.svg",
        "london.svg",
    ]
    whole = _read((pictures / "london.svg").read_bytes())
    filled = [
        path for path in whole.findall(f"{SVG}path") if path.get("fill") in draft_picture.COLOURS
    ]
    assert len(filled) == made().counted["areas"]
    assert "checked by nobody" in (whole.findtext(f"{SVG}title") or "")
    # Two areas side by side are never one colour.
    assert len({path.get("fill") for path in filled}) > 1
    one = _read((pictures / "borough-quillhaven.svg").read_bytes())
    labels = [text.text for text in one.findall(f"{SVG}text")][:-1]
    assert labels and all((label or "").isdigit() for label in labels)


# What a run reads, and what it does not


def test_every_file_is_asked_for_as_a_gazetteer_and_none_is_share_alike(tmp_path: Path):
    found = given(tmp_path)
    draft_run.make(found.inputs, tmp_path / "out", settings=SETTINGS)
    read = {opened.receipt.source_id for opened in found.inputs.opened}
    assert read == set(READ) - {town.CENTRES}
    for source_id in READ:
        source = registry().get(source_id)
        registry().require(source_id, Use.GAZETTEER)
        assert source.status is Status.APPROVED, source_id
        assert not source.share_alike and not source.licences & SHARE_ALIKE_LICENCES, source_id


@pytest.mark.parametrize("refused", sorted(READ))
def test_a_run_stops_at_a_file_the_gate_does_not_give_and_writes_no_curated_file(
    tmp_path: Path, refused: str
):
    sources = tuple(
        source.model_copy(update={"uses": (Use.SCORING,)}) if source.id == refused else source
        for source in registry()
    )
    found = given(tmp_path, Registry(sources=sources))
    with pytest.raises(LockError) as stopped:
        draft_run.make(found.inputs, tmp_path / "out", settings=SETTINGS)
    assert (stopped.value.rule, stopped.value.subject) == ("gate_refuses", refused)
    assert refused not in {opened.receipt.source_id for opened in found.inputs.opened}
    assert not any((tmp_path / "out" / name).exists() for name in CURATED)


@pytest.mark.parametrize("path", MODULES, ids=lambda path: path.name)
def test_no_module_of_the_whole_draft_names_a_source_the_gate_refuses(path: Path):
    """OpenStreetMap least of all: ADR 0004. Nor homes, nor anything about who lives anywhere."""
    text = path.read_text(encoding="utf-8").casefold()
    held = {
        node.value
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert not held & set(REFUSED)
    for word in ("osm-", "geofabrik", "overture", "census", "wikipedia"):
        assert word not in text, word


def test_nothing_is_written_to_the_store(tmp_path: Path):
    found = given(tmp_path)
    before = every_file(found.store)
    draft_run.make(found.inputs, tmp_path / "out", settings=SETTINGS)
    assert every_file(found.store) == before


def test_no_socket_can_be_made_while_a_draft_is_made(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    tried: list[str] = []

    def reaching(inputs: Inputs, out: Path, **_: object) -> dict[str, object]:
        try:
            socket.socket()
        except NetworkRefused as refused:
            tried.append(str(refused))
        return {"areas": 0}

    monkeypatch.setattr(draft_run, "make", reaching)
    assert run(tmp_path, tmp_path / "out") == 0
    assert tried == ["this step may not reach a network: only fetch does"]


# What a run refuses


def test_a_run_writes_nothing_into_a_folder_that_git_tracks(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    tracked = AREAS / "drafted"
    assert run(tmp_path, tracked) == 2
    printed = capsys.readouterr()
    assert "git tracks" in printed.err
    assert printed.out == "step=areas-draft status=unreadable\n"
    assert not tracked.exists()


def test_a_run_does_not_write_over_a_folder_that_holds_something_unless_it_is_told_to(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    out = tmp_path / "out"
    out.mkdir()
    (out / "kept.txt").write_text("kept", encoding="utf-8")
    assert run(tmp_path, out) == 2
    assert "holds something already" in capsys.readouterr().err
    assert sorted(path.name for path in out.iterdir()) == ["kept.txt"]
    assert run(tmp_path, out, "--again") == 0
    assert (out / "areas.csv").is_file() and (out / "kept.txt").is_file()


def test_a_run_stops_where_no_store_is_named_or_no_receipts_are_there(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    assert run(tmp_path / "a", tmp_path / "out", store=False) == 2
    assert FOLDER_VARIABLE in capsys.readouterr().err
    assert run(tmp_path / "b", tmp_path / "out", receipts=False) == 2
    assert "receipts" in capsys.readouterr().err
    assert run(tmp_path / "c", tmp_path / "out", "--ids", str(tmp_path / "none.csv")) == 2
    assert "ids" in capsys.readouterr().err
    assert not (tmp_path / "out").exists()


def test_a_file_that_is_not_what_its_receipt_says_stops_the_run_and_names_the_rule(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    found = given(tmp_path)
    held = receipts_folder(tmp_path / "receipts", found.receipts)
    for path in (found.store / "raw" / town.LOOKUP).rglob("*.csv"):
        path.write_bytes(path.read_bytes() + b"\n")
    status = draft_run.main(
        ["--out", str(tmp_path / "out"), "--receipts", str(held)],
        {FOLDER_VARIABLE: str(found.store)},
    )
    printed = capsys.readouterr()
    assert status == 2
    assert printed.out.startswith("step=areas-draft status=refused ")
    assert printed.err.startswith("error: ") and str(tmp_path) not in printed.err


def test_a_run_may_be_made_by_the_designs_own_rule_and_says_which_rule_made_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    assert run(tmp_path / "a", tmp_path / "out", "--points", "6") == 2
    assert "together" in capsys.readouterr().err
    assert run(tmp_path / "b", tmp_path / "out", "--points", "9", "--publishers", "2") == 0
    counted = json.loads((tmp_path / "out" / "counts.json").read_bytes())
    assert counted["names"]["rule"]["points"] == 9
    assert counted["names"]["rule"]["publishers"] == 2
    assert counted["names"]["areas"] == 1


def test_a_place_keeps_the_id_an_earlier_draft_gave_it(tmp_path: Path):
    first = make(tmp_path / "one")
    ids = first.out / "made" / "names" / "ids.csv"
    again = given(tmp_path / "two")
    draft_run.make(again.inputs, tmp_path / "two" / "out", ids=ids, settings=SETTINGS)
    assert (tmp_path / "two" / "out" / "areas.csv").read_bytes() == (
        first.out / "areas.csv"
    ).read_bytes()


# What a person decided at the review desk


# The answers of the desk's queue of names, as its own table of answers holds them. The
# desk cannot take the ground from under an area, so the draft is made again from these.
DECIDED = """\
item,reviewer,answer,of,pick,note,second,decided_on,synthetic
n:lon-n0010,r1,inside,lon-n0001,Thrushcombe,,false,2026-09-25,true
n:lon-n0008,r1,drop,,Kindlewharf,,false,2026-09-25,true
n:lon-n0001,r1,area,,Alderwick,,false,2026-09-25,true
n:lon-n0006,r1,unknown,,Farrowmere,,false,2026-09-25,true
n:lon-n0009,r2,drop,,Wexmoor,,false,2026-09-25,true
a:lon-n0001:foxholt,r1,drop,,Foxholt,,false,2026-09-25,true
"""


def decided(folder: Path, text: str = DECIDED) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "names.csv").write_text(text, encoding="utf-8")
    return folder / "names.csv"


def test_a_draft_made_again_leaves_out_the_names_the_founder_turned_down(tmp_path: Path):
    first = made()
    ids = first.out / "made" / "names" / "ids.csv"
    again = tmp_path / "out"
    said = draft_run.read_decided(decided(tmp_path))
    assert said == {"lon-n0010": "inside", "lon-n0008": "drop", "lon-n0001": "area"}
    draft_run.make(given(tmp_path).inputs, again, ids=ids, settings=replace(SETTINGS, decided=said))
    draft = type(first)(again, first.store, {})
    areas = {row["area_id"]: row["name"] for row in draft.rows("areas.csv")}
    # Every other area stands under the id it had.
    assert areas == {"lon-n0001": "Alderwick", "lon-n0006": "Farrowmere", "lon-n0009": "Wexmoor"}
    # Every output area is still in exactly one area, and in one that stands.
    given_to = [row["area_id"] for row in draft.rows("oa_to_area.csv")]
    assert len(given_to) == len(town.LONDON) and set(given_to) == set(areas)
    # The name that was turned down is another name, where its record lies.
    others = {(row["alias"], row["kind"]): row["area_id"] for row in draft.rows("aliases.csv")}
    assert others["Thrushcombe", "inside"] in areas
    # The name that is not kept is in no curated file, and its id is given to no other.
    for name in ("areas.csv", "aliases.csv", "name_evidence.csv", "area_names.csv"):
        assert "Kindlewharf" not in (again / name).read_text(encoding="utf-8").split(",")
    assert "lon-n0008" not in areas and "lon-n0010" not in areas
    assert (again / "made" / "names" / "ids.csv").read_bytes() == ids.read_bytes()
    applied = {row["area_id"]: row for row in draft.rows("made/names/decided.csv")}
    assert {key: row["answer"] for key, row in applied.items()} == said
    assert applied["lon-n0010"]["was"] == "area"


def test_a_run_reads_what_was_decided_and_the_list_of_areas_that_are_kept(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    kept = tmp_path / "kept.csv"
    kept.write_text("area_id\nlon-n0009\n", encoding="utf-8")
    assert draft_run.read_kept(kept) == frozenset({"lon-n0009"})
    status = run(
        tmp_path, tmp_path / "out", "--decided", str(decided(tmp_path)), "--kept", str(kept)
    )
    printed = capsys.readouterr()
    assert status == 0 and printed.err == ""
    counted = json.loads((tmp_path / "out" / "counts.json").read_bytes())
    assert counted["decided_at_the_desk"] == {"area": 1, "drop": 1, "inside": 1}
    # The area on the list, and the one the founder said is an area.
    assert counted["areas_kept_however_small"] == 2


def test_an_area_on_the_kept_list_stands_however_small_it_is(tmp_path: Path):
    small = replace(SETTINGS, of_areas=assign.Rules(smallest=31))
    draft_run.make(given(tmp_path / "a").inputs, tmp_path / "a" / "out", settings=small)
    kept = replace(small, of_areas=assign.Rules(smallest=31, kept=frozenset({"lon-n0010"})))
    draft_run.make(given(tmp_path / "b").inputs, tmp_path / "b" / "out", settings=kept)

    def areas(folder: Path) -> set[str]:
        rows = (folder / "out" / "areas.csv").read_text(encoding="utf-8").splitlines()[1:]
        return {row.split(",")[0] for row in rows}

    assert "lon-n0010" not in areas(tmp_path / "a")
    assert "lon-n0010" in areas(tmp_path / "b")


@pytest.mark.parametrize(
    ("text", "said"),
    [
        ("item,reviewer,answer\nn:lon-n9999,r1,drop\n", "does not hold"),
        ("item,reviewer,answer\nn:lon-n0010,r1,drop\nn:lon-n0010,r1,inside\n", "twice"),
        ("item,answer\nn:lon-n0010,drop\n", "columns"),
        ("area_id,answer\nlon-n0010,away\n", "answer"),
    ],
)
def test_a_run_stops_at_a_file_of_decisions_it_cannot_apply(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], text: str, said: str
):
    status = run(tmp_path, tmp_path / "out", "--decided", str(decided(tmp_path, text)))
    printed = capsys.readouterr()
    assert status == 2 and said in printed.err
    assert "lon-n" not in printed.err and "lon-n" not in printed.out
    assert not (tmp_path / "out" / "areas.csv").exists()


def test_a_name_may_be_made_an_area_by_hand_under_its_own_id(tmp_path: Path):
    """The desk cannot make another name an area. A person writes the id of the place."""
    by_hand = decided(tmp_path, "area_id,answer\nlon-n0004,area\n")
    said = draft_run.read_decided(by_hand)
    draft_run.make(
        given(tmp_path).inputs, tmp_path / "out", settings=replace(SETTINGS, decided=said)
    )
    rows = (tmp_path / "out" / "areas.csv").read_text(encoding="utf-8")
    assert "lon-n0004,eskerfold,Eskerfold," in rows
