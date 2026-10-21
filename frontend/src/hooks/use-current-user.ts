import { useQuery } from "@tanstack/react-query";

import { apiGet } from "@/lib/api";
import type { CurrentUser } from "@/lib/types";

export function useCurrentUser() {
  return useQuery({
    queryKey: ["me"],
    queryFn: () => apiGet<CurrentUser>("/me"),
    staleTime: 5 * 60 * 1000,
  });
}
