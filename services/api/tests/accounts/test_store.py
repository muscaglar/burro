"""Where accounts are kept: one file, one small layer over it, and no statement made of strings.

Every name and address here is made up.
"""

import ast
import os
import sqlite3
import stat
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import burro_api
import pytest
from burro_api.accounts import store as layer
from burro_api.accounts.events import Event, Outcome
from burro_api.accounts.store import (
    VERSION,
    Account,
    Held,
    Kept,
    Link,
    Signed,
    Store,
    StoreError,
)
from burro_api.accounts.wire import Browser, PreferencesBody, Switch

AT = "2026-09-26T12:00:00Z"
LATER = "2026-09-26T12:15:00Z"
SPEC = '{"schema_version":1}'
TABLES = {
    "accounts",
    "login_tokens",
    "sessions",
    "saved_searches",
    "recent_searches",
    "preferences",
    "audit_events",
}


def account(number: int) -> Account:
    return Account(
        id=f"account-{number:014d}", email=f"p{number}@example.org", made_at=AT, adult_at=AT
    )


def signed(number: int, of: Account) -> Signed:
    return Signed(
        token_hash=f"{number:064x}",
        public_id=f"session-{number:014d}",
        account_id=of.id,
        made_at=AT,
        seen_at=AT,
        ends_at=LATER,
        revoked_at=None,
        browser=Browser.FIREFOX.value,
    )


def kept(number: int) -> Kept:
    return Kept(
        id=f"search-{number:015d}", spec=SPEC, release_id="syn-2026-09-23-01", name="n", made_at=AT
    )


def link(number: int, email: str, made_at: str = AT, binding: str = "b" * 64) -> Link:
    return Link(
        token_hash=f"{number:064x}",
        email=email,
        made_at=made_at,
        ends_at=LATER,
        used_at=None,
        binding_hash=binding,
    )


@pytest.fixture
def store(tmp_path: Path) -> Store:
    return Store(tmp_path / "accounts.db")


def with_everything(store: Store, number: int) -> Account:
    """An account with one of everything that can be kept under it."""
    made = account(number)
    with store.writing() as held:
        held.add_account(made)
        held.add_session(signed(number, made))
        held.add_search(made.id, kept(number))
        held.add_recent(made.id, kept(number))
        held.set_preference(made.id, "keep_recent", Switch.ON.value)
        held.add_event(made.id, Event.SESSION_CREATED.value, Outcome.OK.value, AT)
        held.add_link(link(number, made.email))
    return made


def counts(store: Store) -> dict[str, int]:
    probe = sqlite3.connect(store.path)
    try:
        return {
            # The names are this test's own, and no statement of the service is made so.
            table: probe.execute(f"SELECT count(*) FROM {table}").fetchone()[0]  # noqa: S608
            for table in sorted(TABLES)
        }
    finally:
        probe.close()


# The file.


def test_the_file_is_made_for_its_owner_alone_and_is_set_as_the_design_says(store: Store):
    assert stat.S_IMODE(store.path.stat().st_mode) == 0o600

    found = store.settings()

    assert found == {
        "journal_mode": "wal",
        "foreign_keys": 1,
        "busy_timeout": 5000,
        "secure_delete": 1,
        "trusted_schema": 0,
        "user_version": VERSION,
    }


def test_the_layout_holds_the_seven_tables_and_each_holds_its_columns_to_their_kind(store: Store):
    probe = sqlite3.connect(store.path)
    rows = probe.execute("SELECT name, sql FROM sqlite_master WHERE type = 'table'").fetchall()
    probe.close()

    assert {name for name, _ in rows} == TABLES
    # A strict table takes no text where a number belongs, and no number where text does.
    assert all(sql.rstrip().endswith("STRICT") for _, sql in rows)


def test_opening_the_file_again_changes_nothing_and_loses_nothing(tmp_path: Path):
    first = Store(tmp_path / "accounts.db")
    made = with_everything(first, 1)
    before = counts(first)
    first.close()

    again = Store(tmp_path / "accounts.db")

    assert counts(again) == before and again.settings()["user_version"] == VERSION
    with again.reading() as held:
        assert held.account(made.id) == made


def test_a_file_of_a_later_layout_is_refused_and_is_left_as_it_was(tmp_path: Path):
    path = tmp_path / "accounts.db"
    Store(path).close()
    probe = sqlite3.connect(path)
    probe.execute("PRAGMA user_version = 99")
    probe.commit()
    probe.close()

    with pytest.raises(StoreError) as refused:
        Store(path)

    assert refused.value.rule == "newer_layout"
    probe = sqlite3.connect(path)
    assert probe.execute("PRAGMA user_version").fetchone()[0] == 99
    probe.close()


def test_a_change_to_the_layout_that_fails_leaves_the_file_as_it_was(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    path = tmp_path / "accounts.db"
    Store(path).close()
    broken = ("CREATE TABLE more (id TEXT PRIMARY KEY) STRICT", "CREATE TABLE more (id TEXT)")
    monkeypatch.setattr(layer, "CHANGES", (*layer.CHANGES, broken))

    with pytest.raises(StoreError) as refused:
        Store(path)

    assert refused.value.rule == "layout_not_applied"
    assert refused.value.__cause__ is None and refused.value.__suppress_context__
    probe = sqlite3.connect(path)
    tables = {row[0] for row in probe.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert tables == TABLES and probe.execute("PRAGMA user_version").fetchone()[0] == VERSION
    probe.close()


class Heard:
    """Stands between the layer and the file, and keeps every statement that is run."""

    def __init__(self, connection: sqlite3.Connection, run: list[str]) -> None:
        self._connection = connection
        self._run = run

    def execute(self, statement: str, *values: Any) -> sqlite3.Cursor:
        self._run.append(" ".join(statement.split()))
        return self._connection.execute(statement, *values)

    def close(self) -> None:
        self._connection.close()


def test_a_change_to_the_layout_is_applied_under_a_lock_and_whole(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    run: list[str] = []
    connect = sqlite3.connect

    def heard(*args: Any, **kwargs: Any) -> Heard:
        return Heard(connect(*args, **kwargs), run)

    monkeypatch.setattr(sqlite3, "connect", heard)

    Store(tmp_path / "accounts.db").close()
    first = list(run)
    run.clear()
    Store(tmp_path / "accounts.db").close()

    # The file is set, and then held by this one alone while its layout is brought on:
    # nobody else reads or writes meanwhile, and the whole is kept or none of it.
    at = first.index("BEGIN EXCLUSIVE")
    assert first[at + 1] == "PRAGMA user_version"
    assert first[at + 2].startswith("CREATE TABLE accounts")
    assert first[-2:] == ["PRAGMA user_version = 1", "COMMIT"]
    assert "PRAGMA journal_mode = WAL" in first[:at] and "PRAGMA foreign_keys = ON" in first[:at]
    # Opened again, the file has had every change, and none is applied a second time.
    assert run[-3:] == ["BEGIN EXCLUSIVE", "PRAGMA user_version", "COMMIT"]
    assert not [statement for statement in run if statement.startswith("CREATE")]


def test_each_change_to_the_layout_says_which_version_it_leaves(store: Store):
    for number, change in enumerate(layer.CHANGES, start=1):
        assert change[-1] == f"PRAGMA user_version = {number}"
    assert len(layer.CHANGES) == VERSION


def test_a_file_that_is_no_file_of_accounts_is_refused_and_is_left_as_it_was(tmp_path: Path):
    path = tmp_path / "accounts.db"
    written = b"This is somebody's letter, and no file of accounts.\n" * 200
    path.write_bytes(written)
    path.chmod(0o600)

    with pytest.raises(StoreError) as refused:
        Store(path)

    assert refused.value.rule == "not_a_file_of_accounts"
    assert path.read_bytes() == written


@pytest.mark.parametrize("mode", [0o644, 0o640, 0o604, 0o660, 0o606, 0o610])
def test_a_file_that_others_may_open_is_refused(tmp_path: Path, mode: int):
    path = tmp_path / "accounts.db"
    Store(path).close()
    path.chmod(mode)

    with pytest.raises(StoreError) as refused:
        Store(path)

    assert refused.value.rule == "open_to_others"
    assert stat.S_IMODE(path.stat().st_mode) == mode


def test_a_folder_that_is_not_there_is_said_and_nothing_is_made(tmp_path: Path):
    with pytest.raises(StoreError) as refused:
        Store(tmp_path / "nowhere" / "accounts.db")

    assert refused.value.rule == "no_folder" and not (tmp_path / "nowhere").exists()


def test_a_folder_where_the_file_should_be_is_said_to_be_no_file(tmp_path: Path):
    (tmp_path / "accounts.db").mkdir()

    with pytest.raises(StoreError) as refused:
        Store(tmp_path / "accounts.db")

    assert refused.value.rule == "not_a_file"
    assert list((tmp_path / "accounts.db").iterdir()) == []


@pytest.mark.skipif(os.geteuid() == 0, reason="the one who runs the tests may write anywhere")
@pytest.mark.parametrize(
    ("folder", "file"),
    [
        pytest.param(0o555, None, id="a folder that may not be written to, and no file in it"),
        pytest.param(0o000, None, id="a folder that may not be entered"),
        pytest.param(0o700, 0o000, id="a file that may be neither read nor written"),
        pytest.param(0o700, 0o400, id="a file that may be read and not written"),
        pytest.param(0o555, 0o600, id="a file of accounts in a folder that may not be written to"),
    ],
)
def test_what_the_service_may_not_write_to_is_said_in_a_word_of_the_stores_own(
    tmp_path: Path, folder: int, file: int | None
):
    # On a volume that was just made the folder is root's, and the service is not root.
    data = tmp_path / "data"
    data.mkdir()
    path = data / "accounts.db"
    if file is not None:
        Store(path).close()
        path.chmod(file)
    data.chmod(folder)

    try:
        with pytest.raises(StoreError) as refused:
            Store(path)
    finally:
        data.chmod(0o700)

    # What the system says of it names the path. The store says a word of its own, and
    # what the system said is not written out with it.
    assert (refused.value.rule, str(refused.value)) == ("not_permitted", "not_permitted")
    assert refused.value.__cause__ is None
    assert refused.value.__context__ is None or refused.value.__suppress_context__
    # Nothing was made, and nothing was made anybody's that it was not.
    assert [one.name for one in data.iterdir()] == ([] if file is None else ["accounts.db"])
    assert file is None or stat.S_IMODE(path.stat().st_mode) == file


# No statement is made of strings.


def test_no_statement_is_ever_made_by_putting_strings_together():
    source = Path(layer.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)

    # No text is built in the whole of the layer: none is written with a value in it,
    # none is added to another, and none is filled in afterwards.
    assert not [node for node in ast.walk(tree) if isinstance(node, ast.JoinedStr)]
    built = [node for node in ast.walk(tree) if isinstance(node, ast.BinOp)]
    assert not [node for node in built if isinstance(node.op, (ast.Add, ast.Mod))]
    called = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    by_name = [n for n in called if isinstance(n.func, ast.Attribute)]
    assert not {"format", "join", "replace", "executescript", "executemany"} & {
        n.func.attr for n in by_name if isinstance(n.func, ast.Attribute)
    }

    def given(call: ast.Call) -> str:
        statement = call.args[0]
        assert isinstance(statement, ast.Name), ast.dump(statement)
        return statement.id

    # Every statement that is run is handed on by its name. Where a method hands one on,
    # it is a statement that stands written at the top of the layer, in capitals.
    run = [
        given(n) for n in by_name if isinstance(n.func, ast.Attribute) and n.func.attr == "execute"
    ]
    handed = [
        given(n)
        for n in by_name
        if isinstance(n.func, ast.Attribute)
        and n.func.attr in ("_one", "_all", "_count", "_changed")
    ]
    assert len(handed) > 35 and all(name.isupper() for name in handed)
    assert all(name.isupper() or name == "statement" for name in run)
    written = {name for name, value in vars(layer).items() if isinstance(value, str)}
    assert {name for name in (*run, *handed) if name != "statement"} <= written


def test_every_statement_that_takes_a_value_binds_it():
    statements = {
        name: value
        for name, value in vars(layer).items()
        if name.isupper() and isinstance(value, str) and " " in value
    }
    assert len(statements) > 30

    for name, statement in statements.items():
        # A value is a question mark. No quote stands in a statement that is run, so
        # nothing that was sent can ever be read as a part of one.
        assert "'" not in statement and '"' not in statement, name


def test_one_layer_is_the_only_code_that_touches_the_connection():
    root = Path(burro_api.__file__).parent
    touches = [
        path.relative_to(root).as_posix()
        for path in root.rglob("*.py")
        if "sqlite3" in path.read_text(encoding="utf-8")
    ]

    assert touches == ["accounts/store.py"]


def test_what_is_sent_as_a_value_is_kept_as_a_value_and_runs_nothing(store: Store):
    made = account(1)
    cruel = "x'); DROP TABLE accounts; --"
    with store.writing() as held:
        held.add_account(made)
        held.add_search(made.id, Kept(cruel[:22], cruel, cruel, cruel, AT))

    with store.reading() as held:
        [found] = held.searches(made.id)
        assert held.account(cruel) is None and held.account_of(cruel) is None
    assert (found.id, found.spec, found.name) == (cruel[:22], cruel, cruel)
    assert counts(store)["accounts"] == 1


# The closed lists.


def test_the_lists_the_file_holds_a_row_to_are_the_lists_of_the_code(store: Store):
    probe = sqlite3.connect(store.path)
    written = {
        name: sql
        for name, sql in probe.execute("SELECT name, sql FROM sqlite_master WHERE type = 'table'")
    }
    probe.close()

    def listed(table: str, column: str) -> set[str]:
        after = written[table].split(f"CHECK ({column} IN (", 1)[1].split("))", 1)[0]
        return {word.strip().strip("'") for word in after.split(",")}

    assert listed("audit_events", "event") == {event.value for event in Event}
    assert listed("audit_events", "outcome") == {outcome.value for outcome in Outcome}
    assert listed("sessions", "browser") == {browser.value for browser in Browser}
    assert listed("preferences", "key") == set(PreferencesBody.model_fields)


@pytest.mark.parametrize(
    ("event", "outcome"),
    [("signed_in", "ok"), ("link_used", "fine"), ("", ""), ("LINK_USED", "ok")],
)
def test_an_event_that_is_not_on_the_list_cannot_be_kept(store: Store, event: str, outcome: str):
    made = with_everything(store, 1)

    with pytest.raises(sqlite3.IntegrityError), store.writing() as held:
        held.add_event(made.id, event, outcome, AT)

    assert counts(store)["audit_events"] == 1


@pytest.mark.parametrize(("key", "value"), [("theme", "on"), ("keep_recent", "yes"), ("", "on")])
def test_a_preference_that_is_not_on_the_list_cannot_be_kept(store: Store, key: str, value: str):
    made = with_everything(store, 1)

    with pytest.raises(sqlite3.IntegrityError), store.writing() as held:
        held.set_preference(made.id, key, value)

    with store.reading() as held:
        assert held.preferences(made.id) == {"keep_recent": "on"}


def test_a_column_takes_no_value_of_another_kind(store: Store):
    made = account(1)

    with pytest.raises(sqlite3.IntegrityError), store.writing() as held:
        held.add_account(Account(id=made.id, email=made.email, made_at=AT, adult_at=None))  # type: ignore[arg-type]

    assert counts(store)["accounts"] == 0


# One transaction.


def test_what_is_written_together_is_kept_together_or_not_at_all(store: Store):
    made = account(1)

    with pytest.raises(sqlite3.IntegrityError), store.writing() as held:
        held.add_account(made)
        held.add_session(signed(1, made))
        # The account of this one is not there, so the whole is undone.
        held.add_session(signed(2, account(2)))

    assert not any(counts(store).values())


def test_what_cannot_be_kept_leaves_the_file_free_for_whoever_asks_next(
    store: Store, monkeypatch: pytest.MonkeyPatch
):
    made = account(1)
    # As where the volume is full: what was written cannot be kept.
    monkeypatch.setattr(layer, "COMMIT", "COMMIT TO NOTHING")

    with pytest.raises(sqlite3.Error), store.writing() as held:
        held.add_account(made)

    monkeypatch.undo()
    assert counts(store)["accounts"] == 0
    # The file is held by nobody, and the next to ask is answered.
    with store.writing() as held:
        held.add_account(made)
    with store.reading() as held:
        assert held.account(made.id) == made


def test_nothing_is_kept_under_an_account_that_is_not_there(store: Store):
    ghost = account(9)

    def a_session(held: Held) -> None:
        held.add_session(signed(1, ghost))

    def a_search(held: Held) -> None:
        held.add_search(ghost.id, kept(1))

    def a_last_search(held: Held) -> None:
        held.add_recent(ghost.id, kept(1))

    def a_preference(held: Held) -> None:
        held.set_preference(ghost.id, "keep_recent", "on")

    def an_event(held: Held) -> None:
        held.add_event(ghost.id, "link_used", "ok", AT)

    for write in (a_session, a_search, a_last_search, a_preference, an_event):
        with pytest.raises(sqlite3.IntegrityError), store.writing() as held:
            write(held)

    assert not any(counts(store).values())


def test_an_address_has_one_account(store: Store):
    made = account(1)
    with store.writing() as held:
        held.add_account(made)

    with pytest.raises(sqlite3.IntegrityError), store.writing() as held:
        held.add_account(
            Account(id="another-one-0000000000", email=made.email, made_at=AT, adult_at=AT)
        )

    assert counts(store)["accounts"] == 1


def test_many_write_at_once_and_every_row_is_kept(store: Store):
    people = [account(number) for number in range(40)]

    def write(made: Account) -> None:
        with store.writing() as held:
            held.add_account(made)
            for number in range(5):
                held.add_event(made.id, "link_used", "ok", f"2026-09-26T12:00:{number:02d}Z")

    with ThreadPoolExecutor(max_workers=12) as pool:
        list(pool.map(write, people))

    assert counts(store) | {"accounts": 40, "audit_events": 200} == counts(store)


# The account goes, and everything of it goes with it.


def test_deleting_an_account_takes_everything_of_it_and_nothing_of_anybody_elses(store: Store):
    first, second = with_everything(store, 1), with_everything(store, 2)
    assert set(counts(store).values()) == {2}

    with store.writing() as held:
        held.delete_account(first.id)
        held.forget_links_of(first.email)

    assert set(counts(store).values()) == {1}
    with store.reading() as held:
        assert held.account(first.id) is None and held.account(second.id) == second
        assert held.searches(first.id) == () and len(held.searches(second.id)) == 1
        assert held.sessions(first.id) == () and len(held.sessions(second.id)) == 1
        assert held.events(first.id) == () and len(held.events(second.id)) == 1
        assert held.links_of(first.email) == () and len(held.links_of(second.email)) == 1


def test_what_is_deleted_is_gone_from_the_file_and_not_only_from_the_tables(tmp_path: Path):
    store = Store(tmp_path / "accounts.db")
    made = Account("account-to-be-forgot0", "quillfeather.zebrano@example.org", AT, AT)
    with store.writing() as held:
        held.add_account(made)
        held.add_search(
            made.id, Kept("search-to-be-forgott0", '{"marker":"zebranoquill"}', "r", "n", AT)
        )
        held.add_link(link(1, made.email))
    written = b"".join(path.read_bytes() for path in sorted(tmp_path.iterdir()))
    assert b"quillfeather.zebrano" in written and b"zebranoquill" in written

    with store.writing() as held:
        held.delete_account(made.id)
        held.forget_links_of(made.email)
    store.trim()

    left = b"".join(path.read_bytes() for path in sorted(tmp_path.iterdir()))
    assert b"quillfeather" not in left and b"zebranoquill" not in left
    store.close()


# Whose rows.


def test_every_look_up_of_what_is_kept_names_the_account():
    # A row is found by its id and its account together. An id alone finds nothing, so
    # an id that is guessed, or that is somebody else's, gives nothing away.
    of_an_account = ("sessions", "saved_searches", "recent_searches", "preferences", "audit_events")
    statements = {
        name: value
        for name, value in vars(layer).items()
        if name.isupper() and isinstance(value, str) and " " in value
    }
    checked = 0
    for name, statement in statements.items():
        reads = statement.startswith(("SELECT", "UPDATE", "DELETE"))
        if not reads or not any(f" {table} " in f"{statement} " for table in of_an_account):
            continue
        if name in layer.BY_ITS_TOKEN or name in layer.BY_ITS_AGE:
            continue
        assert "account_id = ?" in statement, name
        checked += 1
    assert checked >= 14
    # What is found by its token is a session, by the hash of the token that opens it.
    for name in layer.BY_ITS_TOKEN:
        assert "token_hash = ?" in statements[name] and " sessions " in f"{statements[name]} "
    # And what is let go of by its age is let go of whoever it was of.
    for name in layer.BY_ITS_AGE:
        assert statements[name].startswith("DELETE") and " < ?" in statements[name]


def test_an_id_of_somebody_elses_finds_nothing_and_changes_nothing(store: Store):
    people = [with_everything(store, number) for number in range(1, 7)]
    before = counts(store)

    for mine in people:
        for theirs in people:
            if theirs is mine:
                continue
            number = people.index(theirs) + 1
            with store.writing() as held:
                assert held.forget_search(mine.id, kept(number).id) is False
                assert held.revoke(mine.id, signed(number, theirs).public_id, LATER) is False
                assert (
                    held.put_forward(mine.id, signed(number, theirs).token_hash, LATER, LATER)
                    is False
                )

    assert counts(store) == before
    with store.reading() as held:
        for number, each in enumerate(people, start=1):
            assert [row.id for row in held.searches(each.id)] == [kept(number).id]
            assert [row.id for row in held.recent(each.id)] == [kept(number).id]
            [session] = held.sessions(each.id)
            assert session == signed(number, each)


# Links.


def test_links_are_counted_by_their_address_and_since_a_time(store: Store):
    with store.writing() as held:
        held.add_link(link(1, "a@example.org", "2026-09-26T11:00:00Z"))
        held.add_link(link(2, "a@example.org", "2026-09-26T11:50:00Z"))
        held.add_link(link(3, "a@example.org", "2026-09-26T11:59:00Z"))
        held.add_link(link(4, "b@example.org", "2026-09-26T11:59:00Z"))

    with store.reading() as held:
        assert held.links_to("a@example.org", "2026-09-26T11:45:00Z") == 2
        assert held.links_to("a@example.org", "2026-09-25T12:00:00Z") == 3
        assert held.links_to("c@example.org", "2026-09-25T12:00:00Z") == 0
        assert held.links_since("2026-09-26T11:45:00Z") == 3


def test_using_a_link_ends_every_other_of_its_address_and_none_of_anothers(store: Store):
    with store.writing() as held:
        for number in (1, 2, 3):
            held.add_link(link(number, "a@example.org"))
        held.add_link(link(4, "b@example.org"))

    with store.writing() as held:
        held.end_links("a@example.org", LATER)

    with store.reading() as held:
        assert [row.used_at for row in held.links_of("a@example.org")] == [LATER] * 3
        assert [row.used_at for row in held.links_of("b@example.org")] == [None]


def test_a_link_that_was_used_keeps_the_time_it_was_used(store: Store):
    with store.writing() as held:
        held.add_link(link(1, "a@example.org"))
        held.end_links("a@example.org", AT)
        held.add_link(link(2, "a@example.org"))
        held.end_links("a@example.org", LATER)

    with store.reading() as held:
        assert [row.used_at for row in held.links_of("a@example.org")] == [AT, LATER]


def test_links_are_let_go_of_by_their_age_whoever_asked(store: Store):
    with store.writing() as held:
        held.add_link(link(1, "a@example.org", "2026-09-25T11:59:59Z"))
        held.add_link(link(2, "b@example.org", "2026-09-25T12:00:00Z"))

    with store.writing() as held:
        assert held.forget_links("2026-09-25T12:00:00Z") == 1

    with store.reading() as held:
        assert held.links_of("a@example.org") == () and len(held.links_of("b@example.org")) == 1


def test_the_links_of_a_browser_are_bound_again_and_no_other(store: Store):
    with store.writing() as held:
        held.add_link(link(1, "a@example.org", binding="1" * 64))
        held.add_link(link(2, "a@example.org", binding="2" * 64))
        held.add_link(link(3, "a@example.org", binding="1" * 64))
        held.end_link(f"{3:064x}", AT)

    with store.writing() as held:
        held.bind_again("1" * 64, "9" * 64, AT)

    with store.reading() as held:
        bound = [row.binding_hash for row in held.links_of("a@example.org")]
    # The one that was used, and the one of another browser, are as they were.
    assert bound == ["9" * 64, "2" * 64, "1" * 64]


# Sessions.


def test_a_session_is_found_by_the_hash_of_its_token(store: Store):
    made = with_everything(store, 1)

    with store.reading() as held:
        assert held.session(signed(1, made).token_hash) == signed(1, made)
        assert held.session(signed(2, made).token_hash) is None


def test_revoking_every_session_of_an_account_leaves_every_other_accounts(store: Store):
    first, second = with_everything(store, 1), with_everything(store, 2)
    with store.writing() as held:
        held.add_session(signed(11, first))

    with store.writing() as held:
        assert held.revoke_all(first.id, LATER) == 2
        assert held.revoke_all(first.id, LATER) == 0

    with store.reading() as held:
        assert {row.revoked_at for row in held.sessions(first.id)} == {LATER}
        assert [row.revoked_at for row in held.sessions(second.id)] == [None]


def test_sessions_that_ended_long_ago_are_let_go_of(store: Store):
    made = with_everything(store, 1)
    with store.writing() as held:
        held.add_session(signed(2, made))
        held.revoke(made.id, signed(2, made).public_id, "2026-08-01T00:00:00Z")

    with store.writing() as held:
        assert held.forget_sessions("2026-09-01T00:00:00Z") == 1

    with store.reading() as held:
        assert [row.public_id for row in held.sessions(made.id)] == [signed(1, made).public_id]


# Searches.


def test_the_newest_search_comes_first(store: Store):
    made = account(1)
    with store.writing() as held:
        held.add_account(made)
        for number, at in ((1, AT), (2, LATER), (3, AT), (4, LATER)):
            held.add_search(made.id, Kept(kept(number).id, SPEC, "r", "n", at))

    with store.reading() as held:
        assert [row.id for row in held.searches(made.id)] == [
            kept(4).id,
            kept(2).id,
            kept(3).id,
            kept(1).id,
        ]
        assert held.count_searches(made.id) == 4


def test_the_last_searches_are_cut_to_so_many_and_the_oldest_go(store: Store):
    made, other = account(1), account(2)
    with store.writing() as held:
        held.add_account(made)
        held.add_account(other)
        for number in range(1, 14):
            held.add_recent(made.id, kept(number))
        held.add_recent(other.id, kept(99))

    with store.writing() as held:
        held.trim_recent(made.id, 10)

    with store.reading() as held:
        assert [row.id for row in held.recent(made.id)] == [kept(n).id for n in range(13, 3, -1)]
        assert len(held.recent(other.id)) == 1


def test_a_search_is_found_by_what_it_holds_under_its_own_account_alone(store: Store):
    first, second = with_everything(store, 1), with_everything(store, 2)

    with store.reading() as held:
        found = held.search_like(first.id, SPEC)
        assert found is not None and found.id == kept(1).id
        assert held.search_like(first.id, '{"schema_version":2}') is None
    with store.writing() as held:
        held.forget_recent_like(first.id, SPEC)

    with store.reading() as held:
        assert held.recent(first.id) == () and len(held.recent(second.id)) == 1


# What happened.


def test_what_happened_to_an_account_is_cut_to_so_many_and_let_go_of_by_its_age(store: Store):
    made, other = with_everything(store, 1), with_everything(store, 2)
    with store.writing() as held:
        for minute in range(30):
            held.add_event(made.id, "link_used", "ok", f"2026-09-26T13:{minute:02d}:00Z")

    with store.writing() as held:
        held.trim_events(made.id, 20)
    with store.reading() as held:
        found = held.events(made.id)
        assert len(found) == 20 and found[0].at == "2026-09-26T13:29:00Z"
        assert len(held.events(other.id)) == 1

    with store.writing() as held:
        assert held.forget_events("2026-09-26T13:20:00Z") == 11
    with store.reading() as held:
        assert len(held.events(made.id)) == 10 and held.events(other.id) == ()
