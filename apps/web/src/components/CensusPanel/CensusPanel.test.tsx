/**
 * The census figures of an area, held to docs/design/web.md section 2: closed
 * until it is pressed, asked for only then, and drawn as the API sent it.
 */

import { act, render, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderToStaticMarkup } from "react-dom/server";

import { CENSUS } from "@/content/census";
import { FAILURE } from "@/content/search";
import { recordedAnswer, recordedError } from "@/lib/api/recorded";
import type { CensusOffer } from "@/lib/api/schema";

import { BASE, standInApi, type StandIn } from "../../../test/support/api";
import { faultsIn } from "../../../test/support/axe";
import { watch } from "../../../test/support/watch";
import { CensusPanel } from "./CensusPanel";
import { CENSUS_PART } from "./part";

const offer: CensusOffer = recordedAnswer("get_meta", "meta").body.data.census;
const served = recordedAnswer("get_census", "census").body.data;
const SLUG = "foxholt";

const panel = () => document.getElementById(CENSUS_PART) as HTMLDetailsElement;
const opener = () => panel().querySelector("summary") as HTMLElement;

function show(api: StandIn = standInApi().on("get_census", "census"), slug = SLUG) {
  const view = render(<CensusPanel offer={offer} area={{ slug }} client={api.client} />);
  return { api, user: userEvent.setup({ delay: null }), ...view };
}

/** The tables of the panel, each closed under its own name until it is pressed. */
const tables = () => [...panel().querySelectorAll<HTMLDetailsElement>("details[data-table]")];

/** Opens the panel, and then every table in it, as a person who reads the whole of it does. */
async function opened(api?: StandIn, slug = SLUG) {
  const shown = show(api, slug);
  await shown.user.click(opener());
  await waitFor(() => expect(panel().querySelector("[role='status']")).toBeNull());
  for (const table of tables()) await shown.user.click(table.querySelector("summary") as HTMLElement);
  return shown;
}

afterEach(() => {
  window.location.hash = "";
});

describe("before it is opened", () => {
  test("test_it_is_closed_and_has_asked_for_nothing", () => {
    const { api } = show();

    expect(panel().open).toBe(false);
    expect(api.calls).toEqual([]);
    expect(panel().querySelectorAll("table, [role='status'], [role='alert']")).toHaveLength(0);
  });

  test("test_it_is_the_browsers_own_element_under_the_heading_the_api_sent", () => {
    show();

    expect(panel().tagName).toBe("DETAILS");
    expect(opener()).toHaveClass("target");
    expect(panel().querySelector("summary > h2")).toHaveTextContent(offer.heading);
    expect(panel()).toHaveTextContent(offer.intro);
  });

  test("test_no_figure_of_the_area_is_in_it", () => {
    show();
    const said = panel().textContent ?? "";

    for (const table of served.tables) {
      expect(said.includes(table.title)).toBe(false);
      for (const row of table.rows) if (row.count !== null) expect(said.includes(row.count)).toBe(false);
    }
    expect(said.includes("%")).toBe(false);
  });

  test("test_a_search_engine_is_asked_to_quote_nothing_of_it", () => {
    show();

    expect(panel()).toHaveAttribute("data-nosnippet");
  });

  test("test_with_scripts_off_it_says_that_the_figures_need_them", () => {
    // As the page is built: what a browser with scripts off is sent.
    const built = renderToStaticMarkup(
      <CensusPanel offer={offer} area={{ slug: SLUG }} client={standInApi().client} />,
    );

    expect(built.includes(`<noscript><p>${CENSUS.noScript}</p></noscript>`)).toBe(true);
    expect(built.includes("<details") && !built.includes("<table")).toBe(true);
  });

  test("test_where_no_census_is_served_nothing_is_drawn_and_nothing_is_asked", () => {
    const api = standInApi();
    const off = recordedAnswer("get_meta", "meta-no-census").body.data.census;

    const { container } = render(<CensusPanel offer={off} area={{ slug: SLUG }} client={api.client} />);

    expect(off.available).toBe(false);
    expect(container.innerHTML).toBe("");
    expect(api.calls).toEqual([]);
  });
});

describe("opening it", () => {
  test("test_it_asks_once_for_this_area_and_sends_nothing_else", async () => {
    const { api, user } = await opened();

    expect(api.unexpected).toEqual([]);
    expect(api.calls.map((call) => [call.method, call.url])).toEqual([["GET", `${BASE}/v1/areas/${SLUG}/census`]]);
    expect(api.calls[0]?.sent).toBeNull();
    // Closed and opened again, the answer in hand is shown. Nothing is asked twice.
    await user.click(opener());
    await user.click(opener());
    expect(panel().open).toBe(true);
    expect(api.calls).toHaveLength(1);
    expect(tables()).toHaveLength(served.tables.length);
  });

  test("test_the_answer_may_not_be_kept_and_says_nothing_of_the_page", async () => {
    const { api } = await opened();
    const { init } = api.lastCallTo("get_census");

    expect(init.cache).toBe("no-store");
    expect(init.credentials).toBe("omit");
    expect(init.referrerPolicy).toBe("no-referrer");
    expect(new URL(api.lastCallTo("get_census").url).search).toBe("");
  });

  test("test_nothing_is_written_down_and_the_address_does_not_change", async () => {
    const watching = watch();
    try {
      await opened();

      expect(watching.storage).toEqual([]);
      expect(watching.history).toEqual([]);
      expect(watching.console).toEqual([]);
    } finally {
      watching.stop();
    }
  });

  test("test_while_it_is_asked_for_the_page_says_so", async () => {
    const api = standInApi();
    const held = api.hold("get_census", "census");
    const { user } = show(api);

    await user.click(opener());

    expect(within(panel()).getByRole("status")).toHaveTextContent(CENSUS.loading);
    expect(panel().querySelector("table")).toBeNull();
    await act(async () => {
      held.release();
      await Promise.resolve();
    });
    await waitFor(() => expect(tables()).toHaveLength(served.tables.length));
    expect(panel().querySelector("[role='status']")).toBeNull();
  });

  test("test_the_focus_stays_where_it_was", async () => {
    const { user } = show();

    await user.click(opener());
    await waitFor(() => expect(tables().length).toBeGreaterThan(0));

    expect(document.activeElement).toBe(opener());
  });

  test("test_each_table_is_closed_under_its_own_name_until_it_is_pressed", async () => {
    const { api, user } = show();
    await user.click(opener());
    await waitFor(() => expect(tables().length).toBeGreaterThan(0));

    expect(tables().map((table) => table.open)).toEqual(served.tables.map(() => false));
    expect(tables().map((table) => table.querySelector("summary > h3")?.textContent)).toEqual(
      served.tables.map((table) => table.title),
    );
    for (const table of tables()) expect(table.querySelector("summary")).toHaveClass("target");

    const first = tables()[0] as HTMLDetailsElement;
    await user.click(first.querySelector("summary") as HTMLElement);

    // It came with the answer. Opening a table asks for nothing more.
    expect(first.open).toBe(true);
    expect(tables().slice(1).every((table) => !table.open)).toBe(true);
    expect(api.calls).toHaveLength(1);
  });

  test("test_it_is_opened_by_the_link_that_names_it", async () => {
    const { api } = show();

    act(() => {
      window.location.hash = `#${CENSUS_PART}`;
      window.dispatchEvent(new HashChangeEvent("hashchange"));
    });

    expect(panel().open).toBe(true);
    await waitFor(() => expect(api.callsTo("get_census")).toHaveLength(1));
  });

  test("test_what_is_asked_for_is_let_go_when_the_page_is_left", async () => {
    const api = standInApi().silent("get_census");
    const { user, unmount } = show(api);
    await user.click(opener());

    unmount();

    expect(api.lastCallTo("get_census").init.signal?.aborted).toBe(true);
  });
});

describe("what is drawn", () => {
  test("test_the_day_and_every_note_are_the_apis_in_its_order", async () => {
    await opened();

    expect(panel()).toHaveTextContent(served.date_line);
    const notes = [...panel().querySelectorAll("ol > li")].map((note) => note.textContent);
    expect(notes).toEqual(served.notes);
  });

  test("test_every_table_is_a_table_with_its_caption_and_its_headings", async () => {
    await opened();
    const tables = within(panel()).getAllByRole("table");

    expect(tables).toHaveLength(served.tables.length);
    tables.forEach((table, at) => {
      const sent = served.tables[at];
      expect(table.tagName).toBe("TABLE");
      expect(table.querySelector("caption")?.textContent).toBe(sent?.caption);
      const heads = within(table).getAllByRole("columnheader");
      expect(heads.map((head) => head.textContent)).toEqual([
        sent?.columns.label,
        sent?.columns.share,
        sent?.columns.count,
        sent?.columns.city,
      ]);
      expect(heads.every((head) => head.getAttribute("scope") === "col")).toBe(true);
      const rows = within(table).getAllByRole("rowheader");
      expect(rows.every((row) => row.tagName === "TH" && row.getAttribute("scope") === "row")).toBe(true);
    });
  });

  test("test_the_rows_are_drawn_in_the_order_they_came", async () => {
    await opened();

    within(panel())
      .getAllByRole("table")
      .forEach((table, at) => {
        const drawn = within(table)
          .getAllByRole("rowheader")
          .map((row) => row.querySelector("[aria-hidden='true']")?.textContent ?? row.textContent);
        expect(drawn).toEqual(served.tables[at]?.rows.map((row) => row.label));
      });
  });

  test("test_a_row_is_a_share_its_count_and_the_citys_share_as_they_came", async () => {
    await opened();
    const table = within(panel()).getAllByRole("table")[0] as HTMLElement;
    const sent = served.tables[0];

    within(table)
      .getAllByRole("row")
      .slice(1)
      .forEach((row, at) => {
        const cells = within(row)
          .getAllByRole("cell")
          .map((cell) => cell.querySelector("span:nth-of-type(2) > span")?.textContent);
        const from = sent?.rows[at];
        expect(cells).toEqual([from?.share, from?.count ?? CENSUS.noCount, from?.city_share]);
      });
  });

  test("test_a_share_under_one_in_a_hundred_is_said_in_words_and_gives_no_count", async () => {
    await opened();
    const small = served.tables.flatMap((table) => table.rows).filter((row) => row.count === null);

    expect(small.length).toBeGreaterThan(0);
    expect(small.every((row) => row.share === "fewer than 1 in 100" && row.percent === null)).toBe(true);
    const rows = within(panel())
      .getAllByRole("row")
      .filter((row) => row.textContent?.includes("fewer than 1 in 100") && within(row).queryAllByRole("cell").length > 0);
    const counts = rows.map((row) => within(row).getAllByRole("cell")[1]?.textContent);
    const own = rows.filter((row) => within(row).getAllByRole("cell")[0]?.textContent?.includes("fewer than"));
    expect(own.length).toBe(small.length);
    expect(counts.filter((count) => count?.includes(CENSUS.noCount)).length).toBe(small.length);
  });

  test("test_a_row_with_no_share_to_draw_draws_no_picture", async () => {
    // Seen in a browser: a line alone stood under "fewer than 1 in 100", and said nothing.
    await opened();
    const neither = served.tables
      .flatMap((table) => table.rows)
      .filter((row) => row.percent === null && row.city_percent === null);
    const rows = within(panel())
      .getAllByRole("row")
      .filter((row) => within(row).queryAllByRole("cell").length > 0);
    const bare = rows.filter((row) => row.querySelector("svg") === null);

    expect(neither.length).toBeGreaterThan(0);
    expect(bare).toHaveLength(neither.length);
    for (const row of bare) {
      const [share, , city] = within(row).getAllByRole("cell");
      expect(share?.textContent?.includes("fewer than 1 in 100")).toBe(true);
      expect(city?.textContent?.includes("fewer than 1 in 100")).toBe(true);
    }
  });

  test("test_a_row_under_a_group_is_read_whole_and_printed_under_its_group", async () => {
    await opened();
    const under = served.tables.flatMap((table) => table.rows).find((row) => row.depth === 2);
    const drawn = [...panel().querySelectorAll<HTMLElement>("th[scope='row'][data-depth='2']")][0];

    expect(under).toBeDefined();
    expect(drawn?.querySelector(".visually-hidden")?.textContent).toBe(under?.heading);
    expect(drawn?.querySelector("[aria-hidden='true']")?.textContent).toBe(under?.label);
  });

  test("test_a_table_that_is_left_out_says_so_and_nothing_more", async () => {
    // Seen in a browser: under each of five tables that gave no figure stood what the table
    // counts and the way to its source, which is a page of words about nothing.
    const sent = recordedAnswer("get_census", "census-too-few").body.data;
    await opened(standInApi().on("get_census", "census-too-few"), "grapnel-dock");

    for (const table of sent.tables) {
      const group = within(panel()).getByRole("group", { name: table.title });
      expect(group.textContent).toBe(table.left_out);
      expect(group.querySelectorAll("a, summary, details")).toHaveLength(0);
    }
  });

  test("test_every_table_says_what_it_counts_in_the_publishers_words", async () => {
    await opened();

    for (const table of served.tables) {
      const group = within(panel()).getByRole("group", { name: table.title });
      expect(group).toHaveTextContent(table.definition);
      if (table.note !== null) expect(group).toHaveTextContent(table.note);
      if (table.shown_only !== null) expect(group).toHaveTextContent(table.shown_only);
    }
  });

  test("test_every_table_is_one_press_from_its_source", async () => {
    await opened();

    for (const table of served.tables) {
      const group = within(panel()).getByRole("group", { name: table.title });
      const link = within(group).getByRole("link", { name: CENSUS.source });
      expect(link).toHaveAttribute("href", `/sources#${table.source_id}`);
      expect(link).toHaveAttribute("data-prefetch", "false");
      // A made-up table has no page of a publisher's to open.
      expect(within(group).getAllByRole("link")).toHaveLength(table.source_url === "" ? 1 : 2);
    }
  });

  test("test_the_publishers_page_is_linked_where_the_api_names_one", async () => {
    const real = recordedAnswer("get_census", "census");
    const tables = real.body.data.tables.map((table) => ({
      ...table,
      source_url: "https://publisher.example/table",
      source_label: "The publisher's page for this table",
    }));
    const api = standInApi().on("get_census", () => ({
      ...real,
      body: { ...real.body, data: { ...real.body.data, tables } },
    }));

    await opened(api);

    const links = within(panel()).getAllByRole("link", { name: "The publisher's page for this table" });
    expect(links).toHaveLength(tables.length);
    for (const link of links) {
      expect(link).toHaveAttribute("href", "https://publisher.example/table");
      expect(link).toHaveAttribute("rel", "noreferrer noopener");
    }
  });

  test("test_an_address_that_is_no_web_address_is_never_made_a_link", async () => {
    const real = recordedAnswer("get_census", "census");
    const tables = real.body.data.tables.map((table) => ({
      ...table,
      source_url: "javascript:alert(1)",
      source_label: "The publisher's page for this table",
    }));
    const api = standInApi().on("get_census", () => ({
      ...real,
      body: { ...real.body, data: { ...real.body.data, tables } },
    }));

    await opened(api);

    expect(within(panel()).queryAllByRole("link", { name: "The publisher's page for this table" })).toEqual([]);
    expect(panel().innerHTML.includes("javascript:")).toBe(false);
  });

  test("test_the_foot_says_where_the_figures_came_from_and_how_they_were_made", async () => {
    await opened();

    for (const line of [served.source_line, served.derivation_line, served.licence_line]) {
      expect(panel()).toHaveTextContent(line);
    }
  });

  test("test_a_table_that_is_left_out_says_so_and_draws_no_figure", async () => {
    for (const scenario of ["census-too-few", "census-not-held"] as const) {
      const sent = recordedAnswer("get_census", scenario).body.data;
      const { unmount } = await opened(standInApi().on("get_census", scenario), "grapnel-dock");

      expect(within(panel()).queryAllByRole("table")).toHaveLength(0);
      expect(panel().querySelectorAll("svg")).toHaveLength(0);
      for (const table of sent.tables) {
        expect(table.rows).toEqual([]);
        expect(panel()).toHaveTextContent(table.left_out ?? "");
      }
      // The picture is explained only where there is one.
      expect(panel().textContent?.includes("The bar is")).toBe(false);
      unmount();
    }
  });

  test("test_it_has_no_fault_an_automatic_check_can_find", async () => {
    const { container } = await opened();

    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("when it cannot be read", () => {
  test("test_a_failure_is_said_in_words_with_a_way_to_try_again", async () => {
    const api = standInApi().unreachable("get_census");
    const { user } = await opened(api);

    const alert = within(panel()).getByRole("alert");
    expect(alert).toHaveTextContent(FAILURE.network);
    expect(alert).toHaveTextContent(CENSUS.failed);
    expect(panel().querySelector("table")).toBeNull();

    api.on("get_census", "census");
    await user.click(within(alert).getByRole("button", { name: CENSUS.again }));

    await waitFor(() => expect(tables()).toHaveLength(served.tables.length));
    expect(panel().querySelector("[role='alert']")).toBeNull();
  });

  test("test_a_service_that_serves_no_census_is_said_in_the_apis_words", async () => {
    const off = recordedError("census-off");
    await opened(standInApi().on("get_census", "census-off"));

    const alert = within(panel()).getByRole("alert");
    expect(alert.textContent).toBe(off.body.error.message);
    // Seen in a browser: "Try again" stood under it, and trying again brought the same answer.
    expect(within(alert).queryByRole("button")).toBeNull();
    expect(panel().querySelector("table")).toBeNull();
  });

  test("test_an_answer_that_is_not_the_contracts_is_not_drawn", async () => {
    const real = recordedAnswer("get_census", "census");
    const api = standInApi().on("get_census", () => ({
      ...real,
      body: { ...real.body, data: { area_id: "syn-n0007", rows: [{ area: "syn-n0001", share: "99%" }] } },
    }));

    await opened(api);

    expect(within(panel()).getByRole("alert")).toHaveTextContent(FAILURE.unreadable);
    expect(panel().textContent?.includes("99%")).toBe(false);
  });
});
