"""The measures of a build: one list, and one way to work each out.

Each measure has a module of its own, which reads its publisher's file and
calls a named method. This module is the list of them, for the step that puts
a release together. It holds no arithmetic.

Every measure is called the same way, `measure.build(inputs, ground)`, and
gives the same things back:

| What | It is |
|---|---|
| `worked` | The figure of every area, or why an area has none: a `Worked` by area id |
| `rows` | The row of evidence behind each figure, and behind each figure that is missing |
| `metric` | The row of the catalogue: the name, the unit, the period and every source |
| `files` | The receipt of every file a figure was worked out from |
| `geography` | What the rows of the publisher's file are keyed by, as the file was found to be |

`ground` is the geography of the build: the spine and the land. A measure takes
from it what it needs and no more.

A measure is left out of a release, and never filled in, when its file has no
receipt, when a check of its figures holds it back, or when what it would say
is not what core says the measure is. The step that puts the release together
says which, and why.

A measure is held back by what a check of its figures found: that they do not
yet say what the measure is named for. It is worked out at every build all
the same, so that whoever settles it has the figures. What holds it back is
written in its own module, as `HELD_BACK`, and is taken out in a change a
person reads. Nothing core says of the measure brings it in before then.

One measure is held back by what has not been checked, and not by what a check
found: private outdoor space waits for its row of the proxy audit, which
decision record 0006 asks for before it is in a release.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Protocol

from burro_core.catalogue import FEATURES
from burro_core.ids import FeatureId
from burro_core.release import DECIDED_BY_CORE, Metric

from burro_pipeline.cells.land import Land
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import (
    air_no2,
    brands_nearby,
    bus_routes,
    census_msoa,
    centre_compact,
    centre_small,
    connected,
    conservation_cover,
    culture_venues,
    culture_venues_per_homes,
    evening_cluster_exposure,
    gp_walk,
    green_cover,
    grocery_walk,
    highstreet_access,
    homes_density,
    homes_flats,
    homes_higher_bands,
    homes_post2000,
    homes_pre1919,
    households_dependent_children,
    households_one_person,
    incident_antisocial,
    incident_criminal_damage,
    land_use,
    listed_buildings,
    noise,
    park_facilities,
    park_proximity,
    pharmacy_walk,
    play_space_proximity,
    price_median,
    price_rise,
    private_outdoor_space,
    residents_aged_20_34,
    residents_aged_65_over,
    road_major_exposure,
    school_primary_nearby,
    station_walk,
    venue_food_drink,
    venue_food_drink_per_homes,
    venues_nearby,
    water_access,
)
from burro_pipeline.derive.census_msoa import Of as OfTheCensus
from burro_pipeline.derive.methods import Worked
from burro_pipeline.evidence.method import Kind, Method
from burro_pipeline.evidence.receipt import Geography, Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.evidence.served import Behind
from burro_pipeline.inputs import Inputs

# How a tag is worked out. Core works it out, and the row of a tag names this.
TAGGED = Method(
    derivation_id="tag_of_percentiles@1",
    sentence="The mean of where the area stands on each measure of the tag's recipe, weighted "
    "as the recipe weighs them, and not given where under 60 in 100 of the recipe's weight has "
    "a figure.",
    kind=Kind.AVERAGED,
    parameters={"enough_in_100": 60},
    code="burro_core.catalogue",
)


@dataclass(frozen=True)
class Ground:
    """The geography a build works its figures out on."""

    spine: Spine
    land: Land


class Measured(Protocol):
    """What every measure gives back. Each module's own record holds these, and more of its own."""

    @property
    def worked(self) -> Mapping[str, Worked]: ...
    @property
    def rows(self) -> tuple[EvidenceRow, ...]: ...
    @property
    def metric(self) -> Metric: ...
    @property
    def files(self) -> tuple[Receipt, ...]: ...
    @property
    def geography(self) -> Geography: ...


@dataclass(frozen=True)
class Measure:
    """One measure of a build: what it is, and how it is worked out."""

    feature: FeatureId
    # The registry id of the publisher's file the measure is read from.
    source: str
    # Whether a publisher's name for a file is the name of the file the measure reads. A
    # source may hold several files, and the measure reads one.
    reads: Callable[[str], bool]
    # The arithmetic, as a methods page prints it. The first is the one a row names.
    methods: tuple[Method, ...]
    # What the figure cannot see, as the product would say it beside the figure.
    cannot_see: tuple[str, ...]
    build: Callable[[Inputs, Ground], Measured]
    # Whether the publisher cuts the product to squares of the National Grid, a file for each,
    # so that a figure may rest on the files of several squares.
    in_squares: bool = False
    # Whether the publisher gives the product as a file for each part of the whole, as the
    # food hygiene register gives one for each authority, so that a figure rests on them all.
    in_parts: bool = False
    # What keeps the measure out of a release while its row of the catalogue is not core's:
    # what is not settled, and whose it is to settle. A measure that is carried waits on
    # nothing. The build and the coverage report say it beside the rule.
    waits_on: tuple[str, ...] = ()
    # What a check of the figures found that keeps the measure out of every release,
    # whatever core says of it, and what would settle it. A measure that stood its check
    # holds nothing here.
    held_back: tuple[str, ...] = ()


def says_what_core_says(metric: Metric) -> bool:
    """Whether a row of the catalogue names and measures the feature as core does.

    A release whose row says anything else is refused by core. So a measure
    whose row does is left out of the release, and the build says so.
    """
    core = FEATURES[metric.feature_id]
    return all(getattr(metric, name) == getattr(core, name) for name in DECIDED_BY_CORE)


def _of_stops(feature: FeatureId) -> Measure:
    """One of the measures of how near stops are. Each is read from the national file of
    stops, and the two of railway stations from the file of stations too."""
    of = connected.MEASURES[feature]
    built = connected.builder(feature)
    return Measure(
        feature,
        connected.SOURCE,
        connected.is_the_file,
        connected.METHODS[feature],
        of.cannot_see,
        lambda inputs, ground: built(inputs, ground.spine),
    )


def _of_land(feature: FeatureId) -> Measure:
    """One of the five shares of land. All five are read from one table."""
    of = land_use.MEASURES[feature]
    return Measure(
        feature,
        land_use.SOURCE,
        land_use.is_the_table,
        land_use.METHODS,
        of.cannot_see,
        land_use.builder(feature),
        waits_on=of.waits_on,
    )


def _of_venues(feature: FeatureId) -> Measure:
    """One of the six figures of cafes, gyms and pubs. All six are read from one file."""
    of = venues_nearby.MEASURES[feature]
    return Measure(
        feature,
        venues_nearby.SOURCE,
        venues_nearby.is_the_file,
        (of.method,),
        of.cannot_see,
        venues_nearby.builder(feature),
    )


def _of_brands(feature: FeatureId) -> Measure:
    """One of the measures of brands. All are read from one part of the file of places."""
    return Measure(
        feature,
        brands_nearby.SOURCE,
        brands_nearby.is_the_file,
        (brands_nearby.method_of(feature),),
        brands_nearby.cannot_see(feature),
        lambda inputs, ground: brands_nearby.build(inputs, ground.spine).one(feature),
    )


def _of_the_census(of: OfTheCensus, reads: Callable[[str], bool]) -> Measure:
    """One of the four shares of who lived in an area. Two tables of one source give them."""
    return Measure(
        FeatureId(of.key),
        census_msoa.SOURCE,
        reads,
        census_msoa.METHODS,
        of.cannot_see,
        lambda inputs, ground: census_msoa.build(of, inputs, ground.spine),
    )


_EVERY_OTHER: tuple[Measure, ...] = (
    Measure(
        air_no2.FEATURE,
        air_no2.SOURCE,
        air_no2.is_the_grid,
        air_no2.METHODS,
        air_no2.CANNOT_SEE,
        lambda inputs, ground: air_no2.build(inputs, ground.spine),
    ),
    Measure(
        bus_routes.FEATURE,
        bus_routes.SOURCE,
        bus_routes.is_the_file,
        bus_routes.METHODS,
        bus_routes.CANNOT_SEE,
        lambda inputs, ground: bus_routes.build(inputs, ground.spine),
    ),
    _of_stops(FeatureId.BUS_STOPS_NEARBY),
    Measure(
        centre_compact.FEATURE,
        centre_compact.SOURCE,
        centre_compact.is_the_file,
        centre_compact.METHODS,
        centre_compact.CANNOT_SEE,
        lambda inputs, ground: centre_compact.build(inputs, ground.spine),
        waits_on=centre_compact.WAITS_ON,
    ),
    Measure(
        centre_small.FEATURE,
        centre_small.SOURCE,
        centre_small.is_the_file,
        centre_small.METHODS,
        centre_small.CANNOT_SEE,
        lambda inputs, ground: centre_small.build(inputs, ground.spine),
        waits_on=centre_small.WAITS_ON,
    ),
    Measure(
        conservation_cover.FEATURE,
        conservation_cover.SOURCE,
        conservation_cover.is_the_file,
        conservation_cover.METHODS,
        conservation_cover.CANNOT_SEE,
        lambda inputs, ground: conservation_cover.build(inputs, ground.spine, ground.land),
    ),
    Measure(
        culture_venues.FEATURE,
        culture_venues.SOURCE,
        culture_venues.is_the_file,
        (culture_venues.METHOD,),
        culture_venues.CANNOT_SEE,
        lambda inputs, ground: culture_venues.build(inputs, ground.spine),
    ),
    Measure(
        culture_venues_per_homes.FEATURE,
        culture_venues_per_homes.SOURCE,
        culture_venues_per_homes.is_the_file,
        culture_venues_per_homes.METHODS,
        culture_venues_per_homes.CANNOT_SEE,
        lambda inputs, ground: culture_venues_per_homes.build(inputs, ground.spine),
    ),
    Measure(
        evening_cluster_exposure.FEATURE,
        evening_cluster_exposure.SOURCE,
        evening_cluster_exposure.is_the_file,
        evening_cluster_exposure.METHODS,
        evening_cluster_exposure.CANNOT_SEE,
        lambda inputs, ground: evening_cluster_exposure.build(inputs, ground.spine),
    ),
    Measure(
        gp_walk.FEATURE,
        gp_walk.SOURCE,
        gp_walk.is_the_report,
        gp_walk.METHODS,
        gp_walk.CANNOT_SEE,
        lambda inputs, ground: gp_walk.build(inputs, ground.spine),
    ),
    Measure(
        green_cover.FEATURE,
        green_cover.SOURCE,
        green_cover.is_a_tile,
        green_cover.METHODS,
        green_cover.CANNOT_SEE,
        lambda inputs, ground: green_cover.build(inputs, ground.spine, ground.land),
        in_squares=True,
    ),
    Measure(
        grocery_walk.FEATURE,
        grocery_walk.SOURCE,
        grocery_walk.is_the_file,
        grocery_walk.METHODS,
        grocery_walk.CANNOT_SEE,
        lambda inputs, ground: grocery_walk.build(inputs, ground.spine),
    ),
    Measure(
        highstreet_access.FEATURE,
        highstreet_access.SOURCE,
        highstreet_access.is_the_file,
        highstreet_access.METHODS,
        highstreet_access.CANNOT_SEE,
        lambda inputs, ground: highstreet_access.build(inputs, ground.spine),
    ),
    Measure(
        homes_density.FEATURE,
        homes_density.SOURCE,
        homes_density.is_the_table,
        homes_density.METHODS,
        homes_density.CANNOT_SEE,
        lambda inputs, ground: homes_density.build(inputs, ground.spine, ground.land),
    ),
    Measure(
        homes_flats.FEATURE,
        homes_flats.SOURCE,
        homes_flats.is_the_table,
        homes_flats.METHODS,
        homes_flats.CANNOT_SEE,
        lambda inputs, ground: homes_flats.build(inputs, ground.spine),
    ),
    Measure(
        homes_higher_bands.FEATURE,
        homes_higher_bands.SOURCE,
        homes_higher_bands.is_the_table,
        homes_higher_bands.METHODS,
        homes_higher_bands.CANNOT_SEE,
        lambda inputs, ground: homes_higher_bands.build(inputs, ground.spine),
    ),
    Measure(
        homes_post2000.FEATURE,
        homes_post2000.SOURCE,
        homes_post2000.is_the_table,
        homes_post2000.METHODS,
        homes_post2000.CANNOT_SEE,
        lambda inputs, ground: homes_post2000.build(inputs, ground.spine),
    ),
    Measure(
        homes_pre1919.FEATURE,
        homes_pre1919.SOURCE,
        homes_pre1919.is_the_table,
        homes_pre1919.METHODS,
        homes_pre1919.CANNOT_SEE,
        lambda inputs, ground: homes_pre1919.build(inputs, ground.spine),
    ),
    _of_the_census(
        households_dependent_children.MEASURE, households_dependent_children.is_the_table
    ),
    _of_the_census(households_one_person.MEASURE, households_one_person.is_the_table),
    Measure(
        incident_antisocial.FEATURE,
        incident_antisocial.SOURCE,
        incident_antisocial.is_the_zip,
        incident_antisocial.METHODS,
        incident_antisocial.CANNOT_SEE,
        lambda inputs, ground: incident_antisocial.build(inputs, ground.spine),
    ),
    Measure(
        incident_criminal_damage.FEATURE,
        incident_criminal_damage.SOURCE,
        incident_criminal_damage.is_the_zip,
        incident_criminal_damage.METHODS,
        incident_criminal_damage.CANNOT_SEE,
        lambda inputs, ground: incident_criminal_damage.build(inputs, ground.spine),
    ),
    _of_land(FeatureId.LAND_GARDENS),
    _of_land(FeatureId.LAND_INDUSTRY),
    _of_land(FeatureId.LAND_STORAGE),
    _of_land(FeatureId.LAND_TRANSPORT_OTHER),
    _of_land(FeatureId.LAND_WOODLAND),
    Measure(
        listed_buildings.FEATURE,
        listed_buildings.SOURCE,
        listed_buildings.is_the_file,
        listed_buildings.METHODS,
        listed_buildings.CANNOT_SEE,
        lambda inputs, ground: listed_buildings.build(inputs, ground.spine, ground.land),
    ),
    Measure(
        noise.FEATURE,
        noise.SOURCE,
        noise.is_the_workbook,
        noise.METHODS,
        noise.CANNOT_SEE,
        lambda inputs, ground: noise.build(inputs, ground.spine),
    ),
    _of_stops(FeatureId.OVERGROUND_PROXIMITY),
    Measure(
        park_facilities.FEATURE,
        park_facilities.SOURCE,
        park_facilities.is_a_tile,
        park_facilities.METHODS,
        park_facilities.CANNOT_SEE,
        lambda inputs, ground: park_facilities.build(inputs, ground.spine),
        in_squares=True,
        waits_on=park_facilities.WAITS_ON,
    ),
    Measure(
        park_proximity.LARGE,
        park_proximity.SOURCE,
        park_proximity.is_a_tile,
        park_proximity.METHODS,
        park_proximity.CANNOT_SEE,
        lambda inputs, ground: park_proximity.build_large(inputs, ground.spine),
        in_squares=True,
    ),
    Measure(
        park_proximity.FEATURE,
        park_proximity.SOURCE,
        park_proximity.is_a_tile,
        park_proximity.METHODS,
        park_proximity.CANNOT_SEE,
        lambda inputs, ground: park_proximity.build(inputs, ground.spine),
        in_squares=True,
    ),
    Measure(
        pharmacy_walk.FEATURE,
        pharmacy_walk.SOURCE,
        pharmacy_walk.is_the_list,
        pharmacy_walk.METHODS,
        pharmacy_walk.CANNOT_SEE,
        lambda inputs, ground: pharmacy_walk.build(inputs, ground.spine),
    ),
    Measure(
        play_space_proximity.FEATURE,
        play_space_proximity.SOURCE,
        play_space_proximity.is_a_tile,
        play_space_proximity.METHODS,
        play_space_proximity.CANNOT_SEE,
        lambda inputs, ground: play_space_proximity.build(inputs, ground.spine),
        in_squares=True,
    ),
    Measure(
        price_median.FEATURE,
        price_median.SOURCE,
        price_median.is_a_file,
        price_median.METHODS,
        price_median.CANNOT_SEE,
        lambda inputs, ground: price_median.build(inputs, ground.spine),
    ),
    _of_stops(FeatureId.RAIL_PROXIMITY),
    _of_the_census(residents_aged_20_34.MEASURE, residents_aged_20_34.is_the_table),
    _of_the_census(residents_aged_65_over.MEASURE, residents_aged_65_over.is_the_table),
    Measure(
        price_rise.OVER[10],
        price_rise.SOURCE,
        price_rise.is_a_file,
        (price_rise.risen_over(10),),
        price_rise.CANNOT_SEE,
        lambda inputs, ground: price_rise.build(inputs, ground.spine, 10),
    ),
    Measure(
        price_rise.OVER[5],
        price_rise.SOURCE,
        price_rise.is_a_file,
        (price_rise.risen_over(5),),
        price_rise.CANNOT_SEE,
        lambda inputs, ground: price_rise.build(inputs, ground.spine, 5),
    ),
    Measure(
        private_outdoor_space.FEATURE,
        private_outdoor_space.SOURCE,
        private_outdoor_space.is_the_workbook,
        private_outdoor_space.METHODS,
        private_outdoor_space.CANNOT_SEE,
        lambda inputs, ground: private_outdoor_space.build(inputs, ground.spine),
        waits_on=private_outdoor_space.WAITS_ON,
        held_back=private_outdoor_space.HELD_BACK,
    ),
    Measure(
        road_major_exposure.FEATURE,
        road_major_exposure.SOURCE,
        road_major_exposure.is_the_network,
        road_major_exposure.METHODS,
        road_major_exposure.CANNOT_SEE,
        lambda inputs, ground: road_major_exposure.build(inputs, ground.spine),
    ),
    Measure(
        school_primary_nearby.FEATURE,
        school_primary_nearby.SOURCE,
        school_primary_nearby.is_the_register,
        school_primary_nearby.METHODS,
        school_primary_nearby.CANNOT_SEE,
        lambda inputs, ground: school_primary_nearby.build(inputs, ground.spine),
    ),
    Measure(
        station_walk.FEATURE,
        station_walk.SOURCE,
        station_walk.is_the_file,
        station_walk.METHODS,
        station_walk.CANNOT_SEE,
        lambda inputs, ground: station_walk.build(inputs, ground.spine),
    ),
    _of_stops(FeatureId.UNDERGROUND_PROXIMITY),
    _of_venues(FeatureId.VENUE_CAFE),
    _of_venues(FeatureId.VENUE_CAFE_PER_HOMES),
    _of_venues(FeatureId.VENUE_EVENING),
    _of_venues(FeatureId.VENUE_EVENING_PER_HOMES),
    Measure(
        venue_food_drink.FEATURE,
        venue_food_drink.SOURCE,
        venue_food_drink.is_a_file,
        venue_food_drink.METHODS,
        venue_food_drink.CANNOT_SEE,
        lambda inputs, ground: venue_food_drink.build(inputs, ground.spine),
        in_parts=True,
        waits_on=venue_food_drink.WAITS_ON,
        held_back=venue_food_drink.HELD_BACK,
    ),
    Measure(
        venue_food_drink_per_homes.FEATURE,
        venue_food_drink_per_homes.SOURCE,
        venue_food_drink_per_homes.is_a_file,
        venue_food_drink_per_homes.METHODS,
        venue_food_drink_per_homes.CANNOT_SEE,
        lambda inputs, ground: venue_food_drink_per_homes.build(inputs, ground.spine),
        in_parts=True,
    ),
    _of_venues(FeatureId.VENUE_GYM),
    _of_venues(FeatureId.VENUE_GYM_PER_HOMES),
    Measure(
        water_access.FEATURE,
        water_access.SOURCE,
        water_access.is_the_network,
        water_access.METHODS,
        water_access.CANNOT_SEE,
        lambda inputs, ground: water_access.build(inputs, ground.spine),
    ),
)
# In the order of their ids, which is the order a release lists them in.
MEASURES: tuple[Measure, ...] = tuple(
    sorted(
        (*_EVERY_OTHER, *(_of_brands(feature) for feature in brands_nearby.FEATURES)),
        key=lambda measure: measure.feature.value,
    )
)


def behind() -> dict[str, Behind]:
    """What stands behind each measure of a build, for the check that holds evidence to it."""
    return {
        measure.feature: Behind(
            measure.methods[0].derivation_id,
            measure.source,
            measure.reads,
            measure.in_squares,
            measure.in_parts,
        )
        for measure in MEASURES
    }
