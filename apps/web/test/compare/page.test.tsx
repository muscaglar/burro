/**
 * Comparing two to four areas, held to docs/design/web.md section 2: the
 * areas come from the address, the spec from the search that is open, the
 * rows in the order the API gave them, and every figure from a fact.
 */

import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";

import ComparePage from "@/app/compare/page";
import { CompareView } from "@/components/CompareTable/CompareView";
import { SearchApp } from "@/components/SearchApp/SearchApp";
import { Shell } from "@/components/Shell/Shell";
import { COMPARE, COMPARE_STATUS, COMPARE_TABLE, TRAY } from "@/content/compare";
import { PROMPT, SOURCE } from "@/content/search";
import { CRIME_CAVEAT } from "@/content/settings";
import { BANNER } from "@/content/site";
import { recordedAnswer, recordedError } from "@/lib/api/recorded";
import type { CompareBody, CompareData } from "@/lib/api/schema";
import { chosenFrom } from "@/lib/compare/list";
import { readableDate } from "@/lib/format";
import { fitOf } from "@/lib/map/fill";

import { setOnline, standInApi, type StandIn } from "../support/api";
import { faultsIn } from "../support/axe";
import { figuresNotFrom, saidBy } from "../support/figures";
import { areas, arrived, CANARY, firstSearch, meta, search, settled } from "../support/search";

jest.mock("next/navigation", () => ({ usePathname: () => "/compare" }));

const three: CompareData = recordedAnswer("compare", "compare-three").body.data;
const two: CompareData = recordedAnswer("compare", "compare-two-defaults").body.data;
const ranked = recordedAnswer("rank", "rank-first").body.data;
const slugOf = (areaId: string) => areas.find((area) => area.area_id === areaId)?.slug ?? "";
const THREE = three.areas.map((area) => slugOf(area.area_id));
const TWO = two.areas.map((area) => slugOf(area.area_id));

function comparison(slugs: readonly string[], api: StandIn, more: { unknown?: number; dropped?: number } = {}) {
  return (
    <CompareView
      chosen={chosenFrom(slugs, areas).chosen}
      defaults={meta.data.defaults}
      client={api.client}
      {...more}
    />
  );
}

const inShell = (page: ReactElement) => <Shell meta={meta.meta}>{page}</Shell>;

/** Opens a comparison with no search open, as a link followed from outside does. */
async function open(slugs: readonly string[], api: StandIn = standInApi().on("compare", "compare-two-defaults")) {
  const view = render(inShell(comparison(slugs, api)));
  await arrived();
  return { api, ...view };
}

/** Makes a search, then follows the link to a comparison, as a person does. */
async function openFromASearch(slugs: readonly string[], api = firstSearch().on("compare", "compare-three")) {
  const user = userEvent.setup({ delay: null });
  const view = render(inShell(<SearchApp meta={meta.data} areas={areas} client={api.client} />));
  await arrived();
  await search(user);
  view.rerender(inShell(comparison(slugs, api)));
  await arrived();
  return { api, user, ...view };
}

const sent = (api: StandIn) => api.lastCallTo("compare").body as CompareBody;
const table = () => screen.getByRole("table", { name: COMPARE_TABLE.caption });

beforeEach(() => setOnline(true));

describe("what a comparison is asked on", () => {
  test("test_compare_uses_the_search_that_is_open", async () => {
    const { api } = await openFromASearch(THREE);

    // The spec is the last one the API returned to the search, whole and unchanged.
    expect(sent(api).spec).toEqual(ranked.spec);
    expect(sent(api).area_ids).toEqual(three.areas.map((area) => area.area_id));
    expect(screen.getByRole("main")).toHaveTextContent(COMPARE.fromSearch);
    expect(screen.getByRole("main")).not.toHaveTextContent(COMPARE.fromDefaults.rent);
  });

  test("test_the_search_is_still_there_after_the_comparison", async () => {
    const { api, rerender } = await openFromASearch(THREE);

    rerender(inShell(<SearchApp meta={meta.data} areas={areas} client={api.client} />));
    await settled();

    expect(screen.getAllByRole("article")).toHaveLength(ranked.ranked.length);
    // Coming back asks for nothing again: the search was kept, not made again.
    expect(api.callsTo("interpret")).toHaveLength(1);
    expect(api.callsTo("rank")).toHaveLength(1);
  });

  test("test_with_no_search_open_the_defaults_are_sent_and_the_page_says_so", async () => {
    const { api } = await open(TWO);

    expect(sent(api).spec).toEqual(meta.data.defaults.rent);
    expect(sent(api)).toEqual(recordedAnswer("compare", "compare-two-defaults").request.body);
    expect(screen.getByRole("main")).toHaveTextContent(COMPARE.fromDefaults.rent);
    expect(screen.getByRole("main")).not.toHaveTextContent(COMPARE.fromSearch);
  });

  test("test_the_areas_are_asked_for_by_id_in_the_order_of_the_address", async () => {
    const { api } = await open([...TWO].reverse());

    expect(sent(api).area_ids).toEqual([...two.areas].reverse().map((area) => area.area_id));
    expect(api.lastCallTo("compare").url.includes("?")).toBe(false);
    expect(api.callsTo("compare")).toHaveLength(1);
  });

  test("test_one_area_is_not_a_comparison_and_nothing_is_sent", async () => {
    const { api } = await open(["alderwick"]);

    expect(api.calls).toEqual([]);
    expect(screen.getByRole("main")).toHaveTextContent(COMPARE.tooFew);
    expect(screen.queryByRole("table")).toBeNull();
    // The one area that was named is still there to read about.
    expect(screen.getByRole("link", { name: COMPARE_TABLE.open("Alderwick") })).toHaveAttribute(
      "href",
      "/synthetic/alderwick",
    );
  });
});

describe("the rows of a comparison", () => {
  test("test_the_rows_are_in_the_order_the_api_gave_which_is_the_order_of_the_weights", async () => {
    await openFromASearch(THREE);

    const headers = within(table()).getAllByRole("rowheader");

    expect(headers.map((header) => header.querySelector("span")?.textContent)).toEqual(
      three.rows.map((row) => row.label),
    );
    // What counts most comes first, as the person's own weights put it.
    const weights = three.rows.map((row) => row.weight);
    expect(weights).toEqual([...weights].sort((one, other) => other - one));
    expect(weights[0]).toBeGreaterThan(weights.at(-1) ?? 1);
    expect(headers[0]).toHaveTextContent(COMPARE_TABLE.countsFor(100));
    expect(headers.at(-1)).toHaveTextContent(COMPARE_TABLE.countsFor(5));
  });

  test("test_the_website_does_not_put_the_rows_in_an_order_of_its_own", async () => {
    const shuffled = recordedAnswer("compare", "compare-three");
    const rows = [...shuffled.body.data.rows].reverse();
    const api = firstSearch().on("compare", () => ({
      ...shuffled,
      body: { ...shuffled.body, data: { ...shuffled.body.data, rows } },
    }));

    await openFromASearch(THREE, api);

    expect(
      within(table())
        .getAllByRole("rowheader")
        .map((header) => header.querySelector("span")?.textContent),
    ).toEqual(rows.map((row) => row.label));
  });

  test("test_there_is_one_column_for_each_area_under_its_name", async () => {
    await openFromASearch(THREE);

    const columns = within(table()).getAllByRole("columnheader");

    expect(columns.map((column) => column.textContent)).toEqual([
      COMPARE_TABLE.what,
      ...three.areas.map((area) => area.name),
    ]);
    expect(within(table()).getAllByRole("row")).toHaveLength(three.rows.length + 1);
    expect(within(table()).getAllByRole("cell")).toHaveLength(three.rows.length * three.areas.length);
  });

  test("test_every_cell_says_whose_it_is_for_when_the_rows_are_stacked", async () => {
    await openFromASearch(THREE);

    for (const row of within(table()).getAllByRole("row").slice(1)) {
      const cells = within(row).getAllByRole("cell");
      // The name is for the eye. The heading of the column says it to a screen reader.
      expect(cells.map((cell) => cell.querySelector("[aria-hidden='true']")?.textContent)).toEqual(
        three.areas.map((area) => area.name),
      );
    }
  });

  test("test_every_figure_in_a_comparison_is_one_the_api_sent", async () => {
    await openFromASearch(THREE);
    const allowed = saidBy(three.facts);
    for (const row of three.rows) {
      allowed.add(row.label);
      // How much a thing counts, and what it adds, are the ranking's own working, rounded down.
      allowed.add(COMPARE_TABLE.countsFor(Math.round(row.weight * 100)));
      for (const cell of row.cells) {
        if (cell.contribution !== null) allowed.add(COMPARE_TABLE.adds(Math.floor(cell.contribution * 100 + 1e-9)));
      }
    }
    ranked.scores.forEach((score, at) => allowed.add(COMPARE_TABLE.standing(at + 1, fitOf(score.score))));
    allowed.add(COMPARE.compared(three.areas.length));

    expect(figuresNotFrom(screen.getByRole("main"), allowed)).toEqual([]);
  });

  test("test_no_percentile_and_no_unformatted_figure_is_ever_printed", async () => {
    await openFromASearch(THREE);
    const text = table().textContent ?? "";

    const raw = three.rows
      .flatMap((row) => row.cells.flatMap((cell) => [cell.percentile, cell.utility, cell.contribution]))
      .filter((value): value is number => value !== null && !Number.isInteger(value))
      .map(String);

    expect(raw.length).toBeGreaterThan(40);
    expect(raw.filter((value) => text.includes(value))).toEqual([]);
    expect(/percentile/i.test(text)).toBe(false);
  });

  test("test_what_a_thing_adds_to_the_fit_is_rounded_down", async () => {
    await openFromASearch(THREE);
    const journey = within(table()).getAllByRole("row")[1] as HTMLElement;

    // 0.3175 adds 31, and never 32. It is the second area's journey: the first's is 0.254,
    // which comes to 25 whichever way it is rounded, and so would prove nothing.
    expect(three.rows[0]?.cells[1]?.contribution).toBe(0.3175);
    expect(within(journey).getAllByRole("cell")[1]).toHaveTextContent(COMPARE_TABLE.adds(31));
    expect(within(journey).getAllByRole("cell")[1]).not.toHaveTextContent(COMPARE_TABLE.adds(32));
    expect(within(journey).getAllByRole("cell")[0]).toHaveTextContent(COMPARE_TABLE.adds(25));
  });

  test("test_every_cell_with_a_figure_ends_in_its_source_and_its_date", async () => {
    const { user } = await openFromASearch(THREE);
    const withFigure = three.rows.flatMap((row) =>
      row.cells.filter((cell) => {
        const fact = three.facts.find((one) => one.fact_id === cell.fact_id);
        return fact !== undefined && fact.template !== "missing";
      }),
    );

    const buttons = within(table()).getAllByRole("button", { name: /^Source for / });

    expect(buttons).toHaveLength(withFigure.length);
    expect(new Set(buttons.map((button) => button.getAttribute("aria-label"))).size).toBe(buttons.length);
    await user.click(buttons[0] as HTMLElement);
    const fact = three.facts.find((one) => one.fact_id === withFigure[0]?.fact_id);
    const cell = (buttons[0] as HTMLElement).closest("td") as HTMLElement;
    expect(within(cell).getByRole("link", { name: fact?.sources[0]?.name })).toHaveAttribute(
      "href",
      `/sources#${fact?.sources[0]?.source_id}`,
    );
    expect(cell).toHaveTextContent(`${SOURCE.dataFrom} ${readableDate(fact?.as_of ?? "")}`);
    expect(cell).toHaveTextContent(SOURCE.madeUp);
  });

  test("test_a_row_of_recorded_crime_carries_its_caveat_and_no_other_row_does", async () => {
    // No comparison was recorded with crime switched on, so one row's facts are made crime's here.
    const recorded = recordedAnswer("compare", "compare-two-defaults");
    const facts = recorded.body.data.facts.map((fact) =>
      fact.key === "noise_exposure" ? { ...fact, template: "feature_crime" as const } : fact,
    );
    const api = standInApi().on("compare", () => ({
      ...recorded,
      body: { ...recorded.body, data: { ...recorded.body.data, facts } },
    }));

    await open(TWO, api);
    const rows = within(table()).getAllByRole("rowheader");

    expect(rows.filter((row) => row.textContent?.includes(CRIME_CAVEAT))).toHaveLength(1);
    expect(rows.find((row) => row.textContent?.includes(CRIME_CAVEAT))).toHaveTextContent(/transport noise/);
    expect(/\b(safe|unsafe|dangerous)\b/i.test(screen.getByRole("main").textContent ?? "")).toBe(false);
  });

  test("test_an_area_with_no_figure_for_a_thing_says_so_and_nothing_is_filled_in", async () => {
    await openFromASearch(THREE);
    const air = within(table())
      .getAllByRole("row")
      .find((row) => row.textContent?.includes("nitrogen dioxide")) as HTMLElement;

    const cells = within(air).getAllByRole("cell");

    expect(three.rows.find((row) => row.component === "feature:air_no2")?.cells[2]?.value).toBeNull();
    expect(cells[2]).toHaveTextContent(`Alderwick${COMPARE_TABLE.noFigure}`);
    expect(/\d/.test(cells[2]?.textContent ?? "")).toBe(false);
    expect(within(cells[2] as HTMLElement).queryByRole("button")).toBeNull();
  });
});

describe("the areas of a comparison", () => {
  test("test_an_area_that_was_left_out_says_why_in_words", async () => {
    await openFromASearch(THREE);
    const compared = screen.getByRole("list", { name: COMPARE_TABLE.areas });

    const [farrowmere, , alderwick] = within(compared).getAllByRole("listitem");

    expect(farrowmere).toHaveTextContent(COMPARE_STATUS.ranked);
    expect(alderwick).toHaveTextContent(COMPARE_STATUS.commute_cap);
    // Its journey was never scored, and the page says that and gives no time.
    const journey = within(table()).getAllByRole("row")[1] as HTMLElement;
    expect(within(journey).getAllByRole("cell")[2]).toHaveTextContent(COMPARE_TABLE.notScored);
  });

  test("test_a_ranked_area_says_where_it_stands_in_the_search_that_is_open", async () => {
    await openFromASearch(THREE);
    const compared = within(screen.getByRole("list", { name: COMPARE_TABLE.areas })).getAllByRole("listitem");

    const place = ranked.scores.findIndex((score) => score.area_id === three.areas[0]?.area_id);
    const fit = fitOf(ranked.scores[place]?.score ?? 0);

    expect(place).toBeGreaterThanOrEqual(0);
    expect(compared[0]).toHaveTextContent(COMPARE_TABLE.standing(place + 1, fit));
    // An area that was left out has no place in the order, whatever the search says.
    expect(compared[2]).not.toHaveTextContent(/Rank \d/);
  });

  test("test_a_rank_from_the_ranking_of_an_earlier_search_is_never_shown", async () => {
    const second = recordedAnswer("interpret", "interpret-second-sentence").body.data;
    const api = firstSearch().on("compare", "compare-three");
    const user = userEvent.setup({ delay: null });
    const view = render(inShell(<SearchApp meta={meta.data} areas={areas} client={api.client} />));
    await arrived();
    await search(user);
    // A second sentence is read, and the ranking of it fails. The ranking on screen is the first one's.
    api.on("interpret", "interpret-second-sentence").on("rank", "error-internal");
    await search(user, " and more");

    view.rerender(inShell(comparison(THREE, api)));
    await arrived();

    expect(second.spec_hash).not.toBe(ranked.spec_hash);
    expect(sent(api).spec).toEqual(second.spec);
    expect(screen.getByRole("list", { name: COMPARE_TABLE.areas })).not.toHaveTextContent(/Rank \d/);
    expect(screen.getByRole("list", { name: COMPARE_TABLE.areas })).toHaveTextContent(COMPARE_STATUS.ranked);
  });

  test("test_with_no_search_open_no_area_is_given_a_rank", async () => {
    await open(TWO);

    expect(screen.getByRole("list", { name: COMPARE_TABLE.areas })).not.toHaveTextContent(/Rank \d|Fit \d/);
  });

  test("test_each_area_links_to_its_page_and_can_be_taken_out", async () => {
    await openFromASearch(THREE);

    for (const area of three.areas) {
      expect(screen.getByRole("link", { name: COMPARE_TABLE.open(area.name) })).toHaveAttribute(
        "href",
        `/synthetic/${slugOf(area.area_id)}`,
      );
    }
    expect(screen.getByRole("link", { name: COMPARE_TABLE.takeOut("Alderwick") })).toHaveAttribute(
      "href",
      `/compare?a=${THREE[0]}&a=${THREE[1]}`,
    );
  });

  test("test_the_names_and_the_links_are_there_before_the_api_has_answered", async () => {
    const api = standInApi();
    const held = api.hold("compare", "compare-two-defaults");
    render(inShell(comparison(TWO, api)));

    expect(screen.getByRole("link", { name: COMPARE_TABLE.open("Alderwick") })).toBeInTheDocument();
    expect(screen.getByRole("main")).toHaveTextContent(COMPARE.comparing);
    expect(screen.queryByRole("table")).toBeNull();

    held.release();
    expect(await screen.findByRole("table")).toBeInTheDocument();
    expect(screen.getByRole("main")).toHaveTextContent(COMPARE.compared(2));
  });

  test("test_opening_a_comparison_puts_its_areas_in_the_tray_for_the_way_back", async () => {
    const { api, rerender } = await open(TWO);

    rerender(inShell(<SearchApp meta={meta.data} areas={areas} client={api.client} />));
    await arrived();

    const tray = screen.getByRole("region", { name: TRAY.title });
    expect(within(tray).getAllByRole("listitem").map((item) => item.textContent)).toEqual(
      two.areas.map((area) => `${area.name}×`),
    );
  });
});

describe("a comparison that fails", () => {
  test("test_a_failure_is_said_in_the_apis_words_and_can_be_tried_again", async () => {
    const failure = recordedError("error-internal");
    const { api } = await open(TWO, standInApi().on("compare", "error-internal"));
    const user = userEvent.setup({ delay: null });

    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent(failure.body.error.message);
    expect(alert).toHaveTextContent(failure.headers["x-request-id"] ?? "no id");
    expect(screen.queryByRole("table")).toBeNull();

    api.on("compare", "compare-two-defaults");
    await user.click(within(alert).getByRole("button", { name: PROMPT.tryAgain }));

    expect(await screen.findByRole("table")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).toBeNull();
    expect(api.callsTo("compare")).toHaveLength(2);
  });

  test("test_an_area_the_api_no_longer_has_is_said_in_the_apis_words", async () => {
    await open(TWO, standInApi().on("compare", "compare-area-not-found"));

    expect(screen.getByRole("alert")).toHaveTextContent(
      recordedError("compare-area-not-found").body.error.message,
    );
  });

  test("test_a_comparison_that_cannot_leave_says_so", async () => {
    await open(TWO, standInApi().unreachable("compare"));

    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent(COMPARE.failedTitle));
    expect(screen.queryByRole("table")).toBeNull();
  });

  test("test_the_table_of_the_areas_before_is_not_shown_while_the_new_one_is_waited_for", async () => {
    const api = standInApi().on("compare", "compare-three");
    const { rerender } = render(inShell(comparison(THREE, api)));
    await arrived();
    expect(within(table()).getAllByRole("columnheader")).toHaveLength(4);

    // The person takes an area out. Until the API answers, there is no table to mislead.
    const held = api.hold("compare", "compare-two-defaults");
    rerender(inShell(comparison(TWO, api)));
    await arrived();

    expect(held.waiting()).toBe(1);
    expect(screen.queryByRole("table")).toBeNull();
    expect(screen.getByRole("main")).toHaveTextContent(COMPARE.comparing);
    await act(async () => held.release());
    await arrived();
    expect(within(table()).getAllByRole("columnheader")).toHaveLength(3);
  });

  test("test_an_answer_to_an_older_comparison_is_never_shown_for_a_newer_one", async () => {
    const api = standInApi();
    const late = api.late("compare", "compare-three", "compare-two-defaults");
    const { rerender } = render(inShell(comparison(THREE, api)));
    await arrived();

    // The person takes an area out before the first answer has come.
    rerender(inShell(comparison(TWO, api)));
    await arrived();
    await act(async () => late.release());
    await arrived();

    expect(within(table()).getAllByRole("columnheader").map((column) => column.textContent)).toEqual([
      COMPARE_TABLE.what,
      ...two.areas.map((area) => area.name),
    ]);
  });
});

describe("the address of a comparison", () => {
  const page = (a: string | string[] | undefined) => ComparePage({ searchParams: Promise.resolve({ a }) });

  test("test_the_areas_are_the_ones_the_address_names", async () => {
    const built = await page(TWO);

    expect(built.props.chosen.map((area: { slug: string }) => area.slug)).toEqual(TWO);
    expect(built.props.defaults).toEqual(meta.data.defaults);
    expect([built.props.unknown, built.props.dropped]).toEqual([0, 0]);
  });

  test("test_what_the_address_holds_that_is_no_area_is_counted_and_never_shown", async () => {
    const built = await page(["alderwick", `${CANARY} and quiet`, CANARY, "pellam-cross", "../meta"]);
    const api = standInApi().on("compare", "compare-two-defaults");

    const { container } = render(inShell({ ...built, props: { ...built.props, client: api.client } }));
    await arrived();

    expect(built.props.unknown).toBe(3);
    expect(container.innerHTML.includes(CANARY)).toBe(false);
    expect(JSON.stringify(api.calls).includes(CANARY)).toBe(false);
    expect(screen.getByRole("main")).toHaveTextContent(COMPARE.unknown(3));
    expect(sent(api).area_ids).toEqual(two.areas.map((area) => area.area_id));
  });

  test.each([undefined, "alderwick", [], ["alderwick", "alderwick"]])(
    "test_an_address_that_names_fewer_than_two_areas_compares_nothing: %j",
    async (a) => {
      const built = await page(a);

      expect(built.props.chosen.length).toBeLessThan(2);
    },
  );

  test("test_an_address_that_names_many_areas_compares_the_first_four", async () => {
    const built = await page(areas.slice(0, 40).map((area) => area.slug));

    expect(built.props.chosen).toHaveLength(4);
    // Only so much of an address is read at all.
    expect(built.props.dropped).toBeLessThanOrEqual(12);
  });
});

describe("a comparison with scripts off", () => {
  test("test_the_page_as_the_server_builds_it_names_the_areas_links_to_them_and_says_what_is_missing", async () => {
    const built = await ComparePage({ searchParams: Promise.resolve({ a: TWO }) });

    const html = renderToStaticMarkup(built);

    for (const area of two.areas) {
      expect(html).toContain(`>${area.name}<`);
      expect(html).toContain(`href="/synthetic/${slugOf(area.area_id)}"`);
    }
    expect(html).toContain(`<noscript><p`);
    expect(html.replace(/&#x27;/g, "'")).toContain(COMPARE.needsScripts);
    // The server is told the slugs and nothing of any search, so it builds no figure.
    expect(html).not.toMatch(/<table/);
  });
});

describe("a comparison, by keyboard and to a screen reader", () => {
  test("test_the_page_has_one_main_heading_and_the_banner", async () => {
    await openFromASearch(THREE);

    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(COMPARE.title);
    expect(screen.getByRole("region", { name: BANNER.label })).toHaveTextContent(BANNER.text);
  });

  test.each([
    ["with a table", "compare-three"],
    ["that failed", "error-internal"],
  ])("test_a_comparison_%s_has_no_accessibility_fault", async (_, scenario) => {
    const { container } = await open(THREE, standInApi().on("compare", scenario));

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });

  test("test_a_comparison_with_every_source_open_has_no_accessibility_fault", async () => {
    const { container, user } = await openFromASearch(THREE);

    for (const button of within(table()).getAllByRole("button", { name: /^Source for / })) {
      await user.click(button);
    }

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });

  test("test_every_control_is_native_in_the_tab_order_and_takes_a_target_size", async () => {
    await openFromASearch(THREE);

    const controls = [...screen.getByRole("main").querySelectorAll("a, button, input, select, textarea")];

    expect(controls.length).toBeGreaterThan(20);
    expect(controls.filter((control) => control.getAttribute("tabindex") === "-1")).toEqual([]);
    expect(
      controls.filter((control) => !control.classList.contains("target") && !control.classList.contains("target-min")),
    ).toEqual([]);
  });

  test("test_the_status_of_an_area_is_said_in_words_and_not_by_colour", async () => {
    await openFromASearch(THREE);

    const compared = within(screen.getByRole("list", { name: COMPARE_TABLE.areas })).getAllByRole("listitem");

    expect(compared.map((item) => Object.values(COMPARE_STATUS).some((words) => item.textContent?.includes(words)))).toEqual(
      [true, true, true],
    );
  });
});
