import Link from "next/link";

import { SITE } from "@/content/site";
import { accountsOn } from "@/lib/account/on";
import { paths } from "@/lib/paths";

import { AccountEntry } from "../AccountEntry/AccountEntry";
import { BurroOfEveryPage } from "../kit/Burro/OfEveryPage";
import { Frame } from "../kit/Frame/Frame";
import { boardOnANarrowScreen, BURRO_IN_THE_BOARD, type InTheBoard } from "./look";
import { NavLink } from "./NavLink";
import styles from "./SiteHeader.module.css";

const LINKS = [
  { href: paths.vibes(), label: SITE.nav.vibes },
  { href: paths.methods(), label: SITE.nav.methods },
  { href: paths.sources(), label: SITE.nav.sources },
] as const;

interface Props {
  /**
   * How the three links are drawn on a narrow screen. As `labels` they are their words, and
   * the board is one line. As `keys` they are drawn as buttons, as they are on a wide
   * screen, and the board is two lines: the name, and under it the three. Left out, it is
   * what the look says: labels, so that the first result of a search is whole on the first
   * screen of a phone, unless the look draws Burro in the board of a narrow screen.
   */
  readonly narrow?: "labels" | "keys";
  /** Whether Burro is drawn in the board, beside the name. Left out, what the look says. */
  readonly burro?: InTheBoard;
}

/**
 * The name board: the name of the site, which leads to the search, and the three pages
 * about it: the vibes, the methods and the sources. It is a box on the meadow, so that
 * nothing of it is read on the grass.
 *
 * Burro sits in it, beside the name, behind the rule at its foot, wherever the board has
 * room for him: on a screen 40rem wide or wider, and on a narrower one where the board is
 * two lines. So he is on every page, and stirs there. The name comes first, as it did: the
 * shell sets it as the first thing the board holds. He is no part of the name, and a press
 * on him leads nowhere.
 */
export function SiteHeader({ narrow = boardOnANarrowScreen(), burro = BURRO_IN_THE_BOARD }: Props) {
  return (
    <header className={styles.header}>
      <Frame kind="box" bare className={styles.inner} data-narrow={narrow}>
        <Link href={paths.home()} className={`${styles.name} target`} prefetch={false}>
          {SITE.name}
        </Link>
        {burro === "beside-the-name" ? (
          <span className={styles.burro}>
            <BurroOfEveryPage />
          </span>
        ) : null}
        <nav aria-label={SITE.navLabel}>
          <ul className={styles.links}>
            {LINKS.map(({ href, label }) => (
              <li key={href}>
                <NavLink href={href} className={`${styles.link} target`}>
                  {label}
                </NavLink>
              </li>
            ))}
            {/* The way to sign in, and to an account. It is drawn only where accounts are on. */}
            {accountsOn() ? <AccountEntry className={`${styles.link} target`} /> : null}
          </ul>
        </nav>
      </Frame>
    </header>
  );
}
