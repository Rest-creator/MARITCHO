import { useQuery } from "@tanstack/react-query";

import { fetchMediaCapability } from "@/core/media/upload";
import { queryKeys } from "@/core/query/keys";

/**
 * Whether photos and voice notes can be sent yet (WEB-004). False until the
 * backend has its upload endpoint, and while it can't be asked (offline):
 * then photos stay on the phone, as before.
 */
export function useMediaUploads(): boolean {
  const capability = useQuery({
    queryKey: queryKeys.mediaUploads,
    queryFn: fetchMediaCapability,
    staleTime: 60 * 60_000,
    retry: false,
  });
  return capability.data === true;
}
