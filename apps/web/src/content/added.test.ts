/** @jest-environment node */
/**
 * What the box says once a search is open and Search is pressed on words the search has
 * read. It is read at a moment when a person does not know why nothing happened, by
 * somebody who has never seen Burro. These hold what can be held of that by a rule, and
 * what each line must go on saying however it is put.
 */

import { ADDED } from "./added";
import { PROMPT } from "./search";
import { REFINE } from "./ways";

const lines = Object.entries(ADDED);

/** The sentences of a line: what ends in a full stop, cut where one gives way to the next. */
function sentencesOf(words: string): string[] {
  return words
    .split(/(?<=[.?])\s+/)
    .map((sentence) => sentence.trim())
    .filter((sentence) => sentence !== "");
}

describe("what the box says of words it has read", () => {
  test("test_every_line_is_whole_sentences_and_none_is_cut_down_to_a_fragment", () => {
    const unfinished = lines.filter(([, words]) => !/\.$/.test(words));
    const short = lines.flatMap(([where, words]) =>
      sentencesOf(words)
        .filter((sentence) => sentence.split(/\s+/).length < 4)
        .map((sentence) => [where, sentence]),
    );

    expect(lines).toHaveLength(4);
    expect([unfinished, short]).toEqual([[], []]);
  });

  test("test_no_line_uses_a_word_of_the_design_or_a_character_the_face_of_a_sentence_lacks", () => {
    const unknown = /\bthis data\b|\breleases?\b|\brecipes?\b|\bparts?\b|\bfor want of\b|\bin hand\b/i;

    expect(lines.filter(([, words]) => unknown.test(words))).toEqual([]);
    expect(lines.filter(([, words]) => /[^\x20-\x7e]/.test(words))).toEqual([]);
    expect(lines.filter(([, words]) => /!/.test(words))).toEqual([]);
  });

  test("test_a_line_that_sends_a_person_to_the_settings_names_them_and_the_fold_that_holds_them", () => {
    // Once a search is open the settings are behind one fold. "Use the settings" named
    // nothing a person could find on the page, and the settings are named "Space requirements".
    const sends = lines.filter(([, words]) => /\bspace requirements\b/i.test(words));

    expect(sends.map(([where]) => where)).toEqual(["nothingNew", "changed", "changedToo"]);
    for (const [, words] of sends) expect(words).toContain(`your space requirements under ${REFINE.label}.`);
    expect(lines.filter(([, words]) => /\bsettings?\b/i.test(words))).toEqual([]);
  });

  test("test_each_line_says_that_burro_reads_what_is_added_and_not_what_it_has_read", () => {
    // What is sent to be read is what stands after the words the search has read, and
    // never those words a second time. Each line says so of what happened.
    expect(ADDED.nothingNew).toMatch(/already read everything in the box/);
    expect(ADDED.changed).toMatch(/only reads what you add at the end of the box/);
    expect(ADDED.changed).toMatch(/has not picked up the change/);
    expect(ADDED.changedToo).toMatch(/read what you added/);
    expect(ADDED.changedToo).toMatch(/not the change you made/);
    expect(ADDED.apart).toMatch(/without the words that came before/);
  });

  test("test_a_line_that_says_how_to_make_a_change_says_where_to_type_it", () => {
    for (const words of [ADDED.changed, ADDED.changedToo]) expect(words).toMatch(/at the end of the box/);
  });

  test("test_every_line_is_fixed_text_so_that_none_can_hold_what_was_typed", () => {
    // What was typed stays in the box. A line with a gap in it could be handed the words.
    const held: readonly unknown[] = Object.values(ADDED);

    expect(held.filter((words) => typeof words !== "string")).toEqual([]);
  });

  test("test_the_lines_stand_between_the_box_and_the_answer_and_are_no_longer_than_the_line_of_an_empty_box", () => {
    // What stands over the answer is said in short. The line of a box that is sent with
    // nothing in it stands in the same place, and these are held to twice its length.
    const most = PROMPT.emptyOpen.length * 2;

    expect(lines.filter(([, words]) => words.length > most).map(([where]) => where)).toEqual([]);
  });
});
