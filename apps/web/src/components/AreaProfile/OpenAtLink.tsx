"use client";

import { useEffect, useRef, type ReactNode } from "react";

import { Folded } from "../Disclosure/Folded";

interface Props {
  /** The id a link names to come here. It names a part of the page, never a place. */
  readonly id: string;
  /** What the part is opened by: its bar, which is one of a stack. */
  readonly bar: ReactNode;
  readonly className?: string;
  readonly children: ReactNode;
}

/**
 * A part of a page that is closed until it is pressed, and is open when a
 * link brought the person to it. It is the browser's own element, so it
 * opens and closes with scripts off, and what it holds is on the page either
 * way. The script does one thing more than any fold does: it opens the part
 * that was asked for.
 */
export function OpenAtLink({ id, bar, className, children }: Props) {
  const part = useRef<HTMLDetailsElement>(null);

  useEffect(() => {
    const openIfAskedFor = () => {
      if (window.location.hash === `#${id}` && part.current !== null) part.current.open = true;
    };
    openIfAskedFor();
    window.addEventListener("hashchange", openIfAskedFor);
    return () => window.removeEventListener("hashchange", openIfAskedFor);
  }, [id]);

  return (
    <Folded ref={part} id={id} className={className} bar={bar}>
      {children}
    </Folded>
  );
}
