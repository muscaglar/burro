"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

interface Props {
  readonly href: string;
  readonly className?: string;
  readonly children: string;
}

/**
 * A link in the site's navigation. It says so when it is the page being read. It is on
 * every page, so it is not fetched ahead of time: fetched ahead, every page that is opened
 * asks for three more that nobody may read.
 */
export function NavLink({ href, className, children }: Props) {
  const here = usePathname() === href;
  return (
    <Link href={href} className={className} aria-current={here ? "page" : undefined} prefetch={false}>
      {children}
    </Link>
  );
}
