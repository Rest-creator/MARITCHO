"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { Screen } from "@/components/ui/Screen";
import { Skeleton } from "@/components/ui/States";
import type { Role } from "@/core/api/schemas";
import { queryKeys } from "@/core/query/keys";
import { canActAs } from "@/core/session/roles";
import { homeFor, useSession } from "@/core/session/SessionProvider";
import { useUpdateUserProfile } from "@/features/workers/hooks";

type Props = { role: Extract<Role, "BUYER" | "WORKER">; children: ReactNode };

/**
 * Keeps each side of the app to the mode it was built for. An account that
 * has both sides is switched into this one (e.g. opening a worker link while
 * hiring) instead of being bounced to the other home screen.
 */
export function RoleGate({ role, children }: Props) {
  const { user, isLoading } = useSession();
  const router = useRouter();
  const queryClient = useQueryClient();
  const switchMode = useUpdateUserProfile();
  const hasTriedSwitchRef = useRef<boolean>(false);

  useEffect(() => {
    if (isLoading) return;
    if (user === null) {
      // Signed-out visitors to a protected page most likely already have an account.
      router.replace(`/signup?mode=login&role=${role === "WORKER" ? "worker" : "buyer"}`);
      return;
    }
    if (user.role === role) return;
    if (canActAs(user, role) && !hasTriedSwitchRef.current) {
      hasTriedSwitchRef.current = true;
      switchMode
        .mutateAsync({ role })
        .then((updated) => queryClient.setQueryData(queryKeys.session, updated))
        .catch(() => router.replace(homeFor(user.role)));
      return;
    }
    if (!canActAs(user, role)) router.replace(homeFor(user.role));
  }, [isLoading, user, role, router, switchMode, queryClient]);

  if (isLoading || user === null || user.role !== role) {
    return (
      <Screen glow={role === "WORKER" ? "worker" : "employer"}>
        <Skeleton height={56} />
        <Skeleton height={140} count={3} />
      </Screen>
    );
  }
  return <>{children}</>;
}
