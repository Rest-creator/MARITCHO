"use client";

import { useEffect, useId, useRef, type ReactNode } from "react";
import { createPortal } from "react-dom";

import { Icon } from "@/components/ui/Icon";

type Props = {
  title: string;
  isOpen: boolean;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
  /** Size to content instead of filling the screen below the top inset. */
  isFitContent?: boolean;
};

/** Bottom sheet dialog (design: E3 "Who do you need?"). */
export function Sheet({ title, isOpen, onClose, children, footer, isFitContent = false }: Props) {
  const titleId = useId();
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;
    const previouslyFocused =
      document.activeElement instanceof HTMLElement ? document.activeElement : null;
    panelRef.current?.focus();
    function handleKeyDown(event: KeyboardEvent): void {
      if (event.key === "Escape") onClose();
    }
    document.addEventListener("keydown", handleKeyDown);
    const { overflow } = document.body.style;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = overflow;
      previouslyFocused?.focus();
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return createPortal(
    <div className="sheet-root">
      <button
        type="button"
        className="sheet-scrim"
        aria-label="Close"
        tabIndex={-1}
        onClick={onClose}
      />
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        className={isFitContent ? "sheet sheet--auto" : "sheet"}
      >
        <div className="sheet__handle" aria-hidden="true" />
        <div className="row row--between" style={{ marginTop: 16 }}>
          <h2 id={titleId} className="title">
            {title}
          </h2>
          <button type="button" className="icon-btn" aria-label="Close" onClick={onClose}>
            <Icon name="close" size={18} strokeWidth={2} />
          </button>
        </div>
        <div className="sheet__body">{children}</div>
        {footer && <div style={{ marginTop: 14 }}>{footer}</div>}
      </div>
    </div>,
    document.body,
  );
}
