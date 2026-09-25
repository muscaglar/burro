"""The app: `create_app(deps)` for tests and for the service alike.

It holds one release in memory and no database. Nothing is kept for a search:
the client holds the spec and sends it again to rank, to explain and to share.
"""

from burro_core.explain import TemplateExplainer
from burro_core.interpret import Interpreter, RuleInterpreter
from burro_core.spec import SpecError
from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.routing import APIRoute
from starlette.exceptions import HTTPException

from burro_api.boundary import ERROR_CODE, Boundary
from burro_api.calls import InMemoryCallLog
from burro_api.cap import Cap
from burro_api.deps import Clock, Context, Deps, RandomIds, SystemClock, context_for
from burro_api.errors import ApiError, error_response, from_validation, spec_refused
from burro_api.loading import load_census, load_income, load_release
from burro_api.providers.choose import Choice, by_rules, never_called
from burro_api.reader import ModelInterpreter
from burro_api.routes import areas, census, income, interpret, meta, places, rank, shares
from burro_api.routes.common import NotModified
from burro_api.settings import Settings
from burro_api.stores import InMemoryShareStore
from burro_api.wire import ErrorCode, FieldProblem

__all__ = ["Deps", "create_app", "deps_from"]

TITLE = "Burro API"
# The version of the contract the routes are built to, not of the code.
CONTRACT_VERSION = "2"
DESCRIPTION = (
    "Ranks named neighbourhoods for a preference spec and shows its working. "
    "Every response says whether the data behind it is synthetic, and whether the release "
    "is a preview that is not finished."
)

_CODE_FOR_STATUS = {
    400: ErrorCode.MALFORMED_JSON,
    404: ErrorCode.NOT_FOUND,
    405: ErrorCode.METHOD_NOT_ALLOWED,
}


def _operation_id(route: APIRoute) -> str:
    # The name of the route, which is what a generated client will call it. It
    # is the name of the route's function unless the route was given one of
    # its own: route 2 is `rank`, and its function cannot be, beside core's.
    return route.name


def identify(request: Request) -> None:
    """The place for sign-in. Out of scope for this build: every caller is anonymous.

    An identity read from a header goes here. No route needs one, and no spec
    or share holds a user id.
    """


def admit(request: Request) -> None:
    """The place for a limit on what one caller may ask. None is built: every call is let in.

    The one limit there is does not stand here. It is a cap on calls to a
    model, for the whole service, and it stands where a model is called
    (`cap.py`, ADR 0032): only there is it known that a call is about to be
    made. It counts calls, and nothing of who made them.

    A call that is refused here must still be answered by the rule-based
    interpreter and the form. Never by a login wall.
    """


def _refuse(
    request: Request, context: Context, code: ErrorCode, fields: tuple[FieldProblem, ...] = ()
) -> JSONResponse:
    # Kept for the request's log line. The code is ours; nothing sent is kept.
    request.scope[ERROR_CODE] = code.value
    return error_response(context.meta, code, fields)


def _install_handlers(app: FastAPI, context: Context) -> None:
    def invalid(request: Request, error: Exception) -> JSONResponse:
        assert isinstance(error, RequestValidationError)
        # Only `loc` and `type` are read. What was sent is in the rest.
        code, fields = from_validation(error.errors())
        return _refuse(request, context, code, fields)

    def refused(request: Request, error: Exception) -> JSONResponse:
        assert isinstance(error, ApiError)
        return _refuse(request, context, error.code, error.fields)

    def unrankable(request: Request, error: Exception) -> JSONResponse:
        assert isinstance(error, SpecError)
        refusal = spec_refused(error.problems)
        return _refuse(request, context, refusal.code, refusal.fields)

    def unrouted(request: Request, error: Exception) -> JSONResponse:
        assert isinstance(error, HTTPException)
        code = _CODE_FOR_STATUS.get(error.status_code, ErrorCode.INTERNAL_ERROR)
        response = _refuse(request, context, code)
        allow = (error.headers or {}).get("Allow")
        if allow:
            response.headers["Allow"] = allow
        return response

    def unchanged(request: Request, error: Exception) -> Response:
        assert isinstance(error, NotModified)
        return Response(status_code=304, headers=error.headers)

    app.add_exception_handler(NotModified, unchanged)
    app.add_exception_handler(RequestValidationError, invalid)
    app.add_exception_handler(ApiError, refused)
    app.add_exception_handler(SpecError, unrankable)
    app.add_exception_handler(HTTPException, unrouted)


def create_app(deps: Deps) -> FastAPI:
    context = context_for(deps)
    # The OpenAPI document is published as a file, `contracts/openapi.json`,
    # and not served: the routes of the service are the routes of the contract.
    app = FastAPI(
        title=TITLE,
        version=CONTRACT_VERSION,
        description=DESCRIPTION,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        generate_unique_id_function=_operation_id,
        # A path with a slash too many is no route. A redirect would answer
        # with no envelope, and with the path, share id and all, in a header.
        redirect_slashes=False,
    )
    app.state.context = context

    gates = [Depends(identify), Depends(admit)]
    groups = (interpret, rank, areas, census, income, places, shares, meta)
    routers = [group.router for group in groups]
    for router in routers:
        app.include_router(router, dependencies=gates)
    app.include_router(meta.health)

    _install_handlers(app, context)
    # The routes as they were declared. How the framework nests them once
    # they are included is its own business, and has changed between versions.
    declared = [route for router in (*routers, meta.health) for route in router.routes]
    app.add_middleware(Boundary, context=context, routes=declared)
    return app


def _reader(settings: Settings, choice: Choice, clock: Clock) -> Interpreter:
    """The model-backed reader if a provider was chosen, and otherwise the rules.

    A reader that asks a model is handed the cap on its calls, always: the
    settings hold a number for each, whether or not one was set.
    """
    if choice.client is None:
        return RuleInterpreter()
    return ModelInterpreter(
        choice.client,
        model=choice.model,
        max_tokens=settings.model_max_tokens,
        timeout_s=settings.model_timeout_s,
        with_settings=choice.with_settings,
        cap=Cap(settings.model_calls_per_minute, settings.model_calls_per_day, clock.now),
    )


def _as_capped(settings: Settings, choice: Choice) -> Choice:
    """`choice`, or the rules where either cap on calls to a model is nought.

    A model that is never called reads nothing, so the service is then as it
    is with no model set, and tells people so.
    """
    if settings.model_calls_per_minute and settings.model_calls_per_day:
        return choice
    return never_called(choice)


def deps_from(settings: Settings, choice: Choice | None = None) -> Deps:
    """What the running service depends on: one release, loaded now, and nothing on disk.

    `choice` is who reads what is typed, as `providers.choose` made it of the
    environment. The reader and what people are told are both taken from it,
    so the two cannot be at odds. With none given, the rules read.
    """
    choice = _as_capped(settings, by_rules() if choice is None else choice)
    release = load_release(settings.release_dir)
    clock = SystemClock()
    return Deps(
        release=release,
        census=load_census(settings.census_dir, release, settings.census_named),
        income=load_income(settings.income_dir, release, settings.income_named),
        interpreter=_reader(settings, choice, clock),
        explainer=TemplateExplainer(),
        shares=InMemoryShareStore(),
        calls=InMemoryCallLog(),
        clock=clock,
        ids=RandomIds(),
        told=choice.told,
        model_id=choice.model,
        model_timeout_s=settings.model_timeout_s,
        allowed_origins=settings.allowed_origins,
    )
