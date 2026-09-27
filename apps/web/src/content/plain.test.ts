/** @jest-environment node */
/**
 * The words of an area's page, and of everything the website says of a fact, are written
 * for a person who has never seen Burro: somebody choosing where to live, who has not read
 * its design. These hold what can be held of that by a rule. That a sentence reads well is
 * for a person to judge, and no test says it.
 */

import * as area from "./area";
import * as census from "./census";
import * as crime from "./crime";
import * as facts from "./facts";
import * as income from "./income";
import * as labels from "./labels";

/** A name that stands in a gap, where a line is filled with a name or a figure the API sent. */
const GAP = "Somewhere";

/** Every string of a file of words, with where it stands. A line with a gap is filled with a name. */
function wordsOf(file: string, held: unknown): [where: string, words: string][] {
  const found: [string, string][] = [];
  const walk = (where: string, value: unknown) => {
    if (typeof value === "string") found.push([where, value]);
    else if (typeof value === "function") {
      // What reads a release is no line of words. It is handed a record, and a name breaks it.
      try {
        const said: unknown = (value as (...gaps: string[]) => unknown)(...Array.from({ length: value.length }, () => GAP));
        if (typeof said === "string") found.push([where, said]);
      } catch {
        return;
      }
    } else if (Array.isArray(value)) value.forEach((one, at) => walk(`${where}[${at}]`, one));
    else if (typeof value === "object" && value !== null) {
      for (const [key, one] of Object.entries(value)) walk(`${where}.${key}`, one);
    }
  };
  walk(file, held);
  return found;
}

const copy = [
  ...wordsOf("area", area),
  ...wordsOf("census", census),
  ...wordsOf("crime", crime),
  ...wordsOf("facts", facts),
  ...wordsOf("income", income),
  ...wordsOf("labels", labels),
];

/** The sentences of a line: what ends in a full stop, cut where one sentence gives way to the next. */
function sentencesOf(words: string): string[] {
  if (!/[.?]$/.test(words)) return [];
  return words
    .split(/(?<=[.?])\s+/)
    .map((sentence) => sentence.trim())
    .filter((sentence) => sentence !== "");
}

describe("the words of an area's page and of a fact", () => {
  test("test_the_files_of_words_are_read_whole", () => {
    expect(copy.length).toBeGreaterThan(180);
    // A line with a gap is read with the gap filled, so that the words round it are read too.
    expect(copy.filter(([, words]) => words.includes(GAP)).length).toBeGreaterThanOrEqual(10);
  });

  test("test_no_line_uses_a_word_of_the_product_that_a_newcomer_does_not_know", () => {
    // Each was read on the page of an area by somebody who had not read the design, and
    // none said anything to them: "this data", a release, a recipe and its parts, hundredths.
    const unknown = /\bthis data\b|\breleases?\b|\brecipes?\b|\bparts?\b|\bhundredths\b|\bfor want of\b|\bin hand\b/i;

    expect(copy.filter(([, words]) => unknown.test(words))).toEqual([]);
  });

  test("test_no_line_holds_a_figure_of_its_own", () => {
    // Every figure on a page is a slot of a fact. A line may say of what a share is a share,
    // and that is the one figure written here.
    const ofAHundred = area.PORTRAIT.madeOf.shareOf(0).replace("0", "");
    const held = copy.filter(([, words]) => /\d/.test(words.replace(ofAHundred, "")));

    expect(ofAHundred).toMatch(/100/);
    expect(held).toEqual([]);
  });

  test("test_no_line_gives_a_verdict_on_a_place", () => {
    const verdict =
      /\b(best|better|worst|good|bad|nice|lovely|desirable|popular|sought|safe|safer|unsafe|dangerous|rough|up and coming|affluent|deprived|posh)\b/i;

    // Nor is a figure called better, or a journey the worst: which way a figure counts is
    // said by what follows for the ranking, and a journey does least well against its limit.
    expect(copy.filter(([, words]) => verdict.test(words))).toEqual([]);
  });

  test("test_a_sentence_is_whole_and_is_never_cut_down_to_a_fragment", () => {
    const short = copy.flatMap(([where, words]) =>
      sentencesOf(words)
        .filter((sentence) => sentence.split(/\s+/).length < 4)
        .map((sentence) => [where, sentence]),
    );

    expect(short).toEqual([]);
  });

  test("test_every_line_is_plain_british_english_with_nothing_the_face_of_a_sentence_lacks", () => {
    const loud = copy.filter(([, words]) => /!|\p{Extended_Pictographic}/u.test(words));
    // Plain quotation marks, a hyphen and the dot between two names: no arrow, tick or dash.
    const drawn = copy.filter(([, words]) => /[^\x20-\x7e£·]/.test(words));
    const american = copy.filter(([, words]) => /\b(neighbor|color|center|favorite|meter)s?\b/i.test(words));

    expect([loud, drawn, american]).toEqual([[], [], []]);
  });
});
