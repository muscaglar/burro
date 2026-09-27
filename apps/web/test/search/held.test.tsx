/**
 * The button of the second way in is held at the foot of the window, over the space
 * requirements, and the bar of areas to compare is held there too. What takes the focus by
 * the keyboard is brought clear of both.
 *
 * jsdom lays nothing out, so no test here sees a thing stand under another. Seen in a
 * browser on 2026-09-27, with four areas chosen and the second way in: of 21 things that
 * take the focus, 5 stood under the button at 1440 by 900 and 9 at 390 by 844, and none
 * once what takes the focus was brought clear of the bar of the button. `test/styles.test.ts`
 * holds the style sheet to it. What is held here is that the page says how high the bar is,
 * by the name the style sheet knows it by, for as long as the bar is drawn.
 */

import { screen } from "@testing-library/react";

import { HEIGHT_OF_THE_BAR } from "@/components/SearchApp/bar";
import { SETTINGS } from "@/content/settings";

import { setOnline, standInApi } from "../support/api";
import { firstSearch, openSearch, panelOf, results, settled, way } from "../support/search";

jest.mock("next/navigation", () => ({ usePathname: () => "/" }));

const theButton = () => screen.getByRole("button", { name: SETTINGS.rank });
const told = () => panelOf("deep").style.getPropertyValue(HEIGHT_OF_THE_BAR);

/** Lays the bar of the button out as high as a test says, and everything else as jsdom does: not at all. */
function laidOut(high: () => number) {
  const asItWas = HTMLElement.prototype.getBoundingClientRect;
  const laid = jest.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function (this: HTMLElement) {
    const button = screen.queryByRole("button", { name: SETTINGS.rank });
    const drawn = asItWas.call(this);
    return this === button?.parentElement ? ({ ...drawn, height: high() } as DOMRect) : drawn;
  });
  return () => laid.mockRestore();
}

beforeEach(() => setOnline(true));

describe("how high the bar of the button is, as the search page tells it", () => {
  test("test_nothing_is_told_until_the_second_way_in_is_chosen_and_then_the_part_that_holds_the_bar_is_told", async () => {
    const asJsdomLays = laidOut(() => 74);
    const { user } = await openSearch();

    expect(screen.queryByRole("button", { name: SETTINGS.rank })).toBeNull();
    await way(user, "deep");

    // The bar stands in the part that holds the space requirements, which is what it is held over.
    expect(theButton().parentElement?.parentElement).toBe(panelOf("deep"));
    expect(told()).toBe("74px");
    asJsdomLays();
  });

  test("test_where_the_bar_is_not_laid_out_nothing_is_told_and_the_style_sheet_goes_by_what_was_measured", async () => {
    const { user } = await openSearch();

    await way(user, "deep");

    expect(told()).toBe("");
    expect(panelOf("deep").getAttribute("style") ?? "").not.toContain(HEIGHT_OF_THE_BAR);
  });

  test("test_once_a_search_is_open_the_bar_is_gone_and_nothing_is_left_told", async () => {
    const asJsdomLays = laidOut(() => 74);
    const api = firstSearch(standInApi()).on("rank", "rank-default-rent");
    const { user } = await openSearch(api);
    await way(user, "deep");
    const part = panelOf("deep");
    expect(part.style.getPropertyValue(HEIGHT_OF_THE_BAR)).toBe("74px");

    await user.click(theButton());
    await settled();

    expect(results().length).toBeGreaterThan(0);
    expect(screen.queryByRole("button", { name: SETTINGS.rank })).toBeNull();
    expect(part.style.getPropertyValue(HEIGHT_OF_THE_BAR)).toBe("");
    asJsdomLays();
  });
});
