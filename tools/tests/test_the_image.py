"""The image of the API, held to what it may carry. No image is built here.

An image carries one release. It is the made-up city, as it is committed, or a release
whose lock is committed and whose every byte is as the lock says. The Dockerfile holds
what it carries to that in a stage of its own, which these tests read and then walk:
each thing the stage copies is copied to a folder, and what it runs is run there. So
what is tried here is what a build would do, but for the builder itself.

Every release here is made up.
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from release_lock import APPROVED, lock_of, written

from .test_release_lock import OTHER, RELEASE, built, release_files

ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE = ROOT / "deploy" / "api" / "Dockerfile"
IGNORE = ROOT / "deploy" / "api" / "Dockerfile.dockerignore"
MADE_UP = "syn-2026-09-23-01"
# Where a release of London is taken to before an image is built, from the top of the
# repository. Git ignores it, and the build lets it in.
SERVED = "data/releases/served"


def lines() -> list[str]:
    """The Dockerfile, one instruction to a line, with its comments left out."""
    text = DOCKERFILE.read_text(encoding="utf-8")
    joined = re.sub(r"\s*\\\n\s*", " ", text)
    return [line for line in joined.splitlines() if line and not line.startswith("#")]


def stages() -> dict[str, list[str]]:
    """The instructions of each stage, by its name. The last stage is the image."""
    found: dict[str, list[str]] = {"": []}
    name = ""
    for line in lines():
        if line.startswith("FROM "):
            name = line.partition(" AS ")[2] or "image"
            found[name] = []
        else:
            found[name].append(line)
    return found


def defaults() -> dict[str, str]:
    """What the build is given where whoever builds gives nothing."""
    given = [line.removeprefix("ARG ").partition("=") for line in stages()[""]]
    return {name: value for name, _, value in given}


def let_in() -> list[str]:
    text = IGNORE.read_text(encoding="utf-8")
    return [line.removeprefix("!") for line in text.splitlines() if line.startswith("!")]


def walk(checkout: Path, to: Path, **given: str) -> subprocess.CompletedProcess[str]:
    """Do what the stage that holds a release to its lock does, in a folder of the test's own.

    `checkout` stands for the top of the repository as the build is handed it, and
    `to` for the top of the image. What the stage runs is run with the interpreter
    that runs this test, and what it says is given back.
    """
    args = defaults() | given
    done = subprocess.CompletedProcess[str]([], 0, "", "")
    for line in stages()["release"]:
        for name, value in args.items():
            line = line.replace(f"${{{name}}}", value)
        words = line.split()
        if words[0] == "ARG":
            assert words[1] in args and "=" not in words[1], line
        elif words[0] == "COPY":
            *sources, target = words[1:]
            assert not any(word.startswith("--") for word in sources), line
            for source in sources:
                assert any(source.rstrip("/").startswith(allowed) for allowed in let_in()), source
                found = checkout / source
                assert found.exists(), f"the build would stop: {source} is not in the checkout"
                into = to / target.lstrip("/")
                if found.is_dir():
                    shutil.copytree(found, into, dirs_exist_ok=True)
                else:
                    into.mkdir(parents=True, exist_ok=True)
                    shutil.copy(found, into / found.name)
        else:
            assert words[:2] == ["RUN", "python"], line
            command = line.removeprefix("RUN ").partition(" && ")[0].replace('"', "").split()
            placed = [f"{to}{word}" if word.startswith("/") else word for word in command[1:]]
            done = subprocess.run(
                [sys.executable, *placed], capture_output=True, text=True, check=False
            )
    return done


def a_checkout(folder: Path) -> Path:
    """What a build is handed of this repository: the tools, the locks and the made-up city."""
    for name in ("tools/public_log.py", "tools/release_lock.py"):
        (folder / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / name, folder / name)
    shutil.copytree(ROOT / "data/fixtures/synthetic", folder / "data/fixtures/synthetic")
    (folder / APPROVED).mkdir(parents=True)
    shutil.copy(ROOT / APPROVED / "README.md", folder / APPROVED / "README.md")
    return folder


def taken(checkout: Path, release: str = RELEASE, approved: bool = True) -> Path:
    """A release of London, taken to the checkout as the step `take` would leave it."""
    out = built(checkout / SERVED, release)
    if approved:
        lock = written(lock_of(out, release))
        (checkout / APPROVED / f"{release}.json").write_text(lock, encoding="utf-8")
    return out


# What the Dockerfile says


def test_with_nothing_given_the_image_carries_the_made_up_city_as_it_does_today():
    assert defaults()["RELEASE_ID"] == MADE_UP
    assert defaults()["RELEASE_FROM"] == "data/fixtures/synthetic"
    assert (ROOT / defaults()["RELEASE_FROM"] / defaults()["RELEASE_ID"]).is_dir()
    assert "BURRO_RELEASE_DIR=/srv/burro/release/${RELEASE_ID}" in " ".join(stages()["image"])


def test_nothing_reaches_the_image_from_the_checkout_but_through_the_check():
    copies = [line for line in stages()["image"] if line.startswith(("COPY", "ADD"))]
    assert copies == [
        "COPY --from=build /opt/venv /opt/venv",
        "COPY --from=release /srv/burro/release/ /srv/burro/release/",
    ]
    held = stages()["release"]
    assert [line.split()[0] for line in held] == ["ARG", "ARG", "COPY", "COPY", "COPY", "RUN"]
    assert held[-1].startswith(
        'RUN python /check/release_lock.py carried /srv/burro/release "${RELEASE_ID}" '
        "--approved /check/approved"
    )
    # The release is what the last copy brings, and the locks are copied from where they
    # are committed, whatever folder the release is taken from.
    assert held[3] == f"COPY {APPROVED}/ /check/approved/"
    assert held[4] == "COPY ${RELEASE_FROM}/ /srv/burro/release/"


def test_the_build_is_given_no_secret_and_reaches_no_store():
    text = DOCKERFILE.read_text(encoding="utf-8")
    instructions = "\n".join(lines())
    assert "--mount" not in instructions and "secret" not in instructions.lower()
    assert not re.search(r"BURRO_(STORE|RELEASES)_", text)
    assert not re.search(r"[a-z][a-z0-9+.-]*://", text)
    assert set(defaults()) == {"PYTHON_IMAGE", "RELEASE_ID", "RELEASE_FROM"}


def test_the_build_is_handed_one_folder_of_releases_and_no_other():
    allowed = let_in()
    assert SERVED in allowed and "data/approved" in allowed
    assert [name for name in allowed if name.startswith("data/")] == [
        "data/fixtures/synthetic",
        "data/approved",
        SERVED,
    ]
    assert [name for name in allowed if name.startswith("tools/")] == [
        "tools/public_log.py",
        "tools/release_lock.py",
    ]
    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "data/releases/" in ignored


# What the build would do


def test_the_made_up_city_is_carried_as_it_is_committed(tmp_path: Path):
    done = walk(a_checkout(tmp_path / "checkout"), tmp_path / "image")
    assert (done.returncode, done.stderr) == (0, "")
    assert done.stdout.startswith(f"step=take status=ok release={MADE_UP} files=11 ")
    carried = tmp_path / "image" / "srv" / "burro" / "release"
    assert sorted(path.name for path in carried.iterdir()) == [MADE_UP]


def test_the_made_up_city_is_carried_though_a_release_is_approved(tmp_path: Path):
    """The check of every pull request builds the image with nothing given, and no key."""
    checkout = a_checkout(tmp_path / "checkout")
    taken(checkout)
    shutil.rmtree(checkout / SERVED)
    assert walk(checkout, tmp_path / "image").returncode == 0


def test_a_release_whose_lock_is_committed_is_carried(tmp_path: Path):
    checkout = a_checkout(tmp_path / "checkout")
    taken(checkout)
    done = walk(checkout, tmp_path / "image", RELEASE_ID=RELEASE, RELEASE_FROM=SERVED)
    assert (done.returncode, done.stderr) == (0, "")
    assert done.stdout.startswith(f"step=take status=ok release={RELEASE} files=11 ")
    carried = tmp_path / "image" / "srv" / "burro" / "release"
    assert sorted(path.name for path in carried.iterdir()) == [
        RELEASE,
        f"{RELEASE}-build",
        f"{RELEASE}-income",
    ]


def test_a_release_no_lock_names_ends_the_build(tmp_path: Path):
    checkout = a_checkout(tmp_path / "checkout")
    taken(checkout, approved=False)
    done = walk(checkout, tmp_path / "image", RELEASE_ID=RELEASE, RELEASE_FROM=SERVED)
    assert done.returncode == 1
    assert done.stdout == f"step=take status=missing release={RELEASE}\n"


def test_a_release_is_not_carried_by_the_lock_of_another(tmp_path: Path):
    checkout = a_checkout(tmp_path / "checkout")
    taken(checkout, OTHER)
    shutil.rmtree(checkout / SERVED)
    taken(checkout, approved=False)
    done = walk(checkout, tmp_path / "image", RELEASE_ID=RELEASE, RELEASE_FROM=SERVED)
    assert (done.returncode, done.stdout) == (1, f"step=take status=missing release={RELEASE}\n")
    # Nor under the id of the one that is approved.
    done = walk(checkout, tmp_path / "again", RELEASE_ID=OTHER, RELEASE_FROM=SERVED)
    assert done.returncode == 1
    assert done.stdout == f"step=take status=refused release={OTHER} unlisted=3\n"


def test_a_release_of_which_one_byte_was_changed_ends_the_build(tmp_path: Path):
    checkout = a_checkout(tmp_path / "checkout")
    out = taken(checkout)
    content = release_files()["features.json"]
    (out / RELEASE / "features.json").write_bytes(content.replace(b"73.25", b"73.26"))
    done = walk(checkout, tmp_path / "image", RELEASE_ID=RELEASE, RELEASE_FROM=SERVED)
    assert done.returncode == 1
    assert done.stdout.splitlines() == [
        f"step=take status=differs release={RELEASE} folder=release file=features.json",
        f"step=take status=differs release={RELEASE} files=11 differing=1",
    ]


def test_a_preview_that_lies_beside_what_was_taken_ends_the_build(tmp_path: Path):
    """An image holds what is served and nothing else."""
    checkout = a_checkout(tmp_path / "checkout")
    taken(checkout)
    built(checkout / SERVED, OTHER)
    done = walk(checkout, tmp_path / "image", RELEASE_ID=RELEASE, RELEASE_FROM=SERVED)
    assert (done.returncode, done.stdout) == (
        1,
        f"step=take status=refused release={RELEASE} unlisted=3\n",
    )


def test_a_release_of_london_is_not_carried_under_the_id_of_the_made_up_city(tmp_path: Path):
    checkout = a_checkout(tmp_path / "checkout")
    out = taken(checkout)
    for folder in sorted(out.iterdir()):
        folder.rename(out / folder.name.replace(RELEASE, MADE_UP))
    done = walk(checkout, tmp_path / "image", RELEASE_ID=MADE_UP, RELEASE_FROM=SERVED)
    assert done.returncode == 1
    assert done.stdout == f"step=take status=refused release={MADE_UP} unlisted=2\n"


def test_a_folder_the_build_is_not_handed_cannot_be_named(tmp_path: Path):
    """Whatever folder is named, the build is handed the one that `take` fills and no other."""
    checkout = a_checkout(tmp_path / "checkout")
    built(checkout / "data/releases", RELEASE)
    with pytest.raises(AssertionError, match="data/releases"):
        walk(checkout, tmp_path / "image", RELEASE_ID=RELEASE, RELEASE_FROM="data/releases")


def test_what_the_check_prints_in_a_build_names_no_place_and_gives_no_figure(tmp_path: Path):
    checkout = a_checkout(tmp_path / "checkout")
    out = taken(checkout)
    names = json.loads((out / RELEASE / "neighbourhoods.json").read_bytes())["rows"]
    done = walk(checkout, tmp_path / "image", RELEASE_ID=RELEASE, RELEASE_FROM=SERVED)
    assert done.returncode == 0
    assert all(row["name"] not in done.stdout + done.stderr for row in names)
