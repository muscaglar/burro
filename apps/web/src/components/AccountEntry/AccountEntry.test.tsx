/**
 * The one entry of accounts in the name board. The board draws it only where accounts are
 * on. It says "Sign in" until the service has said that somebody is signed in, and is of
 * one size whichever it says.
 */

import { readFileSync } from "node:fs";
import path from "node:path";

import { act, render, screen, within } from "@testing-library/react";

import { ACCOUNT_NAV } from "@/content/account";
import { SITE } from "@/content/site";
import { forgetAsked, noteAsked } from "@/lib/account/asked";
import { accountPaths } from "@/lib/account/paths";
import { forgetWho, noteSignedIn, noteSignedOut } from "@/lib/account/who";

import { arrived, held, standInAccounts, type AccountStandIn } from "../../../test/support/account";
import { faultsIn } from "../../../test/support/axe";
import { rulesOf } from "../../../test/support/css";
import { isDrawn } from "../kit/drawings";
import { SiteHeader } from "../SiteHeader/SiteHeader";
import { AccountEntry } from "./AccountEntry";
import { ENTRY_ON_A_NARROW_SCREEN, ON_A_NARROW_SCREEN_MAY } from "./look";

let pathname = "/";
jest.mock("next/navigation", () => ({ usePathname: () => pathname }));

const RULES = rulesOf(readFileSync(path.join(__dirname, "AccountEntry.module.css"), "utf8"));
const THREE = [SITE.nav.vibes, SITE.nav.methods, SITE.nav.sources];

async function drawn(to: AccountStandIn = standInAccounts(), narrow?: "gives-way" | "stays") {
  const view = render(
    <ul>
      <AccountEntry className="link target" client={to.client} narrow={narrow} />
    </ul>,
  );
  await arrived();
  return { to, ...view };
}

const theEntry = () => screen.getByRole("link");
/** The drawing a link is handed, as the page names it. */
const drawingOf = (link: HTMLElement, token: string) => /\/art\/([a-z0-9-]+)\.png/.exec(link.style.getPropertyValue(token))?.[1] ?? "";

beforeEach(() => {
  pathname = "/";
  forgetWho();
  forgetAsked();
  delete process.env.NEXT_PUBLIC_BURRO_ACCOUNTS;
});

afterAll(() => {
  delete process.env.NEXT_PUBLIC_BURRO_ACCOUNTS;
});

describe("the name board, with accounts off", () => {
  test("test_it_holds_the_name_and_the_three_pages_and_nothing_of_accounts", () => {
    render(<SiteHeader burro="nowhere" />);

    expect(within(screen.getByRole("banner")).getAllByRole("link").map((link) => link.textContent)).toEqual([SITE.name, ...THREE]);
    expect(screen.getByRole("list").children).toHaveLength(3);
  });

  test("test_nothing_is_asked_of_the_service", async () => {
    const asked = jest.fn(() => Promise.reject(new Error("Nothing may be asked with accounts off.")));
    globalThis.fetch = asked as unknown as typeof fetch;

    render(<SiteHeader burro="nowhere" />);
    await arrived();

    expect(asked).not.toHaveBeenCalled();
  });

  test.each(["", "off", "true", "1", "ON"])("test_it_is_off_unless_the_one_setting_says_on: %s", (value) => {
    process.env.NEXT_PUBLIC_BURRO_ACCOUNTS = value;
    render(<SiteHeader burro="nowhere" />);

    expect(screen.getByRole("list").children).toHaveLength(3);
  });
});

describe("the name board, with accounts on", () => {
  test("test_the_entry_stands_after_the_three_pages_as_an_item_of_their_list_and_is_drawn_as_they_are", async () => {
    process.env.NEXT_PUBLIC_BURRO_ACCOUNTS = "on";
    globalThis.fetch = standInAccounts().fetch;
    const { container } = render(<SiteHeader burro="nowhere" />);
    await arrived();

    const list = screen.getByRole("list");
    expect([...list.children].map((item) => item.tagName)).toEqual(["LI", "LI", "LI", "LI"]);
    expect(within(list).getAllByRole("link").map((link) => link.getAttribute("href"))).toEqual([
      "/vibes",
      "/methods",
      "/sources",
      accountPaths.signIn(),
    ]);
    const entry = within(list).getByRole("link", { name: ACCOUNT_NAV.signIn });
    const beside = within(list).getByRole("link", { name: SITE.nav.sources });
    // It is handed the class of a link of the board, and the pictures of a button, as each is.
    expect(entry.className).toBe(beside.className);
    expect([drawingOf(entry, "--art"), drawingOf(entry, "--art-down")]).toEqual([drawingOf(beside, "--art"), drawingOf(beside, "--art-down")]);
    expect(entry).toHaveAttribute("data-prefetch", "false");
    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("the entry", () => {
  test("test_it_says_sign_in_and_leads_to_signing_in_until_the_service_says_somebody_is_signed_in", async () => {
    const to = standInAccounts(held({ signedIn: true }));
    const waits = to.hold("get_session");
    render(
      <ul>
        <AccountEntry className="link target" client={to.client} />
      </ul>,
    );

    // As the page is built, and until the service has answered.
    expect(theEntry()).toHaveAccessibleName(ACCOUNT_NAV.signIn);
    expect(theEntry()).toHaveAttribute("href", accountPaths.signIn());

    waits.release();
    await arrived();

    expect(theEntry()).toHaveAccessibleName(ACCOUNT_NAV.account);
    expect(theEntry()).toHaveAttribute("href", accountPaths.account());
    expect(to.calls.map((call) => `${call.method} ${call.url}`)).toEqual(["GET /v1/auth/session"]);
  });

  test("test_it_goes_on_saying_sign_in_for_a_person_who_is_not_and_where_the_service_could_not_say", async () => {
    await drawn(standInAccounts(held({ signedIn: false })));
    expect(theEntry()).toHaveAccessibleName(ACCOUNT_NAV.signIn);

    forgetWho();
    document.body.innerHTML = "";
    await drawn(standInAccounts(held({ signedIn: true })).unreachable("get_session"));
    expect(screen.getAllByRole("link").at(-1)).toHaveAccessibleName(ACCOUNT_NAV.signIn);
  });

  test("test_it_hears_a_sign_in_and_a_sign_out_wherever_each_was_made", async () => {
    await drawn();

    act(() => noteSignedIn("rowan.ashdown@example.org"));
    expect(theEntry()).toHaveAccessibleName(ACCOUNT_NAV.account);
    act(() => noteSignedOut());
    expect(theEntry()).toHaveAccessibleName(ACCOUNT_NAV.signIn);
  });

  test("test_the_address_a_person_signed_in_with_is_drawn_nowhere_in_the_board", async () => {
    const { container } = await drawn(standInAccounts(held({ signedIn: true })));

    expect(container.innerHTML.includes("rowan.ashdown")).toBe(false);
  });

  test("test_it_is_of_one_size_whichever_it_says_so_that_nothing_of_the_board_moves_when_the_service_answers", async () => {
    await drawn();
    const says = theEntry().firstElementChild as HTMLElement;
    const sets = (selector: string) => new Map(RULES.filter((rule) => rule.selector === selector && rule.under === null).flatMap((rule) => [...rule.sets]));

    // Both names are in the link, laid in one place. The one that is not said keeps its
    // room, is not drawn, and is kept from whoever hears the page.
    expect([...says.children].map((one) => [one.textContent, one.getAttribute("data-said"), one.getAttribute("aria-hidden")])).toEqual([
      [ACCOUNT_NAV.signIn, "true", null],
      [ACCOUNT_NAV.account, "false", "true"],
    ]);
    expect(sets(".says").get("display")).toBe("inline-grid");
    expect(sets(".one").get("grid-area")).toBe("1 / 1");
    expect([...sets('.one[data-said="false"]')]).toEqual([["visibility", "hidden"]]);

    act(() => noteSignedIn("rowan.ashdown@example.org"));
    expect([...says.children].map((one) => [one.getAttribute("data-said"), one.getAttribute("aria-hidden")])).toEqual([
      ["false", "true"],
      ["true", null],
    ]);
  });

  test.each([
    ["/sign-in", true],
    ["/sign-in/sent", true],
    ["/sign-in/confirm", true],
    ["/account", false],
    ["/", false],
    ["/vibes", false],
  ])("test_it_says_that_it_is_the_page_being_read_on_each_page_of_signing_in: %s", async (at, here) => {
    pathname = at;
    await drawn();

    expect(theEntry().getAttribute("aria-current")).toBe(here ? "page" : null);
    // As a button it is then the button of what is on, and pressed it is that button pressed.
    expect([drawingOf(theEntry(), "--art"), drawingOf(theEntry(), "--art-down")]).toEqual(
      here ? ["ui-button-on", "ui-button-on-down"] : ["ui-button", "ui-button-down"],
    );
    expect(isDrawn(drawingOf(theEntry(), "--art")) && isDrawn(drawingOf(theEntry(), "--art-down"))).toBe(true);
  });

  test("test_once_somebody_is_signed_in_it_is_the_page_of_the_account_that_it_is_of", async () => {
    pathname = "/account";
    await drawn(standInAccounts(held({ signedIn: true })));
    expect(theEntry()).toHaveAttribute("aria-current", "page");

    pathname = "/sign-in";
    document.body.innerHTML = "";
    await drawn(standInAccounts(held({ signedIn: true })));
    expect(screen.getAllByRole("link").at(-1)).not.toHaveAttribute("aria-current");
  });

  test("test_the_service_is_asked_again_when_a_person_comes_back_to_the_tab_they_asked_for_a_link_in", async () => {
    const { to } = await drawn(standInAccounts(held({ signedIn: false })));
    expect(to.callsTo("get_session")).toHaveLength(1);
    const comesBack = async () => {
      await act(async () => {
        document.dispatchEvent(new Event("visibilitychange"));
        window.dispatchEvent(new Event("focus"));
      });
      await arrived();
    };

    // They asked for a link here, signed in in the tab the link opened, and come back to this one.
    noteAsked({ email: "rowan.ashdown@example.org", minutes: 15 });
    to.held.signedIn = true;
    await comesBack();

    expect(to.callsTo("get_session")).toHaveLength(2);
    expect(theEntry()).toHaveAccessibleName(ACCOUNT_NAV.account);
  });

  test("test_somebody_who_is_signed_in_is_asked_about_again_as_they_come_back_to_the_tab", async () => {
    const { to } = await drawn(standInAccounts(held({ signedIn: true })));
    expect(theEntry()).toHaveAccessibleName(ACCOUNT_NAV.account);
    const comesBack = async () => {
      await act(async () => {
        document.dispatchEvent(new Event("visibilitychange"));
        window.dispatchEvent(new Event("focus"));
      });
      await arrived();
    };

    await comesBack();
    // The two that tell of coming back are one asking, and the entry says what it said.
    expect(to.callsTo("get_session")).toHaveLength(2);
    expect(theEntry()).toHaveAccessibleName(ACCOUNT_NAV.account);

    // They signed out meanwhile: in another tab, or of every browser, from another one.
    to.held.signedIn = false;
    await comesBack();

    expect(to.callsTo("get_session")).toHaveLength(3);
    expect(theEntry()).toHaveAccessibleName(ACCOUNT_NAV.signIn);
    // Nobody is signed in and no link was asked for, so coming back asks nothing more.
    await comesBack();
    expect(to.callsTo("get_session")).toHaveLength(3);
  });

  test("test_a_person_who_asked_for_no_link_is_asked_about_once_however_often_they_come_back", async () => {
    const { to } = await drawn(standInAccounts(held({ signedIn: false })));

    for (let times = 0; times < 5; times += 1) {
      await act(async () => {
        document.dispatchEvent(new Event("visibilitychange"));
        window.dispatchEvent(new Event("focus"));
      });
      await arrived();
    }

    expect(to.callsTo("get_session")).toHaveLength(1);
  });

  test("test_a_service_that_could_not_say_is_asked_again_when_a_person_comes_back", async () => {
    const to = standInAccounts(held({ signedIn: true })).unreachable("get_session");
    await drawn(to);
    to.asHeld("get_session");

    await act(async () => {
      window.dispatchEvent(new Event("focus"));
    });
    await arrived();

    expect(to.callsTo("get_session")).toHaveLength(2);
    expect(screen.getAllByRole("link").at(-1)).toHaveAccessibleName(ACCOUNT_NAV.account);
  });

  test("test_the_entry_has_no_accessibility_fault_whichever_it_says", async () => {
    const { container } = await drawn();
    expect(await faultsIn(container)).toEqual([]);

    act(() => noteSignedIn("rowan.ashdown@example.org"));
    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("the entry on a narrow screen", () => {
  const NARROW = /max-width:\s*40rem/;
  const givesWay = RULES.filter((rule) => rule.sets.get("display") === "none");

  test("test_once_a_search_is_open_it_gives_way_so_that_the_board_is_one_line_as_it_is_with_accounts_off", async () => {
    // Measured on a phone 390 wide, after a plain search: with the entry in it the board is
    // 96 px high where it was 52, and the first result stands from 498 to 870 of 844.
    expect(ENTRY_ON_A_NARROW_SCREEN).toBe("gives-way");
    await drawn();
    const item = theEntry().parentElement as HTMLElement;

    expect(item.tagName).toBe("LI");
    expect(item).toHaveAttribute("data-narrow", "gives-way");
    expect(givesWay.map((rule) => [rule.under, rule.selector])).toEqual([
      ["@media (max-width: 40rem)", ':global(body):has([data-search="open"]) .entry[data-narrow="gives-way"]'],
    ]);
    // It is the item that is not laid out, so that nothing of the entry is left in the list.
    expect(item.className).toContain("entry");
  });

  test("test_it_gives_way_on_a_narrow_screen_alone_and_only_while_a_search_is_open", () => {
    expect(givesWay.every((rule) => NARROW.test(rule.under ?? "") && rule.selector.includes('[data-search="open"]'))).toBe(true);
    // Nothing hides it and keeps its room, and nothing dims it.
    expect(RULES.filter((rule) => /\.entry\b/.test(rule.selector) && (rule.sets.has("visibility") || rule.sets.has("opacity")))).toEqual([]);
  });

  test("test_one_line_keeps_it_in_the_board_in_every_state", async () => {
    expect(ON_A_NARROW_SCREEN_MAY).toEqual(["gives-way", "stays"]);
    await drawn(standInAccounts(), "stays");

    expect(theEntry().parentElement).toHaveAttribute("data-narrow", "stays");
    expect(givesWay.filter((rule) => rule.selector.includes("stays"))).toEqual([]);
  });
});
