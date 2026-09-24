import { SITE } from "@/content/site";

import styles from "./SkipLink.module.css";

interface Props {
  /** The id of what to skip to, with its `#`. The page's main content unless said otherwise. */
  readonly href?: `#${string}`;
  readonly children?: string;
}

/** The first thing a keyboard reaches. It is drawn only while it has focus. */
export function SkipLink({ href = "#main", children = SITE.skipToContent }: Props) {
  return (
    <a className={`${styles.skip} target`} href={href}>
      {children}
    </a>
  );
}
