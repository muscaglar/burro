/** @jest-environment node */
/**
 * What the town of an area in the bar is drawn from. No vibe, no measure and no place is
 * named here: each is read from what the service recorded.
 */

import { recordedAnswer } from "@/lib/api/recorded";
import type { MetaData } from "@/lib/api/schema";
import { marksOf } from "@/lib/town/bands";
import { vibesOf } from "@/lib/town/release";
import { townOf } from "@/lib/town/town";
import { PARTS } from "@/lib/town/vibes";

import { ROUGH, sayingSo } from "../../../test/support/rough";
import { marksIn, ofATown, type Handed } from "./town";

const meta: MetaData = recordedAnswer("get_meta", "meta").body.data;
const { areas, bands } = recordedAnswer("list_areas", "areas").body.data;

/** A release in which the first vibe a town is drawn from holds recorded crime. */
function withCrimeInATown(): MetaData {
  const [first] = vibesOf(meta);
  const measure = first?.tag?.terms[0]?.feature_id;
  if (measure === undefined) throw new Error("the recorded release holds no vibe a town is drawn from");
  return {
    ...meta,
    features: meta.features.map((one) => (one.feature_id === measure ? { ...one, dimension: "crime" } : one)),
  };
}

/**
 * A release in which the first vibe a town is drawn from is one the service calls a rough
 * guide, and says why: in the words a service gave such a vibe until it stopped, which are
 * said nowhere else in a release.
 */
function withARoughGuideInATown(): MetaData {
  const [first] = vibesOf(meta);
  const tagId = first?.tag?.tag_id;
  if (tagId === undefined) throw new Error("the recorded release holds no vibe a town is drawn from");
  return sayingSo(meta, [tagId]);
}

/** Whether what a town is handed holds the label of a rough guide, and whether it holds why it is one. */
const holdsWhatIsTold = (handed: unknown) => [ROUGH.label, ROUGH.why].map((words) => JSON.stringify(handed).includes(words));

describe("what the bar is handed of a release", () => {
  test("test_a_town_drawn_from_what_the_bar_is_handed_is_the_town_drawn_from_the_whole_release", () => {
    for (const release of [meta, withCrimeInATown(), withARoughGuideInATown()]) {
      for (const area of areas) {
        const marks = marksOf(bands, area.area_id);
        const whole = townOf(marks, release);
        const handed = townOf(marks, ofATown(release));

        expect([area.area_id, handed.said]).toEqual([area.area_id, whole.said]);
        expect([area.area_id, handed.pieces]).toEqual([area.area_id, whole.pieces]);
      }
    }
  });

  test("test_it_holds_nothing_a_rough_guide_says_of_itself_so_that_no_town_of_the_bar_says_it", () => {
    // The founder: "remove the concept of rough guide, we don't want to pass this on to a
    // user". No town says that a vibe is one, whatever it is handed. What the service says
    // of a rough guide is handed to no town of the bar all the same, so that the browser
    // holds nothing of it that a town could say.
    const release = withARoughGuideInATown();
    const handed = ofATown(release);

    // The release says of a vibe a town is drawn from that it is one, and says why.
    expect(vibesOf(release).map(({ tag }) => tag?.sureness)).toContain("rough_guide");
    expect(holdsWhatIsTold(release)).toEqual([true, true]);
    // What the bar is handed of that release holds neither its label nor why.
    expect(Object.keys(handed).sort()).toEqual(["features", "tags"]);
    expect(holdsWhatIsTold(handed)).toEqual([false, false]);
    for (const area of areas) {
      const marks = marksOf(bands, area.area_id);
      const [ofTheBar, ofTheWhole] = [townOf(marks, handed), townOf(marks, release)];
      expect([area.area_id, holdsWhatIsTold(ofTheBar), holdsWhatIsTold(ofTheWhole)]).toEqual([
        area.area_id,
        [false, false],
        [false, false],
      ]);
    }
  });

  test("test_it_holds_the_vibes_a_town_is_drawn_from_and_no_other_so_that_a_page_hands_the_browser_little", () => {
    const handed = ofATown(meta);

    expect(handed.tags.length).toBeLessThanOrEqual(PARTS.length);
    expect(handed.tags.length).toBeGreaterThan(0);
    expect(handed.tags.length).toBeLessThan(meta.tags.length);
    // Of the measures of a release it holds those of recorded crime in those recipes, and the recorded release has none.
    expect(handed.features).toEqual([]);
    expect(ofATown(withCrimeInATown()).features.map((one) => one.dimension)).toEqual(["crime"]);
    expect(JSON.stringify(handed).length).toBeLessThan(JSON.stringify({ tags: meta.tags, features: meta.features }).length / 10);
  });

  test("test_handed_twice_it_is_what_it_was_handed_once", () => {
    expect(ofATown(ofATown(meta))).toEqual(ofATown(meta));
  });
});

describe("where an area of the bar sits, of all that was handed over", () => {
  const release = ofATown(meta);
  const [one, two, three] = areas;
  const own = marksOf(bands, one?.area_id ?? "").slice(0, 2);

  test("test_what_was_handed_of_the_area_itself_comes_first", () => {
    const handed: Handed = { release, bands, marks: { [one?.area_id ?? ""]: own } };

    expect(marksIn(handed, one?.area_id ?? "")).toBe(own);
  });

  test("test_an_area_nothing_was_handed_of_is_read_from_where_every_area_sits", () => {
    const handed: Handed = { release, bands, marks: { [one?.area_id ?? ""]: own } };

    expect(marksIn(handed, two?.area_id ?? "")).toEqual(marksOf(bands, two?.area_id ?? ""));
  });

  test("test_an_area_that_nothing_is_known_of_has_no_town_and_is_never_drawn_as_a_town_left_blank", () => {
    // A town left blank says that its parts are not known of the area. Of an area the bar
    // was handed nothing of that would be untrue: nothing is drawn, and nothing is said.
    expect(marksIn({ release, marks: { [one?.area_id ?? ""]: own } }, three?.area_id ?? "")).toBeNull();
    expect(marksIn({ release, bands, marks: {} }, "an-area-that-is-in-no-release")).toBeNull();
    expect(marksIn(null, one?.area_id ?? "")).toBeNull();
  });
});
