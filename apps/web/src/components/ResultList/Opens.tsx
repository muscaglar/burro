"use client";

import type { CSSProperties, ReactNode, Ref } from "react";

import { pictureOf } from "@/components/kit/drawings";
import { picturesOf } from "@/components/kit/Press/kinds";
import press from "@/components/kit/Press/Press.module.css";

interface Props {
  /** The whole name, where what is seen is the start of it: "Show the working", and of which area. */
  readonly name: string;
  /** Whether what it opens is open. It is then amber, as what is on is. */
  readonly open: boolean;
  /** The id of what it opens. */
  readonly controls: string;
  readonly onPress: () => void;
  /** The button itself, for whatever gives it the focus back when what it opened is closed. */
  readonly ref?: Ref<HTMLButtonElement>;
  readonly children: ReactNode;
}

/**
 * A button that opens what stands under a result, and closes it. It is drawn as the part
 * Press of the kit draws a button, by the style sheet and the pictures of that part: lit
 * from the top left, with a hard shadow, its face stepping into its shadow under a press.
 *
 * While what it opened is open it is amber, as what is on is. It says that it is open, as
 * a button that opens something does, and never that it is pressed: so it is a part of
 * its own, because a button of the kit that is amber says that it is pressed.
 */
export function Opens({ name, open, controls, onPress, ref, children }: Props) {
  const { up, down } = picturesOf("plain", open);
  const drawn = { "--art": `url("${pictureOf(up)}")`, "--art-down": `url("${pictureOf(down)}")` } as CSSProperties;
  return (
    <button
      ref={ref}
      type="button"
      className={`${press.press} target`}
      aria-label={name}
      aria-expanded={open}
      aria-controls={controls}
      onClick={onPress}
    >
      <span className={press.face} data-kind={open ? "on" : "plain"} style={drawn}>
        <span className={press.says} data-reads="false">
          {children}
        </span>
      </span>
    </button>
  );
}
