"""Two builds of one release must give one manifest. Every release here is made up."""

import hashlib
import io
import json
from pathlib import Path

import pytest
from public_log import is_public
from same_manifest import compare, hash_release

RELEASE_ID = "syn-2026-09-23-01"
FILES = {"places.json": b'{"places":[]}\n', "travel.json": b'{"rows":[]}\n'}


def release(folder: Path, files: dict[str, bytes] | None = None) -> Path:
    """A made-up release in a folder of its own, with a manifest that is true of it."""
    files = FILES if files is None else files
    target = folder / RELEASE_ID
    target.mkdir(parents=True)
    listed = [
        {"name": name, "sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)}
        for name, content in sorted(files.items())
    ]
    for name, content in files.items():
        (target / name).write_bytes(content)
    manifest = {"release_id": RELEASE_ID, "files": listed}
    (target / "manifest.json").write_text(json.dumps(manifest, sort_keys=True) + "\n")
    return folder


def hashed(folder: Path, copy: str = "a") -> tuple[int, str, str]:
    out, outputs = io.StringIO(), io.StringIO()
    status = hash_release(folder, copy, out, outputs)
    return status, out.getvalue(), outputs.getvalue()


def compared(a: str, b: str) -> tuple[int, str, str]:
    out, summary = io.StringIO(), io.StringIO()
    status = compare(a, b, out, summary)
    return status, out.getvalue(), summary.getvalue()


def output_of(folder: Path, copy: str = "a") -> str:
    status, _, outputs = hashed(folder, copy)
    assert status == 0
    return outputs.removeprefix(f"{copy}=").strip()


# The hash of one build


def test_the_hash_of_a_build_is_the_hash_of_its_manifest(tmp_path: Path):
    folder = release(tmp_path)
    status, out, outputs = hashed(folder)
    manifest = hashlib.sha256((folder / RELEASE_ID / "manifest.json").read_bytes()).hexdigest()
    assert status == 0
    assert out == (
        f"step=manifest status=ok copy=a release={RELEASE_ID} files=2 bytes=26 "
        f"manifest_sha256={manifest}\n"
    )
    assert json.loads(outputs.removeprefix("a=")) == {
        "manifest": manifest,
        "files": {name: hashlib.sha256(content).hexdigest() for name, content in FILES.items()},
    }


def test_the_output_is_one_line_named_for_the_copy(tmp_path: Path):
    _, _, outputs = hashed(release(tmp_path), "b")
    assert outputs.startswith("b={") and outputs.count("\n") == 1 and outputs.endswith("\n")


def test_a_file_that_is_not_what_the_manifest_says_fails(tmp_path: Path):
    folder = release(tmp_path)
    (folder / RELEASE_ID / "places.json").write_bytes(b'{"places":["made-up row"]}\n')
    status, out, outputs = hashed(folder)
    assert status == 1
    assert out == "step=manifest status=failed copy=a file=places.json\n"
    assert outputs == ""


def test_a_file_the_manifest_names_and_the_folder_lacks_fails(tmp_path: Path):
    folder = release(tmp_path)
    (folder / RELEASE_ID / "travel.json").unlink()
    assert hashed(folder)[:2] == (1, "step=manifest status=failed copy=a file=travel.json\n")


def test_a_file_the_manifest_does_not_name_fails_and_is_not_named(tmp_path: Path):
    folder = release(tmp_path)
    (folder / RELEASE_ID / "made-up-row.csv").write_bytes(b"made-up row\n")
    status, out, _ = hashed(folder)
    assert status == 1
    assert "made-up" not in out
    assert out == "step=manifest status=failed copy=a unlisted=1\n"


@pytest.mark.parametrize("name", ["../outside.json", "/etc/passwd", "sub/places.json", ""])
def test_a_manifest_that_names_a_file_outside_the_release_fails(tmp_path: Path, name: str):
    folder = release(tmp_path)
    manifest = folder / RELEASE_ID / "manifest.json"
    document = json.loads(manifest.read_text())
    document["files"][0]["name"] = name
    manifest.write_text(json.dumps(document))
    status, out, _ = hashed(folder)
    assert status == 1
    assert out == "step=manifest status=unreadable copy=a\n"


@pytest.mark.parametrize("content", [b"", b"not json", b"[]", b'{"files": "none"}', b"\xff"])
def test_a_manifest_that_cannot_be_read_fails(tmp_path: Path, content: bytes):
    folder = release(tmp_path)
    (folder / RELEASE_ID / "manifest.json").write_bytes(content)
    assert hashed(folder)[:2] == (1, "step=manifest status=unreadable copy=a\n")


def test_a_folder_must_hold_one_release_and_no_more(tmp_path: Path):
    assert hashed(tmp_path)[:2] == (1, "step=manifest status=missing copy=a\n")
    release(tmp_path)
    (tmp_path / "syn-2026-09-23-02").mkdir()
    assert hashed(tmp_path)[:2] == (1, "step=manifest status=missing copy=a\n")


def test_a_copy_is_a_or_b(tmp_path: Path):
    status, out, outputs = hashed(release(tmp_path), "made-up row")
    assert status == 1
    assert "made-up" not in out + outputs


# Two builds, side by side


def test_two_builds_that_agree_pass(tmp_path: Path):
    a, b = output_of(release(tmp_path / "a"), "a"), output_of(release(tmp_path / "b"), "b")
    status, out, summary = compared(a, b)
    manifest = json.loads(a)["manifest"]
    assert status == 0
    assert out == f"step=compare status=ok files=2 differing=0 manifest_sha256={manifest}\n"
    assert manifest in summary and "one manifest" in summary


def test_two_builds_that_differ_fail_and_say_which_file(tmp_path: Path):
    other = FILES | {"travel.json": b'{"rows":[1]}\n'}
    a, b = output_of(release(tmp_path / "a")), output_of(release(tmp_path / "b", other))
    status, out, summary = compared(a, b)
    assert status == 1
    assert out == (
        "step=compare status=differs file=travel.json\n"
        "step=compare status=differs files=2 differing=1\n"
    )
    assert "travel.json" in summary and "differ" in summary


def test_a_file_that_only_one_build_wrote_is_a_difference(tmp_path: Path):
    fewer = {"places.json": FILES["places.json"]}
    a, b = output_of(release(tmp_path / "a")), output_of(release(tmp_path / "b", fewer))
    status, out, _ = compared(a, b)
    assert status == 1
    assert "step=compare status=differs file=travel.json\n" in out


def test_files_that_agree_under_manifests_that_differ_is_a_difference(tmp_path: Path):
    a = output_of(release(tmp_path / "a"))
    b = json.dumps(json.loads(a) | {"manifest": "0" * 64})
    status, out, _ = compared(a, b)
    assert status == 1
    assert out == (
        "step=compare status=differs file=manifest.json\n"
        "step=compare status=differs files=2 differing=1\n"
    )


@pytest.mark.parametrize(
    "missing",
    ["", "not json", "[]", "{}", '{"manifest": "made-up row", "files": {}}', '{"manifest": 1}'],
)
def test_a_build_that_gave_no_manifest_fails(tmp_path: Path, missing: str):
    a = output_of(release(tmp_path))
    for pair in ((a, missing), (missing, a)):
        status, out, summary = compared(*pair)
        assert status == 1
        assert out == "step=compare status=missing\n"
        assert "made-up" not in out + summary


def test_a_file_name_that_is_not_a_release_file_is_never_shown(tmp_path: Path):
    a = output_of(release(tmp_path))
    document = json.loads(a)
    document["files"]["made-up row.csv"] = "0" * 64
    status, out, summary = compared(a, json.dumps(document))
    assert status == 1
    assert "made-up" not in out + summary
    assert "step=compare status=differs files=3 differing=1\n" in out


# What is printed


def test_every_line_printed_is_one_the_public_log_would_show(tmp_path: Path):
    other = FILES | {"travel.json": b'{"rows":[1]}\n'}
    a, b = output_of(release(tmp_path / "a")), output_of(release(tmp_path / "b", other))
    (tmp_path / "a" / RELEASE_ID / "places.json").write_bytes(b"changed\n")
    printed = (
        hashed(tmp_path / "b")[1]
        + hashed(tmp_path / "a")[1]
        + compared(a, a)[1]
        + compared(a, b)[1]
        + compared(a, "")[1]
    )
    assert printed
    assert all(is_public(line) for line in printed.splitlines())


def test_the_synthetic_release_of_this_repository_is_what_its_manifest_says():
    fixture = Path(__file__).resolve().parents[2] / "data" / "fixtures" / "synthetic"
    status, out, _ = hashed(fixture)
    assert status == 0
    assert out.startswith("step=manifest status=ok copy=a release=syn-")
