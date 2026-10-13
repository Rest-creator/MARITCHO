import type { Metadata } from "next";

import { WorkerProfileScreen } from "@/features/jobs/WorkerProfileScreen";

export const metadata: Metadata = { title: "Worker profile" };

type Props = { params: Promise<{ jobId: string; workerId: string }> };

export default async function WorkerProfilePage({ params }: Props) {
  const { jobId, workerId } = await params;
  return <WorkerProfileScreen jobId={jobId} workerId={workerId} />;
}
