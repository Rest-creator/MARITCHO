"use client";

import { useEffect, useRef, useState } from "react";

import { Icon } from "@/components/ui/Icon";
import { Sheet } from "@/components/ui/Sheet";

type Props = {
  onCapture: (photo: File) => void;
  onClose: () => void;
  /** Offered when the camera can't be used (no camera, or permission refused). */
  onUseFiles: () => void;
};

type CameraState = "starting" | "live" | "blocked";

function canUseCamera(): boolean {
  return (
    typeof navigator !== "undefined" && typeof navigator.mediaDevices?.getUserMedia === "function"
  );
}

/**
 * Take a photo with the computer's or phone's camera, inside the app.
 * Phones normally use their own camera app (PhotoPicker); this is for
 * laptops and desktops, where browsers ignore the "use the camera" hint.
 */
export function CameraCapture({ onCapture, onClose, onUseFiles }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [state, setState] = useState<CameraState>(() => (canUseCamera() ? "starting" : "blocked"));

  useEffect(() => {
    if (!canUseCamera()) return;
    let stream: MediaStream | null = null;
    let isCancelled = false;
    const video = videoRef.current;
    navigator.mediaDevices
      .getUserMedia({ video: { facingMode: "environment" }, audio: false })
      .then((granted) => {
        if (isCancelled) {
          granted.getTracks().forEach((track) => track.stop());
          return;
        }
        stream = granted;
        if (video) {
          video.srcObject = granted;
          void video.play();
        }
        setState("live");
      })
      .catch(() => {
        if (!isCancelled) setState("blocked");
      });
    // Leaving always turns the camera off.
    return () => {
      isCancelled = true;
      stream?.getTracks().forEach((track) => track.stop());
      if (video) video.srcObject = null;
    };
  }, []);

  function takePhoto(): void {
    const video = videoRef.current;
    if (!video || video.videoWidth === 0) return;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d")?.drawImage(video, 0, 0);
    canvas.toBlob(
      (blob) => {
        if (blob === null) return;
        onCapture(new File([blob], `camera-${Date.now()}.jpg`, { type: "image/jpeg" }));
      },
      "image/jpeg",
      0.9,
    );
  }

  return (
    <Sheet
      title="Take a photo"
      isOpen
      onClose={onClose}
      isFitContent
      footer={
        state === "blocked" ? (
          <button type="button" className="btn btn--primary btn--cta" onClick={onUseFiles}>
            Choose a photo instead
          </button>
        ) : (
          <button
            type="button"
            className="btn btn--primary btn--cta"
            disabled={state !== "live"}
            onClick={takePhoto}
          >
            <Icon name="camera" size={18} />
            {state === "live" ? "Take photo" : "Starting the camera…"}
          </button>
        )
      }
    >
      {state === "blocked" ? (
        <p className="meta meta--secondary" role="status" style={{ lineHeight: 1.5 }}>
          The camera isn&apos;t available. Allow camera access for this site in your browser, or
          choose a photo you already have.
        </p>
      ) : (
        <video
          ref={videoRef}
          className="camera-preview"
          playsInline
          muted
          aria-label="Camera preview"
        />
      )}
    </Sheet>
  );
}
