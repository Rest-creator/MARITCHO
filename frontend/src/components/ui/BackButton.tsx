"use client";

import type { MouseEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { Icon } from "@/components/ui/Icon";

type Props = {
  /** Where to go when there is no in-app history to pop (deep link, fresh tab). */
  fallbackHref: string;
  label?: string;
  isOverlay?: boolean;
};

export function BackButton({ fallbackHref, label = "Back", isOverlay = false }: Props) {
  const router = useRouter();

  function handleClick(event: MouseEvent<HTMLAnchorElement>): void {
    if (window.history.length > 1) {
      event.preventDefault();
      router.back();
    }
  }

  return (
    <Link
      href={fallbackHref}
      aria-label={label}
      className={isOverlay ? "icon-btn icon-btn--overlay" : "icon-btn"}
      onClick={handleClick}
    >
      <Icon name="back" strokeWidth={2} />
    </Link>
  );
}
