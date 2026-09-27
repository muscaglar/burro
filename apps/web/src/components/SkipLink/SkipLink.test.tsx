import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { SITE } from "@/content/site";

import { faultsIn } from "../../../test/support/axe";
import { rulesOf } from "../../../test/support/css";
import { isDrawn } from "../kit/drawings";
import { SkipLink } from "./SkipLink";

const RULES = rulesOf(readFileSync(path.join(__dirname, "SkipLink.module.css"), "utf8"));
const FORCED = /forced-colors:\s*active/;
const atRest = new Map(RULES.filter((rule) => rule.selector === ".skip" && rule.under === null).flatMap((rule) => [...rule.sets]));

describe("the way to skip to the page itself", () => {
  test("test_it_is_a_link_of_the_browsers_own_to_the_page_itself_and_is_the_first_thing_a_keyboard_reaches", async () => {
    render(
      <>
        <SkipLink />
        <main id="main" tabIndex={-1}>
          <button type="button">What the page holds</button>
        </main>
      </>,
    );

    await userEvent.tab();

    const skip = screen.getByRole("link", { name: SITE.skipToContent });
    expect(skip).toHaveFocus();
    expect(skip).toHaveAttribute("href", "#main");
    expect(skip).toHaveClass("target");
    // A link the website follows for itself is marked so, and leaves the focus where it was.
    expect(skip).not.toHaveAttribute("data-prefetch");
  });

  test("test_it_may_lead_to_another_part_of_a_page_and_say_other_words", () => {
    render(<SkipLink href="#results">Skip to the results</SkipLink>);

    expect(screen.getByRole("link", { name: "Skip to the results" })).toHaveAttribute("href", "#results");
  });

  test("test_it_is_off_the_screen_until_a_keyboard_reaches_it_and_is_then_set_down_where_it_is_laid_out", () => {
    const reached = RULES.filter((rule) => /^\.skip:focus(-visible)?$/.test(rule.selector));

    expect([atRest.get("position"), atRest.get("transform")]).toEqual(["absolute", "translateY(-200%)"]);
    expect(reached.map((rule) => [rule.selector, [...rule.sets]])).toEqual([
      [".skip:focus", [["transform", "none"]]],
      [".skip:focus-visible", [["transform", "none"]]],
    ]);
    // It is hidden by where it lies, and never by being taken out of what is read.
    expect(RULES.filter((rule) => rule.sets.has("display") && rule.sets.get("display") === "none")).toEqual([]);
    expect(RULES.filter((rule) => rule.sets.has("visibility"))).toEqual([]);
  });

  test("test_it_is_drawn_as_the_button_that_matters_most_with_its_words_in_the_face_of_names", () => {
    render(<SkipLink />);
    const skip = screen.getByRole("link", { name: SITE.skipToContent });
    const drawn = ["--art", "--art-down"].map((token) => /\/art\/([a-z0-9-]+)\.png/.exec(skip.style.getPropertyValue(token))?.[1] ?? "");

    expect(drawn).toEqual(["ui-button-go", "ui-button-go-down"]);
    expect(drawn.every(isDrawn)).toBe(true);
    expect(atRest.get("border-image")).toBe(
      "var(--art) 3 3 4 3 fill / calc(var(--px) * 3) calc(var(--px) * 3) calc(var(--px) * 4) repeat",
    );
    expect(atRest.get("image-rendering")).toBe("pixelated");
    // Under the picture: an edge of ink, and the ground of the button, which its words are read on.
    expect([atRest.get("border-color"), atRest.get("background"), atRest.get("color")]).toEqual([
      "var(--ink)",
      "var(--accent) padding-box",
      "var(--on-accent)",
    ]);
    expect([atRest.get("font"), atRest.get("font-synthesis")]).toEqual(["400 var(--name-1) / 1 var(--font-name)", "none"]);
  });

  test("test_a_press_changes_its_picture_and_moves_nothing", () => {
    const pressed = RULES.filter((rule) => /:active\b/.test(rule.selector) && !FORCED.test(rule.under ?? ""));

    expect(pressed.map((rule) => [rule.selector, [...rule.sets]])).toEqual([[".skip:active", [["border-image-source", "var(--art-down)"]]]]);
  });

  test("test_where_the_system_draws_in_its_own_colours_no_picture_is_laid_over_them", () => {
    const forced = RULES.filter((rule) => FORCED.test(rule.under ?? ""));

    expect(forced.map((rule) => [rule.selector, rule.sets.get("border-image-source")])).toEqual([
      [".skip", "none"],
      [".skip:active", "none"],
    ]);
  });

  test("test_it_has_no_accessibility_fault", async () => {
    const { container } = render(
      <>
        <SkipLink />
        <main id="main" tabIndex={-1}>
          <h1>A page</h1>
        </main>
      </>,
    );

    expect(await faultsIn(container)).toEqual([]);
  });
});
