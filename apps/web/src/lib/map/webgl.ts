/**
 * What the browser can do for the map, and what the system asks of it.
 */

let known: boolean | null = null;

/**
 * Whether this browser can draw the map. The map needs WebGL. Where there is
 * none the map is not started at all, and the table stands in for it.
 *
 * The answer is worked out once: a browser gives out only so many of what is
 * asked for here.
 */
export function canDrawMap(): boolean {
  if (typeof document === "undefined") return false;
  if (known !== null) return known;
  try {
    const canvas = document.createElement("canvas");
    known = Boolean(canvas.getContext("webgl2") ?? canvas.getContext("webgl"));
  } catch {
    known = false;
  }
  return known;
}

/** For tests only: a browser that has not been asked yet. */
export function forgetWhetherMapCanBeDrawn(): void {
  known = null;
}

/** True when the system asks for less motion. The map then jumps where it would glide. */
export function prefersReducedMotion(): boolean {
  return typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches;
}
