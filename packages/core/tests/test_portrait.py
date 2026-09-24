"""The portrait of an area: where it sits on every vibe, and what cannot be placed."""

import dataclasses
from collections.abc import Mapping

from burro_core.catalogue import TAGS, band_of, percentile_of
from burro_core.facts import facts_for
from burro_core.ids import FactKind, FeatureId, GrittyVariant, TagId, TagShape
from burro_core.portrait import SCALES, Portrait, PortraitMark, portrait
from burro_core.release import InMemoryRelease

from .support import area_id, small_release, with_figures

RISING = (0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 3.0)
FALLING = (*reversed(RISING[:7]), 3.0)


def ids(marks: tuple[PortraitMark, ...]) -> list[str]:
    return [mark.tag_id.value for mark in marks]


def drawn(release: InMemoryRelease, number: int) -> Portrait:
    found = portrait(release, area_id(number))
    assert found is not None
    return found


def every_mark(found: Portrait) -> list[PortraitMark]:
    return [*found.scales, *found.more, *found.less, *found.others, *found.unplaced]


Figures = tuple[float | None, ...]


def parts_of(tag_id: TagId, figures: Figures) -> dict[FeatureId, Figures]:
    """The same figures for every part of a vibe that is read high, and none read low."""
    return {term.feature_id: figures for term in TAGS[tag_id].terms}


def test_every_vibe_of_the_release_is_on_the_portrait_once():
    for variant in GrittyVariant:
        release = small_release(variant)
        for area in release.neighbourhoods:
            found = portrait(release, area.area_id)
            assert found is not None
            assert sorted(ids(tuple(every_mark(found)))) == sorted(
                vibe.tag_id.value for vibe in release.vibes
            )


def test_an_area_the_release_lacks_has_no_portrait():
    assert portrait(small_release(), "syn-n0099") is None


def test_the_scales_come_first_in_a_fixed_order_that_starts_with_homes():
    release = small_release(GrittyVariant.B)
    for area in release.neighbourhoods:
        scales = ids(drawn(release, int(area.area_id[-1])).scales)
        assert scales == [s.value for s in SCALES if s.value in scales]
    assert SCALES[0] is TagId.HOMES and SCALES[-1] is TagId.STREET_CHARACTER
    assert set(SCALES) == {t for t, tag in TAGS.items() if tag.shape is TagShape.SCALE}
    # The release that carries gritty as land use alone has three scales.
    assert ids(drawn(small_release(GrittyVariant.A), 1).scales) == ["homes", "pace", "built_age"]


def test_a_scale_is_never_in_the_list_of_more_or_of_less():
    release = small_release()
    for number in range(1, 9):
        found = drawn(release, number)
        listed = [*found.more, *found.less, *found.others]
        assert not [m for m in listed if TAGS[m.tag_id].shape is TagShape.SCALE]


def test_more_than_most_is_six_areas_in_ten_strictly_below_and_less_is_as_many_above():
    # Leafy rises with the area, so area 7 has six of seven below it and area 1 six above.
    release = with_figures(small_release(), parts_of(TagId.LEAFY, RISING))
    assert "leafy" in ids(drawn(release, 7).more)
    assert "leafy" in ids(drawn(release, 1).less)
    # Four of seven below is 57%, which is not six in ten. Five of seven is.
    assert "leafy" in ids(drawn(release, 5).others)
    assert "leafy" in ids(drawn(release, 6).more)
    assert "leafy" in ids(drawn(release, 3).others)
    assert "leafy" in ids(drawn(release, 2).less)


def with_raws(release: InMemoryRelease, raws: Mapping[TagId, Figures]) -> InMemoryRelease:
    """A release with the raw value of some vibes given by hand, area by area."""
    rankable = [area.rankable for area in release.neighbourhoods]
    rows = {(row.area_id, row.tag_id): row for row in release.tags}
    carried = {vibe.tag_id for vibe in release.vibes}
    for tag_id, given in raws.items():
        if tag_id not in carried:
            continue
        scores = percentile_of(given, rankable)
        bands = band_of(given, rankable)
        for area, raw, score, band in zip(
            release.neighbourhoods, given, scores, bands, strict=True
        ):
            rows[area.area_id, tag_id] = rows[area.area_id, tag_id].replace(
                raw=raw, score=score, band=band, spread_low=band, spread_high=band
            )
    return dataclasses.replace(release, tags=tuple(rows.values()))


ONE_WAY = tuple(t for t, tag in TAGS.items() if tag.shape is TagShape.ONE_WAY)
LEVEL = (0.5,) * 8


def test_a_list_holds_three_at_most_furthest_first_and_the_rest_are_shown_lower():
    # Area 7 is above every other area on four vibes, and level with them on the rest.
    top = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.9, 0.5)
    # On Leafy one other area is level with it, so it is less far ahead there.
    shared = (0.1, 0.2, 0.3, 0.4, 0.5, 0.9, 0.9, 0.5)
    raws = dict.fromkeys(ONE_WAY, LEVEL) | {
        TagId.LEAFY: shared,
        TagId.PARKS_CLOSE_BY: top,
        TagId.FOODIE: top,
        TagId.FAMILY_AMENITIES: top,
    }
    found = drawn(with_raws(small_release(), raws), 7)
    # Six of seven below on three of them, five of seven on Leafy. Ties go by id.
    assert ids(found.more) == ["family_amenities", "foodie", "parks_close_by"]
    assert "leafy" in ids(found.others)
    assert found.less == ()
    low = drawn(with_raws(small_release(), raws), 1)
    assert ids(low.less) == ["family_amenities", "foodie", "leafy"]
    assert "parks_close_by" in ids(low.others)
    # What is in neither list is shown lower, in the order of the shelf.
    assert ids(low.others) == [
        v.tag_id.value for v in small_release().vibes if v.tag_id.value in ids(low.others)
    ]


def test_a_vibe_the_area_cannot_be_placed_on_is_listed_as_that_and_never_in_the_middle():
    gap = (None, *RISING[1:])
    release = with_figures(small_release(), parts_of(TagId.LEAFY, gap))
    found = drawn(release, 1)
    assert "leafy" in ids(found.unplaced)
    (mark,) = [m for m in found.unplaced if m.tag_id is TagId.LEAFY]
    # No part has a figure, so none is named, and nothing is filled in.
    assert mark.figure_fact_id is None
    assert [part.fact_id for part in mark.parts] == [None, None, None]
    assert [part.hundredths for part in mark.parts] == [40, 30, 30]


def test_a_mark_names_the_facts_that_hold_its_sentence_and_its_figures():
    release = small_release()
    for number in range(1, 9):
        known = {fact.fact_id: fact for fact in facts_for(release, area_id(number), None)}
        for mark in every_mark(drawn(release, number)):
            assert known[mark.fact_id].kind is FactKind.TAG
            assert known[mark.fact_id].key == mark.tag_id
            terms = TAGS[mark.tag_id].terms
            assert [(p.feature_id, p.hundredths, p.reading) for p in mark.parts] == [
                (t.feature_id, t.hundredths, t.reading) for t in terms
            ]
            for part in mark.parts:
                row = release.feature(area_id(number), part.feature_id)
                has = row is not None and row.value is not None
                assert (part.fact_id is not None) == has
                if part.fact_id is not None:
                    assert known[part.fact_id].key == part.feature_id


def test_the_plain_figure_is_of_the_heaviest_part_that_has_one():
    release = small_release()
    # Parks close by: the walk to a park is the heaviest part, at 40.
    (mark,) = [m for m in every_mark(drawn(release, 2)) if m.tag_id is TagId.PARKS_CLOSE_BY]
    assert mark.figure_fact_id == f"{area_id(2)}/feature/park_proximity"
    without = with_figures(release, {FeatureId.PARK_PROXIMITY: (3.0, None, 3.0)})
    (mark,) = [m for m in every_mark(drawn(without, 2)) if m.tag_id is TagId.PARKS_CLOSE_BY]
    # Of two as heavy, the first in the recipe.
    assert mark.figure_fact_id == f"{area_id(2)}/feature/park_large_proximity"
    # A part no release carries has no figure, and is still listed.
    (food,) = [m for m in every_mark(drawn(release, 2)) if m.tag_id is TagId.FOODIE]
    assert [p.fact_id for p in food.parts if p.feature_id is FeatureId.CUISINE_VARIETY] == [None]


def test_the_way_gritty_was_built_is_never_the_first_thing_said_of_an_area():
    rising = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.9, 0.5)
    level = dict.fromkeys(ONE_WAY, LEVEL)
    alone = with_raws(small_release(GrittyVariant.A), level | {TagId.WORKS_WAREHOUSES: rising})
    # Where it would stand alone in a list it is shown lower, with its parts.
    assert drawn(alone, 7).more == ()
    assert "works_warehouses" in ids(drawn(alone, 7).others)
    assert drawn(alone, 1).less == ()
    # Where it would stand first of several, it stands second.
    furthest = (0.1, 0.2, 0.3, 0.4, 0.5, 0.9, 0.9, 0.5)
    several = with_raws(
        small_release(GrittyVariant.A),
        level | {TagId.WORKS_WAREHOUSES: rising, TagId.LEAFY: furthest, TagId.FOODIE: furthest},
    )
    assert ids(drawn(several, 7).more) == ["foodie", "works_warehouses", "leafy"]
    for release in (alone, several):
        for number in range(1, 9):
            found = drawn(release, number)
            for listed in (found.more, found.less):
                assert ids(listed)[:1] != ["works_warehouses"]


def test_a_portrait_holds_ids_and_no_sentence_and_is_the_same_for_everyone():
    release = small_release()
    found = drawn(release, 1)
    assert found == drawn(release, 1)
    again = dataclasses.replace(release, tags=tuple(reversed(release.tags)))
    assert drawn(again, 1) == found
    for mark in every_mark(found):
        assert set(mark.model_dump()) == {"tag_id", "fact_id", "figure_fact_id", "parts"}
