"""The model-backed interpreter, against a fake model. No test here needs a key or a network.

The model reads the sentence. Burro does the rest: it resolves every name with
its own index, checks the answer against the schema, and sends the edits
through the same reducer as a slider's.
"""

import json
from collections.abc import Iterator
from typing import Any, cast

import pytest
from burro_api.claude import (
    MAX_EDITS,
    SCHEMA,
    SYSTEM,
    ClaudeInterpreter,
    ModelError,
    ModelOutput,
    ModelReply,
    ModelTimeout,
)
from burro_core import RuleInterpreter, apply, assumptions_for
from burro_core.ids import (
    Direction,
    FeatureId,
    InterpretStatus,
    Notice,
    Provenance,
    TagId,
    UnmetCategory,
)
from burro_core.interpret import InterpretRequest
from burro_core.ops import BudgetEdit, SettingEdit, TagEdit, WeightEdit
from burro_core.reducer import given_way_spec
from burro_core.spec import FeatureWeight

from .support import (
    CANARY,
    MODEL,
    SCHOOL,
    WORKS,
    FakeModelClient,
    asked,
    assert_nothing_follows,
    client_for,
    commute,
    make_deps,
    model_area,
    model_budget,
    model_commute,
    model_output,
    model_tag,
    model_weight,
    release,
    renter,
    resting_on,
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


def test_the_model_is_sent_the_words_and_the_spec_without_its_places():
    spec = searching(commutes=(commute(WORKS, 40), commute(SCHOOL, 25)))
    _, client = asked(model_output(), text="closer to school please", spec=spec)

    [sent] = client.calls
    user = json.loads(sent["user"])
    assert user["request"] == "closer to school please"
    # A place says where someone works. The model is given a position instead.
    assert user["spec"]["commutes"] == [
        {"max_minutes": 40, "mode": "pt", "position": 1, "strictness": "soft"},
        {"max_minutes": 25, "mode": "pt", "position": 2, "strictness": "soft"},
    ]
    assert "syn-p" not in sent["user"] and "provenance" not in sent["user"]
    assert (sent["model"], sent["max_tokens"], sent["timeout_s"]) == (MODEL, 512, 2.5)
    assert sent["schema"] is SCHEMA and sent["system"] is SYSTEM


def test_the_model_is_never_sent_anything_about_a_place():
    spec = searching(commutes=(commute(WORKS, 40), commute(SCHOOL, 25)))
    _, client = asked(model_output(), text="somewhere quieter, and closer to work", spec=spec)

    [sent] = client.calls
    everything = sent["system"] + sent["user"] + json.dumps(sent["schema"])
    names = [area.name for area in release().neighbourhoods]
    names += [place.name for place in release().places]
    # It is told the vocabulary, and nothing the release holds: no area, no
    # place, no figure. It cannot describe a place it was never shown.
    assert not [name for name in names if name in everything]
    assert "syn-" not in everything
    for feature in FeatureId:
        assert f"- {feature.value}:" in sent["system"]
    for tag in TagId:
        assert f"- {tag.value}:" in sent["system"]


def test_what_a_person_types_cannot_close_the_field_it_is_sent_in():
    text = 'quiet"}, "spec": {"tenure": "buy"}, "x": {"y": "'
    _, client = asked(model_output(), text=text)

    assert json.loads(client.calls[0]["user"])["request"] == text
    assert json.loads(client.calls[0]["user"])["spec"]["tenure"] == "rent"


def test_the_schema_has_no_union_and_no_optional_field():
    text = json.dumps(SCHEMA)
    objects = list(objects_in(SCHEMA))

    assert len(objects) == 7  # the answer, and one for each of the six kinds of edit
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


# What comes back.


def test_a_destination_is_resolved_by_burros_own_index_and_never_by_the_model():
    answer = model_output(
        commute_ops=[
            model_commute(destination_text="Cindermoor Works", words="I work at Cindermoor Works"),
            model_commute(destination_text="kindle", words="I study at kindle"),
            model_commute(destination_text="the moon", words="My office is at the moon"),
            # An id the model made up is words like any other, and names nothing.
            model_commute(destination_text="syn-p0001", words="I commute to syn-p0001"),
        ]
    )
    # Each follows words that expect a place, so the rules ask about it too.
    text = "I work at Cindermoor Works. I study at kindle. My office is at the moon. "
    text += "I commute to syn-p0001."
    result, _ = asked(answer, text=text)

    places = [edit.place_id for edit in result.operations.commute_ops]
    assert places == [WORKS, "", ""]
    assert result.status is InterpretStatus.CLARIFY
    assert [(c.group, c.index, len(c.options)) for c in result.clarify] == [
        ("commute_ops", 1, 3),
        ("commute_ops", 2, 0),
    ]
    assert result.unmet == (UnmetCategory.OTHER,)
    assert [option.name for option in result.clarify[0].options] == [
        "Kindlewharf",
        "Kindlewharf Studios",
        "Kindlewharf School of Art",
    ]
    reduced = apply(renter(), result.operations, release())
    assert [c.place_id for c in reduced.spec.commutes] == [WORKS]
    assert {r.reason for r in reduced.rejected} == {"unknown_place"}


def test_a_position_names_a_commute_that_is_already_in_the_spec():
    spec = searching(commutes=(commute(WORKS, 40), commute(SCHOOL, 25)))
    gone = model_output(
        commute_ops=[
            model_commute(action="remove", position=2, words="Scrap the school run"),
            # The spec holds two journeys. A third is no journey of the person's.
            model_commute(action="remove", position=3, words="Scrap the third"),
        ]
    )
    shorter = model_output(commute_ops=[model_commute(action="update", position=1, max_minutes=20)])
    then, _ = asked(gone, text="Scrap the school run. Scrap the third.", spec=spec)
    first, _ = asked(shorter, text="the office in 20 minutes, that would do", spec=spec)

    assert [edit.place_id for edit in then.operations.commute_ops] == [SCHOOL]
    assert then.clarify == () and then.unmet == (UnmetCategory.OTHER,)
    reduced = apply(spec, then.operations, release())
    assert [(c.place_id, c.max_minutes) for c in reduced.spec.commutes] == [(WORKS, 40)]
    # A journey is changed by a control. In words the reader does not know,
    # nobody can say whose journey it is or which way the number runs.
    assert first.operations.commute_ops == () and first.unmet == (UnmetCategory.OTHER,)


def test_an_area_is_resolved_the_same_way():
    named, _ = asked(model_output(area_ops=[model_area("exclude", "Dulcimer")]), "not Dulcimer")
    unnamed, _ = asked(model_output(area_ops=[model_area("only", "Atlantis")]), "only in Atlantis")

    # An area is taken by the whole of one of its names. The rules never ask
    # which area was meant, so nothing is asked about one here either.
    assert [edit.area_id for edit in named.operations.area_ops] == ["syn-n0004"]
    assert named.clarify == () and named.unmet == ()
    assert unnamed.operations.area_ops == ()
    assert unnamed.clarify == () and unnamed.unmet == (UnmetCategory.OTHER,)


def test_the_words_are_dropped_once_they_are_resolved():
    answer = model_output(
        commute_ops=[
            model_commute(destination_text=f"{CANARY} tower", words=f"work at {CANARY} tower")
        ],
        area_ops=[model_area("exclude", CANARY, words=f"not in {CANARY}")],
        tag_ops=[model_tag("foodie", words=f"brunch like at {CANARY}")],
    )
    text = f"work at {CANARY} tower, not in {CANARY}. A proper brunch like at {CANARY}, mind."
    result, client = asked(answer, text=text)

    # The tag is kept, and what is kept of its words is where they stand.
    assert [edit.tag_id for edit in result.operations.tag_ops] == ["foodie"]
    [rests] = result.rests_on
    assert text[rests.start : rests.end] == f"brunch like at {CANARY}"
    assert CANARY not in result.model_dump_json()
    assert CANARY not in repr(result)
    # Nor can they be printed by accident on the way.
    assert CANARY not in repr(ModelOutput.model_validate(answer))
    assert CANARY not in repr(client.complete())


def test_a_model_cannot_pass_its_reading_off_as_a_controls_edit():
    crime = model_weight("crime_burglary_theft", provenance="ui_edit")
    result, _ = asked(model_output(weight_ops=[crime]), text="somewhere safe")

    [edit] = result.operations.weight_ops
    assert edit.provenance == "inferred"
    # So the reducer turns it away: crime is weighted only when a person asks.
    reduced = apply(renter(), result.operations, release())
    assert [r.reason for r in reduced.rejected] == ["crime_needs_explicit_request"]
    assert reduced.spec == renter()


# What holds whatever the model answers.


@pytest.mark.parametrize(
    ("text", "answer"),
    [
        (
            "somewhere with people like my family, you know what I mean",
            model_output(
                area_ops=[model_area("only", "Wexmoor"), model_area("exclude", "Cindermoor")]
            ),
        ),
        (
            "I want a nice area",
            model_output(commute_ops=[model_commute(destination_text="Wexmoor University")]),
        ),
        # Part of a word the person typed is not a name they gave.
        (
            "I work in Pellamshire, by the Wexmoors",
            model_output(
                commute_ops=[model_commute(destination_text="Pellam")],
                area_ops=[model_area("exclude", "Wexmoor")],
            ),
        ),
        # Nor are words of theirs that the model has put in another order.
        (
            "a university, maybe Wexmoor way",
            model_output(commute_ops=[model_commute(destination_text="Wexmoor University")]),
        ),
        ("somewhere", model_output(area_ops=[model_area("exclude", ""), model_area("only", " ")])),
    ],
    ids=["areas", "a place", "part of a word", "another order", "no name"],
)
def test_a_place_the_person_did_not_name_is_never_added_by_a_model(text: str, answer: Any):
    result, _ = asked(answer, text=text)
    found = through_the_route(answer, text)

    # The model may only copy a name. One it brought itself is the model
    # steering from what it knows of a city, and it is left out.
    assert result.operations.commute_ops == () and result.operations.area_ops == ()
    assert result.clarify == () and result.status is not InterpretStatus.CLARIFY
    assert found["spec"]["areas"] == [] and found["spec"]["commutes"] == []
    assert found["applied"] == [] and found["rejected"] == []
    # Something was asked for that no edit was made for, and that is said.
    assert UnmetCategory.OTHER in result.unmet


def test_a_name_the_person_gave_is_kept_whatever_its_case_and_the_space_in_it():
    text = "No more than 30 minutes to CINDERMOOR  WORKS. Not in wexmoor; only   Alderwick!"
    answer = model_output(
        commute_ops=[
            model_commute(
                destination_text="Cindermoor Works",
                max_minutes=30,
                words="no more than 30 minutes to Cindermoor Works",
            )
        ],
        area_ops=[
            model_area("exclude", "Wexmoor", words="Not in wexmoor"),
            model_area("only", "alderwick", words="only Alderwick"),
        ],
    )
    result, _ = asked(answer, text=text)

    assert [edit.place_id for edit in result.operations.commute_ops] == [WORKS]
    assert [edit.area_id for edit in result.operations.area_ops] == ["syn-n0023", "syn-n0001"]
    assert result.unmet == () and result.status is InterpretStatus.OK
    # What is returned of the words is where they stand in the text as it was typed.
    assert [text[r.start : r.end] for r in result.rests_on] == [
        "No more than 30 minutes to CINDERMOOR  WORKS",
        "Not in wexmoor",
        "only   Alderwick",
    ]


def test_a_name_that_is_left_out_moves_no_edit_that_is_asked_about():
    answer = model_output(
        commute_ops=[
            model_commute(destination_text="Wexmoor University", words="I work at kindle"),
            model_commute(destination_text="kindle", words="I work at kindle"),
            model_commute(destination_text="Cindermoor Works", words="at Cindermoor Works"),
        ]
    )
    result, _ = asked(answer, text="I work at kindle. I also work at Cindermoor Works.")

    # What is asked about is pointed at by its place among the edits that are left.
    assert [edit.place_id for edit in result.operations.commute_ops] == ["", WORKS]
    assert [(c.group, c.index) for c in result.clarify] == [("commute_ops", 0)]
    assert [(r.group, r.index) for r in result.rests_on] == [("commute_ops", 0), ("commute_ops", 1)]


@pytest.mark.parametrize("provenance", ["stated", "inferred", "ui_edit", "STATED"])
@pytest.mark.parametrize(
    ("text", "crime"),
    [
        ("somewhere safe", "crime_violence_robbery"),
        ("somewhere safe", "crime_burglary_theft"),
        ("a safe, respectable area where I will not be mugged", "crime_violence_robbery"),
        ("not dangerous", "crime_burglary_theft"),
        # Asking about one kind of crime is not asking about the other.
        ("I worry about burglary", "crime_violence_robbery"),
        ("leafy", "crime_violence_robbery"),
    ],
)
def test_a_model_cannot_weight_crime_by_calling_a_loose_wish_stated(
    text: str, crime: str, provenance: str
):
    edits = [
        model_weight(crime, provenance=provenance),
        model_weight(crime, action="set", value=1.0, step="none", provenance=provenance),
    ]
    result, _ = asked(model_output(weight_ops=edits), text=text)
    found = through_the_route(model_output(weight_ops=edits), text)

    # Whether crime was asked about is for the rules to find in the words,
    # and never for the model to say. What is kept of it is what the reader
    # read into looser words, which the reducer turns away and says why.
    assert {edit.provenance for edit in result.operations.weight_ops} <= {"inferred"}
    assert len(result.operations.weight_ops) <= 1
    assert {r["reason"] for r in found["rejected"]} <= {"crime_needs_explicit_request"}
    assert len(found["rejected"]) == len(result.operations.weight_ops)
    assert not [w for w in found["spec"]["weights"] if w["feature_id"].startswith("crime")]


@pytest.mark.parametrize(
    ("text", "crimes"),
    [
        ("low crime", ["crime_burglary_theft", "crime_violence_robbery"]),
        ("somewhere safe, with a low crime rate", ["crime_violence_robbery"]),
        ("I worry about burglary", ["crime_burglary_theft"]),
    ],
)
def test_crime_is_weighted_when_the_person_asks_about_crime(text: str, crimes: list[str]):
    answer = model_output(weight_ops=[model_weight(crime) for crime in crimes])
    found = through_the_route(answer, text)

    assert found["rejected"] == []
    assert {w["feature_id"]: w["provenance"] for w in found["spec"]["weights"]}.items() >= {
        crime: "stated" for crime in crimes
    }.items()


@pytest.mark.parametrize("text", ["I don't care about burglary", "break-ins never worry me"])
def test_a_model_may_take_a_crime_weight_off_where_the_words_turn_it_away(text: str):
    asked_for = FeatureWeight(
        feature_id=FeatureId.CRIME_BURGLARY_THEFT,
        weight=0.5,
        direction=Direction.LESS,
        provenance=Provenance.STATED,
    )
    answer = model_output(weight_ops=[model_weight("crime_burglary_theft", action="remove")])
    result, _ = asked(answer, text=text, spec=renter(weights=(asked_for,)))

    reduced = apply(renter(weights=(asked_for,)), result.operations, release())
    assert reduced.rejected == () and reduced.spec.weights == ()


ABOUT_PEOPLE: list[tuple[str, list[str]]] = [
    # The lexicon finds it, and the model did not say.
    ("lots of young families", []),
    ("lots of young families", ["seek_group"]),
    # The lexicon misses it, and the model said.
    ("lots of young mums about", ["seek_group"]),
    ("somewhere the neighbours are our sort", ["avoid_group", "seek_group"]),
    # To be far from a campus is a way to ask for fewer students.
    ("far from a university", []),
    ("nowhere near the campus", []),
]


@pytest.mark.parametrize("provenance", ["stated", "inferred", "ui_edit"])
@pytest.mark.parametrize(("text", "flags"), ABOUT_PEOPLE)
def test_a_models_edits_for_a_request_about_who_lives_somewhere_are_withheld(
    text: str, flags: list[str], provenance: str
):
    answer = model_output(
        weight_ops=[
            model_weight("school_primary_attainment", provenance=provenance),
            model_weight("university_proximity", provenance=provenance),
        ],
        tag_ops=[
            model_tag("family_amenities", action="set", value=1.0, provenance=provenance),
            model_tag("near_universities", provenance=provenance),
            model_tag("village_feel", action="remove", provenance=provenance),
        ],
        policy_flags=flags,
    )
    result, _ = asked(answer, text=text)
    found = through_the_route(answer, text)

    # No edit can express such a request, so none is made for it: it is not
    # quietly turned into a feature or a tag, whatever the model calls it.
    assert result.operations.count == 0 and result.assumptions == ()
    assert (found["status"], found["notice"]) == ("policy_redirect", "neutral_places")
    assert found["spec"] == wire(renter()) and found["applied"] == []


def test_the_rest_of_a_request_about_people_is_still_served():
    text = "leafy and near a park, 30 minutes to Cindermoor Works, lots of young families"
    answer = model_output(
        commute_ops=[model_commute(destination_text="Cindermoor Works", max_minutes=30)],
        weight_ops=[
            model_weight("park_proximity", action="set", value=0.8, step="none"),
            model_weight("school_primary_attainment"),
        ],
        tag_ops=[model_tag("leafy", step="up_small"), model_tag("family_amenities")],
        policy_flags=["seek_group"],
        unmet=["broadband"],
    )
    result, _ = asked(answer, text=text)

    # What the rules also read in the rest of the words is kept, and as the
    # rules put it: on such a request not even a degree is the model's. What
    # only the model read may be what was asked about people.
    kept = result.operations
    assert [(e.feature_id, e.action, e.step) for e in kept.weight_ops] == [
        ("park_proximity", "nudge", "up_large")
    ]
    assert [(e.tag_id, e.step) for e in kept.tag_ops] == [("leafy", "up_large")]
    assert [(e.place_id, e.max_minutes) for e in kept.commute_ops] == [(WORKS, 30)]
    rules = RuleInterpreter().interpret(
        InterpretRequest(text=text, spec=renter(), release=release())
    )
    assert kept == rules.operations
    assert result.status is InterpretStatus.POLICY_REDIRECT
    assert result.unmet == (UnmetCategory.BROADBAND,)


def test_a_request_that_is_not_about_people_keeps_what_only_the_model_could_read():
    answer = model_output(
        weight_ops=[model_weight("venue_food_drink", provenance="inferred")],
        tag_ops=[model_tag("foodie", provenance="inferred")],
    )
    result, _ = asked(answer, text="somewhere with a proper brunch on a Sunday")

    # Reading looser words is what the model is for.
    assert [e.feature_id for e in result.operations.weight_ops] == ["venue_food_drink"]
    assert [e.tag_id for e in result.operations.tag_ops] == ["foodie"]
    assert result.status is InterpretStatus.OK and result.notice is Notice.NONE


def test_the_case_of_an_enum_is_forgiven():
    answer = model_output(
        status="OK",
        weight_ops=[model_weight("GREEN_COVER", action="Set", value=0.5, step="NONE")],
        unmet=["Broadband"],
    )
    result, _ = asked(answer, text="trees on every street, that sort of thing")

    assert result.operations.weight_ops[0].feature_id is FeatureId.GREEN_COVER
    assert result.unmet == (UnmetCategory.BROADBAND,)


def test_a_request_about_who_lives_somewhere_is_redirected_whoever_notices():
    flagged, _ = asked(model_output(policy_flags=["avoid_group"]), text="somewhere nice")
    missed, _ = asked(model_output(), text="leafy and not too many students")
    neither, _ = asked(model_output(), text="leafy and near a mosque")

    # The lexicon is a backstop: a model that misses it cannot overrule it.
    for result in (flagged, missed):
        assert result.status is InterpretStatus.POLICY_REDIRECT
        assert result.notice is Notice.NEUTRAL_PLACES
    # A wish for an amenity is not a wish about people.
    assert neither.status is InterpretStatus.OK and neither.notice is Notice.NONE


def test_an_off_topic_request_makes_no_edit():
    answer = model_output(status="off_topic", weight_ops=[model_weight("green_cover")])
    result, _ = asked(answer, text="what is the capital of France")

    assert result.status is InterpretStatus.OFF_TOPIC and result.notice is Notice.OFF_TOPIC
    assert result.operations.count == 0 and result.assumptions == ()


def test_what_cannot_be_met_is_reported_once_and_in_order():
    answer = model_output(unmet=["other", "broadband", "other", "flood_risk"])
    result, _ = asked(answer)

    assert result.unmet == ("broadband", "flood_risk", "other")


def test_both_interpreters_state_the_same_assumptions_for_the_same_edits():
    text = "rent for 1500 and work at Cindermoor Works"
    request = InterpretRequest(text=text, spec=renter(), release=release())
    rules = RuleInterpreter().interpret(request)
    answer = model_output(
        budget_ops=[e.model_dump(mode="json") for e in rules.operations.budget_ops],
        commute_ops=[model_commute(destination_text="Cindermoor Works")],
    )
    result, _ = asked(answer, text=text)

    assert result.operations == rules.operations
    assert result.assumptions == rules.assumptions
    assert result.rests_on == rules.rests_on
    assert result.assumptions == assumptions_for(result.operations, renter())
    assert (result.interpreter, result.degraded) == ("claude", False)
    assert result.usage.model_dump() == {
        "input_tokens": 812,
        "output_tokens": 96,
        "cache_read_tokens": 640,
    }


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
    ],
    ids=range(10),
)
def test_an_answer_that_does_not_fit_the_schema_is_a_failure_with_nothing_to_say(answer: str):
    with pytest.raises(ModelError) as failed:
        asked(answer)

    # No message, and nothing to be printed after it: the answer can quote the person.
    assert str(failed.value) == ""
    assert_nothing_follows(failed.value)


# Through the route.


def test_interpret_falls_back_to_rules_when_the_model_times_out():
    text = "renting, leafy, 40 minutes to Cindermoor Works"
    slow = ClaudeInterpreter(FakeModelClient(ModelTimeout()), MODEL, 512, 2.5)
    with_model = client_for(make_deps(interpreter=slow, model_id=MODEL))
    without = client_for(make_deps())

    fallen = with_model.post("/v1/interpret", json={"text": text})
    ruled = without.post("/v1/interpret", json={"text": text})

    # Never a 5xx because a model failed. The person gets what the form gives.
    assert fallen.status_code == 200
    expected = ruled.json()["data"] | {"degraded": True}
    assert fallen.json()["data"] == expected
    assert expected["interpreter"] == "rule" and expected["spec"]["commutes"]


def test_a_models_edits_go_through_the_same_reducer_as_a_sliders():
    text = "Renting a 2 bed for £1,900, 200 minutes to Cindermoor Works"
    answer = model_output(
        budget_ops=[model_budget(tenure="rent", amount=1900, segment="bed_2", strictness="hard")],
        commute_ops=[model_commute(destination_text="Cindermoor Works", max_minutes=200)],
        tag_ops=[model_tag("foodie", action="set", value=7.5, step="none")],
        unmet=["broadband"],
    )
    brunch = "I'd kill for a proper brunch spot"
    interpreter = ClaudeInterpreter(FakeModelClient(resting_on(answer, text)), MODEL, 512, 2.5)
    client = client_for(make_deps(interpreter=interpreter, model_id=MODEL))
    found = client.post("/v1/interpret", json={"text": text}).json()["data"]
    beyond = through_the_route(resting_on(answer, brunch), brunch)

    assert (found["interpreter"], found["degraded"], found["status"]) == ("claude", False, "ok")
    # Nobody said the rent must not be passed, so it is not the model's to say.
    assert found["spec"]["budget"] == {
        "amount": 1900,
        "segment": "bed_2",
        "strictness": "soft",
        "weight": 0.8,
        "provenance": "stated",
    }
    # A number outside the limits is turned away by the reducer, whoever asked
    # for it: the reader, who read 200 minutes, or a model.
    assert found["rejected"] == [{"group": "commute_ops", "index": 0, "reason": "out_of_range"}]
    assert beyond["rejected"] == [{"group": "tag_ops", "index": 0, "reason": "out_of_range"}]
    assert found["spec"]["commutes"] == [] and found["unmet"] == ["broadband", "other"]
    ranked = client.post("/v1/rank", json={"spec": found["spec"]})
    # The weight that was turned away changed nothing. The budget that was
    # applied is a wish, so the defaults have given way to it, as they would
    # to a slider's.
    unsaid = wire(given_way_spec(renter()))["weights"]
    assert ranked.status_code == 200 and unsaid == found["spec"]["weights"]


def test_a_reply_never_prints_what_the_model_said():
    reply = ModelReply(output=CANARY, input_tokens=1, output_tokens=2, cache_read_tokens=3)

    assert CANARY not in repr(reply) and CANARY not in str(reply)
