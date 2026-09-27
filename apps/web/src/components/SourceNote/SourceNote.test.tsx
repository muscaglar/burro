import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { SOURCE } from "@/content/search";
import { readRecorded, recordedAnswer, recordedFolder } from "@/lib/api/recorded";
import type { AreaData, ExplanationsData, Fact } from "@/lib/api/schema";

import { rulesOf } from "../../../test/support/css";
import { linesOf, SourceNote } from "./SourceNote";

const farrowmere = recordedAnswer("get_area", "area/farrowmere").body.data;

/** Every fact of every recording: each area's profile, and each search's reasons. */
function everyFact(): Fact[] {
  const facts: Fact[] = [];
  for (const file of readdirSync(path.join(recordedFolder(), "area"))) {
    facts.push(...(readRecorded(`area/${file.replace(/\.json$/, "")}`).body as { data: AreaData }).data.facts);
  }
  for (const file of readdirSync(recordedFolder())) {
    if (!file.startsWith("explanations-")) continue;
    facts.push(...(readRecorded(file.replace(/\.json$/, "")).body as { data: ExplanationsData }).data.facts);
  }
  return facts;
}

const all = everyFact();

describe("the source of a figure", () => {
  test("test_every_recorded_fact_has_a_source_and_a_date_to_show", () => {
    for (const fact of all) {
      const lines = linesOf([fact]);
      expect(lines.length).toBeGreaterThan(0);
      for (const line of lines) {
        expect(line.name).not.toBe("");
        expect(line.asOf).not.toBe("");
      }
    }
  });

  test("test_it_opens_to_the_source_the_date_and_that_the_data_is_made_up", async () => {
    const fact = farrowmere.facts.find((one) => one.kind === "feature");
    if (!fact) throw new Error("no recorded feature");
    render(<SourceNote facts={[fact]} of="this figure" />);
    const button = screen.getByRole("button", { name: SOURCE.buttonFor("this figure") });

    expect(button).toHaveAttribute("aria-expanded", "false");
    await userEvent.setup({ delay: null }).click(button);

    expect(screen.getByRole("link", { name: "Synthetic test data" })).toHaveAttribute("href", "/sources#synthetic");
    expect(screen.getByText(`${SOURCE.dataFrom} ${fact.as_of}`)).toBeInTheDocument();
    expect(screen.getByText(SOURCE.madeUp)).toBeInTheDocument();
  });

  test("test_a_publishers_own_statement_is_shown_with_its_source_where_it_asks_to_see_it_there", async () => {
    // Transport for London asks that its statement is shown wherever a figure made from its
    // data is. The API says which source asks, and brings the statement with the fact.
    const fact: Fact = {
      ...(farrowmere.facts[0] as Fact),
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
    render(<SourceNote facts={[fact]} />);

    await userEvent.setup({ delay: null }).click(screen.getByRole("button", { name: SOURCE.button }));

    const credited = screen.getByRole("link", { name: "Station data" }).closest("li");
    expect(credited).toHaveTextContent(
      "Powered by TfL Open Data. Contains OS data © Crown copyright and database rights 2016.",
    );
    // A source that asks for no more than its name has no more than its name and its publisher.
    const plain = screen.getByRole("link", { name: "NaPTAN" }).closest("li");
    expect(plain?.textContent).toBe(`NaPTAN${SOURCE.by} Department for Transport`);
  });

  test("test_data_that_is_not_made_up_is_not_said_to_be", async () => {
    const fact = { ...(farrowmere.facts[0] as Fact), synthetic: false };
    render(<SourceNote facts={[fact]} />);

    await userEvent.setup({ delay: null }).click(screen.getByRole("button", { name: SOURCE.button }));

    expect(screen.queryByText(SOURCE.madeUp)).toBeNull();
  });

  test("test_a_fact_built_from_several_sources_names_each", async () => {
    const fact: Fact = {
      ...(farrowmere.facts[0] as Fact),
      sources: [
        { source_id: "one-source", name: "One source", publisher: "One publisher" },
        { source_id: "another-source", name: "Another source", publisher: "Another publisher" },
      ],
    };
    render(<SourceNote facts={[fact, fact]} />);

    await userEvent.setup({ delay: null }).click(screen.getByRole("button", { name: SOURCE.button }));

    expect(screen.getAllByRole("link").map((link) => link.getAttribute("href"))).toEqual([
      "/sources#one-source",
      "/sources#another-source",
    ]);
    // Who published each is said beside it, and the date is said once, after them both.
    expect(screen.getByText(`${SOURCE.by} One publisher`)).toBeInTheDocument();
    expect(screen.getByText(`${SOURCE.by} Another publisher`)).toBeInTheDocument();
    expect(screen.getAllByText(new RegExp(`^${SOURCE.dataFrom} `))).toHaveLength(1);
  });

  test("test_the_source_of_a_vibe_says_in_the_apis_words_whose_recipe_it_is_and_that_it_is_a_judgement", async () => {
    // A sentence about a vibe is short on a result. What it leaves out is said here, with its source.
    const explained = recordedAnswer("explain_top", "explanations-first").body.data;
    const sentence = explained.explanations.flatMap((one) => one.reasons).find((one) => one.fact_ids[0]?.includes("/tag/"));
    const vibe = explained.facts.find((fact) => fact.fact_id === sentence?.fact_ids[0]);
    if (!sentence || !vibe) throw new Error("no recorded reason is a vibe");
    render(<SourceNote facts={[vibe]} of="a vibe" />);

    await userEvent.setup({ delay: null }).click(screen.getByRole("button", { name: SOURCE.buttonFor("a vibe") }));

    expect(sentence.text.includes("judgement")).toBe(false);
    expect(vibe.slots.judgement).toBe(
      "Burro chose which measurements go into this vibe and how much each of them counts. That choice is a judgement, and not a fact about the place.",
    );
    expect(screen.getByText(vibe.slots.judgement ?? "none")).toBeInTheDocument();
    expect(screen.getByText(vibe.slots.made_from ?? "none")).toBeInTheDocument();
    // The date of its parts is the date of the fact, and is given as any date is.
    expect(vibe.as_of).toBe(vibe.slots.span);
    expect(screen.getByText(`${SOURCE.dataFrom} ${vibe.as_of}`)).toBeInTheDocument();
  });

  test("test_where_the_line_about_judgement_stands_beside_the_button_it_is_not_said_again", async () => {
    const vibe = farrowmere.facts.find((one) => one.kind === "tag" && one.slots.judgement !== undefined);
    if (!vibe) throw new Error("no recorded vibe");
    const { container } = render(<SourceNote facts={[vibe]} judgementSaid />);

    await userEvent.setup({ delay: null }).click(screen.getByRole("button", { name: SOURCE.button }));

    expect(container.textContent?.includes(vibe.slots.judgement ?? "none")).toBe(false);
    expect(screen.getByText(vibe.slots.made_from ?? "none")).toBeInTheDocument();
  });

  test("test_the_source_of_a_figure_that_is_no_vibe_says_nothing_of_a_recipe", async () => {
    const fact = farrowmere.facts.find((one) => one.kind === "feature");
    if (!fact) throw new Error("no recorded feature");
    const { container } = render(<SourceNote facts={[fact]} />);

    await userEvent.setup({ delay: null }).click(screen.getByRole("button", { name: SOURCE.button }));

    expect(container.textContent?.includes("recipe")).toBe(false);
    expect(container.textContent?.includes("judgement")).toBe(false);
  });

  test("test_with_no_fact_in_hand_it_is_a_link_to_the_sources_page", () => {
    render(<SourceNote facts={[]} of="the journey" />);

    expect(screen.getByRole("link", { name: SOURCE.buttonFor("the journey") })).toHaveAttribute("href", "/sources");
    expect(screen.queryByRole("button")).toBeNull();
  });

  test("test_no_link_to_a_source_is_fetched_ahead_of_time", async () => {
    const fact = farrowmere.facts[0] as Fact;
    const { unmount } = render(<SourceNote facts={[fact]} />);
    await userEvent.click(screen.getByRole("button", { name: SOURCE.button }));

    // Fetched ahead, it would tell the website's own server that a source was opened.
    expect(screen.getAllByRole("link").map((link) => link.getAttribute("data-prefetch"))).toEqual(
      screen.getAllByRole("link").map(() => "false"),
    );
    unmount();

    render(<SourceNote facts={[]} of="the journey" />);
    expect(screen.getByRole("link")).toHaveAttribute("data-prefetch", "false");
  });

  test("test_the_source_is_drawn_with_the_key_whether_it_opens_in_place_or_leads_to_the_page_of_sources", async () => {
    const fact = farrowmere.facts[0] as Fact;
    const keyOf = (control: HTMLElement) => control.querySelector<HTMLElement>("span[aria-hidden='true']");
    const { unmount } = render(<SourceNote facts={[fact]} of="the journey" />);
    const opens = screen.getByRole("button", { name: SOURCE.buttonFor("the journey") });

    // The key is a drawing, kept from a screen reader: the word beside it is what is read.
    expect(keyOf(opens)?.style.getPropertyValue("--art")).toBe('url("/art/ui-key.png")');
    expect(opens).toHaveTextContent(SOURCE.button);
    expect(opens).toHaveAttribute("aria-expanded", "false");
    // It is small in a line of text, and is never smaller than a small control may be.
    expect(opens.classList.contains("target-min")).toBe(true);
    await userEvent.setup({ delay: null }).click(opens);
    expect(opens).toHaveAttribute("aria-expanded", "true");
    expect(document.getElementById(opens.getAttribute("aria-controls") ?? "")).toHaveTextContent(SOURCE.madeUp);
    unmount();

    render(<SourceNote facts={[]} of="the journey" />);
    const leads = screen.getByRole("link", { name: SOURCE.buttonFor("the journey") });
    expect(keyOf(leads)?.style.getPropertyValue("--art")).toBe('url("/art/ui-key.png")');
    expect(leads).toHaveTextContent(SOURCE.button);
    expect(leads.classList.contains("target-min")).toBe(true);
  });

  test("test_every_word_of_a_source_that_is_open_is_ink_because_it_stands_on_sand", () => {
    // On sand only ink is read: the colour of a link, and the colour of what is said quietly, are not.
    const rules = rulesOf(readFileSync(path.join(__dirname, "SourceNote.module.css"), "utf8")).filter(
      (rule) => !/forced-colors/.test(rule.under ?? ""),
    );
    const colours = rules.filter((rule) => rule.sets.has("color")).map((rule) => [rule.selector, rule.sets.get("color")]);

    expect(colours).toEqual([
      [".toSources", "var(--ink)"],
      [".said", "var(--ink)"],
      [".lines", "var(--ink)"],
      [".link", "var(--ink)"],
      // That the data is made up is a notice, on cream of its own.
      [".lines .madeUp", "var(--notice-text)"],
    ]);
    expect(rules.find((rule) => rule.selector === ".lines .madeUp")?.sets.get("background")).toBe("var(--notice-bg)");
    // A name that leads to its entry is told to be a link by its line and its weight.
    const link = rules.find((rule) => rule.selector === ".link")?.sets;
    expect([link?.get("font-weight"), link?.has("text-decoration")]).toEqual(["700", false]);
    // In hand, the key that is a link changes its ground and nothing else: nothing moves.
    const inHand = rules.filter((rule) => /:(hover|focus-visible|active)/.test(rule.selector));
    expect(inHand.map((rule) => [rule.selector, [...rule.sets.keys()]])).toEqual([
      [".toSources:hover", ["background-color"]],
      [".toSources:focus-visible", ["background-color"]],
    ]);
  });
});
