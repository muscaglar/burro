/**
 * Where a stretch of what was typed stands in the box.
 *
 * Route 1 says where words stand as offsets into the text as it was sent,
 * counted in code points (contract 9.2). The box holds the text as it was
 * typed, with whatever space stands before it, and a browser counts in
 * another unit. So an offset is carried over before the box selects by it.
 *
 * Nothing here keeps a word. It takes the text from the box, where it already
 * is, and gives back offsets into it, for the box to select, or the words of
 * one stretch, for the page to draw beside an offer while the box holds them.
 */

import type { Span } from "@/lib/api/schema";

/** For each count of code points into `text`, how far that is as JavaScript counts. */
function unitsOf(text: string): number[] {
  const units = [0];
  for (const character of text) units.push((units.at(-1) ?? 0) + character.length);
  return units;
}

/**
 * The stretches as offsets into the box as it stands, in the order given. One
 * that is empty, or that falls outside the text, is left out.
 *
 * The offsets mean nothing unless the box still holds what was sent: whoever
 * calls this must know that it does.
 */
export function inTheBox(box: string, spans: readonly Span[]): Span[] {
  const lead = box.length - box.trimStart().length;
  const units = unitsOf(box.trim());
  const last = units.length - 1;
  return spans.flatMap(({ start, end }) => {
    if (!Number.isInteger(start) || !Number.isInteger(end) || start < 0 || end > last || end <= start) return [];
    return [{ start: (units[start] ?? 0) + lead, end: (units[end] ?? 0) + lead }];
  });
}

/**
 * The words of one stretch, cut from the box as it stands, or `null` where
 * the stretch is not in it. They are cut and never retyped: what is shown is
 * what the person wrote. Whoever calls this must know that the box still
 * holds what was sent, and must keep the words nowhere.
 */
export function written(box: string, span: Span): string | null {
  const [found] = inTheBox(box, [span]);
  if (found === undefined) return null;
  const words = box.slice(found.start, found.end).trim();
  return words === "" ? null : words;
}
