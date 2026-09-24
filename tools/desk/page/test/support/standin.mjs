// A small stand-in for the desk's server, for the page's tests.
//
// It answers as section 4 of docs/design/desk.md says the server answers, and
// keeps its lines in memory. It is not the server and tests nothing of it. Every
// name in it is made up, and every id begins `syn-`.

import { pathOf, start, step, view } from '../../logic.mjs';

const RULE =
  'Use what you know and what the page shows. Copy no name and no border from a map or a website.';

export const QUESTIONS = {
  names: {
    id: 'names',
    title: 'Names',
    text: 'Is this the name of an area?',
    rule: RULE,
    view: 'map',
    adds: 'pick',
    public: true,
    answers: [
      { code: 'area', label: 'An area' },
      { code: 'same_ground', label: 'Another name, same ground' },
      { code: 'inside', label: 'A smaller place inside' },
      { code: 'wide', label: 'A wider name' },
      { code: 'drop', label: 'Not a name to keep' },
    ],
    flags: { one_publisher: 'one publisher', two_centres: 'two town centres' },
  },
  borders: {
    id: 'borders',
    title: 'Borders',
    text: 'Is this boundary right?',
    rule: RULE,
    view: 'map',
    adds: 'move',
    after: ['names'],
    public: true,
    answers: [
      { code: 'right', label: 'Right' },
      { code: 'wrong', label: 'Wrong' },
      { code: 'unknown', label: 'I do not know this ground' },
    ],
    moved: { text: 'With your moves, is it right now?', answers: { right: 'Right now', wrong: 'Still wrong' } },
    flags: { margin_under_10: 'a close call at the border' },
  },
  sentences: {
    id: 'sentences',
    title: 'Sentences',
    text: 'Is this sentence fit to quote about the place?',
    rule: '',
    view: 'text',
    adds: null,
    public: false,
    answers: [
      { code: 'fit', label: 'Fit to quote' },
      { code: 'residents', label: 'Describes who lives there' },
      { code: 'safety', label: 'Is about safety or crime' },
      { code: 'praise', label: 'Praises or runs down' },
      { code: 'person', label: 'Is about a living person' },
      { code: 'change_or_price', label: 'Is about change or price' },
      { code: 'not_a_place', label: 'Is not about the place' },
    ],
    flags: {},
  },
  kinds: {
    id: 'kinds',
    title: 'Kinds of venue',
    text: 'Is this a {kind}?',
    rule: '',
    view: 'text',
    adds: null,
    public: true,
    answers: [
      { code: 'yes', label: 'Yes' },
      { code: 'no', label: 'No' },
      { code: 'cannot_tell', label: 'Cannot tell' },
    ],
    flags: {},
  },
  ratings: {
    id: 'ratings',
    title: 'Ratings',
    text: '{rubric}',
    rule: '',
    view: 'map',
    adds: null,
    public: false,
    answers: [
      { code: '1', label: '1, least' },
      { code: '2', label: '2' },
      { code: '3', label: '3' },
      { code: '4', label: '4' },
      { code: '5', label: '5, most' },
      { code: 'cannot_say', label: 'Cannot say' },
    ],
    covers: { by: 'area_id', code: 'cannot_say', label: 'I do not know this area' },
    flags: {},
  },
};

function mapOf(focus) {
  return { bbox: [0, 0, 0.02, 0.02], focus, layers: ['cells', 'areas', 'roads', 'names', 'seeds'] };
}

function item(fields) {
  return {
    rev: `${fields.id.replace(/[^0-9a-f]/g, '')}000000000000`.slice(0, 12),
    group: 'quillhaven',
    lines: [],
    text: null,
    map: null,
    picks: null,
    flags: [],
    fill: {},
    preset: {},
    ...fields,
  };
}

export const ITEMS = {
  names: [
    item({
      id: 'n:syn-n0004',
      title: 'Dulcimer Green, Quillhaven',
      lines: [
        { label: 'As written', value: 'Dulcimer Green', source_id: 'synthetic' },
        { label: 'Tier proposed', value: 'area', source_id: 'synthetic' },
      ],
      map: mapOf('syn-n0004'),
      picks: ['Dulcimer Green', 'Dulcimer'],
      flags: ['one_publisher'],
      preset: { of: [], proposed: 'area' },
    }),
    item({
      id: 'a:syn-n0004:dulcimer',
      title: 'Dulcimer, Quillhaven',
      map: mapOf('syn-n0004'),
      picks: ['Dulcimer'],
      preset: { of: ['syn-n0004'], proposed: 'inside' },
    }),
    item({ id: 'n:syn-n0007', title: 'Alderwick, Quillhaven', map: mapOf('syn-n0007'), picks: ['Alderwick'], preset: { of: [], proposed: 'area' } }),
    item({ id: 'n:syn-n0012', title: 'Thrushcombe, Marrowmere', group: 'marrowmere', map: mapOf('syn-n0012'), picks: ['Thrushcombe'], preset: { of: [], proposed: 'area' } }),
  ],
  borders: [
    item({ id: 'syn-n0007', title: 'Alderwick, Quillhaven', map: { ...mapOf('syn-n0007'), layers: ['cells', 'areas', 'wards', 'roads'] }, flags: ['margin_under_10'] }),
    item({ id: 'syn-n0012', title: 'Thrushcombe, Quillhaven', map: mapOf('syn-n0012') }),
  ],
  sentences: [
    item({
      id: 'syn-page-3:17',
      group: 'syn-page-3',
      title: 'Alderwick, in the made-up encyclopaedia',
      lines: [{ label: 'Heading', value: 'Places and buildings', source_id: 'synthetic' }],
      text: {
        before: 'The mill closed long ago.',
        body: 'Alderwick has a clock tower on its green.',
        after: 'A market is held beside it.',
      },
      preset: { page_id: 3, revision_id: 1, sentence: 17 },
    }),
    item({
      id: 'syn-page-3:18',
      group: 'syn-page-3',
      title: 'Alderwick, in the made-up encyclopaedia',
      text: { before: 'Alderwick has a clock tower on its green.', body: 'A market is held beside it.', after: '' },
      preset: { page_id: 3, revision_id: 1, sentence: 18 },
    }),
  ],
  kinds: [
    item({
      id: 'syn-p0037',
      group: 'landmark',
      title: 'The Alderwick Clock',
      lines: [
        { label: 'Name', value: 'The Alderwick Clock', source_id: 'synthetic' },
        { label: 'Category as written', value: 'monument', source_id: 'synthetic' },
        { label: 'Given by', value: 'synthetic', source_id: 'synthetic' },
      ],
      fill: { kind: 'landmark' },
      preset: { kind: 'landmark', source_id: 'synthetic' },
    }),
  ],
  ratings: [
    item({
      id: 'syn-n0004:leafy',
      title: 'Dulcimer Green, Quillhaven',
      map: mapOf('syn-n0004'),
      fill: { rubric: 'How much of the street is under trees, or beside grass?' },
      preset: { area_id: 'syn-n0004', vibe: 'leafy' },
    }),
  ],
};

// A queue of ratings as the desk fills one: every area on every vibe, area by area.
export function ratingsOf(areas, vibes) {
  return areas.flatMap((area) =>
    vibes.map((vibe) =>
      item({
        id: `${area}:${vibe}`,
        title: `Made-up area ${area}`,
        map: mapOf(area),
        fill: { rubric: `How ${vibe} is it? 1 is not at all. 5 is very.` },
        preset: { area_id: area, vibe },
      }),
    ),
  );
}

function median(numbers) {
  if (numbers.length === 0) return null;
  const sorted = [...numbers].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 === 1 ? sorted[middle] : Math.round((sorted[middle - 1] + sorted[middle]) / 2);
}

const FIELDS = ['queue', 'item', 'rev', 'part', 'answer', 'note', 'second', 'settles', 'detail', 'seconds', 'stands'];

// A desk that holds the made-up city, and answers as the server would.
export function standIn(options = {}) {
  const desk = {
    synthetic: options.synthetic !== false,
    reviewer: options.reviewer || 'r1',
    token: options.token || 'token-1',
    port: 8765,
    questions: structuredClone(options.questions || QUESTIONS),
    items: structuredClone(options.items || ITEMS),
    lines: {}, // by queue: this reviewer's lines, in the order written
    others: structuredClone(options.others || {}), // by queue, then item: what another reviewer answered
    resume: options.resume === undefined ? null : options.resume,
    broken: options.broken || 0,
    down: false, // true: no request is answered
    fail: 0, // how many requests to answer with a fault of the server's own
    asked: [], // every request made, as "METHOD path"
    layers: structuredClone(options.layers || {}),
  };

  function linesOf(queue) {
    if (!desk.lines[queue]) desk.lines[queue] = [];
    return desk.lines[queue];
  }

  function stands(queue, id, part) {
    const lines = linesOf(queue);
    const undone = new Set(lines.filter((line) => line.answer === 'undo').map((line) => line.undoes));
    const mine = lines.filter(
      (line) => line.item === id && line.part === part && line.answer !== 'undo' && !undone.has(line.n),
    );
    return mine.length > 0 ? mine[mine.length - 1] : null;
  }

  function movesOf(queue, id) {
    const lines = linesOf(queue);
    const undone = new Set(lines.filter((line) => line.answer === 'undo').map((line) => line.undoes));
    const last = new Map();
    for (const line of lines) {
      if (line.item === id && line.answer === 'move' && !undone.has(line.n)) last.set(line.part, line);
    }
    return [...last.values()];
  }

  function partOf(queue, entry) {
    const covers = desk.questions[queue].covers;
    return covers ? { part: entry.preset[covers.by] ?? null } : {};
  }

  function othersOf(queue, id) {
    return (desk.others[queue] && desk.others[queue][id]) || [];
  }

  function stateOf(queue, entry) {
    const mine = stands(queue, entry.id, '');
    if (mine === null) return 'open';
    if (mine.rev !== entry.rev) return 'stale';
    if (mine.answer === 'skip') return 'skipped';
    const settled = mine.settles === true;
    if (!settled && othersOf(queue, entry.id).some((other) => other.answer !== mine.answer)) return 'disputed';
    return 'done';
  }

  // How many answers that stand a build will set aside until the draft is made again.
  function setAsideOf(queue) {
    const held = desk.questions[queue].set_aside;
    if (!held || !Array.isArray(held.answers)) return 0;
    return desk.items[queue].filter((entry) => {
      const mine = stands(queue, entry.id, '');
      return stateOf(queue, entry) === 'done' && Boolean(entry.preset.holds) && held.answers.includes(mine.answer);
    }).length;
  }

  // The rule that settled an item, as the line that stands for it says, or nothing.
  function byRule(queue, entry) {
    const mine = stands(queue, entry.id, '');
    return queue !== 'rules' && mine !== null && mine.detail && typeof mine.detail.rule === 'string' ? mine.detail.rule : '';
  }

  // Whether the founder's yes to a rule stands, by the code of the rule.
  function adoptedRule(code) {
    const rule = (desk.items.rules || []).find((one) => one.id === code);
    const mine = rule ? stands('rules', rule.id, '') : null;
    return Boolean(rule) && mine !== null && mine.answer === 'yes' && mine.rev === rule.rev;
  }

  // Bring every queue to what the rules say that were adopted, as the desk does: a yes
  // writes a line for each item the rule fits that has no answer, and names the rule.
  // A rule that leans on another settles an item only where the rule the item leans
  // on is adopted too.
  function settle() {
    const found = { settled: 0, taken_back: 0 };
    let heldBack = 0;
    for (const rule of desk.items.rules || []) {
      const queue = rule.preset.queue;
      for (const entry of desk.items[queue] || []) {
        if (entry.preset.fits !== rule.id) continue;
        const held = stands(queue, entry.id, '');
        const ruled = byRule(queue, entry) === rule.id;
        const leant = typeof entry.preset.leans_on !== 'string' || adoptedRule(entry.preset.leans_on);
        const adopted = adoptedRule(rule.id);
        if (adopted && leant && (held === null || held.answer === 'skip')) {
          const gives = rule.preset.gives === 'proposed' ? entry.preset.proposed : rule.preset.gives === '' ? 'rule' : rule.preset.gives;
          write(queue, { item: entry.id, rev: entry.rev, answer: gives, detail: { ...entry.preset, rule: rule.id } });
          found.settled += 1;
        } else if (!(adopted && leant) && ruled) {
          write(queue, { item: entry.id, rev: entry.rev, answer: 'undo', undoes: held.n });
          found.taken_back += 1;
        }
        if (adopted && !leant && (held === null || held.answer === 'skip' || ruled)) heldBack += 1;
      }
    }
    return heldBack > 0 ? { ...found, held_back: heldBack } : found;
  }

  // For a rule that leans on others: each rule it leans on, how it stands, and how many
  // of the leaning rule's items lean on it.
  function leansOf(rule) {
    const others = Array.isArray(rule.preset.leans_on) ? rule.preset.leans_on : [];
    return others.map((other) => ({
      rule: other,
      stands: adoptedRule(other) ? 'adopted' : 'not_adopted',
      items: (desk.items[rule.preset.queue] || []).filter((entry) => entry.preset.fits === rule.id && entry.preset.leans_on === other).length,
    }));
  }

  function countsOf(queue) {
    const states = desk.items[queue].map((entry) => stateOf(queue, entry));
    const count = (state) => states.filter((s) => s === state).length;
    const flagged = desk.items[queue].filter((entry) => entry.flags.length > 0);
    const answers = linesOf(queue).filter((line) => line.part === '' && line.answer !== 'undo');
    return {
      queue,
      title: desk.questions[queue].title,
      total: states.length,
      done: count('done'),
      skipped: count('skipped'),
      stale: count('stale'),
      disputed: count('disputed'),
      by_rule: desk.items[queue].filter((entry) => stateOf(queue, entry) === 'done' && byRule(queue, entry) !== '').length,
      flagged: flagged.length,
      flagged_left: flagged.filter((entry) => stateOf(queue, entry) !== 'done').length,
      median_seconds: median(answers.slice(-50).map((line) => line.seconds)),
      set_aside: setAsideOf(queue),
      waits: waitsOf(queue),
    };
  }

  // What a queue waits on: each queue it is made from that is not yet finished.
  function waitsOf(queue) {
    const after = desk.questions[queue].after || [];
    return after
      .filter((name) => desk.items[name])
      .map((name) => ({ queue: name, title: desk.questions[name].title, left: desk.items[name].filter((entry) => stateOf(name, entry) !== 'done').length, ...(setAsideOf(name) > 0 ? { set_aside: setAsideOf(name) } : {}) }))
      .filter((row) => row.left > 0 || row.set_aside > 0);
  }

  // What is answered is a copy, as it is over a wire: the page never holds the desk's own.
  function answer(status, body) {
    return { status, body: structuredClone({ ...body, synthetic: desk.synthetic }) };
  }

  function refuse(status, error) {
    return answer(status, { error, message: `The desk says: ${error}.` });
  }

  function get(path) {
    if (path === '/api/state') {
      return answer(200, {
        desk: 1,
        reviewer: desk.reviewer,
        token: desk.token,
        banner: desk.synthetic ? 'MADE-UP CITY. Nothing here is a real place.' : 'REAL DATA FOR LONDON. A draft that nobody has checked. What you decide here is built.',
        resume: desk.resume,
        broken_lines: desk.broken,
        queues: Object.keys(desk.items).map(countsOf),
      });
    }
    const parts = path.split('/').map(decodeURIComponent);
    if (parts[2] === 'queue' && desk.items[parts[3]]) {
      const queue = parts[3];
      return answer(200, {
        question: desk.questions[queue],
        items: desk.items[queue].map((entry) => ({ id: entry.id, group: entry.group, state: stateOf(queue, entry), flagged: entry.flags.length > 0, ...partOf(queue, entry) })),
      });
    }
    if (parts[2] === 'item' && desk.items[parts[3]]) {
      const queue = parts[3];
      const entry = desk.items[queue].find((one) => one.id === parts[4]);
      if (!entry) return refuse(404, 'not_found');
      const mine = stands(queue, entry.id, '');
      return answer(200, {
        item: entry,
        state: stateOf(queue, entry),
        ...(queue === 'rules' ? { leans: leansOf(entry) } : {}),
        mine,
        moves: movesOf(queue, entry.id),
        others: mine === null ? [] : othersOf(queue, entry.id),
      });
    }
    if (parts[2] === 'layer') {
      const layer = desk.layers[`${parts[3]}/${parts[4]}`];
      return layer ? { status: 200, body: structuredClone(layer) } : refuse(404, 'not_found');
    }
    return refuse(404, 'not_found');
  }

  function write(queue, fields) {
    const lines = linesOf(queue);
    const line = {
      n: lines.length + 1,
      at: '2026-10-06T21:14:09Z',
      reviewer: desk.reviewer,
      queue,
      question: `${queue}@1`,
      item: '',
      rev: '',
      part: '',
      answer: '',
      note: '',
      second: false,
      settles: false,
      undoes: null,
      detail: {},
      seconds: 0,
      synthetic: desk.synthetic,
      ...fields,
    };
    lines.push(line);
    return line;
  }

  function post(path, headers, body) {
    if (headers['Content-Type'] !== 'application/json') return refuse(403, 'forbidden');
    if (headers['X-Desk-Token'] !== desk.token) return refuse(403, 'forbidden');
    if (typeof body !== 'object' || body === null) return refuse(400, 'bad_request');
    if (JSON.stringify(body).length > 16 * 1024) return refuse(413, 'too_large');
    const queue = body.queue;
    if (!desk.items[queue]) return refuse(404, 'not_found');
    if (path === '/api/undo') {
      if (Object.keys(body).some((key) => key !== 'queue')) return refuse(400, 'bad_request');
      const lines = linesOf(queue);
      const undone = new Set(lines.filter((line) => line.answer === 'undo').map((line) => line.undoes));
      const last = [...lines].reverse().find((line) => line.answer !== 'undo' && !undone.has(line.n));
      if (!last) return answer(200, { undone: null, counts: countsOf(queue) });
      write(queue, { item: last.item, rev: last.rev, part: last.part, answer: 'undo', undoes: last.n });
      const ruled = queue === 'rules' ? { ruled: settle() } : {};
      return answer(200, { undone: last, counts: countsOf(queue), ...ruled });
    }
    if (path !== '/api/decide') return refuse(404, 'not_found');
    if (Object.keys(body).some((key) => !FIELDS.includes(key))) return refuse(400, 'bad_request');
    if (FIELDS.some((key) => !(key in body))) return refuse(400, 'bad_request');
    const entry = desk.items[queue].find((one) => one.id === body.item);
    if (!entry) return refuse(404, 'not_found');
    if (body.rev !== entry.rev) return refuse(409, 'stale_item');
    const codes = [...desk.questions[queue].answers.map((one) => one.code), 'skip', 'move'];
    if (!codes.includes(body.answer)) return refuse(400, 'bad_request');
    if (typeof body.note !== 'string' || body.note.length > 500) return refuse(400, 'bad_request');
    if (body.settles && desk.reviewer !== 'r1') return refuse(400, 'bad_request');
    if (queue === 'names' && body.answer === 'area' && entry.id.startsWith('a:')) return refuse(400, 'bad_request');
    if (body.settles && stateOf(queue, entry) !== 'disputed') {
      return answer(400, { error: 'bad_request', message: 'There is no dispute on this item to settle.' });
    }
    const open = () => desk.items[queue].find((one) => stateOf(queue, one) === 'open');
    const standing = stands(queue, entry.id, body.part);
    const same =
      standing !== null &&
      ['rev', 'answer', 'note', 'second', 'settles'].every((key) => standing[key] === body[key]) &&
      JSON.stringify(standing.detail) === JSON.stringify(body.detail);
    if (same) return answer(200, { line: standing, next: open() ? open().id : null, counts: countsOf(queue) });
    if ((standing === null ? null : standing.n) !== body.stands) {
      return answer(409, { error: 'already_answered', message: 'This item has an answer already. It is shown again.' });
    }
    const { stands: believed, ...fields } = body;
    const line = write(queue, fields);
    const ruled = queue === 'rules' ? { ruled: settle() } : {};
    return answer(200, { line, next: open() ? open().id : null, counts: countsOf(queue), ...ruled });
  }

  // One request, answered at once. `headers` and `body` are as the page sent them.
  desk.ask = (method, path, headers = {}, body = undefined) => {
    desk.asked.push(`${method} ${path}`);
    if (desk.down) return null;
    if (desk.fail > 0) {
      desk.fail -= 1;
      return { status: 500, body: null };
    }
    return method === 'GET' ? get(path) : post(path, headers, body);
  };

  // The same, in the shape of the browser's `fetch`.
  desk.fetch = async (path, init = {}) => {
    const method = init.method || 'GET';
    const body = init.body === undefined ? undefined : JSON.parse(init.body);
    const out = desk.ask(method, path, init.headers || {}, body);
    if (out === null) throw new TypeError('Failed to fetch');
    return {
      ok: out.status >= 200 && out.status < 300,
      status: out.status,
      json: async () => {
        if (out.body === null) throw new SyntaxError('no body');
        return structuredClone(out.body);
      },
    };
  };

  // Start the desk again: it answers, and holds a new token.
  desk.again = (token = 'token-2') => {
    desk.down = false;
    desk.token = token;
  };

  // Change what an item shows, as a new fill does.
  desk.change = (queue, id, fields) => {
    const entry = desk.items[queue].find((one) => one.id === id);
    Object.assign(entry, fields, { rev: `${entry.rev.slice(0, 11)}${entry.rev.endsWith('f') ? 'e' : 'f'}` });
  };

  desk.answersOf = (queue) => linesOf(queue).filter((line) => line.answer !== 'undo');
  return desk;
}

// One sitting at the page, without a screen: what happened goes in, what the
// page decided is carried out against the stand-in, and the state comes back.
export function sitting(desk, options = {}) {
  const sit = {
    state: start(),
    at: options.at === undefined ? 100000 : options.at,
    waits: [],
    maps: [],
    focus: [],
    hold: null, // when a key that is held a moment is let go
    heard: [], // what the page said, each time it said something else
    slow: false, // true: what is written waits on its way until `arrive`
    onTheWay: [],
  };

  function carry(effect) {
    const path = pathOf(effect);
    if (effect.do === 'get') {
      const out = desk.ask('GET', path);
      const base = { type: 'got', what: effect.what, queue: effect.queue, item: effect.item, quiet: effect.quiet === true };
      if (out === null) return { ...base, ok: false, status: 0, data: null };
      return { ...base, ok: out.status === 200, status: out.status, data: out.body };
    }
    const headers = { 'Content-Type': 'application/json', 'X-Desk-Token': sit.state.token };
    const out = desk.ask('POST', path, headers, structuredClone(effect.body));
    const base = { type: 'wrote', what: effect.what };
    if (out === null) return { ...base, ok: false, status: 0, data: null };
    return { ...base, ok: out.status === 200, status: out.status, data: out.body };
  }

  sit.send = (event) => {
    const events = [event];
    let turns = 0;
    while (events.length > 0) {
      // The page must never ask without end.
      turns += 1;
      if (turns > 500) throw new Error(`the page asks without end: ${JSON.stringify(events[0]).slice(0, 200)}`);
      const out = step(sit.state, { ...events.shift(), at: sit.at });
      sit.state = out.state;
      if (sit.heard[sit.heard.length - 1] !== sit.state.said) sit.heard.push(sit.state.said);
      for (const effect of out.effects) {
        if (effect.do === 'post' && sit.slow) sit.onTheWay.push(effect);
        else if (effect.do === 'get' || effect.do === 'post') events.push(carry(effect));
        else if (effect.do === 'wait') sit.waits.push(effect.ms);
        else if (effect.do === 'map') sit.maps.push(effect.op);
        else if (effect.do === 'focus') sit.focus.push(effect.on);
        else if (effect.do === 'hold') sit.hold = sit.at + effect.ms;
      }
    }
    return sit;
  };

  sit.open = () => sit.send({ type: 'open' });
  // Time passes. A key that was held is let go when its moment is over.
  sit.pass = (ms) => {
    const to = sit.at + ms;
    if (sit.hold !== null && sit.hold <= to) {
      sit.at = sit.hold;
      sit.hold = null;
      sit.send({ type: 'release' });
    }
    sit.at = to;
    return sit;
  };
  // Strike a key, after a moment long enough to have read the item, and wait
  // until the page has acted on it.
  sit.key = (key, more = {}) => {
    sit.pass(more.soon ? 0 : 1000).send({ type: 'key', key, ...more });
    return sit.hold === null ? sit : sit.pass(sit.hold - sit.at);
  };
  // Strike the keys of some words one after another, as a person types.
  sit.strike = (words, gap = 120) => {
    for (const key of words) sit.pass(gap).send({ type: 'key', key });
    return sit;
  };
  // What was written arrives at the desk, and its answer comes back.
  sit.arrive = () => {
    const effects = sit.onTheWay.splice(0);
    const slow = sit.slow;
    sit.slow = false;
    for (const effect of effects) sit.send(carry(effect));
    sit.slow = slow;
    return sit;
  };
  sit.type = (text) => sit.send({ type: 'typed', text });
  // The wait is over.
  sit.retry = () => {
    sit.waits.shift();
    return sit.pass(1000).send({ type: 'retry' });
  };
  sit.choose = (queue) => {
    sit.key('q');
    const at = sit.state.queues.findIndex((row) => row.queue === queue);
    return sit.send({ type: 'choose', index: at });
  };
  Object.defineProperty(sit, 'view', { get: () => view(sit.state) });
  Object.defineProperty(sit, 'item', { get: () => (sit.state.now ? sit.state.now.id : null) });
  return sit;
}
