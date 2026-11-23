import { useMutation, useQuery, type UseQueryResult } from "@tanstack/react-query";

import {
  fetchNearbyWorkers,
  fetchReferences,
  fetchServiceAreas,
  fetchSkills,
  fetchStanding,
  fetchSuburbs,
  fetchWorkerProfile,
  fetchWorkerVetting,
  type AddReferenceInput,
  type FetchNearbyWorkersParams,
  type RegisterServiceAreaInput,
  type RegisterSkillInput,
  type SubmitIdPhotoInput,
  type SubmitPoliceClearanceInput,
  type UpdateUserProfileInput,
  type VouchForWorkerInput,
} from "@/core/api/endpoints";
import type {
  Reference,
  ServiceArea,
  Skill,
  Standing,
  Suburb,
  User,
  Vouch,
  WorkerProfile,
  WorkerSummary,
  WorkerVetting,
} from "@/core/api/schemas";
import { mutationKeys, queryKeys } from "@/core/query/keys";

export function useSkills(enabled: boolean = true): UseQueryResult<Skill[]> {
  return useQuery({ queryKey: queryKeys.skills, queryFn: fetchSkills, enabled });
}

export function useServiceAreas(enabled: boolean = true): UseQueryResult<ServiceArea[]> {
  return useQuery({ queryKey: queryKeys.serviceAreas, queryFn: fetchServiceAreas, enabled });
}

export function useStanding(enabled: boolean = true): UseQueryResult<Standing> {
  return useQuery({ queryKey: queryKeys.standing, queryFn: fetchStanding, enabled });
}

export function useWorkerVetting(enabled: boolean = true): UseQueryResult<WorkerVetting> {
  return useQuery({ queryKey: queryKeys.vetting, queryFn: fetchWorkerVetting, enabled });
}

export function useReferences(enabled: boolean = true): UseQueryResult<Reference[]> {
  return useQuery({ queryKey: queryKeys.references, queryFn: fetchReferences, enabled });
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

export function useSubmitIdPhoto() {
  return useMutation<WorkerVetting, Error, SubmitIdPhotoInput>({
    mutationKey: mutationKeys.submitIdPhoto,
  });
}

export function useSubmitPoliceClearance() {
  return useMutation<WorkerVetting, Error, SubmitPoliceClearanceInput>({
    mutationKey: mutationKeys.submitPoliceClearance,
  });
}

export function useAddReference() {
  return useMutation<Reference, Error, AddReferenceInput>({
    mutationKey: mutationKeys.addReference,
  });
}

export function useVouchForWorker() {
  return useMutation<Vouch, Error, VouchForWorkerInput>({
    mutationKey: mutationKeys.vouchForWorker,
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
