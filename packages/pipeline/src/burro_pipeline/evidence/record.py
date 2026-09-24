"""What every record of evidence shares: it is frozen, closed, and has one form and one hash.

The canonical form is the bytes `canonical_json` gives, which is how a release
file is written too. The hash is the SHA-256 of those bytes, so two records
are the same record exactly when their hashes match.

A record that fails to validate says where and why, and never repeats what it
was given. What it was given may be a row of a publisher's file, and the error
may be printed where anyone can read it.
"""

import calendar
import hashlib
import re
from collections.abc import Sequence
from datetime import date, datetime
from functools import lru_cache
from itertools import pairwise
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, ValidationError

from burro_pipeline.release.write import canonical_json

SHA256_PATTERN = r"^[0-9a-f]{64}$"
FILE_ID_PATTERN = r"^f-[0-9a-f]{12}$"
# A year, a month or a day: a publisher dates its data in its own terms.
WHEN_PATTERN = r"^\d{4}(-(0[1-9]|1[0-2])(-(0[1-9]|[12]\d|3[01]))?)?$"
DAY_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$"
TIMESTAMP_PATTERN = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
# The first twelve digits of a hash are enough to name a file, and short enough to read out.
FILE_ID_DIGITS = 12
# The one source that is no dataset. What cites it is made up, and says so.
MADE_UP_SOURCE = "synthetic"


def file_id_of(sha256: str) -> str:
    """The id of a file: `f-` and the first twelve digits of its hash."""
    return f"f-{sha256[:FILE_ID_DIGITS]}"


@lru_cache(maxsize=4096)
def first_and_last_day(when: str) -> tuple[date, date]:
    """The days a year, a month or a day runs from and to.

    Every record asks it of every date it holds, and a build has few dates. So each is
    worked out once. A date the calendar does not have is refused each time it is asked.
    """
    parts = [int(part) for part in when.split("-")]
    if len(parts) == 1:
        return date(parts[0], 1, 1), date(parts[0], 12, 31)
    if len(parts) == 2:
        last = calendar.monthrange(parts[0], parts[1])[1]
        return date(parts[0], parts[1], 1), date(parts[0], parts[1], last)
    day = date(parts[0], parts[1], parts[2])
    return day, day


def strictly_increasing(keys: Sequence[str]) -> bool:
    """Whether a list is sorted and holds nothing twice."""
    return all(a < b for a, b in pairwise(keys))


def given(*items: object) -> bool | None:
    """Whether every item is given, or none is. Null when only some are."""
    count = sum(item is not None for item in items)
    return None if 0 < count < len(items) else count > 0


def _a_real_when(value: str) -> str:
    if not re.fullmatch(WHEN_PATTERN, value):
        raise ValueError("is not a year, a month or a day")
    try:
        first_and_last_day(value)
    except ValueError:
        raise ValueError("is a day the calendar does not have") from None
    return value


def _a_real_day(value: str) -> str:
    if not re.fullmatch(DAY_PATTERN, value):
        raise ValueError("is not a day, as YYYY-MM-DD")
    return _a_real_when(value)


def _a_real_timestamp(value: str) -> str:
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        raise ValueError("is not a time in UTC, as YYYY-MM-DDTHH:MM:SSZ") from None
    return value


Sha256 = Annotated[str, Field(pattern=SHA256_PATTERN)]
FileId = Annotated[str, Field(pattern=FILE_ID_PATTERN)]
When = Annotated[str, AfterValidator(_a_real_when)]
Day = Annotated[str, AfterValidator(_a_real_day)]
Timestamp = Annotated[str, Field(pattern=TIMESTAMP_PATTERN), AfterValidator(_a_real_timestamp)]
Text = Annotated[str, Field(min_length=1)]
# A share is held as it is written, to six decimals, so a record equals what is read back.
Share = Annotated[
    float, Field(ge=0, le=1, allow_inf_nan=False), AfterValidator(lambda share: round(share, 6))
]


class EvidenceRecord(BaseModel):
    """Frozen and closed to unknown fields, with one canonical form and one hash."""

    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)

    def canonical(self) -> bytes:
        """The one way this record is written, so the same record is the same bytes."""
        return canonical_json(self.model_dump(mode="json"))

    def digest(self) -> str:
        """The SHA-256 of the canonical form."""
        return hashlib.sha256(self.canonical()).hexdigest()


def in_words(error: ValidationError) -> str:
    """Where a record failed and why. Never what it was given, nor a field it does not know."""
    said: list[str] = []
    for problem in error.errors(include_input=False, include_url=False):
        unknown = problem["type"] == "extra_forbidden"
        where = ".".join(str(part) for part in problem["loc"][: -1 if unknown else None])
        why = "holds a field that a record does not have" if unknown else problem["msg"]
        said.append(f"{where or 'record'}: {why}")
    return "; ".join(said)
