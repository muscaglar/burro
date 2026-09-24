import { useId } from "react";

import { LOCATOR } from "@/content/search";
import type { GeometryData } from "@/lib/api/schema";
import { boundsOf, pathOf, projector, type Frame } from "@/lib/map/project";

import styles from "./LocatorMap.module.css";

/** The size the picture is drawn at. It is scaled to the room it is given. */
export const LOCATOR_FRAME: Frame = { width: 160, height: 120, padding: 4 };

export interface Outline {
  readonly areaId: string;
  /** The outline of the area, as the path of an SVG. */
  readonly path: string;
}

/**
 * The outline of every area, drawn flat in one frame. It is worked out once
 * for a release and handed to every picture, because each picture draws
 * every area.
 */
export function outlinesOf(geometry: GeometryData, frame: Frame = LOCATOR_FRAME): readonly Outline[] {
  const bounds = boundsOf(geometry);
  if (bounds === null) return [];
  const project = projector(bounds, frame);
  return geometry.features.map((feature) => ({
    areaId: feature.properties.area_id,
    path: pathOf(feature.geometry, project),
  }));
}

interface Props {
  readonly outlines: readonly Outline[];
  readonly areaId: string;
  /** The area's name, as the API gave it. It names the picture. */
  readonly name: string;
}

/**
 * A small picture of where one area is among the rest. It is a picture and
 * no more: it takes no key and no pointer, and its title says what it shows.
 * The area is told from the rest by its heavy outline as well as its colour.
 */
export function LocatorMap({ outlines, areaId, name }: Props) {
  const id = useId();
  if (!outlines.some((outline) => outline.areaId === areaId)) return null;
  const { width, height } = LOCATOR_FRAME;
  return (
    <svg
      className={styles.locator}
      viewBox={`0 0 ${width} ${height}`}
      width={width}
      height={height}
      role="img"
      aria-labelledby={`${id}-title`}
    >
      <title id={`${id}-title`}>{LOCATOR.title(name)}</title>
      <rect className={styles.water} width={width} height={height} />
      {outlines
        .filter((outline) => outline.areaId !== areaId)
        .map((outline) => (
          <path key={outline.areaId} className={styles.area} d={outline.path} />
        ))}
      {outlines
        .filter((outline) => outline.areaId === areaId)
        .map((outline) => (
          <path key={outline.areaId} className={styles.here} d={outline.path} />
        ))}
    </svg>
  );
}
