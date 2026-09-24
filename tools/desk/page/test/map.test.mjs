// What is drawn behind a border, and what never is.

import assert from 'node:assert/strict';
import { test } from 'node:test';

import {
  MAY_DRAW,
  accept,
  areaColour,
  areasAfter,
  boxFor,
  boxOf,
  cellAt,
  coloursOf,
  credit,
  describe,
  drawList,
  fit,
  focusOf,
  layersFor,
  moveView,
  nameOf,
  ownCells,
  paint,
  panBy,
  refit,
  slug,
  themeOf,
  toGround,
  toScreen,
  zoomBy,
} from '../map.mjs';
import { contrast } from './support/colour.mjs';
import { LAYERS, layer } from './support/city.mjs';

const size = { width: 800, height: 600 };
const item = { id: 'syn-n0007', group: 'quillhaven', title: 'Alderwick, Quillhaven', map: { bbox: [0, 0, 0.02, 0.02], focus: 'syn-n0007', layers: ['cells', 'areas', 'roads', 'names', 'seeds'] } };

function near(actual, expected, by = 1e-9) {
  assert.ok(Math.abs(actual - expected) <= by, `${actual} is not ${expected}`);
}

// ---------------------------------------------------------------- what may be asked for

test('only the layers the design allows behind a border are ever asked for', () => {
  const asked = layersFor({
    group: 'quillhaven',
    map: { layers: ['cells', 'basemap', 'tiles', 'osm', 'stations', 'parks', 'rivers', 'msoa', 'imagery', 'residents', 'prices', 'roads'] },
  });
  assert.deepEqual(asked.map((one) => one.key), ['quillhaven/cells', 'quillhaven/roads']);
});

test('the layers that may be drawn are the nine of the design and no other', () => {
  assert.deepEqual([...MAY_DRAW].sort(), ['areas', 'boroughs', 'cells', 'centres', 'names', 'records', 'roads', 'seeds', 'wards']);
});

test('a layer is asked for in the group of its item and boroughs in the group all', () => {
  const asked = layersFor({ group: 'quillhaven', map: { layers: ['cells', 'boroughs'] } });
  assert.deepEqual(asked.map((one) => one.key), ['quillhaven/cells', 'all/boroughs']);
});

test('a layer may name its own group', () => {
  const asked = layersFor({ group: 'quillhaven', map: { layers: ['all/boroughs', { group: 'marrowmere', layer: 'cells' }] } });
  assert.deepEqual(asked.map((one) => one.key), ['all/boroughs', 'marrowmere/cells']);
});

test('a layer named twice is asked for once', () => {
  assert.equal(layersFor({ group: 'g', map: { layers: ['cells', 'cells', 'g/cells'] } }).length, 1);
});

test('an item with no map asks for no layer', () => {
  assert.deepEqual(layersFor({ group: 'g', map: null }), []);
  assert.deepEqual(layersFor({ group: 'g' }), []);
  assert.deepEqual(layersFor(null), []);
});

// ---------------------------------------------------------------- what may be drawn

const want = { group: 'quillhaven', layer: 'cells' };

test('a layer that says what it is and where it is from is drawn', () => {
  assert.deepEqual(accept(LAYERS['quillhaven/cells'], want, true), { ok: true, why: '' });
});

test('a layer made from OpenStreetMap is never drawn', () => {
  for (const id of ['openstreetmap-points-of-interest', 'osm-place-nodes', 'protomaps-basemap-london', 'overture-divisions', 'whosonfirst-gazetteer']) {
    const file = layer('cells', 'quillhaven', [], { source_ids: ['synthetic', id] });
    const out = accept(file, want, true);
    assert.equal(out.ok, false, id);
    assert.match(out.why, /may not stand behind a border/);
  }
});

test('a layer from a banned source or from imagery is never drawn', () => {
  for (const id of ['google-places', 'google-street-view', 'mapillary-street-imagery', 'geograph-images']) {
    assert.equal(accept(layer('cells', 'quillhaven', [], { source_ids: [id] }), want, true).ok, false, id);
  }
});

test('a layer about who lives somewhere, a price or a crime rate is never drawn', () => {
  const ids = [
    'ons-census-2021-protected-characteristics',
    'ons-census-2021-resident-tables',
    'gla-loac-2021',
    'mhclg-iod-2025-underlying-indicators',
    'police-uk-street-level-crime',
    'hmlr-price-paid',
    'ons-price-index-of-private-rents',
    'ons-private-rental-market-london-postcode-district',
  ];
  for (const id of ids) assert.equal(accept(layer('cells', 'quillhaven', [], { source_ids: [id] }), want, true).ok, false, id);
});

test('the sources the design draws from are let through', () => {
  const ids = ['ons-output-areas-2021', 'ons-oa21-lsoa21-msoa21-lad22-lookup', 'os-boundary-line', 'gla-town-centre-boundaries', 'os-open-roads', 'os-open-names', 'wikidata-places-and-landmarks'];
  const file = layer('cells', 'quillhaven', [], { source_ids: ids, synthetic: false });
  assert.equal(accept(file, want, false).ok, true);
});

const records = { group: 'quillhaven', layer: 'records' };
const point = (id, properties) => ({ type: 'Feature', id, properties, geometry: { type: 'Point', coordinates: [0.005, 0.005] } });

test('a record of a source its layer does not name is never drawn', () => {
  // Rule 3. The layer names one publisher and holds a record of another.
  const named = { source_ids: ['os-open-names'], synthetic: false };
  const file = layer('records', 'quillhaven', [point('lon-r1', { source_id: 'os-open-names', as_written: 'A' }), point('lon-r2', { source_id: 'wikidata-places-and-landmarks', as_written: 'B' })], named);
  const out = accept(file, records, false);
  assert.equal(out.ok, false);
  assert.match(out.why, /^records is not drawn: a record is of a source the layer does not name\.$/);
});

test('a record from OpenStreetMap is never drawn, whatever its layer names', () => {
  for (const id of ['osm-place-nodes', 'openstreetmap-points-of-interest', 'overture-places']) {
    const named = { source_ids: ['os-open-names', id], synthetic: false };
    const file = layer('records', 'quillhaven', [point('lon-r1', { source_id: id, as_written: 'A name as it writes it' })], named);
    assert.equal(accept(file, records, false).ok, false, id);
    const hidden = layer('records', 'quillhaven', [point('lon-r1', { source_id: id, as_written: 'A' })], { source_ids: ['os-open-names'], synthetic: false });
    assert.equal(accept(hidden, records, false).ok, false, id);
  }
});

test('a record that does not say which source it is of is never drawn', () => {
  for (const about of [{ as_written: 'A' }, { source_id: '', as_written: 'A' }, { source_id: 7, as_written: 'A' }, null]) {
    const file = layer('records', 'quillhaven', [point('syn-r1', about)]);
    assert.equal(accept(file, records, true).ok, false);
  }
});

test('the records of the made-up city are drawn', () => {
  assert.deepEqual(accept(LAYERS['quillhaven/records'], records, true), { ok: true, why: '' });
});

test('the line under the map names the sources of the records drawn, and no source that none is of', () => {
  const named = { source_ids: ['os-open-names', 'wikidata-places-and-landmarks', 'gla-town-centre-boundaries'], synthetic: false };
  const held = layer('records', 'quillhaven', [point('lon-r1', { source_id: 'os-open-names', as_written: 'A' })], named);
  const cells = layer('cells', 'quillhaven', [], { source_ids: ['ons-output-areas-2021'], synthetic: false });
  assert.equal(credit({ cells, records: held }), 'Drawn from: ons-output-areas-2021, os-open-names. No other map is behind it.');
});

test('a layer that names no source is not drawn', () => {
  assert.equal(accept(layer('cells', 'quillhaven', [], { source_ids: [] }), want, true).ok, false);
  assert.equal(accept(layer('cells', 'quillhaven', [], { source_ids: [''] }), want, true).ok, false);
  const bare = { type: 'FeatureCollection', features: [] };
  assert.equal(accept(bare, want, true).ok, false);
});

test('a made-up layer is not drawn on real data, nor a real one on the made-up city', () => {
  assert.equal(accept(LAYERS['quillhaven/cells'], want, false).ok, false);
  const real = layer('cells', 'quillhaven', [], { source_ids: ['ons-output-areas-2021'], synthetic: false });
  assert.equal(accept(real, want, true).ok, false);
});

test('a file that is another layer than the one asked for is not drawn', () => {
  assert.equal(accept(LAYERS['quillhaven/roads'], want, true).ok, false);
  assert.equal(accept(layer('cells', 'marrowmere', []), want, true).ok, false);
  assert.equal(accept(layer('tiles', 'quillhaven', []), { group: 'quillhaven', layer: 'tiles' }, true).ok, false);
});

test('what is not a layer at all is not drawn', () => {
  for (const file of [null, 'x', {}, { type: 'Feature' }, { type: 'FeatureCollection' }]) {
    assert.equal(accept(file, want, true).ok, false);
  }
});

test('the line under the map names every source drawn from, each once', () => {
  const layers = { cells: LAYERS['quillhaven/cells'], roads: LAYERS['quillhaven/roads'] };
  assert.equal(credit(layers), 'Drawn from: synthetic. No other map is behind it.');
  assert.equal(credit({}), '');
});

test('a layer the page may not draw is not drawn even if it is handed over', () => {
  const tiles = layer('tiles', 'quillhaven', LAYERS['quillhaven/cells'].features);
  const list = drawList({ layers: { tiles }, view: fit(item.map.bbox, size), size, item });
  assert.deepEqual(list.map((one) => one.op), ['clear']);
});

// ---------------------------------------------------------------- the projection

test('the item fits the canvas with room to spare', () => {
  const view = fit([0, 0, 0.02, 0.01], size, 24);
  const [x0, y0] = toScreen(view, size, [0, 0.01]);
  const [x1, y1] = toScreen(view, size, [0.02, 0]);
  assert.ok(x0 >= 24 - 1e-6 && y0 >= 24 - 1e-6);
  assert.ok(x1 <= 800 - 24 + 1e-6 && y1 <= 600 - 24 + 1e-6);
  near(x0, 24, 1e-6);
});

test('north is up and east is right', () => {
  const view = fit([0, 0, 0.02, 0.02], size);
  const [x, y] = toScreen(view, size, [0.01, 0.01]);
  const [xe] = toScreen(view, size, [0.02, 0.01]);
  const [, yn] = toScreen(view, size, [0.01, 0.02]);
  assert.ok(xe > x);
  assert.ok(yn < y);
});

test('a degree of longitude is narrowed by the latitude of the item', () => {
  const view = fit([-0.2, 51.4, 0.0, 51.6], size);
  near(view.squeeze, Math.cos((51.5 * Math.PI) / 180), 1e-12);
  const [x0] = toScreen(view, size, [-0.2, 51.5]);
  const [x1] = toScreen(view, size, [0, 51.5]);
  const [, y0] = toScreen(view, size, [-0.1, 51.4]);
  const [, y1] = toScreen(view, size, [-0.1, 51.6]);
  near((x1 - x0) / (y0 - y1), view.squeeze, 1e-9);
});

test('a point of the screen goes to the ground and back', () => {
  const view = fit([-0.2, 51.4, 0.0, 51.6], size);
  const [lon, lat] = toGround(view, size, [123, 456]);
  const [x, y] = toScreen(view, size, [lon, lat]);
  near(x, 123, 1e-6);
  near(y, 456, 1e-6);
});

test('a box that is no box still gives a view that can be drawn', () => {
  for (const bbox of [null, [], [0, 0, 0, 0], [1, 2, Number.NaN, 4], ['a', 'b', 'c', 'd']]) {
    const view = fit(bbox, size);
    assert.ok(Number.isFinite(view.k) && view.k > 0);
    assert.ok(Number.isFinite(view.lon) && Number.isFinite(view.lat));
  }
});

test('an item that gives no box is fitted to the cells of its own area', () => {
  const bare = { ...item, map: { ...item.map, bbox: null } };
  assert.deepEqual(boxFor(bare, { cells: LAYERS['quillhaven/cells'] }), [0, 0, 0.02, 0.01]);
  assert.deepEqual(boxFor(item, {}), item.map.bbox);
});

test('an item about no area is fitted to every cell, and to nothing when there is none', () => {
  const bare = { ...item, map: { ...item.map, bbox: [0, 0, 0, 0], focus: null } };
  assert.deepEqual(boxFor(bare, { cells: LAYERS['quillhaven/cells'] }), [0, 0, 0.02, 0.02]);
  assert.equal(boxFor(bare, {}), null);
});

test('zooming keeps the point under the pointer where it is', () => {
  const view = fit([0, 0, 0.02, 0.02], size);
  const at = [200, 150];
  const ground = toGround(view, size, at);
  const closer = zoomBy(view, size, 2, at);
  const [x, y] = toScreen(closer, size, ground);
  near(x, 200, 1e-6);
  near(y, 150, 1e-6);
  near(closer.k, view.k * 2, 1e-6);
});

test('zoom stops at a most and a least', () => {
  let view = fit([0, 0, 0.02, 0.02], size);
  const fitted = view.k;
  for (let i = 0; i < 40; i += 1) view = zoomBy(view, size, 2);
  near(view.k, fitted * 64, 1e-6);
  for (let i = 0; i < 40; i += 1) view = zoomBy(view, size, 0.5);
  near(view.k, fitted / 8, 1e-9);
});

test('dragging moves the ground with the hand', () => {
  const view = fit([0, 0, 0.02, 0.02], size);
  const ground = toGround(view, size, [400, 300]);
  const [x, y] = toScreen(panBy(view, 50, -20), size, ground);
  near(x, 450, 1e-6);
  near(y, 280, 1e-6);
});

test('the key 0 fits the item again after the map was moved', () => {
  const fitted = fit(item.map.bbox, size);
  let view = moveView(fitted, size, 'in', fitted);
  view = moveView(view, size, 'left', fitted);
  view = moveView(view, size, 'up', fitted);
  assert.notDeepEqual(view, fitted);
  assert.deepEqual(moveView(view, size, 'fit', fitted), fitted);
});

test('in a canvas of another size the map keeps its middle and is as close as it was', () => {
  const before = fit(item.map.bbox, size);
  const smaller = { width: 800, height: 570 };
  const after = fit(item.map.bbox, smaller);
  assert.deepEqual(refit(before, before, after), after, 'a map that was fitted is fitted still');
  const moved = moveView(moveView(before, size, 'in', before), size, 'left', before);
  const kept = refit(moved, before, after);
  near(kept.lon, moved.lon);
  near(kept.lat, moved.lat);
  near(kept.k / after.k, moved.k / before.k);
  assert.deepEqual(moveView(kept, smaller, 'fit', after), after);
});

test('an arrow with Shift moves the map a quarter as far, so that the cross can be put on any cell', () => {
  // At the desk an arrow moved the map 106 pixels where a cell was 61 wide.
  const fitted = fit(item.map.bbox, size);
  const ground = toGround(fitted, size, [400, 300]);
  for (const [way, dx, dy] of [['right', -19, 0], ['left', 19, 0], ['up', 0, 19], ['down', 0, -19]]) {
    const [x, y] = toScreen(moveView(fitted, size, way, fitted, true), size, ground);
    near(x, 400 + dx, 1e-6);
    near(y, 300 + dy, 1e-6);
  }
  assert.deepEqual(moveView(fitted, size, 'in', fitted, true), moveView(fitted, size, 'in', fitted), 'Shift changes no other key of the map');
});

test('the arrow keys move the map an eighth of the canvas', () => {
  const fitted = fit(item.map.bbox, size);
  const ground = toGround(fitted, size, [400, 300]);
  const [x, y] = toScreen(moveView(fitted, size, 'right', fitted), size, ground);
  near(x, 400 - 75, 1e-6);
  near(y, 300, 1e-6);
});

// ---------------------------------------------------------------- cells and moves

const cells = LAYERS['quillhaven/cells'];

test('a point of the ground is in the cell that holds it', () => {
  assert.equal(cellAt(cells, [0.005, 0.005]).id, 'syn-oa-0001');
  assert.equal(cellAt(cells, [0.015, 0.005]).id, 'syn-oa-0002');
  assert.equal(cellAt(cells, [0.005, 0.015]).id, 'syn-oa-0003');
});

test('a point outside every cell is in none', () => {
  assert.equal(cellAt(cells, [0.5, 0.5]), null);
  assert.equal(cellAt(null, [0, 0]), null);
});

test('a point in the hole of a cell is not in the cell', () => {
  const ring = [[0, 0], [4, 0], [4, 4], [0, 4], [0, 0]];
  const hole = [[1, 1], [3, 1], [3, 3], [1, 3], [1, 1]];
  const holed = layer('cells', 'g', [{ type: 'Feature', id: 'syn-oa-h', properties: { area: 'a', colour: 0 }, geometry: { type: 'Polygon', coordinates: [ring, hole] } }]);
  assert.equal(cellAt(holed, [2, 2]), null);
  assert.equal(cellAt(holed, [0.5, 0.5]).id, 'syn-oa-h');
});

test('a cell in two pieces is found in either', () => {
  const a = [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]];
  const b = [[5, 5], [6, 5], [6, 6], [5, 6], [5, 5]];
  const two = layer('cells', 'g', [{ type: 'Feature', id: 'syn-oa-t', properties: { area: 'a', colour: 0 }, geometry: { type: 'MultiPolygon', coordinates: [[a], [b]] } }]);
  assert.equal(cellAt(two, [5.5, 5.5]).id, 'syn-oa-t');
  assert.equal(cellAt(two, [3, 3]), null);
});

test('a cell is in the area the last move put it in', () => {
  const moves = [
    { n: 7, part: 'syn-oa-0001', detail: { from: 'syn-n0007', to: 'syn-n0012' } },
    { n: 3, part: 'syn-oa-0001', detail: { from: 'syn-n0007', to: 'syn-n0004' } },
  ];
  const areas = areasAfter(cells, moves);
  assert.equal(areas.get('syn-oa-0001'), 'syn-n0012');
  assert.equal(areas.get('syn-oa-0002'), 'syn-n0007');
});

test('a move of a cell the layer does not hold moves nothing', () => {
  const areas = areasAfter(cells, [{ n: 1, part: 'syn-oa-9999', detail: { from: 'a', to: 'b' } }]);
  assert.equal(areas.size, 4);
  assert.equal(areas.has('syn-oa-9999'), false);
});

test('an area has the colour its cells were given', () => {
  assert.deepEqual([...coloursOf(cells)], [['syn-n0007', 2], ['syn-n0012', 5]]);
});

test('a moved cell is drawn in the colour of the area it joined, and marked', () => {
  const view = fit(item.map.bbox, size);
  const before = drawList({ layers: { cells }, view, size, item });
  const after = drawList({ layers: { cells }, view, size, item, moves: [{ n: 1, part: 'syn-oa-0001', detail: { from: 'syn-n0007', to: 'syn-n0012' } }] });
  const shapes = (list) => list.filter((one) => one.op === 'shape');
  assert.equal(shapes(before)[0].fill, areaColour(2, false));
  assert.equal(shapes(after)[0].fill, areaColour(5, false));
  assert.equal(before.filter((one) => one.op === 'dot').length, 0);
  assert.equal(after.filter((one) => one.op === 'dot').length, 1);
});

// The border as it now stands: the edges of the item's cells that no other cell of it shares.
function edges(list) {
  const heavy = list.filter((one) => one.op === 'lines' && one.width === 4);
  return heavy.flatMap((one) => one.paths).map((path) => path.map(([x, y]) => `${Math.round(x)},${Math.round(y)}`).sort().join(' to ')).sort();
}

test('after a move the heavy outline runs round the cells the area now holds', () => {
  // At the desk the fill of a moved cell changed and the heavy line did not: it
  // still ran round the cell that had left, while the page asked "is it right now?".
  const view = fit(item.map.bbox, size);
  const layers = { cells, areas: all.areas };
  const moves = [{ n: 1, part: 'syn-oa-0003', detail: { from: 'syn-n0012', to: 'syn-n0007' } }];
  const at = (lon, lat) => toScreen(view, size, [lon, lat]).map(Math.round).join(',');
  const edge = (a, b) => [at(...a), at(...b)].sort().join(' to ');
  const list = drawList({ layers, view, size, item, moves });
  // Cells 1, 2 and 3 are the area now: an L of three squares, with eight edges round it.
  assert.deepEqual(edges(list), [
    edge([0, 0], [0.01, 0]), edge([0.01, 0], [0.02, 0]), edge([0.02, 0], [0.02, 0.01]), edge([0.02, 0.01], [0.01, 0.01]),
    edge([0.01, 0.01], [0.01, 0.02]), edge([0.01, 0.02], [0, 0.02]), edge([0, 0.02], [0, 0.01]), edge([0, 0.01], [0, 0]),
  ].sort());
  assert.ok(!edges(list).includes(edge([0, 0.01], [0.01, 0.01])), 'no line runs between the cell that joined and the area');
});

test('after a move the outline as drafted is a thin broken line, for the areas that lost or gained a cell', () => {
  const view = fit(item.map.bbox, size);
  const layers = { cells, areas: all.areas };
  const before = drawList({ layers, view, size, item }).filter((one) => one.op === 'shape' && one.fill === null);
  assert.deepEqual(before.map((one) => [one.width, one.dash]), [[4, null], [1.5, null]]);
  assert.deepEqual(edges(drawList({ layers, view, size, item })), [], 'with no move the outline is the one drafted');
  const moves = [{ n: 1, part: 'syn-oa-0003', detail: { from: 'syn-n0012', to: 'syn-n0007' } }];
  const after = drawList({ layers, view, size, item, moves }).filter((one) => one.op === 'shape' && one.fill === null);
  assert.ok(after.every((one) => one.width <= 1.5 && Array.isArray(one.dash)), 'no heavy line is left where the draft ran');
  assert.equal(after.length, 2);
});

test('a move taken back gives the drafted outline back', () => {
  const view = fit(item.map.bbox, size);
  const layers = { cells, areas: all.areas };
  const there = { n: 1, part: 'syn-oa-0003', detail: { from: 'syn-n0012', to: 'syn-n0007' } };
  const back = { n: 2, part: 'syn-oa-0003', detail: { from: 'syn-n0007', to: 'syn-n0012' } };
  const list = drawList({ layers, view, size, item, moves: [there, back] });
  assert.deepEqual(edges(list), []);
  assert.deepEqual(list.filter((one) => one.op === 'shape' && one.fill === null).map((one) => one.width), [4, 1.5]);
});

test('in a whole borough every area that lost or gained a cell is outlined as it now stands', () => {
  const whole = { id: 'quillhaven', group: 'quillhaven', title: 'Quillhaven', map: { bbox: [0, 0, 0.02, 0.02], focus: ['syn-n0007', 'syn-n0012'], layers: ['cells', 'areas'] } };
  const view = fit(whole.map.bbox, size);
  const moves = [{ n: 1, part: 'syn-oa-0003', detail: { from: 'syn-n0012', to: 'syn-n0007' } }];
  const list = drawList({ layers: { cells, areas: all.areas }, view, size, item: whole, moves });
  // Three cells have eight edges round them, and the one cell left has four.
  assert.equal(edges(list).length, 12);
});

test('a cell another reviewer moved is ringed in a stroke of its own, and is not moved for me', () => {
  const view = fit(item.map.bbox, size);
  const theirs = [{ reviewer: 'r2', cell: 'syn-oa-0001', from: 'syn-n0007', to: 'syn-n0012' }];
  const list = drawList({ layers: { cells }, view, size, item, theirs });
  assert.equal(list.filter((one) => one.op === 'shape')[0].fill, areaColour(2, false), 'the draft stands on my map');
  const rings = list.filter((one) => one.op === 'ring');
  assert.equal(rings.length, 1);
  assert.deepEqual(rings[0].dash, [3, 3]);
  assert.equal(list.filter((one) => one.op === 'dot').length, 0, 'the dot is for my own moves');
  assert.ok(list.indexOf(rings[0]) > list.findLastIndex((one) => one.op === 'shape'), 'the ring lies over the cells');
});

test('the words of the map say how many cells another reviewer moved', () => {
  const theirs = [{ reviewer: 'r2', cell: 'syn-oa-0001', from: 'syn-n0007', to: 'syn-n0012' }];
  assert.match(describe({ layers: { cells }, item, theirs }), /Another reviewer moved 1 cell\./);
});

test('a cell that a line of the item is about is ringed on the map', () => {
  const flagged = { ...item, lines: [{ label: 'Cells', value: '2 cells', source_id: '' }, { label: 'syn-oa-0002', value: 'margin 4%', source_id: '' }] };
  const list = drawList({ layers: { cells }, view: fit(item.map.bbox, size), size, item: flagged });
  assert.equal(list.filter((one) => one.op === 'ring').length, 1);
  const ring = list.find((one) => one.op === 'ring');
  assert.ok(list.indexOf(ring) > list.findLastIndex((one) => one.op === 'shape'), 'the ring lies over the cells');
});

// ---------------------------------------------------------------- what a draft marks on a border

const lined = (...codes) => [{ label: 'Cells', value: '2 cells', source_id: '' }, ...codes.map((code) => ({ label: code, value: 'in doubt', source_id: '' }))];
const marked = (marks, codes = Object.keys(marks.cells || {})) => ({ ...item, lines: lined(...codes), map: { ...item.map, marks } });
const texts = (list) => list.filter((one) => one.op === 'text' && !one.legend).map((one) => one.text);
const looks = (list) => list.filter((one) => one.mark).map((one) => one.mark);

test('at the scale an item opens at a cell in doubt has a ring and no code, but for the cell under the cross', () => {
  // Seen at the desk on a border of London with 45 cells in doubt: the codes crowded
  // the area until the map was brought close, and a code was moved away from its ring.
  const flagged = marked({ cells: { 'syn-oa-0001': ['margin_under_10'], 'syn-oa-0002': ['margin_under_10'] } });
  const view = fit(item.map.bbox, size);
  const open = drawList({ layers: { cells }, view, size, item: flagged });
  assert.equal(open.filter((one) => one.op === 'ring' && !one.legend).length, 2);
  assert.deepEqual(texts(open), []);
  // The cross is in the middle of the canvas. The map is moved until it is on a cell.
  const [x, y] = toScreen(view, size, [0.005, 0.005]);
  const moved = panBy(view, size.width / 2 - x, size.height / 2 - y);
  assert.deepEqual(texts(drawList({ layers: { cells }, view: moved, size, item: flagged, cross: true })), ['syn-oa-0001']);
  assert.deepEqual(texts(drawList({ layers: { cells }, view: moved, size, item: flagged })), [], 'with no cross, no cell is under it');
  // Brought close, every ring in view has its code.
  const close = zoomBy(view, size, 2);
  assert.deepEqual(texts(drawList({ layers: { cells }, view: close, size, item: flagged })).sort(), ['syn-oa-0001', 'syn-oa-0002']);
});

test('the mark on a cell in doubt says by its look what the doubt is', () => {
  const view = fit(item.map.bbox, size);
  const every = { 'syn-oa-0001': ['margin_under_10'], 'syn-oa-0002': ['two_boroughs'], 'syn-oa-0003': ['seeds_close'], 'syn-oa-0004': ['two_pieces'] };
  const list = drawList({ layers: { cells }, view, size, item: marked({ cells: every }) });
  assert.deepEqual(looks(list).sort(), ['margin_under_10', 'seeds_close', 'two_boroughs', 'two_pieces']);
  const by = Object.fromEntries(list.filter((one) => one.mark).map((one) => [one.mark, one]));
  assert.equal(by.margin_under_10.op, 'ring');
  assert.equal(by.two_boroughs.op, 'shape');
  assert.equal(by.two_boroughs.rings[0].length, 4, 'a square');
  assert.equal(by.seeds_close.rings[0].length, 4, 'a square on its point');
  assert.equal(by.two_pieces.rings[0].length, 3, 'a triangle');
  assert.notDeepEqual(by.two_boroughs.rings, by.seeds_close.rings);
  for (const one of Object.values(by)) assert.ok(!one.fill, 'a mark hides nothing under it');
  // A cell under two doubts has both marks, one round the other.
  const both = drawList({ layers: { cells }, view, size, item: marked({ cells: { 'syn-oa-0001': ['margin_under_10', 'two_boroughs'] } }) });
  assert.deepEqual(looks(both).sort(), ['margin_under_10', 'two_boroughs']);
});

test('a cell the draft lists and says no doubt of is ringed as before', () => {
  const list = drawList({ layers: { cells }, view: fit(item.map.bbox, size), size, item: { ...item, lines: lined('syn-oa-0002') } });
  assert.equal(list.filter((one) => one.op === 'ring').length, 1);
  assert.deepEqual(looks(list), []);
});

test('the map says what each look means, for the looks that are on it and no other', () => {
  const view = fit(item.map.bbox, size);
  const legend = (marks) => drawList({ layers: { cells, seeds: all.seeds }, view, size, item: marked(marks) }).filter((one) => one.op === 'text' && one.legend).map((one) => one.text);
  assert.deepEqual(legend({ cells: { 'syn-oa-0001': ['margin_under_10'] } }), ['margin under 10%']);
  assert.deepEqual(
    legend({ cells: { 'syn-oa-0001': ['two_boroughs', 'margin_under_10'], 'syn-oa-0002': ['seeds_close'] }, sides: [['syn-oa-0001', 'syn-oa-0003']], seeds: ['syn-n0012'] }),
    ['margin under 10%', 'outside the main borough', 'beside an area whose seed is close', 'a stretch that follows no line', 'the seed that stands close'],
  );
  assert.deepEqual(legend({}), []);
  assert.deepEqual(drawList({ layers: { cells }, view, size, item }).filter((one) => one.legend), []);
});

test('a border flagged for following no line has each stretch that follows none drawn over it', () => {
  // The flag put no cell in doubt, so nothing on the map said which stretch was meant.
  const view = fit(item.map.bbox, size);
  const list = drawList({ layers: { cells }, view, size, item: marked({ sides: [['syn-oa-0001', 'syn-oa-0003']] }, []) });
  const stretches = list.filter((one) => one.mark === 'follows_nothing');
  assert.equal(stretches.length, 1);
  assert.equal(stretches[0].op, 'lines');
  // The two cells share one edge: from the west of the city to its middle, along the line between the areas.
  assert.deepEqual(stretches[0].paths, [[toScreen(view, size, [0.01, 0.01]), toScreen(view, size, [0, 0.01])]]);
  assert.ok(stretches[0].width >= 4 && Array.isArray(stretches[0].dash));
  assert.ok(list.indexOf(stretches[0]) > list.findLastIndex((one) => one.op === 'shape' && one.fill && !one.legend), 'it lies over the cells');
  // Two cells that share no edge mark nothing, and neither does a cell the layer does not hold.
  assert.deepEqual(looks(drawList({ layers: { cells }, view, size, item: marked({ sides: [['syn-oa-0001', 'syn-oa-0004'], ['syn-oa-0001', 'syn-oa-9999']] }, []) })), []);
});

test('a border flagged for a seed close to another marks that seed, and joins the two', () => {
  const view = fit(item.map.bbox, size);
  const list = drawList({ layers: { cells, seeds: all.seeds }, view, size, item: marked({ seeds: ['syn-n0012'] }, []) });
  const other = toScreen(view, size, [0.014, 0.016]);
  const own = toScreen(view, size, [0.006, 0.006]);
  const rings = list.filter((one) => one.op === 'ring' && one.mark === 'seed');
  assert.deepEqual(rings.map((one) => one.at), [other, other], 'two rings, one round the other');
  assert.notEqual(rings[0].r, rings[1].r);
  const joined = list.find((one) => one.op === 'lines' && one.mark === 'seed');
  assert.deepEqual(joined.paths, [[own, other]]);
  assert.ok(texts(list).includes('Thrushcombe'), 'the seed is named');
  // With no seed marked no seed is ringed.
  assert.deepEqual(drawList({ layers: { cells, seeds: all.seeds }, view, size, item }).filter((one) => one.mark === 'seed'), []);
});

test('a town centre that a flag names is named on the map, as the one asked about is', () => {
  // Seen at the desk: a border was flagged for two town centres, both were hatched, and
  // neither was named.
  const view = fit(item.map.bbox, size);
  const outline = (west, south) => [[[west, south], [west + 0.002, south], [west + 0.002, south + 0.002], [west, south + 0.002], [west, south]]];
  const centre = (id, name, west, south) => ({ type: 'Feature', id, properties: { name, class: 'district' }, geometry: { type: 'Polygon', coordinates: outline(west, south) } });
  const centres = layer('centres', 'quillhaven', [centre('syn-t08', 'Tallowgate Parade', 0.003, 0.003), centre('syn-t09', 'Foxholt Market', 0.009, 0.009), centre('syn-t10', 'Osier Row', 0.015, 0.003)]);
  const named = (marks) => drawList({ layers: { centres }, view, size, item: marked(marks, []), cross: true }).filter((one) => one.op === 'text' && !one.legend).map((one) => [one.text, one.bold]);
  const heavy = (marks) => named(marks).filter(([, bold]) => bold).map(([text]) => text).sort();
  assert.deepEqual(heavy({ centres: ['Tallowgate Parade', 'Foxholt Market'] }), ['Foxholt Market', 'Tallowgate Parade']);
  assert.ok(named({ centres: ['Tallowgate Parade', 'Foxholt Market'] }).some(([text]) => text === 'Foxholt Market'), 'though it lies under the cross');
  assert.deepEqual(heavy({}), [], 'no town centre is named in heavy letters for its own sake');
  assert.ok(!named({}).some(([text]) => text === 'Foxholt Market'), 'and one under the cross is left out');
});

test('the words of the map say what is marked on it', () => {
  const marks = { cells: { 'syn-oa-0001': ['margin_under_10'], 'syn-oa-0002': ['two_boroughs'] }, sides: [['syn-oa-0001', 'syn-oa-0003']], seeds: ['syn-n0012'], centres: ['Alderwick'] };
  const words = describe({ layers: all, item: marked(marks) });
  assert.match(words, /Marked: 2 cells in doubt, 1 stretch that follows no line, the seed of Thrushcombe, the town centre Alderwick\./);
  assert.doesNotMatch(describe({ layers: all, item }), /Marked/);
});

test('the cell in the hand is drawn apart from the rest', () => {
  const view = fit(item.map.bbox, size);
  const list = drawList({ layers: { cells }, view, size, item, hand: { cell: 'syn-oa-0002', area: 'syn-n0007' } });
  const thick = list.filter((one) => one.op === 'shape' && one.width === 4);
  assert.equal(thick.length, 1);
  assert.equal(thick[0].stroke, themeOf(false).hand);
});

test('the area the item is about stands out from the areas beside it', () => {
  const view = fit(item.map.bbox, size);
  const shapes = drawList({ layers: { cells }, view, size, item }).filter((one) => one.op === 'shape');
  assert.deepEqual(shapes.map((one) => one.alpha), [1, 1, 0.45, 0.45]);
});

test('an area the person chose is drawn as strongly as the item own, and outlined apart', () => {
  const view = fit(item.map.bbox, size);
  const list = drawList({ layers: { cells, areas: LAYERS['quillhaven/areas'] }, view, size, item, chosen: ['syn-n0012'] });
  const shapes = list.filter((one) => one.op === 'shape');
  assert.deepEqual(shapes.slice(0, 4).map((one) => one.alpha), [1, 1, 1, 1]);
  assert.deepEqual(shapes.slice(4).map((one) => [one.width, one.stroke === themeOf(false).hand]), [[4, false], [4, true]]);
});

test('with no area to be about every cell is drawn alike', () => {
  const whole = { ...item, map: { ...item.map, focus: null } };
  const shapes = drawList({ layers: { cells }, view: fit(item.map.bbox, size), size, item: whole }).filter((one) => one.op === 'shape');
  assert.deepEqual(shapes.map((one) => one.alpha), [1, 1, 1, 1]);
});

test('an item about a whole borough has every cell of the borough as its own, and no cell of the margin', () => {
  const margin = { type: 'Feature', id: 'syn-oa-0009', properties: { area: 'syn-n0020', colour: 7, borough: 'Marrowmere' }, geometry: { type: 'Polygon', coordinates: [[[0.02, 0], [0.03, 0], [0.03, 0.01], [0.02, 0.01], [0.02, 0]]] } };
  const wide = layer('cells', 'quillhaven', [...cells.features, margin]);
  const whole = { id: 'quillhaven', group: 'quillhaven', title: 'Quillhaven', map: { bbox: [0, 0, 0.03, 0.02], focus: 'syn-b-quillhaven', layers: ['cells'] } };
  const shapes = drawList({ layers: { cells: wide }, view: fit(whole.map.bbox, size), size, item: whole }).filter((one) => one.op === 'shape');
  assert.deepEqual(shapes.map((one) => one.alpha), [1, 1, 1, 1, 0.45]);
  assert.equal(describe({ layers: { cells: wide }, item: whole }), 'Map of Quillhaven. 4 cells in 2 areas are in it: syn-n0007, syn-n0012. Beside it: syn-n0020. Shown: cells.');
});

test('a group is named as the desk names it', () => {
  assert.equal(slug('Quillhaven'), 'quillhaven');
  assert.equal(slug('Marrow Mere & Fen'), 'marrow-mere-fen');
  assert.equal(slug('  St. Alder\'s  '), 'st-alder-s');
});

test('an item about nothing in particular has every cell as its own', () => {
  const mine = ownCells({ group: 'all', map: { focus: null } }, new Map([['c', 'a']]));
  assert.equal(mine({ properties: { borough: 'Anywhere' } }, 'a'), true);
});

test('a borough asked about is filled and outlined among the others', () => {
  const boroughs = layer('boroughs', 'all', [
    { type: 'Feature', id: 'syn-b-quillhaven', properties: { name: 'Quillhaven' }, geometry: { type: 'Polygon', coordinates: [[[0, 0], [0.01, 0], [0.01, 0.02], [0, 0.02], [0, 0]]] } },
    { type: 'Feature', id: 'syn-b-marrowmere', properties: { name: 'Marrowmere' }, geometry: { type: 'Polygon', coordinates: [[[0.01, 0], [0.02, 0], [0.02, 0.02], [0.01, 0.02], [0.01, 0]]] } },
  ]);
  const know = { id: 'quillhaven', group: 'all', title: 'Quillhaven', map: { bbox: [0, 0, 0.02, 0.02], focus: 'syn-b-quillhaven', layers: ['boroughs'] } };
  const list = drawList({ layers: { boroughs }, view: fit(know.map.bbox, size), size, item: know });
  const shapes = list.filter((one) => one.op === 'shape');
  assert.deepEqual(shapes.map((one) => [one.fill !== null, one.width]), [[true, 4], [false, 2.5]]);
  const texts = list.filter((one) => one.op === 'text');
  assert.deepEqual(texts.map((one) => [one.text, one.bold]), [['Quillhaven', true], ['Marrowmere', false]]);
});

test('what the item is about may be an id, a list, a point or a record', () => {
  assert.deepEqual([...focusOf({ map: { focus: 'a' } }).ids], ['a']);
  assert.deepEqual([...focusOf({ map: { focus: ['a', 'b'] } }).ids], ['a', 'b']);
  assert.deepEqual(focusOf({ map: { focus: [0.1, 0.2] } }).point, [0.1, 0.2]);
  assert.deepEqual([...focusOf({ map: { focus: { area: 'a', at: [1, 2] } } }).ids], ['a']);
  assert.deepEqual(focusOf({ map: { focus: { area: 'a', at: [1, 2] } } }).point, [1, 2]);
  assert.equal(focusOf({ map: { focus: null } }).ids.size, 0);
  assert.equal(focusOf(null).ids.size, 0);
});

// ---------------------------------------------------------------- the drawing

const all = {
  cells,
  areas: LAYERS['quillhaven/areas'],
  roads: LAYERS['quillhaven/roads'],
  names: LAYERS['quillhaven/names'],
  seeds: LAYERS['quillhaven/seeds'],
  wards: LAYERS['quillhaven/wards'],
  centres: LAYERS['quillhaven/centres'],
  records: LAYERS['quillhaven/records'],
  boroughs: LAYERS['all/boroughs'],
};

test('cells are at the bottom and names on top', () => {
  const list = drawList({ layers: all, view: fit(item.map.bbox, size), size, item });
  const ops = list.map((one) => one.op);
  assert.equal(ops[0], 'clear');
  assert.equal(ops[1], 'shape');
  assert.ok(ops.lastIndexOf('text') > ops.lastIndexOf('shape'));
  assert.ok(ops.lastIndexOf('text') > ops.lastIndexOf('lines'));
  assert.ok(ops.indexOf('lines') > ops.indexOf('shape'), 'roads lie over cells');
});

test('nothing but the background is drawn before the first layer', () => {
  const list = drawList({ layers: {}, view: fit(item.map.bbox, size), size, item });
  assert.deepEqual(list, [{ op: 'clear', fill: themeOf(false).paper }]);
});

test('what is out of view is not drawn', () => {
  const far = { lon: 10, lat: 10, k: 40000, squeeze: 1, fitted: 40000 };
  const list = drawList({ layers: all, view: far, size, item });
  assert.deepEqual(list.map((one) => one.op), ['clear']);
});

test('the outline of the area the item is about is the heaviest', () => {
  const list = drawList({ layers: { areas: all.areas }, view: fit(item.map.bbox, size), size, item });
  assert.deepEqual(list.filter((one) => one.op === 'shape').map((one) => one.width), [4, 1.5]);
});

test('a town centre is hatched and a ward line is thin', () => {
  const list = drawList({ layers: { wards: all.wards, centres: all.centres }, view: fit(item.map.bbox, size), size, item });
  const shapes = list.filter((one) => one.op === 'shape');
  assert.equal(shapes[0].width, 1);
  assert.equal(shapes[0].hatch, null);
  assert.equal(shapes[1].hatch, themeOf(false).mark);
});

test('a record of the name asked about is drawn where its publisher puts it, with the name as written and who wrote it', () => {
  const named = { ...item, picks: ['Alderwick'] };
  const list = drawList({ layers: { records: all.records }, view: fit(item.map.bbox, size), size, item: named });
  assert.deepEqual(list.filter((one) => one.op === 'square').map((one) => one.r), [6]);
  assert.deepEqual(list.filter((one) => one.op === 'text').map((one) => [one.text, one.bold]), [['Alderwick (synthetic)', true]]);
});

test('a record of another name is drawn small, and named only when the map is close', () => {
  const other = { ...item, picks: ['Thrushcombe'] };
  const fitted = fit(item.map.bbox, size);
  const far = drawList({ layers: { records: all.records }, view: fitted, size, item: other });
  assert.deepEqual(far.filter((one) => one.op === 'square').map((one) => one.r), [3]);
  assert.deepEqual(far.filter((one) => one.op === 'text'), []);
  const close = drawList({ layers: { records: all.records }, view: zoomBy(fitted, size, 2, toScreen(fitted, size, [0.005, 0.0045])), size, item: other });
  assert.deepEqual(close.filter((one) => one.op === 'text').map((one) => one.text), ['Alderwick (synthetic)']);
});

test('where a record puts the name asked about is ringed and named, though no layer of records is drawn', () => {
  // Seen at the desk, on the first draft of London: a smaller place inside an area was
  // asked about, and nothing on the map said where in the area the place is.
  const asked = { ...item, title: 'Foxholt Market, Quillhaven', picks: ['Foxholt Market'], map: { ...item.map, focus: { area: 'syn-n0007', at: [0.004, 0.012] } } };
  const view = fit(item.map.bbox, size);
  const list = drawList({ layers: { cells }, view, size, item: asked });
  const rings = list.filter((one) => one.op === 'ring');
  assert.equal(rings.length, 1);
  assert.deepEqual(rings[0].at, toScreen(view, size, [0.004, 0.012]));
  assert.deepEqual(list.filter((one) => one.op === 'text').map((one) => [one.text, one.bold]), [['Foxholt Market', true]]);
  assert.match(describe({ layers: { cells }, item: asked }), /A ring marks where a record puts Foxholt Market\./);
  assert.doesNotMatch(describe({ layers: { cells }, item }), /A ring marks/);
});

test('the town centre whose name is asked about is named, though it lies under the cross', () => {
  // Seen at the desk, on the first draft of London: the name of a town centre was asked
  // about, two town centres were hatched in the area, and neither was named.
  const view = fit(item.map.bbox, size);
  const outline = [[[0.009, 0.009], [0.011, 0.009], [0.011, 0.011], [0.009, 0.011], [0.009, 0.009]]];
  const centres = layer('centres', 'quillhaven', [{ type: 'Feature', id: 'syn-t09', properties: { name: 'Foxholt Market', class: 'district' }, geometry: { type: 'Polygon', coordinates: outline } }]);
  const texts = (asked) => drawList({ layers: { centres }, view, size, item: asked, cross: true }).filter((one) => one.op === 'text').map((one) => [one.text, one.bold]);
  assert.deepEqual(texts({ ...item, picks: ['Thrushcombe'] }), [], 'a town centre under the cross is not named for its own sake');
  assert.deepEqual(texts({ ...item, picks: ['Foxholt Market'] }), [['Foxholt Market', true]]);
  const named = drawList({ layers: { centres }, view, size, item: { ...item, picks: ['Foxholt Market'] }, cross: true }).find((one) => one.op === 'text');
  const middle = [size.width / 2, size.height / 2];
  assert.ok(Math.abs(named.at[1] - middle[1]) > 20 || Math.abs(named.at[0] - middle[0]) > 20, 'it is clear of the cross');
});

test('a name is printed once, whether its seed, its record or the ring names it', () => {
  const view = fit(item.map.bbox, size);
  const texts = (layers, asked) => drawList({ layers, view, size, item: asked }).filter((one) => one.op === 'text').map((one) => one.text);
  const seed = all.seeds.features.find((feature) => feature.properties.name === 'Alderwick');
  const at = seed.geometry.coordinates;
  const area = { ...item, picks: ['Alderwick'], map: { ...item.map, focus: { area: 'syn-n0007', at: [at[0] + 0.004, at[1]] } } };
  assert.deepEqual(texts({ seeds: all.seeds }, area).filter((text) => text === 'Alderwick'), ['Alderwick'], 'the seed names it');
  const named = layer('names', 'quillhaven', [{ type: 'Feature', id: 'syn-r1', properties: { name: 'Alderwick', kind: 'Hamlet' }, geometry: { type: 'Point', coordinates: area.map.focus.at } }]);
  assert.deepEqual(texts({ names: named }, area), ['Alderwick'], 'the ring names it, and the point under the ring does not name it again');
  assert.deepEqual(texts({ records: all.records }, area), ['Alderwick (synthetic)'], 'the record names it');
  const twice = texts({ centres: all.centres, seeds: all.seeds }, area).filter((text) => text === 'Alderwick');
  assert.deepEqual(twice, ['Alderwick'], 'an area whose town centre has its name is named at its seed alone');
});

test('an area is named at its seed, and in its middle where there is no seed', () => {
  const view = fit(item.map.bbox, size);
  const texts = (layers) => drawList({ layers, view, size, item }).filter((one) => one.op === 'text').map((one) => one.text);
  assert.deepEqual(texts({ areas: all.areas }), ['Alderwick', 'Thrushcombe']);
  assert.deepEqual(texts({ areas: all.areas, seeds: all.seeds }), ['Alderwick', 'Thrushcombe']);
  assert.equal(drawList({ layers: { areas: all.areas, seeds: all.seeds }, view, size, item }).filter((one) => one.op === 'dot').length, 2);
});

test('a ward and a town centre are named, after every area', () => {
  const view = fit(item.map.bbox, size);
  const list = drawList({ layers: { wards: all.wards, centres: all.centres, seeds: all.seeds }, view, size, item });
  assert.deepEqual(list.filter((one) => one.op === 'text').map((one) => one.text), ['Alderwick', 'Thrushcombe', 'Alderwick and Thrushcombe']);
});

// The box a label takes on the canvas, as the map reckons it.
function boxOfLabel(one) {
  const wide = one.text.length * one.size * 0.58 + 8;
  const tall = one.size + 6;
  return [one.at[0] - wide / 2, one.at[1] - tall / 2, one.at[0] + wide / 2, one.at[1] + tall / 2];
}

function overlap(a, b) {
  return a[0] <= b[2] && a[2] >= b[0] && a[1] <= b[3] && a[3] >= b[1];
}

test('a label that would lie over another is left out, the more important kept', () => {
  const view = fit(item.map.bbox, size);
  const crowd = { wards: layer('wards', 'quillhaven', [LAYERS['quillhaven/wards'].features[0], { ...LAYERS['quillhaven/wards'].features[0], id: 'syn-w02', properties: { name: 'Another ward' } }]) };
  const list = drawList({ layers: crowd, view, size, item });
  assert.deepEqual(list.filter((one) => one.op === 'text').map((one) => one.text), ['Alderwick and Thrushcombe']);
});

test('the name of an area is moved clear of another name, and is not left out', () => {
  // At the desk two flagged areas of a borough had no name at all: each name
  // would have lain over another, and was dropped.
  const crowd = layer('seeds', 'quillhaven', [
    { type: 'Feature', id: 's1', properties: { area: 'syn-n0012', name: 'Thrushcombe' }, geometry: { type: 'Point', coordinates: [0.01, 0.01] } },
    { type: 'Feature', id: 's2', properties: { area: 'syn-n0007', name: 'Alderwick' }, geometry: { type: 'Point', coordinates: [0.01001, 0.01] } },
  ]);
  const list = drawList({ layers: { seeds: crowd }, view: fit(item.map.bbox, size), size, item });
  const texts = list.filter((one) => one.op === 'text');
  assert.deepEqual(texts.map((one) => one.text), ['Alderwick', 'Thrushcombe'], 'the name the item is about is placed first');
  assert.equal(overlap(boxOfLabel(texts[0]), boxOfLabel(texts[1])), false);
});

test('no name lies under the cross', () => {
  // At the desk the name of the borough was struck through by the cross, and
  // the name of a record lay across the point it marks.
  const view = fit(item.map.bbox, size);
  const middle = toGround(view, size, [400, 300]);
  const borough = { id: 'quillhaven', group: 'all', title: 'Quillhaven', map: { bbox: item.map.bbox, focus: 'quillhaven', layers: ['boroughs'] } };
  const named = { ...item, picks: ['Alderwick'] };
  const record = layer('records', 'quillhaven', [{ type: 'Feature', id: 'syn-e01', properties: { source_id: 'synthetic', as_written: 'Alderwick' }, geometry: { type: 'Point', coordinates: middle } }]);
  const cross = [400 - 18, 300 - 18, 400 + 18, 300 + 18];
  for (const [layers, about] of [[{ boroughs: all.boroughs }, borough], [{ records: record }, named], [{ seeds: all.seeds, records: record }, named]]) {
    const list = drawList({ layers, view, size, item: about, cross: true });
    const texts = list.filter((one) => one.op === 'text');
    assert.ok(texts.length > 0);
    for (const one of texts) assert.equal(overlap(boxOfLabel(one), cross), false, one.text);
    const clear = drawList({ layers, view, size, item: about }).filter((one) => one.op === 'text');
    assert.deepEqual(clear.map((one) => one.text), texts.map((one) => one.text), 'the cross takes no name off the map');
  }
});

test('no text smaller than 16 pixels is drawn on the map', () => {
  const view = zoomBy(fit(item.map.bbox, size), size, 4);
  const list = drawList({ layers: all, view, size, item });
  const sizes = list.filter((one) => one.op === 'text').map((one) => one.size);
  assert.ok(sizes.length > 0);
  assert.ok(sizes.every((n) => n >= 16));
});

test('a small road and its name wait until the map is close', () => {
  const lane = layer('roads', 'quillhaven', [{ type: 'Feature', id: 'r', properties: { class: 'Unclassified', name: 'Mill Lane' }, geometry: { type: 'LineString', coordinates: [[0, 0.01], [0.02, 0.01]] } }]);
  const fitted = fit(item.map.bbox, size);
  const texts = (view) => drawList({ layers: { roads: lane }, view, size, item }).filter((one) => one.op === 'text').length;
  assert.equal(texts(fitted), 0);
  assert.equal(texts(zoomBy(fitted, size, 2)), 1);
  const lines = drawList({ layers: { roads: lane }, view: zoomBy(fitted, size, 0.5), size, item }).filter((one) => one.op === 'lines');
  assert.equal(lines.length, 0);
});

test('every road of one width is drawn in one stroke, the widest last', () => {
  const many = layer('roads', 'quillhaven', Array.from({ length: 300 }, (_, i) => ({
    type: 'Feature',
    id: `syn-rd${i}`,
    properties: { class: i % 3 === 0 ? 'A road' : i % 3 === 1 ? 'B road' : 'Minor road', name: 'Quill Road' },
    geometry: { type: 'LineString', coordinates: [[0.0001 * (i % 100), 0.001], [0.0001 * (i % 100), 0.019]] },
  })));
  const list = drawList({ layers: { roads: many }, view: fit(item.map.bbox, size), size, item });
  const strokes = list.filter((one) => one.op === 'lines');
  assert.deepEqual(strokes.map((one) => [one.width, one.paths.length]), [[1, 100], [2, 100], [3, 100]]);
  const { ctx, calls } = recorder();
  paint(ctx, size, list);
  assert.equal(calls.filter((call) => call[0] === 'stroke').length, 3 + 2 * 0);
});

test('a road of many lengths is named once', () => {
  const lengths = layer('roads', 'quillhaven', [0.002, 0.008, 0.014].map((lon, i) => ({
    type: 'Feature',
    id: `syn-rd${i}`,
    properties: { class: 'A road', name: 'Quill Road' },
    geometry: { type: 'LineString', coordinates: [[lon, 0.002 + 0.006 * i], [lon + 0.004, 0.002 + 0.006 * i]] },
  })));
  const list = drawList({ layers: { roads: lengths }, view: fit(item.map.bbox, size), size, item });
  assert.deepEqual(list.filter((one) => one.op === 'text').map((one) => one.text), ['Quill Road']);
});

test('the cross is drawn in the middle only where a cell can be moved', () => {
  const view = fit(item.map.bbox, size);
  assert.equal(drawList({ layers: all, view, size, item }).some((one) => one.op === 'cross'), false);
  const list = drawList({ layers: all, view, size, item, cross: true });
  assert.deepEqual(list.at(-1).at, [400, 300]);
});

test('the text on the map can be read on every colour of area, light and dark', () => {
  for (const dark of [false, true]) {
    const theme = themeOf(dark);
    assert.ok(contrast(theme.ink, theme.paper) >= 7, `ink on paper, ${dark ? 'dark' : 'light'}`);
    for (let i = 0; i < 12; i += 1) {
      assert.ok(contrast(theme.ink, areaColour(i, dark)) >= 7, `ink on area ${i}, ${dark ? 'dark' : 'light'}`);
    }
  }
});

test('the twelve colours of areas all differ', () => {
  for (const dark of [false, true]) {
    assert.equal(new Set(Array.from({ length: 12 }, (_, i) => areaColour(i, dark))).size, 12);
  }
  assert.equal(areaColour(12, false), areaColour(0, false));
  assert.equal(areaColour(-1, false), areaColour(11, false));
});

// ---------------------------------------------------------------- on the canvas

function recorder() {
  const calls = [];
  const ctx = new Proxy({}, {
    get: (target, name) => (name in target ? target[name] : (...args) => { calls.push([name, ...args]); }),
    set: (target, name, value) => { target[name] = value; calls.push(['set', name, value]); return true; },
  });
  return { ctx, calls };
}

test('everything in the list is put on the canvas and the canvas is left as it was found', () => {
  const { ctx, calls } = recorder();
  const list = drawList({ layers: all, view: zoomBy(fit(item.map.bbox, size), size, 2), size, item, cross: true, hand: { cell: 'syn-oa-0001', area: 'syn-n0007' } });
  paint(ctx, size, list);
  const names = new Set(calls.map((call) => call[0]));
  for (const name of ['fillRect', 'fill', 'stroke', 'fillText', 'strokeText', 'arc', 'clip', 'save', 'restore']) assert.ok(names.has(name), name);
  assert.equal(ctx.globalAlpha, 1);
  assert.equal(calls.filter((call) => call[0] === 'save').length, calls.filter((call) => call[0] === 'restore').length);
});

test('a name from a file reaches the canvas as text and as nothing else', () => {
  const { ctx, calls } = recorder();
  const nasty = '<img src=x onerror=alert(1)>';
  const seeds = layer('seeds', 'quillhaven', [{ type: 'Feature', id: 's', properties: { area: 'syn-n0007', name: nasty }, geometry: { type: 'Point', coordinates: [0.01, 0.01] } }]);
  paint(ctx, size, drawList({ layers: { seeds }, view: fit(item.map.bbox, size), size, item }));
  assert.deepEqual(calls.filter((call) => call[0] === 'fillText').map((call) => call[1]), [nasty]);
});

// ---------------------------------------------------------------- in words

test('the map is said in words for a person who cannot see it', () => {
  const words = describe({ layers: all, item, moves: [] });
  assert.equal(words, 'Map of Alderwick, Quillhaven. 2 cells are in it. Beside it: Thrushcombe. Shown: cells, roads, wards, centres, boroughs, areas, records, seeds, names.');
});

test('the words say what was moved and what could not be drawn', () => {
  const words = describe({
    layers: { cells },
    item,
    moves: [{ n: 1, part: 'syn-oa-0001', detail: { from: 'syn-n0007', to: 'syn-n0012' } }],
    refused: ['roads is not drawn: it names no source.'],
  });
  assert.match(words, /1 cell is in it\./);
  assert.match(words, /1 cell has been moved\./);
  assert.match(words, /roads is not drawn: it names no source\.$/);
});

test('with nothing to draw the words say so', () => {
  assert.equal(describe({ layers: {}, item }), 'No map is drawn for Alderwick, Quillhaven.');
});

test('an area is named as a layer names it, and by its id where none does', () => {
  assert.equal(nameOf(all, 'syn-n0007'), 'Alderwick');
  assert.equal(nameOf({ seeds: all.seeds }, 'syn-n0012'), 'Thrushcombe');
  assert.equal(nameOf({}, 'syn-n0099'), 'syn-n0099');
});

test('the box round a shape is worked out from every point of it', () => {
  assert.deepEqual(boxOf(cells.features[0]), [0, 0, 0.01, 0.01]);
});
