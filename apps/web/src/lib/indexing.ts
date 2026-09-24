/**
 * Whether a search engine may index the website, and the website's own
 * address. docs/design/web.md, section 2.
 *
 * One rule decides every page's `robots`, the header every answer carries,
 * the robots file and the sitemap, so that the four can never disagree. A
 * page may be indexed only when the release is real and the website knows
 * its own address. A made-up place must not be found by a search engine, and
 * a page that cannot say where it lives can give no canonical address.
 *
 * A crawler is never kept out by the robots file. One that is kept out never
 * fetches a page, so it never reads that the page asks to be left out, and
 * may still list the address from a link it found elsewhere. It is let in,
 * and told on the page and in the header.
 *
 * This file is read on the server only, while a page is built.
 */

import { cleanBaseUrl } from "./api/config";
import type { Meta } from "./api/schema";

export const SITE_URL_VARIABLE = "BURRO_SITE_URL";

/** The website's own origin, or `null` when none is set or it is not an origin. */
export function siteOrigin(): string | null {
  const base = cleanBaseUrl(process.env.BURRO_SITE_URL);
  if (base === null) return null;
  const url = new URL(base);
  // The website is served from the top of its host. An address with a path is not its address.
  return url.pathname === "/" ? url.origin : null;
}

/** True when a search engine may index what is built on this release. */
export function mayBeIndexed(meta: Pick<Meta, "synthetic">): boolean {
  return !meta.synthetic && siteOrigin() !== null;
}

/** A path of the website as a whole address, or `null` when the website's address is not set. */
export function wholeAddress(path: string): string | null {
  const origin = siteOrigin();
  if (origin === null || !path.startsWith("/") || path.startsWith("//")) return null;
  return `${origin}${path}`;
}

/** Where the sitemap is served. */
export const SITEMAP_PATH = "/sitemap.xml";

/** What every page tells a search engine that must stay away. */
export const KEEP_OUT = { index: false, follow: false } as const;

/**
 * The same, as a header. A page says it in its own markup. What is not a
 * page, such as the robots file or the icon, can say it only here.
 */
export const KEEP_OUT_HEADER = { key: "X-Robots-Tag", value: "noindex, nofollow" } as const;

/** The pages that are one person's, and are left out whatever the rule says. */
export const ONE_PERSONS = ["/compare", "/s"] as const;

/**
 * Which answers carry the header, as Next reads them: every one while
 * nothing may be indexed, and the pages that are one person's after that.
 */
export function keepOutHeaders(
  may: boolean,
): { readonly source: string; readonly headers: { readonly key: string; readonly value: string }[] }[] {
  const sources: readonly string[] = may ? ONE_PERSONS : ["/:path*"];
  return sources.map((source) => ({ source, headers: [{ ...KEEP_OUT_HEADER }] }));
}
