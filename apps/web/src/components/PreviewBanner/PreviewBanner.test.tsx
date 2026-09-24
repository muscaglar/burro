import { render, screen, within } from "@testing-library/react";

import { BANNER, PREVIEW_BANNER } from "@/content/site";

import { faultsIn } from "../../../test/support/axe";
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
