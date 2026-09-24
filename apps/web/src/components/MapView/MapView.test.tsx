import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { useState } from "react";

import { LEGEND, MAP, MAP_CARD, TABLE } from "@/content/map";
import { COMPLETENESS, FILTERED, UNRANKED } from "@/content/search";
import { recordedAnswer } from "@/lib/api/recorded";
import type { RankData, RankedArea } from "@/lib/api/schema";
import { fillFor, idsBy } from "@/lib/map/fill";
import { LAYER, PATTERN_IMAGE, SOURCE } from "@/lib/map/style";

import { faultsIn } from "../../../test/support/axe";
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
function pinName(area: RankedArea): string {
  const present = area.contributions.filter((part) => part.present).length;
  const asked = area.contributions.length;
  const name = `Rank ${area.rank}, ${nameOf(area.area_id)}, fit ${Math.floor(area.score)} of 100`;
  return present === asked ? name : `${name}. ${COMPLETENESS.some(present, asked)}`;
}

interface Told {
  selected: (string | null)[];
  hovered: (string | null)[];
  shown: string[];
}

/** The map and its table, held together as the page holds them. */
function Held({ ranking, told }: { ranking: RankData | null; told: Told }) {
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
      fallback={<AreaTable {...shared} searched={ranking !== null} />}
    />
  );
}

async function show(ranking: RankData | null = first) {
  const told: Told = { selected: [], hovered: [], shown: [] };
  const view = render(<Held ranking={ranking} told={told} />);
  await arrived();
  if (mapsMade().length > 0) act(() => lastMap().fire("load"));
  return { told, ...view, again: (next: RankData | null) => view.rerender(<Held ranking={next} told={told} />) };
}

const pins = () => [...lastMap().getCanvasContainer().querySelectorAll<HTMLButtonElement>("button")];

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
    await show();

    expect(pins().map((pin) => pin.textContent)).toEqual(["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]);
    expect(pins().map((pin) => pin.getAttribute("aria-label"))).toEqual(first.ranked.slice(0, 10).map(pinName));
    // Recorded: a fit of 80.99, which is said as 80 and never as 81.
    expect(pins()[0]).toHaveAccessibleName("Rank 1, Farrowmere, fit 80 of 100");
    // A pin stands at the centre of its area.
    const farrowmere = areas.find((area) => area.area_id === "syn-n0006");
    expect(lastMap().markers[0]?.position).toEqual(farrowmere?.centroid);
    for (const pin of pins()) expect(pin).toHaveClass("target-min");
  });

  test("test_the_pins_follow_the_ranking_when_it_changes", async () => {
    const { again } = await show();

    again(refined);
    await arrived();

    expect(pins().map((pin) => pin.getAttribute("aria-label"))).toEqual(refined.ranked.slice(0, 10).map(pinName));
  });

  test("test_a_pin_and_the_card_say_when_a_fit_rests_on_part_of_what_counts", async () => {
    // Seen in a browser: an area ranked first on 4 of the 8 things that count had a pin
    // and a card that gave its fit with nothing beside it.
    await show();
    const part = COMPLETENESS.some(5, 10);

    // Recorded: the area ranked second has a figure for 5 of the 10 things that count.
    expect(pins()[1]).toHaveAccessibleName(`Rank 2, Otterby Fields, fit 79 of 100. ${part}`);
    fireEvent.click(pins()[1] as HTMLElement);
    const card = within(screen.getByRole("region", { name: MAP_CARD.label }));
    expect(card.getByText(part)).toBeInTheDocument();

    // One that has a figure for everything says so on its card, and its pin says nothing more.
    expect(pins()[0]).toHaveAccessibleName("Rank 1, Farrowmere, fit 80 of 100");
    fireEvent.click(pins()[0] as HTMLElement);
    expect(card.getByText(COMPLETENESS.all)).toBeInTheDocument();
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

    expect(told.selected).toEqual(["syn-n0003"]);
    const card = within(screen.getByRole("region", { name: MAP_CARD.label }));
    expect(card.getByText("Cindermoor")).toBeInTheDocument();
    expect(card.getByText("Rank 3, fit 78 of 100")).toBeInTheDocument();
    expect(pins()[2]).toHaveAttribute("aria-current", "true");
    expect(pins().filter((pin) => pin.hasAttribute("aria-current"))).toHaveLength(1);
    // The pin that was pressed has the focus, so its area is outlined as one under the focus is.
    expect(lastMap().states.get("syn-n0003")).toEqual({ hovered: true, selected: true });
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

describe("the map, where the browser cannot draw it", () => {
  beforeEach(() => setWebGL(false));

  test("test_the_map_is_not_started_at_all_and_the_table_is_shown_with_a_line_saying_why", async () => {
    await show();

    expect(mapsMade()).toEqual([]);
    expect(screen.getByRole("status")).toHaveTextContent(MAP.noWebGL);
    expect(screen.getByRole("table", { name: TABLE.caption })).toBeInTheDocument();
    expect(screen.queryByRole("group", { name: MAP.controls })).toBeNull();
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
        fallback={<p>the table</p>}
      />,
    );
    await arrived();

    expect(mapsMade()).toEqual([]);
    expect(screen.getByRole("status")).toHaveTextContent(MAP.noGeometry);
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
