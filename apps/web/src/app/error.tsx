"use client";

import { FAULT } from "@/content/site";

interface Props {
  // The error is not read. Its message could repeat what a person typed, so
  // the page says fixed words and reports nothing.
  /** Asks for the page again and draws it again. What "Try again" does, where there is one. */
  readonly retry?: () => void;
  /** Draws the page again from what is in hand. Used where there is no `retry`. */
  readonly reset?: () => void;
}

export default function ErrorPage({ retry, reset }: Props) {
  return (
    <div role="alert">
      <h1>{FAULT.title}</h1>
      <p>{FAULT.text}</p>
      <button type="button" className="target" onClick={() => (retry ?? reset)?.()}>
        {FAULT.retry}
      </button>
    </div>
  );
}
