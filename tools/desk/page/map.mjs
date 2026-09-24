// What is drawn behind a border, and how. Plain functions.
//
// The desk draws its own map on a canvas, from layers the desk's own server
// holds. It uses no map library and no basemap, and asks no other host for
// anything. docs/design/desk.md, section 6, says what may be drawn. A border
// must never be moved to match a label on somebody else's map, so nobody
// else's map is ever on the screen.

// The layers the page may ask for and draw. A layer of any other name is
// never asked for, whatever an item says.
export const MAY_DRAW = ['cells', 'areas', 'boroughs', 'wards', 'centres', 'roads', 'names', 'seeds', 'records'];

// The order they are drawn in, the first at the bottom. What is not in this
// list is not drawn, whoever hands it over.
const ORDER = ['cells', 'roads', 'wards', 'centres', 'boroughs', 'areas', 'records', 'seeds', 'names'];

// A tripwire, not the gate. The gate is the licence registry, which the step
// that fills the queues asks before it copies a layer. These are words in the
// ids of sources that may never stand behind a border: maps that are
// share-alike or banned, imagery, and anything about who lives somewhere.
const NEVER = /openstreetmap|(^|-)osm(-|$)|protomaps|overture|whosonfirst|google|mapillary|geograph|census|resident|loac|(^|-)iod(-|$)|deprivation|crime|price|(^|-)rents?(-|$)|rental/;

const MOST_ZOOM = 64;
const LEAST_ZOOM = 1 / 8;

// ---------------------------------------------------------------- which layers

export function layersFor(item) {
  const map = item && item.map;
  if (!map || !Array.isArray(map.layers)) return [];
  const seen = new Set();
  const out = [];
  for (const entry of map.layers) {
    let group;
    let layer;
    if (typeof entry === 'string') {
      const parts = entry.split('/');
      if (parts.length === 2) [group, layer] = parts;
      else layer = entry;
    } else if (entry && typeof entry === 'object') {
      group = entry.group;
      layer = entry.layer;
    }
    if (!MAY_DRAW.includes(layer)) continue;
    if (typeof group !== 'string' || group === '') group = layer === 'boroughs' ? 'all' : item.group;
    if (typeof group !== 'string' || group === '') continue;
    const key = `${group}/${layer}`;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push({ group, layer, key });
  }
  return out;
}

// Whether a file the desk sent may be drawn as the layer that was asked for.
// It says why not, in words for the person.
export function accept(file, want, synthetic) {
  const no = (why) => ({ ok: false, why: `${want.layer} is not drawn: ${why}.` });
  if (!file || file.type !== 'FeatureCollection' || !Array.isArray(file.features)) return no('the file is not a layer');
  const desk = file.desk;
  if (!desk || typeof desk !== 'object') return no('the file does not say what it is');
  if (desk.layer !== want.layer || desk.group !== want.group) return no('the file is another layer');
  if (!MAY_DRAW.includes(desk.layer)) return no('the page may not draw it');
  if (desk.synthetic !== synthetic) return no(synthetic ? 'it is real and the desk is on the made-up city' : 'it is made up and the desk is on real data');
  if (!Array.isArray(desk.source_ids) || desk.source_ids.length === 0) return no('it names no source');
  for (const id of desk.source_ids) {
    if (typeof id !== 'string' || id === '') return no('it names no source');
    if (NEVER.test(id)) return no(`its source, ${id}, may not stand behind a border`);
  }
  if (desk.layer === 'records') {
    // Each record names a source of its own, and its name is drawn as written.
    // So each is held to what the layer names, and to the same tripwire.
    for (const feature of file.features) {
      const id = feature && feature.properties ? feature.properties.source_id : null;
      if (typeof id !== 'string' || id === '') return no('a record does not say which source it is of');
      if (NEVER.test(id)) return no(`the source of a record, ${id}, may not stand behind a border`);
      if (!desk.source_ids.includes(id)) return no('a record is of a source the layer does not name');
    }
  }
  return { ok: true, why: '' };
}

// The sources a layer's features are from. A layer of records says it of each
// record, so a source that no record is of is not credited.
function sourcesOf(layer) {
  if (layer.desk.layer !== 'records') return layer.desk.source_ids;
  return layer.features.map((feature) => (feature.properties ? feature.properties.source_id : null)).filter((id) => typeof id === 'string' && id !== '');
}

// The sources of what is on the map, each once, for the line under it.
export function credit(layers) {
  const ids = new Set();
  for (const layer of Object.values(layers)) for (const id of sourcesOf(layer)) ids.add(id);
  if (ids.size === 0) return '';
  return `Drawn from: ${[...ids].sort().join(', ')}. No other map is behind it.`;
}

// ---------------------------------------------------------------- shapes

function polygonsOf(geometry) {
  if (!geometry) return [];
  if (geometry.type === 'Polygon') return [geometry.coordinates];
  if (geometry.type === 'MultiPolygon') return geometry.coordinates;
  return [];
}

function linesOf(geometry) {
  if (!geometry) return [];
  if (geometry.type === 'LineString') return [geometry.coordinates];
  if (geometry.type === 'MultiLineString') return geometry.coordinates;
  return [];
}

function pointsOf(geometry) {
  if (!geometry) return [];
  if (geometry.type === 'Point') return [geometry.coordinates];
  if (geometry.type === 'MultiPoint') return geometry.coordinates;
  return [];
}

function eachPoint(geometry, fn) {
  for (const point of pointsOf(geometry)) fn(point);
  for (const line of linesOf(geometry)) for (const point of line) fn(point);
  for (const polygon of polygonsOf(geometry)) for (const ring of polygon) for (const point of ring) fn(point);
}

const boxes = new WeakMap();

// The box round a feature: west, south, east, north. Worked out once.
export function boxOf(feature) {
  const held = boxes.get(feature);
  if (held) return held;
  const box = [Infinity, Infinity, -Infinity, -Infinity];
  eachPoint(feature.geometry, ([lon, lat]) => {
    if (lon < box[0]) box[0] = lon;
    if (lat < box[1]) box[1] = lat;
    if (lon > box[2]) box[2] = lon;
    if (lat > box[3]) box[3] = lat;
  });
  boxes.set(feature, box);
  return box;
}

function meets(a, b) {
  return a[0] <= b[2] && a[2] >= b[0] && a[1] <= b[3] && a[3] >= b[1];
}

function inRing(ring, lon, lat) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i, i += 1) {
    const [xi, yi] = ring[i];
    const [xj, yj] = ring[j];
    if (yi > lat !== yj > lat && lon < ((xj - xi) * (lat - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

function inPolygon(polygon, lon, lat) {
  if (polygon.length === 0 || !inRing(polygon[0], lon, lat)) return false;
  for (let i = 1; i < polygon.length; i += 1) if (inRing(polygon[i], lon, lat)) return false;
  return true;
}

// The cell a point of the ground is in, or null.
export function cellAt(cells, [lon, lat]) {
  if (!cells || !Array.isArray(cells.features)) return null;
  for (const feature of cells.features) {
    const box = boxOf(feature);
    if (lon < box[0] || lon > box[2] || lat < box[1] || lat > box[3]) continue;
    if (polygonsOf(feature.geometry).some((polygon) => inPolygon(polygon, lon, lat))) return feature;
  }
  return null;
}

// The area of every cell once the moves that stand are made, in the order written.
export function areasAfter(cells, moves) {
  const areas = new Map();
  if (cells && Array.isArray(cells.features)) {
    for (const feature of cells.features) areas.set(feature.id, feature.properties ? feature.properties.area : undefined);
  }
  const ordered = [...(Array.isArray(moves) ? moves : [])].sort((a, b) => (a.n || 0) - (b.n || 0));
  for (const move of ordered) {
    if (move && areas.has(move.part) && move.detail && typeof move.detail.to === 'string') areas.set(move.part, move.detail.to);
  }
  return areas;
}

// The areas that lost or gained a cell by the moves that stand. A cell moved
// there and back again changed nothing.
export function changedAreas(cells, areas) {
  const changed = new Set();
  if (cells && Array.isArray(cells.features)) {
    for (const feature of cells.features) {
      const was = feature.properties ? feature.properties.area : undefined;
      const now = areas.get(feature.id);
      if (now === was) continue;
      if (typeof was === 'string') changed.add(was);
      if (typeof now === 'string') changed.add(now);
    }
  }
  return changed;
}

// The border of an area as its cells now lie: every edge that one cell of the
// area has and no other cell of it shares. Each is a length of two points of the
// ground. Two cells share an edge only where both give the same two points,
// which is so of cells cut from one file.
export function outlineOf(cells, areas, id) {
  const edges = new Map();
  const take = (a, b) => {
    const from = `${a[0]},${a[1]}`;
    const to = `${b[0]},${b[1]}`;
    if (from === to) return;
    const key = from < to ? `${from}|${to}` : `${to}|${from}`;
    const held = edges.get(key);
    if (held) held.times += 1;
    else edges.set(key, { times: 1, a, b });
  };
  if (cells && Array.isArray(cells.features)) {
    for (const feature of cells.features) {
      if (areas.get(feature.id) !== id) continue;
      for (const polygon of polygonsOf(feature.geometry)) {
        for (const ring of polygon) {
          for (let i = 0; i + 1 < ring.length; i += 1) take(ring[i], ring[i + 1]);
          if (ring.length > 2) take(ring[ring.length - 1], ring[0]);
        }
      }
    }
  }
  return [...edges.values()].filter((edge) => edge.times === 1).map((edge) => [edge.a, edge.b]);
}

// The colour each area is drawn in, as the layer gives it.
export function coloursOf(cells) {
  const colours = new Map();
  if (cells && Array.isArray(cells.features)) {
    for (const feature of cells.features) {
      const props = feature.properties || {};
      if (typeof props.area === 'string' && Number.isInteger(props.colour) && !colours.has(props.area)) {
        colours.set(props.area, ((props.colour % 12) + 12) % 12);
      }
    }
  }
  return colours;
}

// An area's name, where a layer on the map gives it. Else its id.
export function nameOf(layers, id) {
  const areas = layers.areas;
  if (areas) {
    const found = areas.features.find((feature) => feature.id === id);
    if (found && found.properties && typeof found.properties.name === 'string') return found.properties.name;
  }
  const seeds = layers.seeds;
  if (seeds) {
    const found = seeds.features.find((feature) => feature.properties && feature.properties.area === id);
    if (found && typeof found.properties.name === 'string') return found.properties.name;
  }
  return id;
}

// A name in lower case with hyphens: how the desk names the group of a borough.
export function slug(name) {
  return String(name).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
}

// Which cells are the item's own, as a test of a cell and its area. An item is
// about an area, or about a whole borough, or about nothing in particular.
// Every other cell is drawn fainter: it is there to show what lies beside.
export function ownCells(item, areas) {
  const focus = focusOf(item);
  const held = new Set(areas.values());
  if ([...focus.ids].some((id) => held.has(id))) return (feature, area) => focus.ids.has(area);
  const group = item && typeof item.group === 'string' ? item.group : '';
  if (group === '' || group === 'all') return () => true;
  return (feature) => {
    const borough = feature.properties ? feature.properties.borough : undefined;
    return typeof borough !== 'string' || slug(borough) === group;
  };
}

// The name that is asked about: the first spelling the item offers.
function askedOf(item) {
  const first = item && Array.isArray(item.picks) ? item.picks[0] : '';
  return typeof first === 'string' ? first : '';
}

// What the item is about, as a set of ids and perhaps a point.
export function focusOf(item) {
  const focus = item && item.map ? item.map.focus : null;
  const ids = new Set();
  let point = null;
  const take = (value) => {
    if (typeof value === 'string' && value !== '') ids.add(value);
  };
  if (Array.isArray(focus)) {
    if (focus.length === 2 && focus.every((n) => typeof n === 'number')) point = focus;
    else focus.forEach(take);
  } else if (focus && typeof focus === 'object') {
    for (const value of Object.values(focus)) {
      if (Array.isArray(value) && value.length === 2 && value.every((n) => typeof n === 'number')) point = value;
      else if (Array.isArray(value)) value.forEach(take);
      else take(value);
    }
  } else {
    take(focus);
  }
  return { ids, point };
}

// The box to fit for an item: the one it gives, else the one round what it is
// about, else the one round every cell.
export function boxFor(item, layers) {
  const given = item && item.map ? item.map.bbox : null;
  if (Array.isArray(given) && given.length === 4 && given.every((n) => typeof n === 'number' && Number.isFinite(n)) && given[2] > given[0] && given[3] > given[1]) {
    return given;
  }
  const focus = focusOf(item);
  const round = (features) => {
    const box = [Infinity, Infinity, -Infinity, -Infinity];
    for (const feature of features) {
      const one = boxOf(feature);
      box[0] = Math.min(box[0], one[0]);
      box[1] = Math.min(box[1], one[1]);
      box[2] = Math.max(box[2], one[2]);
      box[3] = Math.max(box[3], one[3]);
    }
    return box.every(Number.isFinite) ? box : null;
  };
  const cells = layers.cells ? layers.cells.features : [];
  const own = cells.filter((feature) => feature.properties && focus.ids.has(feature.properties.area));
  return round(own) || round(cells) || null;
}

// ---------------------------------------------------------------- what a draft marks

// What each mark on a cell in doubt means, in the order the map lists them, by
// the flag the draft names. The look of a mark says what the doubt is: a ring,
// a square, a square on its point, a triangle. Each is drawn round the last,
// so that a cell under two doubts shows both.
const DOUBTS = [
  { flag: 'margin_under_10', look: 'ring', r: 10, says: 'margin under 10%' },
  { flag: 'two_boroughs', look: 'square', r: 13, says: 'outside the main borough' },
  { flag: 'seeds_close', look: 'diamond', r: 19, says: 'beside an area whose seed is close' },
  { flag: 'two_pieces', look: 'triangle', r: 24, says: 'cut off from the largest piece' },
];
const STRETCH = { flag: 'follows_nothing', says: 'a stretch that follows no line' };
const CLOSE_SEED = { flag: 'seed', says: 'the seed that stands close' };

// How close the map must be for every cell in doubt to show its code. At the
// scale an item opens at only the cell under the cross shows one.
const CODES_AT = 2;

// What the draft has the page mark on the map of an item, as plain values:
// nothing a file holds is trusted to be of the right kind.
export function marksOf(item) {
  const held = item && item.map && item.map.marks && typeof item.map.marks === 'object' ? item.map.marks : {};
  const words = (list) => (Array.isArray(list) ? list.filter((one) => typeof one === 'string' && one !== '') : []);
  const cells = new Map();
  if (held.cells && typeof held.cells === 'object') {
    for (const [cell, flags] of Object.entries(held.cells)) cells.set(cell, words(flags));
  }
  const sides = (Array.isArray(held.sides) ? held.sides : []).filter((pair) => Array.isArray(pair) && pair.length === 2 && words(pair).length === 2);
  return { cells, sides, seeds: words(held.seeds), centres: words(held.centres) };
}

// The corners of a mark round a point of the screen, for the looks that have
// corners. A ring has none.
function cornersOf(look, [x, y], r) {
  if (look === 'square') return [[x - r, y - r], [x + r, y - r], [x + r, y + r], [x - r, y + r]];
  if (look === 'diamond') return [[x, y - r], [x + r, y], [x, y + r], [x - r, y]];
  if (look === 'triangle') return [[x, y - r], [x + r * 0.87, y + r / 2], [x - r * 0.87, y + r / 2]];
  return null;
}

// One mark, as what is drawn: a ring, or an outline with corners. It is never
// filled, so that it hides nothing under it.
function markOf(doubt, at, stroke) {
  const corners = cornersOf(doubt.look, at, doubt.r);
  if (corners === null) return { op: 'ring', at, r: doubt.r, stroke, width: 3, mark: doubt.flag };
  return { op: 'shape', rings: [corners], fill: null, alpha: 1, hatch: null, stroke, width: 3, dash: null, mark: doubt.flag };
}

function edgesOf(feature) {
  const edges = new Map();
  for (const polygon of polygonsOf(feature.geometry)) {
    for (const ring of polygon) {
      for (let i = 0; i + 1 < ring.length; i += 1) {
        const a = ring[i];
        const b = ring[i + 1];
        const from = `${a[0]},${a[1]}`;
        const to = `${b[0]},${b[1]}`;
        if (from !== to) edges.set(from < to ? `${from}|${to}` : `${to}|${from}`, [a, b]);
      }
    }
  }
  return edges;
}

// The lengths that two cells share: every edge that both give with the same two
// points, which is so of cells cut from one file.
export function sharedEdges(a, b) {
  if (!a || !b) return [];
  const other = edgesOf(b);
  return [...edgesOf(a)].filter(([key]) => other.has(key)).map(([, edge]) => edge);
}

// ---------------------------------------------------------------- the view

// A flat projection about the middle of the item. `k` is pixels for a degree
// of latitude, and `squeeze` narrows a degree of longitude to match. The
// squeeze is set when the item is fitted and does not change as the map moves.
export function fit(bbox, size, pad = 24) {
  const ok = Array.isArray(bbox) && bbox.length === 4 && bbox.every((n) => typeof n === 'number' && Number.isFinite(n));
  const [west, south, east, north] = ok ? bbox : [-0.01, -0.01, 0.01, 0.01];
  const lat = (south + north) / 2;
  const squeeze = Math.max(0.01, Math.cos((lat * Math.PI) / 180));
  const wide = Math.max(1e-6, (east - west) * squeeze);
  const tall = Math.max(1e-6, north - south);
  const k = Math.min(Math.max(1, size.width - 2 * pad) / wide, Math.max(1, size.height - 2 * pad) / tall);
  return { lon: (west + east) / 2, lat, k, squeeze, fitted: k };
}

export function toScreen(view, size, [lon, lat]) {
  return [size.width / 2 + (lon - view.lon) * view.squeeze * view.k, size.height / 2 - (lat - view.lat) * view.k];
}

export function toGround(view, size, [x, y]) {
  return [view.lon + (x - size.width / 2) / (view.squeeze * view.k), view.lat - (y - size.height / 2) / view.k];
}

// Zoom about a point of the screen, which stays where it is.
export function zoomBy(view, size, factor, at = null) {
  const point = at || [size.width / 2, size.height / 2];
  const k = Math.max(view.fitted * LEAST_ZOOM, Math.min(view.fitted * MOST_ZOOM, view.k * factor));
  const [lon, lat] = toGround(view, size, point);
  const next = { ...view, k };
  const [x, y] = toScreen(next, size, [lon, lat]);
  return panBy(next, point[0] - x, point[1] - y);
}

// Move the map by so many pixels: the ground goes with the hand.
export function panBy(view, dx, dy) {
  return { ...view, lon: view.lon - dx / (view.squeeze * view.k), lat: view.lat + dy / view.k };
}

// The same view in a canvas of another size: the same middle, and as close as
// it was by the measure of what fits. `before` and `after` are the views that
// fit the item in the old canvas and in the new.
export function refit(view, before, after) {
  const close = before.k > 0 ? view.k / before.k : 1;
  return { ...view, k: after.k * close, fitted: after.k };
}

// What a key does to the view. `fitted` is the view that fits the item.
export function moveView(view, size, op, fitted, small = false) {
  // An arrow moves the map an eighth of its shorter side, which may be more
  // than a cell. With Shift it moves a quarter of that.
  const step = Math.round(Math.min(size.width, size.height) / (small ? 32 : 8));
  switch (op) {
    case 'in':
      return zoomBy(view, size, 1.5);
    case 'out':
      return zoomBy(view, size, 1 / 1.5);
    case 'fit':
      return fitted;
    case 'left':
      return panBy(view, step, 0);
    case 'right':
      return panBy(view, -step, 0);
    case 'up':
      return panBy(view, 0, step);
    case 'down':
      return panBy(view, 0, -step);
    default:
      return view;
  }
}

function groundBox(view, size) {
  const [west, north] = toGround(view, size, [0, 0]);
  const [east, south] = toGround(view, size, [size.width, size.height]);
  return [west, south, east, north];
}

// ---------------------------------------------------------------- colours

function hsl(h, s, l) {
  return `hsl(${h} ${s}% ${l}%)`;
}

// Twelve colours for areas. Neighbours in the list are far apart in hue, so
// two areas side by side are told apart by more than a shade.
export function areaColour(index, dark) {
  const i = ((index % 12) + 12) % 12;
  const hue = (i * 150) % 360;
  if (dark) return hsl(hue, 35, i % 2 === 0 ? 18 : 24);
  return hsl(hue, 55, i % 2 === 0 ? 80 : 88);
}

export function themeOf(dark) {
  return dark
    ? { dark: true, paper: '#14161a', ink: '#f2f2ee', soft: '#b9bcc4', line: '#8a8f99', road: '#5d626d', mark: '#ffd166', hand: '#ff9f6b' }
    : { dark: false, paper: '#fbfaf7', ink: '#14161a', soft: '#454a54', line: '#5b606b', road: '#9a9fa8', mark: '#8a2c0d', hand: '#b3261e' };
}

// ---------------------------------------------------------------- what to draw

function roadWidth(kind) {
  const word = String(kind || '').toLowerCase();
  if (/motorway|\ba road|trunk|primary/.test(word)) return 3;
  if (/\bb road|secondary|\bclassified/.test(word)) return 2;
  return 1;
}

function screenRings(view, size, polygon) {
  return polygon.map((ring) => ring.map((point) => toScreen(view, size, point)));
}

function middleOf(feature) {
  const box = boxOf(feature);
  return [(box[0] + box[2]) / 2, (box[1] + box[3]) / 2];
}

// How far round the cross no name is put, in pixels each way from its middle.
const ROUND_CROSS = 18;

// Labels, the most important first. One that would lie over another is left
// out, unless it is the name of an area, of a record asked about or of a cell
// that a line is about: such a name is moved down or up until it is clear, so
// that what the item is about is never without its name. `clear` is what no
// label may lie over: the cross, where there is one.
function place(labels, size, clear = []) {
  const taken = [...clear];
  const said = new Set();
  const out = [];
  for (const label of labels) {
    // A road is many short lengths, each with the road's name. It is named once.
    if (label.once && said.has(label.text)) continue;
    const wide = label.text.length * label.size * 0.58 + 8;
    const tall = label.size + 6;
    const [x, y] = label.at;
    if (x + wide / 2 < 0 || x - wide / 2 > size.width || y + tall / 2 < 0 || y - tall / 2 > size.height) continue;
    const steps = label.rank <= 1 ? [0, 1, -1, 2, -2, 3, -3] : [0];
    for (const step of steps) {
      const at = [x, y + step * (tall + 2)];
      const box = [at[0] - wide / 2, at[1] - tall / 2, at[0] + wide / 2, at[1] + tall / 2];
      if (taken.some((other) => meets(box, other))) continue;
      taken.push(box);
      said.add(label.text);
      out.push({ op: 'text', at, text: label.text, size: label.size, bold: label.bold === true });
      break;
    }
  }
  return out;
}

// Everything to draw, in order, as plain values: what `paint` puts on the
// canvas. `layers` holds only layers that `accept` let through.
export function drawList({ layers, view, size, item = null, moves = [], theirs = [], hand = null, chosen = [], cross = false, dark = false }) {
  const theme = themeOf(dark);
  const byOthers = new Set(theirs.map((move) => move.cell));
  const seen = groundBox(view, size);
  const focus = focusOf(item);
  const areas = areasAfter(layers.cells, moves);
  const changed = changedAreas(layers.cells, areas);
  const colours = coloursOf(layers.cells);
  const zoom = view.k / view.fitted;
  const own = ownCells(item, areas);
  const spellings = new Set(item && Array.isArray(item.picks) ? item.picks : []);
  // A cell that a line of the item is about is ringed, so that the line can be
  // found on the map. Where the draft says what doubt a cell is under, the look
  // of its mark says so.
  const noted = new Set((item && Array.isArray(item.lines) ? item.lines : []).map((line) => line.label));
  const drafted = marksOf(item);
  const named = new Set([...spellings, ...drafted.centres]);
  const middle = [size.width / 2, size.height / 2];
  // The cell under the cross shows its code at any scale: a person puts the
  // cross on a ring to learn which line is about it.
  const under = cross && layers.cells ? cellAt(layers.cells, toGround(view, size, middle)) : null;
  const seen_looks = new Set();
  const list = [{ op: 'clear', fill: theme.paper }];
  const labels = [];
  const marks = [];
  const outlines = [];
  const inView = (feature) => feature && feature.geometry && meets(boxOf(feature), seen);
  const isFocus = (feature) => focus.ids.has(feature.id) || (feature.properties && focus.ids.has(feature.properties.area));

  for (const name of ORDER) {
    const layer = layers[name];
    if (!layer) continue;
    const roads = { 1: [], 2: [], 3: [] };
    for (const feature of layer.features) {
      if (!inView(feature)) continue;
      const props = feature.properties || {};
      if (name === 'cells') {
        const area = areas.get(feature.id);
        const moved = area !== props.area;
        const held = hand !== null && hand.cell === feature.id;
        const mine = own(feature, area) || chosen.includes(area);
        for (const polygon of polygonsOf(feature.geometry)) {
          list.push({
            op: 'shape',
            rings: screenRings(view, size, polygon),
            fill: areaColour(colours.get(area) ?? props.colour ?? 0, dark),
            alpha: mine ? 1 : 0.45,
            stroke: held ? theme.hand : theme.line,
            width: held ? 4 : 0.5,
            dash: null,
          });
        }
        if (moved || held) list.push({ op: 'dot', at: toScreen(view, size, middleOf(feature)), r: held ? 7 : 5, fill: held ? theme.hand : theme.mark, stroke: theme.paper });
        // A cell another reviewer moved is ringed with a broken line. It stays where
        // the draft put it: only the answer that stands moves a cell in a build.
        if (byOthers.has(feature.id)) marks.push({ op: 'ring', at: toScreen(view, size, middleOf(feature)), r: 9, stroke: theme.ink, width: 2, dash: [3, 3] });
        if (noted.has(feature.id) || drafted.cells.has(feature.id)) {
          const at = toScreen(view, size, middleOf(feature));
          const doubts = DOUBTS.filter((doubt) => (drafted.cells.get(feature.id) || []).includes(doubt.flag));
          for (const doubt of doubts) {
            marks.push(markOf(doubt, at, theme.mark));
            seen_looks.add(doubt.flag);
          }
          // A cell the draft lists and says no doubt of is ringed as it always was.
          if (doubts.length === 0) marks.push({ op: 'ring', at, r: 10, stroke: theme.mark, width: 3 });
          // A code on every ring crowds an area. At the scale an item opens at
          // only the cell under the cross shows its code.
          const reach = doubts.length === 0 ? 10 : Math.max(...doubts.map((doubt) => doubt.r));
          if (zoom >= CODES_AT || (under !== null && under.id === feature.id)) {
            labels.push({ rank: 1, at: [at[0], at[1] + reach + 12], text: String(feature.id), size: 16 });
          }
        }
      } else if (name === 'roads') {
        const width = roadWidth(props.class);
        if (width === 1 && zoom < 0.6) continue;
        // Every road of one width is one stroke of the pen: a borough holds
        // thousands of roads, and the map is drawn again as it is dragged.
        for (const line of linesOf(feature.geometry)) roads[width].push(line.map((point) => toScreen(view, size, point)));
        if (typeof props.name === 'string' && props.name !== '' && zoom >= (width > 1 ? 1 : 2)) {
          labels.push({ rank: 5 - width, at: toScreen(view, size, middleOf(feature)), text: props.name, size: 16, once: true });
        }
      } else if (name === 'wards' || name === 'areas' || name === 'boroughs' || name === 'centres') {
        const strong = name !== 'wards' && name !== 'centres' && isFocus(feature);
        // An area the person chose is outlined in the colour of the hand.
        const picked = name === 'areas' && chosen.includes(feature.id);
        // An area that lost or gained a cell is no longer as drafted. Its drafted
        // outline is drawn thin and broken, so that no heavy line says the border
        // runs where it no longer does.
        const redrawn = name === 'areas' && changed.has(feature.id);
        const drafted = { stroke: theme.soft, width: 1.5, dash: [6, 4] };
        const style = picked ? { stroke: theme.hand, width: 4, dash: [10, 5] } : redrawn ? drafted : {
          wards: { stroke: theme.soft, width: 1, dash: [2, 4] },
          centres: { stroke: theme.mark, width: 1.5, dash: [6, 3] },
          boroughs: { stroke: theme.ink, width: strong ? 4 : 2.5, dash: strong ? null : [12, 4] },
          areas: { stroke: theme.ink, width: strong ? 4 : 1.5, dash: null },
        }[name];
        // With no cells under it, the outline the item is about is filled, so that it is found at a glance.
        const fill = strong && !layers.cells ? areaColour(3, dark) : null;
        for (const polygon of polygonsOf(feature.geometry)) {
          list.push({ op: 'shape', rings: screenRings(view, size, polygon), fill, alpha: 1, hatch: name === 'centres' ? theme.mark : null, ...style });
        }
        if (redrawn && strong) {
          // The border the question is about: round the cells the area now holds.
          const paths = outlineOf(layers.cells, areas, feature.id).map((edge) => edge.map((point) => toScreen(view, size, point)));
          if (paths.length > 0) outlines.push({ op: 'lines', paths, stroke: theme.ink, width: 4, dash: null, cap: 'round' });
        }
        if (name === 'boroughs' && typeof props.name === 'string') {
          labels.push({ rank: isFocus(feature) ? 0 : 3, at: toScreen(view, size, middleOf(feature)), text: props.name, size: 18, bold: isFocus(feature) });
        } else if (name === 'areas' && !layers.seeds && typeof props.name === 'string') {
          labels.push({ rank: strong ? 0 : 1, at: toScreen(view, size, middleOf(feature)), text: props.name, size: 18, bold: true });
        } else if (name === 'centres' && typeof props.name === 'string' && named.has(props.name)) {
          // The town centre whose name is asked about, and one that a flag names, is
          // named as an area is: moved clear of the cross and of every other name, and
          // never left out. Nothing else says which of the town centres that are
          // hatched is the one. It is placed after every seed, so that an area of the
          // same name is named at its seed alone.
          labels.push({ rank: 0.5, at: toScreen(view, size, middleOf(feature)), text: props.name, size: 18, bold: true, once: true });
        } else if ((name === 'wards' || name === 'centres') && typeof props.name === 'string' && zoom >= 1) {
          labels.push({ rank: name === 'centres' ? 3 : 4, at: toScreen(view, size, middleOf(feature)), text: props.name, size: 16 });
        }
      } else if (name === 'seeds' || name === 'records' || name === 'names') {
        for (const point of pointsOf(feature.geometry)) {
          const at = toScreen(view, size, point);
          if (name === 'seeds') {
            list.push({ op: 'dot', at, r: 5, fill: theme.ink, stroke: theme.paper });
            if (typeof props.name === 'string') labels.push({ rank: isFocus(feature) ? 0 : 1, at: [at[0], at[1] - 16], text: props.name, size: 18, bold: true });
            if (drafted.seeds.includes(props.area)) {
              // The seed a flag means: two rings round it, and a broken line to the
              // seed of the area the item is about.
              marks.push({ op: 'ring', at, r: 9, stroke: theme.hand, width: 2, mark: 'seed' }, { op: 'ring', at, r: 14, stroke: theme.hand, width: 2, mark: 'seed' });
              seen_looks.add(CLOSE_SEED.flag);
              const own = layer.features.find((one) => one.properties && focus.ids.has(one.properties.area) && pointsOf(one.geometry).length > 0);
              if (own) marks.push({ op: 'lines', paths: [[toScreen(view, size, pointsOf(own.geometry)[0]), at]], stroke: theme.hand, width: 2, dash: [6, 4], mark: 'seed' });
            }
          } else if (name === 'records') {
            // A record of the name that is asked about is drawn large and named.
            // Any other is small, and named only when the map is close.
            const asked = spellings.has(props.as_written);
            list.push({ op: 'square', at, r: asked ? 6 : 3, fill: theme.mark, stroke: theme.paper });
            if (typeof props.as_written === 'string' && (asked || zoom >= 2)) {
              const by = typeof props.source_id === 'string' ? ` (${props.source_id})` : '';
              labels.push({ rank: asked ? 0 : 4, at: [at[0], at[1] + 18], text: `${props.as_written}${by}`, size: 16, bold: asked });
            }
          } else if (typeof props.name === 'string') {
            // The name asked about is said once: where the ring names it, the point under the ring does not.
            labels.push({ rank: 2, at, text: props.name, size: 16, once: spellings.has(props.name) });
          }
        }
      }
    }
    for (const width of [1, 2, 3]) {
      if (roads[width].length > 0) list.push({ op: 'lines', paths: roads[width], stroke: theme.road, width, dash: null });
    }
    // The outlines as they now stand lie over every outline as drafted.
    if (name === 'areas') list.push(...outlines);
  }
  // Each stretch of the border that follows no line: the lengths the two cells of
  // a side share, in a heavy dotted line over the cells.
  if (layers.cells && drafted.sides.length > 0) {
    const byId = new Map(layers.cells.features.map((feature) => [feature.id, feature]));
    const paths = drafted.sides.flatMap(([a, b]) => sharedEdges(byId.get(a), byId.get(b))).map((edge) => edge.map((point) => toScreen(view, size, point)));
    if (paths.length > 0) {
      marks.unshift({ op: 'lines', paths, stroke: theme.mark, width: 5, dash: [2, 8], cap: 'round', mark: STRETCH.flag });
      seen_looks.add(STRETCH.flag);
    }
  }
  list.push(...marks);
  const legend = legendOf(seen_looks, theme);
  if (focus.point) {
    const at = toScreen(view, size, focus.point);
    list.push({ op: 'ring', at, r: 12, stroke: theme.hand, width: 3 });
    // Where no layer of records is drawn, nothing else says which place the ring is round.
    const asked = askedOf(item);
    if (!layers.records && asked !== '') labels.push({ rank: 0, at: [at[0], at[1] + 26], text: asked, size: 18, bold: true, once: true });
  }
  labels.sort((a, b) => a.rank - b.rank);
  const clear = cross ? [[middle[0] - ROUND_CROSS, middle[1] - ROUND_CROSS, middle[0] + ROUND_CROSS, middle[1] + ROUND_CROSS]] : [];
  // No name lies over the words that say what a mark means.
  if (legend.box !== null) clear.push(legend.box);
  list.push(...place(labels, size, clear).map((label) => ({ ...label, fill: theme.ink, halo: theme.paper })));
  list.push(...legend.list);
  if (cross) list.push({ op: 'cross', at: [size.width / 2, size.height / 2], r: 14, stroke: theme.hand, halo: theme.paper, width: 2 });
  return list;
}

// What each look on the map means, in words, in the top left corner: a row for
// each look that is on the map, and none for a look that is not. With no mark
// on the map there is nothing to say.
function legendOf(seen, theme) {
  const rows = [...DOUBTS, STRETCH, CLOSE_SEED].filter((one) => seen.has(one.flag));
  if (rows.length === 0) return { list: [], box: null };
  const tall = 28;
  const wide = 56 + Math.max(...rows.map((row) => row.says.length)) * 16 * 0.58;
  const box = [8, 8, 8 + wide, 8 + rows.length * tall + 8];
  const list = [{ op: 'shape', rings: [[[box[0], box[1]], [box[2], box[1]], [box[2], box[3]], [box[0], box[3]]]], fill: theme.paper, alpha: 0.9, hatch: null, stroke: theme.line, width: 1, dash: null, legend: true }];
  rows.forEach((row, i) => {
    const at = [28, 8 + 4 + tall / 2 + i * tall];
    if (row === STRETCH) list.push({ op: 'lines', paths: [[[14, at[1]], [42, at[1]]]], stroke: theme.mark, width: 5, dash: [2, 8], cap: 'round', legend: true });
    else if (row === CLOSE_SEED) list.push({ op: 'ring', at, r: 5, stroke: theme.hand, width: 2, legend: true }, { op: 'ring', at, r: 9, stroke: theme.hand, width: 2, legend: true });
    else list.push({ ...markOf({ ...row, r: 9 }, at, theme.mark), mark: undefined, legend: true });
    list.push({ op: 'text', at: [50, at[1]], text: row.says, size: 16, bold: false, align: 'left', fill: theme.ink, halo: theme.paper, legend: true });
  });
  return { list, box };
}

// ---------------------------------------------------------------- on the canvas

function trace(ctx, rings) {
  ctx.beginPath();
  for (const ring of rings) {
    ring.forEach(([x, y], i) => (i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)));
    ctx.closePath();
  }
}

function hatch(ctx, rings, colour) {
  let [x0, y0, x1, y1] = [Infinity, Infinity, -Infinity, -Infinity];
  for (const [x, y] of rings[0] || []) {
    x0 = Math.min(x0, x);
    y0 = Math.min(y0, y);
    x1 = Math.max(x1, x);
    y1 = Math.max(y1, y);
  }
  if (!Number.isFinite(x0)) return;
  ctx.save();
  trace(ctx, rings);
  ctx.clip('evenodd');
  ctx.beginPath();
  const tall = y1 - y0;
  for (let x = x0 - tall; x < x1; x += 9) {
    ctx.moveTo(x, y1);
    ctx.lineTo(x + tall, y0);
  }
  ctx.strokeStyle = colour;
  ctx.lineWidth = 1;
  ctx.globalAlpha = 0.5;
  ctx.setLineDash([]);
  ctx.stroke();
  ctx.restore();
}

// Put the list on a canvas. Text from a file is drawn as text and as nothing else.
export function paint(ctx, size, list) {
  for (const one of list) {
    ctx.globalAlpha = 1;
    ctx.setLineDash(one.dash || []);
    if (one.op === 'clear') {
      ctx.fillStyle = one.fill;
      ctx.fillRect(0, 0, size.width, size.height);
    } else if (one.op === 'shape') {
      if (one.fill) {
        trace(ctx, one.rings);
        ctx.globalAlpha = one.alpha;
        ctx.fillStyle = one.fill;
        ctx.fill('evenodd');
        ctx.globalAlpha = 1;
      }
      if (one.hatch) hatch(ctx, one.rings, one.hatch);
      trace(ctx, one.rings);
      ctx.setLineDash(one.dash || []);
      ctx.strokeStyle = one.stroke;
      ctx.lineWidth = one.width;
      ctx.stroke();
    } else if (one.op === 'lines') {
      ctx.beginPath();
      for (const path of one.paths) path.forEach(([x, y], i) => (i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)));
      ctx.strokeStyle = one.stroke;
      ctx.lineWidth = one.width;
      ctx.lineJoin = 'round';
      // An outline is made of lengths that meet at their ends: a round end closes the corner.
      ctx.lineCap = one.cap || 'butt';
      ctx.stroke();
      ctx.lineCap = 'butt';
    } else if (one.op === 'dot' || one.op === 'ring') {
      ctx.beginPath();
      ctx.arc(one.at[0], one.at[1], one.r, 0, Math.PI * 2);
      if (one.fill) {
        ctx.fillStyle = one.fill;
        ctx.fill();
      }
      ctx.strokeStyle = one.stroke;
      ctx.lineWidth = one.width || 2;
      ctx.stroke();
    } else if (one.op === 'square') {
      ctx.fillStyle = one.fill;
      ctx.fillRect(one.at[0] - one.r, one.at[1] - one.r, one.r * 2, one.r * 2);
      ctx.strokeStyle = one.stroke;
      ctx.lineWidth = 2;
      ctx.strokeRect(one.at[0] - one.r, one.at[1] - one.r, one.r * 2, one.r * 2);
    } else if (one.op === 'text') {
      ctx.font = `${one.bold ? '700' : '400'} ${one.size}px system-ui, sans-serif`;
      ctx.textAlign = one.align || 'center';
      ctx.textBaseline = 'middle';
      ctx.lineJoin = 'round';
      ctx.strokeStyle = one.halo;
      ctx.lineWidth = 4;
      ctx.strokeText(one.text, one.at[0], one.at[1]);
      ctx.fillStyle = one.fill;
      ctx.fillText(one.text, one.at[0], one.at[1]);
    } else if (one.op === 'cross') {
      const [x, y] = one.at;
      for (const [colour, width] of [[one.halo, one.width + 3], [one.stroke, one.width]]) {
        ctx.beginPath();
        ctx.moveTo(x - one.r, y);
        ctx.lineTo(x + one.r, y);
        ctx.moveTo(x, y - one.r);
        ctx.lineTo(x, y + one.r);
        ctx.strokeStyle = colour;
        ctx.lineWidth = width;
        ctx.stroke();
      }
    }
  }
  ctx.globalAlpha = 1;
  ctx.setLineDash([]);
}

// ---------------------------------------------------------------- in words

// What the map shows, for a person who cannot see it.
export function describe({ layers, item, moves = [], theirs = [], refused = [] }) {
  const parts = [];
  const title = item && typeof item.title === 'string' ? item.title : 'this item';
  const drawn = ORDER.filter((name) => layers[name]);
  if (drawn.length === 0) parts.push(`No map is drawn for ${title}.`);
  else parts.push(`Map of ${title}.`);
  if (layers.cells) {
    const areas = areasAfter(layers.cells, moves);
    const mine = ownCells(item, areas);
    const inside = layers.cells.features.filter((feature) => mine(feature, areas.get(feature.id)));
    const within = new Set(inside.map((feature) => areas.get(feature.id)));
    const others = new Set([...areas.values()].filter((area) => typeof area === 'string' && !within.has(area)));
    const own = inside.length;
    if (within.size > 1) parts.push(`${own} cells in ${within.size} areas are in it: ${[...within].map((id) => nameOf(layers, id)).sort().slice(0, 40).join(', ')}.`);
    else parts.push(`${own} ${own === 1 ? 'cell is' : 'cells are'} in it.`);
    if (others.size > 0) {
      const names = [...others].map((id) => nameOf(layers, id)).sort();
      parts.push(`Beside it: ${names.slice(0, 12).join(', ')}${names.length > 12 ? ', and more' : ''}.`);
    }
  }
  if (focusOf(item).point && askedOf(item) !== '') parts.push(`A ring marks where a record puts ${askedOf(item)}.`);
  const drafted = marksOf(item);
  const marked = [];
  if (drafted.cells.size > 0) marked.push(`${drafted.cells.size} ${drafted.cells.size === 1 ? 'cell' : 'cells'} in doubt`);
  if (drafted.sides.length > 0) marked.push(`${drafted.sides.length} ${drafted.sides.length === 1 ? 'stretch that follows' : 'stretches that follow'} no line`);
  for (const area of drafted.seeds) marked.push(`the seed of ${nameOf(layers, area)}`);
  for (const centre of drafted.centres) marked.push(`the town centre ${centre}`);
  if (marked.length > 0) parts.push(`Marked: ${marked.join(', ')}.`);
  if (moves.length > 0) parts.push(`${moves.length} ${moves.length === 1 ? 'cell has' : 'cells have'} been moved.`);
  if (theirs.length > 0) parts.push(`Another reviewer moved ${theirs.length} ${theirs.length === 1 ? 'cell' : 'cells'}.`);
  if (drawn.length > 0) parts.push(`Shown: ${drawn.join(', ')}.`);
  for (const why of refused) parts.push(why);
  return parts.join(' ');
}
