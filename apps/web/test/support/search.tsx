/**
 * Opens the search page in a test, as a person would find it: inside the
 * shell, with the banner, and with a stand-in for the API behind it.
 */

import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { SearchApp } from "@/components/SearchApp/SearchApp";
import { Shell } from "@/components/Shell/Shell";
import { TABLE } from "@/content/map";
import { BREAKDOWN, CHIPS, PROMPT, RESULTS } from "@/content/search";
import { SETTINGS } from "@/content/settings";
import { recordedAnswer } from "@/lib/api/recorded";
import { forgetWhetherMapCanBeDrawn } from "@/lib/map/webgl";

import { landed, standInApi, type StandIn } from "./api";
import { forgetMaps } from "./maplibre";

export const meta = recordedAnswer("get_meta", "meta").body;
export const areas = recordedAnswer("list_areas", "areas").body.data.areas;
/** Where every area sits on every vibe that may colour the map. It comes with the page. */
export const bands = recordedAnswer("list_areas", "areas").body.data.bands;

/** A string found nowhere else, planted in everything a person could type. */
export const CANARY = "zqxcanary7431";

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

/** Opens the page and waits for the boundaries of the areas, which it asks for at once. */
export async function openSearch(api: StandIn = firstSearch()) {
  const user = userEvent.setup({ delay: null });
  const view = render(
    <Shell meta={meta.meta}>
      <SearchApp meta={meta.data} areas={areas} bands={bands} client={api.client} />
    </Shell>,
  );
  await arrived();
  return { api, user, ...view };
}

/** The box, whatever its label says: before a search it asks for one, and after one it adds to it. */
export function promptBox(): HTMLTextAreaElement {
  return screen.getByRole("textbox", { name: new RegExp(`^(${PROMPT.label}|${PROMPT.labelOpen})$`) });
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

/** Shows every chip: the row holds six of what was asked for, and the usual settings, until it is opened out. */
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

/** Opens the settings, and then the groups of them that are named, in that order. */
export async function settingsAt(user: User, ...groups: string[]): Promise<void> {
  await open(user, screen.getByRole("button", { name: SETTINGS.title }));
  for (const group of groups) await open(user, screen.getByRole("button", { name: group }));
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

/** Types a sentence and presses Search, then waits for everything it leads to. */
export async function search(user: User, text = "leafy and quiet"): Promise<void> {
  await user.type(promptBox(), text);
  await user.click(screen.getByRole("button", { name: PROMPT.submit }));
  await settled();
}
