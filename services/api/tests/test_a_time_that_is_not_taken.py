"""A time that is not taken is never made up for, by the rules alone or behind a model.

"1 hour, 15 minutes to Pellam Exchange" was offered as a journey with no time.
The answer said "You gave no number of minutes: Burro took 45", and one press
added the journey at 45 minutes, which nobody said. Core now says that the
place was heard and that the time beside it was not taken, and offers nothing
to press (contract, section 8.1).

A model's reading of a journey to such a place is dropped, whatever minutes
it gives, as its reading of a journey to a place to stay away from is. No call
is made: a stand-in hands the answer to the reader.
"""

from typing import Any

import pytest
from burro_api.offers import in_add_all
from burro_api.wording import NO_JOURNEY
from burro_core.interpret import TIME_NOT_TAKEN
from fastapi.testclient import TestClient

from .support import asked, client_for, make_deps, model_commute, model_output, offers

NO_EDITS: dict[str, list[Any]] = {
    "budget_ops": [],
    "commute_ops": [],
    "weight_ops": [],
    "tag_ops": [],
    "area_ops": [],
    "setting_ops": [],
}


@pytest.fixture(scope="module")
def client() -> TestClient:
    return client_for(make_deps())


@pytest.mark.parametrize(
    "text",
    [
        "1 hour, 15 minutes to Pellam Exchange",
        "1 15 to Pellam Exchange",
        "1.30 hours to Pellam Exchange",
        "a few hours to Pellam Exchange",
        "24 hours to Pellam Exchange, I think",
    ],
)
def test_route_1_offers_no_journey_where_the_time_before_a_place_is_not_taken(
    client: TestClient, text: str
):
    response = client.post("/v1/interpret", json={"text": text})
    assert response.status_code == 200
    found = response.json()["data"]

    assert (found["status"], found["operations"]) == ("suggest", NO_EDITS)
    [heard] = found["suggestions"]
    assert (heard["target"], heard["label"]) == ("commute", "Pellam Exchange")
    assert (heard["does"], heard["note"], heard["said"]) == (NO_JOURNEY, TIME_NOT_TAKEN, [])
    # Nothing of it can be pressed, by one press or by a press of its own.
    assert heard["add_all"] == ""
    assert [(way["id"], way["operations"]) for way in heard["choices"]] == [("ignore", NO_EDITS)]
    assert found["spec"]["commutes"] == []
    # The words of the time are said to be unread, and the place is not.
    unread = [text[span["start"] : span["end"]] for span in found["unread"]]
    assert unread and not [left for left in unread if "Pellam" in left]


@pytest.mark.parametrize(
    ("text", "minutes"),
    [
        ("1 hour, 15 minutes to Pellam Exchange", 15),
        ("1 hour, 15 minutes to Pellam Exchange", 75),
        ("1 15 to Pellam Exchange", 15),
        ("1 hour 75 to Pellam Exchange", 75),
        ("a third of an hour to Pellam Exchange", 60),
        ("a third of an hour to Pellam Exchange", 20),
        ("1.30 hours to Pellam Exchange", 90),
    ],
)
def test_a_models_reading_of_such_a_journey_is_dropped_whatever_minutes_it_gives(
    text: str, minutes: int
):
    journey = model_commute(destination_text="Pellam Exchange", max_minutes=minutes, words=text)

    result, _ = asked(model_output(commute_ops=[journey]), text=text)

    [heard] = offers(result).values()
    assert [way.id for way in heard.choices] == ["ignore"]
    assert (heard.note, in_add_all(heard)) == (TIME_NOT_TAKEN, None)
    assert result.operations.commute_ops == ()
