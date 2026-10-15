"use client";

import { useRef, useState, type ChangeEvent } from "react";

import { CameraCapture } from "@/components/ui/CameraCapture";
import { Icon } from "@/components/ui/Icon";
import { Sheet } from "@/components/ui/Sheet";

type Props = {
  isOpen: boolean;
  onClose: () => void;
  onPick: (files: File[]) => void;
  /** Allow several photos from the gallery at once. */
  multiple?: boolean;
};

/** Phones and tablets: their own camera app takes better photos than a browser preview. */
function hasTouchCamera(): boolean {
  return typeof window !== "undefined" && window.matchMedia("(pointer: coarse)").matches;
}

/**
 * "Add a photo": take one now with the camera, or choose from the gallery.
 * On a phone "Take a photo" opens the phone's camera app; on a laptop it
 * opens the webcam inside the app (CameraCapture).
 */
export function PhotoPicker({ isOpen, onClose, onPick, multiple = false }: Props) {
  const galleryRef = useRef<HTMLInputElement>(null);
  const cameraRef = useRef<HTMLInputElement>(null);
  const [isWebcamOpen, setIsWebcamOpen] = useState(false);

  function handleFiles(event: ChangeEvent<HTMLInputElement>): void {
    const files = Array.from(event.target.files ?? []);
    event.target.value = "";
    if (files.length > 0) onPick(files);
    onClose();
  }

  function takePhoto(): void {
    if (hasTouchCamera()) {
      cameraRef.current?.click();
    } else {
      setIsWebcamOpen(true);
    }
  }

  return (
    <>
      <input
        ref={galleryRef}
        type="file"
        accept="image/*"
        multiple={multiple}
        hidden
        data-testid="photo-gallery-input"
        onChange={handleFiles}
      />
      <input
        ref={cameraRef}
        type="file"
        accept="image/*"
        capture="environment"
        hidden
        data-testid="photo-camera-input"
        onChange={handleFiles}
      />

      {isOpen && !isWebcamOpen && (
        <Sheet title="Add a photo" isOpen onClose={onClose} isFitContent>
          <div className="stack" style={{ gap: 10 }}>
            <button type="button" className="btn btn--primary btn--cta" onClick={takePhoto}>
              <Icon name="camera" size={20} />
              Take a photo
            </button>
            <button
              type="button"
              className="btn btn--cta"
              onClick={() => galleryRef.current?.click()}
            >
              <Icon name="image" size={20} />
              Choose from gallery
            </button>
          </div>
        </Sheet>
      )}

      {isWebcamOpen && (
        <CameraCapture
          onCapture={(photo) => {
            setIsWebcamOpen(false);
            onPick([photo]);
            onClose();
          }}
          onClose={() => {
            setIsWebcamOpen(false);
            onClose();
          }}
          onUseFiles={() => {
            setIsWebcamOpen(false);
            galleryRef.current?.click();
          }}
        />
      )}
    </>
  );
}
