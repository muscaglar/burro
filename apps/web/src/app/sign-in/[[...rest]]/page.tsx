import type { Metadata } from "next";

import { WhileOpen } from "@/components/AccountParts/parts";
import { SignIn } from "@/components/SignIn/SignIn";
import { SIGN_IN } from "@/content/account";
import { describedAs, onlyWhereAccountsAreOn, pagesBuilt } from "@/lib/account/page";

// The page is built where accounts are on, and nothing is drawn at its address where they are off.
export const dynamicParams = false;
export const generateStaticParams = pagesBuilt;

export function generateMetadata(): Metadata {
  return describedAs(SIGN_IN.pageTitle, SIGN_IN.pageDescription);
}

/**
 * Where a person asks for a link to sign in with. The page is built once and is the same
 * for everybody: what is typed in it goes from the browser to the website's own route,
 * and from there to the service, in the body of a request.
 */
export default function SignInPage() {
  onlyWhereAccountsAreOn();
  // Whatever the page holds of anybody is let go of as the browser puts it away.
  return (
    <WhileOpen>
      <SignIn />
    </WhileOpen>
  );
}
