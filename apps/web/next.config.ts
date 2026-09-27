import { readdirSync } from "node:fs";
import path from "node:path";

import type { NextConfig } from "next";

import { ledNowhere } from "./src/lib/account/off";
import { apiOrigin } from "./src/lib/api/config";
import { loadMeta } from "./src/lib/api/server";
import { FACES, keptByABrowser, securityHeaders } from "./src/lib/headers";
import { keepOutHeaders, mayBeIndexed } from "./src/lib/indexing";

const development = process.env.NODE_ENV === "development";

/**
 * Whether a search engine may index what is being built. A release that
 * cannot be read is taken for one that may not be: the header is then on
 * every answer, and the pages, which stop the build, say why.
 */
async function mayIndex(): Promise<boolean> {
  try {
    return mayBeIndexed((await loadMeta()).meta);
  } catch {
    return false;
  }
}

/**
 * The faces there are, by the names of their files. Where the folder cannot be read, none
 * is named: a browser then asks for a face each time it draws a page, and the website
 * starts all the same.
 */
function faces(): string[] {
  try {
    return readdirSync(path.join(__dirname, "public", FACES));
  } catch {
    return [];
  }
}

const config: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  // No page asks the framework for a picture: a drawing is a file of `public/art`, laid by a
  // style at its own size. Left on, the framework makes one of any drawing, at any of its
  // widths, for whoever asks, and keeps each. So it makes none, and nothing answers at
  // `/_next/image`.
  images: { unoptimized: true },
  // The app sits two folders down in a repository that is not a Node workspace.
  turbopack: { root: path.resolve(__dirname) },
  // With accounts off the address of a page of accounts is answered as one that the website
  // has nothing at, before any folder is asked: `ledNowhere` says why.
  rewrites: async () => ({ beforeFiles: ledNowhere(), afterFiles: [], fallback: [] }),
  async headers() {
    return [
      {
        source: "/:path*",
        headers: securityHeaders(apiOrigin(process.env.NEXT_PUBLIC_BURRO_API_URL), development),
      },
      // How long a browser may keep a face, said of each file that is there when the website is built.
      ...keptByABrowser(faces()),
      // What a search engine is asked, said again for what is not a page. It is worked out
      // when the website is built, and the pages say it again each time they are.
      ...keepOutHeaders(await mayIndex()),
    ];
  },
};

export default config;
