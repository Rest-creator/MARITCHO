"use client";

import { useMemo } from "react";

import { Screen } from "@/components/ui/Screen";
import { useSession } from "@/core/session/SessionProvider";
import { useAssignedJobs, useMyOffers } from "@/features/jobs/hooks";
import { ConversationList, type ConversationJob } from "@/features/messaging/ConversationList";
import { WorkerTabBar } from "@/features/worker/WorkerTabBar";

export function WorkerMessagesScreen() {
  const { user } = useSession();
  const isWorker = user?.role === "WORKER";
  const assigned = useAssignedJobs(isWorker);
  const offers = useMyOffers(isWorker);

  const jobs = useMemo<ConversationJob[] | undefined>(() => {
    if (!assigned.data && !offers.data) return undefined;
    const byId = new Map<string, ConversationJob>();
    for (const job of assigned.data ?? []) {
      byId.set(job.id, job);
    }
    for (const offer of offers.data ?? []) {
      if (!byId.has(offer.job_id)) {
        byId.set(offer.job_id, {
          id: offer.job_id,
          trade: offer.job_trade,
          suburb: offer.job_suburb,
          status: offer.job_status,
          updated_at: offer.updated_at,
          problem_description: offer.availability_note
            ? `Offer $${offer.quoted_amount} · ${offer.availability_note}`
            : `Offer $${offer.quoted_amount}`,
          worker_id: null,
          has_offer: true,
        });
      }
    }
    return [...byId.values()];
  }, [assigned.data, offers.data]);

  return (
    <Screen glow="worker" hasTabBar>
      <h1 className="title title--page">Messages</h1>
      <ConversationList
        jobs={jobs}
        isPending={assigned.isPending && offers.isPending}
        error={assigned.error ?? offers.error}
        onRetry={() => {
          void assigned.refetch();
          void offers.refetch();
        }}
        emptyHint="When you send an offer or get hired for a job, you can chat with the client here."
      />
      <WorkerTabBar />
    </Screen>
  );
}
