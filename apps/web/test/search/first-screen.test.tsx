/**
 * The first screen says who Burro is for, and offers two ways in, as two
 * tabs: a quick search, which is the box with two helpers under it, and a
 * deep search, which is the settings and the button that makes a search of
 * them. The map is in sight whichever is chosen. Once a search is open the
 * two have become one search: the box at the head of the page, and the
 * settings as one part that refines it.
 *
 * Two things here can only be held against the page as it is built, or
 * against what a browser does: what a browser with scripts off is sent, and
 * that the answer is in sight when a search opens of what stood under the
 * box. The first is read from what the server draws. The second was seen in
 * a browser, and is held by what the page asks of one.
 */

import { readFileSync } from "node:fs";
import path from "node:path";

import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderToString } from "react-dom/server";

import { metadata } from "@/app/page";
import {
  AN_AREA_BY_NAME,
  BUTTON_STANDS,
  DEEP_SEARCH_RANKS_BY,
  FINDS_AN_AREA,
  ON_A_NARROW_SCREEN,
  RANKS,
  STANDS,
  THE_BUTTON_OF_DEEP_SEARCH,
  type ButtonStands,
  type Ranks,
} from "@/components/SearchApp/look";
import { OPENS, SearchApp, type Opens } from "@/components/SearchApp/SearchApp";
import { wordOf } from "@/components/Shelf/Shelf";
import { Shell } from "@/components/Shell/Shell";
import { CARD } from "@/content/card";
import { HELPERS } from "@/content/helpers";
import { LEGEND, MAP, MAP_CARD } from "@/content/map";
import { CHIPS, FIND_AREA, leadFor, PLACE, PROMPT, SEARCH, SHELF, TENURE_CHOICE } from "@/content/search";
import { BUDGET, JOURNEY, KIND_OF_SEARCH, SETTINGS } from "@/content/settings";
import { SITE, WORDS_LINE } from "@/content/site";
import { DEEP, REFINE, WAYS } from "@/content/ways";
import { recordedAnswer } from "@/lib/api/recorded";
import { examplesFor, placedOf } from "@/lib/holds";

import { reasonsFor, setOnline, standInApi } from "../support/api";
import { faultsIn } from "../support/axe";
import { rulesOf } from "../support/css";
import { lastMap } from "../support/maplibre";
import {
  areas,
  arrived,
  bands,
  firstSearch,
  groupsAre,
  helper,
  helpers,
  meta,
  narrowAgain,
  openSearch,
  panelOf,
  promptBox,
  results,
  search,
  settingsAt,
  settled,
  setWebGL,
  setWide,
  tabOf,
  theSettings,
  theSettingsIfAny,
  way,
  ways,
  waysIfAny,
  whatRefines,
} from "../support/search";
import { watch } from "../support/watch";

jest.mock("next/navigation", () => ({ usePathname: () => "/" }));

/** What a test put on the page to read what was built. It goes when the test ends. */
const held: HTMLElement[] = [];

beforeEach(() => setOnline(true));
afterEach(() => {
  narrowAgain();
  setWebGL(false);
  delete (Element.prototype as { scrollIntoView?: unknown }).scrollIntoView;
  for (const part of held.splice(0)) part.remove();
});

/** A part of the page that holds what was built, as a browser would read it. */
function holding(html: string): HTMLElement {
  const part = document.createElement("div");
  part.innerHTML = html;
  document.body.append(part);
  held.push(part);
  return part;
}

/**
 * The search page as the server builds it, read twice. `on` is what a browser with scripts
 * on draws before anything is pressed: what is kept for a browser with none is so many
 * letters to it, as it is to the browser of a test. `off` is what that holds, read as a
 * browser with scripts off reads it, in the order it stands in.
 */
function built() {
  const html = renderToString(
    <Shell meta={meta.meta}>
      <SearchApp meta={meta.data} areas={areas} bands={bands} client={standInApi().client} />
    </Shell>,
  );
  const on = holding(html);
  const kept = [...on.querySelectorAll("noscript")];
  return { html, on, kept, off: holding(kept.map((one) => one.textContent ?? "").join("")) };
}

/**
 * A browser whose style sheet says which screen there is, as the sheet of the page does by
 * the width of the screen. jsdom reads no sheet of the page, so the test says it, of the
 * page as the page names itself. It is taken back when the test ends.
 */
function aScreen(which: "narrow" | "middle" | "wide"): () => void {
  const sheet = document.createElement("style");
  sheet.textContent = `[data-dressed] { --screen: ${which}; }`;
  document.head.append(sheet);
  return () => sheet.remove();
}

/** The spec a recorded ranking returned, which is what the page holds once it is answered. */
const recordedSpec = (name: string) => recordedAnswer("rank", name).body.data.spec;

/** What a search may be for, by the names the settings give the three, in the order they are asked in. */
const THE_KINDS = [TENURE_CHOICE.rent, TENURE_CHOICE.buy, KIND_OF_SEARCH.visit] as const;

const follows = (one: Element, other: Element) =>
  Boolean(one.compareDocumentPosition(other) & Node.DOCUMENT_POSITION_FOLLOWING);
const chips = () => screen.getByRole("region", { name: new RegExp(`^(${CHIPS.label}|${CHIPS.setLabel}|${CHIPS.startLabel})$`) });
const theMap = () => screen.getByRole("region", { name: MAP.label });
/** The groups of the settings that stand open at first, to show that a group opens and closes: the first two, and no other. */
const OPEN_AT_FIRST = [SETTINGS.money, SETTINGS.journeys];
/** The groups that stand open, by the name on the bar of each. */
const standOpen = () =>
  groupsAre()
    .filter(([, open]) => open)
    .map(([name]) => name);
/** A group that is closed at first: the first of the families of vibes, by the name the service gives it. */
const CLOSED_AT_FIRST = meta.data.families[0]?.label ?? "";
const PAGE = rulesOf(readFileSync(path.resolve(__dirname, "..", "..", "src", "components", "SearchApp", "SearchApp.module.css"), "utf8"));

describe("the message", () => {
  test("test_the_heading_is_find_your_area_and_the_line_under_it_says_who_burro_is_for", async () => {
    // The founder: "The overall message of the app/product is to 'Find your area' whether
    // buying, renting, or just visiting, Burro will help you find an area to call your own."
    await openSearch();
    const heading = screen.getByRole("heading", { level: 1 });
    const box = heading.closest("[data-kind]") as HTMLElement;

    expect(heading).toHaveTextContent(/^Find your area$/);
    expect(SEARCH.title).toBe("Find your area");
    const lead = within(box).getByText(/./, { selector: "p" }).textContent ?? "";
    expect(lead).toBe(leadFor(meta.data.holds));
    expect(lead.startsWith(SEARCH.forWhom)).toBe(true);
    for (const who of ["buying", "renting", "just visiting"]) expect([who, SEARCH.forWhom.includes(who)]).toEqual([who, true]);
    expect(SEARCH.forWhom).toContain("an area to call your own");
    // It is a sentence or two, and says nothing is the best.
    expect(lead.split(/(?<=\.)\s+/)).toHaveLength(2);
    expect(/\b(best|perfect|ideal|top)\b/i.test(lead)).toBe(false);
    // Burro sits beside the heading as he does.
    expect(box.querySelector("[data-pose]")).toHaveAttribute("data-pose", "sits");
  });

  test("test_on_a_narrow_screen_the_line_says_who_burro_is_for_and_leaves_the_rest_to_the_two_ways_in", async () => {
    // The map stands between the heading and the two ways in there, and the box is on the
    // first screen with it. Measured at 390 by 844: the second sentence took three lines of
    // the six under the heading, 72 px, and with it the box began under the first screen.
    await openSearch();
    const line = within(screen.getByRole("heading", { level: 1 }).closest("[data-kind]") as HTMLElement).getByText(/./, { selector: "p" });
    const rest = line.querySelector("span") as HTMLElement;

    // Who it is for is said first, on every screen, and the rest is a part of its own.
    expect(line.firstChild?.textContent).toBe(SEARCH.forWhom);
    expect(`${SEARCH.forWhom} ${rest.textContent}`).toBe(leadFor(meta.data.holds));
    expect(rest).toHaveClass("how");
    const gone = PAGE.filter((rule) => rule.selector === ".how");
    expect(gone.map((rule) => [rule.under, rule.sets.get("display")])).toEqual([["@media (max-width: 40rem)", "none"]]);
    // Nothing else of the heading is taken away, on any screen.
    expect(PAGE.filter((rule) => /\.(lead|title|head)\b/.test(rule.selector) && rule.sets.get("display") === "none")).toEqual([]);
  });

  test("test_the_title_of_the_website_and_what_a_search_engine_and_a_shared_link_show_say_the_same", () => {
    const title = `${SEARCH.title} · ${SITE.name}`;

    expect(metadata.title).toEqual({ absolute: title });
    expect(metadata.description).toBe(SITE.description);
    expect(SITE.description.startsWith(SEARCH.forWhom)).toBe(true);
    expect(metadata.openGraph).toMatchObject({ title, description: SITE.description, siteName: SITE.name });
    expect(metadata.twitter).toMatchObject({ title, description: SITE.description });
  });

  test("test_the_line_speaks_of_places_to_reach_only_where_the_data_names_some", () => {
    expect(leadFor({ journeys: true })).toBe(SEARCH.lead);
    expect(leadFor({ journeys: false })).toBe(SEARCH.leadNoJourneys);
    expect(SEARCH.lead).toContain("places you need to reach");
    expect(SEARCH.leadNoJourneys).not.toContain("reach");
    for (const lead of [SEARCH.lead, SEARCH.leadNoJourneys]) expect(lead.startsWith(SEARCH.forWhom)).toBe(true);
  });
});

describe("the first screen, as it is built", () => {
  test("test_with_scripts_on_it_draws_two_tabs_the_first_chosen_the_box_and_two_helpers_each_closed", () => {
    const { on } = built();
    const page = within(on);

    const tabs = within(page.getByRole("tablist", { name: WAYS.label })).getAllByRole("tab");
    expect(tabs.map((tab) => [tab.textContent, tab.getAttribute("aria-selected")])).toEqual([
      [WAYS.quick, "true"],
      [WAYS.deep, "false"],
    ]);
    expect(page.getByRole("textbox", { name: PROMPT.label })).toBeInTheDocument();
    const line = within(page.getByRole("group", { name: HELPERS.label }));
    expect(line.getAllByRole("button").map((button) => [button.textContent, button.getAttribute("aria-expanded")])).toEqual([
      [HELPERS.example, "false"],
      [HELPERS.word, "false"],
    ]);
    // Each names the part it opens, which is in the page and holds nothing.
    for (const button of line.getAllByRole("button")) {
      const part = on.querySelector(`[id="${button.getAttribute("aria-controls")}"]`);
      expect(part?.hasAttribute("hidden")).toBe(true);
      expect(part?.childNodes).toHaveLength(0);
    }
    // The panel of the second way is in the page, so that its tab names something. It is
    // not drawn, and holds nothing until the way is chosen.
    const deep = on.querySelector(`[id="${tabs[1]?.getAttribute("aria-controls")}"]`);
    expect(deep?.getAttribute("role")).toBe("tabpanel");
    expect(deep?.hasAttribute("hidden")).toBe(true);
    expect(deep?.childNodes).toHaveLength(0);
    expect(on.querySelector("[aria-expanded='true'], details[open]")).toBeNull();
    expect(page.queryByRole("heading", { name: PROMPT.examplesTitle })).toBeNull();
    expect(page.queryByRole("heading", { name: SHELF.title })).toBeNull();
    expect(page.queryByRole("combobox")).toBeNull();
    expect(page.queryByRole("textbox", { name: FIND_AREA.labelAlone })).toBeNull();
    expect(page.queryAllByRole("radio")).toEqual([]);
    expect(page.queryByRole("button", { name: REFINE.label })).toBeNull();
  });

  test("test_with_scripts_off_both_ways_are_in_the_page_one_after_the_other_each_under_its_name", () => {
    // A tab needs a script. Where none runs, nothing could choose the second way, so what
    // each holds is in the page as it is built, and a browser with scripts on is never
    // shown it. The box is in the page either way, under the name of the first.
    const { on, off, kept, html } = built();
    const page = within(off);

    // The name of the first way, what its helpers hold, and the second way under its name.
    expect(kept).toHaveLength(3);
    expect(html.match(/<noscript>/g)).toHaveLength(3);
    const [first, second] = [page.getByRole("heading", { name: WAYS.quick }), page.getByRole("heading", { name: WAYS.deep })];
    expect([first.tagName, second.tagName]).toEqual(["H2", "H2"]);
    // The name of the first stands over the box, and the box over what its helpers hold.
    const box = within(on).getByRole("textbox", { name: PROMPT.label });
    expect(follows(kept[0] as HTMLElement, box)).toBe(true);
    expect(follows(box, kept[1] as HTMLElement)).toBe(true);
    expect(follows(within(on).getByRole("group", { name: HELPERS.label }), kept[1] as HTMLElement)).toBe(true);
    expect(follows(kept[1] as HTMLElement, kept[2] as HTMLElement)).toBe(true);

    for (const example of examplesFor(meta.data)) {
      expect(page.getByRole("button", { name: example })).toBeInTheDocument();
    }
    expect(examplesFor(meta.data)).toHaveLength(3);
    for (const tag of placedOf(meta.data, meta.data.tags).slice(0, 3)) {
      expect(page.getByRole("button", { name: wordOf(tag) })).toBeInTheDocument();
    }
    // The second way: what it is, the settings, what ranks by them, and the field that finds an area.
    expect(off.textContent?.includes(DEEP.lead)).toBe(true);
    const settings = page.getByRole("region", { name: SETTINGS.title });
    // Renting, buying or visiting is asked once, by the first group of the settings, which
    // stands open. Each of the three is there to be chosen, and renting is chosen.
    const asked = page.getAllByRole("group", { name: TENURE_CHOICE.legend });
    expect(asked.map((one) => settings.contains(one))).toEqual([true]);
    const kinds = within(asked[0] as HTMLElement);
    expect(kinds.getAllByRole("radio")).toHaveLength(THE_KINDS.length);
    expect(THE_KINDS.map((name) => kinds.getByRole<HTMLInputElement>("radio", { name }).checked)).toEqual([true, false, false]);
    expect(within(settings).getByRole("button", { name: SETTINGS.money })).toHaveAttribute("aria-expanded", "true");
    const ranks = page.getByRole("button", { name: SETTINGS.rank });
    const finds = page.getByRole("textbox", { name: FIND_AREA.labelAlone });
    // In the order of the page: the first way, what its helpers hold, and the second way.
    const order = [
      first,
      page.getByRole("heading", { name: PROMPT.examplesTitle }),
      page.getByRole("heading", { name: SHELF.title }),
      second,
      page.getByText(DEEP.lead),
      settings,
      ranks,
      finds,
    ];
    order.slice(1).forEach((part, at) => expect(follows(order[at] as HTMLElement, part)).toBe(true));
    // No id of the page is used twice, and no fold stands over the settings there.
    const ids = [...document.querySelectorAll("[id]")].map((one) => one.id);
    expect(ids.filter((id, at) => ids.indexOf(id) !== at)).toEqual([]);
    expect(page.queryByRole("button", { name: REFINE.label })).toBeNull();
  });

  test("test_with_scripts_off_no_tab_is_drawn_and_the_second_way_stands_in_the_column_of_the_first", () => {
    const tabs = rulesOf(
      readFileSync(path.resolve(__dirname, "..", "..", "src", "components", "SearchApp", "Ways.module.css"), "utf8"),
    ).filter((rule) => rule.under === "@media (scripting: none)");
    expect(tabs.map((rule) => [rule.selector, rule.sets.get("display")])).toEqual([[".ways", "none"]]);

    const kept = PAGE.filter((rule) => rule.selector === ".columns > noscript" && rule.under === "@media (min-width: 60rem)");
    expect(kept.map((rule) => rule.sets.get("grid-column"))).toContain("1");
  });
});

describe("two ways in", () => {
  test("test_quick_search_is_chosen_at_first_and_holds_the_box_what_a_useful_sentence_holds_and_two_helpers", async () => {
    await openSearch();
    const panel = within(panelOf("quick"));

    expect(tabOf("quick")).toHaveAttribute("aria-selected", "true");
    expect(tabOf("deep")).toHaveAttribute("aria-selected", "false");
    expect(panelOf("quick")).toBeVisible();
    expect(panel.getByRole("textbox", { name: PROMPT.label })).toBe(promptBox());
    expect(panel.getByRole("button", { name: PROMPT.submit })).toBeInTheDocument();
    // Under its heading the box says what a useful sentence holds, and gives one whole
    // sentence as an example: the first that the data can answer the whole of.
    const [example] = examplesFor(meta.data);
    expect(example).toBeDefined();
    expect(panel.getByText(PROMPT.hintFor(meta.data.holds))).toBeInTheDocument();
    expect(panel.getByText(example as string).tagName).toBe("Q");
    expect(promptBox()).toHaveAccessibleDescription(
      `${PROMPT.hintFor(meta.data.holds)} ${PROMPT.forExample} ${example}`,
    );
    // Nothing of how words are handled stands in the panel, and no link leads out of it.
    expect(panelOf("quick").textContent).not.toMatch(/who (else )?reads what you type/i);
    expect(panelOf("quick").textContent?.includes(WORDS_LINE)).toBe(false);
    expect(panelOf("quick").textContent?.includes(meta.data.reader.notice)).toBe(false);
    expect(panel.queryByRole("link")).toBeNull();
    expect(within(helpers()).getAllByRole("button").map((button) => button.textContent)).toEqual([HELPERS.example, HELPERS.word]);
    expect(panelOf("quick")).toContainElement(helpers());
  });

  test("test_the_helper_that_chose_without_typing_is_gone_for_deep_search_is_what_it_was", async () => {
    await openSearch();

    // What it was named is written here, and in no file of site copy that a page draws.
    expect(screen.queryByRole("button", { name: /^Choose without typing/ })).toBeNull();
    expect(screen.queryByText(/Choose without typing/)).toBeNull();
    expect(within(helpers()).getAllByRole("button")).toHaveLength(2);
    expect(screen.queryByRole("button", { name: SETTINGS.title })).toBeNull();
  });

  test("test_deep_search_is_a_sentence_that_says_what_it_is_the_settings_and_the_button_that_ranks", async () => {
    const { user } = await openSearch();

    await way(user, "deep");

    const panel = within(panelOf("deep"));
    expect(panelOf("deep")).toBeVisible();
    expect(panelOf("quick")).not.toBeVisible();
    expect(panel.getByText(DEEP.lead)).toBeVisible();
    const parts = [
      panel.getByText(DEEP.lead),
      theSettings(),
      // The button that ranks by them stands under them, and is the page's own there.
      panel.getByRole("button", { name: SETTINGS.rank }),
    ];
    parts.slice(1).forEach((part, at) => expect(follows(parts[at] as HTMLElement, part)).toBe(true));
    for (const part of parts) expect(panelOf("deep")).toContainElement(part);
    // The settings stand open, under no button of their own, and every group of them is there.
    expect(whatRefines()).toBeNull();
    expect(screen.queryByRole("button", { name: SETTINGS.title })).toBeNull();
    expect(within(theSettings()).getByRole("button", { name: SETTINGS.journeys })).toBeVisible();
    expect(standOpen()).toEqual(OPEN_AT_FIRST);
    // The sentence stands in a box of its own, which holds nothing to press, and the settings in the next.
    const box = parts[0]?.closest("[data-kind]") as HTMLElement;
    expect(box).toHaveAttribute("data-kind", "box");
    expect(box).not.toContainElement(theSettings());
    expect(box.querySelectorAll("button, input, select, textarea, a")).toHaveLength(0);
    // It says what makes the search, by the name the button bears.
    expect(DEEP.lead).toContain(`"${SETTINGS.rank}"`);
    expect(DEEP.lead).not.toMatch(/two questions/);
  });

  test("test_deep_search_asks_renting_buying_or_visiting_and_a_place_to_reach_once_and_the_settings_are_what_asks", async () => {
    // Seen in a browser by three people: its own box asked renting or buying and a place to
    // reach, and directly under it the first two groups of the settings stood open and
    // asked the same, with the same two buttons and a second field. A newcomer could not
    // tell which to answer. By keyboard the first stop and the fourth were two radios heard
    // the very same. The founder has since asked for a third choice, a visit, beside the
    // two: the three are asked once, as the two were.
    const { user, api } = await openSearch();
    api.calls.length = 0;
    await way(user, "deep");
    const panel = within(panelOf("deep"));

    const asked = panel.getAllByRole("group", { name: TENURE_CHOICE.legend });
    expect(asked.map((one) => theSettings().contains(one))).toEqual([true]);
    expect(within(asked[0] as HTMLElement).getAllByRole("radio")).toHaveLength(THE_KINDS.length);
    for (const name of THE_KINDS) expect(panel.getAllByRole("radio", { name })).toHaveLength(1);
    // One field finds a place to reach, in the group of the journeys, and what the group
    // says of it names one field and no other.
    const [reach, ...more] = panel.getAllByRole("combobox").filter((field) => field.tagName === "INPUT");
    expect(more).toEqual([]);
    expect(reach).toHaveAccessibleName(PLACE.label);
    expect(theSettings()).toContainElement(reach as HTMLElement);
    // The other finds an area by its name, which is no question of a search: it is at the
    // foot. It opens no list, so it is a plain field and says nothing of one.
    const find = panel.getByRole("textbox", { name: FIND_AREA.labelAlone });
    expect(theSettings()).not.toContainElement(find);
    expect(panel.queryByRole("combobox", { name: FIND_AREA.label })).toBeNull();
    expect(panel.getByText(JOURNEY.none)).toBeVisible();

    // Before anything is asked for a choice sends nothing, and no search is open: of
    // buying, and of a visit as of buying.
    for (const name of [TENURE_CHOICE.buy, KIND_OF_SEARCH.visit]) {
      await user.click(panel.getByRole("radio", { name }));
      await arrived();
      expect(panel.getByRole("radio", { name })).toBeChecked();
      expect(api.calls).toEqual([]);
      expect(ways()).toBeInTheDocument();
    }
  });

  test("test_an_area_is_found_by_its_name_at_the_foot_of_the_second_way_and_is_no_part_of_a_search", async () => {
    // The field that stood with the two questions found an area by its name too, and was the
    // one way to on the page. It stands after the button that makes the search, finds areas
    // alone, and each is a link to its page.
    const { user, api } = await openSearch();
    await way(user, "deep");
    const panel = within(panelOf("deep"));
    const field = panel.getByRole("textbox", { name: FIND_AREA.labelAlone });

    expect([AN_AREA_BY_NAME, FINDS_AN_AREA]).toEqual(["foot", ["foot", "nowhere"]]);
    expect(follows(panel.getByRole("button", { name: SETTINGS.rank }), field)).toBe(true);
    expect(field).toHaveAccessibleDescription(DEEP.finds);
    expect(DEEP.finds).not.toMatch(/station|workplace|school|journey/i);

    await user.type(field, "pel");
    const found = await panel.findByRole("group", { name: FIND_AREA.title });
    const links = within(found).getAllByRole("link");
    expect(links.map((link) => link.textContent)).toEqual(["Pellam Cross"]);
    expect(links[0]).toHaveAttribute("href", expect.stringMatching(/pellam-cross$/));
    // No place to reach is offered by it: it opens no list, and nothing is added to a search.
    expect(field).not.toHaveAttribute("aria-controls");
    expect(field.closest("[data-kind]")?.querySelectorAll("[role=listbox], [role=option]")).toHaveLength(0);
    expect(api.callsTo("rank")).toEqual([]);
    expect(ways()).toBeInTheDocument();
  });

  test("test_where_the_data_names_no_place_the_field_that_finds_an_area_says_why_it_finds_none", async () => {
    // Seen in a browser, of the field as it was: a place typed in it was met with "No place
    // matches. Try another spelling", where no spelling could match. The settings have no
    // field for a place there, so this is the one field a place would be typed in.
    const user = userEvent.setup({ delay: null });
    const noPlaces = { ...meta.data, holds: { ...meta.data.holds, journeys: false } };
    render(
      <Shell meta={meta.meta}>
        <SearchApp meta={noPlaces} areas={areas} bands={bands} client={firstSearch().client} />
      </Shell>,
    );
    await arrived();
    await way(user, "deep");
    const panel = within(panelOf("deep"));

    expect(panel.queryByRole("combobox", { name: PLACE.label })).toBeNull();
    const field = panel.getByRole("textbox", { name: FIND_AREA.labelAlone });
    expect(field).toHaveAccessibleDescription(FIND_AREA.hintAlone);
    expect(FIND_AREA.hintAlone).toMatch(/\bno places\b/);
    expect(panel.queryByText(DEEP.finds)).toBeNull();
  });

  test("test_one_line_of_the_look_takes_the_field_that_finds_an_area_away", async () => {
    const user = userEvent.setup({ delay: null });
    render(
      <Shell meta={meta.meta}>
        <SearchApp meta={meta.data} areas={areas} bands={bands} client={firstSearch().client} finds="nowhere" />
      </Shell>,
    );
    await arrived();
    await way(user, "deep");

    expect(screen.queryByRole("textbox", { name: FIND_AREA.labelAlone })).toBeNull();
    expect(screen.getByRole("button", { name: SETTINGS.rank })).toBeInTheDocument();
  });

  test("test_nothing_opens_or_closes_the_settings_while_they_stand_in_the_second_way_in", async () => {
    // They are the part that refines a search, in the place it will stand in, held open.
    // What would open and close it is not drawn, by a rule of the page, and Escape closes nothing.
    const { user } = await openSearch();
    await way(user, "deep");
    const fold = theSettings().closest("[data-standing]") as HTMLElement;

    expect(fold).toHaveAttribute("data-standing", "true");
    const hidden = PAGE.filter((rule) => rule.under === null && rule.sets.get("display") === "none").map((rule) => rule.selector);
    expect(hidden).toContain('.refine[data-standing="true"] > .fold > [aria-expanded][aria-controls]');
    expect(hidden).toContain('.refine[data-standing="true"] > .fold > :has(> [aria-expanded][aria-controls])');
    // The page says it of the button too, so that no keyboard stops at it and nobody hears it.
    expect(whatRefines()).toBeNull();
    expect(screen.queryByText(REFINE.label)).not.toBeVisible();

    await user.click(within(theSettings()).getByRole("button", { name: SETTINGS.money }));
    await user.keyboard("{Escape}{Escape}");

    expect(theSettings()).toBeVisible();
    expect(tabOf("deep")).toHaveAttribute("aria-selected", "true");
  });

  test("test_nothing_is_lost_by_changing_tab", async () => {
    const { user, api } = await openSearch();
    const box = promptBox();
    await user.type(box, "leafy and quiet, near a par");
    await helper(user, "example");

    await way(user, "deep");
    await user.click(screen.getByRole("radio", { name: TENURE_CHOICE.buy }));
    // A group that stands open at first is closed, and one that is closed is opened.
    const bar = (name: string) => within(theSettings()).getByRole("button", { name });
    expect([SETTINGS.journeys, CLOSED_AT_FIRST].map((name) => bar(name).getAttribute("aria-expanded"))).toEqual(["true", "false"]);
    await user.click(bar(SETTINGS.journeys));
    await user.click(bar(CLOSED_AT_FIRST));
    const settings = theSettings();
    await way(user, "quick");

    // What was typed is there, in the box it was typed in, and the helper that was open is open.
    expect(promptBox()).toBe(box);
    expect(box).toHaveValue("leafy and quiet, near a par");
    expect(box).toBeVisible();
    expect(screen.getByRole("button", { name: HELPERS.example })).toHaveAttribute("aria-expanded", "true");

    await way(user, "deep");

    // What was set is set, what was opened is open and what was closed is closed: they are
    // the settings they were.
    expect(theSettings()).toBe(settings);
    expect(screen.getByRole("radio", { name: TENURE_CHOICE.buy })).toBeChecked();
    expect([SETTINGS.journeys, CLOSED_AT_FIRST].map((name) => bar(name).getAttribute("aria-expanded"))).toEqual(["false", "true"]);
    // Nothing was sent by changing tab, and no search is open.
    expect(api.callsTo("interpret")).toHaveLength(0);
    expect(api.callsTo("rank")).toHaveLength(0);
    expect(ways()).toBeInTheDocument();
  });

  test("test_nothing_of_either_is_kept_in_the_address_or_in_the_storage_of_the_browser", async () => {
    const seen = watch();
    try {
      const { user } = await openSearch();
      const address = window.location.href;
      await user.type(promptBox(), "zqxcanary7431 by the river");

      await way(user, "deep");
      await user.click(screen.getByRole("radio", { name: TENURE_CHOICE.buy }));
      await way(user, "quick");
      act(() => tabOf("quick").focus());
      await user.keyboard("{ArrowRight}{Home}");

      expect(seen.storage).toEqual([]);
      expect(seen.history).toEqual([]);
      expect(window.location.href).toBe(address);
      expect(seen.everythingOutsideThePage().includes("zqxcanary7431")).toBe(false);
      // Which tab is chosen is said by the tab, and by nothing a link could carry.
      expect(seen.addresses()).not.toMatch(/quick|deep/i);
    } finally {
      seen.stop();
    }
  });

  test("test_they_are_real_tabs_to_a_keyboard", async () => {
    const { user } = await openSearch();

    act(() => tabOf("quick").focus());
    await user.keyboard("{ArrowRight}");
    expect(tabOf("deep")).toHaveFocus();
    expect(tabOf("deep")).toHaveAttribute("aria-selected", "true");
    expect(panelOf("deep")).toBeVisible();

    // Tab goes from the chosen tab into its panel, where the first stop is the bar of the
    // first group of the settings: nothing to answer stands over them.
    await user.tab();
    expect(panelOf("deep")).toContainElement(document.activeElement as HTMLElement);
    expect(document.activeElement).toBe(within(theSettings()).getByRole("button", { name: SETTINGS.money }));

    act(() => tabOf("deep").focus());
    await user.keyboard("{Home}");
    expect(tabOf("quick")).toHaveFocus();
    expect(tabOf("quick")).toHaveAttribute("aria-selected", "true");
    await user.tab();
    expect(promptBox()).toHaveFocus();

    act(() => tabOf("quick").focus());
    await user.keyboard("{End}");
    expect(tabOf("deep")).toHaveAttribute("aria-selected", "true");
    await user.keyboard("{ArrowRight}");
    expect(tabOf("quick")).toHaveAttribute("aria-selected", "true");
  });

  test("test_the_page_has_no_accessibility_fault_whichever_way_is_chosen", async () => {
    const { user, container } = await openSearch();
    expect(await faultsIn(container, { wholePage: true })).toEqual([]);

    await way(user, "deep");
    expect(await faultsIn(container, { wholePage: true })).toEqual([]);

    await user.click(within(theSettings()).getByRole("button", { name: SETTINGS.money }));
    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });

  test("test_words_that_could_not_be_read_leave_the_first_way_chosen_and_name_the_second", async () => {
    // The settings do the same job, and before a search they stand in the second way in.
    // The page opened them under the box. It now says where they are, and moves nothing:
    // what failed is said in the box, which a change of tab would hide.
    const { user } = await openSearch(firstSearch().on("interpret", "error-internal"));
    await user.type(promptBox(), "leafy");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    await screen.findByRole("button", { name: PROMPT.tryAgain });

    expect(tabOf("quick")).toHaveAttribute("aria-selected", "true");
    expect(panelOf("quick")).toBeVisible();
    const said = screen.getAllByRole("status").map((line) => line.textContent ?? "");
    expect(said.filter((line) => line.includes(WAYS.deep))).toHaveLength(1);
    expect(theSettingsIfAny()).toBeNull();
  });
});

describe("the map, on both tabs", () => {
  test("test_the_map_is_in_the_page_whichever_tab_is_chosen_and_is_the_map_it_was", async () => {
    setWebGL(true);
    const { user } = await openSearch();
    act(() => lastMap().fire("load"));
    await arrived();
    const [map, drawn] = [theMap(), lastMap()];

    await way(user, "deep");
    expect(theMap()).toBe(map);
    expect(theMap()).toBeVisible();
    expect(lastMap()).toBe(drawn);
    // It stands outside both panels, so that neither holds it and neither hides it.
    for (const which of ["quick", "deep"] as const) expect(panelOf(which)).not.toContainElement(map);

    await way(user, "quick");
    expect(theMap()).toBe(map);
    expect(lastMap()).toBe(drawn);
  });

  test("test_it_comes_after_both_ways_in_the_page_and_stands_beside_them_on_a_wide_screen", async () => {
    const { user } = await openSearch();
    await way(user, "deep");

    expect(follows(ways(), theMap())).toBe(true);
    expect(follows(panelOf("quick"), theMap())).toBe(true);
    expect(follows(panelOf("deep"), theMap())).toBe(true);
    // Beside them from 60rem, in a column of its own, where no tab and no panel is placed.
    const wide = PAGE.filter((rule) => rule.under === "@media (min-width: 60rem)");
    const columnOf = (part: string) => wide.filter((rule) => rule.selector === part).map((rule) => rule.sets.get("grid-column")).filter(Boolean);
    expect(columnOf(".map")).toEqual(["2"]);
    for (const part of [".form", ".refine"]) expect([part, wide.some((rule) => rule.selector === part && rule.sets.get("grid-column") === "1")]).toEqual([part, true]);
    // No rule places or sizes the map by which way is chosen.
    expect(PAGE.filter((rule) => /\.map\b/.test(rule.selector) && /aria-selected|tabpanel|data-standing|hidden/.test(rule.selector))).toEqual([]);
  });
});

describe("what a helper opens, under the name of the helper", () => {
  test("test_a_name_is_said_once_under_the_helper_that_says_it", async () => {
    // Seen in a browser: the shelf's own heading "Start from a word" stood directly under
    // the helper of the same name, and "Examples" under "Try an example".
    const { user } = await openSearch();
    const drawn = () =>
      screen
        .getAllByRole("heading")
        .filter((heading) => heading.closest(".visually-hidden") === null)
        .map((heading) => heading.textContent);

    await helper(user, "word");
    const shelf = screen.getByRole("region", { name: SHELF.title });
    expect(shelf).toHaveAttribute("aria-labelledby", screen.getByRole("button", { name: HELPERS.word }).id);
    expect(within(shelf).queryByRole("heading", { name: SHELF.title })).toBeNull();
    expect(drawn()).toEqual([SEARCH.title]);

    await helper(user, "example");
    const examples = screen.getByRole("region", { name: PROMPT.examplesTitle });
    expect(within(examples).getByRole("heading", { name: PROMPT.examplesTitle })).toHaveClass("visually-hidden");
    expect(drawn()).toEqual([SEARCH.title]);
  });

  test("test_with_scripts_off_no_helper_stands_over_them_and_each_draws_its_heading", () => {
    const { off } = built();
    const page = within(off);

    for (const name of [PROMPT.examplesTitle, SHELF.title]) {
      expect(page.getByRole("heading", { name })).not.toHaveClass("visually-hidden");
    }
  });
});

describe("the map, while a helper is open", () => {
  test("test_the_map_is_coloured_by_a_word_only_while_the_card_of_the_word_is_open_on_the_shelf", async () => {
    // The map is coloured by the word whose card is open. The card goes with the shelf when
    // the helper that holds it is closed, or another is opened: the map then says nothing
    // of a word that is nowhere on the page.
    setWebGL(true);
    const { user } = await openSearch();
    act(() => lastMap().fire("load"));
    await arrived();
    const legend = () => screen.getByRole("region", { name: LEGEND.title });
    const open = async () => {
      await helper(user, "word");
      await user.click(within(screen.getByRole("region", { name: SHELF.title })).getByRole("button", { name: "leafy" }));
    };

    await open();
    expect(legend().textContent?.includes(LEGEND.vibe("Leafy"))).toBe(true);

    // Another helper is opened.
    await helper(user, "example");
    expect(legend().textContent?.includes(LEGEND.vibe("Leafy"))).toBe(false);
    expect(legend().textContent?.includes(LEGEND.noScore)).toBe(true);
    // The shelf opens again with no card open, as it first stood.
    await helper(user, "word");
    const words = within(screen.getByRole("region", { name: SHELF.title })).getAllByRole("button");
    expect(words.filter((word) => word.getAttribute("aria-expanded") === "true")).toEqual([]);
    expect(legend().textContent?.includes(LEGEND.vibe("Leafy"))).toBe(false);

    // The helper is closed with a card open.
    await user.click(screen.getByRole("button", { name: "leafy" }));
    expect(legend().textContent?.includes(LEGEND.vibe("Leafy"))).toBe(true);
    await user.click(screen.getByRole("button", { name: HELPERS.word }));
    expect(legend().textContent?.includes(LEGEND.vibe("Leafy"))).toBe(false);
  });

  test("test_the_map_says_nothing_of_a_word_while_the_second_way_is_chosen_and_says_it_again_on_the_way_back", async () => {
    // The card of the word is in the first way in. It is kept while the second is chosen,
    // and is not drawn: so the map is not coloured by a word that is nowhere in sight.
    setWebGL(true);
    const { user } = await openSearch();
    act(() => lastMap().fire("load"));
    await arrived();
    const legend = () => screen.getByRole("region", { name: LEGEND.title });
    await helper(user, "word");
    await user.click(within(screen.getByRole("region", { name: SHELF.title })).getByRole("button", { name: "leafy" }));
    expect(legend().textContent?.includes(LEGEND.vibe("Leafy"))).toBe(true);

    await way(user, "deep");
    expect(legend().textContent?.includes(LEGEND.vibe("Leafy"))).toBe(false);
    expect(legend().textContent?.includes(LEGEND.noScore)).toBe(true);

    await way(user, "quick");
    expect(screen.getByRole("button", { name: "leafy" })).toHaveAttribute("aria-expanded", "true");
    expect(legend().textContent?.includes(LEGEND.vibe("Leafy"))).toBe(true);
  });
});

describe("the box, when a first search opens of a sentence", () => {
  /**
   * Stands the field at one place in the window before a search and at another once one is
   * open, as a browser does when the heading over the box gives way, and hears how far the
   * page is asked to scroll. jsdom lays nothing out, and scrolls nothing.
   */
  function standing(at: { readonly before: number; readonly open: number }) {
    const asked: (readonly [number, number])[] = [];
    const measure = jest.spyOn(HTMLTextAreaElement.prototype, "getBoundingClientRect").mockImplementation(function (
      this: HTMLTextAreaElement,
    ) {
      const open = this.closest("[data-search]")?.getAttribute("data-search") === "open";
      const top = open ? at.open : at.before;
      return { top, bottom: top + 46, left: 0, right: 0, x: 0, y: top, width: 0, height: 46, toJSON: () => ({}) };
    });
    const scroll = jest.spyOn(window, "scrollBy").mockImplementation(((x: number, y: number) => {
      asked.push([x, y]);
    }) as typeof window.scrollBy);
    return {
      asked,
      putBack: () => {
        measure.mockRestore();
        scroll.mockRestore();
      },
    };
  }

  test("test_the_field_stays_where_it_stood_in_the_window_as_a_first_search_opens", async () => {
    // Seen on a phone: a person scrolled down to an example, pressed it, and pressed Search.
    // The heading over the box gave way as the search opened, 280 px of it, and the box went
    // up and out of the window from under the press, with the first result after it.
    const { asked, putBack } = standing({ before: 340, open: 60 });
    try {
      const { user } = await openSearch();

      await search(user);

      // The page goes back by as much as went from over the box, and a browser stops at its top.
      expect(asked).toEqual([[0, -280]]);
    } finally {
      putBack();
    }
  });

  test("test_a_sentence_added_to_an_open_search_moves_nothing", async () => {
    const { asked, putBack } = standing({ before: 340, open: 60 });
    try {
      const { user } = await openSearch();
      await search(user);
      asked.length = 0;

      await user.click(promptBox());
      await user.keyboard(", near a park");
      await user.click(screen.getByRole("button", { name: PROMPT.submit }));
      await settled();

      expect(asked).toEqual([]);
    } finally {
      putBack();
    }
  });

  test("test_a_search_that_opens_of_a_word_is_not_moved_for_a_sentence_that_was_never_sent", async () => {
    // A box with nothing in it sends nothing, and no search opens of the press. The search
    // that opens next, of a word of the shelf, is brought into sight as it always was.
    const { asked, putBack } = standing({ before: 340, open: 60 });
    try {
      const { user } = await openSearch(firstSearch().on("rank", "rank-shelf").on("explain_top", "explanations-shelf"));
      await user.click(screen.getByRole("button", { name: PROMPT.submit }));

      await helper(user, "word");
      await user.click(within(screen.getByRole("region", { name: SHELF.title })).getByRole("button", { name: "lively" }));
      await user.click(screen.getByRole("button", { name: SHELF.add }));
      await settled();

      expect(results().length).toBeGreaterThan(0);
      expect(asked).toEqual([]);
    } finally {
      putBack();
    }
  });
});

describe("a first search, where Burro cannot be reached", () => {
  /**
   * A window that scrolls, as a browser's does, over a page whose field stands at one
   * place before a search and at another once one is open: the heading and the map over
   * the box give way as a search opens, and come back as it closes. A browser scrolls no
   * further than the top of the page. jsdom lays nothing out, and scrolls nothing.
   */
  function aWindow(at: { readonly before: number; readonly open: number; readonly scrolled: number; readonly late?: number }) {
    let scrolled = at.scrolled;
    // How much higher what comes back over the box stands than it will, once a search has
    // been seen open, until it has settled.
    let seenOpen = false;
    let unsettled = 0;
    // What is told when a part of the page takes another size, as a browser tells it.
    const told: (() => void)[] = [];
    const sizes = (globalThis as { ResizeObserver?: unknown }).ResizeObserver;
    (globalThis as { ResizeObserver?: unknown }).ResizeObserver = class {
      private readonly tell: () => void;
      constructor(tell: () => void) {
        this.tell = tell;
      }
      observe() {
        told.push(this.tell);
      }
      disconnect() {
        if (told.includes(this.tell)) told.splice(told.indexOf(this.tell), 1);
      }
      unobserve() {
        this.disconnect();
      }
    };
    const brought: { readonly part: Element; readonly how: unknown }[] = [];
    const inThePage = (field: Element) => {
      const open = field.closest("[data-search]")?.getAttribute("data-search") === "open";
      if (!open && seenOpen) unsettled = at.late ?? 0;
      seenOpen = open;
      return open ? at.open : at.before + unsettled;
    };
    const standing = (top: number, high: number) => ({
      top,
      bottom: top + high,
      left: 0,
      right: 0,
      x: 0,
      y: top,
      width: 0,
      height: high,
      toJSON: () => ({}),
    });
    const measure = jest.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function (
      this: HTMLElement,
    ) {
      if (this instanceof HTMLTextAreaElement) return standing(inThePage(this) - scrolled, FIELD);
      // What says that a search failed stands under the field, and is so high with its buttons.
      const field = this.matches("[data-failure]") ? this.closest("section")?.querySelector("textarea") : null;
      if (field) return standing(inThePage(field) - scrolled + FIELD + GAP, NOTICE_HIGH);
      return standing(0, 0);
    });
    const scroll = jest.spyOn(window, "scrollBy").mockImplementation(((x: number, y: number) => {
      scrolled = Math.max(0, scrolled + y);
    }) as typeof window.scrollBy);
    const was = Object.getOwnPropertyDescriptor(window, "scrollY");
    const high = Object.getOwnPropertyDescriptor(window, "innerHeight");
    Object.defineProperty(window, "scrollY", { configurable: true, get: () => scrolled });
    Object.defineProperty(window, "innerHeight", { configurable: true, value: WINDOW });
    Object.defineProperty(Element.prototype, "scrollIntoView", {
      configurable: true,
      writable: true,
      value(this: Element, how: unknown) {
        brought.push({ part: this, how });
      },
    });
    return {
      brought,
      /** Where the field stands in the window. */
      field: () => promptBox().getBoundingClientRect().top,
      /** Where what says that the search failed stands in the window, from its top to its foot. */
      said: () => {
        const said = screen.getByRole("alert").closest("[data-failure]")?.getBoundingClientRect();
        return [said?.top, said?.bottom];
      },
      /** The person scrolls the page, and the page hears of it. */
      scrollBy(by: number) {
        scrolled = Math.max(0, scrolled + by);
        fireEvent.scroll(window);
      },
      /** What came back over the box takes the size it will have, and the browser says so. */
      settles() {
        unsettled = 0;
        act(() => {
          for (const tell of [...told]) tell();
        });
      },
      /** How many parts of the page are watched for their size. */
      watched: () => told.length,
      putBack: () => {
        (globalThis as { ResizeObserver?: unknown }).ResizeObserver = sizes;
        measure.mockRestore();
        scroll.mockRestore();
        if (was) Object.defineProperty(window, "scrollY", was);
        else delete (window as { scrollY?: unknown }).scrollY;
        if (high) Object.defineProperty(window, "innerHeight", high);
      },
    };
  }
  /** How high the window of a phone is, its field, the room under the field, and what says that a search failed. */
  const [WINDOW, FIELD, GAP, NOTICE_HIGH] = [844, 71, 11, 156];
  /** A phone, scrolled by a person to the box: the field stands 310 px down the window. */
  const A_PHONE = { before: 708, open: 132, scrolled: 398 };
  const outOfReach = () => firstSearch().unreachable("interpret");
  const theForm = () => screen.getByRole("region", { name: SEARCH.formLabel });

  test("test_the_field_stands_where_it_stood_when_search_was_pressed_once_the_failure_is_said", async () => {
    // Seen on a phone: the search opened as Search was pressed, and the heading and the map
    // over the box gave way. 67 ms later Burro could not be reached, the search closed
    // again and they came back: the page stood at its top, and the field 398 px lower than
    // it had been pressed at.
    const browser = aWindow(A_PHONE);
    try {
      const { user } = await openSearch(outOfReach());
      expect(browser.field()).toBe(310);

      await search(user);

      expect(screen.getByRole("alert")).toHaveTextContent("Burro could not be reached");
      expect(screen.queryAllByRole("tab")).toHaveLength(2);
      expect(browser.field()).toBe(310);
    } finally {
      browser.putBack();
    }
  });

  test("test_the_field_is_held_where_it_stood_while_what_came_back_over_it_settles", async () => {
    // Measured on a phone: the map that came back over the box was 392 px high as the page
    // was laid out, and 210 once it had settled. The page had been moved to hold the field
    // by then, and the field went 182 px up the window after it.
    const browser = aWindow({ ...A_PHONE, late: 182 });
    try {
      const { user } = await openSearch(outOfReach());
      expect(browser.field()).toBe(310);

      await search(user);
      // The page was moved to hold the field as it was laid out, with the map high still.
      expect(browser.field()).toBe(310);
      const held = browser.watched();
      expect(held).toBeGreaterThan(0);

      browser.settles();

      expect(browser.field()).toBe(310);
      // Nothing holds it once a person presses anything: the page is theirs from then.
      fireEvent.pointerDown(promptBox());
      expect(browser.watched()).toBe(held - 1);
    } finally {
      browser.putBack();
    }
  });

  test("test_what_says_so_stands_in_the_box_directly_after_the_field_and_is_brought_into_sight_as_far_as_it_must_be", async () => {
    const browser = aWindow(A_PHONE);
    const restore = aScreen("narrow");
    try {
      const { user } = await openSearch(outOfReach());

      await search(user);

      const said = screen.getByRole("alert");
      expect(theForm()).toContainElement(said);
      expect(follows(promptBox(), said)).toBe(true);
      // Before what a useful sentence holds, which stood between the field and it.
      expect(follows(said, screen.getByText(PROMPT.hintFor(meta.data.holds)))).toBe(true);
      // It is whole and in sight where the field stood 310 px down the window, and nothing is moved for it.
      expect(browser.field()).toBe(310);
      expect(browser.said()).toEqual([310 + FIELD + GAP, 310 + FIELD + GAP + NOTICE_HIGH]);
      // It holds the way to try again, which is what is brought into sight with it.
      expect(said.closest("[data-failure]")).toContainElement(screen.getByRole("button", { name: PROMPT.tryAgain }));
      // No browser is asked to bring it into sight: one keeps room at the foot of the window for the bar of areas.
      expect(browser.brought).toEqual([]);
    } finally {
      restore();
      browser.putBack();
    }
  });

  test("test_as_the_page_opens_the_field_stands_low_and_what_says_so_is_brought_up_until_the_whole_of_it_is_in_sight", async () => {
    // Seen on a phone: the field stands from 708 to 779 of 844 as the page opens, so what is
    // said under it would end 102 px under the foot of the window. The page goes by as much
    // and a little room, and no further.
    const browser = aWindow({ ...A_PHONE, scrolled: 0 });
    try {
      const { user } = await openSearch(outOfReach());
      expect(browser.field()).toBe(708);

      await search(user);

      const [, foot] = browser.said();
      expect(foot).toBe(WINDOW - 8);
      expect(browser.field()).toBe(708 - (708 + FIELD + GAP + NOTICE_HIGH + 8 - WINDOW));
      expect(browser.field()).toBeGreaterThan(0);
    } finally {
      browser.putBack();
    }
  });

  test("test_the_page_goes_where_a_person_takes_it_while_they_wait_and_the_field_stays_where_that_leaves_it", async () => {
    // A service that is slow to fail: the person scrolls the page meanwhile, and is not
    // brought back to where the field stood when they pressed Search.
    const browser = aWindow(A_PHONE);
    try {
      const api = firstSearch();
      const slow = api.hold("interpret", () => {
        throw new TypeError("Failed to fetch");
      });
      const { user } = await openSearch(api);
      await user.type(promptBox(), "leafy and quiet");
      await user.click(screen.getByRole("button", { name: PROMPT.submit }));
      // The search is open, and a browser stops at the top of the page.
      expect(browser.field()).toBe(132);
      browser.scrollBy(60);
      expect(browser.field()).toBe(72);

      slow.release();
      await settled();

      expect(screen.getByRole("alert")).toBeInTheDocument();
      expect(browser.field()).toBe(72);
    } finally {
      browser.putBack();
    }
  });

  test("test_a_first_search_that_is_stopped_leaves_the_field_where_it_stood_as_stop_was_pressed", async () => {
    const browser = aWindow(A_PHONE);
    try {
      const { user } = await openSearch(firstSearch().silent("interpret"));
      await user.type(promptBox(), "leafy and quiet");
      await user.click(screen.getByRole("button", { name: PROMPT.submit }));
      expect(browser.field()).toBe(132);

      await user.click(screen.getByRole("button", { name: PROMPT.stop }));
      await arrived();

      // Stop stands beside the field, and was pressed where the field then stood.
      expect(screen.queryAllByRole("tab")).toHaveLength(2);
      expect(browser.field()).toBe(132);
    } finally {
      browser.putBack();
    }
  });

  test("test_start_again_shows_the_page_from_where_it_stands_and_holds_nothing", async () => {
    // To begin again is to come back to the first page. Nothing is held for it.
    const browser = aWindow({ ...A_PHONE, scrolled: 0 });
    try {
      const { user } = await openSearch();
      await search(user);
      expect(browser.field()).toBe(132);

      await user.click(screen.getByRole("button", { name: PROMPT.startAgain }));
      await arrived();

      expect(browser.field()).toBe(708);
    } finally {
      browser.putBack();
    }
  });

  test("test_a_failure_with_results_in_sight_moves_nothing", async () => {
    // A person may be anywhere among the results when an answer does not come.
    const browser = aWindow({ ...A_PHONE, scrolled: 0 });
    try {
      const { user, api } = await openSearch();
      await search(user);
      browser.brought.length = 0;
      api.unreachable("interpret");

      await user.click(promptBox());
      await user.keyboard(", near a park");
      await user.click(screen.getByRole("button", { name: PROMPT.submit }));
      await settled();

      expect(screen.getByRole("alert")).toBeInTheDocument();
      expect(results().length).toBeGreaterThan(0);
      expect(browser.brought.filter(({ part }) => part.contains(screen.getByRole("alert")))).toEqual([]);
      expect(browser.field()).toBe(132);
      // Though what says so ends under the foot of a window that is lower than it stands.
      Object.defineProperty(window, "innerHeight", { configurable: true, value: 200 });
      await user.click(screen.getByRole("button", { name: PROMPT.tryAgain }));
      await settled();
      expect(browser.field()).toBe(132);
    } finally {
      browser.putBack();
    }
  });
});

describe("the button that makes a search of the second way in", () => {
  const theButtons = () => within(panelOf("deep")).getAllByRole("button", { name: SETTINGS.rank });
  /** The page, with the button standing as one line of the look has it stand. */
  async function standing(button: ButtonStands, api = standInApi().on("rank", "rank-default-rent").on("explain_top", "explanations-first")) {
    const user = userEvent.setup({ delay: null });
    const view = render(
      <Shell meta={meta.meta}>
        <SearchApp meta={meta.data} areas={areas} bands={bands} client={api.client} button={button} />
      </Shell>,
    );
    await arrived();
    await way(user, "deep");
    return { user, api, ...view };
  }

  test("test_one_line_of_the_look_chooses_and_it_is_held_at_the_foot_of_the_window", () => {
    expect(BUTTON_STANDS).toEqual(["held", "both", "foot"]);
    expect(THE_BUTTON_OF_DEEP_SEARCH).toBe("held");
  });

  test("test_it_is_one_button_that_is_held_at_the_foot_of_the_window_and_rests_under_the_space_requirements", async () => {
    // Measured with the way chosen and nothing scrolled: it stood 2,213 px down a window of
    // 900, and 2,641 px down a phone's of 844, under ten groups.
    const { user } = await openSearch();
    await way(user, "deep");

    expect(theButtons()).toHaveLength(1);
    const [button] = theButtons();
    const bar = button?.parentElement as HTMLElement;
    // It comes after the space requirements in the page, where it rests once the page is scrolled to it.
    expect(follows(theSettings(), bar)).toBe(true);
    const held = PAGE.filter((rule) => rule.under === null && rule.selector === ".held");
    expect(held.map((rule) => [rule.sets.get("position"), rule.sets.get("inset-block-end")])).toEqual([["sticky", "0"]]);
    // It is read on cream within an edge of ink, over whatever stands under it.
    expect(held.map((rule) => [rule.sets.get("background"), rule.sets.get("border")])).toEqual([
      ["var(--page)", "var(--edge) solid var(--border)"],
    ]);
    // Nothing of it moves or changes size under a press, the pointer or the focus.
    expect(PAGE.filter((rule) => /\.held\b.*:(hover|focus|active)/.test(rule.selector))).toEqual([]);
  });

  test("test_held_it_clears_the_bar_of_areas_to_compare_which_is_held_at_the_foot_of_the_window_too", () => {
    const beside = PAGE.filter((rule) => rule.under === null && /:has\(\.tray > \[data-closed="false"\]\) \.held$/.test(rule.selector));

    expect(beside.map((rule) => rule.sets.get("inset-block-end"))).toEqual(["calc(2 * var(--space-8) + var(--space-7))"]);
  });

  test("test_what_burro_says_stands_in_the_bar_over_the_button_and_takes_no_room_until_it_says_something", async () => {
    const { user } = await openSearch();
    await way(user, "deep");
    const line = screen.getAllByRole("status").find((one) => one.getAttribute("aria-live") === "polite") as HTMLElement;
    const [button] = theButtons();

    // It is on the page before it says anything, so that it is heard when it first speaks.
    expect(button?.parentElement).toContainElement(line);
    expect(follows(line, button as HTMLElement)).toBe(true);
    expect(line).toBeEmptyDOMElement();
  });

  test("test_pressed_it_makes_the_search_and_the_answer_is_brought_into_sight", async () => {
    const { user, api } = await standing("held");

    await user.click(theButtons()[0] as HTMLElement);
    await settled();

    expect(api.lastCallTo("rank").body).toMatchObject({ limit: 20 });
    expect(results().length).toBeGreaterThan(0);
    expect(whatRefines()).toHaveFocus();
  });

  test("test_where_the_ranking_does_not_come_the_button_is_where_it_was_with_the_focus_and_what_is_said_over_it", async () => {
    const { user } = await standing("held", standInApi().on("rank", "error-internal"));

    await user.click(theButtons()[0] as HTMLElement);
    await settled();

    const [button] = theButtons();
    expect(button).toHaveFocus();
    expect(button?.parentElement).toContainElement(screen.getByRole("alert"));
    expect(screen.queryAllByRole("tab")).toHaveLength(2);
  });

  test("test_the_second_way_it_was_built_stands_one_at_the_head_of_the_way_and_one_at_its_foot", async () => {
    const { user, api } = await standing("both");

    expect(theButtons()).toHaveLength(2);
    const [head, foot] = theButtons() as [HTMLElement, HTMLElement];
    // The first stands under what the way says of itself, which names it, and over the space requirements.
    expect(head.parentElement).toContainElement(screen.getByText(DEEP.lead));
    expect(follows(head, theSettings())).toBe(true);
    expect(follows(theSettings(), foot)).toBe(true);
    // What Burro says stands at the head of the way, as it did.
    const line = screen.getAllByRole("status").find((one) => one.getAttribute("aria-live") === "polite") as HTMLElement;
    expect(panelOf("deep").firstElementChild).toContainElement(line);

    await user.click(head);
    await settled();

    expect(api.lastCallTo("rank").body).toMatchObject({ limit: 20 });
    expect(results().length).toBeGreaterThan(0);
  });

  test("test_the_third_leaves_it_at_the_foot_alone_as_it_stood", async () => {
    await standing("foot");

    expect(theButtons()).toHaveLength(1);
    const [button] = theButtons();
    expect(follows(theSettings(), button as HTMLElement)).toBe(true);
    expect(button?.parentElement).toBe(panelOf("deep"));
    const line = screen.getAllByRole("status").find((one) => one.getAttribute("aria-live") === "polite") as HTMLElement;
    expect(panelOf("deep").firstElementChild).toContainElement(line);
  });

  test("test_the_page_has_no_accessibility_fault_whichever_way_it_stands", async () => {
    for (const button of BUTTON_STANDS) {
      const { container, unmount } = await standing(button);
      expect([button, await faultsIn(container, { wholePage: true })]).toEqual([button, []]);
      unmount();
    }
  });
});

describe("in the second way in, nothing is ranked until its button is pressed", () => {
  /** The journey to the place that the recorded answer names, as the settings draw it. */
  const PLACE_NAME = "Cindermoor Works";
  const firm = () => screen.getByRole("checkbox", { name: BUDGET.firm });
  const theButton = () => screen.getByRole("button", { name: SETTINGS.rank });
  /** Hears how far the page is asked to scroll, and what it is asked to bring into sight. */
  function moved() {
    const asked: unknown[] = [];
    const scroll = jest.spyOn(window, "scrollBy").mockImplementation(((x: number, y: number) => {
      asked.push([x, y]);
    }) as typeof window.scrollBy);
    Object.defineProperty(Element.prototype, "scrollIntoView", {
      configurable: true,
      writable: true,
      value(this: Element) {
        asked.push(this);
      },
    });
    return { asked, putBack: () => scroll.mockRestore() };
  }

  test("test_one_line_of_the_look_chooses_and_the_button_is_what_it_chooses", () => {
    expect(RANKS).toEqual(["button", "setting"]);
    expect(DEEP_SEARCH_RANKS_BY).toBe("button");
  });

  test("test_a_setting_that_is_moved_is_kept_and_the_page_is_as_it_was", async () => {
    // Seen in a browser by three people: the first setting that was moved made the search by
    // itself. The tabs went, the page became a page of results, and the button the tab ends
    // with was gone when a person reached for it.
    const { asked, putBack } = moved();
    try {
      const { user, api } = await openSearch(standInApi().on("rank", "rank-refined"));
      await way(user, "deep");
      const [heading, settings, setting] = [screen.getByRole("heading", { level: 1 }), theSettings(), firm()];
      api.calls.length = 0;

      await user.click(firm());
      await settled();

      // It was sent to be applied, with the fewest results asked for, and nothing else was asked.
      expect(api.calls.map((call) => call.operation)).toEqual(["rank"]);
      expect(api.lastCallTo("rank").body).toMatchObject({ spec: meta.data.defaults.rent, limit: 1 });
      // No search is open: the heading and both tabs are there, the second chosen, and its button.
      expect(screen.getByRole("heading", { level: 1 })).toBe(heading);
      expect(heading).toBeVisible();
      expect(tabOf("deep")).toHaveAttribute("aria-selected", "true");
      expect(theButton()).toBeVisible();
      expect(whatRefines()).toBeNull();
      expect(screen.queryAllByRole("article")).toEqual([]);
      expect(screen.queryByRole("region", { name: new RegExp(`^(${CHIPS.label}|${CHIPS.setLabel})$`) })).toBeNull();
      expect(document.querySelector("[data-wait]")).toBeNull();
      expect(document.querySelector("main > [data-dressed]")).toHaveAttribute("data-search", "closed");
      // The settings are the settings they were, with what was moved in hand, and nothing moved.
      expect(theSettings()).toBe(settings);
      expect(firm()).toBe(setting);
      expect(firm()).toHaveFocus();
      expect(asked).toEqual([]);
    } finally {
      putBack();
    }
  });

  test("test_one_press_of_an_arrow_key_on_a_slider_makes_no_search", async () => {
    // Seen by keyboard: ArrowRight on "How much the budget counts" took both tabs and the
    // button off the page, and ranked 21 areas.
    const { user, api } = await openSearch(standInApi().on("rank", "rank-refined"));
    await way(user, "deep");
    api.calls.length = 0;
    const slider = within(theSettings()).getAllByRole("slider")[0] as HTMLElement;
    expect(slider).toHaveAccessibleName(BUDGET.weight);

    // A browser moves a slider by one step for the key, and says that it changed: jsdom moves none.
    act(() => slider.focus());
    fireEvent.keyDown(slider, { key: "ArrowRight" });
    fireEvent.change(slider, { target: { value: String(Number((slider as HTMLInputElement).value) + 5) } });
    fireEvent.keyUp(slider, { key: "ArrowRight" });
    // A slider sends what it was moved to a moment after the last key.
    await waitFor(() => expect(api.callsTo("rank")).toHaveLength(1));
    await settled();

    expect(api.callsTo("rank").map((call) => (call.body as { limit: number }).limit)).toEqual([1]);
    expect(api.callsTo("explain_top")).toEqual([]);
    expect(ways()).toBeInTheDocument();
    expect(theButton()).toBeInTheDocument();
    expect(screen.queryAllByRole("article")).toEqual([]);
    expect(within(theSettings()).getAllByRole("slider")[0]).toHaveFocus();
  });

  test("test_a_place_that_is_chosen_is_drawn_as_a_journey_by_its_name_and_makes_no_search", async () => {
    // Seen in a browser: "Pel" was typed, a place was pressed, and the page became a page of
    // results with the settings folded away. The place is named by the answer, as it always
    // is, and its journey stands in its group with every setting of it, to be set before a search.
    // The stand-in answers with the search it recorded, which names the place of its own journey.
    const { user, api } = await openSearch(standInApi().on("rank", "rank-first").on("search_places", "places-search"));
    await way(user, "deep");
    api.calls.length = 0;
    const field = within(theSettings()).getByRole("combobox", { name: PLACE.label });

    await user.type(field, "pel");
    const places = () => document.getElementById(field.getAttribute("aria-controls") ?? "") as HTMLElement;
    await user.click((await within(places()).findAllByRole("option"))[0] as HTMLElement);
    await settled();

    expect(api.callsTo("rank")).toHaveLength(1);
    expect(api.lastCallTo("rank").body).toMatchObject({ limit: 1 });
    expect(within(theSettings()).getByRole("group", { name: JOURNEY.place(PLACE_NAME) })).toBeVisible();
    expect(within(theSettings()).queryByText(JOURNEY.none)).toBeNull();
    // The bar of its group says what it holds, as it does once a search is open.
    expect(within(theSettings()).getByRole("button", { name: SETTINGS.journeys })).toHaveAccessibleDescription(
      new RegExp(`^${PLACE_NAME}`),
    );
    expect(ways()).toBeInTheDocument();
    expect(theButton()).toBeInTheDocument();
    expect(screen.queryAllByRole("article")).toEqual([]);
  });

  test("test_the_settings_are_drawn_as_before_a_search_while_what_is_chosen_is_kept", async () => {
    // A couple of groups stand open, to show that a group folds, and what a person opened
    // and closed stays as they left it: nothing opens or closes under a hand for an answer.
    const { user } = await openSearch(standInApi().on("rank", "rank-refined"));
    await way(user, "deep");
    await user.click(within(theSettings()).getByRole("button", { name: CLOSED_AT_FIRST }));
    expect(standOpen()).toEqual([...OPEN_AT_FIRST, CLOSED_AT_FIRST]);

    await user.click(firm());
    await settled();

    expect(standOpen()).toEqual([...OPEN_AT_FIRST, CLOSED_AT_FIRST]);
    // No button of the settings ranks by them there: the button of the way is the one.
    expect(within(theSettings()).queryByRole("button", { name: SETTINGS.rank })).toBeNull();
    expect(screen.getAllByRole("button", { name: SETTINGS.rank })).toHaveLength(1);
  });

  test("test_the_button_makes_the_search_of_what_was_chosen", async () => {
    const { asked, putBack } = moved();
    try {
      const { user, api } = await openSearch(standInApi().on("rank", "rank-first").on("explain_top", "explanations-first"));
      await way(user, "deep");
      await user.click(firm());
      await settled();
      api.calls.length = 0;
      asked.length = 0;

      await user.click(theButton());
      await settled();

      // The search is ranked as it stands, with nothing more to apply, and its reasons are asked for.
      const sent = api.lastCallTo("rank").body as { spec: unknown; limit: number; operations?: unknown };
      expect(sent.limit).toBe(20);
      expect(sent.operations).toBeUndefined();
      expect(sent.spec).toEqual(recordedSpec("rank-first"));
      expect(api.callsTo("explain_top")).toHaveLength(1);
      expect(results().length).toBeGreaterThan(0);
      expect(waysIfAny()).toBeNull();
      expect(chips()).toBeInTheDocument();
      // The button went as it was pressed. The focus is on what opens the settings, which
      // are closed over the answer, and the box is brought into sight with the answer under it.
      expect(whatRefines()).toHaveFocus();
      expect(whatRefines()).toHaveAttribute("aria-expanded", "false");
      expect(asked.filter((part) => part === screen.getByRole("region", { name: SEARCH.formLabel }))).toHaveLength(1);
    } finally {
      putBack();
    }
  });

  test("test_once_the_search_is_open_a_setting_that_is_moved_is_ranked_at_once", async () => {
    const { user, api } = await openSearch(standInApi().on("rank", "rank-first").on("explain_top", "explanations-first"));
    await way(user, "deep");
    await user.click(firm());
    await settled();
    await user.click(theButton());
    await settled();
    api.calls.length = 0;
    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");
    await settingsAt(user, SETTINGS.money);

    await user.click(firm());
    await settled();

    expect(api.callsTo("rank").map((call) => (call.body as { limit: number }).limit)).toEqual([20]);
    expect(api.callsTo("explain_top")).toHaveLength(1);
    expect(whatRefines()).toHaveAttribute("aria-expanded", "true");
    expect(firm()).toHaveFocus();
  });

  test("test_a_sentence_sent_from_the_first_way_makes_a_search_of_what_was_chosen_and_what_it_says", async () => {
    const api = firstSearch();
    const { user } = await openSearch(api);
    api.on("rank", "rank-refined");
    await way(user, "deep");
    await user.click(firm());
    await settled();
    api.on("rank", "rank-first");

    await way(user, "quick");
    await search(user);

    expect(api.lastCallTo("interpret").body).toMatchObject({ spec: recordedSpec("rank-refined") });
    expect(results().length).toBeGreaterThan(0);
    expect(waysIfAny()).toBeNull();
  });

  test("test_start_again_is_not_offered_there_and_changing_tab_keeps_what_was_chosen", async () => {
    const { user, api } = await openSearch(standInApi().on("rank", "rank-refined"));
    await way(user, "deep");
    await user.click(firm());
    await settled();
    const setting = firm();
    api.calls.length = 0;

    await way(user, "quick");
    // The first way is as it is before a search: nothing says that a search is open.
    expect(screen.queryByRole("button", { name: PROMPT.startAgain })).toBeNull();
    expect(promptBox()).toHaveAccessibleName(PROMPT.label);
    expect(helpers()).toBeInTheDocument();
    await way(user, "deep");

    expect(firm()).toBe(setting);
    expect(api.calls).toEqual([]);
  });

  test("test_what_could_not_be_sent_is_said_over_the_button_that_is_held_in_sight_and_trying_again_makes_no_search", async () => {
    const { user, api } = await openSearch(standInApi().on("rank", "error-internal"));
    await way(user, "deep");

    await user.click(firm());
    await settled();

    expect(panelOf("deep")).toContainElement(screen.getByRole("alert"));
    // It stands with the button, which is held at the foot of the window: a person who is
    // far down the groups sees it, where it stood at the head of the way, far over them.
    expect(theButton().parentElement).toContainElement(screen.getByRole("alert"));
    expect(follows(screen.getByRole("alert"), theButton())).toBe(true);
    expect(follows(theSettings(), screen.getByRole("alert"))).toBe(true);
    expect(ways()).toBeInTheDocument();
    expect(theButton()).toBeInTheDocument();

    api.on("rank", "rank-refined");
    await user.click(screen.getByRole("button", { name: PROMPT.tryAgain }));
    await settled();

    expect(screen.queryByRole("alert")).toBeNull();
    expect(api.lastCallTo("rank").body).toMatchObject({ limit: 1 });
    expect(ways()).toBeInTheDocument();
    expect(screen.queryAllByRole("article")).toEqual([]);
    // What was pressed went with the failure: the tab of the way has the focus.
    expect(tabOf("deep")).toHaveFocus();
  });

  test("test_the_page_has_no_accessibility_fault_with_something_chosen", async () => {
    const { user, container } = await openSearch(standInApi().on("rank", "rank-first"));
    await way(user, "deep");
    await user.click(firm());
    await settled();

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });

  test("test_nothing_that_was_chosen_is_kept_in_the_address_or_in_the_storage_of_the_browser", async () => {
    const seen = watch();
    try {
      const { user } = await openSearch(standInApi().on("rank", "rank-first"));
      const address = window.location.href;
      await way(user, "deep");

      await user.click(firm());
      await settled();

      expect(seen.storage).toEqual([]);
      expect(seen.history).toEqual([]);
      expect(window.location.href).toBe(address);
      // It travels in the body of a request, as every search does, and in no address.
      expect(seen.addresses()).not.toMatch(/syn-p|strict|hard|budget/i);
    } finally {
      seen.stop();
    }
  });
});

describe("a setting, where the look has a search open of it in the second way in", () => {
  /**
   * Stands every control of the settings at one place in the page before a search and at
   * another once one is open, as a browser does when the heading and the tabs over them go
   * and the answer is drawn over them. It
   * hears how far the page is asked to scroll, and stands everything in the window by as
   * much less, as a browser that scrolls does. jsdom lays nothing out, and scrolls nothing.
   */
  function standing(at: { readonly before: number; readonly open: number }) {
    const asked: (readonly [number, number])[] = [];
    let scrolled = 0;
    const measure = jest.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function (
      this: HTMLElement,
    ) {
      const open = this.closest("[data-search]")?.getAttribute("data-search") === "open";
      const top = (open ? at.open : at.before) - scrolled;
      return { top, bottom: top + 44, left: 0, right: 0, x: 0, y: top, width: 0, height: 44, toJSON: () => ({}) };
    });
    const scroll = jest.spyOn(window, "scrollBy").mockImplementation(((x: number, y: number) => {
      asked.push([x, y]);
      scrolled += y;
    }) as typeof window.scrollBy);
    return {
      asked,
      /** The person scrolls the page themselves, by so much. */
      byHand: (y: number) => {
        scrolled += y;
        fireEvent.scroll(window);
      },
      putBack: () => {
        measure.mockRestore();
        scroll.mockRestore();
      },
    };
  }
  /** Hears what the page asks a browser to bring into sight. jsdom lays nothing out, and has no such call. */
  function broughtIntoSight() {
    const asked: Element[] = [];
    Object.defineProperty(Element.prototype, "scrollIntoView", {
      configurable: true,
      writable: true,
      value(this: Element) {
        asked.push(this);
      },
    });
    return asked;
  }
  /**
   * Opens the page where a setting makes the search, which one line of the look chooses,
   * with what becomes of the page as a search opens of it said, where a test says it.
   */
  async function opened(opens?: Opens, ranks: Ranks = "setting") {
    const api = firstSearch();
    const user = userEvent.setup({ delay: null });
    const view = render(
      <Shell meta={meta.meta}>
        <SearchApp meta={meta.data} areas={areas} bands={bands} client={api.client} opens={opens} ranks={ranks} />
      </Shell>,
    );
    await arrived();
    return { api, user, ...view };
  }
  // The journeys stand open as well, and hold a firm limit of their own once a place is named.
  const firm = () => screen.getByRole("checkbox", { name: BUDGET.firm });
  const theForm = () => screen.getByRole("region", { name: SEARCH.formLabel });

  test("test_it_stays_where_it_stood_in_the_window_so_that_a_press_lands_where_it_was_aimed", async () => {
    // Seen on a phone 390 wide: the plus of a slider was pressed at 501 of 844. As the search
    // opened what stood over the settings went and the answer was drawn over them, and the
    // plus stood at 23, with the way to another group of settings where it had been.
    const { asked, putBack } = standing({ before: 501, open: 23 });
    const sight = broughtIntoSight();
    try {
      const { user } = await opened();
      await settingsAt(user, SETTINGS.money);
      await user.click(screen.getAllByRole("radio", { name: TENURE_CHOICE.buy })[0] as HTMLElement);
      expect(asked).toEqual([]);
      const [settings, setting] = [theSettings(), firm()];

      await user.click(firm());
      await settled();

      // The page goes by as much as the setting went, once: when the answer is in it stands
      // where it stood, and nothing more is asked.
      expect(results().length).toBeGreaterThan(0);
      expect(asked).toEqual([[0, -478]]);
      expect(firm()).toHaveFocus();
      // The person is at the setting: the box is not brought into sight from under them.
      expect(sight.filter((part) => part === theForm())).toEqual([]);
      // The settings are the settings they were, with what was moved in hand: they are now
      // the part that refines the search, and it is open.
      expect(theSettings()).toBe(settings);
      expect(firm()).toBe(setting);
      expect(waysIfAny()).toBeNull();
      expect(whatRefines()).toHaveAttribute("aria-expanded", "true");
      expect(within(settings).getByRole("button", { name: SETTINGS.money })).toHaveAttribute("aria-expanded", "true");
    } finally {
      putBack();
    }
  });

  test("test_it_stays_where_it_stood_when_it_is_moved_by_keyboard_alone", async () => {
    const { asked, putBack } = standing({ before: 501, open: 23 });
    try {
      const { user } = await opened();
      await settingsAt(user, SETTINGS.money);

      firm().focus();
      await user.keyboard(" ");
      await settled();

      expect(results().length).toBeGreaterThan(0);
      expect(asked).toEqual([[0, -478]]);
      expect(firm()).toHaveFocus();
    } finally {
      putBack();
    }
  });

  test("test_the_page_goes_where_a_person_takes_it_while_the_ranking_is_on_its_way", async () => {
    // The ranking may be slow. A person who scrolls up to look for it meanwhile is not
    // brought back to the setting when it comes: the setting is held where they left it.
    const { asked, byHand, putBack } = standing({ before: 501, open: 23 });
    try {
      const api = firstSearch();
      const ranking = api.hold("rank", "rank-first");
      const user = userEvent.setup({ delay: null });
      render(
        <Shell meta={meta.meta}>
          <SearchApp meta={meta.data} areas={areas} bands={bands} client={api.client} ranks="setting" />
        </Shell>,
      );
      await arrived();
      await settingsAt(user, SETTINGS.money);
      await user.click(firm());
      expect(ranking.waiting()).toBe(1);
      expect(asked).toEqual([[0, -478]]);

      byHand(-300);
      ranking.release();
      await settled();

      expect(results().length).toBeGreaterThan(0);
      expect(asked).toEqual([[0, -478]]);
    } finally {
      putBack();
    }
  });

  test("test_a_setting_moved_with_a_search_open_is_the_browsers_to_hold_and_the_page_asks_nothing", async () => {
    // Measured in a browser at 390 and at 1100 wide: with a search open a setting that is
    // moved stays where it stood, to the pixel, as the ranking is worked out again.
    const { asked, putBack } = standing({ before: 501, open: 23 });
    try {
      const { user, api } = await opened();
      await search(user);
      api.on("rank", "rank-refined").on("explain_top", "explanations-refined");
      await settingsAt(user, SETTINGS.money);
      asked.length = 0;

      await user.click(firm());
      await settled();

      expect(asked).toEqual([]);
    } finally {
      putBack();
    }
  });

  test("test_a_ranking_that_does_not_come_leaves_the_setting_where_it_stood_too", async () => {
    const { asked, putBack } = standing({ before: 501, open: 23 });
    try {
      const { user, api } = await opened();
      api.on("rank", "error-internal");
      await settingsAt(user, SETTINGS.money);
      const setting = firm();

      await user.click(firm());
      await settled();

      // The settings are as they were, with what was pressed in hand.
      expect(firm()).toBe(setting);
      expect(firm()).toHaveFocus();
      expect(whatRefines()).toBeNull();

      // The search opened of the press and closed as the ranking failed: the page went with
      // the setting, and came back with it. The second way in is chosen, as it was.
      expect(screen.queryAllByRole("article")).toEqual([]);
      expect(asked).toEqual([
        [0, -478],
        [0, 478],
      ]);
      expect(tabOf("deep")).toHaveAttribute("aria-selected", "true");
      expect(firm()).toBeVisible();
    } finally {
      putBack();
    }
  });

  test("test_the_answer_may_be_brought_into_sight_instead_which_one_line_chooses", async () => {
    // Two promises meet where a search opens of a setting, and both cannot be kept:
    // that a press lands where it was aimed, and that the first result is in sight once a
    // ranking follows a press. The other way brings the box into sight with the answer
    // under it, as a word of the shelf does, and the setting keeps the focus.
    const { asked, putBack } = standing({ before: 501, open: 23 });
    const sight = broughtIntoSight();
    try {
      expect(OPENS).toEqual(["held", "answer"]);
      const { user } = await opened("answer");
      await settingsAt(user, SETTINGS.money);

      await user.click(firm());
      await settled();

      expect(results().length).toBeGreaterThan(0);
      expect(asked).toEqual([]);
      expect(sight.filter((part) => part === theForm())).toEqual([theForm()]);
      expect(firm()).toHaveFocus();
    } finally {
      putBack();
    }
  });

  test("test_with_the_answer_brought_into_sight_a_second_press_of_a_double_press_lands_on_nothing", async () => {
    // What was pressed has gone from under the pointer, and something of the answer stands
    // there. A press the browser counts as the second of a double press was aimed at the
    // setting, and lands on nothing. A press of its own lands.
    broughtIntoSight();
    const { user, api } = await opened("answer");
    await settingsAt(user, SETTINGS.money);
    await user.click(firm());
    await settled();
    const remove = screen.getAllByRole("button", { name: /^Remove: / })[0] as HTMLElement;
    const ranked = api.callsTo("rank").length;
    /**
     * A press that follows at once, whatever the machine of the test is busy with: the
     * clock of the page stands, for the press alone, at the moment the page was moved.
     * Seen with seven runs side by side: half a second had gone by before the press was made.
     */
    const atOnce = (detail: number) => {
      const clock = jest.spyOn(performance, "now").mockReturnValue(0);
      try {
        fireEvent.click(remove, { detail });
      } finally {
        clock.mockRestore();
      }
    };

    atOnce(2);
    await settled();
    expect(api.callsTo("rank")).toHaveLength(ranked);
    atOnce(3);
    await settled();
    expect(api.callsTo("rank")).toHaveLength(ranked);

    fireEvent.click(remove, { detail: 1 });
    await settled();
    expect(api.callsTo("rank")).toHaveLength(ranked + 1);
  });

  test("test_with_the_setting_held_a_press_that_follows_lands_as_it_did", async () => {
    // Nothing went from under the pointer, so nothing is kept from a press that follows at once.
    const { user, api } = await opened();
    await settingsAt(user, SETTINGS.money);
    await user.click(firm());
    await settled();
    const ranked = api.callsTo("rank").length;

    fireEvent.click(firm(), { detail: 2 });
    await settled();

    expect(api.callsTo("rank")).toHaveLength(ranked + 1);
  });
});

describe("the answer, when a search opens of what stood under the box", () => {
  /** Hears what the page asks a browser to bring into sight. jsdom lays nothing out, and has no such call. */
  function broughtIntoSight() {
    const asked: { readonly part: Element; readonly how: unknown }[] = [];
    Object.defineProperty(Element.prototype, "scrollIntoView", {
      configurable: true,
      writable: true,
      value(this: Element, how: unknown) {
        asked.push({ part: this, how });
      },
    });
    return asked;
  }
  const theForm = () => screen.getByRole("region", { name: SEARCH.formLabel });

  test("test_a_word_added_from_the_shelf_brings_the_box_into_sight_with_the_answer_under_it", async () => {
    // Seen in a browser: a browser brings what takes the focus clear of the foot of the
    // screen, so pressing "Add to my search" scrolled the page down by 410 px of 900. The
    // shelf then went, and the first result stood 103 px over the top of the screen.
    const asked = broughtIntoSight();
    const { user } = await openSearch(firstSearch().on("rank", "rank-shelf").on("explain_top", "explanations-shelf"));
    await helper(user, "word");
    await user.click(within(screen.getByRole("region", { name: SHELF.title })).getByRole("button", { name: "lively" }));
    expect(asked.filter(({ part }) => part === theForm())).toEqual([]);

    await user.click(screen.getByRole("button", { name: SHELF.add }));
    await settled();

    // Only as far as it must: a box that is in sight is left where it is.
    expect(asked.filter(({ part }) => part === theForm())).toEqual([{ part: theForm(), how: { block: "nearest" } }]);
    expect(theForm()).toContainElement(document.activeElement as HTMLElement);
  });

  test("test_the_settings_ranked_as_they_stand_bring_the_box_into_sight_and_close_over_the_answer", async () => {
    const asked = broughtIntoSight();
    const { user } = await openSearch(standInApi().on("rank", "rank-default-rent").on("explain_top", "explanations-first"));
    await settingsAt(user);

    await user.click(screen.getByRole("button", { name: SETTINGS.rank }));
    await settled();

    expect(asked.filter(({ part }) => part === theForm()).map(({ how }) => how)).toEqual([{ block: "nearest" }]);
    // The button went as it was pressed. The focus is on what opens the settings, which
    // are closed: the person asked for the ranking, and the answer comes first.
    expect(results().length).toBeGreaterThan(0);
    expect(whatRefines()).toHaveFocus();
    expect(whatRefines()).toHaveAttribute("aria-expanded", "false");
    expect(theSettingsIfAny()).toBeNull();
  });

  test("test_the_settings_ranked_where_nothing_was_read_bring_the_first_result_into_sight", async () => {
    // Seen in a browser at 1440 by 900, while Burro still asked: the settings might be
    // ranked as they stood, and a press on the button that did drew the first result 1,882
    // px down the page, out of sight. The search was open already, so no search opened of
    // the press, and nothing was brought into sight. Burro asks nothing now. A search
    // stands open with nothing ranked where nothing was read, and the settings stand open
    // under it: where the results stand is brought into sight as the press lands, so that
    // Burro is seen to hop there, and the first result once it is in.
    const asked = broughtIntoSight();
    const unread = recordedAnswer("interpret", "interpret-nothing-read");
    const { user } = await openSearch(
      firstSearch()
        .on("interpret", "interpret-nothing-read")
        .on("rank", "rank-default-rent")
        .on("explain_top", reasonsFor("rank-default-rent", "explanations-first")),
    );
    await search(user, (unread.request.body as { text: string }).text);
    expect(screen.queryAllByRole("article")).toEqual([]);
    await settingsAt(user);
    asked.length = 0;

    await user.click(within(theSettings()).getByRole("button", { name: SETTINGS.rank }));
    await settled();

    const first = results()[0] as HTMLElement;
    const brought = asked.filter(({ part }) => part.contains(first));
    // Only as far as it must: what is in sight is left where it is. Where the results stand
    // is brought first, for the wait, and then the first result, which stands there.
    expect(brought.map(({ how }) => how)).toEqual([{ block: "nearest" }, { block: "nearest" }]);
    expect(brought.map(({ part }) => part.id)).toEqual(["results", ""]);
    // It is the first result that is brought, and not the box.
    expect(brought.map(({ part }) => part.closest("section")?.id)).toEqual(["results", "results"]);
    expect(asked.filter(({ part }) => part === theForm())).toEqual([]);
    // The button went as it was pressed. The focus is on what opens the settings, which
    // stand open where they stood.
    expect(whatRefines()).toHaveFocus();
    expect(whatRefines()).toHaveAttribute("aria-expanded", "true");
  });

  test("test_a_sentence_that_is_typed_moves_nothing_for_the_box_is_where_the_person_is", async () => {
    const asked = broughtIntoSight();
    const { user } = await openSearch();
    await helper(user, "example");

    await search(user);

    expect(asked.filter(({ part }) => part === theForm())).toEqual([]);
  });

  test("test_a_setting_moved_before_a_search_moves_nothing_for_the_person_is_at_the_setting", async () => {
    const asked = broughtIntoSight();
    const { user } = await openSearch();
    await settingsAt(user, SETTINGS.money);

    await user.click(screen.getAllByRole("radio", { name: TENURE_CHOICE.buy })[0] as HTMLElement);
    await user.click(screen.getByRole("checkbox", { name: BUDGET.firm }));
    await settled();

    expect(asked.filter(({ part }) => part === theForm())).toEqual([]);
  });

  test("test_a_press_that_ranked_the_settings_of_an_open_search_moves_nothing_for_the_sentence_typed_after_it", async () => {
    // Seen in a browser: words were sent of which nothing was read, and the settings were
    // ranked as they stood. The search was open already, so no search opened of that press,
    // and the page kept it. It moved the page for it when the next search opened: for a
    // sentence that was typed, in the box, where the person was.
    const asked = broughtIntoSight();
    const { user, api } = await openSearch(
      firstSearch()
        .on("interpret", "interpret-nothing-read")
        .on("rank", "rank-default-rent")
        .on("explain_top", reasonsFor("rank-default-rent", "explanations-first")),
    );
    await search(user, "What is the best way to learn the piano");
    await settingsAt(user);
    await user.click(screen.getByRole("button", { name: SETTINGS.rank }));
    await settled();
    expect(results().length).toBeGreaterThan(0);
    // The focus is with what opens the settings.
    expect(whatRefines()).toHaveFocus();

    await user.click(screen.getByRole("button", { name: PROMPT.startAgain }));
    api.on("interpret", "interpret-first").on("rank", "rank-first").on("explain_top", "explanations-first");
    await search(user);

    expect(results().length).toBeGreaterThan(0);
    expect(asked.filter(({ part }) => part === theForm()).map(({ how }) => how)).toEqual([]);
  });

  test("test_a_press_that_ranked_nothing_moves_nothing_for_the_setting_moved_after_it", async () => {
    // The settings are ranked as they stand, and Burro cannot be reached: no search is left
    // open by the press. A setting is then moved, by pointer alone, where the look has a
    // search open of it. The person is at the setting, and the page is not moved for the
    // press made before it.
    const asked = broughtIntoSight();
    const api = firstSearch().on("rank", "error-internal");
    const user = userEvent.setup({ delay: null });
    render(
      <Shell meta={meta.meta}>
        <SearchApp meta={meta.data} areas={areas} bands={bands} client={api.client} ranks="setting" />
      </Shell>,
    );
    await arrived();
    await settingsAt(user, SETTINGS.money);
    await user.click(screen.getByRole("button", { name: SETTINGS.rank }));
    await settled();
    expect(screen.queryAllByRole("article")).toEqual([]);
    // The press itself brought the box into sight, once: a person waits there for a first
    // answer. The failure is said in the way they are in, over the button they pressed,
    // which is drawn again where it stood and has the focus: what opens the settings had
    // it while the search was open.
    expect(asked.filter(({ part }) => part === theForm()).map(({ how }) => how)).toEqual([{ block: "nearest" }]);
    expect(panelOf("deep")).toContainElement(screen.getByRole("alert"));
    expect(screen.getByRole("alert")).toBeVisible();
    expect(screen.getByRole("button", { name: SETTINGS.rank })).toHaveFocus();
    asked.length = 0;

    api.on("rank", "rank-first");
    await settingsAt(user, SETTINGS.money);
    await user.click(screen.getByRole("radio", { name: TENURE_CHOICE.buy }));
    await user.click(screen.getByRole("checkbox", { name: BUDGET.firm }));
    await settled();

    expect(results().length).toBeGreaterThan(0);
    expect(asked.filter(({ part }) => part === theForm()).map(({ how }) => how)).toEqual([]);
  });

  test("test_a_press_that_ranked_nothing_moves_nothing_for_the_sentence_sent_by_keyboard_after_it", async () => {
    // The same, and the sentence is typed and sent with no pointer at all.
    const asked = broughtIntoSight();
    const { user, api } = await openSearch(firstSearch().on("rank", "error-internal"));
    await settingsAt(user);
    await user.click(screen.getByRole("button", { name: SETTINGS.rank }));
    await settled();
    expect(screen.queryAllByRole("article")).toEqual([]);
    expect(asked.filter(({ part }) => part === theForm()).map(({ how }) => how)).toEqual([{ block: "nearest" }]);
    asked.length = 0;

    api.on("rank", "rank-first");
    // The button that was pressed has the focus. The box is in the first way in, which
    // the keyboard chooses from the tab of the way, once the keys have been taken to it.
    expect(screen.getByRole("button", { name: SETTINGS.rank })).toHaveFocus();
    act(() => tabOf("deep").focus());
    await user.keyboard("{ArrowLeft}");
    act(() => promptBox().focus());
    await user.keyboard("leafy and quiet{Enter}");
    await settled();

    expect(results().length).toBeGreaterThan(0);
    expect(asked.filter(({ part }) => part === theForm()).map(({ how }) => how)).toEqual([]);
  });
});

describe("once a search is open, the two ways in have become one search", () => {
  test("test_the_tabs_go_and_the_box_stands_at_the_head_with_the_settings_folded_under_what_was_understood", async () => {
    const { user } = await openSearch();
    const box = promptBox();

    await search(user);

    expect(waysIfAny()).toBeNull();
    expect(screen.queryAllByRole("tab")).toEqual([]);
    expect(screen.queryAllByRole("tabpanel")).toEqual([]);
    expect(screen.queryByRole("group", { name: HELPERS.label })).toBeNull();
    // The box is the box it was, with what was typed in it, and adds to the search.
    expect(promptBox()).toBe(box);
    expect(box).toHaveValue("leafy and quiet");
    expect(box).toHaveAccessibleName(PROMPT.labelOpen);
    // The settings are one part of that name, which stands after what Burro understood
    // and before the results, in the page.
    const refines = whatRefines() as HTMLElement;
    expect(refines).toHaveTextContent(new RegExp(`^${REFINE.label}$`));
    expect(REFINE.label).toBe("Refine search");
    expect(follows(chips(), refines)).toBe(true);
    expect(follows(refines, results()[0] as HTMLElement)).toBe(true);
    // Nothing else that can be pressed stands between what was understood and the first result.
    const between = [...document.querySelectorAll<HTMLElement>("main button, main a, main input")].filter(
      (control) => !chips().contains(control) && follows(chips(), control) && follows(control, results()[0] as HTMLElement),
    );
    expect(between).toEqual([refines]);
  });

  test("test_what_refines_a_search_is_offered_once_there_is_something_to_refine_and_not_while_a_first_sentence_is_read", async () => {
    // Seen in a browser: while a first sentence was read "Refine search" stood between the
    // box and Burro, though there was nothing to refine, and when the answer came it went
    // from 378 to 740 as the chips came in over it.
    const api = firstSearch();
    const reading = api.hold("interpret", "interpret-first");
    const { user } = await openSearch(api);
    await user.type(promptBox(), "leafy and quiet");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));

    expect(reading.waiting()).toBe(1);
    expect(waysIfAny()).toBeNull();
    expect(document.querySelector("[data-wait]")).not.toBeNull();
    expect(whatRefines()).toBeNull();
    expect(screen.queryByText(REFINE.label)).toBeNull();

    reading.release();
    await settled();
    expect(whatRefines()).toHaveAttribute("aria-expanded", "false");

    // It stays while a second sentence is read: there is a search to refine, and it is where it was.
    const again = api.hold("interpret", "interpret-second-sentence");
    const refines = whatRefines();
    await user.type(promptBox(), ", near a park");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    expect(again.waiting()).toBe(1);
    expect(whatRefines()).toBe(refines);
    again.release();
    await settled();
  });

  test("test_refine_search_is_closed_at_first_and_holds_the_settings_once_it_is_pressed", async () => {
    const { user, api } = await openSearch();
    await search(user);
    const refines = whatRefines() as HTMLElement;

    expect(refines).toHaveAttribute("aria-expanded", "false");
    expect(theSettingsIfAny()).toBeNull();
    expect(screen.queryByRole("button", { name: SETTINGS.money })).toBeNull();
    // No column of settings stands open, on a screen of any width, and no button of the old name.
    expect(screen.queryByRole("button", { name: SETTINGS.title })).toBeNull();

    await user.click(refines);

    expect(refines).toHaveAttribute("aria-expanded", "true");
    expect(refines).toHaveFocus();
    const opened = document.getElementById(refines.getAttribute("aria-controls") ?? "") as HTMLElement;
    expect(opened).toContainElement(theSettings());
    expect(within(theSettings()).getByRole("button", { name: SETTINGS.money })).toBeVisible();
    // The search has a ranking, so nothing is there to rank it by: a setting that is moved is ranked.
    expect(within(theSettings()).queryByRole("button", { name: SETTINGS.rank })).toBeNull();
    expect(api.callsTo("rank")).toHaveLength(1);

    // Escape closes it from inside, and the focus is on what opens it.
    await user.click(within(theSettings()).getByRole("button", { name: SETTINGS.journeys }));
    await user.keyboard("{Escape}{Escape}");
    expect(refines).toHaveAttribute("aria-expanded", "false");
    expect(refines).toHaveFocus();
    expect(theSettingsIfAny()).toBeNull();
  });

  test("test_a_setting_moved_under_refine_search_ranks_again_and_leaves_the_part_open", async () => {
    const { user, api } = await openSearch();
    await search(user);
    api.on("rank", "rank-refined").on("explain_top", "explanations-refined");
    await settingsAt(user, SETTINGS.money);
    const firm = screen.getByRole("checkbox", { name: BUDGET.firm });

    await user.click(firm);
    await settled();

    expect(api.callsTo("rank")).toHaveLength(2);
    expect(whatRefines()).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("checkbox", { name: BUDGET.firm })).toBe(firm);
    expect(firm).toHaveFocus();
  });

  test("test_start_again_brings_the_two_tabs_back_with_the_first_chosen_and_the_box_in_hand", async () => {
    const { user } = await openSearch();
    await way(user, "deep");
    expect(groupsAre().slice(0, 2).map(([name]) => name)).toEqual(OPEN_AT_FIRST);
    expect(standOpen()).toEqual(OPEN_AT_FIRST);
    // A group that stands open at first is closed, and one that is closed is opened.
    await user.click(within(theSettings()).getByRole("button", { name: SETTINGS.journeys }));
    await user.click(within(theSettings()).getByRole("button", { name: CLOSED_AT_FIRST }));
    expect(standOpen()).toEqual([SETTINGS.money, CLOSED_AT_FIRST]);
    await way(user, "quick");
    await search(user);
    await settingsAt(user);

    await user.click(screen.getByRole("button", { name: PROMPT.startAgain }));

    expect(within(ways()).getAllByRole("tab").map((tab) => tab.getAttribute("aria-selected"))).toEqual(["true", "false"]);
    expect(panelOf("quick")).toBeVisible();
    expect(promptBox()).toHaveValue("");
    expect(promptBox()).toHaveFocus();
    expect(promptBox()).toHaveAccessibleName(PROMPT.label);
    expect(whatRefines()).toBeNull();
    expect(screen.queryAllByRole("article")).toEqual([]);
    // It keeps nothing: the second way is as it first stood, with its first two groups open
    // and no other, whatever was opened and closed before.
    await way(user, "deep");
    expect(standOpen()).toEqual(OPEN_AT_FIRST);
  });

  test("test_start_again_chooses_the_first_way_in_though_the_search_began_from_the_second", async () => {
    const { user } = await openSearch(
      standInApi()
        .on("rank", "rank-default-rent")
        .on("explain_top", reasonsFor("rank-default-rent", "explanations-first")),
    );
    await way(user, "deep");
    await user.click(screen.getByRole("button", { name: SETTINGS.rank }));
    await settled();
    expect(results().length).toBeGreaterThan(0);
    expect(waysIfAny()).toBeNull();

    await user.click(screen.getByRole("button", { name: PROMPT.startAgain }));

    expect(within(ways()).getAllByRole("tab").map((tab) => tab.getAttribute("aria-selected"))).toEqual(["true", "false"]);
    expect(panelOf("quick")).toBeVisible();
    expect(panelOf("deep")).not.toBeVisible();
    // The second way is as it was before it was first chosen: it holds nothing until it is.
    expect(panelOf("deep")).toBeEmptyDOMElement();
    expect(promptBox()).toHaveFocus();
    expect(screen.queryAllByRole("article")).toEqual([]);
  });

  test("test_the_page_has_no_accessibility_fault_with_the_part_closed_or_open", async () => {
    const { user, container } = await openSearch();
    await search(user);
    expect(await faultsIn(container, { wholePage: true })).toEqual([]);

    await settingsAt(user, SETTINGS.money);
    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });
});

describe("an area that is chosen on the map", () => {
  /** What the first search ranks, as it was recorded. */
  const ranked = recordedAnswer("rank", "rank-first").body.data.ranked;
  /** What the page brought into sight, as a browser would have: jsdom scrolls nothing. */
  function watched(): { brought: Element[]; putBack: () => void } {
    const brought: Element[] = [];
    const proto = Element.prototype as { scrollIntoView?: unknown };
    const was = proto.scrollIntoView;
    proto.scrollIntoView = function scrollIntoView(this: Element) {
      brought.push(this);
    };
    return {
      brought,
      putBack: () => {
        if (was === undefined) delete proto.scrollIntoView;
        else proto.scrollIntoView = was;
      },
    };
  }

  test("test_its_card_opens_by_the_map_and_the_list_is_told_of_it_when_the_card_is_asked_to_show_it", async () => {
    // Seen on a phone: a pin was pressed, and the page went 411 px from under the finger, to
    // the result of that area in the list. The card of the map, with "Show in the list", was
    // left under the window. A press on a pin opens its card, and scrolls nothing.
    setWebGL(true);
    const { brought, putBack } = watched();
    try {
      const { user } = await openSearch();
      act(() => lastMap().fire("load"));
      await search(user);
      const cards = results();
      const pin = screen.getByRole("button", { name: /^Rank 4,/ });
      brought.length = 0;

      fireEvent.click(pin);

      const card = screen.getByRole("region", { name: MAP_CARD.label });
      expect(card).toHaveFocus();
      expect(pin).toHaveAttribute("aria-current", "true");
      expect(pin).toHaveAttribute("aria-expanded", "true");
      expect(lastMap().states.get(ranked[3]?.area_id ?? "")).toMatchObject({ selected: true });
      // The list is not told of it: no result is marked, and none is brought into sight.
      expect(cards.filter((one) => one.hasAttribute("aria-current"))).toEqual([]);
      expect(brought).toEqual([]);

      // "Show in the list" is what takes a person to the result.
      await user.click(within(card).getByRole("button", { name: MAP_CARD.showInList }));

      expect(cards[3]).toHaveAttribute("aria-current", "true");
      expect(cards.filter((one) => one.hasAttribute("aria-current"))).toHaveLength(1);
      expect(cards[3]).toHaveFocus();
      expect(pin).toHaveAttribute("aria-current", "true");
    } finally {
      putBack();
    }
  });

  test("test_an_area_chosen_in_the_list_is_chosen_on_the_map_as_it_was", async () => {
    setWebGL(true);
    const { brought, putBack } = watched();
    try {
      const { user } = await openSearch();
      act(() => lastMap().fire("load"));
      await search(user);
      const cards = results();
      const [second, fourth] = [ranked[1]?.area_id ?? "", ranked[3]?.area_id ?? ""];
      const nameOf = (areaId: string) => areas.find((area) => area.area_id === areaId)?.name ?? "";
      /** The button of a result that shows its area on the map, which stands in its working. */
      const showsOnTheMap = async (card: HTMLElement) => {
        await user.click(within(card).getByRole("button", { name: /^Show the working/ }));
        return within(card).getByRole("button", { name: /on the map$/ });
      };
      /** The box the map opens for the area that is chosen, and the area it says it is of. */
      const box = () => screen.getByRole("region", { name: MAP_CARD.label });
      const isOf = () => within(box()).getAllByRole("link")[0]?.textContent;
      /** What each result says a press did, in the line of its working that is heard. */
      const did = () => cards.map((card) => within(card).queryByRole("status")?.textContent ?? "");
      /** One result says it, of its own area, and no other says anything. */
      const saidBy = (at: number | null) =>
        cards.map((_, each) => (each === at ? CARD.shownOnMap(nameOf(ranked[each]?.area_id ?? "")) : ""));

      await user.click(await showsOnTheMap(cards[1] as HTMLElement));

      expect(cards[1]).toHaveAttribute("aria-current", "true");
      expect(lastMap().states.get(second)).toMatchObject({ selected: true });
      // The press leads to the map, which may stand a long way from the working of a result:
      // the box the map opened for the area has the focus, and the working says what was done.
      expect(box()).toHaveFocus();
      expect(isOf()).toBe(nameOf(second));
      expect(did()).toEqual(saidBy(1));
      // The box leads back to the result it is of.
      await user.click(within(box()).getByRole("button", { name: MAP_CARD.showInList }));
      expect(cards[1]).toHaveFocus();
      // Another is then chosen on the map: the list lets go of the one it had marked, and
      // says of it no longer that it is the one marked on the map.
      fireEvent.click(screen.getByRole("button", { name: /^Rank 4,/ }));
      expect(cards.filter((one) => one.hasAttribute("aria-current"))).toEqual([]);
      expect(isOf()).toBe(nameOf(fourth));
      expect(did()).toEqual(saidBy(null));
      // And the one that was chosen on the map is chosen in the list by its own button there.
      brought.length = 0;
      await user.click(await showsOnTheMap(cards[3] as HTMLElement));
      expect(cards[3]).toHaveAttribute("aria-current", "true");
      expect(box()).toHaveFocus();
      expect(isOf()).toBe(nameOf(fourth));
      expect(did()).toEqual(saidBy(3));
    } finally {
      putBack();
    }
  });
});

describe("the order of the page is the order it is drawn in", () => {
  const page = () => document.querySelector("main > [data-dressed]") as HTMLElement;
  /** Every part of the page, by the class the sheet places it by, in the order they come in. */
  const parts = () =>
    [...(page().querySelector("#panel-map")?.parentElement?.children ?? [])].map((part) =>
      part.tagName === "NOSCRIPT"
        ? "unscripted"
        : part.id === "panel-map"
          ? "map"
          : part.id === "results"
            ? "results"
            : part.getAttribute("aria-label") === SEARCH.formLabel
              ? "form"
              : part.hasAttribute("data-standing")
                ? "refine"
                : part.contains(screen.queryByRole("button", { name: /Share this search/ }))
                  ? "tools"
                  : "rest",
    );

  test("test_no_rule_of_the_sheet_draws_a_part_of_the_page_out_of_the_order_of_the_page", () => {
    // Seen on a phone: "Refine search" came before the first result in the page and was
    // drawn after it. The keys went 610 px down to it from the last chip, and 477 back up to
    // the name of the first result, and a browser held the page by it while the result over
    // it grew: a press on "Show the working" threw the page 1,634 px.
    const ordered = PAGE.filter((rule) => rule.sets.has("order") || rule.sets.has("flex-direction") || /reverse/.test(rule.sets.get("flex-flow") ?? ""));

    // What the way to share opens is laid under its button, which comes before it in the page.
    expect(ordered.map((rule) => rule.selector)).toEqual([".tools > div > div"]);
  });

  test("test_the_sheet_says_which_screen_there_is_in_one_word_and_the_page_asks_it_and_no_browser", async () => {
    const said = PAGE.filter((rule) => rule.sets.has("--screen")).map((rule) => [rule.under, rule.selector, rule.sets.get("--screen")]);

    expect(said).toEqual([
      [null, ".search", "middle"],
      ["@media (max-width: 40rem)", ".search", "narrow"],
      ["@media (min-width: 60rem)", ".search", "wide"],
    ]);
    // The page asks the browser for no width.
    const asked = setWide(true);
    const { user } = await openSearch();
    await search(user);
    expect(asked.filter((query) => /width/.test(query))).toEqual([]);
  });

  test("test_on_a_narrow_screen_what_refines_a_search_comes_after_the_first_result_in_the_page_as_on_the_screen", async () => {
    // Measured at 390 by 844: the first result of a plain search stood from 454 to 828,
    // 16 px over the foot of the first screen. The part is 44 px high and more, so drawn
    // over the first result it stood the result 52 px lower, and 36 px of it out of sight.
    const putBack = aScreen("narrow");
    try {
      const { user } = await openSearch();
      await search(user);

      expect(ON_A_NARROW_SCREEN).toBe("after");
      expect(page()).toHaveAttribute("data-refine", "after");
      expect(parts()).toEqual(["form", "results", "refine", "tools", "map", "rest"]);
      const [one, two] = results();
      const refines = whatRefines() as HTMLElement;
      expect(follows(one as HTMLElement, refines)).toBe(true);
      expect(follows(refines, theMap())).toBe(true);
      expect(follows(theMap(), two as HTMLElement)).toBe(true);
      // Every stop of the first result comes before it, so the keys go down the page and never back up.
      const stops = [...(one as HTMLElement).querySelectorAll<HTMLElement>("a, button")];
      expect(stops.length).toBeGreaterThan(3);
      for (const stop of stops) expect(follows(stop, refines)).toBe(true);
      expect(await faultsIn(document.body, { wholePage: true })).toEqual([]);
    } finally {
      putBack();
    }
  });

  test("test_on_any_other_screen_it_comes_before_the_first_result_where_it_is_drawn", async () => {
    for (const which of ["middle", "wide"] as const) {
      const putBack = aScreen(which);
      try {
        const { user, unmount } = await openSearch();
        await search(user);

        expect([which, parts()]).toEqual([which, ["form", "refine", "results", "tools", "map", "rest"]]);
        expect(follows(whatRefines() as HTMLElement, results()[0] as HTMLElement)).toBe(true);
        unmount();
      } finally {
        putBack();
      }
    }
  });

  test("test_one_line_chooses_the_other_way_in_which_it_stands_before_the_first_result_on_a_narrow_screen_too", async () => {
    expect(STANDS).toEqual(["after", "before"]);
    const putBack = aScreen("narrow");
    try {
      const user = userEvent.setup({ delay: null });
      render(
        <Shell meta={meta.meta}>
          <SearchApp meta={meta.data} areas={areas} bands={bands} client={firstSearch().client} refines="before" />
        </Shell>,
      );
      await arrived();
      await search(user);

      expect(page()).toHaveAttribute("data-refine", "before");
      expect(parts()).toEqual(["form", "refine", "results", "tools", "map", "rest"]);
    } finally {
      putBack();
    }
  });

  test("test_before_a_search_the_map_stands_over_the_two_ways_in_wherever_the_page_is_one_column", async () => {
    // The founder: "The map should stay visible on both tabs". On a phone it began at 885 of
    // 844 under Quick search, and at 2,761 under Deep search, under every setting.
    setWebGL(true);
    for (const which of ["narrow", "middle"] as const) {
      const putBack = aScreen(which);
      try {
        const { user, unmount } = await openSearch();
        act(() => lastMap().fire("load"));
        await arrived();

        expect([which, parts()]).toEqual([which, ["map", "form", "refine", "unscripted"]]);
        expect(follows(screen.getByRole("heading", { level: 1 }), theMap())).toBe(true);
        expect(follows(theMap(), ways())).toBe(true);
        // It is the map it was whichever way is chosen, and stands in neither panel.
        const map = theMap();
        await way(user, "deep");
        expect(theMap()).toBe(map);
        expect(follows(theMap(), panelOf("deep"))).toBe(true);
        expect(panelOf("deep")).not.toContainElement(map);
        // It is low there, which its own sheet draws, and the whole of it is one press away.
        expect(map.querySelector("[data-low]")).toHaveAttribute("data-low", "true");
        expect(within(map).getByRole("button", { name: MAP.taller })).toBeInTheDocument();
        unmount();
      } finally {
        putBack();
      }
    }
  });

  test("test_on_a_wide_screen_the_map_comes_after_both_ways_in_the_page_and_the_box_before_it", async () => {
    const putBack = aScreen("wide");
    try {
      await openSearch();

      expect(parts()).toEqual(["form", "refine", "unscripted", "map"]);
      expect(follows(promptBox(), theMap())).toBe(true);
    } finally {
      putBack();
    }
  });

  test("test_the_page_is_built_as_for_one_column_so_that_nothing_moves_on_a_phone_once_its_scripts_have_run", () => {
    // A page is built with no screen to ask. What is built is what a phone draws before any
    // script has run. On a wide screen every part has its column and its row by name, so
    // the part that changes its place in the page stays where it is drawn.
    const { on } = built();
    const map = on.querySelector("#panel-map") as HTMLElement;
    const tabs = within(on).getByRole("tablist", { name: WAYS.label });

    expect(follows(map, tabs)).toBe(true);
    expect(follows(within(on).getByRole("heading", { level: 1 }), map)).toBe(true);
    const wide = PAGE.filter((rule) => rule.under === "@media (min-width: 60rem)");
    const placed = (part: string) => wide.filter((rule) => rule.selector.split(",").map((one) => one.trim()).includes(part));
    for (const part of [".form", ".refine", ".map"]) {
      expect([part, placed(part).some((rule) => rule.sets.has("grid-row")), placed(part).some((rule) => rule.sets.has("grid-column"))]).toEqual([part, true, true]);
    }
  });

  test("test_a_part_that_changes_its_place_in_the_page_is_the_part_it_was_and_the_focus_is_where_it_was", async () => {
    // A phone is turned on its side, or a desk is zoomed: the screen is another, and the
    // page puts its parts in the order it draws them in now.
    const putBack = aScreen("wide");
    let narrowed = () => undefined as void;
    try {
      const { user } = await openSearch();
      await search(user);
      await settingsAt(user, SETTINGS.money);
      const [settings, map, firm] = [theSettings(), theMap(), screen.getByRole("checkbox", { name: BUDGET.firm })];
      act(() => firm.focus());
      expect(parts()).toEqual(["form", "refine", "results", "tools", "map", "rest"]);

      putBack();
      narrowed = aScreen("narrow");
      act(() => void window.dispatchEvent(new Event("resize")));

      expect(parts()).toEqual(["form", "results", "refine", "tools", "map", "rest"]);
      expect(theSettings()).toBe(settings);
      expect(theMap()).toBe(map);
      expect(screen.getByRole("checkbox", { name: BUDGET.firm })).toBe(firm);
      expect(firm).toHaveFocus();
    } finally {
      narrowed();
    }
  });
});
