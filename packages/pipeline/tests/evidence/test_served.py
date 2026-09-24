"""No fact is served without evidence, and the rule finds every fact that has none.

The release is the synthetic one and its evidence is made up. Each test plants
a fault in the evidence and checks that the rule names it, and nothing else.
"""

import ast
import json
from pathlib import Path
from typing import Any

import pytest
from burro_core import default_spec, facts_for
from burro_core.ids import FeatureId, Mode, Provenance, Strictness, Tenure
from burro_core.spec import Commute
from burro_pipeline.evidence import made_up
from burro_pipeline.evidence.lock import Lock, LockError, locked, seal
from burro_pipeline.evidence.made_up import made_up_evidence
from burro_pipeline.evidence.receipt import Receipt
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.served import (
    MEANING,
    Finding,
    counted,
    evidence_key,
    served,
    unevidenced,
)
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.registry import Dimension, Registry, Source, Status, Use
from pydantic import ValidationError

from .examples import CLAIM, METHOD, PAGE
from .support import (
    COMMIT,
    NO_REPOSITORY,
    OF_A_RELEASE,
    REAL_ID,
    RELEASE_ID,
    SURVEY,
    changed,
    evidence,
    from_source,
    lock_of,
    real_evidence,
    real_release,
    registered,
    release,
    survey_registry,
    with_receipt,
    with_rows,
    without,
)

PARK, NAME = "syn-n0001/feature/park_proximity", "syn-n0001/area/name"


# The evidence of a release.


def test_the_synthetic_release_has_a_row_behind_every_fact():
    assert unevidenced(release(), evidence()) == ()
    assert unevidenced(release(), evidence(), lock_of(evidence())) == ()
    real = real_evidence()
    assert unevidenced(real_release(), real, lock_of(real), survey_registry()) == ()


def test_the_rule_sees_every_fact_the_api_would_serve():
    keys = {key for key, _ in served(release())}
    facts = {
        f.fact_id for a in release().neighbourhoods for f in facts_for(release(), a.area_id, None)
    }
    assert facts <= keys
    assert len(facts) == 1047
    # And a row for the journeys of every area by every mode, 24 areas by 3 modes.
    assert {key.split("/")[1] for key in keys - facts} == {"travel"}
    assert len(keys - facts) == 72


def test_every_fact_a_search_can_be_answered_with_rests_on_a_row():
    # A budget, and a journey by each mode to a different place: some are beyond the cutoff.
    base = default_spec(Tenure.RENT)
    spec = base.replace(
        budget=base.budget.replace(amount=1500),
        commutes=tuple(
            Commute(
                place_id=place.place_id,
                mode=mode,
                max_minutes=45,
                strictness=Strictness.SOFT,
                provenance=Provenance.STATED,
            )
            for place, mode in zip(release().places, Mode, strict=False)
        ),
    )
    kinds: set[str] = set()
    for area in release().neighbourhoods:
        for fact in facts_for(release(), area.area_id, spec):
            kinds.add(fact.kind)
            row = evidence().row(evidence_key(fact.fact_id))
            assert row is not None and row.has_a_value, fact.fact_id
    assert {"travel", "budget_fit", "missing"} <= kinds


def test_a_fact_that_depends_on_the_search_rests_on_a_row_that_does_not():
    assert evidence_key("syn-n0001/travel/syn-p0001.pt") == "syn-n0001/travel/pt"
    assert evidence_key("syn-n0001/budget_fit/rent.bed_1") == "syn-n0001/cost/rent.bed_1"
    assert evidence_key("syn-n0001/missing/commute") == NAME
    assert evidence_key(PARK) == PARK


# Faults, planted.


def test_a_fact_with_no_row_is_named():
    planted = (PARK, "syn-n0004/cost/rent.bed_1", "syn-n0007/tag/leafy", "syn-n0024/area/name")
    found = unevidenced(release(), without(*planted))
    assert found == tuple(Finding(fact_id, "fact_has_a_row") for fact_id in sorted(planted))


def test_a_journey_with_no_row_is_named():
    found = unevidenced(release(), without("syn-n0002/travel/cycle"))
    assert found == (Finding("syn-n0002/travel/cycle", "fact_has_a_row"),)


def test_a_station_with_no_row_is_named():
    station = release().stations("syn-n0001")[0].station_id
    found = unevidenced(release(), without(f"syn-n0001/station/{station}"))
    assert found == (Finding(f"syn-n0001/station/{station}", "fact_has_a_row"),)


def test_every_fact_is_named_when_there_is_no_row_at_all():
    found = unevidenced(release(), with_rows(()))
    assert len(found) == 1047 + 72
    assert counted(found) == {"fact_has_a_row": 1119}


def suppress(row: dict[str, Any]) -> None:
    row.update(state=State.SUPPRESSED, weight_covered=0, units_used=0)


def test_a_fact_whose_row_says_there_is_no_figure_is_named():
    found = unevidenced(release(), changed(PARK, suppress))
    assert found == (Finding(PARK, "row_has_a_value"),)


def test_a_row_that_says_there_is_a_figure_the_release_lacks_is_named():
    gap = next(row for row in evidence().rows if row.state is State.BELOW_THRESHOLD)
    held = release().feature(gap.area_id, FeatureId(gap.measure.split("/")[1]))
    assert held is not None and held.value is None

    def fill(row: dict[str, Any]) -> None:
        row.update(state=State.PRESENT, weight_covered=1, units_used=10)

    found = unevidenced(release(), changed(gap.fact_id, fill))
    assert found == (Finding(gap.fact_id, "row_has_a_fact"),)


def test_a_row_for_a_gap_is_not_a_fault():
    gaps = [row for row in evidence().rows if not row.has_a_value]
    assert len(gaps) == 82
    # The release has these gaps on purpose, and the evidence says why each is one.
    assert {row.state for row in gaps} == {State.BELOW_THRESHOLD, State.SOURCE_GAP}
    assert unevidenced(release(), evidence()) == ()


def test_a_fact_that_cites_a_source_with_no_file_behind_it_is_named():
    # Every file of the row now comes from another source than the one the fact cites.
    moved = json.loads(real_evidence().canonical())
    for receipt in moved["receipts"]:
        receipt["source_id"] = "made-up-office"
    office = registered("made-up-office", *OF_A_RELEASE)
    elsewhere = Evidence.model_validate(moved)
    found = unevidenced(real_release(), elsewhere, lock_of(elsewhere), survey_registry(office))
    assert len(found) == 1119
    assert counted(found) == {"source_has_a_file": 1119}
    assert SURVEY in {s.source_id for s in real_release().manifest.sources}


def test_a_row_that_rests_on_a_file_outside_the_lock_is_named():
    homes = next(r for r in evidence().receipts if r.publisher_file == "made-up-homes.csv")
    found = unevidenced(release(), evidence(), lock_of(evidence(), leave_out=homes.file_id))
    resting = [row.fact_id for row in evidence().rows if homes.file_id in row.inputs]
    assert found == tuple(Finding(fact_id, "input_is_locked") for fact_id in sorted(resting))
    assert 0 < len(resting) < len(evidence().rows)


# What is kept for the audit, or for the census table, stands behind no figure.


def homes_of(found: Evidence) -> str:
    """The file of homes, which stands behind every measure, every cost and every journey."""
    return next(r.file_id for r in found.receipts if r.publisher_file == "made-up-homes.csv")


def resting_on(found: Evidence, file_id: str) -> tuple[list[str], list[str]]:
    """The rows that rest on a file, and the facts a release serves from those rows."""
    rows = [row.fact_id for row in found.rows if file_id in row.inputs]
    facts = [key for key, _ in served(real_release()) if key in rows]
    return rows, facts


FAITHS = "made-up-faiths"
# What a receipt may say, and the registry with it, of a file that is kept apart. In each,
# the gate would let the file be fetched.
KEPT_APART = {
    "fetched for the audit": ({"use": "audit_only"}, ()),
    "fetched for the census table": ({"use": "census_table"}, ()),
    "from a source under the audit heading": (
        {"source_id": FAITHS, "use": "validation_only"},
        (
            registered(
                FAITHS,
                Use.AUDIT_ONLY,
                Use.VALIDATION_ONLY,
                status=Status.HELD,
                heading=Dimension.AUDIT,
            ),
        ),
    ),
    "from a source under the residents heading": (
        {"source_id": FAITHS, "use": "scoring"},
        (registered(FAITHS, Use.CENSUS_TABLE, heading=Dimension.RESIDENTS, tables=("TS030",)),),
    ),
    "from a source registered for the audit under another heading": (
        {"source_id": FAITHS, "use": "validation_only"},
        (
            registered(
                FAITHS,
                Use.AUDIT_ONLY,
                Use.VALIDATION_ONLY,
                status=Status.HELD,
                heading=Dimension.CULTURE,
            ),
        ),
    ),
}


@pytest.fixture(scope="module", params=KEPT_APART.values(), ids=list(KEPT_APART))
def planted(request: pytest.FixtureRequest) -> tuple[Evidence, tuple[Finding, ...]]:
    """Evidence in which the file of homes is kept apart, and what the rule finds in it."""
    says, entries = request.param
    found = with_receipt(real_evidence(), homes_of(real_evidence()), **says)
    return found, unevidenced(real_release(), found, lock_of(found), survey_registry(*entries))


def test_a_row_that_rests_on_a_file_kept_for_the_audit_or_the_census_table_is_named(
    planted: tuple[Evidence, tuple[Finding, ...]],
):
    evidence_with_it, found = planted
    rows, _ = resting_on(evidence_with_it, homes_of(evidence_with_it))
    named = {finding.fact_id for finding in found if finding.rule == "input_is_for_the_product"}
    assert named == set(rows)
    # Every measure, every cost and every journey rests on the homes. A name does not.
    assert len(rows) == 1152 and "lon-n0001/area/name" not in named


def test_a_fact_whose_evidence_is_kept_for_the_audit_or_the_census_table_is_named(
    planted: tuple[Evidence, tuple[Finding, ...]],
):
    evidence_with_it, found = planted
    _, facts = resting_on(evidence_with_it, homes_of(evidence_with_it))
    named = {finding.fact_id for finding in found if finding.rule == "evidence_is_for_the_product"}
    assert named == set(facts)
    # A fact is served only where there is a figure, so they are fewer than the rows.
    assert len(facts) == 1070
    assert str(next(f for f in found if f.rule == "evidence_is_for_the_product")) == (
        f"{sorted(facts)[0]} is served, and the evidence behind it rests on a file kept for "
        "the audit or for the census table [evidence_is_for_the_product]"
    )
    # Nothing else is found but the file itself, where the lock holds it under a source
    # that is kept apart. The evidence is in order but for that one file.
    assert {finding.rule for finding in found} - {"lock_is_for_the_product"} == {
        "input_is_for_the_product",
        "evidence_is_for_the_product",
    }


def test_a_made_up_file_for_the_audit_stands_behind_no_made_up_figure_either():
    planted = with_receipt(evidence(), homes_of(evidence()), use="audit_only")
    found = counted(unevidenced(release(), planted))
    assert found == {"evidence_is_for_the_product": 1070, "input_is_for_the_product": 1152}


def test_a_file_fetched_to_look_at_may_be_in_the_lock_with_no_row_resting_on_it():
    fields = PAGE.model_dump(mode="json") | {
        "source_id": "made-up-prices",
        "use": "validation_only",
        "how": "fetched",
        "url": "https://data.example.org/prices.csv",
    }
    held = Evidence.of(
        REAL_ID,
        [*real_evidence().receipts, Receipt.model_validate(fields)],
        real_evidence().methods,
        real_evidence().rows,
    )
    prices = registered("made-up-prices", Use.VALIDATION_ONLY, status=Status.GATED)
    assert unevidenced(real_release(), held, lock_of(held), survey_registry(prices)) == ()


# What the registry does not allow for a use stands behind no figure put to that use.


def measures_of(found: Evidence) -> str:
    """The file of measures, which stands behind every feature and every tag, and nothing else."""
    return next(r.file_id for r in found.receipts if r.publisher_file == "made-up-measures.csv")


PRICES = "made-up-prices"
# A file the gate lets fetch keep in the product's store, and lets seal put in the lock. In
# each, the registry does not allow the source for scoring.
NOT_FOR_SCORING = {
    "gated, and read to validate against": (
        {"source_id": PRICES, "use": "validation_only"},
        registered(PRICES, Use.VALIDATION_ONLY, status=Status.GATED),
    ),
    "held, and read for a prototype": (
        {"source_id": PRICES, "use": "prototyping_only"},
        registered(PRICES, Use.PROTOTYPING_ONLY, status=Status.HELD),
    ),
    "approved for routing and the basemap alone": (
        {"source_id": PRICES, "use": "routing"},
        registered(PRICES, Use.ROUTING, Use.BASEMAP, heading=Dimension.TRANSPORT),
    ),
}


@pytest.mark.parametrize(("says", "entry"), NOT_FOR_SCORING.values(), ids=list(NOT_FOR_SCORING))
def test_a_row_that_rests_on_a_file_the_registry_does_not_allow_for_its_use_is_named(
    says: dict[str, str], entry: Source
):
    # The gate allows the file, for the use its receipt gives. So fetch and seal let it by.
    assert survey_registry(entry).require(PRICES, Use(says["use"])).id == PRICES
    planted = with_receipt(real_evidence(), measures_of(real_evidence()), **says)
    found = unevidenced(real_release(), planted, lock_of(planted), survey_registry(entry))
    rows = [row.fact_id for row in planted.rows if measures_of(planted) in row.inputs]
    assert found == tuple(Finding(row, "input_is_allowed") for row in sorted(rows))
    assert {row.split("/")[1] for row in rows} == {"feature", "tag"} and len(rows) == 840
    assert str(found[0]) == (
        f"{sorted(rows)[0]} rests on a file that the licence registry does not allow for what "
        "this figure is used for, or that was fetched for an internal use [input_is_allowed]"
    )


@pytest.mark.parametrize("use", ["validation_only", "prototyping_only"])
def test_a_row_that_rests_on_a_file_fetched_for_an_internal_use_is_named(use: str):
    # Its source is approved for every use of a release. Its receipt says what it was read for.
    planted = with_receipt(real_evidence(), measures_of(real_evidence()), use=use)
    found = unevidenced(real_release(), planted, lock_of(planted), survey_registry())
    assert counted(found) == {"input_is_allowed": 840}
    # A made-up file is held to its receipt too, with no registry to ask.
    made_up = with_receipt(evidence(), measures_of(evidence()), use=use)
    assert counted(unevidenced(release(), made_up)) == {"input_is_allowed": 840}


OFFICE = "made-up-office"
# The use a source must be registered for to stand behind a row, by the kind of the row.
USE_OF_A_ROW = {
    "area": Use.GAZETTEER,
    "feature": Use.SCORING,
    "tag": Use.SCORING,
    "cost": Use.SCORING,
    "travel": Use.ROUTING,
    "station": Use.DISPLAY,
}


@pytest.mark.parametrize("lacks", sorted(set(USE_OF_A_ROW.values())))
def test_a_source_is_asked_for_the_use_of_the_file_that_serves_the_fact(lacks: Use):
    # Every file comes from a source that is approved for every use of a release but one.
    moved = json.loads(real_evidence().canonical())
    for receipt in moved["receipts"]:
        receipt["source_id"] = OFFICE
    elsewhere = Evidence.model_validate(moved)
    office = registered(OFFICE, *(use for use in OF_A_RELEASE if use is not lacks))
    found = unevidenced(real_release(), elsewhere, lock_of(elsewhere), survey_registry(office))
    named = {f.fact_id for f in found if f.rule == "input_is_allowed"}
    kinds = {kind for kind, use in USE_OF_A_ROW.items() if use is lacks}
    assert named == {row.fact_id for row in elsewhere.rows if row.fact_id.split("/")[1] in kinds}
    assert named
    # Nothing else is found but that the facts cite a source no file came from.
    assert {f.rule for f in found} == {"input_is_allowed", "source_has_a_file"}


def test_every_kind_of_row_has_a_use_to_be_asked_for():
    from burro_pipeline.evidence.row import ROW_KINDS
    from burro_pipeline.evidence.served import USE_OF_A_ROW as held

    assert dict(held) == {kind: USE_OF_A_ROW[kind] for kind in ROW_KINDS}


def test_a_row_with_no_figure_that_rests_on_such_a_file_is_named_too():
    gap = next(row for row in real_evidence().rows if row.state is State.BELOW_THRESHOLD)
    assert measures_of(real_evidence()) in gap.inputs
    planted = with_receipt(real_evidence(), measures_of(real_evidence()), use="validation_only")
    found = unevidenced(real_release(), planted, lock_of(planted), survey_registry())
    assert Finding(gap.fact_id, "input_is_allowed") in found


def test_a_file_that_is_not_made_up_is_allowed_nothing_where_there_is_no_registry_to_ask():
    from burro_pipeline.evidence.served import is_allowed

    fetched, made_up = real_evidence().receipts[0], evidence().receipts[0]
    assert (fetched.made_up, made_up.made_up) == (False, True)
    for use in OF_A_RELEASE:
        assert not is_allowed(fetched, use, None)
        assert is_allowed(fetched, use, survey_registry())
        # A made-up file is under no entry, so nothing is asked of a registry about it.
        assert is_allowed(made_up, use, None)
        assert is_allowed(made_up, use, survey_registry())


def test_a_lock_that_holds_a_file_kept_for_the_audit_is_named_by_the_file():
    faiths = registered(FAITHS, Use.AUDIT_ONLY, status=Status.HELD, heading=Dimension.AUDIT)
    kept_apart = locked(from_source(real_evidence().receipts[0], FAITHS))
    lock = lock_of(real_evidence())
    inputs = sorted((*lock.inputs[1:], kept_apart), key=lambda found: found.name)
    lock = Lock.model_validate(lock.model_dump(mode="json") | {"inputs": inputs})
    found = unevidenced(real_release(), real_evidence(), lock, survey_registry(faiths))
    assert found == (Finding(kept_apart.name, "lock_is_for_the_product"),)
    unknown = unevidenced(real_release(), real_evidence(), lock, survey_registry())
    assert unknown == (Finding(kept_apart.name, "source_is_registered"),)


def test_a_row_that_rests_on_a_file_of_a_source_the_registry_does_not_hold_is_named():
    # Nothing shows that such a file is not kept for the audit.
    planted = with_receipt(real_evidence(), homes_of(real_evidence()), source_id=FAITHS)
    rows, _ = resting_on(planted, homes_of(planted))
    found = unevidenced(real_release(), planted, lock_of(real_evidence()), survey_registry())
    assert found == tuple(Finding(row, "source_is_registered") for row in sorted(rows))
    assert str(found[0]).endswith(
        " rests on a file whose source is not in the licence registry, or is such a file in "
        "the lock [source_is_registered]"
    )


def test_a_real_release_is_checked_against_its_lock_and_the_registry_or_not_at_all():
    found, lock, held = real_evidence(), lock_of(real_evidence()), survey_registry()
    given: list[tuple[Lock | None, Registry | None, str]] = [
        (None, held, "real_release_needs_a_lock"),
        (lock, None, "real_release_needs_a_registry"),
        (None, None, "real_release_needs_a_lock"),
    ]
    for the_lock, the_registry, rule in given:
        with pytest.raises(LockError) as caught:
            unevidenced(real_release(), found, the_lock, the_registry)
        assert (caught.value.rule, caught.value.subject) == (rule, REAL_ID)
    # A made-up release is built from no file, so it has no lock to be held to.
    assert unevidenced(release(), evidence()) == ()


# A method names the code that worked a figure out.


def with_method(code: str) -> Evidence:
    """The made-up evidence, with its one method said to be in another module."""
    fields = json.loads(evidence().canonical())
    fields["methods"][0]["code"] = code
    return Evidence.model_validate(fields)


@pytest.mark.parametrize(
    "code",
    [
        "burro_pipeline.release.synthetic",
        "burro_pipeline.release.synthetic.build",
        "burro_pipeline.evidence.row",
        "burro_core.rank",
        "burro_core",
    ],
)
def test_a_method_whose_module_is_part_of_the_pipeline_or_of_core_is_found(code: str):
    assert unevidenced(release(), with_method(code)) == ()


@pytest.mark.parametrize(
    "code",
    [
        # The example of the README: the step that will hold it is not built.
        METHOD.code,
        "burro_pipeline.release.synthetic.nowhere",
        "burro_pipeline.evidence.readme",
        "burro_pipeline.evidence.row.state",
        "burro_core.nowhere",
        "burro_pipeline_",
        # Modules that are there, and are no part of the pipeline or of core.
        "json",
        "os.path",
        "pydantic",
        "pytest",
    ],
)
def test_a_method_whose_module_cannot_be_found_is_named(code: str):
    found = unevidenced(release(), with_method(code))
    assert found == (Finding("made_up@1", "method_is_found"),)
    assert str(found[0]) == (
        "made_up@1 names a module that is not in the pipeline or in core, so nobody can "
        "read how its figures were worked out [method_is_found]"
    )


def test_looking_for_the_module_of_a_method_loads_nothing():
    import sys

    before = set(sys.modules)
    unevidenced(release(), with_method("burro_pipeline.fetch.s3"))
    unevidenced(release(), with_method("zzyzx.parva"))
    assert set(sys.modules) == before


def test_evidence_of_another_release_stands_behind_nothing():
    other = Evidence.of("syn-2026-09-24-01", evidence().receipts, evidence().methods, ())
    assert unevidenced(release(), other) == (Finding(RELEASE_ID, "evidence_is_of_this_release"),)
    lock = seal("syn-2026-09-24-01", "2026-09-24T00:00:00Z", COMMIT, (), {}, None, NO_REPOSITORY)
    assert unevidenced(release(), evidence(), lock) == (
        Finding(RELEASE_ID, "evidence_is_of_this_release"),
    )
    assert REAL_ID != RELEASE_ID


def test_a_finding_is_said_in_one_line_and_counted_by_rule():
    found = unevidenced(release(), without(PARK, NAME))
    assert str(found[1]) == (
        f"{PARK} is served, and no row of evidence stands behind it [fact_has_a_row]"
    )
    assert counted(found) == {"fact_has_a_row": 2}
    assert counted(()) == {}
    assert all(" " in meaning and "\n" not in meaning for meaning in MEANING.values())


# Evidence that cannot be made.


def fields() -> dict[str, Any]:
    return json.loads(evidence().canonical())


def refusal(document: dict[str, Any]) -> str:
    with pytest.raises(ValidationError) as caught:
        Evidence.model_validate(document)
    return str(caught.value)


def test_evidence_reads_back_as_it_was_written():
    written = evidence().canonical()
    assert Evidence.model_validate_json(written) == evidence()
    assert Evidence.model_validate_json(written).digest() == evidence().digest()
    assert Evidence.model_validate_json(written).row(PARK) == evidence().row(PARK)


def test_evidence_cannot_hold_a_row_that_names_a_method_it_does_not_hold():
    none: list[Any] = []
    document = fields() | {"methods": none}
    assert "names a method the evidence does not hold" in refusal(document)


def test_evidence_cannot_hold_a_row_that_names_a_file_with_no_receipt():
    document = fields()
    document["receipts"] = document["receipts"][1:]
    assert "names a file with no receipt" in refusal(document)


def test_a_row_is_dated_by_the_files_it_rests_on():
    early, late, outside = fields(), fields(), fields()
    early["rows"][0]["retrieved_on"] = "2026-09-22"
    late["rows"][0]["retrieved_on"] = "2026-09-24"
    outside["rows"][0]["data_period"] = {"as_at": "2019"}
    for document in (early, late):
        assert "retrieved_on is not the latest day" in refusal(document)
    assert "data_period reaches outside" in refusal(outside)


def test_every_list_of_evidence_is_in_order_with_nothing_twice():
    for name in ("receipts", "rows"):
        assert "sorted by id" in refusal(fields() | {name: fields()[name][::-1]})
        assert "sorted by id" in refusal(fields() | {name: fields()[name][:1] * 2})


def test_a_claim_is_kept_with_the_receipt_of_its_page():
    held = Evidence.of(RELEASE_ID, [*evidence().receipts, PAGE], evidence().methods, (), [CLAIM])
    assert held.claims == (CLAIM,)
    receipt = held.receipt(CLAIM.page)
    assert receipt is not None and receipt.sha256 == CLAIM.raw_sha256
    with pytest.raises(ValidationError, match="names a page with no receipt"):
        Evidence.of(RELEASE_ID, evidence().receipts, (), (), [CLAIM])


def test_made_up_files_stand_behind_a_made_up_release_and_no_other():
    assert "stands behind a made-up release" in refusal(fields() | {"release_id": REAL_ID})
    real = json.loads(real_evidence().canonical())
    assert "stands behind a made-up release" in refusal(real | {"release_id": RELEASE_ID})
    assert "area of another city" in refusal(real | {"rows": fields()["rows"]})
    with pytest.raises(ValidationError):
        from_source(evidence().receipts[0], SURVEY)


# The made-up evidence itself.


def test_made_up_evidence_is_the_same_every_time():
    assert made_up_evidence(release()).canonical() == evidence().canonical()


def test_made_up_evidence_is_unmistakably_made_up():
    assert {receipt.source_id for receipt in evidence().receipts} == {"synthetic"}
    assert {receipt.how for receipt in evidence().receipts} == {"made_up"}
    assert all(receipt.url == "" for receipt in evidence().receipts)
    assert all(r.publisher_file.startswith("made-up-") for r in evidence().receipts)
    assert [method.derivation_id for method in evidence().methods] == ["made_up@1"]
    assert "measures nothing" in evidence().methods[0].sentence
    assert all(row.fact_id.startswith("syn-") for row in evidence().rows)


def test_evidence_is_made_up_for_a_synthetic_release_and_for_no_other():
    with pytest.raises(ValueError, match="for a synthetic release"):
        made_up_evidence(real_release())


def test_made_up_evidence_reads_no_file_and_reaches_no_network():
    tree = ast.parse(Path(made_up.__file__).read_text(encoding="utf-8"))
    imported = {
        node.module if isinstance(node, ast.ImportFrom) else alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import | ast.ImportFrom)
        for alias in node.names
    }
    outside = {name for name in imported if name and not name.startswith("burro_")}
    assert outside <= {"hashlib", "math", "collections.abc"}
    named = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    assert not named & {"open", "print", "Path"}
