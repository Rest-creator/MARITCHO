/**
 * Worker travel settings, shared by sign-up, the Skills screen and My Account
 * so their limits can't drift apart again. The backend accepts 1–50 km
 * (`UserProfilePatch.travel_km`, ge=1 le=50).
 */
export const MIN_TRAVEL_KM = 1;
export const MAX_TRAVEL_KM = 50;

export const TRAVEL_MEANS_OPTIONS: readonly string[] = [
  "Walking",
  "Kombi / bus",
  "Bicycle",
  "Motorbike",
  "Own vehicle",
];

export function clampTravelKm(value: number): number {
  if (!Number.isFinite(value)) return MIN_TRAVEL_KM;
  return Math.max(MIN_TRAVEL_KM, Math.min(MAX_TRAVEL_KM, Math.round(value)));
}
