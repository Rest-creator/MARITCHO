"use client";

import { createContext, use, useEffect, useMemo, type ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { ApiError } from "@/core/api/http";
import { userSchema, type User } from "@/core/api/schemas";
import { queryKeys } from "@/core/query/keys";
import { UNAUTHORIZED_EVENT } from "@/core/query/query-client";

export type SignInRole = "BUYER" | "WORKER";

export interface SignInInput {
  phone: string;
  role: SignInRole;
  /** The 6-digit code, when one was sent (see requestSignInCode). */
  code?: string;
}

interface SessionValue {
  user: User | null;
  isLoading: boolean;
  signIn: (input: SignInInput) => Promise<User>;
  isSigningIn: boolean;
  signInError: string | null;
  signOut: () => Promise<void>;
}

const SessionContext = createContext<SessionValue | null>(null);

async function readJson(response: Response): Promise<unknown> {
  return response.json().catch(() => null);
}

function detailOf(payload: unknown, fallback: string): string {
  if (typeof payload === "object" && payload !== null && "detail" in payload) {
    const detail = (payload as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
  }
  return fallback;
}

async function fetchSession(): Promise<User | null> {
  const response = await fetch("/api/session", { credentials: "same-origin" }).catch(() => {
    throw new ApiError("You're offline.", 0);
  });
  if (response.status === 401) {
    return null;
  }
  if (!response.ok) {
    throw new ApiError("Could not check your sign-in", response.status);
  }
  return userSchema.nullable().parse(await readJson(response));
}

async function postSession(input: SignInInput): Promise<User> {
  const response = await fetch("/api/session", {
    method: "POST",
    credentials: "same-origin",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(input),
  }).catch(() => {
    throw new ApiError("You're offline. Connect to sign in.", 0);
  });
  const payload = await readJson(response);
  if (!response.ok) {
    throw new ApiError(detailOf(payload, "Sign-in failed. Please try again."), response.status);
  }
  return userSchema.parse(payload);
}

/** Where each role lands after signing in. */
export function homeFor(role: User["role"]): string {
  return role === "WORKER" ? "/worker" : "/employer";
}

type Props = { children: ReactNode };

export function SessionProvider({ children }: Props) {
  const queryClient = useQueryClient();
  const router = useRouter();

  const session = useQuery({
    queryKey: queryKeys.session,
    queryFn: fetchSession,
    staleTime: 5 * 60_000,
  });

  const signInMutation = useMutation({
    mutationFn: postSession,
    onSuccess: (user) => {
      queryClient.setQueryData(queryKeys.session, user);
    },
  });

  useEffect(() => {
    function handleUnauthorized(): void {
      queryClient.setQueryData(queryKeys.session, null);
      router.replace("/signup?expired=1");
    }
    window.addEventListener(UNAUTHORIZED_EVENT, handleUnauthorized);
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, handleUnauthorized);
  }, [queryClient, router]);

  const { mutateAsync: signInAsync, isPending: isSigningIn, error: signInFailure } = signInMutation;

  const value = useMemo<SessionValue>(
    () => ({
      user: session.data ?? null,
      // A `null` still being re-checked is not yet a reason to send anyone to sign-up.
      isLoading: session.isPending || (session.data === null && session.isFetching),
      signIn: signInAsync,
      isSigningIn,
      signInError: signInFailure instanceof Error ? signInFailure.message : null,
      signOut: async () => {
        await fetch("/api/session", { method: "DELETE", credentials: "same-origin" }).catch(
          () => undefined,
        );
        queryClient.clear();
        queryClient.setQueryData(queryKeys.session, null);
        router.replace("/");
      },
    }),
    [
      session.data,
      session.isPending,
      session.isFetching,
      signInAsync,
      isSigningIn,
      signInFailure,
      queryClient,
      router,
    ],
  );

  return <SessionContext value={value}>{children}</SessionContext>;
}

export function useSession(): SessionValue {
  const value = use(SessionContext);
  if (value === null) {
    throw new Error("useSession must be used inside <SessionProvider>");
  }
  return value;
}
