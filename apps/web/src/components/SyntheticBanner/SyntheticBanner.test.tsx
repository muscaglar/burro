import { readFileSync } from "node:fs";
import path from "node:path";

import { act, render, screen, within } from "@testing-library/react";

import { BANNER } from "@/content/site";
import { forgetSynthetic, noteSynthetic } from "@/lib/api/synthetic";

import { faultsIn } from "../../../test/support/axe";
import { isFor, rulesOf } from "../../../test/support/css";
import { LiveSyntheticBanner } from "./LiveSyntheticBanner";
import { SyntheticBanner } from "./SyntheticBanner";

beforeEach(forgetSynthetic);

describe("the banner that says the data is made up", () => {
  test("test_the_banner_says_plainly_that_the_data_is_made_up", () => {
    render(<SyntheticBanner synthetic />);

    const banner = screen.getByRole("region", { name: BANNER.label });
    expect(banner).toHaveTextContent("This is made-up test data.");
    expect(banner).toHaveTextContent("Nothing here describes a real place.");
  });

  test("test_the_banner_cannot_be_closed", () => {
    render(<SyntheticBanner synthetic />);

    const banner = within(screen.getByRole("region", { name: BANNER.label }));
    expect(banner.queryAllByRole("button")).toEqual([]);
    expect(banner.queryAllByRole("link")).toEqual([]);
    expect(banner.queryAllByRole("checkbox")).toEqual([]);
  });

  test("test_there_is_no_banner_when_the_data_is_real", () => {
    const { container } = render(<SyntheticBanner synthetic={false} />);

    expect(container).toBeEmptyDOMElement();
  });

  test("test_on_a_narrow_screen_the_banner_is_one_line_once_a_search_is_open", () => {
    // Seen on a phone: the banner took three lines, 90 px, above an answer that did not fit
    // the screen. Before a search it says all of it. Once one is open it says that the data
    // is made up, in one line, and the rest gives way to the answer.
    render(<SyntheticBanner synthetic />);
    const banner = screen.getByRole("region", { name: BANNER.label });
    const rules = rulesOf(readFileSync(path.join(__dirname, "SyntheticBanner.module.css"), "utf8"));
    const gives = rules.filter((rule) => isFor(rule.selector, "rest") && rule.sets.get("display") === "none");

    expect(banner.textContent).toBe(BANNER.text);
    expect(BANNER.text.startsWith(BANNER.short)).toBe(true);
    expect(BANNER.short).toBe("This is made-up test data.");
    expect(banner.querySelector(".rest")?.textContent).toBe(BANNER.text.slice(BANNER.short.length).trim());
    // Only on a narrow screen, and only while the page says a search is open.
    expect(gives.length).toBeGreaterThan(0);
    for (const rule of gives) {
      expect(rule.under).toMatch(/max-width:\s*40rem/);
      expect(rule.selector).toContain(':has([data-search="open"])');
    }
  });

  test("test_the_banner_has_no_accessibility_fault", async () => {
    const { container } = render(<SyntheticBanner synthetic />);

    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("a page built on real data, when an answer says its data is made up", () => {
  test("test_the_banner_shows_as_soon_as_any_answer_says_so_and_then_stays", () => {
    render(<LiveSyntheticBanner />);
    expect(screen.queryByRole("region", { name: BANNER.label })).toBeNull();

    act(() => noteSynthetic(false));
    expect(screen.queryByRole("region", { name: BANNER.label })).toBeNull();

    act(() => noteSynthetic(true));
    expect(screen.getByRole("region", { name: BANNER.label })).toHaveTextContent(BANNER.text);

    act(() => noteSynthetic(false));
    expect(screen.getByRole("region", { name: BANNER.label })).toBeInTheDocument();
  });
});

describe("how the banner is drawn", () => {
  const RULES = rulesOf(readFileSync(path.join(__dirname, "SyntheticBanner.module.css"), "utf8"));
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
    render(<SyntheticBanner synthetic />);
    const banner = screen.getByRole("region", { name: BANNER.label });
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
