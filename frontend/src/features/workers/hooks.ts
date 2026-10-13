import { useMutation, useQuery, type UseQueryResult } from "@tanstack/react-query";

import {
  fetchReferences,
  fetchServiceAreas,
  fetchSkills,
  fetchStanding,
  fetchSuburbs,
  type RegisterServiceAreaInput,
} from "@/core/api/endpoints";
import type { Reference, ServiceArea, Skill, Standing, Suburb, Trade } from "@/core/api/schemas";
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
  return useMutation<Skill, Error, Trade>({ mutationKey: mutationKeys.registerSkill });
}

export function useRegisterServiceArea() {
  return useMutation<ServiceArea, Error, RegisterServiceAreaInput>({
    mutationKey: mutationKeys.registerServiceArea,
  });
}
