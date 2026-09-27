/** @jest-environment node */
/**
 * What the town of a result is drawn from. No vibe, no measure and no place is named here:
 * each is read from what the service recorded.
 */

import { readdirSync } from "node:fs";

import { readRecorded, recordedAnswer, recordedFolder } from "@/lib/api/recorded";
import type { RankData, RankedArea } from "@/lib/api/schema";
import { bandsOf, marksOf } from "@/lib/town/bands";
import { PARTS } from "@/lib/town/vibes";

import { marksOn } from "./town";

const { areas, bands } = recordedAnswer("list_areas", "areas").body.data;
const pageOf = (slug: string) => recordedAnswer("get_area", `area/${slug}`).body.data;
const first = recordedAnswer("rank", "rank-first").body.data;

/** Every ranking that was recorded of the release the bands were recorded of. */
function everyRanking(): RankData[] {
  return readdirSync(recordedFolder())
    .filter((file) => /^rank-.*\.json$/.test(file))
    .map((file) => readRecorded(file.slice(0, -".json".length)).body as { data?: Partial<RankData> })
    .flatMap(({ data }) => (Array.isArray(data?.ranked) ? [data as RankData] : []));
}

/** How many parts of a town have a band. */
const known = (area: RankedArea, held: typeof bands) =>
  PARTS.filter((part) => bandsOf(marksOn(area, held))[part] !== null).length;

describe("what the town of a result is drawn from", () => {
  test("test_with_nothing_more_in_hand_it_is_the_strip_of_the_result_as_the_service_sent_it", () => {
    for (const area of first.ranked) {
      expect(marksOn(area, [])).toEqual(area.strip);
      expect(marksOn(area)).toEqual(area.strip);
    }
  });

  test("test_no_strip_that_was_recorded_holds_all_four_so_a_town_drawn_from_a_strip_alone_has_a_blank_part", () => {
    // The strip holds what was asked for and two more at the most. It is why the page hands
    // down where every area sits: drawn from its strip alone, no town would be whole.
    const rankings = everyRanking();
    const results = rankings.flatMap((ranking) => ranking.ranked);

    expect(rankings.length).toBeGreaterThan(20);
    expect(results.length).toBeGreaterThan(400);
    expect(Math.max(...results.map((area) => known(area, [])))).toBeLessThan(PARTS.length);
  });

  test("test_handed_where_every_area_sits_it_holds_the_four_bands_the_page_of_the_area_holds", () => {
    expect(first.ranked.length).toBeGreaterThanOrEqual(10);
    for (const area of first.ranked) {
      const slug = areas.find((one) => one.area_id === area.area_id)?.slug ?? "";

      expect([slug, bandsOf(marksOn(area, bands))]).toEqual([slug, bandsOf(pageOf(slug).tags)]);
    }
  });

  test("test_what_the_strip_says_of_a_vibe_is_what_the_town_is_drawn_from_so_that_the_two_never_differ_on_one_result", () => {
    const [area] = first.ranked;
    if (area === undefined) throw new Error("the recording ranks nothing");
    const [mark] = area.strip;
    if (mark === undefined) throw new Error("the first result has no strip");
    // The page was built on a release in which the area sat elsewhere on that vibe.
    const other = mark.band === 5 ? 1 : mark.band + 1;
    const before = bands.map((one) =>
      one.tag_id !== mark.tag_id
        ? one
        : {
            ...one,
            marks: one.marks.map((held) =>
              held.area_id === area.area_id ? { ...held, band: other, spread_low: other, spread_high: other } : held,
            ),
          },
    );
    const found = marksOn(area, before).filter((one) => one.tag_id === mark.tag_id);

    // The vibe is there once, as the strip gives it.
    expect(found).toEqual([mark]);
    expect(marksOf(before, area.area_id).find((one) => one.tag_id === mark.tag_id)?.band).toBe(other);
  });

  test("test_nothing_of_another_area_is_read", () => {
    const [area, next] = first.ranked;
    if (area === undefined || next === undefined) throw new Error("the recording ranks fewer than two");
    const others = bands.map((one) => ({ ...one, marks: one.marks.filter((held) => held.area_id !== area.area_id) }));

    // With every other area in hand and not its own, a town has its strip and no more.
    expect(marksOn(area, others)).toEqual(area.strip);
  });

  test("test_it_is_handed_the_area_and_its_strip_and_neither_its_rank_nor_its_fit", () => {
    const [area] = first.ranked;
    if (area === undefined) throw new Error("the recording ranks nothing");
    const bare = { area_id: area.area_id, strip: area.strip };

    expect(marksOn(bare, bands)).toEqual(marksOn(area, bands));
    // Ranked last with no fit at all, it is drawn from the same.
    const last: RankedArea = { ...area, rank: 99, score: 0 };
    expect(marksOn(last, bands)).toEqual(marksOn(area, bands));
  });
});
