import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen, within } from "@testing-library/react";
import { renderToStaticMarkup } from "react-dom/server";

import { SOURCES } from "@/content/sources";
import { recordedAnswer } from "@/lib/api/recorded";
import type { Source } from "@/lib/api/schema";

import { faultsIn } from "../../../test/support/axe";
import { rulesOf } from "../../../test/support/css";
import { onTheGrass } from "../About/grass";
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

/** True of what stands in sight as the page is built: in no fold, and kept from nobody. */
const inSight = (element: Element | null) =>
  element !== null && element.closest("details, [hidden], .visually-hidden, [aria-hidden='true']") === null;
/** What a fold of a source holds, which is one press away. */
const foldOf = (source: Source) => document.getElementById(source.source_id)?.querySelector("details") as HTMLElement;

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

  test("test_who_published_it_under_which_licence_and_its_link_stand_in_sight_with_its_credit", () => {
    // The licences of the data ask for the credit. None of it is behind a press.
    const said = "The publisher cannot warrant the quality or accuracy of the data.";
    const outlines: Source = { ...greenspace, said_with_attribution: said };
    render(<SourceList sources={[outlines]} features={meta.features} />);
    const entry = entryFor(outlines);

    for (const words of [outlines.attribution, said, outlines.publisher, outlines.licence]) {
      expect([words, inSight(entry.getByText(words))]).toEqual([words, true]);
    }
    expect(inSight(entry.getByRole("link", { name: outlines.url }))).toBe(true);
    for (const name of [SOURCES.rows.publisher, SOURCES.rows.licence, SOURCES.rows.link]) {
      expect([name, inSight(entry.getByText(name))]).toEqual([name, true]);
    }
  });

  test("test_what_else_is_said_of_a_source_is_one_fold_that_is_closed_and_named_for_what_a_person_would_ask", () => {
    const [first, second] = meta.features;
    const features = [
      { ...first!, source_ids: ["open-greenspace"] },
      { ...second!, source_ids: ["open-greenspace"] },
    ];
    render(<SourceList sources={[greenspace]} features={features} />);
    const fold = foldOf(greenspace) as HTMLDetailsElement;

    expect(document.getElementById(greenspace.source_id)?.querySelectorAll("details")).toHaveLength(1);
    expect(fold.open).toBe(false);
    // It says of which source it is, to whoever hears the page: every source has one.
    expect(fold.querySelector("summary")?.textContent).toBe(`${SOURCES.more}: ${greenspace.name}`);
    expect(fold.querySelector("summary .visually-hidden")?.textContent).toBe(`: ${greenspace.name}`);
    // When Burro took its copy, and what it uses the source for.
    expect(within(fold).getByText("1 August 2026").tagName).toBe("TIME");
    expect(within(fold).getAllByRole("listitem").map((item) => item.textContent)).toEqual([first!.label, second!.label]);
    // Nothing of it is lost, and nothing of it is said twice.
    expect(document.body.textContent?.split(first!.label)).toHaveLength(2);
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
    // What a link leads to is in sight when it is reached: a source stands in no fold.
    for (const entry of screen.getAllByRole("article")) expect(entry.closest("details")).toBeNull();
  });

  test("test_the_date_burro_took_its_copy_of_a_source_is_written_out_and_kept_for_a_machine", () => {
    render(<SourceList sources={[greenspace]} features={[]} />);

    const date = entryFor(greenspace).getByText("1 August 2026");

    expect(date.tagName).toBe("TIME");
    expect(date).toHaveAttribute("datetime", "2026-08-01");
    // It is said in a sentence, which the date ends.
    expect(date.parentElement?.textContent).toBe(`${SOURCES.copied.before} 1 August 2026${SOURCES.copied.after}`);
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
      within(foldOf(source))
        .getAllByRole("listitem")
        .map((item) => item.textContent);

    expect(listed(greenspace)).toEqual([first!.label, second!.label]);
    expect(listed(synthetic)).toEqual([second!.label, third!.label]);
    expect(foldOf(greenspace).textContent?.includes(SOURCES.usedFor)).toBe(true);
  });

  test("test_a_credit_with_a_gap_left_in_it_says_in_sight_that_it_is_not_finished", () => {
    // Seen in a browser: "Contains OS data © Crown copyright and database right [year]."
    // The gap is the registry's, and which year fills it is not the website's to say.
    const first = greenspace;
    const gap = { ...first, source_id: "with-a-gap", attribution: "Contains data © Crown copyright [year]." };
    const other = { ...first, source_id: "another-gap", attribution: "Contains data © 20nn" };
    render(<SourceList sources={[first, gap, other]} features={[]} />);

    const notes = screen.getAllByText(SOURCES.unfinished);
    expect(notes).toHaveLength(2);
    expect(document.getElementById("with-a-gap")).toContainElement(notes[0] as HTMLElement);
    for (const note of notes) expect(inSight(note)).toBe(true);
    // The credit is shown as the API sent it. Nothing is written into the gap.
    expect(document.getElementById("with-a-gap")).toHaveTextContent("Contains data © Crown copyright [year].");
    expect(document.getElementById(first.source_id)?.textContent?.includes(SOURCES.unfinished)).toBe(false);
  });

  test("test_a_source_no_feature_names_says_so", () => {
    render(<SourceList sources={[greenspace]} features={meta.features} />);

    expect(entryFor(greenspace).getByText(SOURCES.notUsed)).toBeInTheDocument();
    expect(entryFor(greenspace).queryByText(SOURCES.usedFor)).toBeNull();
  });

  test("test_a_publishers_page_is_linked_and_is_told_nothing_of_where_the_person_came_from", () => {
    render(<SourceList sources={[greenspace]} features={[]} />);

    const link = entryFor(greenspace).getByRole("link");

    expect(link).toHaveAttribute("href", "https://publisher.example/greenspace");
    expect(link.getAttribute("rel")?.split(" ")).toEqual(expect.arrayContaining(["noreferrer"]));
    expect(link).not.toHaveAttribute("target");
  });

  test("test_a_source_with_no_address_has_no_link_and_says_so_in_words", () => {
    render(<SourceList sources={[synthetic]} features={meta.features} />);

    expect(synthetic.url).toBe("");
    expect(entryFor(synthetic).queryByRole("link")).toBeNull();
    expect(entryFor(synthetic).getByText(SOURCES.noLink)).toBeInTheDocument();
    // Not "None", which reads as the name of a page.
    expect(SOURCES.noLink.split(" ").length).toBeGreaterThan(3);
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

  test("test_the_page_reads_with_scripts_off_and_what_opens_is_the_browsers_own", () => {
    const markup = renderToStaticMarkup(<SourceList sources={[synthetic, greenspace]} features={meta.features} />);

    expect(markup).not.toMatch(/<button|aria-expanded|onclick/i);
    expect(markup).not.toMatch(/<details[^>]* open/);
    expect(markup).toContain(greenspace.attribution);
  });
});

describe("the sources, in the look", () => {
  const SHEET = rulesOf(readFileSync(path.resolve(__dirname, "SourceList.module.css"), "utf8"));
  const written = readFileSync(path.resolve(__dirname, "SourceList.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");

  test("test_the_sources_are_one_list_in_one_box_with_the_key_of_a_source_before_each_name", () => {
    const { container } = render(<SourceList sources={[synthetic, greenspace]} features={meta.features} />);
    const box = container.firstElementChild as HTMLElement;
    const list = box.querySelector("ul") as HTMLElement;

    // A list of many small things stands in one box: a box with a shadow round each would be noise.
    expect([box.tagName, box.getAttribute("data-kind")]).toEqual(["DIV", "box"]);
    expect(container.querySelectorAll("[data-kind]")).toHaveLength(1);
    expect([...list.children].map((entry) => [entry.tagName, entry.firstElementChild?.tagName])).toEqual([
      ["LI", "ARTICLE"],
      ["LI", "ARTICLE"],
    ]);
    expect(onTheGrass(container)).toEqual([]);
    // The key is handed to the style sheet by name, and is no element: a name is heard as it was.
    expect(list.style.getPropertyValue("--key")).toBe('url("/art/ui-key.png")');
    expect(container.querySelectorAll("img, svg, [role='img']").length).toBe(0);
    // All that is kept from whoever hears the page is the arrow of the bar of each fold, which says nothing.
    const kept = [...container.querySelectorAll("[aria-hidden]")];
    expect(kept.map((one) => [one.parentElement?.tagName, one.textContent])).toEqual([
      ["SUMMARY", ""],
      ["SUMMARY", ""],
    ]);
    expect(kept.filter((one) => one.closest("h2") !== null)).toEqual([]);
    expect(screen.getByRole("heading", { level: 2, name: greenspace.name }).textContent).toBe(greenspace.name);
  });

  test("test_no_edge_is_dashed_and_one_source_is_parted_from_the_next_by_a_rule_of_sand", () => {
    // The founder: "The dashed border is not understood to a user, please make solid".
    expect(/dashed|dotted/.test(written)).toBe(false);
    const rule = SHEET.find((one) => one.selector === ".source + .source" && one.under === null);
    expect(rule?.sets.get("border-block-start")).toBe("var(--edge) solid var(--sand)");
    for (const one of SHEET.filter((found) => [...found.sets.keys()].some((property) => /^border/.test(property)))) {
      for (const [property, value] of one.sets) {
        if (/^border/.test(property) && /\b(solid|dashed|dotted|double)\b/.test(value)) {
          expect([one.selector, property, /\bsolid\b/.test(value)]).toEqual([one.selector, property, true]);
        }
      }
    }
  });

  test("test_a_credit_is_read_at_the_size_of_a_sentence_that_leads_and_nothing_of_a_source_is_dimmed", () => {
    const credit = SHEET.find((one) => one.selector === ".attribution" && one.under === null);

    expect(credit?.sets.get("font-size")).toBe("var(--size-lead)");
    expect(SHEET.filter((one) => [...one.sets.keys()].some((property) => /^(opacity|filter)$/.test(property)))).toEqual([]);
  });

  test("test_a_release_that_names_no_source_says_so_in_a_slip_of_cream", () => {
    render(<SourceList sources={[]} features={[]} />);

    expect(screen.getByText(SOURCES.none)).toHaveAttribute("data-kind", "plain");
    expect(screen.getByText(SOURCES.none).tagName).toBe("P");
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
