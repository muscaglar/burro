/**
 * Which parts of what a person typed no edit was read from.
 *
 * Route 1 says which words of the text each edit rests on, as offsets
 * (`rests_on`, contract 9.2). It does not say which sentences it made nothing
 * of. The reader reads a sentence only when it knows every word in it, and
 * makes no edit from any other (contract 8.2), so a sentence no edit rests on
 * is a part that was not read. Until the API says which those are
 * (docs/design/web.md, section 13), they are worked out here, by the rule the
 * reader itself ends a sentence by: at a full stop, a question mark or an
 * exclamation mark that ends a word, and at a new line.
 *
 * Nothing here keeps or returns a word. It takes the text from the box, where
 * it already is, and gives back offsets into it, for the box to select.
 */

/** Where words stand in a text: from `start` up to `end`, which is not included. */
export interface Span {
  readonly start: number;
  readonly end: number;
}

// As `burro_core` holds them. A mark of these kinds at the end of a word is not part of the word.
const APOSTROPHES = "'`\u2019\u2018\u02bc\u2032\uff07";
const QUOTES = '"\u201c\u201d\u201e\u00ab\u00bb';
const BEFORE = `([{${QUOTES}${APOSTROPHES}`;
const ENDS = ".!?\u2026";
const AFTER = `)]}${QUOTES}${APOSTROPHES},;:${ENDS}`;
const DASHES = "-\u2013\u2014\u2015";
// Written as text: the line separators themselves, put into a pattern, would end it.
const LINE_BREAK = new RegExp("[\\n\\r\\v\\f\\u001c\\u001d\\u001e\\u0085\\u2028\\u2029]");

/** The sentences of a text, each from its first word to the end of its last, marks included. */
function sentencesOf(text: string): Span[] {
  const sentences: Span[] = [];
  let began = -1;
  let ended = 0;
  let words = 0;
  const close = () => {
    if (words > 0) sentences.push({ start: began, end: ended });
    began = -1;
    words = 0;
  };
  for (const chunk of text.matchAll(/\S+/g)) {
    const typed = chunk[0];
    const from = chunk.index;
    if (began >= 0 && LINE_BREAK.test(text.slice(ended, from))) close();
    let lead = 0;
    while (lead < typed.length && BEFORE.includes(typed.charAt(lead))) lead += 1;
    let tail = typed.length;
    while (tail > lead && AFTER.includes(typed.charAt(tail - 1))) tail -= 1;
    const core = typed.slice(lead, tail);
    const isWord = core !== "" && ![...core].every((character) => DASHES.includes(character));
    const marks = isWord ? typed.slice(tail) : typed;
    if (isWord) {
      if (began < 0) began = from;
      words += 1;
      ended = from + typed.length;
    } else if (began >= 0) ended = from + typed.length;
    if ([...marks].some((mark) => ENDS.includes(mark))) close();
  }
  close();
  return sentences;
}

/** For each count of code points into `text`, how far that is as JavaScript counts. */
function unitsOf(text: string): number[] {
  const units = [0];
  for (const character of text) units.push((units.at(-1) ?? 0) + character.length);
  return units;
}

/**
 * The parts of what is in the box that no edit rests on, in the order they
 * stand, as offsets into the box as it stands now.
 *
 * `restsOn` is route 1's, counted in code points into the text as it was
 * sent, which is what is in the box without the space around it. The offsets
 * mean nothing unless the box still holds what was sent: whoever calls this
 * must know that it does.
 */
export function unreadStretches(box: string, restsOn: readonly Span[]): Span[] {
  const lead = box.length - box.trimStart().length;
  const sent = box.trim();
  const units = unitsOf(sent);
  const last = units.length - 1;
  const within = (count: number) => units[Math.min(last, Math.max(0, Math.trunc(count)))] ?? 0;
  const read = restsOn
    .map(({ start, end }) => ({ start: within(start), end: within(end) }))
    .filter(({ start, end }) => end > start);

  const parts: Span[] = [];
  let joined = false;
  for (const sentence of sentencesOf(sent)) {
    const wasRead = read.some(({ start, end }) => start < sentence.end && end > sentence.start);
    if (wasRead) {
      joined = false;
      continue;
    }
    const before = parts.at(-1);
    // Two sentences side by side that were not read are one part.
    if (joined && before !== undefined) parts[parts.length - 1] = { start: before.start, end: sentence.end + lead };
    else parts.push({ start: sentence.start + lead, end: sentence.end + lead });
    joined = true;
  }
  return parts;
}
