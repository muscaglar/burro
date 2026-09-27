import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen } from "@testing-library/react";

import { LOCATOR } from "@/content/search";
import { recordedAnswer } from "@/lib/api/recorded";
import { CITY_FRAME, CLOSE_FRAME, locate } from "@/lib/map/locate";
import { DRAWN } from "@/lib/map/style";

import { faultsIn } from "../../../test/support/axe";
import { rulesOf } from "../../../test/support/css";
import { LocatorMap, LOCATOR_FRAME, outlinesOf } from "./LocatorMap";

const STYLES = rulesOf(readFileSync(path.join(__dirname, "LocatorMap.module.css"), "utf8"));
/** What the style sheet sets of a selector, where it holds always. */
const setsOf = (selector: string) =>
  new Map(STYLES.filter((rule) => rule.selector === selector && rule.under === null).flatMap((rule) => [...rule.sets]));

const geometry = recordedAnswer("get_geometry", "geometry").body.data;
const HERE = "syn-n0006";

/** Every number of a path, in the order they stand. */
const numbersOf = (drawn: string) => (drawn.match(/-?[\d.]+/g) ?? []).map(Number);

describe("the outline of every area, for a picture that colours each", () => {
  const outlines = outlinesOf(geometry);

  test("test_every_area_is_drawn_once_inside_the_frame", () => {
    expect(outlines).toHaveLength(geometry.features.length);
    for (const { path: drawn } of outlines) {
      expect(Math.min(...numbersOf(drawn))).toBeGreaterThanOrEqual(0);
      expect(Math.max(...numbersOf(drawn))).toBeLessThanOrEqual(LOCATOR_FRAME.width);
    }
  });
});

describe("the picture of where an area is", () => {
  test("test_the_pictures_are_named_once_for_the_area_and_take_no_key_and_no_pointer", async () => {
    const { container } = render(<LocatorMap geometry={geometry} areaId={HERE} name="Farrowmere" />);

    // It is named for what it is, two small maps, and for the area: "the areas of this data"
    // said nothing to somebody who had never seen Burro.
    const picture = screen.getByRole("img", { name: LOCATOR.title("Farrowmere") });
    expect(LOCATOR.title("Farrowmere")).toBe("Two small maps that show where Farrowmere is");
    expect(picture.querySelectorAll("svg")).toHaveLength(2);
    // Each drawing is kept from a screen reader, which hears the name of both once.
    for (const drawing of picture.querySelectorAll("svg")) expect(drawing.getAttribute("aria-hidden")).toBe("true");
    expect(container.querySelectorAll("a, button, [tabindex]")).toHaveLength(0);
    // What each picture shows is said under it, where it can be seen.
    expect(picture.textContent?.includes(LOCATOR.city)).toBe(true);
    expect(picture.textContent?.includes(LOCATOR.close)).toBe(true);
    expect(await faultsIn(container)).toEqual([]);
  });

  test("test_the_city_is_one_shape_however_many_areas_it_holds", () => {
    // Seen on a release of a thousand areas: a thousand outlines in the page of every
    // area, which was 1.8 MB, and the area could not be found among them.
    const { container } = render(<LocatorMap geometry={geometry} areaId={HERE} name="Farrowmere" />);
    const [city] = container.querySelectorAll("svg");

    // The city, and the corners of the mark on it: two shapes, whatever the city holds.
    expect(city?.querySelectorAll("path[class='land']")).toHaveLength(1);
    expect(city?.querySelectorAll("path")).toHaveLength(2);
    const drawn = city?.querySelector("path[class='land']")?.getAttribute("d") ?? "";
    // It is drawn to the whole pixel, inside its frame.
    expect(numbersOf(drawn).every((number) => Number.isInteger(number))).toBe(true);
    expect(Math.max(...numbersOf(drawn))).toBeLessThanOrEqual(CITY_FRAME.width);
    // Every area has a part in it, so that the city has no hole where an area stands.
    expect(drawn.split("M").length - 1).toBeGreaterThanOrEqual(geometry.features.length);
  });

  test("test_a_whole_square_and_a_spot_mark_where_the_area_stands_in_the_city", () => {
    const { container } = render(<LocatorMap geometry={geometry} areaId={HERE} name="Farrowmere" />);
    const [city] = container.querySelectorAll("svg");
    const found = locate(geometry, HERE);

    // One mark, set down where the area stands, to the whole pixel so that its edge is hard.
    const marks = [...(city?.querySelectorAll("[data-mark]") ?? [])];
    expect(marks.map((mark) => mark.getAttribute("transform"))).toEqual([
      `translate(${Math.round(found?.at[0] ?? Number.NaN)} ${Math.round(found?.at[1] ?? Number.NaN)})`,
    ]);
    const [ring, spot] = [...(marks[0]?.children ?? [])];
    expect([ring?.tagName, ring?.getAttribute("class"), spot?.tagName, spot?.getAttribute("class")]).toEqual([
      "path",
      "ring",
      "rect",
      "spot",
    ]);
    // The ring is one square, drawn in one piece and closed: it begins once, runs along its
    // four sides and ends where it began. It was four corners with a gap between each and
    // the next, which is an edge in pieces, and the founder asked for none.
    const drawn = ring?.getAttribute("d") ?? "";
    expect(drawn).toMatch(/^M-?\d+ -?\d+H-?\d+V-?\d+H-?\d+Z$/);
    expect(drawn.match(/M/g)).toHaveLength(1);
    const [left = 0, top = 0, right = 0, foot = 0, back = 0] = numbersOf(drawn);
    expect([right, foot, back]).toEqual([-left, -top, left]);
    expect(left).toBe(top);
    // It stands about the place and clear of it: the place is seen inside it, under the spot.
    expect(numbersOf(drawn).every((number) => Number.isInteger(number) && Math.abs(number) >= 3)).toBe(true);
    expect(["x", "y", "width", "height"].map((name) => Number(spot?.getAttribute(name)))).toEqual([-1, -1, 2, 2]);
    // It is drawn in the colour of the outlines, with a hard edge, and nothing is round.
    expect(city?.querySelectorAll("circle, ellipse")).toHaveLength(0);
    expect([setsOf(".ring").get("stroke"), setsOf(".ring").get("fill"), setsOf(".ring").get("shape-rendering")]).toEqual([
      "var(--map-line)",
      "none",
      "crispEdges",
    ]);
    expect(setsOf(".spot").get("fill")).toBe("var(--map-line)");
    // No line of either picture is drawn in pieces, by the picture or by its style sheet.
    expect(container.innerHTML.includes("dasharray")).toBe(false);
    expect(/dash|dotted/.test(readFileSync(path.join(__dirname, "LocatorMap.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, ""))).toBe(false);
    // Another area is marked elsewhere.
    expect(locate(geometry, "syn-n0001")?.at).not.toEqual(found?.at);
  });

  test("test_the_area_itself_is_the_colour_of_the_thing_in_hand_and_never_that_of_a_band", () => {
    // It was drawn in the deepest green, which is the colour of the best fit, of an area of
    // any fit at all. What is in hand is amber, and has an edge of ink.
    expect([setsOf(".here").get("fill"), setsOf(".here").get("stroke")]).toEqual(["var(--chosen)", "var(--map-line)"]);
    expect([setsOf(".area").get("fill"), setsOf(".land").get("fill")]).toEqual(["var(--map-land)", "var(--map-land)"]);
    const written = readFileSync(path.join(__dirname, "LocatorMap.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
    expect(written.match(/var\(--map-[1-5]\)/g) ?? []).toEqual([]);
  });

  test("test_the_water_is_drawn_under_each_picture_with_the_glints_of_its_tile", () => {
    const { container } = render(<LocatorMap geometry={geometry} areaId={HERE} name="Farrowmere" />);

    // The pictures hold the land and what is marked on it. The water is the style sheet's.
    expect(container.querySelectorAll("rect:not([class='spot']), pattern, defs")).toHaveLength(0);
    for (const picture of [".city", ".close"]) {
      const drawn = setsOf(picture);
      expect([picture, drawn.get("background-color"), drawn.get("border")]).toEqual([
        picture,
        "var(--map-water)",
        "var(--edge) solid var(--border)",
      ]);
      // A glint for each glint of the tile, where the tile has it, in pixels of the map.
      const glints = DRAWN.water.flatMap((row, y) => (row.includes("x") ? [[row.indexOf("x"), y, row.lastIndexOf("x") - row.indexOf("x") + 1]] : []));
      expect(drawn.get("background-position")?.replace(/\s+/g, " ")).toBe(
        glints.map(([x, y]) => `calc(var(--px-map) * ${x}) calc(var(--px-map) * ${y})`).join(", "),
      );
      expect(drawn.get("background-size")).toBe(`calc(var(--px-map) * ${DRAWN.water.length}) calc(var(--px-map) * ${DRAWN.water.length})`);
      expect(glints.map(([, , wide]) => wide)).toEqual(glints.map(() => 3));
    }
    expect(setsOf(".locator").get("--glint")).toBe(
      "conic-gradient(from 270deg at calc(var(--px-map) * 3) var(--px-map), var(--map-glint) 90deg, transparent 0)",
    );
    expect(setsOf(".locator").get("--px-map")).toBe("var(--px-ground)");
  });

  test("test_the_area_is_drawn_close_among_those_around_it_and_over_them", () => {
    const { container } = render(<LocatorMap geometry={geometry} areaId={HERE} name="Farrowmere" />);
    const [, close] = container.querySelectorAll("svg");
    const found = locate(geometry, HERE);

    const drawn = [...(close?.querySelectorAll("path") ?? [])];
    const here = drawn.filter((one) => one.getAttribute("class") === "here");
    expect(here).toHaveLength(1);
    expect(drawn[drawn.length - 1]).toBe(here[0]);
    expect(here[0]?.getAttribute("d")).toBe(found?.here.path);
    // The areas around it are drawn, and far fewer than every area of the city.
    expect(found?.around.length).toBeGreaterThan(0);
    expect(found?.around.length).toBeLessThan(geometry.features.length - 1);
    expect(drawn).toHaveLength((found?.around.length ?? 0) + 1);
    // The area fills a good part of its frame: it can be seen.
    const xs = numbersOf(found?.here.path ?? "").filter((_, at) => at % 2 === 0);
    expect(Math.max(...xs) - Math.min(...xs)).toBeGreaterThan(CLOSE_FRAME.width / 5);
    expect(Math.min(...xs)).toBeGreaterThanOrEqual(0);
    expect(Math.max(...xs)).toBeLessThanOrEqual(CLOSE_FRAME.width);
  });

  test("test_an_area_the_geometry_lacks_has_no_picture_and_nor_has_one_with_no_geometry", () => {
    const { container } = render(<LocatorMap geometry={geometry} areaId="syn-n9999" name="Nowhere" />);
    expect(container).toBeEmptyDOMElement();

    const none = render(<LocatorMap geometry={null} areaId={HERE} name="Farrowmere" />);
    expect(none.container).toBeEmptyDOMElement();
  });

  test("test_the_picture_holds_no_colour_of_its_own", () => {
    const { container } = render(<LocatorMap geometry={geometry} areaId={HERE} name="Farrowmere" />);

    expect(/fill=|stroke=|style=|#[0-9a-f]{3,6}/i.test(container.innerHTML)).toBe(false);
  });
});
