import type { Suburb } from "@/core/api/schemas";

export const DEFAULT_SUBURBS: readonly string[] = [
  "Entumbane",
  "Hillside",
  "Kumalo",
  "Luveve",
  "Njube",
  "Nkulumane",
];

export const DEFAULT_SUBURB_COORDS: readonly Suburb[] = [
  { name: "Entumbane", latitude: -20.22, longitude: 28.55 },
  { name: "Hillside", latitude: -20.185, longitude: 28.63 },
  { name: "Kumalo", latitude: -20.175, longitude: 28.645 },
  { name: "Luveve", latitude: -20.155, longitude: 28.53 },
  { name: "Njube", latitude: -20.197, longitude: 28.542 },
  { name: "Nkulumane", latitude: -20.205, longitude: 28.53 },
];

/**
 * Combines backend suburb coordinates with the seeded pilot centroids so
 * GPS nearest-suburb detection works even offline or before the list loads.
 */
export function mergeSuburbCoords(serverSuburbs: readonly Suburb[] | undefined): Suburb[] {
  const seen = new Map<string, Suburb>();
  for (const item of DEFAULT_SUBURB_COORDS) {
    seen.set(item.name.toLowerCase(), item);
  }
  for (const item of serverSuburbs ?? []) {
    const trimmed = item.name.trim();
    if (trimmed !== "" && Number.isFinite(item.latitude) && Number.isFinite(item.longitude)) {
      seen.set(trimmed.toLowerCase(), {
        name: trimmed,
        latitude: item.latitude,
        longitude: item.longitude,
      });
    }
  }
  return [...seen.values()].sort((a, b) => a.name.localeCompare(b.name));
}

/** Great-circle distance in kilometres between two WGS84 coordinates. */
export function haversineKm(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const toRad = (deg: number): number => (deg * Math.PI) / 180;
  const r = 6371;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  return 2 * r * Math.asin(Math.min(1, Math.sqrt(a)));
}

/**
 * Finds the closest suburb centroid to a device GPS reading (`latitude`, `longitude`).
 */
export function findNearestSuburb(
  latitude: number,
  longitude: number,
  serverSuburbs?: readonly Suburb[],
): { suburb: string; distanceKm: number } {
  const candidates = mergeSuburbCoords(serverSuburbs);
  let bestSuburb = candidates[0]?.name ?? "Hillside";
  let bestKm = Number.POSITIVE_INFINITY;

  for (const item of candidates) {
    const km = haversineKm(latitude, longitude, item.latitude, item.longitude);
    if (km < bestKm) {
      bestKm = km;
      bestSuburb = item.name;
    }
  }

  return {
    suburb: bestSuburb,
    distanceKm: Number.isFinite(bestKm) ? Math.round(bestKm * 10) / 10 : 0,
  };
}

/**
 * Combines backend suburbs with the seeded pilot list so the dropdown works
 * immediately even before the network finishes or while offline.
 */
export function mergeSuburbs(serverSuburbs: readonly Suburb[] | undefined): string[] {
  const seen = new Map<string, string>();
  for (const name of DEFAULT_SUBURBS) {
    seen.set(name.toLowerCase(), name);
  }
  for (const item of serverSuburbs ?? []) {
    const trimmed = item.name.trim();
    if (trimmed !== "") {
      seen.set(trimmed.toLowerCase(), trimmed);
    }
  }
  return [...seen.values()].sort((a, b) => a.localeCompare(b));
}

/** Standard Levenshtein edit distance for close-match typo tolerance ("Khumalo" -> "Kumalo"). */
function editDistance(a: string, b: string): number {
  if (a === b) return 0;
  if (a.length === 0) return b.length;
  if (b.length === 0) return a.length;

  const prev = Array.from({ length: b.length + 1 }, (_, index) => index);
  const curr = new Array<number>(b.length + 1).fill(0);

  for (let i = 1; i <= a.length; i += 1) {
    curr[0] = i;
    for (let j = 1; j <= b.length; j += 1) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      curr[j] = Math.min((curr[j - 1] ?? i) + 1, (prev[j] ?? j) + 1, (prev[j - 1] ?? 0) + cost);
    }
    for (let j = 0; j <= b.length; j += 1) {
      prev[j] = curr[j] ?? 0;
    }
  }
  return prev[b.length] ?? a.length;
}

/** True when all characters of `needle` appear in order inside `haystack`. */
function isSubsequence(needle: string, haystack: string): boolean {
  let index = 0;
  for (let i = 0; i < haystack.length && index < needle.length; i += 1) {
    if (haystack[i] === needle[index]) index += 1;
  }
  return index === needle.length;
}

/**
 * Scores how closely a suburb matches what the user is typing (0 = no match).
 * Higher scores appear first in the dropdown so predictions narrow down to the
 * right match as the user types.
 */
export function suburbMatchScore(query: string, suburb: string): number {
  const q = query.trim().toLowerCase();
  const s = suburb.trim().toLowerCase();
  if (q === "" || s === "") return 0;
  if (s === q) return 100;
  if (s.startsWith(q)) return 85 + Math.round((q.length / s.length) * 10);

  const words = s.split(/\s+/);
  if (words.some((word) => word.startsWith(q))) return 75;
  if (q.length >= 2 && s.includes(q)) return 65;

  if (q.length >= 2) {
    const prefixTarget = s.slice(0, Math.min(s.length, q.length + 1));
    const prefixDist = editDistance(q, prefixTarget);
    const fullDist = editDistance(q, s);
    const minDist = Math.min(prefixDist, fullDist);
    const maxAllowed = q.length >= 4 ? 2 : 1;
    if (minDist <= maxAllowed) {
      return 55 - minDist * 10;
    }
    if (isSubsequence(q, s)) {
      return 25;
    }
  }
  return 0;
}

/**
 * Returns suburbs ranked by closeness to `query`. When `query` is empty,
 * returns the full list so the dropdown works as a standard picker too.
 */
export function matchSuburbs(
  query: string,
  availableSuburbs: readonly string[] = DEFAULT_SUBURBS,
): string[] {
  const trimmed = query.trim();
  if (trimmed === "") return [...availableSuburbs];

  return availableSuburbs
    .map((suburb) => ({ suburb, score: suburbMatchScore(trimmed, suburb) }))
    .filter((entry) => entry.score > 0)
    .sort((a, b) => b.score - a.score || a.suburb.localeCompare(b.suburb))
    .map((entry) => entry.suburb);
}

/** Top close-match suburb prediction for autofill while typing. */
export function predictSuburb(
  query: string,
  availableSuburbs: readonly string[] = DEFAULT_SUBURBS,
): string | null {
  if (query.trim() === "") return null;
  return matchSuburbs(query, availableSuburbs)[0] ?? null;
}

/**
 * Resolves a picked or written-in suburb for `POST /jobs/request`:
 * - Known suburbs (case-insensitive) use their canonical name.
 * - Custom write-in suburbs fall back to the closest known suburb for the
 *   backend FK constraint while preserving the written-in suburb in `address`.
 */
export function resolveSuburbForJob(
  typedSuburb: string,
  address: string,
  availableSuburbs: readonly string[] = DEFAULT_SUBURBS,
): { suburb: string; address: string } {
  const cleanSuburb = typedSuburb.trim();
  const cleanAddress = address.trim();
  const exact = availableSuburbs.find((item) => item.toLowerCase() === cleanSuburb.toLowerCase());
  if (exact !== undefined) {
    return { suburb: exact, address: cleanAddress };
  }
  const fallback =
    predictSuburb(cleanSuburb, availableSuburbs) ?? availableSuburbs[0] ?? "Hillside";
  const combinedAddress =
    cleanSuburb !== "" && !cleanAddress.toLowerCase().includes(cleanSuburb.toLowerCase())
      ? `${cleanAddress}, ${cleanSuburb}`
      : cleanAddress;
  return { suburb: fallback, address: combinedAddress };
}
