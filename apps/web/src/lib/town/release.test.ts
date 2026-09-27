/** @jest-environment node */
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { crimeParts } from "@/content/crime";
import { TOWN } from "@/content/town";
import { recordedAnswer, recordedFolder } from "@/lib/api/recorded";
import type { MetaData, Tag } from "@/lib/api/schema";

import { ROUGH, sayingSo } from "../../../test/support/rough";
import { bandsOf, type Mark } from "./bands";
import { heldBy, mayBeDrawn, vibesOf, type Release } from "./release";
import { blankSaid, saidOf } from "./said";
import { townOf } from "./town";
import { DRAWN_FROM, PARTS, type Part } from "./vibes";

const meta = recordedAnswer("get_meta", "meta").body.data;

/** Every recorded answer of the route that says what a release holds. */
function releases(folder = recordedFolder()): MetaData[] {
  return readdirSync(folder, { withFileTypes: true }).flatMap((entry) => {
    const file = path.join(folder, entry.name);
    if (entry.isDirectory()) return releases(file);
    if (!/^meta(-[a-z-]+)?\.json$/.test(entry.name)) return [];
    const recorded = JSON.parse(readFileSync(file, "utf8")) as { body: { data?: MetaData } };
    return recorded.body.data === undefined ? [] : [recorded.body.data];
  });
}

const marksFor = (known: Partial<Record<Part, number>>): Mark[] =>
  PARTS.map((part) => {
    const band = known[part] ?? null;
    return { tag_id: DRAWN_FROM[part], band, spread_low: band, spread_high: band };
  });
const WHOLE = marksFor({ trees: 3, height: 3, lit: 3, roofs: 3 });

/** The release, with one vibe of it changed. */
const withTag = (part: Part, change: (tag: Tag) => Tag): Release => ({
  ...meta,
  tags: meta.tags.map((tag) => (tag.tag_id === DRAWN_FROM[part] ? change(tag) : tag)),
});
/** A measure of the release that is of recorded crime, as a part of a recipe. */
const ofCrime = () => {
  const measure = meta.features.find((one) => one.dimension === "crime");
  if (measure === undefined) throw new Error("The recorded release holds no measure of recorded crime.");
  return { feature_id: measure.feature_id, hundredths: 10, reading: "high" as const };
};

describe("what a release lets a town be drawn from", () => {
  test("test_every_recorded_release_names_the_four_vibes_and_none_of_them_counts_crime_or_who_lives_there", () => {
    // A town is drawn for every area, unasked. So it is drawn from what is built and what
    // grows, and from nothing that counts people or what was done to them.
    const found = releases();

    expect(found.length).toBeGreaterThan(5);
    for (const release of found) {
      for (const { part, tag, crime } of vibesOf(release)) {
        const counted = (tag?.terms ?? []).map((term) => release.features.find((one) => one.feature_id === term.feature_id)?.dimension);

        expect([part, tag === undefined, crime]).toEqual([part, false, false]);
        expect([part, counted.filter((dimension) => dimension === "crime" || dimension === "residents")]).toEqual([part, []]);
      }
    }
  });

  test.each(PARTS)("test_a_vibe_whose_recipe_holds_recorded_crime_is_not_drawn_whatever_band_the_area_has: %s", (part) => {
    const release = withTag(part, (tag) => ({ ...tag, terms: [...tag.terms, ofCrime()] }));
    const vibe = vibesOf(release).find((one) => one.part === part);
    const label = vibe?.tag?.label ?? "";

    expect(crimeParts(vibe?.tag ?? { terms: [] }, release.features)).toHaveLength(1);
    expect(vibe?.crime).toBe(true);
    expect(vibe === undefined ? true : mayBeDrawn(vibe)).toBe(false);
    expect(heldBy(WHOLE, release).map((mark) => mark.tag_id)).toEqual(
      PARTS.filter((other) => other !== part).map((other) => DRAWN_FROM[other]),
    );
    expect(bandsOf(heldBy(WHOLE, release))[part]).toBeNull();
    expect(townOf(WHOLE, release).bands[part]).toBeNull();
    // It says that it is blank, and why, and gives no band.
    const said = saidOf(WHOLE, release).find((one) => one.part === part);
    expect(said?.state).toBe("blank");
    expect(said?.why).toBe("crime");
    expect(said?.says).toContain(TOWN.countsCrime(label));
    expect(/\d/.test(said?.says ?? "")).toBe(false);
    // In sight it is not said to be unknown, which it is not.
    expect(blankSaid(saidOf(WHOLE, release))).toContain(TOWN.whyBlank.crime);
    expect(blankSaid(saidOf(WHOLE, release))).not.toContain(TOWN.whyBlank.unknown);
  });

  test("test_a_vibe_the_release_does_not_name_is_not_drawn_though_a_band_is_sent_for_it", () => {
    const release: Release = { ...meta, tags: meta.tags.filter((tag) => tag.tag_id !== DRAWN_FROM.height) };

    expect(townOf(WHOLE, release).bands).toEqual({ trees: 3, height: null, lit: 3, roofs: 3 });
    expect(townOf(WHOLE, release).plan.buildings).toBeNull();
  });

  test("test_a_vibe_the_release_says_is_less_sure_is_drawn_as_every_vibe_is_and_nothing_is_said_of_it", () => {
    // The founder: "remove the concept of rough guide, we don't want to pass this on to a user".
    // The whole of what a service says, though a town is handed the vibes and the measures
    // alone: of a vibe a town is drawn from, that it is less sure, in the words a service gave
    // such a vibe until it stopped.
    const release = sayingSo(meta, [DRAWN_FROM.trees]);
    const [plain, lessSure] = [townOf(WHOLE, meta), townOf(WHOLE, release)];

    expect(release.tags.find((tag) => tag.tag_id === DRAWN_FROM.trees)?.sureness).toBe("rough_guide");
    expect(release.rough_guides).toContainEqual({ ...ROUGH, tag_id: DRAWN_FROM.trees });
    // The town is the town of a release that says nothing of how sure the vibe is.
    expect([lessSure.bands, lessSure.plan, lessSure.pieces, lessSure.said]).toEqual([plain.bands, plain.plan, plain.pieces, plain.said]);
    expect([JSON.stringify(lessSure).includes(ROUGH.label), JSON.stringify(lessSure).includes(ROUGH.why)]).toEqual([false, false]);
    // A town holds what is drawn of it and what it says of itself, and nothing of how sure a vibe is.
    expect(Object.keys(lessSure).sort()).toEqual(["bands", "pieces", "plan", "said"]);
    for (const vibe of vibesOf(release)) expect(Object.keys(vibe).sort()).toEqual(["crime", "part", "tag"]);
  });
});
