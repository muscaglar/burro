/**
 * What an area is called, and whether that says its borough already.
 *
 * Until an area has a name of its own it is called by its borough and a
 * number, as its publisher calls it. The borough then stood under the name
 * that began with it, and was said twice.
 */

import type { AreaSummary } from "@/lib/api/schema";

/** True where the name of an area begins with the name of its borough, so that it says it already. */
export function saysItsBorough({ name, borough }: Pick<AreaSummary, "name" | "borough">): boolean {
  if (borough === "") return false;
  return name === borough || name.startsWith(`${borough} `);
}
