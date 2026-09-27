"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { CSSProperties } from "react";

import { ACCOUNT_NAV } from "@/content/account";
import { account, useWho } from "@/lib/account/account";
import type { AccountClient } from "@/lib/account/client";
import { ACCOUNT_PAGES, accountPaths } from "@/lib/account/paths";

import { pictureOf } from "../kit/drawings";
import { picturesOf } from "../kit/Press/kinds";
import styles from "./AccountEntry.module.css";
import { ENTRY_ON_A_NARROW_SCREEN, type OnANarrowScreen } from "./look";

interface Props {
  /** The class of a link of the name board, which the board hands over: it draws this entry as it draws the rest. */
  readonly className?: string;
  /** The routes of accounts to call. A test passes its own. */
  readonly client?: Pick<AccountClient, "getSession">;
  /** What becomes of it on a narrow screen once a search is open. Left out, what the look says. */
  readonly narrow?: OnANarrowScreen;
}

/**
 * The one entry of accounts in the name board. It says "Sign in" and leads to signing in,
 * until the service has said that somebody is signed in: it then says "Account", and
 * leads to the page of the account. The board draws it only where accounts are on.
 *
 * What holds a session is a cookie that no script can read, so the entry asks the service
 * who is signed in, once, as the page opens. A page is built the same for everybody, and
 * is built saying "Sign in".
 *
 * It is of one size whichever it says: both names are laid in one place, and the one that
 * is not said is not drawn and not heard. So nothing of the board moves when the service
 * answers.
 *
 * It is on every page, so it is not fetched ahead of time, as no link of the board is. It
 * is handed the pictures of a button, as it stands and pressed, as the links of the board are.
 *
 * It is an item of the list of the board, and brings the item with it: so where it gives
 * way on a narrow screen, nothing of it is left in the list.
 */
export function AccountEntry({ className, client = account, narrow = ENTRY_ON_A_NARROW_SCREEN }: Props) {
  const who = useWho(client);
  const at = usePathname();
  const signedIn = who.kind === "in";
  // Signing in is three pages, and the entry is of all of them until somebody is signed in.
  const here = signedIn ? at === accountPaths.account() : ACCOUNT_PAGES.includes(at) && at !== accountPaths.account();
  const { up, down } = picturesOf("plain", here);
  const drawn = { "--art": `url("${pictureOf(up)}")`, "--art-down": `url("${pictureOf(down)}")` } as CSSProperties;
  return (
    <li className={styles.entry} data-narrow={narrow}>
      <Link
        href={signedIn ? accountPaths.account() : accountPaths.signIn()}
        className={className}
        style={drawn}
        aria-current={here ? "page" : undefined}
        prefetch={false}
      >
        <span className={styles.says}>
          <span className={styles.one} data-said={!signedIn} aria-hidden={signedIn ? true : undefined}>
            {ACCOUNT_NAV.signIn}
          </span>
          <span className={styles.one} data-said={signedIn} aria-hidden={signedIn ? undefined : true}>
            {ACCOUNT_NAV.account}
          </span>
        </span>
      </Link>
    </li>
  );
}
