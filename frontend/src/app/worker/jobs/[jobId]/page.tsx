import type { Metadata } from "next";

import { JobDetailScreen } from "@/features/worker/JobDetailScreen";

export const metadata: Metadata = { title: "Job details" };

type Props = { params: Promise<{ jobId: string }> };

export default async function WorkerJobDetailPage({ params }: Props) {
  const { jobId } = await params;
  return <JobDetailScreen jobId={jobId} />;
}
