"""Accounts: who is heard, how a person signs in, and what is kept under an account.

Every rule of signing in is here, in one place, and the routes do no more than hand on
what was sent and serve what comes back.

- **Who is heard.** The website, which shows its secret and says whose request it
  passes on, and nobody else. What changes anything must come from a page of the
  website and say so.
- **Asking for a link** is answered the same whoever asks and whatever the address,
  and does the same work: no account is looked for, and the letter is sent once the
  answer has been given. So how long an answer takes says nothing of an address.
- **A link** works once, for a quarter of an hour. Asking whose it is uses nothing up.
  It is bound to the browser that asked for it, and another browser must say that the
  person was asked a second time.
- **A session** is always made anew, and none is ever taken from a client.
- **Whose rows are read** is decided by the session and by nothing a request says.
"""

from collections import deque
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

from burro_core.release import Release
from burro_core.spec import PreferenceSpec, check_spec
from pydantic import ValidationError
from starlette.datastructures import Headers

from burro_api import logs
from burro_api.accounts import tokens
from burro_api.accounts.addresses import regular
from burro_api.accounts.cookies import Cookies
from burro_api.accounts.events import Event, Outcome
from burro_api.accounts.limits import UNKNOWN, Limiter, NotOne, client_of
from burro_api.accounts.names import name_of
from burro_api.accounts.sender import LINK_LASTS_MINUTES, Sender, SendFailed, sender_for
from burro_api.accounts.settings import AccountsSettings, KeepRecent, held_to
from burro_api.accounts.store import Account, Held, Kept, Link, Signed, Store
from burro_api.accounts.wire import (
    Browser,
    Export,
    Happened,
    KeptSearch,
    KeptSearches,
    LinkHeld,
    Me,
    Preferences,
    PreferencesBody,
    RecentSearches,
    SearchState,
    Sessions,
    SignedIn,
    SignedInAt,
    SignInBody,
    SignOutBody,
    Switch,
    WhoseLink,
)
from burro_api.errors import ApiError, spec_refused
from burro_api.wire import ErrorCode

# The headers the website speaks to the service by. The first holds its secret. The
# second holds the address of the client, as the website's own host gave it. The third
# is what a page of the website sends with whatever changes anything, and what a form
# on another site cannot send.
WEBSITE = "x-burro-website"
CLIENT = "x-burro-client-address"
REQUESTED = "x-burro-request"
ONE = "1"
JSON = "application/json"
# Where the page stands that a link opens. The token stands after the `#`, which a
# browser sends to no server: so it is in no log of requests and in no referrer.
CONFIRM = "/sign-in/confirm#t="
STAMP = "%Y-%m-%dT%H:%M:%SZ"

QUARTER = timedelta(minutes=15)
HOUR = timedelta(hours=1)
DAY = timedelta(days=1)
LINK_LASTS = timedelta(minutes=LINK_LASTS_MINUTES)
# How many links one address may be sent, within how long.
LINKS_TO_AN_ADDRESS = ((QUARTER, 3), (DAY, 10))
# How many times one client may ask for a link, and may show a link, in a quarter of
# an hour. The second is not in the design. A link cannot be found by trying, so it
# is a limit on the work a client can ask for, and on nothing else.
LINKS_FROM_A_CLIENT = 10
SHOWN_BY_A_CLIENT = 30
SESSION_LASTS = timedelta(days=30)
# How often a session is put forward at the most, and how long it may last in all.
PUT_FORWARD_AFTER = DAY
SESSION_AT_MOST = timedelta(days=90)
# How lately a person must have signed in to delete their account.
FRESH_FOR = timedelta(minutes=10)
MOST_SEARCHES = 100
MOST_RECENT = 10
# How long what is kept is kept, at the least: `let_go` says when what is older goes.
# Each is a first guess, and the founder's to set.
KEEP_LINKS = DAY
KEEP_SESSIONS = timedelta(days=30)
KEEP_EVENTS = timedelta(days=90)
MOST_EVENTS = 200
# How long nobody is sent a link once the company that sends could not be reached. A
# letter is sent after its answer was given, so the answer cannot say that it failed:
# whoever asks next is told, whatever their address.
DOWN_FOR = timedelta(minutes=1)


def stamp(at: datetime) -> str:
    return at.astimezone(UTC).strftime(STAMP)


def _read(written: str) -> datetime:
    return datetime.strptime(written, STAMP).replace(tzinfo=UTC)


def let_go(held: Held, now: datetime) -> int:
    """Let go of what is too old, of every kind. It says how many rows went.

    No step runs by the clock, so it is asked wherever accounts write already: as a
    link is asked for, as somebody signs in, as a session is put forward, and as the
    service starts. What is too old then goes the next time anybody uses an account,
    and not only as a row of its own kind is next written. On a day when nobody does,
    and while accounts are off and the file is not opened, it stays.
    """
    sessions = held.forget_sessions(stamp(now - KEEP_SESSIONS))
    events = held.forget_events(stamp(now - KEEP_EVENTS))
    return sessions + events + held.forget_links(stamp(now - KEEP_LINKS))


def family(agent: str) -> Browser:
    """The family of a browser, coarsely, from what it says it is. Nothing else of it is kept."""
    said = agent.lower()
    # Each later one says the names of the earlier ones too, so the order is the rule.
    if "edg/" in said or "edga/" in said or "edgios/" in said:
        return Browser.EDGE
    if "firefox/" in said or "fxios/" in said:
        return Browser.FIREFOX
    if "chrome/" in said or "crios/" in said or "chromium/" in said:
        return Browser.CHROME
    return Browser.SAFARI if "safari/" in said else Browser.OTHER


@dataclass(frozen=True)
class Asked:
    """What is known of who asks, once the website has been heard. It shows in no `repr`."""

    # The address of the client, made regular. It is counted, and is kept nowhere.
    client: str = field(repr=False)
    # What the browser holds that binds a link to it, and its session, where each is in
    # the shape of one.
    binding: str | None = field(repr=False)
    session: str | None = field(repr=False)
    browser: Browser
    request_id: str


@dataclass(frozen=True)
class Letter:
    """A link that is to be sent, once the answer to whoever asked has been given.

    It shows in no `repr`: it holds the address, and the link with its token.
    """

    to: str = field(repr=False)
    link: str = field(repr=False)
    # What the link is kept by, to end it where the letter cannot be sent.
    token_hash: str = field(repr=False)
    request_id: str


@dataclass(frozen=True)
class Current:
    """Who is signed in: the account, and the session that says so."""

    account: Account
    session: Signed
    # How long the cookie is to last from now, where the session was put forward.
    put_forward_s: int | None = None


@dataclass(frozen=True)
class Refusal:
    code: ErrorCode
    outcome: Outcome


def _shaped(sent: str | None) -> str | None:
    return sent if sent is not None and tokens.in_shape(sent) else None


class Accounts:
    def __init__(
        self,
        settings: AccountsSettings,
        store: Store,
        sender: Sender | None,
        now: Callable[[], datetime],
        origins: Sequence[str],
    ) -> None:
        self._store = store
        self._sender = sender
        self._now = now
        self._origins = frozenset(origins)
        self._site = settings.site
        # True only on a machine that listens to itself, where no host stands before
        # the website to say who asks.
        self._development = settings.development
        self._secret = settings.website_secret.get_secret_value()
        self._per_hour = settings.links_per_hour
        self._keeps_recent = settings.keep_recent is KeepRecent.FROM_THE_START
        key = settings.limits_key.get_secret_value().encode()
        self._links = Limiter(key, LINKS_FROM_A_CLIENT, QUARTER, now)
        self._shown = Limiter(key, SHOWN_BY_A_CLIENT, QUARTER, now)
        # Until when no link is sent, because the company that sends could not be reached.
        self._down_until: datetime | None = None
        # When each ask of the hour was answered that was sent nothing, its address
        # being over its limit: a time, and nothing of the address. Such an ask leaves
        # no row, so it is counted here, or a full hour would tell whoever asks next
        # which it was.
        self._sent_nothing: deque[str] = deque()
        self.cookies = Cookies(secure=not settings.in_the_clear)

    def __repr__(self) -> str:
        return "Accounts()"

    def close(self) -> None:
        self._store.close()

    def _say(self, event: Event, outcome: Outcome, request_id: str) -> None:
        """One line of the log: what happened and how it ended, and nothing of whom."""
        logs.event("account", request_id=request_id, happened=event.value, outcome=outcome.value)

    def _kept(self, held: Held, account_id: str, event: Event, outcome: Outcome, at: str) -> None:
        """Keep what happened to an account, and let go of what is too old or too much."""
        held.add_event(account_id, event.value, outcome.value, at)
        held.trim_events(account_id, MOST_EVENTS)
        held.forget_events(stamp(_read(at) - KEEP_EVENTS))

    # Who is heard.

    def heard(
        self,
        method: str,
        headers: Headers,
        query: str,
        cookies: Mapping[str, str],
        request_id: str,
    ) -> Asked:
        """Hear the website, and nobody else. What is refused is refused in one way."""
        shown = headers.getlist(WEBSITE)
        # Compared whatever was sent, so that the time it takes tells nothing.
        known = tokens.same_secret(shown[0] if shown else "", self._secret)
        if not known or len(shown) != 1:
            raise ApiError(ErrorCode.NOT_THE_WEBSITE)
        if query:
            # No route of accounts takes a query, and a link or an id must never be in one.
            raise ApiError(ErrorCode.INVALID_REQUEST)
        if method != "GET":
            kind = headers.get("content-type", "").split(";")[0].strip().lower()
            if kind != JSON:
                raise ApiError(ErrorCode.UNSUPPORTED_MEDIA_TYPE)
            # One origin, which is on the list as it is written, and one header that
            # says a page of Burro asked. Two of either are nothing a browser sends.
            origins = headers.getlist("origin")
            from_a_page = len(origins) == 1 and origins[0] in self._origins
            if not from_a_page or headers.getlist(REQUESTED) != [ONE]:
                raise ApiError(ErrorCode.NOT_THE_WEBSITE)
        try:
            client = client_of(headers.getlist(CLIENT))
        except NotOne:
            raise ApiError(ErrorCode.NOT_THE_WEBSITE) from None
        if client == UNKNOWN and not self._development:
            # The website says whose request it passes on, with every one. Were those
            # it said nothing of counted as one client, whoever asked ten times would
            # stop every one of them from signing in.
            raise ApiError(ErrorCode.NOT_THE_WEBSITE)
        return Asked(
            client=client,
            binding=_shaped(cookies.get(self.cookies.link)),
            session=_shaped(cookies.get(self.cookies.session)),
            browser=family(headers.get("user-agent", "")),
            request_id=request_id,
        )

    # Signing in.

    def ask_for_link(self, typed: str, asked: Asked) -> tuple[str, Letter | None]:
        """Make a link for the address, and give back what binds it to the browser that asked.

        With it comes the letter to send once the answer has been given, where there
        is one to send. No account is looked for and nothing is sent before the answer,
        so the answer is the same, and takes the same work, whether or not the address
        has an account and whether or not it is sent a letter.
        """
        now = self._now()
        binding = tokens.fresh()
        letter = self._link_to(typed, asked, tokens.hashed(binding), now)
        if asked.binding is not None:
            # The browser is about to be given what binds its links anew, so the links
            # it asked for before are bound to that too. It is done here, where the
            # answer is one that gives it, and never where a refusal leaves the
            # browser holding what it held.
            with self._store.writing() as held:
                held.bind_again(tokens.hashed(asked.binding), tokens.hashed(binding), stamp(now))
        return binding, letter

    def _link_to(self, typed: str, asked: Asked, bound: str, now: datetime) -> Letter | None:
        """Make a link, within the limits. It returns where the answer is 202.

        What it returns is the letter to send, or nothing where the address is over
        its limit and none is sent.
        """
        if not self._links.lets_in(asked.client):
            self._say(Event.RATE_LIMITED, Outcome.LIMITED, asked.request_id)
            raise ApiError(ErrorCode.RATE_LIMITED)
        email = regular(typed)
        if email is None:
            self._say(Event.LINK_REQUESTED, Outcome.REFUSED, asked.request_id)
            raise ApiError(ErrorCode.INVALID_EMAIL)
        down = self._down_until
        if self._sender is None or (down is not None and now < down):
            # The same whatever the address: nobody is sent a link at the moment.
            self._say(Event.LINK_REQUESTED, Outcome.UNAVAILABLE, asked.request_id)
            raise ApiError(ErrorCode.SIGN_IN_UNAVAILABLE)
        token = tokens.fresh()
        at = stamp(now)
        made = Link(tokens.hashed(token), email, at, stamp(now + LINK_LASTS), None, bound)
        with self._store.writing() as held:
            forgotten = let_go(held, now)
            hour = stamp(now - HOUR)
            while self._sent_nothing and self._sent_nothing[0] <= hour:
                self._sent_nothing.popleft()
            busy = held.links_since(hour) + len(self._sent_nothing) >= self._per_hour
            # Each is counted, whatever the one before it came to.
            counted = [
                held.links_to(email, stamp(now - within)) >= most
                for within, most in LINKS_TO_AN_ADDRESS
            ]
            over = busy or any(counted)
            # The link is written whether or not it is to be kept, and one that is not
            # is taken out again before anything is kept. So an address over its limit
            # costs the file what any address costs it, and how long the answer takes
            # does not say that somebody asked for this address before.
            held.add_link(made)
            if over:
                held.forget_link(made.token_hash)
            if over and not busy:
                # Inside the write, so that its lock holds what is counted here too.
                self._sent_nothing.append(at)
        if forgotten:
            self._store.trim()
        if busy:
            self._say(Event.RATE_LIMITED, Outcome.LIMITED, asked.request_id)
            raise ApiError(ErrorCode.SIGN_IN_BUSY)
        self._say(Event.LINK_REQUESTED, Outcome.OK, asked.request_id)
        if over:
            # Answered as every address is, so that the answer does not say that this
            # one was asked for before. Nothing is sent, and nothing is kept.
            self._say(Event.RATE_LIMITED, Outcome.LIMITED, asked.request_id)
            return None
        return Letter(email, f"{self._site}{CONFIRM}{token}", made.token_hash, asked.request_id)

    def send(self, letter: Letter) -> None:
        """Send a link that was made. It is called once the answer has been given.

        So an answer never waits on the company that sends, and is given as soon for
        an address that is sent a letter as for one that is over its limit and is sent
        none. The answer cannot say that the letter failed, so whoever asks next is
        told, for a minute, where the company could not be reached.
        """
        if self._sender is None:
            return
        try:
            self._sender.send(letter.to, letter.link)
        except SendFailed as failed:
            self._not_sent(letter, reached=failed.reached)
            return
        except Exception:
            # Whatever else goes wrong is let fall to the edge, which writes its type
            # and never what it says: that may hold the address, or the link.
            self._not_sent(letter, reached=False)
            raise
        self._say(Event.LINK_SENT, Outcome.OK, letter.request_id)

    def _not_sent(self, letter: Letter, reached: bool) -> None:
        now = self._now()
        with self._store.writing() as held:
            # A link that was not sent opens nothing. It is still counted.
            held.end_link(letter.token_hash, stamp(now))
        if not reached:
            self._down_until = now + DOWN_FOR
        # What the company would not take may be about the address. So nobody who
        # asks after is told of it, and the answer was the one every address is given.
        outcome = Outcome.REFUSED if reached else Outcome.UNAVAILABLE
        self._say(Event.LINK_SEND_FAILED, outcome, letter.request_id)

    def _may_show(self, asked: Asked) -> None:
        if not self._shown.lets_in(asked.client):
            self._say(Event.RATE_LIMITED, Outcome.LIMITED, asked.request_id)
            raise ApiError(ErrorCode.RATE_LIMITED)

    def _found(self, held: Held, token: str, at: str) -> Link | Refusal:
        """The link a token opens, or why it opens nothing."""
        if not tokens.in_shape(token):
            return Refusal(ErrorCode.LINK_NOT_VALID, Outcome.REFUSED)
        hashed = tokens.hashed(token)
        link = held.link(hashed)
        if link is None or not tokens.same(link.token_hash, hashed):
            return Refusal(ErrorCode.LINK_NOT_VALID, Outcome.REFUSED)
        if link.used_at is not None:
            return Refusal(ErrorCode.LINK_USED, Outcome.USED)
        if link.ends_at <= at:
            return Refusal(ErrorCode.LINK_EXPIRED, Outcome.EXPIRED)
        return link

    def _in_the_browser_that_asked(self, link: Link, asked: Asked) -> bool:
        if asked.binding is None:
            return False
        return tokens.same(link.binding_hash, tokens.hashed(asked.binding))

    def whose(self, token: str, asked: Asked) -> WhoseLink:
        """Whose link this is. It reads, and writes nothing: so it uses nothing up."""
        self._may_show(asked)
        with self._store.reading() as held:
            found = self._found(held, token, stamp(self._now()))
            account = None if isinstance(found, Refusal) else held.account_of(found.email)
        if isinstance(found, Refusal):
            self._say(Event.LINK_REJECTED, found.outcome, asked.request_id)
            raise ApiError(found.code)
        return WhoseLink(
            email=found.email,
            same_browser=self._in_the_browser_that_asked(found, asked),
            new_account=account is None,
        )

    def sign_in(self, body: SignInBody, asked: Asked) -> tuple[SignedIn, str]:
        """Use a link up and make a session. What is given back with the answer is the session.

        That the link has not ended and was not used is checked, and marked, in one
        transaction: so of two that come at once, one signs in.
        """
        self._may_show(asked)
        now = self._now()
        at = stamp(now)
        session = tokens.fresh()
        refused: Refusal | None = None
        signed: SignedIn | None = None
        revoked = False
        forgotten = 0
        with self._store.writing() as held:
            found = self._found(held, body.token, at)
            if isinstance(found, Refusal):
                # Logged, and not kept with the account. What is kept of an account is
                # so many rows, and whoever holds a link that has ended could show it
                # until every row was of that, and none of who had signed in.
                refused = found
            else:
                account = held.account_of(found.email)
                if not (self._in_the_browser_that_asked(found, asked) or body.other_browser):
                    refused = Refusal(ErrorCode.OTHER_BROWSER, Outcome.REFUSED)
                elif account is None and not body.adult:
                    refused = Refusal(ErrorCode.AGE_NOT_CONFIRMED, Outcome.REFUSED)
                else:
                    signed = SignedIn(email=found.email, new_account=account is None)
                    if account is None:
                        account = Account(tokens.fresh_id(), found.email, at, at)
                        held.add_account(account)
                    held.end_links(found.email, at)
                    revoked = self._revoked_what_was_shown(held, asked, at)
                    forgotten = let_go(held, now)
                    held.add_session(
                        Signed(
                            token_hash=tokens.hashed(session),
                            public_id=tokens.fresh_id(),
                            account_id=account.id,
                            made_at=at,
                            seen_at=at,
                            ends_at=stamp(now + SESSION_LASTS),
                            revoked_at=None,
                            browser=asked.browser.value,
                        )
                    )
                    self._kept(held, account.id, Event.LINK_USED, Outcome.OK, at)
                    self._kept(held, account.id, Event.SESSION_CREATED, Outcome.OK, at)
        if forgotten:
            self._store.trim()
        if refused is not None or signed is None:
            outcome = refused.outcome if refused else Outcome.REFUSED
            self._say(Event.LINK_REJECTED, outcome, asked.request_id)
            raise ApiError(refused.code if refused else ErrorCode.LINK_NOT_VALID)
        if revoked:
            self._say(Event.SESSION_REVOKED, Outcome.OK, asked.request_id)
        self._say(Event.LINK_USED, Outcome.OK, asked.request_id)
        self._say(Event.SESSION_CREATED, Outcome.OK, asked.request_id)
        return signed, session

    def _revoked_what_was_shown(self, held: Held, asked: Asked, at: str) -> bool:
        """Revoke the session the browser came with, so that signing in leaves it one."""
        if asked.session is None:
            return False
        hashed = tokens.hashed(asked.session)
        shown = held.session(hashed)
        if shown is None or not held.revoke_shown(hashed, at):
            return False
        self._kept(held, shown.account_id, Event.SESSION_REVOKED, Outcome.OK, at)
        return True

    # A session.

    def session_of(self, asked: Asked) -> Current | None:
        """Who is signed in, or nobody. A session that is used is put forward, once a day.

        It is the one thing that is written for whoever only reads, so what is too old
        is let go of with it: that is each day that anybody who is signed in comes back.
        """
        if asked.session is None:
            return None
        now = self._now()
        at = stamp(now)
        hashed = tokens.hashed(asked.session)
        with self._store.reading() as held:
            found = held.session(hashed)
            if found is None or not tokens.same(found.token_hash, hashed):
                return None
            if found.revoked_at is not None or found.ends_at <= at:
                return None
            account = held.account(found.account_id)
        if account is None:
            return None
        if _read(found.seen_at) + PUT_FORWARD_AFTER > now:
            return Current(account, found)
        # Never past so long from when it was made, however often it is used.
        ends = min(now + SESSION_LASTS, _read(found.made_at) + SESSION_AT_MOST)
        with self._store.writing() as held:
            held.put_forward(account.id, hashed, at, stamp(ends))
            forgotten = let_go(held, now)
        if forgotten:
            self._store.trim()
        put_forward = replace(found, seen_at=at, ends_at=stamp(ends))
        return Current(account, put_forward, int((ends - now).total_seconds()))

    def lasts_s(self) -> int:
        """How long the cookie of a session that was just made is to last, in seconds."""
        return int(SESSION_LASTS.total_seconds())

    def link_lasts_s(self) -> int:
        return int(LINK_LASTS.total_seconds())

    def sign_out(self, current: Current, request_id: str) -> None:
        """Revoke the session at the service. A cookie that is kept opens nothing after."""
        at = stamp(self._now())
        with self._store.writing() as held:
            if held.revoke(current.account.id, current.session.public_id, at):
                self._kept(held, current.account.id, Event.SESSION_REVOKED, Outcome.OK, at)
        self._say(Event.SESSION_REVOKED, Outcome.OK, request_id)

    def _live(self, held: Held, current: Current, at: str) -> tuple[SignedInAt, ...]:
        found = held.sessions(current.account.id)
        return tuple(
            self._served(each, current)
            for each in found
            if each.revoked_at is None and each.ends_at > at
        )

    def _served(self, signed: Signed, current: Current) -> SignedInAt:
        return SignedInAt(
            session_id=signed.public_id,
            browser=Browser(signed.browser),
            made_at=signed.made_at,
            seen_at=signed.seen_at,
            ends_at=signed.ends_at,
            current=signed.public_id == current.session.public_id,
            revoked=signed.revoked_at is not None,
        )

    def sessions(self, current: Current) -> Sessions:
        with self._store.reading() as held:
            return Sessions(sessions=self._live(held, current, stamp(self._now())), signed_in=True)

    def end_sessions(self, body: SignOutBody, current: Current, request_id: str) -> Sessions:
        """Sign out of one browser, by the id it is named by, or of every one."""
        if body.everywhere is (body.session_id is not None):
            # Either the one that is named, or every one. Both, or neither, is no request.
            raise ApiError(ErrorCode.INVALID_REQUEST)
        at = stamp(self._now())
        with self._store.writing() as held:
            if body.session_id is None:
                held.revoke_all(current.account.id, at)
            elif not held.revoke(current.account.id, body.session_id, at):
                raise ApiError(ErrorCode.SESSION_NOT_FOUND)
            self._kept(held, current.account.id, Event.SESSION_REVOKED, Outcome.OK, at)
            left = self._live(held, current, at)
        self._say(Event.SESSION_REVOKED, Outcome.OK, request_id)
        return Sessions(sessions=left, signed_in=any(each.current for each in left))

    # What a person who has signed in can do.

    def _preferences(self, held: Held, account_id: str) -> Preferences:
        chosen = held.preferences(account_id).get("keep_recent")
        usual = Switch.ON if self._keeps_recent else Switch.OFF
        return Preferences(keep_recent=Switch(chosen) if chosen else usual)

    def me(self, current: Current) -> Me:
        with self._store.reading() as held:
            preferences = self._preferences(held, current.account.id)
        return Me(
            email=current.account.email,
            made_at=current.account.made_at,
            preferences=preferences,
            fresh=self._fresh(current),
        )

    def _fresh(self, current: Current) -> bool:
        return _read(current.session.made_at) + FRESH_FOR > self._now()

    def _gone(self, taken: int) -> None:
        """Take what was taken away out of the file, and not only out of its tables.

        A search says where somebody goes. Once it is taken away it is written over in
        the file, and what was written ahead of the file is brought into it and cut to
        nothing: so it is in no byte that is left, whoever comes to read the volume.
        """
        if taken:
            self._store.trim()

    def set_preferences(self, body: PreferencesBody, current: Current) -> Preferences:
        taken = 0
        with self._store.writing() as held:
            if body.keep_recent is not None:
                held.set_preference(current.account.id, "keep_recent", body.keep_recent.value)
                if body.keep_recent is Switch.OFF:
                    # What was kept because they let Burro keep it goes as they stop.
                    taken = held.forget_recent(current.account.id)
            found = self._preferences(held, current.account.id)
        self._gone(taken)
        return found

    def _readable(self, kept: Kept, release: Release) -> KeptSearch:
        """A search as it is served: checked again by the schema the ranking uses."""
        try:
            spec = PreferenceSpec.model_validate_json(kept.spec)
        except (ValidationError, ValueError):
            spec = None
        if spec is None:
            state = SearchState.UNREADABLE
        elif check_spec(spec, release):
            state = SearchState.RELEASE_CHANGED
        else:
            state = SearchState.OK
        return KeptSearch(
            search_id=kept.id,
            name=kept.name,
            spec=spec,
            release_id=kept.release_id,
            kept_at=kept.made_at,
            state=state,
        )

    def _to_keep(self, spec: PreferenceSpec, release: Release) -> Kept:
        """What is kept of a search: the spec, checked, and a name worked out from it."""
        problems = check_spec(spec, release)
        if problems:
            raise spec_refused(problems)
        return Kept(
            id=tokens.fresh_id(),
            spec=spec.model_dump_json(),
            release_id=release.manifest.release_id,
            name=name_of(spec, release),
            made_at=stamp(self._now()),
        )

    def searches(self, current: Current, release: Release) -> KeptSearches:
        with self._store.reading() as held:
            found = held.searches(current.account.id)
        served = tuple(self._readable(each, release) for each in found)
        return KeptSearches(searches=served, most=MOST_SEARCHES)

    def keep_search(self, spec: PreferenceSpec, current: Current, release: Release) -> KeptSearch:
        made = self._to_keep(spec, release)
        with self._store.writing() as held:
            # The same search is kept once, however often it is pressed.
            like = held.search_like(current.account.id, made.spec)
            if like is None:
                if held.count_searches(current.account.id) >= MOST_SEARCHES:
                    raise ApiError(ErrorCode.TOO_MANY_SEARCHES)
                held.add_search(current.account.id, made)
        return self._readable(like or made, release)

    def forget_search(self, search_id: str, current: Current, release: Release) -> KeptSearches:
        with self._store.writing() as held:
            if not held.forget_search(current.account.id, search_id):
                raise ApiError(ErrorCode.SEARCH_NOT_FOUND)
        self._gone(1)
        return self.searches(current, release)

    def _recent(self, held: Held, current: Current, release: Release) -> RecentSearches:
        kept = self._preferences(held, current.account.id).keep_recent is Switch.ON
        found = held.recent(current.account.id) if kept else ()
        served = tuple(self._readable(each, release) for each in found)
        return RecentSearches(kept=kept, searches=served, most=MOST_RECENT)

    def recent(self, current: Current, release: Release) -> RecentSearches:
        with self._store.reading() as held:
            return self._recent(held, current, release)

    def keep_recent(
        self, spec: PreferenceSpec, current: Current, release: Release
    ) -> RecentSearches:
        """Put a search among the last ten, where the person lets Burro keep them."""
        made = self._to_keep(spec, release)
        pushed_out = 0
        with self._store.writing() as held:
            if self._preferences(held, current.account.id).keep_recent is Switch.ON:
                # One that is searched again comes to the top, and is not held twice.
                held.forget_recent_like(current.account.id, made.spec)
                held.add_recent(current.account.id, made)
                pushed_out = held.trim_recent(current.account.id, MOST_RECENT)
            found = self._recent(held, current, release)
        self._gone(pushed_out)
        return found

    def forget_recent(self, current: Current, release: Release) -> RecentSearches:
        with self._store.writing() as held:
            taken = held.forget_recent(current.account.id)
            found = self._recent(held, current, release)
        self._gone(taken)
        return found

    def export(self, current: Current, release: Release) -> Export:
        """Everything Burro holds of the account, read at one moment."""
        account = current.account
        with self._store.reading() as held:
            return Export(
                exported_at=stamp(self._now()),
                email=account.email,
                made_at=account.made_at,
                adult_at=account.adult_at,
                preferences=self._preferences(held, account.id),
                searches=tuple(self._readable(e, release) for e in held.searches(account.id)),
                recent=tuple(self._readable(e, release) for e in held.recent(account.id)),
                sessions=tuple(self._served(e, current) for e in held.sessions(account.id)),
                events=tuple(
                    Happened(event=Event(e.event), outcome=Outcome(e.outcome), at=e.at)
                    for e in held.events(account.id)
                ),
                links=tuple(
                    LinkHeld(asked_at=e.made_at, ends_at=e.ends_at, used=e.used_at is not None)
                    for e in held.links_of(account.email)
                ),
            )

    def delete(self, current: Current, request_id: str) -> None:
        """Delete the account and everything of it, in one transaction."""
        if not self._fresh(current):
            raise ApiError(ErrorCode.SIGN_IN_AGAIN)
        with self._store.writing() as held:
            held.delete_account(current.account.id)
            held.forget_links_of(current.account.email)
        # So that what was deleted is gone from the file, and not only from its tables.
        self._store.trim()
        self._say(Event.ACCOUNT_DELETED, Outcome.OK, request_id)


def open_accounts(
    settings: AccountsSettings,
    host: str,
    origins: Sequence[str],
    now: Callable[[], datetime],
    sender: Sender | None = None,
) -> Accounts:
    """Accounts as they are set, with the file opened. Made only where accounts are on."""
    held_to(settings, host, origins)
    found = sender_for(settings) if sender is None else sender
    store = Store(Path(settings.database))
    try:
        with store.writing() as held:
            forgotten = let_go(held, now())
        if forgotten:
            store.trim()
        return Accounts(settings, store, found, now, origins)
    except BaseException:
        store.close()
        raise
