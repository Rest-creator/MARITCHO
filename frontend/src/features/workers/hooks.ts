import { useMutation, useQuery, type UseQueryResult } from "@tanstack/react-query";

import {
  fetchNearbyWorkers,
  fetchReferences,
  fetchServiceAreas,
  fetchSkills,
  fetchStanding,
  fetchSuburbs,
  fetchWorkerProfile,
  type FetchNearbyWorkersParams,
  type RegisterServiceAreaInput,
  type RegisterSkillInput,
  type UpdateUserProfileInput,
} from "@/core/api/endpoints";
import type {
  Reference,
  ServiceArea,
  Skill,
  Standing,
  Suburb,
  User,
  WorkerProfile,
  WorkerSummary,
} from "@/core/api/schemas";
import { mutationKeys, queryKeys } from "@/core/query/keys";

export function useSkills(): UseQueryResult<Skill[]> {
  return useQuery({ queryKey: queryKeys.skills, queryFn: fetchSkills });
}

export function useServiceAreas(): UseQueryResult<ServiceArea[]> {
  return useQuery({ queryKey: queryKeys.serviceAreas, queryFn: fetchServiceAreas });
}

export function useStanding(): UseQueryResult<Standing> {
  return useQuery({ queryKey: queryKeys.standing, queryFn: fetchStanding });
}

export function useReferences(): UseQueryResult<Reference[]> {
  return useQuery({ queryKey: queryKeys.references, queryFn: fetchReferences });
}

/** Suburb list changes rarely — keep it for a day. */
export function useSuburbs(): UseQueryResult<Suburb[]> {
  return useQuery({
    queryKey: queryKeys.suburbs,
    queryFn: fetchSuburbs,
    staleTime: 24 * 60 * 60_000,
  });
}

export function useRegisterSkill() {
  return useMutation<Skill, Error, RegisterSkillInput>({ mutationKey: mutationKeys.registerSkill });
}

export function useRegisterServiceArea() {
  return useMutation<ServiceArea, Error, RegisterServiceAreaInput>({
    mutationKey: mutationKeys.registerServiceArea,
  });
}

export function useUpdateUserProfile() {
  return useMutation<User, Error, UpdateUserProfileInput>({
    mutationKey: mutationKeys.updateProfile,
  });
}

export function useNearbyWorkers(
  params: FetchNearbyWorkersParams = {},
): UseQueryResult<WorkerSummary[]> {
  const suburb = params.suburb?.trim() ?? "";
  const trade = params.trade ?? "";
  const query = params.q?.trim() ?? "";
  return useQuery({
    queryKey: queryKeys.nearbyWorkers(suburb, trade, query),
    queryFn: ({ signal }) => fetchNearbyWorkers(params, signal),
  });
}

export function useWorkerProfile(workerId: string, suburb?: string): UseQueryResult<WorkerProfile> {
  const cleanSuburb = suburb?.trim() ?? "";
  return useQuery({
    queryKey: queryKeys.workerProfile(workerId, cleanSuburb),
    queryFn: ({ signal }) => fetchWorkerProfile(workerId, cleanSuburb, signal),
  });
}
