import type { Metadata } from "next";
import Link from "next/link";

import { NOT_FOUND } from "@/content/site";
import { paths } from "@/lib/paths";

// A page that is not there says so in its title, and is not taken for the search.
export const metadata: Metadata = { title: NOT_FOUND.title };

export default function NotFound() {
  return (
    <>
      <h1>{NOT_FOUND.title}</h1>
      <p>{NOT_FOUND.text}</p>
      <p>
        <Link className="target" href={paths.home()}>
          {NOT_FOUND.back}
        </Link>
      </p>
    </>
  );
}
