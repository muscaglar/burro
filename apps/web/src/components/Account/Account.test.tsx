/**
 * The page of an account: the searches that are kept, the last searches and the choice of
 * whether they are kept, where the person is signed in, a copy of everything Burro holds,
 * and deleting the account.
 */

import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderToStaticMarkup } from "react-dom/server";

import { ACCOUNT } from "@/content/account";
import { NOTICE } from "@/content/search";
import { wasOpened } from "@/lib/account/opened";
import { accountPaths } from "@/lib/account/paths";
import { keepsRecent, noteKeeps } from "@/lib/account/recent";
import { askWho, forgetWho, noteSignedIn, whoIs } from "@/lib/account/who";
import { recordedAnswer } from "@/lib/api/recorded";
import { LIST_LENGTH } from "@/lib/search/flow";
import { SessionProvider, useSessionIfAny, type Session } from "@/lib/session/session";

import {
  arrived,
  EMAIL,
  held,
  kept,
  messageOf,
  OTHER_SPEC,
  SPEC,
  standInAccounts,
  type AccountStandIn,
  type Held,
} from "../../../test/support/account";
import { standInApi, type StandIn } from "../../../test/support/api";
import { faultsIn } from "../../../test/support/axe";
import { watch } from "../../../test/support/watch";
import { Account } from "./Account";

const led: string[] = [];
jest.mock("next/navigation", () => ({
  usePathname: () => "/account",
  useRouter: () => ({ push: (to: string) => led.push(to) }),
}));

const meta = recordedAnswer("get_meta", "meta").body.data;
const areas = recordedAnswer("list_areas", "areas").body.data.areas;
const CANARY = "zqxcanary7431";

/** What a file holds, as text. jsdom's own cannot say. */
const textOf = (file: Blob) =>
  new Promise<string>((resolve) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.readAsText(file);
  });

/** Says which session it is drawn in, so that a test can read the search the session holds. */
function Tells({ to }: { readonly to: (session: Session | null) => void }) {
  to(useSessionIfAny());
  return null;
}

function ranks(): StandIn {
  return standInApi().on("rank", "rank-first").on("explain_top", "explanations-first");
}

async function opened(over: Partial<Held> = {}, to: AccountStandIn = standInAccounts(held({ signedIn: true, ...over })), api: StandIn = ranks()) {
  const user = userEvent.setup({ delay: null });
  const view = render(<Account meta={meta} areas={areas} client={to.client} ranks={api.client} />);
  await arrived();
  return { to, api, user, ...view };
}

const theHeading = () => screen.getByRole("heading", { level: 1 });
const part = (name: string) => screen.getByRole("region", { name });
const rowsOf = (list: string) => within(screen.getByRole("list", { name: list })).getAllByRole("listitem");
const saved = () => rowsOf(ACCOUNT.searches.list);
const of = (does: string, name: string) => ACCOUNT.searches.of(does, name);

beforeEach(() => {
  led.length = 0;
  forgetWho();
  noteKeeps(null);
  wasOpened();
  Object.assign(URL, { createObjectURL: jest.fn(() => "blob:made-up"), revokeObjectURL: jest.fn() });
});

describe("the page of an account", () => {
  test("test_it_is_built_the_same_for_everybody_and_holds_nothing_of_anybody_until_the_service_is_asked", async () => {
    const to = standInAccounts(held({ signedIn: true }));
    const waits = to.hold("get_me");
    const { container } = render(<Account meta={meta} areas={areas} client={to.client} ranks={ranks().client} />);

    expect(theHeading()).toHaveTextContent(ACCOUNT.title);
    expect(screen.getByRole("status")).toHaveTextContent(ACCOUNT.opening);
    expect(container.textContent?.includes(EMAIL)).toBe(false);
    expect(await faultsIn(container)).toEqual([]);

    waits.release();
    await arrived();
    expect(screen.getByText(ACCOUNT.as(EMAIL))).toBeInTheDocument();
  });

  test("test_the_page_as_it_is_built_says_that_an_account_needs_javascript", () => {
    const built = renderToStaticMarkup(<Account meta={meta} areas={areas} client={standInAccounts().client} ranks={ranks().client} />);

    expect(/<noscript>(.*?)<\/noscript>/.exec(built)?.[1] ?? "").toContain(ACCOUNT.noScript);
    expect(ACCOUNT.noScript).toMatch(/JavaScript/);
    expect(built).not.toMatch(/@example\.org/);
  });

  test("test_it_says_who_is_signed_in_and_holds_every_part_under_a_heading_of_its_own", async () => {
    await opened();

    expect(theHeading()).toHaveTextContent(ACCOUNT.title);
    expect(screen.getByText(ACCOUNT.as(EMAIL))).toBeInTheDocument();
    expect(screen.getAllByRole("heading", { level: 2 }).map((heading) => heading.textContent)).toEqual([
      ACCOUNT.searches.title,
      ACCOUNT.recent.title,
      ACCOUNT.sessions.title,
      ACCOUNT.copy.title,
      ACCOUNT.remove.title,
    ]);
    expect(whoIs()).toEqual({ kind: "in", email: EMAIL });
  });

  test("test_whose_account_it_is_is_decided_by_the_session_and_no_request_names_an_account", async () => {
    const { to } = await opened();

    expect(to.calls.map((call) => `${call.method} ${call.url}`).sort()).toEqual([
      "GET /v1/me",
      "GET /v1/me/recent",
      "GET /v1/me/searches",
      "GET /v1/me/sessions",
    ]);
    // Asking sends no body, and no address of any request holds anything of the person.
    expect(to.calls.filter((call) => call.sent !== null)).toEqual([]);
    expect(JSON.stringify(to.calls.map((call) => [call.url, [...call.headers]])).includes(EMAIL)).toBe(false);
    expect(to.unexpected).toEqual([]);
  });

  test("test_a_person_who_is_not_signed_in_is_told_so_and_led_to_signing_in", async () => {
    const { to, container } = await opened({ signedIn: false });

    expect(theHeading()).toHaveTextContent(ACCOUNT.out.title);
    expect(screen.getByText(ACCOUNT.out.text)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: ACCOUNT.out.signIn })).toHaveAttribute("href", accountPaths.signIn());
    // Nothing else is asked of the service, and nothing of an account is drawn.
    expect(to.calls.map((call) => call.operation)).toEqual(["get_me"]);
    expect(screen.queryAllByRole("heading", { level: 2 })).toEqual([]);
    expect(whoIs().kind).toBe("out");
    expect(await faultsIn(container)).toEqual([]);
  });

  test("test_a_session_that_ended_elsewhere_is_said_as_soon_as_an_answer_says_so", async () => {
    const { to, user } = await opened();

    // The person signed out in another browser, and then presses something here.
    to.held.signedIn = false;
    await user.click(screen.getByRole("button", { name: ACCOUNT.copy.make }));
    await arrived();

    expect(theHeading()).toHaveTextContent(ACCOUNT.out.title);
    expect(screen.queryByText(ACCOUNT.as(EMAIL))).toBeNull();
  });

  test("test_a_page_opened_for_one_person_begins_again_once_the_service_says_that_another_is_signed_in", async () => {
    const { to, user } = await opened();
    expect(saved()).toHaveLength(3);
    // The question that deletes at one press stands open, under the name of the first person.
    await user.click(screen.getByRole("button", { name: ACCOUNT.remove.ask }));
    expect(screen.getByRole("button", { name: ACCOUNT.remove.yes })).toBeInTheDocument();

    // In another tab of the same browser the person signed out, and somebody else signed in.
    const other = "juniper.vale@example.org";
    Object.assign(to.held, { email: other, searches: [], recent: [], fresh: false });
    // The tab is come back to, and the service says who is signed in now.
    await act(async () => {
      await askWho(to.client);
    });
    await arrived();

    expect(whoIs()).toEqual({ kind: "in", email: other });
    expect(screen.getByText(ACCOUNT.as(other))).toBeInTheDocument();
    expect(screen.queryByText(ACCOUNT.as(EMAIL))).toBeNull();
    // Nothing of the first person is left: what is listed is the other's, and no press deletes anything.
    expect(within(part(ACCOUNT.searches.title)).getByText(ACCOUNT.searches.none)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: ACCOUNT.remove.yes })).toBeNull();
    expect(within(part(ACCOUNT.remove.title)).getByText(ACCOUNT.remove.again)).toBeInTheDocument();
    expect(to.callsTo("delete_me")).toEqual([]);
    // What had the focus went with what was drawn, and the focus did not go with it.
    expect(theHeading()).toHaveFocus();
  });

  test("test_a_service_that_could_not_be_reached_is_said_and_can_be_asked_again", async () => {
    const to = standInAccounts(held({ signedIn: true })).unreachable("get_me");
    const { user, container } = await opened({}, to);

    expect(screen.getByRole("alert")).toHaveTextContent(ACCOUNT.failed);
    expect(await faultsIn(container)).toEqual([]);
    to.asHeld("get_me");
    await user.click(screen.getByRole("button", { name: ACCOUNT.tryAgain }));
    await arrived();

    expect(screen.getByText(ACCOUNT.as(EMAIL))).toBeInTheDocument();
    // What was pressed went with the failure it stood in, and the focus did not go with it.
    expect(theHeading()).toHaveFocus();
  });

  test("test_the_page_has_no_accessibility_fault", async () => {
    const { container } = await opened();

    expect(await faultsIn(container)).toEqual([]);
  });

  test("test_every_control_is_a_native_one_of_the_size_of_a_control_and_every_one_is_named", async () => {
    const { container } = await opened();

    const controls = [...container.querySelectorAll<HTMLElement>("a, button, input")];
    expect(controls.length).toBeGreaterThan(10);
    expect(controls.filter((control) => !control.matches(".target, .target-min")).map((control) => control.textContent)).toEqual([]);
    expect(controls.filter((control) => control.getAttribute("tabindex") === "-1")).toEqual([]);
    expect(container.querySelectorAll("[role='button'], [role='link'], [onclick]")).toHaveLength(0);
    for (const button of screen.getAllByRole("button")) expect(button).toHaveAccessibleName();
    // Two buttons that say the same are told apart by their whole names.
    const names = screen.getAllByRole("button").map((button) => button.getAttribute("aria-label") ?? button.textContent);
    expect(new Set(names).size).toBe(names.length);
  });
});

describe("the searches that are kept", () => {
  test("test_each_is_shown_by_the_name_the_service_gave_it_with_when_it_was_kept", async () => {
    const { to } = await opened();

    expect(saved().map((row) => within(row).getAllByRole("paragraph").slice(0, 2).map((line) => line.textContent))).toEqual(
      to.held.searches.map((search) => [search.name, ACCOUNT.searches.kept(search.kept_at === "2026-09-24T18:05:11Z" ? "24 September 2026" : search.kept_at === "2026-09-20T09:41:00Z" ? "20 September 2026" : "2 August 2026")]),
    );
    expect(screen.getByText(ACCOUNT.searches.named)).toBeInTheDocument();
    expect(screen.getByText(ACCOUNT.searches.count(3, 100))).toBeInTheDocument();
  });

  test("test_the_order_is_the_services_and_the_page_sorts_nothing", async () => {
    const inOrder = [kept("b", "Second by name"), kept("a", "First by name", { kept_at: "2020-01-01T00:00:00Z" })];
    await opened({ searches: inOrder });

    expect(saved().map((row) => within(row).getAllByRole("paragraph")[0]?.textContent)).toEqual(["Second by name", "First by name"]);
  });

  test("test_a_person_who_has_kept_none_is_told_how_to_keep_one", async () => {
    const { container } = await opened({ searches: [] });

    expect(within(part(ACCOUNT.searches.title)).getByText(ACCOUNT.searches.none)).toBeInTheDocument();
    expect(screen.queryByRole("list", { name: ACCOUNT.searches.list })).toBeNull();
    expect(await faultsIn(container)).toEqual([]);
  });

  test("test_a_search_is_opened_by_ranking_its_spec_now_and_the_page_leads_to_the_search", async () => {
    let session: Session | null = null;
    const to = standInAccounts(held({ signedIn: true }));
    const api = ranks();
    const user = userEvent.setup({ delay: null });
    // Inside one session, as every page is: the shell of the website holds it.
    render(
      <SessionProvider>
        <Tells to={(told) => (session = told)} />
        <Account meta={meta} areas={areas} client={to.client} ranks={api.client} />
      </SessionProvider>,
    );
    await arrived();
    const [first] = to.held.searches;
    // An area was chosen to compare, from the search that was open before.
    act(() => (session as Session | null)?.compare.toggle({ area_id: "syn-n0001", slug: "alderwick", name: "Alderwick" }));

    await user.click(screen.getByRole("button", { name: of(ACCOUNT.searches.open, first?.name ?? "") }));
    await arrived();

    expect(api.callsTo("rank").map((call) => call.body)).toEqual([{ spec: SPEC, limit: LIST_LENGTH }]);
    expect(led).toEqual(["/"]);
    // Nothing of the search before is left, as none is when a search is begun again.
    expect((session as Session | null)?.compare.get()).toEqual([]);
    // The search is open in the search of the tab, which the search page draws.
    const open = (session as Session | null)?.search()?.store.getState();
    expect(open?.phase).toBe("results");
    expect(open?.rankedHash).toBe(recordedAnswer("rank", "rank-first").body.data.spec_hash);
    expect(open?.shared).toBeNull();
    // The search page is told that a press led to it, so that it hands the focus on.
    expect(wasOpened()).toBe(true);
    // Nothing of the search is in an address, and no request of accounts was made to open it.
    expect(to.calls.filter((call) => call.method !== "GET")).toEqual([]);
  });

  test("test_a_search_that_could_not_be_opened_says_why_in_its_own_row_and_leads_nowhere", async () => {
    const api = ranks().on("rank", "rank-stale-spec");
    const { to, user, container } = await opened({}, undefined, api);
    const [first] = to.held.searches;
    const opens = screen.getByRole("button", { name: of(ACCOUNT.searches.open, first?.name ?? "") });

    await user.click(opens);
    await arrived();

    expect(led).toEqual([]);
    expect(wasOpened()).toBe(false);
    const said = within(saved()[0] as HTMLElement).getByRole("alert");
    expect(said).toHaveTextContent(ACCOUNT.searches.couldNotOpen);
    expect(within(said).getByText(NOTICE.requestId, { exact: false })).toBeInTheDocument();
    expect(opens).toHaveFocus();
    expect(await faultsIn(container)).toEqual([]);
  });

  test("test_a_search_the_service_says_can_no_longer_be_searched_says_why_and_cannot_be_opened", async () => {
    await opened({
      searches: [
        kept("a", "Changed since", { state: "release_changed" }),
        kept("b", "Cannot be read", { state: "unreadable", spec: null }),
      ],
    });
    const [changed, unread] = saved() as [HTMLElement, HTMLElement];

    expect(within(changed).getByText(ACCOUNT.searches.state.release_changed)).toBeInTheDocument();
    expect(within(unread).getByText(ACCOUNT.searches.state.unreadable)).toBeInTheDocument();
    // Each can be taken away, and neither can be opened.
    for (const row of [changed, unread]) {
      expect(within(row).getAllByRole("button").map((button) => button.textContent)).toEqual([ACCOUNT.searches.remove]);
    }
  });

  test("test_taking_one_away_names_it_in_the_body_of_the_request_and_the_list_is_the_services_answer", async () => {
    const { to, user } = await opened();
    const [, second] = to.held.searches;

    await user.click(screen.getByRole("button", { name: of(ACCOUNT.searches.remove, second?.name ?? "") }));
    await arrived();

    const call = to.lastCallTo("forget_search");
    expect([call.method, call.url, call.body]).toEqual(["DELETE", "/v1/me/searches", { search_id: second?.search_id }]);
    expect(saved()).toHaveLength(2);
    expect(screen.queryByText(second?.name ?? "")).toBeNull();
    expect(within(part(ACCOUNT.searches.title)).getByRole("status")).toHaveTextContent(ACCOUNT.searches.removed);
    expect(screen.getByText(ACCOUNT.searches.count(2, 100))).toBeInTheDocument();
  });

  test("test_the_row_that_goes_hands_the_focus_to_the_row_that_takes_its_place_and_the_last_to_the_heading", async () => {
    const { to, user } = await opened({ searches: [kept("a", "One"), kept("b", "Two"), kept("c", "Three")] });

    await user.click(screen.getByRole("button", { name: of(ACCOUNT.searches.remove, "Two") }));
    await arrived();
    expect(screen.getByRole("button", { name: of(ACCOUNT.searches.open, "Three") })).toHaveFocus();

    await user.click(screen.getByRole("button", { name: of(ACCOUNT.searches.remove, "Three") }));
    await arrived();
    // It was the last of the list: the one before it takes the focus.
    expect(screen.getByRole("button", { name: of(ACCOUNT.searches.open, "One") })).toHaveFocus();

    await user.click(screen.getByRole("button", { name: of(ACCOUNT.searches.remove, "One") }));
    await arrived();
    expect(to.held.searches).toEqual([]);
    expect(screen.getByRole("heading", { level: 2, name: ACCOUNT.searches.title })).toHaveFocus();
  });

  test("test_one_that_could_not_be_taken_away_stays_and_says_why", async () => {
    const to = standInAccounts(held({ signedIn: true })).on("forget_search", "search_not_found");
    const { user } = await opened({}, to);
    const [first] = to.held.searches;
    const removes = screen.getByRole("button", { name: of(ACCOUNT.searches.remove, first?.name ?? "") });

    await user.click(removes);
    await arrived();

    expect(saved()).toHaveLength(3);
    const said = within(saved()[0] as HTMLElement).getByRole("alert");
    expect(said).toHaveTextContent(ACCOUNT.searches.couldNotRemove);
    expect(said).toHaveTextContent(messageOf("search_not_found"));
    expect(removes).toHaveFocus();
  });

  test("test_one_thing_is_done_at_a_time_and_what_waits_says_that_it_is_off", async () => {
    const to = standInAccounts(held({ signedIn: true }));
    const { user } = await opened({}, to);
    const waits = to.hold("forget_search");
    const [first, second] = to.held.searches;
    const removes = screen.getByRole("button", { name: of(ACCOUNT.searches.remove, first?.name ?? "") });

    await user.click(removes);
    expect(removes).toHaveAttribute("aria-disabled", "true");
    expect(removes).toHaveFocus();
    expect(within(part(ACCOUNT.searches.title)).getByRole("status")).toHaveTextContent(ACCOUNT.searches.removing);
    await user.click(removes);
    await user.click(screen.getByRole("button", { name: of(ACCOUNT.searches.remove, second?.name ?? "") }));
    waits.release();
    await arrived();

    expect(to.callsTo("forget_search").map((call) => call.body)).toEqual([{ search_id: first?.search_id }]);
  });

  test("test_the_list_that_could_not_be_had_is_said_and_asked_for_again", async () => {
    const to = standInAccounts(held({ signedIn: true })).unreachable("list_searches");
    const { user } = await opened({}, to);

    const said = within(part(ACCOUNT.searches.title)).getByRole("alert");
    expect(said).toHaveTextContent(ACCOUNT.searches.couldNotList);
    to.asHeld("list_searches");
    await user.click(within(said).getByRole("button", { name: ACCOUNT.tryAgain }));
    await arrived();

    expect(saved()).toHaveLength(3);
  });
});

describe("the last searches, and whether they are kept", () => {
  const theTick = () => screen.getByRole("checkbox", { name: ACCOUNT.recent.keep(10) });
  const recent = () => rowsOf(ACCOUNT.recent.list);

  test("test_the_tick_says_what_the_service_says_and_what_it_means_is_said_under_it", async () => {
    await opened({ keepRecent: "on" });

    expect(theTick()).toBeChecked();
    expect(theTick()).toHaveAccessibleDescription(ACCOUNT.recent.hint);
    expect(ACCOUNT.recent.hint).toMatch(/never the words you typed/);
    expect(recent()).toHaveLength(2);
  });

  test("test_where_the_person_does_not_let_burro_keep_them_none_is_listed_and_the_page_says_so", async () => {
    const { container } = await opened({ keepRecent: "off" });

    expect(theTick()).not.toBeChecked();
    expect(screen.getByText(ACCOUNT.recent.off)).toBeInTheDocument();
    expect(screen.queryByRole("list", { name: ACCOUNT.recent.list })).toBeNull();
    expect(screen.queryByRole("button", { name: ACCOUNT.recent.forget })).toBeNull();
    expect(await faultsIn(container)).toEqual([]);
  });

  test("test_taking_the_tick_off_is_sent_as_a_preference_and_the_list_is_what_is_kept_now", async () => {
    const { to, user } = await opened({ keepRecent: "on" });

    await user.click(theTick());
    await arrived();

    const call = to.lastCallTo("set_preferences");
    expect([call.method, call.url, call.body]).toEqual(["PUT", "/v1/me/preferences", { keep_recent: "off" }]);
    expect(theTick()).not.toBeChecked();
    expect(theTick()).toHaveFocus();
    expect(screen.getByText(ACCOUNT.recent.off)).toBeInTheDocument();

    await user.click(theTick());
    await arrived();
    expect(to.lastCallTo("set_preferences").body).toEqual({ keep_recent: "on" });
    expect(theTick()).toBeChecked();
    expect(screen.getByText(ACCOUNT.recent.none)).toBeInTheDocument();
  });

  test("test_the_box_says_what_was_pressed_at_once_and_is_off_until_the_service_has_answered", async () => {
    const to = standInAccounts(held({ signedIn: true, keepRecent: "on" }));
    const { user } = await opened({}, to);
    const waits = to.hold("set_preferences");

    await user.click(theTick());

    // As a box does. What is listed under it is still what the service holds.
    expect(theTick()).not.toBeChecked();
    expect(theTick()).toHaveAttribute("aria-disabled", "true");
    expect(theTick()).toHaveFocus();
    expect(recent()).toHaveLength(2);
    // A second press while it waits changes nothing, and sends nothing.
    await user.click(theTick());
    expect(theTick()).not.toBeChecked();

    waits.release();
    await arrived();

    expect(to.callsTo("set_preferences").map((call) => call.body)).toEqual([{ keep_recent: "off" }]);
    expect(theTick()).not.toBeChecked();
    expect(theTick()).not.toHaveAttribute("aria-disabled");
    expect(screen.getByText(ACCOUNT.recent.off)).toBeInTheDocument();
  });

  test("test_a_change_the_service_did_not_take_is_not_shown_as_taken", async () => {
    const to = standInAccounts(held({ signedIn: true, keepRecent: "on" })).unreachable("set_preferences");
    const { user } = await opened({}, to);

    await user.click(theTick());
    await arrived();

    expect(theTick()).toBeChecked();
    expect(within(part(ACCOUNT.recent.title)).getByRole("alert")).toHaveTextContent(ACCOUNT.recent.couldNotSet);
    expect(recent()).toHaveLength(2);
  });

  test("test_one_of_them_is_saved_by_sending_its_spec_and_the_saved_searches_are_listed_again", async () => {
    const { to, user } = await opened();
    const [, second] = to.held.recent;
    const saves = screen.getByRole("button", { name: of(ACCOUNT.recent.save, second?.name ?? "") });

    await user.click(saves);
    await arrived();

    const call = to.lastCallTo("keep_search");
    expect([call.method, call.url, call.body]).toEqual(["POST", "/v1/me/searches", { spec: OTHER_SPEC }]);
    expect(saved()).toHaveLength(4);
    expect(within(part(ACCOUNT.recent.title)).getByRole("status")).toHaveTextContent(ACCOUNT.recent.saved);
    expect(saves).toHaveFocus();
  });

  test("test_an_account_that_holds_as_many_as_it_may_says_so_in_the_services_words", async () => {
    const to = standInAccounts(held({ signedIn: true })).on("keep_search", "too_many_searches");
    const { user } = await opened({}, to);
    const [first] = to.held.recent;

    await user.click(screen.getByRole("button", { name: of(ACCOUNT.recent.save, first?.name ?? "") }));
    await arrived();

    expect(within(recent()[0] as HTMLElement).getByRole("alert")).toHaveTextContent(messageOf("too_many_searches"));
    expect(saved()).toHaveLength(3);
  });

  test("test_every_one_of_them_is_forgotten_at_one_press_and_the_focus_is_handed_to_the_heading", async () => {
    const { to, user } = await opened();

    await user.click(screen.getByRole("button", { name: ACCOUNT.recent.forget }));
    await arrived();

    const call = to.lastCallTo("forget_recent");
    expect([call.method, call.url]).toEqual(["DELETE", "/v1/me/recent"]);
    expect(to.held.recent).toEqual([]);
    expect(screen.queryByRole("list", { name: ACCOUNT.recent.list })).toBeNull();
    expect(screen.getByText(ACCOUNT.recent.none)).toBeInTheDocument();
    expect(within(part(ACCOUNT.recent.title)).getByRole("status")).toHaveTextContent(ACCOUNT.recent.forgotten);
    expect(screen.getByRole("heading", { level: 2, name: ACCOUNT.recent.title })).toHaveFocus();
    // The tick stays as it was: forgetting them does not stop Burro keeping the next.
    expect(theTick()).toBeChecked();
  });

  test("test_what_the_service_says_of_keeping_them_is_what_the_search_page_is_told", async () => {
    await opened({ keepRecent: "off" });

    expect(keepsRecent()).toBe(false);
  });
});

describe("where a person is signed in", () => {
  const sessions = () => rowsOf(ACCOUNT.sessions.list);

  test("test_each_browser_is_shown_by_its_family_with_three_dates_and_the_one_in_use_says_so", async () => {
    await opened();
    const [here, other] = sessions() as [HTMLElement, HTMLElement];

    expect(within(here).getAllByRole("paragraph").map((line) => line.textContent)).toEqual([
      ACCOUNT.sessions.browser.chrome,
      ACCOUNT.sessions.here,
      ACCOUNT.sessions.made("26 September 2026"),
      ACCOUNT.sessions.seen("26 September 2026"),
      ACCOUNT.sessions.ends("26 October 2026"),
    ]);
    expect(within(other).getAllByRole("paragraph").map((line) => line.textContent)).toEqual([
      ACCOUNT.sessions.browser.safari,
      ACCOUNT.sessions.made("12 September 2026"),
      ACCOUNT.sessions.seen("25 September 2026"),
      ACCOUNT.sessions.ends("25 October 2026"),
    ]);
    expect(within(here).getByRole("button")).toHaveTextContent(ACCOUNT.sessions.signOutHere);
    expect(within(other).getByRole("button")).toHaveTextContent(ACCOUNT.sessions.signOut);
  });

  test("test_the_id_of_a_session_is_drawn_nowhere_and_put_in_no_attribute", async () => {
    const { to, container } = await opened();

    for (const session of to.held.sessions) {
      expect(container.innerHTML.includes(session.session_id)).toBe(false);
    }
    for (const search of [...to.held.searches, ...to.held.recent]) {
      expect(container.innerHTML.includes(search.search_id)).toBe(false);
    }
  });

  test("test_signing_out_of_another_browser_names_it_in_a_body_and_its_line_goes", async () => {
    const { to, user } = await opened();
    const [, other] = to.held.sessions;

    await user.click(within(sessions()[1] as HTMLElement).getByRole("button"));
    await arrived();

    const call = to.lastCallTo("end_sessions");
    expect([call.method, call.url, call.body]).toEqual(["DELETE", "/v1/me/sessions", { session_id: other?.session_id, everywhere: false }]);
    expect(sessions()).toHaveLength(1);
    expect(within(part(ACCOUNT.sessions.title)).getByRole("status")).toHaveTextContent(ACCOUNT.sessions.out);
    // The line went with the press, and the focus is on the line that is left.
    expect(within(sessions()[0] as HTMLElement).getByRole("button")).toHaveFocus();
    expect(theHeading()).toHaveTextContent(ACCOUNT.title);
    expect(whoIs().kind).toBe("in");
  });

  test("test_signing_out_of_this_browser_revokes_the_session_at_the_service_and_the_page_says_so", async () => {
    const { to, user, container } = await opened();

    await user.click(screen.getByRole("button", { name: ACCOUNT.sessions.signOutHere }));
    await arrived();

    const call = to.lastCallTo("sign_out");
    expect([call.method, call.url, call.body]).toEqual(["DELETE", "/v1/auth/session", {}]);
    expect(to.held.signedIn).toBe(false);
    expect(theHeading()).toHaveTextContent(ACCOUNT.signedOut.title);
    expect(theHeading()).toHaveFocus();
    expect(screen.getByText(ACCOUNT.signedOut.text)).toBeInTheDocument();
    expect(screen.queryByText(ACCOUNT.as(EMAIL))).toBeNull();
    expect(whoIs().kind).toBe("out");
    expect(await faultsIn(container)).toEqual([]);
  });

  test("test_signing_out_everywhere_revokes_every_session_and_this_one_among_them", async () => {
    const { to, user } = await opened();

    expect(screen.getByText(ACCOUNT.sessions.everywhereHint)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: ACCOUNT.sessions.everywhere }));
    await arrived();

    expect(to.lastCallTo("end_sessions").body).toEqual({ everywhere: true });
    expect(to.held.sessions).toEqual([]);
    expect(theHeading()).toHaveTextContent(ACCOUNT.signedOut.title);
    expect(theHeading()).toHaveFocus();
    expect(screen.getByText(ACCOUNT.signedOut.everywhere)).toBeInTheDocument();
    expect(whoIs().kind).toBe("out");
  });

  test("test_a_sign_out_that_failed_leaves_the_person_signed_in_and_says_why", async () => {
    const to = standInAccounts(held({ signedIn: true })).unreachable("sign_out").on("end_sessions", "session_not_found");
    const { user } = await opened({}, to);

    await user.click(screen.getByRole("button", { name: ACCOUNT.sessions.signOutHere }));
    await arrived();
    expect(within(part(ACCOUNT.sessions.title)).getByRole("alert")).toHaveTextContent(ACCOUNT.sessions.couldNotSignOut);
    expect(theHeading()).toHaveTextContent(ACCOUNT.title);

    await user.click(within(sessions()[1] as HTMLElement).getByRole("button"));
    await arrived();
    expect(within(part(ACCOUNT.sessions.title)).getByRole("alert")).toHaveTextContent(messageOf("session_not_found"));
    expect(sessions()).toHaveLength(2);
    expect(whoIs().kind).toBe("in");
  });

  test("test_two_browsers_of_one_family_are_told_apart_by_the_names_of_their_buttons", async () => {
    const { to } = await opened();
    to.held.sessions.push({ ...(to.held.sessions[1] as (typeof to.held.sessions)[number]), session_id: "N6BkBdeSvd7xEk0NJVc003", made_at: "2026-09-01T10:00:00Z" });
    await act(async () => undefined);

    const again = await opened({ sessions: to.held.sessions });
    const names = within(again.container).getAllByRole("button", { name: new RegExp(`^${ACCOUNT.sessions.signOut}: `) }).map((button) => button.getAttribute("aria-label"));

    expect(names).toHaveLength(2);
    expect(new Set(names).size).toBe(2);
  });
});

describe("a copy of everything Burro holds", () => {
  test("test_it_is_asked_for_at_a_press_and_offered_as_a_file_that_leads_to_no_server", async () => {
    const { to, user } = await opened();
    const makes = screen.getByRole("button", { name: ACCOUNT.copy.make });
    expect(screen.queryByRole("link", { name: ACCOUNT.copy.save })).toBeNull();
    expect(to.callsTo("export_me")).toEqual([]);

    await user.click(makes);
    await arrived();

    expect(to.callsTo("export_me").map((call) => [call.method, call.url])).toEqual([["GET", "/v1/me/export"]]);
    const saves = screen.getByRole("link", { name: ACCOUNT.copy.save });
    expect(saves).toHaveAttribute("href", "blob:made-up");
    expect(saves).toHaveAttribute("download", ACCOUNT.copy.file);
    expect(saves).toHaveClass("target");
    expect(within(part(ACCOUNT.copy.title)).getByRole("status")).toHaveTextContent(ACCOUNT.copy.ready);
    // The button that made it keeps the focus, and the link is what a keyboard comes to next.
    expect(makes).toHaveFocus();
    await user.tab();
    expect(saves).toHaveFocus();
  });

  test("test_the_file_holds_what_the_service_gave_and_the_page_draws_none_of_it", async () => {
    const made: Blob[] = [];
    (URL.createObjectURL as jest.Mock).mockImplementation((held: Blob) => {
      made.push(held);
      return "blob:made-up";
    });
    const { to, user, container } = await opened({ email: `${CANARY}@example.org` });
    const before = container.innerHTML.split(CANARY).length;

    await user.click(screen.getByRole("button", { name: ACCOUNT.copy.make }));
    await arrived();

    expect(made).toHaveLength(1);
    expect(made[0]?.type).toBe("application/json");
    const copy = JSON.parse(await textOf(made[0] as Blob)) as Record<string, unknown>;
    expect(copy).toMatchObject({ email: `${CANARY}@example.org`, searches: to.held.searches, sessions: to.held.sessions });
    expect(Object.keys(copy).sort()).toEqual(
      ["adult_at", "email", "events", "exported_at", "links", "made_at", "preferences", "recent", "searches", "sessions"],
    );
    // The page draws no more of the person than it did before the copy was made.
    expect(container.innerHTML.split(CANARY).length).toBe(before);
  });

  test("test_the_address_of_a_copy_is_let_go_when_another_is_made_and_when_the_page_is_left", async () => {
    const { user, unmount } = await opened();

    await user.click(screen.getByRole("button", { name: ACCOUNT.copy.make }));
    await arrived();
    expect(URL.revokeObjectURL).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: ACCOUNT.copy.make }));
    await arrived();
    expect(URL.revokeObjectURL).toHaveBeenCalledTimes(1);
    unmount();

    expect(URL.revokeObjectURL).toHaveBeenCalledTimes(2);
    expect(URL.createObjectURL).toHaveBeenCalledTimes(2);
  });

  test("test_a_copy_that_could_not_be_made_says_why_and_offers_no_file", async () => {
    const to = standInAccounts(held({ signedIn: true })).unreachable("export_me");
    const { user } = await opened({}, to);

    await user.click(screen.getByRole("button", { name: ACCOUNT.copy.make }));
    await arrived();

    expect(within(part(ACCOUNT.copy.title)).getByRole("alert")).toHaveTextContent(ACCOUNT.copy.failed);
    expect(screen.queryByRole("link", { name: ACCOUNT.copy.save })).toBeNull();
  });
});

describe("deleting the account", () => {
  const asks = () => screen.getByRole("button", { name: ACCOUNT.remove.ask });

  test("test_the_page_says_what_goes_and_that_it_cannot_be_undone_before_anything_is_pressed", async () => {
    await opened();

    expect(within(part(ACCOUNT.remove.title)).getByText(ACCOUNT.remove.text)).toBeInTheDocument();
    expect(ACCOUNT.remove.text).toMatch(/This cannot be undone\.$/);
    expect(within(part(ACCOUNT.remove.title)).getByText(ACCOUNT.remove.shares)).toBeInTheDocument();
  });

  test("test_a_press_asks_a_second_time_and_sends_nothing", async () => {
    const { to, user, container } = await opened();

    await user.click(asks());
    await arrived();

    expect(to.callsTo("delete_me")).toEqual([]);
    expect(screen.getByText(ACCOUNT.remove.sure)).toHaveFocus();
    expect(screen.getByRole("button", { name: ACCOUNT.remove.yes })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: ACCOUNT.remove.no })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: ACCOUNT.remove.ask })).toBeNull();
    expect(await faultsIn(container)).toEqual([]);
  });

  test("test_a_person_who_says_no_keeps_their_account_and_the_focus_goes_back_to_what_asked", async () => {
    const { to, user } = await opened();

    await user.click(asks());
    await user.click(screen.getByRole("button", { name: ACCOUNT.remove.no }));
    await arrived();

    expect(to.callsTo("delete_me")).toEqual([]);
    expect(to.held.signedIn).toBe(true);
    expect(asks()).toHaveFocus();
    expect(screen.queryByText(ACCOUNT.remove.sure)).toBeNull();
  });

  test("test_a_person_who_says_yes_is_told_that_it_is_gone_and_is_signed_out", async () => {
    const { to, user, container } = await opened();

    await user.click(asks());
    await user.click(screen.getByRole("button", { name: ACCOUNT.remove.yes }));
    await arrived();

    const call = to.lastCallTo("delete_me");
    expect([call.method, call.url, call.body]).toEqual(["DELETE", "/v1/me", {}]);
    expect(theHeading()).toHaveTextContent(ACCOUNT.remove.done.title);
    expect(theHeading()).toHaveFocus();
    expect(screen.getByText(ACCOUNT.remove.done.text)).toBeInTheDocument();
    expect(container.textContent?.includes(EMAIL)).toBe(false);
    expect(screen.queryAllByRole("button")).toEqual([]);
    expect(whoIs().kind).toBe("out");
    expect(await faultsIn(container)).toEqual([]);
  });

  test("test_a_person_who_signed_in_long_ago_is_told_to_sign_in_again_and_is_offered_no_button_that_deletes", async () => {
    const { to, container } = await opened({ fresh: false });

    const remove = part(ACCOUNT.remove.title);
    expect(within(remove).getByText(ACCOUNT.remove.again)).toBeInTheDocument();
    expect(within(remove).getByRole("link", { name: ACCOUNT.remove.signIn })).toHaveAttribute("href", accountPaths.signIn());
    expect(within(remove).queryAllByRole("button")).toEqual([]);
    expect(to.callsTo("delete_me")).toEqual([]);
    expect(await faultsIn(container)).toEqual([]);
  });

  test("test_where_the_service_says_so_only_as_it_is_asked_it_is_said_in_its_words_with_the_way_to_sign_in", async () => {
    // The page was told the sign-in was a short while ago, and it was longer by the press.
    const to = standInAccounts(held({ signedIn: true })).on("delete_me", "sign_in_again");
    const { user } = await opened({}, to);

    await user.click(asks());
    await user.click(screen.getByRole("button", { name: ACCOUNT.remove.yes }));
    await arrived();

    const said = within(part(ACCOUNT.remove.title)).getByRole("alert");
    expect(said).toHaveTextContent(messageOf("sign_in_again"));
    expect(within(said).getByRole("link", { name: ACCOUNT.remove.signIn })).toHaveAttribute("href", accountPaths.signIn());
    expect(theHeading()).toHaveTextContent(ACCOUNT.title);
    expect(whoIs().kind).toBe("in");
  });

  test("test_the_button_that_deletes_is_off_while_it_waits_and_a_second_press_sends_nothing_more", async () => {
    const to = standInAccounts(held({ signedIn: true }));
    const { user } = await opened({}, to);
    const waits = to.hold("delete_me");

    await user.click(asks());
    const yes = screen.getByRole("button", { name: ACCOUNT.remove.yes });
    await user.click(yes);
    expect(yes).toHaveAttribute("aria-disabled", "true");
    expect(yes).toHaveFocus();
    await user.click(yes);
    await user.click(screen.getByRole("button", { name: ACCOUNT.remove.no }));
    waits.release();
    await arrived();

    expect(to.callsTo("delete_me")).toHaveLength(1);
    expect(theHeading()).toHaveTextContent(ACCOUNT.remove.done.title);
  });
});

describe("what the tab holds of a search once a person has left", () => {
  const share = recordedAnswer("create_share", "share-made-exact").body.data;

  /** The page of an account, in a tab whose search holds a ranking, an area to compare and a link that was made of it. */
  async function withASearchOpenInTheTab(to: AccountStandIn = standInAccounts(held({ signedIn: true }))) {
    let session: Session | null = null;
    const user = userEvent.setup({ delay: null });
    render(
      <SessionProvider>
        <Tells to={(told) => (session = told)} />
        <Account meta={meta} areas={areas} client={to.client} ranks={ranks().client} />
      </SessionProvider>,
    );
    await arrived();
    await user.click(screen.getByRole("button", { name: of(ACCOUNT.searches.open, to.held.searches[0]?.name ?? "") }));
    await arrived();
    const tab = session as Session | null;
    act(() => {
      tab?.compare.toggle({ area_id: "syn-n0001", slug: "alderwick", name: "Alderwick" });
      tab?.link.set({ of: tab.search()?.store.getState().rankedHash ?? null, exact: true, share });
    });
    expect(tab?.search()?.store.getState().phase).toBe("results");
    return { user, tab };
  }

  /** What a tab holds of a search: where the search stands, its ranking, the two hashes, what was read, what is compared and the link. */
  const heldOf = (tab: Session | null) => {
    const open = tab?.search()?.store.getState();
    return [open?.phase, open?.ranking, open?.rankedHash, open?.specHash, open?.read, tab?.compare.get(), tab?.link.get()];
  };
  const NO_SEARCH = ["empty", null, null, null, null, [], null];

  test("test_signing_out_of_this_browser_leaves_no_search_in_the_tab", async () => {
    const { user, tab } = await withASearchOpenInTheTab();

    await user.click(screen.getByRole("button", { name: ACCOUNT.sessions.signOutHere }));
    await arrived();

    // The page that says so leads to the search page, where whoever sits down next would read it.
    expect(theHeading()).toHaveTextContent(ACCOUNT.signedOut.title);
    expect(screen.getByRole("link", { name: ACCOUNT.signedOut.toSearch })).toBeInTheDocument();
    expect(heldOf(tab)).toEqual(NO_SEARCH);
    expect(tab?.search()?.store.getState().spec).toEqual(meta.defaults.rent);
  });

  test("test_signing_out_everywhere_leaves_no_search_in_the_tab", async () => {
    const { user, tab } = await withASearchOpenInTheTab();

    await user.click(screen.getByRole("button", { name: ACCOUNT.sessions.everywhere }));
    await arrived();

    expect(theHeading()).toHaveTextContent(ACCOUNT.signedOut.title);
    expect(heldOf(tab)).toEqual(NO_SEARCH);
  });

  test("test_deleting_the_account_leaves_no_search_in_the_tab", async () => {
    const { user, tab } = await withASearchOpenInTheTab();

    await user.click(screen.getByRole("button", { name: ACCOUNT.remove.ask }));
    await user.click(screen.getByRole("button", { name: ACCOUNT.remove.yes }));
    await arrived();

    expect(theHeading()).toHaveTextContent(ACCOUNT.remove.done.title);
    expect(heldOf(tab)).toEqual(NO_SEARCH);
  });

  test("test_a_sign_out_that_failed_leaves_the_search_of_the_tab_as_it_was", async () => {
    const { user, tab } = await withASearchOpenInTheTab(standInAccounts(held({ signedIn: true })).unreachable("sign_out"));
    const before = heldOf(tab);

    await user.click(screen.getByRole("button", { name: ACCOUNT.sessions.signOutHere }));
    await arrived();

    // The person is signed in still, so the search is theirs still.
    expect(theHeading()).toHaveTextContent(ACCOUNT.title);
    expect(heldOf(tab)).toEqual(before);
    expect(before[0]).toBe("results");
  });
});

describe("what the page keeps", () => {
  test("test_nothing_of_the_account_is_put_in_an_address_or_in_anything_the_browser_keeps", async () => {
    const watching = watch();
    try {
      noteSignedIn(`${CANARY}@example.org`);
      const { to, user } = await opened({ email: `${CANARY}@example.org` });
      const at = window.location.href;

      await user.click(screen.getByRole("checkbox", { name: ACCOUNT.recent.keep(10) }));
      await arrived();
      await user.click(screen.getByRole("button", { name: of(ACCOUNT.searches.remove, to.held.searches[0]?.name ?? "") }));
      await arrived();
      await user.click(screen.getByRole("button", { name: ACCOUNT.remove.ask }));
      await user.click(screen.getByRole("button", { name: ACCOUNT.remove.no }));

      expect([watching.storage, watching.console, watching.history]).toEqual([[], [], []]);
      expect(watching.everythingOutsideThePage().includes(CANARY)).toBe(false);
      expect(watching.ids().includes(CANARY)).toBe(false);
      expect([window.location.href === at, document.title.includes(CANARY), led]).toEqual([true, false, []]);
      expect(to.calls.filter((call) => call.url.includes(CANARY) || JSON.stringify([...call.headers]).includes(CANARY))).toEqual([]);
    } finally {
      watching.stop();
    }
  });
});
