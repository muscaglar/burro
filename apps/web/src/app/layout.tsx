import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import { preload } from "react-dom";

import { Shell } from "@/components/Shell/Shell";
import { SITE } from "@/content/site";
import { loadMeta } from "@/lib/api/server";
import { FACES } from "@/lib/headers";
import { KEEP_OUT, mayBeIndexed } from "@/lib/indexing";

import "@/styles/tokens.css";
import "@/styles/base.css";

// A built page is kept for an hour at most: the `max-age` the API sends.
export const revalidate = 3600;

export async function generateMetadata(): Promise<Metadata> {
  const { meta } = await loadMeta();
  return {
    title: { default: SITE.name, template: `%s · ${SITE.name}` },
    description: SITE.description,
    referrer: "no-referrer",
    // A made-up place must not be found by a search engine. Nor may a page that
    // cannot say where it lives: the rule is one, in `lib/indexing.ts`.
    robots: mayBeIndexed(meta) ? undefined : KEEP_OUT,
  };
}

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  // The look is one, and has no dark colours. The browser is told so before it has read a
  // style sheet, so that it draws nothing of its own dark and does not darken the page.
  colorScheme: "only light",
};

/** The file of the face of names that holds the letters of English, which every page draws its name board in. */
const FACE_OF_NAMES = `${FACES}/jersey-10-latin.woff2`;

export default async function RootLayout({ children }: { readonly children: ReactNode }) {
  const { meta } = await loadMeta();
  // A face is asked for once the style sheets have come, which is as the page is first painted.
  // Until the face of names is in, the name board and every heading are drawn in its stand-in,
  // which is far wider: so the links of the board stand under the name and a heading takes a
  // line more, and the whole page jumps as the face comes. Asked for with the page, it is in
  // before the first paint. The face of a sentence is not asked ahead: its stand-in is near it
  // in width, so next to nothing moves as it comes, and its file is seven times the size.
  preload(FACE_OF_NAMES, { as: "font", type: "font/woff2", crossOrigin: "anonymous" });
  return (
    <html lang="en-GB">
      <body>
        <Shell meta={meta}>{children}</Shell>
      </body>
    </html>
  );
}
