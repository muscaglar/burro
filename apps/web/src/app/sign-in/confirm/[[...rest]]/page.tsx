import type { Metadata } from "next";

import { WhileOpen } from "@/components/AccountParts/parts";
import { Confirm } from "@/components/SignIn/Confirm";
import { CONFIRM } from "@/content/account";
import { describedAs, onlyWhereAccountsAreOn, pagesBuilt } from "@/lib/account/page";

// The page is built where accounts are on, and nothing is drawn at its address where they are off.
export const dynamicParams = false;
export const generateStaticParams = pagesBuilt;

export function generateMetadata(): Metadata {
  // The layout says that no page sends a referrer, and this one says it again for itself:
  // where it leads next is told nothing of the address it was opened at.
  return { ...describedAs(CONFIRM.pageTitle, CONFIRM.pageDescription), referrer: "no-referrer" };
}

/**
 * The page a link to sign in opens. The token of the link is after the `#` of the
 * address, which a browser sends to no server, so this page is built once and is the same
 * for every link. The browser reads the token, takes it out of the address, and asks the
 * service whose link it is.
 */
export default function ConfirmPage() {
  onlyWhereAccountsAreOn();
  // Whatever the page holds of anybody is let go of as the browser puts it away.
  return (
    <WhileOpen>
      <Confirm />
    </WhileOpen>
  );
}
