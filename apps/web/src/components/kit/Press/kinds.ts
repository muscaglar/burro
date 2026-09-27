/**
 * What a button is made of. It is kept apart from the button, which runs in the browser:
 * what a page drawn on the server takes from a file that runs in the browser is a
 * component and nothing else.
 */

import type { Drawing } from "../drawings";

/**
 * `go` is the one button that matters most in sight, in cobalt. `plain` is every other, in
 * page. `stop` is for what ends or takes away, in page with an edge of poppy.
 */
export type PressKind = "go" | "plain" | "stop";

export const PRESS_KINDS: readonly PressKind[] = ["go", "plain", "stop"];

/** The picture of a button of each kind. What is on has one picture, whatever its kind. */
const OF_A_KIND: Readonly<Record<PressKind | "on", Drawing>> = {
  go: "ui-button-go",
  plain: "ui-button",
  stop: "ui-button-stop",
  on: "ui-button-on",
};

/** The same, pressed: its face has stepped into the place of its shadow, on the canvas of the button up. */
const PRESSED: Readonly<Record<PressKind | "on", Drawing>> = {
  go: "ui-button-go-down",
  plain: "ui-button-down",
  stop: "ui-button-stop-down",
  on: "ui-button-on-down",
};

/** The two pictures of a button: as it stands, and pressed. What is on, or chosen, is amber. */
export function picturesOf(kind: PressKind, on: boolean): { readonly up: Drawing; readonly down: Drawing } {
  const drawn = on ? "on" : kind;
  return { up: OF_A_KIND[drawn], down: PRESSED[drawn] };
}
