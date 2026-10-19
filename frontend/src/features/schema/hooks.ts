import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError } from "@/lib/api/client";
import { schemaApi } from "@/lib/api/schema";

export function useSchema(connectionId: string | undefined) {
  return useQuery({
    queryKey: ["schema", connectionId],
    queryFn: () => schemaApi.get(connectionId as string),
    enabled: Boolean(connectionId),
    // A 404 means "not discovered yet": that's a state, not something to retry.
    retry: (count, error) => !(error instanceof ApiError && error.status === 404) && count < 1,
  });
}

export function useRefreshSchema() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (connectionId: string) => schemaApi.refresh(connectionId),
    onSuccess: (data, connectionId) => queryClient.setQueryData(["schema", connectionId], data.snapshot),
  });
}

export function useRetrieve() {
  return useMutation({
    mutationFn: (args: { connectionId: string; question: string }) =>
      schemaApi.retrieve(args.connectionId, args.question),
  });
}