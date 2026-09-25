"""A publisher's file, as a step of a build reads it: through the gate, its receipt and the lock.

Every file here is made up and a few lines long. The store is a folder the test
makes, and the registry is three made-up entries. Nothing is fetched.
"""

import hashlib
import io
import socket
import zipfile
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import cast

import pytest
from burro_pipeline.evidence.lock import InputKind, Lock, LockedInput, LockError
from burro_pipeline.evidence.receipt import How, Period, Receipt
from burro_pipeline.evidence.record import file_id_of
from burro_pipeline.fetch.offline import sockets_refused
from burro_pipeline.fetch.store import FolderStore, Held, Store, StoreError
from burro_pipeline.inputs import Inputs, period_of, retrieved_on
from burro_pipeline.registry import (
    CommercialUse,
    Dimension,
    Licence,
    Registry,
    Source,
    Status,
    Use,
    VerifiedHow,
)

from .fetch.dated_support import header_of, register

# A string found nowhere else. If a refusal repeats what a file holds, this shows up in it.
CANARY = "Zzyzx Parva"
HOMES = f"﻿unit_code,unit_name,homes\r\nU001,{CANARY},120\r\nU002,{CANARY},80\r\n".encode()
HOMES_2026 = b"\xef\xbb\xbfunit_code,unit_name,homes\r\nU001,made up,125\r\n"
PARKS = b"park_id,hectares\n1,4.2\n"
MEMBER = "it does not hold the one file that is read"


def source(source_id: str, *uses: Use, dimension: Dimension = Dimension.HOUSING) -> Source:
    return Source(
        id=source_id,
        name="Made up",
        publisher="Made-up Office",
        url="https://made-up.example/about",
        dimension=dimension,
        licence=Licence.OGL_3,
        commercial_use=CommercialUse.YES,
        share_alike=False,
        attribution="Contains made-up data.",
        attribution_verified=True,
        status=Status.APPROVED,
        uses=uses,
        verified_how=VerifiedHow.PRIMARY_SOURCE,
        verified_on="2026-09-23",  # pyright: ignore[reportArgumentType]
        evidence_urls=("https://made-up.example/licence",),
    )


REGISTRY = Registry(
    (
        source("made-up-homes", Use.SCORING, Use.ROUTING),
        source("made-up-parks", Use.DISPLAY),
        source("made-up-residents", Use.AUDIT_ONLY, dimension=Dimension.AUDIT),
    )
)


def zipped(name: str, content: bytes) -> bytes:
    packed = io.BytesIO()
    with zipfile.ZipFile(packed, "w") as archive:
        archive.writestr(f"made-up/{name}", content)
        archive.writestr("made-up/notes.txt", CANARY)
    return packed.getvalue()


def receipt(source_id: str, name: str, content: bytes, edition: str = "2025", **said: str):
    sha256 = hashlib.sha256(content).hexdigest()
    fields = {
        "file_id": file_id_of(sha256),
        "source_id": source_id,
        "use": Use.SCORING,
        "publisher_file": name,
        "url": "https://files.made-up.example/about",
        "sha256": sha256,
        "bytes": len(content),
        "retrieved_at": "2026-09-23T21:09:21Z",
        "how": How.FETCHED,
        "edition": edition,
        "data_period": Period(as_at="2025-03-31"),
    }
    return Receipt.model_validate(fields | said)


def inputs_of(folder: Path, *files: tuple[Receipt, bytes]) -> Inputs:
    store = FolderStore(folder / "store")
    for given, content in files:
        path = folder / "given" / given.file_id
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        store.put(given.source_id, given.publisher_file, path)
    return Inputs(REGISTRY, [given for given, _ in files], store, folder / "work")


def held(folder: Path) -> dict[str, bytes]:
    return {
        path.relative_to(folder).as_posix(): path.read_bytes()
        for path in sorted(folder.rglob("*"))
        if path.is_file()
    }


HOMES_RECEIPT = receipt("made-up-homes", "homes.csv", HOMES)


def refused(inputs: Inputs, source_id: str, use: Use, edition: str | None = None) -> LockError:
    with pytest.raises(LockError) as stopped:
        inputs.open(source_id, use, edition=edition)
    assert CANARY not in str(stopped.value)
    assert str(inputs.work.parent) not in str(stopped.value)
    return stopped.value


def test_a_step_is_handed_a_checked_copy_of_a_file_with_its_receipt(tmp_path: Path):
    inputs = inputs_of(tmp_path, (HOMES_RECEIPT, HOMES))
    opened = inputs.open("made-up-homes", Use.SCORING)
    assert opened.receipt == HOMES_RECEIPT
    assert opened.path.read_bytes() == HOMES
    assert opened.path.is_relative_to(tmp_path / "work")
    assert inputs.opened == (opened,)


def test_a_file_asked_for_twice_is_one_file_a_step_was_handed(tmp_path: Path):
    inputs = inputs_of(tmp_path, (HOMES_RECEIPT, HOMES))
    assert inputs.open("made-up-homes", Use.SCORING) is inputs.open("made-up-homes", Use.ROUTING)
    assert len(inputs.opened) == 1


def test_nothing_is_written_to_the_store(tmp_path: Path):
    inputs = inputs_of(tmp_path, (HOMES_RECEIPT, HOMES))
    before = held(tmp_path / "store")
    inputs.open("made-up-homes", Use.SCORING)
    assert held(tmp_path / "store") == before


# A store that is reached over a network


class Reached:
    """A store that is reached over a network: it answers only while a socket may be made.

    It stands in for an object store. Behind it is a folder, so nothing here
    reaches a network. It counts what it was asked for.
    """

    kind = "object_store"

    def __init__(self, folder: Path) -> None:
        self.behind = FolderStore(folder)
        self.part = self.behind.part
        self.asked: list[str] = []

    def get(self, sha256: str, to: Path) -> Held:
        # What the guard of a step puts in the place of a socket is a class of its own.
        if socket.socket.__module__ == sockets_refused.__module__:
            raise StoreError("the store could not be reached")
        self.asked.append(sha256)
        return self.behind.get(sha256, to)

    def list(self) -> list[Held]:
        return self.behind.list()


def in_place_of_the_environment(store: Reached) -> Callable[[Mapping[str, str]], Store]:
    """What a step asks for its store, where it is to be given this one whatever is named."""

    def named(_: Mapping[str, str]) -> Store:
        return cast(Store, store)

    return named


def reached(tmp_path: Path, *files: tuple[Receipt, bytes]) -> tuple[Inputs, Reached]:
    inputs = inputs_of(tmp_path, *files)
    store = Reached(tmp_path / "store")
    inputs.store = cast(Store, store)
    return inputs, store


def test_every_file_is_copied_out_of_a_store_before_any_is_read(tmp_path: Path):
    """A step reads with no socket open, and an object store is reached over a network."""
    parks = receipt("made-up-parks", "parks.csv", PARKS)
    inputs, store = reached(tmp_path, (HOMES_RECEIPT, HOMES), (parks, PARKS))
    assert inputs.copy_out() == (2, len(HOMES) + len(PARKS))
    assert sorted(store.asked) == sorted([HOMES_RECEIPT.sha256, parks.sha256])
    with sockets_refused():
        opened = inputs.open("made-up-homes", Use.SCORING)
        assert opened.path.read_bytes() == HOMES
        assert inputs.open("made-up-parks", Use.DISPLAY).path.read_bytes() == PARKS
    # Nothing more was asked of the store: each copy was there, and was the file.
    assert len(store.asked) == 2


def test_a_file_that_was_not_copied_out_is_not_read_with_no_socket_open(tmp_path: Path):
    inputs, store = reached(tmp_path, (HOMES_RECEIPT, HOMES))
    with sockets_refused():
        error = refused(inputs, "made-up-homes", Use.SCORING)
    assert (error.rule, store.asked) == ("file_is_in_the_vault", [])


def test_a_file_that_is_copied_out_already_is_not_asked_for_again(tmp_path: Path):
    inputs, store = reached(tmp_path, (HOMES_RECEIPT, HOMES))
    assert inputs.copy_out() == (1, len(HOMES))
    assert inputs.copy_out() == (1, len(HOMES))
    assert len(store.asked) == 1


def test_a_copy_that_is_not_the_file_is_copied_out_again(tmp_path: Path):
    inputs, store = reached(tmp_path, (HOMES_RECEIPT, HOMES))
    inputs.copy_out()
    (copy,) = [path for path in (tmp_path / "work").rglob("*") if path.is_file()]
    copy.write_bytes(HOMES.replace(b"120", b"121"))
    inputs.copy_out()
    assert copy.read_bytes() == HOMES and len(store.asked) == 2


def test_a_file_the_store_does_not_hold_stops_the_copying_and_is_named_by_its_id(
    tmp_path: Path,
):
    inputs, _ = reached(tmp_path, (HOMES_RECEIPT, HOMES))
    (tmp_path / "store" / HOMES_RECEIPT.vault_key()).unlink()
    with pytest.raises(LockError) as stopped:
        inputs.copy_out()
    assert (stopped.value.rule, stopped.value.subject) == (
        "file_is_in_the_vault",
        HOMES_RECEIPT.file_id,
    )


def test_a_file_the_lock_does_not_name_is_not_copied_out(tmp_path: Path):
    inputs, store = reached(tmp_path, (HOMES_RECEIPT, HOMES))
    inputs.lock = Lock(
        release_id="lon-2026-10-02-01",
        built_at="2026-10-02T09:00:00Z",
        commit="0" * 40,
        inputs=(
            LockedInput(
                name=file_id_of("1" * 64),
                kind=InputKind.PUBLISHER_FILE,
                sha256="1" * 64,
                bytes=1,
                source_id="made-up-homes",
            ),
        ),
    )
    with pytest.raises(LockError) as stopped:
        inputs.copy_out()
    assert stopped.value.rule == "input_is_locked" and store.asked == []


def test_a_file_kept_for_the_audit_is_not_copied_out(tmp_path: Path):
    given = receipt("made-up-residents", "residents.csv", PARKS, use="audit_only")
    inputs, store = reached(tmp_path, (given, PARKS), (HOMES_RECEIPT, HOMES))
    assert inputs.copy_out() == (1, len(HOMES))
    assert store.asked == [HOMES_RECEIPT.sha256]


# The gate


def test_the_gate_is_asked_for_the_use_the_step_puts_the_file_to(tmp_path: Path):
    """The file was fetched for scoring. A step that would display it is refused."""
    inputs = inputs_of(tmp_path, (HOMES_RECEIPT, HOMES))
    error = refused(inputs, "made-up-homes", Use.DISPLAY)
    assert (error.rule, error.subject) == ("gate_refuses", "made-up-homes")
    assert "is not registered for display" in str(error)
    assert inputs.opened == () and not (tmp_path / "work").exists()


def test_a_source_the_registry_does_not_hold_is_refused(tmp_path: Path):
    given = receipt("made-up-rivers", "rivers.csv", PARKS)
    error = refused(inputs_of(tmp_path, (given, PARKS)), "made-up-rivers", Use.SCORING)
    assert error.rule == "gate_refuses"


def test_a_file_kept_for_the_audit_is_never_handed_to_a_step(tmp_path: Path):
    """The gate allows such a file for the audit. It is no input of a product release."""
    given = receipt("made-up-residents", "residents.csv", PARKS, use="audit_only")
    error = refused(inputs_of(tmp_path, (given, PARKS)), "made-up-residents", Use.AUDIT_ONLY)
    assert (error.rule, error.subject) == ("file_is_for_the_product", given.file_id)


def test_a_file_fetched_for_the_census_table_is_never_handed_to_a_step(tmp_path: Path):
    given = receipt("made-up-homes", "homes.csv", HOMES, use="census_table")
    error = refused(inputs_of(tmp_path, (given, HOMES)), "made-up-homes", Use.SCORING)
    assert error.rule == "file_is_for_the_product"


# The receipt


def test_a_file_with_no_receipt_is_not_read_though_the_store_holds_it(tmp_path: Path):
    inputs = inputs_of(tmp_path, (HOMES_RECEIPT, HOMES))
    inputs.receipts = []
    error = refused(inputs, "made-up-homes", Use.SCORING)
    assert (error.rule, error.subject) == ("input_has_one_receipt", "made-up-homes")


def test_two_files_of_one_source_are_told_apart_by_edition_or_by_name(tmp_path: Path):
    later = receipt("made-up-homes", "homes-2026.csv", HOMES_2026, edition="2026")
    inputs = inputs_of(tmp_path, (HOMES_RECEIPT, HOMES), (later, HOMES_2026))
    assert refused(inputs, "made-up-homes", Use.SCORING).rule == "input_has_one_receipt"
    assert inputs.open("made-up-homes", Use.SCORING, edition="2026").receipt == later
    by_name = inputs.open("made-up-homes", Use.SCORING, named=lambda name: name == "homes.csv")
    assert by_name.receipt == HOMES_RECEIPT
    assert refused(inputs, "made-up-homes", Use.SCORING, edition="2027").rule == (
        "input_has_one_receipt"
    )


def test_a_file_changed_in_the_store_is_refused(tmp_path: Path):
    inputs = inputs_of(tmp_path, (HOMES_RECEIPT, HOMES))
    kept = tmp_path / "store" / HOMES_RECEIPT.vault_key()
    kept.write_bytes(HOMES + b"U003,made up,1\n")
    error = refused(inputs, "made-up-homes", Use.SCORING)
    assert (error.rule, error.subject) == ("file_is_in_the_vault", HOMES_RECEIPT.file_id)
    assert not list((tmp_path / "work").rglob("homes.csv"))


def test_a_file_that_is_not_in_the_store_is_refused(tmp_path: Path):
    inputs = inputs_of(tmp_path, (HOMES_RECEIPT, HOMES))
    (tmp_path / "store" / HOMES_RECEIPT.vault_key()).unlink()
    assert refused(inputs, "made-up-homes", Use.SCORING).rule == "file_is_in_the_vault"


def test_a_copy_that_was_changed_is_taken_from_the_store_again(tmp_path: Path):
    inputs = inputs_of(tmp_path, (HOMES_RECEIPT, HOMES))
    first = inputs.open("made-up-homes", Use.SCORING).path
    first.write_bytes(b"changed\n")
    again = inputs_of(tmp_path, (HOMES_RECEIPT, HOMES))
    assert again.open("made-up-homes", Use.SCORING).path.read_bytes() == HOMES


# Every file of a source that gives a file for each part of the whole


def of_an_authority(number: int, day: str = "2026-09-16", rows: int = 2) -> tuple[Receipt, bytes]:
    """A made-up register of a made-up authority, and the receipt fetch writes of it.

    It is shaped as a file of the food hygiene register is, and says the day of
    its extract in its header. Every business in it has the one made-up name.
    """
    said = f"<!-- Made up for a test, of a made-up authority numbered {number}. -->"
    content = register(header_of(day), before=said, rows=rows)
    address = f"https://files.made-up.example/files/register-{number}.xml"
    given = receipt(
        "made-up-homes",
        f"register-{number}.xml",
        content,
        edition=f"extract of {day}",
        url=address,
        listed_url=address,
        edition_from={"where": "xml_header", "at": "Header/ExtractDate", "period_too": True},  # pyright: ignore[reportArgumentType]
        data_period={"as_at": day},  # pyright: ignore[reportArgumentType]
    )
    return given, content


def test_every_file_of_a_source_is_handed_over_in_the_order_of_their_names(tmp_path: Path):
    three = [of_an_authority(number) for number in (503, 501, 502)]
    inputs = inputs_of(tmp_path, *three)
    opened = inputs.open_each("made-up-homes", Use.SCORING)
    assert [one.receipt.publisher_file for one in opened] == [
        "register-501.xml",
        "register-502.xml",
        "register-503.xml",
    ]
    for one in opened:
        assert hashlib.sha256(one.path.read_bytes()).hexdigest() == one.receipt.sha256
    assert set(inputs.opened) == set(opened) and len(inputs.opened) == 3
    # Asked again, they are the same files, and a step was handed each once.
    assert inputs.open_each("made-up-homes", Use.ROUTING) == opened
    assert len(inputs.opened) == 3


def test_the_files_of_a_source_may_be_told_from_its_other_files_by_name(tmp_path: Path):
    inputs = inputs_of(tmp_path, of_an_authority(501), of_an_authority(502), (HOMES_RECEIPT, HOMES))
    opened = inputs.open_each(
        "made-up-homes", Use.SCORING, named=lambda name: name.startswith("register-")
    )
    assert [one.receipt.publisher_file for one in opened] == [
        "register-501.xml",
        "register-502.xml",
    ]
    assert HOMES_RECEIPT not in [one.receipt for one in inputs.opened]


def test_a_step_never_picks_one_of_two_editions_of_a_file(tmp_path: Path):
    """The build says which edition it takes, and hands a step that one alone."""
    older, newer = of_an_authority(501), of_an_authority(501, "2026-09-17", rows=3)
    given_both = inputs_of(tmp_path / "both", older, newer, of_an_authority(502))
    with pytest.raises(LockError) as stopped:
        given_both.open_each("made-up-homes", Use.SCORING)
    assert (stopped.value.rule, stopped.value.subject) == ("input_has_one_receipt", "made-up-homes")
    assert given_both.opened == () and not (tmp_path / "both" / "work").exists()
    # A step that names the edition is handed the files of that edition.
    named = given_both.open_each("made-up-homes", Use.SCORING, edition="extract of 2026-09-17")
    assert [one.receipt for one in named] == [newer[0]]
    # Given the one a build took, the step is handed it.
    given_one = inputs_of(tmp_path / "one", newer, of_an_authority(502))
    assert [one.receipt.edition for one in given_one.open_each("made-up-homes", Use.SCORING)] == [
        "extract of 2026-09-17",
        "extract of 2026-09-16",
    ]


def test_a_source_with_no_file_among_those_given_is_refused(tmp_path: Path):
    inputs = inputs_of(tmp_path, (HOMES_RECEIPT, HOMES))
    with pytest.raises(LockError) as stopped:
        inputs.open_each("made-up-homes", Use.SCORING, named=lambda name: name.endswith(".xml"))
    assert stopped.value.rule == "input_has_one_receipt"
    with pytest.raises(LockError) as stopped:
        inputs.open_each("made-up-homes", Use.SCORING, edition="2026")
    assert stopped.value.rule == "input_has_one_receipt"
    inputs.receipts = []
    with pytest.raises(LockError) as stopped:
        inputs.open_each("made-up-homes", Use.SCORING)
    assert stopped.value.rule == "input_has_one_receipt"


def test_the_gate_is_asked_before_any_file_of_a_source_is_looked_for(tmp_path: Path):
    inputs = inputs_of(tmp_path, of_an_authority(501), of_an_authority(502))
    with pytest.raises(LockError) as stopped:
        inputs.open_each("made-up-homes", Use.DISPLAY)
    assert (stopped.value.rule, stopped.value.subject) == ("gate_refuses", "made-up-homes")
    assert inputs.opened == () and not (tmp_path / "work").exists()


def test_each_file_of_a_source_is_held_to_the_lock(tmp_path: Path):
    first, second = of_an_authority(501), of_an_authority(502)
    inputs = inputs_of(tmp_path, first, second)
    inputs.lock = lock_of(first[0])
    with pytest.raises(LockError) as stopped:
        inputs.open_each("made-up-homes", Use.SCORING)
    assert (stopped.value.rule, stopped.value.subject) == ("input_is_locked", second[0].file_id)
    inputs.lock = lock_of(first[0], second[0])
    assert len(inputs.open_each("made-up-homes", Use.SCORING)) == 2


# The lock


def lock_of(*receipts: Receipt, packages: str | None = None) -> Lock:
    named = [
        LockedInput(
            name=given.file_id,
            kind=InputKind.PUBLISHER_FILE,
            sha256=given.sha256,
            bytes=given.bytes,
            source_id=given.source_id,
        )
        for given in receipts
    ]
    return Lock(
        release_id="lon-2026-09-23-01",
        built_at="2026-09-23T00:00:00Z",
        commit="0123456789abcdef0123456789abcdef01234567",
        packages=packages,
        inputs=tuple(sorted(named, key=lambda locked: locked.name)),
    )


def test_a_file_the_lock_names_is_handed_over_and_one_it_does_not_is_refused(tmp_path: Path):
    parks = receipt("made-up-parks", "parks.csv", PARKS)
    inputs = inputs_of(tmp_path, (HOMES_RECEIPT, HOMES), (parks, PARKS))
    inputs.lock = lock_of(HOMES_RECEIPT)
    assert inputs.open("made-up-homes", Use.SCORING).path.read_bytes() == HOMES
    error = refused(inputs, "made-up-parks", Use.DISPLAY)
    assert (error.rule, error.subject) == ("input_is_locked", parks.file_id)
    assert not list((tmp_path / "work").rglob("parks.csv"))


def test_a_build_is_a_development_build_until_its_lock_holds_its_packages(tmp_path: Path):
    inputs = inputs_of(tmp_path, (HOMES_RECEIPT, HOMES))
    assert inputs.development
    inputs.lock = lock_of(HOMES_RECEIPT)
    assert inputs.development
    inputs.lock = lock_of(HOMES_RECEIPT, packages="0" * 64)
    assert not inputs.development


# Reading a table


def test_a_table_is_read_without_the_mark_at_its_start(tmp_path: Path):
    opened = inputs_of(tmp_path, (HOMES_RECEIPT, HOMES)).open("made-up-homes", Use.SCORING)
    with opened.text() as text:
        rows = list(opened.rows(text, ("unit_code", "homes")))
    assert rows == [{"unit_code": "U001", "homes": "120"}, {"unit_code": "U002", "homes": "80"}]


def test_a_row_holds_the_columns_a_step_named_and_no_other(tmp_path: Path):
    opened = inputs_of(tmp_path, (HOMES_RECEIPT, HOMES)).open("made-up-homes", Use.SCORING)
    with opened.text() as text:
        for row in opened.rows(text, ("unit_code",)):
            assert set(row) == {"unit_code"} and CANARY not in row.values()


def test_a_table_inside_a_zip_is_read_by_the_end_of_its_name(tmp_path: Path):
    packed = zipped("homes-2025.csv", HOMES)
    given = receipt("made-up-homes", "homes.zip", packed)
    opened = inputs_of(tmp_path, (given, packed)).open("made-up-homes", Use.SCORING)
    assert opened.member(".csv") == "made-up/homes-2025.csv"
    with opened.text(".csv") as text:
        assert [row["homes"] for row in opened.rows(text, ("homes",))] == ["120", "80"]


@pytest.mark.parametrize(
    ("content", "inside", "columns", "why"),
    [
        (HOMES, None, ("unit_code", "flats"), "a column is missing"),
        (HOMES, ".csv", ("homes",), "it is not a zip"),
        (zipped("homes.csv", HOMES), ".xlsx", ("homes",), MEMBER),
        (zipped("homes.csv", HOMES), "", ("homes",), MEMBER),
        (b"unit_code,homes\nU001\n", None, ("homes",), "a row is short"),
        (b"unit_code,homes\n\xff\xfe,1\n", None, ("homes",), "it could not be read as text"),
    ],
    ids=["column", "not-a-zip", "no-member", "two-members", "short-row", "not-text"],
)
def test_a_file_that_is_not_what_a_step_reads_stops_it_and_is_not_repeated(
    tmp_path: Path, content: bytes, inside: str | None, columns: tuple[str, ...], why: str
):
    given = receipt("made-up-homes", "homes.csv", content)
    opened = inputs_of(tmp_path, (given, content)).open("made-up-homes", Use.SCORING)
    with pytest.raises(LockError) as stopped, opened.text(inside) as text:
        list(opened.rows(text, columns))
    assert (stopped.value.rule, stopped.value.subject) == ("input_is_as_described", given.file_id)
    assert str(stopped.value).endswith(f": {why} [input_is_as_described]")
    assert CANARY not in str(stopped.value) and "flats" not in str(stopped.value)


# The period and the day of several files


def test_the_period_of_several_files_runs_from_the_first_day_of_any_to_the_last():
    census = receipt("made-up-homes", "a.csv", b"a", data_period={"as_at": "2021-03-21"})  # pyright: ignore[reportArgumentType]
    stock = receipt("made-up-homes", "b.csv", b"b", retrieved_at="2026-09-24T08:00:00Z")
    assert period_of([census, stock]) == Period(start="2021-03-21", end="2025-03-31")
    assert period_of([stock]) == Period(as_at="2025-03-31")
    assert retrieved_on([census, stock]) == "2026-09-24"
