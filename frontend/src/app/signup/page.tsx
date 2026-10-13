import type { Metadata } from "next";

import { SignUpScreen } from "@/features/accounts/SignUpScreen";

export const metadata: Metadata = { title: "Sign up" };

type Props = { searchParams: Promise<Record<string, string | string[] | undefined>> };

export default async function SignUpPage({ searchParams }: Props) {
  const params = await searchParams;
  return (
    <SignUpScreen
      initialRole={params.role === "worker" ? "WORKER" : "BUYER"}
      isLogin={params.mode === "login" || params.expired === "1"}
      isExpired={params.expired === "1"}
    />
  );
}
