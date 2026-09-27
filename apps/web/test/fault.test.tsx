/**
 * What "Try again" does on the page of a fault while a search is held.
 *
 * The shell holds the search for as long as the tab is open, and the page of a fault stands
 * inside the shell. So a search page that threw of what its search holds is drawn again from
 * that same search, and throws again, however often it is asked for: seen in a browser, where
 * only loading the page anew brought the first page back.
 */

import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactElement } from "react";

import ErrorPage from "@/app/error";
import { SearchApp } from "@/components/SearchApp/SearchApp";
import { Shell } from "@/components/Shell/Shell";
import { TRAY } from "@/content/compare";
import { FAULT } from "@/content/site";
import { paths, SHARED } from "@/lib/paths";

import { areas, arrived, firstSearch, meta, results, search, settled, waysIfAny } from "./support/search";

let mockAddress = "/";

jest.mock("next/navigation", () => ({ usePathname: () => mockAddress }));

const inShell = (page: ReactElement) => <Shell meta={meta.meta}>{page}</Shell>;

/** Makes a search, chooses its first area to compare, and then has the page of a fault stand in its place. */
async function faultAfterASearch(address: string) {
  const api = firstSearch();
  const user = userEvent.setup({ delay: null });
  const searchPage = inShell(<SearchApp meta={meta.data} areas={areas} client={api.client} />);
  const view = render(searchPage);
  await arrived();
  await search(user);
  await user.click(screen.getAllByRole("button", { name: /^Add to compare/ })[0] as HTMLElement);
  const asked = { retry: jest.fn(), reset: jest.fn() };
  mockAddress = address;
  view.rerender(inShell(<ErrorPage {...asked} />));
  const back = async () => {
    mockAddress = paths.home();
    view.rerender(searchPage);
    await settled();
  };
  return { api, asked, back };
}

/** The areas chosen to compare, each by the cross that takes it out of the bar. */
const chosenToCompare = () => screen.queryAllByRole("button", { name: new RegExp(`^${TRAY.remove("")}`) });

afterEach(() => {
  mockAddress = "/";
});

describe("trying again from the page of a fault", () => {
  test.each([
    ["the search page", paths.home()],
    ["the page a shared link opens", SHARED],
  ])("test_on_a_page_that_is_drawn_from_the_search_trying_again_lets_go_of_the_search_that_is_held: %s", async (_, address) => {
    const { api, asked, back } = await faultAfterASearch(address);

    act(() => screen.getByRole("button", { name: FAULT.retry }).click());

    expect(asked.retry).toHaveBeenCalledTimes(1);
    expect(asked.reset).not.toHaveBeenCalled();
    await back();
    // The first page, as it stands before a search: the two ways in, and no result.
    expect(waysIfAny()).not.toBeNull();
    expect(screen.queryAllByRole("article")).toEqual([]);
    expect(chosenToCompare()).toEqual([]);
    // Nothing of the search before is asked for again.
    expect(api.callsTo("interpret")).toHaveLength(1);
    expect(api.callsTo("rank")).toHaveLength(1);
  });

  test("test_on_any_other_page_trying_again_keeps_the_search_that_is_held", async () => {
    const { api, asked, back } = await faultAfterASearch("/compare");

    act(() => screen.getByRole("button", { name: FAULT.retry }).click());

    expect(asked.retry).toHaveBeenCalledTimes(1);
    await back();
    expect(waysIfAny()).toBeNull();
    expect(results().length).toBeGreaterThan(0);
    expect(chosenToCompare()).toHaveLength(1);
    expect(api.callsTo("rank")).toHaveLength(1);
  });

  test("test_the_button_goes_with_the_page_of_a_fault_and_hands_the_focus_to_what_stays", async () => {
    await faultAfterASearch("/compare");
    const button = screen.getByRole("button", { name: FAULT.retry });
    button.focus();

    act(() => button.click());

    expect(screen.getByRole("main")).toHaveFocus();
  });
});
