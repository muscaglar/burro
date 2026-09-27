/** @jest-environment node */
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { recordedAnswer } from "@/lib/api/recorded";

import { DRAWN_FROM, PARTS } from "./vibes";

const WEB = path.resolve(__dirname, "..", "..", "..");
const meta = recordedAnswer("get_meta", "meta").body.data;

/** Every file of the town: the rule, the part, its words and its drawings. */
function filesOfTheTown(): string[] {
  const within = (folder: string) =>
    readdirSync(path.join(WEB, folder)).map((name) => path.join(folder, name));
  return [
    ...within("src/lib/town"),
    ...within("src/components/Town"),
    "src/content/town.ts",
    "art/town.sprite.txt",
  ].sort();
}

const read = (file: string) => readFileSync(path.join(WEB, file), "utf8");
const escaped = (text: string) => text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

describe("the four vibes a town is drawn from", () => {
  test("test_each_part_is_drawn_from_a_vibe_of_its_own_which_the_recorded_release_holds", () => {
    const ids = PARTS.map((part) => DRAWN_FROM[part]);

    expect(PARTS).toHaveLength(4);
    expect(Object.keys(DRAWN_FROM).sort()).toEqual([...PARTS].sort());
    expect(new Set(ids).size).toBe(4);
    expect(ids.filter((id) => !meta.tags.some((tag) => tag.tag_id === id))).toEqual([]);
  });

  test("test_no_file_of_the_town_but_the_table_names_a_vibe_by_its_id", () => {
    // An id is written in quotes where it is named. The table is the one file that does,
    // so that a release that names its vibes otherwise is met in one place.
    const ids = meta.tags.map((tag) => escaped(tag.tag_id)).join("|");
    const named = new RegExp(`["'\`](${ids})["'\`]`);
    const naming = filesOfTheTown().filter((file) => named.test(read(file)));

    expect(filesOfTheTown().length).toBeGreaterThan(10);
    expect(naming).toEqual(["src/lib/town/vibes.ts"]);
    // And it names the four, and no fifth.
    const table = [...read("src/lib/town/vibes.ts").matchAll(new RegExp(`["'\`](${ids})["'\`]`, "g"))].map(([, id]) => id);
    expect(table.sort()).toEqual(PARTS.map((part) => DRAWN_FROM[part]).sort());
  });

  test("test_no_file_of_the_town_names_a_measure_or_a_family_by_its_id", () => {
    const ids = [...meta.features.map((measure) => measure.feature_id), ...meta.families.map(({ family }) => family)];
    const named = new RegExp(`["'\`](${ids.map(escaped).join("|")})["'\`]`);

    expect(ids.length).toBeGreaterThan(100);
    expect(filesOfTheTown().filter((file) => named.test(read(file)))).toEqual([]);
  });

  test("test_no_file_of_the_town_names_a_vibe_or_an_end_of_one_as_the_service_calls_it", () => {
    // What a vibe is called, and what its ends are called, are the service's to say. A
    // town says them after it, and holds none of its own: not in a part, a test, a style
    // sheet, a drawing or its words.
    const names = [
      ...new Set(meta.tags.flatMap((tag) => [tag.label, tag.short_label, tag.low_end, tag.high_end])),
    ].filter((name): name is string => name !== null);
    const held = filesOfTheTown().flatMap((file) =>
      names.filter((name) => new RegExp(`\\b${escaped(name)}\\b`).test(read(file))).map((name) => `${file}: ${name}`),
    );

    expect(names.length).toBeGreaterThan(20);
    expect(held).toEqual([]);
  });
});
