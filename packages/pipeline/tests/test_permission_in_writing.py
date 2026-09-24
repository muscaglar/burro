"""Sources whose only ground for use is a written reply that the founder alone has read.

Three owners publish no licence that allows reuse. The founder reports that each gave
permission in writing. Nobody else has read the replies. So each source is registered
under bespoke terms, stays gated, and says what would settle it. Each has a dated note
of what the founder reported. Nothing here reads a reply: none is in the repository.
"""

import re
from datetime import date
from functools import cache
from pathlib import Path

import pytest
from burro_pipeline.registry import Registry, RegistryError, Source, Use, check, load

REPOSITORY = Path(__file__).parents[3]
REGISTRY = REPOSITORY / "registry" / "sources"
EVIDENCE = REPOSITORY / "registry" / "evidence"


@cache
def of_the_repository() -> Registry:
    """The repository's own registry, read once for all the tests here. It is frozen."""
    return load(REGISTRY)


REPORTED_ON = "2026-09-23"
# A reply speaks as "we" to "you". A note speaks of the owner and of Burro, and never so.
AS_A_REPLY_SPEAKS = re.compile(r"\b(?:I|we|us|our|ours|you|your|yours)\b", re.IGNORECASE)
# A file of saved evidence, as registry/README.md asks: <source-id>-<yyyy-mm-dd>.<ext>
NAMED = re.compile(r"(?P<source>[a-z0-9]+(?:-[a-z0-9]+)*)-(?P<day>\d{4}-\d{2}-\d{2})\.[a-z0-9]+")

# Each source, the heading it sits under, and the uses the founder asked the owner for.
BY_PERMISSION: dict[str, tuple[str, set[Use]]] = {
    "parkrun-events": ("places", {Use.SCORING, Use.DISPLAY}),
    "gla-tree-canopy-cover-2024": ("environment", {Use.SCORING}),
    "gla-green-cover-2024": ("environment", {Use.SCORING}),
    "arts-council-england-libraries-basic-dataset": ("culture", {Use.SCORING}),
    "arts-council-england-accredited-museums": ("culture", {Use.SCORING}),
    "arts-council-england-national-portfolio": ("culture", {Use.SCORING}),
}

# No permission is reported for these two. They stay as they were.
NO_PERMISSION_REPORTED = ["gla-laei-2022", "gla-planning-london-datahub"]


@pytest.mark.parametrize("source_id", BY_PERMISSION)
def test_a_source_used_by_permission_is_registered_for_what_was_asked(source_id: str):
    source = of_the_repository().get(source_id)
    dimension, asked = BY_PERMISSION[source_id]
    assert source.dimension == dimension
    assert source.licence == "Bespoke-terms"
    assert set(source.uses) == asked


@pytest.mark.parametrize("source_id", BY_PERMISSION)
def test_a_reply_only_the_founder_has_read_approves_nothing(source_id: str):
    source = of_the_repository().get(source_id)
    assert source.status == "gated"
    assert source.verified_how == "secondary_source"
    assert source.attribution_verified is False


@pytest.mark.parametrize("use", list(Use))
@pytest.mark.parametrize("source_id", BY_PERMISSION)
def test_the_gate_refuses_a_source_used_by_permission_for_every_use(source_id: str, use: Use):
    with pytest.raises(RegistryError, match="not approved"):
        of_the_repository().require(source_id, use)


@pytest.mark.parametrize("source_id", BY_PERMISSION)
def test_a_source_used_by_permission_cannot_be_approved_by_changing_its_status_alone(
    source_id: str,
):
    entry = of_the_repository().get(source_id)
    approved = Source.model_validate(entry.model_dump() | {"status": "approved"})
    rules = {problem.rule for problem in check([approved], date.today())}
    assert "approved_is_proven" in rules


@pytest.mark.parametrize("source_id", BY_PERMISSION)
def test_the_entry_says_whose_report_it_rests_on_and_what_would_settle_it(source_id: str):
    source = of_the_repository().get(source_id)
    assert "only the founder has read" in source.status_reason
    assert "What would settle it: the founder files a dated note of the reply" in (
        source.status_reason
    )
    assert f"registry/evidence/{source_id}-{REPORTED_ON}.md" in source.notes


@pytest.mark.parametrize("source_id", BY_PERMISSION)
def test_the_conditions_say_what_the_permission_covers(source_id: str):
    conditions = of_the_repository().get(source_id).conditions
    first, *rest = conditions
    assert first.startswith("Permission in writing, as the founder reports.")
    assert REPORTED_ON in first
    said = " ".join(rest)
    assert "covers what was asked and no more" in said
    assert "A change of use means asking" in said
    assert "Credit " in said
    # A credit is Burro's wording until the owner publishes its own. None is taken from a reply.
    assert "from the reply" not in said
    assert "until the owner publishes its own" in said


@pytest.mark.parametrize("source_id", BY_PERMISSION)
def test_an_entry_says_that_a_page_was_not_read_and_not_what_a_site_answered(source_id: str):
    """What a site answers to a program may be said by whatever stands between the two.
    So an entry says what is known: that nobody has read the page."""
    source = of_the_repository().get(source_id)
    said = " ".join([source.status_reason, source.notes, *source.conditions]).casefold()
    for words in ("refused every", "answered it with", "http 40", "returned 40"):
        assert words not in said


@pytest.mark.parametrize("source_id", NO_PERMISSION_REPORTED)
def test_a_source_with_no_permission_reported_stays_held(source_id: str):
    source = of_the_repository().get(source_id)
    assert (source.status, source.licence, source.uses) == ("held", "None-stated", ())
    assert "A written reply from the GLA settles it." in source.status_reason


# The notes of what the founder reported


def note(source_id: str) -> str:
    """A note as one line, so that where a line breaks changes nothing."""
    path = EVIDENCE / f"{source_id}-{REPORTED_ON}.md"
    return " ".join(path.read_text(encoding="utf-8").split())


def test_every_file_of_saved_evidence_is_named_for_a_source_and_a_day():
    registry = of_the_repository()
    saved = [path for path in sorted(EVIDENCE.iterdir()) if path.name != "README.md"]
    assert saved
    for path in saved:
        named = NAMED.fullmatch(path.name)
        assert named is not None, path.name
        assert registry.get(named["source"]).id == named["source"]
        assert date.fromisoformat(named["day"]) <= date.today()


@pytest.mark.parametrize("source_id", BY_PERMISSION)
def test_a_note_says_what_was_reported_and_whose_report_it_is(source_id: str):
    text = note(source_id)
    for said in (
        f"`{source_id}`",
        "What Burro asked to do",
        "It gave permission, in writing, as the founder reports",
        f"{REPORTED_ON}, as the founder reports",
        "The founder holds the reply",
        "Nobody else has read it",
        "covers what was asked, and no more",
        "A change of use means asking",
        "What would settle it",
    ):
        assert said in text, said


@pytest.mark.parametrize("source_id", BY_PERMISSION)
def test_a_note_does_not_pass_for_the_reply(source_id: str):
    text = note(source_id)
    assert "It is not the reply" in text
    assert "whoever wrote it has not read the reply" in text
    # What nobody told the writer is said to be missing, and is not filled in.
    assert text.count("Not recorded") >= 2


@pytest.mark.parametrize("source_id", BY_PERMISSION)
def test_a_note_prints_no_words_of_a_reply(source_id: str):
    """The words of a reply stay with the reply. A note says that the founder reports a
    permission and holds the reply, and quotes nothing."""
    path = EVIDENCE / f"{source_id}-{REPORTED_ON}.md"
    lines = path.read_text(encoding="utf-8").splitlines()
    assert [line for line in lines if line.lstrip().startswith(">")] == []
    text = note(source_id)
    assert not re.search(r"[\"\u201c\u201d]", text)
    assert AS_A_REPLY_SPEAKS.findall(text) == []
    assert "The words of the reply are not printed here" in text
    assert "It quotes nothing of the reply" in text
    assert "no more of the reply than" not in text


@pytest.mark.parametrize("source_id", BY_PERMISSION)
def test_a_note_holds_no_address_and_nothing_a_letter_opens_or_closes_with(source_id: str):
    text = note(source_id)
    assert "@" not in text
    assert not re.search(r"\b(?:Dear|Regards|Sincerely|Mr|Mrs|Ms|Dr)\b", text)
    # A postcode, and a telephone number.
    assert not re.search(r"\b[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}\b", text)
    assert not re.search(r"(?:\+44|\b0)[0-9][0-9 ]{8,}", text)
