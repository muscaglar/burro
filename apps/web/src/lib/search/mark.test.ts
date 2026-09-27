import {
  added,
  answered as answeredTo,
  begunAgain,
  changeOf,
  edited,
  found,
  moved,
  NO_BOX,
  NOTHING_READ,
  notRead,
  putBack,
  ranked,
  readNoMore,
  sent,
  type Box,
  type Change,
  type Mark,
} from "./mark";

// A string found nowhere else, planted in what a person types.
const CANARY = "zqxcanary7431";

/** The change that a box makes of what it held and what it holds, as a browser tells of it. */
function typedOver(held: string, selected: { start: number; end: number }, typed: string): { holds: string; change: Change } {
  const holds = `${held.slice(0, selected.start)}${typed}${held.slice(selected.end)}`;
  const change = changeOf(
    { start: selected.start, holds: held.length },
    { end: selected.start + typed.length, holds: holds.length },
  );
  return { holds, change };
}

const read = (to: number, changed = false): Mark => ({ to, changed });
/** A box of which so much was read. */
const box = (to: number, more: Partial<Box> = {}): Box => ({ ...NO_BOX, read: read(to), ...more });
/** The words that were sent are answered, and something came of them. */
const answered = (open: Box) => answeredTo(open, true);
/** So many letters typed at the end of a box that held so many. */
const typed = (letters: number, held: number): Change => ({ at: held, out: 0, into: letters, holds: held + letters });

describe("where the box was changed", () => {
  test("test_a_letter_typed_at_the_end_is_placed_at_the_end", () => {
    expect(changeOf({ start: 5, holds: 5 }, { end: 6, holds: 6 })).toEqual({ at: 5, out: 0, into: 1, holds: 6 });
  });

  test("test_a_letter_typed_among_others_is_placed_where_the_caret_stood", () => {
    expect(changeOf({ start: 2, holds: 5 }, { end: 3, holds: 6 })).toEqual({ at: 2, out: 0, into: 1, holds: 6 });
  });

  test("test_a_letter_taken_out_from_behind_the_caret_or_from_before_it_is_placed", () => {
    // Backspace takes the letter before the caret, and leaves the caret where the letter was.
    expect(changeOf({ start: 4, holds: 9 }, { end: 3, holds: 8 })).toEqual({ at: 3, out: 1, into: 0, holds: 8 });
    // Delete takes the letter after it, and the caret stays.
    expect(changeOf({ start: 4, holds: 9 }, { end: 4, holds: 8 })).toEqual({ at: 4, out: 1, into: 0, holds: 8 });
    // A word taken out at once, as a key does that takes a word.
    expect(changeOf({ start: 9, holds: 9 }, { end: 4, holds: 4 })).toEqual({ at: 4, out: 5, into: 0, holds: 4 });
  });

  test("test_what_is_typed_or_pasted_over_a_selection_is_placed_where_the_selection_began", () => {
    const { change } = typedOver("leafy and quiet", { start: 6, end: 9 }, "or");

    expect(change).toEqual({ at: 6, out: 3, into: 2, holds: 14 });
    // All of it selected, and a sentence pasted over it.
    expect(changeOf({ start: 0, holds: 15 }, { end: 40, holds: 40 })).toEqual({ at: 0, out: 15, into: 40, holds: 40 });
  });

  test("test_a_change_that_is_undone_is_placed_by_where_it_ends", () => {
    // Letters typed at the end are undone while the caret stands among the words before them.
    expect(changeOf({ start: 3, holds: 20 }, { end: 12, holds: 12 }, "undone")).toEqual({ at: 12, out: 8, into: 0, holds: 12, how: "undone" });
    // Letters that were taken out come back, and the caret is left after them.
    expect(changeOf({ start: 3, holds: 12 }, { end: 20, holds: 20 }, "undone")).toEqual({ at: 12, out: 0, into: 8, holds: 20, how: "undone" });
    // It says that it was undone where it cannot be placed too, and a change that was typed says nothing of how.
    expect(changeOf({ start: 3, holds: 12 }, { end: 2, holds: 20 }, "undone")).toEqual({ at: null, out: 12, into: 20, holds: 20, how: "undone" });
    expect("how" in changeOf({ start: 5, holds: 5 }, { end: 6, holds: 6 })).toBe(false);
  });

  test("test_a_change_that_is_done_again_is_placed_as_one_that_is_undone_and_says_which_it_was", () => {
    expect(changeOf({ start: 3, holds: 12 }, { end: 20, holds: 20 }, "redone")).toEqual({ at: 12, out: 0, into: 8, holds: 20, how: "redone" });
    expect(changeOf({ start: 3, holds: 20 }, { end: 12, holds: 12 }, "redone")).toEqual({ at: 12, out: 8, into: 0, holds: 12, how: "redone" });
  });

  test("test_what_the_keys_that_undo_leave_selected_is_what_they_put_back", () => {
    // "lively" comes back where "quiet" stood, and is left selected: six came, and five went.
    expect(changeOf({ start: 3, holds: 15 }, { start: 10, end: 16, holds: 16 }, "undone")).toEqual({
      at: 10,
      out: 5,
      into: 6,
      holds: 16,
      how: "undone",
    });
    // As many came as went: by the counts alone nothing would have changed.
    expect(changeOf({ start: 3, holds: 15 }, { start: 0, end: 4, holds: 15 }, "undone")).toMatchObject({ at: 0, out: 4, into: 4 });
    expect(changeOf({ start: 3, holds: 15 }, { end: 4, holds: 15 }, "undone")).toMatchObject({ at: 4, out: 0, into: 0 });
    // Eight came and five are selected: that does not add up, and the change is placed by where it ends.
    expect(changeOf({ start: 3, holds: 12 }, { start: 15, end: 20, holds: 20 }, "undone")).toMatchObject({ at: 12, out: 0, into: 8 });
    // A caret is nothing selected, and what is selected once letters are typed places nothing.
    expect(changeOf({ start: 3, holds: 12 }, { start: 20, end: 20, holds: 20 }, "undone")).toMatchObject({ at: 12, out: 0, into: 8 });
    expect(changeOf({ start: 5, holds: 5 }, { start: 2, end: 6, holds: 6 })).toEqual({ at: 5, out: 0, into: 1, holds: 6 });
  });

  test("test_a_change_that_does_not_add_up_is_said_not_to_be_placed", () => {
    // The box holds more, and the caret stands where it stood: nobody can say where it grew.
    expect(changeOf({ start: 4, holds: 9 }, { end: 4, holds: 12 })).toEqual({ at: null, out: 9, into: 12, holds: 12 });
    // More went than stood after where the change is said to begin.
    expect(changeOf({ start: 8, holds: 9 }, { end: 8, holds: 2 }).at).toBeNull();
  });

  test("test_a_change_is_counts_and_holds_no_word_of_what_was_typed", () => {
    const { holds, change } = typedOver(`leafy ${CANARY}`, { start: 6, end: 6 + CANARY.length }, `${CANARY} and quiet`);

    expect(holds.includes(CANARY)).toBe(true);
    expect(Object.values(change).every((count) => typeof count === "number")).toBe(true);
    expect(JSON.stringify(change).includes(CANARY)).toBe(false);
  });
});

describe("how far the search has read, once the box is changed", () => {
  test("test_what_is_typed_after_what_was_read_leaves_it_as_it_was", () => {
    const mark = read(15);

    expect(moved(mark, { at: 15, out: 0, into: 1, holds: 16 })).toBe(mark);
    expect(moved(mark, { at: 22, out: 3, into: 0, holds: 30 })).toBe(mark);
  });

  test("test_a_change_among_the_words_that_were_read_moves_the_place_and_is_said", () => {
    // Two letters typed among them: the place moves on with the words after them.
    expect(moved(read(15), { at: 6, out: 0, into: 2, holds: 17 })).toEqual({ to: 17, changed: true });
    // Three taken out and two put in.
    expect(moved(read(15), { at: 6, out: 3, into: 2, holds: 30 })).toEqual({ to: 14, changed: true });
    // As many put in as were taken out: the place stays, and the words are not what was read.
    expect(moved(read(15), { at: 0, out: 5, into: 5, holds: 15 })).toEqual({ to: 15, changed: true });
  });

  test("test_taking_out_the_end_of_what_was_read_leaves_less_that_was_read", () => {
    // The last word is taken out, a letter at a time, and another typed in its place.
    const one = moved(read(15), { at: 14, out: 1, into: 0, holds: 14 });
    const all = [13, 12, 11, 10].reduce((mark, at) => moved(mark, { at, out: 1, into: 0, holds: at }), one);

    expect(one).toEqual({ to: 14, changed: false });
    expect(all).toEqual({ to: 10, changed: false });
    // What is typed from there is new, and is what is sent.
    expect(moved(all, { at: 10, out: 0, into: 6, holds: 16 })).toBe(all);
    expect(added("leafy and lively", all)).toBe("lively");
  });

  test("test_a_change_that_begins_among_what_was_read_and_ends_after_it_begins_what_is_new", () => {
    expect(moved(read(15), { at: 10, out: 12, into: 4, holds: 30 })).toEqual({ to: 10, changed: false });
    // What was changed before is still not what was read.
    expect(moved(read(15, true), { at: 10, out: 12, into: 4, holds: 30 })).toEqual({ to: 10, changed: true });
  });

  test("test_a_box_that_is_emptied_or_typed_over_whole_has_nothing_in_it_that_was_read", () => {
    expect(moved(read(15, true), { at: 0, out: 15, into: 0, holds: 0 })).toBe(NOTHING_READ);
    expect(moved(read(15), { at: 0, out: 15, into: 1, holds: 1 })).toBe(NOTHING_READ);
    expect(moved(read(15), { at: 0, out: 40, into: 22, holds: 22 })).toBe(NOTHING_READ);
    // And nothing was read of a box of which nothing was read.
    expect(moved(NOTHING_READ, { at: 3, out: 0, into: 1, holds: 9 })).toBe(NOTHING_READ);
  });

  test("test_a_change_that_cannot_be_placed_leaves_nothing_to_be_read_a_second_time", () => {
    // It may have been made anywhere. All that the box holds is taken as read, and as changed.
    expect(moved(read(15), { at: null, out: 20, into: 26, holds: 26 })).toEqual({ to: 26, changed: true });
    expect(added("x".repeat(26), moved(read(15), { at: null, out: 20, into: 26, holds: 26 }))).toBe("");
    // Where nothing was read there is nothing to read twice.
    expect(moved(NOTHING_READ, { at: null, out: 20, into: 26, holds: 26 })).toBe(NOTHING_READ);
  });

  test("test_a_change_of_nothing_changes_nothing", () => {
    const mark = read(15);

    expect(moved(mark, { at: 4, out: 0, into: 0, holds: 15 })).toBe(mark);
  });
});

describe("what is sent to be read", () => {
  test("test_it_is_what_stands_after_what_was_read_as_it_was_typed", () => {
    const first = "leafy and quiet";

    expect(added(`${first}, near a park `, read(first.length))).toBe(", near a park ");
    expect(added(first, read(first.length))).toBe("");
    expect(added(first, NOTHING_READ)).toBe(first);
  });

  test("test_a_place_the_box_does_not_reach_sends_nothing_and_never_fails", () => {
    expect(added("leafy", read(40))).toBe("");
    expect(added("leafy", read(-3))).toBe("leafy");
  });
});

describe("what the search knows of the box", () => {
  test("test_words_that_are_sent_are_read_once_they_are_answered_and_not_before", () => {
    const sending = sent(NO_BOX, 15);

    expect(sending.read).toBe(NOTHING_READ);
    expect(sending.sending).toEqual({ to: 15, changed: false });
    expect(answered(sending)).toEqual({ ...NO_BOX, read: { to: 15, changed: false }, shown: 0, before: NOTHING_READ });
    expect(ranked(answered(sending)).before).toBeNull();
  });

  test("test_what_is_added_is_read_from_where_the_search_had_read_to", () => {
    const after = ranked(answered(sent(box(15), 12)));

    expect(after.read).toEqual({ to: 27, changed: false });
    // The service counts where words stand from the start of what it was sent.
    expect(after.shown).toBe(15);
  });

  test("test_typing_after_what_was_read_tells_the_search_nothing_that_it_keeps", () => {
    // A person types what they add, letter by letter. Nothing of it is kept, not even how much.
    const open = box(15);

    expect(edited(open, typed(1, 15))).toBe(open);
    expect(edited(open, typed(1, 40))).toBe(open);
    expect(edited(open, { at: 20, out: 3, into: 0, holds: 30 })).toBe(open);
    // But that the box is not as it was sent, once: where the words of a reading stood is then not known.
    const shown = box(15, { shown: 0 });
    expect(edited(shown, typed(1, 15))).toEqual(open);
    expect(edited(NO_BOX, typed(1, 0))).toBe(NO_BOX);
  });

  test("test_words_that_were_not_read_are_still_to_be_read", () => {
    const after = notRead(sent(box(15), 12));

    expect(after.read).toEqual({ to: 15, changed: false });
    expect([after.sending, after.before]).toEqual([null, null]);
  });

  test("test_words_that_nothing_came_of_are_still_to_be_read", () => {
    // Nothing of them was made part of the search, so nothing of them can be read twice. A
    // person says them another way where they stand, and all of it is sent.
    const after = answeredTo(sent(box(15), 12), false);

    expect(after.read).toEqual({ to: 15, changed: false });
    expect(after.sending).toBeNull();
    // Where they stand is known all the same, so that they can be shown in the box.
    expect(after.shown).toBe(15);
    expect(added("leafy and quiet, by bicycle", after.read)).toBe(", by bicycle");
    // What is typed among them then is no change to words that were read.
    expect(edited(after, { at: 17, out: 0, into: 4, holds: 31 }).read).toEqual({ to: 15, changed: false });
  });

  test("test_words_that_a_model_goes_on_reading_are_read_once_it_makes_something_of_them", () => {
    const rules = answeredTo(sent(box(15), 12), false, true);

    expect(rules.read.to).toBe(15);
    expect(rules.sending).toEqual({ to: 27, changed: false });
    expect(answeredTo(rules, true).read).toEqual({ to: 27, changed: false });
    // It made nothing of them either, or did not answer: they are still to be read.
    expect(answeredTo(rules, false).read.to).toBe(15);
    expect(readNoMore(rules)).toEqual({ ...rules, sending: null });
    expect(readNoMore(box(15))).toEqual(box(15));
  });

  test("test_stop_puts_back_how_far_the_search_had_read_when_the_sentence_was_sent", () => {
    const readAndNotRanked = answered(sent(box(15), 12));

    expect(readAndNotRanked.read.to).toBe(27);
    expect(putBack(readAndNotRanked)).toEqual({ ...NO_BOX, read: { to: 15, changed: false } });
    // A sentence sent before the last one was ranked is undone with it.
    const again = answered(sent(readAndNotRanked, 3));
    expect(again.read.to).toBe(30);
    expect(putBack(again).read.to).toBe(15);
  });

  test("test_every_place_moves_with_the_words_when_the_box_is_changed_while_words_are_read", () => {
    const sending = sent(box(15), 12);

    // Two letters are typed among the words that were read before.
    const among = edited(sending, { at: 3, out: 0, into: 2, holds: 29 });
    expect(among.read).toEqual({ to: 17, changed: true });
    expect(among.before).toEqual({ to: 17, changed: true });
    expect(among.sending).toEqual({ to: 29, changed: true });
    // More is typed after the words that are being read: they are read as they were sent.
    const after = edited(sending, typed(4, 27));
    expect(after.sending).toEqual({ to: 27, changed: false });
    expect(answered(after).read).toEqual({ to: 27, changed: false });
    expect(added("x".repeat(31), answered(after).read)).toBe("xxxx");
  });

  test("test_where_the_words_stand_is_not_known_once_the_box_has_changed", () => {
    const shown = answered(sent(NO_BOX, 15));

    expect(shown.shown).toBe(0);
    expect(edited(shown, typed(1, 15)).shown).toBeNull();
    // Nor for words that were changed while they were read.
    const changed = answered(edited(sent(NO_BOX, 15), { at: 3, out: 1, into: 1, holds: 15 }));
    expect(changed.shown).toBeNull();
    expect(changed.read).toEqual({ to: 15, changed: true });
  });

  test("test_a_box_that_is_drawn_again_is_empty_and_nothing_in_it_was_read", () => {
    const left = box(27, { shown: 15, before: read(15) });

    expect(found(left, 0)).toEqual({ ...NO_BOX, before: NOTHING_READ });
    expect(found(box(27, { shown: 15 }), 0)).toEqual(NO_BOX);
    // A box that holds all that was read is left as the search knows it.
    expect(found(left, 27)).toBe(left);
    expect(found(left, 40)).toBe(left);
    expect(found(NO_BOX, 0)).toBe(NO_BOX);
    // A box that holds less than was read: nobody knows what it holds, so none of it is read again.
    expect(found(left, 9).read).toEqual({ to: 9, changed: true });
    expect(found(left, 9).shown).toBeNull();
  });

  test("test_a_search_that_begins_again_has_read_nothing_of_what_the_box_still_holds", () => {
    expect(begunAgain()).toBe(NO_BOX);
    expect(added("leafy and quiet", begunAgain().read)).toBe("leafy and quiet");
  });

  test("test_what_is_known_of_the_box_is_counts_and_whether_a_thing_is_so", () => {
    const leaves = (value: unknown): unknown[] =>
      value !== null && typeof value === "object" ? Object.values(value).flatMap(leaves) : [value];
    const sentence = `leafy and quiet, near ${CANARY}`;
    const more = added(sentence, read(15));
    const open = answered(sent(box(15), more.length));

    expect(more.includes(CANARY)).toBe(true);
    expect(open.read.to).toBe(sentence.length);
    expect(leaves(open).map((leaf) => (leaf === null ? "null" : typeof leaf))).toEqual(
      expect.arrayContaining(["number", "boolean"]),
    );
    expect(leaves(open).filter((leaf) => leaf !== null && typeof leaf !== "number" && typeof leaf !== "boolean")).toEqual([]);
    expect(JSON.stringify(open).includes(CANARY)).toBe(false);
  });
});

describe("words that were read, taken out of the box and put back", () => {
  // Seen in a browser: the whole of a box that was read was selected, a letter was typed
  // over it by accident, and the keys that undo put the sentence back. Search then sent the
  // sentence again, onto a search that had been set by hand: what came back into the box
  // stood after the place the search had read to, and was taken for new.
  const first = "leafy and quiet";
  /** So many characters are taken out from such a place, of a box that held so many. */
  const takenOut = (at: number, out: number, held: number): Change => ({ at, out, into: 0, holds: held - out });
  /**
   * The keys that undo leave the box holding so many. What they put back they leave
   * selected, and where they took letters out they leave the caret.
   */
  const undone = (held: number, holds: number, selected: { start?: number; end: number } = { end: holds }): Change =>
    changeOf({ start: held, holds: held }, { ...selected, holds }, "undone");
  /** The keys that do again leave the caret after what they put back, or where they took letters out. */
  const redone = (held: number, holds: number, end = holds): Change =>
    changeOf({ start: held, holds: held }, { end, holds }, "redone");
  const marks = ({ read, sending, before }: Box) => ({ read, sending, before });

  test("test_the_end_of_what_was_read_is_not_new_once_the_keys_that_undo_put_it_back", () => {
    const open = box(15);

    // " quiet" is selected and taken out: what is left that was read ends where it stood.
    const out = edited(open, takenOut(9, 6, 15));
    expect(out.read).toEqual({ to: 9, changed: false });
    expect(out.gone).toBe(6);
    // The keys that undo put it back. The box holds what it held, and nothing in it is new.
    const back = edited(out, undone(9, 15, { start: 9, end: 15 }));

    expect(marks(back)).toEqual(marks(open));
    expect([back.gone, back.back]).toEqual([0, []]);
    expect(added(first, back.read)).toBe("");
  });

  test("test_a_box_that_was_typed_over_or_emptied_and_put_back_holds_nothing_new", () => {
    // All of it selected and one letter typed, which leaves nothing that was read.
    const over = edited(box(15), { at: 0, out: 15, into: 1, holds: 1 });
    expect(over.read).toEqual(NOTHING_READ);
    expect(edited(over, undone(1, 15, { start: 0, end: 15 })).read).toEqual({ to: 15, changed: false });
    // All of it taken out.
    const emptied = edited(box(15), takenOut(0, 15, 15));
    expect(emptied.read).toEqual(NOTHING_READ);
    expect(edited(emptied, undone(0, 15, { start: 0, end: 15 })).read).toEqual({ to: 15, changed: false });
    expect(added(first, edited(emptied, undone(0, 15)).read)).toBe("");
  });

  test("test_letters_taken_out_one_by_one_are_not_new_when_they_are_put_back", () => {
    const out = [14, 13, 12].reduce((now, at) => edited(now, takenOut(at, 1, at + 1)), box(15));
    expect(out.read).toEqual({ to: 12, changed: false });
    expect(out.gone).toBe(3);

    // All three at once, as a browser puts back what one run of a key took out.
    expect(marks(edited(out, undone(12, 15, { start: 12, end: 15 })))).toEqual(marks(box(15)));
    // Or one, and then two. Of a box put back in part nobody can be sure, and it is said.
    const one = edited(out, undone(12, 13, { start: 12, end: 13 }));
    expect(one.read).toEqual({ to: 13, changed: true });
    expect(marks(edited(one, undone(13, 15, { start: 13, end: 15 })))).toEqual(marks(box(15)));
  });

  test("test_what_is_put_back_after_more_was_done_to_the_box_is_taken_as_read_and_is_said", () => {
    // " quiet" is taken out, "near" is typed where it stood, and the keys that undo are
    // pressed twice: "near" goes, and " quiet" comes back.
    const typedOver = edited(edited(box(15), takenOut(9, 6, 15)), typed(4, 9));
    expect(typedOver.read).toEqual({ to: 9, changed: false });
    const less = edited(typedOver, undone(13, 9));
    expect(less.read).toEqual({ to: 9, changed: false });

    const back = edited(less, undone(9, 15, { start: 9, end: 15 }));

    // It cannot be told from what was read, so none of it is sent. That a change was made is said.
    expect(back.read).toEqual({ to: 15, changed: true });
    expect(added(first, back.read)).toBe("");
  });

  test("test_words_typed_over_the_end_and_read_bring_nothing_new_when_they_are_undone", () => {
    // " quiet" is typed over with " calm", which is sent and read. The keys that undo then
    // put " quiet" back where " calm" stood, in one go: the box holds one letter more.
    const over = edited(box(15), { at: 9, out: 6, into: 5, holds: 14 });
    const calm = ranked(answered(sent(over, 5)));
    expect(calm.read).toEqual({ to: 14, changed: false });

    for (const selected of [{ start: 9, end: 15 }, { end: 15 }]) {
      const back = edited(calm, undone(14, 15, selected));

      expect(back.read).toEqual({ to: 15, changed: true });
      expect(added(first, back.read)).toBe("");
    }
  });

  test("test_words_that_were_read_and_undone_out_of_the_box_are_not_new_when_they_are_done_again", () => {
    // ", park" was typed after the sentence, sent and read. The keys that undo take it out.
    const read = ranked(answered(sent(box(15), 6)));
    const out = edited(read, undone(21, 15));
    expect(out.read.to).toBe(15);

    const again = edited(out, redone(15, 21));

    expect(again.read).toEqual({ to: 21, changed: false });
    expect(added(`${first}, park`, again.read)).toBe("");
  });

  test("test_what_was_typed_and_not_read_is_new_still_when_it_is_undone_and_done_again", () => {
    // Nothing that was read was taken out, so nothing that was read can be put back.
    const open = box(15);
    const more = edited(open, typed(6, 15));
    expect(more).toBe(open);

    const again = edited(edited(more, undone(21, 15)), redone(15, 21));

    expect(marks(again)).toEqual(marks(open));
    expect(added(`${first}, park`, again.read)).toBe(", park");
    // Nor after words were taken out that were typed after what was read.
    expect(marks(edited(edited(more, takenOut(17, 4, 21)), undone(17, 21, { start: 17, end: 21 })))).toEqual(marks(open));
  });

  test("test_what_the_keys_that_undo_take_out_of_what_was_added_leaves_the_rest_of_it_to_be_read", () => {
    // A letter of the sentence was taken out by accident and typed again, more was typed,
    // and the last of it undone. One letter more than was read may be what was read.
    const retyped = edited(edited(box(15), takenOut(14, 1, 15)), typed(1, 14));
    const more = edited(retyped, typed(13, 15));
    expect(added(`${first}, near a park`, more.read)).toBe("t, near a park");

    const less = edited(more, undone(28, 21));

    expect(less.read).toEqual({ to: 15, changed: true });
    expect(added(`${first}, near`, less.read)).toBe(", near");
  });

  test("test_words_that_were_read_are_not_new_when_they_are_cut_out_and_pasted_back", () => {
    const out = edited(box(15), takenOut(9, 6, 15));

    // Where they stood.
    const back = edited(out, { at: 9, out: 0, into: 6, holds: 15, how: "pasted" });
    expect(back.read).toEqual({ to: 15, changed: true });
    // Or at the end, after a comma: they are moved, and what stands before them is not read either.
    const moved = edited(edited(out, typed(2, 9)), { at: 11, out: 0, into: 6, holds: 17, how: "pasted" });
    expect(moved.read).toEqual({ to: 17, changed: true });
    expect(added("leafy and, quiet ", moved.read)).toBe("");
  });

  test("test_a_copy_of_what_was_read_is_not_new_when_it_is_pasted", () => {
    // After the sentence, which is then in the box twice.
    expect(edited(box(15), { at: 15, out: 0, into: 15, holds: 30, how: "pasted" }).read).toEqual({ to: 30, changed: true });
    // Or over the whole of it.
    expect(edited(box(15), { at: 0, out: 15, into: 15, holds: 15, how: "pasted" }).read).toEqual({ to: 15, changed: true });
    // What is pasted that was never in the box is new, as what is typed is.
    expect(edited(box(15), { at: 15, out: 0, into: 15, holds: 30 })).toEqual(box(15));
  });

  test("test_what_the_search_knew_before_words_were_taken_out_is_let_go_when_the_search_moves_on", () => {
    // Words are taken out while others are read. Their answer moves every place, so what
    // was known before is not put back: what the keys that undo bring is taken as read.
    const out = edited(sent(box(15), 6), takenOut(9, 6, 21));
    expect(out.back).toHaveLength(1);
    // And so with what the keys that do again lead to.
    const undid = edited(sent(box(15), 6), undone(21, 15));
    expect(undid.again).toHaveLength(1);

    for (const open of [out, undid]) {
      for (const moved of [sent(open, 3), answered(open), answeredTo(open, false), notRead(open), readNoMore(open), ranked(open), putBack(open)]) {
        expect([moved.back, moved.again]).toEqual([[], []]);
        expect(moved.gone).toBe(open.gone);
      }
    }
    const back = edited(ranked(answered(out)), undone(15, 21, { start: 9, end: 15 }));
    expect(back.read).toEqual({ to: 21, changed: true });
  });

  test("test_a_box_that_is_drawn_again_and_a_search_that_begins_again_hold_nothing_to_put_back", () => {
    const out = edited(box(15), takenOut(9, 6, 15));
    const undid = edited(out, undone(9, 12, { start: 9, end: 12 }));
    expect([undid.back.length, undid.again.length]).toEqual([1, 1]);

    expect(found(undid, 0)).toEqual(NO_BOX);
    expect(found(undid, 9)).toMatchObject({ gone: 0, back: [], again: [] });
    expect(begunAgain()).toEqual(NO_BOX);
    expect(NO_BOX).toMatchObject({ gone: 0, back: [], again: [] });
  });

  test("test_what_is_kept_to_know_it_is_counts_and_whether_a_thing_is_so", () => {
    const leaves = (value: unknown): unknown[] =>
      value !== null && typeof value === "object" ? Object.values(value).flatMap(leaves) : [value];
    const { holds, change } = typedOver(`${first} ${CANARY}`, { start: 9, end: 16 + CANARY.length }, "");
    const out = edited(sent(box(15), 1 + CANARY.length), change);
    // The keys that undo put a part of it back, and what they lead from is kept too.
    const undid = edited(out, undone(9, 12, { start: 9, end: 12 }));

    expect(holds).toBe("leafy and");
    expect(out.back).toMatchObject([{ held: 16 + CANARY.length, read: { to: 15 } }]);
    expect(undid.again).toMatchObject([{ held: 9, read: { to: 9 } }]);
    expect(leaves(undid).length).toBeGreaterThan(24);
    expect(leaves(undid).filter((leaf) => leaf !== null && typeof leaf !== "number" && typeof leaf !== "boolean")).toEqual([]);
    expect(JSON.stringify([out, undid]).includes(CANARY)).toBe(false);
  });
});

describe("where the keys that undo and that do again lead", () => {
  // Found by changing many boxes at random and following every word. What the search knew
  // of the box was put back once the keys that undo left the box as long as it had been,
  // and they had led further back than that: to a box as long, that held other words.
  const first = "leafy and quiet";
  const takenOut = (at: number, out: number, held: number): Change => ({ at, out, into: 0, holds: held - out });
  const undone = (held: number, holds: number, selected: { start?: number; end: number } = { end: holds }): Change =>
    changeOf({ start: held, holds: held }, { ...selected, holds }, "undone");
  const redone = (held: number, holds: number, end = holds): Change =>
    changeOf({ start: held, holds: held }, { end, holds }, "redone");

  test("test_the_keys_that_undo_pressed_again_lead_further_back_and_no_word_that_was_read_is_new", () => {
    // Eleven letters were read. Eight of them are taken out, six typed where they stood and
    // read, and two more typed: the box holds eleven, of which nine were read.
    const out = edited(box(11), takenOut(1, 8, 11));
    const more = edited(ranked(answered(sent(edited(out, typed(6, 3)), 6))), typed(2, 9));
    expect(more.read.to).toBe(9);
    // The keys that undo take out all eight that were typed.
    const less = edited(more, undone(11, 3));
    expect(less.read.to).toBe(3);

    // Pressed again, they put back the eight that were taken out first. The box holds
    // eleven as it did a moment ago, and they are the eleven that were read.
    const back = edited(less, undone(3, 11, { start: 1, end: 9 }));

    expect(back.read).toEqual({ to: 11, changed: true });
    expect(added("x".repeat(11), back.read)).toBe("");
    // So where the browser leaves no more than a caret after what it put back.
    expect(added("x".repeat(11), edited(less, undone(3, 11, { end: 9 })).read)).toBe("");
  });

  test("test_the_keys_that_do_again_lead_back_to_the_box_as_it_was_before_the_keys_that_undo", () => {
    // All of a sentence that was read is selected, and thirty letters are pasted over it
    // from elsewhere. The keys that undo put the sentence back, and nothing in it is new.
    const over = edited(box(85), { at: 0, out: 85, into: 30, holds: 30 });
    const back = edited(over, undone(30, 85, { start: 0, end: 85 }));
    expect(back.read).toEqual({ to: 85, changed: false });

    // The keys that do again put back what was pasted: none of it was read, and all of it is new.
    const again = edited(back, redone(85, 30));

    expect(again.read).toEqual(NOTHING_READ);
    expect(added("x".repeat(30), again.read)).toHaveLength(30);
    // And back, and again.
    const once = edited(again, undone(30, 85, { start: 0, end: 85 }));
    expect(once.read).toEqual({ to: 85, changed: false });
    expect(edited(once, redone(85, 30)).read).toEqual(NOTHING_READ);
  });

  test("test_the_keys_that_do_again_lead_back_through_every_press_of_the_keys_that_undo", () => {
    // Seen in a browser: ", park" was read, and ", cheap" typed after it. The keys that
    // undo were pressed four times, until the box was empty, and the keys that do again
    // four times. ", cheap" was never read, and is what is sent.
    const read = edited(ranked(answered(sent(box(15), 6))), typed(7, 21));
    const undid = [21, 15, 6, 0].reduce((now, holds, press) => edited(now, undone([28, 21, 15, 6][press] ?? 0, holds)), read);
    expect(undid.read).toEqual(NOTHING_READ);
    expect(undid.again).toHaveLength(4);

    const again = [6, 15, 21, 28].reduce((now, holds, press) => edited(now, redone([0, 6, 15, 21][press] ?? 0, holds)), undid);

    expect(again.read).toEqual({ to: 21, changed: false });
    expect(added(`${first}, park, cheap`, again.read)).toBe(", cheap");
    expect([again.gone, again.again]).toEqual([0, []]);
    // And back again, as far as they were pressed.
    const back = [21, 15].reduce((now, holds, press) => edited(now, undone([28, 21][press] ?? 0, holds)), again);
    expect(back.read.to).toBe(15);
    expect(edited(edited(back, redone(15, 21)), redone(21, 28)).read).toEqual({ to: 21, changed: false });
  });

  test("test_no_more_is_kept_than_a_person_presses_those_keys_in_a_row", () => {
    const many = Array.from({ length: 200 }, (_, press) => 200 - press);

    const undid = many.reduce((now, holds) => edited(now, undone(holds, holds - 1)), box(200));

    expect(undid.again.length).toBeLessThanOrEqual(64);
    expect(undid.read.to).toBe(0);
  });

  test("test_what_is_typed_lets_go_of_where_those_keys_would_lead", () => {
    const back = edited(edited(box(15), takenOut(9, 6, 15)), undone(9, 12, { start: 9, end: 12 }));
    expect([back.back.length, back.again.length]).toEqual([1, 1]);

    const more = edited(back, typed(4, 12));

    expect([more.back, more.again]).toEqual([[], []]);
  });

  test("test_what_was_kept_is_put_back_only_where_as_much_went_as_had_come", () => {
    // Five letters are read, the last of them typed over another. The last two are rubbed
    // out, and the keys that undo put back two: the one that was read, or the one it was
    // typed over. The box is as long either way, and what is selected is the same.
    const out = [4, 3].reduce((now, at) => edited(now, takenOut(at, 1, at + 1)), box(5));

    expect(edited(out, undone(3, 5, { start: 3, end: 5 })).read).toEqual({ to: 5, changed: false });
    // Where they put back more than was taken out, and took out what stood there, it is
    // not the box as it was: what they put back is taken as read, and it is said.
    const other = edited(out, undone(3, 5, { start: 0, end: 5 }));
    expect(other.read).toEqual({ to: 5, changed: true });
  });

  test("test_what_those_keys_put_in_place_of_words_that_were_read_is_not_read_and_it_is_said", () => {
    // "quiet" was typed over "lively" before it was sent, and was read. The keys that undo
    // put "lively" back in its place: no letter of it was read, and none of it is sent as
    // though it were added.
    const lively = "leafy and lively";
    const read = box(15);

    const back = edited(read, undone(15, 16, { start: 10, end: 16 }));

    expect(back.read).toEqual({ to: 16, changed: true });
    expect(added(lively, back.read)).toBe("");
    // As long a word in its place leaves the counts as they were. What is selected says that it came.
    expect(edited(read, undone(15, 15, { start: 10, end: 15 })).read).toEqual({ to: 15, changed: true });
  });

  test("test_words_that_were_read_and_are_undone_out_of_the_box_are_said_to_be_changed", () => {
    // What those keys take out may leave other words where it stood: nobody can tell.
    const read = ranked(answered(sent(box(15), 6)));

    expect(edited(read, undone(21, 15)).read).toEqual({ to: 15, changed: true });
    // What they take out of what was never read says nothing of what was.
    expect(edited(edited(box(15), typed(6, 15)), undone(21, 15)).read).toEqual({ to: 15, changed: false });
  });

  test("test_the_keys_that_do_again_lead_nobody_knows_where_once_the_search_has_moved_on", () => {
    // Nine letters are typed over five. The keys that undo put the five back, which are
    // sent and read. The keys that do again put the nine in their place.
    const five = ranked(answered(sent(edited(found(NO_BOX, 9), undone(9, 5, { start: 0, end: 5 })), 5)));
    expect(five.read).toEqual({ to: 5, changed: false });

    const nine = edited(five, redone(5, 9));

    // What stands after what was read is sent, and that the words before it are not as they were read is said.
    expect(nine.read).toEqual({ to: 5, changed: true });
    // Nothing of the box was read: there is nothing to say of it.
    expect(edited(found(NO_BOX, 5), redone(5, 9)).read).toEqual(NOTHING_READ);
  });
});
