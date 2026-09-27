"""Where accounts are kept: one file, and the one layer that touches it.

SQLite, through the standard library. Write-ahead logging, foreign keys on, a busy
timeout, and what is deleted is written over and not only let go of. One connection,
behind a lock, so that what is written together is kept together or not at all.

**Every statement stands written here, and binds its values.** None is ever made by
putting strings together, so nothing that was sent can be read as a part of one. A test
reads this file and fails on a statement that is built.

**Whose rows are read is said in the statement.** A row of a search, a session, a
preference or an event is found by its account, which the session gives and no request
can. An id alone finds nothing.

The layout has a version. A change to it is a list of statements, applied as the file
is opened, forward only, under a lock, and whole or not at all.
"""

import os
import sqlite3
import stat
from collections.abc import Generator
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any, cast

# How long a statement waits for the file where another has it, in milliseconds.
BUSY_TIMEOUT_MS = 5000
# The file is its owner's alone to read and to write.
OWNER_ALONE = stat.S_IRUSR | stat.S_IWUSR
# What nobody but its owner may do with it: anything at all.
OF_OTHERS = stat.S_IRWXG | stat.S_IRWXO

# The layout, as the changes that made it. One is added and none is ever altered: a
# file that was made by the first is brought on by the second. Each says as its last
# statement which version it leaves.
CHANGES: tuple[tuple[str, ...], ...] = (
    (
        """
        CREATE TABLE accounts (
            id TEXT PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            made_at TEXT NOT NULL,
            adult_at TEXT NOT NULL
        ) STRICT
        """,
        """
        CREATE TABLE login_tokens (
            token_hash TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            made_at TEXT NOT NULL,
            ends_at TEXT NOT NULL,
            used_at TEXT,
            binding_hash TEXT NOT NULL
        ) STRICT
        """,
        "CREATE INDEX login_tokens_by_email ON login_tokens (email, made_at)",
        "CREATE INDEX login_tokens_by_age ON login_tokens (made_at)",
        "CREATE INDEX login_tokens_by_browser ON login_tokens (binding_hash)",
        """
        CREATE TABLE sessions (
            token_hash TEXT PRIMARY KEY,
            public_id TEXT NOT NULL UNIQUE,
            account_id TEXT NOT NULL REFERENCES accounts (id) ON DELETE CASCADE,
            made_at TEXT NOT NULL,
            seen_at TEXT NOT NULL,
            ends_at TEXT NOT NULL,
            revoked_at TEXT,
            browser TEXT NOT NULL CHECK (browser IN ('chrome', 'edge', 'firefox', 'safari',
                'other'))
        ) STRICT
        """,
        "CREATE INDEX sessions_by_account ON sessions (account_id)",
        """
        CREATE TABLE saved_searches (
            id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL REFERENCES accounts (id) ON DELETE CASCADE,
            spec TEXT NOT NULL,
            release_id TEXT NOT NULL,
            name TEXT NOT NULL,
            made_at TEXT NOT NULL
        ) STRICT
        """,
        "CREATE INDEX saved_searches_by_account ON saved_searches (account_id, made_at)",
        """
        CREATE TABLE recent_searches (
            id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL REFERENCES accounts (id) ON DELETE CASCADE,
            spec TEXT NOT NULL,
            release_id TEXT NOT NULL,
            name TEXT NOT NULL,
            made_at TEXT NOT NULL
        ) STRICT
        """,
        "CREATE INDEX recent_searches_by_account ON recent_searches (account_id, made_at)",
        """
        CREATE TABLE preferences (
            account_id TEXT NOT NULL REFERENCES accounts (id) ON DELETE CASCADE,
            key TEXT NOT NULL CHECK (key IN ('keep_recent')),
            value TEXT NOT NULL CHECK (value IN ('on', 'off')),
            PRIMARY KEY (account_id, key)
        ) STRICT
        """,
        """
        CREATE TABLE audit_events (
            id INTEGER PRIMARY KEY,
            account_id TEXT NOT NULL REFERENCES accounts (id) ON DELETE CASCADE,
            event TEXT NOT NULL CHECK (event IN ('link_requested', 'link_sent',
                'link_send_failed', 'link_used', 'link_rejected', 'session_created',
                'session_revoked', 'rate_limited', 'account_deleted')),
            outcome TEXT NOT NULL CHECK (outcome IN ('ok', 'refused', 'expired', 'used',
                'limited', 'unavailable')),
            at TEXT NOT NULL
        ) STRICT
        """,
        "CREATE INDEX audit_events_by_account ON audit_events (account_id, id)",
        "PRAGMA user_version = 1",
    ),
)
VERSION = 1

# How the file is set, each time it is opened.
WRITE_AHEAD = "PRAGMA journal_mode = WAL"
FOREIGN_KEYS = "PRAGMA foreign_keys = ON"
BUSY_TIMEOUT = "PRAGMA busy_timeout = 5000"
# What is deleted is written over with noughts, in the file and not only in the tables.
WRITTEN_OVER = "PRAGMA secure_delete = ON"
# Nothing the file itself says is run as code.
UNTRUSTED = "PRAGMA trusted_schema = OFF"
# Bring what is written ahead into the file, and cut the log of it to nothing.
TRIM = "PRAGMA wal_checkpoint(TRUNCATE)"
READ_VERSION = "PRAGMA user_version"
READ_WRITE_AHEAD = "PRAGMA journal_mode"
READ_FOREIGN_KEYS = "PRAGMA foreign_keys"
READ_BUSY_TIMEOUT = "PRAGMA busy_timeout"
READ_WRITTEN_OVER = "PRAGMA secure_delete"
READ_UNTRUSTED = "PRAGMA trusted_schema"

BEGIN_TO_READ = "BEGIN DEFERRED"
BEGIN_TO_WRITE = "BEGIN IMMEDIATE"
# The lock a change to the layout is made under: nobody else reads or writes meanwhile.
BEGIN_ALONE = "BEGIN EXCLUSIVE"
COMMIT = "COMMIT"
ROLLBACK = "ROLLBACK"

# Accounts.
ACCOUNT = "SELECT id, email, made_at, adult_at FROM accounts WHERE id = ?"
ACCOUNT_OF = "SELECT id, email, made_at, adult_at FROM accounts WHERE email = ?"
ADD_ACCOUNT = "INSERT INTO accounts (id, email, made_at, adult_at) VALUES (?, ?, ?, ?)"
# Everything kept under it goes with it: each table names the account it is of.
DELETE_ACCOUNT = "DELETE FROM accounts WHERE id = ?"

# Links. A link is found by the hash of its token, and counted by its address.
LINK = (
    "SELECT token_hash, email, made_at, ends_at, used_at, binding_hash "
    "FROM login_tokens WHERE token_hash = ?"
)
LINKS_OF = (
    "SELECT token_hash, email, made_at, ends_at, used_at, binding_hash "
    "FROM login_tokens WHERE email = ? ORDER BY made_at, rowid"
)
ADD_LINK = (
    "INSERT INTO login_tokens (token_hash, email, made_at, ends_at, used_at, binding_hash) "
    "VALUES (?, ?, ?, ?, ?, ?)"
)
# Since a time, and not at it: a link that is a quarter of an hour old is counted no more.
LINKS_TO = "SELECT count(*) FROM login_tokens WHERE email = ? AND made_at > ?"
LINKS_SINCE = "SELECT count(*) FROM login_tokens WHERE made_at > ?"
END_LINK = "UPDATE login_tokens SET used_at = ? WHERE token_hash = ? AND used_at IS NULL"
END_LINKS = "UPDATE login_tokens SET used_at = ? WHERE email = ? AND used_at IS NULL"
BIND_AGAIN = (
    "UPDATE login_tokens SET binding_hash = ? "
    "WHERE binding_hash = ? AND used_at IS NULL AND ends_at > ?"
)
FORGET_LINK = "DELETE FROM login_tokens WHERE token_hash = ?"
FORGET_LINKS = "DELETE FROM login_tokens WHERE made_at < ?"
FORGET_LINKS_OF = "DELETE FROM login_tokens WHERE email = ?"

# Sessions.
SESSION = (
    "SELECT token_hash, public_id, account_id, made_at, seen_at, ends_at, revoked_at, browser "
    "FROM sessions WHERE token_hash = ?"
)
SESSIONS = (
    "SELECT token_hash, public_id, account_id, made_at, seen_at, ends_at, revoked_at, browser "
    "FROM sessions WHERE account_id = ? ORDER BY made_at DESC, rowid DESC"
)
ADD_SESSION = (
    "INSERT INTO sessions "
    "(token_hash, public_id, account_id, made_at, seen_at, ends_at, revoked_at, browser) "
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
)
PUT_FORWARD = (
    "UPDATE sessions SET seen_at = ?, ends_at = ? "
    "WHERE account_id = ? AND token_hash = ? AND revoked_at IS NULL"
)
REVOKE = (
    "UPDATE sessions SET revoked_at = ? "
    "WHERE account_id = ? AND public_id = ? AND revoked_at IS NULL"
)
REVOKE_ALL = "UPDATE sessions SET revoked_at = ? WHERE account_id = ? AND revoked_at IS NULL"
REVOKE_SHOWN = "UPDATE sessions SET revoked_at = ? WHERE token_hash = ? AND revoked_at IS NULL"
FORGET_SESSIONS = "DELETE FROM sessions WHERE ends_at < ? OR revoked_at < ?"

# Searches that were kept.
SEARCHES = (
    "SELECT id, spec, release_id, name, made_at FROM saved_searches "
    "WHERE account_id = ? ORDER BY made_at DESC, rowid DESC"
)
COUNT_SEARCHES = "SELECT count(*) FROM saved_searches WHERE account_id = ?"
SEARCH_LIKE = (
    "SELECT id, spec, release_id, name, made_at FROM saved_searches "
    "WHERE account_id = ? AND spec = ? ORDER BY made_at DESC, rowid DESC LIMIT 1"
)
ADD_SEARCH = (
    "INSERT INTO saved_searches (id, account_id, spec, release_id, name, made_at) "
    "VALUES (?, ?, ?, ?, ?, ?)"
)
FORGET_SEARCH = "DELETE FROM saved_searches WHERE account_id = ? AND id = ?"

# The last searches.
RECENT = (
    "SELECT id, spec, release_id, name, made_at FROM recent_searches "
    "WHERE account_id = ? ORDER BY made_at DESC, rowid DESC"
)
ADD_RECENT = (
    "INSERT INTO recent_searches (id, account_id, spec, release_id, name, made_at) "
    "VALUES (?, ?, ?, ?, ?, ?)"
)
FORGET_RECENT = "DELETE FROM recent_searches WHERE account_id = ?"
FORGET_RECENT_LIKE = "DELETE FROM recent_searches WHERE account_id = ? AND spec = ?"
TRIM_RECENT = (
    "DELETE FROM recent_searches WHERE account_id = ? AND id NOT IN ("
    "SELECT id FROM recent_searches WHERE account_id = ? "
    "ORDER BY made_at DESC, rowid DESC LIMIT ?)"
)

# Preferences.
PREFERENCES = "SELECT key, value FROM preferences WHERE account_id = ? ORDER BY key"
SET_PREFERENCE = (
    "INSERT INTO preferences (account_id, key, value) VALUES (?, ?, ?) "
    "ON CONFLICT (account_id, key) DO UPDATE SET value = excluded.value"
)

# What happened to an account.
EVENTS = "SELECT event, outcome, at FROM audit_events WHERE account_id = ? ORDER BY id DESC"
ADD_EVENT = "INSERT INTO audit_events (account_id, event, outcome, at) VALUES (?, ?, ?, ?)"
TRIM_EVENTS = (
    "DELETE FROM audit_events WHERE account_id = ? AND id NOT IN ("
    "SELECT id FROM audit_events WHERE account_id = ? ORDER BY id DESC LIMIT ?)"
)
FORGET_EVENTS = "DELETE FROM audit_events WHERE at < ?"

# The statements that name no account, and why each need not. A session is found by
# the hash of the token that opens it: the token is what says whose it is.
BY_ITS_TOKEN = frozenset({"SESSION", "REVOKE_SHOWN"})
# And what is too old is let go of, whoever it was of.
BY_ITS_AGE = frozenset({"FORGET_SESSIONS", "FORGET_EVENTS"})


@dataclass(frozen=True)
class Account:
    id: str
    email: str
    made_at: str
    adult_at: str


@dataclass(frozen=True)
class Link:
    # The SHA-256 of the token, and never the token.
    token_hash: str
    email: str
    made_at: str
    ends_at: str
    used_at: str | None
    # The SHA-256 of what binds the link to the browser that asked for it.
    binding_hash: str


@dataclass(frozen=True)
class Signed:
    """A session, as it is kept."""

    # The SHA-256 of the session, and never the session.
    token_hash: str
    # What a person names it by. It is not the session and says nothing of it.
    public_id: str
    account_id: str
    made_at: str
    seen_at: str
    ends_at: str
    revoked_at: str | None
    browser: str


@dataclass(frozen=True)
class Kept:
    """A search, as it is kept: the spec as text, and never a word that was typed."""

    id: str
    spec: str
    release_id: str
    name: str
    made_at: str


@dataclass(frozen=True)
class Happening:
    event: str
    outcome: str
    at: str


class StoreError(Exception):
    """The file of accounts cannot be used. It says which rule, and never what a row holds."""

    def __init__(self, rule: str) -> None:
        self.rule = rule
        super().__init__(rule)


Row = tuple[Any, ...]


class Held:
    """The file, held for one transaction. Every statement of accounts is a method of it."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def _one(self, statement: str, values: Row) -> Row | None:
        return cast(Row | None, self._connection.execute(statement, values).fetchone())

    def _all(self, statement: str, values: Row) -> list[Row]:
        return cast(list[Row], self._connection.execute(statement, values).fetchall())

    def _count(self, statement: str, values: Row) -> int:
        return int(self._connection.execute(statement, values).fetchone()[0])

    def _changed(self, statement: str, values: Row) -> int:
        return self._connection.execute(statement, values).rowcount

    # Accounts.

    def account(self, account_id: str) -> Account | None:
        found = self._one(ACCOUNT, (account_id,))
        return Account(*found) if found else None

    def account_of(self, email: str) -> Account | None:
        found = self._one(ACCOUNT_OF, (email,))
        return Account(*found) if found else None

    def add_account(self, made: Account) -> None:
        self._changed(ADD_ACCOUNT, (made.id, made.email, made.made_at, made.adult_at))

    def delete_account(self, account_id: str) -> bool:
        return self._changed(DELETE_ACCOUNT, (account_id,)) > 0

    # Links.

    def link(self, token_hash: str) -> Link | None:
        found = self._one(LINK, (token_hash,))
        return Link(*found) if found else None

    def links_of(self, email: str) -> tuple[Link, ...]:
        return tuple(Link(*found) for found in self._all(LINKS_OF, (email,)))

    def add_link(self, made: Link) -> None:
        values = (
            made.token_hash,
            made.email,
            made.made_at,
            made.ends_at,
            made.used_at,
            made.binding_hash,
        )
        self._changed(ADD_LINK, values)

    def links_to(self, email: str, since: str) -> int:
        return self._count(LINKS_TO, (email, since))

    def links_since(self, since: str) -> int:
        return self._count(LINKS_SINCE, (since,))

    def end_link(self, token_hash: str, at: str) -> bool:
        return self._changed(END_LINK, (at, token_hash)) > 0

    def end_links(self, email: str, at: str) -> int:
        return self._changed(END_LINKS, (at, email))

    def bind_again(self, bound_to: str, bind_to: str, at: str) -> int:
        """Bind the links of one browser to what that browser now holds."""
        return self._changed(BIND_AGAIN, (bind_to, bound_to, at))

    def forget_link(self, token_hash: str) -> bool:
        return self._changed(FORGET_LINK, (token_hash,)) > 0

    def forget_links(self, before: str) -> int:
        return self._changed(FORGET_LINKS, (before,))

    def forget_links_of(self, email: str) -> int:
        return self._changed(FORGET_LINKS_OF, (email,))

    # Sessions.

    def session(self, token_hash: str) -> Signed | None:
        found = self._one(SESSION, (token_hash,))
        return Signed(*found) if found else None

    def sessions(self, account_id: str) -> tuple[Signed, ...]:
        return tuple(Signed(*found) for found in self._all(SESSIONS, (account_id,)))

    def add_session(self, made: Signed) -> None:
        values = (
            made.token_hash,
            made.public_id,
            made.account_id,
            made.made_at,
            made.seen_at,
            made.ends_at,
            made.revoked_at,
            made.browser,
        )
        self._changed(ADD_SESSION, values)

    def put_forward(self, account_id: str, token_hash: str, seen_at: str, ends_at: str) -> bool:
        return self._changed(PUT_FORWARD, (seen_at, ends_at, account_id, token_hash)) > 0

    def revoke(self, account_id: str, public_id: str, at: str) -> bool:
        return self._changed(REVOKE, (at, account_id, public_id)) > 0

    def revoke_all(self, account_id: str, at: str) -> int:
        return self._changed(REVOKE_ALL, (at, account_id))

    def revoke_shown(self, token_hash: str, at: str) -> bool:
        return self._changed(REVOKE_SHOWN, (at, token_hash)) > 0

    def forget_sessions(self, before: str) -> int:
        """Let go of every session that ended, or was revoked, before a time."""
        return self._changed(FORGET_SESSIONS, (before, before))

    # Searches that were kept.

    def searches(self, account_id: str) -> tuple[Kept, ...]:
        return tuple(Kept(*found) for found in self._all(SEARCHES, (account_id,)))

    def count_searches(self, account_id: str) -> int:
        return self._count(COUNT_SEARCHES, (account_id,))

    def search_like(self, account_id: str, spec: str) -> Kept | None:
        found = self._one(SEARCH_LIKE, (account_id, spec))
        return Kept(*found) if found else None

    def add_search(self, account_id: str, made: Kept) -> None:
        values = (made.id, account_id, made.spec, made.release_id, made.name, made.made_at)
        self._changed(ADD_SEARCH, values)

    def forget_search(self, account_id: str, search_id: str) -> bool:
        return self._changed(FORGET_SEARCH, (account_id, search_id)) > 0

    # The last searches.

    def recent(self, account_id: str) -> tuple[Kept, ...]:
        return tuple(Kept(*found) for found in self._all(RECENT, (account_id,)))

    def add_recent(self, account_id: str, made: Kept) -> None:
        values = (made.id, account_id, made.spec, made.release_id, made.name, made.made_at)
        self._changed(ADD_RECENT, values)

    def forget_recent(self, account_id: str) -> int:
        return self._changed(FORGET_RECENT, (account_id,))

    def forget_recent_like(self, account_id: str, spec: str) -> int:
        return self._changed(FORGET_RECENT_LIKE, (account_id, spec))

    def trim_recent(self, account_id: str, keep: int) -> int:
        return self._changed(TRIM_RECENT, (account_id, account_id, keep))

    # Preferences.

    def preferences(self, account_id: str) -> dict[str, str]:
        return {str(key): str(value) for key, value in self._all(PREFERENCES, (account_id,))}

    def set_preference(self, account_id: str, key: str, value: str) -> None:
        self._changed(SET_PREFERENCE, (account_id, key, value))

    # What happened to an account.

    def events(self, account_id: str) -> tuple[Happening, ...]:
        return tuple(Happening(*found) for found in self._all(EVENTS, (account_id,)))

    def add_event(self, account_id: str, event: str, outcome: str, at: str) -> None:
        self._changed(ADD_EVENT, (account_id, event, outcome, at))

    def trim_events(self, account_id: str, keep: int) -> int:
        return self._changed(TRIM_EVENTS, (account_id, account_id, keep))

    def forget_events(self, before: str) -> int:
        return self._changed(FORGET_EVENTS, (before,))


def _made_for_its_owner(path: Path) -> None:
    """Make the file if it is not there, for its owner alone to read and to write.

    What the system says of a file it will not open names the path, and not that it is
    of accounts. So each refusal that a person who sets accounts up is likely to meet is
    said in a word of the store's own.
    """
    if not path.parent.is_dir():
        raise StoreError("no_folder")
    if not os.access(path.parent, os.W_OK | os.X_OK):
        # The file is written ahead of beside itself, so its folder is written to as well.
        # On a volume that was just made the folder is root's, and the service is not root.
        raise StoreError("not_permitted")
    flags = os.O_RDWR | os.O_CREAT
    try:
        os.close(os.open(path, flags, OWNER_ALONE))
    except PermissionError:
        raise StoreError("not_permitted") from None
    except IsADirectoryError:
        raise StoreError("not_a_file") from None
    if not path.is_file():
        raise StoreError("not_a_file")
    if path.stat().st_mode & OF_OTHERS:
        # A file that was put there by hand, which anybody on the machine may read.
        # It is not made its owner's alone in silence: whoever put it there is told.
        raise StoreError("open_to_others")


class Store:
    """The file of accounts, opened once and held for as long as the service runs."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = Lock()
        _made_for_its_owner(path)
        # Every transaction is begun and ended here, by name, and never by the library.
        self._connection = sqlite3.connect(
            path, timeout=5.0, isolation_level=None, check_same_thread=False
        )
        try:
            self._opened()
        except BaseException:
            self._connection.close()
            raise

    def _opened(self) -> None:
        """Set the file and bring its layout on, or say by which rule it cannot be used.

        What the library says went wrong is let go of. It names no value, and a
        service that cannot start says why in a word of its own.
        """
        try:
            self._set()
        except sqlite3.Error:
            raise StoreError("not_a_file_of_accounts") from None
        try:
            self._brought_on()
        except sqlite3.Error:
            raise StoreError("layout_not_applied") from None

    def _set(self) -> None:
        for statement in (WRITE_AHEAD, FOREIGN_KEYS, BUSY_TIMEOUT, WRITTEN_OVER, UNTRUSTED):
            self._connection.execute(statement).fetchall()
        if self.settings() | {"user_version": 0} != SET_AS:
            raise StoreError("not_set")

    def _brought_on(self) -> None:
        """Apply every change to the layout that the file has not had, under a lock."""
        connection = self._connection
        connection.execute(BEGIN_ALONE)
        try:
            version = int(connection.execute(READ_VERSION).fetchone()[0])
            if version > VERSION:
                # Made by a later build. What it holds may be what this one cannot read.
                raise StoreError("newer_layout")
            for change in CHANGES[version:]:
                for statement in change:
                    connection.execute(statement)
            connection.execute(COMMIT)
        except BaseException:
            self._undone()
            raise

    def _undone(self) -> None:
        """Undo what was begun, where anything was. The file is never left held.

        What could not be kept may be what could not be begun, and then there is
        nothing to undo: to ask for it would hide the fault that matters.
        """
        if self._connection.in_transaction:
            self._connection.execute(ROLLBACK)

    def settings(self) -> dict[str, object]:
        """How the file is set, as the file itself says."""
        asked = {
            "journal_mode": READ_WRITE_AHEAD,
            "foreign_keys": READ_FOREIGN_KEYS,
            "busy_timeout": READ_BUSY_TIMEOUT,
            "secure_delete": READ_WRITTEN_OVER,
            "trusted_schema": READ_UNTRUSTED,
            "user_version": READ_VERSION,
        }
        with self._lock:
            return {
                name: self._connection.execute(statement).fetchone()[0]
                for name, statement in asked.items()
            }

    @contextmanager
    def _held(self, statement: str) -> Generator[Held]:
        with self._lock:
            self._connection.execute(statement)
            try:
                yield Held(self._connection)
                self._connection.execute(COMMIT)
            except BaseException:
                # Whatever went wrong, in what was asked or in keeping it: nothing of
                # it is kept, and whoever asks next finds the file free.
                self._undone()
                raise

    def reading(self) -> AbstractContextManager[Held]:
        """Hold the file to read from it. What is read is of one moment."""
        return self._held(BEGIN_TO_READ)

    def writing(self) -> AbstractContextManager[Held]:
        """Hold the file to write to it. What is written is kept together or not at all."""
        return self._held(BEGIN_TO_WRITE)

    def trim(self) -> None:
        """Bring what was written ahead into the file, so that nothing deleted is left beside it."""
        with self._lock:
            self._connection.execute(TRIM).fetchall()

    def close(self) -> None:
        with self._lock:
            self._connection.close()


SET_AS: dict[str, object] = {
    "journal_mode": "wal",
    "foreign_keys": 1,
    "busy_timeout": BUSY_TIMEOUT_MS,
    "secure_delete": 1,
    "trusted_schema": 0,
    "user_version": 0,
}
