import { recordedAnswer } from "@/lib/api/recorded";

import { ART } from "@/lib/art/names";

import {
  BELOW_A_PIN,
  extentsOf,
  fits,
  LETTERING,
  linesOf,
  named,
  PIN,
  roomFor,
  typeOfPage,
  UNDER_A_PIN,
  whole,
  type ToName,
} from "./labels";

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
    expect(linesOf("Larks by Foxholt")).toEqual(["Larks by", "Foxholt"]);
    // Every name of the release is drawn whole, in the words it came in.
    for (const area of areas) expect(linesOf(area.name).join(" ")).toBe(area.name);
  });

  test("test_a_name_is_drawn_only_where_its_area_has_room_for_the_whole_of_it", () => {
    // Room is what the area takes on the screen, in pixels.
    expect(fits("Foxholt", { width: 120, height: 60 }, false)).toBe(true);
    expect(fits("Foxholt", { width: 30, height: 60 }, false)).toBe(false);
    expect(fits("Foxholt", { width: 120, height: 10 }, false)).toBe(false);
    // Two lines need the height of two.
    expect(fits("Hollinsworth Quay", { width: 120, height: 48 }, false)).toBe(true);
    expect(fits("Hollinsworth Quay", { width: 120, height: 40 }, false)).toBe(false);
    // An area with a pin has less room: the name stands under the pin.
    expect(fits("Foxholt", { width: 120, height: 40 }, false)).toBe(true);
    expect(fits("Foxholt", { width: 120, height: 40 }, true)).toBe(false);
    expect(fits("Foxholt", { width: 120, height: 80 }, true)).toBe(true);
    // Room is never worked out from a name that is cut: a wider name needs a wider area.
    expect(roomFor("Brackenhythe", false).width).toBeGreaterThan(roomFor("Foxholt", false).width);
  });

  test("test_a_name_is_given_the_room_of_the_face_of_names_at_its_widest", () => {
    // Measured in a browser, in the face of names at 20 pixels: "Brackenhythe" is 97.5
    // pixels wide and "Larkspur" 62.2, which are 8.1 and 7.8 a letter, and the widest of
    // the names that were measured came to 8.6. A line is 16 pixels high. The plate a name
    // stands on has an edge and room inside it, which are 12 pixels, and 2 more are kept.
    expect(LETTERING).toEqual({ letter: 8.6, line: 16, around: { plate: 14, halo: 6 } });
    expect(roomFor("Brackenhythe", false)).toEqual({ width: 12 * 8.6 + 14, height: 16 + 14 });
    expect(roomFor("Brackenhythe", false).width).toBeGreaterThanOrEqual(97.5 + 12);
    expect(roomFor("Larkspur", false).width).toBeGreaterThanOrEqual(62.2 + 12);
    // No name of the release is given less room than its letters take at their widest.
    for (const area of areas) {
      const widest = Math.max(...linesOf(area.name).map((line) => line.length));
      expect(roomFor(area.name, false).width).toBe(widest * 8.6 + 14);
    }
  });

  test("test_a_name_with_a_halo_needs_less_room_than_a_name_on_a_plate_so_that_more_areas_are_named", () => {
    // A plate has an edge and room inside it: two pixels of edge and four of room at each
    // side. A halo is two pixels about a letter. A name is on a plate unless it is said not to be.
    expect(roomFor("Foxholt", false)).toEqual(roomFor("Foxholt", false, "plate"));
    expect(roomFor("Foxholt", false, "halo")).toEqual({ width: 7 * 8.6 + 6, height: 16 + 6 });
    expect(roomFor("Foxholt", false, "plate").width - roomFor("Foxholt", false, "halo").width).toBe(8);
    // Measured in a browser: "Foxholt" is 51.5 pixels wide, and its halo 4 more.
    expect(roomFor("Foxholt", false, "halo").width).toBeGreaterThanOrEqual(51.5 + 4);
    expect(fits("Foxholt", { width: 70, height: 26 }, false, "halo")).toBe(true);
    expect(fits("Foxholt", { width: 70, height: 26 }, false, "plate")).toBe(false);
    expect(fits("Foxholt", { width: 70, height: 26 }, false)).toBe(false);
  });

  test("test_a_name_is_given_more_room_where_the_type_of_the_page_was_made_larger", () => {
    // Seen in a browser, with the type of the browser a quarter larger: a name was drawn
    // larger, as it should be, in the room of a name of the size the website sets, and
    // stood over the edge of its area.
    const [set, larger] = [roomFor("Foxholt", false), roomFor("Foxholt", false, "plate", 1.25)];

    expect(roomFor("Foxholt", false, "plate", 1)).toEqual(set);
    // Its letters take more. Its edge and the room inside it are pixels of the screen, and take what they took.
    expect(larger).toEqual({ width: 7 * 8.6 * 1.25 + 14, height: 16 * 1.25 + 14 });
    expect(fits("Foxholt", { width: 80, height: 40 }, false, "plate", 1)).toBe(true);
    expect(fits("Foxholt", { width: 80, height: 40 }, false, "plate", 1.25)).toBe(false);
    // A pin is a drawing, and is of one size whatever the type.
    expect(roomFor("Foxholt", true, "plate", 1.25).height - larger.height).toBe(UNDER_A_PIN);
  });

  test("test_the_type_of_the_page_is_read_from_the_page_and_is_as_it_was_set_where_it_cannot_be", () => {
    const root = document.documentElement;

    root.style.fontSize = "20px";
    expect(typeOfPage()).toBe(1.25);
    root.style.fontSize = "16px";
    expect(typeOfPage()).toBe(1);
    root.style.fontSize = "";
    expect(typeOfPage()).toBe(1);
  });

  test("test_a_name_under_a_pin_is_given_the_room_of_the_pin_and_stands_clear_of_its_point", () => {
    // A pin is 16 pixels of its drawing high, each of which is 2 of the screen, and stands
    // on its place by its point. The name stands under the point, and clear of it.
    expect(BELOW_A_PIN).toBeGreaterThan(0);
    expect(UNDER_A_PIN).toBe(16 * 2 + BELOW_A_PIN);
    expect(roomFor("Foxholt", true).height - roomFor("Foxholt", false).height).toBe(UNDER_A_PIN);
  });
});

describe("which areas the map names, and where each name stands", () => {
  // The window of the map beside the answer, measured at 1440 by 900.
  const WINDOW = { width: 248, height: 240 };
  const PLATE = { drawn: "plate", larger: 1 } as const;
  /** An area with all the room it could ask for, in the middle of the window unless it is said to be elsewhere. */
  const area = (id: string, name: string, at: { x: number; y: number } = { x: 124, y: 120 }, more: Partial<ToName> = {}): ToName => ({
    id,
    name,
    at,
    room: { width: 400, height: 400 },
    pin: null,
    ...more,
  });
  /** An area of the first ten, as small as an area of a thousand is drawn: it has no room for any name. */
  const pinned = (id: string, name: string, at: { x: number; y: number }, pin = at): ToName => ({
    id,
    name,
    at,
    room: { width: 8, height: 8 },
    pin,
  });
  const ids = (names: readonly { id: string }[]) => names.map((name) => name.id);
  const overlap = (one: { left: number; top: number; right: number; bottom: number }, other: typeof one) =>
    one.left < other.right && other.left < one.right && one.top < other.bottom && other.top < one.bottom;

  test("test_a_name_is_never_cut_by_the_edge_of_the_window_of_the_map", () => {
    // Seen in a browser, at 1440 by 900 with the map drawn nearer: "Larkspur Hill" stood from
    // 67 px left of the window of the map, and "Otterby Fields" ran 58 px past its right edge.
    const width = roomFor("Foxholt", false).width;
    const held = (at: { x: number; y: number }) => ids(named([area("a", "Foxholt", at)], WINDOW, { ...PLATE, by: "room" }));

    expect(held({ x: 124, y: 120 })).toEqual(["a"]);
    // Its middle is in the window, and its letters would not all be.
    expect(held({ x: width / 2 - 1, y: 120 })).toEqual([]);
    expect(held({ x: WINDOW.width - width / 2 + 1, y: 120 })).toEqual([]);
    expect(held({ x: 124, y: 10 })).toEqual([]);
    expect(held({ x: 124, y: WINDOW.height - 10 })).toEqual([]);
    // Against the edge, and whole, it is drawn.
    expect(held({ x: width / 2, y: 120 })).toEqual(["a"]);
    expect(held({ x: WINDOW.width - width / 2, y: 120 })).toEqual(["a"]);
    // The same goes for a name under a pin, whichever way the areas to name are chosen.
    for (const by of ["room", "pins"] as const) {
      const under = (at: { x: number; y: number }) =>
        ids(named([area("a", "Foxholt", at, { pin: at })], WINDOW, { ...PLATE, by }));
      expect(under({ x: 124, y: 120 })).toEqual(["a"]);
      expect(under({ x: 5, y: 120 })).toEqual([]);
      expect(under({ x: 124, y: WINDOW.height - 10 })).toEqual([]);
    }
  });

  test("test_what_stands_whole_in_a_window_is_told_from_what_its_edge_would_cut", () => {
    expect(whole({ left: 0, top: 0, right: 248, bottom: 240 }, WINDOW)).toBe(true);
    expect(whole({ left: -0.5, top: 0, right: 100, bottom: 30 }, WINDOW)).toBe(false);
    expect(whole({ left: 200, top: 0, right: 248.5, bottom: 30 }, WINDOW)).toBe(false);
    expect(whole({ left: 0, top: -1, right: 100, bottom: 30 }, WINDOW)).toBe(false);
    expect(whole({ left: 0, top: 220, right: 100, bottom: 241 }, WINDOW)).toBe(false);
    // A window that is not laid out yet cuts nothing: there is nothing to be cut by.
    expect(whole({ left: -500, top: -500, right: -400, bottom: -480 }, null)).toBe(true);
    expect(ids(named([area("a", "Foxholt", { x: -900, y: -900 })], null, { ...PLATE, by: "room" }))).toEqual(["a"]);
  });

  test("test_the_first_ten_are_named_under_their_pins_wherever_the_window_has_room", () => {
    // Seen in a browser, at 1440 by 900: the map named no area as it was first drawn. No
    // area had room for its own name, in a window 248 px wide that holds the whole city:
    // and of a thousand areas none ever has, until the map is drawn a long way nearer.
    const first = [pinned("1", "Foxholt", { x: 60, y: 60 }), pinned("2", "Wexmoor", { x: 180, y: 150 })];

    expect(ids(named(first, WINDOW, { ...PLATE, by: "room" }))).toEqual([]);
    const names = named(first, WINDOW, { ...PLATE, by: "pins" });
    expect(ids(names)).toEqual(["1", "2"]);
    // Each stands under the point of its pin, clear of it, with its middle under the point.
    for (const [at, name] of names.entries()) {
      const pin = first[at]?.pin ?? { x: 0, y: 0 };
      const { width, height } = roomFor(first[at]?.name ?? "", false);
      expect(name.under).toBe(true);
      expect(name.box).toEqual({
        left: pin.x - width / 2,
        top: pin.y + BELOW_A_PIN,
        right: pin.x + width / 2,
        bottom: pin.y + BELOW_A_PIN + height,
      });
      expect(name.offset).toEqual([0, BELOW_A_PIN]);
    }
  });

  test("test_an_area_with_no_pin_is_named_only_where_its_own_area_has_room_for_the_whole_of_its_name", () => {
    // A name with no pin over it says which area it is of by where it lies, and by nothing else.
    const small = area("a", "Foxholt", { x: 124, y: 120 }, { room: { width: 40, height: 50 } });
    const large = area("b", "Foxholt", { x: 124, y: 120 });

    for (const by of ["room", "pins"] as const) {
      expect(ids(named([small], WINDOW, { ...PLATE, by }))).toEqual([]);
      const [name] = named([large], WINDOW, { ...PLATE, by });
      expect(name?.under).toBe(false);
      expect(name?.offset).toEqual([0, 0]);
      const { width, height } = roomFor("Foxholt", false);
      expect(name?.box).toEqual({ left: 124 - width / 2, top: 120 - height / 2, right: 124 + width / 2, bottom: 120 + height / 2 });
    }
  });

  test("test_no_name_lies_over_a_pin_or_over_another_name_and_the_better_ranked_is_named_first", () => {
    // The pins of the first ten crowd a small map. The areas are given in the order of their ranks.
    const crowd = [
      pinned("1", "Farrowmere", { x: 120, y: 60 }),
      // Its name would lie over the name of the first.
      pinned("2", "Gorsebeck", { x: 190, y: 40 }),
      // Its name would lie over the pin of the fourth, which stands under it.
      pinned("3", "Cindermoor", { x: 120, y: 170 }),
      // Its name would be cut by the foot of the window.
      pinned("4", "Marrowfen", { x: 120, y: 210 }),
    ];
    const names = named(crowd, WINDOW, { ...PLATE, by: "pins" });

    expect(ids(names)).toEqual(["1"]);
    // Given the other way round, it is the other that is named: the order is the order of the ranks.
    expect(ids(named([crowd[1] as ToName, crowd[0] as ToName], WINDOW, { ...PLATE, by: "pins" }))).toEqual(["2"]);
    // Whatever is named, no name lies over another, and none over a pin.
    const many = Array.from({ length: 10 }, (_, at) => pinned(String(at + 1), "Foxholt", { x: 30 + ((at * 53) % 190), y: 40 + ((at * 37) % 160) }));
    const drawn = named(many, WINDOW, { ...PLATE, by: "pins" });
    expect(drawn.length).toBeGreaterThan(1);
    for (const one of drawn) {
      for (const other of drawn) if (one !== other) expect(overlap(one.box, other.box)).toBe(false);
      for (const { pin } of many) {
        if (pin === null) continue;
        const head = { left: pin.x - PIN.width / 2, top: pin.y - PIN.height, right: pin.x + PIN.width / 2, bottom: pin.y };
        expect(overlap(one.box, head)).toBe(false);
      }
    }
  });

  test("test_the_name_of_an_area_whose_pin_was_moved_off_it_stands_under_the_pin", () => {
    // Two of the first ten may be next to each other, and the pin of the second is then
    // drawn beside the first. A name under no pin would be taken for a name with none.
    const moved = pinned("2", "Foxholt", { x: 100, y: 100 }, { x: 128, y: 100 });
    const [name] = named([moved], WINDOW, { ...PLATE, by: "pins" });
    const { width } = roomFor("Foxholt", false);

    expect(name?.offset).toEqual([28, BELOW_A_PIN]);
    expect([name?.box.left, name?.box.top]).toEqual([128 - width / 2, 100 + BELOW_A_PIN]);
  });

  test("test_a_name_under_a_pin_near_the_edge_of_the_window_stands_as_near_under_it_as_leaves_it_whole", () => {
    // The window of the map is 248 px wide beside the answer, and a name is some 100: a pin
    // in three stands nearer its edge than half a name is wide.
    const { width } = roomFor("Foxholt", false);
    const under = (x: number) => named([pinned("1", "Foxholt", { x, y: 100 })], WINDOW, { ...PLATE, by: "pins" })[0];

    // With room at either hand its middle is under the point of its pin.
    expect(under(124)?.offset).toEqual([0, BELOW_A_PIN]);
    // Near an edge it stands against the edge, whole, and the pin is still over it.
    const right = under(230);
    expect([right?.box.left, right?.box.right]).toEqual([WINDOW.width - width, WINDOW.width]);
    expect(right?.offset[0]).toBeCloseTo(WINDOW.width - width / 2 - 230);
    expect(right?.offset[1]).toBe(BELOW_A_PIN);
    const left = under(20);
    expect([left?.box.left, left?.box.right]).toEqual([0, width]);
    // No further than keeps the whole of the pin over it: a name beside its pin is the name of no pin.
    const furthest = (width - PIN.width) / 2;
    expect(under(WINDOW.width - width / 2 + furthest)).toBeDefined();
    expect(under(WINDOW.width - width / 2 + furthest + 1)).toBeUndefined();
    expect(under(width / 2 - furthest - 1)).toBeUndefined();
    // A name with no pin lies over the middle of its area, or is not drawn.
    expect(named([area("a", "Foxholt", { x: 230, y: 100 })], WINDOW, { ...PLATE, by: "pins" })).toEqual([]);
  });

  test("test_a_pin_takes_the_room_of_its_drawing_at_two_pixels_of_the_screen_to_one_of_its_own", () => {
    expect(PIN).toEqual({ width: ART.pin.width * 2, height: ART.pin.height * 2 });
    expect(UNDER_A_PIN).toBe(PIN.height + BELOW_A_PIN);
  });

  test("test_a_name_is_given_more_room_where_the_type_of_the_page_was_made_larger_and_fewer_are_named", () => {
    const pair = [pinned("1", "Foxholt", { x: 80, y: 100 }), pinned("2", "Wexmoor", { x: 166, y: 100 })];

    expect(ids(named(pair, WINDOW, { drawn: "plate", larger: 1, by: "pins" }))).toEqual(["1", "2"]);
    expect(ids(named(pair, WINDOW, { drawn: "plate", larger: 1.5, by: "pins" }))).toEqual(["1"]);
  });
});
