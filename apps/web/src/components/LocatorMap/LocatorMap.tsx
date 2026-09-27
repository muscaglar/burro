import { LOCATOR } from "@/content/search";
import type { GeometryData } from "@/lib/api/schema";
import { CITY_FRAME, CLOSE_FRAME, locate } from "@/lib/map/locate";
import { boundsOf, pathOf, projector, type Frame } from "@/lib/map/project";

import styles from "./LocatorMap.module.css";

/** The size a picture of every area is drawn at. It is scaled to the room it is given. */
export const LOCATOR_FRAME: Frame = { width: 160, height: 120, padding: 4 };

export interface Outline {
  readonly areaId: string;
  /** The outline of the area, as the path of an SVG. */
  readonly path: string;
}

/**
 * The outline of every area, drawn flat in one frame. It is worked out once
 * for a release and handed to every picture that colours every area.
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
  /** The boundary of every area. `null` while it is not in hand. */
  readonly geometry: GeometryData | null;
  readonly areaId: string;
  /** The area's name, as the API gave it. It names the picture. */
  readonly name: string;
}

/** How far from the place each side of its mark stands, in pixels. */
const MARK = { out: 6 } as const;

/**
 * The mark: one square about the middle of the picture it is drawn in, drawn in one piece
 * and closed. It was four corners with a gap between each and the next, as the pointer of
 * a map in a game is drawn: an edge in pieces, which a person who walked the website did
 * not understand.
 */
const SQUARE = `M${-MARK.out} ${-MARK.out}H${MARK.out}V${MARK.out}H${-MARK.out}Z`;

/**
 * Two small pictures of where one area is. The first is the whole city as one
 * shape, with a square about the place the area stands and a spot in the
 * middle of it. The second is the area drawn close, among the
 * areas around it, and told from them by its heavy outline as well as its
 * colour, which is that of the thing in hand.
 *
 * It was one picture of every area, 120 px wide, and on a release of a
 * thousand areas the area could not be found in it.
 *
 * They are pictures and no more: they take no key and no pointer, and they
 * are named once, together, for whoever hears the page.
 */
export function LocatorMap({ geometry, areaId, name }: Props) {
  const found = geometry === null ? null : locate(geometry, areaId);
  if (found === null) return null;
  // The mark is drawn to the whole pixel, so that its sides have a hard edge.
  const [x, y] = [Math.round(found.at[0]), Math.round(found.at[1])];
  return (
    <div className={styles.locator} role="img" aria-label={LOCATOR.title(name)}>
      <figure className={styles.picture}>
        <svg
          className={styles.city}
          viewBox={`0 0 ${CITY_FRAME.width} ${CITY_FRAME.height}`}
          width={CITY_FRAME.width}
          height={CITY_FRAME.height}
          aria-hidden="true"
        >
          {/* The water is under the picture, and is the style sheet's to draw. */}
          <path className={styles.land} d={found.city} />
          <g data-mark="" transform={`translate(${x} ${y})`}>
            <path className={styles.ring} d={SQUARE} />
            <rect className={styles.spot} x="-1" y="-1" width="2" height="2" />
          </g>
        </svg>
        <figcaption>{LOCATOR.city}</figcaption>
      </figure>
      <figure className={styles.picture}>
        <svg
          className={styles.close}
          viewBox={`0 0 ${CLOSE_FRAME.width} ${CLOSE_FRAME.height}`}
          width={CLOSE_FRAME.width}
          height={CLOSE_FRAME.height}
          aria-hidden="true"
        >
          {found.around.map((outline) => (
            <path key={outline.areaId} className={styles.area} d={outline.path} />
          ))}
          <path className={styles.here} d={found.here.path} />
        </svg>
        <figcaption>{LOCATOR.close}</figcaption>
      </figure>
    </div>
  );
}
