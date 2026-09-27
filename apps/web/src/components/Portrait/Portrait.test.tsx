import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { render, screen, within } from "@testing-library/react";
import { renderToStaticMarkup } from "react-dom/server";

import { PORTRAIT } from "@/content/area";
import { BAND_ONE_WAY, RESTS_ON } from "@/content/bands";
import { CRIME_ACCOUNT, CRIME_RULE } from "@/content/crime";
import { CANNOT_PLACE, FACT_COLUMNS } from "@/content/facts";
import { KNOWN } from "@/content/kit";
import { READING } from "@/content/labels";
import { SOURCE, STRIP } from "@/content/search";
import { CRIME_CAVEAT } from "@/content/settings";
import { readRecorded, recordedAnswer, recordedFolder } from "@/lib/api/recorded";
import type { AreaData, MetaData } from "@/lib/api/schema";
import { GROUPS, inShort, portraitOf, restsOn, shownOn, type Group, type MarkRow } from "@/lib/area/portrait";
import { readableDate } from "@/lib/format";
import { inWords, isRange, plainly } from "@/lib/vibes";

import { faultsIn } from "../../../test/support/axe";
import { rulesOf } from "../../../test/support/css";
import { ROUGH, sayingSo } from "../../../test/support/rough";
import { NO_PICTURE, picturesAtEnds } from "../kit/Ends/picture";
import { LISTS_STAND, THINGS_STAND } from "./look";
import { Portrait } from "./Portrait";

const meta: MetaData = recordedAnswer("get_meta", "meta").body.data;
const profile = (slug: string): AreaData => recordedAnswer("get_area", `area/${slug}`).body.data;
const SLUGS = readdirSync(path.join(recordedFolder(), "area")).map((file) => file.replace(/\.json$/, ""));

/** The release where gritty is built as one part of a place, and runs one way. */
const variantA: MetaData = (readRecorded("variant-a/meta").body as { data: MetaData }).data;

/**
 * A profile whose facts say nothing of what a band rests on but the two counts, as every
 * fact did before the engine gave the clause. It holds whatever the answers are recorded from.
 */
const withNoClause = (data: AreaData): AreaData => ({
  ...data,
  facts: data.facts.map((fact) => ({
    ...fact,
    slots: Object.fromEntries(Object.entries(fact.slots).filter(([slot]) => slot !== "share" && slot !== "partly")),
  })),
});

function show(slug: string, given: MetaData = meta) {
  const data = profile(slug);
  const view = render(<Portrait data={data} meta={given} />);
  return { data, portrait: portraitOf(data, given), ...view };
}

/** The list a heading stands over, with its vibes. */
const list = (group: Group) => screen.queryByRole("group", { name: PORTRAIT.groups[group] });
/** Every vibe the area is placed on: each is one line, which opens what it is made of. */
const vibes = () => [...document.querySelectorAll<HTMLDetailsElement>("details[data-vibe]")];
const lines = () => vibes().map((part) => part.querySelector("summary") as HTMLElement);
/** The part of the page that one vibe is: the line that names it, and what the line opens. */
function vibe(label: string): HTMLDetailsElement {
  const found = vibes().find((part) => part.querySelector("summary > span")?.textContent === label);
  if (!found) throw new Error("The portrait holds no such vibe.");
  return found;
}
const line = (label: string) => vibe(label).querySelector("summary") as HTMLElement;
/** What the area is like, in short: the part the portrait opens with. */
const short = () => screen.getByRole("group", { name: PORTRAIT.short.title });
/**
 * The picture of a line: the two ends and the five steps between them, which is kept whole
 * from a screen reader. The small drawing of the vibe, before its name, is no part of it.
 */
const pictureIn = (one: HTMLElement | null | undefined) =>
  one?.querySelector("[data-on]")?.closest("summary > [aria-hidden='true']") ?? null;
/** Which of the five cells of a line are filled, from the low end to the high end. */
const filled = (label: string) =>
  [...line(label).querySelectorAll("[data-on]")].map((cell) => cell.getAttribute("data-on") === "true");

describe("where an area sits on each vibe", () => {
  test("test_the_lists_stand_under_their_headings_in_the_order_of_the_portrait", () => {
    const { portrait } = show("foxholt");

    const headings = screen.getAllByRole("heading", { level: 3 }).map((heading) => heading.textContent);

    expect(screen.getByRole("heading", { level: 2 })).toHaveTextContent(PORTRAIT.title);
    // What it is like in short comes first, and then every vibe under the heading of its list.
    expect(headings).toEqual([
      PORTRAIT.short.title,
      PORTRAIT.groups.scales,
      PORTRAIT.groups.more,
      PORTRAIT.groups.less,
      PORTRAIT.groups.others,
    ]);
    for (const group of GROUPS) {
      const drawn =
        list(group) === null ? [] : [...(list(group) as HTMLElement).querySelectorAll("details[data-vibe] > summary > span:first-child")];
      expect(drawn.map((name) => name.textContent)).toEqual(portrait[group].map((mark) => mark.tag.label));
    }
  });

  test("test_a_list_that_holds_no_vibe_has_no_heading", () => {
    show("brackenhythe");

    expect(profile("brackenhythe").portrait.less).toEqual([]);
    expect(list("less")).toBeNull();
    expect(list("unplaced")).toBeNull();
    expect(list("more")).not.toBeNull();
  });

  test.each(SLUGS)("test_every_vibe_is_said_as_a_band_in_words_and_drawn_as_a_mark_on_a_line: %s", (slug) => {
    const { portrait } = show(slug);

    for (const mark of shownOn(portrait)) {
      const { placed, tag } = mark;
      if (placed === null) throw new Error("A vibe that is shown has no band.");
      const words =
        placed.spread_high - placed.spread_low >= 2
          ? STRIP.bands(placed.spread_low, placed.spread_high)
          : STRIP.band(placed.band);
      // In words, which a screen reader hears and a person reads.
      expect(line(tag.label).textContent?.includes(words)).toBe(true);
      expect(line(tag.label).textContent?.includes(STRIP.from(tag.low_end ?? STRIP.least, tag.high_end ?? STRIP.most))).toBe(true);
      // As a mark on a line of five, between the names of its two ends.
      const cells = filled(tag.label);
      expect(cells).toHaveLength(5);
      expect(cells.map((on, at) => (on ? at + 1 : 0)).filter(Boolean)).toEqual(
        placed.spread_high - placed.spread_low >= 2
          ? [1, 2, 3, 4, 5].filter((band) => band >= placed.spread_low && band <= placed.spread_high)
          : [placed.band],
      );
      const picture = pictureIn(line(tag.label));
      expect(picture?.textContent).toBe(`${tag.low_end ?? STRIP.least}${tag.high_end ?? STRIP.most}`);
    }
  });

  test.each(SLUGS)("test_no_vibe_is_shown_as_a_percentage_a_score_or_a_rank: %s", (slug) => {
    const { data, portrait } = show(slug);

    // The figure beside a vibe is of one part of it, under that part's own name, and may be
    // a share of land or of homes. It is taken out here: what is left is what is said of the vibe.
    const figures = GROUPS.flatMap((group) => portrait[group]).flatMap((mark) =>
      mark.pictured === null ? [] : [`${mark.pictured.label}: ${mark.pictured.slots.value}`],
    );
    const said = lines().map((one) => figures.reduce((text, figure) => text.replace(figure, ""), one.textContent ?? ""));
    const scores = data.tags
      .flatMap((tag) => [tag.raw, tag.score, tag.coverage])
      .filter((value): value is number => value !== null && !Number.isInteger(value))
      .map(String);

    expect(said.length).toBe(shownOn(portrait).length);
    expect(said.filter((text) => /%|percent|score|rank/i.test(text))).toEqual([]);
    // What a vibe is ranked on is served with the profile, and is in no line of the portrait.
    expect(scores.filter((value) => said.some((text) => text.includes(value)))).toEqual([]);
    // Nor is it in what the area is like in short, which says a band in words.
    const inShortSaid = figures.reduce((text, figure) => text.replace(figure, ""), short().textContent ?? "");
    expect(/%|percent|score|rank/i.test(inShortSaid)).toBe(false);
    expect(scores.filter((value) => inShortSaid.includes(value))).toEqual([]);
  });

  test("test_the_band_is_never_told_by_colour_alone", () => {
    show("thrushcombe");

    // The picture is kept from a screen reader, because the words beside it say the same.
    // So the words must be drawn, and not hidden.
    expect(lines()).toHaveLength(14);
    for (const one of lines()) {
      const words = [...one.querySelectorAll("span")].filter(
        (span) => /^band \d of 5$/.test(span.childNodes[0]?.textContent ?? "") && !span.classList.contains("visually-hidden"),
      );
      expect(words).toHaveLength(1);
      expect(words[0]?.closest("[aria-hidden='true']")).toBeNull();
    }
  });

  test("test_a_mixed_area_is_drawn_as_a_range_and_said_to_vary_within_the_area", () => {
    show("foxholt");

    expect(line("Going out")).toHaveTextContent("varies within this area, between band 3 and band 5 of 5");
    expect(filled("Going out")).toEqual([false, false, true, true, true]);
    expect(line("Going out").querySelector("[data-range='true']")).not.toBeNull();
    // Never a point in the middle.
    expect(line("Going out")).not.toHaveTextContent("band 4 of 5");
  });

  test("test_a_scale_names_both_its_ends_and_a_vibe_that_runs_one_way_runs_from_least_to_most", () => {
    show("thrushcombe");

    expect(pictureIn(line("Houses or flats"))?.textContent).toBe("HousesFlats");
    expect(pictureIn(line("Leafy"))?.textContent).toBe(`${STRIP.least}${STRIP.most}`);
  });

  test("test_a_figure_a_person_can_picture_stands_beside_each_vibe_of_the_lists_and_beside_no_scale", () => {
    const { portrait } = show("foxholt");

    for (const group of ["more", "less", "others"] as const) {
      for (const mark of portrait[group]) {
        expect(mark.pictured).not.toBeNull();
        expect(line(mark.tag.label).textContent?.includes(`${mark.pictured?.label}: ${mark.pictured?.slots.value}`)).toBe(true);
      }
    }
    // Food and drink is a share of the places within reach, and not a count for each square kilometre.
    expect(line("Food and drink").textContent?.includes("per km")).toBe(false);
    expect(line("Food and drink")).toHaveTextContent(
      "Places to eat and drink that belong to no chain, as a share of those within 800 m of home, in a straight line: 27%",
    );
    // A scale says its two ends. The heaviest part of one may be a figure of recorded crime,
    // which is never shown before it is asked for.
    for (const mark of portrait.scales) {
      expect(line(mark.tag.label).textContent?.includes(mark.figure?.slots.value ?? "no figure")).toBe(false);
    }
    expect(portrait.scales.some((mark) => mark.figure?.template === "feature_crime")).toBe(true);
  });
});

describe("what Burro cannot place", () => {
  const unplaced = () => list("unplaced") as HTMLElement;

  test("test_an_area_that_cannot_be_placed_says_so_once_with_why_and_not_once_for_each_vibe", () => {
    const { portrait } = show("otterby-fields");

    expect(portrait.unplaced).toHaveLength(13);
    expect(within(unplaced()).getByRole("heading", { level: 3 })).toHaveTextContent(PORTRAIT.groups.unplaced);
    // Why is said once on the page, however many vibes it is true of.
    expect(document.body.textContent?.split(PORTRAIT.unplacedWhy)).toHaveLength(2);
    // Every vibe is named, by the name the API gives it, in one line and in the API's order.
    const names = unplaced().querySelector("p")?.textContent ?? "";
    const at = portrait.unplaced.map((mark) => names.indexOf(mark.tag.label));
    expect(at.every((found) => found >= 0)).toBe(true);
    expect(at).toEqual([...at].sort((one, other) => one - other));
    // Before anything is opened it is three lines and one thing to press: not ten lines of the same.
    const drawn = [...unplaced().querySelectorAll("h3, p, li, summary")].filter(
      (one) => one.closest("details") === null || one.matches("details > summary"),
    );
    expect(drawn).toHaveLength(4);
    expect(unplaced().querySelectorAll("summary")).toHaveLength(1);
    expect(unplaced().querySelector("summary")).toHaveTextContent(PORTRAIT.unplacedOpens);
    expect(unplaced().querySelector("summary")).toHaveClass("target-min");
  });

  test("test_no_vibe_that_cannot_place_the_area_is_drawn_as_a_mark_or_put_in_the_middle", () => {
    show("otterby-fields");

    // No line, no cell and no band: nothing that could be read as the middle.
    expect(unplaced().querySelectorAll("[data-on]")).toHaveLength(0);
    expect(unplaced().querySelectorAll("details[data-vibe]")).toHaveLength(0);
    expect(/band \d/.test(unplaced().textContent ?? "")).toBe(false);
    expect(Object.values(BAND_ONE_WAY).filter((words) => unplaced().textContent?.includes(words))).toEqual([]);
  });

  test("test_what_is_known_of_each_is_one_press_away_with_its_counts_its_source_and_what_is_missing", () => {
    const { portrait } = show("otterby-fields");
    const opened = unplaced().querySelector("details") as HTMLDetailsElement;

    expect(opened.open).toBe(false);
    for (const mark of portrait.unplaced) {
      const row = within(opened).getByRole("group", { name: mark.tag.label, hidden: true });
      // How many parts of its recipe have a figure, of how many: both counts are the API's.
      expect(row).toHaveTextContent(`${FACT_COLUMNS.partsKnown}${mark.fact.slots.known}`);
      expect(row).toHaveTextContent(`${FACT_COLUMNS.parts}${mark.fact.slots.parts}`);
      expect(row).toHaveTextContent(CANNOT_PLACE);
      expect(within(row).getByRole("link", { name: mark.fact.sources[0]?.name, hidden: true })).toHaveAttribute(
        "href",
        `/sources#${mark.fact.sources[0]?.source_id}`,
      );
      expect(row).toHaveTextContent(`${SOURCE.dataFrom} ${readableDate(mark.fact.as_of)}`);
      // Which parts have no figure, by the names the API gives them.
      const item = row.closest("li") as HTMLElement;
      for (const name of restsOn(mark)?.missing ?? []) expect(item.textContent?.includes(name)).toBe(true);
      expect(item.textContent?.includes(RESTS_ON.without)).toBe(true);
    }
    // A part this data does not carry is counted, and never shown by its code.
    for (const code of ["gp_walk", "pharmacy_walk", "cuisine_variety", "private_outdoor_space"]) {
      expect(document.body.textContent?.includes(code)).toBe(false);
    }
  });

  test("test_the_summary_says_how_many_vibes_cannot_place_the_area_and_leads_to_why", () => {
    show("otterby-fields");

    expect(short()).toHaveTextContent(PORTRAIT.short.unplaced(13, 14));
    const why = within(short()).getByRole("link", { name: PORTRAIT.short.why });
    expect(document.getElementById((why.getAttribute("href") ?? "").slice(1))).toBe(
      within(unplaced()).getByRole("heading", { level: 3 }),
    );
    expect(why).toHaveClass("target-min");
  });

  test("test_an_area_that_every_vibe_can_place_says_nothing_of_this", () => {
    show("thrushcombe");

    expect(list("unplaced")).toBeNull();
    expect(short().textContent?.includes("cannot place")).toBe(false);
  });

  test("test_the_one_vibe_the_area_can_be_placed_on_is_placed", () => {
    show("otterby-fields");

    expect(list("scales")?.querySelectorAll("summary")).toHaveLength(1);
    expect(line("Houses or flats")).toHaveTextContent(/band \d of 5/);
  });
});

describe("what an area is like, in short", () => {
  test.each(SLUGS)("test_the_portrait_opens_with_five_lines_at_most_each_a_vibe_said_in_words: %s", (slug) => {
    const { portrait } = show(slug);
    const expected = inShort(portrait, meta.features);

    const said = within(short()).queryAllByRole("listitem");

    expect(said.length).toBeLessThanOrEqual(5);
    expect(said.map((item) => item.querySelector("span")?.textContent)).toEqual(expected.map((mark) => mark.tag.label));
    expected.forEach((mark, at) => {
      if (mark.placed === null) throw new Error("A vibe of the summary has no band.");
      // In words a person would use, which are true of the band the fact holds.
      expect(said[at]?.textContent?.includes(plainly(mark.tag, mark.placed) ?? "no words")).toBe(true);
      expect(/band \d/.test(said[at]?.textContent ?? "")).toBe(false);
    });
    // It stands before every list of the portrait.
    const first = document.querySelector("details[data-vibe]");
    if (first !== null) expect(short().compareDocumentPosition(first) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  test("test_what_the_area_is_like_comes_first_and_what_explains_it_stands_after_it", () => {
    // Measured on a phone, 390 by 844: what a vibe is stood over the five lines in three
    // lines of its own, and the first thing said of the area began under the first screen.
    // A person came for what the area is like. So the lines stand directly under their
    // label, and what explains them stands after them: what a vibe is, what could not be
    // worked out, and the sources.
    show("pellam-cross");
    const lines = within(short()).getByRole("list");
    const lead = within(short()).getByText(PORTRAIT.short.lead);

    expect(short().querySelector("h3")?.nextElementSibling).toBe(lines);
    expect(lines.nextElementSibling).toBe(lead);
    expect([...short().children].map((part) => part.tagName).slice(0, 3)).toEqual(["H3", "UL", "P"]);
    // It is said once, in sight, and is no heading and nothing to press.
    expect(within(short()).getAllByText(PORTRAIT.short.lead)).toHaveLength(1);
    expect(lead.closest("details, [hidden], [aria-hidden='true'], .visually-hidden")).toBeNull();
    // What opens the sources of the lines is the last thing of the part, as it was.
    expect(short().lastElementChild?.tagName).toBe("DETAILS");
  });

  test("test_what_could_not_be_worked_out_is_said_after_what_a_vibe_is", () => {
    const [slug = ""] = SLUGS.filter((one) => portraitOf(profile(one), meta).unplaced.length > 0 && inShort(portraitOf(profile(one), meta), meta.features).length > 0);
    const { portrait } = show(slug);
    const placed = shownOn(portrait).length + portrait.unplaced.length;

    expect([...short().children].map((part) => part.tagName)).toEqual(["H3", "UL", "P", "P", "DETAILS"]);
    expect(short().children[2]).toHaveTextContent(PORTRAIT.short.lead);
    expect(short().children[3]).toHaveTextContent(PORTRAIT.short.unplaced(portrait.unplaced.length, placed));
  });

  test("test_it_says_what_the_area_has_most_of_and_least_of_against_the_rest", () => {
    show("pellam-cross");

    const said = within(short()).getAllByRole("listitem").map((item) => item.textContent ?? "");

    expect(said.some((text) => text.includes("Everyday on foot") && text.includes("among the most"))).toBe(true);
    expect(said.some((text) => text.includes("Leafy") && text.includes("among the least"))).toBe(true);
    // Each is said of the area among the areas compared. "Here" was read as the area itself.
    expect(said.filter((text) => /\bhere\b/i.test(text))).toEqual([]);
    expect(said.some((text) => text.includes("Houses or flats") && text.includes("at the Flats end"))).toBe(true);
  });

  test("test_each_line_gives_a_figure_a_person_can_picture_which_is_a_fact_of_the_apis", () => {
    const { data, portrait } = show("thrushcombe");

    const said = within(short()).getAllByRole("listitem");

    inShort(portrait, meta.features).forEach((mark, at) => {
      if (mark.pictured === null) return;
      expect(data.facts.map((fact) => fact.fact_id)).toContain(mark.pictured.fact_id);
      expect(said[at]?.textContent?.includes(`${mark.pictured.label}: ${mark.pictured.slots.value}`)).toBe(true);
    });
    expect(said[0]).toHaveTextContent(
      "Places to eat and drink that belong to no chain, as a share of those within 800 m of home, in a straight line: 84%",
    );
    expect(said[1]).toHaveTextContent(
      "Distance to the nearest marked entrance to a park of 20 hectares or more, in a straight line: 1,420 m",
    );
  });

  test("test_it_ends_in_the_source_and_the_date_of_what_it_says", () => {
    const { portrait } = show("thrushcombe");
    const first = inShort(portrait, meta.features)[0];

    expect(within(short()).getAllByRole("link", { name: first?.fact.sources[0]?.name })[0]).toHaveAttribute(
      "href",
      `/sources#${first?.fact.sources[0]?.source_id}`,
    );
    expect(short()).toHaveTextContent(`${SOURCE.dataFrom} ${first?.fact.as_of}`);
    expect(short()).toHaveTextContent(SOURCE.madeUp);
  });

  test("test_no_line_of_it_is_of_a_vibe_that_holds_recorded_crime_and_no_figure_in_it_is_of_crime", () => {
    for (const slug of ["pellam-cross", "lantern-yard", "cindermoor"]) {
      const view = show(slug);
      expect(short().textContent?.includes("Gritty")).toBe(false);
      expect(/recorded|crime|damage|anti-social/i.test(short().textContent ?? "")).toBe(false);
      view.unmount();
    }
  });

  test("test_it_holds_nothing_to_press_but_the_way_to_a_source_and_reads_with_scripts_off", () => {
    const html = renderToStaticMarkup(<Portrait data={profile("thrushcombe")} meta={meta} />);
    show("thrushcombe");

    expect(short().querySelectorAll("button, input")).toHaveLength(0);
    // What opens is the browser's own, and opens the sources of the lines and nothing else.
    const opens = [...short().querySelectorAll("details")];
    expect(opens.map((part) => part.querySelector(":scope > summary")?.textContent)).toEqual([PORTRAIT.short.sources]);
    expect(opens.map((part) => part.querySelectorAll("a[href^='/sources#']").length > 0)).toEqual([true]);
    expect(html).toContain(PORTRAIT.short.title);
    expect(html).toContain(BAND_ONE_WAY[5]);
  });

  test("test_an_area_that_nothing_sets_apart_says_so_and_draws_no_empty_list", () => {
    const thrushcombe = profile("thrushcombe");
    // Every vibe in the middle band: nothing is furthest from the middle.
    const level = {
      ...thrushcombe,
      facts: thrushcombe.facts.map((fact) =>
        fact.kind === "tag" ? { ...fact, slots: { ...fact.slots, band: "3", spread_low: "3", spread_high: "3" } } : fact,
      ),
    };
    render(<Portrait data={level} meta={meta} />);

    expect(short()).toHaveTextContent(PORTRAIT.short.none);
    expect(within(short()).queryAllByRole("listitem")).toEqual([]);
    expect(within(short()).queryByRole("list")).toBeNull();
  });
});

describe("a band that rests on part of a recipe", () => {
  test("test_the_line_of_the_vibe_says_so_beside_the_band_in_words", () => {
    render(<Portrait data={withNoClause(profile("marrowfen"))} meta={meta} />);

    // Marrowfen has no figure for transport noise: Quiet streets is placed from three parts of four.
    expect(line("Quiet streets")).toHaveTextContent(`${STRIP.band(2)}`);
    expect(line("Quiet streets").textContent?.includes(RESTS_ON.short("3", "4"))).toBe(true);
    // It is drawn where it can be seen, and not kept for a screen reader.
    const said = [...line("Quiet streets").querySelectorAll("span")].find(
      (span) => span.textContent === RESTS_ON.short("3", "4"),
    );
    expect(said?.closest(".visually-hidden")).toBeNull();
    // A band that rests on the whole of its recipe says no such thing.
    expect(line("Leafy").textContent?.includes("of its")).toBe(false);
  });

  test.each(SLUGS)("test_a_band_that_rests_on_part_says_approx_data_after_the_mark_of_what_is_not_whole_as_a_result_does: %s", (slug) => {
    const { portrait } = show(slug);

    for (const mark of shownOn(portrait)) {
      const one = document.querySelector<HTMLElement>(`details[data-vibe="${mark.tag.tag_id}"] > summary`) as HTMLElement;
      const said = [...one.querySelectorAll<HTMLElement>("[data-known='some']")];
      const rests = restsOn(mark);
      // Once, where the band rests on part of what goes into it, and nowhere else.
      expect([mark.tag.tag_id, said.length]).toEqual([mark.tag.tag_id, rests === null ? 0 : 1]);
      if (rests === null) continue;
      const [approx] = said;
      // The mark, which is dress, and then the two words, which are read and heard.
      expect([mark.tag.tag_id, approx?.textContent]).toEqual([mark.tag.tag_id, KNOWN.some]);
      const drawn = approx?.querySelector<HTMLElement>("[style*='/art/']");
      expect([mark.tag.tag_id, drawn?.style.getPropertyValue("--art")]).toEqual([mark.tag.tag_id, 'url("/art/ui-approx.png")']);
      expect(drawn).toHaveAttribute("aria-hidden", "true");
      expect(approx?.closest("[aria-hidden='true'], .visually-hidden")).toBeNull();
      // The page of an area says what it rests on too, after the two words, in sight.
      const onWhat = rests.partly ?? RESTS_ON.short(rests.known, rests.parts);
      const after = one.textContent?.split(KNOWN.some)[1] ?? "";
      expect([mark.tag.tag_id, after.includes(onWhat)]).toEqual([mark.tag.tag_id, true]);
    }
  });

  test("test_what_the_vibe_opens_to_says_which_parts_are_missing", () => {
    render(<Portrait data={withNoClause(profile("marrowfen"))} meta={meta} />);

    const opened = vibe("Quiet streets");

    expect(opened.textContent?.includes(RESTS_ON.full("3", "4"))).toBe(true);
    expect(opened.textContent?.includes(`${RESTS_ON.without}: Share of residents exposed to 55 dB or more of transport noise`)).toBe(
      true,
    );
    // Each part is named as the API names it, as it came: a name may hold a figure of its own.
    const names = [...opened.querySelectorAll("p span > span")].map((name) => name.textContent);
    expect(names).toContain("Share of residents exposed to 55 dB or more of transport noise");
    expect(vibe("Leafy").textContent?.includes(RESTS_ON.without)).toBe(false);
  });

  test("test_a_part_this_data_does_not_carry_is_named_among_what_is_missing", () => {
    // Seen in a browser: "No figure for: 2 parts this data does not carry". Neither was named.
    const { data } = show("thrushcombe");

    // The line says how much the band was worked out from, in the sentence the service gives.
    const clause = data.facts.find((fact) => fact.kind === "tag" && fact.key === "everyday_on_foot")?.slots.partly;
    expect(clause).toBe("Burro has a figure for 3 of the 5 measurements that go into this vibe, and they count for 70 of 100 in it.");
    expect(line("Everyday on foot").textContent?.includes(clause ?? "no clause")).toBe(true);
    const said = vibe("Everyday on foot").textContent ?? "";
    expect(
      said.includes(
        `${RESTS_ON.without}: ${RESTS_ON.waits("Distance to the nearest GP practice, in a straight line, with each practice placed by its postcode")}; ${RESTS_ON.waits("Distance to the nearest pharmacy, in a straight line, with each pharmacy placed by its postcode")}`,
      ),
    ).toBe(true);
    expect(said.includes(RESTS_ON.notCarried(2))).toBe(false);
  });

  test.each(SLUGS)("test_the_summary_says_it_too_in_the_two_words_after_their_mark: %s", (slug) => {
    const { data } = show(slug);

    const lines = inShort(portraitOf(data, meta), meta.features);
    const items = within(short()).queryAllByRole("listitem");
    expect(items).toHaveLength(lines.length);
    lines.forEach((mark, at) => {
      const said = [...(items[at]?.querySelectorAll<HTMLElement>("[data-known='some']") ?? [])];
      // A line of what an area is like is short: it says that the band is not whole, and
      // what it rests on is said on the line of the vibe, under it.
      expect([mark.tag.tag_id, said.map((one) => one.textContent)]).toEqual([mark.tag.tag_id, restsOn(mark) === null ? [] : [KNOWN.some]]);
      expect([mark.tag.tag_id, items[at]?.textContent?.includes(" of its ")]).toEqual([mark.tag.tag_id, false]);
    });
  });

  test("test_some_line_of_what_an_area_is_like_rests_on_part_so_that_the_summary_is_held", () => {
    const resting = SLUGS.filter((slug) => inShort(portraitOf(profile(slug), meta), meta.features).some((mark) => restsOn(mark) !== null));

    expect(resting.length).toBeGreaterThan(0);
  });

  test("test_what_a_band_rests_on_is_said_in_the_apis_own_clause_where_the_fact_holds_one", () => {
    // One fact holds a clause, and no other does: so the page says both ways side by side.
    const marrowfen = withNoClause(profile("marrowfen"));
    const clause = "Worked out from 3 of its 4 parts, 70 of 100 by weight.";
    const told = {
      ...marrowfen,
      facts: marrowfen.facts.map((fact) =>
        fact.kind === "tag" && fact.key === "quiet_residential"
          ? { ...fact, slots: { ...fact.slots, share: "70", partly: clause } }
          : fact,
      ),
    };
    render(<Portrait data={told} meta={meta} />);

    // On the line, beside the band, and where the line is opened: word for word as it came.
    expect(line("Quiet streets").textContent?.includes(clause)).toBe(true);
    expect(vibe("Quiet streets").textContent?.split(clause).length).toBeGreaterThanOrEqual(3);
    // The website's own words for it give way to the API's.
    const own = [...vibe("Quiet streets").querySelectorAll("span, p")].filter(
      (one) => one.textContent === RESTS_ON.short("3", "4") || one.textContent === RESTS_ON.full("3", "4"),
    );
    expect(own).toEqual([]);
    expect(vibe("Quiet streets").textContent?.includes(RESTS_ON.full("3", "4"))).toBe(false);
    // Which parts are missing is still said, by the names the API gives them.
    expect(vibe("Quiet streets").textContent?.includes(`${RESTS_ON.without}: Share of residents exposed to 55 dB`)).toBe(true);
    // A fact that holds no clause is said in the website's words, from the counts it does hold.
    expect(line("Houses or flats").textContent?.includes(RESTS_ON.short("2", "3"))).toBe(true);
  });

  test("test_the_apis_clause_stands_as_a_sentence_of_its_own_and_is_followed_by_one_full_stop", () => {
    const marrowfen = profile("marrowfen");
    const clause = "Worked out from 3 of its 4 parts, 70 of 100 by weight.";
    const told = {
      ...marrowfen,
      facts: marrowfen.facts.map((fact) =>
        fact.kind === "tag" && fact.key === "quiet_residential"
          ? { ...fact, slots: { ...fact.slots, share: "70", partly: clause } }
          : fact,
      ),
    };
    render(<Portrait data={told} meta={meta} />);

    const said = line("Quiet streets").textContent ?? "";

    // It begins with a capital, so it follows a full stop, and ends in its own. The two
    // words that say the band is not whole stand before it, as a sentence of their own.
    expect(said.includes(`${STRIP.from(STRIP.least, STRIP.most)}. ${KNOWN.some}. ${clause}`)).toBe(true);
    expect(said.includes(`, ${clause}`)).toBe(false);
    expect(/\.\s*\./.test(said)).toBe(false);
  });

  test("test_what_the_area_is_like_in_short_keeps_to_the_two_words_so_that_a_line_stays_short", () => {
    const thrushcombe = profile("thrushcombe");
    const clause = "Worked out from 2 of its 3 parts, 80 of 100 by weight.";
    const told = {
      ...thrushcombe,
      facts: thrushcombe.facts.map((fact) =>
        fact.kind === "tag" && fact.key === "foodie" ? { ...fact, slots: { ...fact.slots, share: "80", partly: clause } } : fact,
      ),
    };
    render(<Portrait data={told} meta={meta} />);

    const food = within(short())
      .getAllByRole("listitem")
      .find((item) => item.textContent?.startsWith("Food and drink"));

    // It says that the band is not whole. The whole of what the API says is on the line of the vibe.
    expect(food?.textContent?.includes(KNOWN.some)).toBe(true);
    expect(food?.textContent?.includes(RESTS_ON.short("2", "3"))).toBe(false);
    expect(food?.textContent?.includes(clause)).toBe(false);
    expect(line("Food and drink").textContent?.includes(clause)).toBe(true);
  });
});

describe("the parts behind a vibe, one press away", () => {
  test("test_every_vibe_is_closed_until_it_is_pressed_and_opens_with_scripts_off", () => {
    const html = renderToStaticMarkup(<Portrait data={profile("thrushcombe")} meta={meta} />);
    show("thrushcombe");

    // The browser's own element: it opens with no script, and what it holds is in the page.
    expect([...document.querySelectorAll("details")].filter((part) => part.open)).toEqual([]);
    expect(vibes()).toHaveLength(meta.tags.length);
    expect(html).not.toMatch(/<button|aria-expanded|onclick/i);
    expect(html).toContain("Flats as a share of homes");
    for (const one of lines()) {
      expect(one).toHaveClass("target-min");
      expect(one).toHaveTextContent(PORTRAIT.opens);
    }
  });

  test.each(SLUGS)("test_each_part_gives_its_share_its_figure_its_band_its_source_and_its_date: %s", (slug) => {
    const { portrait } = show(slug);
    const every: readonly MarkRow[] = shownOn(portrait);

    for (const mark of every) {
      const parts = [...vibe(mark.tag.label).querySelectorAll<HTMLElement>("li > [role='group']")];
      expect(parts).toHaveLength(mark.parts.length);
      mark.parts.forEach((part, at) => {
        const row = parts[at] as HTMLElement;
        expect(row).toHaveTextContent(`${PORTRAIT.madeOf.share}${PORTRAIT.madeOf.shareOf(part.term.hundredths)}`);
        if (part.fact === null) return;
        expect(row).toHaveAccessibleName(part.fact.label);
        expect(row).toHaveTextContent(`${FACT_COLUMNS.value}${part.fact.slots.value}`);
        expect(row).toHaveTextContent(`${FACT_COLUMNS.band}${part.fact.slots.band}`);
        expect(row).toHaveTextContent(`${FACT_COLUMNS.standing}${part.fact.slots.standing}`);
        expect(within(row).getByRole("link", { name: part.fact.sources[0]?.name, hidden: true })).toHaveAttribute(
          "href",
          `/sources#${part.fact.sources[0]?.source_id}`,
        );
        expect(row).toHaveTextContent(`${SOURCE.dataFrom} ${part.fact.as_of}`);
        expect(row).toHaveTextContent(SOURCE.madeUp);
      });
      // The shares of a recipe add up to a hundred, whatever the area has a figure for.
      expect(mark.parts.reduce((sum, part) => sum + part.term.hundredths, 0)).toBe(100);
    }
  });

  test("test_a_part_with_no_figure_says_so_and_nothing_is_filled_in", () => {
    const { portrait } = show("grapnel-dock");
    const without = shownOn(portrait).flatMap((mark) =>
      mark.parts.filter((part) => part.metric !== null && part.fact === null).map((part) => ({ mark, part })),
    );

    expect(without.length).toBeGreaterThan(0);
    for (const { mark, part } of without) {
      const row = within(vibe(mark.tag.label)).getByRole("group", { name: part.metric?.label, hidden: true });
      expect(row).toHaveTextContent(PORTRAIT.madeOf.noFigure);
      // Its name and its share, and nothing else that is a figure: no value, no band, no source.
      const said = (row.textContent ?? "")
        .replace(part.metric?.label ?? "", "")
        .replace(PORTRAIT.madeOf.shareOf(part.term.hundredths), "");
      expect(said).not.toMatch(/\d/);
      expect(within(row).queryByRole("link", { hidden: true })).toBeNull();
    }
  });

  test("test_a_part_this_data_does_not_carry_is_said_to_be_missing_and_never_shown_by_its_code", () => {
    const { portrait } = show("thrushcombe");
    const missing = GROUPS.flatMap((group) => portrait[group]).flatMap((mark) =>
      mark.parts.filter((part) => part.metric === null).map((part) => ({ mark, part })),
    );

    expect(missing.map(({ part }) => part.term.feature_id).sort()).toEqual([
      "cuisine_variety",
      "gp_walk",
      "pharmacy_walk",
      "private_outdoor_space",
    ]);
    for (const { mark, part } of missing) {
      // It is named as the API names it, and said not to be in the data yet.
      expect(part.waits).not.toBeNull();
      expect(within(vibe(mark.tag.label)).getByRole("group", { name: part.waits ?? "", hidden: true })).toHaveTextContent(
        PORTRAIT.madeOf.waits,
      );
      expect(vibe(mark.tag.label).textContent?.includes(PORTRAIT.madeOf.notCarried)).toBe(false);
      expect(document.body.textContent?.includes(part.term.feature_id)).toBe(false);
    }
  });

  test("test_a_vibe_no_area_can_be_placed_on_is_told_from_one_that_cannot_place_this_area", () => {
    // Seen in a browser: "Too few parts of each recipe have a figure for this area", of
    // vibes that no area of the data has a band for.
    const preview: MetaData = recordedAnswer("get_meta", "preview/meta").body.data;
    const data: AreaData = recordedAnswer("get_area", "preview/area-alderwick").body.data;
    render(<Portrait data={data} meta={preview} />);
    const said = list("unplaced")?.textContent ?? "";
    const nowhere = preview.recipes.filter((held) => !held.placed).map((held) => held.tag_id);

    expect(nowhere).toHaveLength(11);
    expect(said.includes(PORTRAIT.notInData)).toBe(true);
    // Every vibe Alderwick cannot be placed on is one that no area can, so the other is not said.
    expect(data.portrait.unplaced.map((mark) => mark.tag_id).sort()).toEqual([...nowhere].sort());
    expect(said.includes(PORTRAIT.unplacedWhy)).toBe(false);
    // What each waits on is named, one press away.
    expect(said.includes(RESTS_ON.waits("Land that is residential garden"))).toBe(true);
    expect(said.includes("parts this data does not carry")).toBe(false);
  });

  test("test_an_area_that_lacks_figures_of_its_own_says_so_of_those_vibes_alone", () => {
    // On a release that holds everything, an area no vibe can place lacks figures of its own.
    show("otterby-fields");
    const said = list("unplaced")?.textContent ?? "";

    expect(said.includes(PORTRAIT.unplacedWhy)).toBe(true);
    expect(said.includes(PORTRAIT.notInData)).toBe(false);
  });

  test("test_a_part_of_a_scale_says_which_end_a_higher_figure_counts_towards", () => {
    show("thrushcombe");

    const flats = within(vibe("Houses or flats")).getByRole("group", { name: "Flats as a share of homes", hidden: true });
    const gardens = within(vibe("Leafy")).getByRole("group", { name: "Land that is residential garden", hidden: true });

    expect(flats).toHaveTextContent(`${PORTRAIT.madeOf.reading}A higher figure counts towards Flats`);
    expect(gardens).toHaveTextContent(`${PORTRAIT.madeOf.reading}${READING.high}`);
  });

  test("test_what_a_vibe_opens_to_says_what_it_means_where_its_band_came_from_and_that_it_is_a_judgement", () => {
    const { portrait } = show("thrushcombe");

    for (const mark of shownOn(portrait)) {
      const opened = vibe(mark.tag.label);
      const row = within(opened).getByRole("group", { name: mark.tag.label, hidden: true });
      expect(opened).toHaveTextContent(mark.tag.meaning);
      expect(row).toHaveTextContent(`${FACT_COLUMNS.compared}${mark.fact.slots.compared}`);
      expect(row).toHaveTextContent(`${FACT_COLUMNS.partsDated}${mark.fact.slots.span}`);
      expect(row).toHaveTextContent(mark.fact.slots.judgement ?? "no judgement");
      // A vibe is Burro's own recipe. The line of its sources says so, in the API's words.
      expect(row).toHaveTextContent(`${mark.fact.slots.made_from} ${mark.fact.sources[0]?.name}`);
      expect(within(opened).getByRole("link", { name: PORTRAIT.madeOf.about(mark.tag.label), hidden: true })).toHaveAttribute(
        "href",
        `/vibes#${mark.tag.tag_id}`,
      );
    }
  });

  test("test_a_vibe_that_holds_recorded_crime_says_so_where_it_is_opened_with_when_recorded_crime_counts", () => {
    show("thrushcombe");

    const opened = vibe("Gritty");

    expect(opened.textContent?.includes(`${CRIME_ACCOUNT.counts}: `)).toBe(true);
    expect(opened.textContent?.includes(CRIME_RULE)).toBe(true);
    expect(opened.textContent?.includes(CRIME_ACCOUNT.asking)).toBe(true);
    // It is said of no vibe that holds none, and is not drawn before the vibe is opened.
    for (const label of ["Leafy", "Going out", "Houses or flats"]) expect(vibe(label).textContent?.includes(CRIME_RULE)).toBe(false);
    expect(line("Gritty").textContent?.includes(CRIME_ACCOUNT.counts)).toBe(false);
    expect(short().textContent?.includes(CRIME_ACCOUNT.counts)).toBe(false);
  });

  test("test_a_figure_of_recorded_crime_carries_its_caveat_wherever_it_is_a_part", () => {
    const { portrait } = show("thrushcombe");
    const street = portrait.scales.find((mark) => mark.tag.tag_id === "street_character");
    const crime = street?.parts.filter((part) => part.fact?.template === "feature_crime") ?? [];

    expect(crime).toHaveLength(2);
    for (const part of crime) {
      expect(within(vibe("Gritty")).getByRole("group", { name: part.fact?.label, hidden: true })).toHaveTextContent(
        CRIME_CAVEAT,
      );
    }
    // No word of the page is a verdict, and none is the word the service gives a vibe that is less sure.
    expect(/\b(safe|safer|safest|unsafe|dangerous|rough|dodgy|sketchy)\b/i.test(document.body.textContent ?? "")).toBe(false);
  });
});

describe("a vibe the service says is less sure, on the page of an area", () => {
  // The service says which vibe it is, in a code, and no word more. One that is older than
  // the website, or later, may say its label and why: so the page is handed the release as
  // such a service gave it, with both laid on it.
  const said = sayingSo(meta);
  const village = () => meta.tags.find((tag) => tag.tag_id === ROUGH.tag_id)!;

  test("test_its_line_says_where_the_area_sits_as_the_line_of_every_vibe_does_and_nothing_of_how_sure_it_is", () => {
    // The founder: "remove the concept of rough guide, we don't want to pass this on to a user".
    show("thrushcombe", said);

    expect([said.rough_guides, village().sureness]).toEqual([[ROUGH], "rough_guide"]);
    const its = vibe("Village feel");
    expect(its.open).toBe(false);
    expect(line("Village feel")).toHaveTextContent(plainly(village(), { band: 5, spread_low: 5, spread_high: 5 }) ?? "");
    expect(line("Village feel")).toHaveTextContent(STRIP.band(5));
    // Nothing stands beside its band, and nothing under its line but the line of the next vibe.
    expect(line("Village feel").textContent?.includes(ROUGH.label)).toBe(false);
    expect(its.nextElementSibling === null || its.nextElementSibling.tagName === "DETAILS").toBe(true);
    expect(document.querySelector("[data-rough-guide]")).toBeNull();
    expect(screen.queryAllByRole("note")).toEqual([]);
  });

  test.each(SLUGS)("test_no_page_of_an_area_says_its_label_or_its_sentence_anywhere: %s", (slug) => {
    const { portrait } = show(slug, said);
    const drawn = document.body.textContent ?? "";

    expect(drawn.length).toBeGreaterThan(200);
    expect([drawn.includes(ROUGH.label), drawn.includes(ROUGH.why), /less sure|rough guide/i.test(drawn)]).toEqual([false, false, false]);
    expect(document.querySelector("[data-rough-guide]")).toBeNull();
    // The vibe itself is shown wherever the service places the area on it.
    const placed = shownOn(portrait).filter((mark) => mark.tag.tag_id === "village_feel");
    expect(vibes().filter((part) => part.getAttribute("data-vibe") === "village_feel")).toHaveLength(placed.length);
  });

  test("test_it_is_in_no_line_of_what_the_area_is_like_in_short_and_in_neither_list_of_most_and_least", () => {
    // What is less sure is not what an area is said to be like, and that is said by nothing:
    // the vibe has its own line among the rest, as it had.
    const { portrait } = show("thrushcombe");

    expect(short().textContent?.includes("Village feel")).toBe(false);
    expect([...portrait.more, ...portrait.less].map((mark) => mark.tag.tag_id)).not.toContain("village_feel");
    expect(portrait.others.map((mark) => mark.tag.tag_id)).toContain("village_feel");
  });

  test("test_whatever_the_service_says_of_whichever_vibe_no_label_and_no_sentence_is_drawn", () => {
    const every = sayingSo(meta, meta.tags.map((tag) => tag.tag_id));
    render(<Portrait data={profile("thrushcombe")} meta={every} />);
    const drawn = document.body.textContent ?? "";

    expect(every.rough_guides.map((told) => [told.tag_id, told.label, told.why])).toEqual(meta.tags.map((tag) => [tag.tag_id, ROUGH.label, ROUGH.why]));
    expect(every.tags.filter((tag) => tag.sureness !== "rough_guide")).toEqual([]);
    expect(document.querySelector("[data-rough-guide]")).toBeNull();
    expect([drawn.includes(ROUGH.label), drawn.includes(ROUGH.why), /less sure|rough guide/i.test(drawn)]).toEqual([false, false, false]);
  });
});

describe("the portrait, whichever way gritty is built", () => {
  test("test_the_way_gritty_was_built_is_a_vibe_like_any_other_and_is_named_by_the_release", () => {
    // The profile is of the release that builds it as a scale. Held against the other
    // release, the scale has no name there, and is left out: nothing is said of it.
    render(<Portrait data={profile("thrushcombe")} meta={variantA} />);

    expect(variantA.tags.map((tag) => tag.tag_id)).toContain("works_warehouses");
    expect(screen.queryByText("Gritty")).toBeNull();
    expect(vibes()).toHaveLength(13);
  });
});

describe("the portrait, by keyboard and to a screen reader", () => {
  test.each(["thrushcombe", "foxholt", "otterby-fields"])("test_the_portrait_has_no_accessibility_fault: %s", async (slug) => {
    const { container } = show(slug);

    expect(await faultsIn(container)).toEqual([]);
  });

  /**
   * What a line reads as to whoever hears the page, from what the service gives of its
   * vibe: its name, its two ends, where the area sits in words, the band with what the
   * bands run between, the two words and what the band rests on where it is not whole, the
   * figure of one of its measurements where its list says one, and what the line opens.
   */
  function readsAs(mark: MarkRow, group: Group): string {
    const { tag, placed, pictured } = mark;
    if (placed === null) throw new Error("A vibe that is shown has no band.");
    const [low, high] = [tag.low_end ?? STRIP.least, tag.high_end ?? STRIP.most];
    const rests = restsOn(mark);
    // A sentence of the service ends in a full stop of its own.
    const onWhat = rests === null ? null : (rests.partly ?? `${RESTS_ON.short(rests.known, rests.parts)}.`);
    // A scale says its two ends, and no figure.
    const figure = group === "scales" || pictured?.slots.value === undefined ? null : `${pictured.label}: ${pictured.slots.value}`;
    return [
      `${tag.label}${low}${high}`,
      isRange(placed) ? "" : `${plainly(tag, placed)}, `,
      `${inWords(placed)}, ${STRIP.from(low, high)}`,
      onWhat === null ? "" : `. ${KNOWN.some}. ${onWhat}`,
      figure === null ? "" : `${onWhat === null ? ". " : " "}${figure}`,
      onWhat !== null && figure === null ? " " : ". ",
      PORTRAIT.opens,
    ].join("");
  }

  test.each(SLUGS)("test_every_line_reads_as_whole_sentences_to_a_screen_reader: %s", (slug) => {
    const { portrait } = show(slug);

    for (const group of GROUPS.filter((one) => one !== "unplaced")) {
      for (const mark of portrait[group]) {
        expect([mark.tag.tag_id, line(mark.tag.label).textContent]).toEqual([mark.tag.tag_id, readsAs(mark, group)]);
      }
    }
  });

  test("test_the_recorded_areas_hold_lines_of_every_kind_so_that_each_is_read", () => {
    const all = SLUGS.flatMap((slug) => {
      const portrait = portraitOf(profile(slug), meta);
      return GROUPS.filter((one) => one !== "unplaced").flatMap((group) => portrait[group].map((mark) => ({ mark, group })));
    });
    const kinds = new Set(
      all.map(({ mark, group }) =>
        [
          group === "scales" ? "a scale" : "one way",
          restsOn(mark) === null ? "whole" : restsOn(mark)?.partly === null ? "not whole" : "not whole, in a sentence of the service",
          mark.placed !== null && isRange(mark.placed) ? "varies" : "in one band",
        ].join(", "),
      ),
    );

    // Both kinds of vibe, whole and not, in one band and across several.
    for (const kind of ["a scale", "one way"]) {
      for (const whole of ["whole", "not whole, in a sentence of the service"]) {
        expect([...kinds]).toContain(`${kind}, ${whole}, in one band`);
      }
    }
    expect([...kinds].some((kind) => kind.endsWith("varies"))).toBe(true);
  });

  test.each(SLUGS)("test_a_line_whose_band_rests_on_part_reads_as_it_did_before_the_service_gave_its_sentence: %s", (slug) => {
    // An answer that is older than the sentence says the two counts, and the line says them
    // in words of its own, which end in a full stop as the sentence of the service does.
    const data = withNoClause(profile(slug));
    render(<Portrait data={data} meta={meta} />);
    const portrait = portraitOf(data, meta);

    for (const group of GROUPS.filter((one) => one !== "unplaced")) {
      for (const mark of portrait[group]) {
        expect(restsOn(mark)?.partly ?? null).toBeNull();
        expect([mark.tag.tag_id, line(mark.tag.label).textContent]).toEqual([mark.tag.tag_id, readsAs(mark, group)]);
      }
    }
  });
});

describe("the look of the portrait", () => {
  /** The line of a vibe, by the id the service gives the vibe. No vibe is named here. */
  const lineOf = (tagId: string) => document.querySelector<HTMLElement>(`details[data-vibe="${tagId}"] > summary`);
  /** The small pictures a line draws at the ends of its steps, by the drawing each is. */
  const endsDrawn = (tagId: string) =>
    [...(lineOf(tagId)?.querySelectorAll<HTMLElement>("[data-at] > [style]") ?? [])].map((end) => end.style.getPropertyValue("--art"));
  const served = (name: string) => `url("/art/${name}.png")`;

  test.each(SLUGS)("test_every_vibe_has_one_small_picture_at_each_end_of_its_steps_chosen_by_the_id_of_the_vibe: %s", (slug) => {
    const { portrait } = show(slug);
    const shown = shownOn(portrait);

    for (const { tag } of shown) {
      // One at each end, and the low end stands first: a vibe that runs between two named
      // ends, and one that runs one way, from little of the thing to much of it.
      expect([tag.tag_id, endsDrawn(tag.tag_id)]).toEqual([tag.tag_id, picturesAtEnds(tag.tag_id).map(served)]);
      // The two are opposites, so no vibe has one picture at both its ends.
      const [low, high] = endsDrawn(tag.tag_id);
      expect([tag.tag_id, low === high]).toEqual([tag.tag_id, false]);
      // The steps stand between the two, in the page as to the eye.
      const picture = pictureIn(lineOf(tag.tag_id));
      expect([...(picture?.children ?? [])].map((part) => part.getAttribute("data-at") ?? "steps")).toEqual(["low", "steps", "high"]);
    }
    // The release holds vibes of both kinds, so both are held.
    expect(new Set(meta.tags.map((tag) => tag.shape))).toEqual(new Set(["scale", "one_way"]));
  });

  test("test_every_vibe_of_the_release_has_pictures_of_its_own_and_none_is_left_under_the_blank_one", () => {
    const blank = meta.tags.filter((tag) => picturesAtEnds(tag.tag_id).includes(NO_PICTURE));

    expect(blank.map((tag) => tag.tag_id)).toEqual([]);
  });

  test("test_a_vibe_whose_ends_nobody_has_drawn_takes_the_blank_picture_at_both_and_is_never_drawn_as_nothing", () => {
    const data = profile(SLUGS[0] ?? "");
    const [placed] = shownOn(portraitOf(data, meta)).filter(({ tag }) => tag.shape === "scale");
    if (placed === undefined) throw new Error("The first recorded area is placed on no scale.");
    // A vibe that is new to the website: the service names it and its ends, and nobody has drawn them.
    const renamed = "a_vibe_nobody_drew";
    const held = {
      ...meta,
      tags: meta.tags.map((tag) => (tag.tag_id === placed.tag.tag_id ? { ...tag, tag_id: renamed, low_end: "An end nobody drew" } : tag)),
    };
    const told = {
      ...data,
      portrait: Object.fromEntries(
        Object.entries(data.portrait).map(([group, marks]) => [
          group,
          marks.map((mark) => (mark.tag_id === placed.tag.tag_id ? { ...mark, tag_id: renamed } : mark)),
        ]),
      ),
    } as unknown as AreaData;
    render(<Portrait data={told} meta={held as unknown as MetaData} />);

    expect(endsDrawn(renamed)).toEqual([served(NO_PICTURE), served(NO_PICTURE)]);
    // The name of each end is drawn as the service gave it, with its picture.
    expect(pictureIn(lineOf(renamed))?.textContent).toBe(`An end nobody drew${placed.tag.high_end}`);
  });

  test("test_the_pictures_are_for_the_eye_and_say_nothing_to_a_screen_reader", () => {
    const { portrait } = show(SLUGS[0] ?? "");

    for (const { tag } of shownOn(portrait)) {
      const line = lineOf(tag.tag_id) as HTMLElement;
      const drawn = [...line.querySelectorAll<HTMLElement>("[style*='/art/']")];
      // The peg of the steps, and the two ends of a scale: each is kept from a screen reader, and holds no word.
      expect(drawn.length).toBeGreaterThan(0);
      expect(drawn.filter((one) => one.closest("[aria-hidden='true']") === null).length).toBe(0);
      expect(drawn.filter((one) => (one.textContent ?? "") !== "" && !one.matches("[data-range]")).length).toBe(0);
      expect(within(line).queryAllByRole("img")).toEqual([]);
    }
  });

  test.each(SLUGS)("test_a_band_that_rests_on_part_of_its_recipe_has_the_step_its_peg_stands_on_chequered: %s", (slug) => {
    const { portrait } = show(slug);

    for (const mark of shownOn(portrait)) {
      const steps = lineOf(mark.tag.tag_id)?.querySelector("[data-part]");
      expect([mark.tag.tag_id, steps?.getAttribute("data-part")]).toEqual([mark.tag.tag_id, String(restsOn(mark) !== null)]);
      // On a narrow screen its steps are the narrower ones, so that its words have room beside them.
      expect([mark.tag.tag_id, steps?.getAttribute("data-narrow")]).toEqual([mark.tag.tag_id, "true"]);
    }
  });

  test("test_a_line_reads_whole_where_what_its_band_rests_on_is_not_drawn_for_want_of_room", () => {
    // In a list as narrow as a phone the two words stand alone, and what the band rests on
    // is one press away. A style sheet takes it out of the line, so the line must read as
    // whole sentences without it, to whoever hears the page as to whoever sees it.
    const written = readFileSync(path.join(__dirname, "Portrait.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
    const narrow = rulesOf(written).filter((rule) => rule.selector === ".restsOn" && rule.sets.get("display") === "none");
    expect(narrow.map((rule) => rule.under)).toEqual(["@container (max-width: 45.99rem)"]);

    for (const slug of SLUGS) {
      const { portrait, unmount } = show(slug);
      for (const mark of shownOn(portrait)) {
        const one = (lineOf(mark.tag.tag_id) as HTMLElement).cloneNode(true) as HTMLElement;
        for (const taken of one.querySelectorAll(".restsOn")) taken.remove();
        const said = one.textContent ?? "";
        // No word runs into the next with no stop between them, and no stop is said twice.
        expect([slug, mark.tag.tag_id, /\.\s*\./.test(said)]).toEqual([slug, mark.tag.tag_id, false]);
        if (restsOn(mark) !== null) expect([slug, mark.tag.tag_id, said.includes(`. ${KNOWN.some}. `)]).toEqual([slug, mark.tag.tag_id, true]);
      }
      unmount();
    }
  });

  test("test_what_says_that_an_area_varies_is_broken_as_a_sentence_is_and_a_band_alone_is_said_whole", () => {
    // Measured on a phone, 390 wide: the line that says between which bands an area varies
    // was set on one line, 384 px wide, and the pages of three areas were 26 px wider than
    // the window. A band alone is a few words and is never broken: what says that an area
    // varies is a sentence, and is broken as one.
    const written = readFileSync(path.join(__dirname, "Portrait.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
    const rules = rulesOf(written).filter((rule) => rule.under === null);
    const of = (selector: string) => rules.filter((rule) => rule.selector === selector).map((rule) => rule.sets.get("white-space"));

    expect(of(".band")).toEqual(["nowrap"]);
    expect(of('.band[data-varies="true"]')).toEqual(["normal"]);
    // Nothing else of a line is kept on one line but the few words of what it opens, and
    // the two words that say a band is not whole, which stand with their mark.
    const onOneLine = rulesOf(written).filter((rule) => rule.sets.get("white-space") === "nowrap");
    expect(onOneLine.map((rule) => rule.selector).sort()).toEqual([".approx", ".band", ".opens"]);

    // The areas that vary on a vibe are found in what was recorded, and none is named here.
    const varies = SLUGS.filter((slug) =>
      shownOn(portraitOf(profile(slug), meta)).some(({ placed }) => placed !== null && isRange(placed)),
    );
    expect(varies.length).toBeGreaterThan(0);
    for (const slug of varies) {
      const { portrait, unmount } = show(slug);
      for (const { tag, placed } of shownOn(portrait)) {
        if (placed === null) continue;
        const band = lineOf(tag.tag_id)?.querySelector<HTMLElement>("[data-varies]");
        expect([slug, tag.tag_id, band?.getAttribute("data-varies")]).toEqual([slug, tag.tag_id, String(isRange(placed))]);
        expect([slug, tag.tag_id, band?.textContent]).toEqual([slug, tag.tag_id, inWords(placed)]);
      }
      unmount();
    }
  });

  test("test_what_a_line_opens_has_its_arrow_after_its_words_which_points_down_while_closed_and_up_while_open", () => {
    // A person who walked the website asked for the arrow of what folds at its far end.
    // It stood before the words and pointed at them, and then down: what folds was drawn
    // three ways. It stands after the words, points down at what is closed and up once
    // that is open, as the arrow of every bar of the website does.
    const written = readFileSync(path.join(__dirname, "Portrait.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
    const rules = rulesOf(written).filter((rule) => !/forced-colors/.test(rule.under ?? ""));
    const of = (selector: string) => new Map(rules.filter((rule) => rule.selector === selector).flatMap((rule) => [...rule.sets]));

    // It is a mark of the style sheet, which holds no word, and is laid after the words it stands with.
    const arrow = of(".opens::before");
    expect(arrow.get("content")).toBe('""');
    expect([of(".opens").get("display"), arrow.get("order")]).toEqual(["inline-flex", "1"]);
    // The head of an arrow, drawn pointing up: three rows of ink, of one pixel, of three and
    // of five. Turned half way round it points down, and as it is drawn it points up.
    expect((arrow.get("background") ?? "").split(/,\s*(?=linear-gradient)/).map((one) => one.replace(/\s+/g, " ").trim())).toEqual([
      "linear-gradient(var(--ink), var(--ink)) calc(var(--px) * 2) var(--px) / var(--px) var(--px) no-repeat",
      "linear-gradient(var(--ink), var(--ink)) var(--px) calc(var(--px) * 2) / calc(var(--px) * 3) var(--px) no-repeat",
      "linear-gradient(var(--ink), var(--ink)) 0 calc(var(--px) * 3) / calc(var(--px) * 5) var(--px) no-repeat",
    ]);
    expect(arrow.get("transform")).toBe("rotate(180deg)");
    expect(of(".mark[open] > .line .opens::before").get("transform")).toBe("none");
    expect(rules.filter((rule) => /\.opens::after/.test(rule.selector)).map((rule) => rule.selector)).toEqual([]);
    // It turns in a room as wide as it is high, so that nothing moves as it turns.
    expect([arrow.get("width"), arrow.get("height")]).toEqual(["calc(var(--px) * 5)", "calc(var(--px) * 5)"]);
    // With forced colours it is cut out of one colour of the system, and points up as it is drawn.
    const forced = rulesOf(written).filter((rule) => /forced-colors/.test(rule.under ?? "") && rule.selector === ".opens::before");
    expect(forced.map((rule) => [rule.sets.get("background"), rule.sets.get("clip-path")])).toEqual([["CanvasText", "polygon(50% 20%, 100% 80%, 0 80%)"]]);
    // What it opens is said first, and the arrow follows it, to the eye and in the page.
    show(SLUGS[0] ?? "");
    for (const line of lines()) expect(line.lastElementChild).toHaveTextContent(PORTRAIT.opens);
  });

  test("test_on_a_narrow_list_the_label_of_what_it_is_like_stands_on_the_line_of_the_heading_where_both_have_room", () => {
    // Measured on a phone, 390 by 844: the heading and the label under it took 73 px
    // before a word was said of the area. The label stands at the far end of the line of
    // the heading, where the part that opens the portrait is wide enough for both and no
    // wider than a phone: with text twice as large it is not, and the label stands under
    // the heading as it did.
    const written = readFileSync(path.join(__dirname, "Portrait.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
    const rules = rulesOf(written);
    const beside = rules.filter((rule) => /^@container\b/.test(rule.under ?? "") && /\.short\b/.test(rule.selector));
    const of = (selector: string) => new Map(beside.filter((rule) => rule.selector === selector).flatMap((rule) => [...rule.sets]));

    // What opens the portrait is asked its own width, as the list of a group is: the label
    // and the heading stand in it, and in no list.
    expect(
      new Map(rules.filter((rule) => rule.selector === ".opening" && rule.under === null).flatMap((rule) => [...rule.sets])).get("container-type"),
    ).toBe("inline-size");
    expect([...new Set(beside.map((rule) => rule.under))]).toEqual(["@container (min-width: 18rem) and (max-width: 39.99rem)"]);
    // The label is pulled up onto the foot of the line of the heading, by its own height
    // and the room over it, and keeps its size: it is as high as its words and its plate.
    const label = of(".short > h3");
    const plate = new Map(
      rules.filter((rule) => rule.under === null && rule.selector.split(",").some((one) => one.trim() === ".short h3")).flatMap((rule) => [...rule.sets]),
    );
    expect([label.get("justify-self"), label.get("align-self")]).toEqual(["end", "start"]);
    expect(label.get("--plate")).toBe("calc(var(--name-1) * 1.2 + var(--px) * 2)");
    expect([plate.get("font"), plate.get("padding")]).toEqual(["400 var(--name-1) / 1.2 var(--font-name)", "calc(var(--px) * 1) calc(var(--px) * 3)"]);
    expect(label.get("margin-block-start")).toBe("calc((var(--plate) + var(--space-3)) * -1)");
    // The lines stand as far under the heading as the label stood: the room a label kept under itself is given back.
    expect([...of(".short > h3 + .shortLines")]).toEqual([["margin-block-start", "calc(var(--space-2) * -1)"]]);
    expect(new Map(rules.filter((rule) => rule.selector === ".short" && rule.under === null).flatMap((rule) => [...rule.sets])).get("gap")).toBe("var(--space-2)");
    expect(new Map(rules.filter((rule) => rule.selector === ".opening" && rule.under === null).flatMap((rule) => [...rule.sets])).get("gap")).toBe("var(--space-3)");
    // Nothing is taken out of the page and laid over it, and nothing is hidden.
    expect(beside.filter((rule) => rule.sets.has("position") || rule.sets.has("display")).map((rule) => rule.selector)).toEqual([]);
  });

  test("test_the_portrait_is_handed_the_arrow_and_the_key_it_is_drawn_with_by_name", () => {
    show(SLUGS[0] ?? "");
    const handed = (name: string) => screen.getByRole("region", { name: PORTRAIT.title }).style.getPropertyValue(name);

    expect([handed("--arrow"), handed("--key")]).toEqual(['url("/art/ui-arrow.png")', 'url("/art/ui-key.png")']);
    for (const length of ["--arrow-w", "--arrow-h", "--key-w", "--key-h"]) {
      expect([length, /^[1-9]\d*$/.test(handed(length))]).toEqual([length, true]);
    }
  });

  test("test_apart_each_list_stands_in_a_box_of_its_own_and_together_all_stand_in_the_box_of_the_portrait", () => {
    const data = profile(SLUGS[0] ?? "");
    const drawn = (lists: "apart" | "together") => {
      const view = render(<Portrait data={data} meta={meta} lists={lists} />);
      const whole = screen.getByRole("region", { name: PORTRAIT.title });
      const found = {
        whole: whole.getAttribute("data-kind"),
        parts: [...whole.children].map((part) => [part.tagName, part.getAttribute("role"), part.getAttribute("data-kind")]),
        said: whole.textContent,
      };
      view.unmount();
      return found;
    };
    const lists = portraitOf(data, meta);
    const groups = GROUPS.filter((group) => lists[group].length > 0);

    const apart = drawn("apart");
    const together = drawn("together");

    // What it is like and where it is, with what is said of the lists at its foot, then each list.
    expect(apart.whole).toBeNull();
    expect(apart.parts).toEqual([["DIV", null, "box"], ...groups.map(() => ["DIV", "group", "box"])]);
    expect(together.whole).toBe("box");
    expect(together.parts).toEqual([["DIV", null, null], ...groups.map(() => ["DIV", "group", null])]);
    // It says the same either way, in the same order.
    expect(apart.said === together.said).toBe(true);
    expect(groups.length).toBeGreaterThan(2);
  });

  test("test_what_is_said_of_the_lists_stands_once_at_the_foot_of_what_opens_the_portrait", () => {
    const data = profile(SLUGS[0] ?? "");
    for (const lists of ["apart", "together"] as const) {
      const { unmount } = render(<Portrait data={data} meta={meta} lists={lists} />);
      const said = screen.getByText(PORTRAIT.lead);
      const whole = screen.getByRole("region", { name: PORTRAIT.title });

      // It is a paragraph of the part that holds the heading, and the last thing in it.
      expect([lists, said.tagName, said.parentElement?.parentElement === whole]).toEqual([lists, "P", true]);
      expect([lists, said.parentElement?.lastElementChild === said]).toEqual([lists, true]);
      expect([lists, said.parentElement?.querySelector("h2")?.textContent]).toEqual([lists, PORTRAIT.title]);
      // Every list comes after it, for the eye and for whoever hears the page.
      for (const list of within(whole).getAllByRole("group")) {
        if (list.parentElement !== whole) continue;
        expect([lists, Boolean(said.compareDocumentPosition(list) & Node.DOCUMENT_POSITION_FOLLOWING)]).toEqual([lists, true]);
      }
      unmount();
    }
  });

  test("test_every_rule_of_the_portrait_is_solid_and_none_is_drawn_in_dashes_or_in_dots", () => {
    // A person who walked the website did not know what a dashed edge was for. What is
    // said of the lists, and what starts a search from a list, each stood under a dashed rule.
    const written = readFileSync(path.join(__dirname, "Portrait.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
    const rules = rulesOf(written);
    const under = (selector: string) =>
      rules.filter((rule) => rule.under === null && rule.selector === selector).map((rule) => rule.sets.get("border-block-start"));

    expect(/dashed|dotted|repeating-linear-gradient/.test(written)).toBe(false);
    expect([under(".lead"), under(".under")]).toEqual([["var(--edge) solid var(--border)"], ["var(--edge) solid var(--border)"]]);
    // Every edge the portrait sets is solid, in ink or in sand, and one art pixel wide.
    const edges = rules.flatMap((rule) => [...rule.sets].filter(([property]) => /^border(-block|-inline)?(-start|-end)?$/.test(property)).map(([, value]) => value));
    expect(edges.length).toBeGreaterThan(5);
    expect(edges.filter((value) => !/^var\(--edge\) solid var\(--(border|ink|sand)\)$/.test(value))).toEqual([]);
  });

  test("test_a_page_that_hands_nothing_has_the_lists_as_the_line_that_chooses_says", () => {
    show(SLUGS[0] ?? "");

    expect(screen.getByRole("region", { name: PORTRAIT.title })).toHaveAttribute("data-lists", LISTS_STAND);
    expect(screen.getByRole("region", { name: PORTRAIT.title })).toHaveAttribute("data-things", THINGS_STAND);
  });

  test("test_the_small_drawing_of_a_vibe_stands_before_its_name_and_is_chosen_by_what_the_service_calls_the_vibe", () => {
    const data = profile(SLUGS[0] ?? "");
    const { unmount } = render(<Portrait data={data} meta={meta} things="beside" />);
    const shown = shownOn(portraitOf(data, meta));
    /** The drawing a line shows before the name of its vibe, by where it is served from. */
    const thingOf = (tagId: string) =>
      [...(lineOf(tagId)?.querySelectorAll<HTMLElement>("span:first-child [style]") ?? [])]
        .filter((one) => pictureIn(lineOf(tagId))?.contains(one) === false)
        .map((one) => one.style.getPropertyValue("--art"));

    expect(shown.length).toBeGreaterThan(8);
    for (const { tag } of shown) {
      const name = lineOf(tag.tag_id)?.querySelector(":scope > span:first-child");
      // By the id the service gives the vibe, then by its family, then the plain one: never nothing.
      const drawn = thingOf(tag.tag_id);
      expect([tag.tag_id, drawn.length]).toEqual([tag.tag_id, 1]);
      expect([tag.tag_id, /^url\("\/art\/thing-[a-z-]+\.png"\)$/.test(drawn[0] ?? "")]).toEqual([tag.tag_id, true]);
      // It is dress. The name is heard as it was, once, and the drawing says nothing.
      expect(name?.textContent).toBe(tag.label);
      expect(name?.querySelectorAll("[role='img'], [aria-label], img, svg").length).toBe(0);
      expect(name?.querySelector("[style]")?.closest("[aria-hidden='true']") === null).toBe(false);
    }
    unmount();

    // Where the look draws none, a line is its name, its steps and its words.
    render(<Portrait data={data} meta={meta} things="nowhere" />);
    for (const { tag } of shown) expect([tag.tag_id, thingOf(tag.tag_id)]).toEqual([tag.tag_id, []]);
  });

  test("test_a_vibe_the_release_gives_no_family_and_no_drawing_of_its_own_takes_the_plain_one", () => {
    const data = profile(SLUGS[0] ?? "");
    const [placed] = shownOn(portraitOf(data, meta));
    if (placed === undefined) throw new Error("The first recorded area is placed on no vibe.");
    // A vibe that is new to the website: the service names it, and nobody has drawn it.
    const renamed = "a_vibe_nobody_drew";
    const held = {
      ...meta,
      tags: meta.tags.map((tag) => (tag.tag_id === placed.tag.tag_id ? { ...tag, tag_id: renamed, family: "none" } : tag)),
    };
    const told = {
      ...data,
      portrait: Object.fromEntries(
        Object.entries(data.portrait).map(([group, marks]) => [
          group,
          marks.map((mark) => (mark.tag_id === placed.tag.tag_id ? { ...mark, tag_id: renamed } : mark)),
        ]),
      ),
    } as unknown as AreaData;
    render(<Portrait data={told} meta={held as unknown as MetaData} things="beside" />);

    const drawn = lineOf(renamed)?.querySelector<HTMLElement>(":scope > span:first-child [style]");

    expect(drawn?.style.getPropertyValue("--art")).toBe('url("/art/thing-plain.png")');
  });

  test.each(["apart", "together"] as const)("test_the_portrait_has_no_accessibility_fault_with_its_lists_%s", async (lists) => {
    const { container } = render(<Portrait data={profile(SLUGS[0] ?? "")} meta={meta} lists={lists} />);

    expect(await faultsIn(container)).toEqual([]);
  });
});
