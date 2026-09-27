/** @jest-environment node */
/**
 * A town never stands without its line. The part that draws one with its line is `Town`,
 * and the key of every town says the same over all of its towns. What draws a town and
 * nothing beside it is theirs alone: this reads the source of the website, so that a page
 * that is written next cannot come to draw a town with no word beside it.
 */

import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

const SRC = path.resolve(__dirname, "..", "..");
const TOWN = path.resolve(__dirname);
const RULE = path.resolve(SRC, "lib", "town");

function filesUnder(folder: string): string[] {
  return readdirSync(folder, { withFileTypes: true }).flatMap((entry) => {
    const file = path.join(folder, entry.name);
    if (entry.isDirectory()) return filesUnder(file);
    return /\.tsx?$/.test(entry.name) ? [file] : [];
  });
}

const named = (file: string) => path.relative(SRC, file);
const others = filesUnder(SRC).filter((file) => !file.startsWith(TOWN + path.sep) && !file.startsWith(RULE + path.sep));
const asking = (wanted: RegExp) => others.filter((file) => wanted.test(readFileSync(file, "utf8"))).map(named);

describe("what may draw a town", () => {
  test("test_nothing_but_the_town_and_its_key_draws_a_town_with_no_line_beside_it", () => {
    expect(others.length).toBeGreaterThan(100);
    // The drawing alone, and its style sheet.
    expect(asking(/from\s+["'][^"']*Town\/Drawing(\.module\.css)?["']/)).toEqual([]);
    // And what the drawing is made of: the pieces, and where each is laid.
    expect(asking(/from\s+["'][^"']*lib\/town\/(pieces|plan|picture)["']/)).toEqual([]);
  });

  test("test_no_drawing_of_a_town_is_named_outside_the_town_so_that_none_is_laid_by_another_hand", () => {
    expect(asking(/["'`/]town-(plot|lot|low|mid|tall|roofs|trees)\b/).filter((file) => file !== path.join("lib", "art", "names.ts"))).toEqual([]);
  });

  test("test_what_reads_the_drawings_from_disk_is_asked_for_by_tests_alone", () => {
    const reading = filesUnder(RULE)
      .concat(filesUnder(TOWN))
      .filter((file) => !/\.test\.tsx?$/.test(file))
      .filter((file) => /from\s+["']\.\/picture["']|lib\/town\/picture["']/.test(readFileSync(file, "utf8")));

    expect(reading.map(named)).toEqual([]);
  });
});
