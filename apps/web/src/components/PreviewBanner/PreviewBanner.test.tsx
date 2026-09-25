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
