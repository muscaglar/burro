/**
 * The map library, with the style sheet it needs. It is loaded only when a
 * map is about to be drawn, so a page with no map, or a browser that cannot
 * draw one, never fetches it.
 */

import "maplibre-gl/dist/maplibre-gl.css";

import { Map, Marker } from "maplibre-gl";

export { Map, Marker };
