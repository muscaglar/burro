import { COMPARE } from "@/content/compare";

import { Art } from "../kit/Art/Art";
import styles from "./CompareTray.module.css";
import { INVITE_STANDS, TWO_TOWNS, type InviteStands } from "./look";

interface Props {
  /** Where this one stands: over the list it is said of, or under the first result of it. */
  readonly stands: "over" | "under";
  /** Where it is to stand where there is room over the list. Left out, it is what `look.ts` chooses. */
  readonly wide?: InviteStands;
}

/** True where a list draws what says that areas can be compared in this place. */
export function invites(stands: "over" | "under", wide: InviteStands = INVITE_STANDS): boolean {
  if (wide === "none") return false;
  // Asked to stand under the first result wherever a list is drawn, it is drawn there alone.
  return !(wide === "under" && stands === "over");
}

/**
 * What says that areas can be compared, before anybody has chosen one: choose two to four
 * areas, and Burro puts them side by side. Before it stands the small drawing of two towns.
 *
 * It is drawn in a line, and what holds it gives it the cream it is read on. It is on the
 * page twice, and a style sheet shows the one that has room. Before the first result, where
 * a result is wide: the search page draws it there, beside what refines the search, and a
 * list that stands a slip over itself draws it in the slip. And under the first result,
 * where a result is narrow, as on a phone, where the first result is whole on the first
 * screen and nothing is put between the box and it: the list draws it there. What is not
 * shown is not read out either.
 *
 * It says what can be done, and nothing of any area: it is drawn the same whatever the
 * list holds, and whether or not an area is chosen.
 */
export function Invite({ stands, wide = INVITE_STANDS }: Props) {
  if (!invites(stands, wide)) return null;
  return (
    <span className={styles.invite} data-stands={stands} data-says="invite">
      {/* The drawing is dress. The sentence beside it says what it stands for. */}
      <span className={styles.twoTowns} aria-hidden="true">
        {TWO_TOWNS.map((drawing) => (
          <Art key={drawing} name={drawing} alt="" />
        ))}
      </span>
      <span>{COMPARE.invite}</span>
    </span>
  );
}
