/** @jest-environment node */
/**
 * The map's own style sheet, held against the map library's. Found in a
 * browser, where no test could see it: the library puts its own class on the
 * map's element and sets `position: relative` on it. Loaded after the
 * website's, and weighing the same, it won. The element was then no longer
 * laid over its frame, had no height, and the map drew nothing.
 *
 * Which style sheet loads last is not the website's to decide: the library's
 * is fetched on demand. So wherever both say what an element is to be, the
 * website's rule must weigh more.
 */

import { readFileSync } from "node:fs";
import path from "node:path";

import { heavier, isFor, rulesOf, weightOf, type Rule, type Weight } from "../../../test/support/css";

const OURS = rulesOf(readFileSync(path.join(__dirname, "MapView.module.css"), "utf8"));
const THEIRS = rulesOf(
  readFileSync(path.resolve(__dirname, "../../../node_modules/maplibre-gl/dist/maplibre-gl.css"), "utf8"),
);

/**
 * The elements that carry a class of each: the website's, and the one the
 * library adds to the same element when the map starts.
 */
const SHARED = [
  { element: "the map", ours: "map", theirs: "maplibregl-map" },
  { element: "a pin", ours: "pin", theirs: "maplibregl-marker" },
] as const;

/** The sides that `inset` sets, so that it is held against a rule that sets one of them. */
const SIDES = ["top", "right", "bottom", "left"];
const propertiesOf = (rule: Rule) =>
  [...rule.sets.keys()].flatMap((property) => (property === "inset" ? ["inset", ...SIDES] : [property]));

/** Every property two sets of rules both set, with the heaviest rule of each that sets it. */
function contested(ours: readonly Rule[], theirs: readonly Rule[]) {
  const heaviest = (rules: readonly Rule[], property: string): Weight | null =>
    rules
      .filter((rule) => propertiesOf(rule).includes(property))
      .map((rule) => weightOf(rule.selector))
      .reduce<Weight | null>((best, weight) => (best === null || heavier(weight, best) ? weight : best), null);
  // The lightest of ours that sets it: every rule of ours must win, not only the heaviest.
  const lightest = (rules: readonly Rule[], property: string): Weight | null =>
    rules
      .filter((rule) => propertiesOf(rule).includes(property))
      .map((rule) => weightOf(rule.selector))
      .reduce<Weight | null>((least, weight) => (least === null || heavier(least, weight) ? weight : least), null);
  const properties = new Set(ours.flatMap(propertiesOf));
  return [...properties].flatMap((property) => {
    const [mine, other] = [lightest(ours, property), heaviest(theirs, property)];
    return mine === null || other === null ? [] : [{ property, ours: mine, theirs: other }];
  });
}

describe("how much a selector weighs", () => {
  test.each<[string, Weight]>([
    [".map", [0, 1, 0]],
    [".frame > .map", [0, 2, 0]],
    [".maplibregl-map", [0, 1, 0]],
    [".maplibregl-map:fullscreen", [0, 2, 0]],
    [".map :global(.maplibregl-canvas):focus-visible", [0, 3, 0]],
    [".pin:global(.target-min)", [0, 2, 0]],
    [".pin[aria-current=\"true\"]", [0, 2, 0]],
    ["button.pin::before", [0, 1, 2]],
    ["#map .pin", [1, 1, 0]],
    [":where(a.target, a.target-min)", [0, 0, 0]],
    [".control:not(.whole, #one)", [1, 1, 0]],
    ["li:nth-child(2n + 1) a", [0, 1, 2]],
  ])("test_the_weight_of_a_selector_is_worked_out_as_a_browser_does: %s", (selector, weight) => {
    expect(weightOf(selector)).toEqual(weight);
  });

  test("test_a_rule_is_read_with_everything_it_sets_whatever_it_is_under", () => {
    const rules = rulesOf(`
      /* .hidden { position: fixed } */
      .one, .two > .three { position: absolute; inset: 0 }
      @media (max-width: 40rem) { .four { display: block; } }
    `);

    expect(rules.map(({ selector, under }) => [selector, under])).toEqual([
      [".one", null],
      [".two > .three", null],
      [".four", "@media (max-width: 40rem)"],
    ]);
    expect([...(rules[1]?.sets ?? [])]).toEqual([
      ["position", "absolute"],
      ["inset", "0"],
    ]);
  });
});

describe("the map's style sheet against the library's", () => {
  test("test_the_library_still_says_where_the_map_element_is_to_be", () => {
    // If the library stops setting it, this guard has nothing to guard and should be looked at again.
    const theirs = THEIRS.filter((rule) => isFor(rule.selector, "maplibregl-map"));

    expect(theirs.find((rule) => rule.sets.has("position"))?.sets.get("position")).toBe("relative");
  });

  test("test_the_map_element_is_laid_over_its_frame", () => {
    const ours = OURS.filter((rule) => isFor(rule.selector, "map") && rule.under === null);
    const sets = new Map(ours.flatMap((rule) => [...rule.sets]));

    // Laid over the frame, it takes the frame's size. Left in the flow, it has no height at all.
    expect(sets.get("position")).toBe("absolute");
    expect(sets.get("inset")).toBe("0");
  });

  test.each(SHARED.map((shared) => [shared.element, shared] as const))(
    "test_no_rule_of_the_website_can_be_outranked_by_the_librarys: %s",
    (_, { ours, theirs }) => {
      const mine = OURS.filter((rule) => isFor(rule.selector, ours));
      const other = THEIRS.filter((rule) => isFor(rule.selector, theirs));

      expect(mine.length).toBeGreaterThan(0);
      expect(other.length).toBeGreaterThan(0);
      // Where they weigh the same, the one loaded last wins, and that is the library's.
      const lost = contested(mine, other).filter((both) => !heavier(both.ours, both.theirs));

      expect(lost).toEqual([]);
    },
  );

  test("test_the_buttons_that_move_the_map_are_not_laid_over_it", () => {
    // Seen in a browser: a button laid over the top right of the map covered an area.
    const laidOver = OURS.filter(
      (rule) =>
        (isFor(rule.selector, "controls") || isFor(rule.selector, "control") || isFor(rule.selector, "whole")) &&
        /^(absolute|fixed|sticky)$/.test(rule.sets.get("position") ?? ""),
    );

    expect(OURS.some((rule) => isFor(rule.selector, "controls"))).toBe(true);
    expect(laidOver.map((rule) => rule.selector)).toEqual([]);
  });

  test("test_the_guard_fails_on_the_rule_as_it_was_when_the_map_drew_nothing", () => {
    const asItWas = rulesOf(".map { position: absolute; inset: 0; }");
    const theirs = THEIRS.filter((rule) => isFor(rule.selector, "maplibregl-map"));

    expect(contested(asItWas, theirs).filter((both) => !heavier(both.ours, both.theirs))).toEqual([
      { property: "position", ours: [0, 1, 0], theirs: [0, 1, 0] },
    ]);
  });
});
