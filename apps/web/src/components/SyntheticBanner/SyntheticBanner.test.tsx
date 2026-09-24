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
