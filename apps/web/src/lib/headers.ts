/**
 * The headers every page is served with.
 *
 * The content security policy allows the website's own origin and the API's,
 * and no other: no script, style, font or image comes from anyone else. The
 * two faces and every drawing are files of the website's own, under /fonts/
 * and /art/, so the policy lets them by and lets nothing else. It is worked
 * out here, as a plain function, so that a test can hold it to that.
 */

export interface Header {
  readonly key: string;
  readonly value: string;
}

/**
 * `apiOrigin` is the origin of the API, or `null` when no address is set.
 * `development` allows what the development server needs to reload a page.
 */
export function contentSecurityPolicy(apiOrigin: string | null, development = false): string {
  const self = "'self'";
  const directives: readonly (readonly [string, readonly string[]])[] = [
    ["default-src", [self]],
    // Next writes the page's own data into it as inline script, and a page
    // that is built ahead of time can carry no nonce.
    ["script-src", [self, "'unsafe-inline'", ...(development ? ["'unsafe-eval'"] : [])]],
    // The map sets the size and place of what it draws as inline styles.
    ["style-src", [self, "'unsafe-inline'"]],
    // A drawing is a file of the website's own. `data:` and `blob:` are made
    // by the page itself, as the map makes them, and name no origin.
    ["img-src", [self, "data:", "blob:"]],
    // A face is a file of the website's own, and is never made by the page.
    ["font-src", [self]],
    ["connect-src", apiOrigin === null ? [self] : [self, apiOrigin]],
    // The map draws in a worker it makes from its own code.
    ["worker-src", [self, "blob:"]],
    ["object-src", ["'none'"]],
    ["base-uri", [self]],
    ["form-action", [self]],
    ["frame-ancestors", ["'none'"]],
  ];
  return directives.map(([name, values]) => `${name} ${values.join(" ")}`).join("; ");
}

export function securityHeaders(apiOrigin: string | null, development = false): Header[] {
  return [
    { key: "Content-Security-Policy", value: contentSecurityPolicy(apiOrigin, development) },
    // No site a link leads to is told which page the person came from.
    { key: "Referrer-Policy", value: "no-referrer" },
    { key: "X-Content-Type-Options", value: "nosniff" },
    // The website asks for none of these, so nothing on it may.
    { key: "Permissions-Policy", value: "camera=(), geolocation=(), microphone=()" },
  ];
}

/** Where the faces are served from. */
export const FACES = "/fonts";

const YEAR = 365 * 24 * 60 * 60;

/**
 * How long a browser may keep a face, as Next reads it. `files` are the names of the faces
 * in `public/fonts`.
 *
 * A face never changes under its name: one that is drawn again is given a new name, and
 * test/faces.test.ts holds each file to what it held. So a browser keeps it for a year and
 * does not ask again, and a page that is opened a second time is drawn in its faces at once.
 *
 * Each file is named whole. A pattern would say the same of a face that is not there, and
 * a browser would keep for a year that it is not.
 */
export function keptByABrowser(files: readonly string[]): { readonly source: string; readonly headers: Header[] }[] {
  return files
    .filter((file) => /^[a-z0-9-]+\.woff2$/.test(file))
    .map((file) => ({
      source: `${FACES}/${file}`,
      headers: [{ key: "Cache-Control", value: `public, max-age=${YEAR}, immutable` }],
    }));
}
