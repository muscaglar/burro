"use client";

import { useEffect } from "react";

import { noteSynthetic } from "@/lib/api/synthetic";

/**
 * Tells the tab that the page it is on was built on made-up data.
 *
 * The shell draws the banner itself on such a page, so this draws nothing.
 * It is for the one page that has no shell: the page shown when the layout
 * itself fails, which can then still say the data was made up.
 */
export function RemembersSynthetic() {
  useEffect(() => {
    noteSynthetic(true);
  }, []);
  return null;
}
