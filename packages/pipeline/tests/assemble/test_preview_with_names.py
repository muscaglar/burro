"""The step `preview`, given a draft of names, on the whole of a made-up build.

The town is Quillhaven and Tallowgate, which do not exist. The draft is made
up too: its names are names of the made-up city of the synthetic release, and
it gives the town's output areas to neighbourhoods of those names.
"""

import csv
import io
import json
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any

import pytest
from burro_core.facts import facts_for
from burro_core.ids import FactKind, NameState, Part
from burro_core.places import Names
from burro_pipeline.assemble import cli as assemble
from burro_pipeline.assemble import names
from burro_pipeline.evidence.lock import InputKind, Lock
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.served import unevidenced
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.registry import load
from burro_pipeline.registry.model import Use
from burro_pipeline.release.read import read_release, read_served
from public_log import is_public

from . import names_support as drafts
from .support import ONE, REGISTRY, RELEASE, THREE, TWO, File, Made, files, made

Printed = pytest.CaptureFixture[str]
LOOKUP, OUTLINES = "ons-oa21-lsoa21-msoa21-lad22-lookup", "ons-output-areas-2021"
# The centres of output areas: a build that names places to reach says where the homes of
# each area stand, so the file stands behind every area too.
HOMES_AT = "ons-oa-pwc-2021"
# The made-up file of place names, as the list of a build names it.
PLACE_NAMES = File(
    "place-names",
    drafts.PLACES,
    Use.GAZETTEER,
    "opname_csv_gb.zip",
    "2026-07",
    "2026-07",
    drafts.NAMES_FILE,
)


def read(path: Path) -> Any:
    return json.loads(path.read_bytes())


def drafted(build: Made, **changes: Any) -> Path:
    """A made-up draft in a folder, which says it read the files of the build."""
    read_from = {
        drafts.PLACES: PLACE_NAMES.sha256,
        drafts.CENTRES: files()["town-centres"].sha256,
    }
    folder = build.folder / "draft"
    folder.mkdir(exist_ok=True)
    for name, content in drafts.files(read_from=read_from, **changes).items():
        (folder / name).write_bytes(content)
    # A draft holds other files, which a build does not read.
    (folder / "about.txt").write_text("Made up for a test.", encoding="utf-8")
    return folder


def with_names(folder: Path, **changes: Any) -> tuple[Made, Path]:
    """The made-up build with the file of place names among its files, and a draft of names."""
    build = made(folder, changed={PLACE_NAMES.item: PLACE_NAMES})
    return build, drafted(build, **changes)


@pytest.fixture(scope="module")
def build(tmp_path_factory: pytest.TempPathFactory) -> Made:
    """The made-up build with names, built once for every test that only reads it."""
    found, draft = with_names(tmp_path_factory.mktemp("named"))
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        assert found.run("--names", str(draft)) == 0
    return found


def areas_of(build: Made) -> dict[str, Any]:
    return {area.area_id: area for area in read_release(build.release).neighbourhoods}


def test_each_area_bears_the_name_of_its_neighbourhood_with_its_label_beside_it(build: Made):
    found = areas_of(build)
    assert {area: row.name for area, row in found.items()} == {
        ONE: "Alderwick, west",
        TWO: "Alderwick, east",
        THREE: "Eskerfold",
    }
    assert {area: row.named.label for area, row in found.items()} == {
        ONE: "Quillhaven 001",
        TWO: "Quillhaven 002",
        THREE: "Tallowgate 001",
    }
    assert found[ONE].aliases == ("Alderwick",)
    assert found[THREE].aliases == ()
    # The id and the slug of an area are made from its label, so neither moves with a name.
    assert [row.slug for row in found.values()] == [
        "quillhaven-001",
        "quillhaven-002",
        "tallowgate-001",
    ]


def test_every_name_says_who_wrote_it_and_that_no_person_has_checked_it(build: Made):
    found = areas_of(build)
    assert found[ONE].named.source_ids == (drafts.CENTRES, drafts.PLACES)
    assert found[THREE].named.source_ids == (drafts.PLACES,)
    assert {row.named.state for row in found.values()} == {NameState.DRAFT}
    release = read_release(build.release)
    fact = next(f for f in facts_for(release, ONE, None) if f.kind is FactKind.AREA)
    registry = load(REGISTRY)
    publishers = [registry.get(source).publisher for source in (drafts.CENTRES, drafts.PLACES)]
    assert fact.slots["written_by"] == " and ".join(publishers)
    assert (fact.slots["label"], fact.slots["state"]) == ("Quillhaven 001", "draft")


def test_the_file_of_areas_cites_every_source_that_writes_a_name_and_is_dated_by_the_newest(
    build: Made,
):
    origin = read_release(build.release).origin(Part.NEIGHBOURHOODS)
    assert origin.source_ids == tuple(
        sorted((drafts.CENTRES, HOMES_AT, LOOKUP, OUTLINES, drafts.PLACES))
    )
    # The names are of July 2026, and the lookup of December 2022.
    assert origin.as_of == "2026-07"
    credited = {source.source_id for source in read_release(build.release).manifest.sources}
    assert {drafts.CENTRES, drafts.PLACES} <= credited


def test_a_search_by_name_finds_every_area_that_bears_it(build: Made):
    found = Names(read_release(build.release)).search_areas("alderwick", 8)
    assert [(match.id, match.score) for match in found] == [(TWO, 1.0), (ONE, 1.0)]
    assert [match.name for match in found] == ["Alderwick, east", "Alderwick, west"]


def test_every_fact_of_the_release_has_evidence_behind_it_and_the_name_rests_on_its_files(
    build: Made,
):
    release = read_served(build.release)
    evidence = Evidence.model_validate_json((build.beside / "evidence.json").read_bytes())
    lock = Lock.model_validate_json((build.beside / "lock.json").read_bytes())
    assert unevidenced(release, evidence, lock, load(REGISTRY)) == ()
    behind = {area: evidence.row(f"{area}/area/name") for area in (ONE, TWO, THREE)}
    assert all(row is not None for row in behind.values())
    rows = {area: row for area, row in behind.items() if row is not None}
    assert {row.derivation_id for row in rows.values()} == {names.NAMED.derivation_id}
    sources = {
        receipt.source_id
        for file_id in rows[THREE].inputs
        if (receipt := evidence.receipt(file_id)) is not None
    }
    assert sources == {drafts.CENTRES, HOMES_AT, LOOKUP, OUTLINES, drafts.PLACES}
    # How much of an area lies in the neighbourhood whose name it bears.
    assert (rows[ONE].units_used, rows[ONE].units_expected) == (4, 4)
    assert (rows[TWO].units_used, rows[TWO].units_expected) == (2, 4)
    assert (rows[THREE].units_used, rows[THREE].units_expected) == (3, 4)
    assert [rows[area].state for area in (ONE, TWO, THREE)] == [
        State.PRESENT,
        State.PARTIAL,
        State.PARTIAL,
    ]
    assert names.NAMED.derivation_id in {method.derivation_id for method in evidence.methods}


def test_the_lock_names_the_files_of_the_draft_by_their_hashes(build: Made):
    lock = Lock.model_validate_json((build.beside / "lock.json").read_bytes())
    held = {given.name: given for given in lock.inputs if given.kind is InputKind.GAZETTEER}
    assert sorted(held) == [
        "gazetteer/areas.csv",
        "gazetteer/name_evidence.csv",
        "gazetteer/oa_to_area.csv",
    ]
    for name, content in names.files_of(build.folder / "draft").items():
        assert lock.admit(content).name == f"gazetteer/{name}"
    assert lock.holds(PLACE_NAMES.receipt().file_id)


def test_the_build_says_what_its_names_come_to_and_writes_a_table_of_them(build: Made):
    said = read(build.beside / "build.json")["names"]
    assert said["method"] == names.NAMED.derivation_id
    assert said["source_ids"] == [drafts.CENTRES, drafts.PLACES]
    assert (said["areas"], said["areas_that_bear_a_name"], said["names"]) == (3, 3, 2)
    assert said["names_borne_by_two_areas_or_more"] == 1
    assert not any(name in json.dumps(said) for name in ("Alderwick", "Eskerfold"))
    with (build.beside / "names.csv").open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    assert [(row["label"], row["name"], row["state"]) for row in rows] == [
        ("Quillhaven 001", "Alderwick, west", "draft"),
        ("Quillhaven 002", "Alderwick, east", "draft"),
        ("Tallowgate 001", "Eskerfold", "draft"),
    ]
    assert rows[0]["source_ids"] == f"{drafts.CENTRES}; {drafts.PLACES}"
    assert (rows[1]["output_areas_in_it"], rows[1]["output_areas"]) == ("2", "4")
    # A release folder holds the files of the release and nothing else.
    assert not (build.release / "names.csv").exists()


def test_the_step_prints_one_line_of_names_which_names_no_area(tmp_path: Path, capsys: Printed):
    found, draft = with_names(tmp_path)
    assert found.run("--names", str(draft)) == 0
    out = capsys.readouterr()
    said = out.out.splitlines()
    assert all(is_public(line) for line in said)
    assert said[2] == f"step=names status=ok release={RELEASE} areas=3 named=3 files=2"
    for name in ("Alderwick", "Eskerfold", "Foxholt", "Quillhaven 001"):
        assert name not in out.out
        assert name not in out.err


def test_built_twice_from_the_same_draft_it_writes_the_same_bytes(tmp_path: Path, build: Made):
    again, draft = with_names(tmp_path)
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        assert again.run("--names", str(draft)) == 0
    for folder in (again.release, again.beside):
        for path in sorted(folder.iterdir()):
            first = (build.out / folder.name / path.name).read_bytes()
            assert path.read_bytes() == first, path.name


def test_a_name_a_person_decided_at_the_desk_is_served_as_checked(tmp_path: Path):
    chosen = (
        drafts.Wrote(drafts.ESKERFOLD, drafts.PLACES, "Eskerfold", chosen_by=drafts.FOUNDER),
        *(row for row in drafts.EVIDENCE if row.place_id != drafts.ESKERFOLD),
    )
    found, draft = with_names(tmp_path, evidence=chosen)
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        assert found.run("--names", str(draft)) == 0
    served = areas_of(found)
    assert served[THREE].named.state is NameState.CHECKED
    assert served[ONE].named.state is NameState.DRAFT
    assert read(found.beside / "build.json")["names"]["names_a_person_has_checked"] == 1


def test_an_area_that_lies_in_no_named_neighbourhood_keeps_its_label(tmp_path: Path):
    nowhere = {**drafts.GIVEN, **dict.fromkeys((5, 6, 7, 8), drafts.NO_NAME)}
    found, draft = with_names(tmp_path, given=nowhere)
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        assert found.run("--names", str(draft)) == 0
    served = areas_of(found)
    assert (served[TWO].name, served[TWO].named, served[TWO].aliases) == (
        "Quillhaven 002",
        None,
        (),
    )
    assert served[ONE].name == "Alderwick"
    release = read_served(found.release)
    evidence = Evidence.model_validate_json((found.beside / "evidence.json").read_bytes())
    lock = Lock.model_validate_json((found.beside / "lock.json").read_bytes())
    assert unevidenced(release, evidence, lock, load(REGISTRY)) == ()


def test_with_no_draft_every_area_is_under_its_label_as_before(tmp_path: Path):
    found = made(tmp_path, changed={PLACE_NAMES.item: PLACE_NAMES})
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        assert found.run() == 0
    served = areas_of(found)
    assert [row.name for row in served.values()] == [
        "Quillhaven 001",
        "Quillhaven 002",
        "Tallowgate 001",
    ]
    assert all(row.named is None and row.aliases == () for row in served.values())
    origin = read_release(found.release).origin(Part.NEIGHBOURHOODS)
    assert (origin.source_ids, origin.as_of) == ((HOMES_AT, LOOKUP, OUTLINES), "2022-12")
    assert "names" not in read(found.beside / "build.json")
    assert not (found.beside / "names.csv").exists()
    lock = Lock.model_validate_json((found.beside / "lock.json").read_bytes())
    assert all(given.kind is InputKind.PUBLISHER_FILE for given in lock.inputs)


def test_no_figure_of_a_build_moves_when_its_areas_bear_names(tmp_path: Path, build: Made):
    # Ranking is a function of the figures of a release. A name is no figure: the files that
    # hold the figures are the same bytes with a draft of names and with none.
    plain = made(tmp_path, changed={PLACE_NAMES.item: PLACE_NAMES})
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        assert plain.run() == 0
    moved = [
        path.name
        for path in sorted(plain.release.iterdir())
        if path.read_bytes() != (build.release / path.name).read_bytes()
    ]
    assert moved == ["manifest.json", "neighbourhoods.json"]
    assert sorted(path.name for path in build.release.iterdir()) == sorted(
        path.name for path in plain.release.iterdir()
    )


@pytest.mark.parametrize(
    ("file", "holds", "why"),
    [
        (names.EVIDENCE, None, names.UNREADABLE),
        (names.AREAS, b"area_id\nlon-n0001\n", names.LACKS_A_COLUMN),
        (names.GIVEN, b"", names.UNREADABLE),
    ],
)
def test_a_draft_that_cannot_be_read_stops_the_build_and_nothing_is_written(
    tmp_path: Path, capsys: Printed, file: str, holds: bytes | None, why: str
):
    found, draft = with_names(tmp_path)
    if holds is None:
        (draft / file).unlink()
    else:
        (draft / file).write_bytes(holds)
    assert found.run("--names", str(draft)) == 2
    out = capsys.readouterr()
    assert out.out.splitlines() == ["step=assemble status=unreadable"]
    assert why in out.err
    assert "Alderwick" not in out.err
    assert not found.out.exists()


def test_a_draft_made_from_a_file_that_is_no_file_of_the_build_stops_the_build(
    tmp_path: Path, capsys: Printed
):
    # The build holds no file of place names: its list does not name one.
    found = made(tmp_path)
    draft = drafted(found)
    assert found.run("--names", str(draft)) == 2
    out = capsys.readouterr()
    assert out.out.splitlines()[-1] == "step=assemble status=unreadable"
    assert names.NOT_IN_THE_BUILD in out.err
    assert not found.out.exists()


def test_the_step_takes_a_draft_through_the_pipelines_one_command_line():
    args = assemble.parsed(
        [
            "preview",
            *("--release-id", RELEASE),
            *("--built-at", "2026-09-23T00:00:00Z"),
            *("--out", "data/releases"),
            *("--names", "scratch/draft"),
        ]
    )
    assert args.names == Path("scratch/draft")
    assert (
        assemble.parsed(["preview", "--release-id", RELEASE, "--built-at", "x", "--out", "y"]).names
        is None
    )
