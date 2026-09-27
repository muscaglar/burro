/**
 * Opening a shared link, held to docs/design/web.md section 2: the id is
 * read from the fragment, sent in the path of one call, and the page says
 * what a share holds and how this one may differ from what its sender saw.
 */

import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import SharedPage from "@/app/s/page";
import { SearchApp } from "@/components/SearchApp/SearchApp";
import { NOTICE_STANDS } from "@/components/SharedSearch/look";
import { SharedSearch } from "@/components/SharedSearch/SharedSearch";
import { SHOWN_AT_FIRST } from "@/components/ResultList/ResultList";
import { Shell } from "@/components/Shell/Shell";
import { Town } from "@/components/Town/Town";
import { HELPERS } from "@/content/helpers";
import { MAP } from "@/content/map";
import { CHIPS, PROMPT, RESULTS, SEARCH, TENURE_CHOICE } from "@/content/search";
import { SETTINGS } from "@/content/settings";
import { SHARE, SHARED } from "@/content/share";
import { BANNER } from "@/content/site";
import { WAYS } from "@/content/ways";
import { readRecorded, recordedAnswer, recordedError } from "@/lib/api/recorded";
import type { Meta, Operations } from "@/lib/api/schema";
import { bandsToDraw } from "@/lib/holds";
import { edits } from "@/lib/search/edits";

import { reasonsFor, setOnline, standInApi, type StandIn } from "../support/api";
import { faultsIn } from "../support/axe";
import {
  areas,
  arrived,
  bands,
  CANARY,
  everyChip,
  everyResult,
  firstSearch,
  meta,
  narrowAgain,
  openSearch,
  removeChip,
  results,
  search,
  settingsAt,
  settled,
  setWide,
  theSettings,
  theSettingsIfAny,
  waysIfAny,
  whatRefines,
} from "../support/search";
import { watch } from "../support/watch";
import { focusGoesOnlyToWhatIsDrawn } from "../access/drawn";

jest.mock("next/navigation", () => ({ usePathname: () => "/s" }));

const opened = recordedAnswer("get_share", "share-opened");
const stale = recordedAnswer("get_share", "share-opened-stale");
const ID = opened.request.path.split("/").pop() ?? "";
const STALE_ID = stale.request.path.split("/").pop() ?? "";

/** The reasons of the search a share holds, as they were recorded, said to be for the spec that share holds. */
const reasonsOf = (scenario: string) =>
  scenario.startsWith("share-opened") ? reasonsFor(scenario, "explanations-share-opened") : "explanations-share-opened";

/** The service that answers a share, which names the release it holds in every answer it gives. */
const sharing = (scenario = "share-opened") =>
  standInApi()
    .movedTo((readRecorded(scenario).body as { meta: Meta }).meta.release_id)
    .on("get_share", scenario)
    .on("explain_top", reasonsOf(scenario));

/** Puts the browser at the page a shared link opens, with what follows the `#` of the link. */
function goTo(fragment: string | null) {
  window.location.hash = fragment ?? "";
}

/**
 * What says that the search came from a link. Where it stands behind a way to it, as it
 * does where it stands after the first result, the way is pressed first, as a person would.
 */
async function theNotice(user: ReturnType<typeof userEvent.setup> = userEvent.setup({ delay: null })): Promise<HTMLElement> {
  const way = screen.queryByRole("button", { name: SHARED.title });
  if (way !== null && way.getAttribute("aria-expanded") === "false") await user.click(way);
  return screen.getByRole("region", { name: SHARED.title });
}

async function open(fragment: string | null, api: StandIn = sharing()) {
  goTo(fragment);
  const user = userEvent.setup({ delay: null });
  const view = render(
    <Shell meta={meta.meta}>
      <SharedSearch meta={meta.data} areas={areas} bands={bands} client={api.client} />
    </Shell>,
  );
  await arrived();
  return { api, user, ...view };
}

beforeEach(() => {
  setOnline(true);
  focusGoesOnlyToWhatIsDrawn();
  window.history.replaceState(null, "", "/s");
});
afterEach(() => {
  window.history.replaceState(null, "", "/");
  narrowAgain();
});

describe("opening a shared link", () => {
  test("test_the_share_is_asked_for_by_the_id_in_the_fragment", async () => {
    const { api } = await open(ID);
    await settled();

    expect(api.callsTo("get_share").map((call) => call.path)).toEqual([`/v1/shares/${ID}`]);
    expect(api.lastCallTo("get_share").method).toBe("GET");
    expect(api.lastCallTo("get_share").url.includes("?")).toBe(false);
  });

  test("test_the_page_shows_the_shared_search_ranked_now_under_its_own_heading", async () => {
    await open(ID);
    await settled();

    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(SHARED.title);
    expect(results()).toHaveLength(SHOWN_AT_FIRST);
    await everyResult(userEvent.setup({ delay: null }));
    expect(results()).toHaveLength(opened.body.data.ranked.length);
    const first = areas.find((area) => area.area_id === opened.body.data.ranked[0]?.area_id);
    expect(results()[0]).toHaveTextContent(first?.name ?? "no name");
  });

  test("test_the_settings_of_the_shared_search_are_shown_as_chips", async () => {
    const { user } = await open(ID);
    await settled();
    await everyChip(user);

    // No words were read into a shared search, so it is not said to have been understood.
    const chips = within(screen.getByRole("region", { name: CHIPS.setLabel }));

    expect(chips.getByText("Leafy")).toBeInTheDocument();
    expect(chips.getByText("Quiet streets")).toBeInTheDocument();
    expect(chips.getByText("£1,700 a month")).toBeInTheDocument();
  });

  test("test_the_page_says_what_a_share_holds_and_that_places_are_stood_in_for", async () => {
    const { user } = await open(ID);
    await settled();

    const header = await theNotice(user);

    expect(header).toHaveTextContent(SHARED.text);
    expect(header).toHaveTextContent(SHARED.holds);
    expect(SHARED.holds).toMatch(/not what was typed/);
    expect(SHARED.holds).toMatch(/station or district/);
    expect(SHARED.holds).toMatch(/unless the sender chose to share the exact places/);
  });

  test("test_a_share_whose_places_were_replaced_says_the_ranking_may_differ", async () => {
    const { user } = await open(ID);
    await settled();
    const header = await theNotice(user);

    expect(opened.body.data.coarsened).toBe(true);
    expect(header).toHaveTextContent(SHARED.coarsened);
    expect(header).not.toHaveTextContent(SHARED.exact);
    expect(header).not.toHaveTextContent(SHARED.stale);
  });

  test("test_a_share_made_on_older_data_says_so_and_names_both_releases", async () => {
    const { user } = await open(STALE_ID, sharing("share-opened-stale"));
    await settled();

    const header = await theNotice(user);

    expect(stale.body.data.stale).toBe(true);
    expect(header).toHaveTextContent(SHARED.stale);
    expect(header).toHaveTextContent(`${SHARED.madeOn} ${stale.body.data.original_release_id}`);
    // It is shown on the release that ranked it, which the answer names, and not on the
    // one the page was built on: they are two, and that is why the share is stale.
    expect(stale.body.meta.release_id).not.toBe(stale.body.data.original_release_id);
    expect(header).toHaveTextContent(`${SHARED.shownOn} ${stale.body.meta.release_id}`);
    expect(header).not.toHaveTextContent(SHARED.coarsened);
  });

  test("test_a_stale_share_names_the_release_that_ranked_it_when_the_form_could_not_be_read_again", async () => {
    // The page keeps the form it was built with. The ranking is still the newer release's.
    const { user } = await open(STALE_ID, sharing("share-opened-stale").on("get_meta", "error-internal"));
    await settled();

    const header = await theNotice(user);
    expect(header).toHaveTextContent(`${SHARED.shownOn} ${stale.body.meta.release_id}`);
    expect(header).not.toHaveTextContent(`${SHARED.shownOn} ${meta.meta.release_id}`);
  });

  test("test_a_share_whose_places_were_kept_says_they_are_the_ones_the_sender_named", async () => {
    const { user } = await open(STALE_ID, sharing("share-opened-stale"));
    await settled();

    expect(stale.body.data.coarsened).toBe(false);
    expect(stale.body.data.spec.commutes).toHaveLength(1);
    expect(await theNotice(user)).toHaveTextContent(SHARED.exact);
  });

  test("test_a_share_with_no_place_says_nothing_of_places_being_kept_or_replaced", async () => {
    const api = sharing().on("get_share", () => ({
      ...stale,
      body: { ...stale.body, data: { ...stale.body.data, spec: { ...stale.body.data.spec, commutes: [] } } },
    }));
    const { user } = await open(STALE_ID, api);
    await settled();

    const header = await theNotice(user);
    expect(header).not.toHaveTextContent(SHARED.exact);
    expect(header).not.toHaveTextContent(SHARED.coarsened);
  });

  test("test_what_a_share_holds_is_said_while_it_is_being_opened", async () => {
    const api = standInApi();
    const held = api.hold("get_share", "share-opened");
    api.on("explain_top", "explanations-share-opened");
    await open(ID, api);

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(SHARED.title);
    expect(screen.getByRole("main")).toHaveTextContent(SHARED.holds);
    expect(screen.getByRole("status")).toHaveTextContent(SHARED.opening);
    expect(screen.queryByRole("list", { name: RESULTS.listLabel })).toBeNull();

    held.release();
    await settled();
    expect(results()).toHaveLength(SHOWN_AT_FIRST);
  });

  test("test_a_shared_search_can_be_refined_and_the_edit_goes_with_the_shares_spec", async () => {
    const { api, user } = await open(ID);
    await settled();
    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");

    await removeChip(user, "Leafy");
    await settled();

    const sent = api.lastCallTo("rank").body as { spec: unknown; operations: Operations };
    expect(sent.spec).toEqual(opened.body.data.spec);
    expect(sent.operations.tag_ops).toHaveLength(1);
    // It still says where it came from, and that changing it does not change the link.
    expect(await theNotice(user)).toHaveTextContent(SHARED.text);
  });

  test("test_a_link_that_is_already_open_is_not_opened_again_over_what_was_changed", async () => {
    const { api, user, rerender } = await open(ID);
    await settled();
    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");
    await removeChip(user, "Leafy");
    await settled();

    // The person reads another page and comes back to the link.
    rerender(<Shell meta={meta.meta}>{null}</Shell>);
    rerender(
      <Shell meta={meta.meta}>
        <SharedSearch meta={meta.data} areas={areas} client={api.client} />
      </Shell>,
    );
    await settled();

    expect(api.callsTo("get_share")).toHaveLength(1);
    // The journey was made a firm limit after the share was opened, and it still is.
    expect(opened.body.data.spec.commutes[0]?.strictness).toBe("soft");
    expect(screen.getByRole("region", { name: CHIPS.setLabel })).toHaveTextContent(CHIPS.firm);
  });

  test("test_another_link_followed_in_the_same_tab_opens_the_other_share", async () => {
    const api = standInApi()
      .inTurn("get_share", "share-opened", "share-opened-stale")
      .on("explain_top", "explanations-share-opened");
    await open(ID, api);
    await settled();

    await act(async () => {
      window.location.hash = `#${STALE_ID}`;
      window.dispatchEvent(new HashChangeEvent("hashchange"));
    });
    await settled();

    expect(api.callsTo("get_share").map((call) => call.path)).toEqual([
      `/v1/shares/${ID}`,
      `/v1/shares/${STALE_ID}`,
    ]);
    expect(await theNotice()).toHaveTextContent(SHARED.stale);
  });
});

describe("an opened share, laid out as the search page is", () => {
  const comesBefore = (one: Element, other: Element) =>
    Boolean(one.compareDocumentPosition(other) & Node.DOCUMENT_POSITION_FOLLOWING);
  const chips = () => screen.getByRole("region", { name: CHIPS.setLabel });

  test.each([false, true])(
    "test_the_settings_of_a_shared_search_are_one_fold_closed_at_first_on_a_screen_of_any_width: wide %s",
    async (wide) => {
      // From 80rem they stood open beside the shared search, and under it behind a button
      // after the first result. No column of settings stands open since: they are one part,
      // which refines the search, closed until it is pressed, whatever the width.
      const asked = setWide(wide);
      await open(ID);
      await settled();

      // The page asks the browser no width: where its parts stand is its style sheet's to say.
      expect(asked.filter((query) => /width/.test(query))).toEqual([]);
      expect(theSettingsIfAny()).toBeNull();
      expect(screen.queryByRole("button", { name: SETTINGS.title })).toBeNull();
      const refine = whatRefines() as HTMLElement;
      expect(refine).toHaveAttribute("aria-expanded", "false");
      // The answer comes first: what the search holds, the way to refine it, which is one
      // stop while it is closed, the first result, and then the map and the rest. What says
      // that the search was shared stands where the one line says: over it all, in one line,
      // or one press away after the first result, beside the way to share a search.
      const [one, two] = results();
      if (NOTICE_STANDS === "over") {
        expect(comesBefore(screen.getByRole("region", { name: SHARED.title }), chips())).toBe(true);
      } else {
        expect(screen.queryByRole("region", { name: SHARED.title })).toBeNull();
        const share = screen.getByRole("button", { name: SHARE.open });
        const way = screen.getByRole("button", { name: SHARED.title });
        expect(comesBefore(one as HTMLElement, share)).toBe(true);
        expect(comesBefore(share, way)).toBe(true);
        expect(comesBefore(way, two as HTMLElement)).toBe(true);
      }
      const map = screen.getByRole("region", { name: MAP.label });
      expect(comesBefore(chips(), refine)).toBe(true);
      expect(comesBefore(refine, one as HTMLElement)).toBe(true);
      expect(comesBefore(one as HTMLElement, map)).toBe(true);
      expect(comesBefore(map, two as HTMLElement)).toBe(true);
      // Nothing that is pressed stands between the way to refine and the first result.
      const between = [...document.querySelectorAll<HTMLElement>("a[href], button, input, select, textarea")].filter(
        (control) => comesBefore(refine, control) && comesBefore(control, one as HTMLElement),
      );
      expect(between.map((control) => control.textContent)).toEqual([]);
    },
  );

  test.each([false, true])(
    "test_the_settings_of_a_shared_search_change_the_search_that_was_shared_and_stay_open_under_the_hand: wide %s",
    async (wide) => {
      setWide(wide);
      const { api, user } = await open(ID);
      await settled();
      api.on("rank", "rank-refined").on("explain_top", "explanations-refined");

      await settingsAt(user, SETTINGS.money);
      const buying = within(theSettings()).getByRole("radio", { name: TENURE_CHOICE.buy });
      await user.click(buying);
      await settled();

      expect(api.lastCallTo("rank").body).toMatchObject({
        spec: opened.body.data.spec,
        operations: edits.tenure("buy"),
      });
      // What was pressed is where it was, with the focus, in the settings that are open still.
      expect(whatRefines()).toHaveAttribute("aria-expanded", "true");
      expect(within(theSettings()).getByRole("radio", { name: TENURE_CHOICE.buy })).toHaveFocus();
      expect(within(theSettings()).getByRole("button", { name: SETTINGS.money })).toHaveAttribute("aria-expanded", "true");
    },
  );

  test("test_a_shared_search_is_open_so_no_way_in_and_no_helper_is_drawn_at_any_width", async () => {
    for (const wide of [false, true]) {
      setWide(wide);
      const { unmount } = await open(ID);
      await settled();

      // The two tabs and the helpers under the first are for beginning, and this search has begun.
      expect(waysIfAny()).toBeNull();
      expect(screen.queryAllByRole("tab")).toEqual([]);
      expect(screen.queryAllByRole("tabpanel")).toEqual([]);
      expect(screen.queryByRole("group", { name: HELPERS.label })).toBeNull();
      for (const name of [HELPERS.example, HELPERS.word, WAYS.quick, WAYS.deep]) {
        expect(screen.queryByRole("button", { name })).toBeNull();
      }
      unmount();
    }
  });

  test.each([false, true])("test_an_opened_share_has_no_accessibility_fault_with_a_wide_screen: %s", async (wide) => {
    setWide(wide);
    const { container, user } = await open(ID);
    await settled();

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
    // With the settings opened too, and a group of them open: whichever groups stand open at
    // first, which is the settings' own to say, one is opened here unless it is open already.
    await settingsAt(user, SETTINGS.money);
    expect(within(theSettings()).getByRole("button", { name: SETTINGS.money })).toHaveAttribute("aria-expanded", "true");
    expect(within(theSettings()).getAllByRole("button", { expanded: true }).length).toBeGreaterThan(0);
    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });
});

describe("a shared search, begun again", () => {
  // What has the focus is said as a yes or a no: a test that fails must not print the page.
  const onNothing = () => document.activeElement === null || document.activeElement === document.body;
  const inTheBox = () => document.activeElement === screen.getByRole("textbox", { name: PROMPT.labelOpen });
  const onWhatItHolds = () => document.activeElement === screen.getByRole("region", { name: CHIPS.setLabel });

  test("test_start_again_opens_the_share_as_the_link_holds_it_and_the_focus_is_never_left_on_nothing", async () => {
    // Seen in a browser: the search went with the press, the box that had taken the focus
    // went with it, and the focus was left on nothing while the share was opened again and after.
    const { api, user } = await open(ID);
    await settled();
    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");
    await removeChip(user, "Leafy");
    await settled();
    const again = api.hold("get_share", "share-opened");
    api.on("explain_top", reasonsOf("share-opened"));

    await user.click(screen.getByRole("button", { name: PROMPT.startAgain }));

    // While the share is opened again the focus is where it is being opened.
    const opening = screen.getByRole("status");
    expect(opening.textContent).toBe(SHARED.opening);
    expect(onNothing()).toBe(false);
    expect(document.activeElement?.getAttribute("tabindex")).toBe("-1");
    expect(document.activeElement?.contains(opening)).toBe(true);

    again.release();
    await settled();

    // The search is as the link holds it, and the focus is on what it holds, which is what
    // the press changed. It is not in the box: the box makes room while it has the focus,
    // and the first result stood 45 px lower for it, which on a phone is off the first screen.
    expect(api.callsTo("get_share")).toHaveLength(2);
    expect(onWhatItHolds()).toBe(true);
    expect(inTheBox()).toBe(false);
    expect(screen.getByRole("textbox", { name: PROMPT.labelOpen }).getAttribute("data-tall")).toBe("false");
    await everyChip(user);
    expect(within(screen.getByRole("region", { name: CHIPS.setLabel })).queryByText("Leafy")).not.toBeNull();
  });

  test("test_a_share_that_opens_of_itself_takes_the_focus_from_nobody", async () => {
    // A page that opens takes no focus: a person begins at its head, as on any page.
    await open(ID);
    await settled();

    expect(results()).toHaveLength(SHOWN_AT_FIRST);
    expect(onNothing()).toBe(true);
  });

  test("test_a_share_that_opens_once_it_was_tried_again_hands_the_focus_to_what_it_holds", async () => {
    // The button that tries again goes with the failure, and what holds the place of the
    // search goes as the search opens: the focus is handed on each time.
    const { api, user } = await open(ID, sharing("error-internal"));
    const alert = await screen.findByRole("alert");
    api.on("get_share", "share-opened");

    await user.click(within(alert).getByRole("button", { name: SHARED.tryAgain }));
    await settled();

    expect(results()).toHaveLength(SHOWN_AT_FIRST);
    expect(onWhatItHolds()).toBe(true);
  });

  test("test_another_link_followed_in_the_same_tab_is_a_page_that_opens_and_takes_no_focus", async () => {
    const api = standInApi()
      .inTurn("get_share", "share-opened", "share-opened-stale")
      .on("explain_top", "explanations-share-opened");
    await open(ID, api);
    await settled();

    await act(async () => {
      window.location.hash = `#${STALE_ID}`;
      window.dispatchEvent(new HashChangeEvent("hashchange"));
    });
    await settled();

    expect(results()).toHaveLength(SHOWN_AT_FIRST);
    expect([inTheBox(), onWhatItHolds()]).toEqual([false, false]);
  });
});

describe("going back to a link", () => {
  test("test_going_back_to_a_link_in_the_same_tab_opens_it", async () => {
    const api = standInApi().on("get_share", "share-opened").on("explain_top", "explanations-share-opened");
    await open(null, api);
    expect(screen.getByRole("main")).toHaveTextContent(SHARED.none.title);

    // The browser goes back to an entry of its history that holds the link.
    await act(async () => {
      window.history.replaceState(null, "", `/s#${ID}`);
      window.dispatchEvent(new PopStateEvent("popstate"));
    });
    await settled();

    expect(api.callsTo("get_share").map((call) => call.path)).toEqual([`/v1/shares/${ID}`]);
    expect(results()).toHaveLength(SHOWN_AT_FIRST);
  });
});

describe("a link that leads nowhere", () => {
  test.each([
    ["share-not-found", 404],
    ["share-gone", 410],
  ])("test_the_apis_words_are_shown_and_asking_again_is_not_offered: %s", async (scenario, status) => {
    const failure = recordedError(scenario);
    const { api } = await open(ID, sharing(scenario));

    const alert = await screen.findByRole("alert");

    expect(failure.status).toBe(status);
    expect(alert).toHaveTextContent(SHARED.failedTitle);
    expect(alert).toHaveTextContent(failure.body.error.message);
    expect(within(alert).queryByRole("button", { name: SHARED.tryAgain })).toBeNull();
    expect(within(alert).getByRole("link", { name: SHARED.own })).toHaveAttribute("href", "/");
    expect(screen.queryByRole("list", { name: RESULTS.listLabel })).toBeNull();
    expect(api.callsTo("get_share")).toHaveLength(1);
    expect(api.callsTo("explain_top")).toHaveLength(0);
  });

  test("test_a_fault_can_be_tried_again_and_the_share_then_opens", async () => {
    const failure = recordedError("error-internal");
    const { api, user } = await open(ID, sharing("error-internal"));
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(failure.body.error.message);
    expect(alert).toHaveTextContent(failure.headers["x-request-id"] ?? "no id");

    api.on("get_share", "share-opened");
    await user.click(within(alert).getByRole("button", { name: SHARED.tryAgain }));
    await settled();

    expect(results()).toHaveLength(SHOWN_AT_FIRST);
    expect(screen.queryByRole("alert")).toBeNull();
    expect(api.callsTo("get_share")).toHaveLength(2);
  });

  test("test_a_share_that_cannot_be_reached_says_so_and_can_be_tried_again", async () => {
    await open(ID, standInApi().unreachable("get_share"));

    const alert = await screen.findByRole("alert");

    expect(alert).toHaveTextContent(SHARED.failedTitle);
    expect(within(alert).getByRole("button", { name: SHARED.tryAgain })).toHaveClass("target");
  });

  test("test_an_address_with_no_id_says_so_and_asks_for_nothing", async () => {
    const { api } = await open(null);

    expect(screen.getByRole("main")).toHaveTextContent(SHARED.none.title);
    expect(screen.getByRole("main")).toHaveTextContent(SHARED.none.text);
    expect(screen.getByRole("link", { name: SHARED.own })).toHaveAttribute("href", "/");
    expect(api.calls).toEqual([]);
  });

  test.each([
    "short",
    `${CANARY}`,
    `${ID}x`,
    `${ID.slice(0, 21)}!`,
    `${ID}/../meta`,
    `${ID}?text=${CANARY}`,
    encodeURIComponent(`leafy and quiet ${CANARY}`),
  ])("test_what_is_not_an_id_is_never_sent_anywhere_and_never_shown: %s", async (fragment) => {
    const watching = watch();
    try {
      const { api, container } = await open(fragment);

      expect(screen.getByRole("main")).toHaveTextContent(SHARED.notOne.title);
      expect(api.calls).toEqual([]);
      // What the address held is not repeated on the page, in a link, or anywhere else.
      expect(container.textContent?.includes(CANARY)).toBe(false);
      expect([...container.querySelectorAll("[href]")].filter((link) => link.getAttribute("href")?.includes(CANARY))).toEqual([]);
      expect(watching.console).toEqual([]);
      expect(watching.storage).toEqual([]);
    } finally {
      watching.stop();
    }
  });
});

describe("where the id of a share may be", () => {
  test("test_a_share_id_is_only_ever_in_the_fragment_and_in_the_one_call_that_opens_it", async () => {
    const watching = watch();
    try {
      const { api, user, container } = await open(ID);
      await settled();
      api.on("rank", "rank-refined").on("explain_top", "explanations-refined");
      await removeChip(user, "Leafy");
      await settled();
      // The settings are opened, and two groups of them, so that what they hold is on the page.
      await settingsAt(user, SETTINGS.money, SETTINGS.journeys);
      expect(within(theSettings()).getAllByRole("button", { expanded: true }).length).toBeGreaterThanOrEqual(2);

      // One call holds it, in its path. No body does, and no other address.
      const naming = api.calls.filter((call) => `${call.url} ${call.sent ?? ""}`.includes(ID));
      expect(naming.map((call) => `${call.method} ${call.path}`)).toEqual([`GET /v1/shares/${ID}`]);
      // The address of the page holds it in the fragment, where the link put it, and nowhere else.
      expect(window.location.pathname + window.location.search).toBe("/s");
      expect(window.location.hash).toBe(`#${ID}`);
      // Nothing the page draws holds it: no text, no link, no id of an element.
      expect(container.innerHTML.includes(ID)).toBe(false);
      expect(watching.ids().includes(ID)).toBe(false);
      expect(watching.history).toEqual([]);
      expect(watching.storage).toEqual([]);
      expect(watching.console).toEqual([]);
      expect(document.title.includes(ID)).toBe(false);
    } finally {
      watching.stop();
    }
  });

  test("test_the_page_is_built_the_same_for_every_link", async () => {
    goTo(ID);

    const built = await SharedPage();

    // The server is sent no fragment, so what it builds holds no id and no search.
    expect(JSON.stringify(built.props).includes(ID)).toBe(false);
    // It holds what the release holds, and no more: what a form needs, every area, and where
    // every area sits, which the town of a result is drawn from. None is of a search.
    expect(Object.keys(built.props).sort()).toEqual(["areas", "bands", "meta"]);
    expect(built.props.bands).toEqual(bandsToDraw(meta.data, bands));
    expect(JSON.stringify(built.props).includes(JSON.stringify(opened.body.data.spec))).toBe(false);
  });
});

describe("the town of a result, on the page a shared link opens", () => {
  const townOf = (result: Element) => result.querySelector("figure") as HTMLElement;
  const heardOf = (town: Element) => within(town as HTMLElement).getByRole("img").getAttribute("aria-label");
  const profileOf = (areaId: string) =>
    recordedAnswer("get_area", `area/${areas.find((area) => area.area_id === areaId)?.slug ?? ""}`).body.data;
  const nameOf = (areaId: string) => areas.find((area) => area.area_id === areaId)?.name ?? "";

  test("test_the_town_of_a_result_of_a_shared_search_is_the_town_of_the_page_of_its_area", async () => {
    // A strip holds what was asked for and two more, and a town is drawn from four vibes:
    // drawn from its strip, a town said of a part that it is not known, where the page of
    // the area draws it. The page is built with where every area sits, as the search page is.
    await open(ID);
    await settled();

    expect(results()).toHaveLength(SHOWN_AT_FIRST);
    results().forEach((result, at) => {
      const areaId = opened.body.data.ranked[at]?.area_id ?? "";
      const alone = render(<Town marks={profileOf(areaId).tags} meta={meta.data} of={nameOf(areaId)} />);
      const page = { heard: heardOf(alone.container), says: alone.container.querySelector("figcaption")?.textContent };
      alone.unmount();

      expect([at, heardOf(townOf(result))]).toEqual([at, page.heard]);
      expect([at, townOf(result).querySelector("figcaption")?.textContent]).toEqual([at, page.says]);
    });
  });
});

describe("an opened share, by keyboard and to a screen reader", () => {
  test("test_the_page_carries_the_banner_that_says_the_data_is_made_up", async () => {
    await open(ID);
    await settled();

    expect(screen.getByRole("region", { name: BANNER.label })).toHaveTextContent(BANNER.text);
  });

  test.each([
    ["opened", ID, "share-opened"],
    ["not found", ID, "share-not-found"],
    ["with no id", null, "share-opened"],
    ["with what is not an id", "nothing", "share-opened"],
  ])("test_a_share_%s_has_no_accessibility_fault", async (_, fragment, scenario) => {
    const { container } = await open(fragment, sharing(scenario));
    await waitFor(() => expect(container.querySelector("[aria-busy='true']")).toBeNull());
    await arrived();

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
  });

  test("test_a_search_the_person_began_does_not_say_it_is_a_shared_one", async () => {
    const { user } = await openSearch(firstSearch());
    await search(user);

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(SEARCH.title);
    expect(SEARCH.title).not.toBe(SHARED.title);
    expect(screen.queryByRole("region", { name: SHARED.title })).toBeNull();
    expect(screen.getByRole("main")).not.toHaveTextContent(SHARED.text);
  });

  test("test_a_shared_search_still_says_so_on_the_search_page_itself", async () => {
    const { api, rerender } = await open(ID);
    await settled();

    // The person follows the link in the header to the search page.
    rerender(
      <Shell meta={meta.meta}>
        <SearchApp meta={meta.data} areas={areas} client={api.client} />
      </Shell>,
    );
    await settled();

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(SEARCH.title);
    // Over the box the line that says so is a heading, since the heading of this page does
    // not say it. After the first result the way to it says so, as a button does.
    if (NOTICE_STANDS === "over") expect(screen.getByRole("heading", { level: 2, name: SHARED.title })).toBeInTheDocument();
    else expect(screen.getByRole("button", { name: SHARED.title })).toHaveAttribute("aria-expanded", "false");
    expect(await theNotice()).toHaveTextContent(SHARED.coarsened);
    expect(results()).toHaveLength(SHOWN_AT_FIRST);
    expect(api.callsTo("get_share")).toHaveLength(1);
  });
});
