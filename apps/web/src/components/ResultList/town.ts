/**
 * What the town of a result is drawn from: where its area sits on the vibes, as the page
 * holds it already. Nothing is asked of the service for a town.
 *
 * A result holds its strip: the vibes that were asked for, and two more at the most. A
 * town is drawn from four vibes, and no strip holds all four, so a town drawn from its
 * strip alone has a part left blank and says that the part is not known. Where every area
 * sits on every vibe comes with the search page, from the list of areas. Handed that, the
 * town of a result is whole, and is the town the page of its area draws.
 *
 * It is plain code with no state. It is handed an area and its strip, and neither its rank
 * nor its fit: a town says nothing of how well an area did.
 */

import type { RankedArea, VibeBands } from "@/lib/api/schema";
import { marksOf, type Mark } from "@/lib/town/bands";

/**
 * Where the area of a result sits on each vibe. What its strip says of a vibe comes first,
 * and is what the town is drawn from: the strip stands beside the town, and the two never
 * say two things of one area. Of every other vibe it is what the page holds of the area.
 */
export function marksOn(
  area: Pick<RankedArea, "area_id" | "strip">,
  bands: readonly VibeBands[] = [],
): readonly Mark[] {
  const held = marksOf(bands, area.area_id).filter((one) => !area.strip.some((mark) => mark.tag_id === one.tag_id));
  return [...area.strip, ...held];
}
