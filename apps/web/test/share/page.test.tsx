/**
 * Opening a shared link, held to docs/design/web.md section 2: the id is
 * read from the fragment, sent in the path of one call, and the page says
 * what a share holds and how this one may differ from what its sender saw.
 */

import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import SharedPage from "@/app/s/page";
import { SearchApp } from "@/components/SearchApp/SearchApp";
import { SharedSearch } from "@/components/SharedSearch/SharedSearch";
import { Shell } from "@/components/Shell/Shell";
import { CHIPS, RESULTS, SEARCH } from "@/content/search";
import { SETTINGS } from "@/content/settings";
import { SHARED } from "@/content/share";
import { BANNER } from "@/content/site";
import { readRecorded, recordedAnswer, recordedError } from "@/lib/api/recorded";
import type { Meta, Operations } from "@/lib/api/schema";

import { setOnline, standInApi, type StandIn } from "../support/api";
import { faultsIn } from "../support/axe";
import { areas, arrived, CANARY, firstSearch, meta, openSearch, results, search, settled } from "../support/search";
import { watch } from "../support/watch";

jest.mock("next/navigation", () => ({ usePathname: () => "/s" }));

const opened = recordedAnswer("get_share", "share-opened");
const stale = recordedAnswer("get_share", "share-opened-stale");
const ID = opened.request.path.split("/").pop() ?? "";
const STALE_ID = stale.request.path.split("/").pop() ?? "";

/** The service that answers a share, which names the release it holds in every answer it gives. */
const sharing = (scenario = "share-opened") =>
  standInApi()
    .movedTo((readRecorded(scenario).body as { meta: Meta }).meta.release_id)
    .on("get_share", scenario)
    .on("explain_top", "explanations-first");

/** Puts the browser at the page a shared link opens, with what follows the `#` of the link. */
function goTo(fragment: string | null) {
  window.location.hash = fragment ?? "";
}

async function open(fragment: string | null, api: StandIn = sharing()) {
  goTo(fragment);
  const user = userEvent.setup({ delay: null });
  const view = render(
    <Shell meta={meta.meta}>
      <SharedSearch meta={meta.data} areas={areas} client={api.client} />
    </Shell>,
  );
  await arrived();
  return { api, user, ...view };
}

beforeEach(() => {
  setOnline(true);
  window.history.replaceState(null, "", "/s");
});
afterEach(() => window.history.replaceState(null, "", "/"));

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
    expect(results()).toHaveLength(opened.body.data.ranked.length);
    const first = areas.find((area) => area.area_id === opened.body.data.ranked[0]?.area_id);
    expect(results()[0]).toHaveTextContent(first?.name ?? "no name");
  });

  test("test_the_settings_of_the_shared_search_are_shown_as_chips", async () => {
    await open(ID);
    await settled();

    // No words were read into a shared search, so it is not said to have been understood.
    const chips = within(screen.getByRole("region", { name: CHIPS.setLabel }));

    expect(chips.getByText("Leafy")).toBeInTheDocument();
    expect(chips.getByText("Quiet residential")).toBeInTheDocument();
    expect(chips.getByText("£1,700 a month")).toBeInTheDocument();
  });

  test("test_the_page_says_what_a_share_holds_and_that_places_are_stood_in_for", async () => {
    await open(ID);
    await settled();

    const header = screen.getByRole("region", { name: SHARED.title });

    expect(header).toHaveTextContent(SHARED.text);
    expect(header).toHaveTextContent(SHARED.holds);
    expect(SHARED.holds).toMatch(/not what was typed/);
    expect(SHARED.holds).toMatch(/station or district/);
    expect(SHARED.holds).toMatch(/unless the sender chose to share the exact places/);
  });

  test("test_a_share_whose_places_were_replaced_says_the_ranking_may_differ", async () => {
    await open(ID);
    await settled();

    expect(opened.body.data.coarsened).toBe(true);
    expect(screen.getByRole("region", { name: SHARED.title })).toHaveTextContent(SHARED.coarsened);
    expect(screen.getByRole("region", { name: SHARED.title })).not.toHaveTextContent(SHARED.exact);
    expect(screen.getByRole("region", { name: SHARED.title })).not.toHaveTextContent(SHARED.stale);
  });

  test("test_a_share_made_on_older_data_says_so_and_names_both_releases", async () => {
    await open(STALE_ID, sharing("share-opened-stale"));
    await settled();

    const header = screen.getByRole("region", { name: SHARED.title });

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
    await open(STALE_ID, sharing("share-opened-stale").on("get_meta", "error-internal"));
    await settled();

    const header = screen.getByRole("region", { name: SHARED.title });
    expect(header).toHaveTextContent(`${SHARED.shownOn} ${stale.body.meta.release_id}`);
    expect(header).not.toHaveTextContent(`${SHARED.shownOn} ${meta.meta.release_id}`);
  });

  test("test_a_share_whose_places_were_kept_says_they_are_the_ones_the_sender_named", async () => {
    await open(STALE_ID, sharing("share-opened-stale"));
    await settled();

    expect(stale.body.data.coarsened).toBe(false);
    expect(stale.body.data.spec.commutes).toHaveLength(1);
    expect(screen.getByRole("region", { name: SHARED.title })).toHaveTextContent(SHARED.exact);
  });

  test("test_a_share_with_no_place_says_nothing_of_places_being_kept_or_replaced", async () => {
    const api = sharing().on("get_share", () => ({
      ...stale,
      body: { ...stale.body, data: { ...stale.body.data, spec: { ...stale.body.data.spec, commutes: [] } } },
    }));
    await open(STALE_ID, api);
    await settled();

    const header = screen.getByRole("region", { name: SHARED.title });
    expect(header).not.toHaveTextContent(SHARED.exact);
    expect(header).not.toHaveTextContent(SHARED.coarsened);
  });

  test("test_what_a_share_holds_is_said_while_it_is_being_opened", async () => {
    const api = standInApi();
    const held = api.hold("get_share", "share-opened");
    api.on("explain_top", "explanations-first");
    await open(ID, api);

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(SHARED.title);
    expect(screen.getByRole("main")).toHaveTextContent(SHARED.holds);
    expect(screen.getByRole("status")).toHaveTextContent(SHARED.opening);
    expect(screen.queryByRole("list", { name: RESULTS.listLabel })).toBeNull();

    held.release();
    await settled();
    expect(results()).toHaveLength(20);
  });

  test("test_a_shared_search_can_be_refined_and_the_edit_goes_with_the_shares_spec", async () => {
    const { api, user } = await open(ID);
    await settled();
    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");

    await user.click(screen.getByRole("button", { name: `${CHIPS.remove}: Leafy` }));
    await settled();

    const sent = api.lastCallTo("rank").body as { spec: unknown; operations: Operations };
    expect(sent.spec).toEqual(opened.body.data.spec);
    expect(sent.operations.tag_ops).toHaveLength(1);
    // It still says where it came from, and that changing it does not change the link.
    expect(screen.getByRole("region", { name: SHARED.title })).toHaveTextContent(SHARED.text);
  });

  test("test_a_link_that_is_already_open_is_not_opened_again_over_what_was_changed", async () => {
    const { api, user, rerender } = await open(ID);
    await settled();
    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");
    await user.click(screen.getByRole("button", { name: `${CHIPS.remove}: Leafy` }));
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
      .on("explain_top", "explanations-first");
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
    expect(screen.getByRole("region", { name: SHARED.title })).toHaveTextContent(SHARED.stale);
  });
});

describe("going back to a link", () => {
  test("test_going_back_to_a_link_in_the_same_tab_opens_it", async () => {
    const api = standInApi().on("get_share", "share-opened").on("explain_top", "explanations-first");
    await open(null, api);
    expect(screen.getByRole("main")).toHaveTextContent(SHARED.none.title);

    // The browser goes back to an entry of its history that holds the link.
    await act(async () => {
      window.history.replaceState(null, "", `/s#${ID}`);
      window.dispatchEvent(new PopStateEvent("popstate"));
    });
    await settled();

    expect(api.callsTo("get_share").map((call) => call.path)).toEqual([`/v1/shares/${ID}`]);
    expect(results()).toHaveLength(20);
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

    expect(results()).toHaveLength(20);
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
      await user.click(screen.getByRole("button", { name: `${CHIPS.remove}: Leafy` }));
      await settled();
      await user.click(screen.getByRole("button", { name: SETTINGS.title }));

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
    expect(Object.keys(built.props).sort()).toEqual(["areas", "meta"]);
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
    expect(screen.getByRole("heading", { level: 2, name: SHARED.title })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: SHARED.title })).toHaveTextContent(SHARED.coarsened);
    expect(results()).toHaveLength(20);
    expect(api.callsTo("get_share")).toHaveLength(1);
  });
});
