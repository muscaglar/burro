"use client";

import type { Map as MapLibreMap, Marker as MapLibreMarker } from "maplibre-gl";
import {
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  useSyncExternalStore,
  type ReactNode,
} from "react";

import { MAP } from "@/content/map";
import { RESULTS } from "@/content/search";
import type {
  AreaSummary,
  Filtered,
  GeometryData,
  RankedArea,
  Score,
  Unranked,
} from "@/lib/api/schema";
import { fillFor, fitOf, PINS } from "@/lib/map/fill";
import { boundsOf } from "@/lib/map/project";
import {
  addPatterns,
  applyFills,
  applyTheme,
  buildStyle,
  LAYER,
  markArea,
  themeOfPage,
} from "@/lib/map/style";
import { canDrawMap, prefersReducedMotion } from "@/lib/map/webgl";

import { basedOn } from "../AreaTable/AreaTable";
import { MapCard } from "./MapCard";
import { MapControls } from "./MapControls";
import { MapLegend } from "./MapLegend";
import styles from "./MapView.module.css";

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
  /** What stands in for the map where it cannot be drawn: the table. */
  readonly fallback: ReactNode;
}

const never = () => () => undefined;

type Library = { Map: typeof MapLibreMap; Marker: typeof MapLibreMarker };

/** The room left round the areas when the whole city is shown. */
const PADDING = 24;

/**
 * The map: the areas drawn from the API's own geometry, on a plain
 * background, with no basemap and nothing fetched from any host.
 *
 * It says nothing the page does not also say in words. Rank is the number in
 * a pin. Fit is a band of colour whose range the legend gives in figures. An
 * area with no rank carries a pattern, and its reason is in the card and in
 * the table. Where the browser cannot draw it, it is not started at all, and
 * the table is shown with a line saying why.
 *
 * The list and the map are in step: what is under the pointer or the focus
 * in one is outlined in the other, and what is chosen in one is chosen in
 * the other.
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
  fallback,
}: Props) {
  const id = useId();
  const container = useRef<HTMLDivElement>(null);
  const held = useRef<{ map: MapLibreMap; library: Library } | null>(null);
  const marked = useRef<{ selected: string | null; hovered: string | null }>({
    selected: null,
    hovered: null,
  });
  const told = useRef({ onSelect, onHover });
  // True once the person has moved the map, by hand, by key or with a button. Until then
  // the map is the page's to fit to its frame.
  const movedByHand = useRef(false);
  // The geometry the map is ready to draw. It is ready when this is the geometry in hand.
  const [readyFor, setReadyFor] = useState<GeometryData | null>(null);
  const [broken, setBroken] = useState(false);
  // Not known on the server. In the browser it is asked once.
  const drawable = useSyncExternalStore(never, canDrawMap, () => null);
  const ready = geometry !== null && readyFor === geometry;

  const fills = useMemo(
    () => fillFor(scores, filtered, unranked, emptySpec),
    [scores, filtered, unranked, emptySpec],
  );
  const bounds = useMemo(() => (geometry ? boundsOf(geometry) : null), [geometry]);

  useEffect(() => {
    told.current = { onSelect, onHover };
  });

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
        const still = prefersReducedMotion();
        const around = boundsOf(geometry);
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
          ...(around ? { bounds: [around[0], around[1]] as [[number, number], [number, number]] } : {}),
          fitBoundsOptions: { padding: PADDING },
        });
        const made = map;
        made.touchZoomRotate?.disableRotation();
        made.keyboard?.disableRotation();

        const canvas = made.getCanvas();
        canvas.setAttribute("aria-label", MAP.label);
        canvas.setAttribute("aria-describedby", `${id}-keys`);

        const areaOf = (event: { features?: readonly { id?: unknown }[] }) => {
          const areaId = event.features?.[0]?.id;
          return typeof areaId === "string" ? areaId : null;
        };
        made.on("click", LAYER.fill, (event) => told.current.onSelect(areaOf(event)));
        made.on("mousemove", LAYER.fill, (event) => {
          canvas.style.cursor = "pointer";
          told.current.onHover(areaOf(event));
        });
        made.on("mouseleave", LAYER.fill, () => {
          canvas.style.cursor = "";
          told.current.onHover(null);
        });
        made.on("styleimagemissing", () => addPatterns(made, theme));
        // A move a person made comes with the event that made it. One the page made does not.
        made.on("movestart", (event: { originalEvent?: unknown }) => {
          if (event.originalEvent !== undefined) movedByHand.current = true;
        });
        // The map keeps its centre when its frame changes size, as when a window is made
        // narrower or a phone is turned on its side, and areas were then left outside the
        // frame. While nobody has moved it, it is fitted to the frame again.
        made.on("resize", () => {
          if (movedByHand.current || !around) return;
          made.fitBounds([around[0], around[1]] as [[number, number], [number, number]], {
            padding: PADDING,
            animate: false,
          });
        });
        made.once("load", () => {
          if (stopped) return;
          movedByHand.current = false;
          addPatterns(made, theme);
          held.current = { map: made, library };
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
  }, [drawable, geometry, id]);

  // Colour the areas by the ranking, and draw them again if the system turns dark or light.
  useEffect(() => {
    const element = container.current;
    if (!ready || held.current === null || element === null) return;
    const { map } = held.current;
    applyFills(map, fills, themeOfPage(element));
    if (typeof matchMedia !== "function") return;
    const scheme = matchMedia("(prefers-color-scheme: dark)");
    const redraw = () => applyTheme(map, fills, themeOfPage(element));
    scheme.addEventListener("change", redraw);
    return () => scheme.removeEventListener("change", redraw);
  }, [ready, fills]);

  // A numbered pin on each of the first ten, in rank order.
  useEffect(() => {
    if (!ready || held.current === null || emptySpec) return;
    const { map, library } = held.current;
    const pins = ranked.slice(0, PINS).flatMap((area) => {
      const summary = areas.find((known) => known.area_id === area.area_id);
      if (!summary) return [];
      const button = document.createElement("button");
      button.type = "button";
      button.className = `${styles.pin} target-min`;
      button.textContent = String(area.rank);
      button.dataset.area = area.area_id;
      button.setAttribute(
        "aria-label",
        // A fit that rests on part of what counts says so wherever it is given.
        MAP.pin(area.rank, summary.name, RESULTS.fitOf(fitOf(area.score)), basedOn(area)),
      );
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        // The map takes a press for its own, so a pin that is pressed is given the focus
        // here. Left to the browser, the focus was on nothing once the pin was pressed.
        button.focus({ preventScroll: true });
        told.current.onSelect(area.area_id);
      });
      button.addEventListener("focus", () => told.current.onHover(area.area_id));
      button.addEventListener("blur", () => told.current.onHover(null));
      const [longitude, latitude] = summary.centroid;
      return [new library.Marker({ element: button }).setLngLat([longitude, latitude]).addTo(map)];
    });
    return () => pins.forEach((pin) => pin.remove());
  }, [ready, ranked, areas, emptySpec]);

  // The chosen area and the one under the pointer are outlined. The chosen pin is larger and says so.
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
    }
  }, [ready, selectedId, hoveredId, ranked]);

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

  if (geometryFailed || drawable === false || broken) {
    return (
      <div className={styles.without}>
        <p role="status">{geometryFailed ? MAP.noGeometry : MAP.noWebGL}</p>
        {fallback}
      </div>
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

  return (
    <div className={styles.view}>
      <div className={styles.frame}>
        {/* The size is set before the map is drawn, so that nothing moves when it is. */}
        <div ref={container} className={styles.map} data-ready={ready} />
        {ready ? null : (
          <p className={styles.loading} role="status">
            {MAP.loading}
          </p>
        )}
      </div>
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
          summary={chosen}
          scores={scores}
          filtered={filtered}
          unranked={unranked}
          emptySpec={emptySpec}
          ranked={ranked.find((area) => area.area_id === chosen.area_id)}
          onShowInList={() => onShowInList(chosen.area_id)}
          onClose={close}
        />
      ) : null}
      <MapLegend searched={scores.length + filtered.length + unranked.length > 0} emptySpec={emptySpec} />
    </div>
  );
}
