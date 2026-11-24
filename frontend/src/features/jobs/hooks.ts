import { useMutation, useQuery, type UseQueryResult } from "@tanstack/react-query";

import { useDebouncedValue } from "@/core/hooks/useDebouncedValue";
import {
  fetchAssignedJobs,
  fetchDisputes,
  fetchJob,
  fetchJobEligibility,
  fetchMatches,
  fetchMyJobs,
  fetchMyOffers,
  fetchOpenJobs,
  fetchRecord,
  searchOpenJobs,
  searchSkillsVector,
  type BookJobInput,
  type CompleteJobInput,
  type CreateJobInput,
  type RaiseDisputeInput,
  type RespondToDisputeInput,
  type SubmitOfferInput,
  type SubmitQuoteInput,
  type SubmitReviewInput,
  type UpdateJobInput,
} from "@/core/api/endpoints";
import type {
  Dispute,
  Job,
  JobEligibility,
  JobOffer,
  JobSearchResult,
  MatchCandidate,
  MyJob,
  MyOffer,
  OpenJob,
  RecordEntry,
  SkillSearchResult,
  Trade,
} from "@/core/api/schemas";
import { mutationKeys, queryKeys } from "@/core/query/keys";

/* Reads — cached on the device and served first when offline. */

/**
 * Jobs and offers are changed by the *other* person (a new job posted, an
 * offer accepted, a price confirmed on site), so the cached copy is shown
 * straight away but always re-checked when a screen opens. Otherwise a
 * reload within the default 30 s keeps showing the old list.
 */
const CHANGED_BY_OTHERS = { staleTime: 0 } as const;

export function useMyJobs(isEnabled: boolean = true): UseQueryResult<MyJob[]> {
  return useQuery({
    queryKey: queryKeys.myJobs,
    queryFn: fetchMyJobs,
    enabled: isEnabled,
    ...CHANGED_BY_OTHERS,
  });
}

export function useJob(jobId: string): UseQueryResult<Job> {
  return useQuery({
    queryKey: queryKeys.job(jobId),
    queryFn: () => fetchJob(jobId),
    enabled: jobId.length > 0,
    ...CHANGED_BY_OTHERS,
  });
}

/**
 * How often a buyer waiting on an open job checks who accepted: like
 * inDrive, answers should show up while they watch. Small payload.
 */
const OFFER_POLL_MS = 15_000;

/**
 * Offers arrive while the buyer watches, so this list is never treated as
 * fresh: refetch on every visit, on returning to the tab, and every
 * 15 s while the job is open.
 */
export function useMatches(
  jobId: string,
  isEnabled: boolean = true,
): UseQueryResult<MatchCandidate[]> {
  return useQuery({
    queryKey: queryKeys.matches(jobId),
    queryFn: () => fetchMatches(jobId),
    enabled: isEnabled,
    staleTime: 0,
    refetchInterval: isEnabled ? OFFER_POLL_MS : false,
    refetchOnWindowFocus: isEnabled,
  });
}

export function useRecord(jobId: string, isEnabled: boolean): UseQueryResult<RecordEntry> {
  return useQuery({
    queryKey: queryKeys.record(jobId),
    queryFn: () => fetchRecord(jobId),
    enabled: isEnabled,
  });
}

export function useDisputes(jobId: string, isEnabled: boolean): UseQueryResult<Dispute[]> {
  return useQuery({
    queryKey: queryKeys.disputes(jobId),
    queryFn: () => fetchDisputes(jobId),
    enabled: isEnabled,
  });
}

/** Why a job isn't on this worker's list (skills mismatch vs. already filled). */
export function useJobEligibility(
  jobId: string,
  isEnabled: boolean,
): UseQueryResult<JobEligibility> {
  return useQuery({
    queryKey: queryKeys.jobEligibility(jobId),
    queryFn: () => fetchJobEligibility(jobId),
    enabled: isEnabled,
    staleTime: 60_000,
    retry: false,
  });
}

export function useOpenJobs(isEnabled: boolean = true): UseQueryResult<OpenJob[]> {
  return useQuery({
    queryKey: queryKeys.openJobs,
    queryFn: ({ signal }) => fetchOpenJobs(undefined, signal),
    enabled: isEnabled,
    ...CHANGED_BY_OTHERS,
  });
}

export function useOpenJobsSearch(query: string): UseQueryResult<OpenJob[]> {
  const trimmed = query.trim();
  const debounced = useDebouncedValue(trimmed, 350);
  return useQuery({
    queryKey: queryKeys.openJobsSearch(debounced),
    queryFn: ({ signal }) => fetchOpenJobs(debounced, signal),
    enabled: debounced.length >= 2,
    staleTime: 10_000,
  });
}

export function useSearchOpenJobs(
  query: string,
  options: { trade?: Trade; suburb?: string } = {},
): UseQueryResult<JobSearchResult[]> {
  const trimmed = query.trim();
  const debounced = useDebouncedValue(trimmed, 350);
  return useQuery({
    queryKey: queryKeys.jobSearch(debounced, options.trade ?? "", options.suburb ?? ""),
    queryFn: ({ signal }) =>
      searchOpenJobs({ q: debounced, trade: options.trade, suburb: options.suburb }, signal),
    enabled: debounced.length >= 2,
    staleTime: 10_000,
  });
}

export function useSearchSkills(query: string): UseQueryResult<SkillSearchResult[]> {
  const trimmed = query.trim();
  const debounced = useDebouncedValue(trimmed, 250);
  return useQuery({
    queryKey: queryKeys.skillSearch(debounced),
    queryFn: ({ signal }) => searchSkillsVector(debounced, signal),
    enabled: debounced.length >= 2,
    staleTime: 60_000,
  });
}

export function useAssignedJobs(isEnabled: boolean = true): UseQueryResult<Job[]> {
  return useQuery({
    queryKey: queryKeys.assignedJobs,
    queryFn: fetchAssignedJobs,
    enabled: isEnabled,
    ...CHANGED_BY_OTHERS,
  });
}

export function useMyOffers(isEnabled: boolean = true): UseQueryResult<MyOffer[]> {
  return useQuery({
    queryKey: queryKeys.myOffers,
    queryFn: fetchMyOffers,
    enabled: isEnabled,
    ...CHANGED_BY_OTHERS,
  });
}

/*
 * Writes — the mutationFn comes from the defaults registered in
 * query-client.ts, so a write made offline is queued, persisted and
 * replayed when the connection returns.
 */

export function useCreateJob() {
  return useMutation<Job, Error, CreateJobInput>({ mutationKey: mutationKeys.createJob });
}

export function useUpdateJob() {
  return useMutation<Job, Error, UpdateJobInput>({ mutationKey: mutationKeys.updateJob });
}

export function useSubmitOffer() {
  return useMutation<JobOffer, Error, SubmitOfferInput>({ mutationKey: mutationKeys.submitOffer });
}

export function useBookJob() {
  return useMutation<Job, Error, BookJobInput>({ mutationKey: mutationKeys.bookJob });
}

export function useSubmitQuote() {
  return useMutation<Job, Error, SubmitQuoteInput>({ mutationKey: mutationKeys.submitQuote });
}

export function useCompleteJob() {
  return useMutation<Job, Error, CompleteJobInput>({ mutationKey: mutationKeys.completeJob });
}

export function useSubmitReview() {
  return useMutation<void, Error, SubmitReviewInput>({ mutationKey: mutationKeys.submitReview });
}

export function useRaiseDispute() {
  return useMutation<Dispute, Error, RaiseDisputeInput>({ mutationKey: mutationKeys.raiseDispute });
}

export function useRespondToDispute() {
  return useMutation<Dispute, Error, RespondToDisputeInput>({
    mutationKey: mutationKeys.respondToDispute,
  });
}
