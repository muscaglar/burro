/**
 * The button on the search page that keeps a search. With accounts off it draws nothing
 * and asks nothing. For a person who has not signed in it leads to signing in. What it
 * keeps is the spec the page holds, and never a word that was typed.
 */

import { readFileSync } from "node:fs";
import path from "node:path";

import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useEffect } from "react";

import { ACCOUNT_NAV, KEEP } from "@/content/account";
import { forgetAsked, noteAsked } from "@/lib/account/asked";
import { noteOpened } from "@/lib/account/opened";
import { accountPaths } from "@/lib/account/paths";
import { forgetStands, keepsRecent, noteKeeps } from "@/lib/account/recent";
import { askWho, forgetWho, noteSignedIn } from "@/lib/account/who";
import { recordedAnswer } from "@/lib/api/recorded";
import type { Flow } from "@/lib/search/flow";
import { SearchProvider, useSearch } from "@/lib/search/store";

import { arrived, held, messageOf, standInAccounts, type AccountStandIn, type Held } from "../../../test/support/account";
import { standInApi, type StandIn } from "../../../test/support/api";
import { faultsIn } from "../../../test/support/axe";
import { rulesOf } from "../../../test/support/css";
import { watch } from "../../../test/support/watch";
import { KeepSearch } from "./KeepSearch";

jest.mock("next/navigation", () => ({ usePathname: () => "/" }));

const meta = recordedAnswer("get_meta", "meta").body.data;
const areas = recordedAnswer("list_areas", "areas").body.data.areas;
const first = recordedAnswer("rank", "rank-first").body.data;
const refined = recordedAnswer("rank", "rank-refined").body.data;
const shared = recordedAnswer("get_share", "share-opened").body.data;
const CANARY = "zqxcanary7431";
/** How long a ranking stands before it is kept among the last ones, in a test. */
const SOON = 20;

function ranks(): StandIn {
  return standInApi()
    .on("interpret", "interpret-first")
    .on("rank", "rank-first")
    .on("explain_top", "explanations-first")
    .on("get_share", "share-opened");
}

let flow: Flow | null = null;

/** Hands the search to the test, which does to it what a person does on the page. */
function Hands() {
  const search = useSearch();
  useEffect(() => {
    flow = search.flow;
  }, [search.flow]);
  // What the search holds, where the page hands the focus when what was pressed goes.
  return <div id="understood" tabIndex={-1} />;
}

interface Opened {
  readonly accounts?: Partial<Held>;
  readonly to?: AccountStandIn;
  readonly api?: StandIn;
  readonly on?: boolean;
  readonly after?: number;
  /** What opens the search: a ranking, a sentence that is read, or a link somebody shared. */
  readonly by?: "ranking" | "sentence" | "share" | "nothing";
}

async function opened({ accounts = {}, to = standInAccounts(held(accounts)), api = ranks(), on = true, after = SOON, by = "ranking" }: Opened = {}) {
  const user = userEvent.setup({ delay: null });
  const view = render(
    <SearchProvider meta={meta} areas={areas} client={api.client}>
      <Hands />
      <KeepSearch client={to.client} on={on} after={after} />
    </SearchProvider>,
  );
  await arrived();
  await act(async () => {
    if (by === "ranking") await flow?.rankNow();
    if (by === "sentence") await flow?.submitText(`leafy and quiet, 30 minutes to ${CANARY}`);
    if (by === "share") await flow?.openShare("N6BkBdeSvd7xEk0NJVZNzw");
  });
  await arrived();
  return { to, api, user, ...view };
}

/**
 * Lets longer pass than a ranking stands before it is kept among the last ones, and what
 * follows arrive. It is for what must not happen: what must happen is waited for by
 * `sentToBeKept`, however busy the machine is.
 */
async function aWhileLater(): Promise<void> {
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, SOON * 5));
  });
  await arrived();
}

/** Waits until so many searches were sent to be kept among the last ones, and their answers are in. */
async function sentToBeKept(to: AccountStandIn, count: number): Promise<void> {
  await waitFor(() => expect(to.callsTo("keep_recent")).toHaveLength(count), { timeout: 4_000 });
  await arrived();
}

const saves = () => screen.getByRole("button", { name: KEEP.save });

beforeEach(() => {
  flow = null;
  forgetWho();
  forgetAsked();
  noteKeeps(null);
  forgetStands();
});

describe("with accounts off", () => {
  test("test_nothing_is_drawn_and_nothing_is_asked", async () => {
    const { to, container } = await opened({ on: false, accounts: { signedIn: true } });
    await aWhileLater();

    expect(container.querySelectorAll("a, button")).toHaveLength(0);
    expect(container.textContent).toBe("");
    expect(to.calls).toEqual([]);
  });

  test("test_whether_accounts_are_on_is_what_the_one_setting_says", async () => {
    const api = ranks();
    const drawn = () => {
      const view = render(
        <SearchProvider meta={meta} areas={areas} client={api.client}>
          <KeepSearch client={standInAccounts().client} />
        </SearchProvider>,
      );
      const controls = view.container.querySelectorAll("a, button").length;
      view.unmount();
      return controls;
    };

    expect(drawn()).toBe(0);
    process.env.NEXT_PUBLIC_BURRO_ACCOUNTS = "on";
    try {
      expect(drawn()).toBe(1);
    } finally {
      delete process.env.NEXT_PUBLIC_BURRO_ACCOUNTS;
    }
  });
});

describe("for a person who has not signed in", () => {
  test("test_the_button_leads_to_signing_in_and_says_so", async () => {
    const { to, container } = await opened();

    const leads = screen.getByRole("link", { name: KEEP.signIn });
    expect(leads).toHaveAttribute("href", accountPaths.signIn());
    // Which page a person reads next is told to no server ahead of time.
    expect(leads).toHaveAttribute("data-prefetch", "false");
    expect(leads).toHaveClass("target");
    expect(screen.queryByRole("button")).toBeNull();
    // Nothing of the search is sent anywhere: the service was asked who is signed in, and no more.
    expect(to.calls.map((call) => call.operation)).toEqual(["get_session"]);
    expect(await faultsIn(container)).toEqual([]);
  });

  test("test_what_they_were_doing_is_kept_in_memory_and_in_nothing_the_browser_keeps", async () => {
    const watching = watch();
    try {
      const { to } = await opened({ by: "sentence" });
      const at = window.location.href;
      await aWhileLater();

      // The address of where it leads is fixed, and holds nothing of the search.
      expect(screen.getByRole("link", { name: KEEP.signIn }).getAttribute("href")).toBe("/sign-in");
      expect([watching.storage, watching.console, watching.history]).toEqual([[], [], []]);
      expect(watching.everythingOutsideThePage().includes(CANARY)).toBe(false);
      expect(window.location.href).toBe(at);
      expect(to.calls.filter((call) => call.sent !== null)).toEqual([]);
    } finally {
      watching.stop();
    }
  });

  test("test_a_service_that_could_not_say_who_is_signed_in_is_taken_for_nobody", async () => {
    const to = standInAccounts(held({ signedIn: true })).unreachable("get_session");
    await opened({ to });

    expect(screen.getByRole("link", { name: KEEP.signIn })).toBeInTheDocument();
    expect(to.callsTo("keep_search")).toEqual([]);
  });

  test("test_once_they_have_signed_in_elsewhere_and_come_back_the_button_keeps_a_search", async () => {
    const { to } = await opened();
    expect(screen.getByRole("link", { name: KEEP.signIn })).toBeInTheDocument();

    // They asked for a link, signed in in the tab it opened, and come back to this one.
    noteAsked({ email: "rowan.ashdown@example.org", minutes: 15 });
    to.held.signedIn = true;
    await act(async () => {
      window.dispatchEvent(new Event("focus"));
    });
    await arrived();

    expect(saves()).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: KEEP.signIn })).toBeNull();
  });
});

describe("for a person who has signed in", () => {
  test("test_a_press_keeps_the_spec_the_page_holds_in_the_body_of_one_request", async () => {
    const { to, user } = await opened({ accounts: { signedIn: true } });

    await user.click(saves());
    await arrived();

    const call = to.lastCallTo("keep_search");
    expect([call.method, call.url, call.body]).toEqual(["POST", "/v1/me/searches", { spec: first.spec }]);
    expect(to.callsTo("keep_search")).toHaveLength(1);
    expect(to.held.searches[0]?.spec).toEqual(first.spec);
  });

  test("test_what_is_kept_is_what_burro_understood_and_no_word_that_was_typed", async () => {
    const { to, user } = await opened({ accounts: { signedIn: true }, by: "sentence" });

    await user.click(saves());
    await arrived();
    await sentToBeKept(to, 1);

    // The spec is the last one the API returned, and nothing else goes with it.
    const sent = to.calls.filter((call) => call.sent !== null);
    expect(sent.map((call) => Object.keys(call.body as object))).toEqual(sent.map(() => ["spec"]));
    expect(JSON.stringify(to.calls.map((call) => [call.url, call.sent, [...call.headers]])).includes(CANARY)).toBe(false);
    expect(KEEP.what).toMatch(/never the words you typed/);
  });

  test("test_once_kept_the_button_says_so_and_is_off_and_the_page_says_where_it_is_found", async () => {
    const { to, user, container } = await opened({ accounts: { signedIn: true } });

    await user.click(saves());
    await arrived();

    const kept = screen.getByRole("button", { name: KEEP.saved });
    expect(kept).toHaveAttribute("aria-disabled", "true");
    expect(kept).toHaveFocus();
    expect(screen.getByRole("status")).toHaveTextContent(`${KEEP.done} ${KEEP.what}`);
    expect(screen.getByRole("link", { name: KEEP.toAccount })).toHaveAttribute("href", accountPaths.account());
    // A second press keeps nothing more.
    await user.click(kept);
    await user.keyboard("{Enter}");
    await arrived();
    expect(to.callsTo("keep_search")).toHaveLength(1);
    expect(await faultsIn(container)).toEqual([]);
  });

  test("test_once_the_search_changes_it_can_be_kept_again", async () => {
    const { to, api, user } = await opened({ accounts: { signedIn: true } });
    await user.click(saves());
    await arrived();
    expect(screen.getByRole("button", { name: KEEP.saved })).toBeInTheDocument();

    api.on("rank", "rank-refined");
    await act(async () => {
      await flow?.rankNow();
    });
    await arrived();

    expect(saves()).not.toHaveAttribute("aria-disabled");
    expect(screen.getByRole("status")).toHaveTextContent("");
    await user.click(saves());
    await arrived();
    expect(to.callsTo("keep_search").map((call) => call.body)).toEqual([{ spec: first.spec }, { spec: refined.spec }]);
  });

  test("test_what_one_person_saved_is_not_said_to_be_saved_to_whoever_signs_in_after_them", async () => {
    const { to, user } = await opened({ accounts: { signedIn: true } });
    await user.click(saves());
    await arrived();
    expect(screen.getByRole("button", { name: KEEP.saved })).toBeInTheDocument();

    // In another tab the person signed out, and somebody else signed in.
    Object.assign(to.held, { email: "juniper.vale@example.org", searches: [] });
    await act(async () => {
      await askWho(to.client);
    });
    await arrived();

    // It was saved for the one before them. Their account holds no such search, and the page does not say that it does.
    expect(screen.queryByRole("button", { name: KEEP.saved })).toBeNull();
    expect(saves()).not.toHaveAttribute("aria-disabled");
    expect(screen.getByRole("status")).toHaveTextContent("");
    expect(screen.queryByRole("link", { name: KEEP.toAccount })).toBeNull();
  });

  test("test_an_answer_that_comes_once_somebody_else_has_signed_in_is_not_said_to_them", async () => {
    const to = standInAccounts(held({ signedIn: true }));
    // The answer is held back, so that who is signed in can change before it is given.
    const waits = to.hold("keep_search");
    const { user } = await opened({ to });
    await user.click(saves());
    await waitFor(() => expect(waits.waiting()).toBe(1), { timeout: 4_000 });

    to.held.email = "juniper.vale@example.org";
    await act(async () => {
      await askWho(to.client);
    });
    waits.release();
    await arrived();

    expect(screen.queryByRole("button", { name: KEEP.saved })).toBeNull();
    expect(saves()).not.toHaveAttribute("aria-disabled");
    expect(screen.getByRole("status")).toHaveTextContent("");
  });

  test("test_while_no_ranking_stands_on_the_page_nothing_can_be_kept", async () => {
    const { to, user } = await opened({ accounts: { signedIn: true }, by: "nothing" });

    expect(saves()).toHaveAttribute("aria-disabled", "true");
    await user.click(saves());
    await arrived();

    expect(to.callsTo("keep_search")).toEqual([]);
  });

  test("test_the_button_is_off_while_it_waits_and_keeps_the_focus", async () => {
    const to = standInAccounts(held({ signedIn: true }));
    const { user } = await opened({ to });
    const waits = to.hold("keep_search");

    await user.click(saves());
    expect(saves()).toHaveAttribute("aria-disabled", "true");
    expect(saves()).not.toBeDisabled();
    expect(saves()).toHaveFocus();
    expect(screen.getByRole("status")).toHaveTextContent(KEEP.saving);
    await user.click(saves());
    waits.release();
    await arrived();

    expect(to.callsTo("keep_search")).toHaveLength(1);
  });

  test.each(["too_many_searches", "internal_error"] as const)(
    "test_a_search_that_could_not_be_kept_says_why_in_the_services_words_and_can_be_tried_again: %s",
    async (code) => {
      const to = standInAccounts(held({ signedIn: true })).on("keep_search", code);
      const { user, container } = await opened({ to });

      await user.click(saves());
      await arrived();

      expect(screen.getByRole("alert")).toHaveTextContent(KEEP.failed);
      expect(screen.getByRole("alert")).toHaveTextContent(messageOf(code));
      expect(saves()).not.toHaveAttribute("aria-disabled");
      expect(saves()).toHaveFocus();
      expect(await faultsIn(container)).toEqual([]);

      to.asHeld("keep_search");
      await user.click(saves());
      await arrived();
      expect(screen.queryByRole("alert")).toBeNull();
      expect(screen.getByRole("button", { name: KEEP.saved })).toBeInTheDocument();
    },
  );

  test("test_a_session_that_ended_elsewhere_turns_the_button_into_the_way_to_sign_in", async () => {
    const { to, user } = await opened({ accounts: { signedIn: true } });

    to.held.signedIn = false;
    await user.click(saves());
    await arrived();

    expect(to.held.searches).toHaveLength(3);
    expect(screen.getByRole("link", { name: KEEP.signIn })).toBeInTheDocument();
  });
});

describe("the last searches", () => {
  test("test_a_search_that_has_stood_a_while_is_sent_to_be_kept_among_them_where_the_person_lets_burro", async () => {
    const { to } = await opened({ accounts: { signedIn: true, keepRecent: "on" } });

    await sentToBeKept(to, 1);

    const call = to.lastCallTo("keep_recent");
    expect([call.method, call.url, call.body]).toEqual(["POST", "/v1/me/recent", { spec: first.spec }]);
    // Whether they do was asked of the service first.
    expect(to.calls.map((one) => one.operation)).toEqual(["get_session", "get_me", "keep_recent"]);
  });

  test("test_nothing_of_a_search_is_sent_where_the_person_does_not_let_burro_keep_them", async () => {
    const { to } = await opened({ accounts: { signedIn: true, keepRecent: "off" } });

    await aWhileLater();

    expect(to.callsTo("keep_recent")).toEqual([]);
    expect(to.calls.filter((call) => call.sent !== null)).toEqual([]);
    expect(keepsRecent()).toBe(false);
  });

  test("test_nothing_is_sent_until_the_service_has_said_whether_they_do", async () => {
    const to = standInAccounts(held({ signedIn: true, keepRecent: "on" })).unreachable("get_me");
    await opened({ to });

    await aWhileLater();

    expect(to.callsTo("keep_recent")).toEqual([]);
    expect(keepsRecent()).toBeNull();
  });

  test("test_nothing_is_sent_for_a_person_who_has_not_signed_in", async () => {
    const { to } = await opened({ accounts: { signedIn: false } });

    await aWhileLater();

    expect(to.calls.map((call) => call.operation)).toEqual(["get_session"]);
  });

  test("test_a_search_is_sent_once_however_long_it_stands_and_again_once_it_changes", async () => {
    const { to, api } = await opened({ accounts: { signedIn: true } });

    await sentToBeKept(to, 1);
    await aWhileLater();
    expect(to.callsTo("keep_recent")).toHaveLength(1);

    api.on("rank", "rank-refined");
    await act(async () => {
      await flow?.rankNow();
    });
    await sentToBeKept(to, 2);

    expect(to.callsTo("keep_recent").map((call) => call.body)).toEqual([{ spec: first.spec }, { spec: refined.spec }]);
  });

  test("test_a_search_that_changes_before_it_has_stood_a_while_is_not_sent", async () => {
    // As long as a ranking must stand is long here, so that a busy machine does not let it pass.
    const { to, api } = await opened({ accounts: { signedIn: true }, after: 1_500 });
    expect(to.callsTo("keep_recent")).toHaveLength(0);

    // A setting is moved: the ranking changes before the first has stood as long as it must.
    api.on("rank", "rank-refined");
    await act(async () => {
      await flow?.rankNow();
    });
    await sentToBeKept(to, 1);
    await aWhileLater();

    expect(to.callsTo("keep_recent").map((call) => call.body)).toEqual([{ spec: refined.spec }]);
  });

  test("test_a_search_that_came_from_a_link_somebody_shared_is_not_the_persons_own_and_is_not_sent", async () => {
    const { to, user } = await opened({ accounts: { signedIn: true }, by: "share" });

    await aWhileLater();
    expect(to.callsTo("keep_recent")).toEqual([]);

    // It can be kept all the same, by a press.
    await user.click(saves());
    await arrived();
    expect(to.lastCallTo("keep_search").body).toEqual({ spec: shared.spec });
  });

  test("test_the_service_is_believed_where_it_says_it_kept_none", async () => {
    const to = standInAccounts(held({ signedIn: true, keepRecent: "on" }));
    // The answer is held back, so that what the service holds can change before it is given.
    const waits = to.hold("keep_recent");
    await opened({ to });
    await waitFor(() => expect(waits.waiting()).toBe(1), { timeout: 4_000 });
    expect(keepsRecent()).toBe(true);

    // The person took the tick off in another tab, since this page asked.
    to.held.keepRecent = "off";
    waits.release();

    await waitFor(() => expect(keepsRecent()).toBe(false), { timeout: 4_000 });
    expect(to.callsTo("keep_recent")).toHaveLength(1);
  });

  test("test_whether_they_are_kept_is_asked_again_of_the_next_person_who_does_not_let_burro_keep_them", async () => {
    const { to, api } = await opened({ accounts: { signedIn: true, keepRecent: "on" } });
    await sentToBeKept(to, 1);

    // In another tab the person signed out, and somebody signed in who has ticked nothing.
    Object.assign(to.held, { email: "juniper.vale@example.org", keepRecent: "off" });
    await act(async () => {
      await askWho(to.client);
    });
    await arrived();
    // Whoever sits at this tab now makes a search.
    api.on("rank", "rank-refined");
    await act(async () => {
      await flow?.rankNow();
    });
    await aWhileLater();

    // Nothing of it is sent: what was learned of the one before is not held of them.
    expect(to.callsTo("keep_recent").map((call) => call.body)).toEqual([{ spec: first.spec }]);
    expect(keepsRecent()).toBe(false);
  });

  test("test_whether_they_are_kept_is_asked_again_of_the_next_person_who_lets_burro_keep_them", async () => {
    const { to, api } = await opened({ accounts: { signedIn: true, keepRecent: "off" } });
    await aWhileLater();
    expect(to.callsTo("keep_recent")).toEqual([]);

    // In another tab the person signed out, and somebody signed in who has ticked the box.
    Object.assign(to.held, { email: "juniper.vale@example.org", keepRecent: "on" });
    await act(async () => {
      await askWho(to.client);
    });
    await arrived();
    api.on("rank", "rank-refined");
    await act(async () => {
      await flow?.rankNow();
    });

    // Their search is kept, as they asked, though the one before them kept none.
    await sentToBeKept(to, 1);
    expect(to.callsTo("keep_recent").map((call) => call.body)).toEqual([{ spec: refined.spec }]);
    expect(keepsRecent()).toBe(true);
  });

  test("test_a_search_that_stands_as_another_person_signs_in_is_not_sent_to_be_kept_for_them", async () => {
    // The first person lets nothing be kept, so their search was sent nowhere.
    const { to, api } = await opened({ accounts: { signedIn: true, keepRecent: "off" } });
    await aWhileLater();
    expect(to.callsTo("keep_recent").map((call) => call.body)).toEqual([]);

    // In another tab they signed out, and somebody signed in who lets Burro keep their last searches.
    Object.assign(to.held, { email: "juniper.vale@example.org", keepRecent: "on" });
    await act(async () => {
      await askWho(to.client);
    });
    await waitFor(() => expect(keepsRecent()).toBe(true), { timeout: 4_000 });
    await aWhileLater();

    // What stands was made by the one before them, and says where that person must get to.
    expect(to.callsTo("keep_recent").map((call) => call.body)).toEqual([]);

    // A search that they make themselves is kept, as they asked.
    api.on("rank", "rank-refined");
    await act(async () => {
      await flow?.rankNow();
    });
    await sentToBeKept(to, 1);
    expect(to.callsTo("keep_recent").map((call) => call.body)).toEqual([{ spec: refined.spec }]);
  });

  test("test_a_search_that_was_made_while_nobody_was_signed_in_is_not_sent_to_be_kept_for_whoever_signs_in_next", async () => {
    const { to, api, user } = await opened({ accounts: { signedIn: false, keepRecent: "on" } });
    await aWhileLater();

    // Somebody signs in, in the tab that a link opened, and this tab is come back to.
    to.held.signedIn = true;
    await act(async () => {
      await askWho(to.client);
    });
    await waitFor(() => expect(keepsRecent()).toBe(true), { timeout: 4_000 });
    await aWhileLater();

    // Whoever made it was told that a search is gone as the page is closed.
    expect(to.callsTo("keep_recent").map((call) => call.body)).toEqual([]);
    // It can be saved all the same, by a press of whoever is signed in.
    await user.click(saves());
    await arrived();
    expect(to.lastCallTo("keep_search").body).toEqual({ spec: first.spec });

    api.on("rank", "rank-refined");
    await act(async () => {
      await flow?.rankNow();
    });
    await sentToBeKept(to, 1);
    expect(to.callsTo("keep_recent").map((call) => call.body)).toEqual([{ spec: refined.spec }]);
  });

  test("test_whose_a_search_is_is_held_while_the_search_page_is_left_and_come_back_to", async () => {
    const to = standInAccounts(held({ signedIn: true, keepRecent: "off" }));
    const api = ranks();
    const page = (drawn: boolean) => (
      <SearchProvider meta={meta} areas={areas} client={api.client}>
        <Hands />
        {drawn ? <KeepSearch client={to.client} on after={SOON} /> : null}
      </SearchProvider>
    );
    const view = render(page(true));
    await arrived();
    await act(async () => {
      await flow?.rankNow();
    });
    await arrived();

    // The person reads the page of an area, and the search stays open in the tab meanwhile.
    view.rerender(page(false));
    // Somebody else signs in, in another tab, who lets Burro keep their last searches.
    Object.assign(to.held, { email: "juniper.vale@example.org", keepRecent: "on" });
    await act(async () => {
      await askWho(to.client);
    });
    view.rerender(page(true));
    await waitFor(() => expect(keepsRecent()).toBe(true), { timeout: 4_000 });
    await aWhileLater();

    expect(to.callsTo("keep_recent").map((call) => call.body)).toEqual([]);
  });

  test("test_once_nobody_is_signed_in_what_was_known_of_keeping_them_is_let_go", async () => {
    const { to, user } = await opened({ accounts: { signedIn: true } });
    await sentToBeKept(to, 1);
    expect(keepsRecent()).toBe(true);

    to.held.signedIn = false;
    await user.click(saves());
    await arrived();

    expect(keepsRecent()).toBeNull();
  });
});

describe("where the button stands", () => {
  const SHEET = rulesOf(readFileSync(path.join(__dirname, "KeepSearch.module.css"), "utf8"));
  const PAGE = rulesOf(readFileSync(path.join(__dirname, "..", "SearchApp", "SearchApp.module.css"), "utf8"));
  const sets = (selector: string, under: RegExp | null = null) =>
    new Map(
      SHEET.filter((rule) => rule.selector === selector && (under === null ? rule.under === null : under.test(rule.under ?? ""))).flatMap(
        (rule) => [...rule.sets],
      ),
    );

  test("test_it_is_laid_out_by_the_page_as_what_holds_the_way_to_share_a_search_is", async () => {
    const { container } = await opened({ accounts: { signedIn: true } });
    const holds = container.querySelector("button")?.parentElement as HTMLElement;

    // The page lays out what stands beside the way to share a search: a button in the row,
    // and what it says under the row. If that sheet comes to lay it out another way, this fails.
    expect(holds.tagName).toBe("DIV");
    expect(PAGE.filter((rule) => /^\.tools( > div)+$/.test(rule.selector)).map((rule) => [rule.selector, [...rule.sets]])).toEqual([
      [".tools > div", [["display", "contents"]]],
      [".tools > div > div", [["order", "1"], ["flex-basis", "100%"], ["min-width", "0"]]],
    ]);
    expect([...holds.children].map((one) => one.tagName)).toEqual(["BUTTON", "A", "DIV"]);
  });

  test("test_what_it_says_takes_no_room_until_it_says_something_and_is_on_the_page_all_the_same", async () => {
    const { user, container } = await opened({ accounts: { signedIn: true } });
    const says = container.querySelector("[data-says]") as HTMLElement;

    // It is heard when it first speaks only if it was on the page before it spoke.
    expect(says).toHaveAttribute("data-says", "false");
    expect(screen.getByRole("status")).toBeInTheDocument();
    expect(sets(".says").get("position")).toBe("absolute");
    expect(sets('.says[data-says="true"]').get("position")).toBe("static");
    // Once it says something it is read on cream, inside an edge of ink: nothing is read on the grass.
    expect(sets('.says[data-says="true"]').get("background")).toBe("var(--page)");
    expect(sets('.says[data-says="true"]').get("border")).toBe("var(--edge) solid var(--border)");

    await user.click(saves());
    await arrived();
    expect(says).toHaveAttribute("data-says", "true");
  });

  test("test_the_way_to_the_account_stands_beside_it_on_a_narrow_screen_alone", async () => {
    const { container } = await opened({ accounts: { signedIn: true } });

    const leads = screen.getByRole("link", { name: ACCOUNT_NAV.account });
    expect(leads).toHaveAttribute("href", accountPaths.account());
    expect(leads).toHaveAttribute("data-prefetch", "false");
    // On a narrow screen the entry of the name board gives way once a search is open, and
    // this stands in its place. On any other it is not laid out, and the board has it.
    expect([...sets("a.account")]).toEqual([["display", "none"]]);
    expect([...sets("a.account", /max-width:\s*40rem/)]).toEqual([["display", "inline-flex"]]);
    expect(container.querySelectorAll("a")).toHaveLength(1);
  });

  test("test_where_the_entry_stays_in_the_board_no_second_way_to_the_account_is_drawn", async () => {
    const to = standInAccounts(held({ signedIn: true }));
    const api = ranks();
    render(
      <SearchProvider meta={meta} areas={areas} client={api.client}>
        <KeepSearch client={to.client} on narrow="stays" />
      </SearchProvider>,
    );
    await arrived();

    expect(screen.queryByRole("link", { name: ACCOUNT_NAV.account })).toBeNull();
  });

  test("test_nobody_who_has_not_signed_in_is_shown_the_way_to_an_account", async () => {
    await opened();

    expect(screen.queryByRole("link", { name: ACCOUNT_NAV.account })).toBeNull();
  });
});

describe("a search that was opened from the page of an account", () => {
  test("test_what_the_search_holds_takes_the_focus_since_what_was_pressed_went_with_that_page", async () => {
    noteSignedIn("rowan.ashdown@example.org");
    noteOpened();
    await opened({ accounts: { signedIn: true } });

    expect(document.getElementById("understood")).toHaveFocus();
  });

  test("test_a_search_page_that_is_opened_another_way_takes_the_focus_from_nobody", async () => {
    await opened({ accounts: { signedIn: true } });

    expect(document.body).toHaveFocus();
  });
});
