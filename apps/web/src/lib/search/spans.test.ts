import { recordedAnswer } from "@/lib/api/recorded";

import { inTheBox } from "./spans";

const textOf = (scenario: string) => (recordedAnswer("interpret", scenario).request.body as { text: string }).text;

describe("where a stretch of what was typed stands in the box", () => {
  test("test_a_stretch_is_where_the_api_says_it_is", () => {
    const text = textOf("interpret-suggest");
    const { unread, suggestions } = recordedAnswer("interpret", "interpret-suggest").body.data;

    expect(inTheBox(text, unread).map(({ start, end }) => text.slice(start, end))).toEqual(["are so"]);
    expect(
      suggestions.map(({ spans }) => inTheBox(text, spans).map(({ start, end }) => text.slice(start, end))),
    ).toEqual([["Pubs"], ["noisy"]]);
  });

  test("test_space_before_what_was_typed_moves_every_stretch_along", () => {
    const text = textOf("interpret-suggest");
    const { unread } = recordedAnswer("interpret", "interpret-suggest").body.data;
    const box = `  \n ${text}  `;

    expect(inTheBox(box, unread).map(({ start, end }) => box.slice(start, end))).toEqual(["are so"]);
  });

  test("test_the_api_counts_in_code_points_and_the_box_in_units", () => {
    // Two characters that are each two units long, before the stretch.
    const box = "\u{1F3E1}\u{1F333} leafy";

    expect(inTheBox(box, [{ start: 3, end: 8 }]).map(({ start, end }) => box.slice(start, end))).toEqual(["leafy"]);
  });

  test("test_a_stretch_that_is_empty_or_outside_the_text_is_left_out", () => {
    expect(inTheBox("leafy", [{ start: 2, end: 2 }])).toEqual([]);
    expect(inTheBox("leafy", [{ start: 3, end: 1 }])).toEqual([]);
    expect(inTheBox("leafy", [{ start: 0, end: 9 }])).toEqual([]);
    expect(inTheBox("leafy", [{ start: -1, end: 2 }])).toEqual([]);
    expect(inTheBox("leafy", [{ start: 0.5, end: 2 }])).toEqual([]);
  });

  test("test_it_gives_back_offsets_and_never_a_word", () => {
    const found = inTheBox("leafy and quiet", [{ start: 0, end: 5 }]);

    expect(JSON.stringify(found)).toBe('[{"start":0,"end":5}]');
  });
});
