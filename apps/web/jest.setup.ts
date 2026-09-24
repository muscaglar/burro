import "@testing-library/jest-dom";

import { configure } from "@testing-library/dom";
import { createElement, type AnchorHTMLAttributes } from "react";

// A test that fails says what it looked for and did not find. It does not
// print the page, which is long, and holds whatever the test typed into it.
configure({
  getElementError(message) {
    const error = new Error((message ?? "").split("\n\n", 1)[0]);
    error.name = "TestingLibraryElementError";
    return error;
  },
});

// A link is a link. Next's own fetches the page it leads to ahead of time,
// which a test has no use for and no server to answer.
jest.mock("next/link", () => ({
  __esModule: true,
  default: ({
    href,
    prefetch,
    ...rest
  }: AnchorHTMLAttributes<HTMLAnchorElement> & { href: string; prefetch?: boolean }) =>
    // Whether it was asked not to fetch ahead is kept, so that a test can hold a link to it.
    createElement("a", { ...rest, href, ...(prefetch === false ? { "data-prefetch": "false" } : {}) }),
}));

// Tests run offline. A test that reaches for the network is wrong, so the
// real fetch is taken away and a test that needs one passes its own.
beforeEach(() => {
  globalThis.fetch = (() => {
    throw new Error("A test called fetch without a stand-in. Tests run offline.");
  }) as typeof fetch;
});

// jsdom draws nothing: it has no WebGL and no canvas to draw on, and says so
// loudly when asked. Here it says so quietly, as a browser with no WebGL does.
// A test of the map puts a stand-in in its place.
if (typeof HTMLCanvasElement !== "undefined") {
  HTMLCanvasElement.prototype.getContext = (() => null) as typeof HTMLCanvasElement.prototype.getContext;
}
