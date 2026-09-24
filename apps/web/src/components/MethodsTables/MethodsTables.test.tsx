import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen, within } from "@testing-library/react";

import { DIMENSION, POLARITY } from "@/content/labels";
import { METHODS } from "@/content/methods";
import { recordedAnswer } from "@/lib/api/recorded";
import type { MetaData, Metric } from "@/lib/api/schema";

import { faultsIn } from "../../../test/support/axe";
import { MethodsTables } from "./MethodsTables";

const meta = recordedAnswer("get_meta", "meta").body.data;

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
      expect(card.getByText(metric.vintage)).toBeInTheDocument();
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
    const real = realLooking();
    render(<MethodsTables meta={real} />);

    const notes = screen.getAllByText(METHODS.features.notRanked);

    expect(notes).toHaveLength(1);
    expect(notes[0]?.closest("li")).toHaveTextContent(real.features[1]!.label);
  });

  test("test_a_dimension_the_release_carries_nothing_for_says_so", () => {
    const without = { ...meta, features: meta.features.filter((m) => m.dimension !== "crime") };
    render(<MethodsTables meta={without} />);

    expect(screen.getByRole("region", { name: DIMENSION.crime })).toHaveTextContent(
      METHODS.features.none,
    );
  });

  test("test_every_tag_shows_its_whole_formula", () => {
    render(<MethodsTables meta={meta} />);
    const labels = new Map(meta.features.map((metric) => [metric.feature_id, metric.label]));

    for (const tag of meta.tags) {
      const table = within(screen.getByRole("table", { name: tag.label }));
      const rows = table.getAllByRole("row").slice(1);
      expect(rows.map((row) => within(row).getByRole("rowheader").textContent)).toEqual(
        tag.terms.map((term) => labels.get(term.feature_id)),
      );
      expect(rows.map((row) => within(row).getAllByRole("cell")[1]?.textContent)).toEqual(
        tag.terms.map((term) => `${term.hundredths} of 100`),
      );
    }
    expect(meta.tags).toHaveLength(12);
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
  });

  test("test_no_figure_is_shown_that_the_api_did_not_send", () => {
    const real = realLooking();
    const { container } = render(<MethodsTables meta={real} />);
    const sent = numbersSent(real);
    // The numbers site copy states: how long a model's provider may keep what it is sent,
    // and how many homes make a cost sure. Each is held to the project's own record by a test.
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
    ]);
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
    expect(words).toHaveTextContent("may keep it for up to 30 days");
    expect(words).toHaveTextContent("never put in a web address");
    expect(words).toHaveTextContent("stores nothing in your browser");
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
