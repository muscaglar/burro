/** @jest-environment node */
import { recordedAnswer } from "@/lib/api/recorded";

import { bandsOf, markOf, marksOf, NOTHING_KNOWN, type Mark } from "./bands";
import { DRAWN_FROM, PARTS, type Part } from "./vibes";

const meta = recordedAnswer("get_meta", "meta").body.data;
const { areas, bands } = recordedAnswer("list_areas", "areas").body.data;
const pageOf = (slug: string) => recordedAnswer("get_area", `area/${slug}`).body.data;

/** A mark made by hand, of the vibe a part is drawn from. */
const markFor = (part: Part, band: number | null): Mark => ({
  tag_id: DRAWN_FROM[part],
  band,
  spread_low: band,
  spread_high: band,
});

describe("the four bands of an area", () => {
  test("test_each_part_has_the_band_the_service_gave_for_its_vibe_on_the_page_of_the_area", () => {
    for (const { slug } of areas) {
      const { tags } = pageOf(slug);
      const read = bandsOf(tags);

      for (const part of PARTS) {
        const sent = tags.find((tag) => tag.tag_id === DRAWN_FROM[part]);
        expect([slug, part, read[part]]).toEqual([slug, part, sent?.band ?? null]);
      }
    }
  });

  test("test_the_bands_of_every_area_give_the_town_that_the_page_of_the_area_gives", () => {
    // A result is drawn from the bands the service sends with the search page, and the page
    // of an area from its own. Both must draw one town.
    const differing = areas.filter(
      ({ area_id, slug }) => JSON.stringify(bandsOf(marksOf(bands, area_id))) !== JSON.stringify(bandsOf(pageOf(slug).tags)),
    );

    expect(areas.length).toBeGreaterThan(20);
    expect(differing.map(({ slug }) => slug)).toEqual([]);
  });

  test("test_the_strip_of_a_result_may_be_handed_over_as_it_came", () => {
    const [first] = recordedAnswer("rank", "rank-first").body.data.ranked;
    const strip = first?.strip ?? [];

    expect(strip.length).toBeGreaterThan(0);
    for (const part of PARTS) {
      const sent = strip.find((mark) => mark.tag_id === DRAWN_FROM[part]);
      expect([part, bandsOf(strip)[part]]).toEqual([part, sent?.band ?? null]);
    }
  });

  test("test_an_area_that_a_vibe_cannot_place_has_no_band_for_that_part", () => {
    const unplaced = areas.flatMap(({ slug }) =>
      PARTS.filter((part) => markOf(pageOf(slug).tags, part)?.band === null).map((part) => ({ slug, part })),
    );

    // The recorded release holds such areas, so this is no test of nothing.
    expect(unplaced.length).toBeGreaterThan(3);
    for (const { slug, part } of unplaced) expect([slug, part, bandsOf(pageOf(slug).tags)[part]]).toEqual([slug, part, null]);
  });

  test("test_a_vibe_the_service_said_nothing_of_has_no_band", () => {
    expect(bandsOf([])).toEqual(NOTHING_KNOWN);
    expect(bandsOf([markFor("trees", 4)])).toEqual({ ...NOTHING_KNOWN, trees: 4 });
    expect(marksOf(bands, "an area the release does not hold")).toEqual([]);
  });

  test.each([0, 6, -1, 2.5, Number.NaN, Number.POSITIVE_INFINITY])(
    "test_a_band_that_is_none_of_the_five_is_not_known_and_is_never_rounded_to_one: %d",
    (band) => {
      expect(bandsOf(PARTS.map((part) => markFor(part, band)))).toEqual(NOTHING_KNOWN);
    },
  );

  test("test_nothing_but_the_four_vibes_is_read", () => {
    const four = PARTS.map((part) => DRAWN_FROM[part]);
    const others = meta.tags.filter((tag) => !four.some((id) => id === tag.tag_id));
    const { tags } = pageOf(areas[0]?.slug ?? "");
    const moved = tags.map((tag) => (others.some((other) => other.tag_id === tag.tag_id) ? { ...tag, band: 1 + ((tag.band ?? 0) % 5) } : tag));

    expect(others.length).toBeGreaterThan(5);
    expect(moved).not.toEqual(tags);
    expect(bandsOf(moved)).toEqual(bandsOf(tags));
  });
});
