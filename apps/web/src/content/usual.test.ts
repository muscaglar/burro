/** @jest-environment node */
/**
 * What the settings say of what Burro counts in every search. It is read by somebody who has
 * never seen Burro, who has just been told that a fit is based on ten things where they asked
 * for four. These hold what can be held of that by a rule, and what each line must go on
 * saying however it is put.
 */

import { USUAL } from "./usual";

/** Names as the API gives them to the settings a search starts from. None is written into the website. */
const SIX = ["Cleaner air", "Nearer a town centre", "Less transport noise", "Nearer a park", "More lines nearby", "Nearer a station"];
const ONE = ["Cleaner air"];

/** Every sentence of the head of the settings that names what is counted in every search. */
const SAYS = [USUAL.before, USUAL.little, USUAL.also, USUAL.alone] as const;
const lines = [...SAYS.flatMap((say) => [say(SIX), say(ONE)]), USUAL.onTheBar("Nearer a park")];

/** The sentences of a line: what ends in a full stop, cut where one gives way to the next. */
function sentencesOf(words: string): string[] {
  return words
    .split(/(?<=[.?])\s+/)
    .map((sentence) => sentence.trim())
    .filter((sentence) => sentence !== "");
}

describe("what the settings say of what burro counts in every search", () => {
  test("test_every_line_is_whole_sentences_and_none_is_more_than_two", () => {
    // A sentence or two: it stands over the settings a person opened to change one thing.
    const said = lines.filter((words) => words !== USUAL.onTheBar("Nearer a park"));

    expect(said.filter((words) => !/\.$/.test(words))).toEqual([]);
    expect(said.filter((words) => sentencesOf(words).length > 2)).toEqual([]);
    expect(said.flatMap((words) => sentencesOf(words).filter((sentence) => sentence.split(/\s+/).length < 8))).toEqual([]);
  });

  test("test_no_line_uses_a_word_of_the_design_or_a_character_the_face_of_a_sentence_lacks", () => {
    const unknown = /\bthis data\b|\breleases?\b|\brecipes?\b|\bparts?\b|\bweights?\b|\bdefaults?\b|\bassumed\b|\busual settings?\b/i;

    expect(lines.filter((words) => unknown.test(words))).toEqual([]);
    expect(lines.filter((words) => /[^\x20-\x7e]/.test(words))).toEqual([]);
    expect(lines.filter((words) => /!/.test(words))).toEqual([]);
  });

  test("test_each_is_named_as_the_api_names_it_and_the_names_are_said_as_a_person_says_a_list", () => {
    for (const say of SAYS) {
      expect(say(SIX)).toContain(
        "Cleaner air, Nearer a town centre, Less transport noise, Nearer a park, More lines nearby and Nearer a station.",
      );
      expect(say(ONE)).toContain(": Cleaner air.");
      // One thing is not said to be a few, and is not spoken of as many.
      expect(say(ONE)).toMatch(/\bone everyday thing\b/);
      expect(say(ONE)).not.toMatch(/\bthings that\b|\beach\b|\bthem\b/);
      expect(say(SIX)).toMatch(/\ba few everyday things\b/);
    }
  });

  test("test_every_line_says_that_each_can_be_turned_up_down_or_off_and_where", () => {
    // The chip that hinted at them is gone. What nobody chose can be changed, and the line says where.
    for (const say of SAYS) {
      for (const names of [SIX, ONE]) expect(say(names)).toMatch(/up, down or off in its group below\.$/);
    }
  });

  test("test_only_one_line_says_how_much_they_count_and_it_gives_no_verdict", () => {
    // It is said only where it is so, which the settings work out from the search.
    expect(USUAL.little(SIX)).toContain("Each of them counts for much less than the things you asked for");
    expect(USUAL.little(ONE)).toContain("It counts for much less than the things you asked for");
    for (const say of [USUAL.before, USUAL.also, USUAL.alone]) {
      expect(say(SIX)).not.toMatch(/\bless\b|\bmore\b|\blittle\b/);
    }
    expect(lines.filter((words) => /\b(best|better|good|bad|worse|worst|safe|important)\b/i.test(words))).toEqual([]);
  });

  test("test_where_nothing_was_asked_for_the_line_says_what_the_ranking_goes_by", () => {
    expect(USUAL.alone(SIX)).toMatch(/^You have not asked for anything yet, so Burro has ranked the areas by /);
    // Before a search nothing is ranked, and the line does not say that anything is.
    expect(USUAL.before(SIX)).not.toMatch(/\branked\b|\branking\b/);
    expect(USUAL.before(SIX)).toMatch(/^Burro already takes /);
  });

  test("test_the_bar_of_a_group_says_what_it_holds_of_them_as_the_head_says_it", () => {
    expect(USUAL.onTheBar("Nearer a park")).toBe("Counted in every search: Nearer a park");
    for (const say of SAYS) expect(say(SIX)).toContain("in every search");
  });
});
