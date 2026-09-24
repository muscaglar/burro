/**
 * What a comparison and a share may hold, and where. docs/design/web.md,
 * section 10.
 *
 * A canary, a string found nowhere else, is planted in the sentence, in the
 * place search and in the name of a place. The run then makes a search,
 * chooses areas to compare, makes a link twice, copies it, and opens the
 * comparison. Each test looks at one place something could have leaked to.
 */

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactElement } from "react";

import { CompareView } from "@/components/CompareTable/CompareView";
import { SearchApp } from "@/components/SearchApp/SearchApp";
import { Shell } from "@/components/Shell/Shell";
import { COMPARE, TRAY } from "@/content/compare";
import { PLACE } from "@/content/search";
import { SHARE } from "@/content/share";
import { recordedAnswer, responseFrom } from "@/lib/api/recorded";
import type { FoundPlace, PreferenceSpec } from "@/lib/api/schema";
import { chosenFrom } from "@/lib/compare/list";

import { BASE, setOnline, type StandIn } from "../support/api";
import { areas, arrived, CANARY, firstSearch, meta, search, settled } from "../support/search";
import { watch, type Watch } from "../support/watch";

jest.mock("next/navigation", () => ({ usePathname: () => "/" }));

const PLACE_NAME = `Zqxplace ${CANARY} Works`;
const PLACE_ID = "syn-p0777";
const made = recordedAnswer("create_share", "share-made").body.data;
const ranked = recordedAnswer("rank", "rank-first");

/** The spec the search holds once the place has been picked, as the API would return it. */
const withThePlace: PreferenceSpec = {
  ...ranked.body.data.spec,
  commutes: ranked.body.data.spec.commutes.map((commute) => ({ ...commute, place_id: PLACE_ID })),
};

function standIn(): StandIn {
  const places = recordedAnswer("search_places", "places-search");
  const found: FoundPlace = { place_id: PLACE_ID, name: PLACE_NAME, kind: "landmark", coarse_name: PLACE_NAME };
  return firstSearch()
    .on("search_places", () => responseFrom({ ...places, body: { ...places.body, data: { places: [found] } } }))
    .on("create_share", "share-made")
    .on("compare", "compare-two-defaults");
}

const inShell = (page: ReactElement) => <Shell meta={meta.meta}>{page}</Shell>;

interface Seen {
  readonly calls: StandIn["calls"];
  readonly watched: Pick<Watch, "console" | "storage" | "history">;
  readonly addresses: string;
  readonly address: string;
  readonly title: string;
  /** The link as the panel showed it, each time one was made. */
  readonly links: readonly string[];
  readonly copied: readonly string[];
  /** Every address a link on the page led to, while the link to the share was on it. */
  readonly hrefs: readonly string[];
  readonly compareLink: string;
  /** The markup of the page while the link was on it, with the field that holds the link taken out. */
  readonly pageWithoutTheField: string;
}

let seen: Seen;

beforeAll(async () => {
  setOnline(true);
  const copied: string[] = [];
  const watching = watch();
  try {
    const api = standIn();
    const user = userEvent.setup({ delay: null });
    // Put in place after the stand-in for a person is, which brings a clipboard of its own.
    Object.defineProperty(window.navigator, "clipboard", {
      configurable: true,
      value: { writeText: async (text: string) => void copied.push(text) },
    });
    const view = render(inShell(<SearchApp meta={meta.data} areas={areas} client={api.client} />));
    await arrived();

    // A sentence with the canary in it, and a place with the canary in its name.
    await search(user, `leafy and quiet, near ${CANARY}`);
    api.on("rank", () =>
      responseFrom({ ...ranked, body: { ...ranked.body, data: { ...ranked.body.data, spec: withThePlace } } }),
    );
    await user.type(screen.getAllByRole("combobox", { name: PLACE.label })[0] as HTMLElement, CANARY);
    await user.click(await screen.findByRole("option", { name: new RegExp(CANARY) }));
    await settled();

    // Two areas to compare.
    const [one, two] = ranked.body.data.ranked.map((area) => areas.find((known) => known.area_id === area.area_id));
    await user.click(screen.getByRole("button", { name: COMPARE.add(one?.name ?? "") }));
    await user.click(screen.getByRole("button", { name: COMPARE.add(two?.name ?? "") }));
    const compareLink =
      within(screen.getByRole("region", { name: TRAY.title })).getByRole("link").getAttribute("href") ?? "";

    // A link, made as it is offered, and copied. Then one that keeps the exact places.
    await user.click(screen.getByRole("button", { name: SHARE.open }));
    await user.click(screen.getByRole("button", { name: SHARE.make }));
    const field = () => screen.findByRole<HTMLInputElement>("textbox", { name: SHARE.link });
    const links = [(await field()).value];
    await user.click(screen.getByRole("button", { name: SHARE.copy }));
    const hrefs = [...document.querySelectorAll("[href]")].map((link) => link.getAttribute("href") ?? "");
    const page = document.body.cloneNode(true) as HTMLElement;
    page.querySelectorAll("input, textarea").forEach((one) => one.remove());
    await user.click(screen.getByRole("checkbox", { name: SHARE.exact.label }));
    await user.click(screen.getByRole("button", { name: SHARE.makeAgain }));
    await screen.findByText(SHARE.made);
    links.push((await field()).value);

    // The comparison, which the link in the tray leads to.
    view.rerender(
      inShell(
        <CompareView
          chosen={chosenFrom([one?.slug ?? "", two?.slug ?? ""], areas).chosen}
          defaults={meta.data.defaults}
          client={api.client}
        />,
      ),
    );
    await arrived();

    seen = {
      calls: api.calls,
      watched: { console: [...watching.console], storage: [...watching.storage], history: [...watching.history] },
      addresses: watching.addresses(),
      address: window.location.href,
      title: document.title,
      links,
      copied,
      hrefs,
      compareLink,
      pageWithoutTheField: page.innerHTML,
    };
  } finally {
    watching.stop();
    Reflect.deleteProperty(window.navigator, "clipboard");
  }
});

const callsTo = (operation: string) => seen.calls.filter((call) => call.operation === operation);

describe("what a share holds", () => {
  test("test_the_run_that_was_watched_made_a_search_two_links_and_a_comparison", () => {
    expect(callsTo("interpret")).toHaveLength(1);
    expect(callsTo("create_share")).toHaveLength(2);
    expect(callsTo("compare")).toHaveLength(1);
    expect(seen.links).toHaveLength(2);
    // The place was picked, so the search that was shared holds its id.
    expect(callsTo("create_share").every((call) => call.sent?.includes(PLACE_ID))).toBe(true);
  });

  test("test_nothing_the_person_typed_is_in_the_link", () => {
    for (const link of seen.links) {
      const address = new URL(link);
      expect(link.includes(CANARY)).toBe(false);
      expect(/syn-p\d+/.test(link)).toBe(false);
      expect(address.pathname).toBe("/s");
      expect(address.search).toBe("");
      // The fragment is the id the API made at random, and nothing else.
      expect(address.hash).toBe(`#${made.share_id}`);
      expect(address.origin).toBe(window.location.origin);
    }
  });

  test("test_a_share_is_made_of_the_spec_the_api_returned_and_never_of_the_words", () => {
    const bodies = callsTo("create_share").map((call) => call.body as Record<string, unknown>);

    expect(bodies.map((body) => Object.keys(body).sort())).toEqual([
      ["exact_destinations", "spec"],
      ["exact_destinations", "spec"],
    ]);
    expect(bodies.map((body) => body.spec)).toEqual([withThePlace, withThePlace]);
    for (const call of callsTo("create_share")) expect(call.sent?.includes(CANARY)).toBe(false);
  });

  test("test_the_exact_places_are_shared_only_when_the_box_is_ticked", () => {
    expect(
      callsTo("create_share").map((call) => (call.body as { exact_destinations: boolean }).exact_destinations),
    ).toEqual([false, true]);
  });

  test("test_a_share_id_is_only_ever_in_the_fragment", () => {
    // No call holds the id: it was made by the API, and nothing sends it back.
    const naming = seen.calls.filter((call) => `${call.url} ${call.sent ?? ""}`.includes(made.share_id));
    expect(naming).toEqual([]);
    // No link on the page leads to it, so nothing can fetch it ahead of time.
    expect(seen.hrefs.length).toBeGreaterThan(40);
    expect(seen.hrefs.filter((href) => href.includes(made.share_id) || /^\/s([#?/]|$)/.test(href))).toEqual([]);
    // It is in the field the person copies it from, and nowhere else on the page.
    expect(seen.pageWithoutTheField.includes(made.share_id)).toBe(false);
    // The address of the page never held it, and the history was not touched.
    expect(seen.address).toBe("http://localhost/");
    expect(seen.watched.history).toEqual([]);
    expect(seen.title).toBe("");
  });

  test("test_copying_puts_the_link_on_the_clipboard_and_nothing_else", () => {
    expect(seen.copied).toEqual([seen.links[0]]);
  });

  test("test_a_share_is_sent_as_a_post_with_no_cookie_and_is_kept_by_no_cache", () => {
    for (const call of callsTo("create_share")) {
      expect(call.url).toBe(`${BASE}/v1/shares`);
      expect(call.init).toMatchObject({
        method: "POST",
        credentials: "omit",
        referrerPolicy: "no-referrer",
        cache: "no-store",
      });
    }
  });
});

describe("what a comparison holds", () => {
  test("test_the_link_to_a_comparison_holds_the_slugs_of_the_areas_and_nothing_else", () => {
    const address = new URL(seen.compareLink, "http://localhost");

    expect(address.pathname).toBe("/compare");
    expect([...address.searchParams.keys()]).toEqual(["a", "a"]);
    expect(address.searchParams.getAll("a").every((slug) => areas.some((area) => area.slug === slug))).toBe(true);
    expect(address.hash).toBe("");
    expect(seen.compareLink.includes(CANARY)).toBe(false);
    expect(/syn-[pn]\d+/.test(seen.compareLink)).toBe(false);
  });

  test("test_the_search_goes_to_the_comparison_in_a_post_body_and_never_in_an_address", () => {
    const [call] = callsTo("compare");

    expect(call?.url).toBe(`${BASE}/v1/compare`);
    expect(call?.method).toBe("POST");
    expect((call?.body as { spec: PreferenceSpec }).spec).toEqual(withThePlace);
    expect(call?.sent?.includes(CANARY)).toBe(false);
  });
});

describe("everywhere else", () => {
  test("test_typed_text_travels_only_in_the_two_bodies_it_was_typed_for", () => {
    const holding = seen.calls.filter((call) => JSON.stringify([call.url, call.sent]).includes(CANARY));

    expect(new Set(holding.map((call) => `${call.method} ${call.path}`))).toEqual(
      new Set(["POST /v1/interpret", "POST /v1/places/search"]),
    );
    for (const call of seen.calls) expect(call.url.includes(CANARY)).toBe(false);
  });

  test("test_no_address_on_the_page_holds_what_was_typed_or_a_place", () => {
    expect(seen.addresses.includes(CANARY)).toBe(false);
    expect(/syn-p\d+/.test(seen.addresses)).toBe(false);
  });

  test("test_nothing_is_ever_written_to_browser_storage", () => {
    expect(seen.watched.storage).toEqual([]);
  });

  test("test_nothing_is_written_to_the_console", () => {
    expect(seen.watched.console).toEqual([]);
  });
});
