import { render, screen } from "@testing-library/react";
import { renderToStaticMarkup } from "react-dom/server";

import { SOURCE_LINE } from "@/content/area";
import { SOURCE } from "@/content/search";
import { recordedAnswer } from "@/lib/api/recorded";
import type { Fact } from "@/lib/api/schema";

import { faultsIn } from "../../../test/support/axe";
import { SourceLine } from "./SourceLine";

const facts = recordedAnswer("get_area", "area/alderwick").body.data.facts;
const cost = facts.find((fact) => fact.kind === "cost") as Fact;
const feature = facts.find((fact) => fact.kind === "feature") as Fact;
const vibe = facts.find((fact) => fact.kind === "tag") as Fact;

/** A fact as a real release would hold it: two sources, and data that is not made up. */
const real: Fact = {
  ...feature,
  synthetic: false,
  as_of: "2024-10 to 2026-09",
  sources: [
    { source_id: "os-open-greenspace", name: "OS Open Greenspace", publisher: "Ordnance Survey" },
    { source_id: "ons-boundaries", name: "ONS boundaries", publisher: "Office for National Statistics" },
  ],
};
/** The made-up source, as the line names it: what it is called, and who published it. */
const named = (fact: Fact) => `${fact.sources[0]?.name}, ${SOURCE.by} ${fact.sources[0]?.publisher}`;

describe("the source of a figure, written out", () => {
  test("test_the_line_names_the_source_links_to_it_and_gives_the_date", () => {
    render(<SourceLine facts={[cost]} />);

    const link = screen.getByRole("link", { name: cost.sources[0]?.name });

    expect(link).toHaveAttribute("href", `/sources#${cost.sources[0]?.source_id}`);
    expect(link.closest("p")).toHaveTextContent(
      `${SOURCE_LINE.source}: ${named(cost)}. ${SOURCE.dataFrom} August 2026. ${SOURCE.madeUp}`,
    );
  });

  test("test_a_publishers_own_statement_stands_under_the_figure_where_it_asks_to_see_it_there", () => {
    // Transport for London asks that its statement is shown wherever a figure made from its
    // data is. The API says which source asks, and brings the statement with the fact.
    const credited: Fact = {
      ...real,
      sources: [
        { source_id: "naptan", name: "NaPTAN", publisher: "Department for Transport", attribution: null },
        {
          source_id: "station-data",
          name: "Station data",
          publisher: "Transport for London",
          attribution: "Powered by TfL Open Data\nContains OS data © Crown copyright and database rights 2016",
        },
      ],
    };
    render(<SourceLine facts={[credited, { ...credited, fact_id: "another" }]} />);
    const line = screen.getAllByRole("link")[0]?.closest("p");

    // Each part of it is a sentence, and it is said once however many facts bring it.
    expect(line?.textContent?.split("Powered by TfL Open Data.")).toHaveLength(2);
    expect(line).toHaveTextContent(
      "Powered by TfL Open Data. Contains OS data © Crown copyright and database rights 2016.",
    );
    // A source that asks for no more than its name has no more than its name.
    expect(renderToStaticMarkup(<SourceLine facts={[real]} />)).not.toContain("Powered by");
  });

  test("test_a_statement_that_two_sources_of_one_publisher_bring_is_said_once", () => {
    // Seen in a browser: a figure made from two files of Transport for London, the bus stops
    // and the stations, each of which brings the publisher's statement. It stood twice, one
    // straight after the other.
    const statement = "Powered by TfL Open Data\nContains OS data © Crown copyright and database rights 2016";
    const twice: Fact = {
      ...real,
      sources: [
        { source_id: "bus-stops", name: "Bus stops", publisher: "Transport for London", attribution: statement },
        { source_id: "station-data", name: "Station data", publisher: "Transport for London", attribution: statement },
      ],
    };
    render(<SourceLine facts={[twice]} />);
    const line = screen.getAllByRole("link")[0]?.closest("p");

    expect(screen.getAllByRole("link").map((link) => link.textContent)).toEqual(["Bus stops", "Station data"]);
    expect(line?.textContent?.split("Powered by TfL Open Data.")).toHaveLength(2);
  });

  test("test_each_source_is_named_once_with_its_publisher_and_the_date_is_said_once_after_them", () => {
    // Seen in a browser: thirteen sources in one paragraph, some three times over, each
    // followed by the date of the figure, so that a census of 2021 read "Data from April 2026".
    const other: Fact = { ...real, fact_id: "another", as_of: "2026-04" };
    const third: Fact = { ...real, fact_id: "a-third", as_of: "2026-04", sources: real.sources.slice(0, 1) };
    render(<SourceLine facts={[real, other, third]} />);
    const line = screen.getAllByRole("link")[0]?.closest("p");

    expect(screen.getAllByRole("link").map((link) => link.textContent)).toEqual(["OS Open Greenspace", "ONS boundaries"]);
    expect(line).toHaveTextContent(
      `${SOURCE_LINE.source}: OS Open Greenspace, ${SOURCE.by} Ordnance Survey; ONS boundaries, ${SOURCE.by} Office for National Statistics. ${SOURCE.dataFrom} October 2024 to September 2026 and April 2026.`,
    );
    expect(line?.textContent?.split(SOURCE.dataFrom)).toHaveLength(2);
  });

  test("test_the_sources_of_a_vibe_are_said_to_be_what_its_recipe_is_made_from", () => {
    render(<SourceLine facts={[vibe]} />);

    // The words are the API's: a vibe is Burro's own recipe, and the sources are of its parts.
    expect(vibe.slots.made_from).toBe("Burro's recipe. Made from data published by:");
    expect(screen.getByRole("link").closest("p")).toHaveTextContent(
      `${vibe.slots.made_from} ${named(vibe)}. ${SOURCE.dataFrom} ${vibe.as_of}. ${SOURCE.madeUp}`,
    );
    expect(screen.getByRole("link").closest("p")?.textContent?.startsWith(SOURCE_LINE.source)).toBe(false);
  });

  test("test_a_vibe_beside_a_figure_is_given_as_any_source_is", () => {
    render(<SourceLine facts={[vibe, cost]} />);

    // What is said of a recipe is not said of a figure that is no recipe.
    expect(screen.getAllByRole("link")[0]?.closest("p")?.textContent?.startsWith(`${SOURCE_LINE.source}:`)).toBe(true);
  });

  test("test_made_up_data_is_said_to_be_made_up_and_real_data_is_not", () => {
    const { container, rerender } = render(<SourceLine facts={[cost]} />);
    expect(container).toHaveTextContent(SOURCE.madeUp);

    rerender(<SourceLine facts={[real]} />);

    expect(container).not.toHaveTextContent(SOURCE.madeUp);
  });

  test("test_every_source_of_a_fact_is_named_and_a_period_is_written_as_a_date_is", () => {
    render(<SourceLine facts={[real]} />);

    expect(screen.getAllByRole("link").map((link) => link.getAttribute("href"))).toEqual([
      "/sources#os-open-greenspace",
      "/sources#ons-boundaries",
    ]);
    expect(screen.getAllByText(/October 2024 to September 2026/)).toHaveLength(1);
  });

  test("test_the_date_is_not_broken_from_the_words_before_it", () => {
    // Seen on a phone: a line that broke before ". Data from December 2022."
    render(<SourceLine facts={[cost]} />);

    expect(screen.getByText(`${SOURCE.dataFrom} August 2026.`)).toHaveClass("dated");
  });

  test("test_facts_that_share_a_source_and_a_date_are_given_one_line", () => {
    render(<SourceLine facts={[cost, cost, { ...cost, fact_id: "another" }]} />);

    expect(screen.getAllByRole("link")).toHaveLength(1);
  });

  test("test_with_no_fact_there_is_no_line_and_no_source_is_made_up", () => {
    const { container } = render(<SourceLine facts={[]} />);

    expect(container).toBeEmptyDOMElement();
  });

  test("test_the_line_needs_no_script_and_no_button_to_be_read", () => {
    const html = renderToStaticMarkup(<SourceLine facts={[cost]} />);

    expect(html).toContain(`href="/sources#${cost.sources[0]?.source_id}"`);
    expect(html).toContain("August 2026");
    expect(html).not.toMatch(/<button|aria-expanded|hidden/);
  });

  test("test_the_link_takes_a_target_size_and_is_not_fetched_ahead_of_time", () => {
    render(<SourceLine facts={[cost]} />);

    expect(screen.getByRole("link")).toHaveClass("target-min");
    expect(screen.getByRole("link")).toHaveAttribute("data-prefetch", "false");
  });

  test("test_the_line_has_no_accessibility_fault", async () => {
    const { container } = render(<SourceLine facts={[cost, real]} />);

    expect(await faultsIn(container)).toEqual([]);
  });
});
