"use client";

import { useEffect, useRef, useState, type ChangeEvent } from "react";

import { Icon } from "@/components/ui/Icon";

interface LocalPhoto {
  id: string;
  url: string;
}

type Props = {
  max?: number;
  addLabel?: string;
  /** Rendered as a row of thumbnails (post a job) or a 3-column grid (show your work). */
  layout?: "row" | "grid";
};

/**
 * Camera/gallery picker with on-device previews. The backend accepts photo
 * URLs but has no upload endpoint yet, so photos stay on the phone for now.
 */
export function PhotoStrip({ max = 3, addLabel = "Add photo", layout = "row" }: Props) {
  const [photos, setPhotos] = useState<LocalPhoto[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const photosRef = useRef<LocalPhoto[]>([]);

  useEffect(() => {
    photosRef.current = photos;
  }, [photos]);

  useEffect(() => () => photosRef.current.forEach((photo) => URL.revokeObjectURL(photo.url)), []);

  function handleChange(event: ChangeEvent<HTMLInputElement>): void {
    const files = Array.from(event.target.files ?? []).slice(0, max - photos.length);
    const added = files.map((file) => ({
      id: `${file.name}-${file.lastModified}`,
      url: URL.createObjectURL(file),
    }));
    setPhotos((current) => [...current, ...added]);
    event.target.value = "";
  }

  function remove(id: string): void {
    setPhotos((current) => {
      const target = current.find((photo) => photo.id === id);
      if (target) URL.revokeObjectURL(target.url);
      return current.filter((photo) => photo.id !== id);
    });
  }

  const canAdd = photos.length < max;
  const input = (
    <input
      ref={inputRef}
      type="file"
      accept="image/*"
      capture="environment"
      multiple
      hidden
      onChange={handleChange}
    />
  );

  if (layout === "grid") {
    return (
      <div className="photo-grid">
        {photos.map((photo) => (
          <button
            key={photo.id}
            type="button"
            className="photo-tile"
            aria-label="Remove photo"
            onClick={() => remove(photo.id)}
          >
            {/* eslint-disable-next-line @next/next/no-img-element -- local object URL preview */}
            <img src={photo.url} alt="" />
          </button>
        ))}
        {canAdd && (
          <button type="button" className="photo-add" onClick={() => inputRef.current?.click()}>
            <Icon name="plus" strokeWidth={1.75} />
            {addLabel}
          </button>
        )}
        {input}
      </div>
    );
  }

  return (
    <>
      {photos.map((photo) => (
        <button
          key={photo.id}
          type="button"
          className="thumb"
          aria-label="Remove photo"
          onClick={() => remove(photo.id)}
        >
          {/* eslint-disable-next-line @next/next/no-img-element -- local object URL preview */}
          <img src={photo.url} alt="" />
        </button>
      ))}
      {canAdd && (
        <button
          type="button"
          className="photo-add photo-add--row"
          onClick={() => inputRef.current?.click()}
        >
          <Icon name="camera" size={18} strokeWidth={1.75} />
          {addLabel}
        </button>
      )}
      {input}
    </>
  );
}
