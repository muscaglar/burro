/**
 * Where to draw pins whose areas are so near each other that one pin would
 * stand on another.
 *
 * A pin stands at the middle of its area. On a map of a thousand areas, two of
 * the first ten may be next to each other, and at the width of a city their
 * pins are nearer than a pin is wide. The better ranked of the two keeps its
 * place, and the other is drawn just beside it, as near its area as leaves
 * both numbers to be read.
 */

/**
 * How far apart the points of two pins must be, in pixels. A pin is 26 wide, and its head,
 * which bears its number, is 24 high: so no head stands on another, whichever way the other
 * lies. Under the head is the point of the pin, which may stand before the head of the pin
 * below it. Were the whole height of a pin kept clear, two areas one above the other would
 * have one of their pins moved off its area on a map as small as a phone draws.
 */
export const PIN_ROOM = 28;

export interface PinPoint {
  readonly id: string;
  /** Where the area is on the screen, in pixels. */
  readonly x: number;
  readonly y: number;
}

/** The ways a pin may be moved, the nearest first: around its place, and then further out. */
const WAYS: readonly (readonly [number, number])[] = [1, 1.5, 2, 3].flatMap((far) =>
  [0, 45, 315, 90, 270, 135, 225, 180].map((degrees): readonly [number, number] => {
    const turn = (degrees * Math.PI) / 180;
    return [Math.round(Math.cos(turn) * far * PIN_ROOM), Math.round(Math.sin(turn) * far * PIN_ROOM)];
  }),
);

/**
 * How far to move each pin from where its area is, so that no two are nearer
 * than a pin is wide. The pins are given in the order of their ranks, and an
 * earlier pin is never moved for a later one. A pin with room keeps its place.
 */
export function apart(points: readonly PinPoint[]): ReadonlyMap<string, readonly [number, number]> {
  const placed: (readonly [number, number])[] = [];
  const moved = new Map<string, readonly [number, number]>();
  const free = (x: number, y: number) => placed.every(([px, py]) => Math.hypot(px - x, py - y) >= PIN_ROOM);
  for (const { id, x, y } of points) {
    const way = free(x, y) ? ([0, 0] as const) : (WAYS.find(([dx, dy]) => free(x + dx, y + dy)) ?? ([0, 0] as const));
    placed.push([x + way[0], y + way[1]]);
    moved.set(id, way);
  }
  return moved;
}
