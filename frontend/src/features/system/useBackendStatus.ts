import { useQuery } from "@tanstack/react-query";
import { getBackendStatus } from "@/lib/api/health";

export function useBackendStatus() {
  return useQuery({
    queryKey: ["backend-status"],
    queryFn: getBackendStatus,
    refetchInterval: 15_000,
    staleTime: 10_000,
  });
}