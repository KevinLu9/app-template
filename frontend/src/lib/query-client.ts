import { MutationCache, QueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { ApiError } from "@/lib/api";

export function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        refetchOnWindowFocus: false,
        // Don't retry client errors (401/403/404...); they won't fix themselves.
        retry: (count, error) => !(error instanceof ApiError && error.status < 500) && count < 2,
      },
    },
    mutationCache: new MutationCache({
      onError: (error) => toast.error(error.message),
    }),
  });
}
