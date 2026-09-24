/**
 * A stand-in for `maplibre-gl` in tests. jsdom has no WebGL, so the real
 * library cannot draw there. This one draws nothing and records what it was
 * asked to do, so that a test can say what the map was told.
 *
 * jest.config.ts puts it in place of the library for every test.
 */

type Handler = (event: Record<string, unknown>) => void;

interface Listener {
  readonly event: string;
  readonly layer: string | null;
  readonly handler: Handler;
}

export interface Recorded {
  readonly method: string;
  readonly args: readonly unknown[];
}

const maps: Map[] = [];

export class Marker {
  readonly element: HTMLElement;
  position: [number, number] | null = null;
  map: Map | null = null;

  constructor(options: { element?: HTMLElement } = {}) {
    this.element = options.element ?? document.createElement("div");
  }

  setLngLat(position: [number, number]): this {
    this.position = position;
    return this;
  }

  addTo(map: Map): this {
    this.map = map;
    map.markers.push(this);
    map.getCanvasContainer().append(this.element);
    return this;
  }

  getElement(): HTMLElement {
    return this.element;
  }

  remove(): this {
    if (this.map) this.map.markers = this.map.markers.filter((marker) => marker !== this);
    this.element.remove();
    this.map = null;
    return this;
  }
}

export class Map {
  readonly options: Record<string, unknown>;
  readonly calls: Recorded[] = [];
  readonly images = new Set<string>();
  readonly states = new globalThis.Map<string, Record<string, unknown>>();
  markers: Marker[] = [];
  removed = false;
  /** What is on screen, as the map would say it. A test may set it. */
  view: { contains: (position: unknown) => boolean } = { contains: () => true };

  private listeners: Listener[] = [];
  private readonly canvas: HTMLCanvasElement;
  private readonly canvasContainer: HTMLElement;
  private data: unknown = null;

  constructor(options: Record<string, unknown>) {
    this.options = options;
    const container = options.container as HTMLElement;
    this.canvasContainer = document.createElement("div");
    this.canvas = document.createElement("canvas");
    this.canvas.tabIndex = 0;
    this.canvasContainer.append(this.canvas);
    container.append(this.canvasContainer);
    maps.push(this);
  }

  private record(method: string, ...args: unknown[]) {
    this.calls.push({ method, args });
  }

  on(event: string, layerOrHandler: string | Handler, handler?: Handler): this {
    this.listeners.push(
      typeof layerOrHandler === "string"
        ? { event, layer: layerOrHandler, handler: handler as Handler }
        : { event, layer: null, handler: layerOrHandler },
    );
    return this;
  }

  once(event: string, handler: Handler): this {
    const once: Handler = (payload) => {
      this.off(event, once);
      handler(payload);
    };
    return this.on(event, once);
  }

  off(event: string, layerOrHandler: string | Handler, handler?: Handler): this {
    const wanted = typeof layerOrHandler === "string" ? handler : layerOrHandler;
    this.listeners = this.listeners.filter(
      (listener) => !(listener.event === event && listener.handler === wanted),
    );
    return this;
  }

  /** For a test: what the map would say had happened. */
  fire(event: string, payload: Record<string, unknown> = {}, layer: string | null = null): void {
    for (const listener of [...this.listeners]) {
      if (listener.event === event && listener.layer === layer) listener.handler(payload);
    }
  }

  getCanvas(): HTMLCanvasElement {
    return this.canvas;
  }

  getCanvasContainer(): HTMLElement {
    return this.canvasContainer;
  }

  getContainer(): HTMLElement {
    return this.options.container as HTMLElement;
  }

  isStyleLoaded(): boolean {
    return true;
  }

  hasImage(name: string): boolean {
    return this.images.has(name);
  }

  addImage(name: string, image: unknown, options?: unknown): void {
    this.images.add(name);
    this.record("addImage", name, image, options);
  }

  removeImage(name: string): void {
    this.images.delete(name);
    this.record("removeImage", name);
  }

  getSource(id: string) {
    return {
      setData: (data: unknown) => {
        this.data = data;
        this.record("setData", id, data);
      },
    };
  }

  getData(): unknown {
    return this.data;
  }

  setStyle(style: unknown): void {
    this.record("setStyle", style);
  }

  setPaintProperty(layer: string, name: string, value: unknown): void {
    this.record("setPaintProperty", layer, name, value);
  }

  setFilter(layer: string, filter: unknown): void {
    this.record("setFilter", layer, filter);
  }

  setFeatureState(feature: { source: string; id: string }, state: Record<string, unknown>): void {
    this.states.set(feature.id, { ...this.states.get(feature.id), ...state });
    this.record("setFeatureState", feature, state);
  }

  removeFeatureState(feature: { source: string; id?: string }, key?: string): void {
    if (feature.id === undefined) this.states.clear();
    else if (key === undefined) this.states.delete(feature.id);
    else {
      const { [key]: gone, ...rest } = this.states.get(feature.id) ?? {};
      void gone;
      this.states.set(feature.id, rest);
    }
    this.record("removeFeatureState", feature, key);
  }

  getBounds() {
    return this.view;
  }

  fitBounds(bounds: unknown, options?: unknown): this {
    this.record("fitBounds", bounds, options);
    return this;
  }

  panTo(position: unknown, options?: unknown): this {
    this.record("panTo", position, options);
    return this;
  }

  zoomIn(options?: unknown): this {
    this.record("zoomIn", options);
    return this;
  }

  zoomOut(options?: unknown): this {
    this.record("zoomOut", options);
    return this;
  }

  resize(): this {
    this.record("resize");
    return this;
  }

  remove(): void {
    this.removed = true;
    for (const marker of [...this.markers]) marker.remove();
    this.canvasContainer.remove();
    this.record("remove");
  }

  called(method: string): readonly (readonly unknown[])[] {
    return this.calls.filter((call) => call.method === method).map((call) => call.args);
  }
}

/** Every map made since the last reset, oldest first. */
export function mapsMade(): readonly Map[] {
  return maps;
}

export function lastMap(): Map {
  const last = maps[maps.length - 1];
  if (!last) throw new Error("No map was made.");
  return last;
}

export function forgetMaps(): void {
  maps.length = 0;
}

const maplibre = { Map, Marker };
export default maplibre;
