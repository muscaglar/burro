import Link from "next/link";

import { CONFIDENCE, CONFIDENCE_PIPS, COST } from "@/content/search";
import type { Budget, Confidence, CostEstimate, Fact } from "@/lib/api/schema";
import { grouped } from "@/lib/format";
import { paths } from "@/lib/paths";

import { SourceNote } from "../SourceNote/SourceNote";
import styles from "./CostRange.module.css";

/** What a bar is drawn along: the figure at its start and the figure at its end. */
export interface Scale {
  readonly from: number;
  readonly to: number;
}

interface Props {
  /** The `cost` fact: the figures as the API formatted them, with their source and date. */
  readonly fact: Fact;
  /** The same figures as numbers, which place the bar and nothing else. */
  readonly estimate: CostEstimate;
  /** The person's budget, marked on the range where one is set. */
  readonly budget?: Pick<Budget, "amount">;
  /**
   * The scale every bar of a list is drawn on, so that one budget is in one
   * place on all of them and a dearer home is drawn further along. Left out,
   * the bar is drawn on a scale of its own.
   */
  readonly scale?: Scale | null;
}

/**
 * One scale for several ranges and a budget: from a little under the least
 * figure among them to a little over the most. `null` when there is no range
 * to draw.
 */
export function scaleOf(estimates: readonly CostEstimate[], amount: number | null): Scale | null {
  if (estimates.length === 0) return null;
  const figures = [
    ...estimates.flatMap((estimate) => [estimate.lower_quartile, estimate.upper_quartile]),
    ...(amount === null ? [] : [amount]),
  ];
  const least = Math.min(...figures);
  const most = Math.max(...figures);
  // A little room either side, so that a mark at an end is not cut off.
  const room = Math.max((most - least) * 0.1, 1);
  return { from: least - room, to: most + room };
}

/** Where things sit along the bar, each as a share of its width from 0 to 100. */
export function placesOnBar(estimate: CostEstimate, amount: number | null, scale: Scale | null = null) {
  const { from, to } = scale ?? scaleOf([estimate], amount) ?? { from: 0, to: 1 };
  const width = Math.max(to - from, 1);
  // What a scale does not reach is drawn at its end, and never outside the bar.
  const at = (figure: number) => Math.min(100, Math.max(0, Math.round(((figure - from) / width) * 1000) / 10));
  return {
    lower: at(estimate.lower_quartile),
    median: at(estimate.median),
    upper: at(estimate.upper_quartile),
    budget: amount === null ? null : at(amount),
  };
}

function isConfidence(value: string | undefined): value is Confidence {
  return value === "high" || value === "medium" || value === "low";
}

/**
 * What homes cost in an area: the range, the middle, what it is for, the
 * month it is as of, and how far to trust it.
 *
 * Every figure in words is a slot of the fact, as the API formatted it. The
 * bar is a picture of the same range, and says in words where the budget
 * falls, so it holds nothing the text does not. Confidence is a word; the
 * pips repeat it, and the word leads to what it means.
 */
export function CostRange({ fact, estimate, budget, scale = null }: Props) {
  const { slots } = fact;
  const amount = budget?.amount ?? null;
  const at = placesOnBar(estimate, amount, scale);
  const rent = fact.template === "cost_rent";
  const confidence = isConfidence(slots.confidence) ? slots.confidence : estimate.confidence;
  const falls =
    amount === null
      ? null
      : amount < estimate.lower_quartile
        ? COST.below
        : amount > estimate.upper_quartile
          ? COST.above
          : COST.inside;

  return (
    <div className={styles.cost}>
      <p className={styles.range}>
        <span className={styles.figure}>
          £{slots.lower} {COST.to} £{slots.upper}
        </span>
        {rent ? ` ${COST.aMonth}` : null}
      </p>
      <dl className={styles.facts}>
        <div>
          <dt>{fact.label}</dt>
          <dd>{slots.segment}</dd>
        </div>
        <div>
          <dt>{COST.middle}</dt>
          <dd>£{slots.median}</dd>
        </div>
        <div>
          <dt>{COST.asOf}</dt>
          <dd>{slots.as_of}</dd>
        </div>
        <div>
          <dt>
            {/* Which page a person reads next is told to no server ahead of time. */}
            <Link className={`${styles.means} target-min`} href={paths.methods("confidence")} prefetch={false}>
              {COST.confidence}
            </Link>
          </dt>
          <dd>
            {CONFIDENCE[confidence]}{" "}
            <span className={styles.pips} aria-hidden="true">
              {[1, 2, 3].map((pip) => (
                <span key={pip} data-on={pip <= CONFIDENCE_PIPS[confidence]} />
              ))}
            </span>
          </dd>
        </div>
        {amount !== null ? (
          <div>
            <dt>{COST.budget}</dt>
            <dd>£{grouped(amount)}</dd>
          </div>
        ) : null}
      </dl>
      <div className={styles.bar} role="img" aria-label={COST.picture}>
        <span
          className={styles.span}
          style={{ insetInlineStart: `${at.lower}%`, width: `${at.upper - at.lower}%` }}
        />
        <span className={styles.median} style={{ insetInlineStart: `${at.median}%` }} />
        {at.budget !== null ? (
          <span className={styles.budget} style={{ insetInlineStart: `${at.budget}%` }} />
        ) : null}
      </div>
      {falls !== null ? <p className={styles.falls}>{falls}</p> : null}
      <SourceNote facts={[fact]} of={fact.label} />
    </div>
  );
}
