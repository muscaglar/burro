"use client";

import { useEffect, useRef, type CSSProperties } from "react";

import { framesOf, pictureOf, sizeOf, type Drawing } from "../drawings";
import styles from "./Burro.module.css";
import { watch } from "./onThePage";
import { DRAWING, soilOf, STILL_OF, stirsOf, type Pose } from "./poses";

interface Props {
  readonly pose: Pose;
  /** True where he stirs as he rests. Where he hops he moves whatever is said here. */
  readonly stirs: boolean;
  /** True where soil flies as he hops. Where he rests none does, whatever is said here. Left out, none flies. */
  readonly soil?: boolean;
  /** True where the page draws him, and false where what every page stands in does. Left out, the page draws him. */
  readonly ofThePage?: boolean;
}

/** What a style sheet needs of a drawing of him: where it is served from, how wide the whole of it is, and its frames. */
const drawn = (name: Drawing): CSSProperties =>
  ({
    "--art": `url("${pictureOf(name)}")`,
    "--strip": sizeOf(name).width,
    "--frames": framesOf(name),
  }) as CSSProperties;

/**
 * What is drawn of Burro, in his box. It is dress, and is kept from a screen reader.
 *
 * Where he moves, two drawings lie in his box and one of them is seen: him drawn still,
 * and the strip of what he does. The style sheet shows the strip while a movement runs,
 * and a movement whose length is nought never runs: so where nothing may move he is
 * drawn still, and nothing here has to know it.
 *
 * The soil that flies as he hops lies inside the strip of his hop, and over it. It is
 * moved by what moves that strip and is seen while that strip is seen: so it is never out
 * of step with him, and where he is drawn still there is none.
 *
 * A drawing of him on the page says that it is drawn, for as long as it is: he is one
 * rabbit, and what every page stands in draws him only where the page does not.
 */
export function Drawn({ pose, stirs, soil = false, ofThePage = true }: Props) {
  const moves = pose === "hops" || stirs;
  const box = useRef<HTMLSpanElement>(null);

  useEffect(() => (ofThePage ? watch(box.current) : undefined), [ofThePage]);

  if (!moves) {
    return (
      <span ref={box} className={styles.drawn} aria-hidden="true" data-moves="false">
        <span className={styles.still} style={drawn(STILL_OF[pose])} />
      </span>
    );
  }
  return (
    <span ref={box} className={styles.drawn} aria-hidden="true" data-moves="true">
      <span className={styles.waits} style={drawn(STILL_OF[pose])} />
      {pose === "hops" ? (
        <span className={styles.hops} style={drawn(DRAWING.hops)}>
          {soil ? <span className={styles.soil} style={drawn(soilOf(pose))} /> : null}
        </span>
      ) : (
        // One strip holds all that he does at rest, and every layer is a window on it: so
        // it is asked for once, and no part of him is drawn before the rest of him has come.
        <span className={styles.stirs} style={drawn(stirsOf(pose))}>
          <span className={styles.rests}>
            <span className={styles.body} />
            <span className={styles.ears} />
            <span className={styles.eye} />
            <span className={styles.nose} />
          </span>
          <span className={styles.now} />
        </span>
      )}
    </span>
  );
}
