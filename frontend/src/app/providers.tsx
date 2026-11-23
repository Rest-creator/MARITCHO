"use client";

import { useEffect, type ReactNode } from "react";

import { OfflineBanner } from "@/core/offline/OfflineBanner";
import { ServiceWorkerRegistrar } from "@/core/offline/ServiceWorkerRegistrar";
import { QueryProvider } from "@/core/query/QueryProvider";
import { useLocalProfile } from "@/core/session/profile-store";
import { SessionProvider } from "@/core/session/SessionProvider";

function ThemeSynchronizer(): null {
  const { theme } = useLocalProfile();

  useEffect(() => {
    const root = document.documentElement;
    if (theme === "light") {
      root.dataset.theme = "light";
    } else {
      delete root.dataset.theme;
    }
    const metaTheme = document.querySelector('meta[name="theme-color"]');
    if (metaTheme) {
      metaTheme.setAttribute("content", theme === "light" ? "#ffffff" : "#2d2e83");
    }
  }, [theme]);

  return null;
}

type Props = { children: ReactNode };

export function Providers({ children }: Props) {
  return (
    <QueryProvider>
      <SessionProvider>
        <ThemeSynchronizer />
        <OfflineBanner />
        {children}
        <ServiceWorkerRegistrar />
      </SessionProvider>
    </QueryProvider>
  );
}
