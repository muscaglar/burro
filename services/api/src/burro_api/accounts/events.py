"""What happened, and how it ended: two closed lists of words.

They are all that a line of the log says of accounts, and all that is kept of what
happened to an account. Each is the value of an enum, so neither can hold an address, a
token, the id of a session or of an account, the address of a client, or a spec.
"""

from enum import StrEnum


class Event(StrEnum):
    """What happened."""

    LINK_REQUESTED = "link_requested"
    LINK_SENT = "link_sent"
    LINK_SEND_FAILED = "link_send_failed"
    LINK_USED = "link_used"
    LINK_REJECTED = "link_rejected"
    SESSION_CREATED = "session_created"
    SESSION_REVOKED = "session_revoked"
    RATE_LIMITED = "rate_limited"
    ACCOUNT_DELETED = "account_deleted"


class Outcome(StrEnum):
    """How it ended."""

    OK = "ok"
    REFUSED = "refused"
    EXPIRED = "expired"
    USED = "used"
    LIMITED = "limited"
    UNAVAILABLE = "unavailable"
