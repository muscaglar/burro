/** @jest-environment node */
import { readFileSync } from "node:fs";
import path from "node:path";

import { readRecorded, recordedAnswer, type Recorded } from "@/lib/api/recorded";
import type { InterpretData, MetaData } from "@/lib/api/schema";
import * as server from "@/lib/api/server";

import { problemsWith } from "./contract";
import { asAPageReads, everyRecording, OF_RENTS, offeringSo, ROUGH, ROUGH_NOTE, sayingSo, sayingSoAmong, SAYS_SO, service } from "./rough";

const recorded = recordedAnswer("get_meta", "meta");
const meta: MetaData = recorded.body.data;
const reading = recordedAnswer("interpret", "interpret-suggest-rough-guide");
const read: InterpretData = reading.body.data;

/** A recording, with what it holds of the release or of a reading changed. */
const holding = (of: Recorded, data: unknown): Recorded => ({ ...of, body: { ...(of.body as object), data } });

/** The contract, as it is written, with each run of space as one. */
const contract = () =>
  readFileSync(path.resolve(__dirname, "../../../../docs/design/contract.md"), "utf8").replace(/\s+/g, " ");

describe("what a service said of a rough guide, for a test to lay on an answer", () => {
  test("test_the_label_and_the_sentence_it_keeps_are_the_ones_the_contract_gives_word_for_word", () => {
    // Core holds both still, and the contract writes the sentence out whole, in quotation marks.
    expect(contract().includes(`"${ROUGH.why}"`)).toBe(true);
    // Of the note of an offer it gives the label and how the sentence opens.
    const [, opens] = new RegExp(`"(${ROUGH.label}\\. [^"]+?) \\.\\.\\."`).exec(contract()) ?? [];
    expect(opens?.length).toBeGreaterThan(ROUGH.label.length + 20);
    expect(ROUGH_NOTE.startsWith(opens ?? "nothing")).toBe(true);
    // Each is found by what the service holds its own answers to.
    expect([ROUGH.label, ROUGH.why, ROUGH_NOTE].map((words) => SAYS_SO.test(words))).toEqual([true, true, true]);
    expect(meta.tags.map((tag) => tag.tag_id)).toContain(ROUGH.tag_id);
  });

  test("test_laid_on_an_answer_of_route_11_the_words_stand_where_the_service_gave_them_and_the_rest_is_as_it_came", () => {
    const laid = sayingSo(meta);

    expect(laid.rough_guides).toEqual([ROUGH]);
    expect(Object.keys(laid)).toEqual(Object.keys(meta));
    for (const [name, said] of Object.entries(meta)) {
      if (name !== "rough_guides") expect([name, (laid as unknown as Record<string, unknown>)[name] === said]).toEqual([name, true]);
    }
    // It is an answer of the contract still: the shape of route 11 did not change.
    expect(problemsWith("MetaData", meta)).toEqual([]);
    expect(problemsWith("MetaData", laid)).toEqual([]);
  });

  test("test_the_answer_it_was_handed_is_left_as_it_was_recorded", () => {
    const before = JSON.stringify(meta);

    sayingSo(meta);
    sayingSo(meta, [meta.tags[0]!.tag_id]);
    offeringSo(read);

    expect(JSON.stringify(meta) === before).toBe(true);
    expect(meta.rough_guides).toEqual([]);
    // Read from the file again, it is what the reading was before anything was laid on it.
    expect(JSON.stringify(read) === JSON.stringify(recordedAnswer("interpret", "interpret-suggest-rough-guide").body.data)).toBe(true);
  });

  test("test_which_vibe_is_less_sure_is_the_recorded_services_to_say_and_an_answer_that_does_not_say_it_is_refused", () => {
    const silent = { ...meta, tags: meta.tags.map((tag) => ({ ...tag, sureness: "as_the_rest" as const })) };
    const without = { ...meta, tags: meta.tags.filter((tag) => tag.tag_id !== ROUGH.tag_id) };

    expect(meta.tags.filter((tag) => tag.sureness === "rough_guide").map((tag) => tag.tag_id)).toEqual([ROUGH.tag_id]);
    expect(() => sayingSo(silent)).toThrow(/does not say in its code/);
    expect(() => sayingSo(without)).toThrow(/does not say in its code/);
    // Nor is it enough that it is said of another vibe.
    expect(() => sayingSo(silent, [meta.tags[0]!.tag_id])).toThrow(/does not say in its code/);
  });

  test("test_said_of_other_vibes_as_well_each_is_given_the_code_and_the_words", () => {
    const others = meta.tags.filter((tag) => tag.tag_id !== ROUGH.tag_id).slice(0, 2);
    const laid = sayingSo(meta, others.map((tag) => tag.tag_id));
    const every = sayingSo(meta, meta.tags.map((tag) => tag.tag_id));

    expect(others.map((tag) => tag.sureness)).toEqual(["as_the_rest", "as_the_rest"]);
    const lessSure = laid.tags.filter((tag) => tag.sureness === "rough_guide").map((tag) => tag.tag_id);
    expect([...lessSure].sort()).toEqual([ROUGH.tag_id, ...others.map((tag) => tag.tag_id)].sort());
    // In the order of the vibes of the release, as the service gave them.
    expect(laid.rough_guides).toEqual(lessSure.map((tag_id) => ({ tag_id, label: ROUGH.label, why: ROUGH.why })));
    expect(every.rough_guides.map((told) => told.tag_id)).toEqual(meta.tags.map((tag) => tag.tag_id));
    expect(every.tags.map((tag) => tag.sureness)).toEqual(meta.tags.map(() => "rough_guide"));
    // Nothing else of a vibe is changed, and it is an answer of the contract still.
    const but = ({ sureness, ...rest }: MetaData["tags"][number]) => [sureness.length > 0, rest];
    expect(every.tags.map(but)).toEqual(meta.tags.map(but));
    expect(problemsWith("MetaData", every)).toEqual([]);
  });

  test("test_laid_on_a_reading_the_words_stand_after_the_note_of_each_offer_of_the_vibe_and_of_no_other", () => {
    const laid = offeringSo(read);
    const noted = { ...read, suggestions: read.suggestions.map((offer) => ({ ...offer, note: "What was said before." })) };

    expect(read.suggestions.map((offer) => offer.target)).toEqual(["tag:leafy", "tag:quiet_residential", `tag:${ROUGH.tag_id}`]);
    expect(laid.suggestions.map((offer) => offer.note)).toEqual(["", "", ROUGH_NOTE]);
    expect(ROUGH_NOTE).toBe(`${ROUGH.label}. ${ROUGH.why}`);
    expect(offeringSo(noted).suggestions.map((offer) => offer.note)).toEqual([
      "What was said before.",
      "What was said before.",
      `What was said before. ${ROUGH_NOTE}`,
    ]);
    // Nothing else of an offer is changed, and it is an answer of the contract still.
    const but = ({ note, ...rest }: InterpretData["suggestions"][number]) => [typeof note, rest];
    expect(laid.suggestions.map(but)).toEqual(read.suggestions.map(but));
    expect(Object.keys(laid)).toEqual(Object.keys(read));
    expect(problemsWith("InterpretData", laid)).toEqual([]);
  });

  test("test_a_reading_that_offers_no_such_vibe_is_refused", () => {
    const first = recordedAnswer("interpret", "interpret-first").body.data;

    expect(() => offeringSo(first)).toThrow(/offers no vibe/);
    expect(() => offeringSo({ ...read, suggestions: read.suggestions.slice(0, 2) })).toThrow(/offers no vibe/);
  });

  test("test_among_some_answers_each_that_says_so_is_found_wherever_it_says_it", () => {
    const inTheList = holding(recorded, sayingSo(meta));
    const inTheListInOtherWords = holding(recorded, { ...meta, rough_guides: [{ tag_id: ROUGH.tag_id, label: "Another label", why: "Another sentence." }] });
    const inANote = holding(reading, offeringSo(read));
    const inAnotherCase = holding(reading, {
      ...read,
      suggestions: read.suggestions.map((offer) => ({ ...offer, note: `A village feel (a ${ROUGH.label.toLowerCase()}).` })),
    });

    expect(sayingSoAmong([recorded, reading])).toEqual([]);
    expect(sayingSoAmong([inTheList])).toEqual(["meta"]);
    expect(sayingSoAmong([inTheListInOtherWords])).toEqual(["meta"]);
    expect(sayingSoAmong([inANote])).toEqual(["interpret-suggest-rough-guide"]);
    expect(sayingSoAmong([inAnotherCase])).toEqual(["interpret-suggest-rough-guide"]);
    expect(sayingSoAmong([recorded, inANote, reading, inTheList])).toEqual(["interpret-suggest-rough-guide", "meta"]);
  });

  test("test_the_caution_on_rents_says_nothing_of_a_rough_guide_and_is_set_aside_nowhere", () => {
    // Until 2026-09-27 it said that Burro uses the rents as a rough guide to what a home lets
    // for. A page shows it as it comes, so it was the last place a page could say so.
    const release = readRecorded("let/meta");
    const page = readRecorded("let/area");
    const caution = (release.body as { data: MetaData }).data.rents?.caution ?? "";

    expect(caution.endsWith(` ${OF_RENTS.says}`)).toBe(true);
    expect([SAYS_SO.test(caution), /\brough\b/i.test(caution)]).toEqual([false, false]);
    expect([release, page].map((one) => JSON.stringify(one.body).includes(caution))).toEqual([true, true]);
    expect(sayingSoAmong([release, page])).toEqual([]);
    // Worded as it was, it is found wherever it stands: beside the answer of route 11 that
    // gives it, which set it aside, and in that answer itself.
    const asItWas = (one: Recorded): Recorded => ({
      ...one,
      body: JSON.parse(JSON.stringify(one.body).split(OF_RENTS.says).join(OF_RENTS.said)) as Recorded["body"],
    });
    expect(SAYS_SO.test(OF_RENTS.said)).toBe(true);
    expect(sayingSoAmong([asItWas(release), asItWas(page)])).toEqual(["let/meta", "let/area"]);
    expect(sayingSoAmong([release, asItWas(page)])).toEqual(["let/area"]);
    expect(sayingSoAmong([asItWas(release), page])).toEqual(["let/meta"]);
    // And so is an answer that says it of a vibe.
    const ofAVibe = holding(release, sayingSo((release.body as { data: MetaData }).data));
    expect(sayingSoAmong([ofAVibe, page])).toEqual(["let/meta"]);
  });

  test("test_what_a_page_reads_as_it_is_built_says_so_while_a_test_has_it_say_so_and_is_as_it_was_recorded_otherwise", async () => {
    const reads = asAPageReads(server);

    expect(service.saysSo).toBe(false);
    expect((await reads.loadMeta()).data).toEqual(meta);
    service.saysSo = true;
    const said = await reads.loadMeta();
    expect(said.data).toEqual(sayingSo(meta));
    expect(said.data.rough_guides).toEqual([ROUGH]);
    expect(said.meta).toEqual(recorded.body.meta);
    // Every other route is read as it was, by what read it before.
    expect(Object.keys(reads).sort()).toEqual(Object.keys(server).sort());
    for (const [name, reader] of Object.entries(server)) {
      if (name !== "loadMeta") expect([name, (reads as unknown as Record<string, unknown>)[name] === reader]).toEqual([name, true]);
    }
  });

  test("test_what_a_test_turned_on_is_off_again_in_the_test_after_it", () => {
    // The test before this one left it on.
    expect(service.saysSo).toBe(false);
  });

  test("test_every_answer_that_was_recorded_is_read_and_the_list_of_scenarios_is_not", () => {
    const all = everyRecording();

    expect(all.length).toBeGreaterThan(250);
    expect(all.map((one) => one.scenario)).toContain("meta");
    expect(all.map((one) => one.scenario)).toContain("let/area");
    expect(all.filter((one) => one.request.operation_id === "get_meta").length).toBeGreaterThan(10);
    expect(all.filter((one) => typeof one.scenario !== "string" || one.body === undefined)).toEqual([]);
  });
});
