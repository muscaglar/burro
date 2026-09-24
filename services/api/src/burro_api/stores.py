"""Where a shared search is kept. In memory today, behind an interface a database can take.

A share is the one place a spec is stored, and a person makes one on purpose.
It holds nothing about who made it.
"""

from threading import Lock
from typing import Protocol

from burro_core.ids import TIMESTAMP_PATTERN, ReleaseId
from burro_core.spec import PreferenceSpec
from pydantic import Field

from burro_api.wire import SHARE_ID_PATTERN, Wire

KEEP_AT_MOST = 50_000


class StoredShare(Wire):
    # 128 random bits. Never derived from the spec, so holding a spec does not reveal a link.
    share_id: str = Field(pattern=SHARE_ID_PATTERN)
    # With coarse places, unless the sender asked for the exact ones.
    spec: PreferenceSpec
    coarsened: bool
    original_release_id: ReleaseId
    created_at: str = Field(pattern=TIMESTAMP_PATTERN)


class ShareStore(Protocol):
    def put(self, share: StoredShare) -> None: ...
    def get(self, share_id: str) -> StoredShare | None: ...


class InMemoryShareStore:
    """Keeps shares until restart. The oldest goes first when it is full."""

    def __init__(self, keep_at_most: int = KEEP_AT_MOST) -> None:
        self._shares: dict[str, StoredShare] = {}
        self._keep_at_most = keep_at_most
        self._lock = Lock()

    def put(self, share: StoredShare) -> None:
        with self._lock:
            self._shares[share.share_id] = share
            while len(self._shares) > self._keep_at_most:
                # A dict keeps the order things were put in.
                del self._shares[next(iter(self._shares))]

    def get(self, share_id: str) -> StoredShare | None:
        with self._lock:
            return self._shares.get(share_id)
