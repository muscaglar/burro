/**
 * What an area is called, and what stands beside its name.
 *
 * An area is drawn as its publisher draws it, and its publisher labels it by
 * its borough and a number. Where the area bears the name of a neighbourhood,
 * the name comes first and the label stands beside it, smaller. The label
 * begins with the borough, so it says the borough too. Until an area bears a
 * name it is called by its label, which says its borough already.
 */

import { NAMED } from "@/content/area";
import type { AreaSummary, Fact } from "@/lib/api/schema";

/** An area as a list names it. One that was made before an area could bear a name says nothing of one. */
export type NamedArea = Pick<AreaSummary, "name" | "borough"> & Partial<Pick<AreaSummary, "named">>;

/** True where the name of an area begins with the name of its borough, so that it says it already. */
export function saysItsBorough({ name, borough }: Pick<AreaSummary, "name" | "borough">): boolean {
  if (borough === "") return false;
  return name === borough || name.startsWith(`${borough} `);
}

/**
 * What stands beside the name of an area, in order: its borough, and the label its publisher
 * gives the area. Neither is said twice: a name or a label that begins with the borough says
 * the borough already. Nothing of an area whose name says it all.
 */
export function besideTheName(area: NamedArea): readonly string[] {
  const label = area.named?.label ?? null;
  const said = saysItsBorough(area) || (label !== null && saysItsBorough({ name: label, borough: area.borough }));
  return [...(said || area.borough === "" ? [] : [area.borough]), ...(label === null ? [] : [label])];
}

/** True where the name of an area is a draft: a method chose it, and no person has checked it. */
export function isDraft(area: Partial<Pick<AreaSummary, "named">>): boolean {
  return area.named?.state === "draft";
}

/**
 * What the page of an area says of its name, from the fact of the name: who wrote it, and
 * whether a person has checked it. Who wrote it is the fact's own word. Nothing of an area
 * that bears no name but its label, and nothing where the page has no words for the state.
 */
export function saidOfTheName(fact: Pick<Fact, "slots">): string | null {
  const { state, written_by: by } = fact.slots;
  if (state === undefined || by === undefined) return null;
  const words: Readonly<Record<string, ((by: string) => string) | undefined>> = NAMED.state;
  return words[state]?.(by) ?? null;
}
