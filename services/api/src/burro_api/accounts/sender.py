"""Sending a link: one small interface, and its two kinds.

One kind sends a letter over HTTPS, by a company that a setting names. The company is
given every address a link is sent to, so which company it is, is the founder's to
choose. Two are fitted, and **neither has been run against its company**: there is no
key to run one with. Each makes one call with the standard library, as the adapter of a
model does, to a host and a path that are written here and are no setting.

The other kind is for development. It writes the link to the console, and is refused
unless the service says it is in development and listens to its own machine alone.

A failure to send carries no message. What goes wrong underneath can hold the address,
the link or the key.
"""

import json
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Protocol, TextIO

from burro_api.accounts.settings import AccountsSettings, SenderName
from burro_api.providers.base import Key, Request, Send, over_https

# How long a link works for. It is said in the letter, and the contract serves it.
LINK_LASTS_MINUTES = 15
# How long a company is waited for, in all.
TIMEOUT_S = 10.0
SENT_BY = "Burro"
SUBJECT = "Your link to sign in to Burro"
# Written for a person who has never seen Burro, in whole sentences that are joined.
# It is plain text, and it is the same for everybody: it names nobody. The link stands
# on a line of its own, so that nothing beside it is taken for a part of it.
PARAGRAPHS = (
    "Hello,",
    "Somebody asked to sign in to Burro with this email address. If that was you, open "
    "this link to carry on:",
    "{link}",
    "The link works once, and only for the next {minutes} minutes. If it has run out by "
    "the time you open it, you can ask for a new one on the page where you sign in.",
    "Before Burro signs you in, it shows the email address the link belongs to and asks "
    "you to confirm, so that you can check it is yours.",
    "If you did not ask for this, you can ignore this email, because nobody can sign in "
    "without the link. For the same reason, please do not pass the link on to anybody.",
    "Burro",
)
LETTER = "\n\n".join(PARAGRAPHS) + "\n"
# A success, whatever the company calls it.
TAKEN = range(200, 300)
# A refusal that is the same for every address: a key that is no longer one, a limit of
# the company's, and whatever is wrong at its end. So is a redirect, which is never
# followed. Any other refusal may be about the address it was asked to send to.
FOR_EVERYBODY = frozenset({401, 403, 408, 429})
ITS_OWN_FAULT = 500
REDIRECTS = range(300, 400)


def letter(link: str) -> str:
    return LETTER.format(link=link, minutes=LINK_LASTS_MINUTES)


class SendFailed(Exception):
    """A link was not sent. It says one thing, and holds nothing of what was to be sent.

    `reached` is true where the company was reached and would not take this letter,
    which may be because of the address. It is false where the company could not be
    used at all, which is the same whatever the address.
    """

    def __init__(self, reached: bool) -> None:
        self.reached = reached
        super().__init__()


class Sender(Protocol):
    def send(self, to: str, link: str) -> None:
        """Send the link to the address, or raise `SendFailed`."""
        ...


Written = Callable[[str, str, str, str], Mapping[str, object]]


def _as_postmark(sent_from: str, to: str, subject: str, text: str) -> Mapping[str, object]:
    return {
        "From": f"{SENT_BY} <{sent_from}>",
        "To": to,
        "Subject": subject,
        "TextBody": text,
        "MessageStream": "outbound",
        # A company that follows a link puts an address of its own in the place of
        # Burro's. What stands after the `#` would then be lost, or be sent to it.
        "TrackLinks": "None",
        "TrackOpens": False,
    }


def _as_resend(sent_from: str, to: str, subject: str, text: str) -> Mapping[str, object]:
    return {"from": f"{SENT_BY} <{sent_from}>", "to": [to], "subject": subject, "text": text}


@dataclass(frozen=True)
class Company:
    """A company that sends mail: where it is asked, and how a letter is written for it."""

    host: str
    path: str
    key_header: str
    key_scheme: str
    written: Written


COMPANIES: Mapping[SenderName, Company] = {
    SenderName.POSTMARK: Company(
        host="api.postmarkapp.com",
        path="/email",
        key_header="X-Postmark-Server-Token",
        key_scheme="",
        written=_as_postmark,
    ),
    SenderName.RESEND: Company(
        host="api.resend.com",
        path="/emails",
        key_header="Authorization",
        key_scheme="Bearer ",
        written=_as_resend,
    ),
}


class OverHttps:
    """Sends a letter by a company, in one call over HTTPS."""

    def __init__(
        self,
        company: Company,
        key: Key,
        sent_from: str,
        send: Send = over_https,
        timeout_s: float = TIMEOUT_S,
    ) -> None:
        self._company = company
        self._key = key
        self._sent_from = sent_from
        self._send = send
        self._timeout_s = timeout_s

    def __repr__(self) -> str:
        return "OverHttps()"

    def _asked(self, to: str, link: str) -> bool | None:
        """Nothing where the letter was taken, and otherwise whether the company was reached.

        It never raises for anything that went wrong.
        """
        try:
            company = self._company
            written = company.written(self._sent_from, to, SUBJECT, letter(link))
            request = Request(
                host=company.host,
                path=company.path,
                key_header=company.key_header,
                key=self._key,
                key_scheme=company.key_scheme,
                body=json.dumps(written, ensure_ascii=False).encode(),
                # The body of no answer is read: a refusal can repeat the address.
                wants=frozenset(),
            )
            status = self._send(request, self._timeout_s).status
        except Exception:
            return False
        if status in TAKEN:
            return None
        return not (status in FOR_EVERYBODY or status in REDIRECTS or status >= ITS_OWN_FAULT)

    def send(self, to: str, link: str) -> None:
        reached = self._asked(to, link)
        # Let go of, so that the failure leaves from a frame that holds neither.
        del to, link
        if reached is not None:
            raise SendFailed(reached)


class Console:
    """Writes the link to the console. For development, on a machine that listens to itself.

    It writes to standard error, and the log is written to standard output: so no line
    of the log holds a link, an address or a token, in development as anywhere.
    """

    def __init__(self, out: TextIO | None = None) -> None:
        self._out = out

    def __repr__(self) -> str:
        return "Console()"

    def send(self, to: str, link: str) -> None:
        out = self._out or sys.stderr
        out.write(f"Burro, in development. A link to sign in as {to}:\n  {link}\n")
        out.flush()


def sender_for(accounts: AccountsSettings, send: Send = over_https) -> Sender | None:
    """The sender that is named, or `None` where none is. The settings were held to their rules."""
    if accounts.sender is None:
        return None
    if accounts.sender is SenderName.CONSOLE:
        if not accounts.development:
            # Text of our own, and nothing that was set.
            raise ValueError("the sender for development is for development")
        return Console()
    if accounts.sender_key is None or accounts.sender_from is None:
        raise ValueError("a company that sends needs its key and an address to send from")
    key = Key(accounts.sender_key.get_secret_value())
    return OverHttps(COMPANIES[accounts.sender], key, accounts.sender_from, send=send)


__all__ = [
    "COMPANIES",
    "LINK_LASTS_MINUTES",
    "SUBJECT",
    "Company",
    "Console",
    "OverHttps",
    "SendFailed",
    "Sender",
    "letter",
    "sender_for",
]
