import { readFileSync } from "node:fs";
import path from "node:path";

import { render } from "@testing-library/react";

import { faultsIn } from "../../../test/support/axe";
import { rulesOf, weightOf, heavier } from "../../../test/support/css";
import { Skeleton } from "./Skeleton";

const RULES = rulesOf(readFileSync(path.join(__dirname, "Skeleton.module.css"), "utf8"));
const BASE = rulesOf(readFileSync(path.join(__dirname, "..", "..", "styles", "base.css"), "utf8"));
const setsOf = (selector: string) =>
  new Map(RULES.filter((rule) => rule.selector === selector && rule.under === null).flatMap((rule) => [...rule.sets]));

describe("what holds the place of what is coming", () => {
  test("test_it_says_nothing_to_a_screen_reader_and_holds_nothing_that_is_read_or_pressed", () => {
    const { container } = render(
      <>
        <Skeleton />
        <Skeleton lines={3} />
        <Skeleton shape="card" lines={4} />
        <Skeleton shape="chip" />
      </>,
    );

    for (const one of container.children) expect(one).toHaveAttribute("aria-hidden", "true");
    expect(container.textContent).toBe("");
    expect([...container.querySelectorAll("a, button, input, [tabindex]")]).toEqual([]);
  });

  test("test_it_holds_as_many_lines_as_it_is_told_and_one_where_it_is_told_nothing", () => {
    const { container } = render(
      <>
        <Skeleton />
        <Skeleton lines={3} />
        <Skeleton shape="card" lines={4} />
      </>,
    );

    expect([...container.children].map((one) => one.querySelectorAll(".skeleton").length)).toEqual([1, 3, 4]);
  });

  test("test_it_is_still", () => {
    // It does not shimmer, and nothing of it moves: a person who waits is told so in words.
    const moving = RULES.filter((rule) => [...rule.sets.keys()].some((property) => /^(animation|transition|transform)/.test(property)));

    expect(moving.map((rule) => rule.selector)).toEqual([]);
  });

  test("test_a_line_is_one_whole_bar_in_the_colour_of_a_chip_at_rest_one_line_of_text_high", () => {
    const line = setsOf(".line:global(.skeleton)");

    // Seen in a browser: a row of dashes of sand held the place of a reason, and read as a
    // dashed line, which a person who walked the website did not understand. What holds a
    // place is drawn whole: one bar of sand, as long as the line it holds the place of.
    expect(line.get("background")).toBe("var(--sand)");
    // It is as high as a line of text, whatever the size of the text: it has no height in pixels.
    expect(line.get("height")).toBe("calc(var(--leading-text) * 1em)");
    // The bar is as high as the letters of a line, with the room of a line round it: so two
    // lines that are waited for are two bars, and never one block.
    expect([line.get("background-clip"), line.get("padding-block")]).toEqual(["content-box", "calc(var(--px) * 2)"]);
    expect(line.has("width")).toBe(false);
  });

  test("test_nothing_that_holds_a_place_is_drawn_in_pieces", () => {
    // No ground is laid in strokes with room between them, and none is laid again and again:
    // that is a dashed line by another name, and no search for the word finds it.
    const inPieces = RULES.filter((rule) =>
      [...rule.sets].some(
        ([property, value]) =>
          (/^background/.test(property) && /gradient|url\(|\b(space|round|repeat|repeat-x|repeat-y)\b/.test(value)) ||
          /\b(dashed|dotted)\b/.test(value),
      ),
    );

    expect(RULES.length).toBeGreaterThan(3);
    expect(inPieces.map((rule) => rule.selector)).toEqual([]);
  });

  test("test_its_own_ground_is_drawn_whichever_of_the_two_style_sheets_is_read_last", () => {
    // Every skeleton is given a flat ground by the base. A rule of this sheet that weighs the
    // same is the one drawn only if it is read last, and the order is not the website's to set.
    const given = BASE.filter((rule) => rule.selector === ".skeleton").map((rule) => weightOf(rule.selector));
    const own = RULES.filter((rule) => rule.sets.has("background") && /skeleton/.test(rule.selector));

    expect(given).toHaveLength(1);
    expect(own.map((rule) => rule.selector).sort()).toEqual([".chip:global(.skeleton)", ".line:global(.skeleton)"]);
    for (const rule of own) expect([rule.selector, heavier(weightOf(rule.selector), given[0] ?? [0, 0, 0])]).toEqual([rule.selector, true]);
  });

  test("test_the_place_of_a_card_brings_the_cream_it_stands_on_inside_a_rule_of_ink", () => {
    const card = setsOf(".card");

    expect([card.get("background"), card.get("border")]).toEqual(["var(--bg)", "var(--edge) solid var(--border)"]);
    // It is plain and flat: a card that is not there throws no shadow.
    expect(RULES.filter((rule) => rule.sets.has("box-shadow") || rule.sets.has("border-image"))).toEqual([]);
  });

  test("test_it_has_no_accessibility_fault", async () => {
    const { container } = render(
      <>
        <Skeleton lines={2} />
        <Skeleton shape="card" lines={4} />
        <Skeleton shape="chip" />
      </>,
    );

    expect(await faultsIn(container)).toEqual([]);
  });
});
