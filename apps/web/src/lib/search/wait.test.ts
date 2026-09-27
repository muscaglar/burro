import { readFileSync } from "node:fs";
import path from "node:path";

import { rulesOf } from "../../../test/support/css";
import { leastWait, millisecondsOf, ROUND, roundNow, ROUNDS } from "./wait";

const TOKENS = rulesOf(readFileSync(path.resolve(__dirname, "..", "..", "styles", "tokens.css"), "utf8"));
/** How long the look says a round of his hop is, where movement is welcome. */
const WELCOME = "1250ms";

/** A browser whose style sheet says how long a round of his hop is, as the sheet of the look does. */
function aRoundOf(length: string): () => void {
  const sheet = document.createElement("style");
  sheet.textContent = `:root { ${ROUND}: ${length}; }`;
  document.head.append(sheet);
  return () => sheet.remove();
}

describe("how long a first search waits", () => {
  test("test_one_number_says_how_many_rounds_and_it_is_three_times_down_his_hole_and_up_again", () => {
    // The founder asked for a few seconds, and then for it to "last a tad longer".
    expect(ROUNDS).toBe(3);
    const taken = aRoundOf(WELCOME);
    try {
      expect(roundNow()).toBe(1250);
      expect(leastWait()).toBe(3750);
    } finally {
      taken();
    }
  });

  test("test_the_wait_is_so_many_rounds_of_his_hop_whatever_the_look_says_a_round_is", () => {
    // How many rounds is one number and how long a round is another, and the two cannot
    // part: he is seen to go down and come up a whole number of times, and is down his hole
    // as the answer takes his place.
    for (const [said, length] of [
      ["1000ms", 1000],
      ["1250ms", 1250],
      ["1.5s", 1500],
      ["40ms", 40],
    ] as const) {
      const taken = aRoundOf(said);
      try {
        expect([said, leastWait()]).toEqual([said, ROUNDS * length]);
      } finally {
        taken();
      }
    }
  });

  test("test_a_first_search_waits_between_three_and_a_half_seconds_and_four", () => {
    // What was decided for the founder: three rounds where there were two, each a little
    // slower, about three and a half seconds in all. It was two seconds.
    const wait = ROUNDS * millisecondsOf(WELCOME);

    expect(wait).toBeGreaterThanOrEqual(3500);
    expect(wait).toBeLessThanOrEqual(4000);
  });

  test("test_a_round_is_as_long_as_the_look_says_his_hop_is_and_the_wait_names_no_length_of_its_own", () => {
    // The token that moves him is the token that is waited by: one line stills both.
    const said = TOKENS.filter((rule) => rule.sets.has(ROUND)).map((rule) => [rule.under, rule.selector, rule.sets.get(ROUND)]);

    expect(said).toEqual([
      [null, ":root", "0ms"],
      ["@media (prefers-reduced-motion: no-preference)", ":root", WELCOME],
    ]);
    const source = readFileSync(path.join(__dirname, "wait.ts"), "utf8");
    expect(source.match(/^export const \w+ = \d+;$/gm)).toEqual(["export const ROUNDS = 3;"]);
  });

  test("test_where_less_movement_is_asked_for_nothing_is_waited_for", () => {
    // The look says a round is nought there: there is nothing to watch.
    const still = aRoundOf("0ms");
    try {
      expect(leastWait()).toBe(0);
    } finally {
      still();
    }
  });

  test("test_no_test_of_the_website_waits_since_a_test_lays_no_style_sheet", () => {
    expect(getComputedStyle(document.documentElement).getPropertyValue(ROUND)).toBe("");
    expect(roundNow()).toBe(0);
    expect(leastWait()).toBe(0);
  });

  test.each([
    ["1000ms", 1000],
    [" 1000ms ", 1000],
    ["250ms", 250],
    ["1s", 1000],
    ["1.5s", 1500],
    [".5s", 500],
    ["0ms", 0],
    ["0s", 0],
  ])("test_a_length_of_time_is_read_as_a_style_sheet_writes_one: %s", (said, length) => {
    expect(millisecondsOf(said)).toBe(length);
  });

  test.each(["", "0", "1000", "fast", "calc(1s * 2)", "-1s", "1e3ms", "var(--motion-slow)", "1000 ms"])(
    "test_what_is_no_length_of_time_is_waited_for_not_at_all: %s",
    (said) => {
      expect(millisecondsOf(said)).toBe(0);
    },
  );
});
