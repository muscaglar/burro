"""The reader as the evaluation set asks for it, and a sentence all the way through each adapter.

These need the reader, and the reader needs the engine. They are skipped, and
say so, while the engine cannot be loaded.
"""

import json
from collections.abc import Callable
from typing import Any

import pytest
from burro_api.providers.base import Request, Response
from burro_api.providers.measure import reader
from burro_api.providers.terms import SENT_WITH, SETTINGS, TERMS, WORDS_ALONE

from .cases import CASES, KEY_TEXT, KEYED, SPEC, Case, Sender, listening

each = pytest.mark.parametrize("case", CASES, ids=str)

# Not plain, so that the rules leave words unread and a model is asked.
TEXT = "Honestly, 30 minutes to Cindermoor Works"
KEYS = {
    "gemini": "GEMINI_API_KEY",
    "openai": "OPENAI_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}


@pytest.fixture(scope="module")
def engine() -> Any:
    """What the reader is made of, or a skip that says why there is none."""
    try:
        import burro_api.reader as found_reader
        from burro_api.loading import load_release
        from burro_api.settings import SYNTHETIC_FIXTURE
        from burro_core import default_spec
        from burro_core.ids import InterpretStatus, Tenure
        from burro_core.interpret import InterpretRequest, RuleInterpreter
        from burro_core.reducer import apply

        release = load_release(SYNTHETIC_FIXTURE)
    except Exception:
        pytest.skip("the reader cannot be loaded: the engine under it is being rebuilt")

    class Engine:
        reader = found_reader
        suggest = InterpretStatus.SUGGEST

        @staticmethod
        def asked(text: str) -> Any:
            return InterpretRequest(text, default_spec(Tenure.RENT), release)

        @staticmethod
        def asked_with_a_search(text: str) -> Any:
            """As a person asks who has searched before: a budget, a journey, tags and areas."""
            spec = default_spec(Tenure.RENT)
            first, second = [area.name for area in release.neighbourhoods][:2]
            for said in (
                "my budget is 1700 a month",
                "30 minutes to Cindermoor Works by bike",
                f"not in {first}",
                f"only in {second}",
                "somewhere quiet and leafy",
            ):
                read = RuleInterpreter().interpret(InterpretRequest(said, spec, release))
                spec = apply(spec, read.operations, release).spec
            return InterpretRequest(text, spec, release)

        @staticmethod
        def by_rules(text: str) -> Any:
            return RuleInterpreter().interpret(Engine.asked(text))

    return Engine


def named(case: Case, **changes: str) -> dict[str, str]:
    return {"BURRO_MODEL_PROVIDER": str(case), KEYS[str(case)]: KEY_TEXT} | changes


def journey(engine: Any) -> str:
    """What a model that read the sentence well would answer, in the reader's own schema."""
    names: list[str] = list(engine.reader.SCHEMA["properties"])
    empty: dict[str, Any] = {name: [] for name in names}
    edit = {
        "action": "add",
        "destination_text": "Cindermoor Works",
        "position": 0,
        "mode": "unchanged",
        "max_minutes": 30,
        "strictness": "unchanged",
        "step": "none",
        "provenance": "stated",
        "words": TEXT,
    }
    return json.dumps(empty | {"status": "ok", "commute_ops": [edit]})


def answering_with(case: Case, text: Callable[[], str]) -> Sender:
    return Sender(lambda request: Response(200, json.dumps(case.whole(text())).encode()))


@each
def test_a_sentence_goes_all_the_way_through_the_adapter_and_back(case: Case, engine: Any):
    send = answering_with(case, lambda: journey(engine))
    made = reader(named(case), send)

    result = made.interpret(engine.asked(TEXT))

    [request] = send.requests
    sent = json.loads(request.body)
    # The reader's own instructions and the person's words, where the provider looks for them.
    assert case.system_in(sent).startswith(engine.reader.SYSTEM)
    assert json.loads(case.user_in(sent))["request"] == TEXT
    assert (request.host, request.path) == (case.host, case.path)
    assert request.key.for_header() == KEY_TEXT
    # And the answer is held to the guard, as it is whoever gave it: nothing
    # of it is applied, and what it read is offered as Burro's guess.
    assert result.status is engine.suggest and not result.degraded
    assert result.operations == engine.by_rules(TEXT).operations
    assert result.operations.count == 0
    [offer] = result.suggestions
    guessed = [way for way in offer.choices if getattr(way, "guess", False)]
    assert [edit.max_minutes for way in guessed for edit in way.operations.commute_ops] == [30]
    assert (offer.spans[0].start, offer.spans[0].end) == (0, len(TEXT))
    counts = (result.usage.input_tokens, result.usage.output_tokens, result.usage.cache_read_tokens)
    assert counts == case.counts


@each
def test_the_readers_schema_is_sent_whole_to_each_provider(case: Case, engine: Any):
    from burro_api.providers.base import inlined

    send = answering_with(case, lambda: journey(engine))

    reader(named(case), send).interpret(engine.asked(TEXT))

    sent = json.loads(send.requests[0].body)
    schema = case.schema_in(sent)
    if schema is None:
        assert json.dumps(inlined(engine.reader.SCHEMA)) in case.system_in(sent)
    else:
        assert schema == inlined(engine.reader.SCHEMA)


@each
@pytest.mark.parametrize(
    "text",
    ["", "not json", '{"status": "ok"}', '{"status": "maybe", "budget_ops": []}', "[]"],
    ids=range(5),
)
def test_an_answer_that_does_not_fit_the_schema_is_refused_whoever_gave_it(
    case: Case, engine: Any, text: str
):
    # One provider does not enforce the schema, and none promises the
    # values. What follows every adapter is what holds the answer to it.
    made = reader(named(case), answering_with(case, lambda: text))

    with pytest.raises(Exception) as refused:
        made.interpret(engine.asked(TEXT))

    assert type(refused.value).__name__ == "ModelError"
    assert str(refused.value) == "" and refused.value.args == ()


@each
def test_every_field_that_leaves_with_the_words_is_one_people_are_told_of(case: Case, engine: Any):
    # Where the settings are sent, what leaves is the words and the search as
    # it stands. The notice must name every part of the search that is sent,
    # whoever receives it. A field that is added to a search fails here until
    # the notice tells of it.
    send = answering_with(case, lambda: journey(engine))
    env = named(case, BURRO_MODEL_SENDS_SETTINGS="yes")

    reader(env, send).interpret(engine.asked_with_a_search(TEXT))

    sent_whole = json.loads(send.requests[0].body)
    turn = json.loads(case.user_in(sent_whole))
    assert sorted(turn) == ["request", "spec"]
    assert case.system_in(sent_whole).startswith(engine.reader.SYSTEM_WITH_SETTINGS)
    sent = turn["spec"]
    # The search that is sent is a whole one: what a person can pay, and
    # where they will and will not live.
    assert sent["budget"]["amount"] == 1700
    assert {rule["rule"] for rule in sent["areas"]} == {"exclude", "only"}
    assert sent["commutes"] and sent["tags"] and sent["weights"]
    assert set(sent) == set(SENT_WITH)
    notice = TERMS[case.provider].notice(with_settings=True)
    for name in sent:
        told = SENT_WITH[name]
        assert told is None or (told in SETTINGS and told in notice), name
    # The one thing that is taken out is where a journey leads.
    assert not any("place_id" in journey or "place" in journey for journey in sent["commutes"])
    # And the stand-in the other tests send is made of the same fields.
    assert set(SPEC) <= set(sent)


@each
@pytest.mark.parametrize("set_to", [None, "no", "true"], ids=["unset", "no", "not the word"])
def test_unless_it_is_asked_for_nothing_of_the_search_leaves_with_the_words(
    case: Case, engine: Any, set_to: str | None
):
    # The words go alone, and the notice says so. Nothing of what the person
    # can pay, where they travel to, or where they will not live is sent.
    send = answering_with(case, lambda: journey(engine))
    env = named(case, **({} if set_to is None else {"BURRO_MODEL_SENDS_SETTINGS": set_to}))
    asked = engine.asked_with_a_search(TEXT)

    reader(env, send).interpret(asked)

    [request] = send.requests
    sent_whole = json.loads(request.body)
    assert json.loads(case.user_in(sent_whole)) == {"request": TEXT}
    assert case.system_in(sent_whole).startswith(engine.reader.SYSTEM)
    assert "`spec`" not in case.system_in(sent_whole)
    body = request.body.decode()
    held = json.loads(asked.spec.model_dump_json())
    # The instructions hold a figure or two of their own, as examples. The
    # person's turn holds their words and no figure of their search.
    assert held["budget"]["amount"] == 1700 and "1700" not in case.user_in(sent_whole)
    for area in held["areas"]:
        assert area["area_id"] not in body
    for commute in held["commutes"]:
        assert commute["place_id"] not in body
    assert "syn-" not in body
    notice = TERMS[case.provider].notice(with_settings=False)
    assert WORDS_ALONE in notice and SETTINGS not in notice


@each
def test_the_model_and_the_limits_are_those_of_the_environment(case: Case, engine: Any):
    other = case.other
    seen: list[float] = []

    def send(request: Request, timeout_s: float) -> Response:
        seen.append(timeout_s)
        sent = json.loads(request.body)
        assert case.limit_in(sent) == 1024
        assert other in request.path or sent.get("model") == other
        return Response(200, json.dumps(case.whole(journey(engine))).encode())

    env = named(
        case, BURRO_MODEL_ID=other, BURRO_MODEL_TIMEOUT_S="30", BURRO_MODEL_MAX_TOKENS="1024"
    )
    reader(env, send).interpret(engine.asked(TEXT))

    assert seen == [30.0]


@pytest.mark.parametrize(
    ("env", "says"),
    [
        ({}, "BURRO_MODEL_PROVIDER must name one of: gemini, openai, deepseek, anthropic"),
        ({"BURRO_MODEL_PROVIDER": KEY_TEXT}, "BURRO_MODEL_PROVIDER must name one of"),
        ({"BURRO_MODEL_PROVIDER": "gemini"}, "GEMINI_API_KEY holds no key"),
        (
            {"BURRO_MODEL_PROVIDER": "gemini", "OPENAI_API_KEY": KEY_TEXT},
            "GEMINI_API_KEY holds no key",
        ),
        (
            {"BURRO_MODEL_PROVIDER": "openai", "OPENAI_API_KEY": f"{KEY_TEXT} {KEY_TEXT}"},
            "OPENAI_API_KEY holds no key",
        ),
        (
            {
                "BURRO_MODEL_PROVIDER": "openai",
                "OPENAI_API_KEY": KEY_TEXT,
                "BURRO_MODEL_ID": KEY_TEXT,
            },
            "BURRO_MODEL_ID is not a model this provider's adapter was fitted to",
        ),
        (
            {
                "BURRO_MODEL_PROVIDER": "openai",
                "OPENAI_API_KEY": KEY_TEXT,
                "BURRO_MODEL_ID": "gpt-6-astra",
            },
            "BURRO_MODEL_ID is not a model this provider's adapter was fitted to",
        ),
        (
            {
                "BURRO_MODEL_PROVIDER": "openai",
                "OPENAI_API_KEY": KEY_TEXT,
                "BURRO_MODEL_TIMEOUT_S": KEY_TEXT,
            },
            "BURRO_MODEL_TIMEOUT_S is not a number",
        ),
        (
            {
                "BURRO_MODEL_PROVIDER": "openai",
                "OPENAI_API_KEY": KEY_TEXT,
                "BURRO_MODEL_MAX_TOKENS": "0",
            },
            "BURRO_MODEL_MAX_TOKENS is not more than nought",
        ),
    ],
    ids=range(9),
)
def test_it_says_what_is_missing_and_never_what_was_set(env: dict[str, str], says: str):
    with listening() as records, pytest.raises(SystemExit) as stopped:
        reader(env, Sender(RuntimeError()))

    said = str(stopped.value)
    assert said.startswith(says)
    assert KEYED not in said
    assert stopped.value.__cause__ is None and stopped.value.__context__ is None
    assert records == []


@each
def test_it_asks_nothing_of_the_terms_because_no_person_typed_the_sentences(
    case: Case, engine: Any
):
    # One provider never reads what real people type, and the others read it
    # only once their terms are accepted. Each can be measured all the same.
    made = reader(named(case), answering_with(case, lambda: journey(engine)))

    assert made.interpret(engine.asked(TEXT)).status is engine.suggest


@each
def test_a_model_is_measured_only_if_the_service_could_ask_it(case: Case):
    for model in case.refuses:
        send = Sender(RuntimeError())

        with pytest.raises(SystemExit, match="was fitted to"):
            reader(named(case, BURRO_MODEL_ID=model), send)

        assert send.requests == []
