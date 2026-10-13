"use client";

import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";

import { Screen } from "@/components/ui/Screen";
import { Skeleton } from "@/components/ui/States";
import type { Role } from "@/core/api/schemas";
import { homeFor, useSession } from "@/core/session/SessionProvider";

type Props = { role: Extract<Role, "BUYER" | "WORKER">; children: ReactNode };

/** Keeps each side of the app to the account type it was built for. */
export function RoleGate({ role, children }: Props) {
  const { user, isLoading } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;
    if (user === null) {
      router.replace(`/signup?role=${role === "WORKER" ? "worker" : "buyer"}`);
    } else if (user.role !== role) {
      router.replace(homeFor(user.role));
    }
  }, [isLoading, user, role, router]);

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
