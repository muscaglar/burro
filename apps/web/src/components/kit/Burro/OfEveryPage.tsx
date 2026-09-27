"use client";

import { Burro } from "./Burro";
import { useOnThePage } from "./onThePage";

/**
 * Burro as what every page stands in draws him: he sits, seen from his back up, behind
 * the rule of the name board or of the foot. He stirs there as he does wherever he rests.
 *
 * He is one rabbit. While the page itself draws him, nothing of him is here. Wherever he
 * is drawn he is dress: he is not heard, and a keyboard does not stop at him.
 */
export function BurroOfEveryPage() {
  const onThePage = useOnThePage();
  if (onThePage) return null;
  return <Burro pose="sits" peeps ofEveryPage />;
}
