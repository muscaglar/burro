"use client";

import { useEffect } from "react";

/** The part of the page a fragment names, or `null` where it names none that is there. */
function partAt(fragment: string): HTMLElement | null {
  let id = fragment.replace(/^#/, "");
  try {
    id = decodeURIComponent(id);
  } catch {
    // An address that cannot be read names nothing.
    return null;
  }
  return id === "" ? null : document.getElementById(id);
}

/** Opens every fold that holds a part, and the part itself where it is a fold. True where any was closed. */
function open(part: HTMLElement): boolean {
  let opened = false;
  for (let fold = part.closest("details"); fold !== null; fold = fold.parentElement?.closest("details") ?? null) {
    if (!fold.open) {
      fold.open = true;
      opened = true;
    }
  }
  return opened;
}

/**
 * Opens what holds the part a fragment names, and brings the part into sight where anything
 * was closed. A part that was made to take the focus takes it, so that whoever hears the
 * page is brought to the part as whoever sees it is. A part that was not is given nothing.
 */
function show(fragment: string): void {
  const part = partAt(fragment);
  if (part === null) return;
  // Where nothing was closed the browser has brought the part into sight itself.
  if (open(part)) part.scrollIntoView();
  // It is where it was brought, or where it will be: the focus moves nothing.
  if (part.hasAttribute("tabindex")) part.focus({ preventScroll: true });
}

/** The link a press landed on, where it leads to a part of the page that is open. `null` of any other press. */
function toThisPage(event: MouseEvent): HTMLAnchorElement | null {
  // Pressed with a key held, or with another button, a link is opened in a tab of its own.
  if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return null;
  const link = event.target instanceof Element ? event.target.closest("a[href]") : null;
  if (!(link instanceof HTMLAnchorElement) || link.hash === "") return null;
  const { origin, pathname } = window.location;
  return link.origin === origin && link.pathname === pathname ? link : null;
}

/**
 * Another page leads to a part of this one by its id, and the part may stand in a fold that
 * is closed. Where the address names such a part, every fold that holds it is opened and
 * the part is brought into sight: as the page is opened, and when a link of the page
 * itself leads to it.
 *
 * A link of the page itself is followed in one of two ways. The browser follows a plain
 * one, and says that the address changed. The framework follows its own, as the links of
 * the foot are, by writing the address itself: nobody is then told that it changed. So a
 * press on a link that leads to a part of this page opens what holds the part, whoever
 * follows the link. The framework leaves the focus on the link it followed, which may be
 * at the foot of the page: so the part takes the focus, where it was made to.
 *
 * It reads the address of the page and of the link that was pressed, and nothing else. It
 * keeps nothing and sends nothing. What an address names here is a part of a page that
 * explains, and never a place or a search. With scripts off a browser that opens a fold
 * for what the address names still does, and in any other the fold is one press away.
 *
 * It draws nothing.
 */
export function OpenToAddress() {
  useEffect(() => {
    const told = () => show(window.location.hash);
    const pressed = (event: MouseEvent) => {
      const link = toThisPage(event);
      if (link !== null) show(link.hash);
    };
    told();
    window.addEventListener("hashchange", told);
    document.addEventListener("click", pressed);
    return () => {
      window.removeEventListener("hashchange", told);
      document.removeEventListener("click", pressed);
    };
  }, []);
  return null;
}
