import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen } from "@testing-library/react";
import { renderToStaticMarkup } from "react-dom/server";

import { recordedAnswer } from "@/lib/api/recorded";
import type { BandMark } from "@/lib/api/schema";
import { DRAWN } from "@/lib/map/style";

import { faultsIn } from "../../../test/support/axe";
import { rulesOf } from "../../../test/support/css";
import { outlinesOf } from "../LocatorMap/LocatorMap";
import { VIBE_MAP_FRAME, VibeMap } from "./VibeMap";

const geometry = recordedAnswer("get_geometry", "geometry").body.data;
const { bands } = recordedAnswer("list_areas", "areas").body.data;
const outlines = outlinesOf(geometry, VIBE_MAP_FRAME);
const marksOf = (tagId: string): readonly BandMark[] => bands.find((one) => one.tag_id === tagId)?.marks ?? [];

const TITLE = "The areas of this data coloured by a vibe";
const drawn = (container: HTMLElement) => [...container.querySelectorAll<SVGPathElement>("path[data-area]")];

describe("the map of the city coloured by one vibe", () => {
  test("test_every_area_is_drawn_once_in_the_band_the_api_gives_it", () => {
    const { container } = render(<VibeMap outlines={outlines} marks={marksOf("leafy")} title={TITLE} />);

    const areas = drawn(container);

    expect(areas).toHaveLength(geometry.features.length);
    for (const mark of marksOf("leafy")) {
      const area = areas.find((one) => one.getAttribute("data-area") === mark.area_id);
      expect(area?.getAttribute("data-band")).toBe(mark.band === null ? "none" : String(mark.band));
    }
    expect(new Set(areas.map((one) => one.getAttribute("data-band")))).toEqual(
      new Set(["1", "2", "3", "4", "5", "none"]),
    );
  });

  test("test_an_area_the_vibe_cannot_place_is_drawn_with_dots_and_never_in_the_middle_band", () => {
    const { container } = render(<VibeMap outlines={outlines} marks={marksOf("leafy")} title={TITLE} />);
    const unplaced = marksOf("leafy").filter((mark) => mark.band === null);

    expect(unplaced.length).toBeGreaterThan(0);
    for (const mark of unplaced) {
      const area = drawn(container).find((one) => one.getAttribute("data-area") === mark.area_id);
      expect(area?.getAttribute("data-band")).toBe("none");
      expect(area?.getAttribute("fill")).toMatch(/^url\(#.+\)$/);
    }
    expect(container.querySelectorAll("pattern")).toHaveLength(1);
  });

  test("test_an_area_the_bands_say_nothing_of_is_drawn_as_land_with_no_band", () => {
    const { container } = render(<VibeMap outlines={outlines} marks={marksOf("leafy").slice(1)} title={TITLE} />);
    const first = marksOf("leafy")[0];

    const area = drawn(container).find((one) => one.getAttribute("data-area") === first?.area_id);

    expect(area?.getAttribute("data-band")).toBe("none");
  });

  test("test_the_picture_is_named_and_takes_no_key_and_no_pointer", async () => {
    const { container } = render(<VibeMap outlines={outlines} marks={marksOf("pace")} title={TITLE} />);

    expect(screen.getByRole("img", { name: TITLE }).tagName.toLowerCase()).toBe("svg");
    expect(container.querySelectorAll("a, button, [tabindex]")).toHaveLength(0);
    expect(await faultsIn(container)).toEqual([]);
  });

  test("test_two_maps_on_one_page_do_not_share_the_name_of_a_pattern", () => {
    const { container } = render(
      <>
        <VibeMap outlines={outlines} marks={marksOf("leafy")} title={`${TITLE}, one`} />
        <VibeMap outlines={outlines} marks={marksOf("pace")} title={`${TITLE}, two`} />
      </>,
    );

    const ids = [...container.querySelectorAll("[id]")].map((one) => one.id);

    expect(new Set(ids).size).toBe(ids.length);
    for (const id of ids) expect(id).toMatch(/^[A-Za-z][\w-]*$/);
  });

  test("test_the_picture_holds_no_colour_of_its_own_and_reads_with_scripts_off", () => {
    const html = renderToStaticMarkup(<VibeMap outlines={outlines} marks={marksOf("leafy")} title={TITLE} />);

    // Every colour is a token of the page, set by a class. The one fill written in the picture
    // is the name of its pattern of dots.
    expect(/stroke=|style=|#[0-9a-f]{3,6}\b/i.test(html)).toBe(false);
    expect((html.match(/fill="[^"]*"/g) ?? []).every((fill) => /^fill="url\(#/.test(fill))).toBe(true);
    expect(html).toContain("<title");
  });

  test("test_a_map_that_stands_beside_the_name_of_its_vibe_is_kept_from_a_screen_reader", async () => {
    const { container } = render(<VibeMap outlines={outlines} marks={marksOf("leafy")} />);
    const picture = container.querySelector("svg");

    // With no words of its own it is for the eye alone, and is never a picture with no name.
    expect(picture).toHaveAttribute("aria-hidden", "true");
    expect(picture?.querySelector("title")).toBeNull();
    expect(picture?.hasAttribute("role")).toBe(false);
    expect(screen.queryByRole("img")).toBeNull();
    expect(drawn(container)).toHaveLength(geometry.features.length);
    expect(await faultsIn(container)).toEqual([]);
  });

  test("test_the_water_is_drawn_under_the_picture_with_the_glints_of_its_tile_and_the_land_is_plain", () => {
    const styles = rulesOf(readFileSync(path.join(__dirname, "VibeMap.module.css"), "utf8"));
    const map = new Map(styles.filter((rule) => rule.selector === ".map" && rule.under === null).flatMap((rule) => [...rule.sets]));
    const { container } = render(<VibeMap outlines={outlines} marks={marksOf("leafy")} title={TITLE} />);

    // The picture holds the land. The water is the style sheet's, so that a pixel of it is
    // as large as a pixel of the map however large the picture is drawn.
    expect(container.querySelectorAll("svg > rect")).toHaveLength(0);
    expect([map.get("background-color"), map.get("border"), map.get("--px-map")]).toEqual([
      "var(--map-water)",
      "var(--edge) solid var(--border)",
      "var(--px-ground)",
    ]);
    const glints = DRAWN.water.flatMap((row, y) => (row.includes("x") ? [[row.indexOf("x"), y]] : []));
    expect(map.get("background-position")?.replace(/\s+/g, " ")).toBe(
      glints.map(([x, y]) => `calc(var(--px-map) * ${x}) calc(var(--px-map) * ${y})`).join(", "),
    );
    expect(map.get("background-size")).toBe(`calc(var(--px-map) * ${DRAWN.water.length}) calc(var(--px-map) * ${DRAWN.water.length})`);
    // The second blue of the water is the map's by name, so that the water is turned about in the tokens alone.
    expect(map.get("--glint")).toMatch(/var\(--map-glint\)/);
    expect(map.get("--glint")).not.toMatch(/var\(--haven\)/);
    // A band is one colour, and no grain is laid on it: an area of a thousand is a few pixels across here.
    for (const band of [1, 2, 3, 4, 5]) {
      const drawn = styles.filter((rule) => rule.selector === `.area[data-band="${band}"]`).flatMap((rule) => [...rule.sets]);
      expect([band, drawn]).toEqual([band, [["fill", `var(--map-${band})`]]]);
    }
  });

  test("test_the_dots_of_an_area_that_cannot_be_placed_are_squares_as_the_map_draws_them", () => {
    const { container } = render(<VibeMap outlines={outlines} marks={marksOf("leafy")} title={TITLE} />);
    const dots = [...container.querySelectorAll("pattern > rect[class='dot']")];

    // Two to a tile, corner to corner, and nothing in the picture is round.
    expect(dots).toHaveLength(DRAWN.unranked.join("").replace(/\./g, "").length);
    expect(new Set(dots.map((dot) => `${dot.getAttribute("width")} ${dot.getAttribute("height")}`))).toEqual(new Set(["1 1"]));
    expect(dots.map((dot) => Number(dot.getAttribute("x")) - Number(dot.getAttribute("y")))).toEqual([0, 0]);
    expect(container.querySelectorAll("circle, ellipse")).toHaveLength(0);
  });

  test("test_the_names_of_the_vibes_stand_in_columns_as_wide_as_they_were_and_each_name_may_take_a_second_line", () => {
    // The little maps of the vibes stood side by side at the head of the page of vibes,
    // three to a row on a phone in columns of 107, and what stood beside a name lay over the
    // map beside it. They have gone from there: every vibe is named side by side in the key,
    // and has one map, in its own box. The columns were measured for a name with a label
    // beside it, which said that a vibe was a rough guide. The label is gone, and the columns
    // are as wide as they were: the longest name the service gives is no shorter.
    const sheet = (file: string) => rulesOf(readFileSync(path.join(__dirname, "..", "VibesList", file), "utf8"));
    const [key, vibes] = [sheet("Key.module.css"), sheet("VibesList.module.css")];
    const columns = key
      .filter((rule) => rule.selector === ".things" && rule.sets.has("grid-template-columns"))
      .map((rule) => [rule.under, rule.sets.get("grid-template-columns")]);
    const setsOf = (rules: ReturnType<typeof rulesOf>, selector: string, under: string | null = null) =>
      new Map(rules.filter((rule) => rule.selector === selector && rule.under === under).flatMap((rule) => [...rule.sets]));

    // In the key a column is nine and a half rem at the least, which is 152 px, and from
    // 40rem twelve and a half: as many to a row as have that room. Measured on 2026-09-26:
    // two to a row of 157 at 390 wide, one of 260 at 320, two of 270 at 640, four of 200 at
    // 960 and five of 211 at 1440.
    expect(columns).toEqual([
      [null, "repeat(auto-fill, minmax(min(100%, 9.5rem), 1fr))"],
      ["@media (min-width: 40rem)", "repeat(auto-fill, minmax(12.5rem, 1fr))"],
    ]);
    // A name takes a second line where the column has no room for it on one, and is never cut.
    const named = setsOf(key, ".things > li");
    expect([named.get("display"), named.get("flex-wrap"), named.get("min-width")]).toEqual(["flex", "wrap", "0"]);
    // On its own vibe the name stands in the same way, and the map beside what is said of
    // the vibe is thirteen rem and no wider. Measured where that leaves the name the least,
    // at 960 wide with two vibes to a row: the line of the name was 170 px.
    const line = setsOf(vibes, ".nameLine");
    expect([line.get("display"), line.get("flex-wrap"), line.get("min-width")]).toEqual(["flex", "wrap", "0"]);
    expect(setsOf(vibes, ".vibe", "@media (min-width: 40rem)").get("grid-template-columns")).toBe("minmax(0, 1fr) minmax(0, 13rem)");
    expect(setsOf(vibes, ".vibes", "@media (min-width: 60rem)").get("grid-template-columns")).toBe("repeat(2, minmax(0, 1fr))");
    // No list of little maps is laid out any more, so none can be laid too narrow.
    expect([...key, ...vibes].filter((rule) => /\.contents\b/.test(rule.selector)).map((rule) => rule.selector)).toEqual([]);
  });

  test("test_with_no_boundary_to_draw_there_is_no_picture", () => {
    const { container } = render(<VibeMap outlines={[]} marks={marksOf("leafy")} title={TITLE} />);

    expect(container).toBeEmptyDOMElement();
  });
});
