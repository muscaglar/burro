"""The call-metadata record: what is kept about a call to an interpreter or an explainer.

It is metadata only (ADR 0005). Every field is an int, a bool, an enum or a
string with a fixed pattern, so none can hold free text. There is no hash of
the prompt: a short prompt can be guessed from its hash. Nor is there a hash
of the spec, plain or under a key, nor anything else worked out from one: a
spec says where someone works, and nothing needs to know that two calls were
about the same search (ADR 0011).
"""

from collections import deque
from datetime import datetime, timedelta
from enum import StrEnum
from threading import Lock
from typing import Protocol

from burro_core.ids import TIMESTAMP_PATTERN, ReleaseId
from pydantic import Field

from burro_api.wire import Wire

KEEP_DAYS = 30
KEEP_AT_MOST = 10_000

UUID_PATTERN = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
MODEL_PATTERN = r"^([a-z0-9][a-z0-9.-]{0,63})?$"
VERSION_PATTERN = r"^\d+\.\d+\.\d+$"
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


class Endpoint(StrEnum):
    INTERPRET = "interpret"
    EXPLAIN = "explain"


class Caller(StrEnum):
    RULE = "rule"
    CLAUDE = "claude"
    TEMPLATE = "template"


class CallStatus(StrEnum):
    OK = "ok"
    CLARIFY = "clarify"
    OFF_TOPIC = "off_topic"
    POLICY_REDIRECT = "policy_redirect"
    TIMEOUT = "timeout"
    CAPPED = "capped"
    ERROR = "error"


class CallRecord(Wire):
    """One call. Already shaped as a table row, for the day there is a table."""

    call_id: str = Field(pattern=UUID_PATTERN)
    at: str = Field(pattern=TIMESTAMP_PATTERN)  # to the second
    endpoint: Endpoint
    # The interpreter or explainer that was asked, whether or not it answered.
    interpreter: Caller
    model: str = Field(pattern=MODEL_PATTERN)  # the configured model id, or empty
    status: CallStatus
    degraded: bool
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    cache_read_tokens: int = Field(ge=0)
    latency_ms: int = Field(ge=0)
    release_id: ReleaseId
    engine_version: str = Field(pattern=VERSION_PATTERN)


class CallLog(Protocol):
    """Where call records go. In memory today; a table of the same columns later.

    No record is kept for more than `KEEP_DAYS`, and it is `add` that sees to
    it: the service adds and never reads, so a log that let go of records only
    when it was read would let go of none. Whatever takes the place of the
    one in memory must do the same, in `add` or on a timer of its own.
    """

    def add(self, record: CallRecord) -> None:
        """Keep `record`, and let go of every record that is by now too old."""
        ...

    def records(self, now: datetime) -> tuple[CallRecord, ...]:
        """The records that are no older than `KEEP_DAYS` at `now`, oldest first."""
        ...


def _oldest_kept(now: datetime) -> str:
    # Timestamps are in one fixed format, so they sort and compare as text.
    return (now - timedelta(days=KEEP_DAYS)).strftime(TIMESTAMP_FORMAT)


class InMemoryCallLog:
    """Keeps the latest records until restart, and none older than 30 days."""

    def __init__(self, keep_at_most: int = KEEP_AT_MOST) -> None:
        self._records: deque[CallRecord] = deque(maxlen=keep_at_most)
        # The latest time any record has carried. Age is measured from it, so
        # a clock that is put back brings nothing back.
        self._latest = ""
        self._lock = Lock()

    def _forget(self, oldest: str) -> None:
        """Let go of every record older than `oldest`, wherever it stands.

        Records stand in the order they were added, which is not the order
        of time when a clock has been put back, so an old record may stand
        behind a young one. Nothing is rebuilt unless something is too old.
        """
        if any(record.at < oldest for record in self._records):
            kept = [record for record in self._records if record.at >= oldest]
            self._records.clear()
            self._records.extend(kept)

    def add(self, record: CallRecord) -> None:
        with self._lock:
            self._latest = max(self._latest, record.at)
            oldest = _oldest_kept(datetime.strptime(self._latest, TIMESTAMP_FORMAT))
            self._forget(oldest)
            if record.at >= oldest:
                self._records.append(record)

    def records(self, now: datetime) -> tuple[CallRecord, ...]:
        with self._lock:
            self._forget(_oldest_kept(now))
            return tuple(self._records)
