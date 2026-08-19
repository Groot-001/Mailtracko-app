import { useQuery } from "@tanstack/react-query";
import { getContactListCount, listContactLists, listEmailAccounts } from "./workspaceApi";

export const useEmailAccounts = () =>
  useQuery({
    queryKey: ["email-accounts", "list"],
    queryFn: listEmailAccounts,
    staleTime: 1000 * 60 * 2,
  });

export const useContactLists = () =>
  useQuery({
    queryKey: ["contact-lists", "list"],
    queryFn: listContactLists,
    staleTime: 1000 * 60 * 2,
  });

export const useContactListCount = (listUuid?: string) =>
  useQuery({
    queryKey: ["contact-lists", listUuid, "count"],
    queryFn: () => getContactListCount(listUuid as string),
    enabled: Boolean(listUuid),
  });
