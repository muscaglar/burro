"""Which receipt a build takes of a file that states its own edition.

A publisher that replaces a file under one address leaves the file itself to
say which file it is. The list states no edition for it, so nothing the list
states pairs it with a receipt. These hold a build to the rule that does:

    the receipts of an item   those fetch could have written from the item
    the one a build takes     the edition it is told to, or the newest by the
                              day the file states
    what the lock says        the item, and the edition that was taken
    what stops a build        two receipts of one item that state one edition,
                              and an edition that is named and has no receipt

Every file here is made up: a register of a made-up authority, whose businesses
have made-up names. Nothing is fetched. The vault is a table of sizes held in
the test, and the registry is two made-up entries.
"""

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from burro_pipeline.evidence.cli import main
from burro_pipeline.evidence.lock import (
    InputKind,
    Lock,
    LockedInput,
    LockError,
    Taken,
    locked,
    read_lock,
    seal,
    stated_in,
    take,
)
from burro_pipeline.evidence.receipt import EditionFrom, Period, Receipt, Where, clean_url
from burro_pipeline.evidence.record import file_id_of
from burro_pipeline.fetch.run import written_down
from burro_pipeline.fetch.sources import LISTS, Listed, load_list
from burro_pipeline.registry import Registry, Use
from public_log import is_public
from pydantic import ValidationError

from ..fetch.dated_support import header_of, register
from .support import NO_REPOSITORY, as_toml, list_as_toml, listed, registered, registry_of

Printed = pytest.CaptureFixture[str]

RELEASE, BUILT_AT = "lon-2026-09-25-01", "2026-09-25T00:00:00Z"
COMMIT = "0123456789abcdef0123456789abcdef01234567"
# A string found nowhere else. If a refusal repeats what it was handed, this shows up in it.
CANARY = "Zzyzx Parva"
SOURCE = "made-up-register"
ADDRESS = "https://files.made-up.example/files/register-501.xml"
IN_THE_HEADER = {
    "where": "xml_header",
    "at": "Header/ExtractDate",
    "words": "extract of",
    "period_too": True,
}
THE_DAY_RETRIEVED = {"where": "retrieved", "at": "", "words": "retrieved", "period_too": True}
LAST_CHANGE = {
    "where": "geopackage",
    "at": "gpkg_contents.last_change",
    "words": "last changed",
    "period_too": False,
}
RUNS_TO = {
    "where": "street_extract",
    "at": "OSMHeader.osmosis_replication_timestamp",
    "period_too": True,
}
OLDER, NEWER, NEWEST = "2026-09-16", "2026-09-17", "2026-10-01"
HOMES = b"oa21cd,homes\nE00000001,131\n"


def item(name: str = "register-501", **changed: object) -> Listed:
    """A file of a list that states no edition, and says where the file states its own."""
    fields: dict[str, object] = {
        "item": name,
        "source_id": SOURCE,
        "use": "scoring",
        "what": "Made-up register of a made-up authority",
        "format": "xml",
        "page": "https://made-up.example/register",
        "url": ADDRESS.replace("register-501", name),
        "max_bytes": 1_000_000,
        "edition_from": IN_THE_HEADER,
        **changed,
    }
    return Listed.model_validate(fields)


def receipt(
    day: str, of: Listed | None = None, rows: int = 2, retrieved_at: str = "", **changed: Any
) -> Receipt:
    """The receipt fetch writes of a made-up register that states a day in its header."""
    of = of or item()
    assert of.edition_from is not None
    content = register(header_of(day), rows=rows)
    sha256 = hashlib.sha256(content).hexdigest()
    fields: dict[str, Any] = {
        "file_id": file_id_of(sha256),
        "source_id": of.source_id,
        "use": of.use,
        "publisher_file": of.url.rsplit("/", 1)[-1],
        "url": of.url,
        "listed_url": of.url,
        "sha256": sha256,
        "bytes": len(content),
        "retrieved_at": retrieved_at or "2026-09-24T09:12:31Z",
        "how": "fetched",
        "edition": of.edition_from.written(day),
        "edition_from": of.edition_from.in_a_receipt(),
        "data_period": Period(as_at=day[:10]),
    }
    return Receipt.model_validate(fields | changed)


def stated(content: bytes = HOMES) -> Receipt:
    """The receipt of a file whose edition the list states, as every file of a first build."""
    sha256 = hashlib.sha256(content).hexdigest()
    return Receipt(
        file_id=file_id_of(sha256),
        source_id="made-up-homes",
        use=Use.SCORING,
        publisher_file="made-up-homes.csv",
        url="https://files.made-up.example/files/made-up-homes.csv",
        sha256=sha256,
        bytes=len(content),
        retrieved_at="2026-09-23T09:12:31Z",
        how="fetched",  # pyright: ignore[reportArgumentType]
        edition="2025",
        data_period=Period(as_at="2025-03-31"),
    )


def registry() -> Registry:
    return registry_of(registered(SOURCE, Use.SCORING), registered("made-up-homes", Use.SCORING))


def sealed(
    receipts: tuple[Receipt, ...],
    named: tuple[Listed, ...] = (),
    editions: dict[str, str] | None = None,
) -> Lock:
    return seal(
        RELEASE,
        BUILT_AT,
        COMMIT,
        receipts,
        {found.vault_key(): found.bytes for found in receipts},
        registry(),
        NO_REPOSITORY,
        listed=named or (item(),),
        editions=editions,
    )


def refused(*given: Any, **more: Any) -> LockError:
    with pytest.raises(LockError) as caught:
        sealed(*given, **more)
    assert CANARY not in str(caught.value) and "\n" not in str(caught.value)
    return caught.value


def of(lock: Lock, found: Receipt) -> LockedInput:
    (one,) = [held for held in lock.inputs if held.name == found.file_id]
    return one


# Which receipts are of an item


def test_a_receipt_is_of_an_item_when_fetch_could_have_written_it_from_the_item():
    assert stated_in(receipt(OLDER), item()) == OLDER
    # It was fetched from the address the list gives, however the publisher handed it on.
    moved = receipt(OLDER, url="https://cdn.made-up.example/held/register-501.xml")
    assert stated_in(moved, item()) == OLDER


@pytest.mark.parametrize(
    "other",
    [
        {"source_id": "made-up-homes"},
        {"use": "display"},
        {"listed_url": ADDRESS.replace("501", "502")},
        {"listed_url": None},
        {"edition_from": None},
        {"edition_from": EditionFrom(where=Where.RETRIEVED, at="", period_too=True)},
        {"edition": f"extracted on {OLDER}"},
        {"edition": OLDER},
        {"edition": "extract of 2026"},
        {"edition": f"extract of {OLDER} {CANARY}"},
    ],
    ids=lambda other: " and ".join(other),
)
def test_a_receipt_that_says_anything_else_of_its_file_is_not_of_the_item(other: dict[str, Any]):
    assert stated_in(receipt(OLDER, **other), item()) is None


def test_a_receipt_is_of_no_item_whose_edition_the_list_states():
    of_the_list = listed(stated(), "homes")
    assert stated_in(stated(), of_the_list) is None
    assert stated_in(receipt(OLDER), of_the_list) is None


def test_where_the_file_gives_the_edition_alone_the_period_is_the_lists():
    """The day a GeoPackage was last changed is about the file, so the list states the period."""
    period = {"as_at": "2025-12-22"}
    centres = item("centres", format="gpkg", edition_from=LAST_CHANGE, data_period=period)
    kept = receipt("2025-12-22", centres, data_period=Period(as_at="2025-12-22"))
    assert kept.edition == "last changed 2025-12-22"
    assert stated_in(kept, centres) == "2025-12-22"
    of_another_period = receipt("2025-12-22", centres, data_period=Period(as_at="2025-06"))
    assert stated_in(of_another_period, centres) is None


def test_a_time_is_read_as_a_day_is():
    streets = item("streets", format="other", edition_from=RUNS_TO)
    kept = receipt("2026-09-22T20:22:59Z", streets)
    assert kept.edition == "2026-09-22T20:22:59Z"
    assert stated_in(kept, streets) == "2026-09-22T20:22:59Z"


# The lists that hold no address yet, by name: a list cannot lose its addresses unseen, and
# one that gains its first is taken off here.
NO_ADDRESS_YET = frozenset({"m5-journeys"})


@pytest.mark.parametrize("name", sorted(path.stem for path in LISTS.glob("*.toml")))
def test_the_address_of_an_item_is_compared_as_fetch_writes_it_in_a_receipt(name: str):
    """A receipt holds the list's address as fetch wrote it down. A build compares the same."""
    files = [file for file in load_list(name).files if file.url]
    assert bool(files) != (name in NO_ADDRESS_YET)
    for file in files:
        assert clean_url(file.url) == written_down(file.url, file.url), file.item


# Which one a build takes


def test_with_one_edition_the_build_takes_it():
    (one,), without = take([receipt(OLDER), stated()], [item()])
    assert one == Taken("register-501", receipt(OLDER), (), named=False)
    assert without == ()


def test_a_build_takes_the_newest_by_the_day_the_file_states():
    # The older file was retrieved last, and sorts last by its id and first by its name.
    older = receipt(OLDER, retrieved_at="2026-11-30T09:12:31Z")
    newer, newest = receipt(NEWER), receipt(NEWEST)
    for given in ([older, newer, newest], [newest, older, newer], [newer, newest, older]):
        (one,), _ = take(given, [item()])
        assert (one.receipt, one.named) == (newest, False)
        assert one.passed_over == (older, newer)


def test_the_day_is_the_one_the_file_states_and_never_the_day_it_was_retrieved():
    early = receipt(NEWER, retrieved_at="2026-09-18T00:00:00Z")
    late = receipt(OLDER, retrieved_at="2026-12-24T00:00:00Z")
    (one,), _ = take([late, early], [item()])
    assert one.receipt == early


def test_a_file_with_no_date_is_ordered_by_the_day_it_was_first_retrieved():
    report = item("report", format="csv", edition_from=THE_DAY_RETRIEVED)
    first, second = receipt("2026-09-24", report), receipt("2026-10-02", report, rows=3)
    assert second.edition == "retrieved 2026-10-02"
    (one,), _ = take([second, first], [report])
    assert (one.receipt, one.passed_over) == (second, (first,))


def test_a_build_that_is_told_which_edition_takes_that_one():
    older, newer = receipt(OLDER), receipt(NEWER)
    (one,), _ = take([older, newer], [item()], {"register-501": older.edition})
    assert one == Taken("register-501", older, (newer,), named=True)
    # The newest may be named too. It is then taken because it was named.
    (one,), _ = take([older, newer], [item()], {"register-501": newer.edition})
    assert one == Taken("register-501", newer, (older,), named=True)


def test_each_file_of_a_list_is_taken_by_itself():
    """The register is a file for each authority, and each is extracted on a day of its own."""
    first, second = item("register-501"), item("register-502")
    receipts = [
        receipt(OLDER, first),
        receipt(NEWER, first),
        receipt(OLDER, second, rows=4),
    ]
    found, without = take(receipts, [first, second], {"register-501": f"extract of {OLDER}"})
    assert [(one.item, one.receipt.edition, one.named) for one in found] == [
        ("register-501", f"extract of {OLDER}", True),
        ("register-502", f"extract of {OLDER}", False),
    ]
    assert without == ()


def test_a_file_with_no_receipt_is_said_to_have_none_and_nothing_stands_in():
    first, second = item("register-501"), item("register-502")
    found, without = take([receipt(OLDER, first)], [first, second])
    assert [one.item for one in found] == ["register-501"]
    assert without == ("register-502",)


# What stops a build


def test_two_receipts_of_one_file_that_state_one_edition_stop_the_build():
    one, other = receipt(OLDER), receipt(OLDER, rows=3)
    assert (one.edition, one.listed_url) == (other.edition, other.listed_url)
    assert one.sha256 != other.sha256
    for given in ((one, other), (other, one), (one, other, receipt(NEWER, rows=4))):
        error = refused(given)
        assert error.rule == "listed_file_has_one_receipt"
        assert error.subject in (one.file_id, other.file_id)
    # Naming the edition does not settle which of the two files is meant.
    assert refused((one, other), editions={"register-501": one.edition}).rule == (
        "listed_file_has_one_receipt"
    )


def test_an_edition_that_is_named_and_has_no_receipt_stops_the_build():
    error = refused((receipt(OLDER),), editions={"register-501": f"extract of {NEWER}"})
    assert (error.rule, error.subject) == (
        "named_edition_has_a_receipt",
        "the edition named for register-501",
    )
    assert NEWER not in str(error)
    # What was named is never repeated: it may be anything.
    error = refused((receipt(OLDER),), editions={"register-501": CANARY})
    assert error.rule == "named_edition_has_a_receipt"


@pytest.mark.parametrize("name", ["homes", "register-999", CANARY])
def test_an_edition_named_for_a_file_that_does_not_state_its_own_stops_the_build(name: str):
    """A file whose edition the list states has the one edition. There is nothing to name."""
    named = (item(), listed(stated(), "homes"))
    error = refused((receipt(OLDER), stated()), named, editions={name: "2025"})
    assert (error.rule, error.subject) == (
        "named_edition_has_a_receipt",
        "an edition that was named",
    )


def test_a_seal_is_refused_when_a_file_that_states_its_own_edition_has_no_receipt():
    error = refused((stated(),), (item(), listed(stated(), "homes")))
    assert (error.rule, error.subject) == ("listed_file_has_a_receipt", "register-501")


def test_a_receipt_that_is_of_no_file_of_the_list_is_still_refused():
    """An edition that is passed over is of a listed file. A receipt of another address is not."""
    elsewhere = receipt(OLDER, rows=5, listed_url=ADDRESS.replace("501", "777"))
    error = refused((receipt(OLDER), elsewhere))
    assert (error.rule, error.subject) == ("receipt_is_listed", elsewhere.file_id)


# What the lock says


def test_the_lock_says_which_file_of_the_list_it_took_and_which_edition():
    taken, other = receipt(NEWER), stated()
    lock = sealed((taken, other), (item(), listed(other, "homes")))
    assert (of(lock, taken).item, of(lock, taken).edition) == ("register-501", taken.edition)
    written = json.loads(lock.canonical())
    (said,) = [held for held in written["inputs"] if held["name"] == taken.file_id]
    assert (said["item"], said["edition"]) == ("register-501", f"extract of {NEWER}")
    # It holds no address and no day of a fetch, as no lock does.
    assert "https://" not in lock.canonical().decode()
    assert taken.retrieved_at[:10] not in lock.canonical().decode()


def test_the_lock_of_a_file_whose_edition_the_list_states_is_written_as_it_was():
    """The list states that edition, and the lock names the commit the list is read at."""
    other = stated()
    lock = sealed((other,), (listed(other, "homes"),))
    (said,) = json.loads(lock.canonical())["inputs"]
    assert sorted(said) == ["bytes", "kind", "name", "sha256", "source_id"]
    assert (of(lock, other).item, of(lock, other).edition) == (None, None)
    assert locked(other) == LockedInput.model_validate(said)


def test_an_edition_that_is_passed_over_is_not_sealed_and_is_not_refused():
    older, newer = receipt(OLDER), receipt(NEWER)
    lock = sealed((older, newer))
    assert lock.holds(newer.file_id) and not lock.holds(older.file_id)
    assert len(lock.inputs) == 1


def test_sealed_twice_from_the_same_receipts_the_lock_is_the_same_bytes():
    given = (receipt(OLDER), receipt(NEWER), stated())
    named = (item(), listed(stated(), "homes"))
    first = sealed(given, named)
    assert sealed(given[::-1], named[::-1]).canonical() == first.canonical()
    assert sealed((given[1], given[2], given[0]), named).digest() == first.digest()


def test_after_a_newer_file_arrives_the_lock_names_the_newer_unless_told_to_take_the_older():
    older, newer = receipt(OLDER), receipt(NEWER)
    before = sealed((older,))
    assert of(before, older).edition == f"extract of {OLDER}"
    # The newer file arrives, and the same build is sealed again.
    after = sealed((older, newer))
    assert of(after, newer).edition == f"extract of {NEWER}"
    assert after.digest() != before.digest()
    # Told to take the edition the first lock names, it seals the first lock again.
    named = {held.item: held.edition for held in before.inputs if held.item and held.edition}
    assert named == {"register-501": f"extract of {OLDER}"}
    assert sealed((older, newer), editions=named).canonical() == before.canonical()


def test_a_lock_reads_back_as_it_was_written():
    lock = sealed((receipt(OLDER), stated()), (item(), listed(stated(), "homes")))
    assert Lock.model_validate_json(lock.canonical()) == lock


@pytest.mark.parametrize(
    "fields",
    [
        {"item": "register-501"},
        {"edition": f"extract of {OLDER}"},
        {"item": "Register 501", "edition": f"extract of {OLDER}"},
        {"item": "register-501", "edition": ""},
    ],
    ids=["no edition", "no file of the list", "no name a list gives", "an empty edition"],
)
def test_a_lock_names_a_file_of_the_list_and_its_edition_together(fields: dict[str, str]):
    whole = locked(receipt(OLDER)).model_dump(mode="json")
    with pytest.raises(ValidationError):
        LockedInput.model_validate(whole | fields)


def test_only_a_publishers_file_has_an_edition():
    areas = {
        "name": "gazetteer/oa_to_area.csv",
        "kind": InputKind.GAZETTEER,
        "sha256": hashlib.sha256(b"oa21cd,area_id\n").hexdigest(),
        "bytes": 15,
    }
    assert LockedInput.model_validate(areas).edition is None
    with pytest.raises(ValidationError):
        LockedInput.model_validate(
            areas | {"item": "register-501", "edition": f"extract of {OLDER}"}
        )


# The step `seal`, run as a person runs it


def a_build(folder: Path, *receipts: Receipt) -> list[str]:
    """The arguments that seal a made-up register and a made-up table of homes."""
    for found in (*receipts, stated()):
        path = folder / found.path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(found.canonical())
    (folder / "registry.toml").write_text(as_toml(registry()), encoding="utf-8")
    listing = {found.vault_key(): found.bytes for found in (*receipts, stated())}
    (folder / "vault.json").write_text(json.dumps(listing), encoding="utf-8")
    where = ", ".join(f"{name} = {json.dumps(value)}" for name, value in IN_THE_HEADER.items())
    of_the_register = "\n".join(
        [
            "[[file]]",
            'item = "register-501"',
            f'source_id = "{SOURCE}"',
            'use = "scoring"',
            'what = "Made-up register of a made-up authority"',
            'format = "xml"',
            'page = "https://made-up.example/register"',
            f'url = "{ADDRESS}"',
            "max_bytes = 1_000_000",
            f"edition_from = {{ {where} }}",
            "",
        ]
    )
    written = f"{list_as_toml([listed(stated(), 'homes')])}\n{of_the_register}"
    (folder / "made-up.toml").write_text(written, encoding="utf-8")
    assert load_list(folder / "made-up.toml").files[1] == item()
    return [
        "seal",
        *("--release-id", RELEASE, "--built-at", BUILT_AT, "--commit", COMMIT),
        *("--receipts", str(folder / "data" / "receipts")),
        *("--list", str(folder / "made-up.toml")),
        *("--vault-listing", str(folder / "vault.json")),
        *("--registry", str(folder / "registry.toml"), "--root", str(folder)),
        *("--out", str(folder / "locks")),
    ]


def said(capsys: Printed) -> tuple[list[str], str]:
    out = capsys.readouterr()
    assert all(is_public(line) for line in out.out.splitlines())
    assert CANARY not in out.out + out.err
    return out.out.splitlines(), out.err


def test_seal_says_how_many_files_it_took_by_their_own_edition(tmp_path: Path, capsys: Printed):
    assert main(a_build(tmp_path, receipt(OLDER))) == 0
    lock = read_lock(tmp_path / "locks" / f"{RELEASE}.json")
    lines, words = said(capsys)
    assert lines == [
        f"step=seal status=ok release={RELEASE} inputs=2 own_edition=1 named=0 passed_over=0 "
        f"development=1 lock_sha256={lock.digest()}"
    ]
    # One edition has a receipt, so there was nothing to choose, and nothing is noted.
    assert words == ""
    assert of(lock, receipt(OLDER)).edition == f"extract of {OLDER}"


def test_seal_takes_the_newest_and_says_that_it_passed_one_over(tmp_path: Path, capsys: Printed):
    assert main(a_build(tmp_path, receipt(OLDER), receipt(NEWER))) == 0
    lock = read_lock(tmp_path / "locks" / f"{RELEASE}.json")
    lines, words = said(capsys)
    assert " inputs=2 own_edition=1 named=0 passed_over=1 " in lines[0]
    assert words.splitlines() == [
        "note: register-501 has 2 editions with a receipt. This build takes the newest, and "
        "its lock says which. To take another, give --edition register-501=EDITION"
    ]
    assert lock.holds(receipt(NEWER).file_id) and not lock.holds(receipt(OLDER).file_id)


def test_seal_is_told_to_take_the_older_and_seals_the_lock_of_the_day_before(
    tmp_path: Path, capsys: Printed
):
    before = tmp_path / "before"
    assert main(a_build(before, receipt(OLDER))) == 0
    after = tmp_path / "after"
    told = ["--edition", f"register-501=extract of {OLDER}"]
    assert main([*a_build(after, receipt(OLDER), receipt(NEWER)), *told]) == 0
    name = f"{RELEASE}.json"
    assert (after / "locks" / name).read_bytes() == (before / "locks" / name).read_bytes()
    lines, words = said(capsys)
    assert " inputs=2 own_edition=1 named=1 passed_over=1 " in lines[1]
    assert "This build takes the one that was named" in words


@pytest.mark.parametrize(
    ("receipts", "told", "rule"),
    [
        ((OLDER, OLDER), (), "listed_file_has_one_receipt"),
        ((OLDER,), (f"register-501=extract of {NEWER}",), "named_edition_has_a_receipt"),
        ((OLDER,), ("homes=2025",), "named_edition_has_a_receipt"),
        ((), (), "listed_file_has_a_receipt"),
    ],
    ids=["one edition twice", "an edition with no receipt", "no such file", "no receipt"],
)
def test_seal_stops_and_writes_no_lock(
    receipts: tuple[str, ...],
    told: tuple[str, ...],
    rule: str,
    tmp_path: Path,
    capsys: Printed,
):
    given = [receipt(day, rows=2 + n) for n, day in enumerate(receipts)]
    arguments = [*a_build(tmp_path, *given), *(word for one in told for word in ("--edition", one))]
    assert main(arguments) == 2
    lines, words = said(capsys)
    assert len(lines) == 1 and lines[0].startswith(f"step=seal status=refused {rule}=1")
    assert words.count("\n") == 1 and f"[{rule}]" in words
    assert NEWER not in words
    assert not (tmp_path / "locks").exists()


@pytest.mark.parametrize(
    "told",
    [
        ["--edition", "register-501"],
        ["--edition", f"=extract of {OLDER}"],
        ["--edition", f"{CANARY}="],
        ["--edition", "register-501=a", "--edition", "register-501=b"],
    ],
    ids=["no edition", "no file", "nothing after the sign", "one file twice"],
)
def test_seal_is_told_an_edition_as_the_name_of_a_file_and_its_edition(
    told: list[str], tmp_path: Path, capsys: Printed
):
    with pytest.raises(SystemExit) as stopped:
        main([*a_build(tmp_path, receipt(OLDER)), *told])
    assert stopped.value.code == 2
    out = capsys.readouterr()
    assert out.out == "" and CANARY not in out.err
    assert not (tmp_path / "locks").exists()
