/**
 * Where the API is. One environment variable says so, and nothing else does.
 *
 * It is read here and nowhere else. The browser calls this address itself, so
 * what a person types never passes through the website's own server. A build
 * reads the same address, and reads the recorded answers when it is not set.
 */

export const API_URL_VARIABLE = "NEXT_PUBLIC_BURRO_API_URL";

/** The address with no slash at the end, or `null` when none is set or it is not an address. */
export function apiBaseUrl(): string | null {
  // Written out in full, because Next puts the value into the browser's code
  // only where it finds the name spelt like this.
  return cleanBaseUrl(process.env.NEXT_PUBLIC_BURRO_API_URL);
}

export function cleanBaseUrl(value: string | undefined): string | null {
  const trimmed = value?.trim();
  if (!trimmed) return null;
  let url: URL;
  try {
    url = new URL(trimmed);
  } catch {
    return null;
  }
  if (url.protocol !== "https:" && url.protocol !== "http:") return null;
  // An address with a name and a password in it would send them with every call.
  if (url.username || url.password || url.search || url.hash) return null;
  return `${url.origin}${url.pathname}`.replace(/\/+$/, "");
}

/** The origin of the API, for the content security policy. `null` when none is set. */
export function apiOrigin(value: string | undefined): string | null {
  const base = cleanBaseUrl(value);
  return base ? new URL(base).origin : null;
}
