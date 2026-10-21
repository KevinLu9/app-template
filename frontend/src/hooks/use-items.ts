import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { apiGet, apiSend } from "@/lib/api";
import type { Item, ItemInput } from "@/lib/types";

const KEY = ["items"];

export function useItems() {
  return useQuery({
    queryKey: KEY,
    queryFn: async () => (await apiGet<{ items: Item[] }>("/items")).items,
  });
}

export function useCreateItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: ItemInput) => apiSend<Item>("POST", "/items", input),
    onSuccess: () => {
      toast.success("Item created");
      return queryClient.invalidateQueries({ queryKey: KEY });
    },
  });
}

export function useDeleteItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiSend<void>("DELETE", `/items/${id}`),
    onSuccess: () => {
      toast.success("Item deleted");
      return queryClient.invalidateQueries({ queryKey: KEY });
    },
  });
}
