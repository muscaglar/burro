"""Writing a release to disk and reading it back, and the licence gate that stands in between."""

import dataclasses
import hashlib
import json
import re
from datetime import date
from functools import cache
from pathlib import Path
from typing import Any

import pytest
from burro_core.release import (
    DATA_FILES,
    MANIFEST,
    NEIGHBOURHOODS,
    RULES,
    InMemoryRelease,
    ReleaseError,
    parse_release,
)
from burro_pipeline.registry import (
    CommercialUse,
    Dimension,
    Licence,
    Registry,
    RegistryError,
    Source,
    Status,
    Use,
    VerifiedHow,
    check,
)
from burro_pipeline.release import (
    UnreadableRelease,
    build_synthetic,
    canonical_json,
    read_release,
    write_release,
)
from burro_pipeline.release.cli import main
from burro_pipeline.release.read import IGNORED, MEANING
from burro_pipeline.release.synthetic import RELEASE_ID
from burro_pipeline.release.write import packed

REAL_ID = "lon-2026-09-23-01"
# A string found nowhere else. If a refusal repeats what a file says, this shows up in it.
CANARY = "Zzyzx Parva"


@cache
def synthetic() -> InMemoryRelease:
    return build_synthetic()


def written(tmp_path: Path) -> Path:
    write_release(synthetic(), tmp_path)
    return tmp_path / RELEASE_ID


@cache
def files() -> dict[str, bytes]:
    return packed(synthetic())


def on_disk(tmp_path: Path) -> Path:
    """A folder that holds the synthetic release, for a test of what is read from one.

    The writer checks a release against every rule before it writes, which is
    most of what writing costs, and a test of the reader needs only the bytes.
    They are the bytes the writer writes: a test below holds them to it.
    """
    folder = tmp_path / RELEASE_ID
    folder.mkdir(parents=True)
    for name, content in files().items():
        (folder / name).write_bytes(content)
    return folder


def refusal(folder: Path) -> UnreadableRelease:
    with pytest.raises(UnreadableRelease) as caught:
        read_release(folder)
    return caught.value


def put(folder: Path, name: str, content: bytes) -> None:
    """Change a file and bring the manifest into line, so that the checksum is not what fails."""
    (folder / name).write_bytes(content)
    manifest = json.loads((folder / MANIFEST).read_bytes())
    for entry in manifest["files"]:
        if entry["name"] == name:
            entry.update(sha256=hashlib.sha256(content).hexdigest(), bytes=len(content))
    (folder / MANIFEST).write_bytes(canonical_json(manifest))


def changed(folder: Path, name: str, change: Any) -> None:
    document = json.loads((folder / name).read_bytes())
    change(document)
    put(folder, name, canonical_json(document))


def test_written_release_reads_back_the_same(tmp_path: Path):
    as_written = write_release(synthetic(), tmp_path)
    read = read_release(tmp_path / RELEASE_ID)
    assert read == as_written
    # And the folder the tests of the reader are given holds what the writer wrote.
    wrote = {file.name: file.read_bytes() for file in (tmp_path / RELEASE_ID).iterdir()}
    given = on_disk(tmp_path / "given")
    assert {file.name: file.read_bytes() for file in given.iterdir()} == wrote
    # All that writing adds to what was built is the manifest's list of files.
    assert dataclasses.replace(read, manifest=synthetic().manifest) == synthetic()
    assert {entry.name for entry in read.manifest.files} == set(DATA_FILES)


def test_a_release_gets_a_folder_named_for_its_id_holding_its_files_and_nothing_else(
    tmp_path: Path,
):
    folder = written(tmp_path)
    assert [entry.name for entry in tmp_path.iterdir()] == [RELEASE_ID]
    assert {entry.name for entry in folder.iterdir()} == {*DATA_FILES, MANIFEST}


def test_every_file_is_written_as_canonical_json(tmp_path: Path):
    for file in written(tmp_path).iterdir():
        content = file.read_bytes()
        text = content.decode("utf-8")
        assert content == canonical_json(json.loads(text)), file.name
        assert text.endswith("}\n") and "\n" not in text[:-1], file.name
        # No float carries more than six decimals.
        assert not re.search(r"\d\.\d{7,}", text), file.name


def test_the_manifest_holds_the_checksum_and_length_of_every_other_file(tmp_path: Path):
    folder = written(tmp_path)
    manifest = json.loads((folder / MANIFEST).read_bytes())
    assert [entry["name"] for entry in manifest["files"]] == sorted(DATA_FILES)
    for entry in manifest["files"]:
        content = (folder / entry["name"]).read_bytes()
        assert entry["sha256"] == hashlib.sha256(content).hexdigest()
        assert entry["bytes"] == len(content)


def test_the_manifest_counts_what_was_written_and_not_what_the_builder_claimed(tmp_path: Path):
    none = synthetic().manifest.counts.replace(neighbourhoods=0, rankable=0, stations=0)
    lying = dataclasses.replace(synthetic(), manifest=synthetic().manifest.replace(counts=none))
    assert write_release(lying, tmp_path).manifest.counts == synthetic().manifest.counts


@pytest.mark.parametrize("name", [MANIFEST, *DATA_FILES])
def test_a_missing_file_is_refused_in_one_readable_line(tmp_path: Path, name: str):
    folder = on_disk(tmp_path)
    (folder / name).unlink()
    error = refusal(folder)
    assert (error.file, error.rule) == (name, "files_match_manifest")
    assert str(error) == f"{folder}: {name} is missing [files_match_manifest]"


def test_a_changed_file_is_refused_in_one_readable_line(tmp_path: Path):
    folder = on_disk(tmp_path)
    content = (folder / "cost.json").read_bytes()
    (folder / "cost.json").write_bytes(content.replace(b"1", b"2", 1))
    error = refusal(folder)
    assert (error.file, error.rule) == ("cost.json", "files_match_manifest")
    assert "cost.json is not the file the manifest lists: it has changed" in str(error)
    assert "\n" not in str(error)


def test_a_file_that_does_not_belong_is_refused(tmp_path: Path):
    folder = on_disk(tmp_path)
    (folder / "notes.txt").write_text("not part of any release")
    assert refusal(folder).file == "notes.txt"
    (folder / "notes.txt").unlink()
    (folder / "old").mkdir()
    assert (refusal(folder).file, refusal(folder).rule) == ("old", "file_is_readable")


def test_a_file_the_finder_leaves_behind_is_ignored(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    as_written = write_release(synthetic(), tmp_path)
    folder = tmp_path / RELEASE_ID
    # What a Mac leaves in any folder that has been opened in a window. It is not JSON,
    # and if it were read as part of the release that is what the refusal would say.
    (folder / IGNORED).write_bytes(b"\x00\x00\x00\x01Bud1" + CANARY.encode())
    assert IGNORED == ".DS_Store"
    assert read_release(folder) == as_written
    assert main(["check", str(folder)]) == 0
    assert capsys.readouterr().err == ""
    # It was left where it was: a reader changes nothing.
    assert (folder / IGNORED).exists()


def test_a_release_with_a_file_missing_is_refused_whatever_the_finder_left(tmp_path: Path):
    folder = on_disk(tmp_path)
    (folder / IGNORED).write_bytes(b"")
    (folder / "cost.json").unlink()
    assert (refusal(folder).file, refusal(folder).rule) == ("cost.json", "files_match_manifest")


STRAY = [
    ".ds_store",  # the name is taken as it is spelt
    ".DS_Store.json",
    ".DS_Store ",
    "DS_Store",
    "._.DS_Store",
    "._manifest.json",
    ".localized",
    ".gitkeep",
    ".hidden",
    "Thumbs.db",
    "desktop.ini",
    "notes.txt",
    "manifest.json.bak",
]


@pytest.mark.parametrize("name", STRAY)
def test_every_other_stray_file_is_still_refused(tmp_path: Path, name: str):
    folder = on_disk(tmp_path)
    (folder / name).write_bytes(b"")
    error = refusal(folder)
    assert (error.file, error.rule) == (name, "files_match_manifest")
    assert str(error).startswith(f"{folder}: {name} is not the file the manifest lists")


def test_a_folder_by_the_name_of_the_file_the_finder_leaves_is_refused(tmp_path: Path):
    # Only a file is left out. A folder of that name is nothing the Finder made.
    folder = on_disk(tmp_path)
    (folder / IGNORED).mkdir()
    assert (refusal(folder).file, refusal(folder).rule) == (IGNORED, "file_is_readable")


def not_json(folder: Path) -> None:
    put(folder, "travel.json", b'{"area_ids": [' + CANARY.encode())


def manifest_cut_short(folder: Path) -> None:
    content = (folder / MANIFEST).read_bytes()
    (folder / MANIFEST).write_bytes(content[: len(content) // 2])


def unknown_field(folder: Path) -> None:
    def add(document: dict[str, Any]) -> None:
        document["rows"][3][CANARY] = 1

    changed(folder, "features.json", add)


def field_left_out(folder: Path) -> None:
    def leave_out(document: dict[str, Any]) -> None:
        del document["rows"][3]["coverage"]

    changed(folder, "features.json", leave_out)


def wrong_type(folder: Path) -> None:
    def retype(document: dict[str, Any]) -> None:
        document["places"][5]["centroid"] = CANARY

    changed(folder, "places.json", retype)


def number_out_of_range(folder: Path) -> None:
    def overshoot(document: dict[str, Any]) -> None:
        document["rows"][7]["percentile"] = 100.5

    changed(folder, "features.json", overshoot)


def unknown_area(folder: Path) -> None:
    def rename(document: dict[str, Any]) -> None:
        document["rows"][0]["area_id"] = "syn-n9999"

    changed(folder, "cost.json", rename)


def percentile_moved(folder: Path) -> None:
    def move(document: dict[str, Any]) -> None:
        row = document["rows"][7]
        row["percentile"] = 40.0 if row["percentile"] == 50.0 else 50.0

    changed(folder, "features.json", move)


def more_of_a_recipe_claimed(folder: Path) -> None:
    def claim(document: dict[str, Any]) -> None:
        # Food and drink, of which no release holds every part yet.
        assert document["rows"][4]["tag_id"] == "foodie" and document["rows"][4]["coverage"] < 1
        document["rows"][4]["coverage"] = 1.0

    changed(folder, "tags.json", claim)


def score_moved(folder: Path) -> None:
    def move(document: dict[str, Any]) -> None:
        row = document["rows"][3]
        row["score"] = 40.0 if row["score"] == 50.0 else 50.0

    changed(folder, "tags.json", move)


MALFORMED = [
    (not_json, "travel.json", "json_is_valid", "travel.json is not valid JSON"),
    (manifest_cut_short, MANIFEST, "json_is_valid", "manifest.json is not valid JSON"),
    (unknown_field, "features.json", "shape_is_valid", "features.json, at rows[3], is not shaped"),
    (
        field_left_out,
        "features.json",
        "shape_is_valid",
        "features.json, at rows[3].coverage, is not shaped as the contract says",
    ),
    (wrong_type, "places.json", "shape_is_valid", "places.json, at places[5].centroid, is not"),
    (
        number_out_of_range,
        "features.json",
        "values_are_in_range",
        "features.json, at rows[7].percentile, holds a number outside the range it may take",
    ),
    (
        unknown_area,
        "cost.json",
        "references_resolve",
        "cost.json, at rows[0], names an area, destination, place, station or source that",
    ),
    # What is ranked on never parts from what is shown. A figure that was changed by hand,
    # or worked out wrongly, is refused as plainly as a file that was cut short.
    (
        percentile_moved,
        "features.json",
        "percentiles_match_values",
        "features.json, at rows[7], holds a percentile that is not the one its values give",
    ),
    (
        more_of_a_recipe_claimed,
        "tags.json",
        "raw_matches_recipe",
        "tags.json, at rows[4], places an area on a vibe by figures that are not the ones the "
        "release holds for it, or says more of the recipe was there than was",
    ),
    (
        score_moved,
        "tags.json",
        "scores_match_raw",
        "tags.json, at rows[3], holds a score for a vibe that is not the one its raw values give",
    ),
]


@pytest.mark.parametrize(
    ("spoil", "file", "rule", "says"), MALFORMED, ids=[case[0].__name__ for case in MALFORMED]
)
def test_a_malformed_file_is_refused_in_one_readable_line(
    tmp_path: Path, spoil: Any, file: str, rule: str, says: str
):
    folder = on_disk(tmp_path)
    spoil(folder)
    error = refusal(folder)
    assert (error.file, error.rule) == (file, rule)
    line = str(error)
    assert line.startswith(f"{folder}: {says}"), line
    assert line.endswith(f"[{rule}]")
    assert "\n" not in line
    # Where and why, and never what the file said.
    assert CANARY not in line
    assert CANARY not in repr(error)


def test_a_folder_that_is_not_there_is_refused_in_one_readable_line(tmp_path: Path):
    error = refusal(tmp_path / RELEASE_ID)
    assert str(error) == f"{tmp_path / RELEASE_ID} is not a folder that can be read [{error.rule}]"
    file = tmp_path / "a-file"
    file.write_text("")
    assert refusal(file).rule == "folder_is_readable"


def test_a_release_in_a_folder_of_another_name_is_refused(tmp_path: Path):
    moved = on_disk(tmp_path).rename(tmp_path / "syn-2026-09-24-01")
    error = refusal(moved)
    assert error.rule == "release_id_matches_folder"
    assert "names a release other than the folder it is in" in str(error)


def test_a_release_is_read_by_its_folders_own_name_however_the_path_is_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    folder = on_disk(tmp_path)
    monkeypatch.chdir(folder)
    assert read_release(Path()) == read_release(folder)


def test_every_refusal_core_can_make_has_a_meaning_in_plain_words():
    # The rules of the contract, and the five refusals core adds to them.
    beyond_the_rules = {
        "shape_is_valid",
        "files_are_expected",
        "files_match_manifest",
        "release_id_matches_folder",
        "json_is_valid",
    }
    rules = {getattr(rule, "__name__", "") for rule in RULES}
    when_writing = {
        "real_release_needs_a_registry",
        "release_is_never_overwritten",
        "folder_holds_something_else",
    }
    assert rules | beyond_the_rules | when_writing <= set(MEANING)
    assert all(meaning and meaning[0].islower() for meaning in MEANING.values())


# The licence gate. A real release is made here by renaming the synthetic one,
# which is the only way this build has of making one.

SOURCE_FOR = {
    "neighbourhoods.json": "made-up-gazetteer",
    "catalogue.json": "made-up-survey",
    "cost.json": "made-up-survey",
    "travel.json": "made-up-timetable",
    "stations.json": "made-up-stations",
    "places.json": "made-up-index",
}
USES = {
    "made-up-gazetteer": Use.GAZETTEER,
    "made-up-survey": Use.SCORING,
    "made-up-timetable": Use.ROUTING,
    "made-up-stations": Use.DISPLAY,
    "made-up-index": Use.DESTINATION_SEARCH,
}


def registered(source_id: str, *uses: Use, status: Status = Status.APPROVED) -> Source:
    return Source(
        id=source_id,
        name=source_id,
        publisher="A made-up publisher",
        url="https://example.org/data",
        dimension=Dimension.GEOGRAPHY,
        licence=Licence.OGL_3,
        commercial_use=CommercialUse.YES,
        share_alike=False,
        attribution="Contains made-up data.",
        attribution_verified=True,
        status=status,
        status_reason="" if status is Status.APPROVED else "Its terms have not been read.",
        uses=uses,
        verified_how=VerifiedHow.PRIMARY_SOURCE,
        verified_on=date(2026, 9, 23),
        evidence_urls=("https://example.org/licence",),
    )


def registry(**changes: Source) -> Registry:
    sources = {source_id: registered(source_id, use) for source_id, use in USES.items()}
    found = Registry(tuple((sources | changes).values()))
    assert check(found, date(2026, 9, 23)) == []
    return found


def cite(row: dict[str, Any], source_id: str) -> None:
    key = "source_ids" if "source_ids" in row else "source_id"
    row[key] = [source_id] if key == "source_ids" else source_id


@cache
def renamed() -> str:
    """The synthetic release with real ids, as one text, made once."""
    # Gritty as land use alone: as a scale it holds recorded crime, and no real
    # release may carry it.
    return json.dumps(build_synthetic(gritty_variant="a").documents()).replace("syn-", "lon-")


def real_release(**cited_in: str) -> InMemoryRelease:
    """The synthetic release with real ids, each file citing the source that `SOURCE_FOR` gives.

    `cited_in` changes the source one file cites: `catalogue="made-up-timetable"`.
    """
    return cited(tuple(sorted(cited_in.items())))


@cache
def cited(cited_in: tuple[tuple[str, str], ...]) -> InMemoryRelease:
    sources = SOURCE_FOR | {f"{file}.json": source for file, source in cited_in}
    documents: dict[str, Any] = json.loads(renamed())
    manifest = documents[MANIFEST]
    manifest.update(synthetic=False, city="lon", seed=None)
    manifest["sources"] = [
        manifest["sources"][0] | {"source_id": source_id, "attribution": "Contains made-up data."}
        for source_id in sorted(set(sources.values()))
    ]
    rows = {"catalogue.json": "metrics", "cost.json": "rows", "places.json": "places"}
    for file, source_id in sources.items():
        for row in documents[file][rows[file]] if file in rows else [documents[file]]:
            cite(row, source_id)
    # Who wrote the name of an area is a source of the file of areas.
    for area in documents[NEIGHBOURHOODS]["neighbourhoods"]:
        if area["named"] is not None:
            cite(area["named"], sources[NEIGHBOURHOODS])
    return parse_release(documents)


def test_a_real_release_is_written_when_every_source_is_registered_for_its_use(tmp_path: Path):
    as_written = write_release(real_release(), tmp_path, registry())
    assert as_written.manifest.synthetic is False
    assert read_release(tmp_path / REAL_ID) == as_written


def test_real_release_is_refused_without_a_registry(tmp_path: Path):
    with pytest.raises(ReleaseError) as caught:
        write_release(real_release(), tmp_path)
    assert caught.value.rule == "real_release_needs_a_registry"
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    ("file", "source_id", "use"),
    [
        ("catalogue", "made-up-timetable", "scoring"),
        ("cost", "made-up-stations", "scoring"),
        ("travel", "made-up-survey", "routing"),
        ("stations", "made-up-index", "display"),
        ("places", "made-up-gazetteer", "destination_search"),
        ("neighbourhoods", "made-up-survey", "gazetteer"),
    ],
)
def test_source_must_be_registered_for_the_use_its_file_needs(
    tmp_path: Path, file: str, source_id: str, use: str
):
    # Each source is approved, but for another use than the file that names it needs.
    refused = f"{file}.json: '{source_id}' is not registered for {use}"
    with pytest.raises(RegistryError, match=refused):
        write_release(real_release(**{file: source_id}), tmp_path, registry())
    assert list(tmp_path.iterdir()) == []


def test_a_source_that_is_not_approved_or_not_registered_never_reaches_a_release(tmp_path: Path):
    gated = registered("made-up-survey", Use.SCORING, status=Status.GATED)
    with pytest.raises(RegistryError, match="'made-up-survey' is gated, not approved"):
        write_release(real_release(), tmp_path, registry(**{"made-up-survey": gated}))
    with pytest.raises(RegistryError, match="'made-up-survey' is not in the licence registry"):
        write_release(real_release(), tmp_path, Registry(()))
    assert list(tmp_path.iterdir()) == []


def test_the_synthetic_release_needs_no_registry_and_an_empty_one_does_not_stop_it(tmp_path: Path):
    assert write_release(synthetic(), tmp_path, Registry(())).manifest.synthetic is True


def test_calling_a_release_synthetic_does_not_get_real_sources_past_the_gate(tmp_path: Path):
    real = real_release()
    disguised = dataclasses.replace(real, manifest=real.manifest.replace(synthetic=True))
    with pytest.raises(ReleaseError) as caught:
        write_release(disguised, tmp_path)
    assert caught.value.rule == "synthetic_is_consistent"
    assert list(tmp_path.iterdir()) == []


def test_a_release_that_breaks_a_rule_is_never_written(tmp_path: Path):
    alone = synthetic().neighbourhoods[0].replace(neighbours=())
    lopsided = dataclasses.replace(
        synthetic(), neighbourhoods=(alone, *synthetic().neighbourhoods[1:])
    )
    with pytest.raises(ReleaseError) as caught:
        write_release(lopsided, tmp_path)
    assert caught.value.rule == "neighbours_are_symmetric"
    assert list(tmp_path.iterdir()) == []


def test_a_release_whose_scores_part_from_what_it_shows_is_never_written(tmp_path: Path):
    first, *rest = synthetic().tags
    assert first.score is not None
    parted = dataclasses.replace(
        synthetic(), tags=(first.replace(score=40.0 if first.score == 50.0 else 50.0), *rest)
    )
    with pytest.raises(ReleaseError) as caught:
        write_release(parted, tmp_path)
    assert caught.value.rule == "scores_match_raw"
    assert list(tmp_path.iterdir()) == []


def test_a_real_release_is_never_written_over(tmp_path: Path):
    write_release(real_release(), tmp_path, registry())
    before = (tmp_path / REAL_ID / MANIFEST).read_bytes()
    with pytest.raises(ReleaseError) as caught:
        write_release(real_release(), tmp_path, registry())
    assert caught.value.rule == "release_is_never_overwritten"
    assert (tmp_path / REAL_ID / MANIFEST).read_bytes() == before


def test_the_synthetic_release_is_rebuilt_in_place(tmp_path: Path):
    folder = written(tmp_path)
    (folder / "tags.json").write_bytes(b"{}")
    (folder / "places.json").unlink()
    assert read_release(written(tmp_path)) == write_release(synthetic(), tmp_path)


def test_the_synthetic_release_is_rebuilt_beside_a_file_the_finder_left(tmp_path: Path):
    folder = written(tmp_path)
    (folder / IGNORED).write_bytes(b"Bud1")
    assert read_release(written(tmp_path)) == write_release(synthetic(), tmp_path)
    # It is not the writer's to remove, and it is not written over.
    assert (folder / IGNORED).read_bytes() == b"Bud1"
    assert {entry.name for entry in folder.iterdir()} == {*DATA_FILES, MANIFEST, IGNORED}


def test_a_folder_that_holds_something_else_is_left_as_it_was(tmp_path: Path):
    mine = tmp_path / RELEASE_ID / "thesis.txt"
    mine.parent.mkdir()
    mine.write_text("three years of work")
    with pytest.raises(ReleaseError) as caught:
        write_release(synthetic(), tmp_path)
    assert (caught.value.file, caught.value.rule) == ("thesis.txt", "folder_holds_something_else")
    assert [entry.name for entry in mine.parent.iterdir()] == ["thesis.txt"]
    assert mine.read_text() == "three years of work"


def test_the_command_builds_the_release_and_checks_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    assert main(["build-synthetic", "--out", str(tmp_path)]) == 0
    assert main(["check", str(tmp_path / RELEASE_ID)]) == 0
    built, checked = capsys.readouterr().out.splitlines()
    assert built == checked
    assert built.startswith(f"{RELEASE_ID}: 24 areas (22 rankable), 108 measures, 40 destinations")
    assert built.endswith(", synthetic")


def test_the_command_refuses_a_broken_release_in_one_line(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    folder = on_disk(tmp_path)
    (folder / "geometry.json").unlink()
    assert main(["check", str(folder)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == f"error: {folder}: geometry.json is missing [files_match_manifest]\n"


def test_the_command_refuses_a_release_id_that_is_not_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    assert main(["build-synthetic", "--out", str(tmp_path), "--release-id", "tuesday"]) == 2
    assert capsys.readouterr().err.count("\n") == 1
    # A synthetic release cannot pass itself off as a real one by taking a real id.
    assert main(["build-synthetic", "--out", str(tmp_path), "--release-id", REAL_ID]) == 2
    assert "[synthetic_is_consistent]" in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []
