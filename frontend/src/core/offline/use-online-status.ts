import { useSyncExternalStore } from "react";
import { onlineManager } from "@tanstack/react-query";

/** Same signal TanStack Query uses to pause and resume network work. */
export function useOnlineStatus(): boolean {
  return useSyncExternalStore(
    (listener) => onlineManager.subscribe(listener),
    () => onlineManager.isOnline(),
    () => true,
  );
}
