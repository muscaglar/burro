import { orderOf, screenSaidBy, SCREENS, type Part, type Screen } from "./order";

const before = (one: Part, other: Part, order: readonly Part[]) => order.indexOf(one) < order.indexOf(other);
const EVERY: readonly (Screen | null)[] = [null, ...SCREENS];

describe("the order of the page", () => {
  test("test_before_a_search_the_map_stands_over_the_two_ways_in_wherever_the_page_is_one_column", () => {
    // The founder: "The map should stay visible on both tabs". Seen on a phone: under Quick
    // search it began at 885 of 844, and under Deep search at 2,761, under every setting.
    for (const screen of ["narrow", "middle"] as const) {
      expect([screen, orderOf(screen, false, "after")]).toEqual([screen, ["map", "form", "refine", "unscripted"]]);
    }
  });

  test("test_on_a_wide_screen_it_stands_beside_them_and_comes_after_the_box_in_the_page", () => {
    const order = orderOf("wide", false, "after");

    expect(order).toEqual(["form", "refine", "unscripted", "map"]);
    expect(before("form", "map", order)).toBe(true);
  });

  test("test_a_page_is_built_as_for_one_column_since_it_is_built_with_no_screen_to_ask", () => {
    // What is built is what a phone draws before any script has run: nothing moves there
    // when the scripts have. A wide screen places every part by name, so nothing moves there either.
    expect(orderOf(null, false, "after")).toEqual(orderOf("narrow", false, "after"));
  });

  test("test_once_a_search_is_open_on_a_narrow_screen_what_refines_it_comes_after_the_first_result", () => {
    // Seen on a phone, by keyboard: the keys went to "Refine search" before the first result,
    // which was drawn over it, and then back up the page by 477 px.
    const order = orderOf("narrow", true, "after");

    expect(order).toEqual(["form", "results", "refine", "tools", "map", "rest"]);
    expect(before("results", "refine", order)).toBe(true);
  });

  test("test_on_any_other_screen_it_comes_before_the_first_result_where_it_is_drawn", () => {
    for (const screen of [null, "middle", "wide"] as const) {
      expect([screen, orderOf(screen, true, "after")]).toEqual([screen, ["form", "refine", "results", "tools", "map", "rest"]]);
    }
  });

  test("test_one_line_of_the_look_stands_it_before_the_first_result_on_a_narrow_screen_too", () => {
    expect(orderOf("narrow", true, "before")).toEqual(orderOf("wide", true, "before"));
    expect(before("refine", "results", orderOf("narrow", true, "before"))).toBe(true);
  });

  test("test_the_answer_comes_before_the_map_and_the_rest_of_the_results_after_it_on_every_screen", () => {
    for (const screen of EVERY) {
      for (const refines of ["after", "before"] as const) {
        const order = orderOf(screen, true, refines);
        expect(order[0]).toBe("form");
        expect(before("results", "tools", order)).toBe(true);
        expect(before("tools", "map", order)).toBe(true);
        expect(order.at(-1)).toBe("rest");
      }
    }
  });

  test("test_no_part_is_in_the_page_twice_and_none_is_left_out", () => {
    for (const screen of EVERY) {
      for (const open of [true, false]) {
        const order = orderOf(screen, open, "after");
        expect(new Set(order).size).toBe(order.length);
        expect([...order].sort()).toEqual(
          (open ? ["form", "map", "refine", "rest", "results", "tools"] : ["form", "map", "refine", "unscripted"]).sort(),
        );
      }
    }
  });
});

describe("what the style sheet says of the screen", () => {
  test("test_it_is_one_of_three_words_and_where_nothing_is_said_the_screen_is_a_wide_one", () => {
    expect(SCREENS).toEqual(["narrow", "middle", "wide"]);
    expect(screenSaidBy(" narrow")).toBe("narrow");
    expect(screenSaidBy("middle ")).toBe("middle");
    expect(screenSaidBy("wide")).toBe("wide");
    // A browser that lays nothing out reads no sheet, as the browser of a test.
    expect(screenSaidBy("")).toBe("wide");
    expect(screenSaidBy("anything else")).toBe("wide");
  });
});
