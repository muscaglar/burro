/**
 * The one place of the website that leads to another page without a link being pressed
 * leads to a page of a closed list, by its name, and is handed no address.
 */

import { renderHook } from "@testing-library/react";

import { addressOf, EVERY_WAY, useGo } from "./go";

const pushed: unknown[][] = [];
jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: (...to: unknown[]) => pushed.push(to),
    replace: () => {
      throw new Error("It leads on, and replaces nothing.");
    },
  }),
}));

beforeEach(() => {
  pushed.length = 0;
});

describe("where a press may lead once its answer is in", () => {
  test("test_it_leads_to_a_page_of_the_list_and_to_no_other", () => {
    expect(EVERY_WAY).toEqual(["search", "sent"]);
    expect(EVERY_WAY.map(addressOf)).toEqual(["/", "/sign-in/sent"]);
  });

  test("test_every_address_is_fixed_and_holds_nothing_after_a_question_mark_or_a_hash", () => {
    for (const way of EVERY_WAY) expect(addressOf(way)).toMatch(/^\/([a-z]+(-[a-z]+)*(\/[a-z]+(-[a-z]+)*)*)?$/);
  });

  test("test_it_goes_by_the_router_which_keeps_the_page_in_memory", () => {
    const { result } = renderHook(() => useGo());

    result.current("sent");
    result.current("search");

    expect(pushed).toEqual([["/sign-in/sent"], ["/"]]);
  });

  test("test_what_is_no_way_of_the_list_leads_nowhere", () => {
    const { result } = renderHook(() => useGo());

    expect(() => result.current("https://elsewhere.example/" as never)).toThrow();
    expect(pushed).toEqual([]);
  });
});
