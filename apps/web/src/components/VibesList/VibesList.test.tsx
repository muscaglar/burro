import { readFileSync } from "node:fs";
import path from "node:path";

import { cleanup, render, screen, within } from "@testing-library/react";
import { renderToStaticMarkup } from "react-dom/server";

import { CRIME_ACCOUNT, CRIME_RULE } from "@/content/crime";
import { CASE_LINES, OTHER_NAMES, type OtherName } from "@/content/names";
import { STRIP } from "@/content/search";
import { CRIME_CAVEAT } from "@/content/settings";
import { VIBES } from "@/content/vibes";
import { readRecorded, recordedAnswer } from "@/lib/api/recorded";
import type { AreaData, AreasData, GeometryData, MetaData, Metric, Tag } from "@/lib/api/schema";
import { readableDate } from "@/lib/format";
import { isRange, readingOf } from "@/lib/vibes";

import { faultsIn } from "../../../test/support/axe";
import { NAMED_AT_AN_END, VibesList } from "./VibesList";

const meta: MetaData = recordedAnswer("get_meta", "meta").body.data;
const { areas, bands }: AreasData = recordedAnswer("list_areas", "areas").body.data;
const geometry: GeometryData = recordedAnswer("get_geometry", "geometry").body.data;
/** The release where gritty is built the other way: as one part of a place, which runs one way. */
const variantA: MetaData = (readRecorded("variant-a/meta").body as { data: MetaData }).data;

/** The contract, as it is written, with each run of space as one. */
const contract = () =>
  readFileSync(path.resolve(__dirname, "../../../../../docs/design/contract.md"), "utf8").replace(/[ \t]+/g, " ");

/** The same answer, as a real release might give it: other sources and other periods. */
function realLooking(): MetaData {
  const sources = [
    { ...meta.attributions[0]!, source_id: "open-greenspace", name: "Open Greenspace" },
    { ...meta.attributions[0]!, source_id: "price-paid", name: "Price Paid" },
  ];
  const features = meta.features.map(
    (metric, at): Metric => ({
      ...metric,
      source_ids: at % 2 === 0 ? ["open-greenspace"] : ["open-greenspace", "price-paid"],
      vintage: at % 3 === 0 ? "2024-10 to 2026-09" : metric.vintage,
    }),
  );
  return { ...meta, synthetic: false, attributions: sources, features };
}

const show = (given: MetaData = meta, names?: Readonly<Record<string, readonly OtherName[]>>) =>
  render(<VibesList meta={given} areas={areas} bands={bands} geometry={geometry} names={names} />);

/** What a cell says, without the name of its column, which it says only where the rows are stacked. */
const said = (cell: HTMLElement | undefined) => cell?.lastElementChild?.textContent ?? "";

const vibe = (tagId: string) => {
  const found = document.getElementById(tagId);
  if (found === null) throw new Error("The page holds no such vibe.");
  return found;
};
const ends = (tag: Tag): readonly [string, string] => [tag.low_end ?? STRIP.least, tag.high_end ?? STRIP.most];
const nameOf = (areaId: string) => areas.find((area) => area.area_id === areaId)?.name ?? "";
/** The areas a vibe places in a band, in the order the API gives them. A mixed area is at no one band. */
const inBand = (tagId: string, band: number | null) =>
  (bands.find((one) => one.tag_id === tagId)?.marks ?? [])
    .filter((mark) => mark.band === band && (mark.spread_high ?? 0) - (mark.spread_low ?? 0) < 2)
    .map((mark) => nameOf(mark.area_id));

describe("the page of vibes", () => {
  test("test_every_vibe_of_the_release_is_listed_once_in_the_order_the_api_gives", () => {
    show();

    const names = screen.getAllByRole("heading", { level: 2 }).map((heading) => heading.textContent);

    // Every vibe, and then how an area is placed on one.
    expect(names).toEqual([...meta.tags.map((tag) => tag.label), VIBES.how.title]);
    // The thirteen, and the one way gritty is built in this release.
    expect(meta.tags).toHaveLength(14);
  });

  test("test_each_vibe_can_be_reached_from_the_list_at_the_head_of_the_page", () => {
    show();

    const links = within(screen.getByRole("navigation", { name: VIBES.contents })).getAllByRole("link");

    expect(links.map((link) => [link.textContent, link.getAttribute("href")])).toEqual(
      meta.tags.map((tag) => [tag.label, `#${tag.tag_id}`]),
    );
    for (const link of links) {
      expect(vibe((link.getAttribute("href") ?? "").slice(1))).toBeInTheDocument();
      expect(link).toHaveClass("target-min");
    }
  });

  test("test_every_vibe_says_what_it_means_names_its_ends_and_says_what_it_cannot_see", () => {
    show();

    for (const tag of meta.tags) {
      const part = vibe(tag.tag_id);
      expect(part).toHaveTextContent(tag.meaning);
      expect(part).toHaveTextContent(
        tag.shape === "scale" ? VIBES.scale(tag.low_end ?? "", tag.high_end ?? "") : VIBES.oneWay,
      );
      // Every line, word for word, and in the API's order.
      const lines = [...(part.querySelector(`[aria-label="${VIBES.cannotSee}"]`)?.querySelectorAll("li") ?? [])];
      expect(lines.map((line) => line.textContent)).toEqual(tag.cannot_see);
    }
    // Every vibe says first that an area is many streets.
    expect(new Set(meta.tags.map((tag) => tag.cannot_see[0]))).toEqual(
      new Set(["One street or one home. An area is many streets."]),
    );
  });

  test("test_the_page_can_never_disagree_with_the_engine_because_it_holds_no_vibe_of_its_own", () => {
    show();
    // Gritty is one vibe. Works and warehouses is a part of it, and no vibe of its own.
    expect(screen.getByRole("heading", { level: 2, name: "Gritty" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { level: 2, name: "Works and warehouses" })).toBeNull();
    cleanup();

    // Built on a release that holds no recorded crime, it lists every vibe but Gritty.
    show(variantA);

    expect(screen.getByRole("heading", { level: 2, name: "Works and warehouses" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { level: 2, name: "Gritty" })).toBeNull();
    expect(vibe("works_warehouses")).toHaveTextContent(VIBES.oneWay);
    // A release with no vibe lists none, and says nothing of any.
    cleanup();
    show({ ...meta, tags: [] });
    expect(screen.getAllByRole("heading", { level: 2 }).map((heading) => heading.textContent)).toEqual([
      VIBES.how.title,
    ]);
  });

  test("test_a_vibe_that_counts_who_lived_somewhere_says_so_and_no_other_vibe_counts_them", () => {
    // Every part of every recipe is of a place, its buildings or what was recorded there,
    // but for the one part of each of the two vibes that count who lived there.
    const of = (featureId: string) => meta.features.find((one) => one.feature_id === featureId)?.describes;
    const counting = meta.tags.filter((tag) => tag.terms.some((term) => of(term.feature_id) === "residents"));
    show();

    expect(counting.map((tag) => tag.tag_id)).toEqual(["family_area", "young_professionals"]);
    for (const tag of counting) {
      const counted = tag.terms.filter((term) => of(term.feature_id) === "residents");
      // One part of it, read from its high end, and four in ten of it at most.
      expect(counted.map((term) => [term.reading, term.hundredths <= 40])).toEqual([["high", true]]);
      expect(tag.shape).toBe("one_way");
      // Its own words say which census, and the page draws them as they came.
      expect(tag.meaning).toContain("Census 2021");
      expect(tag.meaning).toContain("It counts who lived there beside what is there");
      expect(vibe(tag.tag_id)).toHaveTextContent(tag.meaning);
      expect(vibe(tag.tag_id)).toHaveTextContent(VIBES.oneWay);
    }
    const parts = new Set(
      meta.tags.filter((tag) => !counting.includes(tag)).flatMap((tag) => tag.terms.map((term) => term.feature_id)),
    );
    const described = meta.features.filter((metric) => parts.has(metric.feature_id)).map((metric) => metric.describes);

    expect(new Set(described)).toEqual(new Set(["place", "buildings", "events"]));
    // Only the one vibe that is built two ways holds a part of what was recorded.
    const recorded = meta.tags.filter((tag) =>
      tag.terms.some((term) => meta.features.find((one) => one.feature_id === term.feature_id)?.describes === "events"),
    );
    expect(recorded.map((tag) => tag.tag_id)).toEqual(["street_character"]);
  });
});

describe("every vibe at a glance", () => {
  const glance = () => screen.getByRole("navigation", { name: VIBES.contents });

  test("test_the_head_of_the_page_sets_the_city_coloured_by_each_vibe_side_by_side", () => {
    show();

    const items = within(glance()).getAllByRole("listitem");

    expect(items).toHaveLength(meta.tags.length);
    meta.tags.forEach((tag, at) => {
      const item = items[at] as HTMLElement;
      const [low, high] = ends(tag);
      // The city coloured by the vibe, its name, and the two ends its bands run between.
      const picture = item.querySelector("svg");
      const marks = bands.find((one) => one.tag_id === tag.tag_id)?.marks ?? [];
      for (const mark of marks) {
        expect(picture?.querySelector(`[data-area="${mark.area_id}"]`)?.getAttribute("data-band")).toBe(
          mark.band === null ? "none" : String(mark.band),
        );
      }
      expect(within(item).getByRole("link")).toHaveTextContent(tag.label);
      expect(item.textContent?.includes(VIBES.glance.ends(low, high))).toBe(true);
    });
  });

  test("test_each_small_map_is_a_picture_for_the_eye_and_the_map_of_the_vibe_itself_is_the_one_that_is_named", () => {
    show();

    // A screen reader hears the name of each vibe once in the list, and finds its map by its name below.
    for (const picture of glance().querySelectorAll("svg")) {
      expect(picture).toHaveAttribute("aria-hidden", "true");
      expect(picture.querySelector("title")).toBeNull();
    }
    expect(within(glance()).queryAllByRole("img")).toEqual([]);
    expect(screen.getAllByRole("img")).toHaveLength(meta.tags.length);
  });

  test("test_which_way_the_colours_run_is_said_once_over_the_maps", () => {
    show();

    expect(glance().textContent?.split(VIBES.glance.lead)).toHaveLength(2);
    expect(VIBES.glance.lead).toContain("darker");
  });

  test("test_with_no_map_to_draw_the_list_is_the_names_of_the_vibes_and_no_more", () => {
    render(<VibesList meta={meta} />);

    expect(glance().querySelectorAll("svg")).toHaveLength(0);
    expect(within(glance()).getAllByRole("link").map((link) => link.textContent)).toEqual(
      meta.tags.map((tag) => tag.label),
    );
  });
});

describe("one vibe beside the next", () => {
  test("test_every_vibe_holds_the_same_parts_in_the_same_order_so_that_one_is_read_against_the_next", () => {
    show();

    const shape = (tagId: string) => [...vibe(tagId).querySelectorAll("h3")].map((heading) => heading.textContent);

    const first = shape(meta.tags[0]?.tag_id ?? "");
    expect(first).toEqual([VIBES.found.title, VIBES.recipe.title, VIBES.cannotSee]);
    for (const tag of meta.tags) expect(shape(tag.tag_id)).toEqual(first);
    // The map of each stands before its words, under its name and what it means.
    for (const tag of meta.tags) {
      const part = vibe(tag.tag_id);
      const picture = within(part).getByRole("img");
      const found = within(part).getByRole("heading", { level: 3, name: VIBES.found.title });
      expect(picture.compareDocumentPosition(found) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    }
  });

  test("test_a_vibe_has_as_many_parts_as_the_rows_it_is_laid_out_in", () => {
    // Seen in a browser: a line was added to every vibe and not to the count of its rows, and
    // the last two parts of each were drawn on top of each other.
    const css = readFileSync(path.resolve(__dirname, "VibesList.module.css"), "utf8");
    const rows = Number(/\.vibe \{\s*grid-row: span (\d+);/.exec(css)?.[1]);
    const preview: MetaData = recordedAnswer("get_meta", "preview/meta").body.data;

    for (const given of [meta, preview, variantA]) {
      cleanup();
      show(given);
      for (const tag of given.tags) {
        // The map and where the vibe is found stand side by side, in one row.
        expect(vibe(tag.tag_id).children.length - 1).toBe(rows);
      }
    }
  });

  test("test_each_vibe_has_the_map_of_the_city_coloured_by_it_in_the_bands_the_api_gives", () => {
    show();

    for (const tag of meta.tags) {
      const [low, high] = ends(tag);
      const picture = within(vibe(tag.tag_id)).getByRole("img", { name: VIBES.map.title(tag.label, low, high) });
      const marks = bands.find((one) => one.tag_id === tag.tag_id)?.marks ?? [];
      expect(marks).toHaveLength(areas.length);
      for (const mark of marks) {
        const drawn = picture.querySelector(`[data-area="${mark.area_id}"]`);
        expect(drawn?.getAttribute("data-band")).toBe(mark.band === null ? "none" : String(mark.band));
      }
      // Under the map, in words: which way the colours run, and by the names of its two ends.
      expect(vibe(tag.tag_id)).toHaveTextContent(VIBES.map.runs(low, high));
    }
  });

  test("test_a_scale_names_both_its_ends_and_the_areas_at_each", () => {
    show();
    const pace = meta.tags.find((tag) => tag.tag_id === "pace") as Tag;
    const part = vibe("pace");

    const high = within(part).getByRole("group", { name: VIBES.found.end("Buzzy") });
    const low = within(part).getByRole("group", { name: VIBES.found.end("Calm") });

    expect([pace.low_end, pace.high_end]).toEqual(["Calm", "Buzzy"]);
    expect(within(high).getAllByRole("link").map((link) => link.textContent)).toEqual(inBand("pace", 5));
    expect(within(low).getAllByRole("link").map((link) => link.textContent)).toEqual(inBand("pace", 1));
    expect(inBand("pace", 5)).toContain("Pellam Cross");
    // The high end is said first, as the vibe is named for it, and then the low.
    expect(high.compareDocumentPosition(low) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  test("test_a_vibe_that_runs_one_way_names_the_areas_with_most_of_it_and_with_least", () => {
    show();
    const part = vibe("leafy");

    const most = within(part).getByRole("group", { name: VIBES.found.most });
    const least = within(part).getByRole("group", { name: VIBES.found.least });

    expect(within(most).getAllByRole("link").map((link) => link.textContent)).toEqual(inBand("leafy", 5));
    expect(within(least).getAllByRole("link").map((link) => link.textContent)).toEqual(inBand("leafy", 1));
  });

  test("test_every_area_named_is_one_press_from_its_page_and_is_not_fetched_ahead_of_time", () => {
    show();

    const links = [...document.querySelectorAll<HTMLAnchorElement>("a[href^='/synthetic/']")];

    expect(links.length).toBeGreaterThan(50);
    for (const link of links) {
      const area = areas.find((one) => `/synthetic/${one.slug}` === link.getAttribute("href"));
      expect(link.textContent).toBe(area?.name);
      expect(link).toHaveAttribute("data-prefetch", "false");
      expect(link).toHaveClass("target-min");
    }
  });

  test("test_an_area_the_vibe_cannot_place_is_named_as_that_and_is_at_neither_end", () => {
    show();
    const part = vibe("leafy");
    const unplaced = inBand("leafy", null);

    const group = within(part).getByRole("group", { name: VIBES.found.unplaced, hidden: true });

    expect(unplaced.length).toBeGreaterThan(0);
    expect(within(group).getAllByRole("link", { hidden: true }).map((link) => link.textContent)).toEqual(unplaced);
    for (const end of [VIBES.found.most, VIBES.found.least]) {
      const named = within(within(part).getByRole("group", { name: end })).getAllByRole("link");
      expect(named.filter((link) => unplaced.includes(link.textContent ?? ""))).toEqual([]);
    }
    expect(part).toHaveTextContent(VIBES.map.notPlaced);
  });

  test("test_every_area_is_in_one_band_or_none_and_a_mixed_area_is_at_no_one_end", () => {
    show();

    for (const tag of meta.tags) {
      const all = within(vibe(tag.tag_id)).getByRole("group", { name: VIBES.found.every, hidden: true });
      const named = within(all).getAllByRole("link", { hidden: true }).map((link) => link.textContent);
      expect([...named].sort()).toEqual(areas.map((area) => area.name).sort());
    }
    // Foxholt spans bands 3 to 5 on Going out: it is not said to sit at the Buzzy end.
    const mixed = bands.find((one) => one.tag_id === "pace")?.marks.find((mark) => nameOf(mark.area_id) === "Foxholt");
    expect([mixed?.spread_low, mixed?.spread_high]).toEqual([3, 5]);
    const buzzy = within(vibe("pace")).getByRole("group", { name: VIBES.found.end("Buzzy") });
    expect(within(buzzy).queryByRole("link", { name: "Foxholt" })).toBeNull();
  });

  test("test_no_vibe_is_shown_as_a_percentage_a_score_or_a_rank", () => {
    show();

    for (const tag of meta.tags) {
      const text = [...vibe(tag.tag_id).querySelectorAll("h2, h3, p, figcaption, a")]
        .map((one) => one.textContent ?? "")
        .filter((words) => words !== tag.meaning)
        .join(" ");
      expect(/%|percent|score|\brank/i.test(text)).toBe(false);
    }
  });
});

describe("the recipe of a vibe", () => {
  test("test_the_recipe_is_drawn_in_short_with_the_share_of_each_part_and_how_it_is_read", () => {
    show();
    const labels = new Map(meta.features.map((metric) => [metric.feature_id, metric.label]));
    // A part the release does not carry is named as the API names it, and said to be missing.
    const waited = new Map(
      meta.recipes.flatMap((held) => held.waits_on.map((part) => [part.feature_id, part.label] as const)),
    );
    expect(waited.size).toBe(4);

    for (const tag of meta.tags) {
      const parts = [...(vibe(tag.tag_id).querySelector(`[aria-label="${VIBES.recipe.caption(tag.label)}"]`)?.querySelectorAll("li") ?? [])];
      expect(parts).toHaveLength(tag.terms.length);
      tag.terms.forEach((term, at) => {
        const carried = labels.get(term.feature_id);
        expect(parts[at]?.textContent?.includes(carried ?? waited.get(term.feature_id) ?? "no name")).toBe(true);
        expect(parts[at]?.textContent?.includes(VIBES.recipe.waits)).toBe(carried === undefined);
        // It is never shown as a part with no name, nor by its code.
        expect(parts[at]?.textContent?.includes(VIBES.recipe.notCarried)).toBe(false);
        expect(parts[at]?.textContent?.includes(VIBES.recipe.share(term.hundredths))).toBe(true);
        expect(parts[at]?.textContent?.includes(readingOf(tag, term.reading))).toBe(true);
      });
      expect(tag.terms.reduce((sum, term) => sum + term.hundredths, 0)).toBe(100);
    }
    for (const code of ["gp_walk", "pharmacy_walk", "cuisine_variety", "private_outdoor_space"]) {
      expect(document.body.textContent?.includes(code)).toBe(false);
    }
  });

  test("test_a_part_that_other_recipes_hold_says_which", () => {
    show();
    const part = (tagId: string, label: string) =>
      [...(vibe(tagId).querySelector(`[aria-label^="What"]`)?.querySelectorAll("li") ?? [])].find((one) =>
        one.textContent?.includes(label),
      );

    // Homes built before 1919 is a part of Village feel and of Age of buildings.
    expect(part("village_feel", "Homes built before 1919")).toHaveTextContent(VIBES.recipe.alsoIn("Age of buildings"));
    expect(part("built_age", "Homes built before 1919")).toHaveTextContent(VIBES.recipe.alsoIn("Village feel"));
    // Land that is residential garden is a part of Leafy alone.
    expect(part("leafy", "Land that is residential garden")?.textContent?.includes("Also a part of")).toBe(false);
  });

  test("test_the_period_and_the_source_of_each_part_are_one_press_away_as_the_release_states_them", () => {
    const real = realLooking();
    show(real);

    for (const tag of real.tags) {
      const table = within(vibe(tag.tag_id)).getByRole("table", { name: VIBES.recipe.caption(tag.label), hidden: true });
      expect(table.closest("details")?.querySelector("summary")).toHaveTextContent(VIBES.detail);
      const rows = within(table).getAllByRole("row", { hidden: true }).slice(1);
      tag.terms.forEach((term, at) => {
        const metric = real.features.find((one) => one.feature_id === term.feature_id);
        const cells = within(rows[at] as HTMLElement).getAllByRole("cell", { hidden: true });
        expect(said(cells[0])).toBe(readingOf(tag, term.reading));
        expect(said(cells[1])).toBe(`${term.hundredths} ${VIBES.recipe.shareOf}`);
        if (metric === undefined) {
          // Nothing is filled in for a part this data does not carry.
          expect(cells[2]).toHaveTextContent(VIBES.recipe.noPeriod);
          expect(within(cells[3] as HTMLElement).queryByRole("link", { hidden: true })).toBeNull();
          return;
        }
        // The period is the release's, written as every other date on the website is.
        expect(said(cells[2])).toBe(readableDate(metric.vintage));
        expect(
          within(cells[3] as HTMLElement)
            .getAllByRole("link", { hidden: true })
            .map((link) => link.getAttribute("href")),
        ).toEqual(metric.source_ids.map((id) => `/sources#${id}`));
      });
    }
  });

  test("test_the_sources_of_a_vibe_are_the_sources_of_its_parts_each_named_once", () => {
    const real = realLooking();
    show(real);

    for (const tag of real.tags) {
      const ids = new Set(
        tag.terms.flatMap((term) => real.features.find((one) => one.feature_id === term.feature_id)?.source_ids ?? []),
      );
      const listed = within(vibe(tag.tag_id).querySelector(`[aria-label="${VIBES.sources}"]`) as HTMLElement).getAllByRole(
        "link",
        { hidden: true },
      );

      expect(listed.map((link) => link.getAttribute("href")).sort()).toEqual([...ids].map((id) => `/sources#${id}`).sort());
      for (const link of listed) {
        expect(link).toHaveAttribute("data-prefetch", "false");
        expect(["Open Greenspace", "Price Paid"]).toContain(link.textContent);
      }
    }
  });

  test("test_every_part_of_a_recipe_says_its_role_so_that_it_stays_a_table_when_stacked", () => {
    show();

    const tables = screen.getAllByRole("table", { hidden: true });
    expect(tables).toHaveLength(meta.tags.length);
    for (const table of tables) {
      expect(table).toHaveAttribute("role", "table");
      for (const row of table.querySelectorAll("tr")) expect(row).toHaveAttribute("role", "row");
      for (const header of table.querySelectorAll("thead th")) expect(header).toHaveAttribute("role", "columnheader");
      for (const header of table.querySelectorAll("tbody th")) expect(header).toHaveAttribute("role", "rowheader");
      const names = [...table.querySelectorAll("thead th")].map((header) => header.textContent);
      for (const row of table.querySelectorAll("tbody tr")) {
        const cells = [...row.querySelectorAll("td")];
        for (const cell of cells) expect(cell).toHaveAttribute("role", "cell");
        // Stacked, each cell says what it is of, for the eye. The column says it to a reader.
        expect(cells.map((cell) => cell.querySelector("[aria-hidden='true']")?.textContent)).toEqual(names.slice(1));
      }
    }
  });
});

describe("room for the case for other names", () => {
  const weighed: Readonly<Record<string, readonly OtherName[]>> = {
    pace: [
      { name: "Pace", lines: ["It is one word.", "It names no end.", "It was the name of the recipe."] },
      { name: "Bustle", lines: ["One word."] },
    ],
    no_such_vibe: [{ name: "Nothing", lines: ["It is of no vibe of this data."] }],
  };

  test("test_the_names_weighed_for_a_vibe_stand_under_its_name_each_with_its_case", () => {
    show(meta, weighed);
    const part = vibe("pace");

    const room = within(part).getByRole("group", { name: VIBES.names.title });

    expect(within(room).getAllByRole("term").map((term) => term.textContent)).toEqual(["Pace", "Bustle"]);
    expect(room).toHaveTextContent("It is one word.");
    // It stands under the name, before what the vibe means.
    const name = within(part).getByRole("heading", { level: 2 });
    expect(name.compareDocumentPosition(room) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(room.compareDocumentPosition(screen.getAllByText(meta.tags[2]?.meaning ?? "")[0] as HTMLElement) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  test("test_a_case_is_three_lines_at_most", () => {
    const long = { pace: [{ name: "Pace", lines: ["One.", "Two.", "Three.", "Four."] }] };
    show(meta, long);

    const room = within(vibe("pace")).getByRole("group", { name: VIBES.names.title });

    expect(CASE_LINES).toBe(3);
    expect(within(room).getAllByRole("definition")[0]?.querySelectorAll("p")).toHaveLength(3);
    expect(room.textContent?.includes("Four.")).toBe(false);
  });

  test("test_a_vibe_with_no_other_name_weighed_draws_no_empty_room_and_a_name_for_no_vibe_is_not_drawn", () => {
    show(meta, weighed);

    expect(within(vibe("leafy")).queryByRole("group", { name: VIBES.names.title })).toBeNull();
    expect(document.body.textContent?.includes("It is of no vibe of this data.")).toBe(false);
  });

  test("test_the_name_the_engine_gives_is_the_name_of_the_vibe_whatever_is_weighed", () => {
    show(meta, weighed);

    expect(within(vibe("pace")).getByRole("heading", { level: 2 })).toHaveTextContent("Going out");
    expect(screen.queryByRole("heading", { name: "Pace" })).toBeNull();
  });

  test("test_no_name_is_set_down_until_the_cases_are_written", () => {
    // The room is there. What stands in it is the founder's to choose.
    expect(Object.keys(OTHER_NAMES).filter((id) => !meta.tags.some((tag) => tag.tag_id === id))).toEqual([]);
    for (const names of Object.values(OTHER_NAMES)) {
      for (const one of names) expect(one.lines.length).toBeLessThanOrEqual(CASE_LINES);
    }
  });
});

describe("a vibe that counts recorded crime", () => {
  test("test_it_says_so_on_its_face_with_the_one_account_of_when_recorded_crime_counts", () => {
    show();
    const part = vibe("street_character");

    expect(part).toHaveTextContent(CRIME_ACCOUNT.counts);
    expect(part).toHaveTextContent("Recorded criminal damage");
    expect(part).toHaveTextContent("Recorded anti-social behaviour");
    expect(part).toHaveTextContent(CRIME_RULE);
    expect(part).toHaveTextContent(CRIME_ACCOUNT.asking);
    // With the caveat of every figure of recorded crime, word for word as the contract has it.
    expect(part).toHaveTextContent(CRIME_CAVEAT);
    expect(contract()).toContain(CRIME_CAVEAT);
  });

  test("test_no_other_vibe_says_it_and_built_the_other_way_no_vibe_does", () => {
    show();
    for (const tag of meta.tags.filter((one) => one.tag_id !== "street_character")) {
      expect(vibe(tag.tag_id).textContent?.includes(CRIME_ACCOUNT.counts)).toBe(false);
    }
    cleanup();

    show(variantA);

    expect(document.body.textContent?.includes(CRIME_ACCOUNT.counts)).toBe(false);
    expect(/\b(safe|safer|unsafe|dangerous|rough)\b/i.test(document.body.textContent ?? "")).toBe(false);
  });
});

describe("how an area is placed on a vibe", () => {
  test("test_how_an_area_is_placed_is_said_as_the_contract_defines_it", () => {
    show();
    const how = screen.getByRole("region", { name: VIBES.how.title });

    expect(contract()).toContain("If `coverage < 0.6` then `raw`, `score` and `band` are null");
    expect(how).toHaveTextContent("parts that carry 60 of the 100 shares");
    expect(contract()).toContain("where an area sits among the same population, in fifths");
    expect(how).toHaveTextContent("in fifths");
    expect(contract()).toContain("Areas that are level share a band.");
    expect(how).toHaveTextContent("Areas that are level share a band.");
    expect(contract()).toContain("The recipe is Burro's own. The weights are a judgement.");
    expect(how).toHaveTextContent("The recipe is Burro's own, and the weights are a judgement.");
    // The one number the page states for itself is the 60, with the 100 and the five bands it is said of.
    expect((VIBES.how.points.join(" ").match(/\d+/g) ?? []).sort()).toEqual(["1", "100", "100", "5", "60"].sort());
  });

  test("test_a_mixed_area_is_said_to_span_three_bands_as_the_engine_counts_them", () => {
    show();
    const how = screen.getByRole("region", { name: VIBES.how.title });

    // The engine draws a range where the spread is three bands or more: bands 3 to 5 is one.
    expect(contract()).toContain("Used where the spread is three bands or more");
    expect(how.textContent?.includes("span three bands or more")).toBe(true);
    // Two bands that are three apart span four. The page once said "three bands apart".
    expect(how.textContent?.includes("bands apart")).toBe(false);
    // It is the homes of an area that differ, and never the parts of a recipe.
    expect(how.textContent?.includes("parts of one area")).toBe(false);
    expect(isRange({ band: 4, spread_low: 3, spread_high: 5 })).toBe(true);
    expect(isRange({ band: 4, spread_low: 4, spread_high: 5 })).toBe(false);
    // The release holds such an area, and its fact says so in the engine's own template.
    const mixed: AreaData = (readRecorded("area/foxholt").body as { data: AreaData }).data;
    const pace = mixed.facts.find((fact) => fact.kind === "tag" && fact.key === "pace");
    expect(pace?.template).toBe("vibe_range");
    expect([pace?.slots.spread_low, pace?.slots.spread_high]).toEqual(["3", "5"]);
  });
});

describe("the page of vibes, on data that is not finished", () => {
  const preview: MetaData = recordedAnswer("get_meta", "preview/meta").body.data;
  const listed: AreasData = recordedAnswer("list_areas", "preview/areas").body.data;
  const drawn = () =>
    render(<VibesList meta={preview} areas={listed.areas} bands={listed.bands} geometry={geometry} />);
  const placed = preview.recipes.filter((held) => held.placed).map((held) => held.tag_id);

  test("test_a_vibe_no_area_is_placed_on_has_no_map_and_names_no_area", () => {
    // Seen on a release of a thousand areas: eight of eleven vibes each named every area
    // under "Burro cannot place", over a map of dots. The page was 44 MB.
    drawn();

    expect(placed).toEqual(["quiet_residential", "parks_close_by", "homes"]);
    for (const tag of preview.tags) {
      const section = vibe(tag.tag_id);
      const isPlaced = placed.includes(tag.tag_id);
      expect(within(section).queryAllByRole("img")).toHaveLength(isPlaced ? 1 : 0);
      expect(section.textContent?.includes(VIBES.map.notYet)).toBe(!isPlaced);
      if (!isPlaced) {
        expect(within(section).queryAllByRole("link", { name: /./ }).filter((link) => /^\/synthetic\//.test(link.getAttribute("href") ?? ""))).toEqual([]);
        expect(section.textContent?.includes(VIBES.found.unplaced)).toBe(false);
      }
    }
    // At the head of the page a vibe with no map says why it has none.
    const glance = within(screen.getByRole("navigation", { name: VIBES.contents })).getAllByRole("listitem");
    preview.tags.forEach((tag, at) => {
      const isPlaced = placed.includes(tag.tag_id);
      expect(glance[at]?.querySelectorAll("svg")).toHaveLength(isPlaced ? 1 : 0);
      expect(glance[at]?.textContent?.includes(VIBES.notYet)).toBe(!isPlaced);
    });
  });

  test("test_every_vibe_says_how_much_of_its_recipe_is_held_as_one_number_and_names_what_it_waits_on", () => {
    // Seen in a browser: "A part this data does not carry", of every part that was missing,
    // and the shares of the parts that were held were never added up.
    drawn();

    for (const held of preview.recipes) {
      const section = vibe(held.tag_id);
      expect(section.textContent?.includes(VIBES.held(held.held, held.needed))).toBe(true);
      for (const part of held.waits_on) expect(section.textContent?.includes(part.label)).toBe(true);
      expect(section.textContent?.includes(VIBES.recipe.notCarried)).toBe(false);
    }
    expect(preview.recipes.find((held) => held.tag_id === "leafy")?.held).toBe(30);
    expect(preview.recipes.find((held) => held.tag_id === "pace")?.held).toBe(0);
  });

  test("test_the_outline_of_each_area_is_in_the_page_once_however_many_maps_it_draws", () => {
    const html = renderToStaticMarkup(
      <VibesList meta={preview} areas={listed.areas} bands={listed.bands} geometry={geometry} />,
    );
    const paths = html.match(/<path [^>]*\bd="M/g) ?? [];
    const pointers = html.match(/<use /g) ?? [];

    // One outline for each area, and a pointer to it from each of the six maps.
    expect(paths).toHaveLength(geometry.features.length);
    expect(pointers).toHaveLength(geometry.features.length * placed.length * 2);
    const ids = [...html.matchAll(/ id="([^"]+)"/g)].map((found) => found[1]);
    expect(new Set(ids).size).toBe(ids.length);
    for (const found of html.matchAll(/<use [^>]*href="#([^"]+)"/g)) expect(ids).toContain(found[1]);
  });

  test("test_an_end_that_holds_more_areas_than_can_be_read_says_how_many_and_names_them_one_press_away", () => {
    const many = Array.from({ length: 40 }, (_, at) => ({
      area_id: `syn-n9${String(at).padStart(3, "0")}`,
      slug: `made-up-${at}`,
      name: `Made up ${at}`,
    }));
    const marks = many.map((area) => ({ area_id: area.area_id, band: 5, spread_low: 5, spread_high: 5 }));
    render(
      <VibesList
        meta={{ ...meta, tags: meta.tags.slice(0, 1) }}
        areas={many}
        bands={[{ tag_id: meta.tags[0]!.tag_id, marks }]}
      />,
    );
    const section = vibe(meta.tags[0]!.tag_id);
    const most = section.querySelector(`#${meta.tags[0]!.tag_id}-high`)?.parentElement;

    expect(NAMED_AT_AN_END).toBeLessThan(many.length);
    expect(most?.textContent?.includes(VIBES.found.many(many.length))).toBe(true);
    expect(most?.querySelectorAll("a")).toHaveLength(0);
    // Every one of them is named in its band, which is closed until it is pressed.
    const every = section.querySelector("details");
    expect(every?.open).toBe(false);
    expect(every?.querySelectorAll("a")).toHaveLength(many.length);
  });

  test("test_the_page_has_no_accessibility_fault_on_such_data", async () => {
    const { container } = render(
      <main>
        <h1>{VIBES.title}</h1>
        <VibesList meta={preview} areas={listed.areas} bands={listed.bands} geometry={geometry} />
      </main>,
    );

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });
});

describe("the page of vibes, with scripts off and to a screen reader", () => {
  test("test_the_page_reads_with_scripts_off_and_what_opens_is_the_browsers_own", () => {
    const html = renderToStaticMarkup(<VibesList meta={meta} areas={areas} bands={bands} geometry={geometry} />);
    show();

    // What is one press away is the browser's own element, closed at first, and in the page.
    expect(html).not.toMatch(/<button|aria-expanded|onclick/i);
    expect([...document.querySelectorAll("details")].filter((part) => part.open)).toEqual([]);
    for (const opens of document.querySelectorAll("details > summary")) expect(opens).toHaveClass("target-min");
    for (const tag of meta.tags) expect(html).toContain(`id="${tag.tag_id}"`);
    expect(html).toContain("Land that is residential garden");
  });

  test("test_without_the_bands_or_the_boundaries_every_vibe_is_still_said_in_words", () => {
    render(<VibesList meta={meta} />);

    for (const tag of meta.tags) {
      expect(vibe(tag.tag_id)).toHaveTextContent(tag.meaning);
      expect(vibe(tag.tag_id)).toHaveTextContent(VIBES.map.none);
      expect(within(vibe(tag.tag_id)).queryByRole("img")).toBeNull();
    }
  });

  test("test_the_page_has_no_accessibility_fault", async () => {
    const { container } = render(
      <main>
        <h1>{VIBES.title}</h1>
        <VibesList meta={realLooking()} areas={areas} bands={bands} geometry={geometry} names={{ pace: [{ name: "Pace", lines: ["It says what is counted."] }] }} />
      </main>,
    );

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });
});
