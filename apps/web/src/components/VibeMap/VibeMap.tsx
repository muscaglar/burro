import { useId } from "react";

import type { BandMark } from "@/lib/api/schema";
import { fillForVibe } from "@/lib/map/fill";
import type { Frame } from "@/lib/map/project";

import type { Outline } from "../LocatorMap/LocatorMap";
import styles from "./VibeMap.module.css";

/** The size the picture is drawn at. It is scaled to the room it is given. */
export const VIBE_MAP_FRAME: Frame = { width: 200, height: 150, padding: 4 };

interface Props {
  /** The outline of every area, from `outlinesOf(geometry, VIBE_MAP_FRAME)`. */
  readonly outlines: readonly Outline[];
  /** The band of every area on the vibe, from route 4. */
  readonly marks: readonly BandMark[];
  /**
   * What the picture shows, in words: the vibe, and the two ends its bands run between. Left
   * out where the picture stands beside those words, and it is then kept from a screen
   * reader, which would hear them twice.
   */
  readonly title?: string;
  /**
   * Where the outlines are drawn once for the whole page, the beginning of the id each is
   * drawn under (`SharedOutlines`). The map then points at each outline and draws none of
   * its own. A page of many maps once held the outline of every area once for every map.
   */
  readonly shared?: string;
}

/** The id an outline is drawn under, where a page draws it once for all its maps. */
const sharedId = (shared: string, areaId: string) => `${shared}-${areaId}`;

/**
 * The outline of every area, drawn once and shown nowhere: each map of the page points at
 * them. It takes no room and is kept from a screen reader.
 */
export function SharedOutlines({ outlines, id }: { readonly outlines: readonly Outline[]; readonly id: string }) {
  if (outlines.length === 0) return null;
  return (
    <svg className={styles.shared} width="0" height="0" aria-hidden="true" focusable="false">
      <defs>
        {outlines.map((outline) => (
          <path key={outline.areaId} id={sharedId(id, outline.areaId)} d={outline.path} />
        ))}
      </defs>
    </svg>
  );
}

/**
 * The city coloured by one vibe, in the five bands the API gives: the lighter
 * the nearer the low end. An area the vibe cannot place is drawn with dots,
 * and never in the middle band. It is a picture and no more: it takes no key
 * and no pointer, its title says what it shows, and the areas at each end are
 * named in words beside it, because one band is too like the next to read a
 * band from.
 *
 * It is drawn on the server, from what came with the page. Nobody is told
 * which vibe a person looks at.
 */
export function VibeMap({ outlines, marks, title, shared }: Props) {
  // A name of its own for the pattern of dots, made of letters alone so that it can be pointed at.
  const id = `vibe-map-${useId().replace(/[^A-Za-z0-9]/g, "")}`;
  if (outlines.length === 0) return null;
  const fills = fillForVibe(marks);
  const { width, height } = VIBE_MAP_FRAME;
  return (
    <svg
      className={styles.map}
      viewBox={`0 0 ${width} ${height}`}
      width={width}
      height={height}
      {...(title === undefined ? { "aria-hidden": true } : { role: "img", "aria-labelledby": `${id}-title` })}
    >
      {title === undefined ? null : <title id={`${id}-title`}>{title}</title>}
      <defs>
        <pattern id={`${id}-dots`} width="4" height="4" patternUnits="userSpaceOnUse">
          <rect className={styles.land} width="4" height="4" />
          <circle className={styles.dot} cx="2" cy="2" r="0.7" />
        </pattern>
      </defs>
      <rect className={styles.water} width={width} height={height} />
      {outlines.map((outline) => {
        const band = fills.get(outline.areaId)?.band ?? 0;
        if (shared !== undefined) {
          return (
            <use
              key={outline.areaId}
              className={styles.area}
              data-area={outline.areaId}
              data-band={band === 0 ? "none" : band}
              href={`#${sharedId(shared, outline.areaId)}`}
              {...(band === 0 ? { fill: `url(#${id}-dots)` } : {})}
            />
          );
        }
        return band === 0 ? (
          <path
            key={outline.areaId}
            className={styles.area}
            data-area={outline.areaId}
            data-band="none"
            fill={`url(#${id}-dots)`}
            d={outline.path}
          />
        ) : (
          <path key={outline.areaId} className={styles.area} data-area={outline.areaId} data-band={band} d={outline.path} />
        );
      })}
    </svg>
  );
}
