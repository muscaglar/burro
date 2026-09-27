/** @jest-environment node */
import { BAND_ON_A_SCALE, BAND_ONE_WAY } from "@/content/bands";
import { STRIP } from "@/content/search";
import { TOWN } from "@/content/town";
import { recordedAnswer } from "@/lib/api/recorded";
import type { Tag } from "@/lib/api/schema";

import { bandsOf, markOf, type Mark } from "./bands";
import type { Release } from "./release";
import { blankOf, blankSaid, notDrawn, saidOf } from "./said";
import { DRAWN_FROM, PARTS, type Part } from "./vibes";

const meta = recordedAnswer("get_meta", "meta").body.data;
const { areas } = recordedAnswer("list_areas", "areas").body.data;
const pageOf = (slug: string) => recordedAnswer("get_area", `area/${slug}`).body.data;
const tagOf = (part: Part): Tag => {
  const tag = meta.tags.find((one) => one.tag_id === DRAWN_FROM[part]);
  if (tag === undefined) throw new Error("The recorded release does not hold a vibe a town is drawn from.");
  return tag;
};

/** Marks made by hand: the band of each part that is named, and no band for the rest. */
const marksFor = (bands: Partial<Record<Part, number | null>>, spread = 0): Mark[] =>
  PARTS.map((part) => {
    const band = bands[part] ?? null;
    return {
      tag_id: DRAWN_FROM[part],
      band,
      spread_low: band === null ? null : band - spread,
      spread_high: band === null ? null : band + spread,
    };
  });
const saidFor = (marks: readonly Mark[], part: Part, release: Release = meta) => {
  const said = saidOf(marks, release).find((one) => one.part === part);
  if (said === undefined) throw new Error("A part of a town says nothing.");
  return said;
};

describe("what a town says of itself", () => {
  test("test_it_says_its_four_parts_in_one_order_each_by_its_name", () => {
    const said = saidOf(pageOf(areas[0]?.slug ?? "").tags, meta);

    expect(said.map(({ part }) => part)).toEqual(PARTS);
    expect(said.map(({ name }) => name)).toEqual(PARTS.map((part) => TOWN.parts[part]));
  });

  test("test_every_part_of_every_recorded_area_names_its_vibe_as_the_service_does_and_says_its_band", () => {
    for (const { slug } of areas) {
      const { tags } = pageOf(slug);
      for (const part of PARTS) {
        const band = markOf(tags, part)?.band ?? null;
        const { says } = saidFor(tags, part);

        expect([slug, part, says.includes(tagOf(part).label)]).toEqual([slug, part, true]);
        if (band !== null) expect([slug, part, says.includes(String(band))]).toEqual([slug, part, true]);
      }
    }
  });

  test("test_a_band_is_said_in_the_words_every_page_uses_for_it_with_the_ends_the_service_names", () => {
    for (const part of PARTS) {
      const tag = tagOf(part);
      const { says, state } = saidFor(marksFor({ trees: 4, height: 4, lit: 4, roofs: 4 }), part);
      const plain =
        tag.low_end === null || tag.high_end === null ? BAND_ONE_WAY[4] : BAND_ON_A_SCALE[4](tag.low_end, tag.high_end);

      expect(state).toBe("drawn");
      expect(says).toBe(`${tag.label}, ${STRIP.band(4)}, ${plain}`);
    }
  });

  test("test_a_mixed_area_is_said_to_vary_and_says_the_band_its_town_is_drawn_as", () => {
    // The recorded release holds areas that are mixed on a vibe a town is drawn from.
    const mixed = areas.flatMap(({ slug }) =>
      PARTS.flatMap((part) => {
        const mark = markOf(pageOf(slug).tags, part);
        const wide = mark !== undefined && mark.spread_high !== null && mark.spread_low !== null && mark.spread_high - mark.spread_low >= 2;
        return wide ? [{ slug, part, mark }] : [];
      }),
    );

    expect(mixed.length).toBeGreaterThan(0);
    for (const { slug, part, mark } of mixed) {
      const { says, state } = saidFor(pageOf(slug).tags, part);

      expect(state).toBe("drawn");
      expect(says).toBe(
        TOWN.mixed(tagOf(part).label, STRIP.bands(mark.spread_low ?? 0, mark.spread_high ?? 0), STRIP.band(mark.band ?? 0)),
      );
    }
  });

  test("test_no_figure_is_said_that_is_not_a_band", () => {
    const bands = new Set(["1", "2", "3", "4", "5"]);
    for (const { slug } of areas) {
      for (const { says } of saidOf(pageOf(slug).tags, meta)) {
        expect((says.match(/\d+(\.\d+)?/g) ?? []).filter((figure) => !bands.has(figure))).toEqual([]);
      }
    }
  });
});

describe("what a town says of what it leaves blank", () => {
  test.each(PARTS)("test_a_part_the_area_cannot_be_placed_on_says_what_is_left_blank_and_names_the_vibe: %s", (part) => {
    const { says, state } = saidFor(marksFor({ trees: 3, height: 3, lit: 3, roofs: 3, [part]: null }), part);

    expect(state).toBe("blank");
    expect(says).toBe(TOWN.because(TOWN.blank[part], TOWN.notKnown(tagOf(part).label)));
    // It gives no band, the middle least of all.
    expect(/\d/.test(says)).toBe(false);
  });

  test.each(PARTS)("test_a_part_whose_vibe_the_release_does_not_hold_says_so_and_names_no_vibe: %s", (part) => {
    const without = { ...meta, tags: meta.tags.filter((tag) => tag.tag_id !== DRAWN_FROM[part]) };
    // Even were a band sent for it, nothing could be said of it, and nothing is drawn of it.
    const { says, state } = saidFor(marksFor({ trees: 3, height: 3, lit: 3, roofs: 3 }), part, without);

    expect(state).toBe("blank");
    expect(says).toBe(TOWN.because(TOWN.blank[part], TOWN.notHeld));
    expect(says.includes(tagOf(part).label)).toBe(false);
  });

  test("test_a_window_and_a_roof_that_are_known_say_that_they_are_not_drawn_where_no_building_is", () => {
    const marks = marksFor({ trees: 2, lit: 4, roofs: 5 });

    for (const part of ["lit", "roofs"] as const) {
      const { says, state } = saidFor(marks, part);

      expect(state).toBe("unbuilt");
      expect(says).toBe(TOWN.because(TOWN.blankUnbuilt[part], TOWN.unbuilt(tagOf(part).label)));
      // The band is not said, since it is not drawn.
      expect(/\d/.test(says)).toBe(false);
    }
    expect(saidFor(marks, "height").state).toBe("blank");
    expect(saidFor(marks, "trees").state).toBe("drawn");
  });

  test("test_a_window_is_said_to_be_dark_only_where_a_building_is_drawn_to_hold_it", () => {
    // With no building there is no window, dark or lit, and the town does not say there is.
    expect(saidFor(marksFor({ height: 2 }), "lit").says).toBe(TOWN.because(TOWN.blank.lit, TOWN.notKnown(tagOf("lit").label)));
    expect(saidFor(marksFor({ trees: 2 }), "lit").says).toBe(TOWN.because(TOWN.blankUnbuilt.lit, TOWN.notKnown(tagOf("lit").label)));
    expect(TOWN.blank.lit).not.toBe(TOWN.blankUnbuilt.lit);
    expect(blankOf("lit", true)).toBe(TOWN.blank.lit);
    expect(blankOf("trees", false)).toBe(TOWN.blank.trees);
  });

  test("test_what_is_not_drawn_is_listed_in_the_order_of_the_parts_and_nothing_where_all_is_drawn", () => {
    expect(notDrawn(saidOf(marksFor({ trees: 1, height: 1, lit: 1, roofs: 1 }), meta))).toEqual([]);
    expect(notDrawn(saidOf(marksFor({ height: 2, lit: 3 }), meta))).toEqual([TOWN.listed.trees, TOWN.listed.roofs]);
    expect(notDrawn(saidOf(marksFor({ lit: 3 }), meta))).toEqual([TOWN.listed.trees, TOWN.listed.height, TOWN.listed.lit, TOWN.listed.roofs]);
    expect(notDrawn(saidOf([], meta))).toEqual(PARTS.map((part) => TOWN.listed[part]));
  });

  test("test_in_sight_it_says_which_parts_are_blank_and_why_and_nothing_where_the_whole_town_is_drawn", () => {
    expect(blankSaid(saidOf(marksFor({ trees: 1, height: 1, lit: 1, roofs: 1 }), meta))).toBeNull();
    expect(blankSaid(saidOf(marksFor({ height: 2, lit: 3 }), meta))).toBe(
      `${TOWN.leftBlank([TOWN.listed.trees, TOWN.listed.roofs])} ${TOWN.whyBlank.unknown}`,
    );
    // A window and a roof that are known and have no building say that they have none.
    expect(blankSaid(saidOf(marksFor({ trees: 2, lit: 3, roofs: 3 }), meta))).toBe(
      `${TOWN.leftBlank([TOWN.listed.height, TOWN.listed.lit, TOWN.listed.roofs])} ${TOWN.whyBlank.unknown} ${TOWN.whyBlank.unbuilt}`,
    );
    // Where nothing is known of them either, that is all there is to say.
    expect(blankSaid(saidOf(marksFor({ trees: 2 }), meta))).toBe(
      `${TOWN.leftBlank([TOWN.listed.height, TOWN.listed.lit, TOWN.listed.roofs])} ${TOWN.whyBlank.unknown}`,
    );
  });

  test("test_why_a_part_is_not_drawn_is_kept_with_what_it_says", () => {
    const said = saidOf(marksFor({ trees: 2, lit: 3 }), meta);

    expect(said.map(({ part, why }) => [part, why])).toEqual([
      ["trees", null],
      ["height", "unknown"],
      ["lit", "unbuilt"],
      ["roofs", "unknown"],
    ]);
  });

  test("test_the_recorded_areas_that_cannot_be_placed_say_which_part_is_blank", () => {
    const blank = areas.flatMap(({ slug }) => saidOf(pageOf(slug).tags, meta).filter(({ state }) => state === "blank").map((said) => ({ slug, said })));

    expect(blank.length).toBeGreaterThan(3);
    for (const { slug, said } of blank) {
      const built = bandsOf(pageOf(slug).tags).height !== null;
      expect(said.says).toBe(TOWN.because(blankOf(said.part, built), TOWN.notKnown(tagOf(said.part).label)));
    }
  });
});
