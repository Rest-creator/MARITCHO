import { initials } from "@/core/format/format";

const TONES = ["", "avatar--stone", "avatar--moss", "avatar--warm"] as const;

/** Stable tone per person so the same worker always gets the same colour. */
export function toneFor(seed: string): (typeof TONES)[number] {
  let hash = 0;
  for (const char of seed) {
    hash = (hash * 31 + char.charCodeAt(0)) | 0;
  }
  return TONES[Math.abs(hash) % TONES.length] ?? "";
}

type Props = {
  name: string;
  seed?: string;
  size?: "xs" | "sm" | "md" | "lg" | "xl";
  isOnline?: boolean;
};

export function Avatar({ name, seed, size = "lg", isOnline = false }: Props) {
  const sizeClass = size === "lg" ? "" : `avatar--${size}`;
  const classes = ["avatar", sizeClass, toneFor(seed ?? name)].filter(Boolean).join(" ");
  return (
    <div className={classes} aria-hidden="true">
      {initials(name)}
      {isOnline && <span className="avatar__online" />}
    </div>
  );
}
