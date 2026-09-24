import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen, within } from "@testing-library/react";

import { CRIME_ACCOUNT, CRIME_RULE } from "@/content/crime";
import { DIMENSION, POLARITY, TENURE } from "@/content/labels";
import { METHODS } from "@/content/methods";
import { CRIME_CAVEAT } from "@/content/settings";
import { READER } from "@/content/site";
import { readRecorded, recordedAnswer } from "@/lib/api/recorded";
import type { MetaData, Metric } from "@/lib/api/schema";
import { readableDate } from "@/lib/format";

import { faultsIn } from "../../../test/support/axe";
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
    // Quiet streets rests on it for 40 of the 70 shares it holds.
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
    expect(ranking).toHaveTextContent("under half of what you asked of the place itself");
    expect(ranking).toHaveTextContent("is not ranked");
    expect(ranking).toHaveTextContent("Journeys and cost do not make up for it");
    expect(ranking).toHaveTextContent("Nothing is filled in");
    // It states no figure of its own: the half is said in words.
    expect(/\d/.test(METHODS.ranking.points.join(" "))).toBe(false);
  });

  test("test_what_a_feature_describes_is_said_of_every_kind_the_release_holds", () => {
    render(<MethodsTables meta={meta} />);

    // A figure of recorded crime describes what was recorded, and not a place or a building.
    expect(new Set(meta.features.map((metric) => metric.describes))).toEqual(new Set(["place", "buildings", "events"]));
    expect(METHODS.features.lead).toContain("a place, its buildings or what was recorded there");
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

  test("test_how_a_journey_is_timed_is_said_as_the_contract_defines_it", () => {
    render(<MethodsTables meta={meta} />);

    expect(contract()).toContain("Times are door to door, on a weekday morning peak.");
    expect(contract()).toContain("about {typical} minutes on a typical weekday morning, {missed} if you just miss a service");
    const said = screen.getByRole("region", { name: METHODS.journeys.title });
    expect(said.querySelector("h2")).toHaveAttribute("id", "journeys");
    expect(said).toHaveTextContent("door to door");
    expect(said).toHaveTextContent("weekday morning");
    expect(said).toHaveTextContent("just miss");
    // A journey at the longest time set is worth a half, and one half as long again nothing.
    expect(contract()).toMatch(/UTILITY_AT_CAP += 0\.5\b/);
    expect(contract()).toMatch(/ZERO_AT_SHARE += 1\.5\b/);
    expect(said).toHaveTextContent("for a half at the longest time you set, and for nothing at half as long again");
    // With several places the worst against its own limit counts, which is the API's `slowest`.
    expect(contract()).toContain("`slowest`, the default, takes the `min` of the destinations' utilities");
    expect(said).toHaveTextContent("only the journey that does worst against its own limit counts");
    // It holds no figure of its own: the longest journey the data holds is in the limits, from the API.
    expect(/\d/.test(METHODS.journeys.points.join(" "))).toBe(false);
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
      // A page built ahead of time says that it was, and where what is so now is said.
      expect(words).toHaveTextContent(METHODS.words.reader.asBuilt);
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
