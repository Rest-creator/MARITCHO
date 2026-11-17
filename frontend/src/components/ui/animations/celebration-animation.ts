import {
  animated,
  composition,
  ellipse,
  fill,
  group,
  hex,
  polyline,
  shapeLayer,
  still,
  stroke,
  transform,
  trim,
  type LottieAnimation,
  type ShapeLayer,
} from "@/core/motion/lottie-builders";

/**
 * Badge-unlock burst, 160×160 @ 30 fps, played once (~1.8 s):
 *   0–14   badge pops in with a small overshoot
 *   10–22  tick draws in
 *   8–26   rays shoot out and vanish
 *   4–30   halo ring expands and fades
 *   10–36  sparkles drift outward and fade
 * Marker "settle" (frame 36) is the resting frame for a static still.
 */
export const CELEBRATION_FRAMES = 54;
export const CELEBRATION_REST_FRAME = 36;

const SIZE = 160;
const CENTER: [number, number, number] = [SIZE / 2, SIZE / 2, 0];
const BADGE = 76;
const RAYS = 8;
const SPARKLES = 6;

const BRAND = hex("#00abe3"); // --brand-cyan
const LIGHT = hex("#67d6fa"); // --amber-lighter
const WHITE = hex("#ffffff");

function tickLayer(): ShapeLayer {
  return shapeLayer({
    index: 0,
    name: "tick",
    inPoint: 0,
    outPoint: CELEBRATION_FRAMES,
    position: still(CENTER),
    shapes: [
      group("tick", [
        polyline([
          [-15, 1],
          [-4, 12],
          [17, -11],
        ]),
        stroke(WHITE, 7),
        trim(
          still(0),
          animated([
            [10, 0],
            [22, 100],
          ]),
        ),
      ]),
    ],
  });
}

function badgeLayer(): ShapeLayer {
  return shapeLayer({
    index: 0,
    name: "badge",
    inPoint: 0,
    outPoint: CELEBRATION_FRAMES,
    position: still(CENTER),
    scale: animated([
      [0, [0, 0, 100]],
      [9, [118, 118, 100]],
      [14, [100, 100, 100]],
    ]),
    shapes: [
      group("badge-rim", [ellipse(BADGE), stroke(WHITE, 3, 28)]),
      group("badge-fill", [ellipse(BADGE), fill(BRAND)]),
    ],
  });
}

function raysLayer(): ShapeLayer {
  return shapeLayer({
    index: 0,
    name: "rays",
    inPoint: 0,
    outPoint: CELEBRATION_FRAMES,
    position: still(CENTER),
    shapes: Array.from({ length: RAYS }, (_, ray) =>
      group(
        `ray-${ray}`,
        [
          polyline([
            [0, -50],
            [0, -72],
          ]),
          stroke(LIGHT, 5),
          trim(
            animated([
              [13, 0],
              [24, 100],
            ]),
            animated([
              [8, 0],
              [18, 100],
            ]),
          ),
        ],
        transform({ rotation: still((360 / RAYS) * ray) }),
      ),
    ),
  });
}

function haloLayer(): ShapeLayer {
  return shapeLayer({
    index: 0,
    name: "halo",
    inPoint: 0,
    outPoint: CELEBRATION_FRAMES,
    position: still(CENTER),
    scale: animated([
      [4, [80, 80, 100]],
      [30, [190, 190, 100]],
    ]),
    opacity: animated([
      [4, 0],
      [6, 80],
      [30, 0],
    ]),
    shapes: [group("halo", [ellipse(BADGE), stroke(BRAND, 4)])],
  });
}

function sparklesLayer(): ShapeLayer {
  return shapeLayer({
    index: 0,
    name: "sparkles",
    inPoint: 0,
    outPoint: CELEBRATION_FRAMES,
    position: still(CENTER),
    shapes: Array.from({ length: SPARKLES }, (_, sparkle) => {
      const angle: number = ((360 / SPARKLES) * sparkle + 30) * (Math.PI / 180);
      // `+ 0` turns -0 into 0 so the data survives a JSON round-trip unchanged.
      const at = (radius: number): number[] => [
        Math.round(Math.cos(angle) * radius * 10) / 10 + 0,
        Math.round(Math.sin(angle) * radius * 10) / 10 + 0,
      ];
      return group(
        `sparkle-${sparkle}`,
        [ellipse(7), fill(WHITE)],
        transform({
          position: animated([
            [10, at(40)],
            [34, at(78)],
          ]),
          opacity: animated([
            [0, 0],
            [10, 0],
            [12, 100],
            [22, 100],
            [36, 0],
          ]),
        }),
      );
    }),
  });
}

export function buildCelebrationAnimation(): LottieAnimation {
  return composition({
    name: "maritcho-celebration",
    width: SIZE,
    height: SIZE,
    frames: CELEBRATION_FRAMES,
    layers: [tickLayer(), badgeLayer(), raysLayer(), haloLayer(), sparklesLayer()],
    markers: [
      { tm: 0, dr: CELEBRATION_REST_FRAME, cm: "burst" },
      { tm: CELEBRATION_REST_FRAME, dr: 0, cm: "settle" },
    ],
  });
}
