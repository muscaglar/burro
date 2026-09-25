// The map of the panel: where a point falls, which area a press is in, and
// which colour an area is drawn in. Plain functions, with no browser in them.
//
// It draws the outlines of the release and nothing else: no basemap, no tiles,
// no file of any other machine. An outline is a GeoJSON Polygon or
// MultiPolygon, longitude first.

// The five bands, from the low end to the high end, as one hue from light to
// dark on a light page and from dark to light on a dark one. Each was held to
// the page it is drawn on: the step next to the page still stands out from it.
export const BANDS = {
  light: ['#86b6ef', '#5598e7', '#2a78d6', '#1c5cab', '#0d366b'],
  dark: ['#184f95', '#2a78d6', '#5598e7', '#86b6ef', '#cde2fb'],
};
// An area with no band, an area that was not found, and the line round each.
export const PLAIN = {
  light: { none: '#f0efec', found: '#2a78d6', line: '#5b606b', paper: '#fbfaf7', ink: '#14161a' },
  dark: { none: '#383835', found: '#86b6ef', line: '#8a8f99', paper: '#14161a', ink: '#f2f2ee' },
};
const PAD = 8;

// The rings of an outline: each is a list of points, and a hole is a ring too.
export function ringsOf(geometry) {
  if (!geometry || !Array.isArray(geometry.coordinates)) return [];
  if (geometry.type === 'Polygon') return geometry.coordinates;
  if (geometry.type === 'MultiPolygon') return geometry.coordinates.flat();
  return [];
}

// The box round every outline: west, south, east, north. Null where there is none.
export function boxOf(outlines) {
  let box = null;
  for (const geometry of Object.values(outlines || {})) {
    for (const ring of ringsOf(geometry)) {
      for (const [lon, lat] of ring) {
        box = box === null ? [lon, lat, lon, lat] : [Math.min(box[0], lon), Math.min(box[1], lat), Math.max(box[2], lon), Math.max(box[3], lat)];
      }
    }
  }
  return box;
}

// How the ground is laid on a canvas: flat about the middle of the box, north
// up, the whole box in view with a margin, and one scale both ways.
export function fit(box, width, height) {
  if (box === null || width <= 2 * PAD || height <= 2 * PAD) return null;
  const squeeze = Math.cos((((box[1] + box[3]) / 2) * Math.PI) / 180) || 1;
  const wide = Math.max((box[2] - box[0]) * squeeze, 1e-9);
  const high = Math.max(box[3] - box[1], 1e-9);
  const scale = Math.min((width - 2 * PAD) / wide, (height - 2 * PAD) / high);
  return {
    scale,
    squeeze,
    west: box[0],
    north: box[3],
    left: (width - wide * scale) / 2,
    top: (height - high * scale) / 2,
  };
}

export function toScreen(view, [lon, lat]) {
  return [view.left + (lon - view.west) * view.squeeze * view.scale, view.top + (view.north - lat) * view.scale];
}

export function toGround(view, [x, y]) {
  return [view.west + (x - view.left) / (view.squeeze * view.scale), view.north - (y - view.top) / view.scale];
}

function inRing(ring, [x, y]) {
  let inside = false;
  for (let at = 0, before = ring.length - 1; at < ring.length; before = at, at += 1) {
    const [ax, ay] = ring[at];
    const [bx, by] = ring[before];
    if (ay > y !== by > y && x < ((bx - ax) * (y - ay)) / (by - ay) + ax) inside = !inside;
  }
  return inside;
}

// Whether a point lies in an outline. A point in a hole lies outside it.
export function holds(geometry, point) {
  return ringsOf(geometry).filter((ring) => inRing(ring, point)).length % 2 === 1;
}

// The area a point lies in, or null. Of two that hold it, the first by its id.
export function areaAt(outlines, point) {
  for (const id of Object.keys(outlines || {}).sort()) {
    if (holds(outlines[id], point)) return id;
  }
  return null;
}

// The colour an area is drawn in. `draw` says what the map is of: the five
// bands of a vibe, or the areas that were found.
export function fillOf(draw, id, dark) {
  const mode = dark ? 'dark' : 'light';
  if (draw && draw.fill === 'bands') {
    const band = draw.bands ? draw.bands[id] : null;
    return Number.isInteger(band) && band >= 1 && band <= 5 ? BANDS[mode][band - 1] : PLAIN[mode].none;
  }
  if (draw && draw.fill === 'found' && Array.isArray(draw.ids) && draw.ids.length) {
    return draw.ids.includes(id) ? PLAIN[mode].found : PLAIN[mode].none;
  }
  return PLAIN[mode].none;
}

// What each colour means, in words: a band is never told by its colour alone.
export function legendOf(draw, dark) {
  const mode = dark ? 'dark' : 'light';
  if (draw && draw.fill === 'bands') {
    return [...BANDS[mode].map((colour, at) => ({ colour, words: `Band ${at + 1}` })), { colour: PLAIN[mode].none, words: 'No band' }];
  }
  if (draw && draw.fill === 'found' && Array.isArray(draw.ids) && draw.ids.length) {
    return [
      { colour: PLAIN[mode].found, words: 'Found' },
      { colour: PLAIN[mode].none, words: 'Not found' },
    ];
  }
  return [];
}
