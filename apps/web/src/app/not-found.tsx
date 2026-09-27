import type { Metadata } from "next";

import { Press } from "@/components/kit/Press/Press";
import { PlainPage } from "@/components/Shell/PlainPage";
import { NOT_FOUND } from "@/content/site";
import { paths } from "@/lib/paths";

// A page that is not there says so in its title, and is not taken for the search.
export const metadata: Metadata = { title: NOT_FOUND.title };

/** The page that is not there: one box that says so, and the way to the search. */
export default function NotFound() {
  return (
    <PlainPage kind="lost" title={NOT_FOUND.title} text={NOT_FOUND.text}>
      <Press kind="go" href={paths.home()}>
        {NOT_FOUND.back}
      </Press>
    </PlainPage>
  );
}
