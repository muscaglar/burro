import { NAMED } from "@/content/area";
import { besideTheName, isDraft, type NamedArea } from "@/lib/area/named";

import styles from "./BesideName.module.css";

interface Props {
  readonly area: NamedArea;
  /** How the place it stands in draws what is beside a name: smaller, and in a quieter colour. */
  readonly className?: string | undefined;
  /**
   * True in a table, where the borough has a column of its own and every row would say the
   * same of its name: the label alone is drawn, and only where it is not the name.
   */
  readonly labelOnly?: boolean;
}

/**
 * What stands beside the name of an area, smaller: its borough, the label its
 * publisher gives the area where the area bears another name, and that the
 * name is a draft where no person has checked it. Every name is the API's.
 * Nothing is drawn for an area whose name says it all.
 */
export function BesideName({ area, className, labelOnly = false }: Props) {
  const label = area.named?.label ?? null;
  const parts = labelOnly ? (label === null ? [] : [label]) : besideTheName(area);
  const draft = !labelOnly && isDraft(area);
  if (parts.length === 0 && !draft) return null;
  return (
    <p className={className}>
      {parts.join(NAMED.between)}
      {draft ? (
        <span className={styles.draft}>
          {parts.length > 0 ? NAMED.between : null}
          {NAMED.draft}
        </span>
      ) : null}
    </p>
  );
}
