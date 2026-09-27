"use client";

import type { Map as MapLibreMap, Marker as MapLibreMarker } from "maplibre-gl";
import {
  useCallback,
  useEffect,
  useId,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  useSyncExternalStore,
  type FocusEvent,
  type KeyboardEvent,
  type ReactNode,
} from "react";

import { MAP, TABLE } from "@/content/map";
import { RESULTS } from "@/content/search";
import type {
  AreaSummary,
  Filtered,
  GeometryData,
  RankedArea,
  Score,
  Unranked,
} from "@/lib/api/schema";
import { fillFor, fillForVibe, fitOf, PINS } from "@/lib/map/fill";
import { apart } from "@/lib/map/pins";
import { extentsOf, linesOf, named, roomFor, typeOfPage, whole, type Box, type Name, type Room, type ToName } from "@/lib/map/labels";
import { boundsOf } from "@/lib/map/project";
import {
  addPatterns,
  applyFills,
  buildStyle,
  LAYER,
  markArea,
  pixelOfPage,
  ratioFor,
  themeOfPage,
  zoomOf,
  type MapTheme,
} from "@/lib/map/style";
import { canDrawMap, prefersReducedMotion } from "@/lib/map/webgl";
import { basedOn } from "@/lib/search/card";
import { bringIntoSight, bringIntoSightUnder, holdOffTheSecondPress, keepTheRoomOf, standsAt, type Stood } from "@/lib/sight";
import type { Lens } from "@/lib/vibes";

import { BAR_SAYS } from "../CompareTray/look";
import { Disclosure } from "../Disclosure/Disclosure";
import { Frame } from "../kit/Frame/Frame";
import { Press } from "../kit/Press/Press";
import { MapCard } from "./MapCard";
import { MapControls } from "./MapControls";
import { MapLegend } from "./MapLegend";
import styles from "./MapView.module.css";
import { NAMED, NAMES } from "./names";
import { pinDrawn } from "./pin";
import { fitFor, isStrip, PADDING } from "./strip";

interface Props {
  /** The boundary of every area. `null` while it is loading or when it could not be loaded. */
  readonly geometry: GeometryData | null;
  readonly geometryFailed?: boolean;
  readonly areas: readonly AreaSummary[];
  readonly scores: readonly Score[];
  readonly ranked: readonly RankedArea[];
  readonly filtered: readonly Filtered[];
  readonly unranked: readonly Unranked[];
  readonly emptySpec?: boolean;
  readonly selectedId: string | null;
  readonly hoveredId: string | null;
  readonly onSelect: (areaId: string | null) => void;
  readonly onHover: (areaId: string | null) => void;
  /** Shows the chosen area in the list. */
  readonly onShowInList: (areaId: string) => void;
  /**
   * The vibe the map is coloured by, and where each area sits on it. It is for before a
   * search: a ranking colours the map by fit, and no vibe is given then.
   */
  readonly lens?: Lens | null;
  /** The table that says everything the map does. It is one press away, under the map. */
  readonly table: ReactNode;
  /**
   * True where the map stands over the two ways in, before a search. On a screen of one
   * column it is then a low strip, as wide as the page, so that the box is on the first
   * screen with it: the whole of it is one press away, and the table with it. On a wide
   * screen it says nothing: the map stands beside the page, whole.
   */
  readonly low?: boolean;
}


const never = () => () => undefined;

/** The box that scrolls in itself and holds the map, as the column beside the answer does. `null` where none does. */
function columnOf(part: HTMLElement | null): HTMLElement | null {
  for (let holds = part?.parentElement ?? null; holds !== null && holds !== document.body; holds = holds.parentElement) {
    const { overflowY } = getComputedStyle(holds);
    if (overflowY === "auto" || overflowY === "scroll") return holds;
  }
  return null;
}

type Library = { Map: typeof MapLibreMap; Marker: typeof MapLibreMarker };

/** The map that is drawn, and what it is drawn in: its colours, and the size of a pixel of its grain. */
interface Held {
  readonly map: MapLibreMap;
  readonly library: Library;
  readonly theme: MapTheme;
  readonly pixel: number;
}

/** What takes a press or a finger on the map, each of which is the library's to switch on and off. */
const BY_HAND = ["dragPan", "scrollZoom", "touchZoomRotate", "doubleClickZoom", "boxZoom"] as const;

/** The bounds of a city, as the map library takes them. */
type Fitted = [[number, number], [number, number]];


/**
 * The map: the areas drawn from the API's own geometry, on a plain
 * background, with no basemap and nothing fetched from any host.
 *
 * It is drawn as the map of a gentle game, and is the map of a real city:
 * green land on blue water, each with the grain of its tile, a pin drawn in
 * pixels for each of the first ten, and the whole in a box. Nothing is drawn
 * on it that the data does not hold.
 *
 * It says nothing the page does not also say in words. Rank is the number in
 * a pin. Fit is a band of colour whose range the legend gives in figures. An
 * area with no rank carries a pattern, and its reason is in the card and in
 * the table. Where the browser cannot draw it, it is not started at all, and
 * the table is shown with a line saying why.
 *
 * An area is named on the map where there is room for the whole of its name,
 * so that a person who has never been to the city has their bearings: an area
 * of the first ten under its pin, and any other over itself. A name is never
 * cut, by its area or by the edge of the window the map is seen through, and
 * never lies over a pin or another name. The name is the release's own. It
 * takes no press and covers no area: the pointer goes through it to the area
 * under it.
 *
 * The list and the map are in step: what is under the pointer or the focus
 * in one is outlined in the other, and what is chosen in one is chosen in
 * the other.
 *
 * An area that is chosen on the map opens its card under the map, and the
 * page stays where it is: what was pressed stays under the hand. The pin says
 * that its card is open, and the card takes the focus, so that what it holds
 * is the next stop of a keyboard and is heard. "Show in the list" is what
 * takes a person to the result. Escape closes the card, as its button does,
 * and the focus goes back to the pin.
 *
 * An area may be shown on the map from elsewhere: by "Show on the map" in the
 * working of a result, and by "Show" in a row of the table. The card is then
 * given the focus by what was pressed, and the map brings itself into sight
 * with the card under it, by as little as must be: what was pressed goes
 * from under the hand once, to where a person looks for what they asked
 * for, and not at all where both are in sight already.
 *
 * On a screen of one column the map is a strip, and what shows the whole of
 * it stands over it, so that the button stays under the hand as the map
 * grows under it. A strip is for a glance: a finger that is drawn across it
 * scrolls the page, and moves no map. Before a search it is low, and the
 * city is drawn as wide as it.
 *
 * The table of all areas is one press away, at the foot of the box. Beside
 * the answer the map stands in a column that scrolls in itself, which holds
 * less once the table has closed: the column keeps the room of it, so that
 * the bar that closed it stands where it was pressed.
 */
export function MapView({
  geometry,
  geometryFailed = false,
  areas,
  scores,
  ranked,
  filtered,
  unranked,
  emptySpec = false,
  selectedId,
  hoveredId,
  onSelect,
  onHover,
  onShowInList,
  lens = null,
  table,
  low = false,
}: Props) {
  const id = useId();
  // On a narrow screen the map is a strip above the list, and the whole of it is one press away.
  const [taller, setTaller] = useState(false);
  const container = useRef<HTMLDivElement>(null);
  const held = useRef<Held | null>(null);
  const marked = useRef<{ selected: string | null; hovered: string | null }>({
    selected: null,
    hovered: null,
  });
  const told = useRef({ onSelect, onHover });
  // True once the person has moved the map, by hand, by key or with a button. Until then
  // the map is the page's to fit to its frame.
  const movedByHand = useRef(false);
  // The card of the area that is chosen, and whether it was chosen on the map itself: by
  // its pin, by key or by pointer, or by its ground.
  const card = useRef<HTMLElement>(null);
  const onTheMap = useRef(false);
  // The box of the map, with all that is said of it.
  const view = useRef<HTMLDivElement>(null);
  // True while the map itself gives the card the focus, of a press on the map.
  const ours = useRef(false);
  // How far the page and the column of the map were scrolled, as a browser last said so.
  const scrolled = useRef({ page: 0, column: 0 });
  // Whether the table of all areas is open, where it stood as it was pressed to close it,
  // and what gives up the room that is kept of it.
  const [tableOpen, setTableOpen] = useState(false);
  const fold = useRef<HTMLDivElement>(null);
  const closing = useRef<Stood | null>(null);
  const kept = useRef<(() => void) | null>(null);
  // The area that is chosen, as the map was last drawn: what is pressed on the map is not drawn by the page.
  const chosenNow = useRef(selectedId);
  // The geometry the map is ready to draw. It is ready when this is the geometry in hand.
  const [readyFor, setReadyFor] = useState<GeometryData | null>(null);
  const [broken, setBroken] = useState(false);
  // Not known on the server. In the browser it is asked once.
  const drawable = useSyncExternalStore(never, canDrawMap, () => null);
  const ready = geometry !== null && readyFor === geometry;

  const fills = useMemo(
    () => (lens === null ? fillFor(scores, filtered, unranked, emptySpec) : fillForVibe(lens.marks)),
    [lens, scores, filtered, unranked, emptySpec],
  );
  const bounds = useMemo(() => (geometry ? boundsOf(geometry) : null), [geometry]);
  const extents = useMemo(() => (geometry ? extentsOf(geometry) : null), [geometry]);

  useEffect(() => {
    told.current = { onSelect, onHover };
    chosenNow.current = selectedId;
  });

  /**
   * An area is chosen on the map itself, by its pin or by its ground. Its card then takes
   * the focus as it opens. Where it is the area whose card is open already, nothing is
   * chosen anew, and the card takes the focus at once.
   */
  const chooseHere = useCallback((areaId: string | null) => {
    if (areaId !== null && areaId === chosenNow.current) {
      ours.current = true;
      card.current?.focus({ preventScroll: true });
      ours.current = false;
      return;
    }
    onTheMap.current = areaId !== null;
    told.current.onSelect(areaId);
  }, []);

  // Start the map, once it is known that it can be drawn and there is something to draw.
  useEffect(() => {
    const element = container.current;
    if (drawable !== true || geometry === null || element === null) return;
    let stopped = false;
    let map: MapLibreMap | null = null;

    void (async () => {
      try {
        const library: Library = await import("@/lib/map/library");
        if (stopped) return;
        const theme = themeOfPage(element);
        const pixel = pixelOfPage(element);
        const still = prefersReducedMotion();
        const around = boundsOf(geometry);
        /** How wide and how high the window of the map is, as it is laid out now. */
        const windowOf = () => ({ width: element.clientWidth, height: element.clientHeight });
        /** What the map is fitted to in its window: the whole city, or in a strip the city as wide as it. */
        const fitted = () => {
          if (!around) return null;
          const { bounds: to, padding } = fitFor(around, windowOf());
          return { bounds: [[...to[0]], [...to[1]]] as Fitted, padding };
        };
        const first = fitted();
        map = new library.Map({
          container: element,
          style: buildStyle(theme, geometry),
          // No basemap, so nobody to credit. A basemap brings its credit with it.
          attributionControl: false,
          dragRotate: false,
          pitchWithRotate: false,
          touchPitch: false,
          rollEnabled: false,
          renderWorldCopies: false,
          fadeDuration: still ? 0 : 200,
          ...(first ? { bounds: first.bounds, fitBoundsOptions: { padding: first.padding } } : {}),
        });
        const made = map;
        made.keyboard?.disableRotation();
        /**
         * A strip is for a glance, and stands where a finger scrolls the page: drawn across
         * it, a finger scrolls the page, and the wheel of a mouse does. The keys move the
         * map still, and an area is chosen by a press, as in any window. In any other
         * window the map is moved by hand as it was.
         */
        const byHand = () => {
          const strip = isStrip(windowOf());
          for (const name of BY_HAND) {
            if (strip) made[name]?.disable();
            else made[name]?.enable();
          }
          made.touchZoomRotate?.disableRotation();
        };
        byHand();

        const canvas = made.getCanvas();
        canvas.setAttribute("aria-label", MAP.label);
        canvas.setAttribute("aria-describedby", `${id}-keys`);

        const areaOf = (event: { features?: readonly { id?: unknown }[] }) => {
          const areaId = event.features?.[0]?.id;
          return typeof areaId === "string" ? areaId : null;
        };
        made.on("click", LAYER.fill, (event) => chooseHere(areaOf(event)));
        made.on("mousemove", LAYER.fill, (event) => {
          canvas.style.cursor = "pointer";
          told.current.onHover(areaOf(event));
        });
        made.on("mouseleave", LAYER.fill, () => {
          canvas.style.cursor = "";
          told.current.onHover(null);
        });
        made.on("styleimagemissing", () => addPatterns(made, theme, { zoom: zoomOf(made), pixel }));
        // A move a person made comes with the event that made it. One the page made does not.
        made.on("movestart", (event: { originalEvent?: unknown }) => {
          if (event.originalEvent !== undefined) movedByHand.current = true;
        });
        // The map keeps its centre when its frame changes size, as when a window is made
        // narrower or a phone is turned on its side, and areas were then left outside the
        // frame. While nobody has moved it, it is fitted to the frame again.
        made.on("resize", () => {
          byHand();
          const now = fitted();
          if (movedByHand.current || now === null) return;
          made.fitBounds(now.bounds, { padding: now.padding, animate: false });
        });
        made.once("load", () => {
          if (stopped) return;
          movedByHand.current = false;
          // Handed over again, for the map as it is drawn now: its frame may have changed
          // size, and the map with it, since a picture was first asked for.
          addPatterns(made, theme, { zoom: zoomOf(made), pixel }, true);
          held.current = { map: made, library, theme, pixel };
          marked.current = { selected: null, hovered: null };
          setReadyFor(geometry);
        });
      } catch {
        if (!stopped) setBroken(true);
      }
    })();

    return () => {
      stopped = true;
      held.current = null;
      map?.remove();
    };
  }, [drawable, geometry, id, chooseHere]);

  // Colour the areas by the ranking. The look is one, so the system is not asked which it prefers.
  useEffect(() => {
    if (!ready || held.current === null) return;
    const { map, theme } = held.current;
    applyFills(map, fills, theme);
  }, [ready, fills]);

  // The grain and the patterns are drawn in pixels of one size, however near the map is
  // drawn. The map library draws a pattern larger the nearer the map is, so each is handed
  // over again once the map has been drawn nearer or further.
  useEffect(() => {
    if (!ready || held.current === null) return;
    const { map, theme, pixel } = held.current;
    let drawn = ratioFor({ zoom: zoomOf(map), pixel });
    const again = () => {
      const scale = { zoom: zoomOf(map), pixel };
      if (Math.abs(ratioFor(scale) - drawn) < 0.001) return;
      drawn = ratioFor(scale);
      addPatterns(map, theme, scale, true);
    };
    map.on("zoomend", again);
    return () => {
      map.off("zoomend", again);
    };
  }, [ready]);

  // A numbered pin on each of the first ten, in rank order.
  useEffect(() => {
    if (!ready || held.current === null || emptySpec || lens !== null) return;
    const { map, library } = held.current;
    const pins = ranked.slice(0, PINS).flatMap((area) => {
      const summary = areas.find((known) => known.area_id === area.area_id);
      if (!summary) return [];
      const button = document.createElement("button");
      button.type = "button";
      button.className = `${styles.pin} target-min`;
      // The pin is a drawing, and its number is set in type on the face the drawing leaves bare.
      for (const [name, value] of Object.entries(pinDrawn())) button.style.setProperty(name, value);
      const figure = document.createElement("span");
      figure.className = styles.figure ?? "";
      figure.textContent = String(area.rank);
      button.append(figure);
      button.dataset.area = area.area_id;
      button.setAttribute(
        "aria-label",
        // A fit that rests on part of what counts says so wherever it is given.
        MAP.pin(
          area.rank,
          summary.name,
          RESULTS.fitOf(fitOf(area.score)),
          basedOn(scores.find((score) => score.area_id === area.area_id)),
        ),
      );
      // A pin opens the card of its area, and says whether it is open.
      button.setAttribute("aria-expanded", "false");
      button.setAttribute("aria-controls", `${id}-card`);
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        // The map takes a press for its own, so a pin that is pressed is given the focus
        // here. Left to the browser, the focus was on nothing once the pin was pressed.
        button.focus({ preventScroll: true });
        chooseHere(area.area_id);
      });
      const [longitude, latitude] = summary.centroid;
      button.addEventListener("focus", () => {
        told.current.onHover(area.area_id);
        // A pin that has left the window of the map, as the map was moved, is brought back
        // into it as it takes the focus: the focus is never where nothing is drawn.
        const { clientWidth: wide, clientHeight: high } = map.getContainer();
        const { x, y } = map.project([longitude, latitude]);
        if (wide > 0 && high > 0 && (x < 0 || y < 0 || x > wide || y > high)) {
          map.panTo([longitude, latitude], { animate: !prefersReducedMotion() });
        }
      });
      button.addEventListener("blur", () => told.current.onHover(null));
      return [
        {
          id: area.area_id,
          at: [longitude, latitude] as [number, number],
          // A pin stands on its place by its point, which is the middle of its foot.
          marker: new library.Marker({ element: button, anchor: "bottom" }).setLngLat([longitude, latitude]).addTo(map),
        },
      ];
    });
    // Two of the first ten may be next to each other, and from far off their pins would
    // stand on top of each other. The better ranked keeps its place, and the other is drawn
    // just beside it. It is worked out again when the map is drawn nearer or further.
    const spread = () => {
      const moved = apart(pins.map(({ id, at }) => ({ id, ...map.project(at) })));
      for (const { id, marker } of pins) {
        const [x, y] = moved.get(id) ?? [0, 0];
        marker.setOffset([x, y]);
        marker.getElement().toggleAttribute("data-moved", x !== 0 || y !== 0);
      }
    };
    spread();
    map.on("zoomend", spread);
    map.on("resize", spread);
    return () => {
      map.off("zoomend", spread);
      map.off("resize", spread);
      pins.forEach(({ marker }) => marker.remove());
    };
  }, [ready, ranked, scores, areas, emptySpec, lens, id, chooseHere]);

  // The name of each area that is named: under its pin where it has one, and else over the
  // middle of the area. They are worked out again when the map is drawn nearer or further,
  // and once it has been moved: a name that was whole may then meet the edge of the window.
  useEffect(() => {
    if (!ready || held.current === null || extents === null) return;
    const { map, library } = held.current;
    const first = emptySpec || lens !== null ? [] : ranked.slice(0, PINS);
    const rankOf = new Map(first.map((area, at) => [area.area_id, at]));
    // Those of the first ten in the order of their ranks, and then the rest in the order they came.
    const inOrder = [...areas].sort(
      (one, other) => (rankOf.get(one.area_id) ?? first.length) - (rankOf.get(other.area_id) ?? first.length),
    );
    /** The room of the window the map is seen through. `null` where it is not laid out. */
    const windowOf = (): Room | null => {
      const { clientWidth: width, clientHeight: height } = map.getContainer();
      return width > 0 && height > 0 ? { width, height } : null;
    };
    /** Where the middle of an area is in the window, in pixels. */
    const middleOf = ({ centroid: [longitude, latitude] }: AreaSummary) => {
      const { x, y } = map.project([longitude, latitude]);
      return { x, y };
    };
    let drawn: { readonly marker: MapLibreMarker; readonly name: Name; readonly at: [number, number] }[] = [];
    const draw = () => {
      for (const { marker } of drawn) marker.remove();
      // A pin may be drawn beside its area, and the name of the area stands under the pin.
      const moved = apart(
        inOrder.flatMap((area) => (rankOf.has(area.area_id) ? [{ id: area.area_id, ...middleOf(area) }] : [])),
      );
      const toName = inOrder.flatMap((area): ToName[] => {
        const extent = extents.get(area.area_id);
        if (extent === undefined) return [];
        const at = middleOf(area);
        const [one, other] = [map.project([extent.west, extent.north]), map.project([extent.east, extent.south])];
        const by = moved.get(area.area_id);
        return [
          {
            id: area.area_id,
            name: area.name,
            at,
            room: { width: Math.abs(other.x - one.x), height: Math.abs(other.y - one.y) },
            pin: by === undefined ? null : { x: at.x + by[0], y: at.y + by[1] },
          },
        ];
      });
      // A name is drawn as large as the type of the page, which a person may have made larger.
      const names = named(toName, windowOf(), { drawn: NAMES, by: NAMED, larger: typeOfPage() });
      drawn = names.flatMap((name) => {
        const area = areas.find((one) => one.area_id === name.id);
        if (area === undefined) return [];
        const label = document.createElement("span");
        label.className = styles.label ?? "";
        // It is for the eye. Whoever hears the page has the names in the table and on the pins.
        label.setAttribute("aria-hidden", "true");
        label.dataset.label = "";
        for (const words of linesOf(area.name)) {
          const line = document.createElement("span");
          line.textContent = words;
          label.append(line);
        }
        const [longitude, latitude] = area.centroid;
        const marker = new library.Marker({
          element: label,
          anchor: name.under ? "top" : "center",
          offset: [name.offset[0], name.offset[1]],
        })
          .setLngLat([longitude, latitude])
          .addTo(map);
        // The library says of whatever it is handed that it is a button named "Map marker".
        // A name is no button, and what it says is its own words.
        label.removeAttribute("role");
        label.removeAttribute("aria-label");
        return [{ marker, name, at: [longitude, latitude] as [number, number] }];
      });
    };
    // While the map is moved a name goes with the ground it is tied to, and may come to the
    // edge of the window. It is then not drawn, and never drawn cut: it keeps its place,
    // and is drawn again if it comes back whole before the map has come to rest.
    const keep = () => {
      const window = windowOf();
      const larger = typeOfPage();
      for (const { marker, name, at } of drawn) {
        const tied = map.project(at);
        const [x, y] = [tied.x + name.offset[0], tied.y + name.offset[1]];
        const area = areas.find((one) => one.area_id === name.id);
        const { width, height } = roomFor(area?.name ?? "", false, NAMES, larger);
        const box: Box = name.under
          ? { left: x - width / 2, top: y, right: x + width / 2, bottom: y + height }
          : { left: x - width / 2, top: y - height / 2, right: x + width / 2, bottom: y + height / 2 };
        marker.getElement().toggleAttribute("data-cut", !whole(box, window));
      }
    };
    draw();
    map.on("zoomend", draw);
    map.on("moveend", draw);
    map.on("resize", draw);
    map.on("move", keep);
    return () => {
      map.off("zoomend", draw);
      map.off("moveend", draw);
      map.off("resize", draw);
      map.off("move", keep);
      for (const { marker } of drawn) marker.remove();
    };
  }, [ready, extents, areas, ranked, emptySpec, lens]);

  // The chosen area and the one under the pointer are outlined. The chosen pin is amber and says so.
  useEffect(() => {
    if (!ready || held.current === null) return;
    const { map } = held.current;
    const was = marked.current;
    if (was.selected !== selectedId) {
      if (was.selected !== null) markArea(map, was.selected, "selected", false);
      if (selectedId !== null) markArea(map, selectedId, "selected", true);
    }
    if (was.hovered !== hoveredId) {
      if (was.hovered !== null) markArea(map, was.hovered, "hovered", false);
      if (hoveredId !== null) markArea(map, hoveredId, "hovered", true);
    }
    marked.current = { selected: selectedId, hovered: hoveredId };
    for (const pin of container.current?.querySelectorAll<HTMLElement>("[data-area]") ?? []) {
      if (pin.dataset.area === selectedId) pin.setAttribute("aria-current", "true");
      else pin.removeAttribute("aria-current");
      // The card of the area that is chosen is open, and no other.
      pin.setAttribute("aria-expanded", String(pin.dataset.area === selectedId));
    }
  }, [ready, selectedId, hoveredId, ranked]);

  // The card of an area that was chosen on the map takes the focus as it opens, so that a
  // keyboard goes on into it and whoever hears the page hears what opened: it opened seven
  // stops on from the pin, and nothing said so. The page stays where it is, and what was
  // pressed under the hand: where the head of the card is under the foot of what it is seen
  // through, it is brought up by as much as shows it. An area chosen in the list or in the
  // table leaves the focus where it was pressed.
  useLayoutEffect(() => {
    const chosenHere = onTheMap.current;
    onTheMap.current = false;
    if (!chosenHere || selectedId === null || card.current === null) return;
    const pressed =
      [...(container.current?.querySelectorAll<HTMLElement>("button[data-area]") ?? [])].find(
        (pin) => pin.dataset.area === selectedId,
      ) ?? container.current;
    ours.current = true;
    card.current.focus({ preventScroll: true });
    ours.current = false;
    if (pressed) bringIntoSight(card.current, pressed);
  }, [selectedId]);

  // How far the page and the column are scrolled is noted as a browser says so, which is
  // once it has drawn them there: so what is noted as the card takes the focus is where
  // they stood before the focus moved them.
  useEffect(() => {
    const note = () => {
      scrolled.current = { page: window.scrollY, column: columnOf(view.current)?.scrollTop ?? 0 };
    };
    note();
    window.addEventListener("scroll", note, { capture: true, passive: true });
    return () => window.removeEventListener("scroll", note, { capture: true });
  }, []);

  /**
   * The card takes the focus of a press elsewhere, which asked for its area to be shown on
   * the map. A browser that gives a thing the focus brings it into sight its own way: to
   * the middle of a box that scrolls, and clear of the room the page keeps at its foot
   * for the bar of areas, whether or not the bar is there. Measured at 1440 by 900, the
   * page went 40 px from under the press for a card that was in plain sight. So the page
   * and the column are put back where they stood, and the map is brought into sight with
   * the card under it, by as little as must be.
   */
  const onCardFocus = (event: FocusEvent<HTMLElement>) => {
    if (ours.current || event.target !== event.currentTarget || view.current === null) return;
    const column = columnOf(view.current);
    if (column !== null && column.scrollTop !== scrolled.current.column) column.scrollTop = scrolled.current.column;
    if (window.scrollY !== scrolled.current.page) window.scrollBy(0, scrolled.current.page - window.scrollY);
    const bar = document.getElementById(BAR_SAYS)?.closest("section") ?? null;
    const by = bringIntoSightUnder(view.current, event.currentTarget, bar);
    // What was pressed has gone from under the pointer, and the map may stand there.
    if (by !== 0) holdOffTheSecondPress(view.current);
  };

  /** The table is opened or closed. Where it stood is kept of the press that closes it. */
  const toggleTable = (open: boolean) => {
    const bar = fold.current?.querySelector<HTMLElement>("button[aria-expanded]") ?? null;
    closing.current = open || bar === null ? null : standsAt(bar);
    setTableOpen(open);
  };

  // Once the table is off the page, and before the page is drawn: the column keeps the
  // room of it. What is kept is given up as the table opens again, which has the room.
  useLayoutEffect(() => {
    const stood = closing.current;
    closing.current = null;
    if (!tableOpen && stood === null) return;
    kept.current?.();
    kept.current = tableOpen || stood === null ? null : keepTheRoomOf(stood);
  }, [tableOpen]);

  useEffect(() => () => kept.current?.(), []);

  // Nothing pans unless the chosen area is off screen.
  useEffect(() => {
    if (!ready || held.current === null || selectedId === null) return;
    const { map } = held.current;
    const centroid = areas.find((area) => area.area_id === selectedId)?.centroid;
    if (!centroid) return;
    const [longitude, latitude] = centroid;
    if (map.getBounds().contains([longitude, latitude])) return;
    map.panTo([longitude, latitude], { animate: !prefersReducedMotion() });
  }, [ready, selectedId, areas]);

  // The table says everything the map does. It is one press away, whether or not there is a map.
  // It stands at the foot of the box of the map. Beside the answer that is the foot of a
  // column that scrolls in itself, and what it opened began under it, out of sight.
  const theTable = (
    <div ref={fold} className={styles.fold}>
      <Disclosure label={TABLE.title} className={styles.table} open={tableOpen} onToggle={toggleTable} bring>
        {table}
      </Disclosure>
    </div>
  );

  if (geometryFailed || drawable === false || broken) {
    return (
      <Frame kind="box" className={styles.without}>
        <p role="status">{geometryFailed ? MAP.noGeometry : MAP.noWebGL}</p>
        <div className={styles.more}>{theTable}</div>
      </Frame>
    );
  }

  const move = (how: "in" | "out" | "whole") => {
    const map = held.current?.map;
    if (!map) return;
    const animate = !prefersReducedMotion();
    // "Show every area" fits the map, and it is then the page's to fit again. Nearer or
    // further is where the person put it.
    movedByHand.current = how !== "whole";
    if (how === "in") map.zoomIn({ animate });
    else if (how === "out") map.zoomOut({ animate });
    else if (bounds) {
      map.fitBounds([bounds[0], bounds[1]] as [[number, number], [number, number]], {
        padding: PADDING,
        animate,
      });
    }
  };

  const chosen = areas.find((area) => area.area_id === selectedId);

  // The card goes when it is closed, and its button with it. The focus goes back to what the
  // card was opened from: the pin of the area, or the map itself where the area has no pin.
  const close = () => {
    const pin = [...(container.current?.querySelectorAll<HTMLElement>("button[data-area]") ?? [])].find(
      (one) => one.dataset.area === selectedId,
    );
    (pin ?? held.current?.map.getCanvas())?.focus({ preventScroll: true });
    onSelect(null);
  };

  /** Escape closes the card from inside it, as its button does. */
  const onKeyDown = (event: KeyboardEvent<HTMLElement>) => {
    if (event.key !== "Escape") return;
    event.stopPropagation();
    close();
  };

  /**
   * Shows the whole of the map, or the strip again. The map is fitted to its window as
   * the window changes, whatever a key had moved it to: a person asked for the whole of it.
   */
  const showWhole = () => {
    movedByHand.current = false;
    setTaller(!taller);
  };

  return (
    // The map stands in a box, and so does all that is said of it: nothing is read on the grass.
    <Frame kind="box" bare ref={view} className={styles.view} data-taller={taller} data-low={low} data-names={NAMES}>
      {/* Drawn on a screen of one column only, where the map is a strip. It stands over the
          map, so that it stays where it was pressed as the map grows under it. It says
          whether the whole map is shown by being on, and keeps its name: with a name that
          turned as well it said "Show less of the map, pressed", and was wider for it. */}
      <div className={styles.whole}>
        <Press on={taller} onPress={showWhole}>
          {MAP.taller}
        </Press>
      </div>
      <div className={styles.window}>
        {/* The size is set before the map is drawn, so that nothing moves when it is. */}
        <div ref={container} className={styles.map} data-ready={ready} />
        {ready ? null : (
          <p className={styles.loading} role="status">
            {MAP.loading}
          </p>
        )}
      </div>
      <div className={styles.below}>
        {/* Under the map and not over it: a button laid over the map covers an area. The keys
            are said here for whoever can see the page, and to a screen reader by the map itself. */}
        <div className={styles.under}>
          <MapControls disabled={!ready} onMove={move} />
          <p id={`${id}-keys`} className={styles.keys}>
            {MAP.keys}
          </p>
        </div>
        {chosen ? (
          <MapCard
            ref={card}
            id={`${id}-card`}
            onKeyDown={onKeyDown}
            onFocus={onCardFocus}
            summary={chosen}
            scores={scores}
            filtered={filtered}
            unranked={unranked}
            emptySpec={emptySpec}
            inList={ranked.some((area) => area.area_id === chosen.area_id)}
            lens={lens}
            onShowInList={() => onShowInList(chosen.area_id)}
            onClose={close}
          />
        ) : null}
        <MapLegend
          searched={scores.length + filtered.length + unranked.length > 0}
          emptySpec={emptySpec}
          lens={lens}
          filtered={filtered.length > 0}
          unranked={unranked.length > 0}
        />
        <div className={styles.more}>{theTable}</div>
      </div>
    </Frame>
  );
}
