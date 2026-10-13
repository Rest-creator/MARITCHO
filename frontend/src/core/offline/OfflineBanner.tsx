"use client";

import { useMutationState } from "@tanstack/react-query";

import { Icon } from "@/components/ui/Icon";
import { useOnlineStatus } from "@/core/offline/use-online-status";

export function pendingLabel(count: number): string {
  if (count === 0) return "You're offline — showing what was saved on this phone.";
  return `You're offline — ${count} ${count === 1 ? "change" : "changes"} saved, will send when you reconnect.`;
}

export function OfflineBanner() {
  const isOnline = useOnlineStatus();
  const pending = useMutationState({ filters: { predicate: (m) => m.state.isPaused } });

  if (isOnline) return null;

  return (
    <div className="offline-banner" role="status" aria-live="polite">
      <Icon name="wifiOff" size={16} />
      <span>{pendingLabel(pending.length)}</span>
    </div>
  );
}
