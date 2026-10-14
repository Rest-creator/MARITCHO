import { useCallback, useRef, useState } from "react";

import { compressImage } from "@/core/media/compress-image";
import { newUploadKey, uploadMedia, type MediaKind } from "@/core/media/upload";

interface Upload {
  /** Shrinks photos first, uploads, and resolves to the stored file's URL. */
  upload: (file: Blob, kind: MediaKind) => Promise<string>;
  isUploading: boolean;
}

const FILENAMES: Record<MediaKind, string> = { photo: "photo.jpg", voice_note: "voice-note" };

/**
 * Upload one file at a time. Retrying the same Blob reuses its idempotency
 * key, so a retry after a dropped connection can't store it twice.
 */
export function useUpload(): Upload {
  const keys = useRef(new WeakMap<Blob, string>());
  const [pending, setPending] = useState(0);

  const upload = useCallback(async (file: Blob, kind: MediaKind): Promise<string> => {
    let key = keys.current.get(file);
    if (key === undefined) {
      key = newUploadKey();
      keys.current.set(file, key);
    }
    setPending((count) => count + 1);
    try {
      const body = kind === "photo" ? await compressImage(file) : file;
      const filename =
        kind === "voice_note"
          ? `${FILENAMES.voice_note}${audioExtension(file.type)}`
          : FILENAMES.photo;
      const stored = await uploadMedia({ file: body, kind, filename, idempotencyKey: key });
      return stored.url;
    } finally {
      setPending((count) => count - 1);
    }
  }, []);

  return { upload, isUploading: pending > 0 };
}

export function audioExtension(mimeType: string): string {
  if (mimeType.includes("webm")) return ".webm";
  if (mimeType.includes("ogg")) return ".ogg";
  if (mimeType.includes("mp4") || mimeType.includes("aac")) return ".m4a";
  return "";
}
