"use client";

type Props = { isOn: boolean; onToggle: (next: boolean) => void; label: string };

export function Switch({ isOn, onToggle, label }: Props) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={isOn}
      aria-label={label}
      className="switch"
      onClick={() => onToggle(!isOn)}
    >
      <span className="switch__thumb" />
    </button>
  );
}
