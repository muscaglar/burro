import type { Metadata } from "next";

import { WhileOpen } from "@/components/AccountParts/parts";
import { Sent } from "@/components/SignIn/Sent";
import { SENT } from "@/content/account";
import { describedAs, onlyWhereAccountsAreOn, pagesBuilt } from "@/lib/account/page";

// The page is built where accounts are on, and nothing is drawn at its address where they are off.
export const dynamicParams = false;
export const generateStaticParams = pagesBuilt;

export function generateMetadata(): Metadata {
  return describedAs(SENT.pageTitle, SENT.pageDescription);
}

/**
 * Says that a link to sign in was sent. It is built once, and says the same whoever asked
 * and whatever the address: its own address holds nothing, and it sends nothing.
 */
export default function SentPage() {
  onlyWhereAccountsAreOn();
  // Whatever the page holds of anybody is let go of as the browser puts it away.
  return (
    <WhileOpen>
      <Sent />
    </WhileOpen>
  );
}
