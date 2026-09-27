/**
 * Opens the search page in a test, as a person would find it: inside the
 * shell, with the banner, and with a stand-in for the API behind it.
 */

import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { SearchApp } from "@/components/SearchApp/SearchApp";
import { groupsOf } from "@/components/SettingsPanel/groups";
import { Shell } from "@/components/Shell/Shell";
import { HELPERS, type HelperId } from "@/content/helpers";
import { TABLE } from "@/content/map";
import { BREAKDOWN, CHIPS, PROMPT, RESULTS } from "@/content/search";
import { SETTINGS } from "@/content/settings";
import { REFINE, WAYS, type WayId } from "@/content/ways";
import { recordedAnswer } from "@/lib/api/recorded";
import type { MetaData } from "@/lib/api/schema";
import { forgetWhetherMapCanBeDrawn } from "@/lib/map/webgl";

import { landed, standInApi, type StandIn } from "./api";
import { forgetMaps } from "./maplibre";

export const meta = recordedAnswer("get_meta", "meta").body;
export const areas = recordedAnswer("list_areas", "areas").body.data.areas;
/** Where every area sits on every vibe that may colour the map. It comes with the page. */
export const bands = recordedAnswer("list_areas", "areas").body.data.bands;

/** A string found nowhere else, planted in everything a person could type. */
export const CANARY = "zqxcanary7431";

/**
 * What the service noticed in "Pubs are so noisy", as it answers a sentence that says the
 * noise of the person's own home: the words give no way of the pubs, which run two ways,
 * and less noise is the person's own wish, which waits for nobody. Of the sentence as it
 * was recorded the service says that the noise is said of the pubs, and waits. No answer
 * that was recorded holds a thing that is taken beside one that runs two ways, so this is
 * that answer, with what the service says of a wish of one's own laid on its second offer.
 */
export function noisyAtHome() {
  const recorded = recordedAnswer("interpret", "interpret-suggest");
  const suggestions = recorded.body.data.suggestions.map((offer, at) =>
    at === 1 ? { ...offer, only_by_choice: false, note: "" } : offer,
  );
  return { ...recorded, body: { ...recorded.body, data: { ...recorded.body.data, suggestions } } };
}

/** A stand-in that answers a first search as it was recorded. */
export function firstSearch(api: StandIn = standInApi()): StandIn {
  return api
    .on("interpret", "interpret-first")
    .on("rank", "rank-first")
    .on("explain_top", "explanations-first")
    .on("search_places", "places-search");
}

/** Whether the browser of the test can draw a map. jsdom cannot, so a test that wants one says so. */
export function setWebGL(available: boolean): void {
  forgetWhetherMapCanBeDrawn();
  forgetMaps();
  HTMLCanvasElement.prototype.getContext = (() =>
    available ? {} : null) as unknown as typeof HTMLCanvasElement.prototype.getContext;
}

/**
 * Lets what is already on its way arrive: an answer read, a state set, a page drawn.
 *
 * An answer lands a moment after it is asked for, and how long a moment is differs from one
 * machine to the next. So it waits until the stand-in has given every answer it was asked
 * for, and what each led the page to ask for. An answer that a test holds back is not
 * waited for.
 */
export async function arrived(): Promise<void> {
  await act(async () => {
    await landed();
  });
}

/**
 * How wide the browser of the test says its screen is, to whatever asks: as wide as can
 * be, or narrow. jsdom lays nothing out and cannot be asked. The search page asks no width
 * of a browser, and where its parts stand is its style sheet's to say: so a test that
 * holds that a page is the same on a screen of any width says both, and reads in what is
 * given back that nothing of a width was asked. It is said before the page is opened, and
 * taken back with `narrowAgain` when the test ends.
 */
export function setWide(wide: boolean): string[] {
  const asked: string[] = [];
  Object.defineProperty(window, "matchMedia", {
    configurable: true,
    value: (query: string) => {
      asked.push(query);
      return {
        matches: wide && /min-width/.test(query),
        media: query,
        addEventListener: () => undefined,
        removeEventListener: () => undefined,
      };
    },
  });
  return asked;
}

/** The browser of the test can no longer be asked how wide it is, as jsdom cannot. */
export function narrowAgain(): void {
  delete (window as { matchMedia?: unknown }).matchMedia;
}

/**
 * Opens the page and waits for the boundaries of the areas, which it asks for at once.
 * `form` is the release the page is handed, where a test hands it another than the one
 * that was recorded.
 */
export async function openSearch(api: StandIn = firstSearch(), form: MetaData = meta.data) {
  const user = userEvent.setup({ delay: null });
  const view = render(
    <Shell meta={meta.meta}>
      <SearchApp meta={form} areas={areas} bands={bands} client={api.client} />
    </Shell>,
  );
  await arrived();
  return { api, user, ...view };
}

/**
 * The box, whatever its label says: before a search it asks for one, and after one it adds
 * to it. Before a search it is in the first way in, and is not found while the second is
 * chosen: a test that went there goes back with `way(user, "quick")`, as a person would.
 */
export function promptBox(): HTMLTextAreaElement {
  return screen.getByRole("textbox", { name: new RegExp(`^(${PROMPT.label}|${PROMPT.labelOpen})$`) });
}

/**
 * The line under the box that says what has just happened: how many areas Burro ranked, and
 * what the order means. It is found by what it is, the one line of the page that is said
 * aloud as it changes, and never by its words, which may be written again.
 */
export function theLine(): HTMLElement {
  const lines = screen.getAllByRole("status").filter((line) => line.getAttribute("aria-live") === "polite");
  if (lines.length !== 1) throw new Error(`The page holds ${lines.length} lines that say what happened, and not one.`);
  return lines[0] as HTMLElement;
}

/** The list of results, from its first. The first result stands before the map, and the rest after it. */
export function resultList(): HTMLElement {
  return screen.getByRole("list", { name: RESULTS.listLabel });
}

/** The rest of the list of results, from the second, which stands after the map. */
export function restOfTheList(): HTMLElement {
  return screen.getByRole("list", { name: RESULTS.restLabel });
}

/** The cards and rows of the list, in the order they are in: the first, and then the rest. */
export function results(): HTMLElement[] {
  return screen
    .getAllByRole("list", { name: new RegExp(`^${RESULTS.listLabel}`) })
    .flatMap((list) => within(list).queryAllByRole("article"));
}

/**
 * What a part of the page says to whoever reads it: its text, without what is drawn for
 * the eye alone, as the name of a column is in each cell of a table that is stacked.
 */
export function saidIn(part: Element): string {
  const copy = part.cloneNode(true) as Element;
  copy.querySelectorAll("[aria-hidden='true']").forEach((drawn) => drawn.remove());
  return copy.textContent ?? "";
}

type User = ReturnType<typeof userEvent.setup>;

/** Presses a button that opens something, unless what it opens is open already. */
async function open(user: User, button: HTMLElement | null): Promise<void> {
  if (button !== null && button.getAttribute("aria-expanded") !== "true") await user.click(button);
}

/** The two tabs a search begins at, which are there before a search and at no other time. */
export function ways(): HTMLElement {
  return screen.getByRole("tablist", { name: WAYS.label });
}

/** The two tabs, or `null` once a search is open: the tabs are for beginning. */
export function waysIfAny(): HTMLElement | null {
  return screen.queryByRole("tablist", { name: WAYS.label });
}

/** The tab of a way in. */
export function tabOf(which: WayId): HTMLElement {
  return within(ways()).getByRole("tab", { name: WAYS[which] });
}

/** The panel of a way in, which its tab names, whether or not it is drawn. */
export function panelOf(which: WayId): HTMLElement {
  return document.getElementById(tabOf(which).getAttribute("aria-controls") ?? "") as HTMLElement;
}

/** Chooses a way in, unless it is chosen already. */
export async function way(user: User, which: WayId): Promise<void> {
  if (tabOf(which).getAttribute("aria-selected") !== "true") await user.click(tabOf(which));
}

/**
 * Goes to the way in that holds what is about to be used, as a person would, while there
 * are ways to choose from. Once a search is open there is none, and nothing is pressed.
 */
async function goTo(user: User, which: WayId): Promise<void> {
  if (waysIfAny() !== null) await way(user, which);
}

/**
 * What opens and closes the settings once a search is open, or `null` before one. Before
 * a search the settings stand open in the second way in, and what would open and close
 * them is not drawn.
 */
export function whatRefines(): HTMLElement | null {
  return screen.queryByRole("button", { name: REFINE.label });
}

/** The settings, where they are drawn: under their own name, in the second way in or in the part that refines. */
export function theSettings(): HTMLElement {
  return screen.getByRole("region", { name: SETTINGS.title });
}

/** The settings, or `null` where they are not drawn. */
export function theSettingsIfAny(): HTMLElement | null {
  return screen.queryByRole("region", { name: SETTINGS.title });
}

/**
 * The groups of the settings, in the order they stand in: the name on the bar of each, and
 * whether it stands open. A couple stand open at first, so a test that opens one looks
 * first. A search in which an area is hidden has a group more, for the areas, which is
 * not among these.
 */
export function groupsAre(): (readonly [name: string, open: boolean])[] {
  return groupsOf(meta.data.defaults.rent, meta.data, areas, {}).map(({ label }) => [
    label,
    within(theSettings()).getByRole("button", { name: label }).getAttribute("aria-expanded") === "true",
  ]);
}

/** The line of helpers under the box, in the first way in, which is there before a search and at no other time. */
export function helpers(): HTMLElement {
  return screen.getByRole("group", { name: HELPERS.label });
}

/**
 * Opens a helper of the first way in, unless it is open already, and chooses that way
 * first where the other is chosen. What a quick search can begin from without typing is
 * one press away: an example, and a word of the shelf.
 */
export async function helper(user: User, which: HelperId): Promise<void> {
  await goTo(user, "quick");
  await open(user, within(helpers()).getByRole("button", { name: HELPERS[which] }));
}

/** Shows every chip: the row holds six of what was asked for until it is opened out, and on a narrow screen fewer. */
export async function everyChip(user: User): Promise<void> {
  await open(user, screen.queryByRole("button", { name: /^\+\d+ more$/ }));
}

/**
 * What a chip says of itself once it is opened: every part of it, and which of them
 * nobody chose. In the row a chip says what was said, and that the rest was assumed.
 */
export async function chipInFull(user: User, name: RegExp): Promise<string> {
  const chip = screen.getByRole("button", { name });
  await open(user, chip);
  return chip.textContent ?? "";
}

/** Takes a chip out of the search, by the name on it. */
export async function removeChip(user: User, name: string): Promise<void> {
  await everyChip(user);
  await user.click(screen.getByRole("button", { name: `${CHIPS.remove}: ${name}` }));
}

/** Shows every result: the list holds the first ten until it is asked for the rest. */
export async function everyResult(user: User): Promise<void> {
  const more = screen.queryByRole("button", { name: /^Show \d+ more$/ });
  if (more !== null) await user.click(more);
}

/** Opens the table of every area, which is one press from the map. */
export async function theTable(user: User): Promise<HTMLElement> {
  const button = screen.getByRole("button", { name: TABLE.title });
  await open(user, button);
  const opened = document.getElementById(button.getAttribute("aria-controls") ?? "");
  return within(opened as HTMLElement).getByRole("table");
}

/** Opens the working of the result of an area, and answers with the result. */
export async function workingOf(user: User, name: string): Promise<HTMLElement> {
  const button = screen.getByRole("button", { name: RESULTS.workingOf(name) });
  await open(user, button);
  return button.closest("article") as HTMLElement;
}

/**
 * Opens everything of a search that is one press away: every chip, every
 * result, the working of each and how its fit is worked out, and the table.
 * It is for a test of the whole of what a search can show.
 */
export async function theWholeOfIt(): Promise<void> {
  const press = (name: RegExp | string) => {
    for (const button of screen.queryAllByRole("button", { name })) {
      if (button.getAttribute("aria-expanded") !== "true") fireEvent.click(button);
    }
  };
  press(/^\+\d+ more$/);
  press(/^Show \d+ more$/);
  press(new RegExp(`^${RESULTS.showWorking}: `));
  press(new RegExp(`^${BREAKDOWN.title}: `));
  press(TABLE.title);
  await arrived();
}

/**
 * Brings the settings into sight, wherever they stand, and then opens the groups of them
 * that are named, in that order, unless one is open already: a couple stand open at first.
 * Before a search the settings stand open in the second way in, "Deep search". Once a
 * search is open they are the part that refines it, "Refine search", closed until it is
 * pressed.
 *
 * Before a search it leaves the second way chosen, and the box is in the first: a test
 * that then types goes back with `way(user, "quick")`, as `search` and `helper` do.
 */
export async function settingsAt(user: User, ...groups: string[]): Promise<void> {
  if (waysIfAny() !== null) await way(user, "deep");
  else await open(user, whatRefines());
  for (const group of groups) await open(user, within(theSettings()).getByRole("button", { name: group }));
}

/** Waits until nothing is being worked out, and everything that was asked for is in. */
export async function settled(): Promise<void> {
  await waitFor(() => {
    expect(screen.queryByRole("button", { name: PROMPT.stop })).toBeNull();
    expect(document.querySelectorAll("[aria-busy='true']")).toHaveLength(0);
    expect(document.querySelectorAll(".skeleton")).toHaveLength(0);
  });
  await arrived();
}

/**
 * Types a sentence and presses Search, then waits for everything it leads to. Before a
 * search the box is in the first way in, which is chosen first where the other is.
 */
export async function search(user: User, text = "leafy and quiet"): Promise<void> {
  await goTo(user, "quick");
  await user.type(promptBox(), text);
  await user.click(screen.getByRole("button", { name: PROMPT.submit }));
  await settled();
}
