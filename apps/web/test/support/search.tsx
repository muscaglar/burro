/**
 * Opens the search page in a test, as a person would find it: inside the
 * shell, with the banner, and with a stand-in for the API behind it.
 */

import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { SearchApp } from "@/components/SearchApp/SearchApp";
import { Shell } from "@/components/Shell/Shell";
import { PROMPT, RESULTS } from "@/content/search";
import { recordedAnswer } from "@/lib/api/recorded";
import { forgetWhetherMapCanBeDrawn } from "@/lib/map/webgl";

import { standInApi, type StandIn } from "./api";
import { forgetMaps } from "./maplibre";

export const meta = recordedAnswer("get_meta", "meta").body;
export const areas = recordedAnswer("list_areas", "areas").body.data.areas;

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

/** Lets what is already on its way arrive: an answer read, a state set, a page drawn. */
export async function arrived(): Promise<void> {
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
}

/** Opens the page and waits for the boundaries of the areas, which it asks for at once. */
export async function openSearch(api: StandIn = firstSearch()) {
  const user = userEvent.setup({ delay: null });
  const view = render(
    <Shell meta={meta.meta}>
      <SearchApp meta={meta.data} areas={areas} client={api.client} />
    </Shell>,
  );
  await arrived();
  return { api, user, ...view };
}

export function promptBox(): HTMLTextAreaElement {
  return screen.getByRole("textbox", { name: PROMPT.label });
}

export function resultList(): HTMLElement {
  return screen.getByRole("list", { name: RESULTS.listLabel });
}

/** The cards and rows of the list, in the order they are in. */
export function results(): HTMLElement[] {
  return within(resultList()).getAllByRole("article");
}

type User = ReturnType<typeof userEvent.setup>;

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
