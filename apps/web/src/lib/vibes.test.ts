/** @jest-environment node */
import { readFileSync } from "node:fs";
import path from "node:path";

import { BAND_ON_A_SCALE, BAND_ONE_WAY, BAND_VARIES } from "@/content/bands";
import { recordedAnswer } from "@/lib/api/recorded";
import type { AreasData, MetaData } from "@/lib/api/schema";

import { fromTheMiddle, inWords, isRange, plainly, VIBE_BANDS } from "./vibes";

const meta: MetaData = recordedAnswer("get_meta", "meta").body.data;
const areas: AreasData = recordedAnswer("list_areas", "areas").body.data;

const contract = () =>
  readFileSync(path.resolve(__dirname, "../../../../docs/design/contract.md"), "utf8").replace(/[ \t]+/g, " ");

const at = (band: number) => ({ band, spread_low: band, spread_high: band });
const oneWay = { low_end: null, high_end: null };
const scale = { low_end: "Calm", high_end: "Buzzy" };

describe("a band, in words a person would use", () => {
  test("test_a_vibe_that_runs_one_way_is_said_from_least_to_most", () => {
    expect(VIBE_BANDS.map((band) => plainly(oneWay, at(band)))).toEqual([
      "among the least here",
      "on the low side here",
      "around the middle here",
      "on the high side here",
      "among the most here",
    ]);
  });

  test("test_a_scale_is_said_by_the_names_the_api_gives_its_ends", () => {
    expect(VIBE_BANDS.map((band) => plainly(scale, at(band)))).toEqual([
      "at the Calm end",
      "towards Calm",
      "between Calm and Buzzy",
      "towards Buzzy",
      "at the Buzzy end",
    ]);
    // No end is written into the website: every scale of the release is said by its own.
    for (const tag of meta.tags.filter((one) => one.shape === "scale")) {
      expect(plainly(tag, at(5))).toBe(`at the ${tag.high_end} end`);
      expect(plainly(tag, at(1))).toBe(`at the ${tag.low_end} end`);
    }
  });

  test("test_a_mixed_area_is_said_to_vary_and_is_never_put_at_a_point", () => {
    const mixed = { band: 4, spread_low: 3, spread_high: 5 };

    expect(isRange(mixed)).toBe(true);
    expect(plainly(scale, mixed)).toBe(BAND_VARIES);
    expect(plainly(oneWay, mixed)).toBe(BAND_VARIES);
    expect(fromTheMiddle(mixed)).toBe(0);
  });

  test("test_what_is_no_band_is_said_in_no_words", () => {
    for (const band of [0, 6, 2.5, Number.NaN]) expect(plainly(oneWay, at(band))).toBeNull();
  });

  test("test_every_word_is_true_of_the_band_as_the_contract_counts_it", () => {
    // A band is counted by the areas strictly below, in whole areas: band 5 has four in five
    // or more below it, band 4 three in five or more. So "on the high side" is true of band 4
    // whatever is level with it. No word says how many sit above, which a band does not say,
    // and none is the heading of a list of the portrait, which the API fills by a rule of its own.
    expect(contract()).toContain("`band = 1 + min(4, (5 * L) // N)`");
    expect(contract()).toContain("Areas that are level share a band.");
    const band = (below: number, compared: number) => 1 + Math.min(4, Math.floor((5 * below) / compared));
    for (let compared = 1; compared <= 40; compared += 1) {
      for (let below = 0; below < compared; below += 1) {
        const share = below / compared;
        const words = plainly(oneWay, at(band(below, compared)));
        if (words === BAND_ONE_WAY[5]) expect(share).toBeGreaterThanOrEqual(0.8);
        if (words === BAND_ONE_WAY[4]) expect(share).toBeGreaterThanOrEqual(0.6);
        if (words === BAND_ONE_WAY[2]) expect(share).toBeLessThan(0.4);
        if (words === BAND_ONE_WAY[1]) expect(share).toBeLessThan(0.2);
      }
    }
    for (const words of [...Object.values(BAND_ONE_WAY), ...VIBE_BANDS.map((one) => BAND_ON_A_SCALE[one]("a", "b"))]) {
      expect(/above|(more|less) than most|worse|better|best|worst/i.test(words)).toBe(false);
      expect(/\d|%/.test(words)).toBe(false);
    }
  });

  test("test_the_words_go_with_the_band_and_never_take_its_place", () => {
    // Every band the release serves can be said both ways: in words, and as one band of five.
    const marks = areas.bands.flatMap((lens) => {
      const tag = meta.tags.find((one) => one.tag_id === lens.tag_id);
      return tag === undefined ? [] : lens.marks.map((mark) => ({ tag, mark }));
    });
    const placed = marks.flatMap(({ tag, mark }) =>
      mark.band === null || mark.spread_low === null || mark.spread_high === null
        ? []
        : [{ tag, placed: { band: mark.band, spread_low: mark.spread_low, spread_high: mark.spread_high } }],
    );

    expect(placed.length).toBeGreaterThan(200);
    for (const one of placed) {
      expect(plainly(one.tag, one.placed)).not.toBeNull();
      expect(inWords(one.placed)).toMatch(/band \d/);
    }
  });
});
