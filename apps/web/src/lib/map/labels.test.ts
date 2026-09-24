import { recordedAnswer } from "@/lib/api/recorded";

import { extentsOf, fits, linesOf, roomFor } from "./labels";

const geometry = recordedAnswer("get_geometry", "geometry").body.data;
const areas = recordedAnswer("list_areas", "areas").body.data.areas;

describe("the names of the areas on the map", () => {
  test("test_every_area_of_the_release_has_an_extent_that_holds_its_centre", () => {
    const extents = extentsOf(geometry);

    expect(extents.size).toBe(geometry.features.length);
    for (const area of areas) {
      const extent = extents.get(area.area_id);
      const [longitude, latitude] = area.centroid;
      expect(extent).toBeDefined();
      if (extent === undefined) continue;
      expect(extent.west <= longitude && longitude <= extent.east).toBe(true);
      expect(extent.south <= latitude && latitude <= extent.north).toBe(true);
    }
  });

  test("test_a_long_name_of_two_words_takes_two_lines_and_no_word_is_ever_cut", () => {
    expect(linesOf("Foxholt")).toEqual(["Foxholt"]);
    expect(linesOf("Brackenhythe")).toEqual(["Brackenhythe"]);
    expect(linesOf("Hollinsworth Quay")).toEqual(["Hollinsworth", "Quay"]);
    expect(linesOf("Otterby Fields")).toEqual(["Otterby", "Fields"]);
    // Three words are parted where the two lines are nearest in length.
    expect(linesOf("Stoke by Nayland")).toEqual(["Stoke by", "Nayland"]);
    // Every name of the release is drawn whole, in the words it came in.
    for (const area of areas) expect(linesOf(area.name).join(" ")).toBe(area.name);
  });

  test("test_a_name_is_drawn_only_where_its_area_has_room_for_the_whole_of_it", () => {
    // Room is what the area takes on the screen, in pixels.
    expect(fits("Foxholt", { width: 120, height: 60 }, false)).toBe(true);
    expect(fits("Foxholt", { width: 30, height: 60 }, false)).toBe(false);
    expect(fits("Foxholt", { width: 120, height: 10 }, false)).toBe(false);
    // Two lines need the height of two.
    expect(fits("Hollinsworth Quay", { width: 120, height: 40 }, false)).toBe(true);
    expect(fits("Hollinsworth Quay", { width: 120, height: 24 }, false)).toBe(false);
    // An area with a pin has less room: the name stands under the pin.
    expect(fits("Foxholt", { width: 120, height: 40 }, false)).toBe(true);
    expect(fits("Foxholt", { width: 120, height: 40 }, true)).toBe(false);
    expect(fits("Foxholt", { width: 120, height: 80 }, true)).toBe(true);
    // Room is never worked out from a name that is cut: a wider name needs a wider area.
    expect(roomFor("Brackenhythe", false).width).toBeGreaterThan(roomFor("Foxholt", false).width);
  });
});
