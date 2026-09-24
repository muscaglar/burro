import { render, screen } from "@testing-library/react";

import { recordedAnswer } from "@/lib/api/recorded";

import { faultsIn } from "../../../test/support/axe";
import { LocatorMap, LOCATOR_FRAME, outlinesOf } from "./LocatorMap";

const geometry = recordedAnswer("get_geometry", "geometry").body.data;

describe("the picture of where an area is", () => {
  const outlines = outlinesOf(geometry);

  test("test_every_area_is_drawn_once_inside_the_frame", () => {
    expect(outlines).toHaveLength(geometry.features.length);
    for (const { path: drawn } of outlines) {
      const numbers = (drawn.match(/-?[\d.]+/g) ?? []).map(Number);
      expect(Math.min(...numbers)).toBeGreaterThanOrEqual(0);
      expect(Math.max(...numbers)).toBeLessThanOrEqual(LOCATOR_FRAME.width);
    }
  });

  test("test_the_picture_is_named_for_the_area_and_takes_no_key_and_no_pointer", async () => {
    const { container } = render(<LocatorMap outlines={outlines} areaId="syn-n0006" name="Farrowmere" />);

    const picture = screen.getByRole("img", { name: "Where Farrowmere is among the areas of this data" });
    expect(picture.tagName.toLowerCase()).toBe("svg");
    expect(container.querySelectorAll("a, button, [tabindex]")).toHaveLength(0);
    expect(container.querySelectorAll("path")).toHaveLength(outlines.length);
    expect(await faultsIn(container)).toEqual([]);
  });

  test("test_the_area_is_told_from_the_rest_by_its_outline_and_is_drawn_over_them", () => {
    const { container } = render(<LocatorMap outlines={outlines} areaId="syn-n0006" name="Farrowmere" />);

    const drawn = [...container.querySelectorAll("path")];
    const here = drawn.filter((one) => one.getAttribute("class") === "here");
    expect(here).toHaveLength(1);
    expect(drawn[drawn.length - 1]).toBe(here[0]);
    expect(here[0]?.getAttribute("d")).toBe(outlines.find((one) => one.areaId === "syn-n0006")?.path);
  });

  test("test_an_area_the_geometry_lacks_has_no_picture", () => {
    const { container } = render(<LocatorMap outlines={outlines} areaId="syn-n9999" name="Nowhere" />);

    expect(container).toBeEmptyDOMElement();
  });

  test("test_the_picture_holds_no_colour_of_its_own", () => {
    const { container } = render(<LocatorMap outlines={outlines} areaId="syn-n0006" name="Farrowmere" />);

    expect(/fill=|stroke=|style=|#[0-9a-f]{3,6}/i.test(container.innerHTML)).toBe(false);
  });
});
