import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { connectionsApi, type ConnectionInput, type ConnectionPatch } from "@/lib/api/connections";

const KEY = ["connections"] as const;

export function useConnections() {
  return useQuery({ queryKey: KEY, queryFn: connectionsApi.list });
}

export function useConnectionMutations() {
  const queryClient = useQueryClient();
  const refresh = () => queryClient.invalidateQueries({ queryKey: KEY });
  return {
    create: useMutation({
      mutationFn: (input: ConnectionInput) => connectionsApi.create(input),
      onSuccess: refresh,
    }),
    update: useMutation({
      mutationFn: (args: { id: string; input: ConnectionPatch }) => connectionsApi.update(args.id, args.input),
      onSuccess: refresh,
    }),
    test: useMutation({ mutationFn: (id: string) => connectionsApi.test(id), onSuccess: refresh }),
    disconnect: useMutation({ mutationFn: (id: string) => connectionsApi.disconnect(id), onSuccess: refresh }),
    remove: useMutation({ mutationFn: (id: string) => connectionsApi.remove(id), onSuccess: refresh }),
  };
}