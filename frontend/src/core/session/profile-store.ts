import { useSyncExternalStore } from "react";
import { z } from "zod";

import { gradeSchema } from "@/core/api/schemas";

/*
 * On-device profile details the backend does not (yet) store: the display
 * name typed at sign-up, the worker's availability switch and travel
 * radius. Nothing sensitive lives here — the session token is an httpOnly
 * cookie the page cannot read.
 */

const STORAGE_KEY = "maricho-profile";

const profileSchema = z.object({
  name: z.string().max(80).default(""),
  phone: z.string().max(20).default(""),
  isAvailable: z.boolean().default(true),
  travelKm: z.number().int().min(1).max(50).default(10),
  homeSuburb: z.string().max(100).default(""),
  /** Last job address a buyer used, offered as the default next time. */
  lastAddress: z.string().max(500).default(""),
  lastSuburb: z.string().max(100).default(""),
  /** Next-of-kin / emergency contact phone number (+263). */
  nextOfKinPhone: z.string().max(20).default(""),
  /** Preferred settlement currency for jobs/deposits (ADR-002). */
  preferredCurrency: z.enum(["USD", "ECOCASH", "ZWG"]).default("USD"),
  /** Default landmark narrative for employer job postings (ADR-004). */
  defaultLandmark: z.string().max(300).default(""),
  /** Primary transport mode for workers ("Walking", "Kombi / bus", etc.). */
  travelMeans: z.string().max(50).default(""),
  /** Short trade summary or work note kept on device. */
  bio: z.string().max(240).default(""),
  /** Highest worker tier this phone has already celebrated, so each unlock plays once. */
  celebratedGrade: gradeSchema.default("REGISTERED"),
});

export type LocalProfile = z.infer<typeof profileSchema>;

export const EMPTY_PROFILE: LocalProfile = profileSchema.parse({});

const listeners = new Set<() => void>();
let cached: LocalProfile | null = null;

function read(): LocalProfile {
  if (cached !== null) {
    return cached;
  }
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    const parsed = profileSchema.safeParse(raw === null ? {} : JSON.parse(raw));
    cached = parsed.success ? parsed.data : EMPTY_PROFILE;
  } catch {
    cached = EMPTY_PROFILE;
  }
  return cached;
}

export function updateProfile(patch: Partial<LocalProfile>): void {
  const next = profileSchema.parse({ ...read(), ...patch });
  cached = next;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  } catch {
    // Storage blocked (private mode / quota): keep the in-memory copy.
  }
  listeners.forEach((listener) => listener());
}

/** Test hook: forget the in-memory copy so the next read hits storage. */
export function resetProfileCache(): void {
  cached = null;
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function useLocalProfile(): LocalProfile {
  return useSyncExternalStore(subscribe, read, () => EMPTY_PROFILE);
}
