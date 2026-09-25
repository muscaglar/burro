"""What the tests of evidence share: the synthetic release, its made-up evidence, and a real one.

Nothing here is real. The release is the committed synthetic one. The "real"
release is the same made-up city with real ids and with gritty built from land
use, which is the only way this build has of making one. No file of a
publisher is read.
"""

import json
import os
import shutil
import subprocess
import tempfile
from collections.abc import Callable, Iterable
from datetime import date
from functools import cache
from pathlib import Path
from typing import Any

from burro_core.ids import GrittyVariant
from burro_core.release import MANIFEST, InMemoryRelease, parse_release
from burro_pipeline.evidence.lock import Lock, locked
from burro_pipeline.evidence.made_up import made_up_evidence
from burro_pipeline.evidence.receipt import Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.fetch.sources import FetchList, Format, Listed, Take
from burro_pipeline.registry import (
    CommercialUse,
    Dimension,
    Licence,
    Registry,
    Source,
    Status,
    Use,
    VerifiedHow,
    check,
)
from burro_pipeline.release import build_synthetic, read_release

REPOSITORY = Path(__file__).parents[4]
RELEASE_ID, REAL_ID = "syn-2026-09-23-01", "lon-2026-09-23-01"
FIXTURE = REPOSITORY / "data" / "fixtures" / "synthetic" / RELEASE_ID
# A string found nowhere else. If something printed repeats what it was given, this shows.
CANARY = "Zzyzx Parva"
# The source every file of the made-up real release cites, and the one its files come from.
SURVEY = "made-up-survey"
COMMIT = "0123456789abcdef0123456789abcdef01234567"
# A folder that is in no working copy of any repository: no folder above it holds one. A
# lock sealed there takes the commit it is given. The tests may themselves be run in a
# working copy, and one with changes, so no folder beside them will do. A test holds this.
NO_REPOSITORY = Path(tempfile.gettempdir()).resolve()
# The uses the files of a release ask of a source.
OF_A_RELEASE = (Use.GAZETTEER, Use.SCORING, Use.ROUTING, Use.DISPLAY, Use.DESTINATION_SEARCH)


@cache
def release() -> InMemoryRelease:
    return read_release(FIXTURE)


@cache
def evidence() -> Evidence:
    return made_up_evidence(release())


@cache
def from_land_use() -> InMemoryRelease:
    """The made-up city with gritty built from land use, under the id of the committed one.

    It holds no recorded crime, and so carries every vibe but Gritty. The "real"
    release of these tests is made from this one.
    """
    return build_synthetic(release_id=RELEASE_ID, gritty_variant=GrittyVariant.A)


def with_rows(rows: Iterable[EvidenceRow], of: Evidence | None = None) -> Evidence:
    """The same evidence with other rows."""
    of = of or evidence()
    return Evidence.of(of.release_id, of.receipts, of.methods, rows, of.claims)


def without(*fact_ids: str) -> Evidence:
    """The made-up evidence with some rows taken out."""
    assert all(evidence().row(fact_id) is not None for fact_id in fact_ids)
    return with_rows(row for row in evidence().rows if row.fact_id not in fact_ids)


def changed(fact_id: str, change: Callable[[dict[str, Any]], object]) -> Evidence:
    """The made-up evidence with one row changed."""
    rows: list[EvidenceRow] = []
    for row in evidence().rows:
        fields = row.model_dump(mode="json")
        if row.fact_id == fact_id:
            change(fields)
        rows.append(EvidenceRow.model_validate(fields))
    return with_rows(rows)


@cache
def real_release() -> InMemoryRelease:
    """The synthetic release with real ids, every file citing the one made-up source."""
    text = json.dumps(from_land_use().documents()).replace("syn-", "lon-")
    documents: dict[str, Any] = json.loads(text.replace('"synthetic"', f'"{SURVEY}"'))
    documents[MANIFEST].pop(SURVEY)
    documents[MANIFEST].update(synthetic=False, city="lon", seed=None)
    # A release credits a source as the licence registry does: see `registered`.
    held = registered(SURVEY)
    documents[MANIFEST]["sources"][0].update(
        name=held.name,
        publisher=held.publisher,
        licence=held.licence.value,
        attribution=held.attribution,
        url=held.url,
    )
    return parse_release(documents)


@cache
def real_evidence() -> Evidence:
    """Evidence for the made-up real release: the made-up evidence, under real ids."""
    made_up = made_up_evidence(from_land_use())
    fields = json.loads(made_up.canonical().decode().replace("syn-", "lon-"))
    for receipt in fields["receipts"]:
        name = receipt["publisher_file"]
        receipt.update(source_id=SURVEY, how="fetched", url=f"https://data.example.org/{name}")
    return Evidence.model_validate(fields)


def from_source(receipt: Receipt, source_id: str) -> Receipt:
    """A receipt as it would be if its file came from another source."""
    return Receipt.model_validate(receipt.model_dump(mode="json") | {"source_id": source_id})


def registered(
    source_id: str,
    *uses: Use,
    status: Status = Status.APPROVED,
    heading: Dimension = Dimension.GEOGRAPHY,
    tables: tuple[str, ...] = (),
) -> Source:
    """A made-up entry of the licence registry."""
    return Source(
        id=source_id,
        name=source_id,
        publisher="A made-up publisher",
        url="https://example.org/data",
        dimension=heading,
        tables=tables,
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


def registry_of(*sources: Source) -> Registry:
    """A registry of made-up entries, which must break no rule of the registry."""
    found = Registry(sources)
    assert check(found, date(2026, 9, 23)) == []
    return found


def as_toml(registry: Registry) -> str:
    """A registry as a person writes it, so that a step can read it from a file."""
    written = ["schema_version = 1\n"]
    for source in registry:
        fields = source.model_dump(mode="json", exclude_defaults=True)
        # A day is written bare. Everything else is written as JSON writes it.
        lines = [
            f"{name} = {value if name == 'verified_on' else json.dumps(value)}"
            for name, value in fields.items()
        ]
        written.append("[[source]]\n" + "\n".join(lines) + "\n")
    return "\n".join(written)


def survey_registry(*more: Source) -> Registry:
    """The registry of the made-up real release: its one source, approved for every use."""
    return registry_of(registered(SURVEY, *OF_A_RELEASE, heading=Dimension.HOUSING), *more)


def lock_of(found: Evidence, leave_out: str = "") -> Lock:
    """The lock of a build that took every file of the evidence, or all but one."""
    kept = [receipt for receipt in found.receipts if receipt.file_id != leave_out]
    inputs = tuple(locked(receipt) for receipt in kept)
    return Lock(
        release_id=found.release_id, built_at="2026-09-23T00:00:00Z", commit=COMMIT, inputs=inputs
    )


def with_receipt(found: Evidence, file_id: str, **changes: object) -> Evidence:
    """The same evidence, with one receipt saying something else of its file."""
    assert found.receipt(file_id) is not None
    fields = json.loads(found.canonical())
    for receipt in fields["receipts"]:
        if receipt["file_id"] == file_id:
            receipt.update(changes)
    return Evidence.model_validate(fields)


def listed(receipt: Receipt, item: str = "") -> Listed:
    """The file of a receipt, as the list of its build names it. The list is fetch's own.

    Where part of the file was taken, the list says which part, as the receipt does.
    """
    taken = receipt.taken
    return Listed(
        item=item or f"item-{receipt.file_id[2:]}",
        source_id=receipt.source_id,
        use=receipt.use,
        what="A made-up file",
        format=Format.OTHER if taken is None else Format.PARQUET,
        page="https://example.org/data",
        max_bytes=receipt.bytes,
        edition=receipt.edition,
        data_period=receipt.data_period,
        take=None
        if taken is None
        else Take(box=taken.box, box_in=taken.box_in, columns=taken.columns),
    )


def list_as_toml(files: Iterable[Listed], build: str = "made-up") -> str:
    """A list as a person writes it, so that a step can read it from a file."""
    written = [f'schema_version = 1\nbuild = "{build}"\n']
    for file in files:
        fields = file.model_dump(mode="json", exclude_defaults=True, exclude_none=True)
        period = fields.pop("data_period", None)
        lines = [f"{name} = {json.dumps(value)}" for name, value in fields.items()]
        if period is not None:
            inside = ", ".join(f"{name} = {json.dumps(value)}" for name, value in period.items())
            lines.append(f"data_period = {{ {inside} }}")
        written.append("[[file]]\n" + "\n".join(lines) + "\n")
    return "\n".join(written)


def read_back(files: Iterable[Listed], folder: Path) -> FetchList:
    """A list as fetch reads it from a file, so that a test holds what fetch gives."""
    from burro_pipeline.fetch.sources import load_list

    path = folder / "made-up.toml"
    path.write_text(list_as_toml(files), encoding="utf-8")
    return load_list(path)


# Git itself, to make a repository for a test to read. No code of the pipeline runs it.
def _where_git_is() -> str | None:
    """The git the tests run, which is the one on the path.

    On a Mac the one on the path may be a stub, which looks the real one up each
    time it is run and takes longer over that than git takes over its work. The
    tests run git some hundred times, so there the real one is looked up once.
    """
    found, finder = shutil.which("git"), shutil.which("xcrun")
    if found is None or finder is None or Path(found) != Path("/usr/bin/git"):
        return found
    looked_up = subprocess.run(  # noqa: S603  a program of the system, with words written here
        [finder, "--find", "git"], capture_output=True, text=True, check=False
    )
    real = looked_up.stdout.strip()
    return real if looked_up.returncode == 0 and Path(real).is_file() else found


GIT = _where_git_is()


def git(root: Path, *words: str) -> str:
    """Run git in a folder of a test, as a made-up person, and give what it printed.

    It reads no settings of the machine or of the person who runs the tests,
    so that a commit is never signed and never bears a real name.

    The tests run git some hundred times, from a process that has grown large. Left to
    close every file it holds first, Python copies that whole process to start each
    one. Python opens no file that a program it starts is given, so there is nothing
    to close, and git is started without the copy.
    """
    # What git would take from the run it is started in: another repository, or its index.
    of_the_run = {name: held for name, held in os.environ.items() if not name.startswith("GIT_")}
    apart = of_the_run | {
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_AUTHOR_NAME": "A made-up person",
        "GIT_AUTHOR_EMAIL": "made-up@example.org",
        "GIT_AUTHOR_DATE": "2026-09-23T00:00:00Z",
        "GIT_COMMITTER_NAME": "A made-up person",
        "GIT_COMMITTER_EMAIL": "made-up@example.org",
        "GIT_COMMITTER_DATE": "2026-09-23T00:00:00Z",
    }
    done = subprocess.run(  # noqa: S603  git, with the words a test gives it
        [GIT or "git", "-C", str(root), *words],
        capture_output=True,
        text=True,
        env=apart,
        check=True,
        close_fds=False,
    )
    return done.stdout.strip()
