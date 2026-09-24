import Link from "next/link";

import { SITE } from "@/content/site";
import type { Meta } from "@/lib/api/schema";
import { paths } from "@/lib/paths";

import styles from "./SiteFooter.module.css";

interface Props {
  readonly meta: Meta;
}

const LINKS = [
  { href: paths.vibes(), label: SITE.nav.vibes },
  { href: paths.methods(), label: SITE.nav.methods },
  { href: paths.sources(), label: SITE.nav.sources },
  { href: paths.accessibility(), label: SITE.nav.accessibility },
] as const;

/** The four pages about the site, and the release and engine behind every figure. */
export function SiteFooter({ meta }: Props) {
  return (
    <footer className={styles.footer}>
      <div className={styles.inner}>
        <nav aria-label={SITE.footerLabel}>
          <ul className={styles.links}>
            {LINKS.map(({ href, label }) => (
              <li key={href}>
                <Link href={href} className={`${styles.link} target`} prefetch={false}>
                  {label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
        <dl className={styles.release}>
          <div>
            <dt>{SITE.footer.release}</dt>
            <dd>
              <code>{meta.release_id}</code>
            </dd>
          </div>
          <div>
            <dt>{SITE.footer.engine}</dt>
            <dd>
              <code>{meta.engine_version}</code>
            </dd>
          </div>
        </dl>
      </div>
    </footer>
  );
}
