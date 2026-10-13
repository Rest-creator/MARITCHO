"use client";

import { useState, type ReactNode } from "react";
import { createSyncStoragePersister } from "@tanstack/query-sync-storage-persister";
import { defaultShouldDehydrateQuery } from "@tanstack/react-query";
import { PersistQueryClientProvider } from "@tanstack/react-query-persist-client";

import { CACHE_MAX_AGE_MS, createQueryClient, shouldPersistQuery } from "@/core/query/query-client";

/** Bump when a cached payload shape changes, so stale caches are discarded. */
const CACHE_BUSTER = "maricho-v1";

function safeStorage(): Storage | undefined {
  try {
    return typeof window === "undefined" ? undefined : window.localStorage;
  } catch {
    return undefined;
  }
}

type Props = { children: ReactNode };

export function QueryProvider({ children }: Props) {
  const [client] = useState(createQueryClient);
  const [persister] = useState(() =>
    createSyncStoragePersister({
      storage: safeStorage(),
      key: "maricho-cache",
      throttleTime: 1000,
    }),
  );

  return (
    <PersistQueryClientProvider
      client={client}
      persistOptions={{
        persister,
        maxAge: CACHE_MAX_AGE_MS,
        buster: CACHE_BUSTER,
        dehydrateOptions: {
          // Keep paused (offline-queued) mutations so they survive a reload.
          shouldDehydrateMutation: (mutation) => mutation.state.isPaused,
          shouldDehydrateQuery: (query) =>
            defaultShouldDehydrateQuery(query) &&
            shouldPersistQuery(query.queryKey, query.state.data),
        },
      }}
      onSuccess={() => {
        void client.resumePausedMutations();
      }}
    >
      {children}
    </PersistQueryClientProvider>
  );
}
