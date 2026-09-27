"use client";

import { useSyncExternalStore, type ReactNode } from "react";

import { DISAGREES } from "@/content/site";
import type { Meta } from "@/lib/api/schema";
import { disagrees, NOTHING_SAID, subscribeToWhatWasSaid, whatWasSaid } from "@/lib/api/said";

import { PlainPage } from "./PlainPage";

interface Props {
  /** The release the page was built on. */
  readonly meta: Meta;
  readonly children: ReactNode;
}

/**
 * The page, while every answer is of the kind of data the page was built on.
 *
 * A page is built on one release and may be read while the service holds
 * another. If an answer says its data is made up and the page was built on
 * data that is not, or the other way, or one is a preview and the other is
 * not, then what the page says of itself is not true of what it would show.
 * Nothing of the page is shown then, and a plain notice says why: one box on the meadow,
 * marked as a notice is, and said at once to whoever hears the page.
 *
 * A release that moved on to another of the same kind changes nothing here:
 * the search keeps what each release made apart.
 */
export function AsItWasBuilt({ meta, children }: Props) {
  const said = useSyncExternalStore(subscribeToWhatWasSaid, whatWasSaid, () => NOTHING_SAID);
  if (!disagrees(meta, said)) return <>{children}</>;
  return <PlainPage kind="held" title={DISAGREES.heading} text={DISAGREES.text} />;
}
