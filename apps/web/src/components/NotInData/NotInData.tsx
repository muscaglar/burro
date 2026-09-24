import Link from "next/link";

import { NOT_IN_DATA } from "@/content/search";
import type { MetaData, NotInRelease } from "@/lib/api/schema";
import { recipeOf } from "@/lib/holds";
import { paths } from "@/lib/paths";

import styles from "./NotInData.module.css";

interface Props {
  /**
   * What was asked for that the release holds for no area, as route 1 names each thing:
   * its target, its label, and where its words stand. The words are never drawn here.
   */
  readonly missing: readonly Pick<NotInRelease, "target" | "label">[];
  /** What the release holds of each recipe, from route 11. */
  readonly meta: Pick<MetaData, "recipes">;
}

/** What kind of thing a target names, by how it begins. */
function kindOf(target: string): "budget" | "commute" | "vibe" | "feature" {
  if (target === "budget" || target === "commute") return target;
  return target.startsWith("tag:") ? "vibe" : "feature";
}

/**
 * What a person asked for that the data does not hold yet, said by name directly under
 * the box, with why. A vibe says how much of its recipe is held and what it waits on.
 *
 * It was said nowhere. "Leafy and quiet" was ranked as quiet alone under both words,
 * and a budget that could not be tested was offered, accepted, and left no area ranked.
 * Nothing here is offered and nothing is pressed: the page says what is not there.
 *
 * The name of each thing, the share of a recipe and the name of each part it waits on
 * are the API's. A budget and a journey are named by the page, as a setting is: the
 * API's label for one may hold the amount that was typed.
 */
export function NotInData({ missing, meta }: Props) {
  if (missing.length === 0) return null;
  const vibes = missing.some(({ target }) => kindOf(target) === "vibe");
  return (
    <div className={styles.missing} role="status" aria-label={NOT_IN_DATA.title}>
      <p className={styles.title}>{NOT_IN_DATA.title}</p>
      <p>{NOT_IN_DATA.lead(missing.length)}</p>
      <ul className={styles.things}>
        {missing.map(({ target, label }) => {
          const kind = kindOf(target);
          const held = kind === "vibe" ? recipeOf(meta, target.slice("tag:".length)) : undefined;
          const name = kind === "budget" || kind === "commute" ? NOT_IN_DATA[kind] : label;
          return (
            <li key={target}>
              <strong>{name}</strong>
              {". "}
              {NOT_IN_DATA.why[kind]}
              {held !== undefined && held.waits_on.length > 0
                ? ` ${NOT_IN_DATA.waitsOn(
                    held.waits_on.map((part) => NOT_IN_DATA.part(part.label, part.hundredths)).join("; "),
                  )}`
                : null}
            </li>
          );
        })}
      </ul>
      {vibes ? (
        <p>
          {/* Which page a person reads next is told to no server ahead of time. */}
          <Link className="target-min" href={paths.vibes()} prefetch={false}>
            {NOT_IN_DATA.more}
          </Link>
        </p>
      ) : null}
    </div>
  );
}
