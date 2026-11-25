import "server-only";

import { cache } from "react";
import { headers } from "next/headers";

import { jobShareSchema, type JobShare } from "@/core/api/schemas";
import { backendFetch } from "@/server/backend";
import { BACKEND_ROUTES } from "@/server/backend-routes";

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export type JobShareResult =
  { kind: "found"; job: JobShare } | { kind: "missing" } | { kind: "unavailable" };

/**
 * The public teaser for a shared job link. Cached per request, so the page,
 * its metadata and its preview image share one backend call.
 */
export const getJobShare = cache(async (jobId: string): Promise<JobShareResult> => {
  if (!UUID_PATTERN.test(jobId)) return { kind: "missing" };
  const path = BACKEND_ROUTES.jobShare.path.replace("{job_id}", encodeURIComponent(jobId));
  try {
    const response = await backendFetch(path, { headers: { accept: "application/json" } });
    if (response.status === 404 || response.status === 422) return { kind: "missing" };
    if (!response.ok) return { kind: "unavailable" };
    const parsed = jobShareSchema.safeParse(await response.json());
    return parsed.success ? { kind: "found", job: parsed.data } : { kind: "unavailable" };
  } catch {
    return { kind: "unavailable" };
  }
});

/**
 * This site's public origin, for absolute preview URLs (LinkedIn and WhatsApp
 * ignore relative og:image paths). Taken from the proxy's forwarded headers,
 * so it is right behind Caddy without extra configuration.
 */
export async function publicOrigin(): Promise<string> {
  const configured = process.env.MARICHO_PUBLIC_URL;
  if (configured) return configured.replace(/\/+$/, "");
  const incoming = await headers();
  const host = incoming.get("x-forwarded-host") ?? incoming.get("host") ?? "localhost:3000";
  const proto =
    incoming.get("x-forwarded-proto") ?? (host.startsWith("localhost") ? "http" : "https");
  return `${proto.split(",")[0]?.trim() ?? "https"}://${host.split(",")[0]?.trim() ?? host}`;
}
