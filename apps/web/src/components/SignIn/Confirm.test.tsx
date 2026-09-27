/**
 * The page a link to sign in opens. It takes the token out of the address at once, says
 * whose link it is, and signs nobody in until the button is pressed: so a program that
 * opens the links of a mailbox uses nothing up, and a link that somebody else sent cannot
 * sign a person in to that somebody's account unseen.
 */

import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderToStaticMarkup } from "react-dom/server";

import { CONFIRM, SIGN_IN } from "@/content/account";
import { NOTICE } from "@/content/search";
import { forgetAsked, noteAsked, whatWasAsked } from "@/lib/account/asked";
import { accountPaths } from "@/lib/account/paths";
import { forgetWho, whoIs } from "@/lib/account/who";

import { arrived, EMAIL, held, messageOf, standInAccounts, TOKEN, type AccountStandIn, type Held } from "../../../test/support/account";
import { faultsIn } from "../../../test/support/axe";
import { watch } from "../../../test/support/watch";
import { Confirm } from "./Confirm";

jest.mock("next/navigation", () => ({ usePathname: () => "/sign-in/confirm" }));

const PAGE = accountPaths.confirm();
const CANARY = "zqxcanary7431";

/** Puts the browser of the test at an address, as opening a link does. */
function at(address: string): void {
  window.history.pushState(null, "", address);
}

/** Opens the page at the address of a link, against a stand-in that holds what it is told to. */
async function opened(over: Partial<Held> = {}, address = `${PAGE}#t=${TOKEN}`, to: AccountStandIn = standInAccounts(held(over))) {
  at(address);
  const user = userEvent.setup({ delay: null });
  const view = render(<Confirm client={to.client} />);
  await arrived();
  return { to, user, ...view };
}

const signsIn = (email = EMAIL) => screen.getByRole("button", { name: CONFIRM.ready.signIn(email) });
const theHeading = () => screen.getByRole("heading", { level: 1 });
const sentToSignIn = (to: AccountStandIn) => to.callsTo("sign_in").map((call) => call.body);

beforeEach(() => {
  forgetWho();
  forgetAsked();
});

afterEach(() => at("/"));

describe("the token of the link", () => {
  test("test_it_is_taken_out_of_the_address_bar_at_once_and_before_anything_is_asked", async () => {
    at(`${PAGE}#t=${TOKEN}`);
    const to = standInAccounts();
    // What the address was as each request left the page.
    const seen: string[] = [];
    const client = {
      ...to.client,
      whoseLink: (...sent: Parameters<typeof to.client.whoseLink>) => {
        seen.push(window.location.href);
        return to.client.whoseLink(...sent);
      },
    };

    render(<Confirm client={client} />);

    // It is out of the address as the page is first drawn, before any answer is in.
    expect(window.location.href).toBe(`http://localhost${PAGE}`);
    await arrived();
    expect(seen).toEqual([`http://localhost${PAGE}`]);
  });

  test("test_it_is_put_in_the_place_of_the_entry_that_held_it_and_no_entry_is_added", async () => {
    at(`${PAGE}#t=${TOKEN}`);
    // The watch takes the place of the history, so what is asked of it is kept and not done.
    const watching = watch();
    try {
      const to = standInAccounts();
      render(<Confirm client={to.client} />);
      await arrived();

      // One entry is put in the place of another, by the address of the page and nothing more.
      expect(watching.history).toEqual([["replaceState", null, "", PAGE]]);
      expect(JSON.stringify(watching.history).includes(TOKEN)).toBe(false);
      expect([watching.storage, watching.console]).toEqual([[], []]);
    } finally {
      watching.stop();
    }
  });

  test("test_it_goes_to_the_service_in_the_body_of_a_request_and_in_no_address", async () => {
    const { to } = await opened();

    expect(to.calls.map((call) => [call.method, call.url, call.body])).toEqual([["POST", "/v1/auth/link/whose", { token: TOKEN }]]);
    expect(JSON.stringify(to.calls.map((call) => [call.url, [...call.headers]])).includes(TOKEN)).toBe(false);
  });

  test("test_it_is_nowhere_on_the_page_in_no_attribute_and_in_nothing_the_browser_keeps", async () => {
    const { to, user } = await opened();
    // Watched from here, once the address holds it no longer: the watch takes the place of the history.
    const watching = watch();
    try {
      const before = document.documentElement.innerHTML.includes(TOKEN);
      await user.click(signsIn());
      await arrived();

      expect([before, document.documentElement.innerHTML.includes(TOKEN)]).toEqual([false, false]);
      expect([watching.storage, watching.console, watching.history]).toEqual([[], [], []]);
      expect(watching.everythingOutsideThePage().includes(TOKEN)).toBe(false);
      expect(watching.ids().includes(TOKEN)).toBe(false);
      expect(document.title.includes(TOKEN)).toBe(false);
      // It was sent twice, each time in a body: to ask whose link it is, and to sign in.
      expect(to.calls.filter((call) => call.sent?.includes(TOKEN)).map((call) => call.operation)).toEqual(["whose_link", "sign_in"]);
    } finally {
      watching.stop();
    }
  });

  test.each([
    ["nothing after the hash", PAGE, CONFIRM.none.title],
    ["a bare hash", `${PAGE}#`, CONFIRM.none.title],
    ["what is no link", `${PAGE}#t=${CANARY}`, CONFIRM.notOne.title],
    ["a link with something after it", `${PAGE}#t=${TOKEN}&next=${CANARY}`, CONFIRM.notOne.title],
    ["a link with no name before it", `${PAGE}#${TOKEN}`, CONFIRM.notOne.title],
  ])("test_what_is_not_a_link_is_sent_nowhere_and_shown_nowhere: %s", async (_, address, title) => {
    const { to, container } = await opened({}, address);

    expect(theHeading()).toHaveTextContent(title);
    expect(to.calls).toEqual([]);
    expect(document.documentElement.innerHTML.includes(CANARY)).toBe(false);
    expect(window.location.href).toBe(`http://localhost${PAGE}`);
    // The way on is to ask for a link.
    expect(screen.getByRole("link", { name: address.includes("#t") || address.endsWith(TOKEN) ? CONFIRM.askAgain : CONFIRM.ask })).toHaveAttribute(
      "href",
      accountPaths.signIn(),
    );
    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("whose link it is", () => {
  test("test_the_page_says_whose_link_it_is_and_signs_nobody_in_until_the_button_is_pressed", async () => {
    const { to, user } = await opened();

    expect(theHeading()).toHaveTextContent(CONFIRM.title);
    expect(screen.getByText(EMAIL)).toBeInTheDocument();
    expect(signsIn()).toBeInTheDocument();
    // Asking used nothing up, and nobody is signed in.
    expect(sentToSignIn(to)).toEqual([]);
    expect(to.held.signedIn).toBe(false);
    expect(whoIs().kind).not.toBe("in");

    await user.click(signsIn());
    await arrived();

    expect(sentToSignIn(to)).toEqual([{ token: TOKEN, adult: false, other_browser: false }]);
    expect(to.held.signedIn).toBe(true);
  });

  test("test_nothing_but_a_press_sends_the_token_to_sign_in", async () => {
    const { to, rerender } = await opened();

    // A page that is drawn again, and time that passes, sign nobody in.
    rerender(<Confirm client={to.client} />);
    await arrived();
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 50));
    });

    expect(sentToSignIn(to)).toEqual([]);
    expect(to.callsTo("whose_link")).toHaveLength(1);
  });

  test("test_the_page_says_to_check_the_address_and_what_follows_if_it_is_somebody_elses", async () => {
    await opened();

    expect(screen.getByText(CONFIRM.ready.lead)).toBeInTheDocument();
    expect(screen.getByText(CONFIRM.ready.check)).toBeInTheDocument();
    expect(CONFIRM.ready.check).toMatch(/somebody else's/);
    expect(CONFIRM.ready.check).toMatch(/into their account/);
  });

  test("test_the_address_is_drawn_as_words_and_as_nothing_else", async () => {
    const odd = `"><img src=x onerror=alert(1)>@example.org`;
    const { container } = await opened({ email: odd });

    expect(screen.getByText(odd)).toBeInTheDocument();
    expect(container.querySelector("img")).toBeNull();
    expect(signsIn(odd)).toBeInTheDocument();
    // It is in no attribute: the name of the button is its words.
    const attributes = [...container.querySelectorAll("*")].flatMap((one) => [...one.attributes].map((attribute) => attribute.value));
    expect(attributes.filter((value) => value.includes("onerror"))).toEqual([]);
  });

  test("test_once_signed_in_the_page_says_so_and_the_focus_is_on_what_says_it", async () => {
    noteAsked({ email: EMAIL, minutes: 15 });
    const { user, container } = await opened();

    await user.click(signsIn());
    await arrived();

    expect(theHeading()).toHaveTextContent(CONFIRM.done.title);
    expect(theHeading()).toHaveFocus();
    expect(screen.getByText(CONFIRM.done.text(EMAIL))).toBeInTheDocument();
    expect(screen.queryByText(CONFIRM.done.made)).toBeNull();
    expect(screen.getByRole("link", { name: CONFIRM.done.toSearch })).toHaveAttribute("href", "/");
    expect(screen.getByRole("link", { name: CONFIRM.done.toAccount })).toHaveAttribute("href", accountPaths.account());
    // Whoever shows who is signed in is told, and what was asked is let go.
    expect(whoIs()).toEqual({ kind: "in", email: EMAIL });
    expect(whatWasAsked()).toBeNull();
    expect(await faultsIn(container)).toEqual([]);
  });

  test("test_the_button_is_off_while_it_waits_and_a_second_press_sends_nothing_more", async () => {
    const { to, user } = await opened();
    const waits = to.hold("sign_in");

    await user.click(signsIn());
    expect(signsIn()).toHaveAttribute("aria-disabled", "true");
    expect(signsIn()).toHaveFocus();
    expect(screen.getByText(CONFIRM.signingIn)).toHaveAttribute("role", "status");
    await user.click(signsIn());
    await user.keyboard("{Enter}");
    waits.release();
    await arrived();

    expect(sentToSignIn(to)).toHaveLength(1);
    expect(theHeading()).toHaveTextContent(CONFIRM.done.title);
  });

  test("test_the_page_has_no_accessibility_fault_while_it_checks_and_once_it_says_whose_link_it_is", async () => {
    at(`${PAGE}#t=${TOKEN}`);
    const to = standInAccounts();
    const waits = to.hold("whose_link");
    const { container } = render(<Confirm client={to.client} />);

    expect(screen.getByRole("status")).toHaveTextContent(CONFIRM.checking);
    expect(await faultsIn(container)).toEqual([]);
    waits.release();
    await arrived();

    expect(screen.queryByText(CONFIRM.checking)).toBeNull();
    expect(await faultsIn(container)).toEqual([]);
  });

  test("test_a_page_that_opens_of_itself_takes_the_focus_from_nobody", async () => {
    await opened();

    expect(document.body).toHaveFocus();
  });
});

describe("a link that was asked for in another browser", () => {
  test("test_the_page_says_so_plainly_from_the_start", async () => {
    const { container } = await opened({ sameBrowser: false });

    expect(screen.getByText(CONFIRM.elsewhere.title)).toBeInTheDocument();
    expect(screen.getByText(CONFIRM.elsewhere.text)).toBeInTheDocument();
    expect(CONFIRM.elsewhere.text).toMatch(/If you did not ask for a sign-in link yourself, do not go on/);
    expect(await faultsIn(container)).toEqual([]);
  });

  test("test_it_is_said_of_no_link_that_was_asked_for_in_this_browser", async () => {
    await opened({ sameBrowser: true });

    expect(screen.queryByText(CONFIRM.elsewhere.title)).toBeNull();
  });

  test("test_a_press_sends_nothing_and_the_page_shows_the_address_again_and_asks_a_second_time", async () => {
    const { to, user, container } = await opened({ sameBrowser: false });

    await user.click(signsIn());
    await arrived();

    expect(sentToSignIn(to)).toEqual([]);
    expect(to.held.signedIn).toBe(false);
    const question = screen.getByRole("heading", { level: 2, name: CONFIRM.elsewhere.again });
    expect(question).toHaveFocus();
    expect(screen.getByText(CONFIRM.elsewhere.as)).toBeInTheDocument();
    expect(screen.getByText(EMAIL)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: CONFIRM.elsewhere.yes(EMAIL) })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: CONFIRM.elsewhere.no })).toBeInTheDocument();
    // The notice stays in sight while the page asks.
    expect(screen.getByText(CONFIRM.elsewhere.text)).toBeInTheDocument();
    expect(await faultsIn(container)).toEqual([]);
  });

  test("test_only_once_the_second_asking_is_answered_is_the_token_sent_with_that_the_person_was_asked", async () => {
    const { to, user } = await opened({ sameBrowser: false });

    await user.click(signsIn());
    await user.click(screen.getByRole("button", { name: CONFIRM.elsewhere.yes(EMAIL) }));
    await arrived();

    expect(sentToSignIn(to)).toEqual([{ token: TOKEN, adult: false, other_browser: true }]);
    expect(theHeading()).toHaveTextContent(CONFIRM.done.title);
    expect(theHeading()).toHaveFocus();
  });

  test("test_a_person_who_says_no_is_not_signed_in_and_the_link_is_let_go_unused", async () => {
    const { to, user, container } = await opened({ sameBrowser: false });

    await user.click(signsIn());
    await user.click(screen.getByRole("button", { name: CONFIRM.elsewhere.no }));
    await arrived();

    expect(sentToSignIn(to)).toEqual([]);
    expect(to.held.signedIn).toBe(false);
    expect(theHeading()).toHaveTextContent(CONFIRM.elsewhere.stopped.title);
    expect(theHeading()).toHaveFocus();
    expect(screen.getByText(CONFIRM.elsewhere.stopped.text)).toBeInTheDocument();
    // Nothing is left on the page that could send it.
    expect(screen.queryAllByRole("button")).toEqual([]);
    expect(await faultsIn(container)).toEqual([]);
  });

  test("test_a_link_the_service_says_was_asked_for_elsewhere_only_as_it_is_used_is_asked_about_a_second_time_too", async () => {
    // The page was told the link was asked for here, and the service says otherwise as the
    // link is used: what bound it to the browser may have ended meanwhile.
    const to = standInAccounts(held({ sameBrowser: true }));
    to.inTurn("sign_in", "other_browser");
    const { user } = await opened({}, `${PAGE}#t=${TOKEN}`, to);

    await user.click(signsIn());
    await arrived();

    expect(to.held.signedIn).toBe(false);
    expect(screen.getByRole("heading", { level: 2, name: CONFIRM.elsewhere.again })).toHaveFocus();
    expect(screen.getByText(CONFIRM.elsewhere.title)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: CONFIRM.elsewhere.yes(EMAIL) }));
    await arrived();

    expect(sentToSignIn(to)).toEqual([
      { token: TOKEN, adult: false, other_browser: false },
      { token: TOKEN, adult: false, other_browser: true },
    ]);
    expect(theHeading()).toHaveTextContent(CONFIRM.done.title);
  });
});

describe("a first sign-in, which makes an account", () => {
  const theTick = () => screen.getByRole("checkbox", { name: CONFIRM.first.tick });

  test("test_the_page_says_that_an_account_would_be_made_and_asks_the_person_to_say_they_are_18_or_over", async () => {
    const { container } = await opened({ newAccount: true });

    expect(screen.getByText(CONFIRM.first.text)).toBeInTheDocument();
    expect(theTick()).not.toBeChecked();
    expect(await faultsIn(container)).toEqual([]);
  });

  test("test_nobody_with_an_account_is_asked", async () => {
    await opened({ newAccount: false });

    expect(screen.queryByRole("checkbox")).toBeNull();
  });

  test("test_no_account_is_made_until_the_person_has_said_so", async () => {
    const { to, user, container } = await opened({ newAccount: true });

    await user.click(signsIn());
    await arrived();

    expect(sentToSignIn(to)).toEqual([]);
    expect(theTick()).toHaveFocus();
    expect(theTick()).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByRole("alert")).toHaveTextContent(CONFIRM.first.needed);
    expect(theTick()).toHaveAccessibleDescription(CONFIRM.first.needed);
    expect(await faultsIn(container)).toEqual([]);

    await user.click(theTick());
    expect(screen.queryByRole("alert")).toBeNull();
    await user.click(signsIn());
    await arrived();

    expect(sentToSignIn(to)).toEqual([{ token: TOKEN, adult: true, other_browser: false }]);
    expect(screen.getByText(CONFIRM.done.made)).toBeInTheDocument();
  });

  test("test_a_tick_is_sent_for_nobody_who_was_not_asked", async () => {
    const { to, user } = await opened({ newAccount: false });

    await user.click(signsIn());
    await arrived();

    expect(sentToSignIn(to)).toEqual([{ token: TOKEN, adult: false, other_browser: false }]);
  });

  test("test_a_first_sign_in_from_another_browser_asks_both_and_sends_both", async () => {
    const { to, user } = await opened({ newAccount: true, sameBrowser: false });

    await user.click(theTick());
    await user.click(signsIn());
    await user.click(screen.getByRole("button", { name: CONFIRM.elsewhere.yes(EMAIL) }));
    await arrived();

    expect(sentToSignIn(to)).toEqual([{ token: TOKEN, adult: true, other_browser: true }]);
  });
});

describe("a link that cannot be used", () => {
  test.each(["link_expired", "link_used", "link_not_valid"] as const)(
    "test_it_is_said_in_the_services_own_words_and_the_way_on_is_a_new_link: %s",
    async (code) => {
      const to = standInAccounts().on("whose_link", code);
      const { container } = await opened({}, `${PAGE}#t=${TOKEN}`, to);

      const said = screen.getByRole("alert");
      expect(said).toHaveTextContent(messageOf(code));
      expect(within(said).getByText(NOTICE.requestId, { exact: false })).toBeInTheDocument();
      expect(within(said).getByRole("link", { name: CONFIRM.askAgain })).toHaveAttribute("href", accountPaths.signIn());
      // Nothing is left that could send it, and nothing was sent to sign in.
      expect(screen.queryAllByRole("button")).toEqual([]);
      expect(sentToSignIn(to)).toEqual([]);
      expect(await faultsIn(container)).toEqual([]);
    },
  );

  test("test_a_link_that_ran_out_between_the_asking_and_the_press_says_so_and_the_focus_is_handed_on", async () => {
    const to = standInAccounts().on("sign_in", "link_expired");
    const { user } = await opened({}, `${PAGE}#t=${TOKEN}`, to);

    await user.click(signsIn());
    await arrived();

    expect(screen.getByRole("alert")).toHaveTextContent(messageOf("link_expired"));
    expect(screen.queryAllByRole("button")).toEqual([]);
    expect(theHeading()).toHaveFocus();
  });

  test("test_a_service_that_could_not_be_reached_can_be_asked_again_and_the_focus_is_never_on_nothing", async () => {
    const to = standInAccounts().unreachable("whose_link");
    const { user } = await opened({}, `${PAGE}#t=${TOKEN}`, to);

    const again = screen.getByRole("button", { name: CONFIRM.tryAgain });
    expect(screen.getByRole("alert")).toHaveTextContent(CONFIRM.couldNotCheck);
    to.asHeld("whose_link");
    await user.click(again);
    await arrived();

    expect(to.callsTo("whose_link")).toHaveLength(2);
    expect(signsIn()).toBeInTheDocument();
    expect(theHeading()).toHaveFocus();
  });

  test("test_a_sign_in_that_failed_is_said_under_the_button_which_stays_and_keeps_the_focus", async () => {
    const to = standInAccounts().unreachable("sign_in");
    const { user, container } = await opened({}, `${PAGE}#t=${TOKEN}`, to);

    await user.click(signsIn());
    await arrived();

    expect(screen.getByRole("alert")).toHaveTextContent(CONFIRM.failed);
    expect(signsIn()).toHaveFocus();
    expect(signsIn()).not.toHaveAttribute("aria-disabled");
    expect(await faultsIn(container)).toEqual([]);

    // The link is still in hand, and a second press tries again.
    to.asHeld("sign_in");
    await user.click(signsIn());
    await arrived();
    expect(theHeading()).toHaveTextContent(CONFIRM.done.title);
  });
});

describe("a link that is opened where the page already stands", () => {
  test("test_it_is_read_and_taken_out_of_the_address_though_the_page_is_not_loaded_again", async () => {
    const { to } = await opened({}, PAGE);
    expect(theHeading()).toHaveTextContent(CONFIRM.none.title);

    await act(async () => {
      window.location.hash = `t=${TOKEN}`;
      window.dispatchEvent(new HashChangeEvent("hashchange"));
    });
    await arrived();

    expect(window.location.href).toBe(`http://localhost${PAGE}`);
    expect(to.callsTo("whose_link").map((call) => call.body)).toEqual([{ token: TOKEN }]);
    expect(signsIn()).toBeInTheDocument();
  });

  test("test_the_link_that_was_opened_last_is_the_one_in_hand", async () => {
    const other = `${TOKEN.slice(0, 42)}Z`;
    const { to, user } = await opened();

    await act(async () => {
      window.location.hash = `t=${other}`;
      window.dispatchEvent(new HashChangeEvent("hashchange"));
    });
    await arrived();
    await user.click(signsIn());
    await arrived();

    expect(to.callsTo("whose_link").map((call) => call.body)).toEqual([{ token: TOKEN }, { token: other }]);
    expect(sentToSignIn(to)).toEqual([{ token: other, adult: false, other_browser: false }]);
  });
});

describe("with JavaScript off", () => {
  test("test_the_page_as_it_is_built_says_that_signing_in_needs_javascript", () => {
    // The page as the server builds it, which is what a browser with JavaScript off is shown.
    const built = renderToStaticMarkup(<Confirm client={standInAccounts().client} />);
    const kept = /<noscript>(.*?)<\/noscript>/.exec(built)?.[1] ?? "";

    expect(kept).toContain(SIGN_IN.noScript);
    // It is built the same for every link, and holds nothing of any.
    expect(built).toContain(CONFIRM.checking);
    expect(built.includes(TOKEN)).toBe(false);
  });
});
