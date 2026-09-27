"""The gate of accounts: what every request to a route of accounts passes first.

It stands before anything is made of what was sent. A request is heard only from the
website, which shows its secret, and what changes anything only from a page of the
website. So nothing is made of a body that anybody else sent, and it never reaches a
route. The edge of the service has counted its bytes by then, and no more.

It is a kind of route and not a dependency, because a dependency is asked only once the
body has been made a record of.
"""

from collections.abc import Callable, Coroutine
from typing import Annotated, Any, cast

from fastapi import Depends, Request, Response
from fastapi.routing import APIRoute

from burro_api.accounts.service import Accounts, Asked, Current
from burro_api.boundary import REQUEST_ID
from burro_api.deps import Context
from burro_api.errors import ApiError
from burro_api.wire import ErrorCode

# Where what was heard of a request is kept for its route.
ASKED = "burro_asked"

Handler = Callable[[Request], Coroutine[Any, Any, Response]]


def _accounts(request: Request) -> Accounts:
    found = cast(Context, request.app.state.context).deps.accounts
    if found is None:
        # The routes are served only where accounts are on, so this is never met.
        raise ApiError(ErrorCode.NOT_FOUND)
    return found


class OfTheWebsite(APIRoute):
    """A route that hears the website alone, before anything is made of what was sent."""

    def get_route_handler(self) -> Handler:
        route = super().get_route_handler()

        async def heard(request: Request) -> Response:
            made = request.scope.get(REQUEST_ID)
            asked = _accounts(request).heard(
                request.method,
                request.headers,
                request.url.query,
                request.cookies,
                made if isinstance(made, str) else "",
            )
            setattr(request.state, ASKED, asked)
            return await route(request)

        return heard


def _asked(request: Request) -> Asked:
    return cast(Asked, getattr(request.state, ASKED))


def _signed_in(
    asked: Annotated[Asked, Depends(_asked)],
    accounts: Annotated[Accounts, Depends(_accounts)],
    response: Response,
) -> Current:
    """Who is signed in, by the session and by nothing else that was sent."""
    current = accounts.session_of(asked)
    if current is None or asked.session is None:
        raise ApiError(ErrorCode.NOT_SIGNED_IN)
    if current.put_forward_s is not None:
        # The session was put forward, so the cookie is given again to last as long.
        cookies = accounts.cookies
        cookies.give(response, cookies.session, asked.session, current.put_forward_s)
    return current


Held = Annotated[Accounts, Depends(_accounts)]
Heard = Annotated[Asked, Depends(_asked)]
SignedInAs = Annotated[Current, Depends(_signed_in)]
