import { act, render, screen } from "@testing-library/react";
import type { ReactElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";

import AreaPage from "@/app/[city]/[area]/page";
import AccessibilityPage from "@/app/accessibility/page";
import ComparePage from "@/app/compare/page";
import ErrorPage from "@/app/error";
import GlobalError from "@/app/global-error";
import MethodsPage from "@/app/methods/page";
import NotFound, { metadata as notFoundMetadata } from "@/app/not-found";
import HomePage, { metadata as homeMetadata } from "@/app/page";
import SharedPage from "@/app/s/page";
import SourcesPage from "@/app/sources/page";
import VibesPage from "@/app/vibes/page";
import { Shell } from "@/components/Shell/Shell";
import { ACCESSIBILITY } from "@/content/accessibility";
import { BANNER, FAULT, NOT_FOUND, SITE } from "@/content/site";
import { VIBES } from "@/content/vibes";
import { recordedAnswer } from "@/lib/api/recorded";
import { forgetSynthetic, noteSynthetic, syntheticSeen } from "@/lib/api/synthetic";

import { faultsIn } from "./support/axe";
import { arrived } from "./support/search";

jest.mock("next/navigation", () => ({ usePathname: () => "/" }));

const { meta, data } = recordedAnswer("get_meta", "meta").body;

const PAGES: readonly (readonly [string, () => ReactElement | Promise<ReactElement>])[] = [
  ["the home page", HomePage],
  ["the page of an area", () => AreaPage({ params: Promise.resolve({ city: "synthetic", area: "alderwick" }) })],
  // With no address set for the API the browser's client sends nothing, so these are as they are built.
  ["a comparison", () => ComparePage({ searchParams: Promise.resolve({ a: ["alderwick", "pellam-cross"] }) })],
  ["the page a shared link opens", SharedPage],
  ["the vibes", VibesPage],
  ["methods", MethodsPage],
  ["data sources", SourcesPage],
  ["the accessibility statement", AccessibilityPage],
  ["not found", NotFound],
  ["the error page", () => <ErrorPage reset={() => undefined} />],
];

async function show(page: () => ReactElement | Promise<ReactElement>) {
  const view = render(<Shell meta={meta}>{await page()}</Shell>);
  // What a page asks for as soon as it is drawn is let arrive, so that the page is as a person finds it.
  await arrived();
  return view;
}

describe.each(PAGES)("%s", (_, page) => {
  test("test_the_page_has_one_main_heading", async () => {
    await show(page);

    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
  });

  test("test_the_page_carries_the_banner_that_says_the_data_is_made_up", async () => {
    await show(page);

    expect(screen.getByRole("region", { name: BANNER.label })).toHaveTextContent(BANNER.text);
  });

  test("test_the_page_has_no_accessibility_fault", async () => {
    const { container } = await show(page);

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });

  test("test_everything_on_the_page_can_be_reached_by_keyboard", async () => {
    const { container } = await show(page);

    // Every control is a native link or button, and none is taken out of the tab order.
    const controls = [...container.querySelectorAll("a, button, input, select, textarea")];
    const unreachable = controls.filter(
      (control) =>
        control.getAttribute("tabindex") === "-1" ||
        (control.tagName === "A" && !control.hasAttribute("href")),
    );
    const madeUp = container.querySelectorAll("[role='button'], [role='link'], [onclick]");

    expect(controls.length).toBeGreaterThan(0);
    expect(unreachable).toEqual([]);
    expect([...madeUp]).toEqual([]);
  });

  test("test_nothing_on_the_page_comes_from_another_origin", async () => {
    const { container } = await show(page);

    const loaded = [...container.querySelectorAll("[src], link[href], [srcset], [poster]")];

    expect(loaded).toEqual([]);
  });

  test("test_every_table_on_the_page_says_what_it_is_a_table_of", async () => {
    const { container } = await show(page);

    const unnamed = [...container.querySelectorAll("table")].filter((table) => {
      const named = (table.getAttribute("aria-labelledby") ?? "")
        .split(/\s+/)
        .some((id) => id !== "" && (document.getElementById(id)?.textContent ?? "").trim() !== "");
      const caption = (table.querySelector("caption")?.textContent ?? "").trim() !== "";
      return !named && !caption && !(table.getAttribute("aria-label") ?? "").trim();
    });

    expect(unnamed.map((table) => table.textContent?.slice(0, 60))).toEqual([]);
  });

  test("test_a_link_that_stands_alone_takes_a_target_size", async () => {
    const { container } = await show(page);

    // A link in a sentence is sized by its line, as the guidelines allow. One that is
    // all there is of its paragraph, its cell or its item is a control like any other.
    const alone = [...container.querySelectorAll<HTMLAnchorElement>("a[href]")].filter((link) => {
      const around = link.closest("p, li, dd, td, th");
      return around === null || around.textContent?.trim() === link.textContent?.trim();
    });
    const unsized = alone.filter((link) => !link.matches(".target, .target-min"));

    expect(alone.length).toBeGreaterThan(0);
    expect(unsized.map((link) => link.textContent)).toEqual([]);
  });

  test("test_no_link_to_an_area_a_source_or_a_comparison_is_fetched_ahead_of_time", async () => {
    const { container } = await show(page);

    // Fetched ahead, a link tells the website's own server what a person may read next.
    // The links of the header and the footer are on every page, and tell it nothing.
    const telling = [...container.querySelectorAll<HTMLAnchorElement>("main a[href]")].filter((link) =>
      /^\/(sources|compare|synthetic|london)(\/|#|\?|$)/.test(link.getAttribute("href") ?? ""),
    );
    const ahead = telling.filter((link) => link.getAttribute("data-prefetch") !== "false");

    expect(ahead.map((link) => link.getAttribute("href"))).toEqual([]);
  });

  test("test_a_page_built_on_made_up_data_tells_the_tab_so", async () => {
    forgetSynthetic();

    await show(page);

    // The page for a fault in the layout has no shell to tell it, and asks this.
    expect(syntheticSeen()).toBe(true);
  });
});

describe("the pages built from the API", () => {
  test("test_the_methods_page_holds_every_feature_of_the_release", async () => {
    await show(MethodsPage);

    for (const metric of data.features) {
      expect(screen.getByRole("heading", { name: metric.label })).toBeInTheDocument();
    }
    expect(data.features).toHaveLength(109);
  });

  test("test_the_vibes_page_holds_every_vibe_of_the_release_with_its_recipe", async () => {
    await show(VibesPage);

    for (const tag of data.tags) {
      expect(screen.getByRole("heading", { level: 2, name: tag.label })).toBeInTheDocument();
      expect(screen.getByRole("table", { name: VIBES.recipe.caption(tag.label) })).toBeInTheDocument();
    }
    expect(data.tags).toHaveLength(14);
  });

  test("test_the_sources_page_holds_every_source_of_the_release", async () => {
    await show(SourcesPage);

    for (const source of data.attributions) {
      expect(screen.getByRole("article", { name: source.name })).toHaveTextContent(
        source.attribution,
      );
    }
    expect(data.attributions.length).toBeGreaterThan(0);
  });
});

describe("the accessibility statement", () => {
  test("test_the_statement_says_what_has_not_been_tested", async () => {
    await show(AccessibilityPage);

    for (const gap of ACCESSIBILITY.notTested.points) {
      expect(screen.getByText(gap)).toBeInTheDocument();
    }
    expect(screen.getByRole("main")).toHaveTextContent("It has not been audited");
    expect(ACCESSIBILITY.notTested.points.join(" ")).toMatch(/screen reader/);
    expect(ACCESSIBILITY.notTested.points.join(" ")).toMatch(/200%/);
    expect(ACCESSIBILITY.notTested.points.join(" ")).toMatch(/320 pixels/);
    expect(ACCESSIBILITY.notTested.points.join(" ")).toMatch(/Forced colours/);
    // What is stacked on a narrow screen was laid out by reading its styles, and seen by nobody.
    expect(ACCESSIBILITY.notTested.points.join(" ")).toMatch(/journeys of a result/);
  });

  test("test_nothing_is_said_to_have_been_tested_by_hand_that_has_not_been", () => {
    // The website has been opened in a browser, and what was found there was put right.
    // That was not a test of anything listed here, so nothing has been taken off the list.
    expect(ACCESSIBILITY.notTested.points).toEqual(
      expect.arrayContaining([
        "Use with a screen reader.",
        "Text at 200% zoom.",
        "Reflow on a screen 320 pixels wide.",
        "Forced colours and high contrast modes.",
        "The real size of each control on a touch screen.",
        "The map, used by keyboard alone.",
        "The comparison of areas on a narrow screen, where its rows are stacked.",
        "Copying the link to a shared search, in a real browser.",
      ]),
    );
  });

  test("test_the_statement_says_what_is_known_to_fall_short", async () => {
    await show(AccessibilityPage);

    // The page a fault in the server shows is the framework's, and sets no language.
    expect(screen.getByRole("heading", { name: ACCESSIBILITY.short.title })).toBeInTheDocument();
    for (const fault of ACCESSIBILITY.short.points) expect(screen.getByText(fault)).toBeInTheDocument();
    expect(ACCESSIBILITY.short.points.join(" ")).toMatch(/language/);
    // The table of every area is stacked on a narrow screen now, as the other tables are, so the
    // statement no longer says that it is not. It says that nobody has seen it on a phone.
    expect(ACCESSIBILITY.short.points.join(" ")).not.toMatch(/table of every area/);
    expect(ACCESSIBILITY.built.points.join(" ")).toMatch(/each area of the table is a block/);
    expect(ACCESSIBILITY.notTested.points.join(" ")).toMatch(/table of every area on a narrow screen/);
    // Nor do the chips stand on one line that scrolls sideways.
    expect(ACCESSIBILITY.short.points.join(" ")).not.toMatch(/scroll sideways/);
    // What a phone does not draw, so that the answer comes first, is said as a shortfall.
    expect(ACCESSIBILITY.short.points.join(" ")).toMatch(/kept for a screen reader and are not drawn/);
    // The scale of a slider is drawn now, so the statement no longer says that it is not.
    expect(ACCESSIBILITY.short.points.join(" ")).not.toMatch(/scale of a slider/);
    expect(ACCESSIBILITY.built.points.join(" ")).toMatch(/0 and 100 mean/);
  });

  test("test_the_statement_says_what_the_page_does_with_the_focus_and_no_more", async () => {
    await show(AccessibilityPage);

    // Found in a browser and put right: the focus was left on nothing in four places.
    const built = ACCESSIBILITY.built.points.join(" ");
    expect(built).toMatch(/Focus is always visible/);
    expect(built).toMatch(/never left on nothing/);
    for (const point of ACCESSIBILITY.built.points) expect(screen.getByText(point)).toBeInTheDocument();
  });

  test("test_the_statement_invents_no_address_to_report_a_problem_to", async () => {
    const { container } = await show(AccessibilityPage);

    const main = screen.getByRole("main");

    expect(main).toHaveTextContent(ACCESSIBILITY.report.noAddressYet);
    expect(main.querySelectorAll("a[href^='mailto:'], a[href^='http']")).toHaveLength(0);
    expect(container.textContent).not.toMatch(/[\w.]+@[\w.]+\.\w+/);
  });
});

describe("the error page", () => {
  test("test_the_error_boundary_says_fixed_words_and_reports_nothing", async () => {
    const canary = "zqxcanary7431";
    const written: unknown[][] = [];
    for (const method of ["log", "info", "warn", "error", "debug"] as const) {
      jest.spyOn(console, method).mockImplementation((...args) => void written.push(args));
    }
    const props = { error: new Error(`could not read: ${canary}`), reset: jest.fn() };

    const { container } = render(<ErrorPage {...props} />);

    expect(screen.getByRole("alert")).toHaveTextContent(`${FAULT.title}${FAULT.text}`);
    expect(container.innerHTML).not.toContain(canary);
    expect(written).toEqual([]);
  });

  test("test_trying_again_is_a_button_of_full_size", async () => {
    const reset = jest.fn();
    render(<ErrorPage reset={reset} />);

    const retry = screen.getByRole("button", { name: FAULT.retry });
    retry.click();

    expect(retry).toHaveClass("target");
    expect(reset).toHaveBeenCalledTimes(1);
  });

  test("test_trying_again_asks_for_the_page_again_where_it_can", async () => {
    const asked = { retry: jest.fn(), reset: jest.fn() };
    render(<ErrorPage {...asked} />);

    screen.getByRole("button", { name: FAULT.retry }).click();

    // Drawing again what is in hand would only fail again. The page is asked for again.
    expect(asked.retry).toHaveBeenCalledTimes(1);
    expect(asked.reset).not.toHaveBeenCalled();
  });
});

describe("the page for a fault in the layout", () => {
  beforeEach(forgetSynthetic);

  function built(): Document {
    const markup = renderToStaticMarkup(<GlobalError reset={() => undefined} />);
    return new DOMParser().parseFromString(`<!DOCTYPE html>${markup}`, "text/html");
  }

  test("test_it_is_a_whole_page_in_a_stated_language_with_a_title_of_its_own", () => {
    const page = built();

    expect(page.documentElement.getAttribute("lang")).toBe("en-GB");
    expect(page.title).toBe(`${FAULT.title} · ${SITE.name}`);
    expect(page.querySelectorAll("h1")).toHaveLength(1);
    expect(page.querySelectorAll("main")).toHaveLength(1);
    expect(page.querySelector("meta[name='robots']")?.getAttribute("content")).toBe("noindex, nofollow");
    expect(page.querySelector("meta[name='referrer']")?.getAttribute("content")).toBe("no-referrer");
  });

  test("test_it_says_fixed_words_and_reports_nothing", () => {
    const canary = "zqxcanary7431";
    const written: unknown[][] = [];
    for (const method of ["log", "info", "warn", "error", "debug"] as const) {
      jest.spyOn(console, method).mockImplementation((...args) => void written.push(args));
    }
    const props = { error: new Error(`could not read: ${canary}`), reset: jest.fn() };

    const markup = renderToStaticMarkup(<GlobalError {...props} />);

    expect(markup).toContain(FAULT.title);
    expect(markup).toContain(FAULT.text);
    expect(markup.includes(canary)).toBe(false);
    expect(written).toEqual([]);
  });

  test("test_it_loads_nothing_from_another_origin_and_holds_no_form", () => {
    const page = built();

    expect([...page.querySelectorAll("[src], link[href], form, svg, img")]).toEqual([]);
  });

  test("test_trying_again_is_a_button_of_full_size", () => {
    const page = built();

    const [retry, ...others] = [...page.querySelectorAll("button")];

    expect(retry?.textContent).toBe(FAULT.retry);
    expect(retry?.getAttribute("type")).toBe("button");
    expect(retry?.classList.contains("target")).toBe(true);
    expect(others).toEqual([]);
  });

  test("test_it_carries_the_banner_once_the_tab_has_been_told_the_data_is_made_up", () => {
    // Drawn without its document, which a test has already: the banner is what is looked for.
    const spared = jest.spyOn(console, "error").mockImplementation(() => undefined);
    const { container } = render(<GlobalError reset={() => undefined} />);
    expect(container.textContent?.includes(BANNER.text)).toBe(false);

    act(() => noteSynthetic(true));

    expect(container.textContent?.includes(BANNER.text)).toBe(true);
    spared.mockRestore();
  });

  test("test_with_nothing_known_of_the_data_it_says_nothing_of_it", () => {
    const page = built();

    expect(page.body.textContent?.includes(BANNER.text)).toBe(false);
    // It shows no figure and names no place, so there is nothing to mistake for a fact.
    expect(/\d/.test(page.body.textContent ?? "")).toBe(false);
  });
});

describe("the search page", () => {
  test("test_its_title_says_what_the_page_is_for_as_its_heading_does", async () => {
    await show(HomePage);

    const heading = screen.getByRole("heading", { level: 1 }).textContent;
    expect(homeMetadata.title).toEqual({ absolute: `${heading} · ${SITE.name}` });
  });
});

describe("a page that is not there", () => {
  test("test_its_title_says_so_and_is_not_the_title_of_the_search", () => {
    expect(notFoundMetadata.title).toBe(NOT_FOUND.title);
    expect(notFoundMetadata.title).not.toBe(SITE.name);
  });

  test("test_the_way_back_is_a_link_of_full_size", async () => {
    await show(NotFound);

    expect(screen.getByRole("link", { name: NOT_FOUND.back })).toHaveClass("target");
  });
});
