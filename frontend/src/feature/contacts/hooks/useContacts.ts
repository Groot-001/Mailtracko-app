import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { AxiosProgressEvent } from "axios";
import {
  listContacts,
  importContactsCsv,
  exportContactsCsv,
  createContact,
} from "../api/contactsApi";
import type { ListContactsParams } from "../types/contacts.types";

export const CONTACTS_KEY = ["contacts"] as const;

export const useContacts = (listUuid?: string, params?: ListContactsParams) => {
  return useQuery({
    queryKey: [...CONTACTS_KEY, "list", listUuid, params],
    queryFn: () => listContacts(listUuid!, params),
    enabled: !!listUuid,
    staleTime: 1000 * 30,
    refetchInterval: 30_000,
    refetchIntervalInBackground: false,
  });
};

export const useImportContactsCsv = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ listUuid, file, onUploadProgress }: { listUuid: string; file: File; onUploadProgress?: (e: AxiosProgressEvent) => void }) =>
      importContactsCsv(listUuid, file, { onUploadProgress }),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: [...CONTACTS_KEY, "list", variables.listUuid] });
      queryClient.invalidateQueries({ queryKey: ["contact-lists"] });
      queryClient.invalidateQueries({ queryKey: [...CONTACTS_KEY, "import-history"] });
    },
  });
};

export const useCreateContact = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      listUuid,
      payload,
    }: {
      listUuid: string;
      payload: { email: string; metadata?: Record<string, string>; subscribed?: boolean };
    }) => createContact(listUuid, payload),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: [...CONTACTS_KEY, "list", variables.listUuid] });
      queryClient.invalidateQueries({ queryKey: ["contact-lists"] });
    },
  });
};

export const useDeleteContact = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ listUuid, contactUuid }: { listUuid: string; contactUuid: string }) =>
      // lazy import to avoid circulars
      import("../api/contactsApi").then((m) => m.deleteContact(listUuid, contactUuid)),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: [...CONTACTS_KEY, "list", variables.listUuid] });
      queryClient.invalidateQueries({ queryKey: ["contact-lists"] });
    },
  });
};

export const useExportContactsCsv = () => {
  return useMutation({
    mutationFn: (listUuid: string) => exportContactsCsv(listUuid),
  });
};
