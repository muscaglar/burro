import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";

import AreaPage from "@/app/[city]/[area]/page";
import ComparePage from "@/app/compare/page";
import ErrorPage from "@/app/error";
import GlobalError from "@/app/global-error";
import MethodsPage from "@/app/methods/page";
import NotFound, { metadata as notFoundMetadata } from "@/app/not-found";
import HomePage, { metadata as homeMetadata } from "@/app/page";
import SharedPage from "@/app/s/page";
import SourcesPage from "@/app/sources/page";
import VibesPage from "@/app/vibes/page";
import { AT_REST } from "@/components/kit/Burro/look";
import { Shell } from "@/components/Shell/Shell";
import { BANNER, FAULT, NOT_FOUND, SITE } from "@/content/site";
import { VIBES } from "@/content/vibes";
import { WAYS } from "@/content/ways";
import { ROUTES } from "@/lib/api/operations";
import { recordedAnswer } from "@/lib/api/recorded";
import { loadMeta } from "@/lib/api/server";
import { paths } from "@/lib/paths";
import { forgetSynthetic, noteSynthetic, syntheticSeen } from "@/lib/api/synthetic";

import { faultsIn } from "./support/axe";
import { asWritten } from "./support/contrast";
import { rulesOf } from "./support/css";
import { ROUGH, service } from "./support/rough";
import { arrived } from "./support/search";

const SRC = path.resolve(__dirname, "..", "src");

jest.mock("next/navigation", () => ({ usePathname: () => "/" }));

// A page reads the release as it is built. It reads it as it was recorded, but where a test
// has the service say of a rough guide what one said until it stopped.
jest.mock("@/lib/api/server", () =>
  jest
    .requireActual<typeof import("./support/rough")>("./support/rough")
    .asAPageReads(jest.requireActual<typeof import("@/lib/api/server")>("@/lib/api/server")),
);

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

    // Every control is a native link or button, and none is taken out of the order of the
    // keyboard but a tab that is not chosen. The keyboard stops at the chosen tab of a list,
    // and the arrow keys, Home and End lead from it to the others: so Tab goes from the
    // tabs into what the chosen one shows.
    const controls = [...container.querySelectorAll("a, button, input, select, textarea")];
    const besideTheChosen = controls.filter((control) => {
      const chosen = [...(control.closest("[role='tablist']")?.querySelectorAll("[role='tab'][aria-selected='true']") ?? [])];
      return (
        control.getAttribute("role") === "tab" &&
        control.getAttribute("aria-selected") === "false" &&
        chosen.length === 1 &&
        chosen.every((tab) => tab.tagName === "BUTTON" && tab.getAttribute("tabindex") === "0")
      );
    });
    const unreachable = controls.filter(
      (control) =>
        (control.getAttribute("tabindex") === "-1" && !besideTheChosen.includes(control)) ||
        (control.tagName === "A" && !control.hasAttribute("href")),
    );
    // A tab is a native button that says it is a tab. Nothing else is made to be pressed by a role alone.
    const madeUp = container.querySelectorAll("[role='button'], [role='link'], [onclick], [role='tab']:not(button)");

    expect(controls.length).toBeGreaterThan(0);
    expect(unreachable).toEqual([]);
    expect([...madeUp]).toEqual([]);
    // Every list of tabs has a tab that is chosen, where the keyboard stops, and the panel of each is on the page.
    for (const list of container.querySelectorAll("[role='tablist']")) {
      const tabs = [...list.querySelectorAll("[role='tab']")];
      expect(tabs.filter((tab) => tab.getAttribute("aria-selected") === "true")).toHaveLength(1);
      expect(tabs.map((tab) => tab.getAttribute("tabindex"))).toEqual(
        tabs.map((tab) => (tab.getAttribute("aria-selected") === "true" ? "0" : "-1")),
      );
      for (const tab of tabs) {
        expect(document.getElementById(tab.getAttribute("aria-controls") ?? "")?.getAttribute("role")).toBe("tabpanel");
      }
    }
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

  test("test_nothing_moves_without_end_on_the_page_but_the_rabbit_who_is_dress_and_takes_no_press", async () => {
    const { container } = await show(page);

    // Burro is the one thing that moves without end, wherever he is drawn: in the page, or
    // in the name board of every page where the look draws him there. The founder asked
    // for the button that stopped him to go, and relies on what a person has set in their
    // system: where it asks for less movement his style sheet stills him. So he is dress
    // and nothing else. No keyboard stops at him and no screen reader hears him, and
    // nothing of the page is said or done by him alone.
    const moving = [...container.querySelectorAll<HTMLElement>("[data-pose]")].filter(
      (he) => he.querySelector("[data-moves='true']") !== null,
    );

    expect(container.querySelectorAll("[data-moves='true']")).toHaveLength(moving.length);
    for (const he of moving) {
      expect(he).toHaveAttribute("aria-hidden", "true");
      expect(he.textContent).toBe("");
      expect(he.querySelectorAll("button, a, input, select, textarea, [tabindex], [role]")).toHaveLength(0);
    }
    expect([...container.querySelectorAll("button")].filter((button) => /rabbit/i.test(button.getAttribute("aria-label") ?? ""))).toEqual([]);
  });

  test("test_the_foot_of_the_page_leads_to_what_is_said_of_what_a_person_types", async () => {
    await show(page);

    // The link and the lines under the search box are gone. What is typed, where it goes and
    // that it is not kept is said among the methods, and every page leads to it from its foot.
    const foot = within(screen.getByRole("contentinfo"));
    const way = foot.getAllByRole("link").filter((link) => link.getAttribute("href") === paths.methods("words"));

    expect(way).toHaveLength(1);
    expect(way[0]).toHaveAccessibleName("Privacy: How your words are handled");
    expect(way[0]).toHaveClass("target");
  });

  test("test_nothing_on_the_page_leads_to_a_statement_of_accessibility_and_the_page_claims_no_standard", async () => {
    const { container } = await show(page);

    // The website said that it aimed to meet a standard, on a page of its own that every
    // page led to. The founder asked for the page to go, and the claim went with it.
    const links = [...container.querySelectorAll("a[href]")];
    expect(links.length).toBeGreaterThan(0);
    expect(links.filter((link) => /accessib/i.test(`${link.getAttribute("href")} ${link.textContent}`)).map((link) => link.getAttribute("href"))).toEqual([]);
    expect(/\bWCAG\b|Web Content Accessibility Guidelines|\blevel AA\b|accessibility statement/i.test(container.textContent ?? "")).toBe(false);
  });

  test("test_nothing_on_the_page_says_that_a_vibe_is_a_rough_guide_or_that_it_is_less_sure", async () => {
    // The service says which vibe is less sure, in a code, and no word more. One that is
    // older than the website, or later, may say its label and why: so the page is built on
    // a release that says both. The founder asked for none of it to be passed on: no label,
    // no sentence, and nothing drawn as either.
    service.saysSo = true;
    const { container } = await show(page);

    expect(data.tags.filter((tag) => tag.sureness === "rough_guide").map((tag) => tag.tag_id)).toEqual([ROUGH.tag_id]);
    expect([data.rough_guides, (await loadMeta()).data.rough_guides]).toEqual([[], [ROUGH]]);
    const said = container.textContent ?? "";
    expect(said.length).toBeGreaterThan(200);
    expect([said.includes(ROUGH.label), said.includes(ROUGH.why)]).toEqual([false, false]);
    expect(/rough guide|less sure/i.test(said)).toBe(false);
    expect(container.querySelectorAll("[data-rough-guide]")).toHaveLength(0);
    // Nor is it said to whoever hears the page and sees none of it, or under the pointer.
    const heard = [...container.querySelectorAll("*")].flatMap((part) =>
      ["aria-label", "aria-description", "aria-roledescription", "aria-valuetext", "title", "alt", "placeholder"].flatMap((name) => part.getAttribute(name) ?? []),
    );
    expect(heard.length).toBeGreaterThan(0);
    expect(heard.filter((words) => /rough guide|less sure/i.test(words) || words.includes(ROUGH.label) || words.includes(ROUGH.why))).toEqual([]);
  });

  test("test_a_page_built_on_made_up_data_tells_the_tab_so", async () => {
    forgetSynthetic();

    await show(page);

    // The page for a fault in the layout has no shell to tell it, and asks this.
    expect(syntheticSeen()).toBe(true);
  });
});

describe("what a page hands the part of it that runs in the browser", () => {
  test.each([
    ["the home page", HomePage],
    ["the page a shared link opens", SharedPage],
  ] as const)("test_it_is_handed_the_release_without_what_the_service_says_of_a_rough_guide: %s", async (_, page) => {
    // What a part that runs in the browser is handed is written into the page as it is
    // sent. Both pages handed the whole of route 11, and so the label of a rough guide and
    // the sentence that says why, which no page draws. The service says neither since, and
    // one may again: so the page is built on a release that says both.
    service.saysSo = true;
    const built = (await page()) as ReactElement<{ meta: Record<string, unknown> }>;
    const sent = JSON.stringify(built.props);
    const { data: told } = await loadMeta();

    expect([data.rough_guides, told.rough_guides]).toEqual([[], [ROUGH]]);
    expect("rough_guides" in built.props.meta).toBe(false);
    expect([sent.includes(ROUGH.label), sent.includes(ROUGH.why)]).toEqual([false, false]);
    // The rest of what the service said is handed as it came.
    const { rough_guides: left, ...rest } = told;
    expect(left).toEqual([ROUGH]);
    expect(Object.keys(built.props.meta).sort()).toEqual(Object.keys(rest).sort());
    expect(JSON.stringify(built.props.meta) === JSON.stringify(rest)).toBe(true);
  });
});

describe("the pages built from the API", () => {
  test("test_the_methods_page_holds_every_feature_of_the_release", async () => {
    await show(MethodsPage);

    for (const metric of data.features) {
      expect(screen.getByRole("heading", { name: metric.label })).toBeInTheDocument();
    }
    expect(data.features).toHaveLength(110);
  });

  test("test_the_vibes_page_holds_every_vibe_of_the_release_with_its_recipe", async () => {
    await show(VibesPage);

    for (const tag of data.tags) {
      expect(screen.getByRole("heading", { level: 3, name: tag.label })).toBeInTheDocument();
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

describe("the statement of accessibility, which is gone", () => {
  /** Every file under a folder of the website, by its path from that folder. */
  const under = (folder: string, from = folder): string[] =>
    readdirSync(folder, { withFileTypes: true }).flatMap((entry) =>
      entry.isDirectory() ? under(path.join(folder, entry.name), from) : [path.relative(from, path.join(folder, entry.name))],
    );

  test("test_the_website_has_no_page_of_it_no_words_of_it_and_builds_no_address_for_it", () => {
    expect(under(path.join(SRC, "app")).filter((file) => /accessib/i.test(file))).toEqual([]);
    expect(under(path.join(SRC, "content")).filter((file) => /accessib/i.test(file))).toEqual([]);
    expect(Object.keys(paths).filter((name) => /accessib/i.test(name))).toEqual([]);
    expect(Object.keys(SITE.nav)).toEqual(["vibes", "methods", "sources"]);
  });

  test("test_nothing_that_is_drawn_names_its_address_or_says_that_the_website_meets_a_standard", () => {
    // What is said to whoever reads the code is drawn on no page, and is not read here.
    const drawn = under(SRC)
      .filter((file) => /\.tsx?$/.test(file) && !/\.test\.tsx?$/.test(file) && !file.startsWith(path.join("lib", "api")))
      .map((file) => [file, readFileSync(path.join(SRC, file), "utf8").replace(/\/\*[\s\S]*?\*\/|(?<![:"'`])\/\/.*$/gm, "")] as const);

    expect(drawn.length).toBeGreaterThan(200);
    expect(drawn.filter(([, code]) => /["'`]\/accessibility\b|paths\.accessibility|nav\.accessibility/.test(code)).map(([file]) => file)).toEqual([]);
    expect(drawn.filter(([, code]) => /\bWCAG\b|Web Content Accessibility Guidelines|\blevel AA\b/.test(code)).map(([file]) => file)).toEqual([]);
  });
});

describe("what was built for whoever presses, reads and waits, which stays", () => {
  test("test_the_sizes_of_what_is_pressed_and_read_and_the_length_of_a_wait_are_what_they_were", () => {
    // The statement named these figures, and each was worked out here from where it is set,
    // so that the statement was found out the day one of them changed. The statement is
    // gone. What it said was built is built still, and is held as it was.
    const tokens = asWritten();
    const pixels = (token: string) => Number.parseInt(tokens[token] ?? "", 10);
    const row = rulesOf(readFileSync(path.join(SRC, "components", "ChipRow", "ChipRow.module.css"), "utf8"));
    /** What is pressed in a chip of a narrow row: a main control, less four art pixels. */
    const press = row.filter((rule) => rule.sets.has("--press")).map((rule) => rule.sets.get("--press"));
    /** The button that opens the chips that are folded is as high as what is pressed in a chip. */
    const rest = row.filter((rule) => rule.selector === ".rest" && /max-width/.test(rule.under ?? "")).map((rule) => rule.sets.get("--target"));

    // A main control, the least a control may be, and what is pressed in a chip on a narrow screen.
    expect([pixels("--target"), pixels("--target-min"), pixels("--target") - pixels("--px") * 4]).toEqual([44, 24, 36]);
    expect(press).toEqual(["calc(var(--target) - var(--px) * 4)"]);
    expect(rest).toEqual(["var(--press)"]);
    // A short label is set in the face of names at the least of its four sizes, and a name at the next.
    expect([Number.parseFloat(tokens["--name-1"] ?? "") * 16, Number.parseFloat(tokens["--name-2"] ?? "") * 16]).toEqual([20, 30]);
    // Nothing moves unless movement is welcome, and a ranking is waited for as long as this and no longer.
    expect(tokens["--motion-hop"]).toBe("0ms");
    expect(ROUTES.rank.timeoutMs).toBeLessThanOrEqual(5_000);
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

  test("test_it_opens_on_two_ways_in_as_tabs_with_the_first_chosen_and_the_other_a_key_away", async () => {
    await show(HomePage);
    const user = userEvent.setup({ delay: null });
    const tabs = within(screen.getByRole("tablist", { name: WAYS.label })).getAllByRole("tab");

    expect(tabs.map((tab) => [tab.textContent, tab.getAttribute("aria-selected")])).toEqual([
      [WAYS.quick, "true"],
      [WAYS.deep, "false"],
    ]);
    // The tab that is not chosen is no stop of Tab, and is reached from the chosen one by an arrow key.
    tabs[0]?.focus();
    await user.keyboard("{ArrowRight}");
    expect(tabs[1]).toHaveFocus();
    expect(tabs.map((tab) => tab.getAttribute("aria-selected"))).toEqual(["false", "true"]);
    expect(tabs.map((tab) => tab.getAttribute("tabindex"))).toEqual(["-1", "0"]);
    // And back, by the same key: the keys go round.
    await user.keyboard("{ArrowRight}");
    expect(tabs[0]).toHaveFocus();
    expect(tabs.map((tab) => tab.getAttribute("aria-selected"))).toEqual(["true", "false"]);
  });

  test("test_the_rabbit_of_the_first_page_moves_where_he_sits_and_no_button_stands_by_him", async () => {
    const { container } = await show(HomePage);
    const user = userEvent.setup({ delay: null });
    const drawn = [...container.querySelectorAll<HTMLElement>("[data-pose]")];
    const moves = (he: HTMLElement) => he.querySelector("[data-moves='true']") !== null;

    // Before a search he sits: beside the heading, and in the name board where the look
    // draws him there. He is one rabbit, however many times he is drawn.
    expect(drawn.length).toBeGreaterThanOrEqual(1);
    expect(new Set(drawn.map((he) => he.getAttribute("data-pose")))).toEqual(new Set(["sits"]));
    expect(drawn.map(moves)).toEqual(drawn.map(() => AT_REST === "stirs"));
    for (const he of drawn) {
      expect(he.querySelectorAll("button")).toHaveLength(0);
      // A press on him lands on nothing of his: he moves as he moved, and he has no focus to take.
      await user.click(he);
      expect(he.contains(document.activeElement)).toBe(false);
    }
    expect(drawn.map(moves)).toEqual(drawn.map(() => AT_REST === "stirs"));
    // The first thing a keyboard comes to in the page itself is a tab of the two ways in, and nothing of him.
    const first = [...(container.querySelector("main")?.querySelectorAll("a[href], button, input, textarea") ?? [])][0];
    expect(first?.closest("[data-pose]") ?? null).toBeNull();
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
