import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen } from "@testing-library/react";

import { sizeOf } from "@/components/kit/drawings";

import { faultsIn } from "../../../test/support/axe";
import { rulesOf } from "../../../test/support/css";
import { STEP_OF_THE_LINES_HELD, Track } from "./Track";

const read = (file: string) => readFileSync(file, "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
const CSS = read(path.join(__dirname, "Track.module.css"));
const STYLES = rulesOf(CSS);
/** The part Peg of the kit, which draws the same band with its words beside it. */
const OF_THE_KIT = rulesOf(read(path.join(__dirname, "..", "kit", "Peg", "Peg.module.css")));
const atRest = (rules: typeof STYLES, selector: string) =>
  new Map(
    rules
      .filter((rule) => rule.selector === selector && rule.under === null)
      .flatMap((rule) => [...rule.sets].map(([property, value]): [string, string] => [property, value.replace(/\s+/g, " ")])),
  );
const setsOf = (selector: string) => atRest(STYLES, selector);
const filled = (container: HTMLElement) =>
  [...container.querySelectorAll("[data-on]")].map((cell) => cell.getAttribute("data-on") === "true");
/** Where the mark begins, in steps from the low end, and how many it lies across. */
const markOf = (container: HTMLElement) => {
  const track = container.firstElementChild as HTMLElement;
  return [track.style.getPropertyValue("--at"), track.style.getPropertyValue("--over")];
};
const at = (band: number) => ({ band, spread_low: band, spread_high: band });

describe("the line an area is marked on", () => {
  test.each([1, 2, 3, 4, 5])("test_the_cell_of_the_band_is_filled_and_no_other: band %i", (band) => {
    const { container } = render(<Track placed={at(band)} says={`band ${band} of 5`} />);

    expect(filled(container)).toEqual([1, 2, 3, 4, 5].map((cell) => cell === band));
  });

  test.each([1, 2, 3, 4, 5])("test_it_is_five_steps_with_a_peg_on_one_and_never_a_bar_that_fills: band %i", (band) => {
    const { container } = render(<Track placed={at(band)} />);

    // One step is marked, which is the step of its band: and not every step as far as that one.
    expect(container.querySelectorAll("[data-on]")).toHaveLength(5);
    expect(container.querySelectorAll("[data-on='true']")).toHaveLength(1);
    expect(markOf(container)).toEqual([String(band - 1), "1"]);
    expect(container.querySelectorAll(".peg")).toHaveLength(1);
    expect(container.querySelector(".rail")).toBeNull();
  });

  test("test_the_peg_is_the_drawing_of_a_peg_shown_at_its_own_size_and_never_stretched", () => {
    const { container } = render(<Track placed={at(2)} />);
    const track = container.firstElementChild as HTMLElement;
    const { width, height } = sizeOf("ui-peg");

    expect(track.style.getPropertyValue("--art")).toBe('url("/art/ui-peg.png")');
    expect([track.style.getPropertyValue("--w"), track.style.getPropertyValue("--h")]).toEqual([String(width), String(height)]);
    expect(setsOf(".peg").get("background")).toBe(
      "var(--art) 0 0 / calc(var(--px) * var(--w)) calc(var(--px) * var(--h)) no-repeat",
    );
    expect(setsOf(".peg").get("image-rendering")).toBe("pixelated");
    // It stands in the middle of its step, whatever the width of a step.
    expect(setsOf(".peg").get("inset-inline-start")).toBe(
      "calc( var(--px) * (1 + (var(--step) + 1) * var(--at) + (var(--step) - var(--w)) / 2) )",
    );
    for (const step of [9, 7]) expect((step - width) % 2).toBe(0);
  });

  test("test_it_is_drawn_as_the_part_of_the_kit_draws_a_band_point_for_point", () => {
    // The page of an area and a comparison draw this line, and a result may draw the part
    // of the kit: a band is one picture wherever it stands.
    const [track, steps] = [setsOf(".track"), atRest(OF_THE_KIT, ".steps")];

    // A step is nine art pixels wide where whatever holds the line says no other width.
    expect([track.get("--step"), track.get("--rise"), track.get("--room")]).toEqual([
      "var(--track-step, 9)",
      "6",
      "calc(var(--h) - 3)",
    ]);
    expect(steps.get("grid-template-columns")).toBe("repeat(5, calc(var(--px) * 9))");
    expect(track.get("grid-template-columns")).toBe("repeat(5, calc(var(--px) * var(--step)))");
    expect(steps.get("padding")).toBe("calc(var(--px) * (var(--h) - 3)) var(--px) 0");
    expect(track.get("padding")).toBe("calc(var(--px) * var(--room)) var(--px) 0");
    expect(track.get("gap")).toBe(steps.get("gap"));
    expect(atRest(OF_THE_KIT, ".step").get("height")).toBe("calc(var(--px) * 6)");
    expect(setsOf(".cell").get("height")).toBe("calc(var(--px) * var(--rise))");
    for (const property of ["border", "background"]) {
      expect(setsOf(".cell").get(property)).toBe(atRest(OF_THE_KIT, ".step").get(property));
      expect(setsOf('.cell[data-on="true"]').get(property)).toBe(atRest(OF_THE_KIT, '.step[data-here="true"]').get(property));
    }
    expect(setsOf('.track[data-part="true"] .cell[data-on="true"]').get("background")).toBe(
      atRest(OF_THE_KIT, '.peg[data-part="true"] .step[data-here="true"]').get("background"),
    );
    expect(setsOf('.track[data-range="true"] .cell[data-on="true"]').get("background")).toBe(
      atRest(OF_THE_KIT, '.peg[data-mixed="true"] .step[data-here="true"]').get("background"),
    );
    // An area that cannot be placed is the one thing the two draw apart: the part of the kit
    // draws its steps in dashes still, and this line draws none.
    for (const property of ["height", "border", "border-block-end"]) {
      expect(setsOf(".rail").get(property)).toBe(atRest(OF_THE_KIT, ".rail").get(property));
    }
  });

  test("test_whatever_holds_lines_that_stand_one_under_the_next_may_say_how_wide_a_step_of_them_is", () => {
    // A result as narrow as a phone draws narrower steps in every line of it, so that each
    // line is as wide as the next and the steps of one stand under the steps of another.
    // It says so to the lines it holds, and a line that is told nothing is as it was.
    const said = STYLES.filter((rule) => rule.sets.has("--step"));

    expect(said.map((rule) => [rule.under, rule.selector, rule.sets.get("--step")])).toEqual([
      [null, ".track", "var(--track-step, 9)"],
      [null, '.track[data-small="true"]', "5"],
      ["@media (max-width: 40rem)", '.track[data-narrow="true"]', "7"],
    ]);
    // Small steps, and the narrow steps a line asks for itself, are what they were whatever is
    // said. The line says nothing of it itself: it is whatever holds the line that does.
    expect(STEP_OF_THE_LINES_HELD).toBe("--track-step");
    expect(STYLES.filter((rule) => rule.sets.has(STEP_OF_THE_LINES_HELD))).toEqual([]);
    const holder = rulesOf(readFileSync(path.join(__dirname, "..", "Strip", "Strip.module.css"), "utf8"));
    expect(holder.filter((rule) => rule.sets.has(STEP_OF_THE_LINES_HELD)).map((rule) => rule.sets.get(STEP_OF_THE_LINES_HELD))).toEqual(["7"]);
    // The peg of the look is as wide as the narrowest step a line can be told to draw it on.
    const { width } = sizeOf("ui-peg");
    for (const step of [9, 7]) expect([step, step >= width, (step - width) % 2]).toEqual([step, true, 0]);
  });

  test("test_the_room_of_the_peg_is_there_whether_a_peg_is_or_not", () => {
    // A line with a peg and a line with none are of one height: nothing moves as one gives way to the other.
    expect(setsOf(".peg").get("position")).toBe("absolute");
    expect(setsOf(".rail").get("position")).toBe("absolute");
    const states = STYLES.filter((rule) => /\.track\[data-(placed|range|part)/.test(rule.selector) && rule.under === null);
    expect(states.length).toBeGreaterThan(1);
    expect([...new Set(states.flatMap((rule) => [...rule.sets.keys()]))].sort()).toEqual(["background"]);
  });

  test("test_a_mixed_area_fills_the_cells_it_spans_and_is_never_a_point_in_the_middle", () => {
    const { container } = render(<Track placed={{ band: 3, spread_low: 2, spread_high: 4 }} says="varies" />);

    expect(filled(container)).toEqual([false, true, true, true, false]);
    expect(container.querySelector("[data-range='true']")).not.toBeNull();
    // A rail joins the steps it spans, from the first to the last, and there is no peg at all.
    expect(container.querySelector(".peg")).toBeNull();
    expect(container.querySelectorAll(".rail")).toHaveLength(1);
    expect(markOf(container)).toEqual(["1", "3"]);
    expect(setsOf('.track[data-range="true"] .cell[data-on="true"]').get("background")).toBe("var(--sand)");
  });

  test("test_an_area_that_spans_two_bands_is_drawn_in_the_one_it_sits_in", () => {
    const { container } = render(<Track placed={{ band: 3, spread_low: 3, spread_high: 4 }} says="band 3 of 5" />);

    expect(filled(container)).toEqual([false, false, true, false, false]);
    expect(container.querySelector(".rail")).toBeNull();
  });

  test("test_a_band_that_rests_on_part_of_its_recipe_has_its_step_chequered_and_its_peg_as_any_other", () => {
    const { container } = render(<Track placed={at(2)} part />);

    expect(container.firstElementChild).toHaveAttribute("data-part", "true");
    expect(filled(container)).toEqual([false, true, false, false, false]);
    expect(container.querySelectorAll(".peg")).toHaveLength(1);
    expect(setsOf('.track[data-part="true"] .cell[data-on="true"]').get("background")).toBe(
      "repeating-conic-gradient(var(--ink) 0 25%, var(--page) 0 50%) 0 0 / calc(var(--px) * 4) calc(var(--px) * 4)",
    );
    // It is told nothing of the kind, and is drawn as any other.
    render(<Track placed={at(2)} />);
    expect(document.querySelectorAll("[data-part='false']")).toHaveLength(1);
  });

  test("test_an_area_that_cannot_be_placed_has_five_empty_steps_and_no_peg_never_the_middle_and_never_nought", () => {
    const { container } = render(<Track placed={null} says="Cannot be placed" />);

    expect(container.firstElementChild).toHaveAttribute("data-placed", "false");
    // Five steps, and no step is marked: not the middle one, and not the first.
    expect(container.firstElementChild?.children).toHaveLength(5);
    expect(container.querySelectorAll("[data-on]")).toHaveLength(0);
    expect(container.querySelector(".peg, .rail")).toBeNull();
    // Each step has the solid edge of any step, and holds nothing. It is told from a line
    // that places an area by having no step of ink and no peg, and by the words beside it.
    expect(STYLES.filter((rule) => /data-placed/.test(rule.selector)).map((rule) => rule.selector)).toEqual([]);
    expect(setsOf(".cell").get("border")).toBe("var(--px) solid var(--ink)");
    expect(screen.getByRole("img")).toHaveAccessibleName("Cannot be placed");
  });

  test("test_no_edge_of_the_line_is_drawn_in_dashes_or_in_dots_with_forced_colours_as_without", () => {
    // A person who walked the website did not know what a dashed edge was for. The steps of
    // an area that cannot be placed were in dashes, drawn in art pixels: the two sides of a
    // step and the ends of its top and its foot, over an edge that was taken away.
    expect(/dashed|dotted|repeating-linear-gradient/.test(CSS)).toBe(false);
    expect(STYLES.filter((rule) => /transparent/.test(rule.sets.get("border-color") ?? "")).map((rule) => rule.selector)).toEqual([]);
    expect(/--dash\b/.test(CSS)).toBe(false);
    // An edge is set by the step, by the rail of a mixed area, and by nothing else.
    expect(STYLES.filter((rule) => rule.under === null && [...rule.sets.keys()].some((property) => /^border/.test(property))).map((rule) => rule.selector)).toEqual([
      ".cell",
      ".rail",
      '.track[data-small="true"] .rail',
    ]);
  });

  test("test_in_a_list_of_many_small_things_the_step_has_a_cap_and_no_drawing_of_a_peg", () => {
    const { container } = render(<Track placed={at(4)} small />);
    const small = setsOf('.track[data-small="true"]');
    const cap = setsOf('.track[data-small="true"] .peg');

    expect(container.firstElementChild).toHaveAttribute("data-small", "true");
    expect(filled(container)).toEqual([false, false, false, true, false]);
    expect([small.get("--step"), small.get("--rise")]).toEqual(["5", "5"]);
    // The cap is over its step, as wide as the step, and is a mark of poppy: it is no word.
    expect(cap.get("background")).toBe("var(--poppy)");
    expect(cap.get("width")).toBe("calc(var(--px) * var(--step))");
    expect(cap.get("inset-inline-start")).toBe("calc(var(--px) * (1 + (var(--step) + 1) * var(--at)))");
  });

  test("test_alone_it_is_a_picture_that_says_in_words_what_it_shows", () => {
    render(<Track placed={at(4)} says="band 4 of 5, counted from one end to the other" />);

    expect(screen.getByRole("img")).toHaveAccessibleName("band 4 of 5, counted from one end to the other");
  });

  test("test_beside_the_words_that_say_the_same_it_is_kept_from_a_screen_reader", () => {
    const { container } = render(<Track placed={at(4)} />);

    // It would be heard twice. What it shows is never left to the picture alone.
    expect(screen.queryByRole("img")).toBeNull();
    expect(container.firstElementChild).toHaveAttribute("aria-hidden", "true");
  });

  test("test_the_cell_that_is_filled_differs_in_more_than_hue_and_nothing_is_drawn_see_through", () => {
    const on = STYLES.filter((rule) => rule.selector.trim() === '.cell[data-on="true"]' && rule.under === null);
    const off = STYLES.filter((rule) => rule.selector.trim() === ".cell" && rule.under === null);

    // Filled, a cell is the colour of the words. Empty, it is the colour that is read on, with an edge of ink.
    expect(on.map((rule) => rule.sets.get("background"))).toEqual(["var(--ink)"]);
    expect(off.map((rule) => rule.sets.get("background"))).toEqual(["var(--page)"]);
    expect(off.map((rule) => rule.sets.get("border"))).toEqual(["var(--px) solid var(--ink)"]);
    expect(STYLES.filter((rule) => rule.sets.has("opacity"))).toEqual([]);
  });

  test("test_a_narrow_line_has_narrower_steps_and_the_peg_still_stands_in_the_middle_of_one", () => {
    const narrow = STYLES.filter((rule) => rule.selector === '.track[data-narrow="true"]');

    expect(narrow.map((rule) => [rule.under, [...rule.sets]])).toEqual([["@media (max-width: 40rem)", [["--step", "7"]]]]);
  });

  test("test_the_line_has_no_accessibility_fault", async () => {
    const { container } = render(
      <p>
        <Track placed={at(2)} says="band 2 of 5" />
        <Track placed={{ band: 2, spread_low: 1, spread_high: 3 }} />
        <Track placed={at(2)} says="band 2 of 5, on part of its recipe" part />
        <Track placed={null} says="Cannot be placed" />
        <Track placed={at(5)} small />
      </p>,
    );

    expect(await faultsIn(container)).toEqual([]);
  });
});
