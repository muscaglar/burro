/**
 * Runs axe over what a test has rendered, and says what it found in a line
 * for each fault.
 *
 * axe runs here in jsdom, which lays nothing out. It cannot judge contrast,
 * size or what is on screen: test/tokens.test.ts works the contrast out, and
 * the rest is checked by hand in a browser.
 */

import axe from "axe-core";

interface Options {
  /**
   * Whether what was rendered is a whole page. A whole page is held to more:
   * everything in a landmark, one main landmark and a main heading. A part
   * of a page is not expected to hold them.
   */
  readonly wholePage?: boolean;
}

const NEEDS_LAYOUT = ["color-contrast", "color-contrast-enhanced", "target-size"];
// The title and the language are set by the layout, on an element no test renders into.
const SET_BY_THE_LAYOUT = ["document-title", "html-has-lang"];

export async function faultsIn(
  container: Element,
  { wholePage = false }: Options = {},
): Promise<string[]> {
  const off = [...NEEDS_LAYOUT, ...SET_BY_THE_LAYOUT];
  // axe holds a page to its landmarks only when it is given the whole document.
  const results = await axe.run(wholePage ? container.ownerDocument : container, {
    rules: Object.fromEntries(off.map((rule) => [rule, { enabled: false }])),
  });
  return results.violations.flatMap((violation) =>
    violation.nodes.map((node) => `${violation.id}: ${node.target.join(" ")}`),
  );
}
