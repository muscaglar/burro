import { render, screen } from "@testing-library/react";
import { renderToStaticMarkup } from "react-dom/server";

import { recordedAnswer } from "@/lib/api/recorded";
import type { BandMark } from "@/lib/api/schema";

import { faultsIn } from "../../../test/support/axe";
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

  test("test_with_no_boundary_to_draw_there_is_no_picture", () => {
    const { container } = render(<VibeMap outlines={[]} marks={marksOf("leafy")} title={TITLE} />);

    expect(container).toBeEmptyDOMElement();
  });
});
