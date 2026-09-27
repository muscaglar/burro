import type { ReactNode } from "react";

import styles from "./Shell.module.css";

/**
 * The page itself, where no shell stands round it: on the page of a fault in the layout,
 * which the layout would have drawn its shell round.
 *
 * It is laid out by the sheet of the shell, which every page lays. The framework has every
 * page fetch ahead what that page is drawn with: a sheet of its own was fetched by every
 * page and laid by none.
 */
export function Alone({ children }: { readonly children: ReactNode }) {
  return (
    <main id="main" className={styles.alone}>
      {children}
    </main>
  );
}
