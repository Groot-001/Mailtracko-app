import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  initGoogleSheetsOauth,
  listGoogleSheetsTabs,
  importFromGoogleSheet,
} from "../api/contactsApi";
import { CONTACTS_KEY } from "./useContacts";

export const GOOGLE_SHEETS_KEY = ["google-sheets"] as const;

export const useGoogleSheetsInit = () => {
  return useMutation({
    mutationFn: initGoogleSheetsOauth,
  });
};

export const useGoogleSheetsTabs = (sheetUrl?: string) => {
  return useQuery({
    queryKey: [...GOOGLE_SHEETS_KEY, "tabs", sheetUrl],
    queryFn: () => listGoogleSheetsTabs(sheetUrl!),
    enabled: !!sheetUrl,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
};

export const useImportFromGoogleSheet = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      listUuid,
      sheetUrl,
      tabName,
    }: {
      listUuid: string;
      sheetUrl: string;
      tabName: string;
    }) => importFromGoogleSheet(listUuid, sheetUrl, tabName),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: [...CONTACTS_KEY, "list", variables.listUuid] });
      queryClient.invalidateQueries({ queryKey: ["contact-lists"] });
      queryClient.invalidateQueries({ queryKey: [...CONTACTS_KEY, "import-history"] });
    },
  });
};
