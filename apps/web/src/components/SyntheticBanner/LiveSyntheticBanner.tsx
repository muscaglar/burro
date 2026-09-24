"use client";

import { useSyncExternalStore } from "react";

import { subscribeToSynthetic, syntheticSeen } from "@/lib/api/synthetic";

import { SyntheticBanner } from "./SyntheticBanner";

/**
 * The banner for a page that was built on data that is not made up. It shows
 * as soon as any answer from the API says its data is, and then stays.
 */
export function LiveSyntheticBanner() {
  const seen = useSyncExternalStore(subscribeToSynthetic, syntheticSeen, () => false);
  return <SyntheticBanner synthetic={seen} />;
}
