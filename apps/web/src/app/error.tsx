"use client";

import { usePathname } from "next/navigation";
import type { MouseEvent } from "react";

import { Press } from "@/components/kit/Press/Press";
import { PlainPage } from "@/components/Shell/PlainPage";
import { FAULT } from "@/content/site";
import { paths, SHARED } from "@/lib/paths";
import { useSessionIfAny } from "@/lib/session/session";

interface Props {
  // The error is not read. Its message could repeat what a person typed, so
  // the page says fixed words and reports nothing.
  /** Asks for the page again and draws it again. What "Try again" does, where there is one. */
  readonly retry?: () => void;
  /** Draws the page again from what is in hand. Used where there is no `retry`. */
  readonly reset?: () => void;
}

/** The pages that are drawn from the search the tab holds: the search page, and the page a shared link opens. */
const DRAWN_FROM_THE_SEARCH: readonly string[] = [paths.home(), SHARED];

/**
 * The page of a fault: one box that says so, marked as a failure is, and the way to try again.
 *
 * It stands inside the shell, which holds the search for as long as the tab is open. A page
 * that is drawn from that search and threw of what it holds throws again each time it is
 * drawn from it, and asking for the page again does not let go of it. So where the fault
 * stands on such a page the search is begun again before the page is tried again, as "Start
 * again" begins it there: the search page then opens as it first stands, and a shared link
 * is opened once more. A fault of any other page leaves the search as it was, to go back to.
 */
export default function ErrorPage({ retry, reset }: Props) {
  const session = useSessionIfAny();
  const drawnFromTheSearch = DRAWN_FROM_THE_SEARCH.includes(usePathname());
  const tryAgain = (event: MouseEvent<HTMLElement>) => {
    if (drawnFromTheSearch) {
      session?.compare.clear();
      session?.search()?.flow.startAgain();
    }
    // The button goes with the page of a fault. What stays takes the focus, which is never left on nothing.
    event.currentTarget.closest<HTMLElement>("main")?.focus({ preventScroll: true });
    (retry ?? reset)?.();
  };
  return (
    <PlainPage kind="fault" title={FAULT.title} text={FAULT.text}>
      <Press kind="go" onPress={tryAgain}>
        {FAULT.retry}
      </Press>
    </PlainPage>
  );
}
