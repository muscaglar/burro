import { readFileSync } from "node:fs";
import path from "node:path";

import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { useState } from "react";

import { COMPARE } from "@/content/compare";
import { LEGEND, MAP, MAP_CARD, TABLE } from "@/content/map";
import { COMPLETENESS, FILTERED, UNRANKED } from "@/content/search";
import { PIN_ROOM } from "@/lib/map/pins";
import { recordedAnswer } from "@/lib/api/recorded";
import type { RankData, RankedArea } from "@/lib/api/schema";
import { fillFor, fillForVibe, idsBy } from "@/lib/map/fill";
import { LAYER, PATTERN_IMAGE, SOURCE } from "@/lib/map/style";
import { paths } from "@/lib/paths";
import type { Lens } from "@/lib/vibes";

import { faultsIn } from "../../../test/support/axe";
import { isFor, rulesOf } from "../../../test/support/css";
import { lastMap, mapsMade } from "../../../test/support/maplibre";
import { arrived, setWebGL } from "../../../test/support/search";
import { AreaTable } from "../AreaTable/AreaTable";
import { MapView } from "./MapView";

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
    expect([...lastMap().images].sort()).toEqual(Object.values(PATTERN_IMAGE).sort());
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

  test("test_a_pin_that_is_pressed_keeps_the_focus", async () => {
    // Seen in a browser: after a pin was pressed the focus was on nothing, because the map
    // takes the press for its own and the pin never took the focus.
    await show();

    fireEvent.click(pins()[2] as HTMLElement);

    expect(document.activeElement).toBe(pins()[2]);
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
    // The pin that was pressed has the focus, so its area is outlined as one under the focus is.
    expect(lastMap().states.get("syn-n0008")).toEqual({ hovered: true, selected: true });
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
    for (const button of controls.getAllByRole("button")) expect(button).toHaveClass("target-min");
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

  test("test_the_legend_names_the_vibe_and_both_its_ends", async () => {
    await show(null, lensOf("pace"));
    const legend = within(screen.getByRole("region", { name: LEGEND.title }));

    expect(legend.getByText(LEGEND.vibe("Going out"))).toBeInTheDocument();
    expect(legend.getAllByRole("listitem").map((item) => item.textContent)).toEqual([
      LEGEND.vibeEnd(1, "Calm"),
      LEGEND.vibeBand(2),
      LEGEND.vibeBand(3),
      LEGEND.vibeBand(4),
      LEGEND.vibeEnd(5, "Buzzy"),
      LEGEND.notPlaced,
    ]);
  });

  test("test_a_vibe_that_runs_one_way_is_counted_from_least_to_most", async () => {
    await show(null, lensOf("leafy"));
    const legend = within(screen.getByRole("region", { name: LEGEND.title }));

    expect(legend.getByText(LEGEND.vibeEnd(1, "least"))).toBeInTheDocument();
    expect(legend.getByText(LEGEND.vibeEnd(5, "most"))).toBeInTheDocument();
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
    expect(card.getByText(`Going out: varies within this area, from band ${mixed.spread_low} to band ${mixed.spread_high} of 5`)).toBeInTheDocument();

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

  test("test_the_map_is_a_strip_as_high_as_the_design_says_and_the_whole_of_it_is_one_press_away", async () => {
    await show();
    const frame = STYLES.filter((rule) => isFor(rule.selector, "frame") && rule.under === null);

    // 240 px: docs/design/web.md, section 6. It was 176 while the strip stood above the first
    // result. It stands after it now, so it is as high as ten pins need to stand apart.
    expect(frame.map((rule) => rule.sets.get("height")).filter(Boolean)).toEqual(["240px", "70vh"]);
    const whole = screen.getByRole("button", { name: MAP.taller });
    expect(whole).toHaveAttribute("aria-pressed", "false");

    fireEvent.click(whole);

    expect(screen.getByRole("button", { name: MAP.shorter })).toHaveAttribute("aria-pressed", "true");
  });

  test("test_on_a_narrow_screen_a_pin_is_smaller_so_that_ten_stand_apart_and_is_still_as_big_as_a_target", () => {
    // Seen on a phone: pins of 28 px on a strip 174 px high, where pins 1, 3 and 4 lay over
    // one another by 1 to 3 px.
    const pin = STYLES.filter((rule) => narrow(rule) && isFor(rule.selector, "pin") && !/aria-current/.test(rule.selector));

    expect(pin.map((rule) => [rule.sets.get("width"), rule.sets.get("height")])).toEqual([["24px", "24px"]]);
    // 24 px is the least a thing that is pressed may be: docs/design/web.md, section 8.
    expect(readFileSync(path.resolve(__dirname, "../../styles/tokens.css"), "utf8")).toMatch(/--target-min:\s*24px/);
  });

  test("test_what_moves_the_map_and_what_explains_it_wait_with_the_whole_map", () => {
    const waits = STYLES.filter((rule) => narrow(rule) && rule.sets.get("display") === "none");

    expect(waits.map((rule) => rule.selector).join(" ")).toMatch(/data-taller="false".*under/);
    expect(waits.map((rule) => rule.selector).join(" ")).toMatch(/data-taller="false".*legend/);
    // The table says everything the map does, and is one press away either way.
    expect(waits.map((rule) => rule.selector).join(" ")).not.toMatch(/table|more/);
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

describe("the map, when the system turns dark or light", () => {
  let turn: (() => void) | null = null;

  beforeEach(() => {
    setWebGL(true);
    Object.defineProperty(window, "matchMedia", {
      configurable: true,
      value: (query: string) => ({
        matches: false,
        media: query,
        addEventListener: (_: string, listener: () => void) => {
          if (query.includes("prefers-color-scheme")) turn = listener;
        },
        removeEventListener: () => {
          if (query.includes("prefers-color-scheme")) turn = null;
        },
      }),
    });
  });

  afterEach(() => {
    setWebGL(false);
    delete (window as { matchMedia?: unknown }).matchMedia;
  });

  test("test_the_map_is_drawn_again_in_the_colours_of_the_page", async () => {
    await show(refined);
    const before = lastMap().calls.length;
    document.documentElement.style.setProperty("--map-water", "#0c2735");
    document.documentElement.style.setProperty("--map-line", "#eef0f1");

    act(() => turn?.());

    const since = lastMap().calls.slice(before);
    expect(since.filter((call) => call.method === "setPaintProperty").map((call) => call.args.slice(0, 2))).toEqual([
      [LAYER.water, "background-color"],
      [LAYER.outline, "line-color"],
      [LAYER.fill, "fill-color"],
    ]);
    // The patterns are drawn again too, in the new colour of the outlines.
    expect(since.filter((call) => call.method === "addImage").map((call) => call.args[0]).sort()).toEqual(
      Object.values(PATTERN_IMAGE).sort(),
    );
    document.documentElement.removeAttribute("style");
  });

  test("test_the_map_stops_listening_when_the_page_is_left", async () => {
    const { unmount } = await show(refined);
    expect(turn).not.toBeNull();

    unmount();

    expect(turn).toBeNull();
  });
});
