"""Routes 11 and 12: what a form needs, and whether the service is up.

Route 11 returns the vocabulary, both defaults and the limits. With it and the
routes that rank, the product works as a form with no model at all. It also
says who reads what is typed, and what people are told of it, so that no
client writes a provider's terms of its own.
"""

from burro_core.catalogue import CATALOGUE_VERSION, FAMILIES
from burro_core.census import offer
from burro_core.explain import REASON_MIN_UTILITY, TRADE_OFF_MAX_UTILITY
from burro_core.ids import Mode, Tenure, segments_for
from burro_core.interpret import MAX_TEXT
from burro_core.release import Cutoffs, Release, recipes_held
from burro_core.spec import LIMITS
from fastapi import APIRouter, Request, Response

from burro_api.deps import Ctx
from burro_api.providers.choose import Told
from burro_api.providers.terms import Provider
from burro_api.routes.common import (
    ANY_ROUTE,
    NOT_MODIFIED,
    PREFIX,
    default_for,
    envelope,
    of_the_release,
)
from burro_api.wire import (
    MAX_BODY_BYTES,
    Defaults,
    Envelope,
    FamilyLabel,
    Health,
    Holds,
    MetaData,
    Reader,
    ServedLimits,
)

router = APIRouter(prefix=PREFIX)
health = APIRouter()


def _limits(release: Release) -> ServedLimits:
    return ServedLimits(
        **{name: getattr(LIMITS, name) for name in type(LIMITS).model_fields},
        # A commute may not be capped above what the release routed (section 6.1).
        cutoff_minutes=Cutoffs(
            pt=release.cutoff(Mode.PT),
            cycle=release.cutoff(Mode.CYCLE),
            walk=release.cutoff(Mode.WALK),
        ),
        max_text=MAX_TEXT,
        max_body_bytes=MAX_BODY_BYTES,
        reason_min_utility=REASON_MIN_UTILITY,
        trade_off_max_utility=TRADE_OFF_MAX_UTILITY,
    )


def _holds(release: Release) -> Holds:
    """Whether the release can answer a journey or a budget at all. Asked of the release itself."""
    return Holds(
        journeys=bool(release.places),
        costs=any(
            release.costed(tenure, segment) for tenure in Tenure for segment in segments_for(tenure)
        ),
    )


def _reader(told: Told) -> Reader:
    """What people are told of who reads, as it is served. Nothing of how the service is set."""
    return Reader(
        model_reads=told.model_reads,
        provider=None if told.provider is None else Provider(told.provider),
        company=told.company,
        notice=told.notice,
        terms_url=told.terms_url,
        settings_sent=told.settings_sent,
    )


@router.get("/meta", response_model=Envelope[MetaData], responses=ANY_ROUTE | NOT_MODIFIED)
def get_meta(context: Ctx, request: Request, response: Response) -> Envelope[MetaData]:
    """The release that is loaded, the vocabulary, the defaults, the limits, and who reads."""
    told = context.deps.told
    of_the_release(context, request, response, told)
    release = context.release
    manifest = release.manifest
    return envelope(
        context,
        MetaData(
            release_id=manifest.release_id,
            built_at=manifest.built_at,
            synthetic=manifest.synthetic,
            preview=manifest.preview,
            engine_version=context.meta.engine_version,
            catalogue_version=CATALOGUE_VERSION,
            counts=manifest.counts,
            holds=_holds(release),
            # Every source is credited, with its licence.
            attributions=manifest.sources,
            features=release.metrics,
            # The vibes the release carries, which hold one way of gritty and not both.
            tags=release.vibes,
            recipes=recipes_held(release),
            families=tuple(
                FamilyLabel(family=family, label=label) for family, label in FAMILIES.items()
            ),
            gritty_variant=manifest.gritty_variant,
            defaults=Defaults(
                rent=default_for(release, Tenure.RENT), buy=default_for(release, Tenure.BUY)
            ),
            limits=_limits(release),
            reader=_reader(told),
            # The words of the block that offers the census. No figure, and no area.
            census=offer(context.deps.census),
        ),
    )


@health.get("/healthz", response_model=Health, responses=ANY_ROUTE)
def healthz() -> Health:
    """Whether the service is up. It says nothing about the release, so it has no `meta`."""
    return Health(ok=True)
