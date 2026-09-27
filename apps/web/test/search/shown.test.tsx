/**
 * What the search page shows, and the words it uses, as a person who has
 * never seen it finds them. docs/design/web.md, sections 4 and 5.2.
 *
 * Two of the tests below waited on the API, marked as failing, until it named
 * every place of a spec and said every reason from its good side. It does
 * both now, and the marks are off. A test that waits on the API is marked
 * `test.failing`: it passes while it fails, and fails the day it passes.
 */

import { readdirSync } from "node:fs";

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { picturesAtEnds } from "@/components/kit/Ends/picture";
import { SearchApp } from "@/components/SearchApp/SearchApp";
import { Shell } from "@/components/Shell/Shell";
import { Town } from "@/components/Town/Town";

import { CARD } from "@/content/card";
import { CRIME_ACCOUNT, crimeVibes } from "@/content/crime";
import { COMBINE } from "@/content/labels";
import { MAP } from "@/content/map";
import { CHIPS, JOURNEYS, RESULTS, SOURCE, STRIP } from "@/content/search";
import { TOWN } from "@/content/town";
import { readRecorded, recordedAnswer, recordedFolder } from "@/lib/api/recorded";
import type { ExplanationsData, RankData } from "@/lib/api/schema";
import type { Mark } from "@/lib/town/bands";
import { saidOf } from "@/lib/town/said";

import { standInApi, type Responder } from "../support/api";
import {
  areas,
  arrived,
  everyChip,
  everyResult,
  meta,
  openSearch,
  promptBox,
  results,
  search,
  settled,
  workingOf,
} from "../support/search";

jest.mock("next/navigation", () => ({ usePathname: () => "/" }));

const sentenceOf = (scenario: string) =>
  (recordedAnswer("interpret", scenario).request.body as { text: string }).text;

/** A household with two places to reach, as it was recorded: the sentence, its ranking and its reasons. */
const twoJourneys = () =>
  standInApi()
    .on("interpret", "interpret-two-journeys")
    .on("rank", "rank-two-journeys")
    .on("explain_top", "explanations-two-journeys");

async function searchedForTwoPlaces() {
  const opened = await openSearch(twoJourneys());
  await search(opened.user, sentenceOf("interpret-two-journeys"));
  await settled();
  return opened;
}

const nameOf = (areaId: string) => areas.find((area) => area.area_id === areaId)?.name ?? "";

/** Everything on the page that is a place shown by number, and not by its name. */
const shownByNumber = () =>
  [...document.querySelectorAll("main li, main th, main legend, main button, main p")]
    .map((element) => element.textContent ?? "")
    .filter((text) => /\bPlace \d+\b/.test(text));

/** The part of a result under the word "Trade-off". */
const tradeOff = (result: HTMLElement) =>
  within(result).getByRole("heading", { name: RESULTS.tradeOffTitle }).parentElement as HTMLElement;

/**
 * Opens the working of the result of an area, and says whether it holds the source of a
 * trade-off: the heading of that part, or the key that is named for it.
 */
async function sourceOfATradeOffIn(user: ReturnType<typeof userEvent.setup>, name: string): Promise<boolean> {
  const working = within(await workingOf(user, name));
  return (
    working.queryByRole("heading", { name: CARD.sourceOfTheTradeOff }) !== null ||
    working.queryByRole("button", { name: SOURCE.buttonFor(RESULTS.sourceOfTradeOff(name)) }) !== null
  );
}

describe("a place the person named", () => {
  test("test_every_place_the_person_named_is_shown_by_its_name_wherever_it_is_shown", async () => {
    // Seen in a browser: one of two workplaces was shown as "Place 1". The answers of routes
    // 1, 2 and 10 now name every place of the spec they return: section 13, gap 1.
    const { user } = await searchedForTwoPlaces();
    await everyChip(user);
    await everyResult(user);
    const [top] = recordedAnswer("rank", "rank-two-journeys").body.data.ranked;
    const result = await workingOf(user, nameOf(top?.area_id ?? ""));
    const chips = within(screen.getByRole("region", { name: CHIPS.label }));

    expect(chips.getByRole("button", { name: /^Foxholt Market/ })).toBeInTheDocument();
    expect(chips.getByRole("button", { name: /^Wexmoor University/ })).toBeInTheDocument();
    expect(within(result).getAllByRole("rowheader").map((header) => header.textContent)).toEqual(
      expect.arrayContaining(["Foxholt Market", "Wexmoor University"]),
    );
    expect(shownByNumber()).toEqual([]);
    expect(screen.queryByText(/cannot show the name/)).toBeNull();
  });

  test("test_with_two_places_the_page_says_which_journey_counts_before_the_settings_are_opened", async () => {
    const { user } = await searchedForTwoPlaces();
    await everyChip(user);
    const chips = within(screen.getByRole("region", { name: CHIPS.label }));
    const [top] = recordedAnswer("rank", "rank-two-journeys").body.data.ranked;

    expect(chips.getByRole("button", { name: new RegExp(`^${COMBINE.slowest}`) })).toHaveTextContent(CHIPS.assumed);
    const result = await workingOf(user, nameOf(top?.area_id ?? ""));
    expect(within(result).getByText(JOURNEYS.usesOne("Wexmoor University"))).toBeInTheDocument();
  });
});

describe("what is said under the word trade-off", () => {
  /** The reasons as they were recorded, with the trade-off of the first area changed. */
  const withFirstTradeOff = (change: (data: ExplanationsData) => ExplanationsData): Responder => () => {
    const recorded = readRecorded("explanations-first");
    const body = recorded.body as { data: ExplanationsData };
    return { ...recorded, body: { ...body, data: change(body.data) } };
  };

  test("test_when_the_api_gives_no_trade_off_the_card_says_that_none_was_found", async () => {
    const none = withFirstTradeOff((data) => ({
      ...data,
      explanations: data.explanations.map((one, at) => (at === 0 ? { ...one, trade_off: null } : one)),
    }));
    const { user } = await openSearch(
      standInApi().on("interpret", "interpret-first").on("rank", "rank-first").on("explain_top", none),
    );
    await search(user);
    await settled();

    expect(tradeOff(results()[0] as HTMLElement)).toHaveTextContent(RESULTS.noTradeOff);
    expect(within(tradeOff(results()[0] as HTMLElement)).queryByRole("button")).toBeNull();
    // The next card has one, and says it in the API's words.
    const given = recordedAnswer("explain_top", "explanations-first").body.data.explanations[1]?.trade_off;
    expect(tradeOff(results()[1] as HTMLElement)).toHaveTextContent(given?.text ?? "no trade-off");
    // The source of a trade-off stands in the working, of a result that has one and of no other.
    const [first, next] = recordedAnswer("rank", "rank-first").body.data.ranked;
    expect(await sourceOfATradeOffIn(user, nameOf(first?.area_id ?? ""))).toBe(false);
    expect(await sourceOfATradeOffIn(user, nameOf(next?.area_id ?? ""))).toBe(true);
  });

  test("test_a_strength_the_api_gave_as_a_trade_off_is_not_shown_as_one", async () => {
    // As an engine before 1.3.0 answered: the least good thing, though the area does it well.
    const text = "A strength, said as an older engine would give it.";
    const strength = withFirstTradeOff((data) => ({
      ...data,
      explanations: data.explanations.map((one) =>
        one.area_id === "syn-n0006"
          ? {
              ...one,
              trade_off: {
                text,
                fact_ids: ["syn-n0006/tag/quiet_residential"],
                origin: "template" as const,
                replaced: false,
              },
            }
          : one,
      ),
    }));
    const { user } = await openSearch(
      standInApi().on("interpret", "interpret-first").on("rank", "rank-first").on("explain_top", strength),
    );
    await search(user);
    await settled();

    // Recorded: Farrowmere is first, and is in the fourth band of five for quiet streets.
    expect(nameOf("syn-n0006")).toBe("Farrowmere");
    expect(within(results()[0] as HTMLElement).getByRole("heading", { name: "Farrowmere" })).toBeInTheDocument();
    expect(document.body.textContent?.includes(text)).toBe(false);
    expect(tradeOff(results()[0] as HTMLElement)).toHaveTextContent(RESULTS.noTradeOff);
    // Nor does the working give it a source as the trade-off of the area.
    expect(await sourceOfATradeOffIn(user, "Farrowmere")).toBe(false);
    expect(document.body.textContent?.includes(text)).toBe(false);
  });
});

describe("the side a sentence is said from", () => {
  const SEARCHES = readdirSync(recordedFolder())
    .filter((name) => /^explanations-.*\.json$/.test(name))
    .map((name) => name.slice("explanations-".length, -".json".length));

  /** The word each sentence of a kind compares by, for each thing the recordings hold a sentence about. */
  function comparedBy(kind: "reasons" | "trade_off"): Map<string, Set<string>> {
    const words = new Map<string, Set<string>>();
    for (const search of SEARCHES) {
      const { explanations, facts } = recordedAnswer("explain_top", `explanations-${search}`).body.data;
      for (const explanation of explanations) {
        const sentences = kind === "reasons" ? explanation.reasons : [explanation.trade_off];
        for (const sentence of sentences) {
          const fact = facts.find((one) => one.fact_id === sentence?.fact_ids[0]);
          // A fact holds the word for each side. The sentence says which one was used.
          const word = [fact?.slots.comparative_worse, fact?.slots.comparative].find(
            (one) => one !== undefined && sentence?.text.includes(` ${one} `),
          );
          if (fact === undefined || word === undefined) continue;
          words.set(`${fact.kind}:${fact.key}`, new Set([...(words.get(`${fact.kind}:${fact.key}`) ?? []), word]));
        }
      }
    }
    return words;
  }

  /** The things a reason is said of in the very word a trade-off is said of them. */
  function saidFromTheBadSide(): string[] {
    const bad = comparedBy("trade_off");
    return [...comparedBy("reasons")].flatMap(([thing, words]) =>
      [...words].filter((word) => bad.get(thing)?.has(word)).map((word) => `${thing} ${word}`),
    );
  }

  /** What stands under "Why it fits" in the working of a result: each line of it, as it is written. */
  const reasonsIn = (result: HTMLElement) =>
    within(within(result).getByRole("heading", { name: RESULTS.reasonsTitle }).parentElement as HTMLElement)
      .getAllByRole("listitem")
      .map((reason) => reason.textContent);

  test("test_a_reason_is_shown_word_for_word_as_the_api_said_it", async () => {
    const ranking: RankData = recordedAnswer("rank", "rank-buyer-family").body.data;
    const { explanations } = recordedAnswer("explain_top", "explanations-buyer-family").body.data;
    const { user } = await openSearch(
      standInApi()
        .on("interpret", "interpret-buyer-family")
        .on("rank", "rank-buyer-family")
        .on("explain_top", "explanations-buyer-family"),
    );
    await search(user, sentenceOf("interpret-buyer-family"));
    await settled();

    // The website lays the sentence out. It does not reword it, and it does not turn it round.
    // A result says no reason until its working is opened. Every reason is there, under
    // "Why it fits", in the order the API gave them, and each ends in the key of its source.
    for (const [at, area] of ranking.ranked.slice(0, 5).entries()) {
      const reasons = explanations.find((one) => one.area_id === area.area_id)?.reasons ?? [];
      const result = results()[at] as HTMLElement;
      expect([at, reasons.length > 0]).toEqual([at, true]);
      expect(within(result).queryByRole("heading", { name: RESULTS.reasonsTitle })).toBeNull();
      expect(reasons.filter((reason) => result.textContent?.includes(reason.text))).toEqual([]);

      await workingOf(user, nameOf(area.area_id));

      expect(reasonsIn(result)).toEqual(
        reasons.map((reason) => `${reason.text}${reason.origin === "model" ? RESULTS.byModel : ""}${SOURCE.button}`),
      );
    }
  });

  test("test_no_reason_is_said_in_the_word_a_trade_off_is_said_in", () => {
    // Seen in a browser: under "Why it fits", a walk to a park that was "further than" 47%
    // of areas. A reason is now said from its good side: section 13, gap 17.
    expect(comparedBy("reasons").size).toBeGreaterThan(3);
    expect(comparedBy("trade_off").size).toBeGreaterThan(3);
    expect(saidFromTheBadSide()).toEqual([]);
    // The same thing is said from either side, by which way it falls for the area.
    expect([...(comparedBy("reasons").get("feature:park_proximity") ?? [])]).toEqual(["closer than"]);
    expect([...(comparedBy("trade_off").get("feature:park_proximity") ?? [])]).toEqual(["further than"]);
  });
});

describe("the word gritty, which is built two ways", () => {
  /** The page as it is built on a release, with the service that holds that release behind it. */
  async function openOn(variant: "" | "variant-a/") {
    const form = recordedAnswer("get_meta", `${variant}meta`).body;
    const listed = recordedAnswer("list_areas", `${variant}areas`).body.data;
    const api = standInApi()
      .on("interpret", `${variant}interpret-gritty`)
      .on("rank", `${variant}rank-gritty`)
      .on("explain_top", `${variant}explanations-gritty`);
    const user = userEvent.setup({ delay: null });
    render(
      <Shell meta={form.meta}>
        <SearchApp meta={form.data} areas={listed.areas} bands={listed.bands} client={api.client} />
      </Shell>,
    );
    await arrived();
    await user.type(promptBox(), sentenceOf(`${variant}interpret-gritty`));
    await user.keyboard("{Enter}");
    await settled();
    return { api, user, form, listed };
  }
  const chipsSaid = () =>
    within(screen.getByRole("region", { name: CHIPS.label }))
      .getAllByRole("listitem")
      .map((chip) => chip.textContent?.replace(/×|Turn/g, "") ?? "");
  /** What was recorded of the search on a release: the vibe the word was read as, and what was written of the first area. */
  function recordedOn(variant: "" | "variant-a/") {
    const ranking = recordedAnswer("rank", `${variant}rank-gritty`).body.data;
    const { explanations, facts } = recordedAnswer("explain_top", `${variant}explanations-gritty`).body.data;
    const { tags } = recordedAnswer("get_meta", `${variant}meta`).body.data;
    const [first] = ranking.ranked;
    const vibe = tags.find((tag) => tag.tag_id === ranking.spec.tags[0]?.tag_id);
    const written = explanations.find((one) => one.area_id === first?.area_id);
    if (first === undefined || vibe === undefined || written === undefined) throw new Error("Nothing was recorded of it.");
    const listed = recordedAnswer("list_areas", `${variant}areas`).body.data.areas;
    const name = listed.find((area) => area.area_id === first.area_id)?.name ?? "";
    /** True of a sentence that is about the vibe: the first fact it cites is the fact of the vibe. */
    const isOfTheVibe = (sentence: { readonly fact_ids: readonly string[] } | null) => {
      const about = facts.find((fact) => fact.fact_id === sentence?.fact_ids[0]);
      return about?.kind === "tag" && about.key === vibe.tag_id;
    };
    return { vibe, written, name, isOfTheVibe };
  }
  /** Where a drawing is served from, as the style of what draws it says. */
  const served = (name: string) => `url("/art/${name}.png")`;
  /**
   * Opens the working of the first result, and in it the source of everything that is of the
   * vibe: of each sentence about it, and of its figure where no sentence of the result holds
   * it. It answers with what each source says, once it is open.
   */
  async function sourcesOfTheVibe(user: ReturnType<typeof userEvent.setup>, variant: "" | "variant-a/") {
    const { vibe, written, name, isOfTheVibe } = recordedOn(variant);
    const working = within(await workingOf(user, name));
    const of = [
      ...written.reasons.flatMap((reason, at) => (isOfTheVibe(reason) ? [RESULTS.sourceOfReason(at + 1, name)] : [])),
      // The figure of the vibe stands under the trade-off where the trade-off is about it, and
      // with the figures behind each vibe where it is not.
      isOfTheVibe(written.trade_off) ? RESULTS.sourceOfTradeOff(name) : vibe.label,
    ];
    const said: string[] = [];
    for (const what of of) {
      const key = working.getByRole("button", { name: SOURCE.buttonFor(what) });
      await user.click(key);
      said.push(document.getElementById(key.getAttribute("aria-controls") ?? "")?.textContent ?? "");
    }
    return said;
  }

  test("test_where_it_is_a_scale_the_chip_names_the_end_and_nothing_is_assumed", async () => {
    const { form } = await openOn("");
    const { vibe } = recordedOn("");

    expect(form.data.gritty_variant).toBe("b");
    expect(chipsSaid()).toContain(`${CHIPS.towards("Gritty", "Gritty")}, ${CRIME_ACCOUNT.chip}`);
    expect(chipsSaid().filter((said) => said.includes("“"))).toEqual([]);
    expect(screen.getByRole("button", { name: CHIPS.turnTo("Gritty", "Polished") })).toBeInTheDocument();
    // The first result shows where it sits between the two ends: a gauge, on the line of the
    // vibe, with a picture at each end. No name of an end is written on a result: the name
    // of the gauge says both ends, and which of them was asked for, to whoever hears the page.
    const card = results()[0] as HTMLElement;
    const lines = within(card).getAllByRole("listitem");
    expect(lines.map((line) => line.textContent)).toEqual([vibe.label]);
    const gauge = within(lines[0] as HTMLElement).getByRole("img");
    expect(gauge).toHaveAccessibleName(
      `${STRIP.band(5)}, ${STRIP.from("Polished", "Gritty")}, ${STRIP.askedFor("Gritty")}`,
    );
    expect(card.textContent?.includes("Polished")).toBe(false);
    // The picture of each end is chosen by the id the API gives the vibe, and the two are not one.
    const [low, high] = picturesAtEnds(vibe.tag_id);
    const ends = [...gauge.querySelectorAll<HTMLElement>("[aria-hidden='true'][style*='/art/end-']")];
    expect(ends.map((end) => end.style.getPropertyValue("--art"))).toEqual([served(low), served(high)]);
    expect(low === high).toBe(false);
  });

  test("test_where_it_is_one_part_of_a_place_the_chip_quotes_the_word_and_says_it_was_assumed", async () => {
    const { form, api } = await openOn("variant-a/");

    expect(form.data.gritty_variant).toBe("a");
    // The word has two meanings. The chip says which was taken, in the row, before anything is pressed.
    expect(chipsSaid()).toContain(`Works and warehouses, ${CHIPS.readFrom("gritty")} ${CHIPS.assumed}`);
    expect(screen.queryByRole("button", { name: /^Turn/ })).toBeNull();
    // The word is the reader's own, from its answer. What was typed is sent once, and kept nowhere.
    expect(recordedAnswer("interpret", "variant-a/interpret-gritty").body.data.assumptions).toContainEqual(
      expect.objectContaining({ code: "word", word: "gritty" }),
    );
    expect(api.callsTo("interpret")).toHaveLength(1);
    // The first result shows where it sits on it: a picture, counted from least to most.
    const card = results()[0] as HTMLElement;
    expect(card.textContent?.includes("Works and warehouses")).toBe(true);
    const pictures = within(card).getAllByRole("img").map((one) => one.getAttribute("aria-label") ?? "");
    expect(pictures.some((said) => said.includes(STRIP.from(STRIP.least, STRIP.most)) && said.endsWith(STRIP.asked))).toBe(true);
  });

  test("test_where_it_counts_recorded_crime_the_results_say_so_before_anything_is_opened", async () => {
    // Seen in a browser: "somewhere a bit gritty" was read, and areas were ranked on recorded
    // criminal damage among other things. The words "recorded" and "crime" were nowhere on the
    // page, even with the source of the sentence open.
    const { user } = await openOn("");
    const understood = screen.getByRole("region", { name: CHIPS.label });

    expect(understood.textContent?.includes("recorded crime")).toBe(true);
    // No key of a source stands on a result until its working is opened. There, the source of
    // the sentence about the vibe names the parts of its recipe that are of crime, and so
    // does the source of its figure.
    const said = await sourcesOfTheVibe(user, "");
    const parts = crimeVibes(recordedAnswer("get_meta", "meta").body.data)[0]?.parts.map((part) => part.label) ?? [];
    expect(parts).toHaveLength(2);
    expect(said).toHaveLength(2);
    expect(said.map((source) => source.includes(CRIME_ACCOUNT.counts))).toEqual([true, true]);
    for (const part of parts) expect(said.map((source) => source.includes(part))).toEqual([true, true]);
  });

  test("test_where_it_is_built_from_land_use_nothing_is_said_to_count_recorded_crime", async () => {
    const { user } = await openOn("variant-a/");
    const said = await sourcesOfTheVibe(user, "variant-a/");

    expect(/recorded crime/i.test(screen.getByRole("region", { name: CHIPS.label }).textContent ?? "")).toBe(false);
    // Each source is open, and says what a source says: where the data is from.
    expect(said).toHaveLength(2);
    expect(said.map((source) => source.includes(SOURCE.dataFrom))).toEqual([true, true]);
    expect(said.map((source) => source.includes(CRIME_ACCOUNT.counts))).toEqual([false, false]);
    expect(results()[0]?.textContent?.includes(CRIME_ACCOUNT.counts)).toBe(false);
  });

  test("test_neither_way_of_building_it_holds_a_figure_about_who_lives_somewhere", () => {
    for (const variant of ["", "variant-a/"] as const) {
      const { features, tags } = recordedAnswer("get_meta", `${variant}meta`).body.data;
      const gritty = tags.find((tag) => tag.tag_id === "street_character" || tag.tag_id === "works_warehouses");
      const parts = (gritty?.terms ?? []).map((term) => features.find((one) => one.feature_id === term.feature_id));

      expect(parts.length).toBeGreaterThan(0);
      // A part is a fact about a place, its buildings or what was recorded there. There is no other kind.
      for (const part of parts) {
        if (part !== undefined) expect(["place", "buildings", "events"]).toContain(part.describes);
      }
      expect(gritty?.cannot_see.length).toBeGreaterThan(1);
    }
  });
});

describe("the town of a result", () => {
  /** The searches whose strips differ most: what was asked for is what a strip holds. */
  const SEARCHES = ["first", "buyer-family", "nights-out", "scale", "two-journeys", "by-the-river"] as const;
  const profileOf = (areaId: string) =>
    recordedAnswer("get_area", `area/${areas.find((area) => area.area_id === areaId)?.slug ?? ""}`).body.data;
  const townOf = (result: Element) => result.querySelector("figure") as HTMLElement;
  const heardOf = (town: Element) => within(town as HTMLElement).getByRole("img").getAttribute("aria-label");
  /** What the part draws and says of what it is handed, with nothing about it. */
  function alone(marks: readonly Mark[], name: string) {
    const { container, unmount } = render(<Town marks={marks} meta={meta.data} of={name} />);
    const town = { heard: heardOf(container), says: container.querySelector("figcaption")?.textContent };
    unmount();
    return town;
  }

  test.each(SEARCHES)("test_the_town_of_a_result_is_the_town_of_the_page_of_its_area_whatever_was_searched_for: %s", async (scenario) => {
    // Seen in a browser: drawn from the strip of its result, which holds what was asked for
    // and two more, the town of the first result said "Left blank: lit windows. What is not
    // known is not drawn.", and the page of that area drew them. The page holds where every
    // area sits, and hands it to the list.
    const { user } = await openSearch(
      standInApi()
        .on("interpret", `interpret-${scenario}`)
        .on("rank", `rank-${scenario}`)
        .on("explain_top", `explanations-${scenario}`)
        .on("search_places", "places-search"),
    );
    await search(user, sentenceOf(`interpret-${scenario}`));
    await settled();
    const ranked = recordedAnswer("rank", `rank-${scenario}`).body.data.ranked;

    expect(results().length).toBeGreaterThan(0);
    results().forEach((result, at) => {
      const areaId = ranked[at]?.area_id ?? "";
      const page = alone(profileOf(areaId).tags, nameOf(areaId));

      expect([at, heardOf(townOf(result))]).toEqual([at, page.heard]);
      expect([at, townOf(result).querySelector("figcaption")?.textContent]).toEqual([at, page.says]);
    });
  });

  test.each(SEARCHES)("test_a_part_of_a_town_is_blank_for_what_is_not_known_and_never_for_what_was_not_asked_for: %s", async (scenario) => {
    const { user } = await openSearch(
      standInApi()
        .on("interpret", `interpret-${scenario}`)
        .on("rank", `rank-${scenario}`)
        .on("explain_top", `explanations-${scenario}`)
        .on("search_places", "places-search"),
    );
    await search(user, sentenceOf(`interpret-${scenario}`));
    await settled();
    const ranked = recordedAnswer("rank", `rank-${scenario}`).body.data.ranked;
    /** How often a town says that something is not known of its area, whatever it is. */
    const timesNotKnown = (heard: string) => heard.split(TOWN.notKnown("")).length - 1;

    results().forEach((result, at) => {
      const areaId = ranked[at]?.area_id ?? "";
      // What the service holds no band for, of the area: that, and nothing else, is not known of it.
      const notKnown = saidOf(profileOf(areaId).tags, meta.data).filter(({ why }) => why === "unknown");
      const heard = heardOf(townOf(result)) ?? "";

      expect([at, timesNotKnown(heard)]).toEqual([at, notKnown.length]);
      for (const part of notKnown) expect([at, part.part, heard.includes(`${part.says}.`)]).toEqual([at, part.part, true]);
      // What is left blank for it is said in sight, in the words of the town, and of no other town.
      const inSight = townOf(result).querySelector("figcaption")?.textContent ?? "";
      expect([at, inSight.includes(TOWN.whyBlank.unknown)]).toEqual([at, notKnown.length > 0]);
    });
  });
});

describe("the map", () => {
  test("test_the_keys_that_move_the_map_are_not_said_where_there_is_no_map", async () => {
    // The test browser cannot draw a map, so the table stands in for it, with no keys to say.
    await openSearch();

    expect(screen.queryByText(MAP.keys)).toBeNull();
  });
});
