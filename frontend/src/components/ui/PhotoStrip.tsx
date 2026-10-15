"use client";

import { useEffect, useRef, useState } from "react";

import { Icon } from "@/components/ui/Icon";
import { PhotoPicker } from "@/components/ui/PhotoPicker";

interface LocalPhoto {
  id: string;
  url: string;
  file: File;
}

type Props = {
  max?: number;
  addLabel?: string;
  /** Rendered as a row of thumbnails (post a job) or a 3-column grid (show your work). */
  layout?: "row" | "grid";
  /** Called with the chosen photos (in order) whenever they change. */
  onChange?: (files: File[]) => void;
};

/**
 * Camera/gallery picker with on-device previews. Uploading is the parent's
 * job (`onChange` hands it the files); nothing is sent from here.
 */
export function PhotoStrip({ max = 3, addLabel = "Add photo", layout = "row", onChange }: Props) {
  const [photos, setPhotos] = useState<LocalPhoto[]>([]);
  const [isPickerOpen, setIsPickerOpen] = useState(false);
  const photosRef = useRef<LocalPhoto[]>([]);

  useEffect(() => {
    photosRef.current = photos;
  }, [photos]);

  useEffect(() => {
    onChange?.(photos.map((photo) => photo.file));
  }, [photos, onChange]);

  useEffect(() => () => photosRef.current.forEach((photo) => URL.revokeObjectURL(photo.url)), []);

  function addFiles(picked: File[]): void {
    const files = picked.slice(0, max - photos.length);
    const added = files.map((file) => ({
      id: `${file.name}-${file.lastModified}-${file.size}`,
      url: URL.createObjectURL(file),
      file,
    }));
    setPhotos((current) => [...current, ...added]);
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
    <PhotoPicker
      isOpen={isPickerOpen}
      onClose={() => setIsPickerOpen(false)}
      onPick={addFiles}
      multiple={max - photos.length > 1}
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
          <button type="button" className="photo-add" onClick={() => setIsPickerOpen(true)}>
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
          onClick={() => setIsPickerOpen(true)}
        >
          <Icon name="camera" size={18} strokeWidth={1.75} />
          {addLabel}
        </button>
      )}
      {input}
    </>
  );
}
