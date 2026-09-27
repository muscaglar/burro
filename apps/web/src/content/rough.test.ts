/** @jest-environment node */
import { readFileSync } from "node:fs";
import path from "node:path";

import { readRecorded, recordedAnswer } from "@/lib/api/recorded";
import type { MetaData } from "@/lib/api/schema";

import { everyRecording, ROUGH, sayingSoAmong } from "../../test/support/rough";
import * as rough from "./rough";
import { heldBack, isRough } from "./rough";

const meta: MetaData = recordedAnswer("get_meta", "meta").body.data;
const variantA: MetaData = (readRecorded("variant-a/meta").body as { data: MetaData }).data;
const source = readFileSync(path.resolve(__dirname, "rough.ts"), "utf8");

describe("a vibe the service says is less sure", () => {
  test("test_the_service_still_says_which_vibe_it_is_in_a_code_and_says_nothing_more_of_it_in_any_recorded_answer", () => {
    const lessSure = (given: MetaData) => given.tags.filter((tag) => tag.sureness === "rough_guide").map((tag) => tag.tag_id);

    // It is so whichever way gritty was built.
    expect([lessSure(meta), lessSure(variantA)]).toEqual([[ROUGH.tag_id], [ROUGH.tag_id]]);
    // Until 2026-09-26 it gave the label and the sentence of that vibe, in a list that it
    // serves still, so that the shape of its answer is as it was. The list holds nothing.
    expect([meta.rough_guides, variantA.rough_guides]).toEqual([[], []]);
    // And no answer that was recorded says either anywhere, of any route.
    const recorded = everyRecording();
    expect(recorded.length).toBeGreaterThan(250);
    expect(sayingSoAmong(recorded)).toEqual([]);
  });

  test("test_the_website_holds_nothing_that_reads_or_joins_what_such_a_vibe_says_of_itself", () => {
    // The founder: "remove the concept of rough guide, we don't want to pass this on to a user".
    // A function was kept that gave nothing of any vibe, and one that joined a label to its
    // sentence, for the parts that called them. Nothing calls them, and they are gone.
    expect(Object.keys(rough).sort()).toEqual(["LESS_SURE", "heldBack", "isRough"]);
  });

  test("test_what_is_done_with_it_is_said_by_nothing_and_is_chosen_in_one_line", () => {
    // A vibe that is less sure is held back from what the website says in short: the lines
    // of what an area is like, what two areas share, and the examples of what a vibe is.
    expect(meta.tags.filter(isRough).map((tag) => tag.tag_id)).toEqual(["village_feel"]);
    expect(/^export const LESS_SURE: LessSure = "held-back";$/m.test(source)).toBe(true);
    // A vibe that does not say is as sure as the rest, and so is one of an answer written before the field.
    for (const tag of meta.tags.filter((one) => one.tag_id !== "village_feel")) expect([tag.tag_id, tag.sureness, isRough(tag)]).toEqual([tag.tag_id, "as_the_rest", false]);
    const before: { tag_id: "village_feel"; sureness?: "rough_guide" } = { tag_id: "village_feel" };
    expect(isRough(before)).toBe(false);
    // Chosen the other way, no vibe is held back from anything.
    expect(meta.tags.filter((tag) => heldBack(tag, "as-the-rest"))).toEqual([]);
    expect(meta.tags.filter((tag) => heldBack(tag, "held-back")).map((tag) => tag.tag_id)).toEqual(["village_feel"]);
  });

  test("test_no_vibe_no_label_and_no_sentence_is_written_into_the_website", () => {
    // The file holds the rule and no word of any vibe.
    const written = source.replace(/\/\*\*[\s\S]*?\*\//g, "");
    for (const tag of meta.tags) {
      expect(written.includes(tag.tag_id)).toBe(false);
      expect(written.includes(tag.label)).toBe(false);
    }
    // Nor what a service said of such a vibe until it stopped, which no recorded answer holds.
    expect([written.includes(ROUGH.label), written.includes(ROUGH.why)]).toEqual([false, false]);
    // It reads nothing of what the service says a rough guide says of itself.
    expect(/rough_guides|\.label\b|\.why\b|\bfind\(/.test(written)).toBe(false);
  });
});
