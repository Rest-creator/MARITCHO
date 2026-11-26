import { useMutation, useQuery, useQueryClient, type UseQueryResult } from "@tanstack/react-query";

import {
  fetchClientReviewsForJob,
  fetchJobReviews,
  fetchWorkerReviews,
  replyToReview,
  reportReview,
} from "@/core/api/endpoints";
import type { JobReviews, Review, ReviewPage } from "@/core/api/schemas";
import { queryKeys } from "@/core/query/keys";

export function useJobReviews(jobId: string, enabled: boolean = true): UseQueryResult<JobReviews> {
  return useQuery({
    queryKey: queryKeys.jobReviews(jobId),
    queryFn: () => fetchJobReviews(jobId),
    enabled,
    // The other party can review at any moment, which reveals both reviews:
    // never trust a cached copy when the screen opens.
    staleTime: 0,
    refetchOnMount: "always",
  });
}

export function useWorkerReviews(workerId: string | undefined): UseQueryResult<ReviewPage> {
  return useQuery({
    queryKey: queryKeys.workerReviews(workerId ?? ""),
    queryFn: () => fetchWorkerReviews(workerId ?? ""),
    enabled: workerId !== undefined && workerId !== "",
  });
}

export function useClientReviewsForJob(jobId: string): UseQueryResult<ReviewPage> {
  return useQuery({
    queryKey: queryKeys.clientReviewsForJob(jobId),
    queryFn: () => fetchClientReviewsForJob(jobId),
    // Nice to have on a job page; never worth an error state.
    retry: false,
  });
}

/** Reply and report need a connection: they're answered on the spot. */
export function useReplyToReview(workerId: string) {
  const queryClient = useQueryClient();
  return useMutation<Review, Error, { reviewId: string; reply: string }>({
    mutationFn: ({ reviewId, reply }) => replyToReview(reviewId, reply),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.workerReviews(workerId) }),
  });
}

export function useReportReview() {
  return useMutation<Review, Error, { reviewId: string; reason: string }>({
    mutationFn: ({ reviewId, reason }) => reportReview(reviewId, reason),
  });
}
