/**
 * Minimal typed builders for Bodymovin/Lottie JSON (the format After Effects
 * exports). Maritcho's first animations are authored here in code so they
 * stay a few KB, use the exact brand tokens, and need no binary assets. A
 * designer's AE export can replace any of them file-for-file: the player only
 * cares that it receives a `LottieAnimation`-shaped object with the same
 * frame layout (documented next to each animation).
 */

export type Rgba = readonly [number, number, number, number];

interface Ease {
  x: number[];
  y: number[];
}

interface Keyframe {
  t: number;
  s: number[];
  o?: Ease;
  i?: Ease;
}

export type Prop = { a: 0; k: number | number[] } | { a: 1; k: Keyframe[] };

interface Bezier {
  i: number[][];
  o: number[][];
  v: number[][];
  c: boolean;
}

export interface TransformItem {
  ty: "tr";
  p: Prop;
  a: Prop;
  s: Prop;
  r: Prop;
  o: Prop;
  sk: Prop;
  sa: Prop;
}

export type ShapeItem =
  | { ty: "gr"; nm: string; it: ShapeItem[] }
  | { ty: "el"; d: 1; p: Prop; s: Prop }
  | { ty: "sh"; d: 1; ks: { a: 0; k: Bezier } }
  | { ty: "fl"; c: Prop; o: Prop; r: 1 }
  | { ty: "st"; c: Prop; o: Prop; w: Prop; lc: 2; lj: 2 }
  | { ty: "tm"; s: Prop; e: Prop; o: Prop; m: 1 }
  | TransformItem;

interface LayerTransform {
  o: Prop;
  r: Prop;
  p: Prop;
  a: Prop;
  s: Prop;
}

export interface ShapeLayer {
  ddd: 0;
  ind: number;
  ty: 4;
  nm: string;
  sr: 1;
  ks: LayerTransform;
  ao: 0;
  shapes: ShapeItem[];
  ip: number;
  op: number;
  st: 0;
  bm: 0;
}

/** AE composition marker: `tm` start frame, `dr` duration, `cm` name. */
export interface Marker {
  tm: number;
  dr: number;
  cm: string;
}

export interface LottieAnimation {
  v: string;
  nm: string;
  fr: number;
  ip: 0;
  op: number;
  w: number;
  h: number;
  ddd: 0;
  assets: [];
  layers: ShapeLayer[];
  markers: Marker[];
}

/** Material "emphasized decelerate": fast start, soft landing. */
const EASE_OUT: { o: Ease; i: Ease } = { o: { x: [0.3], y: [0] }, i: { x: [0.2], y: [1] } };

export function hex(color: string, alpha: number = 1): Rgba {
  const value: number = Number.parseInt(color.replace("#", ""), 16);
  return [((value >> 16) & 255) / 255, ((value >> 8) & 255) / 255, (value & 255) / 255, alpha];
}

export function still(value: number | readonly number[]): Prop {
  return { a: 0, k: typeof value === "number" ? value : [...value] };
}

/** Keyframes as `[frame, value]` pairs in ascending frame order. */
export function animated(
  frames: ReadonlyArray<readonly [number, number | readonly number[]]>,
): Prop {
  return {
    a: 1,
    k: frames.map(([t, value], index): Keyframe => {
      const s: number[] = typeof value === "number" ? [value] : [...value];
      return index === frames.length - 1 ? { t, s } : { t, s, ...EASE_OUT };
    }),
  };
}

export function transform(
  options: { position?: Prop; rotation?: Prop; opacity?: Prop; scale?: Prop } = {},
): TransformItem {
  return {
    ty: "tr",
    p: options.position ?? still([0, 0]),
    a: still([0, 0]),
    s: options.scale ?? still([100, 100]),
    r: options.rotation ?? still(0),
    o: options.opacity ?? still(100),
    sk: still(0),
    sa: still(0),
  };
}

export function group(name: string, items: ShapeItem[], groupTransform?: TransformItem): ShapeItem {
  return { ty: "gr", nm: name, it: [...items, groupTransform ?? transform()] };
}

export function polyline(points: ReadonlyArray<readonly [number, number]>): ShapeItem {
  const zero: number[][] = points.map(() => [0, 0]);
  return {
    ty: "sh",
    d: 1,
    ks: { a: 0, k: { i: zero, o: zero, v: points.map(([x, y]) => [x, y]), c: false } },
  };
}

export function ellipse(size: number): ShapeItem {
  return { ty: "el", d: 1, p: still([0, 0]), s: still([size, size]) };
}

export function fill(color: Rgba, opacity: number = 100): ShapeItem {
  return { ty: "fl", c: still(color), o: still(opacity), r: 1 };
}

export function stroke(color: Rgba, width: number, opacity: number = 100): ShapeItem {
  return { ty: "st", c: still(color), o: still(opacity), w: still(width), lc: 2, lj: 2 };
}

/** Trim paths: draws only the part of the path between `start`% and `end`%. */
export function trim(start: Prop, end: Prop): ShapeItem {
  return { ty: "tm", s: start, e: end, o: still(0), m: 1 };
}

export function shapeLayer(options: {
  index: number;
  name: string;
  inPoint: number;
  outPoint: number;
  shapes: ShapeItem[];
  position?: Prop;
  scale?: Prop;
  opacity?: Prop;
}): ShapeLayer {
  return {
    ddd: 0,
    ind: options.index,
    ty: 4,
    nm: options.name,
    sr: 1,
    ks: {
      o: options.opacity ?? still(100),
      r: still(0),
      p: options.position ?? still([0, 0, 0]),
      a: still([0, 0, 0]),
      s: options.scale ?? still([100, 100, 100]),
    },
    ao: 0,
    shapes: options.shapes,
    ip: options.inPoint,
    op: options.outPoint,
    st: 0,
    bm: 0,
  };
}

/** Layers are listed top-most first, as in After Effects. */
export function composition(options: {
  name: string;
  width: number;
  height: number;
  frames: number;
  layers: ShapeLayer[];
  markers?: Marker[];
}): LottieAnimation {
  return {
    v: "5.12.0",
    nm: options.name,
    fr: 30,
    ip: 0,
    op: options.frames,
    w: options.width,
    h: options.height,
    ddd: 0,
    assets: [],
    layers: options.layers.map((layer, index) => ({ ...layer, ind: index + 1 })),
    markers: options.markers ?? [],
  };
}
