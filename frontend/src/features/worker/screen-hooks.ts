import { useQuery, useQueryClient, type UseQueryResult } from "@tanstack/react-query";

import { fetchWorkerHomeScreen, fetchWorkerWorkScreen } from "@/core/api/endpoints";
import type { WorkerHomeScreen, WorkerWorkScreen } from "@/core/api/schemas";
import { queryKeys } from "@/core/query/keys";

/*
 * One request per worker screen (ADR-009 phase 2). Each bundle also fills
 * the per-list caches it contains, so a screen opened next (job detail,
 * skills) already has its data and the offline copy stays complete.
 * Re-checked on every visit, like the lists it replaces: other people
 * change this data.
 */

/** W4 · My work: standing, offers and hired jobs. */
export function useWorkerWorkScreen(): UseQueryResult<WorkerWorkScreen> {
  const queryClient = useQueryClient();
  return useQuery({
    queryKey: queryKeys.workerWorkScreen,
    queryFn: async () => {
      const screen = await fetchWorkerWorkScreen();
      queryClient.setQueryData(queryKeys.standing, screen.standing);
      queryClient.setQueryData(queryKeys.myOffers, screen.offers);
      queryClient.setQueryData(queryKeys.assignedJobs, screen.assigned);
      return screen;
    },
    staleTime: 0,
  });
}

/** W2 · Jobs near you: skills, open jobs and the worker's own offers. */
export function useWorkerHomeScreen(): UseQueryResult<WorkerHomeScreen> {
  const queryClient = useQueryClient();
  return useQuery({
    queryKey: queryKeys.workerHomeScreen,
    queryFn: async () => {
      const screen = await fetchWorkerHomeScreen();
      queryClient.setQueryData(queryKeys.skills, screen.skills);
      queryClient.setQueryData(queryKeys.openJobs, screen.open_jobs);
      queryClient.setQueryData(queryKeys.myOffers, screen.offers);
      return screen;
    },
    staleTime: 0,
  });
}
