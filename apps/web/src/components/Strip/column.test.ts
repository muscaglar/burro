/** @jest-environment node */
/**
 * What a style sheet is handed of the column of names: the names that stand in it, as the
 * words of one declaration. No vibe and no place is named here but by the recording.
 */

import { recordedAnswer } from "@/lib/api/recorded";

import { asLines, namesOf, withThePlaceOf } from "./column";

const meta = recordedAnswer("get_meta", "meta").body.data;
const first = recordedAnswer("rank", "rank-first").body.data;

describe("the names that stand in one column", () => {
  test("test_each_name_that_a_strip_of_the_list_draws_is_in_it_once_in_the_order_it_is_first_met", () => {
    const names = namesOf(first.ranked.map((area) => area.strip), meta.tags);
    const drawn = first.ranked.flatMap((area) => area.strip.map((mark) => mark.tag_id));
    const labels = [...new Set(drawn)].map((id) => meta.tags.find((tag) => tag.tag_id === id)?.label);

    expect(names).toEqual(labels);
    expect(new Set(names).size).toBe(names.length);
    expect(names.length).toBeGreaterThan(3);
    // It holds a name of what is drawn and of nothing else: not of every vibe of the release.
    expect(names.length).toBeLessThan(meta.tags.length);
  });

  test("test_a_vibe_the_release_does_not_name_has_no_name_in_it_and_no_code_stands_in_for_one", () => {
    const [area] = first.ranked;
    const stranger = { ...(area?.strip[0] as (typeof first.ranked)[number]["strip"][number]), tag_id: "not_a_vibe" as never };

    expect(namesOf([[stranger]], meta.tags)).toEqual([]);
    expect(namesOf([], meta.tags)).toEqual([]);
  });
});

describe("the names, as a style sheet is handed them", () => {
  test("test_each_name_is_a_line_of_its_own_in_one_string", () => {
    expect(asLines(["Leafy", "Quiet streets"])).toBe('"Leafy\\a Quiet streets"');
    expect(asLines(["Leafy"])).toBe('"Leafy"');
    // With no name it is a string that holds nothing, and never no string at all.
    expect(asLines([])).toBe('""');
  });

  test("test_a_name_can_end_the_string_it_stands_in_by_nothing_it_holds", () => {
    // A name is the service's. Whatever it holds, it is a word of the string and no more:
    // a mark that would end the string, a line that would break it, a sign of an escape.
    expect(asLines(['A "quiet" end'])).toBe('"A \\22 quiet\\22  end"');
    expect(asLines(["one\\two"])).toBe('"one\\5c two"');
    expect(asLines(["one\ntwo\r\nthree"])).toBe('"one two three"');
    expect(asLines(["a;b}c{d"])).toBe('"a;b}c{d"');
    for (const name of ['"', "\\", '\\"', "\n", "a\\\n", '";} body{display:none} .x{content:"']) {
      const lines = asLines([name, "after"]);
      const inside = lines.slice(1, -1);
      // No mark of the string stands in it bare, and no line breaks it.
      expect([name, /["\n\r\f]/.test(inside)]).toEqual([name, false]);
      // Every sign of an escape in it begins one that is whole: six signs of a number and the room that ends it.
      expect([name, inside.replace(/\\[0-9a-f]{1,6} /g, "").includes("\\")]).toEqual([name, false]);
      expect([name, lines.startsWith('"'), lines.endsWith('"')]).toEqual([name, true, true]);
    }
  });

  test("test_what_is_handed_is_a_custom_property_of_the_names_and_of_what_stands_beside_them", () => {
    const handed = withThePlaceOf({ names: ["Leafy", "Going out"], groups: ["Asked for"] });

    expect(handed).toEqual({ "--names": '"Leafy\\a Going out"', "--groups": '"Asked for"' });
    // What is not handed is not set, so that what holds the strip may have set it.
    expect(withThePlaceOf({})).toEqual({});
    expect(Object.keys(withThePlaceOf({ beside: [] }))).toEqual([]);
    // What else stands in the column is a label on a board: its words, and the room its
    // board has about them, as a count of art pixels.
    expect(
      withThePlaceOf({
        beside: [
          { says: "Why it fits", more: 8 },
          { says: "Trade-off", more: 19 },
        ],
      }),
    ).toEqual({
      "--beside-1": '"Why it fits"',
      "--beside-1-more": "8",
      "--beside-2": '"Trade-off"',
      "--beside-2-more": "19",
    });
    // The room is a whole number of art pixels and no less than none: a drawing is never laid at a fraction of one.
    for (const more of [-1, 0.5, Number.NaN, Number.POSITIVE_INFINITY]) {
      expect([more, withThePlaceOf({ beside: [{ says: "a board", more }] })["--beside-1-more" as never]]).toEqual([more, "0"]);
    }
  });
});
