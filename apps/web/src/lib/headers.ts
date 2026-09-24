/**
 * The headers every page is served with.
 *
 * The content security policy allows the website's own origin and the API's,
 * and no other: no script, style, font or image comes from anyone else. It is
 * worked out here, as a plain function, so that a test can hold it to that.
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
    // `data:` and `blob:` are made by the page itself, and name no origin.
    ["img-src", [self, "data:", "blob:"]],
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
