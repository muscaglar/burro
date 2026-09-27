/**
 * The three pages that explain, each drawn whole in the shell, as a browser is sent it: the
 * vibes, the methods and the sources. A statement of accessibility was the fourth, and is
 * gone: the founder asked for it to go.
 *
 * `test/pages.test.tsx` holds every page of the website to what every page is held to. This
 * holds these three to the look: that each stands on the meadow as boxes, that nothing of
 * it is read on the grass, and that it says what it said.
 */

import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { render, screen, within } from "@testing-library/react";
import type { ReactElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";

import MethodsPage from "@/app/methods/page";
import SourcesPage from "@/app/sources/page";
import VibesPage from "@/app/vibes/page";
import { Shell } from "@/components/Shell/Shell";
import { leadOf } from "@/components/VibesList/lead";
import { ABOUT } from "@/content/about";
import { METHODS } from "@/content/methods";
import { SOURCES } from "@/content/sources";
import { TOWN } from "@/content/town";
import { VIBES } from "@/content/vibes";
import { recordedAnswer } from "@/lib/api/recorded";

import { rulesOf, type Rule } from "../../../test/support/css";
import { arrived } from "../../../test/support/search";
import { onTheGrass } from "./grass";

jest.mock("next/navigation", () => ({ usePathname: () => "/" }));

const { meta, data } = recordedAnswer("get_meta", "meta").body;

type Page = () => ReactElement | Promise<ReactElement>;

const PAGES: readonly (readonly [name: string, page: Page, title: string, lead: string])[] = [
  ["the vibes", VibesPage, VIBES.title, `${leadOf(data)} ${VIBES.order}`],
  ["methods", MethodsPage, METHODS.title, METHODS.lead],
  ["data sources", SourcesPage, SOURCES.title, SOURCES.lead],
];

async function show(page: Page) {
  const view = render(<Shell meta={meta}>{await page()}</Shell>);
  await arrived();
  return view;
}

const dressed = () => screen.getByRole("main").querySelector(":scope > [data-dressed]") as HTMLElement;

/** Every rule of every style sheet of a part of the website. */
function everyRule(folder = path.resolve(__dirname, "..")): Rule[] {
  return readdirSync(folder, { withFileTypes: true }).flatMap((entry) => {
    const file = path.join(folder, entry.name);
    if (entry.isDirectory()) return everyRule(file);
    return entry.name.endsWith(".module.css") ? rulesOf(readFileSync(file, "utf8")) : [];
  });
}

const RULES = everyRule();

/** What the style of an element sets, by name, as it is written in the page. */
const setBy = (one: Element) =>
  (one.getAttribute("style") ?? "")
    .split(";")
    .map((part) => part.trim())
    .filter((part) => part.includes(":"))
    .map((part): [string, string] => [part.slice(0, part.indexOf(":")).trim(), part.slice(part.indexOf(":") + 1).trim()]);

/**
 * True of what hands a drawing to its style sheet and draws nothing of it itself, as a
 * list that holds words does where it may hold no element that is dress. Its own style
 * sets names for a sheet to read and nothing else. And every sheet that reads a name
 * which holds a drawing lays it as a mark before or after what is read, which holds no
 * word: such a mark is heard by nobody, and stands for nothing that is not said.
 */
function handsItToItsSheet(one: Element): boolean {
  const set = setBy(one);
  if (set.some(([name]) => !name.startsWith("--"))) return false;
  return set
    .filter(([, value]) => value.includes("/art/"))
    .every(([name]) => {
      const reads = RULES.filter((rule) => [...rule.sets.values()].some((value) => value.includes(`var(${name})`)));
      const marks = (rule: Rule) =>
        /::(before|after)$/.test(rule.selector) &&
        RULES.filter((other) => other.selector === rule.selector && other.sets.has("content")).every(
          (other) => other.sets.get("content") === '""',
        ) &&
        RULES.some((other) => other.selector === rule.selector && other.sets.get("content") === '""');
      return reads.length > 0 && reads.every(marks);
    });
}
/** The names of the parts of a page that are landmarks, in the order they stand. */
const regions = () => within(screen.getByRole("main")).queryAllByRole("region").map((region) => region.getAttribute("aria-labelledby") ?? "");

describe.each(PAGES)("%s, in the look", (_, page, title, lead) => {
  test("test_the_page_tells_the_shell_that_it_stands_boxes_of_its_own_on_the_grass", async () => {
    await show(page);

    expect(screen.getByRole("main").children).toHaveLength(1);
    expect(dressed()).not.toBeNull();
  });

  test("test_its_heading_and_what_it_is_for_stand_in_the_first_box_of_the_page", async () => {
    await show(page);
    const head = dressed().firstElementChild as HTMLElement;

    expect(head).toHaveAttribute("data-kind", "box");
    expect(within(head).getByRole("heading", { level: 1 }).textContent).toBe(title);
    expect(within(head).getByText(lead)).toBeInTheDocument();
  });

  test("test_whatever_stands_on_the_grass_is_a_box_or_holds_nothing_but_boxes", async () => {
    await show(page);

    // The whole of the page, with what another hand draws and is held as it came: the list
    // of sources brings a box for each source, so nothing of it is left out.
    expect(onTheGrass(dressed())).toEqual([]);
  });

  test("test_no_drawing_of_the_page_is_fetched_as_a_picture_and_none_is_of_the_rabbit", async () => {
    const { container } = await show(page);
    const drawn = [...dressed().querySelectorAll<HTMLElement>("[style*='/art/']")];

    expect(container.querySelectorAll("main img, main [src], main [srcset]")).toHaveLength(0);
    // Burro is drawn where a person searches, and on no page that explains.
    expect(drawn.filter((one) => /\/art\/burro/.test(one.getAttribute("style") ?? ""))).toEqual([]);
    // A drawing is dress, or is a picture that says in words what it shows. What holds
    // words may hand a drawing to its style sheet by name, and draw nothing of it itself:
    // the sheet lays it as a mark that holds no word, as the key before the name of a source.
    for (const one of drawn) {
      const said = one.closest("[aria-hidden='true'], [role='img']");
      expect([one.getAttribute("style"), said !== null || handsItToItsSheet(one)]).toEqual([one.getAttribute("style"), true]);
    }
  });

  test("test_the_page_reads_with_scripts_off", async () => {
    const markup = renderToStaticMarkup(await page());

    expect(markup).toContain(title);
    expect(markup).not.toMatch(/<button|aria-expanded|onclick/i);
    // What opens is the browser's own, and is closed as the page is built.
    expect(markup).not.toMatch(/<details[^>]* open/);
  });
});

describe("the page of vibes, in the look", () => {
  test("test_the_key_comes_first_and_the_vibes_after_it", async () => {
    await show(VibesPage);

    const boxes = [...dressed().children].filter((one) => one.matches("[data-kind='box'], details, div"));
    const [head, key, over, vibes, how] = boxes;

    // What the page is for, the key, what is true of every vibe, the vibes, and how an area is placed.
    expect(boxes).toHaveLength(5);
    expect(within(head as HTMLElement).getByRole("heading", { level: 1 })).toHaveTextContent(VIBES.title);
    expect(within(key as HTMLElement).getByRole("heading", { level: 2 })).toHaveTextContent(ABOUT.key.title);
    expect(within(over as HTMLElement).getByRole("heading", { level: 2 })).toHaveTextContent(VIBES.each.title);
    expect([...(vibes?.children ?? [])].map((one) => one.id)).toEqual(data.tags.map((tag) => tag.tag_id));
    expect([how?.tagName, how?.id]).toEqual(["DETAILS", "how"]);
  });

  test("test_the_parts_of_the_page_that_are_landmarks_are_the_key_with_its_parts_what_is_said_over_the_vibes_and_every_vibe", async () => {
    await show(VibesPage);

    const parts = regions();
    const town = screen.getByRole("region", { name: TOWN.key.title });

    expect(parts.slice(0, 6)).toEqual(["key", "key-things", "key-steps", "key-result", "key-map", town.getAttribute("aria-labelledby")]);
    expect(parts[6]).toBe("vibes");
    expect(parts.slice(7)).toEqual(data.tags.map((tag) => `${tag.tag_id}-name`));
    // What a town is built of is inside the key, and stands in its box.
    expect(town.closest("[data-kind='box']")).toBe(screen.getByRole("region", { name: ABOUT.key.title }));
  });

  test("test_the_headings_of_the_page_are_in_order_and_none_is_skipped", async () => {
    await show(VibesPage);

    const ranks = within(screen.getByRole("main"))
      .getAllByRole("heading")
      .map((heading) => Number(heading.tagName.slice(1)));

    expect(ranks[0]).toBe(1);
    ranks.forEach((rank, at) => {
      if (at > 0) expect([at, rank - (ranks[at - 1] ?? rank) <= 1]).toEqual([at, true]);
    });
  });

  test("test_the_vibes_are_far_shorter_what_stands_in_sight_of_all_of_them_is_less_than_a_third_of_what_stood", async () => {
    await show(VibesPage);

    // Counted as the page was built before: 14 vibes drew 3,011 words in sight. jsdom lays
    // nothing out, so what a browser measured is in the design: this holds what it depends on.
    const inSight = (one: Element) => one.closest("details, [hidden], .visually-hidden, [aria-hidden='true']") === null;
    const words = data.tags
      .flatMap((tag) => [...(document.getElementById(tag.tag_id)?.querySelectorAll("h3, p, li, dt, dd, th, td, a") ?? [])])
      .filter(inSight)
      .flatMap((one) => (one.children.length === 0 ? (one.textContent ?? "").split(/\s+/) : []))
      .filter((word) => word !== "");

    expect(words.length).toBeGreaterThan(data.tags.length * 5);
    expect(words.length).toBeLessThan(1000);
  });
});

describe("the methods, in the look", () => {
  test("test_the_page_is_three_boxes_as_it_is_built_its_heading_a_short_account_and_the_bar_of_one_fold", async () => {
    await show(MethodsPage);
    const [head, account, fold, ...more] = [...dressed().children];

    expect(more).toEqual([]);
    expect([head?.getAttribute("data-kind"), account?.getAttribute("data-kind")]).toEqual(["box", "box"]);
    expect(account).toHaveTextContent(METHODS.account.looks);
    expect(fold?.tagName).toBe("DETAILS");
    expect((fold as HTMLDetailsElement).open).toBe(false);
    expect(fold?.querySelector(":scope > summary")).toHaveAttribute("data-kind", "box");
    expect(fold?.querySelector(":scope > summary")?.textContent).toBe(METHODS.detail);
  });

  test("test_every_part_another_page_leads_to_is_in_the_page_under_its_id", async () => {
    await show(MethodsPage);

    // `paths.methods` names them. Each stands in the fold, which is opened for whoever comes by such a link.
    for (const id of ["confidence", "journeys", "names", "words"]) {
      const part = document.getElementById(id);
      expect([id, part?.tagName, part?.closest("details") !== null]).toEqual([id, "H2", true]);
    }
  });

  test("test_what_a_town_is_built_of_is_not_said_a_second_time_here", async () => {
    await show(MethodsPage);

    expect(screen.queryByRole("region", { name: TOWN.key.title })).toBeNull();
    expect(regions()).toContain("vibes");
    expect(screen.getByRole("main")).toHaveTextContent(METHODS.vibes.key);
  });
});

describe("the sources, in the look", () => {
  test("test_the_key_the_look_draws_a_source_by_stands_beside_the_heading_and_says_nothing", async () => {
    await show(SourcesPage);
    const head = dressed().firstElementChild as HTMLElement;
    const drawn = [...head.querySelectorAll<HTMLElement>("[style*='/art/']")];

    expect(drawn.map((one) => one.style.getPropertyValue("--art"))).toEqual(['url("/art/ui-key.png")']);
    expect(drawn[0]).toHaveAttribute("aria-hidden", "true");
    expect(within(head).getByRole("heading", { level: 1 })).toHaveAccessibleName(SOURCES.title);
  });

  test("test_the_list_of_sources_stands_in_one_box_under_the_heading_and_every_source_is_in_it_in_sight", async () => {
    await show(SourcesPage);
    const [head, list, ...more] = [...dressed().children];

    // Two boxes and no more: what the page is for, and the list.
    expect([head?.getAttribute("data-kind"), list?.getAttribute("data-kind"), more.length]).toEqual(["box", "box", 0]);
    for (const source of data.attributions) {
      const entry = within(list as HTMLElement).getByRole("article", { name: source.name });
      expect(entry).toHaveTextContent(source.attribution);
      // The licences of the data ask for the credit: it stands in no fold.
      expect(within(entry).getByText(source.attribution).closest("details")).toBeNull();
      expect(entry.closest("details")).toBeNull();
    }
  });

  test("test_what_else_is_said_of_a_source_is_closed_as_the_page_is_built", async () => {
    await show(SourcesPage);

    const folds = [...dressed().querySelectorAll("details")];

    expect(folds).toHaveLength(data.attributions.length);
    expect(folds.filter((fold) => fold.open)).toEqual([]);
    for (const fold of folds) expect(fold.querySelector("summary")?.textContent?.startsWith(SOURCES.more)).toBe(true);
  });
});
