/**
 * Where the address of a page of accounts leads while accounts are off: to where no page
 * stands.
 *
 * With accounts off no page of accounts is built. Asked for all the same, its address is
 * tried against every folder of the website. The framework then writes a fault to the log
 * for each page of accounts that it tried. And an address of two parts, as `/sign-in/sent`
 * is, is taken by the page of an area, which answers with a frame that says nothing until
 * scripts have run, and lets a cache keep it.
 *
 * So the address of a page of accounts, and whatever follows it, is led to an address at
 * which no page stands, before any folder is asked. It is then answered as any address is
 * that the website has nothing at: by the page that says so, whole, which nothing keeps.
 *
 * It is a rule of the settings of the website, and no middleware. With accounts on it
 * holds nothing.
 */

import { accountsOn } from "./on";
import { ACCOUNT_PAGES } from "./paths";

/** An address of one part at which no page stands, and which no folder of the website takes. */
export const NOWHERE = "/no-page-stands-here";

export interface Led {
  readonly source: string;
  readonly destination: string;
}

/** The addresses that are led nowhere: none with accounts on, and with them off every one a page of accounts stands at or under. */
export function ledNowhere(): Led[] {
  if (accountsOn()) return [];
  // What the pages of accounts stand under, by the first part of the address of each.
  const roots = [...new Set(ACCOUNT_PAGES.map((page) => `/${page.split("/")[1] ?? ""}`))];
  return roots.flatMap((root) => [root, `${root}/:rest*`]).map((source) => ({ source, destination: NOWHERE }));
}
