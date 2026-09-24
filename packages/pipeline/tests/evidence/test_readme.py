"""The README of the evidence folder says what the code does, and a test holds it to that."""

import json
import re
from pathlib import Path

from burro_core.explain import render
from burro_core.facts import facts_for
from burro_pipeline import evidence as package
from burro_pipeline.evidence import lock as lock_module
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.served import MEANING

from .examples import METHOD, RECEIPT, ROW
from .support import evidence, release

README = Path(package.__file__).parent / "README.md"
TEXT = README.read_text(encoding="utf-8")
PARK = "syn-n0001/feature/park_proximity"


def test_the_readme_prints_the_examples_as_they_are():
    printed = [json.loads(block) for block in re.findall(r"```json\n(.*?)```", TEXT, re.DOTALL)]
    assert printed == [record.model_dump(mode="json") for record in (RECEIPT, METHOD, ROW)]
    assert "`CLAIM` in `packages/pipeline/tests/evidence/examples.py`" in TEXT


def test_the_readme_traces_a_figure_the_release_holds_to_the_files_behind_it():
    fact = next(f for f in facts_for(release(), "syn-n0001", None) if f.fact_id == PARK)
    assert f'"{render(fact).text}"' in TEXT
    assert f"cites the source `{fact.sources[0].source_id}` as of {fact.as_of}" in TEXT
    row = evidence().row(PARK)
    assert row is not None and row.derivation_id is not None
    assert f"state `{row.state}`, {row.units_used} of {row.units_expected} units" in TEXT
    assert row.weight_covered == 1 and f"retrieved on {row.retrieved_on}" in TEXT
    method = evidence().method(row.derivation_id)
    assert method is not None and f'`{method.derivation_id}`: "{method.sentence}"' in TEXT
    files = [evidence().receipt(file_id) for file_id in row.inputs]
    for file in files:
        assert file is not None
        assert f"`{file.file_id}`" in TEXT and f"`{file.publisher_file}`" in TEXT
    last = files[-1]
    assert last is not None and f"`{last.vault_key()}`" in TEXT


def test_the_readme_names_every_state_every_refusal_and_every_finding():
    for state in State:
        assert f"| `{state}` |" in TEXT
    sealing = set(lock_module.MEANING) - {"input_is_locked", "receipt_is_valid", "lock_is_valid"}
    for rule in (*sealing, *MEANING):
        assert f"| `{rule}` |" in TEXT, rule


def test_every_link_in_the_readme_leads_to_a_file():
    links = re.findall(r"\]\(([^)#]+)\)", TEXT)
    assert len(links) == 3
    for link in links:
        assert (README.parent / link).resolve().is_file(), link


def test_the_readme_is_plain():
    assert "!" not in TEXT
    assert all(ord(sign) < 128 for sign in TEXT)
