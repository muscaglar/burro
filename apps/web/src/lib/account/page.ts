/**
 * What every page of accounts says of itself to a browser and to a search engine, and
 * that there is no such page where accounts are off.
 *
 * A page of accounts is one person's way in, or one person's account. It is built the same
 * for everybody and holds nothing of anybody, and it is never a page to index.
 *
 * This file is read on the server only, while a page is built.
 */

import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { NOT_FOUND } from "@/content/site";
import { KEEP_OUT } from "@/lib/indexing";

import { accountsOn } from "./on";

/**
 * Which pages are built at an address of accounts: the one, where accounts are on, and
 * none where they are off.
 *
 * Every page of accounts stands in a folder that takes whatever follows its address, and
 * says with `dynamicParams` that nothing is drawn but what is listed here. So with
 * accounts off no page of accounts is built and none is drawn when it is asked for. A
 * page that was built and then said that it was not there would be answered by an empty
 * frame, which says nothing until JavaScript has run.
 *
 * That the address is then answered by the page that says there is no such page, whole,
 * is more than a folder can hold: another folder of the website may take an address that
 * this one turned away. The settings of the website hold it, and `off.ts` says how.
 *
 * What follows the address is nothing, always: an address with anything after it is one
 * that is not listed, and no page of accounts is drawn at it. With accounts on it is
 * answered as any address is that no page stands at, which for one of two parts is by
 * the page of an area.
 */
export function pagesBuilt(): { rest: string[] }[] {
  return accountsOn() ? [{ rest: [] }] : [];
}

/** Answers that there is no such page, where accounts are off. It is asked before a page draws anything. */
export function onlyWhereAccountsAreOn(): void {
  if (!accountsOn()) notFound();
}

/** What a page of accounts says of itself. With accounts off it says what a page that is not there says. */
export function describedAs(title: string, description: string): Metadata {
  if (!accountsOn()) return { title: NOT_FOUND.title, robots: KEEP_OUT };
  return { title, description, robots: KEEP_OUT };
}
