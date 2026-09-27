import Link from "next/link";

import { METHODS } from "@/content/methods";
import { SITE } from "@/content/site";
import type { Meta } from "@/lib/api/schema";
import { paths } from "@/lib/paths";

import { BurroOfEveryPage } from "../kit/Burro/OfEveryPage";
import { Frame } from "../kit/Frame/Frame";
import { overTheFoot, WORDS_IN_THE_FOOT, type WordsInTheFoot } from "../SiteHeader/look";
import styles from "./SiteFooter.module.css";

interface Props {
  readonly meta: Meta;
  /**
   * Whether Burro is drawn over the foot on a narrow screen, where the name board has no
   * room for him. Left out, what the look says.
   */
  readonly burro?: boolean;
  /** By what name the foot leads to what is said of what a person types. Left out, what the look says. */
  readonly words?: WordsInTheFoot;
}

const LINKS = [
  { href: paths.vibes(), label: SITE.nav.vibes },
  { href: paths.methods(), label: SITE.nav.methods },
  { href: paths.sources(), label: SITE.nav.sources },
] as const;

/** Where what is said of what a person types stands: a part of the methods, under a heading of its own. */
const WORDS = paths.methods("words");

/**
 * The foot: the three pages about the site, the way to what is said of what a person
 * types, and the release and engine behind every figure. It is a box on the meadow, as the
 * name board is.
 *
 * What a person types, where it goes and that it is not kept was said under the search box,
 * with a link to the whole of it. A person who walked the website asked for both to go from
 * there. It is said where it was, among the methods, and every page leads to it from here.
 *
 * On a narrow screen Burro sits behind the rule at its head, on the grass, seen from his
 * back up: the name board of a phone is one line and has no room for him. He takes no
 * room of his own. He comes first in the foot, as he is seen first, and nothing of him is
 * heard or pressed.
 */
export function SiteFooter({ meta, burro = overTheFoot(), words = WORDS_IN_THE_FOOT }: Props) {
  return (
    <footer className={styles.footer}>
      <Frame kind="box" bare className={styles.inner}>
        {burro ? (
          <span className={styles.burro}>
            <BurroOfEveryPage />
          </span>
        ) : null}
        <nav aria-label={SITE.footerLabel}>
          <ul className={styles.links}>
            {LINKS.map(({ href, label }) => (
              <li key={href}>
                <Link href={href} className={`${styles.link} target`} prefetch={false}>
                  {label}
                </Link>
              </li>
            ))}
            <li>
              {/* Which page a person reads next is told to no server ahead of time. */}
              {words === "as-headed" ? (
                <Link href={WORDS} className={`${styles.link} target`} prefetch={false}>
                  {METHODS.words.title}
                </Link>
              ) : (
                // What is seen of it is the start of its name: the rest says where it leads.
                <Link
                  href={WORDS}
                  className={`${styles.link} target`}
                  prefetch={false}
                  aria-label={SITE.privacyLeadsTo(SITE.privacy, METHODS.words.title)}
                >
                  {SITE.privacy}
                </Link>
              )}
            </li>
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
      </Frame>
    </footer>
  );
}
