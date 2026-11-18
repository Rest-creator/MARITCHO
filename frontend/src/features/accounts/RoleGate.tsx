"use client";

import { useEffect, type ReactNode } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { Screen } from "@/components/ui/Screen";
import { Sheet } from "@/components/ui/Sheet";
import { Skeleton } from "@/components/ui/States";
import type { Role } from "@/core/api/schemas";
import { queryKeys } from "@/core/query/keys";
import { canActAs } from "@/core/session/roles";
import { homeFor, useSession } from "@/core/session/SessionProvider";
import { useUpdateUserProfile } from "@/features/workers/hooks";

type Props = { role: Extract<Role, "BUYER" | "WORKER">; children: ReactNode };

const ROLE_LABEL: Record<"BUYER" | "WORKER", string> = { BUYER: "hiring", WORKER: "working" };

/**
 * Keeps each side of the app to the mode it was built for. An account that
 * has both sides is offered a switch into this one (e.g. opening a worker
 * link while hiring) instead of being bounced to the other home screen — but
 * the switch itself is persisted account-wide (affects every open tab/
 * session), so it only happens after the person explicitly confirms it, not
 * as a side effect of merely landing on this route.
 */
export function RoleGate({ role, children }: Props) {
  const { user, isLoading } = useSession();
  const router = useRouter();
  const queryClient = useQueryClient();
  const switchMode = useUpdateUserProfile();
  const canSwitch = user !== null && user.role !== role && canActAs(user, role);

  useEffect(() => {
    if (isLoading) return;
    if (user === null) {
      // Signed-out visitors to a protected page most likely already have an account.
      router.replace(`/signup?mode=login&role=${role === "WORKER" ? "worker" : "buyer"}`);
      return;
    }
    if (user.role === role || canActAs(user, role)) return;
    router.replace(homeFor(user.role));
  }, [isLoading, user, role, router]);

  function confirmSwitch(): void {
    switchMode
      .mutateAsync({ role })
      .then((updated) => queryClient.setQueryData(queryKeys.session, updated))
      .catch(() => user && router.replace(homeFor(user.role)));
  }

  function declineSwitch(): void {
    if (user) router.replace(homeFor(user.role));
  }

  if (isLoading || user === null || user.role !== role) {
    return (
      <Screen glow={role === "WORKER" ? "worker" : "employer"}>
        <Skeleton height={56} />
        <Skeleton height={140} count={3} />
        {user !== null && (
          <Sheet title="Switch mode?" isOpen={canSwitch} onClose={declineSwitch}>
            <p>
              This page is for {ROLE_LABEL[role]}. Switch your account into {ROLE_LABEL[role]} mode
              now? This changes it everywhere you&apos;re signed in.
            </p>
            <div className="row" style={{ gap: 8, marginTop: 14 }}>
              <button type="button" className="btn btn--soft" onClick={declineSwitch}>
                Not now
              </button>
              <button
                type="button"
                className="btn"
                onClick={confirmSwitch}
                disabled={switchMode.isPending}
              >
                Switch mode
              </button>
            </div>
          </Sheet>
        )}
      </Screen>
    );
  }
  return <>{children}</>;
}
