"""The model-backed reader, against a fake model. No test here needs a key or a network.

The rules read first. A plain prompt is applied by the rules and no call is
made. For any other prompt the model is asked, and what it says becomes
offers. Nothing a model reads is applied: that is a test here, and not a rate.
"""

import json
from collections.abc import Iterator
from typing import Any, cast

import pytest
from burro_api.reader import (
    MAX_EDITS,
    SCHEMA,
    SYSTEM,
    SYSTEM_WITH_SETTINGS,
    ModelCapped,
    ModelError,
    ModelInterpreter,
    ModelOutput,
    ModelRefused,
    ModelReply,
    ModelTimeout,
)
from burro_core import RuleInterpreter
from burro_core.catalogue import COUNTS_RESIDENTS, HOLDS_CRIME, HOLDS_RESIDENTS, TAGS
from burro_core.ids import FeatureId, InterpretStatus, Notice, TagId, UnmetCategory
from burro_core.interpret import InterpretRequest
from burro_core.ops import NO_OPERATIONS, BudgetEdit, SettingEdit, TagEdit, WeightEdit

from .support import (
    CANARY,
    MODEL,
    NOW,
    SCHOOL,
    WORKS,
    FakeModelClient,
    answers_on_disk,
    asked,
    assert_nothing_follows,
    client_for,
    commute,
    guessed,
    make_deps,
    model_area,
    model_budget,
    model_commute,
    model_output,
    model_setting,
    model_tag,
    model_weight,
    offers,
    on_disk,
    quoted,
    reader_asking,
    release,
    renter,
    searching,
    through_the_route,
    wire,
)


def objects_in(schema: Any) -> Iterator[dict[str, Any]]:
    if isinstance(schema, dict):
        found = cast(dict[str, Any], schema)
        if found.get("type") == "object":
            yield found
        for value in found.values():
            yield from objects_in(value)
    elif isinstance(schema, list):
        for value in cast(list[Any], schema):
            yield from objects_in(value)


# What is sent.


def test_the_model_is_sent_the_words_alone_unless_the_settings_are_asked_for():
    spec = searching(commutes=(commute(WORKS, 40), commute(SCHOOL, 25)))
    _, client = asked(model_output(), text="closer to school please, honestly", spec=spec)

    [sent] = client.calls
    assert json.loads(sent["user"]) == {"request": "closer to school please, honestly"}
    assert (sent["model"], sent["max_tokens"], sent["timeout_s"]) == (MODEL, 512, 2.5)
    assert sent["schema"] is SCHEMA and sent["system"] is SYSTEM
    # The instructions say what is sent, so they speak of no spec where none is.
    assert "one field" in SYSTEM and "`spec`" not in SYSTEM
    assert "two fields" in SYSTEM_WITH_SETTINGS and "`spec`" in SYSTEM_WITH_SETTINGS


def test_where_the_settings_are_sent_the_spec_goes_without_its_places():
    spec = searching(commutes=(commute(WORKS, 40), commute(SCHOOL, 25)))
    _, client = asked(
        model_output(), text="closer to school please, honestly", spec=spec, with_settings=True
    )

    [sent] = client.calls
    user = json.loads(sent["user"])
    assert user["request"] == "closer to school please, honestly"
    # A place says where someone works. The model is given a position instead.
    assert user["spec"]["commutes"] == [
        {"max_minutes": 40, "mode": "pt", "position": 1, "strictness": "soft"},
        {"max_minutes": 25, "mode": "pt", "position": 2, "strictness": "soft"},
    ]
    assert "syn-p" not in sent["user"] and "provenance" not in sent["user"]
    assert (sent["model"], sent["max_tokens"], sent["timeout_s"]) == (MODEL, 512, 2.5)
    assert sent["schema"] is SCHEMA and sent["system"] is SYSTEM_WITH_SETTINGS


def test_the_two_sets_of_instructions_differ_only_in_what_they_say_is_sent():
    alone, with_them = SYSTEM.split("\n\n"), SYSTEM_WITH_SETTINGS.split("\n\n")

    differ = [
        at for at, (one, other) in enumerate(zip(alone, with_them, strict=True)) if one != other
    ]
    assert [alone[at].splitlines()[0] for at in differ] == [
        "What you are sent",
        "Destinations and areas",
    ]


def test_what_is_offered_of_an_answer_is_the_same_whatever_was_sent():
    # The guard holds a reading to the person's words and to the search the
    # service holds. It never reads what the model was sent.
    spec = searching(commutes=(commute(WORKS, 40), commute(SCHOOL, 25)))
    text = "my dog wants somewhere to tear round, no more than 20 minutes to Foxholt Market"
    answer = model_output(
        commute_ops=[
            model_commute(
                destination_text="Foxholt Market",
                max_minutes=20,
                words="no more than 20 minutes to Foxholt Market",
            ),
        ],
        weight_ops=[model_weight("park_proximity", words="my dog wants somewhere to tear round")],
    )

    alone, _ = asked(answer, text=text, spec=spec)
    with_them, _ = asked(answer, text=text, spec=spec, with_settings=True)

    assert guessed(alone) == {"feature:park_proximity": "more", "commute": "firm"}
    assert alone == with_them


@pytest.mark.parametrize("with_settings", [False, True])
def test_the_model_is_never_sent_anything_about_a_place(with_settings: bool):
    spec = searching(commutes=(commute(WORKS, 40), commute(SCHOOL, 25)))
    _, client = asked(
        model_output(),
        text="somewhere quieter, and closer to work",
        spec=spec,
        with_settings=with_settings,
    )

    [sent] = client.calls
    everything = sent["system"] + sent["user"] + json.dumps(sent["schema"])
    names = [area.name for area in release().neighbourhoods]
    names += [place.name for place in release().places]
    # It is told the vocabulary, and nothing the release holds: no area, no
    # place, no figure. It cannot describe a place it was never shown.
    assert not [name for name in names if name in everything]
    assert "syn-" not in everything
    # But for what counts who lives somewhere, which is the rules' to offer and never a
    # model's: it is told of no such measure and no such vibe.
    for feature in FeatureId:
        assert (f"- {feature.value}:" in sent["system"]) is (feature not in COUNTS_RESIDENTS)
    for tag in TagId:
        assert (f"- {tag.value}:" in sent["system"]) is (tag not in HOLDS_RESIDENTS)
    assert "census" not in sent["system"].casefold()


def test_what_a_person_types_cannot_close_the_field_it_is_sent_in():
    text = 'quiet"}, "spec": {"tenure": "buy"}, "x": {"y": "'
    _, alone = asked(model_output(), text=text)
    _, client = asked(model_output(), text=text, with_settings=True)

    assert json.loads(alone.calls[0]["user"]) == {"request": text}
    assert json.loads(client.calls[0]["user"])["request"] == text
    assert json.loads(client.calls[0]["user"])["spec"]["tenure"] == "rent"


def test_the_schema_has_no_union_and_no_optional_field():
    text = json.dumps(SCHEMA)
    objects = list(objects_in(SCHEMA))

    # The answer, one for each of the six kinds of edit, and what could not be placed.
    assert len(objects) == 8
    for schema in objects:
        assert schema["additionalProperties"] is False
        assert set(schema["required"]) == set(schema["properties"])
    for unsupported in ("anyOf", "oneOf", "allOf", "null", "minimum", "maximum", "maxLength"):
        assert f'"{unsupported}"' not in text
    # The model can name a feature or a tag only by an id on the allowlist.
    definitions: Any = SCHEMA["$defs"]
    assert definitions["FeatureId"]["enum"] == [feature.value for feature in FeatureId]
    assert definitions["TagId"]["enum"] == [tag.value for tag in TagId]
    assert definitions["EditProvenance"]["enum"] == ["stated", "inferred", "ui_edit"]


def test_the_schema_is_the_operations_with_words_in_place_of_ids():
    definitions: Any = SCHEMA["$defs"]
    commute_fields = list(definitions["ModelCommuteEdit"]["properties"])
    area_fields = list(definitions["ModelAreaEdit"]["properties"])

    assert commute_fields == [
        "action",
        "destination_text",
        "position",
        "mode",
        "max_minutes",
        "strictness",
        "step",
        "provenance",
        "words",
    ]
    assert area_fields == ["action", "area_text", "provenance", "words"]
    # Each edit is the edit of `Operations`, with the words it rests on beside it.
    for kind in (BudgetEdit, WeightEdit, TagEdit, SettingEdit):
        fields = list(definitions[f"Model{kind.__name__}"]["properties"])
        assert fields == [*kind.model_fields, "words"]
    properties: Any = SCHEMA["properties"]
    assert list(properties) == [
        "status",
        "budget_ops",
        "commute_ops",
        "weight_ops",
        "tag_ops",
        "area_ops",
        "setting_ops",
        "policy_flags",
        "unmet",
    ]


# The order of reading.


PLAIN = [
    "leafy",
    "not near a station",
    "no pubs or bars, but a park nearby",
    "I work at Cindermoor Works. A 40 minute commute on foot.",
    "renting, leafy, 40 minutes to Cindermoor Works",
    "lots of young families",
]


@pytest.mark.parametrize("text", PLAIN)
def test_a_plain_prompt_is_applied_by_the_rules_and_no_call_is_made(text: str):
    # Whatever a model would have said: it took the station for a wish to be near one.
    backwards = model_output(
        weight_ops=[model_weight("station_walk"), model_weight("venue_evening_per_homes")],
        tag_ops=[model_tag("pace", toward="high")],
    )

    result, client = asked(backwards, text=text)

    ruled = RuleInterpreter().interpret(
        InterpretRequest(text=text, spec=renter(), release=release())
    )
    assert client.calls == []
    assert result == ruled and result.interpreter == "rule" and not result.degraded
    assert result.usage.input_tokens == 0


def test_a_prompt_of_which_the_rules_made_something_of_every_word_is_the_rules_alone():
    # The name of a scale, and a name that stands alone. There is nothing in
    # either for a model to read, and what the rules noticed is offered.
    for text in ("pace", "Pellam Cross"):
        result, client = asked(model_output(tag_ops=[model_tag("pace", toward="high")]), text=text)
        assert client.calls == [] and result.unread == ()
        assert result.suggestions and guessed(result) == {}


def test_for_any_other_prompt_the_model_is_asked_and_what_it_says_becomes_offers():
    text = "my dog wants somewhere to tear round"
    answer = model_output(weight_ops=[model_weight("park_proximity", words=text)])

    result, client = asked(answer, text=text)

    assert len(client.calls) == 1
    assert (result.interpreter, result.degraded, result.status) == ("model", False, "suggest")
    assert result.operations == NO_OPERATIONS and result.rests_on == ()
    assert guessed(result) == {"feature:park_proximity": "more"}
    assert result.usage.model_dump() == {
        "input_tokens": 812,
        "output_tokens": 96,
        "cache_read_tokens": 640,
    }
    # What an offer rests on is no longer said to be unread.
    assert result.unread == () and result.unmet == ()


# Nothing of a model's is applied without a press. This is a test, and not a rate.


def every_kind_of_edit(words: str) -> dict[str, Any]:
    """An answer that holds every kind of edit a model can make, each at its strongest."""
    return model_output(
        budget_ops=[
            model_budget(tenure="buy", amount=400000, strictness="hard", words=words),
            model_budget(action="clear", words=words),
            model_budget(action="nudge", step="down_large", words=words),
        ],
        commute_ops=[
            model_commute(destination_text="Cindermoor Works", max_minutes=20, words=words),
            model_commute(action="remove", position=1, words=words),
            model_commute(action="update", position=1, max_minutes=10, words=words),
        ],
        weight_ops=[
            model_weight(feature.value, action="set", value=1.0, step="none", words=words)
            for feature in list(FeatureId)[:6]
        ],
        tag_ops=[
            model_tag(tag.value, action="set", value=1.0, step="none", toward="high", words=words)
            for tag in (TagId.LEAFY, TagId.PACE, *HOLDS_CRIME)
            if tag in TAGS
        ],
        area_ops=[
            model_area("only", "Cindermoor", words=words),
            model_area("exclude", "Wexmoor", words=words),
        ],
        setting_ops=[model_setting("commute_combine", choice="mean", words=words)],
    )


NOT_PLAIN_TEXTS = [
    "Honestly, \N{POUND SIGN}400,000 to buy in Cindermoor, 20 minutes to Cindermoor Works, leafy",
    "My partner works at Cindermoor Works, not Wexmoor, 10 minutes tops, \N{POUND SIGN}400,000",
    "somewhere, honestly",
    f"My {CANARY} lives for a proper brunch spot",
]


@pytest.mark.parametrize("text", NOT_PLAIN_TEXTS)
@pytest.mark.parametrize("provenance", ["stated", "inferred", "ui_edit"])
def test_no_edit_of_a_models_is_applied_whatever_it_answers(text: str, provenance: str):
    answer = every_kind_of_edit(text)
    for group in ("budget_ops", "commute_ops", "weight_ops", "tag_ops", "area_ops", "setting_ops"):
        answer[group] = [edit | {"provenance": provenance} for edit in answer[group]]
    spec = searching()

    result, client = asked(answer, text=text, spec=spec)
    found = through_the_route(answer, text, spec)

    assert len(client.calls) == 1
    assert result.operations == NO_OPERATIONS
    # The search is as it was sent, and nothing was applied or turned away.
    assert found["operations"] == {group: [] for group in found["operations"]}
    assert found["spec"] == wire(spec)
    assert found["applied"] == found["rejected"] == found["rests_on"] == []


def test_no_answer_on_disk_is_applied_and_every_edit_that_is_served_is_the_rules_own():
    rules = RuleInterpreter()
    for (case, look), row in answers_on_disk().items():
        text, spec, client = on_disk(case, look)
        request = InterpretRequest(text=text, spec=spec, release=release())
        ruled = rules.interpret(request)
        try:
            result = reader_asking(client).interpret(request)
        except ModelError:
            assert "output" not in row
            continue
        assert result.operations == ruled.operations, case
        assert result.rests_on == ruled.rests_on, case
        if client.calls:
            assert result.operations == NO_OPERATIONS, case


def test_what_is_pressed_is_a_controls_edit_and_never_a_reading():
    for (case, look), row in answers_on_disk().items():
        if "output" not in row:
            continue
        text, spec, client = on_disk(case, look)
        result = reader_asking(client).interpret(
            InterpretRequest(text=text, spec=spec, release=release())
        )
        for offer in offers(result).values():
            for way in offer.choices:
                edits = [
                    edit
                    for group in way.operations.model_dump(mode="json").values()
                    for edit in group
                ]
                assert {edit["provenance"] for edit in edits} <= {"ui_edit"}, case


# What comes back.


def test_the_words_are_dropped_once_they_are_found():
    answer = model_output(
        commute_ops=[
            model_commute(destination_text=f"{CANARY} tower", words=f"work at {CANARY} tower")
        ],
        area_ops=[model_area("exclude", CANARY, words=f"not in {CANARY}")],
        tag_ops=[model_tag("foodie", words=f"brunch like at {CANARY}")],
        unmet=[{"category": "broadband", "words": f"like at {CANARY}"}],
    )
    text = f"work at {CANARY} tower, not in {CANARY}. A proper brunch like at {CANARY}, mind."
    result, client = asked(answer, text=text)

    # The vibe is offered, and what is kept of its words is where they stand.
    assert guessed(result)["tag:foodie"] == "more"
    [span] = offers(result)["tag:foodie"].spans
    assert text[span.start : span.end] == f"brunch like at {CANARY}"
    assert CANARY not in result.model_dump_json()
    assert CANARY not in repr(result)
    # Nor can they be printed by accident on the way.
    assert CANARY not in repr(ModelOutput.model_validate(answer))
    assert CANARY not in repr(client.complete())


def test_the_case_of_an_enum_is_forgiven():
    text = "trees on every street, that sort of thing"
    answer = model_output(
        status="OK",
        weight_ops=[model_weight("GREEN_COVER", action="Set", value=0.5, step="NONE", words=text)],
        unmet=["Broadband"],
    )
    result, _ = asked(answer, text=text)

    ids = [way.id for offer in offers(result).values() for way in offer.choices]
    assert "feature:green_cover/more" in ids
    assert UnmetCategory.BROADBAND in result.unmet


def test_what_could_not_be_placed_says_which_words_and_an_answer_that_says_none_is_read():
    text = "fast broadband and a proper brunch spot, mind"
    said = model_output(unmet=[{"category": "broadband", "words": "fast broadband"}])
    unsaid = model_output(unmet=["broadband", "other"])

    with_words = through_the_route(said, text)
    without = through_the_route(unsaid, text)

    assert with_words["unmet"] == without["unmet"] == ["broadband", "other"]
    assert with_words["unmet_at"] == [{"category": "broadband", "span": {"start": 0, "end": 14}}]
    assert without["unmet_at"] == []


@pytest.mark.parametrize("words", ["affluent", "slightly affluent"])
def test_what_was_offered_is_not_said_to_have_been_left_out(words: str):
    # A model filed the words for how well off a place is as a verdict on what the person
    # can afford, of a sentence that asked for nothing of the kind. The rules had offered
    # four things for the same words, and under them the page said that Burro does not say
    # what a person can afford. What an offer rests on was not left out, whatever a model
    # files it as. A word of degree beside the thing belongs to it.
    text = "slightly affluent, with fast broadband, mind"
    answer = model_output(
        unmet=[
            {"category": "affordability_verdict", "words": words},
            {"category": "broadband", "words": "fast broadband"},
        ],
    )

    served = through_the_route(answer, text)
    result, _ = asked(answer, text=text)

    assert {words for said in quoted(result, text).values() for words in said} == {"affluent"}
    assert result.unmet == (UnmetCategory.BROADBAND, UnmetCategory.OTHER)
    assert served["unmet"] == ["broadband", "other"]
    [filed] = served["unmet_at"]
    assert filed["category"] == "broadband"
    assert text[filed["span"]["start"] : filed["span"]["end"]] == "fast broadband"


@pytest.mark.parametrize(
    "words",
    [
        # Words that no offer rests on.
        "tell me what I can afford there",
        # Words that an offer rests on, and more that name something of their own.
        "affluent, and tell me what I can afford there",
        # No words at all: code cannot say what the model meant, and the model may be right.
        "",
    ],
)
def test_what_a_model_could_not_place_is_kept_where_its_words_say_more_than_an_offer(words: str):
    text = "slightly affluent, and tell me what I can afford there"
    category = "affordability_verdict"
    filed = {"category": category, "words": words} if words else category

    result, _ = asked(model_output(unmet=[filed]), text=text)

    assert {words for said in quoted(result, text).values() for words in said} == {"affluent"}
    assert UnmetCategory.AFFORDABILITY_VERDICT in result.unmet


def test_a_request_about_who_lives_somewhere_is_redirected_whoever_notices():
    flagged, _ = asked(model_output(policy_flags=["avoid_group"]), text="somewhere nice, honestly")
    missed, _ = asked(model_output(), text="leafy and not too many students, honestly")
    neither, _ = asked(model_output(), text="leafy and near a mosque, honestly")

    # The lexicon is a backstop: a model that misses it cannot overrule it.
    for result in (flagged, missed):
        assert result.status is InterpretStatus.POLICY_REDIRECT
        assert result.notice is Notice.NEUTRAL_PLACES
    # A wish for an amenity is not a wish about people.
    assert neither.notice is Notice.NONE


def test_an_off_topic_request_makes_no_offer():
    text = "what is the capital of France"
    answer = model_output(status="off_topic", weight_ops=[model_weight("green_cover", words=text)])
    result, _ = asked(answer, text=text)

    assert result.status is InterpretStatus.OFF_TOPIC and result.notice is Notice.OFF_TOPIC
    assert result.operations.count == 0 and result.suggestions == ()


def test_a_model_that_answers_off_topic_does_not_overrule_the_rules():
    text = "Pubs are so noisy"
    result, _ = asked(model_output(status="off_topic"), text=text)
    ruled = RuleInterpreter().interpret(
        InterpretRequest(text=text, spec=renter(), release=release())
    )

    # The rules noticed something, so their answer is served in the model's place.
    assert result == ruled.replace(degraded=True, usage=result.usage)
    assert result.suggestions and result.usage.input_tokens == 812


def test_what_cannot_be_met_is_reported_once_and_in_order():
    answer = model_output(unmet=["other", "broadband", "other", "flood_risk"])
    result, _ = asked(answer)

    assert result.unmet == ("broadband", "flood_risk", "other")


@pytest.mark.parametrize(
    "answer",
    [
        "not json at all",
        "[]",
        json.dumps({"status": "ok"}),
        json.dumps(model_output(note="an extra field")),
        json.dumps(model_output(weight_ops=[model_weight("residents_under_30")])),
        json.dumps(model_output(tag_ops=[{"action": "set", "tag_id": "leafy"}])),
        json.dumps(model_output(weight_ops=[model_weight("green_cover", value="NaN")])),
        json.dumps(model_output(commute_ops=[model_commute(destination_text="x" * 500)])),
        json.dumps(model_output(tag_ops=[None])),
        json.dumps(model_output(weight_ops=[model_weight("green_cover")] * (MAX_EDITS + 1))),
        json.dumps(model_output(unmet=[{"category": "broadband"}])),
        json.dumps(model_output(unmet=[{"category": "who_lives_there", "words": ""}])),
    ],
    ids=range(12),
)
def test_an_answer_that_does_not_fit_the_schema_is_a_failure_with_nothing_to_say(answer: str):
    with pytest.raises(ModelError) as failed:
        asked(answer)

    # No message, and nothing to be printed after it: the answer can quote the person.
    assert str(failed.value) == ""
    assert_nothing_follows(failed.value)


# A number in the model's answer must be a number.

NUMBERS: list[tuple[str, str, dict[str, Any]]] = [
    ("budget_ops", "amount", model_budget(amount=1500)),
    ("commute_ops", "position", model_commute(action="remove", position=1)),
    ("commute_ops", "max_minutes", model_commute(action="update", position=1, max_minutes=30)),
    ("weight_ops", "value", model_weight("park_proximity", action="set", value=1.0, step="none")),
    ("tag_ops", "value", model_tag("leafy", action="set", value=1.0, step="none")),
    ("setting_ops", "value", model_setting("commute_weight", value=1.0)),
]
NOT_NUMBERS = [True, False, "1", "0.5", "30", "", "one", "NaN", "Infinity", None, [1], {"n": 1}]


def test_every_number_a_model_can_answer_with_is_held_to_the_rule():
    schema: Any = SCHEMA
    numbers: set[tuple[str, str]] = set()
    for group, edits in schema["properties"].items():
        record = schema["$defs"].get(edits.get("items", {}).get("$ref", "").rsplit("/", 1)[-1], {})
        for name, held in record.get("properties", {}).items():
            if held.get("type") in ("integer", "number"):
                numbers.add((group, name))

    assert numbers == {(group, name) for group, name, _ in NUMBERS}


@pytest.mark.parametrize("wrong", NOT_NUMBERS, ids=repr)
@pytest.mark.parametrize(("group", "name", "edit"), NUMBERS, ids=[n for _, n, _ in NUMBERS])
def test_a_number_in_a_models_answer_must_be_a_number(
    group: str, name: str, edit: dict[str, Any], wrong: Any
):
    answer = json.dumps(model_output(**{group: [edit | {name: wrong, "words": "forget"}]}))

    with pytest.raises(ModelError) as failed:
        asked(answer, text="forget the commute, honestly", spec=searching())

    assert str(failed.value) == ""
    assert_nothing_follows(failed.value)


# When the model is slow, capped or broken.


@pytest.mark.parametrize(
    ("failure", "counted"),
    [
        (ModelTimeout(), "timeout"),
        (ModelCapped(), "capped"),
        (ModelError(), "error"),
        (RuntimeError(CANARY), "error"),
        ("not an answer", "error"),
        (json.dumps(model_output(commute_ops=[model_commute(position=True)])), "error"),
    ],
    ids=["slow", "capped", "broken", "raised", "not an answer", "true for a number"],
)
def test_the_rules_answer_when_the_model_is_slow_capped_or_broken(failure: Any, counted: str):
    text = "Honestly, leafy, and 40 minutes to Cindermoor Works"
    broken = ModelInterpreter(FakeModelClient(failure), MODEL, 512, 2.5)
    deps = make_deps(interpreter=broken, model_id=MODEL)

    fallen = client_for(deps).post("/v1/interpret", json={"text": text})
    ruled = client_for(make_deps()).post("/v1/interpret", json={"text": text})

    # Never a 5xx because a model failed. The person gets what the rules offer.
    assert fallen.status_code == 200
    expected = ruled.json()["data"] | {"degraded": True}
    assert fallen.json()["data"] == expected
    assert expected["interpreter"] == "rule" and len(expected["suggestions"]) == 2
    assert [record.status for record in deps.calls.records(NOW)] == [counted]


def test_the_rules_read_what_the_provider_would_not_and_the_answer_says_so():
    text = "Honestly, leafy, and 40 minutes to Cindermoor Works"
    refusing = ModelInterpreter(FakeModelClient(ModelRefused()), MODEL, 512, 2.5)
    deps = make_deps(interpreter=refusing, model_id=MODEL)

    fallen = client_for(deps).post("/v1/interpret", json={"text": text})
    ruled = client_for(make_deps()).post("/v1/interpret", json={"text": text})

    # The rules read it as they would with no model, and one field says why they did.
    assert fallen.status_code == 200
    assert ruled.json()["data"]["model_refused"] is False
    assert fallen.json()["data"] == ruled.json()["data"] | {"degraded": True, "model_refused": True}
    assert [record.status for record in deps.calls.records(NOW)] == ["refused"]


def test_nothing_but_a_refusal_is_said_to_be_one():
    text = "Honestly, leafy, and 40 minutes to Cindermoor Works"
    answers: list[Any] = [ModelTimeout(), ModelCapped(), ModelError(), model_output()]

    for answer in answers:
        reads = ModelInterpreter(FakeModelClient(answer), MODEL, 512, 2.5)
        client = client_for(make_deps(interpreter=reads, model_id=MODEL))
        for ask_model in (True, False):
            sent = {"text": text, "ask_model": ask_model}
            assert client.post("/v1/interpret", json=sent).json()["data"]["model_refused"] is False
    # Asked for the rules alone, no model is asked, so none can refuse.
    refusing = ModelInterpreter(FakeModelClient(ModelRefused()), MODEL, 512, 2.5)
    alone = client_for(make_deps(interpreter=refusing, model_id=MODEL)).post(
        "/v1/interpret", json={"text": text, "ask_model": False}
    )
    assert alone.json()["data"]["model_refused"] is False


def test_the_rules_offers_are_served_at_once_and_never_wait_on_the_model():
    text = "my dog wants somewhere to tear round, near a park"
    answer = model_output(weight_ops=[model_weight("park_proximity", words=text)])
    model = FakeModelClient(answer)
    deps = make_deps(interpreter=ModelInterpreter(model, MODEL, 512, 2.5), model_id=MODEL)
    client = client_for(deps)

    at_once = client.post("/v1/interpret", json={"text": text, "ask_model": False}).json()["data"]
    ruled = client_for(make_deps()).post("/v1/interpret", json={"text": text}).json()["data"]

    # The rules answered, no model was asked, and the answer says that one has more to read.
    assert model.calls == []
    assert at_once == ruled | {"model_pending": True}
    assert at_once["interpreter"] == "rule" and not at_once["degraded"]
    # Asked again, the model reads, and what it says joins what the rules offered.
    then = client.post("/v1/interpret", json={"text": text}).json()["data"]
    assert len(model.calls) == 1 and not then["model_pending"]
    assert [offer["target"] for offer in then["suggestions"]] == [
        offer["target"] for offer in at_once["suggestions"]
    ]
    assert [way["id"] for way in then["suggestions"][0]["choices"] if way["guess"]] == ["more"]


def test_a_model_is_asked_as_it_was_where_the_rules_left_only_words_that_ask_for_nothing():
    # "I want somewhere" asks for nothing, and is not said to be unread. The rules made
    # nothing of it all the same, so a model is asked, as it was before such words were
    # left out of what is said to be unread: what it marks as its guess is not lost.
    text = "I want somewhere affluent"
    model = FakeModelClient(model_output())
    deps = make_deps(interpreter=ModelInterpreter(model, MODEL, 512, 2.5), model_id=MODEL)
    client = client_for(deps)

    at_once = client.post("/v1/interpret", json={"text": text, "ask_model": False}).json()["data"]
    then = client.post("/v1/interpret", json={"text": text}).json()["data"]

    assert (at_once["unread"], at_once["model_pending"]) == ([], True)
    assert len(model.calls) == 1
    assert (then["unread"], then["model_pending"]) == ([], False)
    # That nothing was made of some word is said as it was.
    assert "other" in at_once["unmet"] and "other" in then["unmet"]


def test_what_a_model_leaves_of_a_stretch_is_not_said_to_be_unread_where_it_asks_for_nothing():
    text = "I want somewhere with a playpark"
    answer = model_output(weight_ops=[model_weight("park_proximity", words="playpark")])
    model = FakeModelClient(answer)
    deps = make_deps(interpreter=ModelInterpreter(model, MODEL, 512, 2.5), model_id=MODEL)
    client = client_for(deps)

    at_once = client.post("/v1/interpret", json={"text": text, "ask_model": False}).json()["data"]
    then = client.post("/v1/interpret", json={"text": text}).json()["data"]

    # The rules know no such word, and say that the whole of the stretch is unread.
    assert at_once["unread"] == [{"start": 0, "end": len(text)}]
    # The model read the word. What is left of the stretch is how the wish was led in to.
    assert [offer["target"] for offer in then["suggestions"]] == ["feature:park_proximity"]
    assert then["unread"] == []
    # A word that nobody read is still said to be unread, with what stands beside it.
    other = "I want somewhere with a playpark and a zebra"
    left = client.post("/v1/interpret", json={"text": other}).json()["data"]["unread"]
    assert [other[span["start"] : span["end"]] for span in left] == ["and a zebra"]


def test_nothing_more_is_pending_where_the_rules_read_the_whole_of_it():
    model = FakeModelClient(model_output())
    deps = make_deps(interpreter=ModelInterpreter(model, MODEL, 512, 2.5), model_id=MODEL)
    client = client_for(deps)

    plain = client.post("/v1/interpret", json={"text": "leafy", "ask_model": False})
    by_rules = client_for(make_deps()).post(
        "/v1/interpret", json={"text": "my dog likes it here", "ask_model": False}
    )

    assert plain.json()["data"]["model_pending"] is False
    # Where the rules are all there is, nothing is ever pending.
    assert by_rules.json()["data"]["model_pending"] is False
    assert model.calls == []


def test_a_call_the_rules_answered_by_themselves_is_on_record_as_the_rules():
    model = FakeModelClient(model_output())
    deps = make_deps(interpreter=ModelInterpreter(model, MODEL, 512, 2.5), model_id=MODEL)

    client_for(deps).post("/v1/interpret", json={"text": "leafy"})

    [record] = deps.calls.records(NOW)
    assert (record.interpreter, record.provider, record.model) == ("rule", "", "")
    assert record.input_tokens == 0


def test_a_reply_never_prints_what_the_model_said():
    reply = ModelReply(output=CANARY, input_tokens=1, output_tokens=2, cache_read_tokens=3)

    assert CANARY not in repr(reply) and CANARY not in str(reply)
