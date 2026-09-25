/**
 * An area's page, held to docs/design/web.md section 2: every figure is a
 * fact of the API's with its source and its date, nothing is filled in, and
 * the page reads with scripts off.
 */

import { readFileSync } from "node:fs";
import path from "node:path";

import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactElement } from "react";

import AreaPage, { generateStaticParams } from "@/app/[city]/[area]/page";
import { AreaProfile } from "@/components/AreaProfile/AreaProfile";
import { columnsOf } from "@/components/FactRow/FactRow";
import { SearchApp } from "@/components/SearchApp/SearchApp";
import { Shell } from "@/components/Shell/Shell";
import { AREA, LOOK, NAMED, PORTRAIT } from "@/content/area";
import { ONE_NUMBER } from "@/content/facts";
import { RESTS_ON } from "@/content/bands";
import { COMPARE, TRAY } from "@/content/compare";
import { CRIME_RULE } from "@/content/crime";
import { DIMENSION, MODE } from "@/content/labels";
import { JOURNEYS, SOURCE, STRIP } from "@/content/search";
import { CRIME_CAVEAT } from "@/content/settings";
import { BANNER } from "@/content/site";
import { sentenceOf } from "@/content/templates";
import { recordedAnswer } from "@/lib/api/recorded";
import type { AreaData, RankBody } from "@/lib/api/schema";
import { cannotSee, GROUPS, portraitOf, shownOn } from "@/lib/area/portrait";
import { alikeRows, costFacts, factsShown, featuresByDimension, sharedVibes, stationFacts } from "@/lib/area/profile";
import { readableDate } from "@/lib/format";
import { NO_EDITS } from "@/lib/search/edits";

import { standInApi } from "../support/api";
import { faultsIn } from "../support/axe";
import { figuresNotFrom, saidBy } from "../support/figures";
import { firstSearch, search, settled } from "../support/search";
import { watch } from "../support/watch";

jest.mock("next/navigation", () => ({
  ...jest.requireActual("next/navigation"),
  usePathname: () => "/synthetic/alderwick",
}));

const meta = recordedAnswer("get_meta", "meta").body;
const areas = recordedAnswer("list_areas", "areas").body.data.areas;
const bands = recordedAnswer("list_areas", "areas").body.data.bands;
const profile = (slug: string): AreaData => recordedAnswer("get_area", `area/${slug}`).body.data;
const at = (city: string, area: string) => ({ params: Promise.resolve({ city, area }) });

async function show(slug: string, city = "synthetic") {
  return render(<Shell meta={meta.meta}>{await AreaPage(at(city, slug))}</Shell>);
}

/** A part of the page, by the id the list of contents names it by. */
const part = (id: string) => {
  const found = document.getElementById(id);
  if (found === null) throw new Error("The page has no such part.");
  // A part that is open is found by its heading, and is the section that holds it.
  return found.tagName === "DETAILS" ? found : (found.closest("section") as HTMLElement);
};

/**
 * What the page says in site copy that holds a figure: a band in words, a share of a recipe,
 * how many parts of a recipe a band rests on, and how many vibes cannot place the area. Each
 * count is the API's, or is of a list the API sent.
 */
function siteCopyWithFigures(): string[] {
  const five = [1, 2, 3, 4, 5];
  const counts = Array.from({ length: 15 }, (_, at) => at);
  return [
    ...five.map((band) => STRIP.band(band)),
    ...five.flatMap((low) => five.map((high) => STRIP.bands(low, high))),
    ...Array.from({ length: 100 }, (_, at) => PORTRAIT.madeOf.shareOf(at + 1)),
    ...counts.flatMap((known) =>
      counts.flatMap((parts) => [RESTS_ON.short(String(known), String(parts)), RESTS_ON.full(String(known), String(parts))]),
    ),
    ...counts.map((count) => RESTS_ON.notCarried(count)),
    ...counts.flatMap((count) => counts.map((of) => PORTRAIT.short.unplaced(count, of))),
  ];
}

/** What `notFound()` throws. Next turns it into the page that says there is no page. */
async function notFoundAt(city: string, area: string): Promise<boolean> {
  try {
    await AreaPage(at(city, area));
    return false;
  } catch (error) {
    return String((error as { digest?: string }).digest).includes("404");
  }
}

describe("which areas have a page", () => {
  test("test_every_area_of_the_release_has_a_page_under_its_city", async () => {
    const pages = await generateStaticParams();

    expect(pages).toHaveLength(24);
    expect(pages).toEqual(areas.map((area) => ({ city: "synthetic", area: area.slug })));
  });

  test.each([
    ["synthetic", "nowhere-at-all"],
    ["synthetic", "Alderwick"],
    ["synthetic", "../meta"],
    ["synthetic", "syn-n0001"],
    ["london", "alderwick"],
    ["paris", "alderwick"],
  ])("test_an_address_the_release_has_no_area_at_is_a_page_not_found: /%s/%s", async (city, area) => {
    expect(await notFoundAt(city, area)).toBe(true);
  });
});

describe("an area whose prices are one number", () => {
  const data = recordedAnswer("get_area", "one-number/area").body.data;
  const form = recordedAnswer("get_meta", "one-number/meta").body.data;
  const geometry = recordedAnswer("get_geometry", "geometry").body.data;

  test("test_each_price_is_one_number_with_what_it_is_of_and_no_range_is_explained", () => {
    render(<AreaProfile data={data} meta={form} geometry={geometry} areas={[]} />);
    const cost = part("cost");
    const prices = costFacts(data, "buy");

    expect(prices.map((fact) => fact.template)).toEqual(Array(4).fill("cost_buy_median"));
    for (const fact of prices) {
      const row = within(cost).getByRole("group", { name: fact.slots.segment });
      expect(row).toHaveTextContent(`£${fact.slots.median}`);
      expect(row).toHaveTextContent(fact.slots.period ?? "no period");
      expect(row).toHaveTextContent(ONE_NUMBER);
      expect(row.textContent?.includes(" to £")).toBe(false);
    }
    // What the two figures of a range mean is said only where there is a range to read.
    expect(cost.textContent?.includes(AREA.cost.lead)).toBe(false);
    expect(cost.textContent?.includes(AREA.cost.confidence)).toBe(false);
    // The release holds no rent, and the page says so.
    expect(costFacts(data, "rent")).toEqual([]);
    expect(cost.textContent?.includes(AREA.cost.none.rent)).toBe(true);
  });

  test("test_every_figure_of_a_price_is_a_slot_of_its_fact", () => {
    render(<AreaProfile data={data} meta={form} geometry={geometry} areas={[]} />);

    expect(figuresNotFrom(part("cost"), saidBy(data.facts))).toEqual([]);
  });
});

describe("an area of data that is not finished", () => {
  test("test_what_a_range_of_costs_means_is_not_said_where_there_is_no_cost", () => {
    // Seen in a browser: "Half of homes of this kind cost between these two figures",
    // over "No rent figure in this data".
    const preview = recordedAnswer("get_area", "preview/area-alderwick").body.data;
    const form = recordedAnswer("get_meta", "preview/meta").body.data;
    const geometry = recordedAnswer("get_geometry", "preview/geometry").body.data;
    render(<AreaProfile data={preview} meta={form} geometry={geometry} areas={[]} />);
    const said = document.body.textContent ?? "";

    expect(preview.facts.some((fact) => fact.kind === "cost")).toBe(false);
    expect(said.includes(AREA.cost.none.rent)).toBe(true);
    expect(said.includes(AREA.cost.lead)).toBe(false);
    expect(said.includes(AREA.cost.confidence)).toBe(false);
  });
});

describe("what an area's page says", () => {
  test("test_the_page_is_named_for_the_area_and_gives_its_borough", async () => {
    await show("alderwick");

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Alderwick");
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(screen.getByRole("article", { name: "Alderwick" })).toHaveTextContent(
      `${AREA.borough}Quillhaven`,
    );
  });

  test("test_the_name_comes_first_and_the_label_of_the_area_stands_under_it", async () => {
    const data = profile("alderwick");
    await show("alderwick");
    const named = data.facts.find((fact) => fact.kind === "area");
    const head = screen.getByRole("heading", { level: 1 }).parentElement as HTMLElement;

    // The label is the fact's own, so it has the source and the date of the fact.
    expect(named?.slots.label).toBe("Quillhaven 001");
    expect(head).toHaveTextContent(`${NAMED.label}Quillhaven 001`);
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Alderwick");
    expect(figuresNotFrom(head, saidBy(data.facts))).toEqual([]);
  });

  test("test_a_name_no_person_has_checked_is_said_to_be_a_draft_with_who_wrote_it", async () => {
    const data = profile("alderwick");
    await show("alderwick");
    const named = data.facts.find((fact) => fact.kind === "area");
    const head = screen.getByRole("heading", { level: 1 }).parentElement as HTMLElement;

    expect(data.area.named?.state).toBe("draft");
    // Who wrote the name is the API's word. That it is a draft is said in the page's words.
    expect(head).toHaveTextContent(NAMED.state.draft(named?.slots.written_by ?? "nobody"));
    expect(head).toHaveTextContent("No person has checked it");
    // One press away is how a name is chosen.
    expect(within(head).getByRole("link", { name: NAMED.how })).toHaveAttribute("href", "/methods#names");
  });

  test("test_a_name_a_person_has_checked_says_so_and_is_no_draft", async () => {
    const data = profile("tallowgate");
    await show("tallowgate");
    const head = screen.getByRole("heading", { level: 1 }).parentElement as HTMLElement;

    expect(data.area.named?.state).toBe("checked");
    expect(head).toHaveTextContent(NAMED.state.checked("Burro"));
    expect(head).not.toHaveTextContent("draft");
    expect(head).toHaveTextContent(`${NAMED.label}Quillhaven 021`);
  });

  test("test_an_area_that_bears_no_name_but_its_label_says_nothing_of_a_name", async () => {
    const data = profile("grapnel-dock");
    await show("grapnel-dock");
    const head = screen.getByRole("heading", { level: 1 }).parentElement as HTMLElement;

    expect(data.area.named).toBeNull();
    expect(head).not.toHaveTextContent(NAMED.label);
    expect(within(head).queryByRole("link", { name: NAMED.how })).toBeNull();
    expect(head).toHaveTextContent(`${AREA.borough}Quillhaven`);
  });

  test("test_the_page_carries_the_banner_that_says_the_data_is_made_up", async () => {
    await show("alderwick");

    expect(screen.getByRole("region", { name: BANNER.label })).toHaveTextContent(BANNER.text);
  });

  test.each(areas.map((area) => area.slug))(
    "test_every_figure_on_the_page_is_one_the_api_sent: %s",
    async (slug) => {
      const data = profile(slug);
      await show(slug);
      const allowed = saidBy(data.facts);
      // A feature or a tag is named by the release, and a name may hold a figure: "a 10-minute walk".
      for (const metric of meta.data.features) allowed.add(metric.label);
      // So is a vibe, with what it means and what it cannot see: each may hold a figure, "under 3 m".
      for (const tag of meta.data.tags) {
        for (const words of [tag.label, tag.meaning, ...tag.cannot_see]) allowed.add(words);
      }
      for (const words of siteCopyWithFigures()) allowed.add(words);
      // What offers the census names its day. The words are the API's, and hold no figure of a place.
      allowed.add(meta.data.census.intro);
      // A sentence of the contract's, filled from the slots of a fact and from nothing else.
      for (const fact of data.facts) {
        const said = sentenceOf(fact);
        if (said !== null) allowed.add(said);
      }

      expect(figuresNotFrom(screen.getByRole("main"), allowed)).toEqual([]);
    },
  );

  test("test_every_fact_the_release_holds_for_the_area_is_on_its_page", async () => {
    const data = profile("alderwick");
    await show("alderwick");
    const main = screen.getByRole("main");

    const shown = factsShown(data, meta.data);

    // Every fact of the profile is laid out, and each is on the page by its own slots.
    expect(shown.map((fact) => fact.fact_id).sort()).toEqual(data.facts.map((fact) => fact.fact_id).sort());
    for (const fact of data.facts) {
      const said = columnsOf(fact).map(([, value]) => value ?? "");
      expect(said.length).toBeGreaterThan(0);
      for (const value of said) expect(main.textContent?.includes(value)).toBe(true);
    }
    expect(new Set(data.facts.map((fact) => fact.kind))).toEqual(
      new Set(["area", "station", "cost", "feature", "tag", "likeness"]),
    );
  });

  test("test_every_fact_is_followed_by_its_source_and_its_date", async () => {
    const data = profile("alderwick");
    await show("alderwick");
    const profileOnPage = screen.getByRole("article", { name: "Alderwick" });

    // What is closed at first is on the page all the same, and is held to the same rule.
    // A row of a fact is named in words of its own. What is not one is left out: a part that
    // opens, a list under its heading, the button that compares, and what has no figure.
    // An area that is like this one is a sentence, in a list, and is held to the same rule.
    const rows = [
      ...[...profileOnPage.querySelectorAll<HTMLElement>("[role='group'][aria-label]")]
        .filter((row) => row.getAttribute("aria-label") !== AREA.compare)
        .filter((row) => !row.textContent?.includes(AREA.features.noFigure))
        .filter((row) => row.getAttribute("aria-label") !== PORTRAIT.madeOf.notCarried)
        // A part this data does not carry is named, and has no figure to give a source for.
        .filter((row) => !row.textContent?.includes(PORTRAIT.madeOf.waits)),
      ...profileOnPage.querySelectorAll<HTMLElement>("#alike ol > li"),
    ];

    const found = new Set<string>();
    for (const row of rows) {
      const name = row.getAttribute("aria-label") ?? "";
      const fact = data.facts.find((one) =>
        one.kind === "likeness"
          ? row.tagName === "LI" && row.textContent?.includes(sentenceOf(one) ?? "no sentence")
          : // A row is named by the kind of home, or by the fact's own label.
            (one.slots.segment ?? one.label) === name ||
            (one.kind === "station" && row.textContent?.includes(one.slots.name ?? "")),
      );
      if (!fact) throw new Error("A row is of no fact.");
      found.add(fact.fact_id);
      const link = within(row).getByRole("link", { name: fact.sources[0]?.name });
      expect(link).toHaveAttribute("href", `/sources#${fact.sources[0]?.source_id}`);
      expect(row.textContent?.includes(`${SOURCE.dataFrom} ${readableDate(fact.as_of)}`)).toBe(true);
      expect(row.textContent?.includes(SOURCE.madeUp)).toBe(true);
    }
    // Every fact has a row, but for the one that names the area, whose source is under the name.
    expect(rows.length).toBeGreaterThanOrEqual(data.facts.length - 1);
    expect([...found].sort()).toEqual(
      data.facts
        .filter((fact) => fact.kind !== "area")
        // A kind of home names its row, and two kinds of tenure may share a name: both are rows.
        .filter((fact) => fact.kind !== "cost" || found.has(fact.fact_id))
        .map((fact) => fact.fact_id)
        .sort(),
    );
  });

  test("test_the_name_and_the_borough_have_their_source_and_their_date", async () => {
    const data = profile("alderwick");
    await show("alderwick");
    const named = data.facts.find((fact) => fact.kind === "area");
    const head = screen.getByRole("heading", { level: 1 }).parentElement as HTMLElement;

    expect(within(head).getByRole("link", { name: named?.sources[0]?.name })).toHaveAttribute(
      "href",
      "/sources#synthetic",
    );
    expect(head).toHaveTextContent(`${SOURCE.dataFrom} ${readableDate(named?.as_of ?? "")}`);
  });

  test("test_a_feature_with_no_figure_says_so_and_nothing_is_filled_in", async () => {
    const data = profile("alderwick");
    const without = data.features.filter((feature) => feature.value === null);
    await show("alderwick");

    expect(without.map((feature) => feature.feature_id)).toEqual(["air_no2"]);
    for (const feature of without) {
      const label = meta.data.features.find((metric) => metric.feature_id === feature.feature_id)?.label ?? "";
      const row = within(part("measured")).getByRole("group", { name: label });
      expect(row).toHaveTextContent(`${label}${AREA.features.noFigure}`);
      // No figure, no comparison, and no source for what is not there.
      expect(/\d/.test(row.textContent ?? "")).toBe(false);
      expect(within(row).queryByRole("link")).toBeNull();
    }
  });

  test("test_the_facts_are_grouped_by_what_they_are_about_in_a_fixed_order", async () => {
    const data = profile("alderwick");
    await show("alderwick");
    const measured = part("measured");

    const groups = featuresByDimension(data, meta.data.features);
    const headings = within(measured)
      .getAllByRole("heading", { level: 3 })
      .map((heading) => heading.textContent);

    expect(headings).toEqual(groups.map((group) => DIMENSION[group.dimension]));
    // Recorded crime comes last.
    expect(headings.at(-1)).toBe(DIMENSION.crime);
    expect(groups.flatMap((group) => group.rows)).toHaveLength(meta.data.features.length);
  });

  test("test_each_group_of_what_is_measured_is_closed_under_its_own_name", async () => {
    // Seen in a browser, on a release of a hundred measures: the part opened to seventeen
    // screens of rows, every group at once, and the brands stood eight screens down.
    const data = profile("alderwick");
    await show("alderwick");
    const measured = part("measured");

    const groups = featuresByDimension(data, meta.data.features);
    const closed = [...measured.querySelectorAll<HTMLDetailsElement>(":scope details")];

    expect(closed.map((group) => group.querySelector(":scope > summary h3")?.textContent)).toEqual(
      groups.map((group) => DIMENSION[group.dimension]),
    );
    expect(closed.filter((group) => group.open)).toEqual([]);
    // Every row is in the group it belongs to, and none stands outside one.
    expect(closed.map((group) => group.querySelectorAll(":scope > ul > li").length)).toEqual(
      groups.map((group) => group.rows.length),
    );
    expect(measured.querySelectorAll("ul > li").length).toBe(groups.flatMap((group) => group.rows).length);
    // What opens a group is the browser's own, so it opens with scripts off.
    for (const group of closed) expect(group.querySelector(":scope > summary")).toHaveClass("target");
  });

  test("test_where_the_page_speaks_of_recorded_crime_it_says_when_recorded_crime_counts", async () => {
    await show("alderwick");
    const measured = part("measured");

    // Under what is measured of recorded crime, the one rule, as every page says it.
    const heading = within(measured).getByRole("heading", { level: 3, name: DIMENSION.crime, hidden: true });
    expect(heading.closest("details:not(#measured)")?.textContent?.includes(CRIME_RULE)).toBe(true);
    // It is said of recorded crime, and under no other heading of what is measured.
    expect(measured.textContent?.split(CRIME_RULE)).toHaveLength(2);
  });

  test("test_recorded_crime_carries_its_caveat_and_no_verdict", async () => {
    await show("alderwick");
    const main = screen.getByRole("main");

    const crime = profile("alderwick").facts.filter((fact) => fact.template === "feature_crime");
    for (const fact of crime) {
      // Under what is measured, and wherever it is a part of a recipe.
      const rows = screen.getAllByRole("group", { name: fact.label });
      expect(rows.length).toBeGreaterThan(0);
      for (const row of rows) expect(row).toHaveTextContent(CRIME_CAVEAT);
    }

    expect(crime).toHaveLength(4);
    expect(/\b(safe|safer|safest|unsafe|dangerous|rough|dodgy|sketchy)\b/i.test(main.textContent ?? "")).toBe(false);
  });

  test("test_the_cost_of_every_kind_of_home_is_given_as_a_range_with_its_date_and_confidence", async () => {
    const data = profile("alderwick");
    await show("alderwick");
    const cost = part("cost");

    for (const tenure of ["rent", "buy"] as const) {
      for (const fact of costFacts(data, tenure)) {
        const row = within(cost).getByRole("group", { name: fact.slots.segment });
        expect(row).toHaveTextContent(`£${fact.slots.lower} to £${fact.slots.upper}`);
        expect(row).toHaveTextContent(`£${fact.slots.median}`);
        expect(row).toHaveTextContent(fact.slots.as_of ?? "");
        expect(row).toHaveTextContent(fact.slots.confidence ?? "");
      }
    }
    expect(costFacts(data, "rent")).toHaveLength(6);
    expect(costFacts(data, "buy")).toHaveLength(4);
    expect(data.cost).toHaveLength(10);
  });

  test("test_the_nearest_station_comes_first_and_is_said_to_be_the_nearest", async () => {
    const data = profile("pellam-cross");
    await show("pellam-cross");
    // A row of a station is named as one. What opens the list of what no vibe can see is no row.
    const rows = [...part("look").querySelectorAll<HTMLElement>("[role='group']")];
    const facts = stationFacts(data);

    expect(facts.length).toBeGreaterThan(1);
    expect(rows).toHaveLength(data.stations.length);
    expect(rows[0]).toHaveAccessibleName("Nearest station");
    expect(rows.slice(1).every((row) => row.getAttribute("aria-label") === "Station within a short walk")).toBe(true);
    rows.forEach((row, position) => {
      const fact = facts[position];
      expect(row).toHaveTextContent(fact?.slots.name ?? "no name");
      expect(row).toHaveTextContent(fact?.slots.lines ?? "no lines");
    });
    // In the order of the walk, as the release gives it.
    const walks = facts.slice(1).map((fact) => data.stations.find((one) => one.station_id === fact.key)?.walk_minutes);
    expect(walks).toEqual([...walks].sort((one, other) => Number(one) - Number(other)));
  });

  test("test_what_the_api_serves_with_no_fact_behind_it_is_not_shown", async () => {
    const data = profile("alderwick");
    await show("alderwick");
    const text = screen.getByRole("main").textContent ?? "";

    // Whether a station is step-free is served, and no fact holds it, so it has no source or date.
    // It is said of no station. That Burro cannot see it is the API's own line, and may be said.
    expect(data.stations.some((station) => "step_free" in station)).toBe(true);
    const stations = [...part("look").querySelectorAll<HTMLElement>("[role='group']")];
    expect(stations.length).toBeGreaterThan(0);
    expect(stations.filter((row) => /step.free/i.test(row.textContent ?? ""))).toEqual([]);
    // Nor is a percentile, a coverage or a tag's raw score ever printed.
    const unsourced = [
      ...data.features.flatMap((feature) => [feature.percentile, feature.coverage]),
      ...data.tags.flatMap((tag) => [tag.raw, tag.score, tag.coverage]),
    ].filter((value): value is number => value !== null && !Number.isInteger(value));
    expect(unsourced.length).toBeGreaterThan(20);
    // A figure that a fact gives may be the same number, and is shown: a count of 0.9 places
    // within reach is a fact, and a share of 0.9 that is covered is not.
    const numbers = (said: string) => said.match(/\d+(?:\.\d+)?/g) ?? [];
    const given = new Set(data.facts.flatMap((fact) => Object.values(fact.slots)).flatMap(numbers));
    const printed = new Set(numbers(text));
    expect(unsourced.map(String).filter((value) => printed.has(value) && !given.has(value))).toEqual([]);
  });

  test("test_every_vibe_of_the_release_is_on_the_page_once_in_the_list_the_api_puts_it_in", async () => {
    const data = profile("alderwick");
    await show("alderwick");
    const character = part("character");

    const drawn = [...character.querySelectorAll("details[data-vibe] > summary > span:first-child")].map(
      (name) => name.textContent,
    );

    expect(drawn).toEqual(GROUPS.flatMap((group) => data.portrait[group].map((mark) => mark.tag_id)).map(
      (id) => meta.data.tags.find((tag) => tag.tag_id === id)?.label,
    ));
    expect(drawn).toHaveLength(meta.data.tags.length);
    // Where it sits is a band in words, between two ends, and is never a percentage.
    for (const mark of shownOn(portraitOf(data, meta.data))) {
      const line = [...character.querySelectorAll("summary")].find((one) => one.firstChild?.textContent === mark.tag.label);
      expect(line?.textContent?.includes(STRIP.band(mark.placed?.band ?? 0))).toBe(true);
    }
  });

  test("test_a_vibe_that_cannot_place_an_area_says_so_once_and_gives_no_band", async () => {
    const otterby = profile("otterby-fields");
    await show("otterby-fields");
    const unplaced = within(part("character")).getByRole("group", { name: PORTRAIT.groups.unplaced });
    const unknown = otterby.facts.filter((fact) => fact.template === "vibe_unknown");

    // Thirteen of the fourteen vibes: Burro says so once, and why, and draws no mark for any of them.
    expect(unknown).toHaveLength(13);
    expect(unplaced.querySelectorAll("summary")).toHaveLength(1);
    expect(screen.getByRole("main").textContent?.split(PORTRAIT.unplacedWhy)).toHaveLength(2);
    for (const fact of unknown) expect(unplaced.querySelector("p")?.textContent?.includes(fact.label)).toBe(true);
    expect(/band \d/.test(unplaced.textContent ?? "")).toBe(false);
    expect(unplaced.querySelectorAll("[data-on]")).toHaveLength(0);
    // What the area is like says how many, in short, before anything else is read.
    expect(within(part("character")).getByRole("group", { name: PORTRAIT.short.title })).toHaveTextContent(
      PORTRAIT.short.unplaced(13, 14),
    );
  });

  test("test_an_area_the_release_does_not_rank_says_so", async () => {
    const unranked = areas.find((area) => !area.rankable);
    if (!unranked) throw new Error("The release ranks every area.");
    await show(unranked.slug);

    expect(screen.getByRole("main")).toHaveTextContent(AREA.notRanked);
  });

  test("test_an_area_the_release_ranks_does_not_say_it_is_unranked", async () => {
    await show("alderwick");

    expect(screen.getByRole("main")).not.toHaveTextContent(AREA.notRanked);
  });

  test("test_the_sources_of_the_page_are_listed_at_its_foot", async () => {
    await show("alderwick");
    const sources = within(part("sources"));

    expect(sources.getByRole("link", { name: "Synthetic test data" })).toHaveAttribute(
      "href",
      "/sources#synthetic",
    );
    expect(sources.getByRole("link", { name: AREA.methods })).toHaveAttribute("href", "/methods");
  });
});

describe("the order of an area's page", () => {
  test("test_the_page_opens_with_the_portrait_and_ends_with_go_and_look", async () => {
    await show("alderwick");
    const article = screen.getByRole("article", { name: "Alderwick" });

    const headings = [...article.querySelectorAll("h2")].map((heading) => heading.textContent);

    expect(headings[0]).toBe(PORTRAIT.title);
    // The tray of areas to compare is at the foot of the screen, and is no part of the page's order.
    expect(headings.filter((title) => title !== TRAY.title).at(-1)).toBe(LOOK.title);
    // Where the area is stands inside the portrait, beside what it is like: it is no part of its own.
    expect(headings.filter((title) => title !== TRAY.title)).toEqual([
      PORTRAIT.title,
      AREA.alike.open,
      AREA.cost.title,
      AREA.features.title,
      AREA.sources.title,
      // Who lived here comes after every figure of the place, and its heading is the API's.
      meta.data.census.heading,
      // So does what the households here are estimated to have as income.
      meta.data.income.heading,
      LOOK.title,
    ]);
  });

  test.each(["alike", "cost", "measured", "sources"])(
    "test_what_is_long_is_closed_until_it_is_pressed_and_opens_with_scripts_off: %s",
    async (id) => {
      await show("alderwick");
      const closed = part(id) as HTMLDetailsElement;

      // The browser's own element: it opens with no script, and what it holds is in the page.
      expect(closed.tagName).toBe("DETAILS");
      expect(closed.open).toBe(false);
      expect(closed.querySelector("summary")).toHaveClass("target");
      expect(closed.querySelector("summary > h2")).not.toBeNull();
      expect(closed.textContent?.length).toBeGreaterThan(100);
    },
  );

  test.each(["cost", "measured", "sources"])(
    "test_a_part_that_is_closed_is_opened_by_the_link_that_names_it: %s",
    async (id) => {
      await show("alderwick");
      expect((part(id) as HTMLDetailsElement).open).toBe(false);

      act(() => {
        window.location.hash = `#${id}`;
        window.dispatchEvent(new HashChangeEvent("hashchange"));
      });

      expect((part(id) as HTMLDetailsElement).open).toBe(true);
      window.location.hash = "";
    },
  );
});

describe("go and look", () => {
  test("test_it_says_where_to_start_from_a_fact_with_its_source_and_its_date", async () => {
    const data = profile("alderwick");
    await show("alderwick");
    const nearest = data.facts.find((fact) => fact.template === "station");

    const row = within(part("look")).getByRole("group", { name: "Nearest station" });

    expect(within(part("look")).getByRole("heading", { level: 3, name: LOOK.start })).toBeInTheDocument();
    expect(row).toHaveTextContent(nearest?.slots.name ?? "no name");
    expect(row).toHaveTextContent(nearest?.slots.walk ?? "no walk");
    expect(within(row).getByRole("link", { name: nearest?.sources[0]?.name })).toHaveAttribute("href", "/sources#synthetic");
    expect(row).toHaveTextContent(`${SOURCE.dataFrom} ${readableDate(nearest?.as_of ?? "")}`);
  });

  test("test_it_says_what_no_figure_can_say_of_each_vibe_shown_in_the_apis_words", async () => {
    const data = profile("alderwick");
    await show("alderwick");
    const shown = shownOn(portraitOf(data, meta.data)).map((mark) => mark.tag);
    const { common, own } = cannotSee(shown, meta.data.tags);

    const heading = within(part("look")).getByRole("heading", { level: 3, name: LOOK.cannotSee });
    const unseen = within(heading.parentElement as HTMLElement);

    // What every vibe cannot see is said once. The rest is under the name of its vibe.
    for (const line of common) expect(unseen.getAllByText(line)).toHaveLength(1);
    const terms = unseen.getAllByRole("term").map((term) => term.textContent);
    expect(terms).toEqual(own.map(({ tag }) => tag.label));
    own.forEach(({ lines }, at) => {
      const said = unseen.getAllByRole("definition")[at] as HTMLElement;
      expect(within(said).getAllByRole("listitem").map((item) => item.textContent)).toEqual(lines);
    });
    expect(unseen.getByRole("link", { name: LOOK.vibes })).toHaveAttribute("href", "/vibes");
  });

  test("test_what_each_vibe_cannot_see_is_one_press_away_and_what_none_can_see_is_in_sight", async () => {
    // Seen in a browser, on a release of fourteen vibes: the list of what each cannot see
    // was two screens of a phone, at the foot of a page that was eight and a half.
    const data = profile("alderwick");
    await show("alderwick");
    const shown = shownOn(portraitOf(data, meta.data)).map((mark) => mark.tag);
    const { common, own } = cannotSee(shown, meta.data.tags);
    const heading = within(part("look")).getByRole("heading", { level: 3, name: LOOK.cannotSee });
    const unseen = heading.parentElement as HTMLElement;

    const closed = unseen.querySelector("details") as HTMLDetailsElement;

    expect(closed.open).toBe(false);
    expect(closed.querySelector(":scope > summary")).toHaveTextContent(LOOK.cannotSeeEach);
    expect(closed.querySelector(":scope > summary")).toHaveClass("target");
    expect(closed.querySelectorAll("dt")).toHaveLength(own.length);
    expect(unseen.querySelectorAll("dt")).toHaveLength(own.length);
    // What every vibe cannot see is in sight before it is opened.
    expect(common.length).toBeGreaterThan(0);
    for (const line of common) expect(closed.textContent?.includes(line)).toBe(false);
    // The way to every vibe is with the list: the head of every page leads there too.
    expect(closed.contains(within(unseen).getByRole("link", { name: LOOK.vibes }))).toBe(true);
  });

  test("test_a_vibe_that_cannot_place_the_area_says_nothing_of_what_to_look_for", async () => {
    await show("otterby-fields");

    // Burro says nothing of the area on thirteen of the fourteen vibes, so there is nothing of them to check.
    const heading = within(part("look")).getByRole("heading", { level: 3, name: LOOK.cannotSee });

    expect(within(heading.parentElement as HTMLElement).getAllByRole("term").map((term) => term.textContent)).toEqual([
      "Houses or flats",
    ]);
  });

  test("test_it_writes_no_sentence_about_the_place", async () => {
    await show("alderwick");
    const look = part("look");

    // Every line in it is site copy that names no place, a fact's slot, or the API's own line.
    const names = ["Alderwick", "Quillhaven"];
    const lines = [LOOK.lead, LOOK.cannotSeeLead].join(" ");

    expect(names.filter((name) => lines.includes(name))).toEqual([]);
    expect(look).toHaveTextContent(LOOK.lead);
    expect(look.querySelectorAll("button, input, form")).toHaveLength(0);
  });

  test("test_a_page_that_offers_who_lived_here_does_not_say_that_no_figure_on_it_tells_who_lives_there", async () => {
    await show("alderwick");
    const heading = within(part("look")).getByRole("heading", { level: 3, name: LOOK.cannotSee });
    const unseen = heading.parentElement as HTMLElement;

    // The page offers the census, and a vibe on it says that it cannot see who lives there.
    expect(meta.data.census.available).toBe(true);
    expect(part("census")).toHaveTextContent(meta.data.census.heading);
    expect(unseen).toHaveTextContent(/who lives there/i);

    // So what is said of the list is said of the vibes, and never of every figure of the page.
    expect(unseen).toHaveTextContent(LOOK.cannotSeeLead);
    expect(LOOK.cannotSeeLead).toMatch(/\bvibe\b/i);
    expect(LOOK.cannotSeeLead).not.toMatch(/\bfigure\b/i);
  });
});

describe("where an area is", () => {
  const where = () => within(part("character")).getByRole("group", { name: AREA.where.title });

  test("test_the_sources_of_what_is_said_in_short_are_one_press_away", async () => {
    // Seen in a browser, on a build of a real city: thirteen sources and seven dates stood
    // written out under the five lines, a screen and a quarter of a phone, between what the
    // area is like and where it is.
    await show("alderwick");
    const short = within(part("character")).getByRole("group", { name: PORTRAIT.short.title });

    const closed = short.querySelector("details") as HTMLDetailsElement;

    expect(closed.open).toBe(false);
    expect(closed.querySelector(":scope > summary")).toHaveTextContent(PORTRAIT.short.sources);
    expect(closed.querySelector(":scope > summary")).toHaveClass("target-min");
    // Every source of the five lines is in it, with the date, and none stands outside it.
    expect(closed.querySelectorAll("a[href^='/sources#']").length).toBeGreaterThan(0);
    expect(short.querySelectorAll("a[href^='/sources#']")).toHaveLength(closed.querySelectorAll("a[href^='/sources#']").length);
    expect(closed.textContent?.includes(SOURCE.dataFrom)).toBe(true);
    // The five lines themselves are in sight.
    expect(closed.querySelectorAll("li")).toHaveLength(0);
    expect(short.querySelectorAll("li").length).toBeGreaterThan(0);
  });

  test("test_it_stands_in_the_portrait_beside_what_the_area_is_like_and_before_every_vibe", async () => {
    await show("alderwick");
    const short = within(part("character")).getByRole("group", { name: PORTRAIT.short.title });
    const first = part("character").querySelector("details[data-vibe]") as HTMLElement;

    expect(short.compareDocumentPosition(where()) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(where().compareDocumentPosition(first) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(within(where()).getByRole("heading", { level: 3, name: AREA.where.title })).toBeInTheDocument();
  });

  test("test_the_picture_names_the_area_and_the_list_beside_it_says_what_is_next_to_it", async () => {
    const data = profile("alderwick");
    await show("alderwick");

    expect(within(where()).getByRole("img")).toHaveAccessibleName(/Alderwick/);
    const neighbours = within(within(where()).getByRole("list", { name: AREA.where.neighbours })).getAllByRole("link");
    expect(neighbours.map((link) => link.textContent)).toEqual(data.neighbours.map((area) => area.name));
    expect(neighbours.map((link) => link.getAttribute("href"))).toEqual(
      data.neighbours.map((area) => `/synthetic/${area.slug}`),
    );
    expect(data.neighbours.length).toBeGreaterThan(0);
    for (const link of neighbours) {
      expect(link).toHaveAttribute("data-prefetch", "false");
      expect(link).toHaveClass("target-min");
    }
  });

  test("test_it_names_the_nearest_station_in_the_contracts_own_sentence_with_its_source_and_date", async () => {
    const data = profile("thrushcombe");
    await show("thrushcombe");
    const nearest = data.facts.find((fact) => fact.template === "station");
    if (!nearest) throw new Error("no recorded station");

    expect(where()).toHaveTextContent("Nearest station: Hollinsworth Quay, about 25 minutes on foot. Lines: Amber line.");
    expect(where().textContent?.includes(sentenceOf(nearest) ?? "no sentence")).toBe(true);
    expect(within(where()).getByRole("link", { name: nearest.sources[0]?.name })).toHaveAttribute(
      "href",
      `/sources#${nearest.sources[0]?.source_id}`,
    );
    expect(where()).toHaveTextContent(`${SOURCE.dataFrom} ${readableDate(nearest.as_of)}`);
  });

  test("test_an_area_with_no_station_in_the_data_says_so_and_names_none", async () => {
    const without = areas.map((area) => profile(area.slug)).find((data) => !data.facts.some((fact) => fact.kind === "station"));
    if (!without) return;
    await show(without.area.slug);

    expect(where()).toHaveTextContent(AREA.where.noStation);
    expect(where().textContent?.includes("minutes on foot")).toBe(false);
  });

  test("test_where_the_data_names_no_station_at_all_no_area_is_said_to_have_none_near_it", () => {
    // Seen in a browser, on a build of a real city that names no station yet: the page of an
    // area said "No station near this area is in this data.", twice, over a vibe that gave
    // the distance to the nearest station as 540 m.
    const data = profile("alderwick");
    const geometry = recordedAnswer("get_geometry", "geometry").body.data;
    const nameless = { ...meta.data, counts: { ...meta.data.counts, stations: 0 } };
    render(
      <Shell meta={meta.meta}>
        <AreaProfile
          data={{ ...data, stations: [], facts: data.facts.filter((fact) => fact.kind !== "station") }}
          meta={nameless}
          geometry={geometry}
          areas={areas}
          bands={bands}
        />
      </Shell>,
    );
    const page = screen.getByRole("main").textContent ?? "";

    expect(page.includes(AREA.where.noStation)).toBe(false);
    expect(page.includes(LOOK.noStation)).toBe(false);
    // It is said once, of the data, where the nearest station would stand.
    expect(page.split(AREA.where.noStations)).toHaveLength(2);
    expect(where()).toHaveTextContent(AREA.where.noStations);
    // With no station to start from, the part that says where to start is left out.
    expect(within(part("look")).queryByRole("heading", { level: 3, name: LOOK.start })).toBeNull();
    expect(within(part("look")).getByRole("heading", { level: 3, name: LOOK.cannotSee })).toBeInTheDocument();
  });

  test("test_the_picture_takes_no_key_and_no_pointer", async () => {
    await show("alderwick");
    const picture = within(where()).getByRole("img");

    expect(picture.querySelectorAll("a, button, [tabindex]")).toHaveLength(0);
  });
});

describe("how long it takes to the places a person named", () => {
  const inShell = (page: ReactElement) => <Shell meta={meta.meta}>{page}</Shell>;
  const journeys = () => screen.queryByRole("group", { name: AREA.journeys.title });
  const ranked = recordedAnswer("rank", "rank-first").body.data;

  /** Makes a search that names a place, then opens the page of an area, as a person does. */
  async function openFromASearch(slug: string, api = firstSearch()) {
    const user = userEvent.setup({ delay: null });
    const view = render(inShell(<SearchApp meta={meta.data} areas={areas} client={api.client} />));
    await search(user);
    view.rerender(inShell(await AreaPage(at("synthetic", slug))));
    return { api, user, ...view };
  }

  test("test_the_page_of_an_area_says_how_long_it_takes_and_whether_that_is_within_the_limit", async () => {
    await openFromASearch("farrowmere");
    const area = ranked.ranked.find((one) => one.area_id === profile("farrowmere").area.area_id);
    const leg = area?.legs[0];
    const commute = ranked.spec.commutes[0];
    if (!leg || !commute || leg.minutes === null) throw new Error("the recorded search names no place");

    const said = journeys();

    // The place is named by the answer that brought the search, and every time is the ranking's.
    expect(said).toHaveTextContent(ranked.places[0]?.name ?? "no name");
    expect(said).toHaveTextContent(MODE[leg.mode]);
    // The time is the one the ranking holds against the limit, so the two cannot disagree.
    expect(said).toHaveTextContent(JOURNEYS.minutes(leg.minutes));
    expect(said).toHaveTextContent(JOURNEYS.withinLimit(commute.max_minutes));
    expect(leg.minutes).toBeLessThanOrEqual(commute.max_minutes);
    // It stands with where the area is, in the portrait, before every vibe.
    expect(within(part("character")).getByRole("group", { name: AREA.where.title })).toContainElement(said);
  });

  test("test_a_journey_over_the_limit_is_said_to_be_over_it", async () => {
    await openFromASearch("alderwick");
    const area = ranked.ranked.find((one) => one.area_id === profile("alderwick").area.area_id);
    const commute = ranked.spec.commutes[0];
    if (!area?.legs[0] || !commute) throw new Error("the recorded search names no place");

    expect(area.legs[0].minutes).toBeGreaterThan(commute.max_minutes);
    expect(journeys()).toHaveTextContent(JOURNEYS.overLimit(commute.max_minutes));
    expect(journeys()?.textContent?.includes(JOURNEYS.withinLimit(commute.max_minutes))).toBe(false);
  });

  test("test_a_journey_that_was_estimated_says_its_band_and_that_it_is_an_estimate_and_no_minutes", async () => {
    // A release that holds no journey time: the ranking brings a band for each journey.
    const estimated = recordedAnswer("rank", "estimate/rank").body.data;
    const api = standInApi()
      .on("interpret", "interpret-first")
      .on("rank", "estimate/rank")
      .on("explain_top", "estimate/explanations");
    await openFromASearch("farrowmere", api);
    const area = estimated.ranked.find((one) => one.area_id === profile("farrowmere").area.area_id);
    const leg = area?.legs[0];
    if (!leg?.estimate) throw new Error("the recorded journey was not estimated");

    const said = journeys();

    expect(leg.status).toBe("estimated");
    expect(said).toHaveTextContent(estimated.places[0]?.name ?? "no name");
    expect(said).toHaveTextContent(`${MODE[leg.mode]}: ${JOURNEYS.estimated[leg.estimate]}. ${JOURNEYS.estimatedFrom}`);
    // It is given in no minutes, and is not said to be within its limit or over it.
    expect(/\d/.test(said?.textContent ?? "")).toBe(false);
    expect(said?.textContent?.includes(JOURNEYS.missing)).toBe(false);
    expect(within(said as HTMLElement).getByRole("button", { name: /^Source/ })).toBeInTheDocument();
  });

  test("test_with_no_search_open_the_page_says_nothing_of_journeys", async () => {
    await show("farrowmere");

    expect(journeys()).toBeNull();
  });

  test("test_a_search_that_names_no_place_says_nothing_of_journeys", async () => {
    const api = standInApi().on("interpret", "interpret-first").on("rank", "rank-shelf").on("explain_top", "explanations-shelf");
    await openFromASearch("farrowmere", api);

    expect(recordedAnswer("rank", "rank-shelf").body.data.spec.commutes).toEqual([]);
    expect(journeys()).toBeNull();
  });

  test("test_an_area_the_results_in_hand_do_not_hold_says_so_and_gives_no_time", async () => {
    // The release does not rank Grapnel Dock, so no search holds a journey from it.
    await openFromASearch("grapnel-dock");

    expect(ranked.ranked.map((one) => one.area_id)).not.toContain(profile("grapnel-dock").area.area_id);
    expect(journeys()).toHaveTextContent(AREA.journeys.notInHand);
    expect(/\d/.test(journeys()?.textContent ?? "")).toBe(false);
  });

  test("test_opening_the_page_asks_the_api_for_nothing_and_puts_no_place_in_an_address", async () => {
    const watching = watch();
    try {
      const { api } = await openFromASearch("farrowmere");
      const before = api.calls.length;
      await settled();

      // The times came with the ranking. The page of an area sends nothing of a search.
      expect(api.calls.length).toBe(before);
      const place = ranked.places[0];
      const links = [...document.querySelectorAll("a[href]")].map((link) => link.getAttribute("href") ?? "");
      expect(links.filter((href) => href.includes(place?.place_id ?? "no id"))).toEqual([]);
      expect(links.filter((href) => /cindermoor-works|Cindermoor%20Works/i.test(href))).toEqual([]);
      expect(watching.storage).toEqual([]);
      expect(watching.history).toEqual([]);
      expect(watching.console).toEqual([]);
    } finally {
      watching.stop();
    }
  });

  test("test_the_part_has_no_accessibility_fault", async () => {
    const { container } = await openFromASearch("farrowmere");

    expect(journeys()).not.toBeNull();
    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });
});

describe("an area's page, by keyboard and to a screen reader", () => {
  test("test_the_page_has_no_accessibility_fault", async () => {
    const { container } = await show("alderwick");

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });

  test("test_every_part_of_the_page_can_be_reached_from_its_list_of_contents", async () => {
    await show("alderwick");
    const contents = screen.getByRole("navigation", { name: AREA.contents });

    const links = within(contents).getAllByRole("link");

    // The portrait is what the page opens with. The list stands under it, and names what follows.
    expect(part("character").compareDocumentPosition(contents) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    // Where the area is stands above the list, in the portrait, and the list names what follows.
    expect(links.map((link) => link.textContent)).toEqual([
      AREA.alike.open,
      AREA.cost.title,
      AREA.features.title,
      AREA.sources.title,
      meta.data.census.heading,
      meta.data.income.heading,
      LOOK.title,
    ]);
    for (const link of links) {
      const target = document.getElementById((link.getAttribute("href") ?? "").slice(1));
      // A part is named by its heading, or by what opens it where it is closed at first.
      const named = target?.tagName === "DETAILS" ? target.querySelector("summary") : target;
      expect(named?.textContent).toBe(link.textContent);
    }
  });

  test("test_every_control_is_native_in_the_tab_order_and_takes_a_target_size", async () => {
    const { container } = await show("alderwick");
    const main = screen.getByRole("main");

    const controls = [...main.querySelectorAll("a, button, input, select, textarea")];

    expect(controls.length).toBeGreaterThan(50);
    expect(controls.filter((control) => control.getAttribute("tabindex") === "-1")).toEqual([]);
    expect(
      controls.filter((control) => !control.classList.contains("target") && !control.classList.contains("target-min")),
    ).toEqual([]);
    expect([...container.querySelectorAll("[role='button'], [role='link'], [onclick]")]).toEqual([]);
  });

  test("test_no_link_on_the_page_is_fetched_before_it_is_pressed", async () => {
    await show("alderwick");
    const profileOnPage = screen.getByRole("article", { name: "Alderwick" });

    // Which area or which source a person reads next is told to no server ahead of time.
    const toPlaces = within(profileOnPage)
      .getAllByRole("link")
      .filter((link) => /^\/(synthetic|sources)/.test(link.getAttribute("href") ?? ""));

    expect(toPlaces.length).toBeGreaterThan(40);
    expect(toPlaces.filter((link) => link.getAttribute("data-prefetch") !== "false")).toEqual([]);
  });

  test("test_nothing_on_the_page_comes_from_another_origin", async () => {
    const { container } = await show("alderwick");

    expect([...container.querySelectorAll("[src], link[href], [srcset], [poster], script")]).toEqual([]);
    expect(
      [...container.querySelectorAll("a[href]")].filter((link) => !/^[/#]/.test(link.getAttribute("href") ?? "")),
    ).toEqual([]);
  });
});

describe("choosing an area to compare, from its page", () => {
  test("test_the_area_can_be_put_among_those_to_compare_and_taken_out_again", async () => {
    await show("alderwick");
    const tray = screen.getByRole("region", { name: TRAY.title });
    // It takes no room until an area is chosen: the portrait comes first.
    expect(tray).toHaveAttribute("data-closed", "true");

    const user = userEvent.setup({ delay: null });

    await user.click(screen.getByRole("button", { name: COMPARE.add("Alderwick") }));

    expect(within(tray).getByText("Alderwick")).toBeInTheDocument();
    expect(tray).toHaveTextContent(TRAY.one);
    // The button says beside itself what the tray does, because the tray is at the foot of the screen.
    expect(screen.getByRole("group", { name: AREA.compare })).toHaveTextContent(TRAY.one);
    await user.click(screen.getByRole("button", { name: COMPARE.remove("Alderwick") }));
    expect(tray).toHaveAttribute("data-closed", "true");
  });
});

describe("the areas most like this one", () => {
  const alike = () => document.getElementById("alike") as HTMLDetailsElement;

  afterEach(() => {
    window.location.hash = "";
  });

  test("test_the_part_is_closed_until_it_is_pressed_and_is_on_the_page_with_scripts_off", async () => {
    await show("alderwick");

    // The browser's own element: it opens with no script, and what it holds is in the page.
    expect(alike().tagName).toBe("DETAILS");
    expect(alike().open).toBe(false);
    expect(alike().querySelector("summary")).toHaveTextContent(AREA.alike.open);
    expect(alike().querySelector("summary")).toHaveClass("target");
    expect(within(alike()).getByRole("heading", { name: AREA.alike.title, hidden: true })).toBeInTheDocument();
    expect(alike().textContent?.includes(AREA.alike.lead)).toBe(true);
  });

  test("test_it_holds_the_five_areas_the_api_names_in_its_order_each_one_press_from_its_page", async () => {
    const data = profile("alderwick");
    await show("alderwick");
    const rows = alikeRows(data, areas);
    const shown = [...alike().querySelectorAll<HTMLElement>("ol > li")];

    expect(rows).toHaveLength(5);
    expect(rows.map((row) => row.fact.fact_id)).toEqual(data.similar.map((one) => one.fact_id));
    expect(shown).toHaveLength(5);
    rows.forEach(({ area, fact }, at) => {
      const row = shown[at] as HTMLElement;
      const link = row.querySelector("a");
      // A name opens that area's page. It starts no search, and is not fetched ahead of time.
      expect(link).toHaveTextContent(area?.name ?? "no name");
      expect(link).toHaveAttribute("href", `/synthetic/${area?.slug}`);
      expect(link).toHaveAttribute("data-prefetch", "false");
      expect(row.textContent?.includes(SOURCE.madeUp)).toBe(true);
      expect(row.textContent?.includes(`${SOURCE.dataFrom} ${readableDate(fact.as_of)}`)).toBe(true);
    });
  });

  test("test_each_area_is_a_sentence_of_the_contracts_and_not_a_row_of_columns", async () => {
    const data = profile("thrushcombe");
    await show("thrushcombe");
    const shown = [...alike().querySelectorAll<HTMLElement>("ol > li")];

    alikeRows(data, areas).forEach(({ fact }, at) => {
      expect(shown[at]?.textContent?.includes(sentenceOf(fact) ?? "no sentence")).toBe(true);
    });
    expect(shown[4]).toHaveTextContent(
      "Thrushcombe is in the same band as Wickerford on 7 of the 23 measures compared, and least alike in Daily life.",
    );
    // No column of a fact is drawn: a likeness reads as one sentence.
    expect(alike().querySelectorAll("dl, dt, dd, [role='group']")).toHaveLength(0);
  });

  test("test_what_the_two_share_is_said_in_words_by_the_names_the_api_gives_the_vibes", async () => {
    const data = profile("thrushcombe");
    await show("thrushcombe");
    const shown = [...alike().querySelectorAll<HTMLElement>("ol > li")];

    let some = 0;
    alikeRows(data, areas).forEach(({ area }, at) => {
      const shared = sharedVibes(data.area.area_id, area?.area_id ?? "", bands, meta.data);
      if (shared.length === 0) {
        expect(shown[at]?.textContent?.includes(AREA.alike.sharesNone)).toBe(true);
        return;
      }
      some += 1;
      expect(shown[at]?.textContent?.includes(AREA.alike.shares)).toBe(true);
      for (const tag of shared) expect(shown[at]?.textContent?.includes(tag.label)).toBe(true);
    });
    expect(some).toBeGreaterThan(0);
    // Recorded crime is never what two areas are said to share.
    expect(alike().textContent?.includes("Gritty")).toBe(false);
  });

  test("test_the_words_over_the_list_say_the_order_as_the_contract_gives_it", async () => {
    await show("thrushcombe");
    const contract = readFileSync(path.resolve(__dirname, "../../../../docs/design/contract.md"), "utf8").replace(/\s+/g, " ");

    // The engine puts the areas in the order of the count each sentence gives.
    expect(contract).toContain("Most alike first: the areas in the same band on the most measures");
    expect(alike().textContent?.includes(AREA.alike.lead)).toBe(true);
    expect(AREA.alike.lead).toContain("the most alike first");
    expect(AREA.alike.lead).toContain("in the same band as this one on the most measures");
  });

  test("test_the_areas_stand_in_the_order_the_api_gives_and_the_website_puts_them_in_none_of_its_own", async () => {
    const data = profile("thrushcombe");
    await show("thrushcombe");
    const shown = [...alike().querySelectorAll<HTMLElement>("ol > li")];

    // Whatever order the answer is in, the page keeps it. It sorts nothing.
    const named = shown.map((row) => row.querySelector("a")?.textContent);
    expect(named).toEqual(data.similar.map((one) => areas.find((area) => area.area_id === one.area_id)?.name));
    const backwards = { ...data, similar: [...data.similar].reverse() };
    expect(alikeRows(backwards, areas).map((row) => row.fact.fact_id)).toEqual(
      [...data.similar].reverse().map((one) => one.fact_id),
    );
  });

  test("test_the_counts_stand_in_the_order_the_words_over_them_promise", async () => {
    // Seen in a browser: the counts read 10, 10, 5, 7, 8 under words that promised the most
    // alike first. The engine now puts the areas in the order of the count each sentence gives.
    const data = profile("thrushcombe");
    await show("thrushcombe");

    const same = alikeRows(data, areas).map((row) => Number(row.fact.slots.same));

    expect(same).toEqual([10, 9, 9, 8, 7]);
    expect(same).toEqual([...same].sort((one, other) => other - one));
    // And so it is of every area that has any.
    for (const one of areas) {
      const counts = alikeRows(profile(one.slug), areas).map((row) => Number(row.fact.slots.same ?? row.fact.slots.measures));
      expect(counts).toEqual([...counts].sort((first, second) => second - first));
    }
  });

  test("test_each_area_that_is_alike_leads_to_the_comparison_of_the_two", async () => {
    const data = profile("alderwick");
    await show("alderwick");

    const rows = alikeRows(data, areas);
    const links = within(alike()).getAllByRole("link", { name: /^Compare Alderwick with /, hidden: true });

    // How two areas differ, vibe by vibe, is the comparison's to show. The address holds two slugs.
    expect(links.map((link) => link.textContent)).toEqual(
      rows.map((row) => AREA.alike.compare("Alderwick", row.area?.name ?? "")),
    );
    expect(links.map((link) => link.getAttribute("href"))).toEqual(
      rows.map((row) => `/compare?a=alderwick&a=${row.area?.slug}`),
    );
    for (const link of links) {
      expect(link).toHaveAttribute("data-prefetch", "false");
      expect(link).toHaveClass("target-min");
    }
  });

  test("test_it_is_open_when_a_result_led_to_it", async () => {
    window.location.hash = "#alike";

    await show("alderwick");

    expect(alike().open).toBe(true);
  });

  test("test_it_opens_when_the_link_in_the_list_of_contents_is_followed", async () => {
    await show("alderwick");
    expect(alike().open).toBe(false);

    act(() => {
      window.location.hash = "#alike";
      window.dispatchEvent(new HashChangeEvent("hashchange"));
    });

    expect(alike().open).toBe(true);
  });

  test("test_where_too_little_is_known_of_an_area_the_page_says_so_and_names_none", async () => {
    await show("otterby-fields");

    expect(profile("otterby-fields").similar).toEqual([]);
    expect(alike().textContent?.includes(AREA.alike.none)).toBe(true);
    expect(alike().querySelectorAll("ol, li, a")).toHaveLength(0);
  });

  test("test_opening_it_sends_nothing_and_writes_nothing_down", async () => {
    const watching = watch();
    const asked = jest.fn();
    globalThis.fetch = asked as unknown as typeof fetch;
    try {
      await show("alderwick");
      const user = userEvent.setup({ delay: null });

      await user.click(alike().querySelector("summary") as HTMLElement);

      // It came with the page. No request is made, so nothing a person typed can be in one.
      expect(alike().open).toBe(true);
      expect(asked).not.toHaveBeenCalled();
      expect(watching.storage).toEqual([]);
      expect(watching.history).toEqual([]);
      expect(watching.console).toEqual([]);
    } finally {
      watching.stop();
    }
  });

  test("test_nothing_about_who_lives_somewhere_is_compared", () => {
    // Every measure two areas are compared on is of the place: the API says which they are.
    const compared = meta.data.features.filter((metric) => metric.in_likeness);

    expect(compared).toHaveLength(23);
    // A feature is a fact about a place, its buildings or what was recorded there. There is
    // no value for who lives somewhere, and nothing that was recorded is compared.
    expect(new Set(compared.map((metric) => metric.describes))).toEqual(new Set(["place", "buildings"]));
    expect(compared.filter((metric) => metric.dimension === "crime")).toEqual([]);
  });
});

describe("starting a search from an area", () => {
  const button = () => screen.queryByRole("link", { name: PORTRAIT.search.button });
  const inShell = (page: ReactElement) => <Shell meta={meta.meta}>{page}</Shell>;
  const more = (slug: string) => portraitOf(profile(slug), meta.data).more.map((mark) => mark.tag);

  test("test_the_button_stands_under_what_the_area_has_more_of_than_most_and_says_what_it_adds", async () => {
    await show("thrushcombe");
    const list = within(part("character")).getByRole("group", { name: PORTRAIT.groups.more });

    expect(more("thrushcombe").map((tag) => tag.label)).toEqual(["Village feel", "Food and drink", "Parks close by"]);
    expect(within(list).getByRole("link", { name: PORTRAIT.search.button })).toHaveAttribute("href", "/");
    expect(list).toHaveTextContent(PORTRAIT.search.adds("Village feel, Food and drink and Parks close by"));
    expect(button()).toHaveClass("target");
  });

  test("test_an_area_that_has_more_of_nothing_than_most_has_no_such_button", async () => {
    await show("marrowfen");

    expect(more("marrowfen")).toEqual([]);
    expect(button()).toBeNull();
  });

  test("test_pressing_it_opens_the_search_with_one_edit_for_each_vibe_and_nothing_typed", async () => {
    const watching = watch();
    try {
      const api = standInApi().on("rank", "rank-shelf").on("explain_top", "explanations-shelf");
      const user = userEvent.setup({ delay: null });
      const view = render(inShell(await AreaPage(at("synthetic", "thrushcombe"))));

      await user.click(button() as HTMLElement);
      // The link leads to the search page, which is drawn inside the same shell.
      view.rerender(inShell(<SearchApp meta={meta.data} areas={areas} client={api.client} />));
      await settled();

      const sent = api.lastCallTo("rank").body as RankBody;
      expect(api.callsTo("rank")).toHaveLength(1);
      // The search starts from the settings the API served, and nothing was read from any words.
      expect(api.callsTo("interpret")).toEqual([]);
      expect(sent.spec).toEqual(meta.data.defaults.rent);
      // One edit for each vibe, worth what a word of the shelf is, and no other edit.
      expect(sent.operations).toEqual({
        ...NO_EDITS,
        tag_ops: more("thrushcombe").map((tag) => ({
          action: "nudge",
          tag_id: tag.tag_id,
          value: 0,
          step: "up_large",
          toward: "high",
          provenance: "ui_edit",
        })),
      });
      // Which area the search was started from is told to no one: the request names vibes alone.
      expect(api.lastCallTo("rank").sent?.includes("thrushcombe")).toBe(false);
      expect(api.lastCallTo("rank").sent?.includes(profile("thrushcombe").area.area_id)).toBe(false);
      expect(api.lastCallTo("rank").url.includes("?")).toBe(false);
      expect(watching.storage).toEqual([]);
      expect(watching.history).toEqual([]);
      expect(watching.console).toEqual([]);
    } finally {
      watching.stop();
    }
  });

  test("test_what_was_asked_for_is_added_once_and_not_again_when_the_search_is_come_back_to", async () => {
    const api = standInApi().on("rank", "rank-shelf").on("explain_top", "explanations-shelf");
    const user = userEvent.setup({ delay: null });
    const view = render(inShell(await AreaPage(at("synthetic", "thrushcombe"))));
    await user.click(button() as HTMLElement);
    view.rerender(inShell(<SearchApp meta={meta.data} areas={areas} client={api.client} />));
    await settled();

    // To the page of an area and back, without pressing the button again.
    view.rerender(inShell(await AreaPage(at("synthetic", "alderwick"))));
    view.rerender(inShell(<SearchApp meta={meta.data} areas={areas} client={api.client} />));
    await settled();

    expect(api.callsTo("rank")).toHaveLength(1);
  });

  test("test_a_page_opened_without_pressing_it_adds_nothing_to_the_search", async () => {
    const api = standInApi().on("rank", "rank-shelf").on("explain_top", "explanations-shelf");
    const view = render(inShell(await AreaPage(at("synthetic", "thrushcombe"))));

    view.rerender(inShell(<SearchApp meta={meta.data} areas={areas} client={api.client} />));
    await settled();

    expect(api.callsTo("rank")).toEqual([]);
  });
});
