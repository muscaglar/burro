import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen } from "@testing-library/react";

import { faultsIn } from "../../../test/support/axe";
import { rulesOf } from "../../../test/support/css";
import { Disclosure } from "./Disclosure";
import { Folded } from "./Folded";
import { BAR_AT_REST } from "./look";
import { drawnAs, foldOf, Summary, theArrow } from "./Summary";

const RULES = rulesOf(readFileSync(path.join(__dirname, "Disclosure.module.css"), "utf8"));
const DRAWN = RULES.filter((rule) => !/forced-colors/.test(rule.under ?? ""));
const setsOf = (selector: string) => new Map(DRAWN.filter((rule) => rule.selector === selector && rule.under === null).flatMap((rule) => [...rule.sets]));

const bar = () => document.querySelector("summary") as HTMLElement;

describe("the bar of a fold that is the browser's own", () => {
  test("test_it_is_the_bar_a_button_that_folds_is_by_the_same_classes_so_that_one_sheet_draws_both", () => {
    // Walked: a thing that opens was drawn four ways. Where a page uses the browser's own
    // element to fold, so that it folds with scripts off, it keeps that element and takes the look.
    render(
      <>
        <Disclosure label="Budget and home" size="bar">
          a
        </Disclosure>
        <Disclosure label="Table of all areas">b</Disclosure>
        <Disclosure label="Source" size="small">
          c
        </Disclosure>
      </>,
    );
    const buttons = ["Budget and home", "Table of all areas", "Source"].map((name) => screen.getByRole("button", { name }).className);

    expect([drawnAs("stacked"), drawnAs("alone"), drawnAs("small")]).toEqual(buttons);
    expect(drawnAs("boxed")).toBe("button bar boxed target");
  });

  test("test_its_arrow_is_first_in_it_and_says_nothing_and_what_is_read_follows", () => {
    render(
      <Folded bar={<Summary label="How Burro works this out" of="Leafy" stands="alone" />} stands="alone">
        words
      </Folded>,
    );

    expect(bar().tagName).toBe("SUMMARY");
    expect([...bar().children].map((part) => [part.tagName, part.className])).toEqual([
      ["SPAN", "mark"],
      ["SPAN", "told"],
    ]);
    expect(bar().firstElementChild).toHaveAttribute("aria-hidden", "true");
    expect(bar().firstElementChild).toBeEmptyDOMElement();
    // It is laid out at the far end, in its cell, by the sheet: the founder asked for it there.
    expect(bar()).toHaveAttribute("data-arrow", "end");
    expect(setsOf(".bar .mark").get("order")).toBe("1");
    // What it is said of is said after the words, to whoever hears the page, and is not drawn.
    expect(bar().textContent).toBe("How Burro works this out: Leafy");
    expect(bar().querySelector(".visually-hidden")?.textContent).toBe(": Leafy");
  });

  test.each([2, 3, 4] as const)("test_what_it_says_may_be_the_heading_of_what_it_opens_and_stands_directly_in_the_bar: %s", (rank) => {
    render(
      <Folded bar={<Summary label="What homes cost" heading={rank} />}>
        <p>What it holds.</p>
      </Folded>,
    );
    const heading = screen.getByRole("heading", { level: rank, name: "What homes cost" });

    // The part is found by its heading, as any part of a page is, and the heading is in what takes the press.
    expect(heading.parentElement).toBe(bar());
    expect(heading).toHaveClass("told");
    expect([...bar().children].map((part) => part.tagName)).toEqual(["SPAN", `H${rank}`]);
  });

  test("test_a_heading_is_never_set_in_the_face_of_names_under_30_and_a_small_one_is_set_heavy_in_the_reading_face", () => {
    // At 20 pixels the face of names reads as small as a sentence at 13.
    expect([setsOf("summary.bar > .told").get("font"), setsOf("summary.bar > .told").get("font-synthesis")]).toEqual([
      "400 var(--name-1) / 1 var(--font-name)",
      "none",
    ]);
    expect([setsOf("summary.bar > h2.told").get("font"), setsOf("summary.bar > h2.told").get("font-synthesis")]).toEqual([
      "400 var(--name-2) / 1 var(--font-name)",
      "none",
    ]);
    for (const small of ["summary.bar > h3.told", "summary.bar > h4.told", 'summary.bar > h3.told[data-reads="true"]', 'summary.bar > h4.told[data-reads="true"]']) {
      expect([small, setsOf(small).get("font")]).toEqual([small, "700 var(--size-h3) / 1.2 var(--font-say)"]);
    }
    // Words that hold a figure are read, as on any bar.
    expect(setsOf('summary.bar > .told[data-reads="true"]').get("font")).toBe("700 var(--size-body) / 1.25 var(--font-say)");
  });

  test("test_words_that_hold_a_figure_say_so_and_so_does_a_label_that_is_more_than_words", () => {
    const { unmount } = render(<Folded bar={<Summary label="Who lived here in 2021" heading={2} />}>a</Folded>);
    expect(bar().querySelector(".told")).toHaveAttribute("data-reads", "true");
    unmount();
    render(<Folded bar={<Summary label="Sources on this page" heading={2} />}>a</Folded>);
    expect(bar().querySelector(".told")).toHaveAttribute("data-reads", "false");
  });

  test("test_it_is_handed_the_arrow_by_name_unless_what_holds_the_fold_hands_it_to_all_it_holds", () => {
    const { unmount } = render(<Folded bar={<Summary label="By itself" />}>a</Folded>);
    expect(bar().style.getPropertyValue("--arrow")).toBe('url("/art/ui-arrow.png")');
    expect([bar().style.getPropertyValue("--arrow-w"), bar().style.getPropertyValue("--arrow-h")]).toEqual(["10", "8"]);
    expect(theArrow()).toEqual({ "--arrow": 'url("/art/ui-arrow.png")', "--arrow-w": 10, "--arrow-h": 8 });
    unmount();

    // Among the figures of the census nothing bears a style of its own: the page hands the arrow.
    render(<Folded bar={<Summary label="Handed" handed />}>a</Folded>);
    expect(bar()).not.toHaveAttribute("style");
  });

  test("test_a_bar_on_the_grass_is_a_box_of_the_kit_and_any_other_is_none", () => {
    const { unmount } = render(
      <Folded stands="boxed" bar={<Summary label="The methods in full" stands="boxed" />}>
        a
      </Folded>,
    );
    expect(bar()).toHaveAttribute("data-kind", "box");
    expect(bar()).toHaveClass("button", "bar", "boxed", "target");
    // It is drawn as the bar of every fold on the face it says its words on, inside the rule of the box.
    expect([setsOf(".boxed > .told").get("background-color"), setsOf(".fold[open] > .boxed > .told").get("background-color")]).toEqual([
      "var(--page)",
      "var(--chosen)",
    ]);
    unmount();

    for (const stands of ["stacked", "alone", "small"] as const) {
      const shown = render(
        <Folded stands={stands} bar={<Summary label="Any other" stands={stands} />}>
          a
        </Folded>,
      );
      expect([stands, bar().hasAttribute("data-kind")]).toEqual([stands, false]);
      shown.unmount();
    }
  });

  test("test_a_small_one_is_no_bar_and_keeps_its_mark_before_its_words", () => {
    render(
      <Folded stands="small" bar={<Summary label="Every area" of="Leafy" stands="small" />}>
        a
      </Folded>,
    );

    expect(bar()).toHaveClass("button", "small", "target-min");
    expect(bar()).not.toHaveClass("bar");
    expect(bar()).not.toHaveAttribute("data-arrow");
    expect(bar()).not.toHaveAttribute("style");
    const said = bar().firstElementChild as HTMLElement;
    expect(said).toHaveClass("says");
    expect(said.firstElementChild).toHaveAttribute("aria-hidden", "true");
    expect(said.textContent).toBe("Every area: Leafy");
  });

  test("test_it_stands_on_what_a_bar_stands_on_while_it_is_closed_and_is_amber_while_its_fold_is_open", () => {
    render(<Folded bar={<Summary label="One of a stack" />}>a</Folded>);

    expect(bar()).toHaveAttribute("data-rest", BAR_AT_REST);
    // The browser's own fold says that it is open by itself: nothing here says it for it.
    expect(bar()).not.toHaveAttribute("aria-expanded");
    expect(foldOf("stacked")).toBe("fold stacked");
    expect([...setsOf(".fold[open] > .bar")]).toEqual([...setsOf('.bar[aria-expanded="true"]')]);
    expect(setsOf(".fold[open] > .bar").get("background-color")).toBe("var(--chosen)");
    // In hand it is drawn as a bar that is closed is, and only while it is closed.
    const inHand = DRAWN.filter((rule) => /^\.fold\b.*:(hover|focus-visible|active)/.test(rule.selector));
    expect(inHand.length).toBeGreaterThan(5);
    expect(inHand.filter((rule) => !/^\.fold(:not\(\[open\]\)|\[open\])/.test(rule.selector)).map((rule) => rule.selector)).toEqual([]);
  });

  test("test_the_browsers_own_mark_is_taken_off_in_every_browser", () => {
    expect(setsOf("summary.button").get("list-style")).toBe("none");
    expect(setsOf("summary.button::-webkit-details-marker").get("display")).toBe("none");
  });

  test("test_a_stack_of_folds_with_a_fold_inside_one_has_no_accessibility_fault", async () => {
    const { container } = render(
      <main>
        <h1>An area</h1>
        <Folded bar={<Summary label="What is measured here" heading={2} />}>
          <Folded bar={<Summary label="Stations and bus stops" heading={3} />}>
            <p>Figures.</p>
          </Folded>
        </Folded>
        <Folded bar={<Summary label="Sources on this page" heading={2} />}>
          <p>Sources.</p>
        </Folded>
      </main>,
    );

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });
});
