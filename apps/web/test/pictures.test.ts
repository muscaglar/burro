/** @jest-environment node */
/**
 * The framework can make a picture of any file of `public`, at any of its widths, for whoever
 * asks at `/_next/image`, and keeps each one it makes. No page asks it for one: a drawing is a
 * file of `public/art`, laid by a style at its own size. So it is turned off, and a page that
 * comes to ask for one fails here.
 */

import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import config from "../next.config";

const SRC = path.resolve(__dirname, "..", "src");

function filesUnder(folder: string): string[] {
  return readdirSync(folder, { withFileTypes: true }).flatMap((entry) => {
    const full = path.join(folder, entry.name);
    return entry.isDirectory() ? filesUnder(full) : [full];
  });
}

test("test_the_framework_makes_no_picture_and_no_page_asks_it_for_one", () => {
  const asking = filesUnder(SRC)
    .filter((file) => /\.tsx?$/.test(file) && !/\.test\.tsx?$/.test(file))
    .filter((file) => /["']next\/(legacy\/)?image["']/.test(readFileSync(file, "utf8")))
    .map((file) => path.relative(SRC, file));

  expect(asking).toEqual([]);
  expect(config.images?.unoptimized).toBe(true);
});
