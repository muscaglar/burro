import { recordedAnswer } from "@/lib/api/recorded";

import { grouped, outOfHundred, readableDate } from "./format";

describe("how a date the API sent is written", () => {
  test("test_a_date_is_written_in_words", () => {
    expect(readableDate("2026-09-23")).toBe("23 September 2026");
    expect(readableDate("2026-09-23T00:00:00Z")).toBe("23 September 2026");
  });

  test("test_a_month_is_written_as_the_api_writes_one_in_a_sentence", () => {
    // The API's own sentence says "August 2026" of a cost whose month is 2026-08.
    const cost = recordedAnswer("get_area", "area/farrowmere").body.data.facts.find(
      (fact) => fact.kind === "cost",
    );

    expect(cost?.as_of).toBe("2026-08");
    expect(readableDate(cost?.as_of ?? "")).toBe(cost?.slots.as_of);
  });

  test("test_anything_else_is_shown_as_it_came", () => {
    for (const asItCame of ["2025", "2026-13", "", "soon", "soon to later", "one to two to three"]) {
      expect(readableDate(asItCame)).toBe(asItCame);
    }
  });

  test("test_a_period_is_written_the_same_way_at_both_its_ends", () => {
    // Seen in a browser: "2021 to 2026-04" beside "April 2026" and "31 March 2025", on one page.
    expect(readableDate("2021 to 2026-04")).toBe("2021 to April 2026");
    expect(readableDate("2024-10 to 2026-09")).toBe("October 2024 to September 2026");
    expect(readableDate("2025-03-31 to 2026-04")).toBe("31 March 2025 to April 2026");
  });

  test("test_a_weight_and_a_whole_number_are_written_for_a_person", () => {
    expect([0, 0.05, 0.5, 1].map(outOfHundred)).toEqual(["0", "5", "50", "100"]);
    expect(grouped(1700)).toBe("1,700");
    expect(grouped(450000)).toBe("450,000");
  });
});
