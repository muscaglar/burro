"use client";

import { useEffect, useRef, useState } from "react";

import { ACCOUNT } from "@/content/account";
import type { Failure } from "@/lib/api/failure";
import type { AccountClient } from "@/lib/account/client";

import { Box, Failed } from "../AccountParts/parts";
import parts from "../AccountParts/parts.module.css";
import { Press } from "../kit/Press/Press";
import styles from "./Account.module.css";

interface Props {
  readonly client: Pick<AccountClient, "exportMe">;
}

/**
 * A copy of everything Burro holds of an account, as a file a person saves.
 *
 * The copy is asked of the service when the button is pressed, and is held in memory
 * while the page is open: it is drawn nowhere on the page, and kept in nothing. It is
 * offered as a file by an address the browser makes for what the page holds, which leads
 * to no server and holds nothing of the copy. That address is let go when another copy is
 * made, and when the page is left.
 *
 * It is as the service gave it, set out so that a person can read it. The button that
 * made it keeps the focus, and the link that saves it is the next thing a keyboard comes to.
 */
export function Copy({ client }: Props) {
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<Failure | null>(null);
  const [file, setFile] = useState<string | null>(null);
  // The address of the copy that is offered, to let go of it when it is no longer.
  const offered = useRef<string | null>(null);

  const letGo = () => {
    if (offered.current !== null) URL.revokeObjectURL(offered.current);
    offered.current = null;
  };

  useEffect(() => letGo, []);

  const make = async () => {
    if (busy) return;
    setBusy(true);
    setFailure(null);
    const answer = await client.exportMe();
    setBusy(false);
    if (!answer.ok) {
      // A call that was stopped has nothing to report.
      if (answer.failure.kind !== "aborted") setFailure(answer.failure);
      return;
    }
    letGo();
    const held = new Blob([`${JSON.stringify(answer.data, null, 2)}\n`], { type: "application/json" });
    offered.current = URL.createObjectURL(held);
    setFile(offered.current);
  };

  return (
    <Box title={ACCOUNT.copy.title}>
      <p>{ACCOUNT.copy.text}</p>
      <div className={parts.ways}>
        <Press off={busy} onPress={() => void make()}>
          {ACCOUNT.copy.make}
        </Press>
      </div>
      <p className={parts.said} role="status">
        {busy ? ACCOUNT.copy.making : file !== null ? ACCOUNT.copy.ready : ""}
      </p>
      {file === null ? null : (
        <p className={styles.saves}>
          {/* It leads to what the page holds, and to no server. */}
          <a className="target" href={file} download={ACCOUNT.copy.file}>
            {ACCOUNT.copy.save}
          </a>
        </p>
      )}
      {failure === null ? null : <Failed title={ACCOUNT.copy.failed} failure={failure} />}
    </Box>
  );
}
