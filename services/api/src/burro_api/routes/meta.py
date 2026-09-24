"""Routes 11 and 12: what a form needs, and whether the service is up.

Route 11 returns the vocabulary, both defaults and the limits. With it and the
routes that rank, the product works as a form with no model at all.
"""

from burro_core.catalogue import CATALOGUE_VERSION, TAGS
from burro_core.ids import Mode, Tenure
from burro_core.interpret import MAX_TEXT
from burro_core.release import Cutoffs, Release
from burro_core.spec import LIMITS
from fastapi import APIRouter, Response

from burro_api.deps import Ctx
from burro_api.routes.common import ANY_ROUTE, PREFIX, default_for, envelope, of_the_release
from burro_api.wire import (
    MAX_BODY_BYTES,
    Defaults,
    Envelope,
    Health,
    MetaData,
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
    )


@router.get("/meta", response_model=Envelope[MetaData], responses=ANY_ROUTE)
def get_meta(context: Ctx, response: Response) -> Envelope[MetaData]:
    """The release that is loaded, the vocabulary, the defaults and the limits."""
    of_the_release(context, response)
    release = context.release
    manifest = release.manifest
    return envelope(
        context,
        MetaData(
            release_id=manifest.release_id,
            built_at=manifest.built_at,
            synthetic=manifest.synthetic,
            engine_version=context.meta.engine_version,
            catalogue_version=CATALOGUE_VERSION,
            counts=manifest.counts,
            # Every source is credited, with its licence.
            attributions=manifest.sources,
            features=release.metrics,
            tags=tuple(TAGS.values()),
            defaults=Defaults(
                rent=default_for(release, Tenure.RENT), buy=default_for(release, Tenure.BUY)
            ),
            limits=_limits(release),
        ),
    )


@health.get("/healthz", response_model=Health, responses=ANY_ROUTE)
def healthz() -> Health:
    """Whether the service is up. It says nothing about the release, so it has no `meta`."""
    return Health(ok=True)
