import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen, within } from "@testing-library/react";

import { BANNER, PREVIEW_BANNER } from "@/content/site";

import { faultsIn } from "../../../test/support/axe";
import { isFor, rulesOf } from "../../../test/support/css";
import { PreviewBanner } from "./PreviewBanner";

describe("the banner that says the release is not finished", () => {
  test("test_the_banner_says_plainly_that_the_release_is_a_preview", () => {
    render(<PreviewBanner preview />);

    const banner = screen.getByRole("region", { name: PREVIEW_BANNER.label });
    expect(banner).toHaveTextContent("This is a preview");
    expect(banner).toHaveTextContent("It is not finished");
  });

  test("test_the_banner_never_says_that_the_data_is_made_up", () => {
    render(<PreviewBanner preview />);

    const said = screen.getByRole("region", { name: PREVIEW_BANNER.label }).textContent ?? "";
    expect(said.toLowerCase().includes("made-up")).toBe(false);
    expect(said.toLowerCase().includes("invented")).toBe(false);
    expect(PREVIEW_BANNER.label).not.toBe(BANNER.label);
  });

  test("test_the_banner_holds_no_figure_and_names_no_place", () => {
    // Site copy names states. A number or a place would be a claim with no fact behind it.
    for (const said of [PREVIEW_BANNER.text, PREVIEW_BANNER.real]) {
      expect(/\d/.test(said)).toBe(false);
      expect(said.includes("London")).toBe(false);
    }
  });

  test("test_a_preview_of_real_data_says_that_its_figures_are_of_real_places", () => {
    // Seen in a browser: a banner that said the data was not finished, and nothing of
    // whether it was real. The made-up release had said "made-up" on every page.
    const { rerender } = render(<PreviewBanner preview real />);
    expect(screen.getByRole("region", { name: PREVIEW_BANNER.label })).toHaveTextContent(PREVIEW_BANNER.real);

    // A preview of made-up data does not: the other banner says what its figures are.
    rerender(<PreviewBanner preview />);
    expect(screen.getByRole("region", { name: PREVIEW_BANNER.label })).not.toHaveTextContent(PREVIEW_BANNER.real);
    rerender(<PreviewBanner preview real={false} />);
    expect(screen.getByRole("region", { name: PREVIEW_BANNER.label })).not.toHaveTextContent(PREVIEW_BANNER.real);
  });

  test("test_on_a_narrow_screen_the_banner_is_one_line_once_a_search_is_open", () => {
    // Seen on a phone, on a preview of real data: the banner took six lines, 138 px of a
    // screen of 844, above an answer that was out of sight. Before a search it says all of
    // it. Once one is open it says that this is a preview, in one line.
    render(<PreviewBanner preview real />);
    const banner = screen.getByRole("region", { name: PREVIEW_BANNER.label });
    const rules = rulesOf(readFileSync(path.join(__dirname, "PreviewBanner.module.css"), "utf8"));
    const drawn = (part: string) =>
      rules
        .filter((rule) => isFor(rule.selector, part) && rule.sets.has("display"))
        .map((rule) => [
          rule.sets.get("display"),
          (rule.under ?? "").includes("max-width: 40rem"),
          rule.selector.includes(':has([data-search="open"])'),
        ]);

    // The words are as they were, whole and in one piece: cut in two where the line ends,
    // they stood a part of a point apart on every page.
    const whole = banner.querySelector(".whole");
    expect(whole?.textContent).toBe(`${PREVIEW_BANNER.text} ${PREVIEW_BANNER.real}`);
    expect(whole?.querySelectorAll("*")).toHaveLength(0);
    // The line that stands for them says how they begin, and is a sentence.
    expect(banner.querySelector(".short")?.textContent).toBe("This is a preview.");
    expect(PREVIEW_BANNER.text.startsWith(PREVIEW_BANNER.short.replace(/\.$/, " "))).toBe(true);
    // It is drawn in place of the whole only on a narrow screen, and only while the page
    // says a search is open. Everywhere else it is not drawn at all.
    expect(drawn("whole")).toEqual([["none", true, true]]);
    expect(drawn("short")).toEqual([
      ["none", false, false],
      ["inline", true, true],
    ]);
  });

  test("test_the_banner_cannot_be_closed", () => {
    render(<PreviewBanner preview />);

    const banner = within(screen.getByRole("region", { name: PREVIEW_BANNER.label }));
    expect(banner.queryAllByRole("button")).toEqual([]);
    expect(banner.queryAllByRole("link")).toEqual([]);
    expect(banner.queryAllByRole("checkbox")).toEqual([]);
  });

  test("test_there_is_no_banner_when_the_release_is_finished", () => {
    const { container } = render(<PreviewBanner preview={false} />);

    expect(container).toBeEmptyDOMElement();
  });

  test("test_the_banner_has_no_accessibility_fault", async () => {
    const { container } = render(<PreviewBanner preview />);

    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("how the banner is drawn", () => {
  const RULES = rulesOf(readFileSync(path.join(__dirname, "PreviewBanner.module.css"), "utf8"));
  const FORCED = /forced-colors:\s*active/;
  const setsOf = (selector: string) =>
    new Map(RULES.filter((rule) => rule.selector === selector && rule.under === null).flatMap((rule) => [...rule.sets]));

  test("test_it_is_cream_with_its_words_in_ink_on_a_rule_of_ink_with_a_band_of_amber_over_the_rule", () => {
    const banner = setsOf(".banner");

    expect([banner.get("background"), banner.get("color")]).toEqual(["var(--notice-bg)", "var(--notice-text)"]);
    expect(banner.get("border-block-end")).toBe("2px solid var(--notice-edge)");
    // The band is its own, and not the shell's alone: the page for a fault in the layout has
    // no shell, and its banner has its edge of amber all the same. It takes no room.
    expect(banner.get("box-shadow")).toBe("inset 0 calc(var(--px) * -2) 0 var(--notice-mark)");
  });

  test("test_the_mark_of_a_notice_is_drawn_behind_the_words_and_is_no_part_of_what_is_said", () => {
    render(<PreviewBanner preview real />);
    const banner = screen.getByRole("region", { name: PREVIEW_BANNER.label });
    const text = setsOf(".text");
    const layers = (text.get("background") ?? "").split("linear-gradient(").slice(1);

    // It is a ground of the paragraph: the page holds no element for it, and no picture.
    expect([...banner.querySelectorAll("img, svg, [aria-hidden], [role='img']")]).toEqual([]);
    expect(banner.querySelectorAll("p")).toHaveLength(1);
    // Five cells of ink on a square of cream, inside a rule of ink: a chequer of three each way.
    expect(layers).toHaveLength(7);
    expect(layers.map((layer) => /^var\(--(ink|page)\), var\(--\1\)\)/.exec(layer)?.[1])).toEqual([
      "ink",
      "ink",
      "ink",
      "ink",
      "ink",
      "page",
      "ink",
    ]);
    expect(layers.every((layer) => /no-repeat[,;]?\s*$/.test(layer.trim()))).toBe(true);
    expect(text.get("--mark")).toBe("calc(var(--cell) * 3)");
    // The words begin clear of it, and their second line under their first.
    expect(text.get("padding-inline-start")).toBe("calc(var(--mark) + var(--edge) * 2 + var(--space-2))");
  });

  test("test_a_cell_of_the_mark_is_a_whole_count_of_art_pixels_on_a_phone_and_on_a_desk", () => {
    const wide = RULES.filter((rule) => rule.selector === ".text" && /min-width:\s*60rem/.test(rule.under ?? ""));

    // Three art pixels of two, and two of three: six pixels of the screen on both.
    expect(setsOf(".text").get("--cell")).toBe("calc(var(--px) * 3)");
    expect(wide.map((rule) => rule.sets.get("--cell"))).toEqual(["calc(var(--px) * 2)"]);
  });

  test("test_the_mark_stands_in_the_middle_of_the_first_line_however_large_the_words_are_set", () => {
    // It is placed by the height of a line, which grows with the size a person has set.
    expect(setsOf(".text").get("--down")).toBe("calc((var(--leading-text) * 1em - var(--mark)) / 2)");
    // Nothing that holds the words has a height of its own.
    const fixed = RULES.filter((rule) => rule.sets.has("height") || rule.sets.has("max-height"));
    expect(fixed.map((rule) => rule.selector)).toEqual([]);
  });

  test("test_where_the_system_draws_in_its_own_colours_the_mark_and_the_band_are_not_drawn", () => {
    const forced = new Map(RULES.filter((rule) => FORCED.test(rule.under ?? "")).map((rule) => [rule.selector, rule.sets]));

    expect(forced.get(".banner")?.get("box-shadow")).toBe("none");
    expect([forced.get(".text")?.get("background"), forced.get(".text")?.get("padding-inline-start")]).toEqual(["none", "0"]);
  });
});
