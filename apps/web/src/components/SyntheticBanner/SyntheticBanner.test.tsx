import { act, render, screen, within } from "@testing-library/react";

import { BANNER } from "@/content/site";
import { forgetSynthetic, noteSynthetic } from "@/lib/api/synthetic";

import { faultsIn } from "../../../test/support/axe";
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
