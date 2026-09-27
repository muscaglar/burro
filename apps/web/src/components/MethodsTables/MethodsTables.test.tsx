import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen, within } from "@testing-library/react";

import { KEPT_WITH_ACCOUNTS } from "@/content/account";
import { CRIME_ACCOUNT, CRIME_RULE, ruleIn } from "@/content/crime";
import { COMBINE, DIMENSION, POLARITY, PT_BASIS, STRICTNESS, TENURE } from "@/content/labels";
import { METHODS } from "@/content/methods";
import { JOURNEYS } from "@/content/search";
import { CRIME_CAVEAT } from "@/content/settings";
import { READER } from "@/content/site";
import { ACCOUNTS_VARIABLE, ON } from "@/lib/account/on";
import { readRecorded, recordedAnswer } from "@/lib/api/recorded";
import type { MetaData, Metric } from "@/lib/api/schema";
import { readableDate } from "@/lib/format";
import { METHODS_PARTS, paths } from "@/lib/paths";

import { faultsIn } from "../../../test/support/axe";
import { rulesOf } from "../../../test/support/css";
import { onTheGrass } from "../About/grass";
import { pictureOf } from "../kit/drawings";
import { drawingOf, PLAIN } from "../kit/Thing/drawn";
import { MethodsTables } from "./MethodsTables";

const meta = recordedAnswer("get_meta", "meta").body.data;
/** The release where gritty is built from land use alone, and holds no figure of crime. */
const variantA: MetaData = (readRecorded("variant-a/meta").body as { data: MetaData }).data;

const LIST = new Intl.ListFormat("en-GB", { style: "long", type: "conjunction" });

/** The contract, as it is written, with each run of space as one. */
const contract = () =>
  readFileSync(path.resolve(__dirname, "../../../../../docs/design/contract.md"), "utf8").replace(/[ \t]+/g, " ");

/** The same answer, as a real release might give it: other sources, and one feature not ranked. */
function realLooking(): MetaData {
  const sources = [
    { ...meta.attributions[0]!, source_id: "open-greenspace", name: "Open Greenspace" },
    { ...meta.attributions[0]!, source_id: "price-paid", name: "Price Paid" },
  ];
  const features = meta.features.map(
    (metric, at): Metric => ({
      ...metric,
      source_ids: at % 2 === 0 ? ["open-greenspace"] : ["open-greenspace", "price-paid"],
      vintage: at === 0 ? "2024-10 to 2026-09" : metric.vintage,
      rankable: at !== 1,
    }),
  );
  return { ...meta, synthetic: false, attributions: sources, features };
}

/** Every run of digits in a text, with the separators between thousands taken out. */
function numbersIn(text: string): string[] {
  return (text.replace(/(\d),(?=\d{3})/g, "$1").match(/\d+(\.\d+)?/g) ?? []).map((found) =>
    found.replace(/^0+(?=\d)/, ""),
  );
}

/** Every number the API sent, as it is and as the share of a hundred a weight is shown as. */
function numbersSent(value: unknown): Set<string> {
  const found = new Set<string>();
  const walk = (part: unknown) => {
    if (typeof part === "number") {
      found.add(String(part));
      found.add(String(Math.round(part * 100)));
    } else if (typeof part === "string") {
      for (const number of numbersIn(part)) found.add(number);
    } else if (Array.isArray(part)) {
      part.forEach(walk);
    } else if (typeof part === "object" && part !== null) {
      Object.values(part).forEach(walk);
    }
  };
  walk(value);
  return found;
}

/** True of what stands in sight as the page is built: in no fold, and kept from nobody. */
const inSight = (element: Element | null) =>
  element !== null && element.closest("details, [hidden], .visually-hidden, [aria-hidden='true']") === null;
/** The account, which is the first box of the methods. */
const account = () => document.querySelector("[data-methods='account']") as HTMLElement;
/** The one fold of the methods, which holds all of it. */
const full = () => document.querySelector("details[data-fold='ground']") as HTMLDetailsElement;

describe("the methods, in short", () => {
  const { account: copy } = METHODS;
  const said = (given: MetaData = meta) => [copy.looks, copy.ranks, copy.wont.before, ruleIn(given), copy.wont.after, copy.sourced];

  test("test_a_short_plain_account_stands_first_in_a_box_in_sight_and_the_rest_is_folded_under_it", () => {
    const { container } = render(<MethodsTables meta={meta} />);

    expect(container.firstElementChild).toBe(account());
    expect(account()).toHaveAttribute("data-kind", "box");
    expect(account().nextElementSibling).toBe(full());
    expect(inSight(account())).toBe(true);
    // Four paragraphs: what Burro looks at, how it ranks, what it will not do, and that every figure has its source.
    const read = [...account().querySelectorAll(":scope > p")].map((one) => one.textContent);
    expect(read).toEqual([copy.looks, copy.ranks, `${copy.wont.before} ${ruleIn(meta)} ${copy.wont.after}`, copy.sourced]);
  });

  test("test_it_can_be_read_in_a_minute_and_stands_under_no_heading_of_its_own", () => {
    render(<MethodsTables meta={meta} />);
    const count = (text: string) => text.split(/\s+/).filter(Boolean).length;
    const own = count([copy.looks, copy.ranks, copy.wont.before, copy.wont.after, copy.sourced].join(" "));
    const rule = count(CRIME_RULE);

    // A person reads some 240 words in a minute. The founder: "Methods is too much information".
    // The account was held to 280 words in all while the rule of recorded crime was one
    // sentence of 26, which left the account 254 of its own. It is held to those still. The
    // rule is said word for word on every page that speaks of recorded crime, and is not the
    // account's to shorten: written again for a newcomer it is two sentences.
    expect(own).toBeGreaterThan(150);
    expect(own).toBeLessThanOrEqual(254);
    // With the rule the account is 288 words. Measured in a browser at 1440 by 900 on
    // 2026-09-26, it ended at 844 and the bar of the fold under it began at 860.
    expect(count(said().join(" "))).toBe(own + rule);
    expect(own + rule).toBeLessThanOrEqual(288);
    // The page says what it is for over it. A heading here would say it a second time.
    expect(within(account()).queryAllByRole("heading")).toEqual([]);
  });

  test("test_it_says_what_burro_looks_at_how_it_ranks_what_it_will_not_do_and_that_every_figure_has_its_source", () => {
    expect(copy.looks).toMatch(/what you tell it/);
    expect(copy.looks).toMatch(/measurements/);
    expect(copy.ranks).toMatch(/the closest match/);
    expect(copy.ranks).toMatch(/the same search on the same data always gives the same answer/);
    expect(copy.wont.before).toMatch(/does not call any area the best/);
    expect(copy.wont.before).toMatch(/leaves it out and says so/);
    expect(copy.wont.before).toMatch(/cannot ask for fewer of any group of people/);
    expect(copy.wont.after).toMatch(/never ranks or scores a place, and it never describes one from its own knowledge/);
    expect(copy.sourced).toMatch(/has a source and a date/);
  });

  test("test_it_says_when_recorded_crime_counts_by_the_one_rule_word_for_word", () => {
    render(<MethodsTables meta={meta} />);
    expect(account()).toHaveTextContent(CRIME_RULE);
    // No word of its own is said of recorded crime: the rule is the only sentence that says it.
    for (const own of [copy.looks, copy.ranks, copy.wont.before, copy.wont.after, copy.sourced]) {
      expect(/crime/i.test(own)).toBe(false);
    }
  });

  test("test_where_no_vibe_holds_recorded_crime_the_rule_is_followed_by_the_line_that_says_so", () => {
    render(<MethodsTables meta={variantA} />);

    expect(account()).toHaveTextContent(`${CRIME_RULE} ${CRIME_ACCOUNT.noVibe}`);
  });

  test("test_it_gives_no_verdict_and_states_no_figure_of_its_own", () => {
    const own = [copy.looks, copy.ranks, copy.wont.before, copy.wont.after, copy.sourced].join(" ");

    expect(/\d/.test(own)).toBe(false);
    // "The best" is said once, of what Burro does not call an area.
    expect(own.match(/\b(best|worst|good area|up and coming)\b/gi)).toEqual(["best"]);
    expect(/!/.test(own)).toBe(false);
  });

  test("test_it_leads_to_the_sources_and_to_the_vibes_with_the_key_to_the_drawings", () => {
    render(<MethodsTables meta={meta} />);

    const links = within(account()).getAllByRole("link");

    expect(links.map((link) => [link.textContent, link.getAttribute("href")])).toEqual([
      [copy.toVibes, "/vibes"],
      [copy.toSources, "/sources"],
    ]);
    for (const link of links) expect(link).toHaveClass("target-min");
  });
});

describe("the methods, in full", () => {
  test("test_all_of_it_is_one_fold_that_is_closed_and_named_for_what_it_holds", () => {
    render(<MethodsTables meta={meta} />);

    expect(document.querySelectorAll("details[data-fold='ground']")).toHaveLength(1);
    expect(full().open).toBe(false);
    expect(full().querySelector(":scope > summary")?.textContent).toBe(METHODS.detail);
    expect(full().querySelector(":scope > summary")).toHaveClass("target");
    // No fold stands in it: whoever opens it has all of it.
    expect(full().querySelectorAll("details")).toHaveLength(0);
  });

  test("test_nothing_of_the_methods_is_lost_every_part_stands_in_the_fold_under_the_id_it_had", () => {
    render(<MethodsTables meta={meta} />);

    const parts = [...full().querySelectorAll("h2")].map((heading) => [heading.id, heading.textContent]);

    expect(parts).toEqual([
      ["ranking", METHODS.ranking.title],
      ["names", METHODS.names.title],
      ["features", METHODS.features.title],
      ["vibes", METHODS.vibes.title],
      ["defaults", METHODS.defaults.title],
      ["limits", METHODS.limits.title],
      ["journeys", METHODS.journeys.title],
      ["confidence", METHODS.confidence.title],
      ["release", METHODS.release.title],
      ["words", METHODS.words.title],
    ]);
    // Every heading of the second rank is in the fold: the account stands under none.
    expect(screen.getAllByRole("heading", { level: 2 })).toHaveLength(parts.length);
  });

  test("test_every_part_that_another_page_leads_to_is_there_by_its_id_and_takes_the_focus_at_its_heading", () => {
    // The foot of every page leads to how a person's words are handled, a result to how a
    // journey is timed, and the page of an area to how it is named and how its rents are
    // held. Each leads to a heading in the fold, which takes the focus as the link is followed.
    expect([...METHODS_PARTS].sort()).toEqual(["confidence", "journeys", "names", "rents", "words"]);
    render(<MethodsTables meta={recordedAnswer("get_meta", "let/meta").body.data} />);

    for (const part of METHODS_PARTS) {
      const heading = document.getElementById(paths.methods(part).split("#")[1] ?? "no part");
      expect([part, heading?.tagName, heading?.getAttribute("tabindex")]).toEqual([part, "H2", "-1"]);
      expect([part, heading?.closest("details") !== null]).toEqual([part, true]);
    }
    // No other heading takes it, and nothing of the page is a stop of the keyboard that was none.
    const taking = [...document.querySelectorAll("h1[tabindex], h2[tabindex], h3[tabindex], h4[tabindex]")].map((heading) => heading.id);
    expect(taking.sort()).toEqual([...METHODS_PARTS].sort());
    expect(document.querySelectorAll("[tabindex]:not([tabindex='-1'])")).toHaveLength(0);
  });

  test("test_what_a_town_is_built_of_is_said_once_in_the_key_and_the_methods_lead_to_it", () => {
    render(<MethodsTables meta={meta} />);
    const vibes = screen.getByRole("region", { name: METHODS.vibes.title });

    // It stood here and on the page of vibes. It is said once now, in the key, and the methods say where.
    expect(document.querySelectorAll("[data-part]")).toHaveLength(0);
    expect(vibes).toHaveTextContent(METHODS.vibes.key);
    expect(METHODS.vibes.key).toMatch(/key to every drawing/);
    expect(METHODS.vibes.key).toMatch(/little town/);
  });
});

describe("the methods page", () => {
  test("test_every_feature_is_shown_with_its_definition_period_and_source_as_the_api_sent_them", () => {
    const real = realLooking();
    render(<MethodsTables meta={real} />);

    for (const metric of real.features) {
      const heading = screen.getByRole("heading", { level: 4, name: metric.label });
      const card = within(heading.closest("li")!);
      expect(card.getByText(metric.definition)).toBeInTheDocument();
      expect(card.getByText(metric.unit)).toBeInTheDocument();
      // The period is the release's, written as every other date on the website is.
      expect(card.getByText(readableDate(metric.vintage))).toBeInTheDocument();
      expect(card.getByText(POLARITY[metric.polarity])).toBeInTheDocument();
      expect(card.getAllByRole("link").map((link) => link.getAttribute("href"))).toEqual(
        metric.source_ids.map((id) => `/sources#${id}`),
      );
    }
  });

  test("test_a_source_is_named_by_its_name_and_linked_by_its_id", () => {
    render(<MethodsTables meta={realLooking()} />);

    const links = screen.getAllByRole("link", { name: "Price Paid" });

    expect(links.length).toBeGreaterThan(0);
    for (const link of links) expect(link).toHaveAttribute("href", "/sources#price-paid");
  });

  test("test_features_are_grouped_under_the_dimension_the_api_gives_them", () => {
    render(<MethodsTables meta={meta} />);

    for (const metric of meta.features) {
      const group = screen.getByRole("region", { name: DIMENSION[metric.dimension] });
      expect(within(group).getByRole("heading", { name: metric.label })).toBeInTheDocument();
    }
  });

  test("test_a_feature_the_release_does_not_rank_says_so", () => {
    // One that no recipe holds either: it is shown, and counts for nothing.
    const alone = meta.features.find(
      (metric) => !meta.tags.some((tag) => tag.terms.some((term) => term.feature_id === metric.feature_id)),
    );
    if (!alone) throw new Error("every recorded feature is a part of some vibe");
    const real = {
      ...meta,
      features: meta.features.map((metric) => ({ ...metric, rankable: metric.feature_id !== alone.feature_id })),
    };
    render(<MethodsTables meta={real} />);

    const notes = screen.getAllByText(METHODS.features.notRanked);

    expect(notes).toHaveLength(1);
    expect(notes[0]?.closest("li")).toHaveTextContent(alone.label);
  });

  test("test_a_measure_that_counts_only_as_a_part_of_a_vibe_says_so_and_names_the_vibe", () => {
    // Seen in a browser: main roads "Shown, but not used in ranking in this release", though
    // Quiet streets rests on it for 20 of the 70 shares it holds.
    const preview: MetaData = recordedAnswer("get_meta", "preview/meta").body.data;
    render(<MethodsTables meta={preview} />);
    const roads = preview.features.find((one) => one.feature_id === "road_major_exposure");
    const entry = screen.getByRole("heading", { level: 4, name: roads?.label }).closest("li") as HTMLElement;

    expect(roads?.rankable).toBe(false);
    expect(preview.tags.find((tag) => tag.tag_id === "quiet_residential")?.terms.map((term) => term.feature_id)).toContain(
      "road_major_exposure",
    );
    // Of the vibes that hold it, only one places any area. A vibe that waits counts in nothing yet.
    const holding = preview.tags
      .filter((tag) => tag.terms.some((term) => term.feature_id === "road_major_exposure"))
      .filter((tag) => preview.recipes.find((held) => held.tag_id === tag.tag_id)?.placed)
      .map((tag) => tag.label);
    expect(holding).toEqual(["Quiet streets"]);
    expect(entry.textContent?.includes(METHODS.features.partOf(LIST.format(holding)))).toBe(true);
    expect(entry.textContent?.includes(METHODS.features.notRanked)).toBe(false);
  });

  test("test_what_the_data_does_not_hold_is_said_and_no_limit_is_given_for_it", () => {
    // Seen in a browser: "Longest journey in this release: 90 minutes", on a release that
    // names no place and holds no journey.
    const preview: MetaData = recordedAnswer("get_meta", "preview/meta").body.data;
    render(<MethodsTables meta={preview} />);
    const limits = within(screen.getByRole("table", { name: METHODS.limits.title }));
    const { rows } = METHODS.limits;

    expect(preview.holds).toEqual({ journeys: false, costs: false });
    for (const name of [rows.rent, rows.buy, rows.minutes, rows.places]) {
      expect(limits.queryByRole("rowheader", { name })).toBeNull();
    }
    expect(limits.queryAllByRole("rowheader", { name: new RegExp(`^${rows.cutoff}`) })).toEqual([]);
    expect(limits.getByRole("rowheader", { name: rows.text })).toBeInTheDocument();
    const said = document.body.textContent ?? "";
    expect(said.includes(METHODS.limits.noJourneys)).toBe(true);
    expect(said.includes(METHODS.limits.noCosts)).toBe(true);
    // How a journey is timed, and how sure a cost is, are said as what is to come.
    expect(screen.getByRole("heading", { name: METHODS.journeys.title }).parentElement?.textContent).toContain(
      METHODS.journeys.notYet,
    );
    expect(screen.getByRole("heading", { name: METHODS.confidence.title }).parentElement?.textContent).toContain(
      METHODS.confidence.notYet,
    );
    // Where a search starts, a budget and a journey are said not to be in the data.
    for (const tenure of ["rent", "buy"] as const) {
      const table = within(screen.getByRole("table", { name: TENURE[tenure] }));
      for (const name of [METHODS.defaults.budget, METHODS.defaults.journeys]) {
        expect(within(table.getByRole("rowheader", { name }).closest("tr") as HTMLElement).getByText(METHODS.notInData)).toBeInTheDocument();
      }
    }
  });

  test("test_a_release_that_holds_journeys_and_costs_says_none_of_this", () => {
    render(<MethodsTables meta={meta} />);
    const said = document.body.textContent ?? "";

    for (const line of [METHODS.limits.noJourneys, METHODS.limits.noCosts, METHODS.journeys.notYet, METHODS.confidence.notYet, METHODS.notInData]) {
      expect(said.includes(line)).toBe(false);
    }
  });

  test("test_a_dimension_the_release_carries_nothing_for_says_so", () => {
    const without = { ...meta, features: meta.features.filter((m) => m.dimension !== "crime") };
    render(<MethodsTables meta={without} />);

    expect(screen.getByRole("region", { name: DIMENSION.crime })).toHaveTextContent(
      METHODS.features.none,
    );
  });

  test("test_how_an_area_with_little_known_of_it_is_ranked_is_said_as_the_contract_defines_it", () => {
    render(<MethodsTables meta={meta} />);
    const ranking = screen.getByRole("region", { name: METHODS.ranking.title });

    // What is missing is left out and the rest count for more. That alone once put first an
    // area with no figure for anything that was asked of the place.
    expect(contract()).toContain("An area with a figure for under half of it, by weight, is not scored");
    expect(contract()).toContain("whatever is known of its journeys and its cost");
    expect(ranking).toHaveTextContent("under half of what you asked of the area itself");
    expect(ranking).toHaveTextContent("is not ranked");
    expect(ranking).toHaveTextContent("Journeys and cost do not make up for it");
    expect(ranking).toHaveTextContent("Nothing is filled in");
    // It states no figure of its own: the half is said in words.
    expect(/\d/.test(METHODS.ranking.points.join(" "))).toBe(false);
  });

  test("test_what_a_feature_describes_is_said_of_every_kind_the_release_holds", () => {
    render(<MethodsTables meta={meta} />);

    // A figure of recorded crime describes what was recorded, and not a place or a building.
    // A figure of the census describes who lived there, and says so in its name.
    expect(new Set(meta.features.map((metric) => metric.describes))).toEqual(
      new Set(["place", "buildings", "events", "residents"]),
    );
    expect(METHODS.features.lead).toContain("a place, its buildings, what was recorded there, or who lived there");
    const counted = meta.features.filter((metric) => metric.describes === "residents");
    expect(counted.map((metric) => metric.feature_id).sort()).toEqual([
      "households_dependent_children",
      "households_one_person",
      "residents_aged_20_34",
      "residents_aged_65_over",
    ]);
    for (const metric of counted) {
      expect(metric.label.endsWith(", Census 2021")).toBe(true);
      expect([metric.unit, metric.polarity, metric.dimension]).toEqual(["%", "more", "residents"]);
    }
    expect(screen.getByRole("region", { name: METHODS.features.title })).toHaveTextContent(METHODS.features.lead);
  });

  test("test_when_recorded_crime_counts_is_said_by_the_one_rule_and_the_vibe_that_holds_it_is_named", () => {
    render(<MethodsTables meta={meta} />);
    const vibes = screen.getByRole("region", { name: METHODS.vibes.title });
    const crime = screen.getByRole("region", { name: DIMENSION.crime });

    expect(screen.getByRole("region", { name: METHODS.ranking.title })).toHaveTextContent(CRIME_RULE);
    // Under what is measured of recorded crime: the rule, and the caveat of every such figure.
    expect(crime).toHaveTextContent(CRIME_RULE);
    expect(crime).toHaveTextContent(CRIME_CAVEAT);
    // Among the vibes: which of them holds it, by the names the API gives, and the way to it.
    expect(vibes).toHaveTextContent(CRIME_ACCOUNT.vibes);
    expect(vibes).toHaveTextContent("Recorded criminal damage");
    expect(vibes).toHaveTextContent("Recorded anti-social behaviour");
    expect(within(vibes).getByRole("link", { name: "Gritty" })).toHaveAttribute("href", "/vibes#street_character");
    expect(vibes.textContent?.includes(CRIME_ACCOUNT.noVibe)).toBe(false);
  });

  test("test_where_no_vibe_holds_recorded_crime_the_methods_say_so_and_name_none", () => {
    render(<MethodsTables meta={variantA} />);
    const vibes = screen.getByRole("region", { name: METHODS.vibes.title });

    expect(vibes).toHaveTextContent(CRIME_ACCOUNT.noVibe);
    expect(vibes.textContent?.includes(CRIME_ACCOUNT.vibes)).toBe(false);
    expect(within(vibes).queryByRole("link", { name: "Works and warehouses" })).toBeNull();
  });

  test("test_the_vibes_have_a_page_of_their_own_which_the_methods_lead_to", () => {
    render(<MethodsTables meta={meta} />);
    const vibes = screen.getByRole("region", { name: METHODS.vibes.title });

    expect(within(vibes).getByRole("link", { name: METHODS.vibes.link })).toHaveAttribute("href", "/vibes");
    // No recipe is written out twice: a second copy is a copy that can fall behind.
    expect(within(vibes).queryByRole("table")).toBeNull();
    expect(within(vibes).getAllByRole("heading")).toHaveLength(1);
    expect(screen.queryByRole("table", { name: /^What .* is made of$/ })).toBeNull();
  });

  test("test_the_defaults_of_a_renter_and_of_a_buyer_are_both_shown", () => {
    render(<MethodsTables meta={meta} />);
    const labels = new Map(meta.features.map((metric) => [metric.feature_id, metric.label]));

    for (const [name, spec] of [
      ["Renting", meta.defaults.rent],
      ["Buying", meta.defaults.buy],
    ] as const) {
      const table = within(screen.getByRole("table", { name }));
      for (const weight of spec.weights) {
        const row = table.getByRole("row", { name: new RegExp(`^${labels.get(weight.feature_id)}`) });
        expect(row).toHaveTextContent(`${Math.round(weight.weight * 100)} of 100`);
      }
    }
  });

  test("test_what_heads_the_third_column_of_where_a_search_starts_is_true_of_every_row_under_it", () => {
    // It was headed "Direction", a word no other page uses, over "Flexible" of the budget and
    // over which journey counts, neither of which is a direction.
    render(<MethodsTables meta={meta} />);
    const { columns, budget, journeys } = METHODS.defaults;

    expect(columns.direction).toBe("How it counts");
    expect(document.body.textContent?.includes("Direction")).toBe(false);
    for (const [name, spec] of [
      [TENURE.rent, meta.defaults.rent],
      [TENURE.buy, meta.defaults.buy],
    ] as const) {
      const table = screen.getByRole("table", { name });
      const third = (row: string) =>
        within(table).getByRole("rowheader", { name: row }).closest("tr")?.querySelectorAll("td")[1]?.lastElementChild?.textContent;
      expect([...table.querySelectorAll("thead th")].map((header) => header.textContent)).toEqual([
        columns.setting,
        columns.value,
        columns.direction,
      ]);
      // The three kinds of row it heads: whether a limit is firm, which journey counts, and which way a figure counts.
      expect(third(budget)).toBe(STRICTNESS[spec.budget.strictness]);
      expect(third(journeys)).toBe(`${COMBINE[spec.commute_combine]}. ${PT_BASIS[spec.pt_basis]}.`);
      expect(spec.weights.length).toBeGreaterThan(0);
    }
  });

  test("test_the_limits_are_the_ones_the_api_serves", () => {
    render(<MethodsTables meta={meta} />);

    const limits = within(screen.getByRole("region", { name: METHODS.limits.title }));

    expect(limits.getByRole("row", { name: /^Monthly rent/ })).toHaveTextContent(
      "£300 to £20,000, in steps of £25",
    );
    expect(limits.getByRole("row", { name: /^Purchase price/ })).toHaveTextContent(
      "£50,000 to £20,000,000, in steps of £5,000",
    );
    expect(limits.getByRole("row", { name: /Public transport/ })).toHaveTextContent("90 minutes");
    expect(limits.getByRole("row", { name: /^Length of a sentence/ })).toHaveTextContent(
      "600 characters",
    );
  });

  test("test_a_limit_the_api_left_out_is_left_out_and_never_made_up", () => {
    const { cutoff_minutes, max_text, max_body_bytes } = meta.limits;
    // The contract requires these three of a release's limits, and no others.
    const bare = { ...meta, limits: { cutoff_minutes, max_text, max_body_bytes } };
    const { container } = render(<MethodsTables meta={bare as unknown as MetaData} />);

    const limits = within(screen.getByRole("region", { name: METHODS.limits.title }));

    expect(limits.queryByRole("row", { name: /^Monthly rent/ })).toBeNull();
    expect(limits.queryByRole("row", { name: /^Places you can ask to reach/ })).toBeNull();
    expect(limits.getByRole("row", { name: /^Length of a sentence/ })).toBeInTheDocument();
    expect(container).not.toHaveTextContent(/undefined|NaN|null/);
  });

  test("test_the_release_and_the_engine_are_named", () => {
    render(<MethodsTables meta={meta} />);

    const release = screen.getByRole("region", { name: METHODS.release.title });

    expect(release).toHaveTextContent(meta.release_id);
    expect(release).toHaveTextContent(meta.engine_version);
    expect(release).toHaveTextContent("23 September 2026");
    expect(release).toHaveTextContent(`${METHODS.release.rows.synthetic}${METHODS.release.yes}`);
    expect(release).toHaveTextContent(`${METHODS.release.rows.preview}${METHODS.release.no}`);
  });

  test("test_a_preview_is_said_to_be_one_beside_whether_its_data_is_made_up", () => {
    render(<MethodsTables meta={{ ...meta, synthetic: false, preview: true }} />);

    const release = screen.getByRole("region", { name: METHODS.release.title });

    expect(release).toHaveTextContent(`${METHODS.release.rows.synthetic}${METHODS.release.no}`);
    expect(release).toHaveTextContent(`${METHODS.release.rows.preview}${METHODS.release.yes}`);
  });

  test("test_no_figure_is_shown_that_the_api_did_not_send", () => {
    const real = realLooking();
    const { container } = render(<MethodsTables meta={real} />);
    const sent = numbersSent(real);
    // The numbers site copy states: how many homes make a cost sure. Each is held to the
    // project's own record by a test. How long a provider keeps words is the service's to say.
    const stated = new Set(
      numbersIn([...METHODS.words.points, ...Object.values(METHODS.confidence.rows)].join(" ")),
    );

    const shown = numbersIn(container.textContent ?? "");
    const invented = shown.filter((number) => !sent.has(number) && !stated.has(number));

    expect(shown.length).toBeGreaterThan(100);
    expect(invented).toEqual([]);
  });

  test("test_what_each_word_for_how_sure_a_cost_is_means_is_said_as_the_contract_defines_it", () => {
    render(<MethodsTables meta={meta} />);

    // "Confidence: medium" is on every cost, and no page said what it meant.
    expect(contract()).toContain("High: at least 50 observations. Medium: 10 to 49, blended. Low: modelled");
    const said = screen.getByRole("region", { name: METHODS.confidence.title });
    expect(said.querySelector("h2")).toHaveAttribute("id", "confidence");
    expect(within(said).getAllByRole("listitem").map((item) => item.textContent)).toEqual([
      METHODS.confidence.rows.high,
      METHODS.confidence.rows.medium,
      METHODS.confidence.rows.low,
      METHODS.confidence.rows.unstated,
    ]);
    // A price that is one number rests on a count nobody gives, and the page says so.
    expect(contract()).toContain("It is `unstated` because the publisher gives a figure with no count of the sales behind it");
    expect(METHODS.confidence.rows.unstated).toMatch(/^Not stated: .*no range.*does not say how many sales/);
    expect(METHODS.confidence.rows.high).toMatch(/^High: .*at least 50\b/);
    expect(METHODS.confidence.rows.medium).toMatch(/^Medium: .*10 to 49\b.*blended/);
    expect(METHODS.confidence.rows.low).toMatch(/^Low: .*modelled/);
  });

  test("test_each_word_for_how_sure_a_cost_is_says_what_follows_for_whoever_reads_the_cost", () => {
    // Every cost leads here. "So the range is blended" and "the range is modelled" said how
    // a range was made, in two words of the trade, and not how far it is to be trusted.
    const { high, medium, low } = METHODS.confidence.rows;

    // It is said in the words of the line over them, "how far it is to be trusted".
    expect(METHODS.confidence.lead).toMatch(/\bhow far it is to be trusted\b/);
    expect(medium).toMatch(/\bcan be trusted less than a high one\b/);
    expect(low).toMatch(/\bcan be trusted the least of the three\b/);
    // "Less sure" is what a service said of a vibe, which no page passes on: no cost is said to be so.
    for (const line of Object.values(METHODS.confidence.rows)) expect([line, /\bless sure\b/i.test(line)]).toEqual([line, false]);
    // A word of the trade is said with what it means.
    expect(medium).toMatch(/\bblended, which means\b/);
    expect(low).toMatch(/\bmodelled, which means\b/);
    // A range is blended where Burro works it out. One that its publisher gives is medium
    // by how many were recorded, and nothing of it is blended: the line is true of both.
    expect(contract()).toContain("`medium` from 10 to 49, and nothing is blended");
    expect(medium).toMatch(/^Medium: only 10 to 49 were recorded, so the range can be trusted less than a high one\. A range that Burro works out\b/);
    // The counts are the contract's, and of a low range it gives none.
    expect(high).toMatch(/\bat least 50\b/);
    expect(numbersIn(low)).toEqual([]);
  });

  test("test_how_an_area_is_named_is_said_as_the_contract_defines_it_and_that_a_name_is_a_draft", () => {
    render(<MethodsTables meta={meta} />);

    const said = screen.getByRole("region", { name: METHODS.names.title });
    // The page of an area leads here by this id.
    expect(said.querySelector("h2")).toHaveAttribute("id", "names");
    expect(within(said).getAllByRole("listitem").map((item) => item.textContent)).toEqual([
      ...METHODS.names.points,
    ]);
    // Which name an area bears, as the contract gives the rule.
    expect(contract()).toContain(
      "An area bears the name of the drafted neighbourhood that holds more of its output areas than any other",
    );
    expect(said).toHaveTextContent("bears the name of the neighbourhood that holds most of its output areas");
    expect(contract()).toContain("keeps its publisher's label");
    expect(said).toHaveTextContent("keeps its label");
    // Two areas of one name, and what each then says.
    expect(contract()).toContain("each adds the side of them it lies on");
    expect(said).toHaveTextContent("each adds the side it lies on");
    // A name is a draft until a person has checked it, and the page says so.
    expect(contract()).toContain("A name is a draft until a person has decided it at the review desk");
    expect(said).toHaveTextContent("Every name is a draft until a person has checked it");
    // No name is coined, and the page names no place and holds no figure.
    expect(said).toHaveTextContent("Burro coins no name and changes none");
    expect(/\d/.test(METHODS.names.points.join(" "))).toBe(false);
  });

  test("test_over_a_made_up_city_how_an_area_is_named_says_first_that_its_names_are_invented", () => {
    // Seen in a browser: the page of every area of the made-up city said that its name comes
    // from Burro, and led here, where the page said that Burro coins no name.
    render(<MethodsTables meta={meta} />);

    const said = screen.getByRole("region", { name: METHODS.names.title });

    expect(meta.synthetic).toBe(true);
    expect([...said.querySelectorAll("p")].map((line) => line.textContent)).toEqual([METHODS.names.madeUp]);
    // It stands before the method, which is then the method of a city that is not made up.
    expect(said.querySelector("p")?.compareDocumentPosition(within(said).getByRole("list")) ?? 0).toBe(
      Node.DOCUMENT_POSITION_FOLLOWING,
    );
    expect(METHODS.names.madeUp).toMatch(/\bmade-up city\b.*\binvented\b/);
    expect(METHODS.names.madeUp).toMatch(/\ba real city\b/);
    // Nothing of the method is taken away, and the way the page of an area leads here by stands.
    expect(within(said).getAllByRole("listitem").map((item) => item.textContent)).toEqual([...METHODS.names.points]);
    expect(said.querySelector("h2")).toHaveAttribute("id", "names");
  });

  test("test_over_a_city_that_is_not_made_up_how_an_area_is_named_says_nothing_of_a_made_up_one", () => {
    // Only an answer knows whether its data is made up, and the line is drawn by what it says.
    render(<MethodsTables meta={realLooking()} />);

    const said = screen.getByRole("region", { name: METHODS.names.title });

    expect(said.querySelectorAll("p")).toHaveLength(0);
    expect(document.body.textContent?.includes(METHODS.names.madeUp)).toBe(false);
    expect(within(said).getAllByRole("listitem").map((item) => item.textContent)).toEqual([...METHODS.names.points]);
  });

  test("test_how_an_area_is_named_names_no_city_and_no_other_place", () => {
    // It said "Burro's draft of London's neighbourhoods", over the made-up city too. The name
    // of a place begins with a capital: in these lines no word does but the first of a
    // sentence, and the name of Burro.
    for (const line of [...METHODS.names.points, METHODS.names.madeUp]) {
      const named = line
        .split(/(?<=\.)\s+/)
        .flatMap((sentence) => sentence.split(/\s+/).slice(1))
        .filter((word) => /^[A-Z]/.test(word) && !/^Burro\b/.test(word));
      expect([line, named]).toEqual([line, []]);
    }
    expect(METHODS.names.points[2]).toMatch(/^To choose a name, Burro first gives each small census output area to the named neighbourhood\b/);
  });

  test("test_how_a_journey_is_timed_is_said_as_the_contract_defines_it", () => {
    render(<MethodsTables meta={meta} />);

    expect(contract()).toContain("Times are door to door, on a weekday morning peak.");
    expect(contract()).toContain(
      "about {typical} minutes on a typical weekday morning, or {missed} minutes if you just miss a service",
    );
    const said = screen.getByRole("region", { name: METHODS.journeys.title });
    expect(said.querySelector("h2")).toHaveAttribute("id", "journeys");
    expect(said).toHaveTextContent("door to door");
    expect(said).toHaveTextContent("weekday morning");
    expect(said).toHaveTextContent("just miss");
    // A journey at the longest time set is worth a half, and one half as long again nothing.
    expect(contract()).toMatch(/UTILITY_AT_CAP += 0\.5\b/);
    expect(contract()).toMatch(/ZERO_AT_SHARE += 1\.5\b/);
    expect(said).toHaveTextContent("for a half at the longest time you set, and for nothing at half as long again");
    // With several places the one that does least well against its own limit counts, which is
    // the API's `slowest`. No journey is said to do badly: it is said against the rest.
    expect(contract()).toContain("`slowest`, the default, takes the `min` of the destinations' utilities");
    expect(said).toHaveTextContent("only the journey that does least well against its own limit counts");
    // It holds no figure of its own: the longest journey the data holds is in the limits, from the API.
    expect(/\d/.test(METHODS.journeys.points.join(" "))).toBe(false);
  });

  test("test_where_a_journey_is_estimated_the_page_says_how_in_the_apis_own_numbers", () => {
    const estimated = recordedAnswer("get_meta", "estimate/meta").body.data;
    const how = estimated.journey_estimate;
    if (!how) throw new Error("the recorded release estimates no journey");
    render(<MethodsTables meta={estimated} />);

    const said = screen.getByRole("region", { name: METHODS.estimate.title });
    // A result leads here by the same id, whether a journey is timed or estimated.
    expect(said.querySelector("h2")).toHaveAttribute("id", "journeys");
    expect(screen.queryByRole("region", { name: METHODS.journeys.title })).toBeNull();
    // The line that stands wherever an estimate is shown comes first, as the API serves it.
    expect(said.querySelector("p")?.textContent?.startsWith(how.said)).toBe(true);
    // It is the line the fact of every estimated journey carries, so the page that explains
    // an estimate says of it what a result says.
    const journeys = recordedAnswer("explain_top", "estimate/explanations").body.data.facts.filter(
      (fact) => fact.template === "travel_estimated",
    );
    expect(journeys.length).toBeGreaterThan(0);
    for (const fact of journeys) expect(fact.slots.estimated).toBe(how.said);
    expect(said).toHaveTextContent("It is never given in minutes.");
    // Every number of it is the API's. Site copy holds none of its own.
    expect(numbersIn(METHODS.estimate.lead)).toEqual([]);
    const sent = numbersSent(how);
    const shown = numbersIn(said.textContent ?? "");
    expect(shown.filter((number) => !sent.has(number))).toEqual([]);
    expect(shown).toEqual(
      [how.fixed_minutes, how.minutes_a_km, how.near_the_underground_m, how.minutes_a_km_near_the_underground]
        .map(String)
        .concat([String(how.within_by), String(how.beyond_by)]),
    );
    expect(said).toHaveTextContent("A firm limit leaves out only the areas that are likely beyond it.");
    expect(said).toHaveTextContent("By bike and on foot nothing is estimated.");
    expect(said).toHaveTextContent("Once Burro has a journey time, the time takes the place of the estimate.");
    // What likely within means is said from the number the API serves, which the founder
    // widened on 2026-09-25, and the page says it is no promise.
    expect(said).toHaveTextContent(
      `Likely within: the estimate is at least ${how.within_by} minutes under your limit.`,
    );
    expect(said).toHaveTextContent("Likely within is what the estimate says, and is no promise.");
    // And what the estimate was held against, and what it could not be held against.
    expect(said).toHaveTextContent(
      "The estimate has been held against journeys timed from the timetables of the Underground and the DLR.",
    );
    expect(said).toHaveTextContent("It could not be held against trains");
    expect(said).not.toHaveTextContent("The numbers are a first guess.");
    expect(said).not.toHaveTextContent("They have not been checked against journeys that were timed.");
  });

  test("test_where_a_rent_is_of_a_wider_place_the_page_says_so_and_says_the_caution_once", () => {
    const let_ = recordedAnswer("get_meta", "let/meta").body.data;
    const said = let_.rents;
    if (!said) throw new Error("the recorded release holds no rent of a wider place");
    render(<MethodsTables meta={let_} />);

    const rents = screen.getByRole("region", { name: METHODS.rents.title });
    // An area's page leads here by this id.
    expect(rents.querySelector("h2")).toHaveAttribute("id", "rents");
    // What is said of the rents themselves is the API's, and comes first.
    expect(rents.querySelector("p")?.textContent).toBe(`${said.of_a_place} ${said.caution}`);
    expect(document.body.textContent?.split(said.caution)).toHaveLength(2);
    expect(rents).toHaveTextContent("half or more of its homes");
    expect(rents).toHaveTextContent("more than a quarter over your budget");
    // It quotes no figure of any place to make the point.
    expect(said.caution).not.toMatch(/[0-9£]/);
  });

  test("test_a_release_whose_rents_are_of_the_area_alone_says_nothing_of_a_wider_place", () => {
    render(<MethodsTables meta={meta} />);

    expect(meta.rents ?? null).toBeNull();
    expect(screen.queryByRole("region", { name: METHODS.rents.title })).toBeNull();
  });

  test("test_a_release_that_holds_its_journey_times_says_nothing_of_an_estimate", () => {
    render(<MethodsTables meta={meta} />);

    expect(meta.journey_estimate ?? null).toBeNull();
    expect(screen.queryByRole("region", { name: METHODS.estimate.title })).toBeNull();
    expect(screen.getByRole("region", { name: METHODS.journeys.title })).toBeInTheDocument();
    // Neither the line the service says of an estimate nor the website's own is on the page.
    const ofAnEstimate = recordedAnswer("get_meta", "estimate/meta").body.data.journey_estimate?.said;
    expect(ofAnEstimate).toBeTruthy();
    for (const line of [ofAnEstimate ?? "", JOURNEYS.estimatedFrom]) {
      expect(document.body.textContent?.includes(line)).toBe(false);
    }
  });

  test("test_how_a_persons_words_are_handled_is_said_in_full", () => {
    render(<MethodsTables meta={meta} />);

    const words = screen.getByRole("region", { name: METHODS.words.title });

    expect(words).toHaveTextContent("Burro does not keep it");
    expect(words).toHaveTextContent("never put in a web address");
    expect(words).toHaveTextContent("stores nothing in your browser");
    // Where no model reads, the service says so, and there is no provider to tell of.
    expect(meta.reader.model_reads).toBe(false);
    expect(words).toHaveTextContent(meta.reader.notice);
    expect(words).toHaveTextContent("not sent to a language model");
    expect(within(words).queryByRole("table")).toBeNull();
  });

  test("test_where_nobody_can_sign_in_the_page_says_nothing_of_a_cookie_or_of_signing_in", () => {
    expect(process.env[ACCOUNTS_VARIABLE]).toBeUndefined();
    render(<MethodsTables meta={meta} />);

    const words = screen.getByRole("region", { name: METHODS.words.title });

    expect(words).toHaveTextContent(METHODS.words.points[2]);
    expect(METHODS.words.points[2]).toMatch(/^The website stores nothing in your browser\./);
    expect(words).not.toHaveTextContent(/cookie|sign in|signed in/i);
  });

  test("test_where_a_person_can_sign_in_the_page_says_what_the_browser_and_burro_then_keep", () => {
    // With accounts on a browser holds two cookies, and the service a search that was kept.
    process.env[ACCOUNTS_VARIABLE] = ON;
    try {
      render(<MethodsTables meta={meta} />);

      const words = screen.getByRole("region", { name: METHODS.words.title });

      expect(words).toHaveTextContent(KEPT_WITH_ACCOUNTS);
      expect(KEPT_WITH_ACCOUNTS).toMatch(/^The website stores nothing in your browser unless you ask for a link to sign in\./);
      expect(KEPT_WITH_ACCOUNTS).toMatch(/it sets a cookie\b.*\ba second cookie keeps you signed in\b/);
      expect(KEPT_WITH_ACCOUNTS).toMatch(/gone when you close the page, unless you are signed in and Burro keeps it for you\.$/);
      // What is true only while nobody can sign in is not said beside it, and no point is added or moved.
      expect(words).not.toHaveTextContent(METHODS.words.points[2]);
      const said = within(words).getAllByRole("listitem").map((point) => point.textContent);
      expect(said).toEqual(METHODS.words.points.map((point, at) => (at === 2 ? KEPT_WITH_ACCOUNTS : point)));
      // A figure of accounts is the service's to say.
      expect(numbersIn(KEPT_WITH_ACCOUNTS)).toEqual([]);
    } finally {
      delete process.env[ACCOUNTS_VARIABLE];
    }
  });

  test("test_what_is_true_of_the_provider_that_reads_is_said_as_the_service_said_it", () => {
    for (const recorded of ["meta-model-reads", "meta-model-reads-with-settings"]) {
      const served = recordedAnswer("get_meta", recorded).body.data;
      const { unmount } = render(<MethodsTables meta={served} />);
      const words = screen.getByRole("region", { name: METHODS.words.title });
      const { reader } = served;

      expect(reader.model_reads).toBe(true);
      expect(words).toHaveTextContent(reader.notice);
      // What the company does with the words is on the company's own page, and the link
      // leads there. Nothing the service did not say of the company is said here.
      expect(within(words).getByRole("link", { name: READER.terms })).toHaveAttribute("href", reader.terms_url);
      expect(within(words).queryByRole("table")).toBeNull();
      // A page built ahead of time says that it was, and points at no line of another page:
      // the one under the search box, which asked the service afresh, is gone.
      expect(words).toHaveTextContent(METHODS.words.reader.asBuilt);
      expect(METHODS.words.reader.asBuilt).toBe("This is what the service said when this page was built.");
      expect(/search box|under the box/i.test(JSON.stringify(METHODS.words))).toBe(false);
      unmount();
    }
  });

  test("test_the_methods_have_no_accessibility_fault", async () => {
    const { container } = render(
      <main>
        <h1>{METHODS.title}</h1>
        <MethodsTables meta={realLooking()} />
      </main>,
    );

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });
});

describe("the methods, in the look", () => {
  const SHEET = rulesOf(readFileSync(path.resolve(__dirname, "MethodsTables.module.css"), "utf8"));
  const setsOf = (selector: string, under: string | null = null) =>
    new Map(SHEET.filter((rule) => rule.selector === selector && rule.under === under).flatMap((rule) => [...rule.sets]));
  const STACKED = "@container (max-width: 30rem)";
  /** Every release that was recorded to show a state of the methods. */
  const RELEASES: readonly (readonly [string, MetaData])[] = [
    ["the made-up city", meta],
    ["a release that holds no recorded crime", variantA],
    ["a preview", recordedAnswer("get_meta", "preview/meta").body.data],
    ["a release whose journeys are estimated", recordedAnswer("get_meta", "estimate/meta").body.data],
    ["a release whose rents are of a wider place", recordedAnswer("get_meta", "let/meta").body.data],
    ["a release that a model reads for", recordedAnswer("get_meta", "meta-model-reads").body.data],
  ];

  test.each(RELEASES)("test_nothing_of_the_methods_is_read_on_the_grass: %s", (_, given) => {
    const { container } = render(<MethodsTables meta={given} />);

    expect(onTheGrass(container)).toEqual([]);
  });

  test("test_every_part_stands_in_a_box_of_its_own_under_its_heading", () => {
    render(<MethodsTables meta={meta} />);

    const parts = screen.getAllByRole("heading", { level: 2 });

    expect(parts.length).toBeGreaterThan(9);
    for (const heading of parts) {
      const box = heading.closest("[data-kind]");
      expect([heading.textContent, box?.getAttribute("data-kind")]).toEqual([heading.textContent, "box"]);
      // Each box is told that it brings its own room, so that the room is said in one place.
      expect(box).not.toHaveClass("roomy");
    }
    // No box stands in a box: a part is a box on the grass, and what it holds has a plain edge.
    for (const box of document.querySelectorAll("[data-kind='box']")) {
      expect(box.parentElement?.closest("[data-kind='box']") ?? null).toBeNull();
    }
  });

  test("test_what_is_measured_is_a_box_for_what_it_is_and_a_box_for_each_group_of_measures", () => {
    render(<MethodsTables meta={meta} />);
    const measured = screen.getByRole("region", { name: METHODS.features.title });

    // It is many parts, and is no box itself: the grass shows between its groups.
    expect(measured).not.toHaveAttribute("data-kind");
    expect([...measured.children].map((part) => part.getAttribute("data-kind"))).toEqual(
      [...measured.children].map(() => "box"),
    );
    expect(measured.firstElementChild).toHaveTextContent(METHODS.features.lead);
    // A group is named by a heading of the third rank, as it was, and is a landmark, as it was.
    const groups = within(measured).getAllByRole("region");
    expect(groups.map((group) => within(group).getByRole("heading", { level: 3 }).textContent)).toEqual(
      groups.map((group) => group.querySelector("h3")?.textContent),
    );
    expect(groups).toHaveLength(measured.children.length - 1);
  });

  test("test_each_measure_is_a_card_with_a_plain_edge_and_the_drawing_of_its_family_before_its_name", () => {
    render(<MethodsTables meta={meta} />);

    const plain = `url("${pictureOf(PLAIN)}")`;
    for (const metric of meta.features) {
      const name = screen.getByRole("heading", { level: 4, name: metric.label });
      const card = name.closest("li");
      const thing = name.previousElementSibling;
      const drawn = thing?.querySelector<HTMLElement>("[style*='/art/']")?.style.getPropertyValue("--art");
      // There are many of them, and a shadow under each would be noise.
      expect([metric.feature_id, card?.getAttribute("data-kind")]).toEqual([metric.feature_id, "plain"]);
      // By the family the service puts the measure in. Where it puts it in none, by the
      // dimension it gives the measure, as the group of the settings that holds it is drawn.
      expect([metric.feature_id, drawn]).toEqual([
        metric.feature_id,
        `url("${pictureOf(drawingOf({ kind: "feature", id: metric.feature_id, family: metric.family ?? metric.dimension }))}")`,
      ]);
      // Every measure of the release has a drawing: none is left under the plain box.
      expect([metric.feature_id, drawn === plain]).toEqual([metric.feature_id, false]);
      expect(thing).toHaveAttribute("aria-hidden", "true");
      expect(name.textContent).toBe(metric.label);
    }
    expect(new Set(meta.features.map((metric) => metric.family)).has(null)).toBe(true);
  });

  test("test_a_measure_of_no_family_and_of_a_dimension_nobody_drew_takes_the_plain_drawing", () => {
    // A measure of a kind that nobody has drawn, which a later release puts in no family.
    const first = meta.features.find((metric) => drawingOf({ kind: "feature", family: metric.dimension }) === PLAIN);
    if (first === undefined) throw new Error("Every dimension of the recorded release has a drawing.");
    const undrawn = { ...first, family: null };
    render(<MethodsTables meta={{ ...meta, features: meta.features.map((metric) => (metric === first ? undrawn : metric)) }} />);

    const name = screen.getByRole("heading", { level: 4, name: first.label });
    const drawn = name.previousElementSibling?.querySelector<HTMLElement>("[style*='/art/']");

    expect(drawn?.style.getPropertyValue("--art")).toBe(`url("${pictureOf(PLAIN)}")`);
  });

  test("test_the_sources_of_a_measure_stand_after_the_key_of_the_look", () => {
    render(<MethodsTables meta={realLooking()} />);

    for (const metric of realLooking().features) {
      const card = screen.getByRole("heading", { level: 4, name: metric.label }).closest("li") as HTMLElement;
      const list = within(card).getByRole("list");
      const key = list.previousElementSibling as HTMLElement | null;
      expect([metric.feature_id, key?.style.getPropertyValue("--art")]).toEqual([metric.feature_id, 'url("/art/ui-key.png")']);
      expect(key).toHaveAttribute("aria-hidden", "true");
      expect(within(list).getAllByRole("link")).toHaveLength(metric.source_ids.length);
    }
  });

  test("test_what_is_drawn_in_a_measure_is_small_on_every_screen", () => {
    // Seen in a browser: on a desk the key of a source took half the room of its source, whose name broke in two.
    expect(setsOf(".feature").get("--px")).toBe("var(--px-ground)");
  });

  test("test_every_table_stands_inside_a_plain_edge_of_ink", () => {
    render(<MethodsTables meta={meta} />);

    const tables = screen.getAllByRole("table");

    expect(tables).toHaveLength(3);
    for (const table of tables) expect(table.parentElement).toHaveAttribute("data-kind", "plain");
  });

  test("test_a_table_is_stacked_in_a_narrow_box_and_every_part_of_it_says_its_role_again", () => {
    // Seen on a phone: the name of a setting, which runs to a line, stood in a column of a
    // hundred pixels, a word to a line and a word broken in two. And with the text made
    // twice as large the table of limits made the page wider than the window.
    render(<MethodsTables meta={meta} />);
    const { columns } = METHODS.defaults;
    const expected: readonly (readonly [string, readonly string[]])[] = [
      [TENURE.rent, [columns.setting, columns.value, columns.direction]],
      [TENURE.buy, [columns.setting, columns.value, columns.direction]],
      [METHODS.limits.title, [METHODS.limits.columns.limit, METHODS.limits.columns.value]],
    ];

    for (const [name, headings] of expected) {
      const table = screen.getByRole("table", { name });
      expect(table).toHaveAttribute("role", "table");
      for (const row of table.querySelectorAll("tr")) expect(row).toHaveAttribute("role", "row");
      for (const header of table.querySelectorAll("thead th")) expect(header).toHaveAttribute("role", "columnheader");
      for (const header of table.querySelectorAll("tbody th")) expect(header).toHaveAttribute("role", "rowheader");
      expect([name, [...table.querySelectorAll("thead th")].map((header) => header.textContent)]).toEqual([name, headings]);
      const rows = [...table.querySelectorAll("tbody tr")];
      expect(rows.length).toBeGreaterThan(3);
      for (const row of rows) {
        const cells = [...row.querySelectorAll("td")];
        for (const cell of cells) expect(cell).toHaveAttribute("role", "cell");
        // Stacked, each cell says what it is of, for the eye. The column says it to a reader.
        expect(cells.map((cell) => cell.querySelector("[aria-hidden='true']")?.textContent)).toEqual(headings.slice(1));
        // What a cell says is what it said: the name of its column is no part of it to a reader.
        for (const cell of cells) expect(cell.lastElementChild).not.toHaveAttribute("aria-hidden");
      }
    }
    // It is stacked by the width of its own box, and not of the screen: two stand side by side on a wide one.
    expect(setsOf(".tenure").get("container-type")).toBe("inline-size");
    expect(setsOf(".limits").get("container-type")).toBe("inline-size");
    expect(screen.getByRole("table", { name: METHODS.limits.title }).closest("[data-kind='plain']")?.parentElement).toHaveClass("limits");
    expect(setsOf("table.stacks tr", STACKED).get("display")).toBe("block");
    expect(setsOf("table.stacks .cellName", STACKED).get("display")).toBe("inline");
    expect(setsOf(".cellName").get("display")).toBe("none");
    // The headings of the columns are kept for a screen reader, and are not taken out of the page.
    expect(setsOf("table.stacks .head", STACKED).get("clip-path")).toBe("inset(50%)");
    expect(SHEET.filter((rule) => /\.head/.test(rule.selector) && rule.sets.get("display") === "none")).toEqual([]);
  });

  test("test_a_setting_the_data_does_not_hold_says_so_across_the_row_and_names_no_column", () => {
    const preview: MetaData = recordedAnswer("get_meta", "preview/meta").body.data;
    render(<MethodsTables meta={preview} />);

    const row = within(screen.getByRole("table", { name: TENURE.rent })).getByRole("rowheader", { name: METHODS.defaults.budget }).closest("tr");
    const cells = [...(row?.querySelectorAll("td") ?? [])];

    expect(cells.map((cell) => [cell.getAttribute("colspan"), cell.textContent])).toEqual([["2", METHODS.notInData]]);
  });

  test("test_when_recorded_crime_counts_is_drawn_as_a_notice_and_in_no_colour_of_a_fault", () => {
    render(<MethodsTables meta={meta} />);
    const crime = screen.getByRole("region", { name: DIMENSION.crime });
    const notice = setsOf(".notice");

    expect(crime.querySelector("h3")?.nextElementSibling?.textContent).toBe(`${CRIME_ACCOUNT.rule}${CRIME_CAVEAT}`);
    expect([notice.get("background"), notice.get("border"), notice.get("box-shadow")]).toEqual([
      "var(--notice-bg)",
      "var(--edge) solid var(--notice-edge)",
      "inset calc(var(--px) * 2) 0 0 var(--notice-mark)",
    ]);
    expect(SHEET.filter((rule) => [...rule.sets.values()].some((value) => /var\(--(poppy|error|error-edge|tradeoff|tradeoff-mark)\)/.test(value)))).toEqual([]);
  });

  test("test_on_a_wide_screen_the_account_is_read_in_two_columns_so_that_all_of_it_is_in_sight_at_once", () => {
    // Seen in a browser at 1440 by 900: in one column, as wide as a line reads well, the
    // account left half of its box bare and its last paragraph under the foot of the window.
    const wide = "@media (min-width: 60rem)";

    expect(setsOf(".account").get("grid-template-columns")).toBe("minmax(0, 1fr)");
    expect([setsOf(".account", wide).get("display"), setsOf(".account", wide).get("columns")]).toEqual(["block", "2"]);
    // A paragraph is read whole in its column, and the ways on stand under both.
    expect(setsOf(".account > p", wide).get("break-inside")).toBe("avoid");
    expect(setsOf(".ways", wide).get("column-span")).toBe("all");
  });

  test("test_the_bar_of_the_fold_is_a_box_on_the_grass_and_what_it_opens_stands_boxes_of_its_own", () => {
    render(<MethodsTables meta={meta} />);

    const bar = full().querySelector(":scope > summary") as HTMLElement;
    const opened = bar.nextElementSibling as HTMLElement;

    expect(bar).toHaveAttribute("data-kind", "box");
    expect(opened).not.toHaveAttribute("data-kind");
    // Each part is a box of the opened fold itself, or stands in what holds boxes and is none.
    for (const part of opened.children) {
      const boxes = part.matches("[data-kind='box']") ? [part] : [...part.children];
      expect(boxes.map((box) => box.getAttribute("data-kind"))).toEqual(boxes.map(() => "box"));
    }
  });
});
