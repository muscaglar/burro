/**
 * What of a page is read on the grass. Nothing may be: a page that is dressed stands on
 * the meadow, and every sentence, figure and link of it stands in a box of cream.
 *
 * It is for a test. jsdom lays nothing out and draws no colour, so a test cannot see the
 * cream: what it can see is that a sentence stands inside a box of the kit, which brings
 * its own, and says which kind of box it is.
 */

/** What is in the page and is not drawn as words: what a drawing holds, and what is kept for a screen reader. */
const NOT_DRAWN = "svg, script, style, template, .visually-hidden";

/** The words of a page that stand in no box of the kit, each as it is written. None, of a page that is dressed whole. */
export function onTheGrass(page: Element): string[] {
  const found: string[] = [];
  const words = page.ownerDocument.createTreeWalker(page, NodeFilter.SHOW_TEXT);
  for (let node = words.nextNode(); node !== null; node = words.nextNode()) {
    const said = (node.textContent ?? "").trim();
    const held = node.parentElement;
    if (said === "" || held === null || held.closest(NOT_DRAWN) !== null) continue;
    const box = held.closest("[data-kind]");
    if (box === null || !page.contains(box)) found.push(said);
  }
  return found;
}
