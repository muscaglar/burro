/**
 * The pages of accounts, as the browser puts each away and shows it again.
 *
 * A browser keeps a page that a person has left, as it stood, and shows it again when they
 * press Back. It asks nothing as it does. So each page lets go of what it holds of anybody
 * as it is put away, and begins again when it is shown: a person who signed out meanwhile
 * is not shown to whoever sits at the browser next.
 */

import { act, render, screen, within } from "@testing-library/react";
import type { ReactElement } from "react";

import * as account from "@/app/account/[[...rest]]/page";
import * as confirm from "@/app/sign-in/confirm/[[...rest]]/page";
import * as signIn from "@/app/sign-in/[[...rest]]/page";
import * as sent from "@/app/sign-in/sent/[[...rest]]/page";
import { Shell } from "@/components/Shell/Shell";
import { ACCOUNT, ACCOUNT_NAV, CONFIRM, SENT, SIGN_IN } from "@/content/account";
import { forgetAsked, noteAsked } from "@/lib/account/asked";
import { forgetAway } from "@/lib/account/away";
import { noteKeeps } from "@/lib/account/recent";
import { forgetWho, whoIs } from "@/lib/account/who";
import { recordedAnswer } from "@/lib/api/recorded";

import { arrived, EMAIL, held, standInAccounts, TOKEN, type AccountStandIn } from "../support/account";

let pathname = "/";
jest.mock("next/navigation", () => ({
  ...jest.requireActual<typeof import("next/navigation")>("next/navigation"),
  usePathname: () => pathname,
  useRouter: () => ({ push: () => undefined }),
}));

const { meta } = recordedAnswer("get_meta", "meta").body;
const KEPT = "Renting a 1 bed up to £1,700 a month, Leafy, Quiet streets";

interface Built {
  readonly default: () => ReactElement | Promise<ReactElement>;
}

async function show(at: string, page: Built, to: AccountStandIn) {
  pathname = at;
  globalThis.fetch = to.fetch;
  const view = render(<Shell meta={meta}>{await page.default()}</Shell>);
  await arrived();
  return view;
}

/** What a browser tells a page as it puts it away, and as it shows it again. */
function told(type: "pagehide" | "pageshow", persisted = true): void {
  const event = new Event(type);
  Object.defineProperty(event, "persisted", { value: persisted });
  act(() => {
    window.dispatchEvent(event);
  });
}

const drawn = () => document.body.textContent ?? "";
const theHeading = () => screen.getByRole("heading", { level: 1 }).textContent;
const theEntry = () => within(screen.getByRole("banner")).getAllByRole("link").at(-1)?.textContent;

beforeEach(() => {
  pathname = "/";
  forgetWho();
  forgetAsked();
  forgetAway();
  noteKeeps(null);
  window.history.replaceState(null, "", "/");
  process.env.NEXT_PUBLIC_BURRO_ACCOUNTS = "on";
});

afterAll(() => {
  delete process.env.NEXT_PUBLIC_BURRO_ACCOUNTS;
});

describe("the page of an account, put away by the browser and shown again", () => {
  test("test_nothing_of_the_account_is_drawn_or_held_once_the_page_is_put_away", async () => {
    const to = standInAccounts(held({ signedIn: true }));
    await show("/account", account, to);
    expect(drawn()).toContain(ACCOUNT.as(EMAIL));
    expect(drawn()).toContain(KEPT);

    told("pagehide");

    // At once, with nothing waited for: what is drawn now is what the browser keeps.
    expect(drawn()).not.toContain(EMAIL);
    expect(drawn()).not.toContain(KEPT);
    expect(document.querySelector("main")?.textContent).toBe("");
    expect(whoIs()).toEqual({ kind: "unknown" });
  });

  test("test_a_person_who_signed_out_meanwhile_is_not_shown_to_whoever_presses_back", async () => {
    const to = standInAccounts(held({ signedIn: true }));
    await show("/account", account, to);
    told("pagehide");
    const asked = to.calls.length;

    // They signed out in another tab, and somebody presses Back.
    to.held.signedIn = false;
    told("pageshow");

    // Nothing of them is drawn before the service is asked, and nothing after.
    expect(drawn()).not.toContain(EMAIL);
    expect(drawn()).not.toContain(KEPT);
    await arrived();
    expect(to.calls.length).toBeGreaterThan(asked);
    expect(theHeading()).toBe(ACCOUNT.out.title);
    expect(drawn()).not.toContain(EMAIL);
    expect(drawn()).not.toContain(KEPT);
    expect(theEntry()).toContain(ACCOUNT_NAV.signIn);
  });

  test("test_a_person_who_is_still_signed_in_finds_their_account_again", async () => {
    const to = standInAccounts(held({ signedIn: true }));
    await show("/account", account, to);
    told("pagehide");
    const asked = to.callsTo("get_me").length;

    told("pageshow");
    await arrived();

    // It was asked of the service again, and is not what the page held before.
    expect(to.callsTo("get_me").length).toBe(asked + 1);
    expect(drawn()).toContain(ACCOUNT.as(EMAIL));
    expect(drawn()).toContain(KEPT);
  });

  test("test_a_page_that_the_browser_does_not_keep_is_left_as_it_is", async () => {
    const to = standInAccounts(held({ signedIn: true }));
    await show("/account", account, to);

    told("pagehide", false);

    expect(drawn()).toContain(ACCOUNT.as(EMAIL));
    expect(drawn()).toContain(KEPT);
  });
});

describe("the pages of signing in, put away by the browser and shown again", () => {
  test("test_the_page_a_link_opens_lets_go_of_the_link_and_of_whose_it_is", async () => {
    const to = standInAccounts(held({ signedIn: false }));
    window.history.replaceState(null, "", `/sign-in/confirm#t=${TOKEN}`);
    await show("/sign-in/confirm", confirm, to);
    expect(drawn()).toContain(CONFIRM.ready.signIn(EMAIL));

    told("pagehide");
    expect(drawn()).not.toContain(EMAIL);
    told("pageshow");
    await arrived();

    // The link is not in hand any more: it is opened again from the email, or not at all.
    expect(theHeading()).toBe(CONFIRM.none.title);
    expect(drawn()).not.toContain(EMAIL);
    expect(to.callsTo("whose_link")).toHaveLength(1);
    expect(to.callsTo("sign_in")).toEqual([]);
    expect(JSON.stringify(to.calls.slice(-2).map((call) => call.sent))).not.toContain(TOKEN);
  });

  test("test_the_page_that_says_a_link_was_sent_lets_go_of_the_address_that_was_typed", async () => {
    const to = standInAccounts(held({ signedIn: false }));
    noteAsked({ email: EMAIL, minutes: 15 });
    await show("/sign-in/sent", sent, to);
    expect(drawn()).toContain(SENT.to(EMAIL));

    told("pagehide");
    expect(drawn()).not.toContain(EMAIL);
    told("pageshow");
    await arrived();

    expect(drawn()).toContain(SENT.toTheAddress);
    expect(drawn()).not.toContain(EMAIL);
  });

  test("test_the_page_of_signing_in_does_not_say_who_was_signed_in_before_it_has_asked_again", async () => {
    const to = standInAccounts(held({ signedIn: true }));
    await show("/sign-in", signIn, to);
    expect(drawn()).toContain(SIGN_IN.already(EMAIL));
    const asked = to.callsTo("get_session").length;

    told("pagehide");
    expect(drawn()).not.toContain(EMAIL);
    to.held.signedIn = false;
    told("pageshow");
    expect(drawn()).not.toContain(EMAIL);
    await arrived();

    expect(to.callsTo("get_session").length).toBe(asked + 1);
    expect(screen.getByRole("textbox", { name: SIGN_IN.field })).toBeInTheDocument();
    expect(drawn()).not.toContain(EMAIL);
  });
});

describe("the name board, on a page that was put away and is shown again", () => {
  test("test_it_says_sign_in_until_the_service_has_said_again_that_somebody_is_signed_in", async () => {
    const to = standInAccounts(held({ signedIn: true }));
    await show("/sign-in/sent", sent, to);
    expect(theEntry()).toContain(ACCOUNT_NAV.account);
    const said = () => within(screen.getByRole("banner")).getByRole("link", { name: /Sign in|Account/ });

    told("pagehide");
    expect(said()).toHaveAccessibleName(ACCOUNT_NAV.signIn);
    told("pageshow");
    await arrived();

    expect(said()).toHaveAccessibleName(ACCOUNT_NAV.account);
    expect(to.callsTo("get_session")).toHaveLength(2);
  });
});
