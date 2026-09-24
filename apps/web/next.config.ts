import path from "node:path";

import type { NextConfig } from "next";

import { apiOrigin } from "./src/lib/api/config";
import { loadMeta } from "./src/lib/api/server";
import { securityHeaders } from "./src/lib/headers";
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

const config: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  // The app sits two folders down in a repository that is not a Node workspace.
  turbopack: { root: path.resolve(__dirname) },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: securityHeaders(apiOrigin(process.env.NEXT_PUBLIC_BURRO_API_URL), development),
      },
      // What a search engine is asked, said again for what is not a page. It is worked out
      // when the website is built, and the pages say it again each time they are.
      ...keepOutHeaders(await mayIndex()),
    ];
  },
};

export default config;
