import type { Metadata } from "next";

import { ACCESSIBILITY } from "@/content/accessibility";
import { readableDate } from "@/lib/format";

export const metadata: Metadata = {
  title: ACCESSIBILITY.title,
  description: ACCESSIBILITY.lead,
};

function Points({ points }: { readonly points: readonly string[] }) {
  return (
    <ul>
      {points.map((point) => (
        <li key={point}>{point}</li>
      ))}
    </ul>
  );
}

export default function AccessibilityPage() {
  const { built, checked, short, notTested, report, updated } = ACCESSIBILITY;
  return (
    <>
      <h1>{ACCESSIBILITY.title}</h1>
      <p>{ACCESSIBILITY.lead}</p>

      <h2>{built.title}</h2>
      <Points points={built.points} />

      <h2>{checked.title}</h2>
      <Points points={checked.points} />

      <h2>{short.title}</h2>
      <Points points={short.points} />

      <h2>{notTested.title}</h2>
      <p>{notTested.lead}</p>
      <Points points={notTested.points} />

      <h2>{report.title}</h2>
      <p>{report.noAddressYet}</p>

      <p className="muted">
        {updated.label}: <time dateTime={updated.date}>{readableDate(updated.date)}</time>
      </p>
    </>
  );
}
