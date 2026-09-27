/** @jest-environment node */
/**
 * What the town at the head of each area of a comparison is drawn from. No vibe, no
 * measure and no place is named here: each is read from what the service recorded.
 */

import { crimeVibes } from "@/content/crime";
import { recordedAnswer } from "@/lib/api/recorded";
import type { CompareData, MetaData } from "@/lib/api/schema";
import { marksOf } from "@/lib/town/bands";
import { vibesOf } from "@/lib/town/release";
import { townOf } from "@/lib/town/town";

import { ROUGH, sayingSo } from "../../../test/support/rough";
import { marksFor, marksOfTheChosen, releaseOf } from "./towns";

const meta: MetaData = recordedAnswer("get_meta", "meta").body.data;
const { areas, bands } = recordedAnswer("list_areas", "areas").body.data;
const compared: CompareData = recordedAnswer("compare", "compare-three").body.data;

/** The release as a comparison is handed it: its vibes, and which of them hold recorded crime. */
const handed = (release: MetaData) => releaseOf(release.tags, crimeVibes(release));

/**
 * A release in which the first vibe a town is drawn from holds recorded crime: the first
 * measure of its recipe is made a measure of crime, as a release may be built.
 */
function withCrimeInATown(): MetaData {
  const [first] = vibesOf(meta);
  const measure = first?.tag?.terms[0]?.feature_id;
  if (measure === undefined) throw new Error("the recorded release holds no vibe a town is drawn from");
  return {
    ...meta,
    features: meta.features.map((one) => (one.feature_id === measure ? { ...one, dimension: "crime" } : one)),
  };
}

describe("what a town of a comparison is drawn from", () => {
  test("test_a_town_drawn_from_what_a_comparison_is_handed_is_the_town_drawn_from_the_whole_release", () => {
    // A comparison is handed the vibes and the measures of crime their recipes hold, and
    // not every measure of the release. A town must come out the same either way.
    for (const release of [meta, withCrimeInATown()]) {
      for (const area of areas) {
        const marks = marksOf(bands, area.area_id);
        const whole = townOf(marks, release);
        const fromHanded = townOf(marks, handed(release));

        expect([area.area_id, fromHanded.said]).toEqual([area.area_id, whole.said]);
        expect([area.area_id, fromHanded.pieces]).toEqual([area.area_id, whole.pieces]);
      }
    }
  });

  test("test_no_town_of_a_comparison_is_handed_what_a_rough_guide_says_of_itself", () => {
    // The founder: "remove the concept of rough guide, we don't want to pass this on to a
    // user". No town says that a vibe is one, whatever it is handed. What the service says
    // of a rough guide is handed to no town of a comparison all the same, so that the
    // browser holds nothing of it that a town could say.
    const holdsWhatIsTold = (held: unknown) => [ROUGH.label, ROUGH.why].map((words) => JSON.stringify(held).includes(words));
    // A release in which the first vibe a town is drawn from is one the service calls a rough
    // guide, and says why: in the words a service gave such a vibe until it stopped.
    const [first] = vibesOf(meta);
    const tagId = first?.tag?.tag_id;
    if (tagId === undefined) throw new Error("the recorded release holds no vibe a town is drawn from");
    const release: MetaData = sayingSo(meta, [tagId]);

    expect(release.rough_guides).toContainEqual({ ...ROUGH, tag_id: tagId });
    expect(vibesOf(release).map(({ tag }) => tag?.sureness)).toContain("rough_guide");
    expect(holdsWhatIsTold(release)).toEqual([true, true]);
    // What a comparison is handed of that release holds neither its label nor why.
    expect(Object.keys(handed(release)).sort()).toEqual(["features", "tags"]);
    expect(holdsWhatIsTold(handed(release))).toEqual([false, false]);
    for (const area of areas) {
      const marks = marksOf(bands, area.area_id);
      const [ofTheComparison, ofTheWhole] = [townOf(marks, handed(release)), townOf(marks, release)];
      expect([area.area_id, holdsWhatIsTold(ofTheComparison), holdsWhatIsTold(ofTheWhole)]).toEqual([
        area.area_id,
        [false, false],
        [false, false],
      ]);
    }
  });

  test("test_a_vibe_whose_recipe_holds_recorded_crime_is_drawn_in_no_town_of_a_comparison", () => {
    const release = withCrimeInATown();
    const [first] = vibesOf(release);

    expect(crimeVibes(release).map((vibe) => vibe.tag.tag_id)).toContain(first?.tag?.tag_id);
    for (const area of areas) {
      const town = townOf(marksOf(bands, area.area_id), handed(release));
      const part = town.said.find((one) => one.part === first?.part);
      expect([area.area_id, part?.state, part?.why]).toEqual([area.area_id, "blank", "crime"]);
    }
    // In the release as it was recorded that vibe is drawn, so the test tells the two apart.
    const drawn = areas.filter((area) => {
      const town = townOf(marksOf(bands, area.area_id), handed(meta));
      return town.said.find((one) => one.part === first?.part)?.state === "drawn";
    });
    expect(drawn.length).toBeGreaterThan(10);
  });

  test("test_the_page_hands_over_the_areas_of_the_comparison_and_no_other", () => {
    const chosen = areas.slice(2, 5);

    const marks = marksOfTheChosen(bands, chosen);

    expect(Object.keys(marks)).toEqual(chosen.map((area) => area.area_id));
    for (const area of chosen) expect(marks[area.area_id]).toEqual(marksOf(bands, area.area_id));
    // A release may hold a thousand areas: what is handed over does not grow with it.
    expect(JSON.stringify(marks).length).toBeLessThan(JSON.stringify(bands).length / 4);
    expect(marksOfTheChosen(bands, [])).toEqual({});
  });

  test("test_before_the_comparison_is_answered_a_town_is_drawn_from_what_the_page_was_built_with", () => {
    const [area] = compared.areas;
    const built = marksOfTheChosen(bands, compared.areas);

    expect(marksFor(area?.area_id ?? "", built, undefined)).toEqual(built[area?.area_id ?? ""]);
    // An area the page was handed nothing of has no mark, and its town is left blank.
    expect(marksFor("an-area-that-was-not-handed-over", built, undefined)).toEqual([]);
  });

  test("test_once_the_comparison_is_answered_a_town_follows_what_the_table_under_it_says", () => {
    const [area] = compared.areas;
    const areaId = area?.area_id ?? "";
    const built = marksOfTheChosen(bands, compared.areas);
    // The release moved on between the page and the answer: every band the page was built with is another.
    const stale = Object.fromEntries(
      Object.entries(built).map(([id, marks]) => [
        id,
        marks.map((mark) => {
          const band = mark.band === null ? null : (mark.band % 5) + 1;
          return { ...mark, band, spread_low: band, spread_high: band };
        }),
      ]),
    );

    const drawnFrom = marksFor(areaId, stale, compared.character);

    for (const row of compared.character) {
      const said = row.marks.find((mark) => mark.area_id === areaId);
      const mark = drawnFrom.find((one) => one.tag_id === row.tag_id);
      expect([row.tag_id, mark?.band]).toEqual([row.tag_id, said?.band]);
    }
    // No vibe is given twice.
    expect(new Set(drawnFrom.map((mark) => mark.tag_id)).size).toBe(drawnFrom.length);
  });

  test("test_a_vibe_the_comparison_says_nothing_of_is_drawn_as_the_page_was_built", () => {
    const [area] = compared.areas;
    const areaId = area?.area_id ?? "";
    const built = marksOfTheChosen(bands, compared.areas);
    const [left, ...rest] = compared.character;

    const drawnFrom = marksFor(areaId, built, rest);

    expect(drawnFrom.find((mark) => mark.tag_id === left?.tag_id)).toEqual(
      built[areaId]?.find((mark) => mark.tag_id === left?.tag_id),
    );
    expect(drawnFrom).toHaveLength(built[areaId]?.length ?? 0);
  });
});
