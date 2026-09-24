import Link from "next/link";

import { SITE } from "@/content/site";
import { paths } from "@/lib/paths";

import { NavLink } from "./NavLink";
import styles from "./SiteHeader.module.css";

const LINKS = [
  { href: paths.vibes(), label: SITE.nav.vibes },
  { href: paths.methods(), label: SITE.nav.methods },
  { href: paths.sources(), label: SITE.nav.sources },
  { href: paths.accessibility(), label: SITE.nav.accessibility },
] as const;

/** The name of the site, which leads to the search, and the four pages about it. */
export function SiteHeader() {
  return (
    <header className={styles.header}>
      <div className={styles.inner}>
        <Link href={paths.home()} className={`${styles.name} target`} prefetch={false}>
          {SITE.name}
        </Link>
        <nav aria-label={SITE.navLabel}>
          <ul className={styles.links}>
            {LINKS.map(({ href, label }) => (
              <li key={href}>
                <NavLink href={href} className={`${styles.link} target`}>
                  {label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </header>
  );
}
