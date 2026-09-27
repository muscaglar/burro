/** @jest-environment node */
/**
 * The words of the kit: what a part says of its own state. Most are heard and not seen,
 * since a part of the kit is drawn with a mark and the mark says nothing. These hold what
 * each must go on saying, however it is put.
 */

import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { ABOUT } from "./about";
import { CANNOT_PLACE } from "./facts";
import { GAUGE, LABEL, PEG } from "./kit";
import { RESULTS } from "./search";

describe("the words of the kit", () => {
  test("test_how_much_a_thing_counts_is_said_with_its_figure_and_out_of_what", () => {
    const said = GAUGE.counts(40);

    // A figure with nothing beside it was read as a score of the place.
    expect(said).toBe("counts 40 of 100");
    // Out of a hundred is said as a fit says it, so that one page does not say it two ways.
    expect(said.endsWith(RESULTS.fitOf(40))).toBe(true);
  });

  test("test_steps_that_hold_no_peg_are_named_for_what_is_drawn_as_the_key_names_them", () => {
    // The name was "Cannot be placed, counted from least to most": two lines joined by a
    // comma, the second of how a band is counted where there is no band to count.
    expect(PEG.empty).toBe("Five empty steps, with no peg");
    expect(ABOUT.band.states.unplaced.startsWith(`${PEG.empty.replace(",", "")} mean`)).toBe(true);
    // What it means stands in words beside the steps, and is heard once.
    expect(PEG.empty).not.toBe(CANNOT_PLACE);
    expect(PEG.empty).not.toMatch(/counted|placed|band/);
  });

  test("test_the_cross_of_a_chip_says_what_it_does_and_to_what", () => {
    expect(LABEL.takeOff("Leafy")).toBe("Remove: Leafy");
    // A chip with no name still has a cross, and the cross still says what it does.
    expect(LABEL.takeOff("")).toBe("Remove");
  });

  test("test_a_state_is_said_before_what_it_is_the_state_of", () => {
    expect(LABEL.of("assumed", "45 minutes")).toBe("assumed: 45 minutes");
  });

  test("test_what_the_button_beside_the_rabbit_said_is_said_by_nothing_of_the_website", () => {
    // The founder: "remove the pause button for the rabbit". Neither of its two names is written again.
    const SAID = ["Stop the rabbit moving", "Let the rabbit move"];
    const SRC = path.resolve(__dirname, "..");
    const under = (folder: string): string[] =>
      readdirSync(folder, { withFileTypes: true }).flatMap((entry) =>
        entry.isDirectory() ? under(path.join(folder, entry.name)) : [path.join(folder, entry.name)],
      );
    const drawn = under(SRC).filter((file) => /\.tsx?$/.test(file) && !/\.test\.tsx?$/.test(file));
    const code = (file: string) => readFileSync(file, "utf8").replace(/\/\*[\s\S]*?\*\/|(?<![:"'`])\/\/.*$/gm, "");
    const naming = drawn.filter((file) => SAID.some((said) => code(file).includes(said)));

    expect(drawn.length).toBeGreaterThan(200);
    expect(naming.map((file) => path.relative(SRC, file))).toEqual([]);
  });

  test("test_no_word_of_the_kit_is_loud_or_holds_a_character_the_face_lacks", () => {
    const words = [GAUGE.counts(0), PEG.empty, LABEL.of("assumed", "Leafy"), LABEL.takeOff("Leafy")];

    expect(words.filter((one) => /!|[^\x20-\x7e]/.test(one))).toEqual([]);
  });
});
