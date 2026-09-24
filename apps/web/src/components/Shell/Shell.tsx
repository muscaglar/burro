import type { ReactNode } from "react";

import type { Meta } from "@/lib/api/schema";
import { SessionProvider } from "@/lib/session/session";

import { SiteFooter } from "../SiteFooter/SiteFooter";
import { SiteHeader } from "../SiteHeader/SiteHeader";
import { SkipLink } from "../SkipLink/SkipLink";
import { LiveSyntheticBanner } from "../SyntheticBanner/LiveSyntheticBanner";
import { RemembersSynthetic } from "../SyntheticBanner/RemembersSynthetic";
import { SyntheticBanner } from "../SyntheticBanner/SyntheticBanner";
import styles from "./Shell.module.css";

interface Props {
  /** The release the page was built on. */
  readonly meta: Meta;
  readonly children: ReactNode;
}

/**
 * What every page has: the skip link, the banner that says the data is made
 * up, the header, the page itself, and the footer.
 *
 * It also holds the session: the search that is open and the areas chosen to
 * compare, in memory, for as long as the tab is open. The shell stays while
 * one page gives way to the next, so both are still there on the next page.
 */
export function Shell({ meta, children }: Props) {
  return (
    <div className={styles.shell}>
      <SkipLink />
      {meta.synthetic ? (
        <>
          <SyntheticBanner synthetic />
          <RemembersSynthetic />
        </>
      ) : (
        <LiveSyntheticBanner />
      )}
      <SiteHeader />
      {/* It takes focus when the skip link is followed, and is not a stop of its own. */}
      <main id="main" tabIndex={-1} className={styles.main}>
        <SessionProvider>{children}</SessionProvider>
      </main>
      <SiteFooter meta={meta} />
    </div>
  );
}
