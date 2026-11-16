import { useMutation, useQuery, type UseQueryResult } from "@tanstack/react-query";

import {
  fetchAssignedJobs,
  fetchDisputes,
  fetchJob,
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
} from "@/core/api/endpoints";
import type {
  Dispute,
  Job,
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

export function useMyJobs(): UseQueryResult<MyJob[]> {
  return useQuery({ queryKey: queryKeys.myJobs, queryFn: fetchMyJobs, ...CHANGED_BY_OTHERS });
}

export function useJob(jobId: string): UseQueryResult<Job> {
  return useQuery({
    queryKey: queryKeys.job(jobId),
    queryFn: () => fetchJob(jobId),
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

export function useOpenJobs(): UseQueryResult<OpenJob[]> {
  return useQuery({
    queryKey: queryKeys.openJobs,
    queryFn: ({ signal }) => fetchOpenJobs(undefined, signal),
    ...CHANGED_BY_OTHERS,
  });
}

export function useOpenJobsSearch(query: string): UseQueryResult<OpenJob[]> {
  const trimmed = query.trim();
  return useQuery({
    queryKey: queryKeys.openJobsSearch(trimmed),
    queryFn: ({ signal }) => fetchOpenJobs(trimmed, signal),
    enabled: trimmed.length >= 2,
    staleTime: 10_000,
  });
}

export function useSearchOpenJobs(
  query: string,
  options: { trade?: Trade; suburb?: string } = {},
): UseQueryResult<JobSearchResult[]> {
  const trimmed = query.trim();
  return useQuery({
    queryKey: queryKeys.jobSearch(trimmed, options.trade ?? "", options.suburb ?? ""),
    queryFn: ({ signal }) =>
      searchOpenJobs({ q: trimmed, trade: options.trade, suburb: options.suburb }, signal),
    enabled: trimmed.length >= 2,
    staleTime: 10_000,
  });
}

export function useSearchSkills(query: string): UseQueryResult<SkillSearchResult[]> {
  const trimmed = query.trim();
  return useQuery({
    queryKey: queryKeys.skillSearch(trimmed),
    queryFn: ({ signal }) => searchSkillsVector(trimmed, signal),
    enabled: trimmed.length >= 2,
    staleTime: 60_000,
  });
}

export function useAssignedJobs(): UseQueryResult<Job[]> {
  return useQuery({
    queryKey: queryKeys.assignedJobs,
    queryFn: fetchAssignedJobs,
    ...CHANGED_BY_OTHERS,
  });
}

export function useMyOffers(): UseQueryResult<MyOffer[]> {
  return useQuery({ queryKey: queryKeys.myOffers, queryFn: fetchMyOffers, ...CHANGED_BY_OTHERS });
}

/*
 * Writes — the mutationFn comes from the defaults registered in
 * query-client.ts, so a write made offline is queued, persisted and
 * replayed when the connection returns.
 */

export function useCreateJob() {
  return useMutation<Job, Error, CreateJobInput>({ mutationKey: mutationKeys.createJob });
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
