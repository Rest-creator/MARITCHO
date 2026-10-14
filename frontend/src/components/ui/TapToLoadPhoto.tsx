"use client";

import { useState } from "react";

import { Icon } from "@/components/ui/Icon";
import { mediaSrc } from "@/core/media/upload";

type Props = {
  url: string | null;
  /** Read out and shown as the button text, e.g. "Photo of the problem". */
  label: string;
};

/**
 * Light Mode: an uploaded photo costs data, so it only downloads when the
 * person taps for it. Once shown, the browser keeps it (the BFF marks media
 * as cacheable), so it never downloads twice.
 */
export function TapToLoadPhoto({ url, label }: Props) {
  const [isShown, setIsShown] = useState(false);
  const src = mediaSrc(url);
  if (src === null) return null;

  if (!isShown) {
    return (
      <button type="button" className="btn btn--sm btn--soft" onClick={() => setIsShown(true)}>
        <Icon name="image" size={16} />
        {label} · tap to load
      </button>
    );
  }
  return (
    // eslint-disable-next-line @next/next/no-img-element -- user upload served through the BFF
    <img src={src} alt={label} className="media-photo" loading="lazy" decoding="async" />
  );
}
