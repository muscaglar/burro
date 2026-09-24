// Layers of a made-up city, for the page's tests. Four cells in a square, in
// open sea at the equator. Every name is made up and every id begins `syn-`.

export function layer(name, group, features, desk = {}) {
  return {
    type: 'FeatureCollection',
    desk: { layer: name, group, source_ids: ['synthetic'], synthetic: true, ...desk },
    features,
  };
}

function square(id, west, south, properties) {
  const east = west + 0.01;
  const north = south + 0.01;
  return {
    type: 'Feature',
    id,
    properties,
    geometry: { type: 'Polygon', coordinates: [[[west, south], [east, south], [east, north], [west, north], [west, south]]] },
  };
}

function box(id, west, south, east, north, properties) {
  return {
    type: 'Feature',
    id,
    properties,
    geometry: { type: 'Polygon', coordinates: [[[west, south], [east, south], [east, north], [west, north], [west, south]]] },
  };
}

function point(id, lon, lat, properties) {
  return { type: 'Feature', id, properties, geometry: { type: 'Point', coordinates: [lon, lat] } };
}

export const LAYERS = {
  'quillhaven/cells': layer('cells', 'quillhaven', [
    square('syn-oa-0001', 0, 0, { area: 'syn-n0007', colour: 2, borough: 'Quillhaven' }),
    square('syn-oa-0002', 0.01, 0, { area: 'syn-n0007', colour: 2, borough: 'Quillhaven' }),
    square('syn-oa-0003', 0, 0.01, { area: 'syn-n0012', colour: 5, borough: 'Quillhaven' }),
    square('syn-oa-0004', 0.01, 0.01, { area: 'syn-n0012', colour: 5, borough: 'Quillhaven' }),
  ]),
  'quillhaven/areas': layer('areas', 'quillhaven', [
    box('syn-n0007', 0, 0, 0.02, 0.01, { name: 'Alderwick' }),
    box('syn-n0012', 0, 0.01, 0.02, 0.02, { name: 'Thrushcombe' }),
  ]),
  'quillhaven/wards': layer('wards', 'quillhaven', [box('syn-w01', 0, 0, 0.02, 0.02, { name: 'Alderwick and Thrushcombe' })]),
  'quillhaven/centres': layer('centres', 'quillhaven', [box('syn-t01', 0.004, 0.004, 0.008, 0.008, { name: 'Alderwick', class: 'district' })]),
  'quillhaven/roads': layer('roads', 'quillhaven', [
    { type: 'Feature', id: 'syn-r01', properties: { class: 'A Road', name: 'Quill Road' }, geometry: { type: 'LineString', coordinates: [[0, 0.01], [0.02, 0.01]] } },
    { type: 'Feature', id: 'syn-r02', properties: { class: 'Unclassified', name: 'Mill Lane' }, geometry: { type: 'MultiLineString', coordinates: [[[0.01, 0], [0.01, 0.02]]] } },
  ]),
  'quillhaven/names': layer('names', 'quillhaven', [point('syn-g01', 0.015, 0.004, { name: 'Alder Bridge', kind: 'other' })]),
  'quillhaven/seeds': layer('seeds', 'quillhaven', [
    point('syn-s07', 0.006, 0.006, { area: 'syn-n0007', name: 'Alderwick' }),
    point('syn-s12', 0.014, 0.016, { area: 'syn-n0012', name: 'Thrushcombe' }),
  ]),
  'quillhaven/records': layer('records', 'quillhaven', [point('syn-e01', 0.005, 0.0045, { source_id: 'synthetic', as_written: 'Alderwick' })]),
  'all/boroughs': layer('boroughs', 'all', [box('quillhaven', 0, 0, 0.02, 0.02, { name: 'Quillhaven' })]),
};
