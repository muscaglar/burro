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
import { rulesOf } from "../../../test/support/css";
import { ROUGH, sayingSo } from "../../../test/support/rough";
import { onTheGrass } from "../About/grass";
import { pictureOf } from "../kit/drawings";
import { NO_PICTURE, picturesAtEnds } from "../kit/Ends/picture";
import { drawingOf } from "../kit/Thing/drawn";
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
/** The one fold of a vibe, which holds how Burro works it out. */
const foldOf = (tagId: string) => {
  const found = vibe(tagId).querySelector<HTMLDetailsElement>(":scope > details");
  if (found === null) throw new Error("The vibe has no fold.");
  return found;
};
/** True of what stands in sight as the page is built: in no fold, and kept from nobody. */
const inSight = (element: Element | null) =>
  element !== null && element.closest("details, [hidden], .visually-hidden, [aria-hidden='true']") === null;
const ends = (tag: Tag): readonly [string, string] => [tag.low_end ?? STRIP.least, tag.high_end ?? STRIP.most];
/**
 * The band an area is drawn in on a map of the page. A map points at the outline of each
 * area, which the page draws once and which says whose it is: the pointer says its band.
 */
const bandOn = (picture: Element | null | undefined, areaId: string): string | null => {
  const outline = document.querySelector(`defs > path[data-area="${areaId}"]`);
  const pointers = picture?.querySelectorAll(`use[href="#${outline?.id ?? "no outline"}"]`) ?? [];
  // It is drawn once on each map, and never twice.
  return pointers.length === 1 ? (pointers[0]?.getAttribute("data-band") ?? null) : null;
};
const nameOf = (areaId: string) => areas.find((area) => area.area_id === areaId)?.name ?? "";
/** The areas a vibe places in a band, in the order the API gives them. A mixed area is at no one band. */
const inBand = (tagId: string, band: number | null) =>
  (bands.find((one) => one.tag_id === tagId)?.marks ?? [])
    .filter((mark) => mark.band === band && (mark.spread_high ?? 0) - (mark.spread_low ?? 0) < 2)
    .map((mark) => nameOf(mark.area_id));
/** The group of areas at an end of a vibe, by what it is called. It stands in the fold. */
const group = (tagId: string, name: string) => within(foldOf(tagId)).getByRole("group", { name, hidden: true });

describe("the page of vibes", () => {
  test("test_every_vibe_of_the_release_is_listed_once_in_the_order_the_api_gives", () => {
    show();

    const names = screen.getAllByRole("heading", { level: 3 }).map((heading) => heading.textContent);

    // Every vibe, under what is said once over them.
    expect(screen.getAllByRole("heading", { level: 2 }).map((heading) => heading.textContent)).toEqual([VIBES.each.title]);
    expect(names).toEqual(meta.tags.map((tag) => tag.label));
    // The thirteen, and the one way gritty is built in this release.
    expect(meta.tags).toHaveLength(14);
  });

  test("test_the_vibes_are_headed_by_what_is_said_over_them_and_what_a_fold_holds_by_its_vibe", () => {
    // Heard in a browser, by its headings: every vibe was of the rank of "The vibes, one by
    // one", which so headed nothing, and of the rank of the key, which no vibe belongs to.
    show();

    const ranked = [...document.querySelectorAll("h1, h2, h3, h4, h5, h6")].map(
      (heading) => [heading.tagName, heading.textContent] as const,
    );

    expect(ranked).toEqual([
      ["H2", VIBES.each.title],
      ...meta.tags.flatMap((tag) => [
        ["H3", tag.label] as const,
        ["H4", VIBES.recipe.title] as const,
        ["H4", VIBES.cannotSee.title] as const,
        ["H4", VIBES.found.title] as const,
      ]),
    ]);
    // The name of a vibe names its box, whatever its rank.
    for (const tag of meta.tags) {
      expect(vibe(tag.tag_id)).toHaveAttribute("aria-labelledby", within(vibe(tag.tag_id)).getByRole("heading", { level: 3 }).id);
    }
  });

  test("test_what_is_true_of_every_vibe_is_said_once_over_them_in_sight", () => {
    show();

    const over = screen.getByRole("region", { name: VIBES.each.title });

    expect([...over.querySelectorAll("p")].map((line) => line.textContent)).toEqual([
      VIBES.each.lead,
      VIBES.each.residents,
      VIBES.each.more,
    ]);
    expect(inSight(over)).toBe(true);
    // Which way the colours of every map run, once. A vibe that counts who lived somewhere is said to say so.
    expect(VIBES.each.lead).toContain("a darker green means more of the vibe");
    expect(VIBES.each.residents).toContain("it counts their age or their households and nothing else");
    // It names the fold by what the fold says.
    expect(VIBES.each.more).toContain(`"${VIBES.works}"`);
  });

  test("test_every_vibe_says_what_it_means_in_sight_and_what_it_cannot_see_in_its_fold", () => {
    show();

    for (const tag of meta.tags) {
      const part = vibe(tag.tag_id);
      const meaning = within(part).getByText(tag.meaning);
      expect([tag.tag_id, inSight(meaning)]).toEqual([tag.tag_id, true]);
      // Every line, word for word, and in the API's order. It is honest, and it stays.
      const lines = [...(foldOf(tag.tag_id).querySelector(`[aria-label="${VIBES.cannotSee.title}"]`)?.querySelectorAll("li") ?? [])];
      expect(lines.map((line) => line.textContent)).toEqual(tag.cannot_see);
    }
    // Every vibe says first that an area is many streets.
    expect(new Set(meta.tags.map((tag) => tag.cannot_see[0]))).toEqual(
      new Set(["What one street or one home is like, because an area is made up of many streets."]),
    );
  });

  test("test_the_page_can_never_disagree_with_the_engine_because_it_holds_no_vibe_of_its_own", () => {
    show();
    // Gritty is one vibe. Works and warehouses is a part of it, and no vibe of its own.
    expect(screen.getByRole("heading", { level: 3, name: "Gritty" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Works and warehouses" })).toBeNull();
    cleanup();

    // Built on a release that holds no recorded crime, it lists every vibe but Gritty.
    show(variantA);

    expect(screen.getByRole("heading", { level: 3, name: "Works and warehouses" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Gritty" })).toBeNull();
    // A release with no vibe lists none, and says nothing of any.
    cleanup();
    show({ ...meta, tags: [] });
    expect(screen.queryAllByRole("heading")).toEqual([]);
    expect(document.body.textContent?.includes(VIBES.each.lead)).toBe(false);
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
      // Its own words say which census, and the page draws them as they came, in sight.
      expect(tag.meaning).toContain("Census 2021");
      expect(tag.meaning).toContain("It counts who lived there as well as what is there");
      expect(inSight(within(vibe(tag.tag_id)).getByText(tag.meaning))).toBe(true);
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

describe("a vibe, in short", () => {
  test("test_what_is_in_sight_of_a_vibe_is_its_name_what_it_means_its_two_ends_and_its_map_and_no_more", () => {
    show();

    // Every vibe but the one that counts recorded crime, which says so on its face. A vibe the
    // service says is less sure is among them: it is shown as every other is.
    expect(meta.tags.filter((one) => one.sureness === "rough_guide").map((one) => one.tag_id)).toEqual(["village_feel"]);
    for (const tag of meta.tags.filter((one) => one.tag_id !== "street_character")) {
      const [low, high] = ends(tag);
      const seen = [...vibe(tag.tag_id).querySelectorAll("h3, p, li, figcaption, summary, td, th, dt, dd")]
        // What stands in no fold, and the bar of a fold that stands in none.
        .filter((one) => inSight(one) || (one.tagName === "SUMMARY" && inSight(one.parentElement?.parentElement ?? null)))
        .map((one) => one.textContent);
      // Its name, what it means, the gauge of its map with its two ends, and the bar of its
      // one fold. Its two ends are said once, where their pictures stand: at the ends of its gauge.
      expect([tag.tag_id, seen]).toEqual([tag.tag_id, [tag.label, tag.meaning, `${low}${high}`, `${VIBES.works}: ${tag.label}`]]);
    }
  });

  test("test_the_founder_asked_for_far_less_in_sight_a_vibe_holds_one_fold_and_no_small_heading_outside_it", () => {
    show();

    for (const tag of meta.tags) {
      const part = vibe(tag.tag_id);
      expect([tag.tag_id, part.querySelectorAll(":scope > details").length]).toEqual([tag.tag_id, 1]);
      // The one heading in sight is the name of the vibe: every other stands in its fold.
      const headings = [...part.querySelectorAll("h1, h2, h3, h4, h5, h6")].filter(inSight);
      expect([tag.tag_id, headings.map((heading) => heading.textContent)]).toEqual([tag.tag_id, [tag.label]]);
      expect([tag.tag_id, [...part.querySelectorAll("table, dl")].filter(inSight)]).toEqual([tag.tag_id, []]);
      // No area is named in sight: where a vibe is found is in its fold.
      expect([tag.tag_id, [...part.querySelectorAll("a")].filter(inSight)]).toEqual([tag.tag_id, []]);
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
        expect(bandOn(picture, mark.area_id)).toBe(mark.band === null ? "none" : String(mark.band));
      }
      expect(picture.closest("details")).toBeNull();
    }
    // One map for each vibe, and no other picture is named on the page.
    expect(screen.getAllByRole("img")).toHaveLength(meta.tags.length);
  });

  test("test_the_gauge_of_every_vibe_has_the_one_picture_of_each_of_its_ends_and_the_two_are_opposites", () => {
    // The founder: "where a gauge may exist, ensure they have a opposing icons for each side
    // of the gauge". The gauge of a vibe on this page is the legend of its map: five shades
    // between its two ends. A scale had its ends pictured apart, under what it means, and a
    // vibe that runs one way had none: the look had one pair of pictures for all of them.
    show();

    expect(new Set(meta.tags.map((tag) => tag.shape))).toEqual(new Set(["scale", "one_way"]));
    for (const tag of meta.tags) {
      const legend = vibe(tag.tag_id).querySelector("figcaption > span");
      const drawn = [...(legend?.querySelectorAll<HTMLElement>("[style*='/art/'], [data-band]") ?? [])].map(
        (one) => one.getAttribute("data-band") ?? one.style.getPropertyValue("--art"),
      );
      const [low, high] = picturesAtEnds(tag.tag_id).map((name) => `url("${pictureOf(name)}")`);
      // The picture of the low end, the five shades from the palest, and the picture of the
      // high end: each picture is chosen by the id the service gives the vibe.
      expect([tag.tag_id, drawn]).toEqual([tag.tag_id, [low, "1", "2", "3", "4", "5", high]]);
      expect([tag.tag_id, low === high, picturesAtEnds(tag.tag_id).includes(NO_PICTURE)]).toEqual([tag.tag_id, false, false]);
      // They are dress. The name of the map says the two ends to whoever hears the page.
      for (const one of legend?.querySelectorAll("[style*='/art/']") ?? []) expect(one.closest("[aria-hidden='true']")).not.toBeNull();
    }
  });

  test("test_the_two_ends_of_a_vibe_are_said_once_where_its_gauge_stands_and_nowhere_else_in_sight", () => {
    show();

    for (const tag of meta.tags) {
      // Under what it means stands nothing of its ends: they were said there and under the map as well.
      expect([tag.tag_id, vibe(tag.tag_id).querySelector("p[data-ends]")]).toEqual([tag.tag_id, null]);
      const [low, high] = ends(tag);
      const named = [...vibe(tag.tag_id).querySelectorAll("span, p")].filter(
        (one) => one.closest("details") === null && one.children.length === 0 && (one.textContent === low || one.textContent === high),
      );
      expect([tag.tag_id, named.map((one) => one.textContent)]).toEqual([tag.tag_id, [low, high]]);
    }
  });

  test("test_a_vibe_whose_map_is_not_drawn_has_its_two_ends_with_their_pictures_under_what_it_means", () => {
    // With no map there is no gauge to stand them at the ends of, and they are still what
    // the vibe runs between. So they stand under what it means, each under its picture.
    render(<VibesList meta={meta} areas={areas} bands={bands} geometry={null} />);

    for (const tag of meta.tags) {
      const [low, high] = ends(tag);
      const line = vibe(tag.tag_id).querySelector("p[data-ends]");
      expect([tag.tag_id, inSight(line)]).toEqual([tag.tag_id, true]);
      // It says first what the two are to whoever cannot see them side by side.
      expect([tag.tag_id, line?.textContent]).toEqual([tag.tag_id, `${VIBES.between} ${low} ${VIBES.to} ${high}`]);
      expect(line?.querySelector(".visually-hidden")?.textContent).toBe(`${VIBES.between} `);
      // The low end is at the left, as it is wherever a band is drawn.
      const drawn = [...(line?.querySelectorAll<HTMLElement>("[style*='/art/']") ?? [])];
      expect([tag.tag_id, drawn.map((one) => one.style.getPropertyValue("--art"))]).toEqual([
        tag.tag_id,
        picturesAtEnds(tag.tag_id).map((name) => `url("${pictureOf(name)}")`),
      ]);
      for (const one of drawn) expect(one).toHaveAttribute("aria-hidden", "true");
      // It stands under what the vibe means.
      expect(within(vibe(tag.tag_id)).getByText(tag.meaning).compareDocumentPosition(line as Element) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    }
  });

  test("test_the_legend_is_five_swatches_in_the_five_colours_of_the_map_between_its_two_ends", () => {
    show();

    for (const tag of meta.tags) {
      const [low, high] = ends(tag);
      const legend = vibe(tag.tag_id).querySelector("figcaption > span");
      // It is for the eye: the name of the map says the same to whoever hears the page.
      expect(legend).toHaveAttribute("aria-hidden", "true");
      // The low end, what runs between the two, and the high end: each end is its picture and its name.
      const parts = [...(legend?.firstElementChild?.children ?? [])];
      expect(parts.map((one) => one.textContent)).toEqual([low, "", high]);
      expect([...(parts[1]?.querySelectorAll("[data-band]") ?? [])].map((one) => one.getAttribute("data-band"))).toEqual(["1", "2", "3", "4", "5"]);
      // Its two ends and the five: one gauge, and nothing else under the map.
      expect(vibe(tag.tag_id).querySelector("figcaption")?.children).toHaveLength(1);
      expect(legend?.children).toHaveLength(1);
    }
  });

  test("test_what_dots_on_a_map_mean_is_said_once_over_the_vibes_and_under_no_map", () => {
    // Every map of the made-up city holds an area that cannot be placed, and each said so under itself.
    show();

    expect(inBand("leafy", null).length).toBeGreaterThan(0);
    expect(VIBES.each.lead).toContain("An area drawn with dots is one that Burro could not work the vibe out for.");
    expect(document.body.textContent?.split("drawn with dots")).toHaveLength(2);
    for (const tag of meta.tags) expect(vibe(tag.tag_id).querySelector("figcaption")?.textContent?.includes("dots")).toBe(false);
  });

  test("test_no_vibe_is_shown_as_a_percentage_a_score_or_a_rank", () => {
    show();

    for (const tag of meta.tags) {
      const text = [...vibe(tag.tag_id).querySelectorAll("h3, h4, p, figcaption, a, summary, caption, th")]
        .map((one) => one.textContent ?? "")
        .filter((words) => words !== tag.meaning)
        .join(" ");
      expect(/%|percent|score|\brank/i.test(text)).toBe(false);
    }
  });
});

describe("how Burro works a vibe out, in its fold", () => {
  test("test_it_is_one_fold_under_each_vibe_closed_and_named_for_what_a_person_would_ask", () => {
    show();

    for (const tag of meta.tags) {
      const fold = foldOf(tag.tag_id);
      expect([tag.tag_id, fold.open, fold.getAttribute("data-fold")]).toEqual([tag.tag_id, false, "bar"]);
      // It says of which vibe it is, to whoever hears the page: every vibe has one.
      expect(fold.querySelector(":scope > summary")?.textContent).toBe(`${VIBES.works}: ${tag.label}`);
      expect(fold.querySelector(":scope > summary .visually-hidden")?.textContent).toBe(`: ${tag.label}`);
      // It stands last in the box of its vibe.
      expect(vibe(tag.tag_id).lastElementChild).toBe(fold);
    }
    expect(VIBES.works).toBe("How Burro works this out");
  });

  test("test_every_fold_holds_the_same_parts_in_the_same_order_so_that_one_is_read_against_the_next", () => {
    show();

    const shape = (tagId: string) => [...foldOf(tagId).querySelectorAll("h4")].map((heading) => heading.textContent);

    const first = shape(meta.tags[0]?.tag_id ?? "");
    expect(first).toEqual([VIBES.recipe.title, VIBES.cannotSee.title, VIBES.found.title]);
    for (const tag of meta.tags) expect(shape(tag.tag_id)).toEqual(first);
  });

  test("test_the_recipe_is_one_table_with_the_share_of_each_part_how_it_is_read_its_period_and_its_source", () => {
    const real = realLooking();
    show(real);
    const labels = new Map(real.features.map((metric) => [metric.feature_id, metric.label]));
    // A part the release does not carry is named as the API names it, and said to be missing.
    const waited = new Map(
      real.recipes.flatMap((held) => held.waits_on.map((part) => [part.feature_id, part.label] as const)),
    );
    expect(waited.size).toBe(4);

    for (const tag of real.tags) {
      const table = within(foldOf(tag.tag_id)).getByRole("table", { name: VIBES.recipe.caption(tag.label), hidden: true });
      const rows = within(table).getAllByRole("row", { hidden: true }).slice(1);
      expect(rows).toHaveLength(tag.terms.length);
      tag.terms.forEach((term, at) => {
        const metric = real.features.find((one) => one.feature_id === term.feature_id);
        const name = within(rows[at] as HTMLElement).getByRole("rowheader", { hidden: true });
        const cells = within(rows[at] as HTMLElement).getAllByRole("cell", { hidden: true });
        const carried = labels.get(term.feature_id);
        expect(name.textContent?.startsWith(carried ?? waited.get(term.feature_id) ?? "no name")).toBe(true);
        expect(name.textContent?.includes(VIBES.recipe.waits)).toBe(carried === undefined);
        // It is never shown as a part with no name, nor by its code.
        expect(name.textContent?.includes(VIBES.recipe.notCarried)).toBe(false);
        expect(said(cells[0])?.startsWith(readingOf(tag, term.reading))).toBe(true);
        expect(said(cells[1])).toBe(VIBES.recipe.share(term.hundredths));
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
      expect(tag.terms.reduce((sum, term) => sum + term.hundredths, 0)).toBe(100);
    }
    for (const code of ["gp_walk", "pharmacy_walk", "cuisine_variety", "private_outdoor_space"]) {
      expect(document.body.textContent?.includes(code)).toBe(false);
    }
  });

  test("test_the_recipe_is_written_out_once_and_nothing_of_it_is_lost", () => {
    // It stood twice: in short, and again as a table behind a second press.
    show();

    expect(screen.getAllByRole("table", { hidden: true })).toHaveLength(meta.tags.length);
    for (const tag of meta.tags) {
      for (const term of tag.terms) {
        const label = meta.features.find((one) => one.feature_id === term.feature_id)?.label;
        if (label === undefined) continue;
        expect([tag.tag_id, label, foldOf(tag.tag_id).textContent?.split(label).length]).toEqual([tag.tag_id, label, 2]);
      }
      expect(foldOf(tag.tag_id).textContent?.includes(VIBES.recipe.lead)).toBe(true);
    }
  });

  test("test_a_part_that_other_recipes_hold_says_which", () => {
    show();
    const part = (tagId: string, label: string) =>
      within(foldOf(tagId))
        .getAllByRole("row", { hidden: true })
        .find((one) => one.textContent?.includes(label));

    // Homes built before 1919 is a part of Village feel and of Age of buildings.
    expect(part("village_feel", "Homes built before 1919")).toHaveTextContent(VIBES.recipe.alsoIn("Age of buildings"));
    expect(part("built_age", "Homes built before 1919")).toHaveTextContent(VIBES.recipe.alsoIn("Village feel"));
    // Land that is residential garden is a part of Leafy alone.
    expect(part("leafy", "Land that is residential garden")?.textContent?.includes(VIBES.recipe.alsoIn("").slice(0, 12))).toBe(false);
  });

  test("test_the_sources_of_a_vibe_are_the_sources_of_its_parts_each_named_once", () => {
    const real = realLooking();
    show(real);

    for (const tag of real.tags) {
      const ids = new Set(
        tag.terms.flatMap((term) => real.features.find((one) => one.feature_id === term.feature_id)?.source_ids ?? []),
      );
      const listed = within(foldOf(tag.tag_id).querySelector(`[aria-label="${VIBES.sources}"]`) as HTMLElement).getAllByRole(
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
      expect(names).toEqual(Object.values(VIBES.recipe.columns));
      for (const row of table.querySelectorAll("tbody tr")) {
        const cells = [...row.querySelectorAll("td")];
        for (const cell of cells) expect(cell).toHaveAttribute("role", "cell");
        // Stacked, each cell says what it is of, for the eye. The column says it to a reader.
        expect(cells.map((cell) => cell.querySelector("[aria-hidden='true']")?.textContent)).toEqual(names.slice(1));
      }
    }
  });

  test("test_where_the_vibe_sits_in_the_settings_and_the_everyday_word_for_it_are_in_the_fold", () => {
    show();
    const leafy = meta.tags.find((tag) => tag.tag_id === "leafy") as Tag;
    const family = meta.families.find((one) => one.family === leafy.family);

    const facts = [...foldOf("leafy").querySelectorAll("dl > div")].map((one) => [
      one.querySelector("dt")?.textContent,
      one.querySelector("dd")?.textContent,
    ]);

    expect(facts).toEqual([
      [VIBES.facts.family, family?.label],
      [VIBES.facts.word, leafy.shelf_word],
    ]);
    // A vibe with no everyday word says nothing of one.
    expect(foldOf("homes").textContent?.includes(VIBES.facts.word)).toBe(false);
  });
});

describe("where a vibe is found, in its fold", () => {
  test("test_a_scale_names_both_its_ends_and_the_areas_at_each", () => {
    show();
    const pace = meta.tags.find((tag) => tag.tag_id === "pace") as Tag;

    const high = group("pace", VIBES.found.end("Buzzy"));
    const low = group("pace", VIBES.found.end("Calm"));

    expect([pace.low_end, pace.high_end]).toEqual(["Calm", "Buzzy"]);
    expect(within(high).getAllByRole("link", { hidden: true }).map((link) => link.textContent)).toEqual(inBand("pace", 5));
    expect(within(low).getAllByRole("link", { hidden: true }).map((link) => link.textContent)).toEqual(inBand("pace", 1));
    expect(inBand("pace", 5)).toContain("Pellam Cross");
    // The high end is said first, as the vibe is named for it, and then the low.
    expect(high.compareDocumentPosition(low) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  test("test_a_vibe_that_runs_one_way_names_the_areas_with_most_of_it_and_with_least", () => {
    show();

    const most = group("leafy", VIBES.found.most);
    const least = group("leafy", VIBES.found.least);

    expect(within(most).getAllByRole("link", { hidden: true }).map((link) => link.textContent)).toEqual(inBand("leafy", 5));
    expect(within(least).getAllByRole("link", { hidden: true }).map((link) => link.textContent)).toEqual(inBand("leafy", 1));
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
    const unplaced = inBand("leafy", null);

    const held = group("leafy", VIBES.found.unplaced);

    expect(unplaced.length).toBeGreaterThan(0);
    expect(within(held).getAllByRole("link", { hidden: true }).map((link) => link.textContent)).toEqual(unplaced);
    for (const end of [VIBES.found.most, VIBES.found.least]) {
      const named = within(group("leafy", end)).getAllByRole("link", { hidden: true });
      expect(named.filter((link) => unplaced.includes(link.textContent ?? ""))).toEqual([]);
    }
  });

  test("test_every_area_is_in_one_band_or_none_behind_a_press_of_its_own_and_a_mixed_area_is_at_no_one_end", () => {
    show();

    for (const tag of meta.tags) {
      const all = group(tag.tag_id, VIBES.found.every);
      const named = within(all).getAllByRole("link", { hidden: true }).map((link) => link.textContent);
      expect([...named].sort()).toEqual(areas.map((area) => area.name).sort());
      // A release of London names a thousand areas: they are one press further, inside the fold.
      const inner = all.closest("details");
      expect([inner?.getAttribute("data-fold"), inner?.parentElement?.closest("details")]).toEqual(["line", foldOf(tag.tag_id)]);
      expect(inner?.querySelector(":scope > summary")?.textContent).toBe(`${VIBES.found.every}: ${tag.label}`);
    }
    // Foxholt spans bands 3 to 5 on Going out: it is not said to sit at the Buzzy end.
    const mixed = bands.find((one) => one.tag_id === "pace")?.marks.find((mark) => nameOf(mark.area_id) === "Foxholt");
    expect([mixed?.spread_low, mixed?.spread_high]).toEqual([3, 5]);
    expect(within(group("pace", VIBES.found.end("Buzzy"))).queryByRole("link", { name: "Foxholt", hidden: true })).toBeNull();
  });

  test("test_what_a_band_is_is_said_where_the_bands_are_named", () => {
    show();

    // A band is a word of Burro's. The key calls it a step, and the fold says that the two are one.
    expect(foldOf("leafy")).toHaveTextContent(VIBES.found.lead);
    expect(VIBES.found.lead).toContain("five bands, which the key draws as five steps");
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

  test("test_the_names_weighed_for_a_vibe_stand_in_its_fold_each_with_its_case", () => {
    show(meta, weighed);

    const room = within(foldOf("pace")).getByRole("group", { name: VIBES.names.title, hidden: true });

    expect(within(room).getAllByRole("term", { hidden: true }).map((term) => term.textContent)).toEqual(["Pace", "Bustle"]);
    expect(room).toHaveTextContent("It is one word.");
  });

  test("test_a_case_is_three_lines_at_most", () => {
    const long = { pace: [{ name: "Pace", lines: ["One.", "Two.", "Three.", "Four."] }] };
    show(meta, long);

    const room = within(foldOf("pace")).getByRole("group", { name: VIBES.names.title, hidden: true });

    expect(CASE_LINES).toBe(3);
    expect(within(room).getAllByRole("definition", { hidden: true })[0]?.querySelectorAll("p")).toHaveLength(3);
    expect(room.textContent?.includes("Four.")).toBe(false);
  });

  test("test_a_vibe_with_no_other_name_weighed_draws_no_empty_room_and_a_name_for_no_vibe_is_not_drawn", () => {
    show(meta, weighed);

    expect(within(vibe("leafy")).queryByRole("group", { name: VIBES.names.title, hidden: true })).toBeNull();
    expect(document.body.textContent?.includes("It is of no vibe of this data.")).toBe(false);
  });

  test("test_the_name_the_engine_gives_is_the_name_of_the_vibe_whatever_is_weighed", () => {
    show(meta, weighed);

    expect(within(vibe("pace")).getByRole("heading", { level: 3 })).toHaveTextContent("Going out");
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
  test("test_it_says_so_on_its_face_in_sight_with_the_one_account_of_when_recorded_crime_counts", () => {
    show();
    const part = vibe("street_character");
    const notice = part.querySelector("[data-counts='recorded-crime']");

    expect(inSight(notice)).toBe(true);
    expect(notice).toHaveTextContent(CRIME_ACCOUNT.counts);
    expect(notice).toHaveTextContent("Recorded criminal damage");
    expect(notice).toHaveTextContent("Recorded anti-social behaviour");
    expect(notice).toHaveTextContent(CRIME_RULE);
    expect(notice).toHaveTextContent(CRIME_ACCOUNT.asking);
    // With the caveat of every figure of recorded crime, word for word as the contract has it.
    expect(notice).toHaveTextContent(CRIME_CAVEAT);
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
    // No word of the page is a verdict, and none is the word the service gives a vibe that is less sure.
    expect(/\b(safe|safer|unsafe|dangerous|rough)\b/i.test(document.body.textContent ?? "")).toBe(false);
  });
});

describe("a vibe the service says is less sure, on the page of vibes", () => {
  // The service says which vibe it is, in a code, and no word more. One that is older than
  // the website, or later, may say its label and why: so the page is handed the release as
  // such a service gave it, with both laid on it.
  const told = sayingSo(meta);
  /** Whatever is handed, the page says none of it: the release as such a service gave it, and one that says it of every vibe. */
  const everyVibe: MetaData = sayingSo(meta, meta.tags.map((tag) => tag.tag_id));

  test("test_the_service_says_which_vibe_it_is_and_the_page_says_nothing_of_it", () => {
    // The founder: "remove the concept of rough guide, we don't want to pass this on to a user".
    show(told);

    expect(meta.tags.filter((one) => one.sureness === "rough_guide").map((one) => one.tag_id)).toEqual([ROUGH.tag_id]);
    expect(told.rough_guides).toEqual([ROUGH]);
    const said = document.body.textContent ?? "";
    expect(said.length).toBeGreaterThan(1_000);
    expect([said.includes(ROUGH.label), said.includes(ROUGH.why), /less sure|rough guide/i.test(said)]).toEqual([false, false, false]);
    expect(document.querySelector("[data-rough-guide]")).toBeNull();
    expect(screen.queryAllByRole("note")).toEqual([]);
  });

  test("test_it_is_laid_out_as_every_other_vibe_is_with_nothing_beside_its_name_and_nothing_under_its_map", () => {
    show(told);

    const village = vibe(ROUGH.tag_id);
    const [named, figure, room, fold] = [...village.children];
    // Its name is the last thing of the line of its name, and what it says of itself is empty.
    expect(within(village).getByRole("heading", { level: 3, name: "Village feel" }).nextElementSibling).toBeNull();
    expect([named?.querySelector("h3") !== null, figure?.tagName, room?.children.length, room?.textContent, fold?.tagName]).toEqual([true, "FIGURE", 0, "", "DETAILS"]);
  });

  test("test_whatever_the_service_says_of_whichever_vibe_no_label_and_no_sentence_is_drawn", () => {
    show(everyVibe);

    const said = document.body.textContent ?? "";
    expect(everyVibe.rough_guides.map((one) => [one.tag_id, one.label, one.why])).toEqual(meta.tags.map((tag) => [tag.tag_id, ROUGH.label, ROUGH.why]));
    expect(everyVibe.tags.filter((tag) => tag.sureness !== "rough_guide")).toEqual([]);
    expect(document.querySelector("[data-rough-guide]")).toBeNull();
    expect([said.includes(ROUGH.label), said.includes(ROUGH.why), /less sure|rough guide/i.test(said)]).toEqual([false, false, false]);
    for (const tag of everyVibe.tags) expect(within(vibe(tag.tag_id)).getByRole("heading", { level: 3 }).nextElementSibling).toBeNull();
  });
});

describe("how an area is placed on a vibe", () => {
  const how = () => document.getElementById("how") as HTMLDetailsElement;

  test("test_it_is_one_fold_at_the_foot_of_the_page_closed_and_named_for_what_a_person_would_ask", () => {
    const { container } = show();

    expect(container.lastElementChild).toBe(how());
    expect([how().tagName, how().open, how().getAttribute("data-fold")]).toEqual(["DETAILS", false, "ground"]);
    expect(how().querySelector(":scope > summary")?.textContent).toBe(VIBES.how.title);
    // What it opens stands under no heading that says what its bar has said.
    expect(how().querySelectorAll("h2, h3, h4")).toHaveLength(0);
    expect(within(how()).getAllByRole("listitem", { hidden: true }).map((item) => item.textContent)).toEqual([...VIBES.how.points]);
    expect(within(how()).getByRole("link", { name: VIBES.methods, hidden: true })).toHaveAttribute("href", "/methods");
  });

  test("test_how_an_area_is_placed_is_said_as_the_contract_defines_it", () => {
    show();

    expect(contract()).toContain("If `coverage < 0.6` then `raw`, `score` and `band` are null");
    expect(how()).toHaveTextContent("measurements that carry 60 of the 100 shares");
    expect(contract()).toContain("where an area sits among the same population, in fifths");
    expect(how()).toHaveTextContent("in fifths");
    expect(contract()).toContain("Areas that are level share a band.");
    expect(how()).toHaveTextContent("Areas that are level share a band.");
    expect(contract()).toContain(
      "Burro chose which measurements go into this vibe and how much each of them counts. That choice is a judgement, and not a fact about the place.",
    );
    expect(how()).toHaveTextContent(
      "Burro chose which measurements go into each vibe and how much each one counts, and that choice is a judgement.",
    );
    // The one number the page states for itself is the 60, with the 100 and the five bands it is said of.
    expect((VIBES.how.points.join(" ").match(/\d+/g) ?? []).sort()).toEqual(["1", "100", "100", "5", "60"].sort());
  });

  test("test_a_mixed_area_is_said_to_span_three_bands_as_the_engine_counts_them", () => {
    show();

    // The engine draws a range where the spread is three bands or more: bands 3 to 5 is one.
    expect(contract()).toContain("Used where the spread is three bands or more");
    expect(how().textContent?.includes("span three bands or more")).toBe(true);
    // Two bands that are three apart span four. The page once said "three bands apart".
    expect(how().textContent?.includes("bands apart")).toBe(false);
    // It is the homes of an area that differ, and never the parts of a recipe.
    expect(how().textContent?.includes("parts of one area")).toBe(false);
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
      // In the place of its map, in sight: why it has none.
      const why = [...section.querySelectorAll("figure p")].map((line) => line.textContent);
      expect([tag.tag_id, why]).toEqual([tag.tag_id, isPlaced ? [] : [VIBES.map.notYet]]);
      if (!isPlaced) {
        expect(section.querySelectorAll("a[href^='/synthetic/']")).toHaveLength(0);
        expect(section.textContent?.includes(VIBES.found.unplaced)).toBe(false);
        expect(section.querySelector("figcaption")).toBeNull();
      }
    }
  });

  test("test_every_vibe_says_how_much_of_its_recipe_is_held_as_one_number_and_names_what_it_waits_on", () => {
    // Seen in a browser: "A part this data does not carry", of every part that was missing,
    // and the shares of the parts that were held were never added up.
    drawn();

    for (const held of preview.recipes) {
      const fold = foldOf(held.tag_id);
      expect(fold.textContent?.includes(held.held === 100 ? VIBES.whole : VIBES.held(held.held, held.needed))).toBe(true);
      for (const part of held.waits_on) expect(fold.textContent?.includes(part.label)).toBe(true);
      expect(fold.textContent?.includes(VIBES.recipe.notCarried)).toBe(false);
    }
    expect(preview.recipes.find((held) => held.tag_id === "leafy")?.held).toBe(30);
    expect(preview.recipes.find((held) => held.tag_id === "pace")?.held).toBe(0);
  });

  test("test_how_much_is_held_is_said_in_a_whole_sentence_with_both_numbers_as_the_api_gives_them", () => {
    expect(VIBES.held(0, 60)).toContain("carry 60 of the 100 shares");
    expect(VIBES.held(0, 60)).toContain("cannot work this vibe out for any area");
    expect(VIBES.held(30, 60)).toContain("they carry 30 of the 100 shares");
    expect(VIBES.held(30, 60)).toContain("cannot work this vibe out for any area yet");
    expect(VIBES.held(70, 60)).toContain("carry 70 of the 100 shares, which is enough to work the vibe out");
    for (const line of [VIBES.held(0, 60), VIBES.held(30, 60), VIBES.held(70, 60)]) {
      expect((line.match(/\d+/g) ?? []).filter((figure) => !["0", "30", "60", "70", "100"].includes(figure))).toEqual([]);
    }
  });

  test("test_the_outline_of_each_area_is_in_the_page_once_however_many_maps_it_draws", () => {
    const html = renderToStaticMarkup(
      <VibesList meta={preview} areas={listed.areas} bands={listed.bands} geometry={geometry} />,
    );
    const paths = html.match(/<path [^>]*\bd="M/g) ?? [];
    const pointers = html.match(/<use /g) ?? [];

    // One outline for each area, and a pointer to it from the one map of each vibe that is placed.
    expect(paths).toHaveLength(geometry.features.length);
    expect(pointers).toHaveLength(geometry.features.length * placed.length);
    const ids = [...html.matchAll(/ id="([^"]+)"/g)].map((found) => found[1]);
    expect(new Set(ids).size).toBe(ids.length);
    for (const found of html.matchAll(/<use [^>]*href="#([^"]+)"/g)) expect(ids).toContain(found[1]);
  });

  test("test_a_pointer_to_an_outline_says_its_band_and_where_the_outline_is_and_nothing_else", () => {
    // Seen on a build of a thousand areas and fourteen vibes: the page was 14 MB. Each of its
    // 26,000 pointers bore a class, the id of its area, and the id again in where it pointed:
    // 120 bytes as it is drawn, and as many again in what React is sent to take the page up.
    const html = renderToStaticMarkup(
      <VibesList meta={meta} areas={areas} bands={bands} geometry={geometry} />,
    );
    const pointers = html.match(/<use [^>]*>/g) ?? [];

    // A vibe has one map now, where it had two: the page draws half the pointers it drew.
    expect(pointers).toHaveLength(geometry.features.length * meta.tags.length);
    for (const pointer of pointers) {
      expect(pointer).toMatch(/^<use data-band="(?:[1-5]|none)" href="#o\d+"(?: fill="url\(#[\w-]+\)")?\/?>$/);
    }
    // Whose each outline is, the page says once, on the outline.
    const outlines = html.match(/<path [^>]*\bd="M/g) ?? [];
    expect(outlines).toHaveLength(geometry.features.length);
    for (const area of areas) expect(html.split(`data-area="${area.area_id}"`)).toHaveLength(2);
    // The areas are drawn in the order of the outlines on every map, as they were: a line
    // is as thin as a point of the screen, and which of two areas is drawn last shows in it.
    const order = pointers.map((pointer) => Number(/href="#o(\d+)"/.exec(pointer)?.[1]));
    const each = geometry.features.length;
    for (let from = 0; from < order.length; from += each) {
      expect(order.slice(from, from + each)).toEqual(Array.from({ length: each }, (_, at) => at));
    }
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
    const every = section.querySelector<HTMLDetailsElement>("details details");
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
    for (const opens of document.querySelectorAll("details > summary")) {
      expect(opens.matches(".target, .target-min")).toBe(true);
    }
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

describe("the page of vibes, in the look", () => {
  const written = readFileSync(path.resolve(__dirname, "VibesList.module.css"), "utf8");
  const SHEET = rulesOf(written);
  const setsOf = (selector: string, under: string | null = null) =>
    new Map(SHEET.filter((rule) => rule.selector === selector && rule.under === under).flatMap((rule) => [...rule.sets]));
  /** The drawings a part holds, by the picture each is drawn from, in the order they stand. */
  const drawnIn = (part: Element | null | undefined) =>
    [...(part?.querySelectorAll<HTMLElement>("[style*='/art/']") ?? [])].map((one) => one.style.getPropertyValue("--art"));
  const pictured = (name: Parameters<typeof pictureOf>[0]) => `url("${pictureOf(name)}")`;

  test("test_every_vibe_stands_in_a_box_of_its_own_and_so_do_what_is_said_over_them_and_the_bar_of_the_fold_at_the_foot", () => {
    show();

    for (const tag of meta.tags) {
      expect([tag.tag_id, vibe(tag.tag_id).tagName, vibe(tag.tag_id).getAttribute("data-kind")]).toEqual([tag.tag_id, "SECTION", "box"]);
    }
    expect(screen.getByRole("region", { name: VIBES.each.title })).toHaveAttribute("data-kind", "box");
    expect(document.querySelector("#how > summary")).toHaveAttribute("data-kind", "box");
    // Each box is told that it brings its own room, so that the room is said in one place.
    for (const box of document.querySelectorAll("[data-kind='box']")) expect(box).not.toHaveClass("roomy");
    // No box stands in a box.
    for (const box of document.querySelectorAll("[data-kind='box']")) {
      expect(box.parentElement?.closest("[data-kind='box']") ?? null).toBeNull();
    }
  });

  test("test_nothing_of_the_page_is_read_on_the_grass", () => {
    for (const given of [meta, variantA, recordedAnswer("get_meta", "preview/meta").body.data, { ...meta, tags: [] }]) {
      cleanup();
      const { container } = show(given);
      expect(onTheGrass(container)).toEqual([]);
    }
    cleanup();
    // Nor where there is no map to draw, and other names were weighed.
    const { container } = render(<VibesList meta={meta} names={{ [meta.tags[0]!.tag_id]: [{ name: "Another name", lines: ["One line."] }] }} />);
    expect(onTheGrass(container)).toEqual([]);
  });

  test("test_every_vibe_has_the_drawing_of_its_thing_before_its_name_which_says_nothing", () => {
    show();

    for (const tag of meta.tags) {
      const name = within(vibe(tag.tag_id)).getByRole("heading", { level: 3 });
      const thing = name.previousElementSibling;
      // By the id the service gives the vibe, then by its family, then the plain one. No vibe is named here.
      expect([tag.tag_id, drawnIn(thing)]).toEqual([tag.tag_id, [pictured(drawingOf({ kind: "tag", id: tag.tag_id, family: tag.family }))]]);
      expect(thing).toHaveAttribute("aria-hidden", "true");
      expect(thing?.textContent).toBe("");
      // The name is the service's, and is what the heading says: the drawing is dress.
      expect(name.textContent).toBe(tag.label);
      expect(name).toHaveAccessibleName(tag.label);
    }
    // A vibe the look has no drawing for is drawn by its family, and one of no family by the plain drawing.
    cleanup();
    // The service may come to serve a vibe, or a family, that the website was not built with.
    const first = meta.tags[0]!;
    const unknown = { ...first, tag_id: "a_vibe_that_is_new", label: "A vibe that is new" } as unknown as Tag;
    const ofNoFamily = { ...first, tag_id: "another_that_is_new", label: "Another", family: "a_family_that_is_new" } as unknown as Tag;
    show({ ...meta, tags: [unknown, ofNoFamily] });
    expect(drawnIn(vibe(unknown.tag_id).querySelector("h3")?.previousElementSibling)).toEqual([
      pictured(drawingOf({ kind: "tag", id: null, family: first.family })),
    ]);
    expect(drawnIn(vibe(ofNoFamily.tag_id).querySelector("h3")?.previousElementSibling)).toEqual([pictured("thing-plain")]);
  });

  test("test_the_small_map_stands_beside_what_is_said_of_the_vibe_where_there_is_room_and_is_never_wider_than_a_phone_has", () => {
    // The map is small: what is said of the vibe is what is read.
    // Seen in a browser: in a column of 12rem the legend of a scale took two lines, its second name under its first.
    expect(setsOf(".figure").get("max-width")).toBe("13rem");
    expect(setsOf(".vibe", "@media (min-width: 40rem)").get("grid-template-columns")).toBe("minmax(0, 1fr) minmax(0, 13rem)");
    // It takes a second line where it has no room for one, as with the text made twice as large.
    expect(setsOf(".legend").get("flex-wrap")).toBe("wrap");
    // The word between the two ends of a scale is one word on one line, and is kept for whoever
    // hears the page where a window has no room for it: seen in a browser, it was broken in two.
    expect(setsOf(".between").get("white-space")).toBe("nowrap");
    expect(setsOf(".between", "@media (max-width: 18rem)").get("clip-path")).toBe("inset(50%)");
    // Two vibes side by side on a wide screen, each beginning on the line the other begins on.
    expect(setsOf(".vibes", "@media (min-width: 60rem)").get("grid-template-columns")).toBe("repeat(2, minmax(0, 1fr))");
  });

  test("test_a_vibe_has_four_parts_each_laid_out_under_the_one_before_it", () => {
    // Seen in a browser: a line was added to every vibe and not to the count of its rows, and
    // the last two parts of each were drawn on top of each other. A vibe is laid out in rows
    // of its own, as many as it needs: what is said of it and its map, what it says of
    // itself, and its fold.
    const preview: MetaData = recordedAnswer("get_meta", "preview/meta").body.data;

    for (const given of [meta, preview, variantA]) {
      cleanup();
      show(given);
      for (const tag of given.tags) expect([tag.tag_id, vibe(tag.tag_id).children.length]).toEqual([tag.tag_id, 4]);
    }
    expect(SHEET.filter((rule) => rule.sets.has("grid-row") || rule.sets.has("grid-template-rows")).map((rule) => rule.selector)).toEqual([]);
  });

  test("test_what_a_vibe_says_of_itself_stands_across_its_box_and_takes_no_room_where_it_says_nothing", () => {
    // Seen in a browser at 1440 by 900: the account of recorded crime stood in the column of
    // the words, twelve lines high, and the vibe beside it was drawn as high with nothing to say.
    show();

    for (const tag of meta.tags) {
      const [named, figure, room, fold] = [...vibe(tag.tag_id).children];
      // A vibe says of itself that it counts recorded crime, and nothing else: not that it is less sure.
      const says = tag.tag_id === "street_character";
      expect([tag.tag_id, named?.querySelector("h3") !== null, figure?.tagName, fold?.tagName]).toEqual([tag.tag_id, true, "FIGURE", "DETAILS"]);
      expect([tag.tag_id, room?.children.length === 0, room?.textContent === ""]).toEqual([tag.tag_id, !says, !says]);
    }
    // The parts of a vibe are parted by room of their own, so that a part that holds nothing takes none.
    expect(setsOf(".vibe").get("gap")).toBe("0 var(--space-4)");
    expect(setsOf(".vibe > .said:not(:empty)").get("margin-block-start")).toBe("var(--space-3)");
    expect(setsOf(".vibe > .works").get("margin-block-start")).toBe("var(--space-3)");
    expect(setsOf(".vibe > *", "@media (min-width: 40rem)").get("grid-column")).toBe("1 / -1");
  });

  test("test_the_bar_of_a_vibe_stands_where_it_stood_under_the_press_that_opens_it_and_so_does_the_bar_beside_it", () => {
    // Seen in a browser at 1440 by 900, by keyboard: the bar of a vibe stood at 352 in the
    // window and after the press that opened it at 303, with the page not scrolled. Two
    // vibes side by side shared their rows, so that each part of one stood level with the
    // same part of the other, and gave the rows up as one of them was opened. Of fourteen
    // bars, two moved under their own press, by 49 px and by 15, and twelve moved the bar
    // beside them, by as much as 65. Nothing moves under a press: so a bar stands directly
    // under what is said of its own vibe, whatever stands beside it, open or closed.
    const written = readFileSync(path.join(__dirname, "VibesList.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");

    // No vibe shares its rows with the one beside it, and none is as high as the one beside it.
    expect(/subgrid/.test(written)).toBe(false);
    expect(setsOf(".vibes", "@media (min-width: 60rem)").get("align-items")).toBe("start");
    // Nothing of the layout is keyed on whether a fold is open, or on what the vibe beside one holds.
    const keyed = SHEET.filter((rule) => /\[open\]|:has\(|\+ \.vibe|~ \.vibe|nth-child/.test(rule.selector));
    expect(keyed.map((rule) => rule.selector)).toEqual([]);
    // Each part of a vibe stands under the one before it, by room of its own.
    expect(setsOf(".vibe").get("align-content")).toBe("start");
    expect(setsOf(".vibe > .works").get("margin-block-start")).toBe("var(--space-3)");
    expect(SHEET.filter((rule) => /\.works\b/.test(rule.selector) && [...rule.sets.keys()].some((property) => /^(margin-block-start|align-self|position|inset)/.test(property) && rule.sets.get(property) === "auto")).map((rule) => rule.selector)).toEqual([]);
  });

  test("test_a_vibe_takes_the_focus_when_a_name_of_the_key_leads_to_it", () => {
    // Seen in a browser: a name of the key was pressed, the vibe came into sight, and the focus was left on nothing.
    show();

    for (const tag of meta.tags) expect([tag.tag_id, vibe(tag.tag_id).getAttribute("tabindex")]).toEqual([tag.tag_id, "-1"]);
    // It is reached by a link and by no key of its own: the order of the keyboard is as it was.
    expect(document.querySelectorAll("[tabindex]:not([tabindex='-1'])")).toHaveLength(0);
  });

  test("test_a_swatch_of_the_legend_is_a_step_of_the_maps_own_colour_with_the_line_of_the_map_for_its_edge", () => {
    for (const band of [1, 2, 3, 4, 5]) {
      expect(setsOf(`.swatch[data-band="${band}"]`).get("background")).toBe(`var(--map-${band})`);
    }
    // A swatch is a whole count of pixels of a drawing each way.
    const swatch = setsOf(".swatch");
    expect([swatch.get("width"), swatch.get("height")]).toEqual(["calc(var(--px) * 8)", "calc(var(--px) * 6)"]);
    expect(swatch.get("border")).toBe("var(--px) solid var(--map-line)");
    // Small on every screen, so that the five and the names of both ends stand on one line under the map.
    expect(setsOf(".legend").get("--px")).toBe("var(--px-ground)");
  });

  test("test_no_edge_of_the_page_is_dashed_and_nothing_of_it_moves", () => {
    const plain = written.replace(/\/\*[\s\S]*?\*\//g, "");

    // The founder: "The dashed border is not understood to a user, please make solid".
    expect(/\b(dashed|dotted)\b/.test(plain)).toBe(false);
    expect(SHEET.filter((rule) => [...rule.sets.keys()].some((property) => /^(transition|animation)/.test(property)))).toEqual([]);
    expect(SHEET.filter((rule) => /:(hover|focus|active)/.test(rule.selector))).toEqual([]);
  });

  test("test_a_vibe_that_counts_recorded_crime_says_so_as_a_notice_and_in_no_colour_of_a_fault", () => {
    const crime = setsOf(".crime");

    expect([crime.get("background"), crime.get("border"), crime.get("box-shadow")]).toEqual([
      "var(--notice-bg)",
      "var(--edge) solid var(--notice-edge)",
      "inset calc(var(--px) * 2) 0 0 var(--notice-mark)",
    ]);
    expect(SHEET.filter((rule) => [...rule.sets.values()].some((value) => /var\(--(poppy|error|error-edge|tradeoff|tradeoff-mark)\)/.test(value)))).toEqual([]);
  });

  test("test_the_sources_of_a_part_and_of_a_vibe_stand_after_the_key_of_the_look", () => {
    const real = realLooking();
    show(real);

    for (const tag of real.tags) {
      const lists = [...vibe(tag.tag_id).querySelectorAll<HTMLElement>("details ul")].filter((list) => list.querySelector("a[href^='/sources']") !== null);
      const carried = tag.terms.filter((term) => real.features.some((one) => one.feature_id === term.feature_id));
      // One for each part of the recipe that the data carries, and one for the vibe as a whole.
      expect([tag.tag_id, lists.length]).toEqual([tag.tag_id, carried.length + 1]);
      for (const list of lists) {
        const key = list.previousElementSibling as HTMLElement | null;
        expect([tag.tag_id, key?.style.getPropertyValue("--art")]).toEqual([tag.tag_id, 'url("/art/ui-key.png")']);
        expect(key).toHaveAttribute("aria-hidden", "true");
      }
    }
  });

  test("test_the_table_of_a_recipe_has_a_plain_edge_of_ink_and_each_row_stands_on_a_rule_of_sand", () => {
    expect(setsOf(".table").get("border")).toBe("var(--edge) solid var(--border)");
    expect(setsOf(".row").get("border-block-end")).toBe("var(--edge) solid var(--sand)");
    expect(setsOf(".row:last-child").get("border-block-end")).toBe("0");
  });
});
