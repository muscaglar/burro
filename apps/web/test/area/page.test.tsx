/**
 * An area's page, held to docs/design/web.md section 2: every figure is a
 * fact of the API's with its source and its date, nothing is filled in, and
 * the page reads with scripts off.
 */

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import AreaPage, { generateStaticParams } from "@/app/[city]/[area]/page";
import { Shell } from "@/components/Shell/Shell";
import { AREA } from "@/content/area";
import { COMPARE, TRAY } from "@/content/compare";
import { DIMENSION } from "@/content/labels";
import { SOURCE } from "@/content/search";
import { CRIME_CAVEAT } from "@/content/settings";
import { BANNER } from "@/content/site";
import { recordedAnswer } from "@/lib/api/recorded";
import type { AreaData } from "@/lib/api/schema";
import { costFacts, factsShown, featuresByDimension, stationFacts, tagRows } from "@/lib/area/profile";
import { readableDate } from "@/lib/format";

import { faultsIn } from "../support/axe";
import { figuresNotFrom, saidBy } from "../support/figures";

jest.mock("next/navigation", () => ({
  ...jest.requireActual("next/navigation"),
  usePathname: () => "/synthetic/alderwick",
}));

const meta = recordedAnswer("get_meta", "meta").body;
const areas = recordedAnswer("list_areas", "areas").body.data.areas;
const profile = (slug: string): AreaData => recordedAnswer("get_area", `area/${slug}`).body.data;
const at = (city: string, area: string) => ({ params: Promise.resolve({ city, area }) });

async function show(slug: string, city = "synthetic") {
  return render(<Shell meta={meta.meta}>{await AreaPage(at(city, slug))}</Shell>);
}

/** What `notFound()` throws. Next turns it into the page that says there is no page. */
async function notFoundAt(city: string, area: string): Promise<boolean> {
  try {
    await AreaPage(at(city, area));
    return false;
  } catch (error) {
    return String((error as { digest?: string }).digest).includes("404");
  }
}

describe("which areas have a page", () => {
  test("test_every_area_of_the_release_has_a_page_under_its_city", async () => {
    const pages = await generateStaticParams();

    expect(pages).toHaveLength(24);
    expect(pages).toEqual(areas.map((area) => ({ city: "synthetic", area: area.slug })));
  });

  test.each([
    ["synthetic", "nowhere-at-all"],
    ["synthetic", "Alderwick"],
    ["synthetic", "../meta"],
    ["synthetic", "syn-n0001"],
    ["london", "alderwick"],
    ["paris", "alderwick"],
  ])("test_an_address_the_release_has_no_area_at_is_a_page_not_found: /%s/%s", async (city, area) => {
    expect(await notFoundAt(city, area)).toBe(true);
  });
});

describe("what an area's page says", () => {
  test("test_the_page_is_named_for_the_area_and_gives_its_borough", async () => {
    await show("alderwick");

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Alderwick");
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(screen.getByRole("article", { name: "Alderwick" })).toHaveTextContent(
      `${AREA.borough}Quillhaven`,
    );
  });

  test("test_the_page_carries_the_banner_that_says_the_data_is_made_up", async () => {
    await show("alderwick");

    expect(screen.getByRole("region", { name: BANNER.label })).toHaveTextContent(BANNER.text);
  });

  test.each(areas.map((area) => area.slug))(
    "test_every_figure_on_the_page_is_one_the_api_sent: %s",
    async (slug) => {
      const data = profile(slug);
      await show(slug);
      const allowed = saidBy(data.facts);
      // A feature or a tag is named by the release, and a name may hold a figure: "a 10-minute walk".
      for (const metric of meta.data.features) allowed.add(metric.label);
      for (const tag of meta.data.tags) allowed.add(tag.label);

      expect(figuresNotFrom(screen.getByRole("main"), allowed)).toEqual([]);
    },
  );

  test("test_every_fact_the_release_holds_for_the_area_is_on_its_page", async () => {
    const data = profile("alderwick");
    await show("alderwick");
    const main = screen.getByRole("main");

    const shown = factsShown(data, meta.data.features, meta.data.tags);

    // Every fact of the profile is laid out, and each is on the page by its own slots.
    expect(shown.map((fact) => fact.fact_id).sort()).toEqual(data.facts.map((fact) => fact.fact_id).sort());
    for (const fact of data.facts) {
      const slot = fact.slots.standing ?? fact.slots.median ?? fact.slots.name ?? "";
      expect(slot).not.toBe("");
      expect(main.textContent?.includes(slot)).toBe(true);
    }
  });

  test("test_every_fact_is_followed_by_its_source_and_its_date", async () => {
    const data = profile("alderwick");
    await show("alderwick");
    const profileOnPage = screen.getByRole("article", { name: "Alderwick" });

    const rows = within(profileOnPage)
      .getAllByRole("group")
      .filter((row) => !row.textContent?.includes(AREA.features.noFigure));

    expect(rows).toHaveLength(data.facts.length - 1);
    for (const row of rows) {
      const name = row.getAttribute("aria-label") ?? "";
      const fact = data.facts.find(
        (one) => (one.slots.segment ?? one.label) === name || (one.kind === "station" && row.textContent?.includes(one.slots.name ?? "")),
      );
      if (!fact) throw new Error("A row is of no fact.");
      const link = within(row).getByRole("link", { name: fact.sources[0]?.name });
      expect(link).toHaveAttribute("href", `/sources#${fact.sources[0]?.source_id}`);
      expect(row.textContent?.includes(`${SOURCE.dataFrom} ${readableDate(fact.as_of)}`)).toBe(true);
      expect(row.textContent?.includes(SOURCE.madeUp)).toBe(true);
    }
  });

  test("test_the_name_and_the_borough_have_their_source_and_their_date", async () => {
    const data = profile("alderwick");
    await show("alderwick");
    const named = data.facts.find((fact) => fact.kind === "area");
    const head = screen.getByRole("heading", { level: 1 }).parentElement as HTMLElement;

    expect(within(head).getByRole("link", { name: named?.sources[0]?.name })).toHaveAttribute(
      "href",
      "/sources#synthetic",
    );
    expect(head).toHaveTextContent(`${SOURCE.dataFrom} ${readableDate(named?.as_of ?? "")}`);
  });

  test("test_a_feature_with_no_figure_says_so_and_nothing_is_filled_in", async () => {
    const data = profile("alderwick");
    const without = data.features.filter((feature) => feature.value === null);
    await show("alderwick");

    expect(without.map((feature) => feature.feature_id)).toEqual(["air_no2"]);
    for (const feature of without) {
      const label = meta.data.features.find((metric) => metric.feature_id === feature.feature_id)?.label ?? "";
      const row = screen.getByRole("group", { name: label });
      expect(row).toHaveTextContent(`${label}${AREA.features.noFigure}`);
      // No figure, no comparison, and no source for what is not there.
      expect(/\d/.test(row.textContent ?? "")).toBe(false);
      expect(within(row).queryByRole("link")).toBeNull();
    }
  });

  test("test_the_facts_are_grouped_by_what_they_are_about_in_a_fixed_order", async () => {
    const data = profile("alderwick");
    await show("alderwick");
    const measured = screen.getByRole("region", { name: AREA.features.title });

    const groups = featuresByDimension(data, meta.data.features);
    const headings = within(measured)
      .getAllByRole("heading", { level: 3 })
      .map((heading) => heading.textContent);

    expect(headings).toEqual(groups.map((group) => DIMENSION[group.dimension]));
    // Recorded crime comes last.
    expect(headings.at(-1)).toBe(DIMENSION.crime);
    expect(groups.flatMap((group) => group.rows)).toHaveLength(meta.data.features.length);
  });

  test("test_recorded_crime_carries_its_caveat_and_no_verdict", async () => {
    await show("alderwick");
    const main = screen.getByRole("main");

    const crime = profile("alderwick").facts.filter((fact) => fact.template === "feature_crime");
    for (const fact of crime) {
      expect(screen.getByRole("group", { name: fact.label })).toHaveTextContent(CRIME_CAVEAT);
    }

    expect(crime).toHaveLength(2);
    expect(/\b(safe|safer|safest|unsafe|dangerous|rough|dodgy|sketchy)\b/i.test(main.textContent ?? "")).toBe(false);
  });

  test("test_the_cost_of_every_kind_of_home_is_given_as_a_range_with_its_date_and_confidence", async () => {
    const data = profile("alderwick");
    await show("alderwick");
    const cost = screen.getByRole("region", { name: AREA.cost.title });

    for (const tenure of ["rent", "buy"] as const) {
      for (const fact of costFacts(data, tenure)) {
        const row = within(cost).getByRole("group", { name: fact.slots.segment });
        expect(row).toHaveTextContent(`£${fact.slots.lower} to £${fact.slots.upper}`);
        expect(row).toHaveTextContent(`£${fact.slots.median}`);
        expect(row).toHaveTextContent(fact.slots.as_of ?? "");
        expect(row).toHaveTextContent(fact.slots.confidence ?? "");
      }
    }
    expect(costFacts(data, "rent")).toHaveLength(6);
    expect(costFacts(data, "buy")).toHaveLength(4);
    expect(data.cost).toHaveLength(10);
  });

  test("test_the_nearest_station_comes_first_and_is_said_to_be_the_nearest", async () => {
    const data = profile("pellam-cross");
    await show("pellam-cross");
    const stations = screen.getByRole("region", { name: AREA.stations.title });

    const rows = within(stations).getAllByRole("group");
    const facts = stationFacts(data);

    expect(facts.length).toBeGreaterThan(1);
    expect(rows).toHaveLength(data.stations.length);
    expect(rows[0]).toHaveAccessibleName("Nearest station");
    expect(rows.slice(1).every((row) => row.getAttribute("aria-label") === "Station within a short walk")).toBe(true);
    rows.forEach((row, position) => {
      const fact = facts[position];
      expect(row).toHaveTextContent(fact?.slots.name ?? "no name");
      expect(row).toHaveTextContent(fact?.slots.lines ?? "no lines");
    });
    // In the order of the walk, as the release gives it.
    const walks = facts.slice(1).map((fact) => data.stations.find((one) => one.station_id === fact.key)?.walk_minutes);
    expect(walks).toEqual([...walks].sort((one, other) => Number(one) - Number(other)));
  });

  test("test_what_the_api_serves_with_no_fact_behind_it_is_not_shown", async () => {
    const data = profile("alderwick");
    await show("alderwick");
    const text = screen.getByRole("main").textContent ?? "";

    // Whether a station is step-free is served, and no fact holds it, so it has no source or date.
    expect(data.stations.some((station) => "step_free" in station)).toBe(true);
    expect(/step.free/i.test(text)).toBe(false);
    // Nor is a percentile, a coverage or a tag's raw score ever printed.
    const unsourced = [
      ...data.features.flatMap((feature) => [feature.percentile, feature.coverage]),
      ...data.tags.flatMap((tag) => [tag.raw, tag.score, tag.coverage]),
    ].filter((value): value is number => value !== null && !Number.isInteger(value));
    expect(unsourced.length).toBeGreaterThan(20);
    expect(unsourced.filter((value) => text.includes(String(value)))).toEqual([]);
  });

  test("test_every_tag_of_the_release_is_on_the_page_with_where_it_ranks", async () => {
    const data = profile("alderwick");
    await show("alderwick");
    const feel = screen.getByRole("region", { name: AREA.tags.title });

    for (const { tag, fact } of tagRows(data, meta.data.tags)) {
      expect(within(feel).getByRole("group", { name: tag.label })).toHaveTextContent(
        fact?.slots.standing ?? AREA.tags.noFigure,
      );
    }
    expect(within(feel).getAllByRole("group")).toHaveLength(meta.data.tags.length);
  });

  test("test_an_area_the_release_does_not_rank_says_so", async () => {
    const unranked = areas.find((area) => !area.rankable);
    if (!unranked) throw new Error("The release ranks every area.");
    await show(unranked.slug);

    expect(screen.getByRole("main")).toHaveTextContent(AREA.notRanked);
  });

  test("test_an_area_the_release_ranks_does_not_say_it_is_unranked", async () => {
    await show("alderwick");

    expect(screen.getByRole("main")).not.toHaveTextContent(AREA.notRanked);
  });

  test("test_the_sources_of_the_page_are_listed_at_its_foot", async () => {
    await show("alderwick");
    const sources = screen.getByRole("region", { name: AREA.sources.title });

    expect(within(sources).getByRole("link", { name: "Synthetic test data" })).toHaveAttribute(
      "href",
      "/sources#synthetic",
    );
    expect(within(sources).getByRole("link", { name: AREA.methods })).toHaveAttribute("href", "/methods");
  });
});

describe("where an area is", () => {
  test("test_the_picture_names_the_area_and_the_list_beside_it_says_what_is_next_to_it", async () => {
    const data = profile("alderwick");
    await show("alderwick");
    const where = screen.getByRole("region", { name: AREA.where.title });

    expect(within(where).getByRole("img")).toHaveAccessibleName(/Alderwick/);
    const neighbours = within(where).getAllByRole("link");
    expect(neighbours.map((link) => link.textContent)).toEqual(data.neighbours.map((area) => area.name));
    expect(neighbours.map((link) => link.getAttribute("href"))).toEqual(
      data.neighbours.map((area) => `/synthetic/${area.slug}`),
    );
    expect(data.neighbours.length).toBeGreaterThan(0);
  });

  test("test_the_picture_takes_no_key_and_no_pointer", async () => {
    await show("alderwick");
    const picture = within(screen.getByRole("region", { name: AREA.where.title })).getByRole("img");

    expect(picture.querySelectorAll("a, button, [tabindex]")).toHaveLength(0);
  });
});

describe("an area's page, by keyboard and to a screen reader", () => {
  test("test_the_page_has_no_accessibility_fault", async () => {
    const { container } = await show("alderwick");

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });

  test("test_every_part_of_the_page_can_be_reached_from_its_list_of_contents", async () => {
    await show("alderwick");
    const contents = screen.getByRole("navigation", { name: AREA.contents });

    const links = within(contents).getAllByRole("link");

    expect(links).toHaveLength(6);
    for (const link of links) {
      const target = document.getElementById((link.getAttribute("href") ?? "").slice(1));
      expect(target?.textContent).toBe(link.textContent);
    }
  });

  test("test_every_control_is_native_in_the_tab_order_and_takes_a_target_size", async () => {
    const { container } = await show("alderwick");
    const main = screen.getByRole("main");

    const controls = [...main.querySelectorAll("a, button, input, select, textarea")];

    expect(controls.length).toBeGreaterThan(50);
    expect(controls.filter((control) => control.getAttribute("tabindex") === "-1")).toEqual([]);
    expect(
      controls.filter((control) => !control.classList.contains("target") && !control.classList.contains("target-min")),
    ).toEqual([]);
    expect([...container.querySelectorAll("[role='button'], [role='link'], [onclick]")]).toEqual([]);
  });

  test("test_no_link_on_the_page_is_fetched_before_it_is_pressed", async () => {
    await show("alderwick");
    const profileOnPage = screen.getByRole("article", { name: "Alderwick" });

    // Which area or which source a person reads next is told to no server ahead of time.
    const toPlaces = within(profileOnPage)
      .getAllByRole("link")
      .filter((link) => /^\/(synthetic|sources)/.test(link.getAttribute("href") ?? ""));

    expect(toPlaces.length).toBeGreaterThan(40);
    expect(toPlaces.filter((link) => link.getAttribute("data-prefetch") !== "false")).toEqual([]);
  });

  test("test_nothing_on_the_page_comes_from_another_origin", async () => {
    const { container } = await show("alderwick");

    expect([...container.querySelectorAll("[src], link[href], [srcset], [poster], script")]).toEqual([]);
    expect(
      [...container.querySelectorAll("a[href]")].filter((link) => !/^[/#]/.test(link.getAttribute("href") ?? "")),
    ).toEqual([]);
  });
});

describe("choosing an area to compare, from its page", () => {
  test("test_the_area_can_be_put_among_those_to_compare_and_taken_out_again", async () => {
    await show("alderwick");
    const tray = screen.getByRole("region", { name: TRAY.title });
    expect(tray).toHaveTextContent(TRAY.none);

    const user = userEvent.setup({ delay: null });

    await user.click(screen.getByRole("button", { name: COMPARE.add("Alderwick") }));

    expect(within(tray).getByText("Alderwick")).toBeInTheDocument();
    expect(tray).toHaveTextContent(TRAY.one);
    await user.click(screen.getByRole("button", { name: COMPARE.remove("Alderwick") }));
    expect(within(tray).getByText(TRAY.none)).toBeInTheDocument();
  });
});
