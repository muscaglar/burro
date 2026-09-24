import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";

import { Shell } from "@/components/Shell/Shell";
import { SITE } from "@/content/site";
import { loadMeta } from "@/lib/api/server";
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
  colorScheme: "light dark",
};

export default async function RootLayout({ children }: { readonly children: ReactNode }) {
  const { meta } = await loadMeta();
  return (
    <html lang="en-GB">
      <body>
        <Shell meta={meta}>{children}</Shell>
      </body>
    </html>
  );
}
