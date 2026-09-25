/** @jest-environment node */
import { readFileSync } from "node:fs";
import path from "node:path";

import { readRecorded, recordedAnswer } from "@/lib/api/recorded";
import type { MetaData } from "@/lib/api/schema";

import { isRough, roughOf, saidOf } from "./rough";

const meta: MetaData = recordedAnswer("get_meta", "meta").body.data;
const variantA: MetaData = (readRecorded("variant-a/meta").body as { data: MetaData }).data;
const tagOf = (tagId: string) => meta.tags.find((tag) => tag.tag_id === tagId)!;
const source = readFileSync(path.resolve(__dirname, "rough.ts"), "utf8");

describe("a vibe that is a rough guide", () => {
  test("test_which_vibe_is_one_and_what_it_says_of_itself_are_the_apis", () => {
    expect(meta.rough_guides).toEqual([
      {
        tag_id: "village_feel",
        label: "Rough guide",
        why: "Of the areas it puts highest, about half read as villages to people, and it takes some busy main roads and some grand inner streets for villages.",
      },
    ]);
    expect(meta.tags.filter(isRough).map((tag) => tag.tag_id)).toEqual(["village_feel"]);
    expect(roughOf(tagOf("village_feel"), meta)).toEqual(meta.rough_guides[0]);
    expect(saidOf(meta.rough_guides[0]!)).toBe(`${meta.rough_guides[0]?.label}. ${meta.rough_guides[0]?.why}`);
    // It is so whichever way gritty was built.
    expect(variantA.rough_guides).toEqual(meta.rough_guides);
  });

  test("test_no_vibe_no_label_and_no_sentence_is_written_into_the_website", () => {
    // The file holds the rule and no word of any vibe: what is said is route 11's.
    const written = source.replace(/\/\*\*[\s\S]*?\*\//g, "");
    for (const tag of meta.tags) {
      expect(written.includes(tag.tag_id)).toBe(false);
      expect(written.includes(tag.label)).toBe(false);
    }
    for (const told of meta.rough_guides) {
      expect(written.includes(told.label)).toBe(false);
      expect(written.includes(told.why)).toBe(false);
    }
  });

  test("test_a_vibe_that_does_not_say_is_as_sure_as_the_rest", () => {
    for (const tag of meta.tags.filter((one) => one.tag_id !== "village_feel")) {
      expect(tag.sureness).toBe("as_the_rest");
      expect(roughOf(tag, meta)).toBeNull();
    }
    // An answer that was written before the field holds none, and nothing is said of any vibe.
    const before: { tag_id: "village_feel"; sureness?: "rough_guide" } = { tag_id: "village_feel" };
    expect(isRough(before)).toBe(false);
    expect(roughOf(before, meta)).toBeNull();
    expect(roughOf(tagOf("village_feel"), {})).toBeNull();
    expect(roughOf(tagOf("village_feel"), { rough_guides: [] })).toBeNull();
  });

  test("test_it_is_never_worked_out_from_anything_but_what_the_vibe_says_of_itself", () => {
    // A label served for a vibe that does not say it is one is said of no vibe.
    const misfiled = { rough_guides: [{ ...meta.rough_guides[0]!, tag_id: "leafy" as const }] };
    expect(roughOf(tagOf("leafy"), misfiled)).toBeNull();
    expect(roughOf(tagOf("village_feel"), misfiled)).toBeNull();
  });
});
