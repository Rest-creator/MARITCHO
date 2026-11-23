import { MutationCache, QueryCache, QueryClient, type QueryKey } from "@tanstack/react-query";

import {
  addReference,
  bookJob,
  completeJob,
  createJob,
  raiseDispute,
  registerServiceArea,
  registerSkill,
  respondToDispute,
  sendMessage,
  submitIdPhoto,
  submitOffer,
  submitPoliceClearance,
  submitQuote,
  submitReview,
  updateJob,
  updateUserProfile,
  vouchForWorker,
  type AddReferenceInput,
  type BookJobInput,
  type CompleteJobInput,
  type CreateJobInput,
  type RaiseDisputeInput,
  type RegisterServiceAreaInput,
  type RegisterSkillInput,
  type RespondToDisputeInput,
  type SendMessageInput,
  type SubmitIdPhotoInput,
  type SubmitOfferInput,
  type SubmitPoliceClearanceInput,
  type SubmitQuoteInput,
  type SubmitReviewInput,
  type UpdateJobInput,
  type UpdateUserProfileInput,
  type VouchForWorkerInput,
} from "@/core/api/endpoints";
import { ApiError } from "@/core/api/http";
import { mutationKeys, queryKeys } from "@/core/query/keys";

export const UNAUTHORIZED_EVENT = "maricho:unauthorized";

/** Cached data stays usable offline for a week — the same window as a session. */
export const CACHE_MAX_AGE_MS = 1000 * 60 * 60 * 24 * 7;

function notifyUnauthorized(error: unknown): void {
  if (error instanceof ApiError && error.isUnauthorized && typeof window !== "undefined") {
    window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
  }
}

/**
 * A signed-out (`null`) session is never written to the device: restoring a
 * stale `null` right after signing in would bounce the person back to sign-up.
 * A signed-in session *is* kept, so the app still opens offline.
 */
export function shouldPersistQuery(queryKey: QueryKey, data: unknown): boolean {
  const isSession =
    queryKey.length === queryKeys.session.length && queryKey[0] === queryKeys.session[0];
  return !(isSession && data === null);
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
  registerReplayable<UpdateJobInput>(client, mutationKeys.updateJob, updateJob, (v) => [
    queryKeys.myJobs,
    queryKeys.job(v.jobId),
    queryKeys.matches(v.jobId),
    queryKeys.openJobs,
    queryKeys.screens,
  ]);
  registerReplayable<SubmitOfferInput>(client, mutationKeys.submitOffer, submitOffer, () => [
    queryKeys.myOffers,
    queryKeys.openJobs,
    queryKeys.screens,
  ]);
  registerReplayable<BookJobInput>(client, mutationKeys.bookJob, bookJob, (v) => [
    queryKeys.myJobs,
    queryKeys.job(v.jobId),
  ]);
  registerReplayable<SubmitQuoteInput>(client, mutationKeys.submitQuote, submitQuote, (v) => [
    queryKeys.assignedJobs,
    queryKeys.job(v.jobId),
    queryKeys.screens,
  ]);
  registerReplayable<CompleteJobInput>(client, mutationKeys.completeJob, completeJob, (v) => [
    queryKeys.myJobs,
    queryKeys.job(v.jobId),
  ]);
  registerReplayable<SubmitReviewInput>(client, mutationKeys.submitReview, submitReview, (v) => [
    queryKeys.job(v.jobId),
    queryKeys.standing,
    queryKeys.screens,
  ]);
  registerReplayable<RaiseDisputeInput>(client, mutationKeys.raiseDispute, raiseDispute, (v) => [
    queryKeys.myJobs,
    queryKeys.job(v.jobId),
  ]);
  registerReplayable<RespondToDisputeInput>(
    client,
    mutationKeys.respondToDispute,
    respondToDispute,
    (v) => [
      queryKeys.assignedJobs,
      queryKeys.disputes(v.jobId),
      queryKeys.job(v.jobId),
      queryKeys.screens,
    ],
  );
  registerReplayable<SendMessageInput>(client, mutationKeys.sendMessage, sendMessage, (v) => [
    queryKeys.messages(v.jobId),
  ]);
  registerReplayable<RegisterSkillInput>(client, mutationKeys.registerSkill, registerSkill, () => [
    queryKeys.skills,
    queryKeys.openJobs,
    queryKeys.screens,
  ]);
  registerReplayable<RegisterServiceAreaInput>(
    client,
    mutationKeys.registerServiceArea,
    registerServiceArea,
    () => [queryKeys.serviceAreas, queryKeys.openJobs, queryKeys.screens],
  );
  registerReplayable<UpdateUserProfileInput>(
    client,
    mutationKeys.updateProfile,
    updateUserProfile,
    () => [queryKeys.session, queryKeys.openJobs, queryKeys.screens],
  );
  registerReplayable<SubmitIdPhotoInput>(client, mutationKeys.submitIdPhoto, submitIdPhoto, () => [
    queryKeys.vetting,
    queryKeys.standing,
    queryKeys.screens,
  ]);
  registerReplayable<SubmitPoliceClearanceInput>(
    client,
    mutationKeys.submitPoliceClearance,
    submitPoliceClearance,
    () => [queryKeys.vetting, queryKeys.standing, queryKeys.screens],
  );
  registerReplayable<AddReferenceInput>(client, mutationKeys.addReference, addReference, () => [
    queryKeys.references,
    queryKeys.vetting,
    queryKeys.standing,
    queryKeys.screens,
  ]);
  registerReplayable<VouchForWorkerInput>(
    client,
    mutationKeys.vouchForWorker,
    vouchForWorker,
    () => [queryKeys.vetting, queryKeys.standing],
  );

  return client;
}
