"""The cap on calls to a model: so many a minute and so many a day, for the whole service.

A call to a model is paid for, and the service is on the open internet. With
no limit of any kind, a key there is an open bill. This is the limit, and the
one there is (ADR 0032).

It counts calls, and nothing of who made them. No address, header, cookie or
token is read, hashed or kept: `lets_in` is handed nothing at all. So one
heavy caller can use up the day for everyone, after which everyone is read by
the rules until the day turns. That is accepted. What stands against abuse is
the host's own protection and blocking after the fact (ADR 0023).

Two counts are held in the memory of the process, behind a lock: the calls
made in the minute that is running, and in the day that is running, by the
clock in UTC. They start again when the process does. There is one machine,
and the provider's own cap on spending is the outer guard.

A call is counted as it is about to be made, before the provider is reached,
so a call that fails or times out is counted. A call that is turned away is
not. Whoever turns a call away answers by the rules, as where a provider says
that it is capped: never by a 429, a login wall or a 5xx.
"""

from collections.abc import Callable
from datetime import UTC, datetime
from enum import StrEnum
from threading import Lock

from burro_api import logs

# The line that is written the first time a cap is reached in its minute or in its day.
CAPPED = "model_capped"

_MINUTES_AN_HOUR = 60
_MINUTES_A_DAY = 24 * _MINUTES_AN_HOUR


class Reached(StrEnum):
    """Which of the two caps turned a call away. A fixed word, named as its setting is."""

    MINUTE = "calls_per_minute"
    DAY = "calls_per_day"


class Cap:
    """Lets in no more calls than so many in a minute, and so many in a day.

    The clock is handed to it, so that a test moves time and waits for
    nothing. A clock that is put back brings no call back: a minute or a day
    is left only for a later one.
    """

    def __init__(self, per_minute: int, per_day: int, now: Callable[[], datetime]) -> None:
        self._per_minute = per_minute
        self._per_day = per_day
        self._now = now
        self._lock = Lock()
        # The minute and the day that are running, each as a number that only
        # grows, and how many calls were let in within each.
        self._minute = 0
        self._day = 0
        self._in_minute = 0
        self._in_day = 0
        # Whether the line has been written for the minute, and for the day.
        self._said_of_minute = False
        self._said_of_day = False

    def lets_in(self) -> bool:
        """Whether a call may be made now. One that may is counted, and one that may not is not."""
        at = self._now().astimezone(UTC)
        day = at.toordinal()
        minute = day * _MINUTES_A_DAY + at.hour * _MINUTES_AN_HOUR + at.minute
        with self._lock:
            if day > self._day:
                self._day, self._in_day, self._said_of_day = day, 0, False
            if minute > self._minute:
                self._minute, self._in_minute, self._said_of_minute = minute, 0, False
            if self._in_day >= self._per_day:
                reached, first = Reached.DAY, not self._said_of_day
                self._said_of_day = True
            elif self._in_minute >= self._per_minute:
                reached, first = Reached.MINUTE, not self._said_of_minute
                self._said_of_minute = True
            else:
                self._in_minute += 1
                self._in_day += 1
                return True
        if first:
            # Which cap, as the word of an enum of ours. No count, and nothing of a call.
            logs.warning(CAPPED, reason=reached.value)
        return False
