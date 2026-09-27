/**
 * The comparison page, as the look draws it: boxes of cream on the grass, a town at the
 * head of each area, each table within a plain edge of ink, and nothing read on the grass.
 *
 * What a comparison asks for, shows and says is held in test/compare. No vibe, no measure
 * and no place is named here: each is read from what the service recorded.
 */

import { readFileSync } from "node:fs";
import path from "node:path";

import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderToStaticMarkup } from "react-dom/server";

import ComparePage from "@/app/compare/page";
import { COMPARE, COMPARE_TABLE } from "@/content/compare";
import { crimeVibes } from "@/content/crime";
import { PROMPT } from "@/content/search";
import { TOWN } from "@/content/town";
import { TOWNS } from "@/content/towns";
import { recordedAnswer } from "@/lib/api/recorded";
import type { CompareData } from "@/lib/api/schema";
import { chosenFrom } from "@/lib/compare/list";

import { standInApi, type StandIn } from "../../../test/support/api";
import { faultsIn } from "../../../test/support/axe";
import { heavier, rulesOf, weightOf } from "../../../test/support/css";
import { ROUGH } from "../../../test/support/rough";
import { arrived } from "../../../test/support/search";
import { CompareTray } from "../CompareTray/CompareTray";
import { CompareView } from "./CompareView";
import { marksOfTheChosen } from "./towns";

const meta = recordedAnswer("get_meta", "meta").body.data;
const { areas, bands } = recordedAnswer("list_areas", "areas").body.data;
const three: CompareData = recordedAnswer("compare", "compare-three").body.data;
const slugsOf = (data: CompareData) =>
  data.areas.map((area) => areas.find((one) => one.area_id === area.area_id)?.slug ?? "");
const THREE = slugsOf(three);

interface More {
  readonly unknown?: number;
  readonly dropped?: number;
  /** False where the page hands over nothing a town is drawn from. */
  readonly towns?: boolean;
}

function comparison(slugs: readonly string[], api: StandIn, { towns = true, ...more }: More = {}) {
  const { chosen } = chosenFrom(slugs, areas);
  return (
    <main>
      <CompareView
        chosen={chosen}
        defaults={meta.defaults}
        tags={meta.tags}
        client={api.client}
        {...(towns ? { crime: crimeVibes(meta), marks: marksOfTheChosen(bands, chosen) } : {})}
        {...more}
      />
    </main>
  );
}

async function open(slugs: readonly string[] = THREE, api = standInApi().on("compare", "compare-three"), more: More = {}) {
  const view = render(comparison(slugs, api, more));
  await arrived();
  return { api, ...view };
}

/**
 * What brings the cream a sentence is read on: a box or a plain frame of the kit, a notice,
 * a failure, a button, which has a ground of its own, and what holds the place of a table.
 */
const ON_CREAM = "[data-kind], .note, .state, .error, .press, .card";

/** Every sentence in sight that stands in nothing which brings cream, and so would be read on the grass. */
function readOnTheGrass(page: Element): string[] {
  const found: string[] = [];
  const walker = page.ownerDocument.createTreeWalker(page, NodeFilter.SHOW_TEXT);
  for (let node = walker.nextNode(); node !== null; node = walker.nextNode()) {
    const text = node.textContent?.trim() ?? "";
    const held = node.parentElement;
    if (text === "" || held === null) continue;
    // What is kept for a screen reader is not drawn, and what a browser with scripts reads of a noscript is not either.
    if (held.closest(".visually-hidden, noscript, script, style") !== null) continue;
    if (held.closest(ON_CREAM) === null) found.push(text);
  }
  return found;
}

const page = (container: HTMLElement) => container.querySelector("main")?.firstElementChild as HTMLElement;
/** What the page is and what it compares on: the box that holds its heading. */
const headOf = (container: HTMLElement) => page(container).querySelector(":scope > .head") as HTMLElement;

describe("the comparison page, as the look draws it", () => {
  test("test_the_page_says_that_it_is_dressed_so_that_the_shell_draws_no_box_round_it", async () => {
    const { container } = await open();

    expect(page(container)).toHaveAttribute("data-dressed");
    expect(page(container)).toHaveClass("view");
  });

  test.each([
    ["answered", THREE, "compare-three", {}],
    ["failed", THREE, "error-internal", {}],
    ["of one area, which is too few", THREE.slice(0, 1), "compare-three", {}],
    ["of no area at all", [], "compare-three", {}],
    ["whose address named what is no area, and too many", THREE, "compare-three", { unknown: 2, dropped: 1 }],
    ["that was handed nothing to draw a town from", THREE, "compare-three", { towns: false }],
  ] as const)("test_nothing_of_a_comparison_is_read_on_the_grass: %s", async (_, slugs, scenario, more) => {
    const { container } = await open(slugs, standInApi().on("compare", scenario), more);

    expect(container.textContent?.length).toBeGreaterThan(100);
    expect(readOnTheGrass(page(container))).toEqual([]);
  });

  test("test_nothing_is_read_on_the_grass_while_the_comparison_is_waited_for", async () => {
    const api = standInApi();
    const held = api.hold("compare", "compare-three");
    const { container } = render(comparison(THREE, api));

    expect(container.querySelector("[aria-busy='true']")).not.toBeNull();
    expect(readOnTheGrass(page(container))).toEqual([]);

    held.release();
    await screen.findByRole("table", { name: COMPARE_TABLE.caption });
  });

  test("test_what_the_page_is_and_what_it_compares_on_stand_in_one_box_in_the_order_they_had", async () => {
    const { container } = await open(THREE, standInApi().on("compare", "compare-three"), { unknown: 1, dropped: 2 });
    const head = headOf(container);

    // It is the first box of the page: the way back alone stands before it.
    expect(page(container).querySelector(":scope > [data-kind]") === head).toBe(true);
    expect(head.previousElementSibling?.className).toBe("back");
    expect(head).toHaveAttribute("data-kind", "box");
    expect([...head.children].map((part) => part.textContent)).toEqual([
      COMPARE.title,
      COMPARE.lead,
      COMPARE.unknown(1),
      COMPARE.dropped(2),
      COMPARE.fromDefaults.rent,
    ]);
    expect(within(head).getByRole("heading", { level: 1 })).toHaveTextContent(COMPARE.title);
    // What it compares on is said to a screen reader as it was: a status.
    expect(within(head).getByRole("status")).toHaveTextContent(COMPARE.fromDefaults.rent);
  });

  test("test_the_page_says_that_the_areas_were_compared_once_the_comparison_is_in_hand_and_not_before", async () => {
    // Seen in a browser: "Burro has compared these areas" stood over the place of a
    // comparison that had not come, and named a table that was not yet on the page.
    const api = standInApi();
    const held = api.hold("compare", "compare-three");
    const { container } = render(comparison(THREE, api));
    const head = headOf(container);

    expect(container.querySelector("[aria-busy='true']")).not.toBeNull();
    // What the page is, and that the areas are set side by side, is said from the first.
    expect([...head.children].map((part) => part.textContent)).toEqual([COMPARE.title, COMPARE.lead]);
    expect(within(head).queryByRole("status")).toBeNull();
    expect(page(container).textContent?.includes("has compared")).toBe(false);

    held.release();
    await screen.findByRole("table", { name: COMPARE_TABLE.caption });

    expect([...head.children].map((part) => part.textContent)).toEqual([COMPARE.title, COMPARE.lead, COMPARE.fromDefaults.rent]);
    expect(within(head).getByRole("status")).toHaveTextContent(COMPARE.fromDefaults.rent);
    // The table it names is on the page with it.
    expect(COMPARE.fromSearch).toContain(`"${COMPARE_TABLE.counts}"`);
    expect(screen.getByRole("heading", { level: 2, name: COMPARE_TABLE.counts })).toBeInTheDocument();
  });

  test("test_a_comparison_that_failed_is_not_said_to_have_been_made_until_it_is_tried_again_and_comes", async () => {
    // Seen in a browser: it stood directly over "The areas could not be compared".
    const api = standInApi().on("compare", "error-internal");
    const { container } = await open(THREE, api);
    const head = headOf(container);

    expect(screen.getByRole("alert")).toHaveTextContent(COMPARE.failedTitle);
    expect([...head.children].map((part) => part.textContent)).toEqual([COMPARE.title, COMPARE.lead]);
    expect(page(container).textContent?.includes("has compared")).toBe(false);

    const held = api.hold("compare", "compare-three");
    await userEvent.setup({ delay: null }).click(within(screen.getByRole("alert")).getByRole("button", { name: PROMPT.tryAgain }));
    // Nor while it is waited for again.
    expect(container.querySelector("[aria-busy='true']")).not.toBeNull();
    expect(page(container).textContent?.includes("has compared")).toBe(false);

    held.release();
    await screen.findByRole("table", { name: COMPARE_TABLE.caption });
    expect(within(head).getByRole("status")).toHaveTextContent(COMPARE.fromDefaults.rent);
  });

  test("test_the_page_as_the_server_builds_it_does_not_say_that_the_areas_were_compared", async () => {
    // With scripts off no comparison comes: the page says that it needs them, and no more.
    const html = renderToStaticMarkup(await ComparePage({ searchParams: Promise.resolve({ a: [...THREE] }) }));

    expect(html).toContain(COMPARE.lead);
    expect(html.replace(/&#x27;/g, "'")).toContain(COMPARE.needsScripts);
    expect(html.includes("has compared")).toBe(false);
  });

  test("test_each_table_stands_within_a_plain_edge_of_ink_under_its_heading_and_has_no_box_with_a_shadow", async () => {
    await open();

    for (const title of [COMPARE_TABLE.character.title, COMPARE_TABLE.counts]) {
      const part = screen.getByRole("region", { name: title });
      expect([title, part.getAttribute("data-kind")]).toEqual([title, "plain"]);
      expect(part.tagName).toBe("SECTION");
      // Its heading comes first, and the table is in the frame with it.
      expect(part.firstElementChild).toBe(within(part).getByRole("heading", { level: 2, name: title }));
      expect(within(part).getAllByRole("table")).toHaveLength(1);
      // A table is many small things: no row of it, and nothing in it, is a box of the look.
      expect(part.querySelector("[data-kind='box'], [data-kind='box-on']")).toBeNull();
    }
    expect(screen.getAllByRole("table")).toHaveLength(2);
  });

  test("test_the_character_comes_before_what_counts_and_the_areas_before_both", async () => {
    const { container } = await open();
    const named = (part: Element) => part.getAttribute("aria-labelledby") ?? part.getAttribute("aria-label") ?? part.className;
    const parts = [...page(container).children].filter((part) => !part.matches(".visually-hidden, noscript"));

    expect(parts.map(named)).toEqual([
      "back",
      expect.stringContaining("head"),
      expect.stringContaining("heads"),
      "answer",
      "on",
    ]);
    // At the head of the comparison stand the areas, each with its town and its name.
    expect(within(parts[2] as HTMLElement).getByRole("list", { name: COMPARE_TABLE.areas })).toBeInTheDocument();
    // What the comparison answered stands where the answer is waited for: the vibes, and then what counts.
    expect([...(parts[3]?.children ?? [])].map(named)).toEqual(["compare-character", "compare-counts"]);
  });

  test("test_where_each_area_sits_on_each_vibe_is_the_first_thing_after_the_areas_themselves", async () => {
    // The founder: "Compare function is great". What a person came for is how the areas
    // differ, vibe by vibe, side by side: nothing stands between the areas and that.
    const { container } = await open();
    const heads = screen.getByRole("list", { name: COMPARE_TABLE.areas });
    const [first, second] = screen.getAllByRole("table");
    const between = [...page(container).querySelectorAll("p, table, ul, h2")].filter(
      (one) =>
        Boolean(heads.compareDocumentPosition(one) & Node.DOCUMENT_POSITION_FOLLOWING) &&
        !heads.contains(one) &&
        Boolean(one.compareDocumentPosition(first as HTMLElement) & Node.DOCUMENT_POSITION_FOLLOWING) &&
        one.closest(".visually-hidden, noscript") === null,
    );

    expect(first).toHaveAccessibleName(COMPARE_TABLE.character.caption);
    expect(second).toHaveAccessibleName(COMPARE_TABLE.caption);
    // Its heading, and what a vibe is and how a line is read: what is said of the table itself.
    expect(between.map((one) => one.textContent)).toEqual([COMPARE_TABLE.character.title, COMPARE_TABLE.character.lead]);
  });

  test("test_trying_again_leaves_the_focus_where_the_answer_will_stand_and_never_on_nothing", async () => {
    // Seen in a browser: the button went with the failure it stood in, and the focus was left on nothing.
    const api = standInApi().on("compare", "error-internal");
    const { container } = await open(THREE, api);
    const user = userEvent.setup({ delay: null });
    const answer = page(container).querySelector(".answer") as HTMLElement;
    const held = api.hold("compare", "compare-three");

    act(() => within(screen.getByRole("alert")).getByRole("button", { name: PROMPT.tryAgain }).focus());
    await user.keyboard("{Enter}");

    // While the comparison is waited for, what holds its place has the focus.
    expect(screen.queryByRole("alert")).toBeNull();
    expect(answer).toContainElement(container.querySelector("[aria-busy='true']"));
    expect(answer).toHaveFocus();

    held.release();
    expect(await screen.findByRole("table", { name: COMPARE_TABLE.caption })).toBeInTheDocument();

    // It is the same place once the answer is in, and the next stop is the first thing of the answer.
    expect(answer).toHaveFocus();
    expect(answer).toHaveAttribute("tabindex", "-1");
    await user.tab();
    expect(answer).toContainElement(document.activeElement as HTMLElement);
    expect(document.activeElement?.tagName).toBe("BUTTON");
  });

  test("test_every_area_has_its_town_at_its_head_where_the_page_hands_over_what_it_is_drawn_from", async () => {
    await open();
    const heads = within(screen.getByRole("list", { name: COMPARE_TABLE.areas })).getAllByRole("listitem");

    expect(heads).toHaveLength(three.areas.length);
    for (const [at, head] of heads.entries()) {
      expect(within(head).getByRole("img").getAttribute("aria-label")).toContain(TOWN.nameOf(three.areas[at]?.name ?? ""));
    }
    // What a town is, is said nowhere on the page: it is said in the key to the drawings and
    // at the head of the page of an area.
    expect(screen.queryByText(TOWNS.line)).toBeNull();
    // A town holds its own line, whole and in short, which the sheet of a comparison does
    // not draw: nothing else of the page says anything of a little town.
    const said = screen.getAllByText(/little town/i).filter((one) => one.closest("figure") === null);
    expect(said.map((one) => one.textContent)).toEqual([]);
    for (const head of heads) {
      const own = within(head).getAllByText(/little town/i);
      expect(own.map((one) => one.matches("figcaption > :first-child, [data-line='short']"))).toEqual([true, true]);
    }
    // A town is a drawing of four vibes, and says no figure in sight: what is heard of it is
    // its own. Each area has one, at its head: the other pictures of the page are the
    // gauges of its tables, each of which says where an area sits on a vibe.
    const pictures = screen.getAllByRole("img");
    expect(pictures.filter((one) => one.closest("td") === null)).toHaveLength(three.areas.length);
    expect(pictures.filter((one) => one.closest("td") === null).every((one) => heads.some((head) => head.contains(one)))).toBe(true);
  });

  test("test_the_bar_of_the_page_a_person_goes_back_to_draws_the_towns_that_stood_at_the_head_of_the_comparison", async () => {
    // Opening a comparison puts its areas in the bar, for the way back. The bar stands on
    // another page, which may hold nothing of these areas: so the comparison hands over
    // what their towns are drawn from, with the areas.
    const api = standInApi().on("compare", "compare-three");
    const { chosen } = chosenFrom(THREE, areas);
    const compared = (
      <CompareView
        chosen={chosen}
        defaults={meta.defaults}
        tags={meta.tags}
        client={api.client}
        crime={crimeVibes(meta)}
        marks={marksOfTheChosen(bands, chosen)}
      />
    );
    const { SessionProvider } = await import("@/lib/session/session");
    const view = render(<SessionProvider>{compared}</SessionProvider>);
    await arrived();
    const atTheHead = within(screen.getByRole("list", { name: COMPARE_TABLE.areas }))
      .getAllByRole("img")
      .map((town) => town.getAttribute("aria-label"));

    view.rerender(
      <SessionProvider>
        <CompareTray />
      </SessionProvider>,
    );

    const bar = screen.getByRole("region");
    expect(within(bar).getAllByRole("listitem")).toHaveLength(three.areas.length);
    expect(within(bar).getAllByRole("img").map((town) => town.getAttribute("aria-label"))).toEqual(atTheHead);
  });

  test("test_no_town_is_drawn_unless_the_page_has_said_which_vibes_hold_recorded_crime", async () => {
    const { chosen } = chosenFrom(THREE, areas);
    render(
      <main>
        <CompareView
          chosen={chosen}
          defaults={meta.defaults}
          tags={meta.tags}
          marks={marksOfTheChosen(bands, chosen)}
          client={standInApi().on("compare", "compare-three").client}
        />
      </main>,
    );
    await arrived();

    // A town draws nothing of a vibe whose recipe holds recorded crime, and cannot know which
    // that is. The pictures that are left are the gauges of the tables, each in its cell.
    expect(within(screen.getByRole("list", { name: COMPARE_TABLE.areas })).queryByRole("img")).toBeNull();
    expect(screen.queryAllByRole("img").filter((one) => one.closest("td") === null)).toEqual([]);
    expect(screen.getByRole("main").textContent?.includes(TOWN.line)).toBe(false);
    expect(screen.getByRole("main").textContent?.includes(TOWNS.line)).toBe(false);
  });

  test("test_the_page_as_the_server_builds_it_draws_the_town_of_each_area_and_says_nothing_of_what_a_town_is", async () => {
    const built = await ComparePage({ searchParams: Promise.resolve({ a: [...THREE] }) });

    const html = renderToStaticMarkup(built);

    expect(html.split('role="img"')).toHaveLength(three.areas.length + 1);
    expect(html.split(TOWNS.line.replace(/'/g, "&#x27;"))).toHaveLength(1);
    for (const area of three.areas) expect(html).toContain(TOWN.nameOf(area.name));
    // What it is handed is of the areas of the address and of no other, and of no search.
    expect(Object.keys(built.props.marks)).toEqual(three.areas.map((area) => area.area_id));
    expect(built.props.crime).toEqual(crimeVibes(meta));
    // Nothing the service says of a vibe it holds to be less sure than the rest is handed over.
    expect(Object.keys(built.props).sort()).toEqual(["chosen", "crime", "defaults", "dropped", "marks", "tags", "unknown"].sort());
  });

  test("test_a_comparison_says_of_no_vibe_that_it_is_a_rough_guide", async () => {
    // The founder: "remove the concept of rough guide, we don't want to pass this on to a
    // user". The recorded comparison compares the vibe the service holds less sure, in a
    // row of the vibes, and says nothing of it that it does not say of any vibe. It is
    // handed the vibes of the release and nothing a service says of one, so it is held to
    // write neither the label a service gave such a vibe nor the sentence that said why.
    const guide = meta.tags.find((tag) => tag.tag_id === ROUGH.tag_id);
    if (guide === undefined) throw new Error("the recorded release holds no such vibe");
    await open();
    const page = screen.getByRole("main");

    expect(guide.sureness).toBe("rough_guide");
    expect(three.character.map((row) => row.tag_id)).toContain(guide.tag_id);
    expect(within(page).getAllByText(guide.label).length).toBeGreaterThan(0);
    expect(page.querySelector("[data-rough-guide]")).toBeNull();
    expect(page.textContent?.includes(ROUGH.label)).toBe(false);
    expect(page.textContent?.includes(ROUGH.why)).toBe(false);
    expect(/rough guide|less sure/i.test(page.textContent ?? "")).toBe(false);
  });

  test("test_one_area_is_no_comparison_and_the_page_says_so_and_what_to_do", async () => {
    // Seen in a browser: with one area left the head still said "These are the areas you
    // chose, set side by side so that you can see how they differ", over one area.
    const { container } = await open(THREE.slice(0, 1));
    const head = headOf(container);

    expect([...head.children].map((part) => part.textContent)).toEqual([COMPARE.title, COMPARE.tooFew]);
    expect(head).not.toHaveTextContent(COMPARE.lead);
    expect(COMPARE.tooFew).toMatch(/one area, which is not enough to compare/);
    expect(COMPARE.tooFew).toMatch(/at least two/);
    expect(COMPARE.tooFew).toContain('"Add to compare"');
    // It is said to a screen reader as what the page compares on is: a status.
    expect(within(head).getByRole("status")).toHaveTextContent(COMPARE.tooFew);
    // The area that is left is still there, by its name, which leads to its page.
    expect(within(screen.getByRole("list", { name: COMPARE_TABLE.areas })).getAllByRole("listitem")).toHaveLength(1);
    // The way on stands under what says so, and is the one cobalt button of the page, and so
    // the one that matters most. No search is open here, so it leads to one that is yet to
    // be made, as the way at the head of the page does, which is drawn plain.
    const [back, on] = screen.getAllByRole("link", { name: COMPARE.start });
    expect(screen.getAllByRole("link", { name: COMPARE.start })).toHaveLength(2);
    expect([back?.closest("p")?.className, on?.closest("p")?.className]).toEqual(["back", "on"]);
    expect(on).toHaveAttribute("href", "/");
    expect(back?.querySelector("[data-kind]")).toHaveAttribute("data-kind", "plain");
    expect(on?.querySelector("[data-kind]")).toHaveAttribute("data-kind", "go");
    expect(page(container).querySelectorAll("[data-kind='go']")).toHaveLength(1);
    expect(Boolean(head.compareDocumentPosition(on as HTMLElement) & Node.DOCUMENT_POSITION_FOLLOWING)).toBe(true);
  });

  test("test_the_area_that_is_left_keeps_the_focus_it_was_handed_as_the_other_is_taken_out", async () => {
    // Seen in a browser, by keyboard: with two areas compared, the way out of one handed the
    // focus to the name of the other, and the focus was on nothing once the comparison of
    // one had come. The areas were drawn anew for a comparison of too few, and what had the
    // focus went with what was drawn before. They are one part of the page, whatever it holds.
    const api = standInApi().on("compare", "compare-three");
    const two = THREE.slice(0, 2);
    const left = three.areas[0]?.name ?? "";
    const view = render(comparison(two, api));
    await arrived();
    const name = screen.getByRole("link", { name: COMPARE_TABLE.open(left) });
    act(() => name.focus());

    // The address names one area, once the other is taken out.
    view.rerender(comparison(two.slice(0, 1), api));
    await arrived();

    expect(screen.getByRole("link", { name: COMPARE_TABLE.open(left) })).toBe(name);
    expect(name).toHaveFocus();
    expect(screen.getByRole("status")).toHaveTextContent(COMPARE.tooFew);
  });

  test("test_a_comparison_of_no_area_says_what_is_needed_to_begin_and_draws_no_frame_for_the_areas", async () => {
    // Seen in a browser: the line about the areas a person chose stood over an empty box.
    const { container } = await open([]);

    // The way back, what the page is, in its box, and the way on: no frame stands between them.
    expect(
      [...page(container).children].map((part) => [...part.classList].find((name) => /^(head|heads|answer|back|on)$/.test(name))),
    ).toEqual(["back", "head", "on"]);
    expect(headOf(container)).toHaveTextContent(COMPARE.none);
    expect(page(container)).not.toHaveTextContent(COMPARE.lead);
    expect(page(container)).not.toHaveTextContent(COMPARE.tooFew);
    expect(COMPARE.none).toMatch(/not chosen any areas/);
    expect(screen.queryByRole("list", { name: COMPARE_TABLE.areas })).toBeNull();
    expect(screen.getAllByRole("link", { name: COMPARE.start }).map((way) => way.querySelector("[data-kind]")?.getAttribute("data-kind"))).toEqual([
      "plain",
      "go",
    ]);
  });

  test("test_the_heading_of_the_page_takes_the_focus_when_it_is_handed_it_and_is_no_stop_of_the_keyboard", async () => {
    await open();
    const heading = screen.getByRole("heading", { level: 1, name: COMPARE.title });

    expect(heading).toHaveAttribute("tabindex", "-1");
    await userEvent.setup({ delay: null }).tab();
    expect(heading).not.toHaveFocus();
  });

  test("test_the_way_back_is_a_button_of_the_look_and_is_not_the_button_that_matters_most", async () => {
    const { container } = await open();
    const ways = screen.getAllByRole("link", { name: COMPARE.start });

    // At the head of the page, before anything else, and again at its foot.
    expect(ways.map((way) => way.closest("p")?.className)).toEqual(["back", "on"]);
    expect(page(container).firstElementChild === ways[0]?.closest("p")).toBe(true);
    expect(page(container).lastElementChild === ways[1]?.closest("p")).toBe(true);
    for (const way of ways) {
      expect(way).toHaveAttribute("href", "/");
      expect(way).toHaveClass("press", "target");
      expect(way.querySelector("[data-kind]")).toHaveAttribute("data-kind", "plain");
    }
    // No button of a comparison that was answered is cobalt: it is read, and sends nothing.
    expect(page(container).querySelector("[data-kind='go']")).toBeNull();
  });

  test("test_the_way_back_stands_on_the_grass_as_a_button_does_and_takes_no_more_room_than_it_is_high", () => {
    const sheet = rulesOf(readFileSync(path.join(__dirname, "CompareView.module.css"), "utf8"));
    const of = (selector: string) => sheet.filter((rule) => rule.selector === selector && rule.under === null);

    // What holds it is a paragraph with no room of its own about it: the page sets what parts
    // its boxes, and the button brings the ground its words are read on.
    for (const selector of [".back", ".on"]) {
      expect([selector, of(selector).map((rule) => [...rule.sets])]).toEqual([selector, [[["margin", "0"]]]]);
    }
    // Nothing of it goes by the width of the screen: it is the same on a phone as on a desk.
    expect(sheet.filter((rule) => /\.(back|on)\b/.test(rule.selector) && rule.under !== null)).toEqual([]);
  });

  test("test_a_comparison_that_failed_is_an_alert_with_the_way_to_try_again_as_a_button_of_the_look", async () => {
    const api = standInApi().on("compare", "error-internal");
    await open(THREE, api);
    const alert = screen.getByRole("alert");

    expect(alert).toHaveClass("error");
    expect(alert.firstElementChild).toHaveTextContent(COMPARE.failedTitle);
    const again = within(alert).getByRole("button", { name: PROMPT.tryAgain });
    expect(again).toHaveClass("press", "target");
    // It is the one button that matters most where a comparison failed, and the one cobalt button of the page.
    expect(again.querySelector("[data-kind]")).toHaveAttribute("data-kind", "go");
    expect(screen.getByRole("main").querySelectorAll("[data-kind='go']")).toHaveLength(1);

    api.on("compare", "compare-three");
    await userEvent.setup({ delay: null }).click(again);

    expect(await screen.findByRole("table", { name: COMPARE_TABLE.caption })).toBeInTheDocument();
    expect(screen.queryByRole("alert")).toBeNull();
  });

  test.each([
    ["answered", "compare-three"],
    ["failed", "error-internal"],
  ])("test_the_page_has_no_accessibility_fault_%s", async (_, scenario) => {
    const { container } = await open(THREE, standInApi().on("compare", scenario));

    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("the style sheet of the comparison page", () => {
  const CSS = readFileSync(path.join(__dirname, "CompareView.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
  const ALL = rulesOf(CSS);
  const STYLES = ALL.filter((rule) => !/forced-colors/.test(rule.under ?? ""));
  const setsOf = (selector: string) =>
    new Map(STYLES.filter((rule) => rule.selector === selector && rule.under === null).flatMap((rule) => [...rule.sets]));

  test("test_a_notice_is_cream_inside_a_rule_of_ink_with_a_band_of_amber_and_its_words_in_ink", () => {
    for (const selector of [".note", ".state"]) {
      const sets = setsOf(selector);
      expect([selector, sets.get("background"), sets.get("border"), sets.get("color"), sets.get("box-shadow")]).toEqual([
        selector,
        "var(--notice-bg)",
        "var(--edge) solid var(--notice-edge)",
        "var(--notice-text)",
        "inset var(--band) 0 0 var(--notice-mark)",
      ]);
    }
  });

  test("test_a_failure_is_cream_inside_a_rule_of_ink_with_a_band_of_poppy_and_its_words_in_ink", () => {
    const sets = setsOf(".error");

    expect([sets.get("background"), sets.get("border"), sets.get("color"), sets.get("box-shadow")]).toEqual([
      "var(--bg)",
      "var(--edge) solid var(--border)",
      "var(--text)",
      "inset var(--band) 0 0 var(--error-edge)",
    ]);
    // Poppy is an edge, and never words: what a failure is called is said in ink.
    expect(setsOf(".errorTitle").get("color")).toBe("var(--error)");
    expect(STYLES.filter((rule) => rule.sets.get("color") === "var(--error-edge)").map((rule) => rule.selector)).toEqual([]);
  });

  test("test_the_heading_of_a_table_stands_on_a_band_of_ink_in_the_face_of_names_and_is_never_small", () => {
    const sets = setsOf(".partTitle");

    expect([sets.get("background"), sets.get("color"), sets.get("font")]).toEqual([
      "var(--ink)",
      "var(--page)",
      "400 var(--name-2) / 1 var(--font-name)",
    ]);
    expect(sets.get("font-synthesis")).toBe("none");
  });

  test("test_the_frame_of_a_table_is_the_kits_and_the_sheet_lays_no_ground_no_edge_and_no_shadow_of_its_own", () => {
    const sets = setsOf(".part");

    expect(["background", "border", "box-shadow", "overflow"].filter((property) => sets.has(property))).toEqual([]);
    expect(CSS).not.toMatch(/var\(--(frame-box|box-shadow)/);
  });

  test("test_what_stands_in_a_plain_edge_ends_where_the_edge_of_ink_of_a_box_ends", () => {
    // Measured in a browser, at 1440 by 900: the edge of ink of every box of the page ended
    // at 1,314, and the edge of each table at 1,320. A box of the kit keeps the room of its
    // shadow inside itself, two art pixels at its far side, and a plain frame keeps none.
    const kit = rulesOf(readFileSync(path.join(__dirname, "..", "kit", "Frame", "Frame.module.css"), "utf8"));
    const drawn = kit.find((rule) => rule.selector === ".box::before" && rule.under === null);
    const tokens = readFileSync(path.join(__dirname, "..", "..", "styles", "tokens.css"), "utf8");
    const wide = /--frame-box-wide:\s*([^;]+);/.exec(tokens)?.[1] ?? "";

    // The rule of a box is drawn four art pixels out from what it holds, and the box keeps six at its far side.
    expect(drawn?.sets.get("inset")).toBe("calc(var(--px) * -4)");
    expect(wide.replace(/\s+/g, " ")).toBe("calc(var(--px) * 4) calc(var(--px) * 6) calc(var(--px) * 6) calc(var(--px) * 4)");
    // So all that stands where the answer stands, which is no box, stands two short of the far side.
    expect(setsOf(".answer").get("padding-inline-end")).toBe("calc(var(--px) * 2)");
    // A plain frame of the kit keeps that room itself where it stands on the grass, as each
    // table does. What holds the tables keeps it for them already, with what is waited for
    // and a failure, which are no frames: so a table keeps none of its own, or it would
    // stand four art pixels short. The rule weighs more than the kit's, whichever is read last.
    const kept = kit.filter((rule) => rule.sets.has("margin-inline-end") && rule.under === null);
    expect(kept.map((rule) => [rule.selector, rule.sets.get("margin-inline-end")])).toEqual([
      [".plain:not(:where(.frame *))", "calc(var(--px) * 2)"],
    ]);
    expect(setsOf(".answer > .part").get("margin-inline-end")).toBe("0");
    expect(heavier(weightOf(".answer > .part"), weightOf(kept[0]?.selector ?? ""))).toBe(true);
    expect(STYLES.filter((rule) => rule.sets.has("margin-inline-end") || rule.sets.has("padding-inline-end")).map((rule) => rule.selector)).toEqual([
      ".answer",
      ".answer > .part",
    ]);
  });

  test("test_on_a_wide_screen_what_the_page_is_stands_beside_what_it_compares_on_so_that_the_areas_stand_sooner", () => {
    // Measured at 1440 by 900 with four areas: one under the other, the head of the page
    // stood from 165 to 465 and the first vibe at 1,085, under the foot of the first screen.
    // Side by side the head ends at 400, and the first vibe stands at 885.
    const WIDE = "@media (min-width: 60rem)";
    const wide = (selector: string) =>
      new Map(ALL.filter((rule) => rule.under === WIDE && rule.selector === selector).flatMap((rule) => [...rule.sets]));

    expect(wide(".head").get("grid-template-columns")).toBe("minmax(0, 1fr) minmax(0, 1fr)");
    expect(wide(".head > h1").get("grid-column")).toBe("1 / -1");
    expect(wide(".head > .lead").get("grid-column")).toBe("1");
    for (const notice of [".head > .note", ".head > .state"]) expect([notice, wide(notice).get("grid-column")]).toEqual([notice, "2"]);
    // Where one area is no comparison the page says nothing of areas set side by side, and
    // what it says instead begins where the heading does. Seen in a browser: it stood at the
    // far side of the box, beside nothing.
    expect(wide(".head:not(:has(> .lead)) > :is(.note, .state)").get("grid-column")).toBe("1 / -1");
    expect(
      heavier(weightOf(".head:not(:has(> .lead)) > :is(.note, .state)"), weightOf(".head > .state")),
    ).toBe(true);
    // The order in which they are read and heard is the order they had.
    const narrow = ALL.filter((rule) => rule.under === null && rule.selector === ".head").flatMap((rule) => rule.sets.get("display") ?? []);
    expect(narrow).toEqual(["grid"]);
    expect(ALL.filter((rule) => /\.head\b/.test(rule.selector) && rule.sets.has("order")).map((rule) => rule.selector)).toEqual([]);
  });

  test("test_every_colour_a_face_and_a_size_is_a_token_and_nothing_is_dimmed_or_moves", () => {
    expect(CSS.match(/#[0-9a-f]{3,8}\b|\b(rgb|hsl|oklch|lab|lch)a?\(/gi) ?? []).toEqual([]);
    expect(CSS.match(/url\([^)]*\)/g) ?? []).toEqual([]);
    const faces = STYLES.flatMap((rule) =>
      [...rule.sets].filter(([property]) => property === "font" || property === "font-family").map(([, value]) => value),
    );
    expect(faces.filter((face) => !/var\(--font-(say|name)\)$/.test(face))).toEqual([]);
    const moving = ALL.filter((rule) =>
      [...rule.sets.keys()].some((property) => /^(animation|transition|transform|translate|rotate|scale|zoom|opacity|filter)/.test(property)),
    );
    expect(moving.map((rule) => rule.selector)).toEqual([]);
    // Nothing that holds words has a height of its own, so that text can be made larger.
    const fixed = ALL.filter((rule) => [...rule.sets.keys()].some((property) => /^(height|max-height|block-size|max-block-size)$/.test(property)));
    expect(fixed.map((rule) => rule.selector)).toEqual([]);
  });

  test("test_what_is_handed_the_focus_takes_it_and_draws_no_ring", () => {
    // Where the answer stands, and the heading of the page: neither is a stop of its own.
    // What each sets with the focus is what is drawn, and no more.
    const withTheFocus = ALL.filter((rule) => /:(hover|focus|focus-within|focus-visible|active)\b/.test(rule.selector));

    expect(withTheFocus.map((rule) => [rule.selector, [...rule.sets.keys()].sort()])).toEqual([
      [".head h1:focus", ["box-shadow", "outline"]],
      [".answer:focus", ["box-shadow", "outline"]],
    ]);
  });
});
