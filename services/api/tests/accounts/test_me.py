"""What a person who has signed in can do, and that nobody can do it to anybody else.

Whose rows are read and written is decided by the session, at the service, and never
by anything a request says.
"""

import json
import re
import sqlite3
from pathlib import Path
from typing import Any

import pytest
from burro_api.accounts.service import MOST_RECENT, MOST_SEARCHES
from burro_api.accounts.settings import KeepRecent
from burro_api.errors import MESSAGES
from burro_api.wire import ErrorCode
from burro_core import default_spec
from burro_core.ids import Tenure
from burro_core.spec import PreferenceSpec

from ..support import (
    CANARY,
    SCHOOL,
    WORKS,
    budget,
    commute,
    make_deps,
    release,
    renter,
    searching,
    wire,
)
from .support import Browser, On, code, data, turned_on
from .test_off import routes
from .test_sessions import signed_in

EMAIL = "marmalade.quokka@example.org"
NOT_SIGNED_IN = (401, "not_signed_in")
ID = r"[A-Za-z0-9_-]{22}"
POUND = "\N{POUND SIGN}"


def search(number: int = 0) -> PreferenceSpec:
    """A search that is unlike every other of its kind: by its budget."""
    return searching(budget=budget(1_000 + 25 * number, hard=True))


def keeping(browser: Browser, spec: PreferenceSpec) -> dict[str, Any]:
    return data(browser.post("/v1/me/searches", {"spec": wire(spec)}))


def person(on: On, number: int) -> Browser:
    return signed_in(on, f"p{number}@example.org", address=f"203.0.113.{number + 20}")


# Nobody who is not signed in.


@pytest.mark.parametrize(("method", "path"), [each for each in routes() if "/v1/me" in each[1]])
def test_nothing_of_an_account_is_asked_for_by_somebody_who_is_not_signed_in(
    tmp_path: Path, method: str, path: str
):
    on = turned_on(tmp_path)
    signed_in(on)
    before = on.held()
    sent = {"spec": wire(search()), "search_id": "a" * 22, "everywhere": True, "keep_recent": "on"}

    for nobody in (Browser(on), Browser(on)):
        nobody.cookies["__Host-burro_session"] = "s" * 43 if nobody.cookies else ""
        refused = nobody.ask(method, path, sent)
        assert code(refused) == NOT_SIGNED_IN
        assert refused.json()["error"]["message"] == (
            "You are not signed in, so please sign in and try again."
        )
        assert EMAIL not in refused.text

    assert on.held() == before


# Keeping a search.


def test_a_search_is_kept_as_what_burro_understood_and_named_from_it(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = signed_in(on)
    spec = searching(budget=budget(1_700, hard=True), commutes=(commute(WORKS, 35),))
    on.later(minutes=3)

    kept = keeping(browser, spec)

    assert re.fullmatch(ID, kept.pop("search_id"))
    assert kept == {
        "name": (
            f"Renting a 1-bedroom home, up to {POUND}1,700 a month, "
            "about 35 minutes to Cindermoor Works by public transport"
        ),
        "spec": wire(spec),
        "release_id": "syn-2026-09-23-01",
        "kept_at": "2026-09-23T12:03:00Z",
        "state": "ok",
    }
    [(held, release_id, name)] = on.rows("SELECT spec, release_id, name FROM saved_searches")
    assert PreferenceSpec.model_validate_json(held) == spec
    assert (release_id, name) == ("syn-2026-09-23-01", kept["name"])


def test_a_search_that_is_a_visit_is_kept_named_and_shown_again(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = signed_in(on)
    visit = default_spec(Tenure.VISIT).replace(commutes=(commute(WORKS, 20),))
    ranked = on.client.post("/v1/rank", json={"spec": wire(visit)})
    assert ranked.status_code == 200

    kept = keeping(browser, visit)
    browser.put("/v1/me/preferences", {"keep_recent": "on"})
    last = data(browser.post("/v1/me/recent", {"spec": wire(visit)}))

    name = "Visiting, about 20 minutes to Cindermoor Works by public transport"
    assert (kept["name"], kept["state"], kept["spec"]) == (name, "ok", wire(visit))
    # A visit holds no budget and no kind of home, kept as it was ranked.
    assert kept["spec"]["tenure"] == "visit" and kept["spec"]["budget"]["amount"] is None
    [shown] = data(browser.get("/v1/me/searches"))["searches"]
    assert shown == kept
    assert last["kept"] is True and [each["name"] for each in last["searches"]] == [name]
    [found] = data(browser.get("/v1/me/export"))["searches"]
    assert found["name"] == name


def test_what_is_kept_holds_no_word_that_anybody_typed(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = signed_in(on)
    typed = f"Renting a 1 bed up to {POUND}1,700 a month, leafy, 35 minutes to Cindermoor Works"
    read = on.client.post("/v1/interpret", json={"text": f"{typed}. I work at {CANARY}"})
    found = on.client.post("/v1/interpret", json={"text": typed}).json()["data"]["spec"]
    assert read.status_code == 200

    kept = data(browser.post("/v1/me/searches", {"spec": found}))

    # A body has no field for what was typed, and a spec holds ids and numbers.
    assert code(browser.post("/v1/me/searches", {"spec": found, "text": typed}))[0] == 422
    assert code(browser.post("/v1/me/searches", {"spec": found, "name": CANARY}))[0] == 422
    assert "leafy" not in kept["name"] and "Leafy" in kept["name"]
    written = on.written().decode("latin-1")
    assert CANARY not in written and "I work at" not in written and "1 bed up to" not in written


def test_the_searches_a_person_kept_are_listed_the_newest_first(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = signed_in(on)
    for number in range(3):
        on.later(minutes=1)
        keeping(browser, search(number))

    found = data(browser.get("/v1/me/searches"))

    assert found["most"] == MOST_SEARCHES == 100
    assert [each["spec"]["budget"]["amount"] for each in found["searches"]] == [1050, 1025, 1000]
    assert [each["kept_at"][14:16] for each in found["searches"]] == ["03", "02", "01"]


def test_the_same_search_is_kept_once_however_often_it_is_pressed(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = signed_in(on)

    first = keeping(browser, search())
    on.later(minutes=5)
    again = keeping(browser, search())

    assert again == first
    assert len(data(browser.get("/v1/me/searches"))["searches"]) == 1


def test_a_hundred_searches_are_kept_at_the_most(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = signed_in(on)
    for number in range(MOST_SEARCHES):
        keeping(browser, search(number))

    refused = browser.post("/v1/me/searches", {"spec": wire(search(MOST_SEARCHES))})

    assert code(refused) == (409, "too_many_searches")
    assert len(on.rows("SELECT * FROM saved_searches")) == MOST_SEARCHES
    # One that is kept already is still answered, and one that is taken away makes room.
    assert keeping(browser, search(7))["state"] == "ok"
    taken = data(browser.get("/v1/me/searches"))["searches"][0]["search_id"]
    assert browser.delete("/v1/me/searches", {"search_id": taken}).status_code == 200
    assert keeping(browser, search(MOST_SEARCHES))["state"] == "ok"


def test_a_search_is_taken_away_and_those_that_are_left_are_given_back(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = signed_in(on)
    first, second = keeping(browser, search(1)), keeping(browser, search(2))

    left = data(browser.delete("/v1/me/searches", {"search_id": first["search_id"]}))

    assert [each["search_id"] for each in left["searches"]] == [second["search_id"]]
    again = browser.delete("/v1/me/searches", {"search_id": first["search_id"]})
    assert code(again) == (404, "search_not_found")


def test_a_refusal_says_of_a_search_what_the_website_says_of_it(tmp_path: Path):
    # The website shows a refusal as it came, under words of its own: "Save this search",
    # "Saved searches", "Remove". It says "keep" of another thing, the last searches.
    browser = signed_in(turned_on(tmp_path))
    gone = browser.delete("/v1/me/searches", {"search_id": "A" * 22})
    assert code(gone) == (404, "search_not_found")
    assert gone.json()["error"]["message"] == MESSAGES[ErrorCode.SEARCH_NOT_FOUND]

    full = MESSAGES[ErrorCode.TOO_MANY_SEARCHES]
    for said in (full, MESSAGES[ErrorCode.SEARCH_NOT_FOUND]):
        assert re.search(r"\bsaved\b", said), said
        assert not re.search(r"\b(?:keep|kept|take|taken)\b", said, re.IGNORECASE), said
    assert f"saved {MOST_SEARCHES} searches" in full
    assert "Remove one and you can save this one." in full


@pytest.mark.parametrize(
    "spec",
    [
        {"schema_version": 1},
        {"schema_version": 2},
        "a search",
        None,
        [],
        {"text": f"leafy {CANARY}"},
    ],
)
def test_a_search_is_checked_by_the_schema_the_ranking_uses_before_it_is_kept(
    tmp_path: Path, spec: Any
):
    on = turned_on(tmp_path)
    browser = signed_in(on)

    for path in ("/v1/me/searches", "/v1/me/recent"):
        refused = browser.post(path, {"spec": spec})
        assert refused.status_code == 422 and CANARY not in refused.text
        assert refused.json()["error"]["code"] in ("invalid_spec", "invalid_request")

    assert not on.rows("SELECT * FROM saved_searches") and not on.rows(
        "SELECT * FROM recent_searches"
    )


def test_a_search_that_names_what_the_data_does_not_hold_is_not_kept(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = signed_in(on)
    gone = wire(renter(commutes=(commute("syn-p9999", 30),)))
    ranked = on.client.post("/v1/rank", json={"spec": gone})

    refused = browser.post("/v1/me/searches", {"spec": gone})

    # As the ranking refuses it, with the same code and the same place in the search.
    assert code(refused) == code(ranked) == (422, "unknown_place")
    assert refused.json()["error"]["fields"] == ranked.json()["error"]["fields"]
    assert not on.rows("SELECT * FROM saved_searches")


def test_a_search_is_checked_again_when_it_is_read(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = signed_in(on)
    kept = keeping(browser, search())
    probe = sqlite3.connect(on.database)
    changed = json.dumps(wire(search()) | {"tenure": f"own {CANARY}"})
    probe.execute("UPDATE saved_searches SET spec = ?", (changed,))
    probe.execute("UPDATE recent_searches SET spec = ?", ("{not a search",))
    probe.commit()
    probe.close()

    [found] = data(browser.get("/v1/me/searches"))["searches"]
    exported = browser.get("/v1/me/export")

    # What can no longer be read as a search is said to be so, and none of it is served.
    assert found == kept | {"spec": None, "state": "unreadable"}
    assert CANARY not in exported.text and data(exported)["searches"] == [found]
    # And it can still be taken away.
    assert browser.delete("/v1/me/searches", {"search_id": kept["search_id"]}).status_code == 200


def test_a_search_kept_on_other_data_says_whether_it_can_be_searched_now(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = signed_in(on)
    kept = keeping(browser, searching(commutes=(commute(SCHOOL, 25),)))
    probe = sqlite3.connect(on.database)
    moved = json.dumps(wire(searching(commutes=(commute("syn-p9999", 25),))))
    probe.execute(
        "UPDATE saved_searches SET spec = ?, release_id = ?", (moved, "syn-2026-01-01-01")
    )
    probe.commit()
    probe.close()

    [found] = data(browser.get("/v1/me/searches"))["searches"]

    # The search is served, as the person kept it, and is said not to stand on the data
    # as it is now: it names a place that is no longer there.
    assert found["state"] == "release_changed" and found["release_id"] == "syn-2026-01-01-01"
    assert found["spec"]["commutes"][0]["place_id"] == "syn-p9999"
    assert found["name"] == kept["name"]


# The last searches, built two ways.


def test_the_last_searches_are_kept_only_once_a_person_turns_it_on(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = signed_in(on)
    nothing: dict[str, Any] = {"kept": False, "searches": [], "most": MOST_RECENT}

    assert data(browser.get("/v1/me"))["preferences"] == {"keep_recent": "off"}
    assert data(browser.post("/v1/me/recent", {"spec": wire(search())})) == nothing
    assert data(browser.get("/v1/me/recent")) == nothing
    assert not on.rows("SELECT * FROM recent_searches")

    assert data(browser.put("/v1/me/preferences", {"keep_recent": "on"})) == {"keep_recent": "on"}
    found = data(browser.post("/v1/me/recent", {"spec": wire(search())}))

    assert found["kept"] is True and [each["spec"] for each in found["searches"]] == [
        wire(search())
    ]
    assert data(browser.get("/v1/me"))["preferences"] == {"keep_recent": "on"}


def test_the_other_way_the_last_searches_are_kept_from_the_start(tmp_path: Path):
    on = turned_on(tmp_path, keep_recent=KeepRecent.FROM_THE_START)
    browser = signed_in(on)

    assert data(browser.get("/v1/me"))["preferences"] == {"keep_recent": "on"}
    found = data(browser.post("/v1/me/recent", {"spec": wire(search())}))

    assert found["kept"] is True and len(found["searches"]) == 1
    # Nobody chose, so no row says they did.
    assert not on.rows("SELECT * FROM preferences")
    # And a person who turns it off is kept to that, whatever the service is set to.
    assert data(browser.put("/v1/me/preferences", {"keep_recent": "off"})) == {"keep_recent": "off"}
    assert data(browser.post("/v1/me/recent", {"spec": wire(search())}))["kept"] is False


def test_the_last_ten_are_kept_and_the_oldest_goes(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = signed_in(on)
    browser.put("/v1/me/preferences", {"keep_recent": "on"})

    for number in range(13):
        on.later(seconds=30)
        browser.post("/v1/me/recent", {"spec": wire(search(number))})

    found = data(browser.get("/v1/me/recent"))
    amounts = [each["spec"]["budget"]["amount"] for each in found["searches"]]
    assert amounts == [1_000 + 25 * number for number in range(12, 2, -1)]
    assert len(on.rows("SELECT * FROM recent_searches")) == MOST_RECENT == 10


def test_a_search_that_is_made_again_comes_to_the_top_and_is_held_once(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = signed_in(on)
    browser.put("/v1/me/preferences", {"keep_recent": "on"})
    for number in (1, 2, 3):
        on.later(seconds=30)
        browser.post("/v1/me/recent", {"spec": wire(search(number))})

    on.later(seconds=30)
    found = data(browser.post("/v1/me/recent", {"spec": wire(search(1))}))

    amounts = [each["spec"]["budget"]["amount"] for each in found["searches"]]
    assert amounts == [1025, 1075, 1050]


def test_turning_it_off_takes_away_what_was_kept(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = signed_in(on)
    browser.put("/v1/me/preferences", {"keep_recent": "on"})
    browser.post("/v1/me/recent", {"spec": wire(search())})
    kept = keeping(browser, search(5))
    assert b"1000" in on.written()

    browser.put("/v1/me/preferences", {"keep_recent": "off"})

    assert not on.rows("SELECT * FROM recent_searches")
    assert data(browser.get("/v1/me/recent")) == {"kept": False, "searches": [], "most": 10}
    # What a person chose to keep is another thing, and is as it was.
    assert [e["search_id"] for e in data(browser.get("/v1/me/searches"))["searches"]] == [
        kept["search_id"]
    ]


def test_a_person_takes_their_last_searches_away_and_may_go_on_keeping_them(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = signed_in(on)
    browser.put("/v1/me/preferences", {"keep_recent": "on"})
    browser.post("/v1/me/recent", {"spec": wire(search())})

    left = data(browser.delete("/v1/me/recent"))

    assert left == {"kept": True, "searches": [], "most": 10}
    assert not on.rows("SELECT * FROM recent_searches")


# What a person takes away.


def beside(on: On) -> bytes:
    """Every byte of the file and of what is written beside it, which hold where a search leads."""
    written = on.written()
    assert SCHOOL.encode() in written
    return written


def to_the_school(number: int = 0) -> PreferenceSpec:
    return searching(budget=budget(2_000 + number), commutes=(commute(SCHOOL, 25),))


def test_a_search_that_is_taken_away_is_gone_from_the_file_and_from_beside_it(tmp_path: Path):
    on = turned_on(tmp_path)
    browser, other = signed_in(on), person(on, 1)
    kept = keeping(browser, to_the_school())
    theirs = keeping(other, search(9))
    assert kept["name"].encode() in beside(on)

    assert browser.delete("/v1/me/searches", {"search_id": kept["search_id"]}).status_code == 200

    # Gone from the bytes, and not only from the tables: where the search said somebody
    # goes, and the name that says it in words.
    written = on.written()
    assert SCHOOL.encode() not in written and kept["name"].encode() not in written
    assert kept["search_id"].encode() not in written
    # What somebody else keeps is as it was.
    assert data(other.get("/v1/me/searches"))["searches"] == [theirs]


def test_last_searches_that_are_taken_away_are_gone_from_the_file_and_from_beside_it(
    tmp_path: Path,
):
    on = turned_on(tmp_path)
    browser = signed_in(on)
    browser.put("/v1/me/preferences", {"keep_recent": "on"})
    browser.post("/v1/me/recent", {"spec": wire(to_the_school())})
    beside(on)

    assert browser.delete("/v1/me/recent").status_code == 200

    assert SCHOOL.encode() not in on.written()


def test_turning_it_off_takes_what_was_kept_out_of_the_file_and_from_beside_it(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = signed_in(on)
    browser.put("/v1/me/preferences", {"keep_recent": "on"})
    browser.post("/v1/me/recent", {"spec": wire(to_the_school())})
    beside(on)

    assert browser.put("/v1/me/preferences", {"keep_recent": "off"}).status_code == 200

    assert SCHOOL.encode() not in on.written()


def test_the_oldest_of_the_last_searches_is_gone_from_the_file_as_it_goes(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = signed_in(on)
    browser.put("/v1/me/preferences", {"keep_recent": "on"})
    browser.post("/v1/me/recent", {"spec": wire(to_the_school())})
    beside(on)

    for number in range(MOST_RECENT):
        on.later(seconds=30)
        browser.post("/v1/me/recent", {"spec": wire(search(number))})

    # The eleventh search pushed the first out, and it is in no byte that is left.
    assert len(on.rows("SELECT * FROM recent_searches")) == MOST_RECENT
    assert SCHOOL.encode() not in on.written()


# Preferences.


@pytest.mark.parametrize(
    "sent",
    [
        {"keep_recent": "yes"},
        {"keep_recent": True},
        {"keep_recent": 1},
        {"keep_recent": "ON"},
        {"theme": "dark"},
        {"keep_recent": "on", "theme": "dark"},
        {"key": "keep_recent", "value": "on"},
        {CANARY: "on"},
    ],
)
def test_a_preference_is_a_key_from_a_closed_list_with_a_value_checked_for_it(
    tmp_path: Path, sent: dict[str, Any]
):
    on = turned_on(tmp_path)
    browser = signed_in(on)

    refused = browser.put("/v1/me/preferences", sent)

    assert code(refused) == (422, "invalid_request")
    assert CANARY not in refused.text and not on.rows("SELECT * FROM preferences")


def test_a_preference_that_is_left_out_stays_as_it_was(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = signed_in(on)
    browser.put("/v1/me/preferences", {"keep_recent": "on"})

    for sent in ({}, {"keep_recent": None}):
        assert data(browser.put("/v1/me/preferences", sent)) == {"keep_recent": "on"}

    assert on.rows("SELECT key, value FROM preferences") == [("keep_recent", "on")]


# Everything Burro holds.


def test_a_person_is_given_everything_burro_holds_of_them(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = signed_in(on)
    browser.put("/v1/me/preferences", {"keep_recent": "on"})
    on.later(minutes=2)
    kept = keeping(browser, search(1))
    browser.post("/v1/me/recent", {"spec": wire(search(2))})
    unused = Browser(on, address="203.0.113.99").ask_for_link(EMAIL)

    found = data(browser.get("/v1/me/export"))

    assert set(found) == {
        "exported_at",
        "email",
        "made_at",
        "adult_at",
        "preferences",
        "searches",
        "recent",
        "sessions",
        "events",
        "links",
    }
    assert (found["email"], found["made_at"], found["adult_at"]) == (
        EMAIL,
        "2026-09-23T12:00:00Z",
        "2026-09-23T12:00:00Z",
    )
    assert found["exported_at"] == "2026-09-23T12:02:00Z"
    assert found["preferences"] == {"keep_recent": "on"}
    assert found["searches"] == [kept] and len(found["recent"]) == 1
    [session] = found["sessions"]
    assert (session["browser"], session["current"], session["revoked"]) == ("firefox", True, False)
    # What happened to the account, the newest first, in words of two closed lists.
    assert [(each["event"], each["outcome"]) for each in found["events"]] == [
        ("session_created", "ok"),
        ("link_used", "ok"),
    ]
    # And the links that were asked for its address, for as long as Burro holds them.
    assert found["links"] == [
        {"asked_at": "2026-09-23T12:00:00Z", "ends_at": "2026-09-23T12:15:00Z", "used": True},
        {"asked_at": "2026-09-23T12:02:00Z", "ends_at": "2026-09-23T12:17:00Z", "used": False},
    ]
    # Nothing in it opens anything: no session, no token and no hash of either.
    served = browser.get("/v1/me/export").text
    for secret in (browser.cookies["__Host-burro_session"], unused):
        assert secret not in served
    assert not re.search(r"[0-9a-f]{64}", served)


def test_every_row_the_file_holds_of_an_account_is_in_what_the_person_is_given(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = signed_in(on)
    browser.put("/v1/me/preferences", {"keep_recent": "on"})
    for number in range(3):
        keeping(browser, search(number))
        browser.post("/v1/me/recent", {"spec": wire(search(number))})
    signed_in(on)

    found = data(browser.get("/v1/me/export"))
    held = on.held()

    assert len(found["searches"]) == len(held["saved_searches"]) == 3
    assert len(found["recent"]) == len(held["recent_searches"]) == 3
    assert len(found["sessions"]) == len(held["sessions"]) == 2
    assert len(found["events"]) == len(held["audit_events"])
    assert len(found["links"]) == len(held["login_tokens"]) == 2
    assert len(held["preferences"]) == 1 and len(held["accounts"]) == 1


def test_a_link_that_has_ended_cannot_be_shown_until_nothing_else_is_kept(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = signed_in(on)
    [(used,)] = on.rows("SELECT token_hash FROM login_tokens")
    token = on.post.token()
    assert used and on.rows("SELECT count(*) FROM audit_events") == [(2,)]

    # Whoever holds a link that was used shows it, from one client after another.
    for number in range(60):
        other = Browser(on, address=f"198.51.100.{number % 250 + 1}")
        refused = other.post("/v1/auth/session", {"token": token, "other_browser": True})
        assert code(refused) == (410, "link_used")

    # What is kept of the account is what it was: that somebody signed in, and when.
    found = data(browser.get("/v1/me/export"))["events"]
    assert [(each["event"], each["outcome"]) for each in found] == [
        ("session_created", "ok"),
        ("link_used", "ok"),
    ]


# Deleting the account.


def test_an_account_is_deleted_with_everything_of_it_in_the_file_and_beside_it(tmp_path: Path):
    on = turned_on(tmp_path)
    browser, other = signed_in(on), person(on, 1)
    browser.put("/v1/me/preferences", {"keep_recent": "on"})
    keeping(browser, searching(commutes=(commute(SCHOOL, 25),)))
    browser.post("/v1/me/recent", {"spec": wire(searching(commutes=(commute(SCHOOL, 25),)))})
    theirs = keeping(other, search(9))
    session = browser.cookies["__Host-burro_session"]
    assert b"marmalade.quokka" in on.written() and SCHOOL.encode() in on.written()
    on.later(minutes=9)

    answered = browser.delete("/v1/me")

    assert data(answered) == {"signed_in": False, "email": None}
    assert not browser.cookies and "Max-Age=0" in browser.given[0]
    held = on.held()
    assert [row[1] for row in held["accounts"]] == ["p1@example.org"]
    assert [len(rows) for rows in held.values()] == [1, 1, 1, 1, 0, 0, 2]
    # Gone from the bytes of the file, and not only from its tables: the address, and
    # where the search said somebody goes.
    assert b"marmalade.quokka" not in on.written() and SCHOOL.encode() not in on.written()
    # The session opens nothing, and the account of somebody else is as it was.
    gone = Browser(on)
    gone.cookies["__Host-burro_session"] = session
    assert code(gone.get("/v1/me")) == NOT_SIGNED_IN
    assert data(other.get("/v1/me/searches"))["searches"] == [theirs]


def test_deleting_asks_for_a_sign_in_in_the_last_ten_minutes(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = signed_in(on)
    on.later(minutes=10)

    assert data(browser.get("/v1/me"))["fresh"] is False
    refused = browser.delete("/v1/me")

    assert code(refused) == (403, "sign_in_again")
    assert refused.json()["error"]["message"].startswith("Please sign in again before you delete")
    assert len(on.rows("SELECT * FROM accounts")) == 1 and browser.cookies
    # Signed in again, the person may.
    browser.sign_in(EMAIL)
    assert data(browser.get("/v1/me"))["fresh"] is True
    assert browser.delete("/v1/me").status_code == 200
    assert not on.rows("SELECT * FROM accounts")


def test_putting_a_session_forward_does_not_make_it_a_fresh_sign_in(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = signed_in(on)
    on.later(days=2)
    assert browser.get("/v1/me").status_code == 200 and browser.given

    assert code(browser.delete("/v1/me")) == (403, "sign_in_again")


def test_an_address_that_was_deleted_signs_in_as_a_new_account(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = signed_in(on)
    keeping(browser, search())
    browser.delete("/v1/me")
    on.later(minutes=1)

    again = browser.sign_in(EMAIL)

    assert data(again) == {"email": EMAIL, "new_account": True}
    assert data(browser.get("/v1/me/searches"))["searches"] == []


# Nobody else's.


def test_no_route_ever_returns_a_row_of_another_account(tmp_path: Path):
    on = turned_on(tmp_path)
    people = [person(on, number) for number in range(8)]
    kept: list[list[str]] = []
    for number, browser in enumerate(people):
        browser.put("/v1/me/preferences", {"keep_recent": "on"})
        mine = [keeping(browser, search(10 * number + n))["search_id"] for n in range(3)]
        for n in range(3):
            browser.post("/v1/me/recent", {"spec": wire(search(10 * number + n))})
        kept.append(mine)

    for number, browser in enumerate(people):
        own = {f"p{number}@example.org", *kept[number]}
        amounts = {1_000 + 25 * (10 * number + n) for n in range(3)}
        for path in (
            "/v1/me",
            "/v1/me/searches",
            "/v1/me/recent",
            "/v1/me/sessions",
            "/v1/me/export",
            "/v1/auth/session",
        ):
            served = browser.get(path).text
            # Its own address and its own searches, where the route serves them...
            if path in ("/v1/me", "/v1/me/export", "/v1/auth/session"):
                assert f"p{number}@example.org" in served
            found = {int(each) for each in re.findall(r'"amount":(\d+)', served)}
            assert found <= amounts, path
            # ...and never an address, an id or a search of anybody else's.
            for other in range(len(people)):
                if other == number:
                    continue
                assert f"p{other}@example.org" not in served, path
                assert not [each for each in kept[other] if each in served], path
        assert own


def test_an_id_that_is_guessed_or_is_somebody_elses_gives_nothing(tmp_path: Path):
    on = turned_on(tmp_path)
    people = [person(on, number) for number in range(6)]
    searches = [
        keeping(browser, search(number))["search_id"] for number, browser in enumerate(people)
    ]
    sessions = [
        data(browser.get("/v1/me/sessions"))["sessions"][0]["session_id"] for browser in people
    ]
    before = on.held()
    guessed = ["a" * 22, "A" * 22, "-" * 22, "0" * 22, searches[0][::-1], sessions[0][::-1]]

    for number, browser in enumerate(people):
        theirs = [each for other, each in enumerate(searches) if other != number]
        for search_id in (*theirs, *guessed, *sessions):
            refused = browser.delete("/v1/me/searches", {"search_id": search_id})
            assert code(refused) == (404, "search_not_found")
        others = [each for other, each in enumerate(sessions) if other != number]
        for session_id in (*others, *guessed, *searches):
            refused = browser.delete("/v1/me/sessions", {"session_id": session_id})
            assert code(refused) == (404, "session_not_found")

    # Not a row of anybody's is other than it was, and everybody is still signed in.
    assert on.held() == before
    for number, browser in enumerate(people):
        assert data(browser.get("/v1/me"))["email"] == f"p{number}@example.org"


@pytest.mark.parametrize(
    "said",
    [
        {"account_id": "theirs"},
        {"email": "p1@example.org"},
        {"account": "p1@example.org"},
        {"user": "p1@example.org"},
        {"session_id": "theirs"},
    ],
)
def test_whose_rows_are_read_is_never_decided_by_what_a_request_says(
    tmp_path: Path, said: dict[str, str]
):
    on = turned_on(tmp_path)
    mine, theirs = person(on, 0), person(on, 1)
    keeping(theirs, search(1))
    [(their_account,)] = on.rows("SELECT id FROM accounts WHERE email = ?", "p1@example.org")
    [(their_session,)] = on.rows(
        "SELECT public_id FROM sessions WHERE account_id = ?", their_account
    )
    named = {
        name: {"theirs": their_account if name == "account_id" else their_session}.get(value, value)
        for name, value in said.items()
    }

    # Said in a header, and said in a body: neither is a field that anything reads.
    in_a_header = mine.get("/v1/me/searches", {f"x-burro-{n}": v for n, v in named.items()})
    in_a_body = mine.post("/v1/me/searches", {"spec": wire(search(2))} | named)

    assert data(in_a_header)["searches"] == []
    assert in_a_body.status_code == 422
    assert "p1@example.org" not in in_a_header.text + in_a_body.text
    assert len(data(theirs.get("/v1/me/searches"))["searches"]) == 1


def test_a_search_knows_nobody_with_accounts_on_as_with_them_off(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = signed_in(on)
    off = Browser(On(make_deps(), on.accounts, on.post, on.clock, on.database))
    sent = {"spec": wire(search())}
    signed = {"cookie": f"__Host-burro_session={browser.cookies['__Host-burro_session']}"}

    for path in ("/v1/rank", "/v1/explanations", "/v1/shares"):
        with_a_session = on.client.post(path, json=sent, headers=signed)
        with_none = on.client.post(path, json=sent)
        without_accounts = off.on.client.post(path, json=sent)
        assert with_a_session.status_code == 200
        for answered in (with_a_session, with_none, without_accounts):
            assert "set-cookie" not in answered.headers
        # The same answer to everybody, but for the id of a share, which is random.
        if path != "/v1/shares":
            assert with_a_session.text == with_none.text == without_accounts.text

    # And nothing was kept for it: a search is kept when a person presses, and not before.
    assert not on.rows("SELECT * FROM saved_searches") and not on.rows(
        "SELECT * FROM recent_searches"
    )
    assert release().manifest.release_id == "syn-2026-09-23-01"
