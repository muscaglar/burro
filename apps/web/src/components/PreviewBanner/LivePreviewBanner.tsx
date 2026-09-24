"use client";

import { useSyncExternalStore } from "react";

import type { Meta } from "@/lib/api/schema";
import { NOTHING_SAID, subscribeToWhatWasSaid, whatWasSaid } from "@/lib/api/said";

import { PreviewBanner } from "./PreviewBanner";

interface Props {
  /** Whether the release the page was built on is a preview. */
  readonly preview: Meta["preview"];
  /** Whether the data the page was built on is made up. */
  readonly synthetic: Meta["synthetic"];
}

/**
 * The banner that says the release is not finished, for a page that is read
 * while the service may answer from another release. It shows if the page
 * was built on a preview, and as soon as any answer says its release is one.
 * Then it stays.
 */
export function LivePreviewBanner({ preview, synthetic }: Props) {
  const said = useSyncExternalStore(subscribeToWhatWasSaid, whatWasSaid, () => NOTHING_SAID);
  // The figures are said to be real only where the page was built on real data and no
  // answer since has said its data is made up.
  return <PreviewBanner preview={preview || said.preview} real={!synthetic && !said.madeUp} />;
}
