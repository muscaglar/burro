"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { CSSProperties } from "react";

import { pictureOf } from "../kit/drawings";
import { picturesOf } from "../kit/Press/kinds";

interface Props {
  readonly href: string;
  readonly className?: string;
  readonly children: string;
}

/**
 * A link in the site's navigation. It says so when it is the page being read. It is on
 * every page, so it is not fetched ahead of time: fetched ahead, every page that is opened
 * asks for the others, which nobody may read.
 *
 * Where there is room it is drawn as a button is, and the page being read as the button of
 * what is on. It is handed the pictures of both, as it stands and pressed, and its style
 * sheet lays them where the screen is wide enough for them.
 */
export function NavLink({ href, className, children }: Props) {
  const here = usePathname() === href;
  const { up, down } = picturesOf("plain", here);
  const drawn = { "--art": `url("${pictureOf(up)}")`, "--art-down": `url("${pictureOf(down)}")` } as CSSProperties;
  return (
    <Link href={href} className={className} style={drawn} aria-current={here ? "page" : undefined} prefetch={false}>
      {children}
    </Link>
  );
}
