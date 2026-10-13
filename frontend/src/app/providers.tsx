"use client";

import type { ReactNode } from "react";

import { OfflineBanner } from "@/core/offline/OfflineBanner";
import { ServiceWorkerRegistrar } from "@/core/offline/ServiceWorkerRegistrar";
import { QueryProvider } from "@/core/query/QueryProvider";
import { SessionProvider } from "@/core/session/SessionProvider";

type Props = { children: ReactNode };

export function Providers({ children }: Props) {
  return (
    <QueryProvider>
      <SessionProvider>
        <OfflineBanner />
        {children}
        <ServiceWorkerRegistrar />
      </SessionProvider>
    </QueryProvider>
  );
}
