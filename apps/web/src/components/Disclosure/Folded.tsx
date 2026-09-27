"use client";

import { useRef, type ComponentProps, type MouseEvent, type ReactNode, type Ref } from "react";

import { foldOf, type Stands } from "./Summary";

interface Props extends Omit<ComponentProps<"details">, "children" | "ref"> {
  /** The bar of the fold: a `Summary`, which says where it stands as this does. */
  readonly bar: ReactNode;
  /** Where its bar stands: one of a stack has a rule of ink between it and the next. */
  readonly stands?: Stands;
  /** What holds the fold may keep hold of it, as to open it when a link names it. */
  readonly ref?: Ref<HTMLDetailsElement>;
  readonly children: ReactNode;
}

/**
 * A fold that is the browser's own: what is long, closed until its bar is pressed. It
 * opens and closes with scripts off, and what it holds is in the page either way.
 *
 * A BAR IS WHERE IT WAS AFTER IT IS PRESSED, open or closed. What opens does so under the
 * bar, which does not move for it. But what lays a fold out may lay it out another way
 * once it is open: on the page of vibes two vibes stand side by side, each part of one
 * level with the same part of the other, and a vibe whose fold is open keeps its own
 * height, so that its bar went 49 px up the window from under the press that opened it.
 * A second press at the same place landed on what the bar had opened.
 *
 * So where the bar stood in the window is kept as the press is heard, and once the fold
 * has opened or closed, before the page is next drawn, the page goes by as much as the
 * bar went. Nothing is moved where the bar did not move, which is wherever a page lays a
 * fold out the same open and closed. It keeps nothing, and with scripts off the fold
 * opens as the page lays it out.
 *
 * What lays a fold out gives it a class of its own, and may say in its own sheet where
 * what the bar says begins (`--bar-begins`), so that it begins where what the bar opens
 * begins. Left unsaid, it begins five art pixels in.
 */
export function Folded({ bar, stands = "stacked", className, ref, onClick, children, ...rest }: Props) {
  /** What waits to put the bar back, where a press has been heard and the page is not yet drawn. */
  const waits = useRef<number | null>(null);

  const held = (event: MouseEvent<HTMLDetailsElement>) => {
    onClick?.(event);
    const fold = event.currentTarget;
    const pressed = event.target instanceof Element ? event.target.closest("summary") : null;
    // A press on what the fold holds, or on the bar of a fold inside it, is not a press on its bar.
    if (pressed === null || pressed.parentElement !== fold) return;
    const stood = pressed.getBoundingClientRect().top;
    if (waits.current !== null) cancelAnimationFrame(waits.current);
    // The browser opens the fold once the press has been heard by all that hears it.
    waits.current = requestAnimationFrame(() => {
      waits.current = null;
      if (!pressed.isConnected) return;
      const now = pressed.getBoundingClientRect().top;
      if (now !== stood) window.scrollBy(0, now - stood);
    });
  };

  return (
    // The press is heard here for the bar, which is the control and takes it: the browser
    // sends a key that opens the fold as a press too, and nothing here acts on either.
    // eslint-disable-next-line jsx-a11y/click-events-have-key-events, jsx-a11y/no-noninteractive-element-interactions
    <details ref={ref} className={foldOf(stands, className)} onClick={held} {...rest}>
      {bar}
      {children}
    </details>
  );
}
