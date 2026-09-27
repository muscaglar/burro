/**
 * Where a person asks for a link to sign in with: one field for an address and one
 * button. What the address is for and what is kept is said before it is asked for, and
 * what becomes of asking is the same whether or not the address has an account.
 */

import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useEffect } from "react";
import { renderToStaticMarkup } from "react-dom/server";

import { SIGN_IN } from "@/content/account";
import { NOTICE } from "@/content/search";
import { forgetAsked, whatWasAsked } from "@/lib/account/asked";
import { accountPaths } from "@/lib/account/paths";
import { forgetWho } from "@/lib/account/who";
import { recordedAnswer } from "@/lib/api/recorded";
import type { Flow } from "@/lib/search/flow";
import { SearchProvider, useSearch } from "@/lib/search/store";
import { SessionProvider } from "@/lib/session/session";

import { arrived, held, messageOf, standInAccounts, type AccountStandIn, type Held } from "../../../test/support/account";
import { standInApi } from "../../../test/support/api";
import { faultsIn } from "../../../test/support/axe";
import { watch } from "../../../test/support/watch";
import { SignIn } from "./SignIn";

const led: string[] = [];
jest.mock("next/navigation", () => ({
  usePathname: () => "/sign-in",
  useRouter: () => ({ push: (to: string) => led.push(to) }),
}));

const CANARY = "zqxcanary7431";
const TYPED = `${CANARY}@example.org`;

async function opened(over: Partial<Held> = {}, to: AccountStandIn = standInAccounts(held(over))) {
  const user = userEvent.setup({ delay: null });
  const view = render(<SignIn client={to.client} />);
  await arrived();
  return { to, user, ...view };
}

const theField = () => screen.getByRole("textbox", { name: SIGN_IN.field });
const theButton = () => screen.getByRole("button", { name: SIGN_IN.send });
const askedFor = (to: AccountStandIn) => to.callsTo("ask_for_link").map((call) => call.body);

beforeEach(() => {
  led.length = 0;
  forgetWho();
  forgetAsked();
});

describe("the page where a link is asked for", () => {
  test("test_it_holds_one_field_for_an_address_and_one_button", async () => {
    const { container } = await opened();

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(SIGN_IN.title);
    expect(container.querySelectorAll("input, textarea, select")).toHaveLength(1);
    expect(screen.getAllByRole("button")).toEqual([theButton()]);
    expect(theButton()).toHaveAttribute("type", "submit");
    expect(theField()).toHaveAttribute("type", "email");
    expect(theField()).toBeRequired();
  });

  test("test_what_the_address_is_for_and_what_is_kept_is_said_before_it_is_asked_for", async () => {
    await opened();

    // In a sentence each, beside the field, to whoever reads the page and whoever hears it.
    expect(theField()).toHaveAccessibleDescription(SIGN_IN.hint);
    expect(SIGN_IN.hint).toMatch(/to send you the sign-in link, and to know which account is yours/);
    expect(SIGN_IN.hint).toMatch(/keeps the address with your account, and you can delete both/);
    // And all that is kept is listed under the form, in sight and not behind a press.
    const kept = screen.getByRole("region", { name: SIGN_IN.kept.title });
    expect(within(kept).getAllByRole("listitem").map((point) => point.textContent)).toEqual([...SIGN_IN.kept.points]);
    expect(SIGN_IN.kept.points.join(" ")).toMatch(/never keeps the words you type into a search/);
    expect(SIGN_IN.kept.points.join(" ")).toMatch(/delete your account and all of it/);
  });

  test("test_a_browser_may_fill_in_the_address_and_checks_no_spelling_of_it", async () => {
    await opened();

    expect(theField()).toHaveAttribute("autocomplete", "email");
    expect(theField()).toHaveAttribute("inputmode", "email");
    // A browser's fuller spell check sends what a field holds to its maker.
    expect(theField()).toHaveAttribute("spellcheck", "false");
    expect(theField()).toHaveAttribute("autocapitalize", "none");
  });

  test("test_the_form_cannot_put_an_address_in_the_address_of_a_page", async () => {
    const { container } = await opened();
    const form = container.querySelector("form");

    // Were it ever sent by the browser and not by the page, it would be sent as a `POST`,
    // and the field has no name: so nothing of it would be sent at all.
    expect(form).toHaveAttribute("method", "post");
    expect(form).not.toHaveAttribute("action");
    expect(theField()).not.toHaveAttribute("name");
  });

  test("test_the_page_has_no_accessibility_fault", async () => {
    const { container } = await opened();

    expect(await faultsIn(container)).toEqual([]);
  });

  test("test_the_page_as_it_is_built_says_that_signing_in_needs_javascript", () => {
    const built = renderToStaticMarkup(<SignIn client={standInAccounts().client} />);

    expect(/<noscript>(.*?)<\/noscript>/.exec(built)?.[1] ?? "").toContain(SIGN_IN.noScript);
    expect(SIGN_IN.noScript).toMatch(/JavaScript/);
  });
});

describe("asking for a link", () => {
  test("test_the_address_goes_in_the_body_of_one_request_and_the_page_leads_to_where_it_says_a_link_was_sent", async () => {
    const { to, user } = await opened();

    await user.type(theField(), "  rowan.ashdown@example.org ");
    await user.click(theButton());
    await arrived();

    expect(askedFor(to)).toEqual([{ email: "rowan.ashdown@example.org" }]);
    expect(to.lastCallTo("ask_for_link").url).toBe("/v1/auth/link");
    expect(led).toEqual([accountPaths.sent()]);
    // What was asked is held for the page that says so, with what the service said.
    expect(whatWasAsked()).toEqual({ email: "rowan.ashdown@example.org", minutes: 15 });
  });

  test("test_the_enter_key_asks_as_the_button_does", async () => {
    const { to, user } = await opened();

    await user.type(theField(), "rowan.ashdown@example.org{Enter}");
    await arrived();

    expect(askedFor(to)).toHaveLength(1);
    expect(led).toEqual([accountPaths.sent()]);
  });

  test("test_what_becomes_of_asking_is_the_same_whether_or_not_the_address_has_an_account", async () => {
    const known = await opened({ newAccount: false });
    await known.user.type(theField(), "rowan.ashdown@example.org");
    await known.user.click(theButton());
    await arrived();
    const afterKnown = [known.container.innerHTML, [...led], whatWasAsked()];
    known.unmount();
    led.length = 0;
    forgetAsked();

    const unknown = await opened({ newAccount: true });
    await unknown.user.type(theField(), "rowan.ashdown@example.org");
    await unknown.user.click(theButton());
    await arrived();

    // The ids React makes differ from one drawing to the next, and nothing else does.
    const plain = (markup: string) => markup.replace(/_r_[a-z0-9]+_/g, "_r_");
    expect([plain(unknown.container.innerHTML), [...led], whatWasAsked()]).toEqual([plain(String(afterKnown[0])), afterKnown[1], afterKnown[2]]);
    expect(unknown.to.lastCallTo("ask_for_link").body).toEqual(known.to.lastCallTo("ask_for_link").body);
  });

  test("test_a_press_on_an_empty_field_sends_nothing_and_says_what_is_missing_at_the_field", async () => {
    const { to, user, container } = await opened();

    await user.click(theButton());
    await arrived();

    expect(to.callsTo("ask_for_link")).toEqual([]);
    expect(led).toEqual([]);
    expect(theField()).toHaveFocus();
    expect(theField()).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByRole("alert")).toHaveTextContent(SIGN_IN.empty);
    expect(theField()).toHaveAccessibleDescription(`${SIGN_IN.hint} ${SIGN_IN.empty}`);
    expect(await faultsIn(container)).toEqual([]);

    // A field of spaces holds nothing either.
    await user.type(theField(), "   ");
    await user.click(theButton());
    expect(to.callsTo("ask_for_link")).toEqual([]);
  });

  test("test_what_is_no_address_is_said_in_the_services_own_words_at_the_field_which_takes_the_focus", async () => {
    const { to, user, container } = await opened();

    await user.type(theField(), "rowan.ashdown");
    await user.click(theButton());
    await arrived();

    expect(askedFor(to)).toEqual([{ email: "rowan.ashdown" }]);
    expect(led).toEqual([]);
    expect(whatWasAsked()).toBeNull();
    expect(screen.getAllByRole("alert")).toHaveLength(1);
    expect(screen.getByRole("alert")).toHaveTextContent(messageOf("invalid_email"));
    expect(theField()).toHaveFocus();
    expect(theField()).toHaveAttribute("aria-invalid", "true");
    // What was typed is still in the field, for the person to mend.
    expect(theField()).toHaveValue("rowan.ashdown");
    expect(await faultsIn(container)).toEqual([]);
  });

  test.each(["rate_limited", "sign_in_busy", "sign_in_unavailable"] as const)(
    "test_a_refusal_is_said_in_the_services_own_words_under_the_button_which_keeps_the_focus: %s",
    async (code) => {
      const to = standInAccounts().on("ask_for_link", code);
      const { user, container } = await opened({}, to);

      await user.type(theField(), "rowan.ashdown@example.org");
      await user.click(theButton());
      await arrived();

      const said = screen.getByRole("alert");
      expect(said).toHaveTextContent(SIGN_IN.failed);
      expect(said).toHaveTextContent(messageOf(code));
      expect(within(said).getByText(NOTICE.requestId, { exact: false })).toBeInTheDocument();
      expect(led).toEqual([]);
      expect(theButton()).toHaveFocus();
      expect(theButton()).not.toHaveAttribute("aria-disabled");
      // The field is not said to be wrong: what failed is not what was typed.
      expect(theField()).not.toHaveAttribute("aria-invalid");
      expect(await faultsIn(container)).toEqual([]);
    },
  );

  test("test_a_service_that_could_not_be_reached_is_said_and_asking_again_goes_on", async () => {
    const to = standInAccounts().unreachable("ask_for_link");
    const { user } = await opened({}, to);

    await user.type(theField(), "rowan.ashdown@example.org");
    await user.click(theButton());
    await arrived();
    expect(screen.getByRole("alert")).toHaveTextContent(SIGN_IN.failed);

    to.asHeld("ask_for_link");
    await user.click(theButton());
    await arrived();

    expect(screen.queryByRole("alert")).toBeNull();
    expect(led).toEqual([accountPaths.sent()]);
  });

  test("test_the_button_is_off_while_it_waits_keeps_its_words_and_a_second_press_asks_for_nothing_more", async () => {
    const to = standInAccounts();
    const waits = to.hold("ask_for_link");
    const { user } = await opened({}, to);

    await user.type(theField(), "rowan.ashdown@example.org");
    await user.click(theButton());

    // It is off and not switched off, so it keeps the focus. It is of one size: its words stay.
    expect(theButton()).toHaveAttribute("aria-disabled", "true");
    expect(theButton()).not.toBeDisabled();
    expect(theButton()).toHaveFocus();
    expect(screen.getByRole("status")).toHaveTextContent(SIGN_IN.sending);
    await user.click(theButton());
    await user.keyboard("{Enter}");
    waits.release();
    await arrived();

    expect(to.callsTo("ask_for_link")).toHaveLength(1);
    expect(led).toEqual([accountPaths.sent()]);
  });
});

describe("what is typed", () => {
  test("test_the_address_is_in_the_field_and_in_the_body_of_one_request_and_nowhere_else", async () => {
    const watching = watch();
    try {
      const { to, user } = await opened();
      const at = window.location.href;

      await user.type(theField(), TYPED);
      const markup = document.documentElement.innerHTML.includes(CANARY);
      const attributes = [...document.querySelectorAll("*")].flatMap((one) => [...one.attributes].map((attribute) => attribute.value));
      await user.click(theButton());
      await arrived();

      // While it is typed the page holds no copy of it: it is what the field holds, and no markup.
      expect([markup, attributes.some((value) => value.includes(CANARY))]).toEqual([false, false]);
      expect([watching.storage, watching.console, watching.history]).toEqual([[], [], []]);
      expect(watching.everythingOutsideThePage().includes(CANARY)).toBe(false);
      expect([window.location.href === at, document.title.includes(CANARY)]).toEqual([true, false]);
      // It left the page once, in a body.
      expect(to.calls.filter((call) => call.sent?.includes(CANARY)).map((call) => call.operation)).toEqual(["ask_for_link"]);
      expect(to.calls.filter((call) => call.url.includes(CANARY) || JSON.stringify([...call.headers]).includes(CANARY))).toEqual([]);
      // And the page it leads to is named by a fixed address, which holds nothing of it.
      expect(led.join(" ").includes(CANARY)).toBe(false);
    } finally {
      watching.stop();
    }
  });

  test("test_a_failure_shows_nothing_of_what_was_typed", async () => {
    const to = standInAccounts().on("ask_for_link", "sign_in_unavailable");
    const { user } = await opened({}, to);

    await user.type(theField(), TYPED);
    await user.click(theButton());
    await arrived();

    expect(screen.getByRole("alert").textContent?.includes(CANARY)).toBe(false);
    expect(document.documentElement.innerHTML.includes(CANARY)).toBe(false);
  });
});

describe("a person who was in the middle of a search", () => {
  const meta = recordedAnswer("get_meta", "meta").body.data;
  const areas = recordedAnswer("list_areas", "areas").body.data.areas;
  let flow: Flow | null = null;

  /** The search of the tab, as the search page opens it, handed to the test. */
  function Searches() {
    const search = useSearch();
    useEffect(() => {
      flow = search.flow;
    }, [search.flow]);
    return null;
  }

  async function withASearch(ranked: boolean) {
    const api = standInApi().on("rank", "rank-first").on("explain_top", "explanations-first");
    const to = standInAccounts();
    const view = render(
      // Inside one session, as every page is: the shell of the website holds it.
      <SessionProvider>
        <SearchProvider meta={meta} areas={areas} client={api.client}>
          <Searches />
        </SearchProvider>
        <SignIn client={to.client} />
      </SessionProvider>,
    );
    await arrived();
    if (ranked) {
      await act(async () => {
        await flow?.rankNow();
      });
      await arrived();
    }
    return { to, ...view };
  }

  test("test_is_told_that_the_search_will_still_be_open_in_the_tab_when_they_come_back", async () => {
    const { to, container } = await withASearch(true);

    expect(screen.getByText(SIGN_IN.stays)).toBeInTheDocument();
    expect(SIGN_IN.stays).toMatch(/Keep the tab open/);
    // Nothing of the search is sent anywhere, or put in an address, to keep it.
    expect(to.calls.map((call) => call.operation)).toEqual(["get_session"]);
    expect(await faultsIn(container)).toEqual([]);
  });

  test("test_nothing_is_said_of_a_search_to_a_person_who_has_none_open", async () => {
    await withASearch(false);
    expect(screen.queryByText(SIGN_IN.stays)).toBeNull();
  });

  test("test_nothing_is_said_of_a_search_on_a_page_that_stands_in_no_session", async () => {
    await opened();
    expect(screen.queryByText(SIGN_IN.stays)).toBeNull();
  });
});

describe("a person who is signed in already", () => {
  test("test_is_told_so_and_led_to_their_account_and_is_asked_for_no_address", async () => {
    const { container } = await opened({ signedIn: true });

    expect(screen.getByText(SIGN_IN.already("rowan.ashdown@example.org"))).toBeInTheDocument();
    expect(screen.getByRole("link", { name: SIGN_IN.toAccount })).toHaveAttribute("href", accountPaths.account());
    expect(screen.queryByRole("textbox")).toBeNull();
    expect(await faultsIn(container)).toEqual([]);
  });
});
