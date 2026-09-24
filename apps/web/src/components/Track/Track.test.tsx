import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen } from "@testing-library/react";

import { faultsIn } from "../../../test/support/axe";
import { rulesOf } from "../../../test/support/css";
import { Track } from "./Track";

const STYLES = rulesOf(readFileSync(path.join(__dirname, "Track.module.css"), "utf8"));
const filled = (container: HTMLElement) =>
  [...container.querySelectorAll("[data-on]")].map((cell) => cell.getAttribute("data-on") === "true");

describe("the line an area is marked on", () => {
  test.each([1, 2, 3, 4, 5])("test_the_cell_of_the_band_is_filled_and_no_other: band %i", (band) => {
    const { container } = render(<Track placed={{ band, spread_low: band, spread_high: band }} says={`band ${band} of 5`} />);

    expect(filled(container)).toEqual([1, 2, 3, 4, 5].map((cell) => cell === band));
  });

  test("test_a_mixed_area_fills_the_cells_it_spans_and_is_never_a_point_in_the_middle", () => {
    const { container } = render(<Track placed={{ band: 3, spread_low: 2, spread_high: 4 }} says="varies" />);

    expect(filled(container)).toEqual([false, true, true, true, false]);
    expect(container.querySelector("[data-range='true']")).not.toBeNull();
  });

  test("test_an_area_that_spans_two_bands_is_drawn_in_the_one_it_sits_in", () => {
    const { container } = render(<Track placed={{ band: 3, spread_low: 3, spread_high: 4 }} says="band 3 of 5" />);

    expect(filled(container)).toEqual([false, false, true, false, false]);
  });

  test("test_alone_it_is_a_picture_that_says_in_words_what_it_shows", () => {
    render(<Track placed={{ band: 4, spread_low: 4, spread_high: 4 }} says="band 4 of 5, counted from Calm to Buzzy" />);

    expect(screen.getByRole("img")).toHaveAccessibleName("band 4 of 5, counted from Calm to Buzzy");
  });

  test("test_beside_the_words_that_say_the_same_it_is_kept_from_a_screen_reader", () => {
    const { container } = render(<Track placed={{ band: 4, spread_low: 4, spread_high: 4 }} />);

    // It would be heard twice. What it shows is never left to the picture alone.
    expect(screen.queryByRole("img")).toBeNull();
    expect(container.firstElementChild).toHaveAttribute("aria-hidden", "true");
  });

  test("test_the_cell_that_is_filled_differs_in_more_than_hue_and_nothing_is_drawn_see_through", () => {
    const on = STYLES.filter((rule) => /\[data-on="true"\]/.test(rule.selector) && rule.under === null);
    const off = STYLES.filter((rule) => rule.selector.trim() === ".cell" && rule.under === null);

    // Filled, a cell is the colour of the text. Empty, it is the colour of the page with an edge.
    expect(on.map((rule) => rule.sets.get("background"))).toEqual(["var(--map-line)"]);
    expect(off.map((rule) => rule.sets.get("background"))).toEqual(["var(--bg)"]);
    expect(off.map((rule) => rule.sets.get("border"))).toEqual(["1px solid var(--map-line)"]);
    expect(STYLES.filter((rule) => rule.sets.has("opacity"))).toEqual([]);
  });

  test("test_the_line_has_no_accessibility_fault", async () => {
    const { container } = render(
      <p>
        <Track placed={{ band: 2, spread_low: 2, spread_high: 2 }} says="band 2 of 5" />
        <Track placed={{ band: 2, spread_low: 1, spread_high: 3 }} />
      </p>,
    );

    expect(await faultsIn(container)).toEqual([]);
  });
});
