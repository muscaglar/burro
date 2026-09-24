"""The design document says what is built, and what the service does today.

`docs/design/models.md` is what the founder reads before a key is handed
over. So what it says of the service is held to the service, and what it
says of the adapters is held to the adapters. Nothing here changes a file,
and nothing calls a provider.
"""

from pathlib import Path
from typing import Any

import pytest
from burro_api.providers.base import PATIENCE, REST_S, STUCK
from burro_api.providers.choose import ADAPTERS, Refusal
from burro_api.providers.terms import (
    ADVICE,
    FORMS,
    RULES_NOTICE,
    SETTINGS,
    TERMS,
    Provider,
    Question,
)

from .cases import CASES, Case

each = pytest.mark.parametrize("case", CASES, ids=str)

ROOT = Path(__file__).resolve().parents[4]
DESIGN = (ROOT / "docs" / "design" / "models.md").read_text(encoding="utf-8")
SERVICE = ROOT / "services" / "api" / "src" / "burro_api"
# What the document says, in bold, for as long as it is true.
WARNING = "**Today `ANTHROPIC_API_KEY` alone turns the model on."
UNTIL = "until step 5 of section 8 is done.**"
MADE_UP = "made-up-and-opens-nothing"
KEYS = {terms.key_variable for terms in TERMS.values()}


def section(number: int) -> str:
    """One numbered section of the document, from its heading to the next."""
    [_, rest] = DESIGN.split(f"\n## {number}. ", 1)
    return rest.split("\n## ", 1)[0]


def asks_the_chooser() -> bool:
    """Whether the service, as its source stands, lets `choose` decide who reads."""
    app = (SERVICE / "app.py").read_text(encoding="utf-8")
    return "providers.choose" in app or "providers import choose" in app


def reads_with(monkeypatch: pytest.MonkeyPatch, env: dict[str, str]) -> str:
    """The name of what the service would read with, given `env` and nothing else."""
    try:
        from burro_api import app
        from burro_api.settings import Settings
    except ImportError:
        pytest.skip("the service cannot be loaded: it is being rebuilt")
    for name in (*KEYS, "BURRO_MODEL_PROVIDER", "BURRO_MODEL_TERMS_ACCEPTED", "BURRO_MODEL_ID"):
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    chosen: Any = getattr(app, "_interpreter", None)
    if chosen is None:
        pytest.skip("the service no longer chooses its reader where it did")
    return type(chosen(Settings.from_env(env))).__name__


@pytest.mark.xfail(
    strict=True,
    reason="until the chooser is wired in, one provider's key alone turns the model on: "
    "docs/design/models.md, section 8, step 5",
)
def test_in_the_service_as_it_stands_a_key_alone_turns_nothing_on(
    monkeypatch: pytest.MonkeyPatch,
):
    # When this passes, the service asks the chooser. Take the mark off, and
    # take the three warnings out of the design document.
    for variable in sorted(KEYS):
        assert reads_with(monkeypatch, {variable: MADE_UP}) == "RuleInterpreter", variable


def test_the_design_warns_in_bold_for_as_long_as_a_key_alone_turns_the_model_on():
    warned = DESIGN.count(WARNING)

    if asks_the_chooser():
        assert warned == 0
        return
    # At the head, where the settings are, and where a key is handed over.
    head = DESIGN.split("\n## 1. ", 1)[0]
    for part in (head, section(2), section(5)):
        assert WARNING in part
        assert "Do not" in part.split(WARNING, 1)[1].split("**", 1)[0]
    assert DESIGN.count(UNTIL) == 3 == warned
    # And the step that ends it says to do it before any key is handed over.
    assert "**Do step 5 before any key reaches" in section(8)
    assert section(5).index(WARNING) < section(5).index("store of secrets")


@each
def test_the_design_names_the_models_each_adapter_was_fitted_to(case: Case):
    fitted = section(1).split("### The models each adapter was fitted to", 1)[1]

    for model in ADAPTERS[case.provider].FITS:
        assert f"`{model}`" in fitted, model
    # And at least the one its documents are plainest about refusing.
    assert f"`{case.refuses[0]}`" in fitted
    assert f"`{TERMS[case.provider].model}`" in section(3)


def test_the_design_names_every_reason_a_model_is_not_used_and_no_other():
    import re

    named = set(re.findall(r"`([a-z_]+)`", section(2).split("| # | What must hold", 1)[1]))

    assert {refusal.value for refusal in Refusal} <= named
    assert "terms_not_read_at_source" not in DESIGN


def test_the_design_says_how_long_a_provider_is_left_alone_as_the_code_has_it():
    assert (
        f"After {PATIENCE} answers in a row of 400, 401, 403 or 404, the provider is asked "
        f"nothing for {REST_S:.0f} seconds"
    ) in section(1)
    assert sorted(STUCK) == [400, 401, 403, 404]
    assert f"{REST_S:.0f} seconds, after {PATIENCE} in a row" in section(10)


def test_the_design_holds_the_forms_of_words_as_they_are_built():
    told = section(6)

    for question in Question:
        assert f"| `{question.value}` | {FORMS[question].said} | {FORMS[question].unsaid} |" in told
    assert f"> {SETTINGS}" in told
    assert RULES_NOTICE in told


def test_the_design_holds_every_answer_as_it_is_built():
    answers = section(6).split("### The answers", 1)[1].split("###", 1)[0]

    for question in Question:
        cells: list[str] = []
        for terms in TERMS.values():
            given = terms.answer(question).answer
            if given is None:
                cells.append("Does not say")
            else:
                cells.append(given[:1].upper() + given[1:] if given else "It may")
        assert f"| `{question.value}` | {' | '.join(cells)} |" in answers, question
    assert "| Question | Google | OpenAI | DeepSeek | Anthropic |" in answers


def test_the_notice_the_design_shows_is_the_one_that_is_built():
    gemini = TERMS[Provider.GEMINI]

    assert f"> {gemini.notice}\n" in section(6)
    assert gemini.notice.endswith(ADVICE)
    assert "sends your words to" not in DESIGN


@pytest.mark.parametrize("terms", TERMS.values(), ids=lambda terms: terms.provider.value)
def test_the_design_says_who_has_been_checked_as_the_table_has_it(terms: Any):
    # Whoever checks a provider's sentences changes the table and this row together.
    [row] = [line for line in section(3).splitlines() if line.startswith("| Checked by a person")]
    cells = [cell.strip() for cell in row.strip("|").split("|")][1:]

    said = dict(zip(Provider, cells, strict=True))[terms.provider]

    assert said == ("Yes" if terms.checked else "No")


def test_the_design_says_at_its_head_whether_any_provider_can_be_turned_on():
    none = "| Which can be turned on today | None. "

    assert (none in DESIGN) is not any(terms.checked for terms in TERMS.values())


def test_the_design_says_what_is_left_to_the_first_real_call():
    left = section(9)

    assert DESIGN.count("\n## 9. To confirm with the first real call\n") == 1
    for provider in ("All four", "Gemini", "OpenAI", "DeepSeek", "Claude"):
        assert f"| {provider} | " in left, provider
    # The two forms of Google's field for a schema, of which one is sent.
    assert "generationConfig.responseJsonSchema" in left
    assert "generationConfig.responseFormat.text.schema" in left
    # Every question is a question.
    rows = [line for line in left.splitlines() if line[:3].strip("| ").isdigit()]
    assert len(rows) >= 16 and all("?" in row for row in rows)


def test_the_design_holds_no_path_and_no_key():
    unwanted = ("/Users/", "/home/", "/private/", "localhost", "sk-", "AIza")

    assert not [word for word in unwanted if word in DESIGN]
    assert "!" not in DESIGN.replace("!=", "")
