"""Sending a link: one small interface, and its two kinds.

No test here reaches a company that sends mail. Each sender is given a function that
answers in the company's place, as each adapter of a model is.
"""

import io
import json
import re
from typing import Any

import pytest
from burro_api.accounts.sender import (
    COMPANIES,
    LINK_LASTS_MINUTES,
    SUBJECT,
    Console,
    OverHttps,
    SendFailed,
    letter,
)
from burro_api.accounts.settings import SenderName
from burro_api.providers.base import Key, Request, Response
from burro_api.providers.interface import ModelError, ModelTimeout

from ..support import CANARY, assert_nothing_follows

KEY_TEXT = f"a-made-up-key-{CANARY}"
TO = "marmalade.quokka@example.org"
FROM = "sign-in@burro.example"
LINK = "https://burro.example/sign-in/confirm#t=" + "t" * 43
each = pytest.mark.parametrize("name", sorted(COMPANIES), ids=str)


class Answers:
    """Stands in for the company. It keeps what it was sent, and answers as it was told to."""

    def __init__(self, answer: Response | Exception) -> None:
        self.answer = answer
        self.sent: list[tuple[Request, float]] = []

    def __call__(self, request: Request, timeout_s: float) -> Response:
        self.sent.append((request, timeout_s))
        if isinstance(self.answer, Exception):
            raise self.answer
        return self.answer


def sender(name: SenderName, send: Answers) -> OverHttps:
    return OverHttps(COMPANIES[name], Key(KEY_TEXT), FROM, send=send)


# The letter.


def test_the_letter_holds_the_link_once_and_says_how_long_it_lasts():
    said = letter(LINK)

    assert said.count(LINK) == 1 and f"{LINK_LASTS_MINUTES} minutes" in said
    assert LINK_LASTS_MINUTES == 15
    # The link stands on a line of its own, so that nothing beside it is taken for part of it.
    assert f"\n{LINK}\n" in said


def test_the_letter_is_written_for_a_person_who_has_never_seen_burro():
    said = letter(LINK).replace(LINK, "")

    assert "!" not in said and "!" not in SUBJECT
    # It says what to do where the person did not ask, and asks them to pass it to nobody.
    assert "did not ask" in said and "ignore" in said
    assert re.search(r"do not (?:pass|forward)", said)
    for word in ("token", "session", "cookie", "spec", "release", "route", "click here"):
        assert word not in said.casefold(), word
    # Whole sentences: each line that says something ends as a sentence does.
    lines = [line for line in said.splitlines() if line.strip() and line.strip() != "Burro"]
    assert all(line.rstrip().endswith((".", ":", ",")) for line in lines), lines


def test_the_letter_is_plain_text_and_the_same_for_everybody():
    assert letter(LINK) == letter(LINK)
    assert "<" not in letter(LINK) and TO not in letter(LINK)


# Over HTTPS.


@each
def test_a_link_is_sent_once_to_the_company_that_is_named(name: SenderName):
    company = COMPANIES[name]
    send = Answers(Response(200))

    sender(name, send).send(TO, LINK)

    [(request, timeout_s)] = send.sent
    assert (request.host, request.path) == (company.host, company.path)
    assert 0 < timeout_s <= 10
    # Its own host and its own path, which are written in the code and are no setting.
    assert re.fullmatch(r"[a-z0-9.-]+\.[a-z]+", request.host) and request.path.startswith("/")
    sent: dict[str, Any] = json.loads(request.body)
    written = json.dumps(sent)
    assert TO in written and FROM in written and SUBJECT in written
    assert LINK in written.replace("\\n", "\n")
    assert KEY_TEXT not in written and KEY_TEXT not in repr(request)


@each
def test_the_key_goes_in_one_header_and_shows_in_nothing(name: SenderName):
    send = Answers(Response(200))
    made = sender(name, send)

    made.send(TO, LINK)

    [(request, _)] = send.sent
    assert request.key.for_header() == KEY_TEXT
    assert request.key_header == COMPANIES[name].key_header
    assert KEY_TEXT not in repr(made) and CANARY not in repr(vars(made))
    assert KEY_TEXT not in json.dumps(dict(request.headers)) and KEY_TEXT not in str(request.body)


@each
def test_nothing_the_company_answers_is_read(name: SenderName):
    # The body of a refusal can repeat the address it refuses. None is asked for.
    send = Answers(Response(200))

    sender(name, send).send(TO, LINK)

    [(request, _)] = send.sent
    assert request.wants == frozenset()


def test_a_letter_is_not_followed_and_is_not_opened_for_the_sender():
    # A company that follows a link puts an address of its own in the place of Burro's,
    # and what stands after the `#` of the link is then lost, or is sent to that company.
    send = Answers(Response(200))

    sender(SenderName.POSTMARK, send).send(TO, LINK)

    [(request, _)] = send.sent
    sent: dict[str, Any] = json.loads(request.body)
    assert (sent["TrackLinks"], sent["TrackOpens"]) == ("None", False)
    assert "HtmlBody" not in sent and sent["TextBody"] == letter(LINK)


@each
@pytest.mark.parametrize("status", [200, 201, 202])
def test_a_letter_that_was_taken_is_sent(name: SenderName, status: int):
    sender(name, Answers(Response(status))).send(TO, LINK)


@each
@pytest.mark.parametrize("status", [401, 403, 408, 429, 500, 502, 503, 504, 301, 302])
def test_a_company_that_cannot_be_used_fails_for_every_address_alike(name: SenderName, status: int):
    with pytest.raises(SendFailed) as failed:
        sender(name, Answers(Response(status))).send(TO, LINK)

    assert failed.value.reached is False


@each
@pytest.mark.parametrize("status", [400, 404, 406, 409, 413, 422])
def test_a_letter_the_company_will_not_take_may_be_about_the_address(name: SenderName, status: int):
    with pytest.raises(SendFailed) as failed:
        sender(name, Answers(Response(status))).send(TO, LINK)

    assert failed.value.reached is True


@each
@pytest.mark.parametrize(
    "failure", [ModelTimeout(), ModelError(), ValueError(f"{TO} {KEY_TEXT}"), OSError(TO)]
)
def test_whatever_goes_wrong_underneath_leaves_as_a_failure_that_holds_nothing(
    name: SenderName, failure: Exception
):
    with pytest.raises(SendFailed) as failed:
        sender(name, Answers(failure)).send(TO, LINK)

    assert failed.value.reached is False
    assert str(failed.value) == "" and failed.value.args == ()
    assert_nothing_follows(failed.value)
    assert TO not in repr(failed.value) and CANARY not in repr(failed.value)


@each
def test_what_is_sent_is_one_document_whatever_the_address_holds(name: SenderName):
    send = Answers(Response(200))
    odd = 'o\'brien+{"x"}@example.org'

    sender(name, send).send(odd, LINK)

    [(request, _)] = send.sent
    sent: dict[str, Any] = json.loads(request.body)
    assert odd in json.dumps(sent, ensure_ascii=False).replace('\\"', '"')
    assert set(sent) == set(json.loads(send.sent[0][0].body))


def test_the_companies_are_a_closed_list_and_the_console_is_none_of_them():
    assert set(COMPANIES) == {SenderName.POSTMARK, SenderName.RESEND}
    assert {name.value for name in SenderName} == {"console", "postmark", "resend"}
    for company in COMPANIES.values():
        assert company.host.islower() and "://" not in company.host


# For development.


def test_the_sender_for_development_writes_the_link_to_the_console_and_sends_nothing():
    out = io.StringIO()

    Console(out).send(TO, LINK)

    written = out.getvalue()
    assert LINK in written and TO in written
    assert written.endswith("\n") and "development" in written


def test_the_sender_for_development_writes_no_line_of_the_log(capsys: pytest.CaptureFixture[str]):
    Console().send(TO, LINK)

    out, err = capsys.readouterr()
    # The log is what is written to standard output, one JSON object a line.
    assert out == "" and LINK in err
