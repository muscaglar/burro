"""What travels over the wire for accounts: what each route takes, and what each gives.

One thing here is what a person typed: the address they sign in with. It travels in a
body, as everything typed does. A search that is kept is the spec, what Burro
understood, and its name is worked out from the spec and is never the person's words.

No id is taken in a path. A search or a session is named in a body, by an id that says
nothing of it, and whose rows are read is decided by the session and never by the id.
"""

from enum import StrEnum
from typing import Annotated

from burro_core.ids import TIMESTAMP_PATTERN, ReleaseId
from burro_core.spec import PreferenceSpec
from pydantic import Field, StrictBool, StringConstraints

from burro_api.accounts.events import Event, Outcome
from burro_api.wire import Body, Wire

# 128 random bits, as URL-safe text.
ID_PATTERN = r"^[A-Za-z0-9_-]{22}$"
# The longest an address may be, and the longest the part before its `@`.
LONGEST_ADDRESS = 254
# A token is 43 characters. What is sent in the place of one may be anything, and is
# answered as a link that Burro does not know: so it is held to a length and no more.
LONGEST_TOKEN = 128

Id = Annotated[str, Field(pattern=ID_PATTERN)]
At = Annotated[str, Field(pattern=TIMESTAMP_PATTERN)]
Token = Annotated[str, StringConstraints(min_length=1, max_length=LONGEST_TOKEN)]


class Switch(StrEnum):
    ON = "on"
    OFF = "off"


class SearchState(StrEnum):
    """Whether a search that was kept can be searched again on the data as it is now."""

    OK = "ok"
    # It names a place, an area or a measure that the data no longer holds.
    RELEASE_CHANGED = "release_changed"
    # What is kept can no longer be read as a search. Its `spec` is not served.
    UNREADABLE = "unreadable"


class Browser(StrEnum):
    """The family of a browser, coarsely. It is all that is kept of what a browser says it is."""

    CHROME = "chrome"
    EDGE = "edge"
    FIREFOX = "firefox"
    SAFARI = "safari"
    OTHER = "other"


# What a route takes.


class LinkBody(Body):
    # The address to send a link to. It is made regular and then checked for its shape.
    email: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=LONGEST_ADDRESS)
    ]


class TokenBody(Body):
    token: Token


class SignInBody(Body):
    token: Token
    # That the person ticked that they are 18 or over. It is asked the first time an
    # address signs in, and no account is made without it.
    adult: StrictBool = False
    # That the person was told the link was asked for in another browser, was shown the
    # address again, and chose to go on.
    other_browser: StrictBool = False


class KeepBody(Body):
    spec: PreferenceSpec


class ForgetBody(Body):
    search_id: Id


class PreferencesBody(Body):
    """What to set. A preference that is left out, or is `null`, stays as it was."""

    keep_recent: Switch | None = None


class SignOutBody(Body):
    # The one to sign out of, by the id `sessions` gives it. It is left out where
    # every one is meant.
    session_id: Id | None = None
    everywhere: StrictBool = False


# Every body a route of accounts takes, for what must hold of them all.
BODIES: tuple[type[Body], ...] = (
    LinkBody,
    TokenBody,
    SignInBody,
    KeepBody,
    ForgetBody,
    PreferencesBody,
    SignOutBody,
)


# What a route gives.


class LinkAsked(Wire):
    """What asking for a link is answered: the same, whoever asked and whatever the address."""

    # How long a link works for, in minutes.
    lasts_minutes: int


class WhoseLink(Wire):
    """Whose link this is. Asking uses nothing up."""

    email: str
    # Whether the link was asked for in the browser that now holds it. Where it was
    # not, a page says so, shows the address again and asks a second time.
    same_browser: bool
    # Whether signing in would make an account. A page then asks the person to say
    # that they are 18 or over.
    new_account: bool


class SignedIn(Wire):
    email: str
    # Whether an account was made by this sign-in.
    new_account: bool


class Session(Wire):
    """Whether the browser that asked is signed in, and as whom."""

    signed_in: bool
    # `null` where nobody is signed in.
    email: str | None


class Preferences(Wire):
    """Every preference as it now stands, whether the person set it or nobody did."""

    # Whether Burro keeps this person's last searches.
    keep_recent: Switch


class Me(Wire):
    email: str
    made_at: At
    preferences: Preferences
    # Whether the person signed in within the last ten minutes, which deleting the
    # account asks for.
    fresh: bool


class KeptSearch(Wire):
    search_id: Id
    # What was understood, said in a line. It is worked out from the spec when the
    # search is kept, and holds no word the person typed.
    name: str
    # `null` where what is kept can no longer be read as a search.
    spec: PreferenceSpec | None
    # The data the search was kept on.
    release_id: ReleaseId
    kept_at: At
    state: SearchState


class KeptSearches(Wire):
    # The newest first.
    searches: tuple[KeptSearch, ...]
    # The most that an account may keep.
    most: int


class RecentSearches(Wire):
    # Whether Burro keeps this person's last searches. Where it does not, none is
    # held and none is listed.
    kept: bool
    # The newest first.
    searches: tuple[KeptSearch, ...]
    most: int


class SignedInAt(Wire):
    """One browser a person is signed in with."""

    # An id to name it by. It is not the session and says nothing of it.
    session_id: Id
    browser: Browser
    made_at: At
    # Put forward once a day at the most, so it says the day and little more.
    seen_at: At
    ends_at: At
    # Whether it is the browser that asked.
    current: bool
    revoked: bool


class Sessions(Wire):
    # Those that have not ended and were not revoked, the newest first.
    sessions: tuple[SignedInAt, ...]
    # Whether the browser that asked is still signed in. It is not, once it has
    # signed out of its own session or of every one.
    signed_in: bool


class Happened(Wire):
    event: Event
    outcome: Outcome
    at: At


class LinkHeld(Wire):
    """A link that was asked for the address of the account, for as long as Burro holds it."""

    asked_at: At
    ends_at: At
    used: bool


class Export(Wire):
    """Everything Burro holds of an account."""

    exported_at: At
    email: str
    made_at: At
    # When the person said that they are 18 or over.
    adult_at: At
    preferences: Preferences
    searches: tuple[KeptSearch, ...]
    recent: tuple[KeptSearch, ...]
    # Every session that is held, those that ended or were revoked among them.
    sessions: tuple[SignedInAt, ...]
    events: tuple[Happened, ...]
    links: tuple[LinkHeld, ...]
