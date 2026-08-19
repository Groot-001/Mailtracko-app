import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  createContactList,
  listContactLists,
  getContactList,
  updateContactList,
  deleteContactList,
} from "../api/contactsApi";

export const CONTACT_LISTS_KEY = ["contact-lists"] as const;

export const useContactLists = (limit = 100, offset = 0) => {
  return useQuery({
    queryKey: [...CONTACT_LISTS_KEY, limit, offset],
    queryFn: () => listContactLists(limit, offset),
    staleTime: 1000 * 30,
    refetchInterval: 30_000,
    refetchIntervalInBackground: false,
  });
};

export const useContactListDetail = (listUuid?: string) => {
  return useQuery({
    queryKey: [...CONTACT_LISTS_KEY, "detail", listUuid],
    queryFn: () => getContactList(listUuid!),
    enabled: !!listUuid,
  });
};

export const useCreateContactList = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ name, description }: { name: string; description?: string }) =>
      createContactList(name, description),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CONTACT_LISTS_KEY });
    },
  });
};

export const useUpdateContactList = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      listUuid,
      name,
      description,
    }: {
      listUuid: string;
      name?: string;
      description?: string;
    }) => updateContactList(listUuid, { name, description }),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: CONTACT_LISTS_KEY });
      queryClient.invalidateQueries({
        queryKey: [...CONTACT_LISTS_KEY, "detail", variables.listUuid],
      });
    },
  });
};

export const useDeleteContactList = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (listUuid: string) => deleteContactList(listUuid),
    onSuccess: (_data, listUuid) => {
      queryClient.invalidateQueries({ queryKey: CONTACT_LISTS_KEY });
      queryClient.invalidateQueries({ queryKey: [...CONTACT_LISTS_KEY, "detail", listUuid] });
    },
  });
};
