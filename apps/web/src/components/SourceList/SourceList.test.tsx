import { render, screen, within } from "@testing-library/react";

import { SOURCES } from "@/content/sources";
import { recordedAnswer } from "@/lib/api/recorded";
import type { Source } from "@/lib/api/schema";

import { faultsIn } from "../../../test/support/axe";
import { SourceList } from "./SourceList";

const meta = recordedAnswer("get_meta", "meta").body.data;
const synthetic = meta.attributions[0]!;

const greenspace: Source = {
  source_id: "open-greenspace",
  name: "Open Greenspace",
  publisher: "A mapping agency",
  licence: "An open licence, version 3",
  attribution: "Contains data from a mapping agency.",
  url: "https://publisher.example/greenspace",
  retrieved_on: "2026-08-01",
  credit_beside_figures: false,
};

function entryFor(source: Source) {
  return within(screen.getByRole("article", { name: source.name }));
}

describe("the data sources page", () => {
  test("test_every_source_is_listed_with_its_licence_and_credit_as_the_api_sent_them", () => {
    render(<SourceList sources={[synthetic, greenspace]} features={meta.features} />);

    for (const source of [synthetic, greenspace]) {
      const entry = entryFor(source);
      expect(entry.getByRole("heading", { level: 2, name: source.name })).toBeInTheDocument();
      expect(entry.getByText(source.attribution)).toBeInTheDocument();
      expect(entry.getByText(source.publisher)).toBeInTheDocument();
      expect(entry.getByText(source.licence)).toBeInTheDocument();
    }
    expect(screen.getAllByRole("article")).toHaveLength(2);
  });

  test("test_what_is_said_with_a_credit_stands_under_it_and_under_no_other", () => {
    // The terms of a publisher may ask that something is said wherever its credit is shown.
    // The API brings it with the source, and the credit stays as the publisher worded it.
    const said = "The publisher cannot warrant the quality or accuracy of the data.";
    const outlines: Source = { ...greenspace, source_id: "outlines", name: "Outlines", said_with_attribution: said };
    render(<SourceList sources={[synthetic, greenspace, outlines]} features={[]} />);

    const credit = entryFor(outlines).getByText(outlines.attribution);
    expect(credit.nextElementSibling).toHaveTextContent(said);
    expect(entryFor(outlines).getAllByText(said)).toHaveLength(1);
    for (const source of [synthetic, greenspace]) {
      expect(entryFor(source).queryByText(said)).toBeNull();
      expect(entryFor(source).getByText(source.attribution).nextElementSibling?.tagName).toBe("DL");
    }
  });

  test("test_every_source_is_anchored_by_its_id_so_a_figure_can_link_to_it", () => {
    const { container } = render(
      <SourceList sources={[synthetic, greenspace]} features={meta.features} />,
    );

    expect(container.querySelector("#synthetic")).toBe(screen.getByRole("article", { name: synthetic.name }));
    expect(container.querySelector("#open-greenspace")).toBe(
      screen.getByRole("article", { name: greenspace.name }),
    );
  });

  test("test_the_date_a_source_was_retrieved_is_written_out_and_kept_for_a_machine", () => {
    render(<SourceList sources={[greenspace]} features={[]} />);

    const date = entryFor(greenspace).getByText("1 August 2026");

    expect(date.tagName).toBe("TIME");
    expect(date).toHaveAttribute("datetime", "2026-08-01");
  });

  test("test_a_source_lists_the_features_that_came_from_it_and_no_others", () => {
    const [first, second, third] = meta.features;
    const features = [
      { ...first!, source_ids: ["open-greenspace"] },
      { ...second!, source_ids: ["synthetic", "open-greenspace"] },
      { ...third!, source_ids: ["synthetic"] },
    ];
    render(<SourceList sources={[synthetic, greenspace]} features={features} />);

    const listed = (source: Source) =>
      entryFor(source)
        .getAllByRole("listitem")
        .map((item) => item.textContent);

    expect(listed(greenspace)).toEqual([first!.label, second!.label]);
    expect(listed(synthetic)).toEqual([second!.label, third!.label]);
  });

  test("test_a_credit_with_a_gap_left_in_it_says_that_it_is_not_finished", () => {
    // Seen in a browser: "Contains OS data © Crown copyright and database right [year]."
    // The gap is the registry's, and which year fills it is not the website's to say.
    const first = greenspace;
    const gap = { ...first, source_id: "with-a-gap", attribution: "Contains data © Crown copyright [year]." };
    const other = { ...first, source_id: "another-gap", attribution: "Contains data © 20nn" };
    render(<SourceList sources={[first, gap, other]} features={[]} />);

    const notes = screen.getAllByText(SOURCES.unfinished);
    expect(notes).toHaveLength(2);
    expect(document.getElementById("with-a-gap")).toContainElement(notes[0] as HTMLElement);
    // The credit is shown as the API sent it. Nothing is written into the gap.
    expect(document.getElementById("with-a-gap")).toHaveTextContent("Contains data © Crown copyright [year].");
    expect(document.getElementById(first.source_id)?.textContent?.includes(SOURCES.unfinished)).toBe(false);
  });

  test("test_a_source_no_feature_names_says_so", () => {
    render(<SourceList sources={[greenspace]} features={meta.features} />);

    expect(entryFor(greenspace).getByText(SOURCES.notUsed)).toBeInTheDocument();
  });

  test("test_a_publishers_page_is_linked_and_is_told_nothing_of_where_the_person_came_from", () => {
    render(<SourceList sources={[greenspace]} features={[]} />);

    const link = entryFor(greenspace).getByRole("link");

    expect(link).toHaveAttribute("href", "https://publisher.example/greenspace");
    expect(link.getAttribute("rel")?.split(" ")).toEqual(expect.arrayContaining(["noreferrer"]));
    expect(link).not.toHaveAttribute("target");
  });

  test("test_a_source_with_no_address_has_no_link", () => {
    render(<SourceList sources={[synthetic]} features={meta.features} />);

    expect(synthetic.url).toBe("");
    expect(entryFor(synthetic).queryByRole("link")).toBeNull();
    expect(entryFor(synthetic).getByText(SOURCES.noLink)).toBeInTheDocument();
  });

  test.each(["javascript:alert(1)", "data:text/html,<script>1</script>", "//no-scheme.example", "not an address"])(
    "test_an_address_that_is_not_a_web_address_is_never_made_a_link: %s",
    (url) => {
      render(<SourceList sources={[{ ...greenspace, url }]} features={[]} />);

      expect(entryFor(greenspace).queryByRole("link")).toBeNull();
      expect(entryFor(greenspace).getByText(url)).toBeInTheDocument();
    },
  );

  test("test_a_release_that_names_no_source_says_so", () => {
    render(<SourceList sources={[]} features={[]} />);

    expect(screen.getByText(SOURCES.none)).toBeInTheDocument();
  });

  test("test_the_sources_have_no_accessibility_fault", async () => {
    const { container } = render(
      <main>
        <h1>{SOURCES.title}</h1>
        <SourceList sources={[synthetic, greenspace]} features={meta.features} />
      </main>,
    );

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });
});
