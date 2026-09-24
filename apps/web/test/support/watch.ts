/**
 * Watches everywhere that what a person types must never reach: the
 * console, every kind of browser storage, the address of the page and its
 * history, and the title.
 *
 * A privacy test starts a watch, runs a whole search with a canary planted
 * in it, and then asks the watch what it saw.
 */

export interface Watch {
  /** Every call to a method of the console, with what it was given. */
  readonly console: unknown[][];
  /** Every touch of browser storage, a cookie, the cache or a service worker, by name. */
  readonly storage: string[];
  /** Every change asked of the address or the history, with what it was given. */
  readonly history: unknown[][];
  /** Everything the watch saw, and the page as it stands, as one text to look for a canary in. */
  everythingOutsideThePage(): string;
  /** The address of the page, its title, every change to its history, and every address in its markup. */
  addresses(): string;
  /** The id of every element, and every attribute that points at one. */
  ids(): string;
  stop(): void;
}

/** The attributes that hold an address. */
const HOLD_AN_ADDRESS = ["href", "src", "srcset", "action", "formaction", "poster", "ping", "cite", "data"];
/** The attributes that hold an id, or point at one. */
const HOLD_AN_ID = ["id", "for", "name", "aria-controls", "aria-labelledby", "aria-describedby", "aria-activedescendant"];

const CONSOLE = ["log", "info", "warn", "error", "debug", "trace", "dir", "table", "group"] as const;
const STORAGE = ["getItem", "setItem", "removeItem", "clear", "key"] as const;

export function watch(): Watch {
  const written: unknown[][] = [];
  const storage: string[] = [];
  const history: unknown[][] = [];
  const undo: (() => void)[] = [];

  for (const method of CONSOLE) {
    const spy = jest.spyOn(console, method).mockImplementation((...args: unknown[]) => {
      written.push([method, ...args]);
    });
    undo.push(() => spy.mockRestore());
  }

  for (const method of STORAGE) {
    const spy = jest.spyOn(Storage.prototype, method).mockImplementation((...args: unknown[]) => {
      storage.push(`storage.${method}(${args.map(String).join(", ")})`);
      return null as never;
    });
    undo.push(() => spy.mockRestore());
  }

  const cookie = Object.getOwnPropertyDescriptor(Document.prototype, "cookie");
  Object.defineProperty(document, "cookie", {
    configurable: true,
    get: () => {
      storage.push("cookie read");
      return "";
    },
    set: (value: string) => {
      storage.push(`cookie set: ${value}`);
    },
  });
  undo.push(() => {
    if (cookie) Object.defineProperty(document, "cookie", cookie);
  });

  // jsdom has none of these. Each is put there as a trap, so that reaching for it is seen.
  const traps: [object, string][] = [
    [window, "indexedDB"],
    [window, "caches"],
    [window, "cookieStore"],
    [navigator, "serviceWorker"],
    [navigator, "sendBeacon"],
  ];
  for (const [owner, name] of traps) {
    const before = Object.getOwnPropertyDescriptor(owner, name);
    Object.defineProperty(owner, name, {
      configurable: true,
      get: () => {
        storage.push(`${name} touched`);
        return undefined;
      },
    });
    undo.push(() => {
      if (before) Object.defineProperty(owner, name, before);
      else delete (owner as Record<string, unknown>)[name];
    });
  }

  for (const method of ["pushState", "replaceState"] as const) {
    const spy = jest.spyOn(window.history, method).mockImplementation((...args: unknown[]) => {
      history.push([method, ...args]);
    });
    undo.push(() => spy.mockRestore());
  }
  const opened = jest.spyOn(window, "open").mockImplementation((...args: unknown[]) => {
    history.push(["open", ...args]);
    return null;
  });
  undo.push(() => opened.mockRestore());

  const attributesNamed = (names: readonly string[]) =>
    [...document.querySelectorAll("*")].flatMap((element) =>
      [...element.attributes]
        .filter((attribute) => names.includes(attribute.name))
        .map((attribute) => `${attribute.name}=${attribute.value}`),
    );
  const addresses = () =>
    JSON.stringify([
      window.location.href,
      document.title,
      document.referrer,
      attributesNamed(HOLD_AN_ADDRESS),
      history,
    ]);

  return {
    console: written,
    storage,
    history,
    addresses,
    ids: () => JSON.stringify(attributesNamed(HOLD_AN_ID)),
    everythingOutsideThePage: () =>
      JSON.stringify([written.map((call) => call.map(String)), storage, history]) + addresses(),
    stop: () => undo.reverse().forEach((put) => put()),
  };
}
