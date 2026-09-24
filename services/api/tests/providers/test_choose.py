"""Which provider reads what is typed, if any. A key alone turns nothing on."""

import logging
from collections.abc import Mapping
from dataclasses import replace

import pytest
from burro_api.logs import LOGGABLE, JsonFormatter
from burro_api.providers.anthropic import AnthropicClient
from burro_api.providers.base import Adapter, over_https
from burro_api.providers.choose import (
    ADAPTERS,
    BY_RULES,
    NOT_USED,
    NOT_USED_BY,
    Choice,
    Refusal,
    by_rules,
    choose,
    told_of,
)
from burro_api.providers.deepseek import DeepSeekClient
from burro_api.providers.gemini import GeminiClient
from burro_api.providers.openai import OpenAIClient
from burro_api.providers.terms import RULES_NOTICE, TERMS, Provider, Question, Read

from .cases import (
    ANSWER,
    CASES,
    CHECKED,
    KEY_TEXT,
    UNCHECKED,
    Case,
    Sender,
    answering,
    as_checked,
    ask,
    fields_of,
    key,
    listening,
    with_each,
)

each = pytest.mark.parametrize("case", CASES, ids=str)


def agreed(case: Case, **changes: str) -> dict[str, str]:
    """The three things that must agree, agreeing."""
    terms = TERMS[case.provider]
    return {
        "BURRO_MODEL_PROVIDER": case.provider.value,
        terms.key_variable: KEY_TEXT,
        "BURRO_MODEL_TERMS_ACCEPTED": case.provider.value,
    } | changes


def chosen(env: Mapping[str, str], **given: object) -> tuple[Choice, list[logging.LogRecord]]:
    with listening() as records:
        choice = choose(env, **given)  # type: ignore[arg-type]
        return choice, list(records)


def assert_one_line_that_names(records: list[logging.LogRecord], provider: Provider | None):
    """One line, whose name is fixed text, and which holds nothing else at all."""
    [record] = records
    assert record.name == "burro_api"
    assert record.msg == (NOT_USED if provider is None else f"model_not_used_{provider.value}")
    assert record.args in ((), None) and fields_of(record) == {}
    assert record.exc_info is None
    line = JsonFormatter().format(record)
    assert set(__import__("json").loads(line)) == {"at", "level", "event"}


def test_with_nothing_set_the_rules_read_and_nothing_is_said():
    choice, records = chosen({})

    assert choice == Choice(client=None, model="", told=BY_RULES, refusal=None) == by_rules()
    assert (choice.told.model_reads, choice.told.provider, choice.told.company) == (
        False,
        None,
        None,
    )
    assert choice.told.notice == RULES_NOTICE
    assert records == []


def test_settings_that_are_not_about_a_model_change_nothing():
    choice, records = chosen({"BURRO_MODEL_ID": "gemini-3.5-flash-lite", "BURRO_PORT": "8000"})

    assert choice == by_rules()
    assert records == []


@each
def test_a_key_alone_turns_nothing_on(case: Case):
    choice, records = chosen({TERMS[case.provider].key_variable: KEY_TEXT}, table=CHECKED)

    assert choice.client is None and choice.told == BY_RULES
    assert choice.refusal is Refusal.NO_PROVIDER
    assert_one_line_that_names(records, None)


@each
def test_a_key_with_no_accepted_terms_gives_no_adapter(case: Case):
    env = agreed(case)
    del env["BURRO_MODEL_TERMS_ACCEPTED"]

    choice, records = chosen(env, table=CHECKED)

    assert choice.client is None and choice.model == "" and choice.told == BY_RULES
    assert choice.refusal is Refusal.TERMS_NOT_ACCEPTED
    assert_one_line_that_names(records, case.provider)


@each
def test_terms_accepted_for_another_provider_give_no_adapter(case: Case):
    for other in Provider:
        if other is not case.provider:
            choice, records = chosen(
                agreed(case, BURRO_MODEL_TERMS_ACCEPTED=other.value), table=CHECKED
            )

            assert choice.client is None and choice.refusal is Refusal.TERMS_NOT_ACCEPTED
            assert_one_line_that_names(records, case.provider)


@pytest.mark.parametrize("accepted", ["yes", "true", "1", "all", "*", "gemini,openai", " "])
def test_terms_are_accepted_by_naming_the_provider_and_in_no_other_way(accepted: str):
    choice, _ = chosen(agreed(CASES[1], BURRO_MODEL_TERMS_ACCEPTED=accepted), table=CHECKED)

    assert choice.client is None and choice.refusal is Refusal.TERMS_NOT_ACCEPTED


@each
def test_a_provider_with_no_key_gives_no_adapter(case: Case):
    env = agreed(case)
    del env[TERMS[case.provider].key_variable]
    # Another provider's key is no key for this one.
    other = next(terms for p, terms in TERMS.items() if p is not case.provider)
    env[other.key_variable] = KEY_TEXT

    choice, records = chosen(env, table=CHECKED)

    assert choice.client is None and choice.refusal is Refusal.NO_KEY
    assert_one_line_that_names(records, case.provider)


@each
@pytest.mark.parametrize(
    "held", ["two words", "line\nbreak", "tab\there", "café", "k" * 513, "a\r\nx-injected: 1"]
)
def test_a_key_that_could_not_go_in_a_header_gives_no_adapter(case: Case, held: str):
    choice, records = chosen(
        agreed(case, **{TERMS[case.provider].key_variable: held}), table=CHECKED
    )

    assert choice.client is None and choice.refusal is Refusal.UNFIT_KEY
    assert_one_line_that_names(records, case.provider)


@pytest.mark.parametrize(
    "named", ["claude", "google", "oai", "chatgpt", "gemini-3.5-flash-lite", "none", "rules", "*"]
)
def test_a_provider_that_is_not_one_of_the_four_gives_no_adapter(named: str):
    env = agreed(CASES[0], BURRO_MODEL_PROVIDER=named, BURRO_MODEL_TERMS_ACCEPTED=named)

    choice, records = chosen(env, table=CHECKED)

    assert choice.client is None and choice.refusal is Refusal.UNKNOWN_PROVIDER
    # What was set is not repeated. It could be anything, a key among them.
    assert_one_line_that_names(records, None)


def test_no_provider_is_chosen_for_whoever_names_none():
    # Not even the one the documents put first. There is no default in code.
    env = {terms.key_variable: KEY_TEXT for terms in TERMS.values()}
    env["BURRO_MODEL_TERMS_ACCEPTED"] = "gemini"

    choice, records = chosen(env, table=CHECKED)

    assert choice.client is None and choice.refusal is Refusal.NO_PROVIDER
    assert_one_line_that_names(records, None)


@each
def test_when_all_agree_the_adapter_is_the_providers_and_people_are_told_so(case: Case):
    send = answering(case.whole(ANSWER))

    choice, records = chosen(agreed(case), table=CHECKED, send=send)

    assert type(choice.client) is case.client and choice.refusal is None
    assert choice.model == case.model == TERMS[case.provider].model
    told = choice.told
    assert (told.model_reads, told.provider) == (True, case.provider.value)
    assert told.company == TERMS[case.provider].company
    assert told.notice == TERMS[case.provider].notice
    # One source for each sentence of the provider's, in the order of the questions.
    assert [source.question for source in told.sources] == [q.value for q in Question]
    assert [source.says for source in told.sources] == [
        TERMS[case.provider].says(question) for question in Question
    ]
    assert all(source.says in told.notice for source in told.sources)
    assert [source.answered for source in told.sources] == [
        answer.answered for answer in TERMS[case.provider].answers
    ]
    assert all(source.addresses and source.read_on == "2026-09-23" for source in told.sources)
    assert all(source.checked_on == "2026-09-23" for source in told.sources)
    assert records == []
    # Choosing makes no call. The adapter it gives makes one when it is asked.
    assert send.requests == []
    assert isinstance(choice.client, Adapter)
    assert ask(choice.client, case, model=choice.model).output == ANSWER
    assert send.requests[0].key.for_header() == KEY_TEXT


def test_the_adapters_are_the_four_and_each_is_its_providers():
    assert dict(ADAPTERS) == {
        Provider.GEMINI: GeminiClient,
        Provider.OPENAI: OpenAIClient,
        Provider.DEEPSEEK: DeepSeekClient,
        Provider.ANTHROPIC: AnthropicClient,
    }


def test_an_adapter_sends_by_the_one_function_that_sends_unless_a_test_gives_another():
    choice, _ = chosen(agreed(CASES[1]), table=CHECKED)

    assert vars(choice.client)["_send"] is over_https


@each
@pytest.mark.parametrize("question", Question, ids=lambda question: question.value)
def test_a_provider_with_one_sentence_that_nobody_has_checked_is_not_turned_on(
    case: Case, question: Question
):
    terms = CHECKED[case.provider]
    but_one = tuple(
        replace(answer, checked_by="", checked_on=None) if answer.question is question else answer
        for answer in terms.answers
    )
    table = dict(CHECKED) | {case.provider: replace(terms, answers=but_one)}

    choice, records = chosen(agreed(case), table=table)

    assert choice.client is None and choice.told == BY_RULES
    assert choice.refusal is Refusal.TERMS_NOT_CHECKED
    assert_one_line_that_names(records, case.provider)


@pytest.mark.parametrize("read", Read)
def test_all_four_are_held_to_the_same_whatever_tool_their_pages_came_back_through(read: Read):
    # The rule, with tables that are made up. Whether a provider is turned
    # on rests on a person's own look at its pages, and on nothing else.
    reached = {provider: with_each(terms, read=read) for provider, terms in UNCHECKED.items()}
    looked_at = {provider: as_checked(terms) for provider, terms in reached.items()}

    held = {str(case): chosen(agreed(case), table=reached)[0].refusal for case in CASES}
    let_through = {str(case): chosen(agreed(case), table=looked_at)[0].refusal for case in CASES}

    assert held == dict.fromkeys(("gemini", "openai", "deepseek", "anthropic"), "terms_not_checked")
    assert let_through == dict.fromkeys(("gemini", "openai", "deepseek", "anthropic"))


@each
def test_the_model_is_the_one_that_is_set_if_its_request_was_read(case: Case):
    choice, _ = chosen(agreed(case, BURRO_MODEL_ID=f" {case.other} "), table=CHECKED)

    assert choice.client is not None and choice.model == case.other
    assert {case.model, case.other} == ADAPTERS[case.provider].FITS


@each
def test_a_model_that_would_refuse_every_call_is_refused_when_the_service_starts(case: Case):
    # Each is a model of the provider's own, which its documents say does
    # not take the request as the adapter sends it, or which is gone. Were
    # it let through, every sentence would be sent to it and refused.
    assert case.refuses
    for model in case.refuses:
        send = answering(case.whole(ANSWER))

        choice, records = chosen(agreed(case, BURRO_MODEL_ID=model), table=CHECKED, send=send)

        assert choice.client is None and choice.told == BY_RULES, model
        assert choice.refusal is Refusal.UNFIT_MODEL, model
        assert not ADAPTERS[case.provider].takes(model), model
        assert_one_line_that_names(records, case.provider)
        assert send.requests == []


@each
@pytest.mark.parametrize(
    "model",
    ["latest", "model/../x", "model?key=x", "Model", "m" * 65, "x-latest", KEY_TEXT, "sk-0123abcd"],
)
def test_a_model_name_that_is_not_allowed_gives_no_adapter(case: Case, model: str):
    choice, records = chosen(agreed(case, BURRO_MODEL_ID=model), table=CHECKED)

    assert choice.client is None and choice.model == ""
    assert choice.refusal is Refusal.UNFIT_MODEL
    assert_one_line_that_names(records, case.provider)


@each
def test_a_model_of_another_provider_gives_no_adapter(case: Case):
    # What happens when the provider is changed and the model is not.
    for other in CASES:
        if other is not case:
            choice, _ = chosen(agreed(case, BURRO_MODEL_ID=other.model), table=CHECKED)

            assert choice.client is None and choice.refusal is Refusal.UNFIT_MODEL


@each
def test_a_name_is_read_whatever_its_case_and_the_space_around_it(case: Case):
    env = agreed(
        case,
        BURRO_MODEL_PROVIDER=f"  {case.provider.value.upper()} ",
        BURRO_MODEL_TERMS_ACCEPTED=f"{case.provider.value.title()}\n",
        **{TERMS[case.provider].key_variable: f" {KEY_TEXT}\n"},
    )

    choice, _ = chosen(env, table=CHECKED)

    assert type(choice.client) is case.client


def test_what_is_chosen_shows_nothing_of_the_key():
    choice, _ = chosen(agreed(CASES[1]), table=CHECKED)

    assert choice.client is not None
    assert "client" not in repr(choice)
    assert repr(choice.client) == "OpenAIClient()"


def test_the_line_is_written_through_the_list_of_what_may_be_logged():
    # The list has no field for a provider, so the name of the event holds
    # it. Every name is fixed text, made of a name in code.
    assert "provider" not in LOGGABLE
    assert NOT_USED == "model_not_used"
    assert {p.value: name for p, name in NOT_USED_BY.items()} == {
        "gemini": "model_not_used_gemini",
        "openai": "model_not_used_openai",
        "deepseek": "model_not_used_deepseek",
        "anthropic": "model_not_used_anthropic",
    }


def test_whoever_is_given_the_warning_is_given_the_provider_and_why_and_nothing_else():
    warned: list[tuple[Provider | None, Refusal]] = []
    env = agreed(CASES[0])
    del env["GEMINI_API_KEY"]

    with listening() as records:
        choose(env, table=CHECKED, warn=lambda provider, why: warned.append((provider, why)))
        choose(agreed(CASES[0]), table=UNCHECKED, warn=lambda p, why: warned.append((p, why)))
        choose({"OPENAI_API_KEY": KEY_TEXT}, warn=lambda p, why: warned.append((p, why)))
        # And is not called at all when a model is turned on, or nothing is set.
        choose(agreed(CASES[0]), table=CHECKED, warn=lambda p, why: warned.append((p, why)))
        choose({}, warn=lambda p, why: warned.append((p, why)))

    assert warned == [
        (Provider.GEMINI, Refusal.NO_KEY),
        (Provider.GEMINI, Refusal.TERMS_NOT_CHECKED),
        (None, Refusal.NO_PROVIDER),
    ]
    assert records == []


def test_why_is_a_fixed_word_and_is_not_in_the_line_that_is_written():
    # The list of what may be logged has no field for it. Until it has, the
    # reason is returned and handed to whoever warns, and the line names the
    # provider alone. Each reason is a word of ours, never a thing that was set.
    assert [refusal.value for refusal in Refusal] == [
        "no_provider",
        "unknown_provider",
        "no_key",
        "unfit_key",
        "terms_not_accepted",
        "terms_not_checked",
        "unfit_model",
    ]
    assert not {"reason", "refusal", "provider"} & LOGGABLE

    _, records = chosen(agreed(CASES[0]), table=UNCHECKED)

    assert_one_line_that_names(records, Provider.GEMINI)
    assert "terms_not_checked" not in JsonFormatter().format(records[0])


@each
def test_a_choice_cannot_hold_a_model_and_tell_people_that_none_reads(case: Case):
    client = case.made(answering(case.whole(ANSWER)))
    told = told_of(TERMS[case.provider])

    assert Choice(client, case.model, told).told.model_reads
    with pytest.raises(ValueError, match="does not fit who reads"):
        Choice(client, case.model, BY_RULES)
    with pytest.raises(ValueError, match="does not fit who reads"):
        Choice(None, "", told)
    with pytest.raises(ValueError, match="does not fit who reads"):
        Choice(client, "", told)
    with pytest.raises(ValueError, match="does not fit who reads"):
        Choice(None, case.model, BY_RULES)
    with pytest.raises(ValueError, match="was refused"):
        Choice(client, case.model, told, Refusal.NO_KEY)


@each
def test_a_choice_cannot_tell_people_of_one_provider_while_another_reads(case: Case):
    client = case.made(answering(case.whole(ANSWER)))

    for other in Provider:
        if other is not case.provider:
            with pytest.raises(ValueError, match="one provider while another reads"):
                Choice(client, case.model, told_of(TERMS[other]))
    with pytest.raises(ValueError, match="one provider while another reads"):
        Choice(client, case.model, replace(told_of(TERMS[case.provider]), provider=None))


def test_what_people_are_told_has_no_default():
    # A default would be "not sent to a language model", said of a model.
    with pytest.raises(TypeError):
        Choice()  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        Choice(client=AnthropicClient(key()), model="claude-haiku-4-5-20251001")  # type: ignore[call-arg]
    assert by_rules().told is BY_RULES and by_rules(Refusal.NO_KEY).refusal is Refusal.NO_KEY


def test_choosing_never_raises_whatever_is_set():
    hostile: list[dict[str, str]] = [
        {"BURRO_MODEL_PROVIDER": "\x00"},
        {"BURRO_MODEL_PROVIDER": "gemini", "GEMINI_API_KEY": "\x00"},
        {"BURRO_MODEL_PROVIDER": "gemini" * 10_000},
        {"BURRO_MODEL_TERMS_ACCEPTED": "gemini"},
        {"BURRO_MODEL_PROVIDER": "openai", "OPENAI_API_KEY": "k", "BURRO_MODEL_ID": "\udcff"},
    ]
    for env in hostile:
        choice, records = chosen(env, table=CHECKED, send=Sender(RuntimeError()))

        assert choice.client is None and choice.told == BY_RULES
        assert len(records) == 1
