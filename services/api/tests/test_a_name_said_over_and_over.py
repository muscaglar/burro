"""A sentence that says one thing over and over is read in a fraction of a second.

Route 1 is open to anybody, and nothing limits what one caller may ask of it. A
sentence of 599 characters that named one place sixty times, each with a time,
held a processor for forty seconds, where a plain sentence takes a few
thousandths of one: a ranking that somebody else asked for meanwhile waited a
hundred times as long as it takes. The rules read the one clause of the
sentence again for each of the sixty places its offer points at, and each
reading worked the times of the sentence out again for each name.

A clause is now read once, however many places of an offer stand in it, and
the times of a sentence are worked out once. And a part of a sentence of many
words is looked through for no two things with no word between them: a word
of one letter said three hundred times, with a wish in the middle, held a
processor for three seconds. And whether a turn leads up to a thing is read once
for the thing, however many things are listed after it: a list of ninety-nine
was read ten thousand times. And what is said of a thing is read by itself,
where the rules would not apply its sentence, once for all the things that
stand in it, and each part of its sentence once for all the things beside it.
Every name here is of the made-up city, and every sentence is one the service
was driven with.
"""

import time
from typing import Any

import pytest
from burro_api import guard, typed
from burro_core.interpret import InterpretRequest, InterpretResult
from fastapi.testclient import TestClient

from .support import client_for, make_deps

# The most characters route 1 takes.
MOST = 600
# What is said over and over. Each held the processor for half a second or more, and the
# first for forty.
SAID = [
    "1h of QH1 ",
    "1h of QH1 but ",
    "QH1 an hour or ",
    "30 mins of QH7 from ",
    "1h of Foxholt or ",
    "QH2 max 30 minutes but ",
    "30 minutes to Kindlewharf of ",
    "Brackenhythe 30 minutes to Dulcimer Green ",
    "a ",
    "a an ",
    "of a ",
    "posh, ",
    "gritty gyms, ",
]
# A run of one word of one letter, with something said in the middle of it or at its end.
# Each held the processor for a second and a half or more, and the first for three.
AMONG = ["near a park", "families", "leafy", "30 minutes to QH1", "within 30 minutes of QH1"]
# The slowest is read in under 0.2 s on a developer's machine. A runner that is ten times
# slower still reads it within this, and what each sentence took before was more. What
# made each slow is held by counting, here and in core, and by no clock.
WITHIN_S = 2.0
# A machine that is busy with other work gives a reading that is too long now and then, so
# a sentence is held to the quickest of a few.
READINGS = 3


def over_and_over(said: str) -> str:
    return (said * (MOST // len(said))).rstrip()


def among(said: str, last: bool) -> str:
    """`said` in the middle of a run of "a", or at the end of one, in 600 characters or fewer."""
    run = ["a"] * ((MOST - len(said) - 1) // 2)
    half = run[: len(run) // 2]
    return " ".join([*run, said] if last else [*half, said, *half])


@pytest.fixture(scope="module")
def client() -> TestClient:
    found = client_for(make_deps())
    # The first call makes the names of the release ready, which no later one does.
    assert found.post("/v1/interpret", json={"text": "leafy", "ask_model": False}).is_success
    return found


def processor_taken(client: TestClient, text: str) -> float:
    began = time.process_time()
    response = client.post("/v1/interpret", json={"text": text, "ask_model": False})
    took = time.process_time() - began
    assert response.status_code == 200
    return took


@pytest.mark.parametrize("said", SAID)
def test_what_is_said_over_and_over_is_read_within_two_seconds_of_processor(
    client: TestClient, said: str
):
    text = over_and_over(said)

    assert any(processor_taken(client, text) < WITHIN_S for _ in range(READINGS))


@pytest.mark.parametrize("last", [False, True], ids=["in the middle", "at the end"])
@pytest.mark.parametrize("said", AMONG)
def test_what_is_said_among_many_words_is_read_within_two_seconds_of_processor(
    client: TestClient, said: str, last: bool
):
    text = among(said, last)

    assert MOST - 4 <= len(text) <= MOST
    assert any(processor_taken(client, text) < WITHIN_S for _ in range(READINGS))


def turns_looked_for(client: TestClient, text: str, monkeypatch: pytest.MonkeyPatch) -> int:
    """How often a stretch is read for a word that turns, while `text` is answered."""
    turned_once = typed.turned_once
    looked: list[int] = []

    def counted(read: typed.Typed, reach: tuple[int, int]) -> bool:
        looked.append(1)
        return turned_once(read, reach)

    with monkeypatch.context() as patched:
        patched.setattr(typed, "turned_once", counted)
        patched.setattr(guard, "turned_once", counted)
        response = client.post("/v1/interpret", json={"text": text, "ask_model": False})
    assert response.status_code == 200 and response.json()["data"]["suggestions"]
    return len(looked)


@pytest.mark.parametrize("said", ["posh, ", "gritty gyms, "])
def test_a_list_is_read_for_a_turn_no_more_often_for_each_thing_as_it_grows_longer(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, said: str
):
    few, many = 9, MOST // len(said)
    short = (said * few).rstrip(" ,")
    long = (said * many).rstrip(" ,")

    of_few = turns_looked_for(client, short, monkeypatch)
    of_many = turns_looked_for(client, long, monkeypatch)

    # As many times for each thing of a long list as of a short one, and a few over.
    assert of_many / many <= of_few / few + 1


def each_saying_something_else(said: str) -> str:
    """`said` over and over, with two letters in place of its "#" that are never the same."""
    letters = "abcdefghijklmnopqrstuvwxyz"
    pairs = (first + second for first in letters for second in letters)
    text = ""
    for pair in pairs:
        more = said.replace("#", pair)
        if len(text) + len(more) > MOST:
            break
        text += more
    return text.rstrip(" ,")


# What is said of a thing is read by itself where the rules would not apply its sentence,
# and so is each part of the sentence beside it. Each of these has the rules read as many
# words again as the sentence holds parts, and none is said twice.
EACH_BY_ITSELF = [
    "pub #, ",
    "# pub, ",
    "lively, # #, ",
    "leafy and want pubs # ",
    "I hate # and want pubs ",
    "pubs because # ",
    "no pubs or #, ",
]


@pytest.mark.parametrize("said", EACH_BY_ITSELF)
def test_things_that_are_each_said_by_themselves_are_read_within_two_seconds_of_processor(
    client: TestClient, said: str
):
    text = each_saying_something_else(said)

    assert MOST - len(said) - 2 <= len(text) <= MOST
    assert any(processor_taken(client, text) < WITHIN_S for _ in range(READINGS))


def test_what_is_said_of_many_things_together_is_read_once(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    rules = guard._RULES  # pyright: ignore[reportPrivateUsage]
    read: list[str] = []

    class Counted:
        def interpret(self, request: InterpretRequest) -> InterpretResult:
            read.append(request.text)
            return rules.interpret(request)

        def __getattr__(self, name: str) -> Any:
            return getattr(rules, name)

    monkeypatch.setattr(guard, "_RULES", Counted())
    wanted = "want a park and a station and cafes and restaurants and pubs and culture"
    text = f"I'm tired of the city and {wanted}"

    response = client.post("/v1/interpret", json={"text": text, "ask_model": False})

    found = response.json()["data"]["suggestions"]
    assert len(found) == 6 and all(offer["add_all"] == "more" for offer in found)
    # Six things stand in what is said, and the rules read it once for all of them.
    assert read == [wanted]


def test_a_part_of_a_sentence_is_read_once_however_many_things_stand_beside_it(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    rules = guard._RULES  # pyright: ignore[reportPrivateUsage]
    read: list[str] = []

    class Counted:
        def interpret(self, request: InterpretRequest) -> InterpretResult:
            read.append(request.text)
            return rules.interpret(request)

        def __getattr__(self, name: str) -> Any:
            return getattr(rules, name)

    monkeypatch.setattr(guard, "_RULES", Counted())
    things = ["pubs", "cafes", "restaurants", "a park", "a station", "culture"]
    text = ", ".join([*things, "QuorvexMib TandleFrosk"])

    response = client.post("/v1/interpret", json={"text": text, "ask_model": False})

    assert response.status_code == 200 and len(response.json()["data"]["suggestions"]) == 6
    # Each part is read once: as what is said of its thing, and as what stands beside
    # the five others.
    assert sorted(read) == sorted([*things, "QuorvexMib TandleFrosk"])


def test_a_name_said_sixty_times_is_offered_as_it_was(client: TestClient):
    text = over_and_over("1h of QH1 ")

    response = client.post("/v1/interpret", json={"text": text, "ask_model": False})

    found = response.json()["data"]
    assert (found["status"], found["applied"]) == ("suggest", [])
    [journey] = found["suggestions"]
    assert journey["target"] == "commute"
    assert len(journey["spans"]) == 60
    assert [text[span["start"] : span["end"]] for span in journey["spans"]] == ["1h of QH1"] * 60


def test_the_clause_of_an_offer_is_read_once_however_many_places_it_points_at(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    rules = guard._RULES  # pyright: ignore[reportPrivateUsage]
    read: list[str] = []

    class Counted:
        def interpret(self, request: InterpretRequest) -> InterpretResult:
            read.append(request.text)
            return rules.interpret(request)

        def __getattr__(self, name: str) -> Any:
            return getattr(rules, name)

    monkeypatch.setattr(guard, "_RULES", Counted())
    text = over_and_over("1h of QH1 ")

    response = client.post("/v1/interpret", json={"text": text, "ask_model": False})

    assert response.status_code == 200
    assert read == [text]
