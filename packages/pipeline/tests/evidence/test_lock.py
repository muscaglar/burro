"""The lock: what a build is made from, by hash, and the step that seals it.

Every file here is made up and a few bytes long. Nothing is fetched. The vault
is a table of sizes held in the test, and the registry is three made-up entries.
"""

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import pytest
from burro_pipeline.evidence.lock import (
    InputKind,
    Lock,
    LockedInput,
    LockError,
    locked,
    read_lock,
    read_receipts,
    seal,
)
from burro_pipeline.evidence.receipt import Geography, Period, Receipt, made_up_receipt
from burro_pipeline.evidence.record import file_id_of
from burro_pipeline.evidence.repository import top_of
from burro_pipeline.fetch.sources import Listed
from burro_pipeline.registry import Dimension, Registry, RegistryError, Source, Status, Use
from pydantic import ValidationError

from .conftest import write
from .examples import RECEIPT
from .support import GIT, NO_REPOSITORY, git, listed, read_back, registered, registry_of

REAL_ID, MADE_UP_ID = "lon-2026-09-23-01", "syn-2026-09-23-01"
BUILT_AT = "2026-09-23T00:00:00Z"
COMMIT = "0123456789abcdef0123456789abcdef01234567"
# A string found nowhere else. If a refusal repeats what a file says, this shows up in it.
CANARY = "Zzyzx Parva"
# A made-up row of a publisher's file. No test may ever see it printed.
PARKS = b"park_id,name,hectares\n1,Dulcimer Green,4.2\n"
HOMES = b"oa21cd,homes\nE00000001,131\n"


def registry(**changes: Source) -> Registry:
    sources = {
        "made-up-parks": registered("made-up-parks", Use.SCORING),
        "made-up-homes": registered("made-up-homes", Use.SCORING, Use.ROUTING),
    }
    return registry_of(*(sources | changes).values())


def receipt(source_id: str, content: bytes, use: Use = Use.SCORING, **changes: str) -> Receipt:
    sha256 = hashlib.sha256(content).hexdigest()
    fields = RECEIPT.model_dump(mode="json") | {
        "file_id": file_id_of(sha256),
        "sha256": sha256,
        "bytes": len(content),
        "source_id": source_id,
        "use": use,
        "how": "fetched",
        "url": f"https://data.example.org/{source_id}.csv",
        "publisher_file": f"{source_id}.csv",
    }
    return Receipt.model_validate(fields | changes)


RECEIPTS = (receipt("made-up-parks", PARKS), receipt("made-up-homes", HOMES))
VAULT = {found.vault_key(): found.bytes for found in RECEIPTS}


def sealed(
    receipts: tuple[Receipt, ...] = RECEIPTS,
    vault: dict[str, int] | None = None,
    held: Registry | None = None,
    root: Path = NO_REPOSITORY,
    release_id: str = REAL_ID,
    named: tuple[Listed, ...] | None = None,
    commit: str | None = COMMIT,
) -> Lock:
    """The lock of some receipts. The list names each of them, unless a test says otherwise."""
    return seal(
        release_id,
        BUILT_AT,
        commit,
        receipts,
        VAULT if vault is None else vault,
        registry() if held is None else held,
        root,
        listed=tuple(listed(found) for found in receipts) if named is None else named,
    )


def refused(**given: Any) -> LockError:
    with pytest.raises(LockError) as caught:
        sealed(**given)
    assert CANARY not in str(caught.value) and "\n" not in str(caught.value)
    return caught.value


# What a build may read.


def test_a_build_admits_an_input_that_its_lock_names(tmp_path: Path):
    lock = sealed()
    assert lock.admit(PARKS).name == RECEIPTS[0].file_id
    (tmp_path / "homes.csv").write_bytes(HOMES)
    assert lock.admit_file(tmp_path / "homes.csv").source_id == "made-up-homes"
    assert lock.holds(RECEIPTS[0].file_id) and not lock.holds("f-000000000000")


def test_a_build_refuses_an_input_whose_hash_is_not_in_its_lock(tmp_path: Path):
    lock = sealed()
    # One byte more, one byte changed, and a file of another name with other bytes.
    for content in (PARKS + b"\n", PARKS.replace(b"4.2", b"4.3"), CANARY.encode()):
        with pytest.raises(LockError) as caught:
            lock.admit(content, "the parks file")
        assert caught.value.rule == "input_is_locked"
        assert str(caught.value) == (
            "the parks file is not an input of this build: its hash is not in the lock "
            "[input_is_locked]"
        )
    (tmp_path / "parks.csv").write_bytes(PARKS + CANARY.encode())
    with pytest.raises(LockError) as caught:
        lock.admit_file(tmp_path / "parks.csv")
    assert caught.value.rule == "input_is_locked"
    assert CANARY not in str(caught.value) and str(tmp_path) not in str(caught.value)


def test_a_made_up_lock_with_nothing_in_it_admits_nothing():
    empty = seal(MADE_UP_ID, BUILT_AT, COMMIT, (), {}, None, NO_REPOSITORY)
    assert empty.inputs == ()
    with pytest.raises(LockError):
        empty.admit(PARKS)


def test_a_lock_with_no_input_is_not_sealed_for_a_release_that_is_not_made_up():
    error = refused(receipts=())
    assert (error.rule, error.subject) == ("lock_has_an_input", "the lock")
    assert str(error) == (
        "the lock names no input, and a release that is not made up is built from at least "
        "one [lock_has_an_input]"
    )


def test_a_lock_with_no_input_is_not_read_for_a_release_that_is_not_made_up(tmp_path: Path):
    # One written by hand, or left by an earlier version of the step.
    fields: dict[str, Any] = sealed().model_dump(mode="json") | {"inputs": ()}
    with pytest.raises(ValidationError, match="is built from at least one input"):
        Lock.model_validate(fields)
    (tmp_path / "lock.json").write_text(json.dumps(fields), encoding="utf-8")
    with pytest.raises(LockError) as caught:
        read_lock(tmp_path / "lock.json")
    assert caught.value.rule == "lock_is_valid"
    assert Lock.model_validate(fields | {"release_id": MADE_UP_ID}).inputs == ()


# Sealing.


def test_a_lock_lists_every_input_by_hash_in_the_order_of_their_names():
    lock = sealed()
    assert [found.name for found in lock.inputs] == sorted(r.file_id for r in RECEIPTS)
    assert {found.sha256 for found in lock.inputs} == {r.sha256 for r in RECEIPTS}
    assert (lock.release_id, lock.built_at, lock.commit) == (REAL_ID, BUILT_AT, COMMIT)
    assert lock.path().as_posix() == f"data/locks/{REAL_ID}.json"


def test_the_same_inputs_seal_to_the_same_lock_whatever_their_order():
    assert sealed(RECEIPTS).canonical() == sealed(RECEIPTS[::-1]).canonical()
    assert sealed().digest() != sealed(RECEIPTS[:1]).digest()


def test_a_lock_holds_no_address_no_date_of_a_fetch_and_no_row():
    written = sealed().canonical().decode()
    assert "https://" not in written and "example.org" not in written
    assert "retrieved" not in written and "Dulcimer" not in written


def test_sealing_asks_the_gate_about_every_file():
    asked: list[tuple[str, Use]] = []

    class Spy(Registry):
        def require(self, source_id: str, use: Use) -> Source:
            asked.append((source_id, use))
            return super().require(source_id, use)

    sealed(held=Spy(registry().sources))
    assert sorted(asked) == sorted((r.source_id, r.use) for r in RECEIPTS)


@pytest.mark.parametrize(
    ("entry", "why"),
    [
        (registered("made-up-parks", Use.DISPLAY), "is not registered for scoring"),
        (registered("made-up-parks", Use.VALIDATION_ONLY, status=Status.GATED), "is gated"),
        (registered("made-up-parks", status=Status.BANNED), "is banned"),
    ],
)
def test_sealing_is_refused_when_the_gate_refuses(entry: Source, why: str):
    error = refused(held=registry(**{"made-up-parks": entry}))
    assert error.rule == "gate_refuses"
    assert error.subject == RECEIPTS[0].file_id
    assert why in str(error)


def test_sealing_is_refused_for_a_source_the_registry_does_not_hold():
    error = refused(receipts=(receipt("made-up-rivers", PARKS),), vault={})
    assert error.rule == "gate_refuses" and "is not in the licence registry" in str(error)


def test_the_gate_is_asked_before_the_vault_is():
    # A file that may not be used is refused for that, whether or not it was ever stored.
    banned = registry(**{"made-up-parks": registered("made-up-parks", status=Status.BANNED)})
    assert refused(held=banned, vault={}).rule == "gate_refuses"


# What is kept for the audit, or for the census table, is no input of a product build.

# Each is a made-up source that the gate lets through for the use its receipt gives. So
# without a rule of its own, each would be sealed.
KEPT_APART = {
    "fetched for the audit": (
        registered("made-up-faiths", Use.AUDIT_ONLY, status=Status.HELD, heading=Dimension.AUDIT),
        Use.AUDIT_ONLY,
    ),
    "fetched for the census table": (
        registered(
            "made-up-census",
            Use.CENSUS_TABLE,
            heading=Dimension.RESIDENTS,
            tables=("TS021",),
        ),
        Use.CENSUS_TABLE,
    ),
    "under the audit heading, and fetched to look at": (
        registered(
            "made-up-faiths",
            Use.AUDIT_ONLY,
            Use.VALIDATION_ONLY,
            status=Status.GATED,
            heading=Dimension.AUDIT,
        ),
        Use.VALIDATION_ONLY,
    ),
    "registered for the audit under another heading": (
        registered(
            "made-up-faiths",
            Use.AUDIT_ONLY,
            Use.VALIDATION_ONLY,
            status=Status.HELD,
            heading=Dimension.CULTURE,
        ),
        Use.VALIDATION_ONLY,
    ),
}
RESIDENTS = b"oa21cd,faith,people\nE00000001,Zzyzx Parva,12\n"


@pytest.mark.parametrize(("entry", "use"), KEPT_APART.values(), ids=list(KEPT_APART))
def test_a_file_kept_for_the_audit_or_the_census_table_is_never_sealed(entry: Source, use: Use):
    held = registry(**{entry.id: entry})
    # The gate itself lets the file through, for the use its receipt gives.
    assert held.require(entry.id, use) == entry
    kept_apart = receipt(entry.id, RESIDENTS, use)
    vault = VAULT | {kept_apart.vault_key(): kept_apart.bytes}
    error = refused(receipts=(*RECEIPTS, kept_apart), vault=vault, held=held)
    assert (error.rule, error.subject) == ("file_is_for_the_product", kept_apart.file_id)
    assert entry.id not in str(error)
    # Alone, and with nothing in the vault: it is refused for what it is, whatever else holds.
    assert refused(receipts=(kept_apart,), vault={}, held=held).rule == "file_is_for_the_product"


@pytest.mark.parametrize("use", [Use.AUDIT_ONLY, Use.CENSUS_TABLE])
def test_a_made_up_file_for_the_audit_is_not_sealed_for_a_made_up_release_either(use: Use):
    made_up = made_up_receipt(
        "made-up-faiths.csv", use, Geography.OA21, Period(as_at="2021-03-21"), BUILT_AT
    )
    with pytest.raises(LockError) as caught:
        seal(MADE_UP_ID, BUILT_AT, COMMIT, (made_up,), {}, None, NO_REPOSITORY)
    assert (caught.value.rule, caught.value.subject) == ("file_is_for_the_product", made_up.file_id)


def test_a_file_fetched_to_look_at_is_still_sealed_so_that_a_check_can_read_it():
    # The checks of a build read sources that are registered to validate against and no more.
    entry = registered("made-up-prices", Use.VALIDATION_ONLY, status=Status.GATED)
    looked_at = receipt("made-up-prices", RESIDENTS, Use.VALIDATION_ONLY)
    vault = VAULT | {looked_at.vault_key(): looked_at.bytes}
    lock = sealed(receipts=(*RECEIPTS, looked_at), vault=vault, held=registry(**{entry.id: entry}))
    assert lock.holds(looked_at.file_id)


def test_a_real_build_is_not_sealed_without_a_registry():
    named = tuple(listed(found) for found in RECEIPTS)
    with pytest.raises(LockError) as caught:
        seal(REAL_ID, BUILT_AT, COMMIT, RECEIPTS, VAULT, None, NO_REPOSITORY, listed=named)
    assert caught.value.rule == "real_build_needs_a_registry"


# The list of the build says which files a lock holds.

PARKS_2024 = receipt("made-up-parks", b"park_id,name\n1,Dulcimer Green\n", edition="2024")
PARKS_AGAIN = receipt("made-up-parks", PARKS + b"2,Zzyzx Parva,1.0\n")
RIVERS = receipt("made-up-rivers", b"river_id,name\n1,Dulcimer Brook\n")
IN_THE_LIST = (listed(RECEIPTS[0], "parks"), listed(RECEIPTS[1], "homes"))


def held_in(*receipts: Receipt) -> dict[str, int]:
    return {found.vault_key(): found.bytes for found in receipts}


def test_a_lock_holds_the_files_the_list_of_the_build_names(tmp_path: Path):
    lock = sealed(named=IN_THE_LIST)
    assert [found.name for found in lock.inputs] == sorted(r.file_id for r in RECEIPTS)
    # And so it does when the list is read from a file, as fetch reads it.
    from_a_file = read_back(IN_THE_LIST, tmp_path)
    assert sealed(named=from_a_file.files) == lock
    assert sealed(named=IN_THE_LIST[::-1]) == lock


def test_sealing_is_refused_when_a_file_of_the_list_has_no_receipt():
    named = (*IN_THE_LIST, listed(RIVERS, "rivers"))
    rivers = registered("made-up-rivers", Use.SCORING)
    error = refused(named=named, held=registry(**{rivers.id: rivers}))
    assert (error.rule, error.subject) == ("listed_file_has_a_receipt", "rivers")
    assert str(error).startswith("rivers is a file of the list, and no receipt of it is in ")
    # Whatever else is there: the file is named, and nothing is sealed without it.
    assert refused(receipts=(), named=IN_THE_LIST).subject == "parks"


def test_sealing_is_refused_when_a_receipt_is_there_that_the_list_does_not_name():
    error = refused(named=IN_THE_LIST[:1])
    assert (error.rule, error.subject) == ("receipt_is_listed", RECEIPTS[1].file_id)
    assert "made-up-homes" not in str(error)
    assert refused(named=()).rule == "receipt_is_listed"


@pytest.mark.parametrize(
    ("named", "left_over"),
    [(RECEIPTS[0], PARKS_2024), (PARKS_2024, RECEIPTS[0])],
    ids=["the list names the new edition", "the list names the old edition"],
)
def test_a_second_edition_of_a_file_is_sealed_only_if_the_list_names_it(
    named: Receipt, left_over: Receipt
):
    both = (RECEIPTS[0], PARKS_2024, RECEIPTS[1])
    assert named.edition != left_over.edition
    wanted = (listed(named, "parks"), IN_THE_LIST[1])
    error = refused(receipts=both, vault=held_in(*both), named=wanted)
    assert (error.rule, error.subject) == ("receipt_is_listed", left_over.file_id)
    # With the other receipt out of the folder, the build is sealed on the one that is named.
    kept = (named, RECEIPTS[1])
    lock = sealed(receipts=kept, vault=held_in(*kept), named=wanted)
    assert lock.holds(named.file_id) and not lock.holds(left_over.file_id)


def test_a_file_the_publisher_gave_twice_under_one_edition_is_not_sealed_twice():
    # The same name, source, edition and period, and other bytes. The list names it once.
    both = (RECEIPTS[0], PARKS_AGAIN, RECEIPTS[1])
    assert PARKS_AGAIN.publisher_file == RECEIPTS[0].publisher_file
    error = refused(receipts=both, vault=held_in(*both), named=IN_THE_LIST)
    assert error.rule == "receipt_is_listed"
    assert error.subject in (RECEIPTS[0].file_id, PARKS_AGAIN.file_id)


def of_one_edition(*names: str) -> tuple[Receipt, ...]:
    """Files of one source, one edition and one period, as the first list has three."""
    return tuple(
        receipt("made-up-homes", f"band,homes,{name}\n".encode(), publisher_file=f"{name}.zip")
        for name in names
    )


def test_files_of_one_source_edition_and_period_are_counted():
    three = of_one_edition("stock-1", "stock-3", "stock-4")
    named = tuple(listed(found, found.publisher_file[:-4]) for found in three)
    assert len({(n.source_id, n.use, n.edition, n.data_period) for n in named}) == 1
    lock = sealed(receipts=three, vault=held_in(*three), named=named)
    assert len(lock.inputs) == 3
    # One is missing. Which of the three it is cannot be read from a receipt.
    error = refused(receipts=three[:2], vault=held_in(*three), named=named)
    assert error.rule == "listed_file_has_a_receipt"
    assert error.subject in {n.item for n in named}
    # One too many.
    four = (*three, *of_one_edition("stock-5"))
    assert refused(receipts=four, vault=held_in(*four), named=named).rule == "receipt_is_listed"


def test_one_of_those_files_given_twice_does_not_stand_in_for_one_that_is_missing():
    three = of_one_edition("stock-1", "stock-3", "stock-4")
    named = tuple(listed(found, found.publisher_file[:-4]) for found in three)
    again = receipt("made-up-homes", b"band,homes,changed\n", publisher_file="stock-1.zip")
    two_and_one_twice = (three[0], again, three[1])
    error = refused(receipts=two_and_one_twice, vault=held_in(*two_and_one_twice), named=named)
    assert error.rule == "listed_file_has_one_receipt"
    assert error.subject in (three[0].file_id, again.file_id)


def test_sealing_is_refused_when_the_vault_lacks_a_file():
    missing = {key: size for key, size in VAULT.items() if "made-up-homes" not in key}
    error = refused(vault=missing)
    assert (error.rule, error.subject) == ("file_is_in_the_vault", RECEIPTS[1].file_id)
    # The refusal names the file by its id. Where the vault keeps it is not said.
    assert "raw/" not in str(error) and RECEIPTS[1].sha256 not in str(error)


def test_sealing_is_refused_when_a_file_in_the_vault_is_not_the_size_its_receipt_gives():
    short = VAULT | {RECEIPTS[0].vault_key(): RECEIPTS[0].bytes - 1}
    assert refused(vault=short).rule == "file_is_in_the_vault"


def test_sealing_is_refused_when_licence_evidence_is_not_saved(tmp_path: Path):
    saved = "registry/evidence/made-up-parks-2026-09-23.pdf"
    with_terms = (receipt("made-up-parks", PARKS, licence_evidence=saved), RECEIPTS[1])
    error = refused(receipts=with_terms, root=tmp_path)
    assert (error.rule, error.subject) == ("licence_evidence_is_saved", RECEIPTS[0].file_id)
    (tmp_path / "registry" / "evidence").mkdir(parents=True)
    (tmp_path / saved).write_bytes(b"%PDF made up")
    assert sealed(receipts=with_terms, root=tmp_path).holds(RECEIPTS[0].file_id)


def test_one_file_has_one_receipt():
    twice = (*RECEIPTS, receipt("made-up-homes", PARKS, Use.ROUTING))
    vault = VAULT | {twice[2].vault_key(): twice[2].bytes}
    assert refused(receipts=twice, vault=vault).rule == "one_receipt_for_a_file"


def test_made_up_files_are_sealed_for_a_made_up_release_and_for_no_other():
    made_up = made_up_receipt(
        "made-up-parks.csv", Use.SCORING, Geography.POINT, Period(as_at="2025"), BUILT_AT
    )
    # A made-up file is in no vault and under no registry entry, so neither is asked.
    lock = seal(MADE_UP_ID, BUILT_AT, COMMIT, (made_up,), {}, None, NO_REPOSITORY)
    assert [found.source_id for found in lock.inputs] == ["synthetic"]
    assert refused(receipts=(made_up,)).rule == "made_up_is_consistent"
    assert refused(release_id=MADE_UP_ID).rule == "made_up_is_consistent"
    with pytest.raises(ValidationError):
        Lock(release_id=REAL_ID, built_at=BUILT_AT, commit=COMMIT, inputs=(locked(made_up),))


def test_a_build_with_no_package_lockfile_is_a_development_build():
    assert sealed().development
    packages = hashlib.sha256(b"a made-up lockfile").hexdigest()
    named = tuple(listed(found) for found in RECEIPTS)
    of_record = seal(
        REAL_ID,
        BUILT_AT,
        COMMIT,
        RECEIPTS,
        VAULT,
        registry(),
        NO_REPOSITORY,
        packages,
        listed=named,
    )
    assert not of_record.development and of_record.packages == packages


def test_a_lock_names_what_is_not_a_publishers_file_too():
    areas = LockedInput(
        name="gazetteer/oa_to_area.csv",
        kind=InputKind.GAZETTEER,
        sha256=hashlib.sha256(b"oa21cd,area_id\n").hexdigest(),
        bytes=15,
    )
    named = tuple(listed(found) for found in RECEIPTS)
    lock = seal(
        REAL_ID,
        BUILT_AT,
        COMMIT,
        RECEIPTS,
        VAULT,
        registry(),
        NO_REPOSITORY,
        others=(areas,),
        listed=named,
    )
    assert lock.admit(b"oa21cd,area_id\n").kind is InputKind.GAZETTEER
    assert [found.name for found in lock.inputs] == sorted(found.name for found in lock.inputs)
    with pytest.raises(ValidationError):
        LockedInput.model_validate(areas.model_dump() | {"source_id": "made-up-parks"})
    with pytest.raises(ValidationError):
        LockedInput.model_validate(locked(RECEIPTS[0]).model_dump() | {"name": "parks"})


@pytest.mark.parametrize(
    "fields",
    [{"commit": "main"}, {"built_at": "today"}, {"release_id": "london"}, {"packages": "none"}],
)
def test_a_lock_names_its_code_by_commit_and_its_time_as_an_input(fields: dict[str, str]):
    with pytest.raises(ValidationError):
        Lock.model_validate(sealed().model_dump(mode="json") | fields)
    named = tuple(listed(found) for found in RECEIPTS)
    with pytest.raises(LockError) as caught:
        seal(REAL_ID, BUILT_AT, "main", RECEIPTS, VAULT, registry(), NO_REPOSITORY, listed=named)
    assert caught.value.rule == "lock_is_valid" and "commit" in str(caught.value)


def test_a_refusal_to_seal_never_repeats_what_it_was_handed():
    named = tuple(listed(found) for found in RECEIPTS)
    with pytest.raises(LockError) as caught:
        seal(
            f"lon-{CANARY}",
            CANARY,
            CANARY,
            RECEIPTS,
            VAULT,
            registry(),
            NO_REPOSITORY,
            listed=named,
        )
    assert caught.value.rule == "lock_is_valid"
    assert CANARY not in str(caught.value)
    assert {"release_id", "built_at", "commit"} <= set(re.findall(r"\w+", str(caught.value)))


# The code a build runs, by its commit.

in_a_repository = pytest.mark.skipif(GIT is None, reason="git is needed to make a repository")


@in_a_repository
def test_a_build_sealed_in_a_repository_takes_the_commit_that_is_checked_out(repository: Path):
    commit = git(repository, "rev-parse", "HEAD")
    assert sealed(root=repository, commit=None).commit == commit
    # A commit that is given too must be that one.
    assert sealed(root=repository, commit=commit).commit == commit
    for other in (COMMIT, commit[::-1], commit[:39] + ("0" if commit[39] != "0" else "1")):
        error = refused(root=repository, commit=other)
        assert (error.rule, error.subject) == ("commit_is_checked_out", "the commit given")
        assert other not in str(error) and commit not in str(error)


@in_a_repository
def test_a_build_is_not_sealed_from_a_working_copy_with_changes(repository: Path):
    write(repository, {"a/first.py": "FIRST = 2\n"})
    error = refused(root=repository, commit=None)
    assert (error.rule, error.subject) == ("tree_has_no_changes", "the working copy")
    assert str(error) == (
        "the working copy holds changes that are not committed, so no commit names the code "
        "it holds: 1 tracked file is not as git last took it [tree_has_no_changes]"
    )
    # Nor when the commit is given, and is the one checked out.
    commit = git(repository, "rev-parse", "HEAD")
    assert refused(root=repository, commit=commit).rule == "tree_has_no_changes"
    git(repository, "add", "--all")
    assert "what is staged is not what is committed" in str(refused(root=repository, commit=None))
    git(repository, "commit", "--quiet", "--message", "Two")
    assert sealed(root=repository, commit=None).commit == git(repository, "rev-parse", "HEAD")


@in_a_repository
def test_a_build_is_not_sealed_in_a_repository_that_cannot_be_read(repository: Path):
    (repository / ".git" / "index").write_text(CANARY, encoding="utf-8")
    error = refused(root=repository, commit=None)
    assert (error.rule, error.subject) == ("repository_is_read", "the repository")
    assert str(repository) not in str(error)


@in_a_repository
@pytest.mark.parametrize("inside", ["a", "a/deeper"])
def test_a_build_sealed_from_a_folder_inside_a_repository_is_held_to_the_repository(
    repository: Path, inside: str
):
    """Sealed from `packages/`, say. The repository above it is read, and no commit is taken."""
    commit = git(repository, "rev-parse", "HEAD")
    within = repository / inside
    assert sealed(root=within, commit=None).commit == commit
    assert sealed(root=within, commit=commit).commit == commit
    error = refused(root=within, commit=COMMIT)
    assert (error.rule, error.subject) == ("commit_is_checked_out", "the commit given")
    # A change in a folder beside it is a change to the working copy.
    write(repository, {"README.md": "changed\n"})
    assert refused(root=within, commit=None).rule == "tree_has_no_changes"
    assert refused(root=within, commit=commit).rule == "tree_has_no_changes"
    assert refused(root=within, commit=COMMIT).rule == "commit_is_checked_out"


def test_outside_a_repository_the_commit_is_the_one_given_and_one_must_be(tmp_path: Path):
    assert sealed(root=tmp_path).commit == COMMIT
    error = refused(root=tmp_path, commit=None)
    assert (error.rule, error.subject) == ("commit_is_named", "the build")


def test_the_folder_these_tests_seal_in_is_in_no_working_copy(tmp_path: Path):
    """The tests may be run in a working copy, and one with changes. They seal outside it."""
    assert top_of(NO_REPOSITORY) is None
    assert top_of(tmp_path) is None


@in_a_repository
def test_the_code_is_looked_at_before_any_file_is(repository: Path):
    write(repository, {"a/first.py": "FIRST = 2\n"})
    banned = registry(**{"made-up-parks": registered("made-up-parks", status=Status.BANNED)})
    assert refused(root=repository, commit=None, held=banned).rule == "tree_has_no_changes"


# Reading what was written.


def test_a_lock_and_its_receipts_read_back_as_they_were_written(tmp_path: Path):
    lock = sealed()
    (tmp_path / "lock.json").write_bytes(lock.canonical())
    assert read_lock(tmp_path / "lock.json") == lock
    for found in RECEIPTS:
        path = tmp_path / found.path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(found.canonical())
    assert read_receipts(tmp_path / "data" / "receipts") == tuple(
        sorted(RECEIPTS, key=lambda found: found.file_id)
    )
    assert read_receipts(tmp_path / "nowhere") == ()


def test_a_receipt_that_is_not_one_is_refused_without_what_it_holds(tmp_path: Path):
    for name, content in (
        ("row.json", b'{"name": "%s", "hectares": 4.2}' % CANARY.encode()),
        ("text.json", CANARY.encode()),
        ("list.json", b'["%s"]' % CANARY.encode()),
    ):
        (tmp_path / name).write_bytes(content)
        with pytest.raises(LockError) as caught:
            read_receipts(tmp_path)
        assert caught.value.rule == "receipt_is_valid"
        assert name in str(caught.value) and CANARY not in str(caught.value)
        (tmp_path / name).unlink()
    (tmp_path / "lock.json").write_bytes(b'{"inputs": "%s"}' % CANARY.encode())
    with pytest.raises(LockError) as caught:
        read_lock(tmp_path / "lock.json")
    assert caught.value.rule == "lock_is_valid" and CANARY not in str(caught.value)


def test_the_gate_itself_is_what_refuses():
    # The lock adds no rule of its own about a source: it says what the registry says.
    for_display = registry(**{"made-up-parks": registered("made-up-parks", Use.DISPLAY)})
    with pytest.raises(RegistryError) as said:
        for_display.require("made-up-parks", Use.SCORING)
    assert str(said.value) in str(refused(held=for_display))
