"use client";

import { TENURE_CHOICE } from "@/content/search";
import type { Tenure } from "@/lib/api/schema";
import { useDraft } from "@/lib/search/draft";

import { Radios } from "./fields";

const TENURES: readonly Tenure[] = ["rent", "buy"];

interface Props {
  readonly tenure: Tenure;
  /**
   * Told of the choice. Before anything is asked for, the page swaps in the
   * other default and sends nothing. After, it is an edit like any other.
   */
  readonly onChoose: (tenure: Tenure) => void;
  readonly version: number;
  readonly problem?: string | null;
}

/** Renting or buying: two radio buttons. */
export function TenureChoice({ tenure, onChoose, version, problem = null }: Props) {
  const [shown, show] = useDraft(tenure, version);
  return (
    <Radios
      legend={TENURE_CHOICE.legend}
      options={TENURES.map((value) => ({ value, label: TENURE_CHOICE[value] }))}
      value={shown}
      problem={problem}
      onChange={(chosen) => {
        show(chosen);
        onChoose(chosen);
      }}
    />
  );
}
