/**
 * The town of an area, whole: what is drawn of it, where, and what it says of itself.
 *
 * It is made from where the area sits on four vibes, and from what the release calls them.
 * It is handed no name, no rank and no fit, so it cannot draw one: two areas that sit alike
 * on the four are one town.
 */

import { bandsOf, type Bands, type Mark } from "./bands";
import { piecesOf, type Piece } from "./pieces";
import { planOf, type Plan } from "./plan";
import { heldBy, type Release } from "./release";
import { saidOf, type Said } from "./said";

export interface Town {
  readonly bands: Bands;
  readonly plan: Plan;
  /** Every piece, in the order they are drawn in. */
  readonly pieces: readonly Piece[];
  /** What each part says, in the order the parts are said in. */
  readonly said: readonly Said[];
}

/**
 * The town of an area. `marks` is where the area sits on the vibes of the release, as the
 * service sent it, of which four are read. `release` is what route 11 says of the vibes.
 */
export function townOf(marks: readonly Mark[], release: Release): Town {
  const bands = bandsOf(heldBy(marks, release));
  const plan = planOf(bands);
  const said = saidOf(marks, release);
  return { bands, plan, pieces: piecesOf(plan), said };
}
