"""Rules every registry entry must satisfy.

Each rule is a small function so a failure names the rule that caught it.
Errors fail CI. Warnings are printed, and fail only under `--strict`, which
is what the launch checklist runs.
"""

import re
import unicodedata
from collections import Counter
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from datetime import date, timedelta
from enum import StrEnum

from burro_pipeline.registry.addresses import held_by_two, written_wrongly
from burro_pipeline.registry.model import (
    HOUSING_TABLES,
    INTERNAL_USES,
    NO_ATTRIBUTION_LICENCES,
    SHARE_ALIKE_ALLOWED_USES,
    SHARE_ALIKE_LICENCES,
    SHOWN_TABLES,
    CommercialUse,
    Dimension,
    Licence,
    Source,
    Status,
    Use,
    VerifiedHow,
)

STALE_AFTER = timedelta(days=365)

# A census table's code however it is written: TS021, c2021ts021, census2021-ts007a.zip,
# TS-021, TS 021, censusTS021, ts021oa. Between its letters and its digits may stand any
# signs that are no letter and no digit, and anything may stand before it. A fourth digit
# makes it no code: a code has three, and a year has four.
_SIGNS = r"[\W_]*"
CENSUS_TABLE_CODE = re.compile(
    rf"t{_SIGNS}s{_SIGNS}(\d){_SIGNS}(\d){_SIGNS}(\d)(?!\d)([a-z]?)", re.IGNORECASE
)


class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class Problem:
    source_id: str
    rule: str
    message: str
    severity: Severity = Severity.ERROR

    def __str__(self) -> str:
        return f"{self.severity}: {self.source_id}: {self.message} [{self.rule}]"


def _urls(source: Source) -> Iterator[tuple[str, str]]:
    yield "url", source.url
    if source.licence_url:
        yield "licence_url", source.licence_url
    for url in source.evidence_urls:
        yield "evidence_urls", url
    for url in source.file_urls:
        yield "file_urls", url


def https_only(source: Source, today: date) -> Iterator[str]:
    for field, url in _urls(source):
        if not url.startswith("https://"):
            yield f"{field} must start with https://, got {url!r}"
        elif "@" in url.split("/")[2]:
            yield f"{field} must not contain credentials"


def share_alike_matches_licence(source: Source, today: date) -> Iterator[str]:
    expected = bool(source.licences & SHARE_ALIKE_LICENCES)
    if source.share_alike != expected:
        names = ", ".join(sorted(source.licences))
        yield f"share_alike is {source.share_alike} but the licences ({names}) say {expected}"


def share_alike_stays_out_of_scoring(source: Source, today: date) -> Iterator[str]:
    if not source.share_alike:
        return
    for use in source.uses:
        if use not in SHARE_ALIKE_ALLOWED_USES:
            yield f"share-alike data may not be used for {use}"


def audit_data_stays_internal(source: Source, today: date) -> Iterator[str]:
    if source.dimension is not Dimension.AUDIT and Use.AUDIT_ONLY not in source.uses:
        return
    for use in source.uses:
        if use not in INTERNAL_USES:
            yield f"audit data may not be used for {use}"


def resident_sources_feed_the_census_table_and_nothing_else(
    source: Source, today: date
) -> Iterator[str]:
    if source.dimension is not Dimension.RESIDENTS:
        return
    # Not an internal use either: it would let a file about residents be fetched before
    # its licence page is saved and the fences around the census table exist.
    for use in source.uses:
        if use is not Use.CENSUS_TABLE:
            yield f"a source about residents may not be used for {use}"
    if not source.tables:
        yield "a source about residents must name its tables"
    for table in source.tables:
        if table not in SHOWN_TABLES:
            yield f"census table {table} is not one that an area's page may show"


def only_resident_sources_feed_the_census_table(source: Source, today: date) -> Iterator[str]:
    if source.dimension is not Dimension.RESIDENTS and Use.CENSUS_TABLE in source.uses:
        yield f"only a source under residents may be used for {Use.CENSUS_TABLE}"


def census_tables_written_in(text: str) -> set[str]:
    """Every census table's code that a text holds, as the statistics office writes it.

    A letter straight after the digits may be part of the code, as in TS007A, or the
    start of a word. So such a code is read both ways: with the letter and without it.
    """
    # Letters and digits of another width are read as plain ones.
    plain = unicodedata.normalize("NFKC", text)
    found: set[str] = set()
    for first, second, third, letter in CENSUS_TABLE_CODE.findall(plain):
        code = f"TS{first}{second}{third}"
        found |= {code, f"{code}{letter.upper()}"}
    return found


def _census_tables_named(source: Source) -> set[str]:
    """Every census table a source names: in `tables`, its id, its name or an address."""
    addresses = (source.url, *source.evidence_urls, *source.file_urls)
    written = " ".join((source.id, source.name, *addresses))
    return {*source.tables, *census_tables_written_in(written)}


def resident_tables_sit_under_residents_or_audit(source: Source, today: date) -> Iterator[str]:
    """A census table named under any other heading is a housing table.

    The rule reads a code. It reads one however it is written, and takes a word that
    ends as a code does for a code. A table that is named with no code at all cannot be
    caught by a code. What catches it is the rule on addresses: a file is fetched only
    from an address that the entry of its source names under `file_urls`, and no entry
    may name an address that another holds (`no_address_is_held_by_two_entries`).
    """
    if source.dimension in (Dimension.RESIDENTS, Dimension.AUDIT):
        return
    for table in sorted(_census_tables_named(source) - HOUSING_TABLES):
        yield (
            f"census table {table} is not a housing table, so it is taken to be about "
            "residents and belongs under residents or audit"
        )


def file_urls_are_written_plainly(source: Source, today: date) -> Iterator[str]:
    """An address of a file is https, holds no login, and can be read one way only."""
    yield from written_wrongly(source)


def approved_is_proven(source: Source, today: date) -> Iterator[str]:
    if source.status is not Status.APPROVED:
        return
    if Licence.NONE_STATED in source.licences:
        yield "approved, but the publisher states no licence"
    if source.commercial_use not in (CommercialUse.YES, CommercialUse.YES_WITH_CONDITIONS):
        yield f"approved, but commercial_use is {source.commercial_use}"
    if source.verified_how is not VerifiedHow.PRIMARY_SOURCE:
        yield f"approved, but verified_how is {source.verified_how}"
    if not source.evidence_urls:
        yield "approved, but evidence_urls is empty"
    if not source.uses:
        yield "approved, but uses is empty, so no ingest step could ever pass the gate"
    if not source.attribution.strip() and not source.licences <= NO_ATTRIBUTION_LICENCES:
        yield "approved, but attribution is empty"
    if source.commercial_use is CommercialUse.YES_WITH_CONDITIONS and not source.conditions:
        yield "commercial use has conditions, but conditions is empty"


def unapproved_says_why(source: Source, today: date) -> Iterator[str]:
    if source.status is not Status.APPROVED and not source.status_reason.strip():
        yield f"status is {source.status}, so status_reason must say why"


def unapproved_stays_internal(source: Source, today: date) -> Iterator[str]:
    if source.status is Status.BANNED and source.uses:
        yield "banned sources must have no uses"
    if source.status is Status.HELD:
        for use in source.uses:
            if use not in INTERNAL_USES:
                yield f"held sources may only have internal uses, not {use}"


def launch_items_belong_to_approved_sources(source: Source, today: date) -> Iterator[str]:
    if source.before_launch and source.status is not Status.APPROVED:
        yield (
            f"before_launch is only read on approved sources, and this one is {source.status}. "
            "Put what is holding it back in status_reason"
        )


def non_commercial_is_not_usable(source: Source, today: date) -> Iterator[str]:
    if source.commercial_use is CommercialUse.NO and source.status in (
        Status.APPROVED,
        Status.GATED,
    ):
        yield f"commercial use is not allowed, so status cannot be {source.status}"


def verified_on_is_not_in_the_future(source: Source, today: date) -> Iterator[str]:
    if source.verified_on > today:
        yield f"verified_on {source.verified_on} is in the future"


def attribution_wording_is_confirmed(source: Source, today: date) -> Iterator[str]:
    if source.status is Status.APPROVED and source.attribution and not source.attribution_verified:
        yield "attribution wording has not been checked against the publisher's page"


def nothing_is_left_to_settle_before_launch(source: Source, today: date) -> Iterator[str]:
    if source.status is Status.APPROVED:
        for item in source.before_launch:
            yield f"to settle before launch: {item}"


def verification_is_fresh(source: Source, today: date) -> Iterator[str]:
    if source.status is Status.APPROVED and today - source.verified_on > STALE_AFTER:
        yield f"licence was last verified on {source.verified_on}; verify it again"


Rule = Callable[[Source, date], Iterable[str]]

ERRORS: tuple[Rule, ...] = (
    https_only,
    share_alike_matches_licence,
    share_alike_stays_out_of_scoring,
    audit_data_stays_internal,
    resident_sources_feed_the_census_table_and_nothing_else,
    only_resident_sources_feed_the_census_table,
    resident_tables_sit_under_residents_or_audit,
    file_urls_are_written_plainly,
    approved_is_proven,
    unapproved_says_why,
    unapproved_stays_internal,
    launch_items_belong_to_approved_sources,
    non_commercial_is_not_usable,
    verified_on_is_not_in_the_future,
)

WARNINGS: tuple[Rule, ...] = (
    attribution_wording_is_confirmed,
    nothing_is_left_to_settle_before_launch,
    verification_is_fresh,
)


def check(sources: Iterable[Source], today: date) -> list[Problem]:
    """Return every problem in the registry, errors first."""
    sources = tuple(sources)
    problems = [
        Problem(source_id, "unique_ids", f"id appears {count} times")
        for source_id, count in Counter(s.id for s in sources).items()
        if count > 1
    ]
    # A publisher serves many datasets from one host. So an address is of one entry, or a
    # file that one entry bans, holds or keeps for the audit could be fetched under another.
    problems += [
        Problem(
            source.id,
            "no_address_is_held_by_two_entries",
            f"an address under file_urls is also held by {other.id}, as a file, as its own "
            "page or as its evidence. An address is of one entry: name a whole address, or a "
            "prefix that ends at this dataset",
        )
        for source, other in held_by_two(sources)
    ]
    for severity, rules in ((Severity.ERROR, ERRORS), (Severity.WARNING, WARNINGS)):
        problems += [
            Problem(source.id, rule.__name__, message, severity)
            for source in sources
            for rule in rules
            for message in rule(source, today)
        ]
    return problems
