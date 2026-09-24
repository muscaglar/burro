"""Not yet used. It waits for milestone M8, on quotations: build nothing on it until then.

The claim: one for each thing a model helped to find.

A claim is a publisher's own words about one area, with the page they were
found on. The page is a file that code fetched, named by its receipt. The
words are in that page as written, at the place the claim says. A model may
have pointed at them. It is recorded as how the claim was found, and is never
a source.

This is the record and what must hold of it alone. The checks that read the
page, the word lists and the second look belong to the research part.
"""

import hashlib
from enum import StrEnum
from typing import Annotated, Literal, Self

from burro_core.ids import SYNTHETIC_PREFIX, AreaId, ReleaseId, SourceId
from pydantic import Field, model_validator

from burro_pipeline.evidence.receipt import is_clean
from burro_pipeline.evidence.record import (
    MADE_UP_SOURCE,
    Day,
    EvidenceRecord,
    FileId,
    Sha256,
    Text,
    Timestamp,
    file_id_of,
    given,
)
from burro_pipeline.release.write import canonical_json

CLAIM_ID_PATTERN = r"^(syn|lon)-c[0-9a-f]{12}$"
# A reason is a code from a closed list that the research part keeps, and never a sentence.
CODE_PATTERN = r"^[a-z][a-z0-9_]*$"

ClaimId = Annotated[str, Field(pattern=CLAIM_ID_PATTERN)]
Code = Annotated[str, Field(pattern=CODE_PATTERN)]


class ClaimKind(StrEnum):
    NAME_ORIGIN = "name_origin"
    HISTORY = "history"
    KNOWN_FOR = "known_for"
    TO_SEE = "to_see"


# The kinds that are about a named thing, which must stand in the words quoted.
NAMES_A_THING = frozenset({ClaimKind.KNOWN_FOR, ClaimKind.TO_SEE})


class FoundBy(StrEnum):
    MODEL_SELECT = "model_select"  # a model pointed at the sentence, and code took the words
    FIRST_SENTENCE = "first_sentence"  # code took the first sentence, and no model chose


class Reviewer(StrEnum):
    """Who reviewed, as a role. Never a name."""

    FOUNDER = "founder"
    SECOND = "second"


class ReviewStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class Derived(EvidenceRecord):
    """How the claim was found. None of it is a source."""

    method: FoundBy
    reader_version: Text
    checks_version: Text
    prompt_version: Text | None = None
    provider: Text | None = None
    model: Text | None = None
    # The second look, by a model from another provider, which can remove and never add.
    second_provider: Text | None = None
    second_model: Text | None = None

    @model_validator(mode="after")
    def _names_a_model_exactly_when_one_chose(self) -> Self:
        chosen = self.method is FoundBy.MODEL_SELECT
        if given(self.prompt_version, self.provider, self.model) is not chosen:
            raise ValueError("a prompt, a provider and a model are named exactly when one chose")
        if given(self.second_provider, self.second_model) is None:
            raise ValueError("the second look names its provider and its model together")
        return self


class Review(EvidenceRecord):
    status: ReviewStatus
    reviewed_on: Day | None = None
    reviewer: Reviewer | None = None
    reason: Code | None = None

    @model_validator(mode="after")
    def _is_signed_when_decided(self) -> Self:
        decided = self.status is not ReviewStatus.PENDING
        if given(self.reviewed_on, self.reviewer) is not decided:
            raise ValueError("a review names its day and its reviewer exactly when it is decided")
        if (self.reason is not None) != (self.status is ReviewStatus.REJECTED):
            raise ValueError("a review gives a reason exactly when it rejects")
        return self


def claim_id_of(area_id: str, source_id: str, page_id: int, quote: str) -> str:
    """The id of a claim, so that the same words keep the same id in every release."""
    named = hashlib.sha256(canonical_json([source_id, page_id, quote])).hexdigest()
    return f"{area_id.split('-')[0]}-c{named[:12]}"


def text_sha256(text: str) -> str:
    """The hash of a page's text, which the offsets of a claim count into."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class Claim(EvidenceRecord):
    claim_id: ClaimId
    area_id: AreaId
    kind: ClaimKind
    # The source's words, as shown. Never edited.
    quote: Text
    # The thing named, for `known_for` and `to_see`. It stands in the quote.
    thing: Text | None = None
    source_id: SourceId
    # The receipt of the page, as code fetched it.
    page: FileId
    title: Text
    # The permanent address of the revision, not of the page. Empty for a made-up page.
    url: str
    # The publisher's own ids.
    page_id: int = Field(ge=0)
    revision_id: int = Field(ge=0)
    # When the revision was made, and when code fetched it.
    source_dated: Timestamp
    retrieved_at: Timestamp
    # Of the bytes fetched, and of the text the offsets count into.
    raw_sha256: Sha256
    text_sha256: Sha256
    # Where the quote stands in the text, in code points, and the heading it stood under.
    start: int = Field(ge=0)
    end: int = Field(ge=1)
    section: str
    derived: Derived
    # Whether the source gave a reference for the sentence.
    has_reference: bool
    review: Review
    first_release: ReleaseId
    licence: Text
    attribution: Text
    # A quotation is always part of a page, and the credit must say so.
    shortened: Literal[True] = True

    @model_validator(mode="after")
    def _holds_together(self) -> Self:
        made_up = self.area_id.startswith(SYNTHETIC_PREFIX)
        if made_up != (self.source_id == MADE_UP_SOURCE):
            raise ValueError("a made-up area is described by the source `synthetic` alone")
        if made_up != self.first_release.startswith(SYNTHETIC_PREFIX):
            raise ValueError("a claim and its first release are both made up, or neither is")
        if self.claim_id != claim_id_of(self.area_id, self.source_id, self.page_id, self.quote):
            raise ValueError("claim_id is not the hash of the source, the page and the quote")
        if self.page != file_id_of(self.raw_sha256):
            raise ValueError("page is not the receipt of the bytes fetched")
        if self.end - self.start != len(self.quote):
            raise ValueError("start and end do not span the quote")
        if (self.thing is not None) != (self.kind in NAMES_A_THING):
            raise ValueError("a thing is named exactly when the kind is about one")
        if self.thing is not None and self.thing not in self.quote:
            raise ValueError("the thing named does not stand in the quote")
        if self.source_dated > self.retrieved_at:
            raise ValueError("a page cannot be fetched before it was written")
        if made_up:
            if self.url:
                raise ValueError("a made-up page has no address")
        elif not is_clean(self.url):
            raise ValueError("url is an https address with no login, key or fragment")
        return self

    def rests_on(self, text: str) -> bool:
        """Whether the quote is in this text as written, at the place the claim says.

        There is no near match. A quote that differs by one letter is not there.
        """
        return text_sha256(text) == self.text_sha256 and text[self.start : self.end] == self.quote

    @property
    def accepted(self) -> bool:
        return self.review.status is ReviewStatus.ACCEPTED
