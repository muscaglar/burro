"""The row of the catalogue a measure writes for its release.

Core decides what a feature is: its name, its unit, which way is more, what
kind of thing it is, what it describes and which family of the settings shows
it. A release repeats all of it, so that it can be read alone, and core
refuses a release that says anything else. A measure says here only what the
build knows and core does not: the sources, the period and the sentence of a
methods page.

A measure whose figure is not what core's name says it is gives a name of its
own. Its row is then not core's, and the build leaves the measure out.

How a figure was made is the build's to say, and never copied from core: it is
the kind of the method its rows of evidence name. A figure that is modelled or
averaged is so carried only where core says the same of the feature.
"""

from collections.abc import Iterable

from burro_core.catalogue import FEATURES
from burro_core.ids import FeatureId, NativeResolution
from burro_core.ids import Method as MadeBy
from burro_core.release import Metric

from burro_pipeline.evidence.method import Method


def catalogue_row(
    feature_id: FeatureId,
    *,
    method: Method,
    source_ids: Iterable[str],
    vintage: str,
    definition: str,
    label: str | None = None,
    native_resolution: NativeResolution | None = None,
    rankable: bool = True,
) -> Metric:
    """The row of one measure: what core decides of the feature, and what the build found.

    `method` is the one the rows of the measure name. `label` and
    `native_resolution` are given only where the figure is not what core says
    the feature is. `rankable` is false where the release shows the figure and
    ranks no area on it by itself.
    """
    core = FEATURES[feature_id]
    return Metric(
        feature_id=core.feature_id,
        label=core.label if label is None else label,
        short_label=core.short_label,
        dimension=core.dimension,
        unit=core.unit,
        polarity=core.polarity,
        kind=core.kind,
        describes=core.describes,
        family=core.family,
        method=MadeBy(method.kind.value),
        in_likeness=core.in_likeness,
        native_resolution=core.native_resolution
        if native_resolution is None
        else native_resolution,
        source_ids=tuple(sorted(set(source_ids))),
        vintage=vintage,
        rankable=rankable,
        definition=definition,
    )
