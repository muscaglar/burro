"""Which provider reads what is typed, if any. A key alone turns nothing on."""

import json
import logging
from collections.abc import Mapping
from dataclasses import fields, replace

import pytest
from burro_api.logs import LOGGABLE, JsonFormatter
from burro_api.providers.anthropic import AnthropicClient
from burro_api.providers.base import Adapter, over_https
from burro_api.providers.choose import (
    ADAPTERS,
    BY_RULES,
    NOT_USED,
    Choice,
    Refusal,
    by_rules,
    choose,
    told_of,
)
from burro_api.providers.deepseek import DeepSeekClient
from burro_api.providers.gemini import GeminiClient
from burro_api.providers.openai import OpenAIClient
from burro_api.providers.terms import (
    RULES_NOTICE,
    SETTINGS,
    TERMS,
    WORDS_ALONE,
    Provider,
    Question,
    Read,
)

from .cases import (
    ANSWER,
    CASES,
    KEY_TEXT,
    KEYED,
    Case,
    Sender,
    all_of,
    answering,
    ask,
    fields_of,
    key,
    listening,
    with_each,
)

each = pytest.mark.parametrize("case", CASES, ids=str)
# The providers that may read what real people type, and the one that never may.
FOR_PEOPLE = tuple(case for case in CASES if case.provider is not Provider.DEEPSEEK)
[DEEPSEEK] = [case for case in CASES if case.provider is Provider.DEEPSEEK]
for_people = pytest.mark.parametrize("case", FOR_PEOPLE, ids=str)


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


def assert_one_line_that_names(
    records: list[logging.LogRecord], provider: Provider | None, why: Refusal | None = None
):
    """One warning: which provider is not used, and why. Both are words of ours, and no more."""
    [record] = records
    assert record.name == "burro_api"
    assert (record.msg, record.levelno) == (NOT_USED, logging.WARNING)
    fields = fields_of(record)
    assert record.args in ((), None) and record.exc_info is None
    assert set(fields) == ({"reason"} if provider is None else {"reason", "provider"})
    assert fields.get("provider") == (None if provider is None else provider.value)
    assert fields["reason"] in {refusal.value for refusal in Refusal}
    assert why is None or fields["reason"] == why.value
    line = json.loads(JsonFormatter().format(record))
    assert set(line) == {"at", "level", "event", *fields} and line["level"] == "warning"
    # Nothing that was set is in it, whatever was set.
    assert KEYED not in JsonFormatter().format(record) and KEYED not in all_of(record)


def test_with_nothing_set_the_rules_read_and_nothing_is_said():
    choice, records = chosen({})

    assert choice == Choice(client=None, model="", told=BY_RULES, refusal=None) == by_rules()
    assert (choice.told.model_reads, choice.told.provider, choice.told.company) == (
        False,
        None,
        None,
    )
    # No company is told of, so there are no terms of a company's to link to.
    assert (choice.told.notice, choice.told.terms_url) == (RULES_NOTICE, None)
    assert records == []


def test_settings_that_are_not_about_a_model_change_nothing():
    choice, records = chosen({"BURRO_MODEL_ID": "gemini-3.5-flash-lite", "BURRO_PORT": "8000"})

    assert choice == by_rules()
    assert records == []


@each
def test_a_key_alone_turns_nothing_on(case: Case):
    choice, records = chosen({TERMS[case.provider].key_variable: KEY_TEXT})

    assert choice.client is None and choice.told == BY_RULES
    assert choice.refusal is Refusal.NO_PROVIDER
    assert_one_line_that_names(records, None, Refusal.NO_PROVIDER)


@each
def test_a_key_with_no_accepted_terms_gives_no_adapter(case: Case):
    env = agreed(case)
    del env["BURRO_MODEL_TERMS_ACCEPTED"]

    choice, records = chosen(env)

    assert choice.client is None and choice.model == "" and choice.told == BY_RULES
    assert choice.refusal is Refusal.TERMS_NOT_ACCEPTED
    assert_one_line_that_names(records, case.provider, Refusal.TERMS_NOT_ACCEPTED)


@each
def test_terms_accepted_for_another_provider_give_no_adapter(case: Case):
    for other in Provider:
        if other is not case.provider:
            choice, records = chosen(agreed(case, BURRO_MODEL_TERMS_ACCEPTED=other.value))

            assert choice.client is None and choice.refusal is Refusal.TERMS_NOT_ACCEPTED
            assert_one_line_that_names(records, case.provider, Refusal.TERMS_NOT_ACCEPTED)


@pytest.mark.parametrize("accepted", ["yes", "true", "1", "all", "*", "gemini,openai", " "])
def test_terms_are_accepted_by_naming_the_provider_and_in_no_other_way(accepted: str):
    choice, _ = chosen(agreed(CASES[1], BURRO_MODEL_TERMS_ACCEPTED=accepted))

    assert choice.client is None and choice.refusal is Refusal.TERMS_NOT_ACCEPTED


@each
def test_a_provider_with_no_key_gives_no_adapter(case: Case):
    env = agreed(case)
    del env[TERMS[case.provider].key_variable]
    # Another provider's key is no key for this one.
    other = next(terms for p, terms in TERMS.items() if p is not case.provider)
    env[other.key_variable] = KEY_TEXT

    choice, records = chosen(env)

    assert choice.client is None and choice.refusal is Refusal.NO_KEY
    assert_one_line_that_names(records, case.provider, Refusal.NO_KEY)


@each
@pytest.mark.parametrize("held", ["", "   ", "\n"])
def test_a_key_that_is_empty_is_no_key(case: Case, held: str):
    choice, records = chosen(agreed(case, **{TERMS[case.provider].key_variable: held}))

    assert choice.client is None and choice.told == BY_RULES
    assert_one_line_that_names(records, case.provider, Refusal.NO_KEY)


@each
@pytest.mark.parametrize(
    "held", ["two words", "line\nbreak", "tab\there", "café", "k" * 513, "a\r\nx-injected: 1"]
)
def test_a_key_that_could_not_go_in_a_header_gives_no_adapter(case: Case, held: str):
    choice, records = chosen(agreed(case, **{TERMS[case.provider].key_variable: held}))

    assert choice.client is None and choice.refusal is Refusal.UNFIT_KEY
    assert_one_line_that_names(records, case.provider, Refusal.UNFIT_KEY)


@pytest.mark.parametrize(
    "named", ["claude", "google", "oai", "chatgpt", "gemini-3.5-flash-lite", "none", "rules", "*"]
)
def test_a_provider_that_is_not_one_of_the_four_gives_no_adapter(named: str):
    env = agreed(CASES[0], BURRO_MODEL_PROVIDER=named, BURRO_MODEL_TERMS_ACCEPTED=named)

    choice, records = chosen(env)

    assert choice.client is None and choice.refusal is Refusal.UNKNOWN_PROVIDER
    # What was set is not repeated. It could be anything, a key among them.
    assert_one_line_that_names(records, None, Refusal.UNKNOWN_PROVIDER)


def test_no_provider_is_chosen_for_whoever_names_none():
    # Not even the one the documents put first. There is no default in code.
    env = {terms.key_variable: KEY_TEXT for terms in TERMS.values()}
    env["BURRO_MODEL_TERMS_ACCEPTED"] = "gemini"

    choice, records = chosen(env)

    assert choice.client is None and choice.refusal is Refusal.NO_PROVIDER
    assert_one_line_that_names(records, None, Refusal.NO_PROVIDER)


@for_people
def test_when_all_agree_the_adapter_is_the_providers_and_people_are_told_so(case: Case):
    send = answering(case.whole(ANSWER))

    choice, records = chosen(agreed(case), send=send)

    assert type(choice.client) is case.client and choice.refusal is None
    assert choice.model == case.model == TERMS[case.provider].model
    told = choice.told
    assert (told.model_reads, told.provider) == (True, case.provider.value)
    assert told.company == TERMS[case.provider].company
    # Unless it is asked for, nothing of the search goes with the words.
    assert (choice.with_settings, told.settings_sent) == (False, False)
    assert told.notice == TERMS[case.provider].notice(with_settings=False)
    # The link to the company's own terms, and nothing of what the table says they hold.
    assert told.terms_url == TERMS[case.provider].terms_url
    assert {held.name for held in fields(told)} == {
        "model_reads",
        "provider",
        "company",
        "notice",
        "terms_url",
        "settings_sent",
    }
    assert not [
        question for question in Question if TERMS[case.provider].says(question) in repr(told)
    ]
    assert records == []
    # Choosing makes no call. The adapter it gives makes one when it is asked.
    assert send.requests == []
    assert isinstance(choice.client, Adapter)
    assert ask(choice.client, case, model=choice.model).output == ANSWER
    assert send.requests[0].key.for_header() == KEY_TEXT


@for_people
@pytest.mark.parametrize(
    ("set_to", "sent"),
    [
        (None, False),
        ("", False),
        ("no", False),
        ("yes", True),
        (" YES\n", True),
        ("true", False),
        ("1", False),
        ("on", False),
        ("all", False),
        (KEY_TEXT, False),
    ],
)
def test_the_settings_go_with_the_words_only_where_that_is_asked_for_by_the_one_word(
    case: Case, set_to: str | None, sent: bool
):
    env = agreed(case) | ({} if set_to is None else {"BURRO_MODEL_SENDS_SETTINGS": set_to})

    choice, records = chosen(env)

    assert choice.client is not None and records == []
    assert (choice.with_settings, choice.told.settings_sent) == (sent, sent)
    assert choice.told.notice == TERMS[case.provider].notice(with_settings=sent)
    assert (SETTINGS in choice.told.notice, WORDS_ALONE in choice.told.notice) == (sent, not sent)


def test_asking_for_the_settings_to_be_sent_turns_nothing_on():
    choice, records = chosen({"BURRO_MODEL_SENDS_SETTINGS": "yes"})

    assert choice == by_rules() and records == []
    # And where the rules read, nothing is sent, whatever was asked for.
    refused, _ = chosen({"BURRO_MODEL_PROVIDER": "gemini", "BURRO_MODEL_SENDS_SETTINGS": "yes"})
    assert (refused.with_settings, refused.told.settings_sent) == (False, False)


@each
def test_a_choice_cannot_send_the_settings_and_tell_people_that_the_words_go_alone(case: Case):
    client = case.made(answering(case.whole(ANSWER)))
    alone, with_them = (told_of(TERMS[case.provider], sent) for sent in (False, True))

    assert Choice(client, case.model, with_them, with_settings=True).told.settings_sent
    with pytest.raises(ValueError, match="does not fit what is sent"):
        Choice(client, case.model, alone, with_settings=True)
    with pytest.raises(ValueError, match="does not fit what is sent"):
        Choice(client, case.model, with_them, with_settings=False)
    with pytest.raises(ValueError, match="does not fit what is sent"):
        Choice(None, "", BY_RULES, with_settings=True)


def test_the_adapters_are_the_four_and_each_is_its_providers():
    assert dict(ADAPTERS) == {
        Provider.GEMINI: GeminiClient,
        Provider.OPENAI: OpenAIClient,
        Provider.DEEPSEEK: DeepSeekClient,
        Provider.ANTHROPIC: AnthropicClient,
    }


def test_an_adapter_sends_by_the_one_function_that_sends_unless_a_test_gives_another():
    choice, _ = chosen(agreed(CASES[1]))

    assert vars(choice.client)["_send"] is over_https


@for_people
@pytest.mark.parametrize("read", Read)
def test_a_provider_is_turned_on_though_no_person_has_checked_what_its_pages_say(
    case: Case, read: Read
):
    # The table is research, and nothing of it is waited for: not who read a
    # page, and not the tool it came back through.
    reached = {provider: with_each(terms, read=read) for provider, terms in TERMS.items()}
    assert not any(terms.checked for terms in reached.values())

    choice, records = chosen(agreed(case), table=reached)

    assert type(choice.client) is case.client and choice.refusal is None
    assert records == []


@pytest.mark.parametrize("model", sorted(DeepSeekClient.FITS))
@pytest.mark.parametrize("sends_settings", ["", "yes"])
def test_the_one_provider_that_may_not_read_what_people_type_is_never_turned_on(
    model: str, sends_settings: str
):
    # Named, keyed, accepted and fitted, and still not used by the service.
    # Its adapter is for the made-up sentences of the evaluation set.
    send = answering(DEEPSEEK.whole(ANSWER))
    env = agreed(DEEPSEEK, BURRO_MODEL_ID=model, BURRO_MODEL_SENDS_SETTINGS=sends_settings)

    choice, records = chosen(env, send=send)

    assert choice.client is None and choice.model == "" and choice.told == BY_RULES
    assert choice.refusal is Refusal.NOT_FOR_PEOPLE
    assert_one_line_that_names(records, Provider.DEEPSEEK, Refusal.NOT_FOR_PEOPLE)
    assert send.requests == []


def test_no_other_provider_is_held_back_from_what_people_type():
    held = {str(case): chosen(agreed(case))[0].refusal for case in CASES}

    assert held == {"gemini": None, "openai": None, "deepseek": "not_for_people", "anthropic": None}


@for_people
def test_the_model_is_the_one_that_is_set_if_its_request_was_read(case: Case):
    choice, _ = chosen(agreed(case, BURRO_MODEL_ID=f" {case.other} "))

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

        choice, records = chosen(agreed(case, BURRO_MODEL_ID=model), send=send)

        assert choice.client is None and choice.told == BY_RULES, model
        assert choice.refusal is Refusal.UNFIT_MODEL, model
        assert not ADAPTERS[case.provider].takes(model), model
        assert_one_line_that_names(records, case.provider, Refusal.UNFIT_MODEL)
        assert send.requests == []


@each
@pytest.mark.parametrize(
    "model",
    ["latest", "model/../x", "model?key=x", "Model", "m" * 65, "x-latest", KEY_TEXT, "sk-0123abcd"],
)
def test_a_model_name_that_is_not_allowed_gives_no_adapter(case: Case, model: str):
    choice, records = chosen(agreed(case, BURRO_MODEL_ID=model))

    assert choice.client is None and choice.model == ""
    assert choice.refusal is Refusal.UNFIT_MODEL
    assert_one_line_that_names(records, case.provider, Refusal.UNFIT_MODEL)


@each
def test_a_model_of_another_provider_gives_no_adapter(case: Case):
    # What happens when the provider is changed and the model is not.
    for other in CASES:
        if other is not case:
            choice, _ = chosen(agreed(case, BURRO_MODEL_ID=other.model))

            assert choice.client is None and choice.refusal is Refusal.UNFIT_MODEL


@for_people
def test_a_name_is_read_whatever_its_case_and_the_space_around_it(case: Case):
    env = agreed(
        case,
        BURRO_MODEL_PROVIDER=f"  {case.provider.value.upper()} ",
        BURRO_MODEL_TERMS_ACCEPTED=f"{case.provider.value.title()}\n",
        **{TERMS[case.provider].key_variable: f" {KEY_TEXT}\n"},
    )

    choice, _ = chosen(env)

    assert type(choice.client) is case.client


def test_what_is_chosen_shows_nothing_of_the_key():
    choice, _ = chosen(agreed(CASES[1]))

    assert choice.client is not None
    assert "client" not in repr(choice)
    assert repr(choice.client) == "OpenAIClient()"


def test_the_line_is_written_through_the_list_of_what_may_be_logged():
    # One name for the event, whoever is not used. The provider and the
    # reason are fields, and both are on the list of what may be logged.
    assert NOT_USED == "model_not_used"
    assert {"provider", "reason"} <= LOGGABLE
    assert not {"refusal", "key", "accepted", "terms"} & LOGGABLE


def test_whoever_is_given_the_warning_is_given_the_provider_and_why_and_nothing_else():
    warned: list[tuple[Provider | None, Refusal]] = []
    env = agreed(CASES[0])
    del env["GEMINI_API_KEY"]

    with listening() as records:
        choose(env, warn=lambda provider, why: warned.append((provider, why)))
        choose(agreed(DEEPSEEK), warn=lambda p, why: warned.append((p, why)))
        choose({"OPENAI_API_KEY": KEY_TEXT}, warn=lambda p, why: warned.append((p, why)))
        # And is not called at all when a model is turned on, or nothing is set.
        choose(agreed(CASES[0]), warn=lambda p, why: warned.append((p, why)))
        choose({}, warn=lambda p, why: warned.append((p, why)))

    assert warned == [
        (Provider.GEMINI, Refusal.NO_KEY),
        (Provider.DEEPSEEK, Refusal.NOT_FOR_PEOPLE),
        (None, Refusal.NO_PROVIDER),
    ]
    assert records == []


def test_why_is_a_fixed_word_and_never_a_thing_that_was_set():
    # The line says which of the things that must hold does not. Each reason
    # is a word of ours, and so is the provider's name.
    assert [refusal.value for refusal in Refusal] == [
        "no_provider",
        "unknown_provider",
        "no_key",
        "unfit_key",
        "terms_not_accepted",
        "unfit_model",
        "not_for_people",
        "capped_at_nought",
    ]

    _, records = chosen(agreed(DEEPSEEK))

    assert_one_line_that_names(records, Provider.DEEPSEEK, Refusal.NOT_FOR_PEOPLE)


@pytest.mark.parametrize(
    "variable",
    ["BURRO_MODEL_PROVIDER", "BURRO_MODEL_TERMS_ACCEPTED", "BURRO_MODEL_ID", "GEMINI_API_KEY"],
)
def test_a_key_set_where_another_setting_belongs_is_in_no_line(variable: str):
    # A value in the wrong variable could be a key, so no value is ever written.
    env = agreed(CASES[0]) | {variable: KEY_TEXT}

    with listening() as records:
        choose(env)

    written = "\n".join((JsonFormatter().format(r) + all_of(r)) for r in records)
    assert KEYED not in written.casefold()


@each
def test_a_choice_cannot_hold_a_model_and_tell_people_that_none_reads(case: Case):
    client = case.made(answering(case.whole(ANSWER)))
    told = told_of(TERMS[case.provider], with_settings=False)

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
                Choice(client, case.model, told_of(TERMS[other], with_settings=False))
    with pytest.raises(ValueError, match="one provider while another reads"):
        told = told_of(TERMS[case.provider], with_settings=False)
        Choice(client, case.model, replace(told, provider=None))


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
        choice, records = chosen(env, send=Sender(RuntimeError()))

        assert choice.client is None and choice.told == BY_RULES
        assert len(records) == 1
