import type { CSSProperties } from "react";

import { SITE } from "@/content/site";

import { pictureOf } from "../kit/drawings";
import { picturesOf } from "../kit/Press/kinds";
import styles from "./SkipLink.module.css";

interface Props {
  /** The id of what to skip to, with its `#`. The page's main content unless said otherwise. */
  readonly href?: `#${string}`;
  readonly children?: string;
}

/** The pictures of the button that matters most in sight, which this is while it is in sight. */
const { up, down } = picturesOf("go", false);
const DRAWN = { "--art": `url("${pictureOf(up)}")`, "--art-down": `url("${pictureOf(down)}")` } as CSSProperties;

/**
 * The first thing a keyboard reaches. It is drawn only while it has focus, and then as a
 * button is drawn.
 *
 * It is a plain link of the browser's own, so that following it gives the focus to what it
 * leads to: a link the website follows for itself moves the page and leaves the focus.
 */
export function SkipLink({ href = "#main", children = SITE.skipToContent }: Props) {
  return (
    <a className={`${styles.skip} target`} href={href} style={DRAWN}>
      {children}
    </a>
  );
}
