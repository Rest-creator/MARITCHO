/*
 * Photos from a phone camera are 3–8 MB. Before anything leaves the device
 * they are redrawn at most 1280 px on the long side as JPEG, which lands
 * around 100–250 KB, small enough for a pay-as-you-go data bundle.
 * Redrawing also drops EXIF, so the photo's GPS position is never sent.
 */

export const MAX_PHOTO_EDGE = 1280;
const QUALITY_STEPS = [0.72, 0.6, 0.5] as const;
/** Try a lower quality until the photo is under this. */
export const TARGET_PHOTO_BYTES = 400 * 1024;

/** Scale `width`×`height` down (never up) so the longer side is at most `maxEdge`. */
export function fitWithin(
  width: number,
  height: number,
  maxEdge: number = MAX_PHOTO_EDGE,
): { width: number; height: number } {
  const longest = Math.max(width, height);
  if (longest <= maxEdge || longest === 0) return { width, height };
  const scale = maxEdge / longest;
  return {
    width: Math.max(1, Math.round(width * scale)),
    height: Math.max(1, Math.round(height * scale)),
  };
}

function toJpeg(canvas: HTMLCanvasElement, quality: number): Promise<Blob> {
  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => (blob ? resolve(blob) : reject(new Error("Could not prepare the photo."))),
      "image/jpeg",
      quality,
    );
  });
}

/** Shrink a camera photo for upload. Rejects if the file is not a readable image. */
export async function compressImage(file: Blob): Promise<Blob> {
  // `from-image` applies the EXIF rotation before the EXIF is dropped.
  const bitmap = await createImageBitmap(file, { imageOrientation: "from-image" }).catch(() => {
    throw new Error("That file isn't a photo we can read.");
  });
  try {
    const size = fitWithin(bitmap.width, bitmap.height);
    const canvas = document.createElement("canvas");
    canvas.width = size.width;
    canvas.height = size.height;
    const context = canvas.getContext("2d");
    if (context === null) throw new Error("Could not prepare the photo.");
    context.drawImage(bitmap, 0, 0, size.width, size.height);

    let smallest: Blob | null = null;
    for (const quality of QUALITY_STEPS) {
      const blob = await toJpeg(canvas, quality);
      if (smallest === null || blob.size < smallest.size) smallest = blob;
      if (blob.size <= TARGET_PHOTO_BYTES) break;
    }
    if (smallest === null) throw new Error("Could not prepare the photo.");
    return smallest;
  } finally {
    bitmap.close();
  }
}
