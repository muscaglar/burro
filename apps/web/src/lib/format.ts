/**
 * How a date the API sent is written for a person to read.
 *
 * Only dates are formatted here. A figure about a place arrives already
 * formatted, in a fact's slots, and is shown as it came.
 */

const DAY = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "long",
  year: "numeric",
  timeZone: "UTC",
});

const MONTH_AND_YEAR = new Intl.DateTimeFormat("en-GB", {
  month: "long",
  year: "numeric",
  timeZone: "UTC",
});

const DATE = /^\d{4}-\d{2}-\d{2}$/;
const MONTH = /^\d{4}-(0[1-9]|1[0-2])$/;
const TIMESTAMP = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$/;

/**
 * A date or a timestamp, as "23 September 2026", and a month, as "August
 * 2026". Anything else is returned as it came: a year, or a period such as
 * "2024-10 to 2026-09", is the release's own words.
 */
export function readableDate(value: string): string {
  if (MONTH.test(value)) {
    const month = new Date(`${value}-01T00:00:00Z`);
    return Number.isNaN(month.getTime()) ? value : MONTH_AND_YEAR.format(month);
  }
  if (!DATE.test(value) && !TIMESTAMP.test(value)) return value;
  const parsed = new Date(DATE.test(value) ? `${value}T00:00:00Z` : value);
  return Number.isNaN(parsed.getTime()) ? value : DAY.format(parsed);
}

/** A weight from 0 to 1, as the whole number from 0 to 100 that a control shows. */
export function outOfHundred(weight: number): string {
  return String(Math.round(weight * 100));
}

/** A whole number with separators between the thousands. */
export function grouped(value: number): string {
  return new Intl.NumberFormat("en-GB", { maximumFractionDigits: 0 }).format(value);
}
