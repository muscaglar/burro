/**
 * What a person types stays in the box it was typed in, and in one `POST`
 * body. docs/design/web.md, section 10.
 *
 * Each test plants a canary, a string found nowhere else, in the sentence, in
 * the place search and in the name of a place the API answers with. It then
 * runs a whole search: read, ask, answer, rank, refine, fail, go offline, and
 * a sentence that is not plain, of which the reader offers what it noticed.
 */

import { act, screen, waitFor, within } from "@testing-library/react";

import { CHIPS, NOTICE, PLACE, PROMPT, RESULTS, SUGGEST } from "@/content/search";
import { JOURNEY, SETTINGS } from "@/content/settings";
import { recordedAnswer, responseFrom } from "@/lib/api/recorded";
import type { FoundPlace } from "@/lib/api/schema";

import { BASE, setOnline, type StandIn } from "../support/api";
import {
  arrived,
  CANARY,
  everyChip,
  everyResult,
  firstSearch,
  openSearch,
  promptBox,
  removeChip,
  search,
  settingsAt,
  settled,
  theTable,
  theWholeOfIt,
} from "../support/search";
import { watch, type Watch } from "../support/watch";

jest.mock("next/navigation", () => ({ usePathname: () => "/" }));

/** A place whose name and whose id are canaries, as the API would answer a search with. */
const PLACE_NAME = `Zqxplace ${CANARY} Works`;
const PLACE_ID = "syn-p0777";

function answeringWithThePlace(api: StandIn): StandIn {
  const places = recordedAnswer("search_places", "places-search");
  const found: FoundPlace = { place_id: PLACE_ID, name: PLACE_NAME, kind: "landmark", coarse_name: PLACE_NAME };
  return api.on("search_places", () =>
    responseFrom({ ...places, body: { ...places.body, data: { places: [found] } } }),
  );
}

/** The first ranking, as the API would answer it for a search that names the place. */
function rankedWithThePlace() {
  const ranked = recordedAnswer("rank", "rank-first");
  const { spec } = ranked.body.data;
  const named = { ...spec, commutes: spec.commutes.map((commute) => ({ ...commute, place_id: PLACE_ID })) };
  // An answer names every place of the spec it returns: that is where the page has the name from.
  const places = [{ place_id: PLACE_ID, name: PLACE_NAME, kind: "landmark" }];
  return responseFrom({ ...ranked, body: { ...ranked.body, data: { ...ranked.body.data, spec: named, places } } });
}

beforeEach(() => setOnline(true));

/** A whole search, with a canary in everything a person types and in a place's name. */
async function wholeSearch() {
  const api = answeringWithThePlace(firstSearch().on("interpret", "interpret-clarify"));
  const opened = await openSearch(api);
  const { user } = opened;
  await run(api, user);
  await everyChip(user);
  return opened;
}

async function run(api: StandIn, user: Awaited<ReturnType<typeof openSearch>>["user"]) {

  // Read a sentence, which leaves a question.
  await search(user, `leafy and quiet, 30 minutes to ${CANARY}`);
  // Search for a place by name, and pick it as the answer.
  const question = within(screen.getByRole("region", { name: /Which place did you mean/ }));
  await user.type(question.getByRole("combobox"), `${CANARY} wor`);
  await user.click(await question.findByRole("option", { name: new RegExp(CANARY) }));
  await settled();
  // Refine with a control.
  api.on("rank", "rank-refined").on("explain_top", "explanations-refined");
  await settingsAt(user, SETTINGS.journeys);
  await user.click(screen.getAllByRole("checkbox", { name: JOURNEY.firm })[0] as HTMLElement);
  await settled();
  // Fail, and try again.
  api.on("rank", "error-internal");
  await removeChip(user, "Leafy");
  await user.click(within(await screen.findByRole("alert")).getByRole("button", { name: PROMPT.tryAgain }));
  await screen.findByRole("alert");
  // A sentence that never reaches Burro, one that cannot be read, and one the API refuses.
  api.unreachable("interpret");
  await user.type(promptBox(), ` and ${CANARY}`);
  await user.click(screen.getByRole("button", { name: PROMPT.submit }));
  // The edit that was waiting is sent again when the words fail, and fails as it did, so
  // what is on screen at the end is the failure of the ranking.
  await waitFor(() => expect(api.callsTo("interpret").at(-1)?.sent?.includes(CANARY)).toBe(true));
  await screen.findByRole("alert");
  await arrived();
  api.on("interpret", "error-internal");
  await user.click(screen.getByRole("button", { name: PROMPT.submit }));
  await waitFor(() => expect(screen.getByText(NOTICE.degraded)).toBeInTheDocument());
  api.on("interpret", "interpret-invalid-text");
  await user.click(screen.getByRole("button", { name: PROMPT.submit }));
  await arrived();
  // Offline, and back.
  setOnline(false);
  act(() => void window.dispatchEvent(new Event("offline")));
  await removeChip(user, "Quiet streets");
  await arrived();
  setOnline(true);
  act(() => void window.dispatchEvent(new Event("online")));
  await arrived();
  // A sentence that is not plain: nothing of it is applied, and what was noticed is offered.
  api.on("interpret", "interpret-suggest").on("rank", "rank-first").on("explain_top", "explanations-first");
  await user.clear(promptBox());
  await user.type(promptBox(), `Pubs are so noisy near ${CANARY}`);
  await user.click(screen.getByRole("button", { name: PROMPT.submit }));
  const offered = within(await screen.findByRole("region", { name: SUGGEST.title }));
  // The words a thing was noticed in, and the words that were not read, are shown in the box.
  await user.click(offered.getAllByRole("button", { name: /^Show the words in the box: / })[0] as HTMLElement);
  await user.click(screen.getByRole("button", { name: SUGGEST.showUnread }));
  // One is chosen, and one is left out.
  await user.click(offered.getByRole("button", { name: "Fewer pubs and bars" }));
  await settled();
  await user.click(screen.getByRole("button", { name: SUGGEST.named("Skip", "Less transport noise") }));
  // A place added by hand, from the field in the settings.
  api.on("rank", rankedWithThePlace);
  await user.type(screen.getAllByRole("combobox", { name: PLACE.label })[0] as HTMLElement, CANARY);
  await user.click(await screen.findByRole("option", { name: new RegExp(CANARY) }));
  await settled();
  // Everything that is one press away is opened, so that whatever it holds is on the page.
  await everyResult(user);
  await theTable(user);
}

/** What one whole search left behind it, everywhere it could have left anything. */
interface Seen {
  readonly calls: StandIn["calls"];
  readonly console: Watch["console"];
  readonly storage: Watch["storage"];
  readonly history: Watch["history"];
  readonly addresses: string;
  readonly ids: string;
  readonly attributes: readonly string[];
  readonly address: string;
  readonly title: string;
  readonly placeIsOnThePage: boolean;
}

let seen: Seen;

// The search is run once, and each test below looks at one place it could have leaked to.
beforeAll(async () => {
  setOnline(true);
  const watching = watch();
  try {
    const { api } = await wholeSearch();
    const chips = within(screen.getByRole("region", { name: CHIPS.label }));
    seen = {
      calls: api.calls,
      console: [...watching.console],
      storage: [...watching.storage],
      history: [...watching.history],
      addresses: watching.addresses(),
      ids: watching.ids(),
      attributes: [...document.querySelectorAll("*")].flatMap((element) =>
        [...element.attributes].map((attribute) => attribute.value),
      ),
      address: window.location.href,
      title: document.title,
      placeIsOnThePage: chips.queryByRole("button", { name: new RegExp(`^${PLACE_NAME}`) }) !== null,
    };
  } finally {
    watching.stop();
  }
});

describe("what a person types", () => {
  test("test_the_search_that_was_watched_was_a_whole_one", () => {
    const operations = new Set(seen.calls.map((call) => call.operation));

    expect([...operations].sort()).toEqual(
      ["explain_top", "get_area", "get_geometry", "get_meta", "interpret", "rank", "search_places"].sort(),
    );
    expect(seen.calls.length).toBeGreaterThan(12);
    expect(seen.placeIsOnThePage).toBe(true);
  });

  test("test_typed_text_never_reaches_a_url", () => {
    for (const call of seen.calls) expect(call.url.includes(CANARY)).toBe(false);
    expect(seen.addresses.includes(CANARY)).toBe(false);
    expect(seen.history).toEqual([]);
    expect(seen.address).toBe("http://localhost/");
    expect(seen.title).toBe("");
  });

  test("test_a_place_name_never_reaches_a_url", () => {
    // The place was picked, so its id is in the search and its name is on the page.
    expect(seen.calls.some((call) => call.sent?.includes(PLACE_ID))).toBe(true);
    for (const call of seen.calls) expect(/Zqxplace|syn-p\d+/i.test(call.url)).toBe(false);
    expect(/Zqxplace|syn-p\d+/i.test(seen.addresses)).toBe(false);
  });

  test("test_nothing_is_ever_written_to_browser_storage", () => {
    expect(seen.storage).toEqual([]);
  });

  test("test_typed_text_never_reaches_the_console", () => {
    // Nothing is written to the console at all, on any path, a failed request among them.
    expect(seen.console).toEqual([]);
  });

  test("test_typed_text_travels_only_in_a_post_body", () => {
    const holding = seen.calls.filter((call) =>
      JSON.stringify([call.url, call.sent, call.init.headers]).includes(CANARY),
    );
    expect(holding.length).toBeGreaterThan(4);
    expect(new Set(holding.map((call) => `${call.method} ${call.path}`))).toEqual(
      new Set(["POST /v1/interpret", "POST /v1/places/search"]),
    );
    for (const call of holding) {
      expect(call.url).toBe(`${BASE}${call.path}`);
      expect(JSON.stringify(call.init.headers).includes(CANARY)).toBe(false);
      expect(call.init).toMatchObject({
        method: "POST",
        credentials: "omit",
        referrerPolicy: "no-referrer",
        cache: "no-store",
      });
      // The sentence is sent as `text` and the place search as `q`, and as nothing else.
      const body = call.body as Record<string, unknown>;
      const fields = Object.keys(body).filter((key) => JSON.stringify(body[key]).includes(CANARY));
      expect(fields).toEqual([call.operation === "interpret" ? "text" : "q"]);
    }
  });

  test("test_no_id_of_a_place_or_of_a_fact_is_written_into_the_pages_markup", () => {
    expect(/syn-p\d+/.test(seen.ids)).toBe(false);
    expect(seen.ids.includes(CANARY)).toBe(false);
    // A fact's id holds the id of a place: `syn-n0006/travel/syn-p0021.pt`.
    expect(/\/(travel|feature|tag|cost|budget_fit|station|area)\//.test(seen.ids)).toBe(false);
    expect(seen.attributes.filter((value) => /syn-p\d+/.test(value))).toEqual([]);
    expect(seen.attributes.length).toBeGreaterThan(500);
  });

  test("test_no_page_is_fetched_ahead_of_time_because_of_what_a_search_led_to", async () => {
    const { user } = await openSearch();
    await search(user);

    // A link to an area is followed when it is pressed. Fetching it before would
    // tell the website's own server which areas a search had led to.
    await theWholeOfIt();
    const toAreas = [...document.querySelectorAll<HTMLAnchorElement>("main a[href^='/synthetic/']")];
    // "More like this" on each result, its page from its working, and every area of the table.
    expect(toAreas.length).toBeGreaterThan(60);
    expect(toAreas.filter((link) => link.dataset.prefetch !== "false")).toEqual([]);
  });

  test("test_more_like_this_on_a_result_leads_to_the_areas_page_and_holds_nothing_that_was_typed", async () => {
    const { user, api } = await openSearch();
    await search(user, `leafy and quiet ${CANARY}`);
    await everyResult(user);
    const sentBefore = api.calls.length;

    const links = screen.getAllByRole("link", { name: new RegExp(`^${RESULTS.moreLike}`) });

    // The address is the area's own page and the name of a part of it. It holds nothing of the
    // search, so opening it tells no one what was typed, and the page it opens was built
    // before the search was made.
    expect(links.length).toBeGreaterThanOrEqual(10);
    for (const link of links) {
      expect(link.getAttribute("href")).toMatch(/^\/synthetic\/[a-z0-9]+(-[a-z0-9]+)*#alike$/);
      expect(link.getAttribute("href")?.includes(CANARY)).toBe(false);
      expect(link).toHaveAttribute("data-prefetch", "false");
    }
    expect(api.calls).toHaveLength(sentBefore);
  });

  test("test_the_prompt_form_cannot_be_sent_as_a_get", async () => {
    await openSearch();

    const form = promptBox().closest("form");
    expect(form).toHaveAttribute("method", "post");
    expect(form).not.toHaveAttribute("action");
    // With no name, a field is left out of what a form sends, whatever sends it.
    expect(promptBox()).not.toHaveAttribute("name");
    expect(promptBox()).toHaveAttribute("autocomplete", "off");
    // Nor is the browser asked to check the spelling, which may send the words to its maker.
    expect(promptBox()).toHaveAttribute("spellcheck", "false");
    const place = screen.getByRole("combobox", { name: PLACE.label });
    expect(place).not.toHaveAttribute("name");
    expect(place).toHaveAttribute("autocomplete", "off");
    expect(place).toHaveAttribute("spellcheck", "false");
    expect(place.closest("form")).toBeNull();
    expect([...document.querySelectorAll("form")]).toEqual([form]);
  });

  test("test_the_text_is_not_kept_in_the_markup_of_the_box", async () => {
    const { user, container } = await openSearch();

    await user.type(promptBox(), `leafy ${CANARY}`);
    await user.type(screen.getByRole("combobox", { name: PLACE.label }), CANARY);
    await arrived();

    // The box holds the text. Nothing else in the page's markup does.
    expect(promptBox()).toHaveValue(`leafy ${CANARY}`);
    expect(container.innerHTML.includes(CANARY)).toBe(false);
  });

  test("test_the_question_never_repeats_what_was_typed", async () => {
    const { user } = await openSearch(firstSearch().on("interpret", "interpret-clarify"));

    await search(user, `30 minutes to ${CANARY}`);

    const page = document.body.cloneNode(true) as HTMLElement;
    page.querySelectorAll("textarea, input").forEach((field) => field.remove());
    expect(page.textContent?.includes(CANARY)).toBe(false);
  });

  test("test_the_words_beside_an_offer_are_cut_from_the_box_and_are_nowhere_else_on_the_page", async () => {
    const { user, api, container } = await openSearch(firstSearch().on("interpret", "interpret-suggest"));
    const typed = `Pubs are so noisy near ${CANARY}`;

    await user.type(promptBox(), typed);
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    const offered = within(await screen.findByRole("region", { name: SUGGEST.title }));
    await user.click(offered.getAllByRole("button", { name: /^Show the words in the box: / })[0] as HTMLElement);
    await user.click(screen.getByRole("button", { name: SUGGEST.showUnread }));

    // The words are selected where they stand, and those an offer rests on are drawn beside it.
    expect(promptBox()).toHaveValue(typed);
    expect(promptBox().selectionEnd).toBeGreaterThan(promptBox().selectionStart);
    const quoted = [...container.querySelectorAll("q")];
    expect(quoted.map((words) => words.textContent)).toEqual(["Pubs are so noisy", "Pubs are so noisy"]);
    expect(quoted.every((words) => words.closest("section")?.getAttribute("aria-labelledby"))).toBe(true);
    // They are in the text of the page there, and in no attribute, no id and no other place.
    const page = container.cloneNode(true) as HTMLElement;
    page.querySelectorAll("textarea, q").forEach((held) => held.remove());
    expect(page.innerHTML.includes(CANARY)).toBe(false);
    expect(page.innerHTML.includes("so noisy")).toBe(false);
    // What nothing was made of is drawn nowhere.
    expect(container.innerHTML.replace(/<textarea[\s\S]*?<\/textarea>/g, "").includes(CANARY)).toBe(false);
    // Nothing is ranked from what was noticed until the person chooses.
    expect(api.callsTo("rank")).toEqual([]);

    api.on("rank", "rank-suggestion-chosen").on("explain_top", "explanations-suggestion-chosen");
    await user.click(offered.getByRole("button", { name: "Fewer pubs and bars" }));
    await settled();

    // What is sent is the edit the API gave with the choice, and nothing of what was typed.
    const chosen = recordedAnswer("rank", "rank-suggestion-chosen");
    expect(api.lastCallTo("rank").body).toEqual(chosen.request.body);
    expect(api.lastCallTo("rank").sent?.includes(CANARY)).toBe(false);
    expect(api.callsTo("interpret")).toHaveLength(1);
  });

  test("test_the_words_beside_an_offer_go_when_the_box_changes", async () => {
    const { user, container } = await openSearch(firstSearch().on("interpret", "interpret-suggest"));

    await user.type(promptBox(), `Pubs are so noisy near ${CANARY}`);
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await screen.findByRole("region", { name: SUGGEST.title });
    expect(container.querySelectorAll("q")).toHaveLength(2);
    await user.type(promptBox(), " and more");

    // Where the words stand is known for the text that was sent, and for no other.
    expect(container.querySelectorAll("q")).toHaveLength(0);
    expect(screen.queryByRole("region", { name: SUGGEST.title })).toBeNull();
  });

  test("test_the_words_are_sent_twice_where_a_model_reads_and_each_time_in_the_body_of_a_post", async () => {
    const api = firstSearch().inTurn("interpret", "interpret-rules-at-once", "interpret-by-model-long");
    const { user } = await openSearch(api);

    await user.type(promptBox(), `quiet, honestly ${CANARY}`);
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await screen.findByRole("region", { name: SUGGEST.title });
    await settled();

    const calls = api.callsTo("interpret");
    expect(calls.map((call) => (call.body as { ask_model: boolean }).ask_model)).toEqual([false, true]);
    expect(calls.every((call) => call.method === "POST" && !call.url.includes(CANARY))).toBe(true);
    expect(calls.every((call) => call.sent?.includes(CANARY))).toBe(true);
    // No other call holds a word of them.
    const others = api.calls.filter((call) => call.operation !== "interpret");
    expect(others.some((call) => call.url.includes(CANARY) || call.sent?.includes(CANARY))).toBe(false);
  });
});
