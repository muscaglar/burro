"use client";

import Link from "next/link";

import { PORTRAIT } from "@/content/area";
import type { Tag } from "@/lib/api/schema";
import { paths } from "@/lib/paths";
import { edits, merged, NO_EDITS } from "@/lib/search/edits";
import { useSessionIfAny } from "@/lib/session/session";

import styles from "./AreaProfile.module.css";

interface Props {
  /** The vibes the area has more of than most, as the API lists them. Each runs one way. */
  readonly vibes: readonly Pick<Tag, "tag_id" | "label">[];
}

const LIST = new Intl.ListFormat("en-GB", { style: "long", type: "conjunction" });

/**
 * Starts a search from an area: the vibes it has more of than most are added
 * to the search, one edit each, as a word of the shelf is. It is a link to
 * the search page, and pressing it tells the session what to add. The search
 * page sends the edits when it is drawn.
 *
 * What is added is the ids of vibes. Nothing a person typed is read or sent,
 * and nothing is put in the address. With scripts off it leads to the search
 * page and adds nothing.
 */
export function SearchForThis({ vibes }: Props) {
  const session = useSessionIfAny();
  if (vibes.length === 0) return null;
  const wanted = vibes.map((vibe) => edits.tagOn(vibe.tag_id, "high")).reduce(merged, NO_EDITS);
  return (
    <p className={styles.searchFor}>
      <Link className={`${styles.searchForLink} target`} href={paths.home()} onClick={() => session?.wanted.set(wanted)}>
        {PORTRAIT.search.button}
      </Link>
      <span className={styles.searchForHint}>{PORTRAIT.search.adds(LIST.format(vibes.map((vibe) => vibe.label)))}</span>
    </p>
  );
}
