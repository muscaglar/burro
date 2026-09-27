import type { Metadata } from "next";

import { Account } from "@/components/Account/Account";
import { WhileOpen } from "@/components/AccountParts/parts";
import { ACCOUNT } from "@/content/account";
import { describedAs, onlyWhereAccountsAreOn, pagesBuilt } from "@/lib/account/page";
import { handed } from "@/lib/api/handed";
import { loadAreas, loadMeta } from "@/lib/api/server";

// A built page is kept for an hour at most: the `max-age` the API sends.
export const revalidate = 3600;

// The page is built where accounts are on, and nothing is drawn at its address where they are off.
export const dynamicParams = false;
export const generateStaticParams = pagesBuilt;

export function generateMetadata(): Metadata {
  return describedAs(ACCOUNT.pageTitle, ACCOUNT.pageDescription);
}

/**
 * The page of an account. It is built once and is the same for everybody: whose account
 * it shows is decided by the session, at the service, once the browser has asked.
 *
 * The server hands over what a search needs to be opened, from routes 11 and 4, as it does
 * for the page a shared link opens: a search that was kept is opened from here.
 */
export default async function AccountPage() {
  onlyWhereAccountsAreOn();
  const [meta, areas] = await Promise.all([loadMeta(), loadAreas()]);
  // Whatever the page holds of anybody is let go of as the browser puts it away.
  return (
    <WhileOpen>
      <Account meta={handed(meta.data)} areas={areas.data.areas} />
    </WhileOpen>
  );
}
