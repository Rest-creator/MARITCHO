import { z } from "zod";

import { ApiError, apiErrorFrom } from "@/core/api/http";

/*
 * Uploads through the BFF to the backend's media endpoint (WEB-004). The
 * contract is the one proposed in issue #1:
 *
 *   POST /media  multipart { file, kind }, Idempotency-Key header
 *     -> 201 { url, content_type, size_bytes }
 *   GET  /media  -> anything but 404 once uploads exist (405 is fine)
 */

export type MediaKind = "photo" | "voice_note";

export const uploadedMediaSchema = z.object({
  url: z.string().min(1),
  content_type: z.string(),
  size_bytes: z.number().int().nonnegative(),
});

export type UploadedMedia = z.infer<typeof uploadedMediaSchema>;

export interface UploadInput {
  file: Blob;
  kind: MediaKind;
  filename: string;
  /** Same key for every retry of the same file, so a replay can't upload it twice. */
  idempotencyKey: string;
}

/** The backend has no upload endpoint yet. */
export function isUploadUnavailable(error: unknown): boolean {
  return (
    error instanceof ApiError &&
    (error.status === 404 || error.status === 405 || error.status === 501)
  );
}

export async function uploadMedia({
  file,
  kind,
  filename,
  idempotencyKey,
}: UploadInput): Promise<UploadedMedia> {
  const form = new FormData();
  form.append("kind", kind);
  form.append("file", file, filename);

  let response: Response;
  try {
    response = await fetch("/api/media", {
      method: "POST",
      credentials: "same-origin",
      headers: { "idempotency-key": idempotencyKey },
      body: form,
    });
  } catch {
    throw new ApiError("You're offline. Connect to send this.", 0);
  }
  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    throw apiErrorFrom(response.status, payload);
  }
  return uploadedMediaSchema.parse(payload);
}

/**
 * Whether the backend accepts uploads yet. `GET /media` is 404 until the
 * upload endpoint exists; a 405 (POST-only route) or a 200 means it does.
 */
export async function fetchMediaCapability(): Promise<boolean> {
  let response: Response;
  try {
    response = await fetch("/api/media", { credentials: "same-origin" });
  } catch {
    throw new ApiError("You're offline.", 0);
  }
  if (response.status === 404) return false;
  if (response.ok || response.status === 405) return true;
  throw apiErrorFrom(response.status, await response.json().catch(() => null));
}

/**
 * Where the browser should load an uploaded file from. A backend path
 * (`/media/…`) goes through the BFF so the session is attached; a full
 * URL (e.g. a signed storage link) is used as it is.
 */
export function mediaSrc(url: string | null): string | null {
  if (url === null || url === "") return null;
  if (url.startsWith("/media/")) return `/api${url}`;
  if (/^https?:\/\//.test(url)) return url;
  return null;
}

/** A fresh idempotency key for one file. */
export function newUploadKey(): string {
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}
