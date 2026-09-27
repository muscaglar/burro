/**
 * A search for somewhere to stay, on the search page.
 *
 * The founder walked the website a second time and wrote: "Add a visiting option under
 * renting or buying, again, this should accomodate people who are looking where to get a
 * hotel etc. Visiting should remove some of the price and bedroom fields, we are just
 * finding a location where they might want to book a hotel."
 *
 * Visiting is a kind of search of its own in the service. What is held here is what the
 * page makes of one that is typed: what Burro understood says "Visiting", no chip of a
 * budget or of a home is drawn, and what a visit cannot hold is said in a line. The
 * choice beside renting and buying is the settings', and is held with them.
 *
 * Every answer is the service's, as it was recorded of that very sentence.
 */

import { screen, within } from "@testing-library/react";

import { CHIPS, LEFT_OUT, PROMPT, RESULTS, SEARCH, STATUS, UNMET } from "@/content/search";
import { recordedAnswer, responseFrom } from "@/lib/api/recorded";
import { WAIT } from "@/content/wait";
import type { InterpretData, Operations, Suggestion } from "@/lib/api/schema";
import { NO_EDITS } from "@/lib/search/edits";

import { reasonsFor, setOnline, standInApi, withTheSpecSent, type Responder } from "../support/api";
import { everyChip, noisyAtHome, openSearch, promptBox, results, settled } from "../support/search";

jest.mock("next/navigation", () => ({ usePathname: () => "/" }));

const sentenceOf = (scenario: string) =>
  (recordedAnswer("interpret", scenario).request.body as { text: string }).text;
const understood = () => screen.getByRole("region", { name: CHIPS.label });
const chips = () =>
  within(understood())
    .getAllByRole("listitem")
    .map((chip) => (chip.querySelector("[data-main]") ?? chip).textContent ?? "");
const sent = (body: unknown) => body as { spec: { tenure: string }; operations?: Operations; limit: number };
/** Everything the page says but what the box holds. */
const thePage = () => {
  const page = document.body.cloneNode(true) as HTMLElement;
  page.querySelectorAll("textarea, input").forEach((field) => field.remove());
  return page.textContent ?? "";
};

/** A service that answers a visit as it was recorded answering one. */
const visiting = () =>
  standInApi()
    .on("interpret", "visiting/interpret")
    .on("rank", "visiting/rank")
    .on("explain_top", "visiting/explanations");

/** The ranking of a visit with one journey, as it was recorded, to the place that is named. */
function rankedTo(place: { readonly id: string; readonly name: string; readonly kind: string }): Responder {
  const recorded = recordedAnswer("rank", "visiting/rank-becomes");
  return () => {
    const { data } = recorded.body;
    const [journey] = data.spec.commutes;
    if (!journey) throw new Error("the recording holds no journey");
    return responseFrom({
      ...recorded,
      body: {
        ...recorded.body,
        data: {
          ...data,
          spec: { ...data.spec, commutes: [{ ...journey, place_id: place.id }] },
          places: [{ place_id: place.id, name: place.name, kind: place.kind }],
        },
      },
    });
  };
}

/**
 * What the service answers where the place that is named is the name of an area: no edit,
 * and a rule for the area, to look only there or to leave it out, with no guess and no way
 * that one press may add. No answer that was recorded holds one. So this is the recorded
 * answer to the same sentence about a place, with what the service gave on 2026-09-26 of
 * an area in the place of its offer, edit for edit, and whatever else a test lays beside it.
 */
function offeringARuleFor(area: { readonly area_id: string; readonly name: string }, beside: readonly Suggestion[] = []): Responder {
  const recorded = recordedAnswer("interpret", "visiting/interpret-mother");
  const [journey] = recorded.body.data.suggestions;
  const skip = journey?.choices.find((way) => way.id === "ignore");
  if (!journey || !skip) throw new Error("the recording holds no offer");
  const ruled = (rule: "only" | "exclude") => ({
    ...NO_EDITS,
    area_ops: [{ action: rule, area_id: area.area_id, provenance: "ui_edit" as const }],
  });
  const offer: Suggestion = {
    ...journey,
    target: "area",
    label: area.name,
    does: `${area.name}: do you want Burro to look only there, or to leave it out?`,
    follows: "",
    note: "",
    add_all: "",
    // What keeps a rule for an area from being taken is said by its ways, which mark no guess.
    only_by_choice: false,
    choices: [
      { id: "more", direction: "more", label: `Look only in ${area.name}`, guess: false, operations: ruled("only") },
      { id: "less", direction: "less", label: "Leave it out of the results", guess: false, operations: ruled("exclude") },
      skip,
    ],
  };
  return () =>
    responseFrom({
      ...recorded,
      body: { ...recorded.body, data: { ...recorded.body.data, suggestions: [offer, ...beside] } },
    });
}

/** The first area of the made-up city, which stands for whichever area a sentence names. */
const [named] = recordedAnswer("list_areas", "areas").body.data.areas;
if (!named) throw new Error("the recording holds no area");

async function say(user: Awaited<ReturnType<typeof openSearch>>["user"], words: string) {
  await user.clear(promptBox());
  await user.type(promptBox(), words);
  await user.click(screen.getByRole("button", { name: PROMPT.submit }));
  await settled();
}

beforeEach(() => setOnline(true));

describe("a search for somewhere to stay", () => {
  test("test_a_sentence_that_says_a_visit_is_ranked_as_one_and_what_burro_understood_says_visiting", async () => {
    const read = recordedAnswer("interpret", "visiting/interpret").body.data;
    const { user, api } = await openSearch(visiting());

    await say(user, sentenceOf("visiting/interpret"));
    await everyChip(user);

    expect([read.spec.tenure, read.spec.tenure_from]).toEqual(["visit", "stated"]);
    // What is ranked is the search the service read, which is the request it was recorded taking.
    expect(api.lastCallTo("rank").body).toEqual(recordedAnswer("rank", "visiting/rank").request.body);
    expect(results().length).toBeGreaterThan(0);
    // The chip that said Renting or Buying says Visiting: the person said so, and it is not assumed.
    expect(chips().at(-1)).toBe("Visiting");
    expect(within(understood()).queryByRole("button", { name: `${CHIPS.remove}: Visiting` })).toBeNull();
  });

  test("test_a_search_with_a_budget_that_becomes_a_visit_is_told_that_a_visit_has_none_and_nothing_of_renting_or_buying", async () => {
    // A search for a home to rent, with a budget, as it was recorded becoming a visit.
    const became = recordedAnswer("rank", "visiting/rank-becomes");
    const before = (became.request.body as { spec: InterpretData["spec"] }).spec;
    expect([before.tenure, before.budget.amount]).toEqual(["rent", 1800]);
    const first = recordedAnswer("interpret", "interpret-first");
    const home = { ...first, body: { ...first.body, data: { ...first.body.data, spec: before } } };
    const { user, api } = await openSearch(
      standInApi()
        .on("interpret", () => responseFrom(home))
        .on("rank", withTheSpecSent("rank-first"))
        .on("explain_top", reasonsFor("rank-first", "explanations-first")),
    );
    await say(user, sentenceOf("interpret-first"));
    api.on("interpret", "visiting/interpret").on("rank", "visiting/rank-becomes").on("explain_top", "visiting/explanations");

    await say(user, sentenceOf("visiting/interpret"));

    const said = screen.getAllByRole("status").map((line) => line.textContent ?? "").join(" ");
    expect(said).toContain(STATUS.budgetWentForAVisit);
    expect(said).not.toContain(STATUS.budgetWent);
    expect(said).not.toMatch(/pay in rent|pay to buy|type a new one/);
  });

  test("test_no_chip_of_a_budget_or_of_a_home_is_drawn_for_a_visit", async () => {
    const { user } = await openSearch(visiting());

    await say(user, sentenceOf("visiting/interpret"));
    await everyChip(user);

    expect(chips().join(" ")).not.toMatch(/£|a month|bedroom|\bflat\b|\bhouse\b|Renting|Buying/i);
    // Nor does what Burro says of the search, beside the box, speak of what a home costs.
    const box = screen.getByRole("region", { name: SEARCH.formLabel }).cloneNode(true) as HTMLElement;
    box.querySelectorAll("textarea").forEach((field) => field.remove());
    expect(box.textContent).not.toMatch(/£|budget|\brent\b|a month/i);
  });

  test("test_a_visit_said_in_a_sentence_that_is_no_plain_list_is_taken_with_what_stands_beside_it", async () => {
    // The service applies nothing of such a sentence, and returns what it noticed: that the
    // person is visiting, and what they want around them. Burro takes both, and asks nothing.
    const noticed = recordedAnswer("interpret", "visiting/interpret-said").body.data;
    const { user, api } = await openSearch(visiting().on("interpret", "visiting/interpret-said"));

    await say(user, sentenceOf("visiting/interpret-said"));
    await everyChip(user);

    expect(noticed.suggestions.map((one) => [one.target, one.label])).toEqual([
      ["tenure", "Visiting"],
      ["tag:leafy", "Leafy"],
    ]);
    expect(api.callsTo("rank")).toHaveLength(1);
    const asked = sent(api.lastCallTo("rank").body);
    expect(asked.spec.tenure).toBe("rent");
    expect(asked.operations?.budget_ops.map((edit) => [edit.action, edit.tenure, edit.amount])).toEqual([["set", "visit", 0]]);
    expect(asked.operations?.tag_ops.map((edit) => edit.tag_id)).toEqual(["leafy"]);
    // The person said that they are visiting: the chip says so, and nothing of it is assumed.
    expect(chips().at(-1)).toBe("Visiting");
    expect(chips().join(" ")).not.toMatch(/£|a month|bedroom/i);
    expect(thePage()).not.toMatch(/Choose what to add|Which (place|area) did you mean/);
  });

  test("test_what_a_night_costs_is_no_budget_and_the_visit_that_the_words_suggest_says_that_it_was_assumed", async () => {
    // "A hotel for so much a night near a place": Burro holds no price of a hotel, and says
    // so in the words the page has for what it cannot hold. Nobody said that they are
    // visiting: Burro takes it, and the chip says that it was assumed.
    const noticed = recordedAnswer("interpret", "visiting/interpret-night").body.data;
    const [, journey] = noticed.suggestions;
    const place = journey?.choices[0]?.operations.commute_ops[0]?.place_id ?? "";
    const { user, api } = await openSearch(
      visiting()
        .on("interpret", "visiting/interpret-night")
        .on("rank", rankedTo({ id: place, name: journey?.label ?? "", kind: "station" })),
    );

    await say(user, sentenceOf("visiting/interpret-night"));
    await everyChip(user);

    expect(noticed.unmet).toContain("prices_and_hours");
    expect(thePage().includes(UNMET.prices_and_hours)).toBe(true);
    const asked = sent(api.lastCallTo("rank").body);
    expect(asked.operations?.budget_ops.map((edit) => [edit.tenure, edit.amount])).toEqual([["visit", 0]]);
    expect(asked.operations?.commute_ops.map((edit) => edit.place_id)).toEqual([place]);
    // No amount is sent, and none is drawn anywhere but in the box.
    expect(api.lastCallTo("rank").sent?.includes("150")).toBe(false);
    expect(thePage().includes("150")).toBe(false);
    expect(chips().at(-1)).toBe(`Visiting ${CHIPS.assumed}`);
    // The journey was said, and one press added it: its place is the person's own.
    expect(chips().some((chip) => chip.startsWith(`${journey?.label},`) || chip === journey?.label)).toBe(true);
    expect(chips().join(" ")).not.toMatch(/£|a month|bedroom/i);
  });

  test("test_a_journey_the_service_cannot_tell_is_needed_waits_for_the_person_and_the_line_names_it_as_a_journey", async () => {
    // "Visiting my mother in a place" names a place to reach, which may be the mother's to
    // reach and not the person's. The service says that the journey waits for the person:
    // Burro adds none on a guess, and says where it is added.
    const noticed = recordedAnswer("interpret", "visiting/interpret-mother").body.data;
    const [journey] = noticed.suggestions;
    const { user, api } = await openSearch(visiting().on("interpret", "visiting/interpret-mother"));

    await say(user, sentenceOf("visiting/interpret-mother"));

    expect(noticed.suggestions.map((one) => [one.target, one.only_by_choice])).toEqual([["commute", true]]);
    expect(api.callsTo("rank")).toEqual([]);
    const left = screen.getByRole("status", { name: LEFT_OUT.title });
    expect((left.querySelector("details") as HTMLDetailsElement).open).toBe(true);
    expect(left.querySelector("summary")?.textContent).toBe(
      `${LEFT_OUT.title}: ${LEFT_OUT.ofAJourney(journey?.label ?? "no place")}`,
    );
    expect(within(left).getAllByRole("listitem").map((item) => item.textContent)).toEqual([
      `${LEFT_OUT.ofAJourney(journey?.label ?? "no place")}. ${LEFT_OUT.why.journey}`,
    ]);
    expect(thePage()).not.toMatch(/do you want Burro|Which (place|area) did you mean|Choose what to add/);
  });

  test("test_a_journey_a_service_leaves_to_the_page_is_added_and_its_chip_says_that_it_was_assumed", async () => {
    // A service that does not say that the journey waits: Burro adds it, and the chip of
    // the place says after its name that it was assumed.
    const recorded = recordedAnswer("interpret", "visiting/interpret-mother");
    const [journey] = recorded.body.data.suggestions;
    if (!journey) throw new Error("the recording holds no offer");
    const place = journey.choices[0]?.operations.commute_ops[0]?.place_id ?? "";
    const left = { ...recorded.body.data, suggestions: [{ ...journey, only_by_choice: false, note: "" }] };
    const { user, api } = await openSearch(
      visiting()
        .on("interpret", () => responseFrom({ ...recorded, body: { ...recorded.body, data: left } }))
        .on("rank", rankedTo({ id: place, name: journey.label, kind: "landmark" })),
    );

    await say(user, sentenceOf("visiting/interpret-mother"));
    await everyChip(user);

    const asked = sent(api.lastCallTo("rank").body);
    expect(asked.operations?.commute_ops.map((edit) => [edit.action, edit.place_id])).toEqual([["add", place]]);
    expect(asked.operations?.budget_ops).toEqual([]);
    expect(chips().find((chip) => chip.startsWith(journey.label))?.startsWith(`${journey.label} ${CHIPS.assumed}`)).toBe(true);
  });

  test("test_an_area_that_is_named_beside_somebody_else_leaves_no_area_out_and_the_line_says_what_was_not_done", async () => {
    // "Visiting my mother in" an area. The service offers a rule for the area, to look only
    // there or to leave it out, and guesses at neither. The first way was taken: one area
    // was ranked, and every other was left out on a guess.
    // Beside it, that it is not noisy, which is said of where the person would live.
    const [noise] = noisyAtHome().body.data.suggestions.slice(1);
    if (!noise) throw new Error("the recording holds too little");
    const { user, api } = await openSearch(
      standInApi()
        .on("interpret", offeringARuleFor(named, [noise]))
        .on("rank", "rank-suggestion-chosen")
        .on("explain_top", "explanations-suggestion-chosen"),
    );

    await say(user, `visiting my mother in ${named.name}, where it is not noisy`);

    // What stood beside it is taken and ranked, and no rule for an area is sent.
    expect(api.callsTo("rank")).toHaveLength(1);
    const asked = sent(api.lastCallTo("rank").body);
    expect(asked.operations?.area_ops).toEqual([]);
    expect(asked.operations?.weight_ops.map((edit) => edit.feature_id)).toEqual(["noise_exposure"]);
    // Every area is ranked that was, and the line that says what happened says how many.
    const ranked = recordedAnswer("rank", "rank-suggestion-chosen").body.data;
    expect(ranked.filtered).toEqual([]);
    expect(thePage().includes(STATUS.rankedUnnamed(ranked.areas_ranked))).toBe(true);
    // The line names what was left out, which is what to do with the area, and not the area.
    const left = screen.getByRole("status", { name: LEFT_OUT.title });
    expect(left.querySelector("summary")?.textContent).toBe(
      `${LEFT_OUT.title}: ${LEFT_OUT.ofAnArea(named.name)}; ${LEFT_OUT.words}`,
    );
    expect(within(left).getAllByRole("listitem")[0]?.textContent).toBe(`${LEFT_OUT.ofAnArea(named.name)}. ${LEFT_OUT.why.area}`);
    // Nothing is asked, and nothing of it is a chip of what Burro understood.
    expect(thePage()).not.toMatch(/do you want Burro|Which (place|area) did you mean|Choose what to add/);
    await everyChip(user);
    expect(chips().join(" ")).not.toMatch(new RegExp(`${named.name}|${CHIPS.only}|${CHIPS.hidden}`));
  });

  test("test_where_a_rule_for_an_area_is_all_that_was_noticed_nothing_is_ranked_and_the_line_stands_open_with_why", async () => {
    const { user, api } = await openSearch(standInApi().on("interpret", offeringARuleFor(named)));

    await say(user, `visiting my mother in ${named.name}`);

    expect(api.callsTo("rank")).toEqual([]);
    expect(screen.queryByRole("list", { name: RESULTS.listLabel })).toBeNull();
    const left = screen.getByRole("status", { name: LEFT_OUT.title });
    expect((left.querySelector("details") as HTMLDetailsElement).open).toBe(true);
    expect(left.textContent?.includes(LEFT_OUT.why.area)).toBe(true);
    // Nothing is ranked, and the page says so: what it says of the area is true of that too.
    expect(thePage().includes(WAIT.notYet)).toBe(true);
    expect(LEFT_OUT.why.area).not.toMatch(/\bhas ranked\b|\bstill ranks\b|\bleft every area in\b/);
  });

  test("test_a_home_and_a_budget_typed_into_a_visit_are_left_out_and_the_line_says_why_in_the_services_words", async () => {
    const unused = recordedAnswer("interpret", "visiting/interpret-home");
    const [flat, budget] = unused.body.data.suggestions;
    const { user, api } = await openSearch(visiting());
    await say(user, sentenceOf("visiting/interpret"));
    const ranked = api.callsTo("rank").length;
    api.on("interpret", "visiting/interpret-home");

    await say(user, `${sentenceOf("visiting/interpret")}, ${sentenceOf("visiting/interpret-home")}`);

    // What was sent to be read was sent with the search as it stands, which is a visit.
    expect((api.lastCallTo("interpret").body as { spec: { tenure: string } }).spec.tenure).toBe("visit");
    // Nothing came of the words, so nothing is ranked again, and the answer stays.
    expect(api.callsTo("rank")).toHaveLength(ranked);
    expect(results().length).toBeGreaterThan(0);
    const left = screen.getByRole("status", { name: LEFT_OUT.title });
    // The name the service gives the budget holds the amount that was typed: the page
    // names the thing itself, and the amount is drawn in the box and nowhere else.
    expect(budget?.label).toMatch(/2,000/);
    expect(left.querySelector("summary")?.textContent).toBe(
      `${LEFT_OUT.title}: ${flat?.label}; ${LEFT_OUT.named_by_the_page.budget}`,
    );
    expect(within(left).getAllByRole("listitem").map((item) => item.textContent)).toEqual([
      `${flat?.label}. ${flat?.does} ${flat?.note}`,
      `${LEFT_OUT.named_by_the_page.budget}. ${budget?.does} ${budget?.note}`,
    ]);
    expect(thePage()).not.toMatch(/2,000|2000/);
    await everyChip(user);
    expect(chips().at(-1)).toBe("Visiting");
    expect(chips().join(" ")).not.toMatch(/£|a month|bedroom/i);
  });
});
