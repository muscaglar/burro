"""The edge of the service: what every request passes on the way in and out.

One middleware, outermost, does five things that must hold for every route:

- it refuses a body that is not JSON or is larger than 16 KiB, before anything reads it;
- it says on every response, errors included, whether the release is synthetic and
  whether it is a preview;
- it catches whatever a route lets fall, so that the server never gets to
  print a traceback, whose last line is the exception's message;
- it writes the one log line for the request, from the route template;
- it tells a browser whether the page that called may read the answer.

The server's own access log is switched off. It would write the path, and a
path can hold a share id.

The origins a browser may call from are a list, and an origin is on it or it
is not: there is no pattern, no "every origin" and no cookie. It is done here
and not by the framework's own middleware, which answers a browser it refuses
in words of its own and not in the error envelope, and which would not see
the refusals this middleware makes itself.
"""

from collections.abc import Sequence

from starlette.datastructures import Headers, MutableHeaders
from starlette.responses import Response
from starlette.routing import BaseRoute, Match
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from burro_api import logs
from burro_api.deps import Context
from burro_api.errors import error_response
from burro_api.wire import MAX_BODY_BYTES, ErrorCode

UNMATCHED = "unmatched"
# Where the request's id and its error code are kept for the routes and the log line.
REQUEST_ID = "burro.request_id"
ERROR_CODE = "burro.error_code"
NO_STORE = "no-store"
JSON = "application/json"
# What a page on an allowed origin may send, and which of our headers it may read.
ALLOWED_METHODS = "GET, POST"
ALLOWED_HEADERS = "Content-Type"
EXPOSED_HEADERS = "X-Burro-Synthetic, X-Burro-Preview, X-Request-Id"
# How long a browser may remember that it asked, in seconds.
ASK_AGAIN_AFTER = "600"

# A method is whatever the client wrote. Only these are logged as they are.
_METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"})
_WITH_BODY = frozenset({"POST", "PUT", "PATCH"})


def template_of(scope: Scope, routes: Sequence[BaseRoute]) -> tuple[str, bool]:
    """The route template, such as `/v1/shares/{share_id}`, and whether the method is its own.

    Never the path that was asked for. It is worked out here, from the routes
    themselves, so that a request refused before it is routed is logged by its
    template like any other.
    """
    partial = UNMATCHED
    for route in routes:
        match, _ = route.matches(scope)
        path = getattr(route, "path", None)
        if not isinstance(path, str):
            continue
        if match is Match.FULL:
            return path, True
        if match is Match.PARTIAL and partial == UNMATCHED:
            # The path is a route's, and the method is not.
            partial = path
    return partial, False


def allowed_origin(headers: Headers, allowed: Sequence[str]) -> str | None:
    """The origin the call came from, if it is on the list, and otherwise nothing.

    What is given back is the entry of the list and never the header, so that
    nothing a caller wrote is ever sent back to it.
    """
    sent = headers.get("origin")
    return next((origin for origin in allowed if origin == sent), None)


def _asks_first(scope: Scope, headers: Headers) -> bool:
    """Whether a browser is asking what it may send, before it sends it."""
    return scope["method"] == "OPTIONS" and "access-control-request-method" in headers


def _refusal(scope: Scope) -> ErrorCode | None:
    """Why a body will not be read, from its headers alone."""
    headers = Headers(scope=scope)
    media_type = headers.get("content-type", "").split(";")[0].strip().lower()
    if media_type != JSON:
        return ErrorCode.UNSUPPORTED_MEDIA_TYPE
    length = headers.get("content-length", "")
    if length.isdecimal() and int(length) > MAX_BODY_BYTES:
        return ErrorCode.BODY_TOO_LARGE
    return None


async def _read(receive: Receive) -> bytes | None:
    """The whole body, or `None` once it is larger than it may be.

    A client can leave out the length or understate it, so the bytes are
    counted as they arrive.
    """
    chunks: list[bytes] = []
    size = 0
    while True:
        message = await receive()
        if message["type"] != "http.request":
            return b"".join(chunks)
        chunk: bytes = message.get("body", b"")
        size += len(chunk)
        if size > MAX_BODY_BYTES:
            return None
        chunks.append(chunk)
        if not message.get("more_body", False):
            return b"".join(chunks)


def _replay(body: bytes, receive: Receive) -> Receive:
    sent = False

    async def replay() -> Message:
        nonlocal sent
        if sent:
            return await receive()
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    return replay


class Boundary:
    def __init__(self, app: ASGIApp, context: Context, routes: Sequence[BaseRoute]) -> None:
        self._app = app
        self._context = context
        self._routes = routes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        clock, meta = self._context.deps.clock, self._context.meta
        began = clock.elapsed()
        # Made here, and never taken from a header: a header is what the client wrote.
        request_id = self._context.deps.ids.request_id()
        scope[REQUEST_ID] = request_id
        method = scope["method"] if scope["method"] in _METHODS else "OTHER"
        route, routed = template_of(scope, self._routes)
        asked = Headers(scope=scope)
        origin = allowed_origin(asked, self._context.deps.allowed_origins)
        status = 0

        async def respond(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                headers = MutableHeaders(scope=message)
                headers["X-Burro-Synthetic"] = "true" if meta.synthetic else "false"
                headers["X-Burro-Preview"] = "true" if meta.preview else "false"
                headers["X-Request-Id"] = request_id
                # Only a route that is a function of the release alone says otherwise.
                headers.setdefault("Cache-Control", NO_STORE)
                # Said of every response, allowed or not, so that a cache never
                # hands the answer for one origin to a page on another.
                headers.add_vary_header("Origin")
                if origin is not None:
                    headers["Access-Control-Allow-Origin"] = origin
                    headers["Access-Control-Expose-Headers"] = EXPOSED_HEADERS
            await send(message)

        async def refuse(code: ErrorCode) -> None:
            scope[ERROR_CODE] = code.value
            await error_response(meta, code)(scope, receive, respond)

        try:
            if origin is not None and _asks_first(scope, asked):
                # From any other origin it is no question at all, and the
                # router answers it as a method the route does not take.
                told = {
                    "Access-Control-Allow-Methods": ALLOWED_METHODS,
                    "Access-Control-Allow-Headers": ALLOWED_HEADERS,
                    "Access-Control-Max-Age": ASK_AGAIN_AFTER,
                }
                await Response(status_code=204, headers=told)(scope, receive, respond)
            # A request for no route, or with a method its route does not take,
            # is answered by the router, which never reads the body.
            elif routed and method in _WITH_BODY:
                refused = _refusal(scope)
                body = None if refused else await _read(receive)
                if refused or body is None:
                    await refuse(refused or ErrorCode.BODY_TOO_LARGE)
                else:
                    await self._app(scope, _replay(body, receive), respond)
            else:
                await self._app(scope, receive, respond)
        except Exception as error:
            # Never raised again. The server would print it, message and all.
            logs.log_failure(error, request_id=request_id, method=method, route=route)
            if status == 0:
                await refuse(ErrorCode.INTERNAL_ERROR)
        finally:
            line: dict[str, logs.Value] = {
                "request_id": request_id,
                "method": method,
                "route": route,
                "status": status,
                "latency_ms": round((clock.elapsed() - began) * 1000),
                "release_id": meta.release_id,
                "engine_version": meta.engine_version,
                "synthetic": meta.synthetic,
                "preview": meta.preview,
            }
            code = scope.get(ERROR_CODE)
            if isinstance(code, str):
                line["error_code"] = code
            logs.event("request", **line)
