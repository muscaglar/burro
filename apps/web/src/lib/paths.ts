/**
 * Every address the website links to is built here, and nowhere else.
 *
 * A path is made from a slug, a source id, the id of a vibe or nothing. None
 * takes anything a person typed, a place, a spec or a fact. A share's id and
 * the id of a vibe go in the fragment, which a browser sends to no server.
 */

import { cityOf, type City } from "./city";

/** A slug or a source id, as the contract writes one. */
const SLUG = /^[a-z0-9]+(-[a-z0-9]+)*$/;
/** The id of a vibe, as the contract writes one. */
const TAG_ID = /^[a-z][a-z0-9]*(_[a-z0-9]+)*$/;
/** A share's id: 128 random bits, as URL-safe text. */
const SHARE_ID = /^[A-Za-z0-9_-]{22}$/;

/** True when the text is a share's id as the API makes one. Anything else is never sent anywhere. */
export function isShareId(value: string): boolean {
  return SHARE_ID.test(value);
}

/** True when the text is a slug as the contract writes one. */
export function isSlug(value: string): boolean {
  return SLUG.test(value);
}

function slugOr(value: string, what: string): string {
  if (!SLUG.test(value)) throw new Error(`Not ${what}.`);
  return value;
}

/** The parts of the methods page that another page leads to. */
export type MethodsPart = "confidence" | "journeys" | "names" | "rents" | "words";

/** The parts of an area's page that another page leads to. */
export type AreaPart = "alike";

export const paths = {
  home: () => "/",
  /** The methods page, or one part of it. */
  methods: (part?: MethodsPart) => (part === undefined ? "/methods" : `/methods#${part}`),
  /** The page of every vibe, or one vibe on it. */
  vibes: (tagId?: string) => {
    if (tagId === undefined) return "/vibes";
    if (!TAG_ID.test(tagId)) throw new Error("Not the id of a vibe.");
    return `/vibes#${tagId}`;
  },
  accessibility: () => "/accessibility",
  /** The sources page, or one source on it. */
  sources: (sourceId?: string) =>
    sourceId === undefined ? "/sources" : `/sources#${slugOr(sourceId, "a source id")}`,
  /** One area's page, or one part of it. The city comes from the area's id. */
  area: (area: { readonly area_id: string; readonly slug: string }, part?: AreaPart) => {
    const city: City | null = cityOf(area.area_id);
    if (city === null) throw new Error("Not an area id.");
    return `/${city}/${slugOr(area.slug, "a slug")}${part === undefined ? "" : `#${part}`}`;
  },
  /** A comparison of two to four areas, by slug. */
  compare: (slugs: readonly string[]) =>
    `/compare?${slugs.map((slug) => `a=${slugOr(slug, "a slug")}`).join("&")}`,
  /** An opened share. */
  share: (shareId: string) => {
    if (!SHARE_ID.test(shareId)) throw new Error("Not a share id.");
    return `/s#${shareId}`;
  },
} as const;
