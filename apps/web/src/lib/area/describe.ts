/**
 * What an area's page tells a search engine: its title, its description, its
 * canonical address and its structured data. docs/design/web.md, section 2.
 *
 * Each says only what the area's own fact says: its name and its borough.
 * Nothing is said of what the place is like, and no figure is given. The
 * canonical address and the structured data are given only when the page may
 * be indexed, which a page built on made-up data never may.
 */

import type { Metadata } from "next";

import { AREA } from "@/content/area";
import type { AreaData, Meta } from "@/lib/api/schema";
import { KEEP_OUT, mayBeIndexed, wholeAddress } from "@/lib/indexing";
import { paths } from "@/lib/paths";

import { areaFact } from "./profile";

/** The name and the borough, as the area's fact states them. `null` when the area has no such fact. */
export function namedBy(data: AreaData): { readonly name: string; readonly borough: string } | null {
  const { name, borough } = areaFact(data)?.slots ?? {};
  return name && borough ? { name, borough } : null;
}

export function metadataFor(data: AreaData, meta: Pick<Meta, "synthetic" | "preview">): Metadata {
  const named = namedBy(data);
  // With no fact to name it the page says nothing of itself, and asks not to be indexed.
  if (named === null) return { robots: KEEP_OUT };
  const canonical = mayBeIndexed(meta) ? wholeAddress(paths.area(data.area)) : null;
  return {
    title: AREA.title(named.name, named.borough),
    description: AREA.description(named.name, named.borough),
    ...(canonical === null ? { robots: KEEP_OUT } : { alternates: { canonical } }),
  };
}

/**
 * The name of the vocabulary the structured data is written in. It is a name
 * and not a place to fetch from: no browser asks it for anything.
 */
const VOCABULARY = "https://schema.org";

/** What the structured data holds. Every value is a slot of the area's fact, or the page's own address. */
export interface PlaceData {
  readonly "@context": typeof VOCABULARY;
  readonly "@type": "Place";
  readonly name: string;
  readonly url: string;
  readonly containedInPlace: { readonly "@type": "AdministrativeArea"; readonly name: string };
}

/** The structured data of an area's page, or `null` when the page may not be indexed. */
export function structuredDataFor(data: AreaData, meta: Pick<Meta, "synthetic" | "preview">): PlaceData | null {
  const named = namedBy(data);
  if (named === null || !mayBeIndexed(meta)) return null;
  const url = wholeAddress(paths.area(data.area));
  if (url === null) return null;
  return {
    "@context": VOCABULARY,
    "@type": "Place",
    name: named.name,
    url,
    containedInPlace: { "@type": "AdministrativeArea", name: named.borough },
  };
}

/**
 * Structured data as the text of a script. Every `<` is written as its
 * escape, so that no name can close the script it is in.
 */
export function asScriptText(value: unknown): string {
  return JSON.stringify(value).replace(/</g, "\\u003c");
}
