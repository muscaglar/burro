import { readdirSync } from "node:fs";
import path from "node:path";

import { render, screen, within } from "@testing-library/react";
import { renderToStaticMarkup } from "react-dom/server";

import { PORTRAIT } from "@/content/area";
import { BAND_ONE_WAY, RESTS_ON } from "@/content/bands";
import { CRIME_ACCOUNT, CRIME_RULE } from "@/content/crime";
import { CANNOT_PLACE, FACT_COLUMNS } from "@/content/facts";
import { READING } from "@/content/labels";
import { SOURCE, STRIP } from "@/content/search";
import { CRIME_CAVEAT } from "@/content/settings";
import { readRecorded, recordedAnswer, recordedFolder } from "@/lib/api/recorded";
import type { AreaData, MetaData } from "@/lib/api/schema";
import { GROUPS, inShort, portraitOf, restsOn, shownOn, type Group, type MarkRow } from "@/lib/area/portrait";
import { readableDate } from "@/lib/format";
import { plainly } from "@/lib/vibes";

import { faultsIn } from "../../../test/support/axe";
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

function show(slug: string) {
  const data = profile(slug);
  const view = render(<Portrait data={data} meta={meta} />);
  return { data, portrait: portraitOf(data, meta), ...view };
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
      const picture = line(tag.label).querySelector("[aria-hidden='true']");
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
    expect(lines()).toHaveLength(11);
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

    expect(line("Going out")).toHaveTextContent("varies within this area, from band 3 to band 5 of 5");
    expect(filled("Going out")).toEqual([false, false, true, true, true]);
    expect(line("Going out").querySelector("[data-range='true']")).not.toBeNull();
    // Never a point in the middle.
    expect(line("Going out")).not.toHaveTextContent("band 4 of 5");
  });

  test("test_a_scale_names_both_its_ends_and_a_vibe_that_runs_one_way_runs_from_least_to_most", () => {
    show("thrushcombe");

    expect(line("Houses or flats").querySelector("[aria-hidden='true']")?.textContent).toBe("HousesFlats");
    expect(line("Leafy").querySelector("[aria-hidden='true']")?.textContent).toBe(`${STRIP.least}${STRIP.most}`);
  });

  test("test_a_figure_a_person_can_picture_stands_beside_each_vibe_of_the_lists_and_beside_no_scale", () => {
    const { portrait } = show("foxholt");

    for (const group of ["more", "less", "others"] as const) {
      for (const mark of portrait[group]) {
        expect(mark.pictured).not.toBeNull();
        expect(line(mark.tag.label).textContent?.includes(`${mark.pictured?.label}: ${mark.pictured?.slots.value}`)).toBe(true);
      }
    }
    // Food and drink is a count of places within a walk, and not a count for each square kilometre.
    expect(line("Food and drink").textContent?.includes("per km")).toBe(false);
    expect(line("Food and drink")).toHaveTextContent("Independent places to eat and drink within a 10-minute walk: 9");
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

    expect(portrait.unplaced).toHaveLength(10);
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

    expect(short()).toHaveTextContent(PORTRAIT.short.unplaced(10, 11));
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

  test("test_it_says_what_the_area_has_most_of_and_least_of_against_the_rest", () => {
    show("pellam-cross");

    const said = within(short()).getAllByRole("listitem").map((item) => item.textContent ?? "");

    expect(said.some((text) => text.includes("Everyday on foot") && text.includes("among the most here"))).toBe(true);
    expect(said.some((text) => text.includes("Leafy") && text.includes("among the least here"))).toBe(true);
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
    expect(said[0]).toHaveTextContent("Independent places to eat and drink within a 10-minute walk: 28");
    expect(said[2]).toHaveTextContent("Straight-line distance to the nearest marked way into a park of 20 ha or more: 1,420 m");
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

    expect(short().querySelectorAll("button, details, input")).toHaveLength(0);
    expect(html).toContain(PORTRAIT.short.title);
    expect(html).toContain("among the most here");
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

    // Marrowfen has no figure for transport noise: Quiet streets is placed from two parts of three.
    expect(line("Quiet streets")).toHaveTextContent(`${STRIP.band(2)}`);
    expect(line("Quiet streets").textContent?.includes(RESTS_ON.short("2", "3"))).toBe(true);
    // It is drawn where it can be seen, and not kept for a screen reader.
    const said = [...line("Quiet streets").querySelectorAll("span")].find(
      (span) => span.textContent === RESTS_ON.short("2", "3"),
    );
    expect(said?.closest(".visually-hidden")).toBeNull();
    // A band that rests on the whole of its recipe says no such thing.
    expect(line("Leafy").textContent?.includes("of its")).toBe(false);
  });

  test("test_what_the_vibe_opens_to_says_which_parts_are_missing", () => {
    render(<Portrait data={withNoClause(profile("marrowfen"))} meta={meta} />);

    const opened = vibe("Quiet streets");

    expect(opened.textContent?.includes(RESTS_ON.full("2", "3"))).toBe(true);
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
    show("thrushcombe");

    expect(line("Everyday on foot").textContent?.includes(RESTS_ON.short("3", "5"))).toBe(true);
    const said = vibe("Everyday on foot").textContent ?? "";
    expect(
      said.includes(
        `${RESTS_ON.without}: ${RESTS_ON.waits("Straight-line distance to the nearest GP practice, placed by its postcode")}; ${RESTS_ON.waits("Straight-line distance to the nearest pharmacy, placed by its postcode")}`,
      ),
    ).toBe(true);
    expect(said.includes(RESTS_ON.notCarried(2))).toBe(false);
  });

  test("test_the_summary_says_it_too", () => {
    show("thrushcombe");

    // No release carries the kinds of food nearby, so Food and drink rests on two parts of three.
    const food = within(short())
      .getAllByRole("listitem")
      .find((item) => item.textContent?.startsWith("Food and drink"));

    expect(food?.textContent?.includes(RESTS_ON.short("2", "3"))).toBe(true);
  });

  test("test_what_a_band_rests_on_is_said_in_the_apis_own_clause_where_the_fact_holds_one", () => {
    const marrowfen = profile("marrowfen");
    const clause = "Worked out from 2 of its 3 parts, 70 of 100 by weight.";
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
      (one) => one.textContent === RESTS_ON.short("2", "3") || one.textContent === RESTS_ON.full("2", "3"),
    );
    expect(own).toEqual([]);
    expect(vibe("Quiet streets").textContent?.includes(RESTS_ON.full("2", "3"))).toBe(false);
    // Which parts are missing is still said, by the names the API gives them.
    expect(vibe("Quiet streets").textContent?.includes(`${RESTS_ON.without}: Share of residents exposed to 55 dB`)).toBe(true);
    // A fact that holds no clause is said in the website's words, from the counts it does hold.
    expect(line("Houses or flats").textContent?.includes(RESTS_ON.short("2", "3"))).toBe(true);
  });

  test("test_the_apis_clause_stands_as_a_sentence_of_its_own_and_is_followed_by_one_full_stop", () => {
    const marrowfen = profile("marrowfen");
    const clause = "Worked out from 2 of its 3 parts, 70 of 100 by weight.";
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

    // It begins with a capital, so it follows a full stop, and ends in its own.
    expect(said.includes(`${STRIP.from(STRIP.least, STRIP.most)}. ${clause}`)).toBe(true);
    expect(said.includes(`, ${clause}`)).toBe(false);
    expect(/\.\s*\./.test(said)).toBe(false);
  });

  test("test_what_the_area_is_like_in_short_keeps_to_the_counts_so_that_a_line_stays_short", () => {
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

    // Both counts are the fact's own. The whole of what the API says is on the line of the vibe.
    expect(food?.textContent?.includes(RESTS_ON.short("2", "3"))).toBe(true);
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

    expect(nowhere).toHaveLength(8);
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
    expect(/\b(safe|safer|safest|unsafe|dangerous|rough|dodgy|sketchy)\b/i.test(document.body.textContent ?? "")).toBe(false);
  });
});

describe("the portrait, whichever way gritty is built", () => {
  test("test_the_way_gritty_was_built_is_a_vibe_like_any_other_and_is_named_by_the_release", () => {
    // The profile is of the release that builds it as a scale. Held against the other
    // release, the scale has no name there, and is left out: nothing is said of it.
    render(<Portrait data={profile("thrushcombe")} meta={variantA} />);

    expect(variantA.tags.map((tag) => tag.tag_id)).toContain("works_warehouses");
    expect(screen.queryByText("Gritty")).toBeNull();
    expect(vibes()).toHaveLength(10);
  });
});

describe("the portrait, by keyboard and to a screen reader", () => {
  test.each(["thrushcombe", "foxholt", "otterby-fields"])("test_the_portrait_has_no_accessibility_fault: %s", async (slug) => {
    const { container } = show(slug);

    expect(await faultsIn(container)).toEqual([]);
  });

  test("test_a_line_whose_band_rests_on_part_reads_as_two_sentences_with_the_apis_clause", () => {
    const thrushcombe = profile("thrushcombe");
    const clause = "Worked out from 2 of its 3 parts, 75 of 100 by weight.";
    const told = {
      ...thrushcombe,
      facts: thrushcombe.facts.map((fact) =>
        fact.kind === "tag" && fact.key === "homes" ? { ...fact, slots: { ...fact.slots, share: "75", partly: clause } } : fact,
      ),
    };
    render(<Portrait data={told} meta={meta} />);

    // The clause is a sentence of its own, and what the line opens follows its full stop.
    expect(line("Houses or flats").textContent).toBe(
      `Houses or flatsHousesFlatsat the Houses end, ${STRIP.band(1)}, ${STRIP.from("Houses", "Flats")}. ${clause} ${PORTRAIT.opens}`,
    );
  });

  test("test_a_line_reads_as_one_sentence_to_a_screen_reader", () => {
    render(<Portrait data={withNoClause(profile("thrushcombe"))} meta={meta} />);

    // The name, where it sits in words, the band with the way it is counted, how much of the
    // recipe the band rests on, and what the line opens.
    expect(line("Houses or flats").textContent).toBe(
      `Houses or flatsHousesFlatsat the Houses end, ${STRIP.band(1)}, ${STRIP.from("Houses", "Flats")}, ${RESTS_ON.short("2", "3")}. ${PORTRAIT.opens}`,
    );
    expect(line("Leafy").textContent).toBe(
      `Leafy${STRIP.least}${STRIP.most}on the high side here, ${STRIP.band(4)}, ${STRIP.from(STRIP.least, STRIP.most)}. Land that is residential garden: 20%. ${PORTRAIT.opens}`,
    );
  });
});
