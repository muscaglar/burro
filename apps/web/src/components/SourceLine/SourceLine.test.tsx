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

/** A fact as a real release would hold it: two sources, and data that is not made up. */
const real: Fact = {
  ...feature,
  synthetic: false,
  as_of: "2024-10 to 2026-09",
  sources: [
    { source_id: "os-open-greenspace", name: "OS Open Greenspace" },
    { source_id: "ons-boundaries", name: "ONS boundaries" },
  ],
};

describe("the source of a figure, written out", () => {
  test("test_the_line_names_the_source_links_to_it_and_gives_the_date", () => {
    render(<SourceLine facts={[cost]} />);

    const link = screen.getByRole("link", { name: cost.sources[0]?.name });

    expect(link).toHaveAttribute("href", `/sources#${cost.sources[0]?.source_id}`);
    expect(link.closest("p")).toHaveTextContent(
      `${SOURCE_LINE.source}: ${cost.sources[0]?.name}. ${SOURCE.dataFrom} August 2026. ${SOURCE.madeUp}`,
    );
  });

  test("test_made_up_data_is_said_to_be_made_up_and_real_data_is_not", () => {
    const { container, rerender } = render(<SourceLine facts={[cost]} />);
    expect(container).toHaveTextContent(SOURCE.madeUp);

    rerender(<SourceLine facts={[real]} />);

    expect(container).not.toHaveTextContent(SOURCE.madeUp);
  });

  test("test_every_source_of_a_fact_is_named_and_a_period_is_left_as_the_release_wrote_it", () => {
    render(<SourceLine facts={[real]} />);

    expect(screen.getAllByRole("link").map((link) => link.getAttribute("href"))).toEqual([
      "/sources#os-open-greenspace",
      "/sources#ons-boundaries",
    ]);
    expect(screen.getAllByText(/2024-10 to 2026-09/)).toHaveLength(2);
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
