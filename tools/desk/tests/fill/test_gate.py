"""The licence gate of the desk: rule 1 of AGENTS.md, held for every file a queue shows."""

import sys
from pathlib import Path

import pytest
from desk.fill import gate

REGISTRY = Path(__file__).resolve().parents[4] / "registry" / "sources"

ENTRY = """
[[source]]
id = "{id}"
name = "A made-up file"
publisher = "A made-up publisher"
url = "https://example.org/"
dimension = "{dimension}"
licence = "OGL-3.0"
commercial_use = "yes"
share_alike = false
attribution = "Made up for a test."
attribution_verified = true
status = "{status}"
status_reason = "{reason}"
uses = [{uses}]
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = ["https://example.org/licence"]
"""


def registry(folder: Path) -> Path:
    """A registry of three made-up entries: one for the gazetteer, one not, and one gated."""
    entries = (
        ("made-up-roads", "geography", "approved", "", '"gazetteer", "scoring"'),
        ("made-up-parks", "environment", "approved", "", '"scoring", "display"'),
        ("made-up-names", "geography", "gated", "Its licence has not been read.", '"gazetteer"'),
    )
    text = "schema_version = 1\n" + "".join(
        ENTRY.format(id=name, dimension=dimension, status=status, reason=reason, uses=uses)
        for name, dimension, status, reason, uses in entries
    )
    path = folder / "registry.toml"
    path.write_text(text, encoding="utf-8")
    return path


def test_the_made_up_city_asks_nobody_and_names_made_up_sources_alone(tmp_path: Path):
    nowhere = tmp_path / "no-registry"
    gate.ask(["synthetic", "synthetic-names"], gate.GAZETTEER, synthetic=True, registry=nowhere)
    with pytest.raises(gate.Refused, match="not made up"):
        gate.ask(["synthetic", "os-open-names"], gate.GAZETTEER, synthetic=True)


def test_a_real_draft_may_not_name_a_made_up_source(tmp_path: Path):
    with pytest.raises(gate.Refused, match="made-up source"):
        gate.ask(["made-up-roads", "synthetic"], gate.GAZETTEER, synthetic=False)


def test_a_source_is_allowed_for_a_use_the_registry_gives_it(tmp_path: Path):
    gate.ask(["made-up-roads"], gate.GAZETTEER, synthetic=False, registry=registry(tmp_path))


def test_a_source_is_refused_for_a_use_the_registry_does_not_give_it(tmp_path: Path):
    with pytest.raises(gate.Refused, match=r"made-up-parks.* is not registered for gazetteer"):
        gate.ask(
            ["made-up-roads", "made-up-parks"],
            gate.GAZETTEER,
            synthetic=False,
            registry=registry(tmp_path),
        )


def test_a_gated_source_is_refused_with_its_reason(tmp_path: Path):
    with pytest.raises(gate.Refused, match="Its licence has not been read"):
        gate.ask(["made-up-names"], gate.GAZETTEER, synthetic=False, registry=registry(tmp_path))


def test_a_source_the_registry_does_not_hold_is_refused(tmp_path: Path):
    with pytest.raises(gate.Refused, match="not in the licence registry"):
        gate.ask(["nobody-knows"], gate.SCORING, synthetic=False, registry=registry(tmp_path))


def test_one_run_says_everything_that_is_refused(tmp_path: Path):
    with pytest.raises(gate.Refused) as refusal:
        gate.ask(
            ["made-up-names", "made-up-parks"],
            gate.GAZETTEER,
            synthetic=False,
            registry=registry(tmp_path),
        )
    assert "made-up-names" in str(refusal.value) and "made-up-parks" in str(refusal.value)


def test_a_real_draft_is_refused_where_the_pipeline_is_not_installed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    # `make desk` runs before `make setup`. A real file is then refused, in words that
    # say what to run, and the made-up city is still filled.
    monkeypatch.setitem(sys.modules, "burro_pipeline.registry", None)
    with pytest.raises(gate.Refused, match="Run make setup, then fill the queues again"):
        gate.ask(["made-up-roads"], gate.GAZETTEER, synthetic=False, registry=registry(tmp_path))
    gate.ask(["synthetic"], gate.GAZETTEER, synthetic=True)


def test_a_row_that_names_no_source_is_refused():
    with pytest.raises(gate.Refused, match="names no source"):
        gate.ask(["synthetic", ""], gate.SCORING, synthetic=True)


def test_the_desk_asks_for_no_use_but_its_own(tmp_path: Path):
    with pytest.raises(gate.Refused, match="not for audit_only"):
        gate.ask(["made-up-roads"], "audit_only", synthetic=False, registry=registry(tmp_path))


def test_every_source_the_design_draws_behind_a_border_is_registered_for_it():
    # docs/design/desk.md, section 6. If the registry takes the use from one of these,
    # the desk can no longer draw it, and this says so before a person finds out.
    drawn = (
        "ons-output-areas-2021",
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
        "os-boundary-line",
        "gla-town-centre-boundaries",
        "os-open-roads",
        "os-open-names",
    )
    gate.ask(drawn, gate.GAZETTEER, synthetic=False, registry=REGISTRY)


@pytest.mark.parametrize("source_id", ["dft-naptan", "os-open-greenspace", "os-open-rivers"])
def test_stations_parks_and_rivers_are_not_drawn_until_the_registry_says_so(source_id: str):
    with pytest.raises(gate.Refused, match="not registered for gazetteer"):
        gate.ask([source_id], gate.GAZETTEER, synthetic=False, registry=REGISTRY)


# A source in words


def test_a_source_is_said_by_who_publishes_it_and_what_it_is_called():
    # Two ids may be two files of one publisher. An id alone does not say so.
    said = {
        source: gate.in_words(source, synthetic=False, registry=REGISTRY)
        for source in ("os-open-names", "os-boundary-line", "gla-town-centre-boundaries")
    }
    assert said == {
        "os-open-names": "Ordnance Survey, OS Open Names",
        "os-boundary-line": "Ordnance Survey, OS Boundary-Line",
        "gla-town-centre-boundaries": "Greater London Authority, Town Centre Boundaries",
    }


def test_a_made_up_source_is_said_to_be_made_up(tmp_path: Path):
    nowhere = tmp_path / "no-registry"
    assert gate.in_words("synthetic", synthetic=True, registry=nowhere) == "Made up"
    assert (
        gate.in_words("synthetic-names", synthetic=True, registry=nowhere)
        == "Made-up publisher of names"
    )


def test_a_source_the_registry_does_not_hold_is_said_by_its_id(tmp_path: Path):
    assert gate.in_words("made-up-canals", synthetic=False, registry=registry(tmp_path)) == (
        "made-up-canals"
    )
    assert gate.in_words("made-up-roads", synthetic=False, registry=registry(tmp_path)) == (
        "A made-up publisher, A made-up file"
    )
