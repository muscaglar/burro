/**
 * What the search page does on a release that is not finished: one that holds a
 * few measures, a band for three vibes of eleven, and no journey and no cost.
 *
 * The website was tested on a release that holds everything, and first met one
 * that does not in a browser. There the first word of the shelf, two of the
 * three examples and the page's own main button each ended in a list of no area,
 * and the page said that no area passed every limit, of a person who had set
 * none. Each test here is of one thing that was seen, and would have caught it.
 *
 * The release is made up. It is the committed one as a first build would hold
 * it, recorded under `preview/`.
 */

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { SearchApp } from "@/components/SearchApp/SearchApp";
import { Shell } from "@/components/Shell/Shell";
import { KNOWN } from "@/content/kit";
import { HELPERS } from "@/content/helpers";
import { WAYS } from "@/content/ways";
import { LEGEND } from "@/content/map";
import {
  CHIPS,
  COMPLETENESS,
  EXAMPLE_POOL,
  NOT_IN_DATA,
  PLACE,
  PROMPT,
  REJECTED,
  REJECTED_LABEL,
  RESULTS,
  SEARCH,
  SHELF,
  STRIP,
  FIND_AREA,
} from "@/content/search";
import { BUDGET, JOURNEY, SETTINGS } from "@/content/settings";
import { saysItsBorough } from "@/lib/area/named";
import { readRecorded, recordedAnswer, responseFrom } from "@/lib/api/recorded";
import type { MetaData } from "@/lib/api/schema";
import { examplesFor, placedOf } from "@/lib/holds";

import { standInApi, type StandIn } from "../support/api";
import {
  arrived,
  helper,
  helpers,
  panelOf,
  promptBox,
  results,
  settingsAt,
  settled,
  theSettings,
  way,
  ways,
} from "../support/search";

jest.mock("next/navigation", () => ({ usePathname: () => "/" }));

const form = recordedAnswer("get_meta", "preview/meta").body;
/** The group of the settings that holds a family of vibes, by the name the service gives the family. */
const groupOf = (family: string) => form.data.families.find((one) => one.family === family)?.label ?? "";
const listed = recordedAnswer("list_areas", "preview/areas").body.data;
const whole = recordedAnswer("get_meta", "meta").body.data;
const sentenceOf = (scenario: string) =>
  (recordedAnswer("interpret", scenario).request.body as { text: string }).text;
const heldOf = (tagId: string) => form.data.recipes.find((held) => held.tag_id === tagId);

/** The service that holds the preview: every route that is of the release answers of it. */
function previewApi(): StandIn {
  return standInApi()
    .on("get_meta", "preview/meta")
    .on("list_areas", "preview/areas")
    .on("get_geometry", "preview/geometry");
}

/** The page as it is built on the preview, with the service that holds it behind it. */
async function openPreview(api: StandIn = previewApi(), data: MetaData = form.data) {
  const user = userEvent.setup({ delay: null });
  render(
    <Shell meta={form.meta}>
      <SearchApp meta={data} areas={listed.areas} bands={listed.bands} client={api.client} />
    </Shell>,
  );
  await arrived();
  return { api, user };
}

/** What the helpers of the first screen say, in the order they stand in. */
const helpersDrawn = () =>
  within(helpers())
    .getAllByRole("button")
    .map((button) => button.textContent);
/** The two ways in, by what their tabs say, in the order they stand in. */
const waysDrawn = () =>
  within(ways())
    .getAllByRole("tab")
    .map((tab) => tab.textContent);

/** Types a recorded sentence and sends it, against the answers recorded for it. */
async function typed(scenario: string, rank?: string, reasons?: string) {
  const api = previewApi().on("interpret", scenario);
  if (rank !== undefined) api.on("rank", rank);
  if (reasons !== undefined) api.on("explain_top", reasons);
  const opened = await openPreview(api);
  await opened.user.type(promptBox(), sentenceOf(scenario));
  await opened.user.keyboard("{Enter}");
  await settled();
  return opened;
}

const shelf = () => within(screen.getByRole("region", { name: SHELF.title }));
const notInData = () => screen.getByRole("status", { name: NOT_IN_DATA.title });
const namedAsMissing = () =>
  within(notInData())
    .getAllByRole("listitem")
    .map((item) => item.querySelector("strong")?.textContent ?? "");

describe("the first screen, on data that is not finished", () => {
  test("test_the_release_of_these_tests_holds_what_a_first_build_holds", () => {
    expect(form.meta.preview).toBe(true);
    expect(form.data.holds).toEqual({ journeys: false, costs: false });
    expect(form.data.recipes.filter((held) => held.placed).map((held) => held.tag_id)).toEqual([
      "quiet_residential",
      "parks_close_by",
      "homes",
    ]);
    expect(whole.holds).toEqual({ journeys: true, costs: true });
  });

  test("test_the_box_asks_only_for_what_the_data_can_answer_and_says_what_it_cannot", async () => {
    await openPreview();

    const hint = PROMPT.hintFor(form.data.holds);
    expect(document.body.textContent?.includes(hint)).toBe(true);
    expect(hint).toContain("no rents, no prices and no journey times");
    // It once asked a person to say what they can pay and where they need to get to.
    expect(document.body.textContent?.includes(PROMPT.hint)).toBe(false);
    expect(document.body.textContent?.includes(SEARCH.lead)).toBe(false);
    expect(document.body.textContent?.includes(SEARCH.leadNoJourneys)).toBe(true);
  });

  test("test_no_field_asks_for_a_place_where_the_data_names_none_and_the_box_finds_areas", async () => {
    // Seen in a browser: a place typed in the field was met with "No place matches. Try
    // another spelling", where no spelling could match. The box finds an area by its name,
    // and says that the data names no place to reach.
    const { api, user } = await openPreview();
    api.on("search_places", () => responseFrom(readRecorded("preview/places-search")));
    // The field stands at the head of the second way in, over the settings.
    await way(user, "deep");

    expect(screen.queryByRole("combobox", { name: PLACE.label })).toBeNull();
    expect(screen.queryByRole("combobox", { name: FIND_AREA.label })).toBeNull();
    expect(document.body.textContent?.includes(FIND_AREA.hintAlone)).toBe(true);
    // It says why it finds no place: Burro has none to reach, and so can work out no journey.
    expect(FIND_AREA.hintAlone).toMatch(/\bno places\b/);
    expect(FIND_AREA.hintAlone).toMatch(/\bjourney\b/);
    await user.type(screen.getByRole("textbox", { name: FIND_AREA.labelAlone }), "alder");
    await arrived();

    const found = await screen.findByRole("group", { name: FIND_AREA.title });
    expect(Array.from(found.querySelectorAll("a")).map((link) => link.textContent)).toEqual(["Alderwick"]);
    // No place is offered to pick: the field lays no list. The settings under it stand
    // open, and the kinds of home in them are the browser's own list, of no place.
    expect(screen.queryAllByRole("listbox")).toEqual([]);
    expect(screen.queryAllByRole("option").filter((one) => one.closest("select") === null)).toEqual([]);
  });

  test("test_every_example_the_page_offers_gives_a_list", async () => {
    // Seen in a browser: two of the three examples ranked no area of 1,002.
    const { user } = await openPreview();
    const offered = examplesFor(form.data);
    await helper(user, "example");

    expect(offered).toHaveLength(3);
    for (const text of offered) {
      expect(screen.getByRole("button", { name: text })).toBeInTheDocument();
      const at = EXAMPLE_POOL.findIndex((example) => example.text === text) + 1;
      const ranked = recordedAnswer("rank", `preview/example-${at}`).body.data;
      expect(ranked.areas_ranked).toBeGreaterThan(0);
      expect(ranked.rejected).toEqual([]);
    }
    // None of the three that a release which holds everything shows can be answered here.
    for (const text of examplesFor(whole)) expect(screen.queryByRole("button", { name: text })).toBeNull();
    await user.click(screen.getByRole("button", { name: offered[0] }));
    expect(promptBox().value).toBe(offered[0]);
  });

  test("test_what_each_example_is_said_to_ask_for_is_what_the_reader_makes_of_it", () => {
    EXAMPLE_POOL.forEach((example, at) => {
      const recorded = recordedAnswer("interpret", `example-${at + 1}`);
      const { operations } = recorded.body.data;
      const asked = [
        ...(operations.budget_ops.some((edit) => edit.amount > 0) ? ["budget"] : []),
        ...(operations.commute_ops.length > 0 ? ["commute"] : []),
        ...operations.weight_ops.map((edit) => `feature:${edit.feature_id}`),
        ...operations.tag_ops.map((edit) => `tag:${edit.tag_id}`),
      ];

      expect((recorded.request.body as { text: string }).text).toBe(example.text);
      expect([...example.asks].sort()).toEqual(asked.sort());
    });
    // On a release that holds everything, the three that were first written are shown.
    expect(examplesFor(whole)).toEqual(EXAMPLE_POOL.slice(0, 3).map((example) => example.text));
  });

  test("test_the_shelf_offers_first_the_words_an_area_can_be_placed_on", async () => {
    // Seen in a browser: "leafy" was the first word of the shelf, and ranked no area.
    const { user } = await openPreview();
    await helper(user, "word");
    const words = () =>
      shelf()
        .getAllByRole("button")
        .map((button) => button.textContent);

    expect(words()).toEqual(["quiet street", "near a big park", "Houses or flats", SHELF.more]);

    await user.click(shelf().getByRole("button", { name: SHELF.more }));

    const waiting = within(shelf().getByRole("list", { name: SHELF.waiting }))
      .getAllByRole("button")
      .map((button) => button.textContent);
    expect(waiting).toEqual([
      "leafy",
      "villagey",
      "lively",
      "period",
      "walkable",
      "Food and drink",
      "Family amenities",
      "Well connected",
      "Gritty",
      "Family area",
      "Young professionals",
    ]);
    expect(words().slice(0, 4)).toEqual(["quiet street", "near a big park", "Houses or flats", SHELF.fewer]);
  });

  test("test_a_word_no_area_can_be_placed_on_says_so_and_cannot_be_added", async () => {
    // Seen in a browser: its card had "Add to my search", which ranked no area, over a map
    // of dots under "Coloured by Leafy, in five bands".
    const { user, api } = await openPreview();
    await helper(user, "word");
    await user.click(shelf().getByRole("button", { name: SHELF.more }));
    await user.click(shelf().getByRole("button", { name: "leafy" }));
    const card = screen.getByRole("region", { name: "Leafy" });
    const held = heldOf("leafy");

    expect(within(card).queryByRole("button", { name: SHELF.add })).toBeNull();
    expect(within(card).getAllByRole("button").map((button) => button.textContent)).toEqual([SHELF.close]);
    expect(within(card).getByRole("note").textContent).toBe(SHELF.notPlaced("Leafy"));
    // The share is one number, and each part it waits on is named.
    expect(held?.held).toBe(30);
    expect(card.textContent?.includes(SHELF.held(30, 60))).toBe(true);
    for (const part of held?.waits_on ?? []) expect(card.textContent?.includes(part.label)).toBe(true);
    expect(held?.waits_on.map((part) => part.hundredths)).toEqual([40, 30]);
    expect(card.textContent?.includes(SHELF.missing(2))).toBe(false);
    // Nothing is coloured by it, in the card or on the map, and nothing was sent.
    expect(within(card).queryByRole("img")).toBeNull();
    expect(document.body.textContent?.includes(LEGEND.vibe("Leafy"))).toBe(false);
    expect(api.callsTo("rank")).toHaveLength(0);
  });

  test("test_a_word_that_rests_on_part_of_its_recipe_says_the_share_and_what_it_waits_on", async () => {
    const { user, api } = await openPreview(previewApi().on("rank", "preview/rank-plain"));
    await helper(user, "word");
    await user.click(shelf().getByRole("button", { name: "quiet street" }));
    const card = screen.getByRole("region", { name: "Quiet streets" });
    const held = heldOf("quiet_residential");

    expect(card.textContent?.includes(SHELF.held(70, 60))).toBe(true);
    // What it waits on is one measure, named as the service names it, which counts for 30 of 100.
    expect(held?.waits_on.map((part) => [part.feature_id, part.hundredths])).toEqual([["evening_cluster_exposure", 30]]);
    expect(held?.waits_on[0]?.label).toMatch(/pubs or bars within 150 m/);
    expect(card.textContent?.includes(held?.waits_on[0]?.label ?? "none")).toBe(true);
    // It can be added, as ever.
    await user.click(within(card).getByRole("button", { name: SHELF.add }));
    await settled();
    expect(api.callsTo("rank")).toHaveLength(1);
  });

  test("test_on_a_release_that_holds_everything_the_first_screen_offers_all_of_it", async () => {
    const user = userEvent.setup({ delay: null });
    const full = recordedAnswer("get_meta", "meta").body;
    const all = recordedAnswer("list_areas", "areas").body.data;
    render(
      <Shell meta={full.meta}>
        <SearchApp meta={full.data} areas={all.areas} bands={all.bands} client={standInApi().client} />
      </Shell>,
    );
    await arrived();

    expect(document.body.textContent?.includes(PROMPT.hint)).toBe(true);
    expect(document.body.textContent?.includes(SEARCH.lead)).toBe(true);
    expect(waysDrawn()).toEqual([WAYS.quick, WAYS.deep]);
    expect(helpersDrawn()).toEqual([HELPERS.example, HELPERS.word]);
    // The second way in holds the field that finds an area by its name, and its settings
    // hold the field that finds a place to reach, under the journeys.
    await way(user, "deep");
    expect(within(panelOf("deep")).getByRole("textbox", { name: FIND_AREA.labelAlone })).toBeInTheDocument();
    await settingsAt(user, SETTINGS.journeys);
    expect(within(theSettings()).getByRole("combobox", { name: PLACE.label })).toBeInTheDocument();
    await way(user, "quick");
    await helper(user, "word");
    expect(shelf().queryByRole("list", { name: SHELF.waiting })).toBeNull();
    await user.click(shelf().getByRole("button", { name: SHELF.more }));
    expect(shelf().queryByRole("list", { name: SHELF.waiting })).toBeNull();
  });

  test("test_the_preview_of_these_tests_gives_every_helper_something_to_offer", async () => {
    const { user } = await openPreview();

    // Three examples it can answer the whole of, and three words an area can be placed on.
    expect(examplesFor(form.data)).toHaveLength(3);
    expect(placedOf(form.data, form.data.tags)).toHaveLength(3);
    expect(helpersDrawn()).toEqual([HELPERS.example, HELPERS.word]);
    // And the second way in, which holds the field that finds an area by its name where
    // the data names no place to reach, and the settings under it.
    expect(waysDrawn()).toEqual([WAYS.quick, WAYS.deep]);
    await way(user, "deep");
    expect(within(panelOf("deep")).getByRole("textbox", { name: FIND_AREA.labelAlone })).toBeInTheDocument();
    expect(panelOf("deep")).toContainElement(theSettings());
  });

  test("test_a_helper_is_not_drawn_where_the_data_gives_it_nothing_to_offer", async () => {
    // A release that places no area on any vibe, and ranks none of what an example asks
    // for. A shelf of words that cannot be added is nothing to start from, and a heading
    // over no example is no help.
    const poorer: MetaData = {
      ...form.data,
      recipes: form.data.recipes.map((held) => ({ ...held, placed: false })),
      features: form.data.features.map((metric) => ({ ...metric, rankable: false })),
    };
    const { user } = await openPreview(previewApi(), poorer);

    expect(examplesFor(poorer)).toEqual([]);
    expect(placedOf(poorer, poorer.tags)).toEqual([]);
    // Neither helper has anything to offer, so no line of helpers is drawn: no button that
    // opens nothing, and no line that holds none.
    expect(screen.queryByRole("group", { name: HELPERS.label })).toBeNull();
    expect(screen.queryByRole("button", { name: HELPERS.example })).toBeNull();
    expect(screen.queryByRole("button", { name: HELPERS.word })).toBeNull();
    // Both ways in are there all the same. The box is in the first, and what is left to
    // choose from is in the second: renting or buying, and the field that finds an area by name.
    expect(waysDrawn()).toEqual([WAYS.quick, WAYS.deep]);
    expect(panelOf("quick")).toContainElement(promptBox());
    await way(user, "deep");
    expect(within(panelOf("deep")).getByRole("textbox", { name: FIND_AREA.labelAlone })).toBeInTheDocument();
    expect(within(panelOf("deep")).getAllByRole("radio").length).toBeGreaterThan(1);
    expect(screen.queryByRole("region", { name: SHELF.title })).toBeNull();
    expect(screen.queryByRole("heading", { name: PROMPT.examplesTitle })).toBeNull();
  });

  test("test_a_helper_is_drawn_for_the_words_alone_where_no_example_can_be_answered", async () => {
    const noExample: MetaData = {
      ...form.data,
      // Every example of the pool asks for a thing this release no longer holds.
      recipes: form.data.recipes.map((held) =>
        held.tag_id === "homes" ? held : { ...held, placed: false },
      ),
      features: form.data.features.map((metric) => ({ ...metric, rankable: false })),
    };
    await openPreview(previewApi(), noExample);

    expect(examplesFor(noExample)).toEqual([]);
    expect(placedOf(noExample, noExample.tags).map((tag) => tag.tag_id)).toEqual(["homes"]);
    expect(helpersDrawn()).toEqual([HELPERS.word]);
    expect(waysDrawn()).toEqual([WAYS.quick, WAYS.deep]);
  });
});

describe("a sentence, on data that is not finished", () => {
  test("test_a_wish_the_data_cannot_answer_is_named_under_the_box_with_what_it_waits_on", async () => {
    // Seen in a browser: "leafy and quiet" showed Leafy as understood, and ranked on quiet
    // alone, with a fit of 97 of 100.
    await typed("preview/interpret-plain", "preview/rank-plain", "preview/explanations-plain");

    expect(namedAsMissing()).toEqual(["Leafy"]);
    const said = notInData().textContent ?? "";
    expect(said.includes(NOT_IN_DATA.lead(1))).toBe(true);
    expect(said.includes(NOT_IN_DATA.why.vibe)).toBe(true);
    for (const part of heldOf("leafy")?.waits_on ?? []) {
      expect(said.includes(NOT_IN_DATA.part(part.label, part.hundredths))).toBe(true);
    }
    // It is no part of what Burro understood, and it is said once.
    const chips = within(screen.getByRole("region", { name: CHIPS.label }))
      .getAllByRole("listitem")
      .map((chip) => chip.textContent ?? "");
    expect(chips.some((chip) => chip.includes("Quiet streets"))).toBe(true);
    expect(chips.some((chip) => chip.includes("Leafy"))).toBe(false);
    expect(screen.queryByRole("region", { name: REJECTED_LABEL })).toBeNull();
    expect(document.body.textContent?.includes(REJECTED.not_in_release)).toBe(false);
    // The list is ranked on what the data does hold.
    expect(results().length).toBeGreaterThan(0);
  });

  test("test_what_is_not_in_the_data_is_said_in_one_line_and_why_is_one_press_away", async () => {
    // Seen in a browser: the notice was 192 px high on a desk and 288 on a phone, above the
    // answer. It names each thing in one line, and opens to why by the browser's own element.
    await typed("preview/interpret-long", "preview/rank-plain", "preview/explanations-plain");

    const opens = notInData().querySelector("details");
    const line = opens?.querySelector("summary");
    expect(opens).not.toBeNull();
    expect(opens?.open).toBe(false);
    expect(line?.textContent).toBe(
      `${NOT_IN_DATA.title}: ${["More culture nearby", NOT_IN_DATA.commute, NOT_IN_DATA.budget].join("; ")}`,
    );
    expect(line).toHaveClass("target-min");
    // Everything else that is said of it is inside what opens, and nothing of it is left out.
    const rest = [...(opens?.children ?? [])].filter((child) => child !== line);
    expect(rest.map((child) => child.textContent ?? "").join(" ")).toContain(NOT_IN_DATA.lead(3));
    expect(notInData().querySelectorAll(":scope > :not(details)")).toHaveLength(0);
  });

  test("test_it_stands_directly_under_the_box_before_what_was_understood", async () => {
    await typed("preview/interpret-plain", "preview/rank-plain", "preview/explanations-plain");
    const understood = screen.getByRole("region", { name: CHIPS.label });

    expect(Boolean(notInData().compareDocumentPosition(understood) & Node.DOCUMENT_POSITION_FOLLOWING)).toBe(true);
    expect(Boolean(promptBox().compareDocumentPosition(notInData()) & Node.DOCUMENT_POSITION_FOLLOWING)).toBe(true);
  });

  test("test_a_budget_that_cannot_be_tested_is_said_to_be_missing_and_the_home_is_kept", async () => {
    await typed("preview/interpret-home");

    expect(namedAsMissing()).toEqual([NOT_IN_DATA.budget]);
    expect(notInData().textContent?.includes(NOT_IN_DATA.why.budget)).toBe(true);
    const chips = screen.getByRole("region", { name: CHIPS.label }).textContent ?? "";
    expect(chips.includes("Buying")).toBe(true);
    expect(chips.includes("£")).toBe(false);
  });

  test("test_of_a_long_sentence_only_what_can_be_answered_is_taken_and_the_page_says_what_cannot", async () => {
    // Seen in a browser: a budget was offered, and the one button that adds what needs no
    // choice added it. No area of 1,002 was left. The service offers only what the data
    // can answer, and that is all Burro takes: no budget and no journey is sent.
    const { api } = await typed("preview/interpret-long", "preview/rank-plain", "preview/explanations-plain");
    const noticed = recordedAnswer("interpret", "preview/interpret-long").body.data.suggestions;

    expect(noticed.map((one) => one.target)).toEqual(["tag:quiet_residential", "feature:park_proximity", "tenure"]);
    expect(screen.queryByRole("region", { name: "Choose what to add" })).toBeNull();
    const sent = api.lastCallTo("rank").body as { operations: { budget_ops: { amount: number }[]; commute_ops: unknown[] } };
    expect(sent.operations.commute_ops).toEqual([]);
    expect(sent.operations.budget_ops.filter((edit) => edit.amount !== 0)).toEqual([]);
    expect(api.lastCallTo("rank").sent?.includes("350")).toBe(false);
    expect(namedAsMissing()).toEqual(["More culture nearby", NOT_IN_DATA.commute, NOT_IN_DATA.budget]);
    // The amount that was typed is drawn nowhere but in the box.
    expect(notInData().textContent?.includes("350")).toBe(false);
    expect(results().length).toBeGreaterThan(0);
  });

  test("test_nothing_is_asked_about_a_place_where_the_data_names_none", async () => {
    await typed("preview/interpret-journey");

    expect(document.body.textContent).not.toMatch(/Which (place|area) did you mean/);
    expect(screen.queryByRole("region", { name: REJECTED_LABEL })).toBeNull();
    // No field finds a place. The settings stand open for what was not read, and a couple
    // of their groups with them: the list of kinds of home is the browser's own, and is no such field.
    expect(screen.queryByRole("combobox", { name: PLACE.label })).toBeNull();
    expect(screen.queryByRole("combobox", { name: FIND_AREA.label })).toBeNull();
    expect(screen.queryByRole("textbox", { name: FIND_AREA.labelAlone })).toBeNull();
    expect(screen.queryAllByRole("combobox").filter((one) => one.tagName !== "SELECT")).toEqual([]);
    expect(screen.queryAllByRole("listbox")).toEqual([]);
    expect(namedAsMissing()).toEqual([NOT_IN_DATA.commute]);
    expect(notInData().textContent?.includes(NOT_IN_DATA.why.commute)).toBe(true);
  });
});

describe("an area that is named for its borough", () => {
  test("test_the_borough_is_not_said_again_under_a_name_that_begins_with_it", async () => {
    // Seen in a browser: "Barking and Dagenham 003", and under it "Barking and Dagenham".
    expect(saysItsBorough({ name: "Alder Vale 003", borough: "Alder Vale" })).toBe(true);
    expect(saysItsBorough({ name: "Alder Vale", borough: "Alder Vale" })).toBe(true);
    expect(saysItsBorough({ name: "Alderwick", borough: "Alder" })).toBe(false);
    expect(saysItsBorough({ name: "Alderwick", borough: "Quillhaven" })).toBe(false);
    expect(saysItsBorough({ name: "Alderwick", borough: "" })).toBe(false);

    // On the made-up release no name begins with its borough, and every card names both.
    await typed("preview/interpret-plain", "preview/rank-plain", "preview/explanations-plain");
    const first = results()[0] as HTMLElement;
    const summary = listed.areas.find((area) => first.textContent?.includes(area.name));
    expect(first.textContent?.includes(summary?.borough ?? "no borough")).toBe(true);
  });
});

describe("a result that has no figure for what was asked for", () => {
  /** The lines of a result that say a thing was asked for and has no figure, before anything is opened. */
  const linesLacked = (card: HTMLElement, name: string) =>
    [STRIP.askedOf(name), STRIP.restOf(name)]
      .flatMap((list) => within(card).queryAllByRole("list", { name: list }))
      .flatMap((list) => within(list).getAllByRole("listitem"))
      .filter((line) => line.querySelector("[data-known='none']") !== null);
  /** What they say, line by line. */
  const lackedOn = (card: HTMLElement, name: string) => linesLacked(card, name).map((line) => line.textContent);
  /** The two words that say a fit is not whole, where a result says them with its fit. */
  const withTheFit = (card: HTMLElement) => within(card.querySelector("header") as HTMLElement).queryByText(KNOWN.some);
  /** Opens the working of a result, and gives what it holds. */
  const workingOf = async (user: ReturnType<typeof userEvent.setup>, card: HTMLElement, name: string) => {
    const opens = within(card).getByRole("button", { name: RESULTS.workingOf(name) });
    await user.click(opens);
    return document.getElementById(opens.getAttribute("aria-controls") ?? "") as HTMLElement;
  };

  test("test_the_card_names_what_the_area_has_no_figure_for_before_anything_is_opened", async () => {
    // Seen in a browser: asked for period homes, the first three results had no figure for
    // them. The card said "Based on 4 of the 5 things", and named nothing. Such an area now
    // stands below every area that has the figure, and its card says which it has none for.
    const { user } = await typed("preview/interpret-period", "preview/rank-lacking", "preview/explanations-lacking");
    const ranking = recordedAnswer("rank", "preview/rank-lacking").body.data;
    // It stands below the ten that are drawn first, so the rest are asked for.
    await user.click(screen.getByRole("button", { name: RESULTS.showMore(ranking.ranked.length - 10) }));
    const lacks = (area: (typeof ranking.ranked)[number]) =>
      area.contributions.some((part) => part.component === "feature:air_no2" && !part.present);
    const lacking = ranking.ranked.find(lacks);
    const name = listed.areas.find((area) => area.area_id === lacking?.area_id)?.name ?? "";
    const air = form.data.features.find((one) => one.feature_id === "air_no2")?.short_label ?? "";

    const complete = ranking.ranked.filter((area) => !lacks(area));
    expect(complete.length).toBeGreaterThan(0);
    expect(lacking?.rank).toBeGreaterThan(Math.max(...complete.map((area) => area.rank)));
    // It is ranked and scored on the rest, and never as nought.
    expect(lacking?.score).toBeGreaterThan(0);
    expect(lacking?.contributions.filter((part) => !part.present).map((part) => part.component)).toEqual([
      "feature:air_no2",
    ]);
    const card = results().find((one) => one.textContent?.includes(name)) as HTMLElement;
    // It is said in sight, with nothing pressed: on a line of its own, by the name the chip
    // has, among what was asked for. And the fit, which leaves it out, is said to be not whole.
    expect(within(card).getByRole("button", { name: RESULTS.workingOf(name) })).toHaveAttribute("aria-expanded", "false");
    expect(lackedOn(card, name)).toEqual([`${air}${KNOWN.none}`]);
    expect(within(card).getByText(KNOWN.none).closest("[aria-hidden='true'], [hidden], .visually-hidden")).toBeNull();
    expect(withTheFit(card)).not.toBeNull();
    // Nothing is drawn of the figure that is not known: no gauge, no step and no nought.
    const [line] = linesLacked(card, name);
    expect(line?.querySelector("[role='img'], [data-on], [data-placed]")).toBeNull();
    expect(/\d/.test(line?.textContent ?? "")).toBe(false);
    // A result that has a figure for everything says nothing of it.
    const whole = results()[0] as HTMLElement;
    expect(whole.textContent?.includes(KNOWN.none)).toBe(false);
    expect(withTheFit(whole)).toBeNull();
    // That the person asked for it, and that the fit leaves it out, is said in full one press away.
    expect(card.textContent?.includes(COMPLETENESS.lacksAsked([air]))).toBe(false);
    const working = await workingOf(user, card, name);
    expect(working.textContent?.includes(COMPLETENESS.some(3, 4))).toBe(true);
    expect(working.textContent?.includes(COMPLETENESS.lacksAsked([air]))).toBe(true);
  });

  test("test_a_usual_setting_with_no_figure_is_named_and_not_said_to_be_asked_for", async () => {
    const { user } = await typed("preview/interpret-plain", "preview/rank-plain", "preview/explanations-plain");
    const ranking = recordedAnswer("rank", "preview/rank-plain").body.data;
    const lacking = ranking.ranked.find((area) => area.contributions.some((part) => !part.present));
    const name = listed.areas.find((area) => area.area_id === lacking?.area_id)?.name ?? "";
    const air = form.data.features.find((one) => one.feature_id === "air_no2")?.short_label ?? "";
    const card = results().find((one) => one.textContent?.includes(name)) as HTMLElement;

    expect(lacking?.contributions.filter((part) => !part.present).map((part) => part.component)).toEqual([
      "feature:air_no2",
    ]);
    // Its fit is said to be not whole, and it has no line among what was asked for: nobody asked for it.
    expect(withTheFit(card)).not.toBeNull();
    expect(lackedOn(card, name)).toEqual([]);
    expect(card.textContent?.includes(KNOWN.none)).toBe(false);
    const working = await workingOf(user, card, name);
    expect(working.textContent?.includes(COMPLETENESS.lacks([air]))).toBe(true);
    expect(working.textContent?.includes(COMPLETENESS.lacksAsked([air]))).toBe(false);
  });
});

describe("the settings, on data that is not finished", () => {
  test("test_no_amount_is_asked_for_where_no_budget_can_be_tested", async () => {
    const { user } = await openPreview();
    await settingsAt(user, SETTINGS.money);
    const money = screen.getByRole("group", { name: BUDGET.legend });

    expect(money.textContent?.includes(BUDGET.notInData)).toBe(true);
    expect(within(money).queryByRole("spinbutton")).toBeNull();
    expect(within(money).queryByRole("textbox")).toBeNull();
    expect(within(money).queryByRole("button", { name: BUDGET.clear })).toBeNull();
    // The kind of home can still be chosen: a search holds it with or without an amount.
    expect(within(money).getByRole("combobox", { name: BUDGET.segment })).toBeInTheDocument();
  });

  test("test_no_place_can_be_added_where_the_data_names_none", async () => {
    const { user } = await openPreview();
    await settingsAt(user, SETTINGS.journeys);

    expect(document.body.textContent?.includes(JOURNEY.notInData)).toBe(true);
    expect(document.body.textContent?.includes(JOURNEY.none)).toBe(false);
    expect(screen.queryByRole("combobox", { name: PLACE.label })).toBeNull();
  });

  test("test_a_vibe_no_area_can_be_placed_on_has_no_slider_and_says_why", async () => {
    const { user } = await openPreview();
    await settingsAt(user, groupOf("green"));
    const leafy = screen.getByRole("group", { name: "Leafy" });
    const parks = screen.getByRole("group", { name: "Parks close by" });

    expect(within(leafy).queryByRole("slider")).toBeNull();
    expect(leafy.textContent?.includes(SHELF.held(30, 60))).toBe(true);
    expect(within(parks).getByRole("slider")).toBeInTheDocument();
  });
});
