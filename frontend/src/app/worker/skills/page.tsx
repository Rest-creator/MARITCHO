import type { Metadata } from "next";

import { safeNextPath } from "@/core/session/next-path";
import { WorkerSkillsScreen } from "@/features/worker/WorkerSkillsScreen";

export const metadata: Metadata = { title: "Your skills" };

type Props = { searchParams: Promise<Record<string, string | string[] | undefined>> };

export default async function WorkerSkillsPage({ searchParams }: Props) {
  const params = await searchParams;
  return <WorkerSkillsScreen nextPath={safeNextPath(params.next)} />;
}
