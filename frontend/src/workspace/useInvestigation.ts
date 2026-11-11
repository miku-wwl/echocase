import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError, request } from "../api/client";
import type { Session } from "../api/client";

export type Operation = {
  route: string;
  body?: unknown;
  method?: string;
  version: number;
  key: string;
  draftRevision?: number;
};

// An operation receipt is a historical result. Only confirmed resource snapshots
// enter Query's cache, and neither a late GET nor an old receipt may regress it.
function latest(old: unknown, incoming: unknown) {
  const previous = old as Session | undefined;
  const next = incoming as Session;
  return previous && previous.version > next.version ? previous : next;
}

export function useInvestigation(id: string, owner: string) {
  const cache = useQueryClient();
  const queryKey = ["session", owner, id];
  const query = useQuery({
    queryKey,
    queryFn: ({ signal }) =>
      request<Session>(`/api/investigations/${id}`, { signal }),
    structuralSharing: latest,
    refetchInterval: 30_000,
  });
  const mutation = useMutation({
    mutationFn: (op: Operation) =>
      request<Session>(`/api/investigations/${id}/${op.route}`, {
        method: op.method ?? "POST",
        body: op.body,
        version: op.version,
        key: op.key,
      }),
    onMutate: async () => {
      await cache.cancelQueries({ queryKey });
    },
    onSuccess: (result) => {
      cache.setQueryData(queryKey, (old: Session | undefined) =>
        latest(old, result),
      );
    },
    onSettled: async () => {
      await Promise.all([
        cache.invalidateQueries({ queryKey }),
        cache.invalidateQueries({ queryKey: ["sessions"] }),
      ]);
    },
    retry: false,
  });
  const uncertain =
    mutation.error instanceof ApiError && mutation.error.status === 0;
  const blocked = mutation.isPending || uncertain;
  const act = (route: string, body?: unknown, method?: string) => {
    if (query.data && !blocked)
      mutation.mutate({
        route,
        body,
        method,
        version: query.data.version,
        key: crypto.randomUUID(),
      });
  };
  return { query, mutation, act, blocked, uncertain };
}
