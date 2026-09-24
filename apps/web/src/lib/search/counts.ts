/**
 * Whether a weight in a spec counts for anything.
 *
 * A spec keeps an entry of 0 for a feature a person took off, so that a change
 * of tenure does not bring its default back (contract section 5.1). Such an
 * entry counts for nothing: the API ranks as if it were not there. The website
 * draws it as off, and never as a thing that was asked for.
 */
export function counts(weight: { readonly weight: number } | undefined): boolean {
  return weight !== undefined && weight.weight > 0;
}
