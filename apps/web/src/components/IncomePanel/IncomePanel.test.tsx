/**
 * The household income of an area: closed until it is pressed, asked for only then, and
 * drawn as the API sent it. It is shown and never ranked on, so nothing stands beside it.
 */

import { act, render, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderToStaticMarkup } from "react-dom/server";

import { INCOME } from "@/content/income";
import { FAILURE } from "@/content/search";
import { recordedAnswer, recordedError } from "@/lib/api/recorded";
import type { IncomeOffer } from "@/lib/api/schema";

import { BASE, standInApi, type StandIn } from "../../../test/support/api";
import { faultsIn } from "../../../test/support/axe";
import { watch } from "../../../test/support/watch";
import { IncomePanel } from "./IncomePanel";
import { INCOME_PART } from "./part";

const offer: IncomeOffer = recordedAnswer("get_meta", "meta").body.data.income;
const served = recordedAnswer("get_income", "income").body.data;
const none = recordedAnswer("get_income", "income-none-given").body.data;
const SLUG = "foxholt";

const panel = () => document.getElementById(INCOME_PART) as HTMLDetailsElement;
const opener = () => panel().querySelector("summary") as HTMLElement;
const figures = () => panel().querySelector("dl");

function show(api: StandIn = standInApi().on("get_income", "income"), slug = SLUG) {
  const view = render(<IncomePanel offer={offer} area={{ slug }} client={api.client} />);
  return { api, user: userEvent.setup({ delay: null }), ...view };
}

async function opened(api?: StandIn, slug = SLUG) {
  const shown = show(api, slug);
  await shown.user.click(opener());
  await waitFor(() => expect(panel().querySelector("[role='status']")).toBeNull());
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
    expect(panel().querySelectorAll("dl, [role='status'], [role='alert']")).toHaveLength(0);
  });

  test("test_it_is_the_browsers_own_element_under_the_heading_the_api_sent", () => {
    show();

    expect(panel().tagName).toBe("DETAILS");
    expect(opener().querySelector("h2")?.textContent).toBe(offer.heading);
    expect(panel()).toHaveTextContent(offer.intro);
    expect(panel()).toHaveAttribute("data-nosnippet");
  });

  test("test_the_page_as_it_is_built_holds_no_figure", () => {
    const built = renderToStaticMarkup(<IncomePanel offer={offer} area={{ slug: SLUG }} />);

    expect(built).toContain(offer.heading);
    for (const figure of [served.estimate, served.lower, served.upper, served.limits]) {
      expect(built.includes(figure ?? "never")).toBe(false);
    }
    expect(/£\s?\d/.test(built)).toBe(false);
    expect(built).toContain(INCOME.noScript);
  });

  test("test_where_none_is_served_nothing_is_drawn_and_nothing_is_asked_for", () => {
    const off: IncomeOffer = recordedAnswer("get_meta", "meta-no-income").body.data.income;
    const api = standInApi();
    const { container } = render(<IncomePanel offer={off} area={{ slug: SLUG }} client={api.client} />);

    expect(off.available).toBe(false);
    expect(container.innerHTML).toBe("");
    expect(api.calls).toEqual([]);
  });
});

describe("opening it", () => {
  test("test_it_asks_once_for_this_area_and_sends_nothing_else", async () => {
    const { api, user } = await opened();

    expect(api.unexpected).toEqual([]);
    expect(api.calls.map((call) => [call.method, call.url])).toEqual([["GET", `${BASE}/v1/areas/${SLUG}/income`]]);
    expect(api.calls[0]?.sent).toBeNull();
    // Closed and opened again, the answer in hand is shown. Nothing is asked twice.
    await user.click(opener());
    await user.click(opener());
    expect(panel().open).toBe(true);
    expect(api.calls).toHaveLength(1);
  });

  test("test_the_answer_may_not_be_kept_and_says_nothing_of_the_page", async () => {
    const { api } = await opened();
    const { init } = api.lastCallTo("get_income");

    expect(init.cache).toBe("no-store");
    expect(init.credentials).toBe("omit");
    expect(init.referrerPolicy).toBe("no-referrer");
    expect(new URL(api.lastCallTo("get_income").url).search).toBe("");
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
    const held = api.hold("get_income", "income");
    const { user } = show(api);

    await user.click(opener());

    expect(within(panel()).getByRole("status")).toHaveTextContent(INCOME.loading);
    expect(figures()).toBeNull();
    await act(async () => {
      held.release();
      await Promise.resolve();
    });
    await waitFor(() => expect(figures()).not.toBeNull());
    expect(panel().querySelector("[role='status']")).toBeNull();
  });

  test("test_it_is_opened_by_the_link_that_names_it", async () => {
    const { api } = show();

    act(() => {
      window.location.hash = `#${INCOME_PART}`;
      window.dispatchEvent(new HashChangeEvent("hashchange"));
    });

    expect(panel().open).toBe(true);
    await waitFor(() => expect(api.callsTo("get_income")).toHaveLength(1));
  });

  test("test_what_is_asked_for_is_let_go_when_the_page_is_left", async () => {
    const api = standInApi().silent("get_income");
    const { user, unmount } = show(api);
    await user.click(opener());

    unmount();

    expect(api.lastCallTo("get_income").init.signal?.aborted).toBe(true);
  });
});

describe("what is drawn", () => {
  test("test_the_figure_its_limits_its_year_and_its_source_are_the_apis_as_they_came", async () => {
    await opened();
    const names = [...panel().querySelectorAll("dt")].map((name) => name.textContent);
    const values = [...panel().querySelectorAll("dd")].map((value) => value.textContent);

    expect(names).toEqual([served.kind, served.limits_label]);
    expect(values).toEqual([served.estimate, served.limits]);
    for (const said of [
      served.year_line,
      served.modelled,
      served.definition,
      served.source_line,
      served.licence_line,
      ...served.notes,
    ]) {
      expect(panel()).toHaveTextContent(said);
    }
    expect([...panel().querySelectorAll("ol > li")].map((note) => note.textContent)).toEqual(served.notes);
  });

  test("test_it_says_that_it_is_an_estimate_from_a_model_and_of_which_year", async () => {
    await opened();

    expect(served.modelled).toMatch(/model/);
    expect(panel()).toHaveTextContent(served.modelled);
    expect(panel().querySelector("p")?.textContent).toBe(offer.intro);
    expect(panel()).toHaveTextContent(served.year_line);
  });

  test("test_nothing_stands_beside_the_figure_and_nothing_is_drawn_of_it", async () => {
    await opened();

    // No bar, no scale, no picture and no table of other areas. One figure, in words.
    expect(panel().querySelectorAll("svg, img, canvas, table, meter, progress, [role='img']")).toHaveLength(0);
    expect(panel().querySelectorAll("dd")).toHaveLength(2);
    expect(panel().querySelectorAll("a[href*='compare'], a[href*='search'], button")).toHaveLength(0);
    const shown = (panel().textContent ?? "").match(/£[\d,]+/g) ?? [];
    expect(new Set(shown)).toEqual(new Set([served.estimate, served.lower, served.upper]));
  });

  test("test_an_area_with_no_estimate_says_so_in_the_apis_words_and_shows_no_figure", async () => {
    await opened(standInApi().on("get_income", "income-none-given"), "otterby-fields");

    expect(none.estimate).toBeNull();
    expect([...panel().querySelectorAll("dd")].map((value) => value.textContent)).toEqual([none.none_given]);
    expect(/£/.test(panel().textContent ?? "")).toBe(false);
  });

  test("test_a_made_up_source_has_no_page_to_open_and_a_real_one_is_opened_with_no_referrer", async () => {
    await opened();
    expect(served.source_url).toBe("");
    expect(panel().querySelectorAll("a")).toHaveLength(0);

    const real = recordedAnswer("get_income", "income");
    const api = standInApi().on("get_income", () => ({
      ...real,
      body: { ...real.body, data: { ...real.body.data, source_url: "https://statistics.example/income" } },
    }));
    document.body.innerHTML = "";
    await opened(api);

    const link = within(panel()).getByRole("link", { name: served.open_source });
    expect(link).toHaveAttribute("href", "https://statistics.example/income");
    expect(link).toHaveAttribute("rel", "noreferrer noopener");
  });

  test("test_an_address_that_is_not_https_is_never_a_link", async () => {
    const real = recordedAnswer("get_income", "income");
    for (const address of ["javascript:alert(1)", "http://statistics.example/", "data:text/html,x", "//x"]) {
      const api = standInApi().on("get_income", () => ({
        ...real,
        body: { ...real.body, data: { ...real.body.data, source_url: address } },
      }));
      const { unmount } = await opened(api);
      expect(panel().querySelectorAll("a")).toHaveLength(0);
      unmount();
    }
  });

  test("test_the_panel_has_no_fault_a_checker_can_find", async () => {
    const { container } = await opened();

    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("when it cannot be read", () => {
  test("test_a_failure_is_said_in_words_with_a_way_to_try_again", async () => {
    const api = standInApi().unreachable("get_income");
    const { user } = await opened(api);

    const alert = within(panel()).getByRole("alert");
    expect(alert).toHaveTextContent(FAILURE.network);
    expect(alert).toHaveTextContent(INCOME.failed);
    expect(figures()).toBeNull();

    api.on("get_income", "income");
    await user.click(within(alert).getByRole("button", { name: INCOME.again }));

    await waitFor(() => expect(figures()).not.toBeNull());
    expect(panel().querySelector("[role='alert']")).toBeNull();
  });

  test("test_a_service_that_serves_none_is_said_in_the_apis_words", async () => {
    const off = recordedError("income-off");
    await opened(standInApi().on("get_income", "income-off"));

    const alert = within(panel()).getByRole("alert");
    expect(alert.textContent).toBe(off.body.error.message);
    expect(within(alert).queryByRole("button")).toBeNull();
    expect(figures()).toBeNull();
  });

  test("test_an_answer_that_is_not_the_contracts_is_not_drawn", async () => {
    const real = recordedAnswer("get_income", "income");
    const api = standInApi().on("get_income", () => ({
      ...real,
      body: { ...real.body, data: { area_id: "syn-n0007", rank: 3, estimate: "£99,999" } },
    }));

    await opened(api);

    expect(within(panel()).getByRole("alert")).toHaveTextContent(FAILURE.unreadable);
    expect(panel().textContent?.includes("99,999")).toBe(false);
  });
});
