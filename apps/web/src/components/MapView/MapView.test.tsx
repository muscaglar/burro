import { readFileSync } from "node:fs";
import path from "node:path";

import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { useState } from "react";

import { CARD } from "@/content/card";
import { COMPARE } from "@/content/compare";
import { LEGEND, MAP, MAP_CARD, TABLE } from "@/content/map";
import { COMPLETENESS, FILTERED, STRIP, UNRANKED } from "@/content/search";
import { BELOW_A_PIN, PIN, roomFor, whole, type Box } from "@/lib/map/labels";
import { PIN_ROOM } from "@/lib/map/pins";
import { boundsOf } from "@/lib/map/project";
import { recordedAnswer } from "@/lib/api/recorded";
import type { RankData, RankedArea } from "@/lib/api/schema";
import { ART } from "@/lib/art/names";
import { fillFor, fillForVibe, idsBy } from "@/lib/map/fill";
import { DRAWN, FINENESS, GRAIN_IMAGE, grainFilter, IMAGES, LAYER, ratioFor, SOURCE } from "@/lib/map/style";
import { paths } from "@/lib/paths";
import { HEAD } from "@/lib/sight";
import type { Lens } from "@/lib/vibes";

import { faultsIn } from "../../../test/support/axe";
import { isFor, rulesOf } from "../../../test/support/css";
import { lastMap, Map as StandIn, mapsMade } from "../../../test/support/maplibre";
import { ROUGH } from "../../../test/support/rough";
import { arrived, setWebGL } from "../../../test/support/search";
import { AreaTable } from "../AreaTable/AreaTable";
import { NO_PICTURE, picturesAtEnds } from "../kit/Ends/picture";
import { drawingOf } from "../kit/Thing/drawn";
import { MapView } from "./MapView";
import { NAMED, NAMES } from "./names";

const geometry = recordedAnswer("get_geometry", "geometry").body.data;
const areas = recordedAnswer("list_areas", "areas").body.data.areas;
const first = recordedAnswer("rank", "rank-first").body.data;
const refined = recordedAnswer("rank", "rank-refined").body.data;
const nameOf = (areaId: string) => areas.find((area) => area.area_id === areaId)?.name ?? "";
/** What a pin says: the rank, the name and the fit, and how much of what counts the fit rests on where that is not all of it. */
function pinName(area: RankedArea, ranking: RankData = first): string {
  const { counted = 0, present = 0 } = ranking.scores.find((score) => score.area_id === area.area_id) ?? {};
  const name = `Rank ${area.rank}, ${nameOf(area.area_id)}, fit ${Math.floor(area.score)} of 100`;
  return present === counted ? name : `${name}. ${COMPLETENESS.some(present, counted)}`;
}

interface Told {
  selected: (string | null)[];
  hovered: (string | null)[];
  shown: string[];
}

/** The map and its table, held together as the page holds them. */
function Held({ ranking, told, lens = null }: { ranking: RankData | null; told: Told; lens?: Lens | null }) {
  const [selectedId, setSelected] = useState<string | null>(null);
  const [hoveredId, setHovered] = useState<string | null>(null);
  const shared = {
    areas,
    scores: ranking?.scores ?? [],
    filtered: ranking?.filtered ?? [],
    unranked: ranking?.unranked ?? [],
    emptySpec: ranking?.empty_spec ?? false,
    selectedId,
    onSelect: (areaId: string | null) => {
      told.selected.push(areaId);
      setSelected(areaId);
    },
    onHover: (areaId: string | null) => {
      told.hovered.push(areaId);
      setHovered(areaId);
    },
  };
  return (
    <MapView
      {...shared}
      geometry={geometry}
      ranked={ranking?.ranked ?? []}
      hoveredId={hoveredId}
      onShowInList={(areaId) => told.shown.push(areaId)}
      lens={lens}
      table={<AreaTable {...shared} lens={lens} searched={ranking !== null} />}
    />
  );
}

async function show(ranking: RankData | null = first, lens: Lens | null = null) {
  const told: Told = { selected: [], hovered: [], shown: [] };
  const view = render(<Held ranking={ranking} told={told} lens={lens} />);
  await arrived();
  if (mapsMade().length > 0) act(() => lastMap().fire("load"));
  return { told, ...view, again: (next: RankData | null) => view.rerender(<Held ranking={next} told={told} />) };
}

const pins = () => [...lastMap().getCanvasContainer().querySelectorAll<HTMLButtonElement>("button")];
/** The names drawn on the map, each as the words it is drawn in. */
const names = () =>
  [...lastMap().getCanvasContainer().querySelectorAll<HTMLElement>("[data-label]")].map((label) =>
    [...label.children].map((line) => line.textContent).join(" "),
  );
/** Draws the map as near as `pixelsPerDegree` says, as zooming does. */
function zoomedTo(pixelsPerDegree: number) {
  lastMap().pixelsPerDegree = pixelsPerDegree;
  act(() => lastMap().fire("zoomend"));
}

describe("the map, where the browser can draw it", () => {
  beforeEach(() => setWebGL(true));
  afterEach(() => setWebGL(false));

  test("test_the_areas_are_drawn_from_the_apis_own_geometry_with_no_basemap", async () => {
    await show();

    const { style, attributionControl } = lastMap().options as {
      style: { sources: Record<string, { data: unknown }>; layers: { id: string }[]; glyphs?: string };
      attributionControl: unknown;
    };
    expect(mapsMade()).toHaveLength(1);
    expect(Object.keys(style.sources)).toEqual([SOURCE]);
    expect(style.sources[SOURCE]?.data).toBe(geometry);
    expect(style.glyphs).toBeUndefined();
    expect(JSON.stringify(style).includes("http")).toBe(false);
    expect(attributionControl).toBe(false);
  });

  test("test_each_area_is_coloured_by_the_band_of_its_fit_and_patterned_where_it_has_no_rank", async () => {
    await show(refined);

    const fills = idsBy(fillFor(refined.scores, refined.filtered, refined.unranked));
    const [, , colour] = lastMap().called("setPaintProperty").find(([layer]) => layer === LAYER.fill) ?? [];
    expect(JSON.stringify(colour)).toContain(JSON.stringify(fills.bands[4]));
    expect(lastMap().called("setFilter")).toEqual(
      expect.arrayContaining([
        [LAYER.filtered, ["in", ["get", "area_id"], ["literal", fills.patterns.filtered]]],
        [LAYER.unranked, ["in", ["get", "area_id"], ["literal", fills.patterns.unranked]]],
      ]),
    );
    expect([...lastMap().images].sort()).toEqual([...IMAGES].sort());
  });

  test("test_the_land_of_each_band_bears_its_grain_and_an_area_with_a_pattern_bears_none", async () => {
    await show(refined);

    const fills = fillFor(refined.scores, refined.filtered, refined.unranked);
    const [, , grain] = lastMap().called("setPaintProperty").find(([layer]) => layer === LAYER.grain) ?? [];
    // The areas of the fourth band bear the grain of the fourth band, and so with each.
    const drawn = grain as unknown[];
    expect(drawn[drawn.indexOf(GRAIN_IMAGE.land[4]) - 1]).toEqual(idsBy(fills).bands[4]);
    expect(drawn[drawn.length - 1]).toBe(GRAIN_IMAGE.land[0]);
    // Lines and dots each go with a reason that is given in words. Nothing is laid under them.
    expect(lastMap().called("setFilter")).toEqual(expect.arrayContaining([[LAYER.grain, grainFilter(fills)]]));
    // The water has its grain from the start: it is in the style the map was made with.
    const { style } = lastMap().options as { style: { layers: { id: string; paint?: Record<string, unknown> }[] } };
    expect(style.layers.find((layer) => layer.id === LAYER.water)?.paint).toMatchObject({
      "background-pattern": GRAIN_IMAGE.water,
    });
  });

  test("test_a_pixel_of_the_grain_is_of_one_size_however_near_the_map_is_drawn", async () => {
    // Seen in a browser: the map library draws a pattern larger the nearer the map is drawn,
    // by any amount from once to twice, and a pixel of the grain was then no whole number of
    // pixels of the screen. Each picture is handed over again once the map has been drawn
    // nearer or further, with how many of its pixels make one of the screen.
    await show();
    /** How large a pixel of a drawing comes out on the screen, for each picture as it was last handed over. */
    const onTheScreen = (zoom: number) =>
      IMAGES.map((name) => {
        const [, , options] = lastMap().called("addImage").findLast(([image]) => image === name) ?? [];
        return (FINENESS / ((options as { pixelRatio?: number } | undefined)?.pixelRatio ?? Number.NaN)) * 2 ** (zoom - Math.floor(zoom));
      });
    const zoomOfTheStandIn = (pixelsPerDegree: number) => Math.log2((pixelsPerDegree * 360) / 512);

    for (const size of onTheScreen(zoomOfTheStandIn(1_000))) expect(size).toBeCloseTo(2, 6);
    const handed = lastMap().called("addImage").length;

    zoomedTo(3_600);
    for (const size of onTheScreen(zoomOfTheStandIn(3_600))) expect(size).toBeCloseTo(2, 6);
    expect(lastMap().called("addImage")).toHaveLength(handed + IMAGES.length);
    expect([...lastMap().images].sort()).toEqual([...IMAGES].sort());
    expect(ratioFor({ zoom: zoomOfTheStandIn(3_600), pixel: 2 })).not.toBeCloseTo(ratioFor({ zoom: zoomOfTheStandIn(1_000), pixel: 2 }), 3);

    // Drawn as near as it was, nothing is handed over again.
    act(() => lastMap().fire("zoomend"));
    expect(lastMap().called("addImage")).toHaveLength(handed + IMAGES.length);
    // Twice as near, a pattern is drawn as it was: the part of the zoom that is over a whole number is the same.
    zoomedTo(7_200);
    expect(lastMap().called("addImage")).toHaveLength(handed + IMAGES.length);
  });

  test("test_the_pictures_are_handed_over_for_the_map_as_it_is_when_it_is_first_drawn", async () => {
    // A picture is asked for as soon as the style names it, which is before the map is
    // drawn. If the frame of the map changes size between the two, and the map with it, a
    // picture that was handed over for the map as it was would be drawn at the wrong size.
    const told: Told = { selected: [], hovered: [], shown: [] };
    render(<Held ranking={first} told={told} />);
    await arrived();
    const ratioAt = (pixelsPerDegree: number) => ratioFor({ zoom: Math.log2((pixelsPerDegree * 360) / 512), pixel: 2 });
    const handed = () => IMAGES.map((name) => (lastMap().called("addImage").findLast(([image]) => image === name)?.[2] as { pixelRatio?: number })?.pixelRatio);

    act(() => lastMap().fire("styleimagemissing"));
    expect(handed()).toEqual(IMAGES.map(() => ratioAt(1_000)));

    lastMap().pixelsPerDegree = 3_600;
    act(() => lastMap().fire("load"));

    expect(handed()).toEqual(IMAGES.map(() => ratioAt(3_600)));
    expect([...lastMap().images].sort()).toEqual([...IMAGES].sort());
  });

  test("test_the_first_ten_are_pinned_in_rank_order_and_each_pin_says_its_rank_name_and_fit", async () => {
    const { again } = await show();

    expect(pins().map((pin) => pin.textContent)).toEqual(["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]);
    expect(pins().map((pin) => pin.getAttribute("aria-label"))).toEqual(
      first.ranked.slice(0, 10).map((area) => pinName(area)),
    );
    expect(first.ranked[0]).toMatchObject({ area_id: "syn-n0006", score: 71.38 });
    expect(pins()[0]).toHaveAccessibleName("Rank 1, Farrowmere, fit 71 of 100");
    // A fit of 78.52 is said as 78, and never as 79.
    const [farrowmereFirst, ...rest] = first.ranked;
    if (farrowmereFirst === undefined) throw new Error("the recording ranks no area");
    again({ ...first, ranked: [{ ...farrowmereFirst, score: 78.52 }, ...rest] });
    await arrived();
    expect(pins()[0]).toHaveAccessibleName("Rank 1, Farrowmere, fit 78 of 100");
    // A pin stands at the centre of its area.
    const farrowmere = areas.find((area) => area.area_id === "syn-n0006");
    expect(lastMap().markers.filter((marker) => marker.element.tagName === "BUTTON")[0]?.position).toEqual(
      farrowmere?.centroid,
    );
    for (const pin of pins()) expect(pin).toHaveClass("target-min");
  });

  test("test_a_pin_is_a_drawing_that_stands_on_its_place_by_its_point_with_its_number_set_in_type", async () => {
    await show();
    const { width, height, face } = ART.pin;

    for (const pin of pins()) {
      // The drawing is named by where it is served, and its size and its face are counts of its own pixels.
      expect(pin.style.getPropertyValue("--art")).toBe('url("/art/pin.png")');
      expect(["--w", "--h"].map((name) => pin.style.getPropertyValue(name))).toEqual([String(width), String(height)]);
      expect(["--left", "--top", "--wide", "--high"].map((name) => pin.style.getPropertyValue(name))).toEqual(face.map(String));
      // The number is type, and is all the pin holds: no figure is drawn in a picture.
      expect([...pin.children].map((child) => [child.tagName, child.className, child.textContent])).toEqual([
        ["SPAN", "figure", pin.textContent],
      ]);
      expect(pin.querySelectorAll("img, svg")).toHaveLength(0);
    }
    // Its point is the middle of its foot, and that is where its place is.
    const markers = lastMap().markers.filter((marker) => marker.element.tagName === "BUTTON");
    expect(markers.map((marker) => marker.options.anchor)).toEqual(markers.map(() => "bottom"));
  });

  test("test_the_pins_follow_the_ranking_when_it_changes", async () => {
    const { again } = await show();

    again(refined);
    await arrived();

    expect(pins().map((pin) => pin.getAttribute("aria-label"))).toEqual(
      refined.ranked.slice(0, 10).map((area) => pinName(area, refined)),
    );
  });

  test("test_a_pin_and_the_card_say_when_a_fit_rests_on_part_of_what_counts", async () => {
    // Seen in a browser: an area ranked first on 4 of the 8 things that count had a pin
    // and a card that gave its fit with nothing beside it.
    await show();
    const part = COMPLETENESS.some(9, 10);

    // Recorded: the area ranked eighth has a figure for 9 of the 10 things that count.
    expect(pins()[7]).toHaveAccessibleName(`Rank 8, Alderwick, fit 59 of 100. ${part}`);
    fireEvent.click(pins()[7] as HTMLElement);
    const card = within(screen.getByRole("region", { name: MAP_CARD.label }));
    expect(card.getByText(part)).toBeInTheDocument();

    // One that has a figure for everything says so on its card, and its pin says nothing more.
    expect(pins()[0]).toHaveAccessibleName("Rank 1, Farrowmere, fit 71 of 100");
    fireEvent.click(pins()[0] as HTMLElement);
    expect(card.getByText(COMPLETENESS.all)).toBeInTheDocument();
  });

  test("test_a_pin_says_how_much_its_fit_rests_on_from_what_the_api_says_of_every_ranked_area", async () => {
    // The API counts it for every area it ranks. The website no longer works it out.
    const partial = { ...first, scores: first.scores.map((score) => ({ ...score, counted: 7, present: 3 })) };
    await show(partial);

    for (const pin of pins()) expect(pin.getAttribute("aria-label")).toContain(COMPLETENESS.some(3, 7));
  });

  test("test_a_pin_that_is_pressed_hands_the_focus_to_the_card_it_opened_and_says_that_it_is_open", async () => {
    // Seen in a browser: after a pin was pressed the focus was on nothing, because the map
    // takes the press for its own and the pin never took the focus. And seen by keyboard,
    // once it did: the card opened under the buttons of the map, seven stops on from the
    // pin, and nothing said so.
    await show();
    expect(pins().map((pin) => pin.getAttribute("aria-expanded"))).toEqual(pins().map(() => "false"));

    fireEvent.click(pins()[2] as HTMLElement);

    const card = screen.getByRole("region", { name: MAP_CARD.label });
    expect(card).toHaveFocus();
    // It is no stop of its own, and what it holds is the next stop of a keyboard.
    expect(card).toHaveAttribute("tabindex", "-1");
    // It is heard by its name and by what it says of the area: its name, and its rank and fit.
    expect(card).toHaveAccessibleDescription("Gorsebeck Rank 3, fit 66 of 100");
    // The pin says that its card is open, and which it is. No other pin says so.
    expect(pins()[2]).toHaveAttribute("aria-expanded", "true");
    expect(pins()[2]).toHaveAttribute("aria-controls", card.id);
    expect(pins().filter((pin) => pin.getAttribute("aria-expanded") === "true")).toHaveLength(1);
  });

  test("test_a_press_on_a_pin_moves_the_page_nowhere", async () => {
    // Seen on a phone: the page scrolled to bring the result of the area into sight in the
    // list, so the pin went 411 px from under the finger, and the card of the map, with
    // "Show in the list", was left under the window. Here the card opens in sight.
    const moved: unknown[] = [];
    const scroll = jest.spyOn(window, "scrollBy").mockImplementation(((x: number, y: number) => {
      moved.push([x, y]);
    }) as typeof window.scrollBy);
    Element.prototype.scrollIntoView = function scrollIntoView() {
      moved.push(this);
    };
    const measure = jest.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function (
      this: HTMLElement,
    ) {
      const [top, foot] = this.tagName === "BUTTON" ? [306, 338] : this.tagName === "SECTION" ? [560, 850] : [0, 0];
      return { top, bottom: foot, left: 0, right: 0, x: 0, y: top, width: 0, height: foot - top, toJSON: () => ({}) };
    });
    const high = window.innerHeight;
    Object.defineProperty(window, "innerHeight", { configurable: true, value: 844 });
    try {
      const { told } = await show();

      fireEvent.click(pins()[0] as HTMLElement);

      expect(screen.getByRole("region", { name: MAP_CARD.label })).toHaveFocus();
      expect(moved).toEqual([]);
      // It is the card's own button that takes a person to the result.
      expect(told.shown).toEqual([]);
      fireEvent.click(screen.getByRole("button", { name: MAP_CARD.showInList }));
      expect(told.shown).toEqual(["syn-n0006"]);
    } finally {
      scroll.mockRestore();
      measure.mockRestore();
      Object.defineProperty(window, "innerHeight", { configurable: true, value: high });
      delete (Element.prototype as { scrollIntoView?: unknown }).scrollIntoView;
    }
  });

  test("test_a_card_that_opens_under_the_foot_of_the_window_is_brought_up_by_its_head_and_no_further", async () => {
    const moved: number[] = [];
    const scroll = jest.spyOn(window, "scrollBy").mockImplementation(((_: number, y: number) => {
      moved.push(y);
    }) as typeof window.scrollBy);
    const measure = jest.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function (
      this: HTMLElement,
    ) {
      const [top, foot] = this.tagName === "BUTTON" ? [700, 732] : this.tagName === "SECTION" ? [830, 1120] : [0, 0];
      return { top, bottom: foot, left: 0, right: 0, x: 0, y: top, width: 0, height: foot - top, toJSON: () => ({}) };
    });
    const high = window.innerHeight;
    Object.defineProperty(window, "innerHeight", { configurable: true, value: 844 });
    try {
      await show();

      fireEvent.click(pins()[0] as HTMLElement);

      expect(moved).toEqual([830 + HEAD - 844]);
    } finally {
      scroll.mockRestore();
      measure.mockRestore();
      Object.defineProperty(window, "innerHeight", { configurable: true, value: high });
    }
  });

  test("test_the_pin_of_the_card_that_is_open_gives_the_card_the_focus_again_and_chooses_nothing_anew", async () => {
    const { told } = await show();
    fireEvent.click(pins()[1] as HTMLElement);
    const card = screen.getByRole("region", { name: MAP_CARD.label });
    act(() => (pins()[1] as HTMLElement).focus());
    expect(card).not.toHaveFocus();

    fireEvent.click(pins()[1] as HTMLElement);

    expect(screen.getByRole("region", { name: MAP_CARD.label })).toBe(card);
    expect(card).toHaveFocus();
    expect(told.selected).toEqual([first.ranked[1]?.area_id]);
    // An area that is chosen in the list after that leaves the focus where it was pressed.
    const held = document.createElement("button");
    document.body.append(held);
    try {
      act(() => held.focus());
      act(() => lastMap().fire("click", { features: [{ id: first.ranked[2]?.area_id }] }, LAYER.fill));
      expect(screen.getByRole("region", { name: MAP_CARD.label })).toHaveFocus();
    } finally {
      held.remove();
    }
  });

  test("test_escape_closes_the_card_from_inside_it_and_the_focus_goes_back_to_the_pin", async () => {
    await show();
    fireEvent.click(pins()[1] as HTMLElement);
    const card = screen.getByRole("region", { name: MAP_CARD.label });

    fireEvent.keyDown(within(card).getByRole("button", { name: MAP_CARD.showInList }), { key: "Escape" });

    expect(screen.queryByRole("region", { name: MAP_CARD.label })).toBeNull();
    expect(pins()[1]).toHaveFocus();
    expect(pins()[1]).toHaveAttribute("aria-expanded", "false");
  });

  test("test_an_area_chosen_in_the_list_opens_its_card_and_leaves_the_focus_where_it_was_pressed", async () => {
    // "Show on the map" is pressed on a result: the focus stays on that button.
    const told: Told = { selected: [], hovered: [], shown: [] };
    const held = document.createElement("button");
    document.body.append(held);
    const shown = (selectedId: string | null) => (
      <MapView
        geometry={geometry}
        areas={areas}
        scores={first.scores}
        ranked={first.ranked}
        filtered={first.filtered}
        unranked={first.unranked}
        selectedId={selectedId}
        hoveredId={null}
        onSelect={(areaId) => told.selected.push(areaId)}
        onHover={() => undefined}
        onShowInList={() => undefined}
        table={<p>the table</p>}
      />
    );
    try {
      const { rerender } = render(shown(null));
      await arrived();
      act(() => lastMap().fire("load"));
      act(() => held.focus());

      rerender(shown("syn-n0006"));

      expect(screen.getByRole("region", { name: MAP_CARD.label })).toBeInTheDocument();
      expect(held).toHaveFocus();
      expect(pins()[0]).toHaveAttribute("aria-expanded", "true");
    } finally {
      held.remove();
    }
  });

  test("test_a_pin_that_has_left_the_window_of_the_map_is_brought_back_into_it_as_it_takes_the_focus", async () => {
    // Seen by keyboard, once the map had been moved by the arrow keys: a pin that had left
    // its window still took the focus, and no pin and no ring was in sight.
    const wide = jest.spyOn(HTMLElement.prototype, "clientWidth", "get").mockReturnValue(358);
    const tall = jest.spyOn(HTMLElement.prototype, "clientHeight", "get").mockReturnValue(300);
    try {
      await show();
      const map = lastMap();
      const at = { x: 100, y: 100 };
      map.project = () => at;

      fireEvent.focus(pins()[0] as HTMLElement);
      expect(map.called("panTo")).toEqual([]);

      at.x = 400;
      fireEvent.focus(pins()[1] as HTMLElement);
      const [to] = map.called("panTo").at(-1) ?? [];
      expect(to).toEqual(areas.find((area) => area.area_id === first.ranked[1]?.area_id)?.centroid);
      at.x = 100;
      at.y = -4;
      fireEvent.focus(pins()[2] as HTMLElement);
      expect(map.called("panTo")).toHaveLength(2);
    } finally {
      wide.mockRestore();
      tall.mockRestore();
    }
  });

  test("test_closing_the_card_of_an_area_puts_the_focus_back_on_its_pin", async () => {
    await show();
    fireEvent.click(pins()[0] as HTMLElement);
    const close = screen.getByRole("button", { name: MAP_CARD.close });
    act(() => close.focus());

    fireEvent.click(close);

    expect(screen.queryByRole("region", { name: MAP_CARD.label })).toBeNull();
    expect(document.activeElement).toBe(pins()[0]);
  });

  test("test_closing_the_card_of_an_area_with_no_pin_puts_the_focus_on_the_map", async () => {
    await show(refined);
    const [left] = refined.filtered;
    act(() => lastMap().fire("click", { features: [{ id: left?.area_id }] }, LAYER.fill));
    const close = screen.getByRole("button", { name: MAP_CARD.close });
    act(() => close.focus());

    fireEvent.click(close);

    expect(document.activeElement).toBe(lastMap().getCanvas());
  });

  test("test_pressing_a_pin_chooses_its_area_and_the_map_says_what_it_is_in_words", async () => {
    const { told } = await show();

    fireEvent.click(pins()[2] as HTMLElement);

    expect(told.selected).toEqual(["syn-n0008"]);
    const card = within(screen.getByRole("region", { name: MAP_CARD.label }));
    expect(card.getByText("Gorsebeck")).toBeInTheDocument();
    expect(card.getByText("Rank 3, fit 66 of 100")).toBeInTheDocument();
    expect(pins()[2]).toHaveAttribute("aria-current", "true");
    expect(pins().filter((pin) => pin.hasAttribute("aria-current"))).toHaveLength(1);
    // Its area is outlined as the one that is chosen. The focus has gone on to the card, so
    // it is outlined no longer as the one under the focus.
    expect(lastMap().states.get("syn-n0008")).toEqual({ hovered: false, selected: true });
  });

  test("test_pressing_an_area_on_the_map_chooses_it_and_an_area_with_no_rank_says_why", async () => {
    const { told } = await show(refined);
    const [left] = refined.filtered;
    if (!left) throw new Error("the recording leaves no area out");

    act(() => lastMap().fire("click", { features: [{ id: left.area_id }] }, LAYER.fill));

    expect(told.selected).toEqual([left.area_id]);
    const card = within(screen.getByRole("region", { name: MAP_CARD.label }));
    expect(card.getByText(nameOf(left.area_id))).toBeInTheDocument();
    expect(card.getByText(FILTERED[left.reason])).toBeInTheDocument();
    expect(card.queryByRole("button", { name: MAP_CARD.showInList })).toBeNull();

    act(() => lastMap().fire("click", { features: [{ id: "syn-n0009" }] }, LAYER.fill));
    expect(card.getByText(UNRANKED.not_rankable)).toBeInTheDocument();
  });

  test("test_the_card_of_an_area_leads_to_its_page_in_one_press_and_puts_it_in_the_tray", async () => {
    // Seen in a browser: pressing an area gave its name, its borough and "Close". There was
    // no way from there to its page, nor to a comparison.
    await show();
    const [top] = first.ranked;
    const area = areas.find((one) => one.area_id === top?.area_id);
    if (!area) throw new Error("the recording ranks no area the page knows");

    fireEvent.click(screen.getByRole("button", { name: pinName(top as RankedArea) }));
    const card = within(screen.getByRole("region", { name: MAP_CARD.label }));

    const link = card.getByRole("link", { name: area.name });
    expect(link).toHaveAttribute("href", paths.area(area));
    // Which page a person reads next is told to no server ahead of time.
    expect(link).toHaveAttribute("data-prefetch", "false");
    expect(card.getByRole("button", { name: COMPARE.addNamed(area.name) })).toBeInTheDocument();
  });

  test("test_before_a_search_the_card_of_an_area_leads_to_its_page_too", async () => {
    await show(null);
    const area = areas.find((one) => one.rankable);
    if (!area) throw new Error("the recording holds no area");

    act(() => lastMap().fire("click", { features: [{ id: area.area_id }] }, LAYER.fill));

    const card = within(screen.getByRole("region", { name: MAP_CARD.label }));
    expect(card.getByRole("link", { name: area.name })).toHaveAttribute("href", paths.area(area));
  });

  test("test_an_area_is_named_on_the_map_where_there_is_room_for_its_name", async () => {
    // Seen by a newcomer: the map was shapes and numbered pins, with no name on it.
    await show(null);

    // Drawn small, no area has room for its name, and none is named.
    expect(names()).toEqual([]);
    // Drawn large, every area is named, by the name the release gives it.
    zoomedTo(10_000);
    expect([...names()].sort()).toEqual(areas.map((area) => area.name).sort());
    // Between the two, the areas that have room are named and the others are not.
    zoomedTo(3_600);
    expect(names().length).toBeGreaterThan(0);
    expect(names().length).toBeLessThan(areas.length);
    // Drawn small again, the names go.
    zoomedTo(1_000);
    expect(names()).toEqual([]);
  });

  test("test_a_name_stands_at_the_centre_of_its_area_and_under_its_pin_where_it_has_one", async () => {
    await show();
    zoomedTo(10_000);
    const labelOf = (name: string) =>
      lastMap().markers.find((marker) => "label" in marker.element.dataset && marker.element.textContent === name.replace(/ /g, ""));
    const pinned = areas.find((area) => area.area_id === first.ranked[1]?.area_id);
    const bare = areas.find((area) => first.ranked.slice(0, 10).every((one) => one.area_id !== area.area_id));
    if (!pinned || !bare) throw new Error("the recording holds no such areas");

    expect(labelOf(pinned.name)?.position).toEqual(pinned.centroid);
    expect(labelOf(pinned.name)?.options).toMatchObject({ anchor: "top" });
    expect(labelOf(pinned.name)?.options.offset?.[1]).toBeGreaterThan(0);
    expect(labelOf(bare.name)?.position).toEqual(bare.centroid);
    expect(labelOf(bare.name)?.options).toMatchObject({ anchor: "center" });
  });

  test("test_a_name_on_the_map_takes_no_press_and_covers_no_area", async () => {
    await show();
    zoomedTo(10_000);
    const labels = [...lastMap().getCanvasContainer().querySelectorAll<HTMLElement>("[data-label]")];
    const rules = rulesOf(readFileSync(path.join(__dirname, "MapView.module.css"), "utf8"));

    expect(labels.length).toBe(areas.length);
    // It is no button and no link, and the pointer goes through it to the area under it. The
    // map library says of whatever it is handed that it is a button named "Map marker".
    expect(labels.filter((label) => label.matches("button, a, [tabindex], [role], [aria-label]")).length).toBe(0);
    expect(rules.filter((rule) => isFor(rule.selector, "label")).map((rule) => rule.sets.get("pointer-events"))).toContain("none");
    // The names are in the table, and on the pins, for whoever hears the page. These are for the eye.
    expect(labels.every((label) => label.getAttribute("aria-hidden") === "true")).toBe(true);
    // A pin is still found by its area, and a name is never taken for one.
    expect(labels.filter((label) => "area" in label.dataset)).toEqual([]);
    expect(pins()).toHaveLength(10);
  });

  test("test_every_name_on_the_map_is_a_name_of_the_release_and_nothing_is_fetched_for_it", async () => {
    await show();
    zoomedTo(10_000);

    // Names and places are the release's alone: no basemap, no glyphs, no host.
    const known = new Set(areas.map((area) => area.name));
    expect(names().filter((name) => !known.has(name))).toEqual([]);
    const style = lastMap().options.style as { glyphs?: unknown; sprite?: unknown; sources: Record<string, unknown> };
    expect([style.glyphs, style.sprite]).toEqual([undefined, undefined]);
    expect(Object.keys(style.sources)).toEqual([SOURCE]);
  });

  test("test_the_names_are_taken_down_with_the_map", async () => {
    const { unmount } = await show();
    zoomedTo(10_000);
    const map = lastMap();
    expect(map.markers.length).toBeGreaterThan(10);

    unmount();

    expect(map.markers).toEqual([]);
  });

  test("test_the_area_under_the_pointer_is_outlined_and_the_outline_goes_when_it_leaves", async () => {
    const { told } = await show();

    act(() => lastMap().fire("mousemove", { features: [{ id: "syn-n0006" }] }, LAYER.fill));
    expect(lastMap().states.get("syn-n0006")).toEqual({ hovered: true });
    act(() => lastMap().fire("mousemove", { features: [{ id: "syn-n0003" }] }, LAYER.fill));
    expect(lastMap().states.get("syn-n0006")).toEqual({ hovered: false });
    expect(lastMap().states.get("syn-n0003")).toEqual({ hovered: true });
    act(() => lastMap().fire("mouseleave", {}, LAYER.fill));

    expect(lastMap().states.get("syn-n0003")).toEqual({ hovered: false });
    expect(told.hovered).toEqual(["syn-n0006", "syn-n0003", null]);
  });

  test("test_an_area_too_little_is_known_of_says_so_in_words_and_gives_no_fit", async () => {
    await show();
    const apart = first.unranked.find((area) => area.reason === "insufficient_data");
    if (!apart) throw new Error("the recording places every area");

    act(() => lastMap().fire("click", { features: [{ id: apart.area_id }] }, LAYER.fill));

    const card = screen.getByRole("region", { name: MAP_CARD.label });
    expect(within(card).getByText("Otterby Fields")).toBeInTheDocument();
    expect(within(card).getByText(UNRANKED.insufficient_data)).toBeInTheDocument();
    // It has no rank and no fit, and no line of the card is left empty.
    expect(/Rank \d|fit \d/.test(card.textContent ?? "")).toBe(false);
    expect([...card.querySelectorAll("p")].filter((line) => line.textContent === "")).toEqual([]);
  });

  test("test_a_pin_that_takes_the_focus_outlines_its_area", async () => {
    await show();

    act(() => pins()[0]?.focus());
    expect(lastMap().states.get("syn-n0006")).toEqual({ hovered: true });
    act(() => pins()[0]?.blur());
    expect(lastMap().states.get("syn-n0006")).toEqual({ hovered: false });
  });

  test("test_show_in_the_list_is_offered_for_an_area_that_is_in_the_list", async () => {
    const { told } = await show();

    fireEvent.click(pins()[0] as HTMLElement);
    fireEvent.click(screen.getByRole("button", { name: MAP_CARD.showInList }));
    expect(told.shown).toEqual(["syn-n0006"]);

    fireEvent.click(screen.getByRole("button", { name: MAP_CARD.close }));
    expect(screen.queryByRole("region", { name: MAP_CARD.label })).toBeNull();
    expect(lastMap().states.get("syn-n0006")).toMatchObject({ selected: false });
  });

  test("test_nothing_pans_unless_the_chosen_area_is_off_screen", async () => {
    await show();

    fireEvent.click(pins()[0] as HTMLElement);
    expect(lastMap().called("panTo")).toEqual([]);

    lastMap().view = { contains: () => false };
    fireEvent.click(pins()[1] as HTMLElement);
    const otterby = areas.find((area) => area.area_id === first.ranked[1]?.area_id);
    expect(lastMap().called("panTo")).toEqual([[otterby?.centroid, { animate: true }]]);
  });

  test("test_the_map_is_fitted_again_when_its_frame_changes_size", async () => {
    // Seen in a browser: the map was drawn at the width of a desk, the window was made as
    // narrow as a phone, and four of the ten pins were outside the frame. The map keeps its
    // centre when its frame changes size. While the person has not moved it, it is fitted
    // to the frame again.
    await show();
    expect(lastMap().called("fitBounds")).toEqual([]);

    act(() => lastMap().fire("resize"));

    const fitted = lastMap().called("fitBounds");
    expect(fitted).toHaveLength(1);
    expect(fitted[0]?.[0]).toEqual((lastMap().options as { bounds: unknown }).bounds);
    expect(fitted[0]?.[1]).toMatchObject({ animate: false });
  });

  test("test_a_map_the_person_has_moved_is_left_where_they_put_it_when_its_frame_changes_size", async () => {
    await show();
    const controls = within(screen.getByRole("group", { name: MAP.controls }));

    // Dragged, or moved with the keys: the map says that a person did it.
    act(() => lastMap().fire("movestart", { originalEvent: new Event("mousedown") }));
    act(() => lastMap().fire("resize"));
    expect(lastMap().called("fitBounds")).toEqual([]);

    // "Show every area" fits it, and it is the page's to fit again from then on.
    fireEvent.click(controls.getByRole("button", { name: MAP.whole }));
    act(() => lastMap().fire("resize"));
    expect(lastMap().called("fitBounds")).toHaveLength(2);

    // Moved with a button, it is the person's again.
    fireEvent.click(controls.getByRole("button", { name: MAP.zoomIn }));
    act(() => lastMap().fire("resize"));
    expect(lastMap().called("fitBounds")).toHaveLength(2);
  });

  test("test_a_map_that_the_page_moved_is_still_the_pages_to_fit", async () => {
    await show();

    // The page pans to an area that is chosen: nobody moved the map by hand.
    act(() => lastMap().fire("movestart", {}));
    act(() => lastMap().fire("resize"));

    expect(lastMap().called("fitBounds")).toHaveLength(1);
  });

  test("test_the_map_has_buttons_to_zoom_and_to_show_the_whole_city", async () => {
    await show();
    const controls = within(screen.getByRole("group", { name: MAP.controls }));

    fireEvent.click(controls.getByRole("button", { name: MAP.zoomIn }));
    fireEvent.click(controls.getByRole("button", { name: MAP.zoomOut }));
    fireEvent.click(controls.getByRole("button", { name: MAP.whole }));

    expect(lastMap().called("zoomIn")).toHaveLength(1);
    expect(lastMap().called("zoomOut")).toHaveLength(1);
    expect(lastMap().called("fitBounds")).toHaveLength(1);
    // Each is a native button of the size of a main control, drawn as the look draws a button.
    for (const button of controls.getAllByRole("button")) {
      expect(button.tagName).toBe("BUTTON");
      expect(button).toHaveClass("target");
      expect(button.firstElementChild).toHaveClass("face");
    }
    // Nearer and further bear a sign, which is drawn and says nothing: the name of the button says what it does.
    const [nearer, further, whole] = controls.getAllByRole("button");
    expect([nearer, further].map((button) => [button?.getAttribute("aria-label"), button?.textContent])).toEqual([
      [MAP.zoomIn, ""],
      [MAP.zoomOut, ""],
    ]);
    expect([nearer, further].map((button) => button?.querySelector("[data-sign]")?.getAttribute("aria-hidden"))).toEqual(["true", "true"]);
    expect(whole).toHaveTextContent(MAP.whole);
  });

  test("test_until_the_map_is_drawn_a_button_that_moves_it_says_it_is_off_and_does_nothing", async () => {
    const told: Told = { selected: [], hovered: [], shown: [] };
    render(<Held ranking={first} told={told} />);
    await arrived();
    const controls = within(screen.getByRole("group", { name: MAP.controls }));
    const buttons = controls.getAllByRole("button");

    // It is off and not switched off, so that it keeps the focus if it has it.
    for (const button of buttons) {
      expect(button).toHaveAttribute("aria-disabled", "true");
      expect(button).not.toBeDisabled();
      fireEvent.click(button);
    }
    expect(["zoomIn", "zoomOut", "fitBounds"].flatMap((method) => lastMap().called(method))).toEqual([]);

    act(() => lastMap().fire("load"));
    for (const button of controls.getAllByRole("button")) expect(button).not.toHaveAttribute("aria-disabled");
  });

  test("test_no_button_is_laid_over_the_map_where_it_would_cover_an_area", async () => {
    const { container } = await show();
    // The frame is what the map is drawn in: the element that holds it, and what is laid over it.
    const frame = lastMap().getCanvas().closest("[data-ready]")?.parentElement as HTMLElement;
    const controls = screen.getByRole("group", { name: MAP.controls });

    // Seen in a browser: "Show every area" sat over the top right of the map and hid an area.
    expect(frame.contains(controls)).toBe(false);
    expect(container.contains(controls)).toBe(true);
    // Pins are the only buttons on the map, and each stands for the area it is on.
    expect([...frame.querySelectorAll("button")]).toEqual(pins());
    // The buttons come after the map, so that the keyboard reaches them once the map is left.
    expect(frame.compareDocumentPosition(controls) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  test("test_the_map_itself_has_a_name_and_says_which_keys_move_it", async () => {
    await show();

    const canvas = lastMap().getCanvas();
    expect(canvas).toHaveAccessibleName(MAP.label);
    expect(canvas).toHaveAccessibleDescription(MAP.keys);
    // The keys are said where a person who sees the page can read them as well.
    expect(screen.getByText(MAP.keys).closest(".visually-hidden, [aria-hidden='true'], [hidden]")).toBeNull();
    expect(canvas.tabIndex).toBe(0);
    expect(lastMap().options).toMatchObject({ dragRotate: false, pitchWithRotate: false });
    expect(lastMap().options).not.toHaveProperty("keyboard", false);
  });

  test("test_the_legend_gives_each_band_in_figures_and_each_pattern_in_words", async () => {
    await show(refined);

    const legend = within(screen.getByRole("region", { name: LEGEND.title }));
    expect(legend.getAllByRole("listitem").map((item) => item.textContent)).toEqual([
      "Fit 80 to 100",
      "Fit 60 to 79",
      "Fit 40 to 59",
      "Fit 20 to 39",
      "Fit 0 to 19",
      LEGEND.filtered,
      LEGEND.unranked,
      `1${LEGEND.pin}`,
    ]);
  });

  test("test_pins_whose_areas_are_too_near_are_drawn_beside_each_other_and_not_on_top", async () => {
    // Seen in a browser, on a map of a thousand areas: the pins of areas that are next to
    // each other stood on top of each other, and their numbers could not be read.
    await show();
    const moved = () => pins().filter((pin) => pin.hasAttribute("data-moved")).map((pin) => pin.textContent);
    /** Where each pin is drawn on the screen: where its area is, and how far it was moved. */
    const drawn = () =>
      lastMap()
        .markers.filter((marker) => marker.element.tagName === "BUTTON")
        .map((marker) => {
          const at = lastMap().project(marker.position ?? [0, 0]);
          return [at.x + marker.offset[0], at.y + marker.offset[1]] as const;
        });

    // Seen from so far off that every pin would stand on the first, each is moved but the first.
    zoomedTo(1);
    expect(moved()).toEqual(pins().slice(1).map((pin) => pin.textContent));
    for (const [at, one] of drawn().entries()) {
      for (const other of drawn().slice(at + 1)) {
        expect(Math.hypot(one[0] - other[0], one[1] - other[1])).toBeGreaterThanOrEqual(PIN_ROOM);
      }
    }
    // Drawn near enough that each has room, every pin stands where its area is.
    zoomedTo(100_000);
    expect(moved()).toEqual([]);
  });

  test("test_the_legend_speaks_of_a_limit_only_where_a_limit_left_an_area_out", async () => {
    // Seen in a browser: "Left out by a limit you set", under a map of a search that set none.
    await show({ ...first, filtered: [], unranked: [] });

    const legend = within(screen.getByRole("region", { name: LEGEND.title }));
    const said = legend.getAllByRole("listitem").map((item) => item.textContent);
    expect(said).not.toContain(LEGEND.filtered);
    expect(said).not.toContain(LEGEND.unranked);
    expect(said).toContain(`1${LEGEND.pin}`);
  });

  test("test_before_a_search_every_area_is_one_plain_colour_with_no_pin", async () => {
    await show(null);

    expect(pins()).toEqual([]);
    const [, , colour] = lastMap().called("setPaintProperty").find(([layer]) => layer === LAYER.fill) ?? [];
    expect(typeof colour).toBe("string");
    expect(within(screen.getByRole("region", { name: LEGEND.title })).getByText(LEGEND.noScore)).toBeInTheDocument();
  });

  test("test_the_map_is_taken_down_when_the_page_is_left", async () => {
    const { unmount } = await show();
    const map = lastMap();

    unmount();

    expect(map.removed).toBe(true);
  });

  test("test_the_map_with_a_ranking_has_no_accessibility_fault", async () => {
    const { container } = await show(refined);
    fireEvent.click(pins()[0] as HTMLElement);

    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("the names on the map, in the window the map is seen through", () => {
  // The window of the map beside the answer, measured at 1440 by 900.
  const WINDOW = { width: 248, height: 240 };
  // How near the whole city is drawn in it, with the room that is kept round the areas.
  const WHOLE_CITY = 1_500;

  beforeEach(() => setWebGL(true));
  afterEach(() => setWebGL(false));

  /**
   * Lays the map out as a browser does: its window has a size, and the middle of what it
   * shows is the middle of the window. `moved` is how far the map was moved by hand, in pixels.
   */
  function seenThrough(pixelsPerDegree: number, moved: readonly [number, number] = [0, 0]) {
    const map = lastMap();
    const bounds = boundsOf(geometry);
    if (bounds === null) throw new Error("the recording holds no area");
    const [[west, south], [east, north]] = bounds;
    const middle = [(west + east) / 2, (south + north) / 2] as const;
    for (const [side, size] of [["clientWidth", WINDOW.width], ["clientHeight", WINDOW.height]] as const) {
      Object.defineProperty(map.getContainer(), side, { configurable: true, value: size });
    }
    map.pixelsPerDegree = pixelsPerDegree;
    map.project = ([longitude, latitude]: readonly [number, number]) => ({
      x: WINDOW.width / 2 + (longitude - middle[0]) * pixelsPerDegree + moved[0],
      y: WINDOW.height / 2 - (latitude - middle[1]) * pixelsPerDegree + moved[1],
    });
  }
  const labels = () =>
    lastMap().markers.filter((marker) => "label" in marker.element.dataset);
  const nameOn = (marker: ReturnType<typeof labels>[number]) =>
    [...marker.element.children].map((line) => line.textContent).join(" ");
  /** What a name takes in the window, from where it is tied, how far from it, and by which of its sides. */
  function boxOf(marker: ReturnType<typeof labels>[number]): Box {
    const at = lastMap().project(marker.position ?? [0, 0]);
    const [x, y] = [at.x + (marker.options.offset?.[0] ?? 0), at.y + (marker.options.offset?.[1] ?? 0)];
    const { width, height } = roomFor(nameOn(marker), false, NAMES);
    return marker.options.anchor === "top"
      ? { left: x - width / 2, top: y, right: x + width / 2, bottom: y + height }
      : { left: x - width / 2, top: y - height / 2, right: x + width / 2, bottom: y + height / 2 };
  }
  const inTheWindow = ({ x, y }: { x: number; y: number }) => x > 0 && x < WINDOW.width && y > 0 && y < WINDOW.height;

  test("test_no_name_is_cut_by_the_edge_of_the_window_of_the_map", async () => {
    // Seen in a browser, at 1440 by 900 with the map drawn nearer: "Larkspur Hill" stood
    // from 67 px left of the window, and "Otterby Fields" ran 58 px past its right edge.
    await show(null);
    seenThrough(6_000, [45, 0]);
    act(() => lastMap().fire("zoomend"));

    expect(labels().length).toBeGreaterThan(0);
    expect(labels().filter((marker) => !whole(boxOf(marker), WINDOW)).map(nameOn)).toEqual([]);
    // An area whose middle is in the window, and whose name would not all be, is not named.
    const named = new Set(labels().map(nameOn));
    const left = areas.filter((area) => inTheWindow(lastMap().project(area.centroid)) && !named.has(area.name));
    expect(left.length).toBeGreaterThan(0);
  });

  test("test_the_names_are_worked_out_again_once_the_map_has_been_moved", async () => {
    await show(null);
    seenThrough(6_000);
    act(() => lastMap().fire("zoomend"));
    const before = labels().map(nameOn).sort();

    // The map is moved by hand, by more than an area is wide.
    seenThrough(6_000, [-200, 0]);
    act(() => lastMap().fire("moveend"));

    expect(labels().length).toBeGreaterThan(0);
    expect(labels().map(nameOn).sort()).not.toEqual(before);
    expect(labels().filter((marker) => !whole(boxOf(marker), WINDOW)).map(nameOn)).toEqual([]);
  });

  test("test_while_the_map_is_moved_a_name_that_comes_to_the_edge_is_not_drawn_cut", async () => {
    await show(null);
    seenThrough(6_000);
    act(() => lastMap().fire("zoomend"));
    const drawn = labels();
    expect(drawn.filter((marker) => marker.element.hasAttribute("data-cut"))).toEqual([]);

    // Under way: the names are where they were on the ground, and the ground has moved.
    seenThrough(6_000, [-60, 0]);
    act(() => lastMap().fire("move"));

    expect(labels()).toEqual(drawn);
    const cut = drawn.filter((marker) => marker.element.hasAttribute("data-cut"));
    expect(cut.length).toBeGreaterThan(0);
    expect(cut.length).toBeLessThan(drawn.length);
    expect(cut.map(nameOn).sort()).toEqual(drawn.filter((marker) => !whole(boxOf(marker), WINDOW)).map(nameOn).sort());
    // What is not drawn keeps its place, and is drawn again if the map is moved back.
    seenThrough(6_000);
    act(() => lastMap().fire("move"));
    expect(drawn.filter((marker) => marker.element.hasAttribute("data-cut"))).toEqual([]);
    const rules = rulesOf(readFileSync(path.join(__dirname, "MapView.module.css"), "utf8"));
    expect(rules.filter((rule) => rule.selector === ".label[data-cut]").map((rule) => [...rule.sets])).toEqual([
      [["visibility", "hidden"]],
    ]);
  });

  test("test_as_the_map_is_first_drawn_it_names_the_first_ten_under_their_pins_where_they_have_room", async () => {
    // Seen in a browser, at 1440 by 900: the map named no area as it was first drawn. The
    // whole city is some 200 px wide there, and no area has room for the whole of its name.
    await show();
    seenThrough(WHOLE_CITY);
    act(() => lastMap().fire("zoomend"));
    const pinned = first.ranked.slice(0, 10).map((area) => nameOf(area.area_id));

    if (NAMED === "room") {
      expect(labels()).toEqual([]);
      return;
    }
    expect(labels().length).toBeGreaterThan(0);
    // Each is the name of one of the first ten, and stands under its pin, clear of its point.
    expect(labels().map(nameOn).filter((name) => !pinned.includes(name))).toEqual([]);
    expect(labels().filter((marker) => marker.options.anchor !== "top" || marker.options.offset?.[1] !== BELOW_A_PIN)).toEqual([]);
    // None is cut, none lies over another, and none lies over a pin.
    const boxes = labels().map(boxOf);
    const over = (one: Box, other: Box) =>
      one.left < other.right && other.left < one.right && one.top < other.bottom && other.top < one.bottom;
    expect(boxes.filter((box) => !whole(box, WINDOW))).toEqual([]);
    for (const [at, one] of boxes.entries()) {
      expect(boxes.filter((other, to) => to !== at && over(one, other))).toEqual([]);
      for (const marker of lastMap().markers.filter((made) => made.element.tagName === "BUTTON")) {
        const point = lastMap().project(marker.position ?? [0, 0]);
        const [x, y] = [point.x + marker.offset[0], point.y + marker.offset[1]];
        expect(over(one, { left: x - PIN.width / 2, top: y - PIN.height, right: x + PIN.width / 2, bottom: y })).toBe(false);
      }
    }
  });

  test("test_before_a_search_a_map_that_holds_the_whole_city_names_no_area_whose_own_area_has_no_room", async () => {
    await show(null);
    seenThrough(WHOLE_CITY);
    act(() => lastMap().fire("zoomend"));

    expect(labels()).toEqual([]);
  });

  test("test_the_name_of_an_area_whose_pin_was_moved_off_it_stands_under_the_pin", async () => {
    await show();
    // From so far off that every pin but the first is moved, in a window with room for one name.
    seenThrough(1);
    act(() => lastMap().fire("zoomend"));
    if (NAMED === "room") return;

    for (const marker of labels()) {
      const area = areas.find((one) => one.name === nameOn(marker));
      const pin = lastMap().markers.find((made) => made.element.dataset.area === area?.area_id);
      expect(marker.options.offset).toEqual([pin?.offset[0], (pin?.offset[1] ?? 0) + BELOW_A_PIN]);
    }
    expect(labels().length).toBeGreaterThan(0);
  });
});

describe("nothing moves when reduced motion is set", () => {
  const reduced = (matches: boolean) => {
    Object.defineProperty(window, "matchMedia", {
      configurable: true,
      value: (query: string) => ({
        matches: matches && query.includes("prefers-reduced-motion"),
        media: query,
        addEventListener: () => undefined,
        removeEventListener: () => undefined,
      }),
    });
  };

  beforeEach(() => setWebGL(true));
  afterEach(() => {
    setWebGL(false);
    delete (window as { matchMedia?: unknown }).matchMedia;
  });

  test("test_nothing_moves_when_reduced_motion_is_set", async () => {
    reduced(true);
    await show();
    lastMap().view = { contains: () => false };

    fireEvent.click(pins()[0] as HTMLElement);
    fireEvent.click(screen.getByRole("button", { name: MAP.zoomIn }));
    fireEvent.click(screen.getByRole("button", { name: MAP.zoomOut }));
    fireEvent.click(screen.getByRole("button", { name: MAP.whole }));

    expect(lastMap().options).toMatchObject({ fadeDuration: 0 });
    const moves = ["panTo", "zoomIn", "zoomOut", "fitBounds"].flatMap((method) => lastMap().called(method));
    expect(moves).toHaveLength(4);
    for (const move of moves) expect(move[move.length - 1]).toMatchObject({ animate: false });
  });

  test("test_the_map_glides_where_motion_is_welcome", async () => {
    reduced(false);
    await show();

    fireEvent.click(screen.getByRole("button", { name: MAP.zoomIn }));

    expect(lastMap().called("zoomIn")).toEqual([[{ animate: true }]]);
  });
});

describe("the map, coloured by one vibe before a search", () => {
  const meta = recordedAnswer("get_meta", "meta").body.data;
  const bands = recordedAnswer("list_areas", "areas").body.data.bands;
  const lensOf = (tagId: string): Lens => {
    const tag = meta.tags.find((one) => one.tag_id === tagId);
    const marks = bands.find((one) => one.tag_id === tagId)?.marks;
    if (tag === undefined || marks === undefined) throw new Error(`the recording holds no bands for ${tagId}`);
    return { tag, marks };
  };

  beforeEach(() => setWebGL(true));
  afterEach(() => setWebGL(false));

  test("test_every_vibe_that_may_colour_the_map_came_with_the_page", () => {
    // The bands of every vibe are served in one answer, so nobody is told which one is looked at.
    const withALens = meta.tags.filter((tag) => tag.lens).map((tag) => tag.tag_id);

    expect(bands.map((one) => one.tag_id).sort()).toEqual([...withALens].sort());
    for (const { marks } of bands) expect(marks.map((mark) => mark.area_id).sort()).toEqual(areas.map((area) => area.area_id).sort());
  });

  test("test_each_area_is_coloured_by_its_band_and_dotted_where_it_cannot_be_placed", async () => {
    const lens = lensOf("pace");
    await show(null, lens);

    const fills = idsBy(fillForVibe(lens.marks));
    const [, , colour] = lastMap().called("setPaintProperty").findLast(([layer]) => layer === LAYER.fill) ?? [];
    for (const band of [1, 2, 3, 4, 5] as const) expect(JSON.stringify(colour)).toContain(JSON.stringify(fills.bands[band]));
    expect(lastMap().called("setFilter")).toEqual(
      expect.arrayContaining([[LAYER.unranked, ["in", ["get", "area_id"], ["literal", fills.patterns.unranked]]]]),
    );
    // An area the vibe cannot place has no band. It is never put in the middle.
    const unplaced = lens.marks.filter((mark) => mark.band === null).map((mark) => mark.area_id);
    expect(unplaced.length).toBeGreaterThan(0);
    expect(fills.patterns.unranked.sort()).toEqual([...unplaced].sort());
    expect(fills.bands[3].filter((areaId) => unplaced.includes(areaId))).toEqual([]);
  });

  /** The vibes that may colour the map, of each kind: by what the service says of each, and by no name. */
  const lenses = meta.tags.filter((tag) => tag.lens && bands.some((one) => one.tag_id === tag.tag_id));
  const served = (name: string) => `url("/art/${name}.png")`;

  test.each(lenses.map((tag) => [tag.tag_id]))(
    "test_the_legend_is_the_gauge_of_the_vibe_with_its_drawing_by_its_name_and_one_picture_at_each_end: %s",
    async (tagId) => {
      const lens = lensOf(tagId);
      await show(null, lens);
      const legend = screen.getByRole("region", { name: LEGEND.title });
      const [low, high] = [lens.tag.low_end ?? STRIP.least, lens.tag.high_end ?? STRIP.most];

      // The small drawing of the vibe stands with its name. It is dress, and says nothing.
      const title = within(legend).getByText(LEGEND.vibe(lens.tag.label));
      const thing = title.querySelector<HTMLElement>("[style*='/art/']");
      expect(thing?.style.getPropertyValue("--art")).toBe(served(drawingOf({ kind: "tag", id: lens.tag.tag_id, family: lens.tag.family })));
      expect(thing?.closest("[aria-hidden='true']")).not.toBeNull();
      // The gauge is one picture, and its name says what it shows: five shades, and which end is which.
      const gauge = within(legend).getByRole("img", { name: LEGEND.vibeRuns(low, high) });
      // The picture of the low end, the five shades from the palest to the darkest, and the picture of the high end.
      const drawn = [...gauge.querySelectorAll<HTMLElement>("[style*='/art/'], [data-band]")].map(
        (one) => one.getAttribute("data-band") ?? one.style.getPropertyValue("--art"),
      );
      const [atLow, atHigh] = picturesAtEnds(lens.tag.tag_id).map(served);
      expect(drawn).toEqual([atLow, "1", "2", "3", "4", "5", atHigh]);
      expect(atLow === atHigh).toBe(false);
      // Each end is named under its picture, as the service names it.
      expect(gauge.textContent).toBe(`${low}${high}`);
      // What else the legend says is what the dots mean, where the map draws any.
      const unplaced = lens.marks.some((mark) => mark.band === null);
      expect(within(legend).queryAllByRole("listitem").map((item) => item.textContent)).toEqual(unplaced ? [LEGEND.notPlaced] : []);
    },
  );

  test("test_the_vibes_that_may_colour_the_map_are_of_both_kinds_and_each_has_pictures_of_its_own", () => {
    expect(new Set(lenses.map((tag) => tag.shape))).toEqual(new Set(["scale", "one_way"]));
    expect(lenses.filter((tag) => picturesAtEnds(tag.tag_id).includes(NO_PICTURE)).map((tag) => tag.tag_id)).toEqual([]);
  });

  test("test_the_gauge_of_the_legend_says_which_end_is_the_palest_and_neither_is_the_better", () => {
    const said = LEGEND.vibeRuns("one end", "the other");

    expect(said).toMatch(/five shades/);
    expect(said.indexOf("one end")).toBeLessThan(said.indexOf("the other"));
    expect(said).toMatch(/palest.*darkest/);
    expect(/better|best|worse|worst|good|bad/i.test(said)).toBe(false);
  });

  test("test_coloured_by_a_vibe_the_service_holds_less_sure_the_map_says_nothing_of_how_sure_it_is", async () => {
    // The founder had the label of a rough guide go, and what stood beside it: no page
    // passes it on. The map is handed the vibe and where each area sits on it, and neither
    // the legend nor the card of an area draws a word of what a service said of the vibe:
    // the label it gave such a vibe, and the sentence that said why.
    const lens = lensOf(ROUGH.tag_id);
    await show(null, lens);
    const legend = screen.getByRole("region", { name: LEGEND.title });

    expect(lens.tag.sureness).toBe("rough_guide");
    expect(within(legend).getByText(LEGEND.vibe("Village feel"))).toBeInTheDocument();
    const placed = lens.marks.find((mark) => mark.band !== null);
    act(() => lastMap().fire("click", { features: [{ id: placed?.area_id }] }, LAYER.fill));
    const card = screen.getByRole("region", { name: MAP_CARD.label });

    expect(card.textContent).toMatch(/^.*Village feel: /);
    for (const part of [legend, card]) {
      expect(part.querySelector("[data-rough-guide]")).toBeNull();
      expect(part.textContent?.includes(ROUGH.label)).toBe(false);
      expect(part.textContent?.includes(ROUGH.why)).toBe(false);
      expect(/rough guide|less sure/i.test(part.textContent ?? "")).toBe(false);
    }
  });

  test("test_the_table_of_areas_names_a_vibe_the_service_holds_less_sure_over_its_column_by_its_name_alone_and_nothing_of_the_map_says_more", async () => {
    // The table named such a vibe over its column with its label after its name, "Village
    // feel, Rough guide". The founder asked that no page say it. So the table of the map,
    // which says everything the map does, names the vibe as it names any other: and nothing
    // the map holds says more, in sight or to whoever hears the page. The map is handed the
    // vibe and nothing a service says of it, so it is held to write none of it of its own.
    const lens = lensOf(ROUGH.tag_id);
    const { container } = await show(null, lens);
    fireEvent.click(screen.getByRole("button", { name: TABLE.title }));
    const table = screen.getByRole("table", { name: TABLE.captionEmpty });

    expect(lens.tag.sureness).toBe("rough_guide");
    const columns = within(table).getAllByRole("columnheader");
    const named = columns.filter((column) => column.textContent?.includes(lens.tag.label));
    expect(named.map((column) => [column.textContent, column.children.length])).toEqual([[lens.tag.label, 0]]);
    // Every area says where it sits on the vibe under that name, as it does of any vibe.
    expect(within(table).getAllByRole("row")).toHaveLength(areas.length + 1);
    // The legend, the card of an area and the table are all the map holds that says anything of a vibe.
    const placed = lens.marks.find((mark) => mark.band !== null);
    act(() => lastMap().fire("click", { features: [{ id: placed?.area_id }] }, LAYER.fill));
    expect(screen.getByRole("region", { name: MAP_CARD.label }).textContent).toMatch(new RegExp(`${lens.tag.label}: `));
    const heard = [...container.querySelectorAll("*")].flatMap((part) =>
      ["aria-label", "aria-description", "title", "alt"].flatMap((name) => part.getAttribute(name) ?? []),
    );
    const all = [container.textContent ?? "", ...heard].join("\n");
    expect(container.querySelector("[data-rough-guide]")).toBeNull();
    expect([all.includes(ROUGH.label), all.includes(ROUGH.why), /rough guide|less sure/i.test(all)]).toEqual([false, false, false]);
  });

  test("test_coloured_by_a_vibe_that_is_as_sure_as_the_rest_the_legend_says_nothing_of_it", async () => {
    const lens = lensOf("pace");
    await show(null, lens);

    expect(lens.tag.sureness).toBe("as_the_rest");
    expect(document.querySelector("[data-rough-guide]")).toBeNull();
    // Nor in the words a service gave a vibe that is less sure, which no part of the map writes.
    const said = document.body.textContent ?? "";
    expect(said.includes(LEGEND.vibe(lens.tag.label))).toBe(true);
    expect([said.includes(ROUGH.label), said.includes(ROUGH.why), /rough guide|less sure/i.test(said)]).toEqual([false, false, false]);
  });

  test("test_a_vibe_that_runs_one_way_is_counted_from_least_to_most", async () => {
    const [oneWay] = lenses.filter((tag) => tag.shape === "one_way");
    if (oneWay === undefined) throw new Error("the recording holds no vibe that runs one way");
    await show(null, lensOf(oneWay.tag_id));
    const legend = within(screen.getByRole("region", { name: LEGEND.title }));

    const gauge = legend.getByRole("img", { name: LEGEND.vibeRuns(STRIP.least, STRIP.most) });
    expect(within(gauge).getByText(STRIP.least)).toBeInTheDocument();
    expect(within(gauge).getByText(STRIP.most)).toBeInTheDocument();
  });

  test("test_no_area_is_pinned_because_none_is_ranked", async () => {
    await show(null, lensOf("pace"));

    expect(pins()).toEqual([]);
  });

  test("test_an_area_chosen_on_the_map_says_its_band_in_words", async () => {
    const lens = lensOf("pace");
    await show(null, lens);
    const mixed = lens.marks.find((mark) => (mark.spread_high ?? 0) - (mark.spread_low ?? 0) >= 2);
    const unplaced = lens.marks.find((mark) => mark.band === null);
    if (!mixed || !unplaced) throw new Error("the recording holds no mixed area, or none that cannot be placed");

    act(() => lastMap().fire("click", { features: [{ id: mixed.area_id }] }, LAYER.fill));
    const card = within(screen.getByRole("region", { name: MAP_CARD.label }));
    // Said in the words a band is said in wherever it is drawn: from which band to which, of five.
    expect(
      card.getByText(`Going out: ${STRIP.bands(mixed.spread_low ?? 0, mixed.spread_high ?? 0)}`),
    ).toBeInTheDocument();

    act(() => lastMap().fire("click", { features: [{ id: unplaced.area_id }] }, LAYER.fill));
    expect(card.getByText(`Going out: ${TABLE.notPlaced}`)).toBeInTheDocument();
  });

  test("test_the_map_is_coloured_by_fit_again_once_there_is_a_ranking", async () => {
    const { again } = await show(null, lensOf("pace"));

    again(first);
    await arrived();

    expect(pins()).toHaveLength(10);
    expect(within(screen.getByRole("region", { name: LEGEND.title })).queryByText(LEGEND.vibe("Going out"))).toBeNull();
  });
});

describe("the map on a narrow screen", () => {
  const STYLES = rulesOf(readFileSync(path.join(__dirname, "MapView.module.css"), "utf8"));
  const narrow = (rule: { under: string | null }) => /max-width:\s*59\.99rem/.test(rule.under ?? "");

  beforeEach(() => setWebGL(true));
  afterEach(() => setWebGL(false));

  test("test_once_a_search_is_open_the_map_is_higher_than_it_was_and_the_whole_of_it_is_one_press_away", async () => {
    // The founder: "Map should be larger on the search result". On a phone it was 358 by 238
    // as it had been. It has the width of the page there, so it is made higher: 300 px.
    await show();
    const window = STYLES.filter((rule) => isFor(rule.selector, "window") && rule.under === null);

    expect(window.map((rule) => rule.sets.get("height")).filter(Boolean)).toEqual(["300px"]);
    expect(300).toBeGreaterThan(238);
    // The whole of it is as high as it is wide, and no higher than seven parts in ten of the window.
    const whole = STYLES.filter((rule) => narrow(rule) && rule.sets.get("height") === "min(70vh, 100vw)").map((rule) => rule.selector);
    expect(whole).toEqual(['.view[data-taller="true"][data-low] .window']);
    const button = screen.getByRole("button", { name: MAP.taller });
    expect(button).toHaveAttribute("aria-pressed", "false");

    fireEvent.click(button);

    expect(screen.getByRole("button", { name: MAP.taller })).toHaveAttribute("aria-pressed", "true");
  });

  test("test_what_shows_the_whole_of_the_map_says_once_whether_it_does_and_keeps_its_name", async () => {
    // Heard in a browser, with the whole map shown: "Show less of the map, pressed". The
    // name had turned and the button said that it was on as well, and the two disagreed.
    // It was 5 px wider for its new name, under the press that turned it.
    await show();
    const button = screen.getByRole("button", { name: MAP.taller });
    const says = () => [button.textContent, button.getAttribute("aria-pressed")];

    expect(says()).toEqual([MAP.taller, "false"]);
    fireEvent.click(button);
    expect(says()).toEqual([MAP.taller, "true"]);
    fireEvent.click(button);
    expect(says()).toEqual([MAP.taller, "false"]);
    expect(screen.queryByRole("button", { name: /less of the map/i })).toBeNull();
  });

  test("test_what_shows_the_whole_of_the_map_stands_over_it_so_that_it_stays_under_the_hand_as_the_map_grows", async () => {
    // Under the map it went down the page by as much as the map grew: 350 px, from under
    // the finger that pressed it. Nothing moves under a press.
    const { container } = await show();
    const button = screen.getByRole("button", { name: MAP.taller });
    const canvas = lastMap().getCanvas();

    expect(Boolean(button.compareDocumentPosition(canvas) & Node.DOCUMENT_POSITION_FOLLOWING)).toBe(true);
    // No rule draws it anywhere but where it comes in the page.
    expect(STYLES.filter((rule) => rule.sets.has("order") && !/^\.table/.test(rule.selector))).toEqual([]);
    // On a wide screen the map is whole already, and nothing is there to show the whole of it.
    const gone = STYLES.filter((rule) => /min-width:\s*60rem/.test(rule.under ?? "") && rule.sets.get("display") === "none");
    expect(gone.map((rule) => rule.selector)).toEqual([".view .whole"]);
    expect(container.querySelector("[data-taller]")).toContainElement(button);
  });

  test("test_over_the_two_ways_in_the_map_is_a_low_strip_and_what_is_said_under_it_waits_with_the_whole_map", async () => {
    // The founder: "The map should stay visible on both tabs". On a phone it began at 885 of
    // 844 under Quick search, and at 2,761 under Deep search. It stands over the tabs there,
    // low, so that the box is on the first screen with it.
    function Low() {
      const [selectedId, setSelected] = useState<string | null>(null);
      return (
        <MapView
          geometry={geometry}
          areas={areas}
          scores={[]}
          ranked={[]}
          filtered={[]}
          unranked={[]}
          selectedId={selectedId}
          hoveredId={null}
          onSelect={setSelected}
          onHover={() => undefined}
          onShowInList={() => undefined}
          table={<p>the table</p>}
          low
        />
      );
    }
    const { container } = render(<Low />);
    await arrived();

    expect(container.querySelector("[data-low]")).toHaveAttribute("data-low", "true");
    const low = STYLES.filter((rule) => /data-low="true"\] \.window$/.test(rule.selector) && rule.sets.has("height"));
    expect(low.map((rule) => [rule.under, rule.sets.get("height")])).toEqual([
      ["@media (max-width: 59.99rem)", "max(120px, 20vw)"],
      // Where the window is not high, as on a small phone, the two tabs are on the first screen still.
      ["@media (max-width: 59.99rem) and (max-height: 44rem)", "88px"],
    ]);
    const waits = STYLES.filter((rule) => narrow(rule) && rule.sets.get("display") === "none").map((rule) => rule.selector);
    // All that is said under the map, but the card of an area that is chosen on the strip.
    expect(waits.filter((selector) => /data-low/.test(selector))).toEqual([
      '.view[data-taller="false"][data-low="true"] .below > :not([data-kind="box-on"])',
      '.view[data-taller="false"][data-low="true"] .below:not(:has(> [data-kind="box-on"]))',
    ]);
    act(() => lastMap().fire("load"));
    act(() => lastMap().fire("click", { features: [{ id: areas[0]?.area_id }] }, LAYER.fill));
    expect(screen.getByRole("region", { name: MAP_CARD.label })).toHaveAttribute("data-kind", "box-on");
    expect(screen.getByRole("region", { name: MAP_CARD.label })).toHaveFocus();
    // Nothing is drawn low on a wide screen, where the map stands whole beside the page.
    expect(STYLES.filter((rule) => /data-low/.test(rule.selector) && !narrow(rule))).toEqual([]);
    // The whole of it is one press away, and the table with it.
    fireEvent.click(screen.getByRole("button", { name: MAP.taller }));
    expect(container.querySelector("[data-taller]")).toHaveAttribute("data-taller", "true");
    expect(screen.getByRole("button", { name: TABLE.title })).toBeInTheDocument();
  });

  test("test_once_a_search_is_open_the_map_is_not_low", async () => {
    const { container } = await show();

    expect(container.querySelector("[data-low]")).toHaveAttribute("data-low", "false");
  });

  test("test_in_a_column_as_narrow_as_a_phone_the_window_of_the_map_gives_way_so_that_its_box_stands_whole", () => {
    // Measured in a browser at 1440 by 900, beside the answer: the box of the map has 868 px
    // of the window, and after a search held 906, with its window 288 high. It scrolled in
    // itself, and the foot of the box, its rule and its shadow, was cut off. Its column is
    // 272 px wide, so a window 288 high was higher than it was wide, and what it gave up is
    // water: the city is as wide as the window and no higher than half of it.
    const wide = STYLES.filter((rule) => isFor(rule.selector, "window") && /min-width:\s*60rem/.test(rule.under ?? ""));
    const least = wide.filter((rule) => rule.sets.has("min-height")).map((rule) => [rule.under, rule.sets.get("min-height")]);

    expect(least).toEqual([
      ["@media (min-width: 60rem)", "18rem"],
      ["@media (min-width: 60rem) and @container (max-width: 20rem)", "15rem"],
    ]);
    // What it gives up is held against what was measured: 48 px, where the box was 38 too high.
    expect((18 - 15) * 16).toBeGreaterThanOrEqual(906 - 868);
    // The box says how wide it is, and the window is asked it: not the screen, which says
    // nothing of how wide a column of it is.
    const view = new Map(STYLES.filter((rule) => rule.selector === ".view" && rule.under === null).flatMap((rule) => [...rule.sets]));
    expect(view.get("container-type")).toBe("inline-size");
    // A strip on a narrow screen is as high as it was.
    expect(STYLES.filter((rule) => /@container/.test(rule.under ?? "") && !/min-width:\s*60rem/.test(rule.under ?? ""))).toEqual([]);
  });

  test("test_as_a_page_of_results_opens_the_window_of_the_map_gives_way_so_that_its_box_ends_within_the_screen", () => {
    // Measured in a browser at 1440 by 900, as a page of results opened with areas left out:
    // the box of the map stood from 165 and was 756.6 px high, its window 389.1 of them, the
    // edge over its window 9, and what stands under its window 358.5. The foot of the box,
    // its rule and its shadow, was 21.6 px under the screen until the page was scrolled.
    const [from, edge, window, under, screen] = [165, 9, 389.1, 358.5, 900];
    expect(from + edge + window + under - screen).toBeCloseTo(21.6);

    const wide = STYLES.filter((rule) => isFor(rule.selector, "window") && /min-width:\s*60rem/.test(rule.under ?? ""));
    const most = wide.filter((rule) => rule.sets.has("max-height")).map((rule) => [rule.under, rule.sets.get("max-height")]);

    // It is as high as the screen has left for it, and never higher than six parts in ten of the screen.
    expect(most).toEqual([["@media (min-width: 60rem)", "min(60vh, calc(100vh - 33.75rem))"]]);
    // What the screen has not left for it: where the box stands from, its edge and what
    // stands under its window, which is words, and is asked in the measure of words.
    const kept = 33.75 * 16;
    expect(kept).toBeGreaterThanOrEqual(from + edge + under);
    expect(from + edge + (screen - kept) + under).toBeLessThanOrEqual(screen);
    // It gives up no more than it must: 29 px of 389, and nothing on a screen 930 high or higher.
    expect(window - (screen - kept)).toBeLessThan(30);
    expect(930 - kept).toBeGreaterThan(window);
    // It is never lower than it was at the least: on a screen too low for the whole box the map is still a map.
    expect(wide.filter((rule) => rule.sets.has("min-height")).map((rule) => rule.sets.get("min-height"))).toEqual(["18rem", "15rem"]);
  });

  test("test_what_moves_the_map_and_what_explains_it_wait_with_the_whole_map", () => {
    const waits = STYLES.filter((rule) => narrow(rule) && rule.sets.get("display") === "none");

    expect(waits.map((rule) => rule.selector).join(" ")).toMatch(/data-taller="false".*under/);
    expect(waits.map((rule) => rule.selector).join(" ")).toMatch(/data-taller="false".*legend/);
    // The table says everything the map does, and is one press away once a search is
    // open. It waits with the whole map where the map is low, over the two ways in.
    expect(waits.map((rule) => rule.selector).join(" ")).not.toMatch(/table|more/);
    expect(waits.filter((rule) => /below/.test(rule.selector)).every((rule) => /data-low="true"/.test(rule.selector))).toBe(true);
  });
});

describe("the map as a strip, where a finger scrolls the page", () => {
  /** What takes a press or a finger on the map, as the library has them: the stand-in has none of its own. */
  const BY_HAND = ["dragPan", "scrollZoom", "touchZoomRotate", "doubleClickZoom", "boxZoom"] as const;
  type Handler = { enable: jest.Mock; disable: jest.Mock; disableRotation: jest.Mock };
  const handlers = () => Object.fromEntries(BY_HAND.map((name) => [name, { enable: jest.fn(), disable: jest.fn(), disableRotation: jest.fn() }])) as Record<(typeof BY_HAND)[number], Handler>;
  let given: ReturnType<typeof handlers>;
  const library = { Map: StandIn as unknown as { prototype: Record<string, unknown> } };

  /** A browser that lays the window of the map out so wide and so high. */
  function laidOut(width: number, height: number) {
    const wide = jest.spyOn(HTMLElement.prototype, "clientWidth", "get").mockReturnValue(width);
    const tall = jest.spyOn(HTMLElement.prototype, "clientHeight", "get").mockReturnValue(height);
    return () => {
      wide.mockRestore();
      tall.mockRestore();
    };
  }

  beforeEach(() => {
    setWebGL(true);
    given = handlers();
    Object.assign(library.Map.prototype, given);
  });
  afterEach(() => {
    setWebGL(false);
    for (const name of BY_HAND) delete library.Map.prototype[name];
  });

  test("test_in_a_strip_the_city_is_drawn_as_wide_as_the_window_and_a_finger_moves_no_map", async () => {
    const putBack = laidOut(358, 120);
    try {
      await show(null);
      const { bounds, fitBoundsOptions } = lastMap().options as {
        bounds: [[number, number], [number, number]];
        fitBoundsOptions: { padding: number };
      };
      const [[west, south], [east, north]] = boundsOf(geometry) ?? [[0, 0], [0, 0]];

      expect([bounds[0][0], bounds[1][0]]).toEqual([west, east]);
      expect(bounds[1][1] - bounds[0][1]).toBeLessThan((north - south) / 10);
      expect((bounds[0][1] + bounds[1][1]) / 2).toBeCloseTo((south + north) / 2, 10);
      expect(fitBoundsOptions.padding).toBe(8);
      for (const name of BY_HAND) {
        expect([name, given[name].disable.mock.calls.length, given[name].enable.mock.calls.length]).toEqual([name, 1, 0]);
      }
    } finally {
      putBack();
    }
  });

  test("test_in_any_other_window_the_whole_city_is_shown_and_the_map_is_moved_by_hand_as_it_was", async () => {
    const putBack = laidOut(358, 300);
    try {
      await show();
      const { bounds, fitBoundsOptions } = lastMap().options as { bounds: unknown; fitBoundsOptions: { padding: number } };

      expect(bounds).toEqual(boundsOf(geometry));
      expect(fitBoundsOptions.padding).toBe(24);
      for (const name of BY_HAND) {
        expect([name, given[name].enable.mock.calls.length, given[name].disable.mock.calls.length]).toEqual([name, 1, 0]);
      }
      // The map is never turned by two fingers, whichever window it is in.
      expect(given.touchZoomRotate.disableRotation).toHaveBeenCalled();
    } finally {
      putBack();
    }
  });

  test("test_as_the_whole_map_is_shown_it_is_fitted_to_its_window_again_whatever_a_key_had_moved_it_to", async () => {
    let putBack = laidOut(358, 120);
    try {
      await show(null);
      // An arrow key moved the map while it was a strip.
      act(() => lastMap().fire("movestart", { originalEvent: {} }));

      fireEvent.click(screen.getByRole("button", { name: MAP.taller }));
      putBack();
      putBack = laidOut(358, 590);
      act(() => lastMap().fire("resize"));

      const [to, how] = lastMap().called("fitBounds").at(-1) ?? [];
      expect(to).toEqual(boundsOf(geometry));
      expect(how).toEqual({ padding: 24, animate: false });
      for (const name of BY_HAND) expect([name, given[name].enable.mock.calls.length]).toEqual([name, 1]);
    } finally {
      putBack();
    }
  });
});

describe("what is drawn on the map, and beside it", () => {
  const STYLES = rulesOf(readFileSync(path.join(__dirname, "MapView.module.css"), "utf8"));
  const written = readFileSync(path.join(__dirname, "MapView.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
  const narrow = (rule: { under: string | null }) => /max-width:\s*59\.99rem/.test(rule.under ?? "");
  /** The face a class is set in, where it holds always. */
  const fontOf = (className: string) =>
    STYLES.filter((rule) => isFor(rule.selector, className) && rule.under === null).flatMap((rule) => rule.sets.get("font") ?? []);

  beforeEach(() => setWebGL(true));
  afterEach(() => setWebGL(false));

  test("test_a_pin_is_of_one_size_on_every_screen_and_is_as_big_as_a_thing_that_is_pressed_may_be", () => {
    // Seen on a phone: pins of 28 px on a strip 174 px high, where pins 1, 3 and 4 lay over
    // one another by 1 to 3 px. A pin is its drawing, shown at two pixels of the screen to
    // one of its own on every screen: 26 wide and 32 high, with its head 24 high.
    // The pin itself, and not what is drawn over it.
    const pin = STYLES.filter((rule) => isFor(rule.selector, "pin") && !/::/.test(rule.selector));
    const sized = pin.filter((rule) => ["width", "height", "font-size", "font"].some((property) => rule.sets.has(property)));
    const tokens = readFileSync(path.resolve(__dirname, "../../styles/tokens.css"), "utf8");

    expect(sized.map((rule) => [rule.selector, rule.under, rule.sets.get("width"), rule.sets.get("height")])).toEqual([
      [".pin", null, "calc(var(--px-map) * var(--w))", "calc(var(--px-map) * var(--h))"],
    ]);
    expect(STYLES.filter((rule) => rule.sets.has("--px-map")).map((rule) => [rule.under, rule.sets.get("--px-map")])).toEqual([
      [null, "var(--px-ground)"],
    ]);
    expect(tokens).toMatch(/--px-ground:\s*2px/);
    // 24 px is the least a thing that is pressed may be: docs/design/web.md, section 8.
    expect(tokens).toMatch(/--target-min:\s*24px/);
    expect(Math.min(ART.pin.width, ART.pin.height) * 2).toBeGreaterThanOrEqual(24);
    // No pin is made smaller for a narrow screen, and none is another size for being chosen.
    expect(pin.filter(narrow)).toEqual([]);
  });

  test("test_the_chosen_pin_is_amber_and_is_of_the_size_it_was", () => {
    // Nothing moves or changes size under a press. The chosen pin was larger than the rest:
    // it is of their size, and is told from them by its colour and to a screen reader.
    const chosen = STYLES.filter((rule) => /\.pin\[aria-current="true"\]/.test(rule.selector) && !/forced-colors/.test(rule.under ?? ""));
    const itself = chosen.filter((rule) => !/::/.test(rule.selector));
    const drawnOver = chosen.filter((rule) => /::before$/.test(rule.selector));

    expect(itself.flatMap((rule) => [...rule.sets.keys()])).toEqual(["z-index"]);
    expect(drawnOver).toHaveLength(1);
    expect(drawnOver[0]?.sets.get("background")).toMatch(/var\(--chosen\)/);
    expect((drawnOver[0]?.sets.get("background") ?? "").match(/var\(--[a-z-]+\)/g)?.filter((token) => !/^var\(--(chosen|px-map|wide|high)\)$/.test(token))).toEqual([]);
  });

  test("test_the_number_of_a_pin_is_a_figure_and_is_set_in_the_reading_face", () => {
    // A rank is a figure, and is read. It is sized as the drawing is, so that it stays on its pin.
    expect(fontOf("figure")).toHaveLength(1);
    expect(fontOf("figure")[0]).toMatch(/^700 calc\(var\(--px-map\) \* .+\) \/ 1 var\(--font-say\)$/);
    expect(STYLES.filter((rule) => isFor(rule.selector, "pin") && /font-name/.test(rule.sets.get("font") ?? ""))).toEqual([]);
  });

  test("test_the_name_of_an_area_is_set_in_the_face_of_names_on_a_plate_of_the_colour_that_is_read_on", () => {
    // The name of an area is a name. Nothing is read on the land itself: it stands on the
    // colour that is read on, with an edge.
    expect(fontOf("label")).toEqual(["400 var(--name-1) / 0.8 var(--font-name)"]);
    const label = new Map(STYLES.filter((rule) => rule.selector === ".label" && rule.under === null).flatMap((rule) => [...rule.sets]));
    expect([label.get("background"), label.get("border"), label.get("color"), label.get("font-synthesis")]).toEqual([
      "var(--bg)",
      "var(--px-map) solid var(--border)",
      "var(--text)",
      "none",
    ]);
  });

  test("test_every_word_laid_over_the_map_names_its_face_so_that_none_is_set_in_the_face_the_map_library_names", async () => {
    // The map library names a face of the system's on the element of the map, and whatever
    // is laid over the map stands in that element: so a word that names no face of its own
    // is set in the library's. Seen in a browser before the map was dressed, of the number
    // of a pin and of the name of an area: they were the only words of the website in
    // neither of its two faces.
    const theirs = rulesOf(readFileSync(path.resolve(__dirname, "../../../node_modules/maplibre-gl/dist/maplibre-gl.css"), "utf8"));
    const named = theirs.filter((rule) => rule.selector === ".maplibregl-map").flatMap((rule) => rule.sets.get("font") ?? []);
    expect(named).toHaveLength(1);
    expect(named[0]).toMatch(/Helvetica/);

    await show();
    zoomedTo(10_000);
    const within = lastMap().getContainer();
    /** True where a class of ours names one of the two faces, by its token, whatever the screen. */
    const namesAFace = (className: string) =>
      STYLES.some(
        (rule) =>
          rule.under === null && rule.selector === `.${className}` && /var\(--font-(say|name)\)$/.test(rule.sets.get("font") ?? ""),
      );
    const words: string[] = [];
    const inNoFace: string[] = [];
    const walker = document.createTreeWalker(within, NodeFilter.SHOW_TEXT);
    for (let node = walker.nextNode(); node !== null; node = walker.nextNode()) {
      if ((node.textContent ?? "").trim() === "") continue;
      words.push(node.textContent ?? "");
      let faced = false;
      for (let held = node.parentElement; held !== null && held !== within && !faced; held = held.parentElement) {
        faced = [...held.classList].some(namesAFace);
      }
      if (!faced) inNoFace.push(node.textContent ?? "");
    }

    // Ten numbers and the name of every area, and each in a face of the website's.
    expect(words.length).toBeGreaterThanOrEqual(10 + areas.length);
    expect(inNoFace).toEqual([]);
  });

  test("test_the_map_says_in_one_place_how_its_names_are_drawn_and_a_name_stands_on_a_plate", async () => {
    const { container } = await show();

    expect(NAMES).toBe("plate");
    expect(container.firstElementChild).toHaveAttribute("data-names", NAMES);
    // The other way is drawn only where the map says so, and sets nothing of a name that stands on a plate.
    const halo = STYLES.filter((rule) => /data-names="halo"/.test(rule.selector) && !/forced-colors/.test(rule.under ?? ""));
    expect(halo.map((rule) => rule.selector)).toEqual(['.view[data-names="halo"] .label']);
    expect(halo[0]?.sets.get("--halo")).toBe("var(--bg)");
    expect(STYLES.filter((rule) => rule.sets.has("text-shadow") && !/data-names="halo"/.test(rule.selector))).toEqual([]);
  });

  test("test_a_line_laid_over_the_map_stands_on_a_plate_of_the_colour_that_is_read_on", () => {
    const loading = new Map(STYLES.filter((rule) => rule.selector === ".loading" && rule.under === null).flatMap((rule) => [...rule.sets]));

    expect([loading.get("background"), loading.get("border")]).toEqual(["var(--bg)", "var(--px-map) solid var(--border)"]);
  });

  test("test_what_explains_a_band_is_drawn_as_the_map_draws_it_and_each_band_has_the_grain_of_its_own", () => {
    const swatch = (selector: string) => new Map(STYLES.filter((rule) => rule.selector === selector).flatMap((rule) => [...rule.sets]));

    // Land with no fit, and then the five bands: each in its colour, with its grain in the
    // colour the map draws the grain of that band in.
    expect([swatch(".swatch").get("background-color"), swatch(".swatch").get("--grain")]).toEqual(["var(--map-land)", "var(--map-3)"]);
    expect([1, 2, 3, 4, 5].map((band) => swatch(`.swatch[data-band="${band}"]`).get("background-color"))).toEqual(
      [1, 2, 3, 4, 5].map((band) => `var(--map-${band})`),
    );
    expect([1, 2, 3, 4, 5].map((band) => swatch(`.swatch[data-band="${band}"]`).get("--grain"))).toEqual(
      [2, 3, 4, 5, 4].map((band) => `var(--map-${band})`),
    );
    // The two patterns are drawn in the colour of the outlines, on land, pixel for pixel as the map lays them.
    expect(swatch(".swatch[data-pattern]").get("--dot")).toMatch(/var\(--map-line\)/);
    for (const pattern of ["filtered", "unranked"] as const) {
      const drawn = swatch(`.swatch[data-pattern="${pattern}"]`);
      const pixels = DRAWN[pattern].flatMap((row, y) => [...row].flatMap((pixel, x) => (pixel === "x" ? [[x, y] as const] : [])));
      const at = (count: number) => (count === 0 ? "0" : count === 1 ? "var(--px-map)" : `calc(var(--px-map) * ${count})`);

      expect([pattern, drawn.get("background-position")?.replace(/\s+/g, " ")]).toEqual([
        pattern,
        pixels.map(([x, y]) => `${at(x)} ${at(y)}`).join(", "),
      ]);
      expect([pattern, drawn.get("background-size")]).toEqual([
        pattern,
        `calc(var(--px-map) * ${DRAWN[pattern].length}) calc(var(--px-map) * ${DRAWN[pattern].length})`,
      ]);
    }
  });

  test("test_the_sign_of_a_button_is_drawn_in_pixels_of_the_button_and_is_still_drawn_in_the_colours_of_the_system", () => {
    const sign = (selector: string, forced: boolean) =>
      new Map(STYLES.filter((rule) => rule.selector === selector && /forced-colors/.test(rule.under ?? "") === forced).flatMap((rule) => [...rule.sets]));

    // Eight pixels of a drawing square, each of them as large as a pixel of the button it is on.
    expect([sign(".sign", false).get("width"), sign(".sign", false).get("height")]).toEqual(["calc(var(--px) * 8)", "calc(var(--px) * 8)"]);
    // It is in the colour of the words of its button, whatever that is.
    expect(sign(".sign", false).get("--bar")).toBe("linear-gradient(currentColor, currentColor)");
    // A minus is one stroke and a plus is two.
    expect((sign(".sign", false).get("background") ?? "").match(/var\(--bar\)/g)).toHaveLength(1);
    expect((sign('.sign[data-sign="more"]', false).get("background") ?? "").match(/var\(--bar\)/g)).toHaveLength(2);
    // Seen in a browser, with the system drawing in colours of its own: both buttons were
    // bare. What a style sheet draws is taken away there, unless it is said to be left.
    expect([sign(".sign", true).get("forced-color-adjust"), sign(".sign", true).get("--bar")]).toEqual([
      "none",
      "linear-gradient(ButtonText, ButtonText)",
    ]);
  });

  test("test_the_style_sheet_names_no_colour_no_face_and_no_picture_of_its_own", () => {
    expect(written.match(/#[0-9a-f]{3,8}\b|\b(rgb|hsl|oklch|lab|lch)a?\(/gi) ?? []).toEqual([]);
    expect(written.match(/url\(/g) ?? []).toEqual([]);
    expect(written.match(/font(-family)?:[^;]*["'][^;]*;/g) ?? []).toEqual([]);
    // A drawing keeps its hard edge, and nothing else is told how to be drawn: said of the
    // map itself, it would be said of what the map library draws.
    expect(STYLES.filter((rule) => rule.sets.has("image-rendering")).map((rule) => [rule.selector, rule.sets.get("image-rendering")])).toEqual([
      [".pin", "pixelated"],
      [".pinSwatch", "pixelated"],
    ]);
  });
});

describe("the card a pin opens, beside the results it stands with", () => {
  const STYLES = rulesOf(readFileSync(path.join(__dirname, "MapView.module.css"), "utf8"));
  const RESULT = rulesOf(readFileSync(path.join(__dirname, "..", "ResultList", "ResultList.module.css"), "utf8"));

  beforeEach(() => setWebGL(true));
  afterEach(() => setWebGL(false));

  test("test_every_way_on_of_the_card_is_a_button_of_the_look_and_none_is_plain_words", async () => {
    // Seen in a browser before the button that compares was dressed: "Compare" stood as plain
    // words in a plain edge, between two buttons of the look.
    await show();
    act(() => lastMap().fire("click", { features: [{ id: first.ranked[0]?.area_id }] }, LAYER.fill));
    const card = screen.getByRole("region", { name: MAP_CARD.label });
    const buttons = within(card).getAllByRole("button");

    expect(buttons.map((button) => button.textContent)).toEqual([MAP_CARD.showInList, COMPARE.addShort, MAP_CARD.close]);
    // Each is drawn by the face inside it, which is the picture of a button, and each is as high as the next.
    expect(buttons.map((button) => button.querySelector(":scope > [data-kind]")?.getAttribute("data-kind"))).toEqual([
      "plain",
      "plain",
      "plain",
    ]);
    expect(buttons.filter((button) => !button.classList.contains("press"))).toEqual([]);
    // No words of the card are pressed but its buttons and the name of the area, which leads to its page.
    expect(within(card).getAllByRole("link").map((link) => link.textContent)).toEqual([nameOf(first.ranked[0]?.area_id ?? "")]);
  });

  test("test_the_name_of_the_area_leads_to_its_page_and_is_drawn_as_a_result_draws_the_name_of_its_area", () => {
    // Seen side by side, on one page: the name of a result in ink with a hard line under it,
    // and the name in the card of the map in cobalt with a soft one.
    const theirs = RESULT.find((rule) => rule.selector === ".toArea" && rule.under === null);
    const mine = STYLES.find((rule) => rule.selector === ".cardName > a" && rule.under === null);

    expect(theirs).toBeDefined();
    expect([...(mine?.sets ?? [])].sort()).toEqual([...(theirs?.sets ?? [])].sort());
    expect(mine?.sets.get("color")).toBe("inherit");
    // It is the name, in the face of names, at the size a result sets the name of its area.
    const name = (rules: typeof STYLES, selector: string) => rules.find((rule) => rule.selector === selector && rule.under === null)?.sets.get("font");
    expect((name(STYLES, ".cardName") ?? "").replace(/\s*\/\s*[\d.]+/, "")).toBe((name(RESULT, ".name") ?? "").replace(/\s*\/\s*[\d.]+/, ""));
  });
});

describe("the map in its box", () => {
  beforeEach(() => setWebGL(true));
  afterEach(() => setWebGL(false));

  test("test_the_map_and_all_that_is_said_of_it_stand_in_one_box_so_that_nothing_is_read_on_the_grass", async () => {
    const { container } = await show(refined);
    fireEvent.click(pins()[0] as HTMLElement);
    const box = container.firstElementChild as HTMLElement;

    expect(container.children).toHaveLength(1);
    expect(box).toHaveAttribute("data-kind", "box");
    // Every word of the map is inside it: the keys, the card, the legend, and the way to the table.
    for (const said of [MAP.keys, MAP_CARD.close, LEGEND.pin, TABLE.title]) {
      expect(within(box).getAllByText(said, { exact: false }).length).toBeGreaterThan(0);
    }
    // The card of the area in hand is the box in hand.
    expect(screen.getByRole("region", { name: MAP_CARD.label })).toHaveAttribute("data-kind", "box-on");
  });

  test("test_where_the_map_cannot_be_drawn_what_is_said_of_it_stands_in_a_box_too", async () => {
    setWebGL(false);
    const { container } = await show();

    expect(container.children).toHaveLength(1);
    expect(container.firstElementChild).toHaveAttribute("data-kind", "box");
    expect(within(container.firstElementChild as HTMLElement).getByRole("status")).toHaveTextContent(MAP.noWebGL);
  });
});

describe("the map, where the browser cannot draw it", () => {
  beforeEach(() => setWebGL(false));

  test("test_the_map_is_not_started_at_all_and_the_table_is_one_press_away_under_a_line_saying_why", async () => {
    await show();

    expect(mapsMade()).toEqual([]);
    expect(screen.getByRole("status")).toHaveTextContent(MAP.noWebGL);
    expect(screen.queryByRole("group", { name: MAP.controls })).toBeNull();
    // The table is closed at first, so that the answer comes first. It is one press away.
    expect(screen.queryByRole("table")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: TABLE.title }));
    expect(screen.getByRole("table", { name: TABLE.caption })).toBeInTheDocument();
  });

  test("test_boundaries_that_could_not_be_loaded_are_said_and_the_table_stands_in", async () => {
    setWebGL(true);
    render(
      <MapView
        geometry={null}
        geometryFailed
        areas={areas}
        scores={[]}
        ranked={[]}
        filtered={[]}
        unranked={[]}
        selectedId={null}
        hoveredId={null}
        onSelect={() => undefined}
        onHover={() => undefined}
        onShowInList={() => undefined}
        table={<p>the table</p>}
      />,
    );
    await arrived();

    expect(mapsMade()).toEqual([]);
    expect(screen.getByRole("status")).toHaveTextContent(MAP.noGeometry);
    fireEvent.click(screen.getByRole("button", { name: TABLE.title }));
    expect(screen.getByText("the table")).toBeInTheDocument();
  });
});

describe("the table of the map, where the map stands in a column that scrolls in itself", () => {
  beforeEach(() => setWebGL(true));
  afterEach(() => setWebGL(false));

  test("test_the_table_is_brought_into_sight_as_it_opens_at_the_foot_of_the_column", async () => {
    // Seen at 1440 by 900, beside the answer: the column of the map stood from 16 to 884
    // and scrolled in itself. "Table of all areas" stood at its foot, from 833, and the
    // table it opened began at 896: out of sight, where on the trunk it opened in sight.
    const measure = jest.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function (
      this: HTMLElement,
    ) {
      const [top, foot] =
        this.tagName === "BUTTON" ? [833, 880] : this.hasAttribute("data-column") ? [16, 884] : [896, 6659];
      return { top, bottom: foot, left: 0, right: 0, x: 0, y: top, width: 0, height: foot - top, toJSON: () => ({}) };
    });
    const high = window.innerHeight;
    Object.defineProperty(window, "innerHeight", { configurable: true, value: 900 });
    const told: Told = { selected: [], hovered: [], shown: [] };
    try {
      const { container } = render(
        <div data-column="" style={{ overflowY: "auto" }}>
          <Held ranking={first} told={told} />
        </div>,
      );
      const column = container.firstElementChild as HTMLElement;
      Object.defineProperty(column, "clientHeight", { configurable: true, value: 868 });
      Object.defineProperty(column, "scrollHeight", { configurable: true, value: 6685 });
      await arrived();
      act(() => lastMap().fire("load"));

      fireEvent.click(screen.getByRole("button", { name: TABLE.title }));

      expect(screen.getByRole("table", { name: TABLE.caption })).toBeInTheDocument();
      // The head of the table is brought over the foot of the column, and no more: brought to
      // the top of the column, the button went 675 px from under the pointer.
      expect(column.scrollTop).toBe(896 + HEAD - 884);
    } finally {
      measure.mockRestore();
      Object.defineProperty(window, "innerHeight", { configurable: true, value: high });
    }
  });
});

describe("what is pressed in the table, which leads to the map over it", () => {
  beforeEach(() => setWebGL(true));
  afterEach(() => setWebGL(false));

  const named = TABLE.select("Cindermoor");
  /** Where each part stands in the window, from its head to its foot. What is not named stands nowhere. */
  interface Stands {
    readonly column?: readonly [number, number];
    readonly map: readonly [number, number];
    readonly card: readonly [number, number];
    readonly bar?: readonly [number, number];
  }
  const stands = (at: Stands) =>
    jest.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function (this: HTMLElement) {
      const [top, foot] = this.hasAttribute("data-column")
        ? (at.column ?? [0, 0])
        : this.hasAttribute("data-taller")
          ? at.map
          : this.getAttribute("aria-label") === MAP_CARD.label
            ? at.card
            : this.getAttribute("aria-label") === COMPARE_BAR
              ? (at.bar ?? [0, 0])
              : [0, 0];
      return { top, bottom: foot, left: 0, right: 0, x: 0, y: top, width: 0, height: foot - top, toJSON: () => ({}) };
    });
  const COMPARE_BAR = "Areas to compare";
  /** What the page was asked to go by, each time it was. */
  const watched = () => {
    const asked: number[] = [];
    const scroll = jest.spyOn(window, "scrollBy").mockImplementation(((_: number, y: number) => {
      asked.push(y);
    }) as typeof window.scrollBy);
    return { asked, scroll };
  };
  const card = () => screen.getByRole("region", { name: MAP_CARD.label });
  /** What the table says a press in it did, in the line that is heard. */
  const did = () => within(screen.getByRole("table").parentElement?.parentElement as HTMLElement).getByRole("status");

  test("test_show_in_a_row_says_what_it_did_and_gives_the_focus_to_the_box_of_the_area", async () => {
    // Seen in a browser: the button said that it was pressed and its row was framed, and
    // nothing else was seen or heard. The box of the area had opened over the head of the
    // window, and the focus was left on the button.
    const { told } = await show();
    fireEvent.click(screen.getByRole("button", { name: TABLE.title }));
    expect(did()).toBeEmptyDOMElement();

    fireEvent.click(screen.getByRole("button", { name: named }));

    expect(told.selected).toEqual(["syn-n0003"]);
    expect(card()).toHaveFocus();
    expect(card()).toHaveTextContent("Cindermoor");
    expect(did().textContent).toBe(CARD.shownOnMap("Cindermoor"));
    expect(screen.getByRole("button", { name: named })).toHaveAttribute("aria-pressed", "true");
    // The box leads back: closed, it hands the focus to the pin of the area, on the map.
    fireEvent.click(within(card()).getByRole("button", { name: MAP_CARD.close }));
    expect(pins().filter((pin) => pin === document.activeElement)).toHaveLength(1);
    // Once no area is chosen, the line says nothing of one that was.
    expect(did()).toBeEmptyDOMElement();
  });

  test("test_the_line_says_it_of_the_area_that_is_chosen_and_of_no_other", async () => {
    await show();
    fireEvent.click(screen.getByRole("button", { name: TABLE.title }));

    fireEvent.click(screen.getByRole("button", { name: named }));
    fireEvent.click(screen.getByRole("button", { name: TABLE.select("Gorsebeck") }));

    expect(card()).toHaveTextContent("Gorsebeck");
    expect(did().textContent).toBe(CARD.shownOnMap("Gorsebeck"));
    // Another is then chosen on the map itself: the table says nothing of the one it showed.
    fireEvent.click(pins()[0] as HTMLButtonElement);
    expect(did()).toBeEmptyDOMElement();
  });

  test("test_on_a_narrow_screen_the_page_goes_to_the_map_with_the_box_of_the_area_under_it", async () => {
    // Seen at 390 by 844: "Show" was pressed in the third row at 329, and the box of the
    // area stood from -378 to -85, over the head of the window, with the map over it.
    const measure = stands({ map: [-729, -30], card: [-378, -85] });
    const { asked, scroll } = watched();
    const high = window.innerHeight;
    Object.defineProperty(window, "innerHeight", { configurable: true, value: 844 });
    try {
      await show();
      fireEvent.click(screen.getByRole("button", { name: TABLE.title }));

      fireEvent.click(screen.getByRole("button", { name: named }));

      // The head of the box of the map at the head of the window, and the card whole under it.
      expect(card()).toHaveFocus();
      expect(asked).toEqual([-729 - 8]);
    } finally {
      measure.mockRestore();
      scroll.mockRestore();
      Object.defineProperty(window, "innerHeight", { configurable: true, value: high });
    }
  });

  test("test_a_press_that_is_counted_as_the_second_of_two_lands_on_nothing_of_the_map_once_the_page_has_gone_to_it", async () => {
    // What was pressed has gone from under the pointer, and the map may stand there: a
    // second press aimed at the row chose another area, and drew the map nearer.
    const measure = stands({ map: [-729, -30], card: [-378, -85] });
    const { scroll } = watched();
    try {
      const { told } = await show();
      fireEvent.click(screen.getByRole("button", { name: TABLE.title }));
      fireEvent.click(screen.getByRole("button", { name: named }));

      fireEvent.click(pins()[4] as HTMLButtonElement, { detail: 2 });
      fireEvent.click(within(card()).getByRole("button", { name: MAP_CARD.close }), { detail: 2 });

      expect(told.selected).toEqual(["syn-n0003"]);
      expect(card()).toHaveTextContent("Cindermoor");
      // A press of its own lands at once.
      fireEvent.click(pins()[4] as HTMLButtonElement, { detail: 1 });
      expect(told.selected).toHaveLength(2);
    } finally {
      measure.mockRestore();
      scroll.mockRestore();
    }
  });

  test("test_beside_the_answer_the_column_of_the_map_goes_to_the_map_and_the_page_does_not", async () => {
    // Seen at 1440 by 900: the column stood scrolled by 955 to the row that was pressed,
    // and the box of the area stood from -470 to -167, over the head of the column.
    const measure = stands({ column: [16, 884], map: [-939, -100], card: [-470, -167] });
    const { asked, scroll } = watched();
    const high = window.innerHeight;
    Object.defineProperty(window, "innerHeight", { configurable: true, value: 900 });
    const told: Told = { selected: [], hovered: [], shown: [] };
    try {
      const { container } = render(
        <div data-column="" style={{ overflowY: "auto" }}>
          <Held ranking={first} told={told} />
        </div>,
      );
      const column = container.firstElementChild as HTMLElement;
      Object.defineProperty(column, "clientHeight", { configurable: true, value: 868 });
      Object.defineProperty(column, "scrollHeight", { configurable: true, value: 4973 });
      await arrived();
      act(() => lastMap().fire("load"));
      fireEvent.click(screen.getByRole("button", { name: TABLE.title }));
      column.scrollTop = 955;
      fireEvent.scroll(column);

      fireEvent.click(screen.getByRole("button", { name: named }));

      expect(card()).toHaveFocus();
      expect(column.scrollTop).toBe(955 - 939 - 16 - 8);
      expect(asked).toEqual([]);
    } finally {
      measure.mockRestore();
      scroll.mockRestore();
      Object.defineProperty(window, "innerHeight", { configurable: true, value: high });
    }
  });

  test("test_an_area_chosen_on_the_map_moves_nothing_for_what_was_pressed_in_the_table_before_it", async () => {
    // What a press in the table moved the page for is forgotten: what is chosen later, on
    // the map itself, moves the page nowhere.
    const measure = stands({ map: [-729, -30], card: [-378, -85] });
    const { asked, scroll } = watched();
    try {
      await show();
      fireEvent.click(screen.getByRole("button", { name: TABLE.title }));
      fireEvent.click(screen.getByRole("button", { name: named }));
      asked.length = 0;

      fireEvent.click(pins()[0] as HTMLButtonElement);
      fireEvent.click(screen.getByRole("button", { name: MAP_CARD.close }));

      expect(asked).toEqual([]);
    } finally {
      measure.mockRestore();
      scroll.mockRestore();
    }
  });
});

describe("the box of an area, as a press elsewhere gives it the focus", () => {
  beforeEach(() => setWebGL(true));
  afterEach(() => setWebGL(false));

  /** The map with an area chosen elsewhere, as "Show on the map" in the working of a result chooses one. */
  const chosenElsewhere = async () => {
    const told: Told = { selected: [], hovered: [], shown: [] };
    const shown = (selectedId: string | null) => (
      <MapView
        geometry={geometry}
        areas={areas}
        scores={first.scores}
        ranked={first.ranked}
        filtered={first.filtered}
        unranked={first.unranked}
        selectedId={selectedId}
        hoveredId={null}
        onSelect={(areaId) => told.selected.push(areaId)}
        onHover={() => undefined}
        onShowInList={() => undefined}
        table={<p>the table</p>}
      />
    );
    const view = render(shown(null));
    await arrived();
    act(() => lastMap().fire("load"));
    view.rerender(shown("syn-n0006"));
    return screen.getByRole("region", { name: MAP_CARD.label });
  };
  const inTheWindow = (at: { map: readonly [number, number]; card: readonly [number, number] }) =>
    jest.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function (this: HTMLElement) {
      const [top, foot] = this.hasAttribute("data-taller") ? at.map : this.getAttribute("aria-label") === MAP_CARD.label ? at.card : [0, 0];
      return { top, bottom: foot, left: 0, right: 0, x: 0, y: top, width: 0, height: foot - top, toJSON: () => ({}) };
    });
  /** The page as a browser scrolls it: how far it stands scrolled, and what it was asked to go by. */
  const aPage = (scrolledTo: number) => {
    let at = scrolledTo;
    const asked: number[] = [];
    const was = Object.getOwnPropertyDescriptor(window, "scrollY");
    Object.defineProperty(window, "scrollY", { configurable: true, get: () => at });
    const scroll = jest.spyOn(window, "scrollBy").mockImplementation(((_: number, y: number) => {
      asked.push(y);
      at += y;
    }) as typeof window.scrollBy);
    return {
      asked,
      /** A browser moves the page, as it does for what it gives the focus, and says so a moment later. */
      goes: (by: number) => {
        at += by;
      },
      says: () => fireEvent.scroll(window),
      putBack: () => {
        scroll.mockRestore();
        if (was) Object.defineProperty(window, "scrollY", was);
      },
    };
  };

  test("test_where_the_map_and_the_box_are_in_sight_the_page_is_put_back_where_a_browser_moved_it_for_the_focus", async () => {
    // Measured at 1440 by 900: "Show on the map" was pressed in the working of a result,
    // and the box of the area opened under the map, from 485 to 764. The page went 40 px
    // all the same: a browser brings what it gives the focus clear of the room the page
    // keeps at its foot for the bar of areas, and no bar was there.
    const high = window.innerHeight;
    Object.defineProperty(window, "innerHeight", { configurable: true, value: 900 });
    const page = aPage(3368);
    const measure = inTheWindow({ map: [16, 880], card: [485, 764] });
    try {
      const card = await chosenElsewhere();
      page.says();

      page.goes(40);
      act(() => card.focus());

      expect(card).toHaveFocus();
      expect(page.asked).toEqual([-40]);
    } finally {
      measure.mockRestore();
      page.putBack();
      Object.defineProperty(window, "innerHeight", { configurable: true, value: high });
    }
  });

  test("test_where_the_box_is_out_of_sight_the_page_goes_to_the_map_once_and_by_no_more_than_it_must", async () => {
    // Seen at 390 by 844: the map stands a long way under the working of a result.
    const high = window.innerHeight;
    Object.defineProperty(window, "innerHeight", { configurable: true, value: 844 });
    const page = aPage(3813);
    const measure = inTheWindow({ map: [780, 1500], card: [1090, 1383] });
    try {
      const card = await chosenElsewhere();
      page.says();

      act(() => card.focus({ preventScroll: true }));

      // The foot of the box at the foot of the window: the map is over it, in sight.
      expect(page.asked).toEqual([1383 + 8 - 844]);
    } finally {
      measure.mockRestore();
      page.putBack();
      Object.defineProperty(window, "innerHeight", { configurable: true, value: high });
    }
  });

  test("test_the_focus_that_comes_to_what_the_box_holds_moves_nothing", async () => {
    const page = aPage(3813);
    const measure = inTheWindow({ map: [780, 1500], card: [1090, 1383] });
    try {
      const card = await chosenElsewhere();
      page.says();

      act(() => within(card).getByRole("button", { name: MAP_CARD.close }).focus());

      expect(page.asked).toEqual([]);
    } finally {
      measure.mockRestore();
      page.putBack();
    }
  });
});

describe("the table of the map, as it closes in a column that scrolls in itself", () => {
  beforeEach(() => setWebGL(true));
  afterEach(() => setWebGL(false));

  test("test_the_column_keeps_the_room_of_the_table_so_that_the_bar_stands_where_it_was_pressed", async () => {
    // Measured at 1440 by 900: "Table of all areas" was pressed at 428 to close the table,
    // and stood at 798 once it had: the column held less, and a browser scrolled it back.
    const measure = jest.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function (
      this: HTMLElement,
    ) {
      const isTheBar = this.tagName === "BUTTON" && this.textContent === TABLE.title;
      const [top, foot] = this.hasAttribute("data-column")
        ? [16, 884]
        : isTheBar
          ? this.getAttribute("aria-expanded") === "true"
            ? [428, 472]
            : [798, 842]
          : [900, 4800];
      return { top, bottom: foot, left: 0, right: 0, x: 0, y: top, width: 0, height: foot - top, toJSON: () => ({}) };
    });
    const told: Told = { selected: [], hovered: [], shown: [] };
    try {
      const { container } = render(
        <div data-column="" style={{ overflowY: "auto" }}>
          <Held ranking={first} told={told} />
        </div>,
      );
      const column = container.firstElementChild as HTMLElement;
      Object.defineProperty(column, "clientHeight", { configurable: true, value: 868 });
      Object.defineProperty(column, "scrollHeight", { configurable: true, value: 4973 });
      await arrived();
      act(() => lastMap().fire("load"));
      const bar = screen.getByRole("button", { name: TABLE.title });
      fireEvent.click(bar);
      column.scrollTop = 557;

      fireEvent.click(bar);

      expect(bar).toHaveAttribute("aria-expanded", "false");
      // As much as the bar went is kept at the foot of the column, which is scrolled as it was.
      expect(column.style.paddingBottom).toBe("370px");
      expect(column.scrollTop).toBe(557);
      // Opened again, the table has the room, and none is kept beside it.
      fireEvent.click(bar);
      expect(bar).toHaveAttribute("aria-expanded", "true");
      expect(column.style.paddingBottom).toBe("");
    } finally {
      measure.mockRestore();
    }
  });

  test("test_on_a_page_that_scrolls_as_a_whole_nothing_is_kept_as_the_table_closes", async () => {
    await show();
    const bar = screen.getByRole("button", { name: TABLE.title });

    fireEvent.click(bar);
    fireEvent.click(bar);

    expect(bar).toHaveAttribute("aria-expanded", "false");
    expect(document.querySelectorAll("[style*='padding']")).toHaveLength(0);
  });
});

describe("the look is one, whatever the system asks", () => {
  const asked: string[] = [];

  beforeEach(() => {
    setWebGL(true);
    asked.length = 0;
    Object.defineProperty(window, "matchMedia", {
      configurable: true,
      value: (query: string) => {
        asked.push(query);
        return { matches: false, media: query, addEventListener: () => undefined, removeEventListener: () => undefined };
      },
    });
  });

  afterEach(() => {
    setWebGL(false);
    delete (window as { matchMedia?: unknown }).matchMedia;
  });

  test("test_the_map_does_not_ask_the_system_whether_it_prefers_dark", async () => {
    // The look has no dark colours. The map once listened for the system turning dark, and
    // drew itself again in colours that are now the same either way.
    const { again, unmount } = await show(refined);
    again(first);
    await arrived();
    fireEvent.click(pins()[0] as HTMLElement);
    unmount();

    expect(asked.filter((query) => /prefers-color-scheme/.test(query))).toEqual([]);
    // Nor does any file of the map: not its component, and not its style.
    for (const file of ["MapView.tsx", "MapCard.tsx", "MapControls.tsx", "MapLegend.tsx", "MapView.module.css", "../../lib/map/style.ts"]) {
      expect([file, /prefers-color-scheme|light-dark\(/.test(readFileSync(path.join(__dirname, file), "utf8"))]).toEqual([file, false]);
    }
  });
});
