"""The four records of evidence: the receipt, the method, the evidence row and the claim.

Every value here is made up. No file was fetched and none is read.
"""

import hashlib
import json
from typing import Any

import pytest
from burro_pipeline.evidence.claim import Claim, claim_id_of
from burro_pipeline.evidence.method import Method
from burro_pipeline.evidence.receipt import Period, Receipt, Where, clean_url
from burro_pipeline.evidence.record import EvidenceRecord, file_id_of, in_words
from burro_pipeline.evidence.row import EvidenceRow, State, state_of
from burro_pipeline.release import canonical_json
from pydantic import ValidationError

from .examples import CLAIM, METHOD, PAGE, PAGE_TEXT, RECEIPT, ROW

# A string found nowhere else. If a refusal repeats what it was given, this shows up in it.
CANARY = "Zzyzx Parva"
EXAMPLES: tuple[EvidenceRecord, ...] = (RECEIPT, METHOD, ROW, CLAIM)
SHA = hashlib.sha256(b"a made-up file").hexdigest()


def changed(record: EvidenceRecord, **changes: Any) -> dict[str, Any]:
    """A record as it is written, with some fields changed. It has not been validated."""
    return record.model_dump(mode="json") | changes


def fetched(**changes: Any) -> dict[str, Any]:
    """A receipt of a file that code fetched from a made-up publisher."""
    real = {
        "file_id": file_id_of(SHA),
        "sha256": SHA,
        "source_id": "made-up-survey",
        "how": "fetched",
        "url": "https://data.example.org/files/parks.gpkg?edition=2025",
    }
    return changed(RECEIPT, **(real | changes))


def refusal(kind: type[EvidenceRecord], fields: dict[str, Any]) -> str:
    with pytest.raises(ValidationError) as caught:
        kind.model_validate(fields)
    return in_words(caught.value)


# What every record shares.


@pytest.mark.parametrize("record", EXAMPLES, ids=lambda record: type(record).__name__)
def test_a_record_is_written_one_way_and_reads_back_the_same(record: EvidenceRecord):
    written = record.canonical()
    assert written == canonical_json(json.loads(written))
    assert type(record).model_validate_json(written) == record
    assert type(record).model_validate_json(written).digest() == record.digest()
    assert record.digest() == hashlib.sha256(written).hexdigest()


def test_the_examples_have_the_hashes_written_here():
    # If one moves, the canonical form moved, and every hash ever written with it. The row
    # moved on 2026-09-24, when it came to hold its figure. No release had been approved.
    assert [record.digest()[:16] for record in EXAMPLES] == [
        "d937248d82ca6f38",
        "a5259d0b7e9fd33d",
        "841a77ce20af32a9",
        "7932fe2d55aba4d9",
    ]


@pytest.mark.parametrize("record", EXAMPLES, ids=lambda record: type(record).__name__)
def test_a_record_cannot_be_changed_and_refuses_a_field_it_does_not_know(record: EvidenceRecord):
    with pytest.raises(ValidationError):
        record.__setattr__(next(iter(type(record).model_fields)), "changed")
    assert "holds a field that a record does not have" in refusal(
        type(record), changed(record, colour="red")
    )


@pytest.mark.parametrize("record", EXAMPLES, ids=lambda record: type(record).__name__)
def test_a_refusal_never_repeats_what_it_was_given(record: EvidenceRecord):
    first = next(iter(type(record).model_fields))
    # Every field holds it, and then one field holds it where a word should be.
    for fields in ({name: CANARY for name in type(record).model_fields}, {first: [CANARY]}):
        with pytest.raises(ValidationError) as caught:
            type(record).model_validate(changed(record) | fields)
        assert CANARY not in in_words(caught.value)
        assert CANARY not in str(caught.value)
    # The name of a field a record does not know is left out too, by `in_words` alone:
    # it is what a refusal is printed with.
    with pytest.raises(ValidationError) as caught:
        type(record).model_validate(changed(record, **{CANARY: 1}))
    assert CANARY not in in_words(caught.value)


# The receipt.


def test_a_file_is_named_by_the_first_twelve_digits_of_its_hash():
    assert RECEIPT.file_id == f"f-{RECEIPT.sha256[:12]}"
    assert "file_id is not" in refusal(Receipt, changed(RECEIPT, file_id="f-000000000000"))


def test_a_receipt_says_where_its_file_is_kept_and_where_it_is_kept_itself():
    receipt = Receipt.model_validate(fetched())
    assert receipt.vault_key() == f"raw/made-up-survey/{SHA}/made-up-parks.gpkg"
    assert receipt.path().as_posix() == f"data/receipts/made-up-survey/f-{SHA[:12]}.json"
    assert receipt.retrieved_on == "2026-09-23"


@pytest.mark.parametrize(
    "address",
    [
        "https://data.example.org/files/parks.gpkg?app_key=abc123",
        "https://data.example.org/files/parks.gpkg?edition=2025&access_token=abc123",
        "https://data.example.org/files/parks.gpkg?X-Amz-Signature=abc123",
        "https://data.example.org/files/parks.gpkg#abc123",
        "https://reader:abc123@data.example.org/files/parks.gpkg",  # public-only: allow
        "https://reader@data.example.org/files/parks.gpkg",  # public-only: allow
    ],
)
def test_a_receipt_refuses_an_address_that_holds_a_key(address: str):
    said = refusal(Receipt, fetched(url=address))
    assert "no login, key or fragment" in said
    assert "abc123" not in said
    # What `clean_url` makes of it is what a receipt stores.
    cleaned = clean_url(address)
    assert "abc123" not in cleaned and "reader" not in cleaned
    assert Receipt.model_validate(fetched(url=cleaned)).url == cleaned


def test_clean_url_keeps_what_names_the_file():
    kept = "https://data.example.org:8443/files/parks.gpkg?edition=2025&id=7"
    assert clean_url(kept + "&api_key=abc123") == kept
    assert clean_url(kept) == kept
    assert clean_url(clean_url(kept)) == clean_url(kept)


@pytest.mark.parametrize(
    "address",
    [
        "http://data.example.org/parks.gpkg",
        "ftp://data.example.org/a",
        "parks.gpkg",
        "",
        "https://",
    ],
)
def test_a_receipt_refuses_an_address_that_is_not_https(address: str):
    assert "https" in refusal(Receipt, fetched(url=address))


def test_an_address_that_cannot_be_read_is_refused_and_not_quoted():
    said = refusal(Receipt, fetched(url=f"https://data.example.org:{CANARY}/parks"))
    assert "https" in said and CANARY not in said


LISTED = "https://data.example.org/files/latest?edition=2025"


def test_a_receipt_may_hold_the_address_the_list_gave_beside_the_one_the_file_came_from():
    receipt = Receipt.model_validate(fetched(listed_url=LISTED))
    assert receipt.listed_url == LISTED != receipt.url
    assert json.loads(receipt.canonical())["listed_url"] == LISTED
    assert Receipt.model_validate_json(receipt.canonical()) == receipt
    # It is held as clean as the address the file came from.
    for address in (f"{LISTED}&api_key=abc123", f"{LISTED}#abc123", "http://data.example.org/a"):
        said = refusal(Receipt, fetched(listed_url=address))
        assert "listed_url is an https address" in said and "abc123" not in said


def test_a_receipt_with_no_listed_address_is_written_as_it_was_before_the_field():
    without = Receipt.model_validate(fetched())
    assert without.listed_url is None
    assert "listed_url" not in json.loads(without.canonical())
    assert Receipt.model_validate(fetched(listed_url=None)) == without
    # So a receipt written before the field reads back as the same record, with the same hash.
    before = canonical_json({k: v for k, v in fetched().items() if k != "listed_url"})
    assert Receipt.model_validate_json(before).canonical() == before
    # A made-up file has no address of either kind, and the README's example is of one.
    assert "listed_url" not in RECEIPT.model_dump(mode="json")
    assert "has no address" in refusal(Receipt, changed(RECEIPT, listed_url=LISTED))


# Where an edition was read, when no page of the publisher states one.
IN_THE_HEADER = {"where": "xml_header", "at": "Header/ExtractDate", "period_too": True}
LAST_CHANGE = {"where": "geopackage", "at": "gpkg_contents.last_change", "period_too": False}
RUNS_TO = {
    "where": "street_extract",
    "at": "OSMHeader.osmosis_replication_timestamp",
    "period_too": True,
}
THE_DAY_RETRIEVED = {"where": "retrieved", "at": "", "period_too": True}


@pytest.mark.parametrize("read", [IN_THE_HEADER, LAST_CHANGE, RUNS_TO, THE_DAY_RETRIEVED])
def test_a_receipt_says_where_its_edition_was_read_when_no_page_stated_it(read: dict[str, Any]):
    receipt = Receipt.model_validate(fetched(edition_from=read))
    assert receipt.edition_from is not None
    assert receipt.edition_from.where is Where(read["where"])
    assert json.loads(receipt.canonical())["edition_from"] == read
    assert Receipt.model_validate_json(receipt.canonical()) == receipt


def test_a_receipt_of_an_edition_that_a_page_stated_is_written_as_it_was_before_the_field():
    """So a reader tells the two apart, and every receipt written before reads back the same."""
    stated = Receipt.model_validate(fetched())
    assert stated.edition_from is None
    assert "edition_from" not in json.loads(stated.canonical())
    assert Receipt.model_validate(fetched(edition_from=None)) == stated
    before = canonical_json({k: v for k, v in fetched().items() if k != "edition_from"})
    assert Receipt.model_validate_json(before).canonical() == before
    assert "edition_from" not in RECEIPT.model_dump(mode="json")
    # Two receipts that state one edition are not the same record if one read it in the file.
    assert Receipt.model_validate(fetched(edition_from=IN_THE_HEADER)) != stated


def test_the_day_a_geopackage_was_last_changed_is_never_the_period_of_its_data():
    """The day is about the file. When its data is as at, the file does not say."""
    said = refusal(Receipt, fetched(edition_from=LAST_CHANGE | {"period_too": True}))
    assert "is about the file" in said


@pytest.mark.parametrize(
    ("read", "said"),
    [
        ({"where": "xml_header", "at": "", "period_too": True}, "the header and the element"),
        ({"where": "xml_header", "at": "ExtractDate", "period_too": True}, "the header and"),
        ({"where": "xml_header", "at": "Header/Extract Date", "period_too": True}, "the header"),
        ({"where": "xml_header", "at": f"Header/{CANARY}", "period_too": True}, "the header"),
        ({"where": "xml_header", "at": "A/B/C", "period_too": True}, "the header"),
        ({"where": "geopackage", "at": "", "period_too": False}, "gpkg_contents.last_change"),
        ({"where": "geopackage", "at": "layer.updated", "period_too": False}, "last_change"),
        ({"where": "street_extract", "at": "", "period_too": True}, "osmosis_replication"),
        ({"where": "retrieved", "at": "Header/ExtractDate", "period_too": True}, "names no place"),
        ({"where": "the page", "at": "", "period_too": True}, "where"),
        ({"where": "retrieved", "at": ""}, "period_too"),
        ({"where": "retrieved", "at": "", "period_too": True, "words": "retrieved"}, "does not"),
    ],
)
def test_where_an_edition_was_read_is_a_place_that_kind_of_file_has(
    read: dict[str, Any], said: str
):
    found = refusal(Receipt, fetched(edition_from=read))
    assert said in found and CANARY not in found


def test_a_made_up_file_states_no_place_its_edition_was_read():
    assert "has no edition that was read" in refusal(
        Receipt, changed(RECEIPT, edition_from=THE_DAY_RETRIEVED)
    )


def test_a_made_up_file_cites_the_source_synthetic_and_nothing_else_does():
    assert (RECEIPT.source_id, RECEIPT.how, RECEIPT.url) == ("synthetic", "made_up", "")
    assert "made-up" in RECEIPT.publisher_file
    assert "cites the source `synthetic`" in refusal(Receipt, fetched(how="made_up", url=""))
    assert "cites the source `synthetic`" in refusal(Receipt, fetched(source_id="synthetic"))
    assert "has no address" in refusal(
        Receipt, changed(RECEIPT, url="https://data.example.org/parks.gpkg")
    )


@pytest.mark.parametrize(
    "name", ["../parks.gpkg", "a/b.csv", "a\\b.csv", ".", "..", ".hidden", "", "a\nb", "x" * 256]
)
def test_a_file_name_cannot_lead_out_of_its_place_in_the_vault(name: str):
    assert "publisher_file" in refusal(Receipt, fetched(publisher_file=name))


@pytest.mark.parametrize(
    "period",
    [
        {"as_at": "2025-03-31"},
        {"as_at": "2025"},
        {"start": "2023-08", "end": "2026-07"},
        {"start": "2024-02-29", "end": "2024-02-29"},
    ],
)
def test_a_period_is_one_date_or_a_span(period: dict[str, str]):
    assert Period.model_validate(period).model_dump(exclude_none=True) == period


@pytest.mark.parametrize(
    "period",
    [
        {},
        {"start": "2023-08"},
        {"end": "2023-08"},
        {"as_at": "2025", "start": "2023", "end": "2026"},
        {"start": "2026-07", "end": "2023-08"},
        {"as_at": "2025-02-30"},
        {"as_at": "2025-13"},
        {"as_at": "25"},
        {"as_at": "2025-3-1"},
    ],
)
def test_a_period_that_is_no_period_is_refused(period: dict[str, str]):
    with pytest.raises(ValidationError):
        Period.model_validate(period)


def test_a_period_runs_from_its_first_day_to_its_last():
    assert Period(as_at="2024-02").days() == ("2024-02-01", "2024-02-29")
    assert Period(start="2023", end="2025-06").days() == ("2023-01-01", "2025-06-30")


@pytest.mark.parametrize(
    "stamp",
    ["2026-09-23", "2026-09-23T09:12:31", "2026-09-23T09:12:31+01:00", "2026-02-30T00:00:00Z"],
)
def test_a_file_is_retrieved_at_a_time_in_utc(stamp: str):
    assert "retrieved_at" in refusal(Receipt, fetched(retrieved_at=stamp))


@pytest.mark.parametrize(
    "path",
    [
        "terms.pdf",
        "/registry/evidence/terms.pdf",
        "registry/evidence/../terms.pdf",
        "registry/evidence/a/terms.pdf",
        "registry/evidence/",
    ],
)
def test_licence_evidence_names_a_file_in_the_evidence_folder(path: str):
    kept = "registry/evidence/made-up-survey-2026-09-23.pdf"
    assert Receipt.model_validate(fetched(licence_evidence=kept)).licence_evidence == kept
    assert "registry/evidence/" in refusal(Receipt, fetched(licence_evidence=path))


def test_the_files_read_from_a_zip_are_named_in_order_each_once():
    inside = [{"name": name, "sha256": SHA, "bytes": 1} for name in ("a.csv", "b.csv")]
    assert len(Receipt.model_validate(fetched(members=inside)).members) == 2
    assert "name order" in refusal(Receipt, fetched(members=inside[::-1]))
    assert "name order" in refusal(Receipt, fetched(members=[inside[0], inside[0]]))


def test_the_geography_of_a_file_is_unknown_until_it_is_read():
    assert Receipt.model_validate(fetched(geography=None)).geography is None
    assert "geography" in refusal(Receipt, fetched(geography="lsoa"))


# The method.


def test_a_method_is_named_and_numbered():
    assert (METHOD.name, METHOD.version) == ("walk_to_nearest", 1)
    for wrong in ("walk_to_nearest", "walk_to_nearest@0", "Walk@1", "walk to nearest@1", "@1"):
        assert "derivation_id" in refusal(Method, changed(METHOD, derivation_id=wrong))


def test_a_method_states_every_parameter_in_its_sentence():
    unsaid = changed(METHOD, parameters={"hectares": 2, "metres": 300})
    assert "does not state every parameter" in refusal(Method, unsaid)
    # A number inside another number is not that number: 30 is not said by 300.
    almost = changed(METHOD, sentence="Parks within 300 metres.", parameters={"metres": 30})
    assert "does not state every parameter" in refusal(Method, almost)
    said = changed(
        METHOD,
        sentence="The share of homes within 1,200 metres of a park of 0.5 hectares, by homes.",
        parameters={"metres": 1200.0, "hectares": 0.5, "weight": "homes"},
    )
    assert Method.model_validate(said).parameters["metres"] == 1200


@pytest.mark.parametrize(
    "sentence", ["", "No full stop", "Two sentences. In one.", "A line\nbreak.", "Is it? No."]
)
def test_a_method_is_said_in_one_sentence(sentence: str):
    assert "sentence" in refusal(Method, changed(METHOD, sentence=sentence, parameters={}))


def test_a_parameter_is_a_number_or_a_word_and_never_yes_or_no():
    assert "parameters" in refusal(Method, changed(METHOD, parameters={"hectares": True}))
    assert "lower case" in refusal(Method, changed(METHOD, parameters={"Hectares": 2}))


# The evidence row.


def test_a_row_is_keyed_by_the_id_of_its_fact():
    assert (ROW.area_id, ROW.measure) == ("syn-n0001", "feature/park_proximity")
    for wrong in (
        "feature/park_proximity",
        "syn-n0001/feature",
        "syn-d0001/feature/park_proximity",
        "syn-n0001/budget_fit/rent.bed_1",
        "syn-n0001/missing/commute",
        "syn-n0001/Feature/park",
    ):
        assert "fact_id" in refusal(EvidenceRow, changed(ROW, fact_id=wrong))


@pytest.mark.parametrize(
    ("state", "covered", "fits"),
    [
        ("present", 1.0, True),
        ("present", 0.99, True),
        ("present", 0.98, False),
        ("partial", 0.98, True),
        ("partial", 0.5, True),
        ("partial", 0.0, False),
        ("partial", 1.0, False),
        ("below_threshold", 0.3, True),
        ("below_threshold", 0.0, False),
        ("below_threshold", 1.0, False),
        ("source_gap", 0.0, True),
        ("source_gap", 0.2, False),
        ("suppressed", 0.0, True),
        ("suppressed", 0.7, True),
    ],
)
def test_the_state_of_a_row_suits_the_share_covered(state: str, covered: float, fits: bool):
    used = 0 if covered == 0 else 5
    value = ROW.value if state in ("present", "partial") else None
    fields = changed(ROW, state=state, weight_covered=covered, units_used=used, value=value)
    if fits:
        assert EvidenceRow.model_validate(fields).has_a_value == (state in ("present", "partial"))
    else:
        assert "does not suit the state" in refusal(EvidenceRow, fields)


def test_a_row_names_its_files_unless_no_file_was_read():
    bare: dict[str, Any] = {"inputs": [], "derivation_id": None}
    bare |= {"data_period": None, "retrieved_on": None}
    nothing = bare | {"weight_covered": 0, "units_used": 0, "units_expected": 0, "value": None}
    for state in (State.NOT_CARRIED, State.NOT_PUBLISHED):
        assert not EvidenceRow.model_validate(changed(ROW, state=state, **nothing)).has_a_value
    assert "names the files it rests on" in refusal(EvidenceRow, changed(ROW, **bare))
    assert "rests on no file" in refusal(
        EvidenceRow, changed(ROW, state="not_carried", weight_covered=0, units_used=0)
    )
    for name in ("derivation_id", "data_period", "retrieved_on"):
        assert "exactly when a file is" in refusal(EvidenceRow, changed(ROW, **{name: None}))


def test_a_row_holds_a_figure_only_where_it_has_one_and_is_one_number():
    assert ROW.value == 290.0 and ROW.has_a_value
    gap = changed(ROW, state="below_threshold", weight_covered=0.3)
    assert "a figure is held only by a row that has one" in refusal(EvidenceRow, gap)
    label = changed(ROW, fact_id="syn-n0001/area/name")
    assert "only by a row of a measure or of a tag" in refusal(EvidenceRow, label)
    assert EvidenceRow.model_validate(changed(ROW, value=None)).has_a_value
    assert "value" in refusal(EvidenceRow, changed(ROW, value="about 290"))


def test_a_row_lists_its_files_and_its_flags_in_order_each_once():
    assert list(ROW.inputs) == sorted(ROW.inputs)
    assert "sorted" in refusal(EvidenceRow, changed(ROW, inputs=list(ROW.inputs)[::-1]))
    assert "sorted" in refusal(EvidenceRow, changed(ROW, inputs=[ROW.inputs[0]] * 2))
    assert "sorted" in refusal(EvidenceRow, changed(ROW, flags=["unit_split", "unit_split"]))
    assert "flags" in refusal(EvidenceRow, changed(ROW, flags=["a_flag_nobody_defined"]))


def test_a_share_is_held_as_it_is_written_so_a_record_equals_what_is_read_back():
    third = EvidenceRow.model_validate(changed(ROW, weight_covered=2 / 3))
    assert third.weight_covered == 0.666667
    assert EvidenceRow.model_validate_json(third.canonical()) == third
    # The state is judged on the share as it is written, so the two cannot disagree on disk.
    nearly = changed(ROW, weight_covered=0.9899999)
    assert "does not suit the state" in refusal(EvidenceRow, nearly)
    assert EvidenceRow.model_validate(nearly | {"state": "present"}).weight_covered == 0.99
    assert state_of(True, round(0.9899999, 6)) is State.PRESENT


def test_a_row_never_uses_more_units_than_it_expected():
    assert "units_used" in refusal(EvidenceRow, changed(ROW, units_used=12, units_expected=11))


@pytest.mark.parametrize(
    ("has_value", "covered", "state"),
    [
        (True, 1.0, State.PRESENT),
        (True, 0.99, State.PRESENT),
        (True, 0.6, State.PARTIAL),
        (False, 0.4, State.BELOW_THRESHOLD),
        (False, 0.0, State.SOURCE_GAP),
    ],
)
def test_a_figure_that_is_missing_is_a_gap_and_never_a_nought(
    has_value: bool, covered: float, state: State
):
    assert state_of(has_value, covered) is state


# The claim.


def test_a_claim_rests_on_the_words_as_written():
    assert CLAIM.rests_on(PAGE_TEXT)
    assert PAGE_TEXT[CLAIM.start : CLAIM.end] == CLAIM.quote
    # No near match: one letter, one space or one more sentence, and the words are not there.
    assert not CLAIM.rests_on(PAGE_TEXT.replace("opened", "opend"))
    assert not CLAIM.rests_on(" " + PAGE_TEXT)
    assert not CLAIM.rests_on(PAGE_TEXT + "It closed in 1964.\n")
    altered = Claim.model_validate(
        changed(
            CLAIM,
            quote=CLAIM.quote.replace("1907", "1807"),
            claim_id=claim_id_of(
                "syn-n0001", "synthetic", 4021, CLAIM.quote.replace("1907", "1807")
            ),
        )
    )
    assert not altered.rests_on(PAGE_TEXT)


def test_the_same_words_keep_the_same_claim_id():
    assert CLAIM.claim_id == claim_id_of("syn-n0009", "synthetic", 4021, CLAIM.quote)
    assert CLAIM.claim_id != claim_id_of("syn-n0001", "synthetic", 4021, CLAIM.quote + " ")
    assert CLAIM.claim_id.startswith("syn-c")
    assert "claim_id is not" in refusal(Claim, changed(CLAIM, claim_id="syn-c000000000000"))


def test_a_claim_names_its_page_by_the_receipt_of_the_bytes_fetched():
    assert (CLAIM.page, CLAIM.raw_sha256) == (PAGE.file_id, PAGE.sha256)
    assert "page is not the receipt" in refusal(Claim, changed(CLAIM, raw_sha256=SHA))


def test_the_place_a_claim_gives_spans_its_quote():
    assert "do not span the quote" in refusal(Claim, changed(CLAIM, end=CLAIM.end + 1))


def test_a_model_is_recorded_as_how_a_claim_was_found_exactly_when_one_chose():
    found = changed(CLAIM.derived)
    by_code = found | {"method": "first_sentence"}
    unnamed = found | {"provider": None}
    alone = found | {"second_provider": "another-made-up-provider"}
    for derived in (by_code, unnamed, alone):
        assert "derived" in refusal(Claim, changed(CLAIM, derived=derived))
    none = by_code | {"provider": None, "model": None, "prompt_version": None}
    assert Claim.model_validate(changed(CLAIM, derived=none)).derived.model is None
    # How a claim was found is never where it came from.
    assert CLAIM.source_id not in (CLAIM.derived.provider, CLAIM.derived.model)


def test_a_review_is_signed_by_a_role_and_never_by_a_name():
    assert "reviewer" in refusal(
        Claim, changed(CLAIM, review=changed(CLAIM.review, reviewer=CANARY))
    )
    unsigned = {"status": "accepted"}
    pending = {"status": "pending"}
    rejected = changed(CLAIM.review, status="rejected")
    assert "review" in refusal(Claim, changed(CLAIM, review=unsigned))
    assert "review" in refusal(Claim, changed(CLAIM, review=rejected))
    assert "review" in refusal(Claim, changed(CLAIM, review=rejected | {"reason": "Not so."}))
    kept = Claim.model_validate(changed(CLAIM, review=rejected | {"reason": "about_residents"}))
    assert not kept.accepted and CLAIM.accepted
    assert not Claim.model_validate(changed(CLAIM, review=pending)).accepted


def test_a_thing_is_named_exactly_when_a_claim_is_about_one_and_stands_in_the_quote():
    assert "thing" in refusal(Claim, changed(CLAIM, thing="Alderwick"))
    assert "thing" in refusal(Claim, changed(CLAIM, kind="known_for"))
    assert "does not stand in the quote" in refusal(
        Claim, changed(CLAIM, kind="to_see", thing="Foxholt")
    )
    named = Claim.model_validate(changed(CLAIM, kind="to_see", thing="Alderwick"))
    assert named.thing is not None and named.thing in named.quote


def test_a_made_up_claim_is_made_up_throughout():
    assert "`synthetic` alone" in refusal(Claim, changed(CLAIM, source_id="made-up-survey"))
    assert "both made up" in refusal(Claim, changed(CLAIM, first_release="lon-2026-09-23-01"))
    assert "has no address" in refusal(Claim, changed(CLAIM, url="https://pages.example.org/a"))


def test_a_page_is_not_fetched_before_it_was_written():
    late = changed(CLAIM, source_dated="2026-09-24T00:00:00Z")
    assert "before it was written" in refusal(Claim, late)
