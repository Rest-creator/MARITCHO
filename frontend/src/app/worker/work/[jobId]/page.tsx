import type { Metadata } from "next";

import { FinishedJobScreen } from "@/features/worker/FinishedJobScreen";

export const metadata: Metadata = { title: "Finished job" };

type Props = { params: Promise<{ jobId: string }> };

export default async function FinishedJobPage({ params }: Props) {
  const { jobId } = await params;
  return <FinishedJobScreen jobId={jobId} />;
}
