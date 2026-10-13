import type { Metadata } from "next";

import { tradeSchema } from "@/core/api/schemas";
import { PostJobScreen } from "@/features/jobs/PostJobScreen";

export const metadata: Metadata = { title: "Post a job" };

type Props = { searchParams: Promise<Record<string, string | string[] | undefined>> };

export default async function PostJobPage({ searchParams }: Props) {
  const params = await searchParams;
  const trade = tradeSchema.safeParse(params.trade);
  return (
    <PostJobScreen
      initialTrade={trade.success ? trade.data : null}
      initialSkillId={typeof params.skill === "string" ? params.skill : null}
      shouldOpenPicker={params.pick === "1"}
    />
  );
}
