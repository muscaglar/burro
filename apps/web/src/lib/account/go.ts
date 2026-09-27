"use client";

/**
 * The one place of the website that leads a person to another page without a link being
 * pressed: once a link to sign in has been asked for, and once a search that was kept has
 * been opened. Each follows a press, and waits on an answer first, so a link alone would
 * lead on whether or not the answer was good.
 *
 * It leads to a page of a closed list, by its name. It is handed no address, so nothing a
 * person typed, no token, no id and nothing of a search can be put into one.
 *
 * It goes by the website's own router, which keeps the page in memory: a search that is
 * open in the tab is still open on the page it leads to.
 */

import { useRouter } from "next/navigation";
import { useCallback } from "react";

import { paths } from "@/lib/paths";

import { accountPaths } from "./paths";

/** Where it may lead, and nowhere else. None takes an argument. */
const WAYS = {
  search: paths.home,
  sent: accountPaths.sent,
} as const satisfies Record<string, () => string>;

export type Way = keyof typeof WAYS;

export const EVERY_WAY = Object.keys(WAYS) as Way[];

/** The address a way leads to. */
export function addressOf(way: Way): string {
  return WAYS[way]();
}

/** Leads to a page of the list. */
export function useGo(): (way: Way) => void {
  const router = useRouter();
  return useCallback((way: Way) => router.push(addressOf(way)), [router]);
}
