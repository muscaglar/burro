"""The evidence of one release: its receipts, its methods, its rows and its claims.

It is one document, so that a release and its evidence are enough to trace a
figure back to a publisher's file. It cannot be made with a loose end: a row
that names a method or a file the document does not hold is refused.
"""

from collections.abc import Iterable
from typing import Literal, Self

from burro_core.ids import SYNTHETIC_PREFIX, ReleaseId
from pydantic import PrivateAttr, model_validator

from burro_pipeline.evidence.claim import Claim
from burro_pipeline.evidence.method import Method
from burro_pipeline.evidence.receipt import Receipt
from burro_pipeline.evidence.record import EvidenceRecord, strictly_increasing
from burro_pipeline.evidence.row import EvidenceRow

SCHEMA_VERSION = 1


def _check_row(row: EvidenceRow, receipts: dict[str, Receipt], methods: set[str]) -> None:
    if row.derivation_id is not None and row.derivation_id not in methods:
        raise ValueError("a row names a method the evidence does not hold")
    if any(file_id not in receipts for file_id in row.inputs):
        raise ValueError("a row names a file with no receipt")
    if row.data_period is None or row.retrieved_on is None:
        return
    inputs = [receipts[file_id] for file_id in row.inputs]
    if row.retrieved_on != max(receipt.retrieved_on for receipt in inputs):
        raise ValueError("retrieved_on is not the latest day a file of the row was retrieved")
    first = min(receipt.data_period.days()[0] for receipt in inputs)
    last = max(receipt.data_period.days()[1] for receipt in inputs)
    start, end = row.data_period.days()
    if start < first or end > last:
        raise ValueError("data_period reaches outside the periods of the files of the row")


class Evidence(EvidenceRecord):
    schema_version: Literal[1] = SCHEMA_VERSION
    release_id: ReleaseId
    receipts: tuple[Receipt, ...]
    methods: tuple[Method, ...]
    rows: tuple[EvidenceRow, ...]
    claims: tuple[Claim, ...] = ()

    _receipts: dict[str, Receipt] = PrivateAttr(default_factory=dict[str, Receipt])
    _methods: dict[str, Method] = PrivateAttr(default_factory=dict[str, Method])
    _rows: dict[str, EvidenceRow] = PrivateAttr(default_factory=dict[str, EvidenceRow])

    @classmethod
    def of(
        cls,
        release_id: str,
        receipts: Iterable[Receipt],
        methods: Iterable[Method],
        rows: Iterable[EvidenceRow],
        claims: Iterable[Claim] = (),
    ) -> Self:
        """The evidence of a release, with every list put in the order it is written in."""
        return cls(
            release_id=release_id,
            receipts=tuple(sorted(receipts, key=lambda receipt: receipt.file_id)),
            methods=tuple(sorted(methods, key=lambda method: method.derivation_id)),
            rows=tuple(sorted(rows, key=lambda row: row.fact_id)),
            claims=tuple(sorted(claims, key=lambda claim: claim.claim_id)),
        )

    def model_post_init(self, context: object) -> None:
        self._receipts.update({receipt.file_id: receipt for receipt in self.receipts})
        self._methods.update({method.derivation_id: method for method in self.methods})
        self._rows.update({row.fact_id: row for row in self.rows})

    @model_validator(mode="after")
    def _has_no_loose_end(self) -> Self:
        ids = (
            [receipt.file_id for receipt in self.receipts],
            [method.derivation_id for method in self.methods],
            [row.fact_id for row in self.rows],
            [claim.claim_id for claim in self.claims],
        )
        if not all(strictly_increasing(listed) for listed in ids):
            raise ValueError("every list is sorted by id, each id once")
        made_up = self.release_id.startswith(SYNTHETIC_PREFIX)
        if any(receipt.made_up != made_up for receipt in self.receipts):
            raise ValueError("a made-up file stands behind a made-up release, and no other")
        prefix = self.release_id.split("-")[0] + "-"
        named = [row.fact_id for row in self.rows] + [claim.area_id for claim in self.claims]
        if not all(name.startswith(prefix) for name in named):
            raise ValueError("a row or a claim is about an area of another city")
        receipts = {receipt.file_id: receipt for receipt in self.receipts}
        methods = {method.derivation_id for method in self.methods}
        for row in self.rows:
            _check_row(row, receipts, methods)
        for claim in self.claims:
            page = receipts.get(claim.page)
            if page is None or page.sha256 != claim.raw_sha256:
                raise ValueError("a claim names a page with no receipt")
            if page.source_id != claim.source_id:
                raise ValueError("a claim and the receipt of its page name different sources")
        return self

    def receipt(self, file_id: str) -> Receipt | None:
        return self._receipts.get(file_id)

    def method(self, derivation_id: str) -> Method | None:
        return self._methods.get(derivation_id)

    def row(self, fact_id: str) -> EvidenceRow | None:
        return self._rows.get(fact_id)

    def sources_of(self, row: EvidenceRow) -> frozenset[str]:
        """The sources whose files a row rests on."""
        return frozenset(self._receipts[file_id].source_id for file_id in row.inputs)
