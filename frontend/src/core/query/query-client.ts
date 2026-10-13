import { MutationCache, QueryCache, QueryClient, type QueryKey } from "@tanstack/react-query";

import {
  bookJob,
  completeJob,
  createJob,
  raiseDispute,
  registerServiceArea,
  registerSkill,
  sendMessage,
  submitOffer,
  submitQuote,
  type BookJobInput,
  type CompleteJobInput,
  type CreateJobInput,
  type RaiseDisputeInput,
  type RegisterServiceAreaInput,
  type SendMessageInput,
  type SubmitOfferInput,
  type SubmitQuoteInput,
} from "@/core/api/endpoints";
import { ApiError } from "@/core/api/http";
import type { Trade } from "@/core/api/schemas";
import { mutationKeys, queryKeys } from "@/core/query/keys";

export const UNAUTHORIZED_EVENT = "maricho:unauthorized";

/** Cached data stays usable offline for a week — the same window as a session. */
export const CACHE_MAX_AGE_MS = 1000 * 60 * 60 * 24 * 7;

function notifyUnauthorized(error: unknown): void {
  if (error instanceof ApiError && error.isUnauthorized && typeof window !== "undefined") {
    window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
  }
}

export function shouldRetry(failureCount: number, error: unknown): boolean {
  if (error instanceof ApiError && !error.isNetwork && error.status < 500) {
    return false;
  }
  return failureCount < 2;
}

/**
 * Registers a mutationFn (plus the reads it should refresh) under a key, so
 * a mutation persisted while offline can be replayed after a reload.
 */
function registerReplayable<TVariables>(
  client: QueryClient,
  key: readonly string[],
  mutationFn: (variables: TVariables) => Promise<unknown>,
  invalidates: (variables: TVariables) => QueryKey[],
): void {
  client.setMutationDefaults(key, {
    mutationFn,
    onSuccess: async (_data: unknown, variables: TVariables) => {
      await Promise.all(
        invalidates(variables).map((queryKey) => client.invalidateQueries({ queryKey })),
      );
    },
  });
}

export function createQueryClient(): QueryClient {
  const client = new QueryClient({
    queryCache: new QueryCache({ onError: notifyUnauthorized }),
    mutationCache: new MutationCache({ onError: notifyUnauthorized }),
    defaultOptions: {
      queries: {
        // Serve the cached copy first and only then try the network —
        // small data bundles and patchy signal are the normal case.
        networkMode: "offlineFirst",
        staleTime: 30_000,
        gcTime: CACHE_MAX_AGE_MS,
        retry: shouldRetry,
        refetchOnWindowFocus: false,
      },
      mutations: {
        networkMode: "online",
        retry: shouldRetry,
      },
    },
  });

  registerReplayable<CreateJobInput>(client, mutationKeys.createJob, createJob, () => [
    queryKeys.myJobs,
  ]);
  registerReplayable<SubmitOfferInput>(client, mutationKeys.submitOffer, submitOffer, () => [
    queryKeys.myOffers,
    queryKeys.openJobs,
  ]);
  registerReplayable<BookJobInput>(client, mutationKeys.bookJob, bookJob, (v) => [
    queryKeys.myJobs,
    queryKeys.job(v.jobId),
  ]);
  registerReplayable<SubmitQuoteInput>(client, mutationKeys.submitQuote, submitQuote, (v) => [
    queryKeys.assignedJobs,
    queryKeys.job(v.jobId),
  ]);
  registerReplayable<CompleteJobInput>(client, mutationKeys.completeJob, completeJob, (v) => [
    queryKeys.myJobs,
    queryKeys.job(v.jobId),
  ]);
  registerReplayable<RaiseDisputeInput>(client, mutationKeys.raiseDispute, raiseDispute, (v) => [
    queryKeys.myJobs,
    queryKeys.job(v.jobId),
  ]);
  registerReplayable<SendMessageInput>(client, mutationKeys.sendMessage, sendMessage, (v) => [
    queryKeys.messages(v.jobId),
  ]);
  registerReplayable<Trade>(client, mutationKeys.registerSkill, registerSkill, () => [
    queryKeys.skills,
    queryKeys.openJobs,
  ]);
  registerReplayable<RegisterServiceAreaInput>(
    client,
    mutationKeys.registerServiceArea,
    registerServiceArea,
    () => [queryKeys.serviceAreas, queryKeys.openJobs],
  );

  return client;
}
