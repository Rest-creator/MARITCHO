/**
 * Builds Theatre.js project state (the JSON Theatre Studio exports) from
 * compact `[seconds, value]` keyframe lists, and evaluates the same lists
 * without Theatre for static fallbacks. Format verified against
 * @theatre/core 0.7.2: definitionVersion "0.4.0", prop paths JSON-encoded,
 * bezier segment = cubic-bezier(left.handles[2..3], right.handles[0..1]).
 */

export type KeyframeTrack = ReadonlyArray<readonly [seconds: number, value: number]>;

interface TheatreKeyframe {
  id: string;
  position: number;
  value: number;
  handles: [number, number, number, number];
  connectedRight: boolean;
  type: "bezier";
}

interface TheatreTrack {
  type: "BasicKeyframedTrack";
  __debugName: string;
  keyframes: TheatreKeyframe[];
}

interface TheatreObjectTracks {
  trackIdByPropPath: Record<string, string>;
  trackData: Record<string, TheatreTrack>;
}

export interface TheatreProjectState {
  sheetsById: Record<
    string,
    {
      staticOverrides: { byObject: Record<string, never> };
      sequence: {
        type: "PositionalSequence";
        length: number;
        subUnitsPerUnit: number;
        tracksByObject: Record<string, TheatreObjectTracks>;
      };
    }
  >;
  definitionVersion: "0.4.0";
  revisionHistory: string[];
}

/** Every segment eases out: cubic-bezier(0.2, 0.8, 0.2, 1). */
const EASE_OUT_HANDLES: [number, number, number, number] = [0.2, 1, 0.2, 0.8];

export function buildTheatreState(options: {
  sheetId: string;
  length: number;
  objects: Record<string, Partial<Record<string, KeyframeTrack>>>;
}): TheatreProjectState {
  const tracksByObject: Record<string, TheatreObjectTracks> = {};
  for (const [objectKey, tracks] of Object.entries(options.objects)) {
    const objectTracks: TheatreObjectTracks = { trackIdByPropPath: {}, trackData: {} };
    for (const [prop, track] of Object.entries(tracks)) {
      if (track === undefined || track.length === 0) continue;
      const trackId = `${objectKey}.${prop}`;
      objectTracks.trackIdByPropPath[JSON.stringify([prop])] = trackId;
      objectTracks.trackData[trackId] = {
        type: "BasicKeyframedTrack",
        __debugName: `${objectKey}:${JSON.stringify([prop])}`,
        keyframes: track.map(([position, value], index) => ({
          id: `${trackId}.${index}`,
          position,
          value,
          handles: EASE_OUT_HANDLES,
          connectedRight: index < track.length - 1,
          type: "bezier",
        })),
      };
    }
    tracksByObject[objectKey] = objectTracks;
  }
  return {
    sheetsById: {
      [options.sheetId]: {
        staticOverrides: { byObject: {} },
        sequence: {
          type: "PositionalSequence",
          length: options.length,
          subUnitsPerUnit: 30,
          tracksByObject,
        },
      },
    },
    definitionVersion: "0.4.0",
    revisionHistory: [],
  };
}

/**
 * Value of a track at `seconds`, like Theatre: holds the first/last value
 * outside the keyframes, linear in between (exact at keyframes and holds,
 * which is all the static fallback samples).
 */
export function valueAt(
  track: KeyframeTrack | undefined,
  seconds: number,
  fallback: number,
): number {
  if (track === undefined || track.length === 0) return fallback;
  const first = track[0];
  const last = track[track.length - 1];
  if (first === undefined || last === undefined) return fallback;
  if (seconds <= first[0]) return first[1];
  if (seconds >= last[0]) return last[1];
  for (let index = 1; index < track.length; index += 1) {
    const right = track[index];
    const left = track[index - 1];
    if (right === undefined || left === undefined) continue;
    if (seconds <= right[0]) {
      const progress: number = (seconds - left[0]) / (right[0] - left[0]);
      return left[1] + (right[1] - left[1]) * progress;
    }
  }
  return last[1];
}
