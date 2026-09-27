"""Routes 15 to 31: signing in by a link sent by email, and what a person keeps.

They are served only where accounts are turned on, and the contract lists them whether
or not they are: a client is made from it.

Each is asked of the website, which passes it on, and is answered to nobody else. A
`GET` changes nothing. Everything else names what it is about in a body, so no id and
nothing a person typed is ever in a path.

A route hands on what was sent and serves what comes back. Every rule of accounts is in
`accounts.service`, and who may ask is decided before a route is reached, by
`accounts.gate`.
"""

from typing import Any

from fastapi import APIRouter, BackgroundTasks, Response

from burro_api.accounts.gate import Heard, Held, OfTheWebsite, SignedInAs
from burro_api.accounts.sender import LINK_LASTS_MINUTES
from burro_api.accounts.wire import (
    Export,
    ForgetBody,
    KeepBody,
    KeptSearch,
    KeptSearches,
    LinkAsked,
    LinkBody,
    Me,
    Preferences,
    PreferencesBody,
    RecentSearches,
    Session,
    Sessions,
    SignedIn,
    SignInBody,
    SignOutBody,
    TokenBody,
    WhoseLink,
)
from burro_api.deps import Ctx
from burro_api.routes.common import PREFIX, RequestId, Responses, envelope
from burro_api.wire import Envelope, ErrorEnvelope

# What each of these routes is marked with in the contract. A client that is made from
# the contract can then tell them from the routes it asks of the service itself: a
# browser asks these of the website, which passes them on.
OF_ACCOUNTS = "accounts"

router = APIRouter(prefix=PREFIX, route_class=OfTheWebsite, tags=[OF_ACCOUNTS])

_ERROR: dict[str, Any] = {"model": ErrorEnvelope}
# What any route of accounts may answer: 403 to anything but the website, and to a page
# that is not the website's own, and 422 to a query, which none of them takes.
ASKED: Responses = {403: _ERROR, 422: _ERROR, 500: _ERROR}
# What changes something says how it is sent, though it may send nothing.
BARE: Responses = ASKED | {413: _ERROR, 415: _ERROR}
CHANGED: Responses = BARE | {400: _ERROR}
NOT_SIGNED_IN: Responses = {401: _ERROR}
NOT_FOUND: Responses = {404: _ERROR}
NOT_YET: Responses = {409: _ERROR}
ENDED: Responses = {410: _ERROR}
LIMITED: Responses = {429: _ERROR}
UNAVAILABLE: Responses = {503: _ERROR}

# The answer to asking for a link: it is on its way, if the address takes mail.
ACCEPTED = 202
NOBODY = Session(signed_in=False, email=None)


# Signing in.


@router.post(
    "/auth/link",
    status_code=ACCEPTED,
    response_model=Envelope[LinkAsked],
    responses=CHANGED | LIMITED | UNAVAILABLE,
)
def ask_for_link(
    body: LinkBody,
    context: Ctx,
    accounts: Held,
    asked: Heard,
    response: Response,
    once_answered: BackgroundTasks,
) -> Envelope[LinkAsked]:
    """Send a link to sign in with. The answer is the same whether or not the address is known."""
    binding, letter = accounts.ask_for_link(body.email, asked)
    if letter is not None:
        # Sent once the answer has been given. An answer that waited on the letter
        # would come sooner for an address that is over its limit and is sent none.
        once_answered.add_task(accounts.send, letter)
    cookies = accounts.cookies
    cookies.give(response, cookies.link, binding, accounts.link_lasts_s())
    return envelope(context, LinkAsked(lasts_minutes=LINK_LASTS_MINUTES))


@router.post(
    "/auth/link/whose",
    response_model=Envelope[WhoseLink],
    responses=CHANGED | ENDED | LIMITED,
)
def whose_link(body: TokenBody, context: Ctx, accounts: Held, asked: Heard) -> Envelope[WhoseLink]:
    """Whose link this is, for a page to show before it signs anybody in. It uses nothing up."""
    return envelope(context, accounts.whose(body.token, asked))


@router.post(
    "/auth/session",
    response_model=Envelope[SignedIn],
    responses=CHANGED | NOT_YET | ENDED | LIMITED,
)
def sign_in(
    body: SignInBody, context: Ctx, accounts: Held, asked: Heard, response: Response
) -> Envelope[SignedIn]:
    """Use a link up and sign the browser in. The first time, it makes the account."""
    signed, session = accounts.sign_in(body, asked)
    cookies = accounts.cookies
    cookies.give(response, cookies.session, session, accounts.lasts_s())
    # The link is used, so what bound it to this browser binds nothing more.
    cookies.take_back(response, cookies.link)
    return envelope(context, signed)


@router.get("/auth/session", response_model=Envelope[Session], responses=ASKED)
def get_session(
    context: Ctx, accounts: Held, asked: Heard, response: Response
) -> Envelope[Session]:
    """Whether the browser is signed in, and as whom. It is answered 200 either way."""
    current = accounts.session_of(asked)
    if current is None or asked.session is None:
        return envelope(context, NOBODY)
    if current.put_forward_s is not None:
        cookies = accounts.cookies
        cookies.give(response, cookies.session, asked.session, current.put_forward_s)
    return envelope(context, Session(signed_in=True, email=current.account.email))


@router.delete("/auth/session", response_model=Envelope[Session], responses=BARE)
def sign_out(
    context: Ctx, accounts: Held, asked: Heard, response: Response, request_id: RequestId
) -> Envelope[Session]:
    """Sign the browser out. Its session is revoked, and not only forgotten."""
    current = accounts.session_of(asked)
    if current is not None:
        accounts.sign_out(current, request_id)
    # Taken back whether or not it opened anything, so that a browser is left with none.
    accounts.cookies.take_back(response, accounts.cookies.session)
    return envelope(context, NOBODY)


# What a person who has signed in can do.


@router.get("/me", response_model=Envelope[Me], responses=ASKED | NOT_SIGNED_IN)
def get_me(context: Ctx, accounts: Held, current: SignedInAs) -> Envelope[Me]:
    """The address of the account and its preferences."""
    return envelope(context, accounts.me(current))


@router.delete("/me", response_model=Envelope[Session], responses=BARE | NOT_SIGNED_IN)
def delete_me(
    context: Ctx,
    accounts: Held,
    current: SignedInAs,
    response: Response,
    request_id: RequestId,
) -> Envelope[Session]:
    """Delete the account and everything of it. It asks for a sign-in in the last ten minutes."""
    accounts.delete(current, request_id)
    accounts.cookies.take_back(response, accounts.cookies.session)
    return envelope(context, NOBODY)


@router.post(
    "/me/searches",
    response_model=Envelope[KeptSearch],
    responses=CHANGED | NOT_SIGNED_IN | NOT_YET,
)
def keep_search(
    body: KeepBody, context: Ctx, accounts: Held, current: SignedInAs
) -> Envelope[KeptSearch]:
    """Keep a search. What is kept is the spec, and a name worked out from it."""
    return envelope(context, accounts.keep_search(body.spec, current, context.release))


@router.get("/me/searches", response_model=Envelope[KeptSearches], responses=ASKED | NOT_SIGNED_IN)
def list_searches(context: Ctx, accounts: Held, current: SignedInAs) -> Envelope[KeptSearches]:
    """The searches a person has kept, the newest first."""
    return envelope(context, accounts.searches(current, context.release))


@router.delete(
    "/me/searches",
    response_model=Envelope[KeptSearches],
    responses=CHANGED | NOT_SIGNED_IN | NOT_FOUND,
)
def forget_search(
    body: ForgetBody, context: Ctx, accounts: Held, current: SignedInAs
) -> Envelope[KeptSearches]:
    """Take one search away, and give back those that are left."""
    return envelope(context, accounts.forget_search(body.search_id, current, context.release))


@router.post(
    "/me/recent", response_model=Envelope[RecentSearches], responses=CHANGED | NOT_SIGNED_IN
)
def keep_recent(
    body: KeepBody, context: Ctx, accounts: Held, current: SignedInAs
) -> Envelope[RecentSearches]:
    """Put a search among the last ten, where the person lets Burro keep them."""
    return envelope(context, accounts.keep_recent(body.spec, current, context.release))


@router.get("/me/recent", response_model=Envelope[RecentSearches], responses=ASKED | NOT_SIGNED_IN)
def list_recent(context: Ctx, accounts: Held, current: SignedInAs) -> Envelope[RecentSearches]:
    """The last ten searches, where the person lets Burro keep them."""
    return envelope(context, accounts.recent(current, context.release))


@router.delete(
    "/me/recent", response_model=Envelope[RecentSearches], responses=BARE | NOT_SIGNED_IN
)
def forget_recent(context: Ctx, accounts: Held, current: SignedInAs) -> Envelope[RecentSearches]:
    """Take every one of the last searches away."""
    return envelope(context, accounts.forget_recent(current, context.release))


@router.put(
    "/me/preferences", response_model=Envelope[Preferences], responses=CHANGED | NOT_SIGNED_IN
)
def set_preferences(
    body: PreferencesBody, context: Ctx, accounts: Held, current: SignedInAs
) -> Envelope[Preferences]:
    """Set a preference, and give back every preference as it now stands."""
    return envelope(context, accounts.set_preferences(body, current))


@router.get("/me/sessions", response_model=Envelope[Sessions], responses=ASKED | NOT_SIGNED_IN)
def list_sessions(context: Ctx, accounts: Held, current: SignedInAs) -> Envelope[Sessions]:
    """Where a person is signed in."""
    return envelope(context, accounts.sessions(current))


@router.delete(
    "/me/sessions",
    response_model=Envelope[Sessions],
    responses=CHANGED | NOT_SIGNED_IN | NOT_FOUND,
)
def end_sessions(
    body: SignOutBody,
    context: Ctx,
    accounts: Held,
    current: SignedInAs,
    response: Response,
    request_id: RequestId,
) -> Envelope[Sessions]:
    """Sign out of one browser, or of every one."""
    left = accounts.end_sessions(body, current, request_id)
    if not left.signed_in:
        accounts.cookies.take_back(response, accounts.cookies.session)
    return envelope(context, left)


@router.get("/me/export", response_model=Envelope[Export], responses=ASKED | NOT_SIGNED_IN)
def export_me(context: Ctx, accounts: Held, current: SignedInAs) -> Envelope[Export]:
    """Everything Burro holds of the account."""
    return envelope(context, accounts.export(current, context.release))
