"use client";

import { Screen } from "@/components/ui/Screen";
import { EmployerTabBar } from "@/features/employer/EmployerTabBar";
import { useMyJobs } from "@/features/jobs/hooks";
import { ConversationList } from "@/features/messaging/ConversationList";

export function EmployerMessagesScreen() {
  const jobs = useMyJobs();
  return (
    <Screen hasTabBar>
      <h1 className="title title--page">Messages</h1>
      <ConversationList
        jobs={jobs.data}
        isPending={jobs.isPending}
        error={jobs.error}
        onRetry={() => void jobs.refetch()}
        emptyHint="Once you hire someone you can chat with them here."
      />
      <EmployerTabBar />
    </Screen>
  );
}
