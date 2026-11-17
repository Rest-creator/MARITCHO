"use client";

import { Screen } from "@/components/ui/Screen";
import { useSession } from "@/core/session/SessionProvider";
import { EmployerTabBar } from "@/features/employer/EmployerTabBar";
import { useMyJobs } from "@/features/jobs/hooks";
import { ConversationList } from "@/features/messaging/ConversationList";

export function EmployerMessagesScreen() {
  const { user } = useSession();
  const jobs = useMyJobs(user?.role === "BUYER");
  return (
    <Screen hasTabBar>
      <h1 className="title title--page">Messages</h1>
      <ConversationList
        jobs={jobs.data}
        isPending={jobs.isPending}
        error={jobs.error}
        onRetry={() => void jobs.refetch()}
        emptyHint="Once a worker answers your job or you hire someone, you can chat with them here."
      />
      <EmployerTabBar />
    </Screen>
  );
}
