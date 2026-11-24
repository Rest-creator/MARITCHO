import type { Metadata } from "next";

import { PostJobScreen } from "@/features/jobs/PostJobScreen";

export const metadata: Metadata = { title: "Edit job" };

type Props = { params: Promise<{ jobId: string }> };

export default async function EditJobPage({ params }: Props) {
  const { jobId } = await params;
  return (
    <PostJobScreen
      initialTrade={null}
      initialSkillId={null}
      shouldOpenPicker={false}
      editJobId={jobId}
    />
  );
}
