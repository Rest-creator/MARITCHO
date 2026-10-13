"use client";

import { Screen } from "@/components/ui/Screen";
import { useAssignedJobs } from "@/features/jobs/hooks";
import { ConversationList } from "@/features/messaging/ConversationList";
import { WorkerTabBar } from "@/features/worker/WorkerTabBar";

export function WorkerMessagesScreen() {
  const jobs = useAssignedJobs();
  return (
    <Screen glow="worker" hasTabBar>
      <h1 className="title title--page">Messages</h1>
      <ConversationList
        jobs={jobs.data}
        isPending={jobs.isPending}
        error={jobs.error}
        onRetry={() => void jobs.refetch()}
        emptyHint="When a client hires you, you can chat with them here."
      />
      <WorkerTabBar />
    </Screen>
  );
}
