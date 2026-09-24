import { recordedAnswer } from "@/lib/api/recorded";

import { unreadStretches, type Span } from "./unread";

const sentenceOf = (scenario: string) =>
  (recordedAnswer("interpret", scenario).request.body as { text: string }).text;
const readOf = (scenario: string) => recordedAnswer("interpret", scenario).body.data.rests_on;

/** Where `words` stand in `text`, as the API counts: in code points. */
function at(text: string, words: string): Span {
  const from = text.indexOf(words);
  if (from < 0) throw new Error("the words are not in the text");
  const start = Array.from(text.slice(0, from)).length;
  return { start, end: start + Array.from(words).length };
}

/** The words of each stretch, cut from the text as a box would select them. */
const wordsOf = (text: string, spans: readonly Span[]) =>
  unreadStretches(text, spans).map(({ start, end }) => text.slice(start, end));

describe("the parts of what was typed that nothing was read from", () => {
  // The sentence a person typed into the website when it was first run in a browser. The
  // reader made one edit of it, from the third sentence, and the page ranked as if it had
  // read all three.
  const TYPED =
    "I rent and can pay up to £1,500 a month for a one bed flat. I work at Cindermoor Works and want to get there within 35 minutes. A park nearby would be good.";

  test("test_a_sentence_no_edit_rests_on_is_a_part_that_was_not_read", () => {
    expect(wordsOf(TYPED, [at(TYPED, "park nearby")])).toEqual([
      "I rent and can pay up to £1,500 a month for a one bed flat. I work at Cindermoor Works and want to get there within 35 minutes.",
    ]);
  });

  test("test_two_parts_with_a_sentence_that_was_read_between_them_are_two_parts", () => {
    const text = "Somewhere with llamas. A park nearby. And a nice vibe please!";

    expect(wordsOf(text, [at(text, "park nearby")])).toEqual(["Somewhere with llamas.", "And a nice vibe please!"]);
  });

  test("test_the_words_between_two_things_that_were_read_in_one_sentence_are_not_a_part", () => {
    // "a", "a month" and "and" stand between the words the edits rest on. They are no part
    // that was not read: the sentence they stand in was read.
    for (const scenario of ["interpret-first", "interpret-two-journeys", "interpret-notice", "interpret-buyer-family"]) {
      expect(wordsOf(sentenceOf(scenario), readOf(scenario))).toEqual([]);
    }
  });

  test("test_a_sentence_ends_where_the_reader_ends_one_and_nowhere_else", () => {
    // At a full stop, a question mark or an exclamation mark that ends a word, and at a new
    // line: contract 8.2. A comma ends none, nor does a stop inside a figure.
    const text = "Up to £1.5k a month, near St. Mary's\nand quiet";

    // "St." ends a sentence, as it does for the reader. Two parts side by side are given as one.
    expect(wordsOf(text, [at(text, "£1.5k")])).toEqual(["Mary's\nand quiet"]);
    expect(wordsOf(text, [at(text, "£1.5k"), at(text, "Mary's")])).toEqual(["and quiet"]);
    expect(wordsOf(text, [at(text, "quiet")])).toEqual(["Up to £1.5k a month, near St. Mary's"]);
    expect(wordsOf(text, [at(text, "St. Mary's")])).toEqual(["and quiet"]);
  });

  test("test_with_nothing_read_the_whole_of_it_is_one_part", () => {
    expect(wordsOf(TYPED, [])).toEqual([TYPED]);
    expect(wordsOf(sentenceOf("interpret-nothing-read"), readOf("interpret-nothing-read"))).toEqual([
      sentenceOf("interpret-nothing-read"),
    ]);
  });

  test("test_marks_alone_are_no_part", () => {
    const text = "A park nearby. ... !!";

    expect(wordsOf(text, [at(text, "park nearby")])).toEqual([]);
  });

  test("test_the_offsets_are_counted_as_the_api_counts_them_and_given_as_the_box_counts_them", () => {
    // The API counts code points. A box counts as JavaScript does, in units of which most
    // emoji take two: contract 9.2. Each part is given where the box would select it.
    const text = "Somewhere fun 🎉🎉. A park nearby. Dogs 🐕 welcome.";
    const span = at(text, "park nearby");

    expect(span.start).toBe(text.indexOf("park nearby") - 2);
    expect(wordsOf(text, [span])).toEqual(["Somewhere fun 🎉🎉.", "Dogs 🐕 welcome."]);
  });

  test("test_the_offsets_are_into_the_text_as_it_was_sent_and_the_parts_are_into_the_box_as_it_stands", () => {
    // The website sends what is in the box without the space around it.
    const box = "  \n Llamas please. A park nearby.  ";
    const sent = box.trim();

    const parts = unreadStretches(box, [at(sent, "park nearby")]);

    expect(parts.map(({ start, end }) => box.slice(start, end))).toEqual(["Llamas please."]);
  });

  test("test_an_offset_outside_the_text_marks_nothing_outside_it", () => {
    const text = "A park nearby.";

    for (const span of [{ start: -5, end: 3 }, { start: 5, end: 500 }, { start: 90, end: 95 }, { start: 8, end: 2 }]) {
      for (const part of unreadStretches(text, [span])) {
        expect(part.start).toBeGreaterThanOrEqual(0);
        expect(part.end).toBeLessThanOrEqual(text.length);
        expect(part.end).toBeGreaterThan(part.start);
      }
    }
  });

  test("test_nothing_of_the_text_is_kept_or_returned", () => {
    const parts = unreadStretches(TYPED, [at(TYPED, "park nearby")]);

    expect(JSON.stringify(parts)).toBe(JSON.stringify(parts.map(({ start, end }) => ({ start, end }))));
    for (const part of parts) expect(Object.values(part).every((value) => typeof value === "number")).toBe(true);
  });
});
