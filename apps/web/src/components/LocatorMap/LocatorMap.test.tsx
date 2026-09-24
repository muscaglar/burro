import { render, screen } from "@testing-library/react";

import { LOCATOR } from "@/content/search";
import { recordedAnswer } from "@/lib/api/recorded";
import { CITY_FRAME, CLOSE_FRAME, locate } from "@/lib/map/locate";

import { faultsIn } from "../../../test/support/axe";
import { LocatorMap, LOCATOR_FRAME, outlinesOf } from "./LocatorMap";

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

    const picture = screen.getByRole("img", { name: "Where Farrowmere is among the areas of this data" });
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

    expect(city?.querySelectorAll("path")).toHaveLength(1);
    const drawn = city?.querySelector("path")?.getAttribute("d") ?? "";
    // It is drawn to the whole pixel, inside its frame.
    expect(numbersOf(drawn).every((number) => Number.isInteger(number))).toBe(true);
    expect(Math.max(...numbersOf(drawn))).toBeLessThanOrEqual(CITY_FRAME.width);
    // Every area has a part in it, so that the city has no hole where an area stands.
    expect(drawn.split("M").length - 1).toBeGreaterThanOrEqual(geometry.features.length);
  });

  test("test_a_ring_marks_where_the_area_stands_in_the_city", () => {
    const { container } = render(<LocatorMap geometry={geometry} areaId={HERE} name="Farrowmere" />);
    const [city] = container.querySelectorAll("svg");
    const found = locate(geometry, HERE);

    const marks = [...(city?.querySelectorAll("circle") ?? [])];
    expect(marks).toHaveLength(2);
    for (const mark of marks) {
      expect([Number(mark.getAttribute("cx")), Number(mark.getAttribute("cy"))]).toEqual(found?.at);
    }
    // Another area is marked elsewhere.
    expect(locate(geometry, "syn-n0001")?.at).not.toEqual(found?.at);
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
