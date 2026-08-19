import { api } from "../../../shared/api/axios";
import type { AxiosProgressEvent } from "axios";
import type {
  ContactList,
  Contact,
  ImportSuccessData,
  SheetsOAuthInitResponse,
  SheetsTabsResponse,
  TimelineItem,
  ListContactsParams,
} from "../types/contacts.types";

interface ApiResponseEnvelope<T> {
  success: boolean;
  message?: string;
  data: T;
}

// ─── Contact List CRUD ────────────────────────────────────────────────────────

export const createContactList = async (
  name: string,
  description?: string
): Promise<ContactList> => {
  // Spec: POST /contact-lists/ (trailing slash required)
  const { data } = await api.post<ApiResponseEnvelope<ContactList>>("/contact-lists/", {
    name,
    description: description || undefined,
  });
  return data.data;
};

export const listContactLists = async (
  limit = 50,
  offset = 0
): Promise<{ items: ContactList[]; total: number; limit: number; offset: number }> => {
  const { data } = await api.get<
    ApiResponseEnvelope<{ items: ContactList[]; total: number; limit: number; offset: number }>
  >("/contact-lists/", {
    params: { limit, offset },
  });
  return data.data;
};

export const getContactList = async (listUuid: string): Promise<ContactList> => {
  const { data } = await api.get<ApiResponseEnvelope<ContactList>>(`/contact-lists/${listUuid}`);
  return data.data;
};

export const updateContactList = async (
  listUuid: string,
  payload: { name?: string; description?: string }
): Promise<ContactList> => {
  const { data } = await api.patch<ApiResponseEnvelope<ContactList>>(
    `/contact-lists/${listUuid}`,
    payload
  );
  return data.data;
};

export interface ContactListCampaignUsage {
  in_use: boolean;
  campaigns: Array<{ uuid: string; name: string; status: string; scheduled_at: string | null }>;
}

export const getContactListCampaignUsage = async (listUuid: string): Promise<ContactListCampaignUsage> => {
  const { data } = await api.get<ApiResponseEnvelope<ContactListCampaignUsage>>(
    `/contact-lists/${listUuid}/campaign-usage`
  );
  return data.data;
};

export const deleteContactList = async (listUuid: string, force = false): Promise<ContactList> => {
  const { data } = await api.delete<ApiResponseEnvelope<ContactList>>(
    `/contact-lists/${listUuid}`,
    { params: { force } },
  );
  return data.data;
};

// ─── Contacts inside list ─────────────────────────────────────────────────────

export const listContacts = async (
  listUuid: string,
  params?: ListContactsParams
): Promise<{ items: Contact[]; total: number; limit: number; offset: number }> => {
  const { data } = await api.get<
    ApiResponseEnvelope<{ items: Contact[]; total: number; limit: number; offset: number }>
  >(`/contact-lists/${listUuid}/contacts`, {
    params: {
      limit: params?.limit ?? 199,
      offset: params?.offset ?? 0,
      search: params?.search || undefined,
      subscribed: params?.subscribed,
      company: params?.company || undefined,
      tag: params?.tag || undefined,
      status: params?.status || undefined,
      verification_status: params?.verification_status || undefined,
      sort_by: params?.sort_by ?? "created_at",
      sort_order: params?.sort_order ?? "desc",
    },
  });
  return data.data;
};

export const createContact = async (
  listUuid: string,
  payload: { email: string; metadata?: Record<string, string>; subscribed?: boolean }
): Promise<Contact> => {
  const { data } = await api.post<ApiResponseEnvelope<Contact>>(
    `/contact-lists/${listUuid}/contacts`,
    payload
  );
  return data.data;
};

export const deleteContact = async (listUuid: string, contactUuid: string): Promise<Contact> => {
  const { data } = await api.delete<ApiResponseEnvelope<Contact>>(
    `/contact-lists/${listUuid}/contacts/${contactUuid}`
  );
  return data.data;
};

export const exportContactsCsv = async (listUuid: string): Promise<void> => {
  const url = `${api.defaults.baseURL}/contact-lists/${listUuid}/contacts/export`;
  // We can fetch via axios with responseType: 'blob' or direct fetch
  const response = await api.get(url, { responseType: "blob" });
  const blob = new Blob([response.data], { type: "text/csv" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `contacts-${listUuid}.csv`;
  link.click();
  URL.revokeObjectURL(link.href);
};

export const importContactsCsv = async (
  listUuid: string,
  file: File,
  options?: { onUploadProgress?: (e: AxiosProgressEvent) => void }
): Promise<ImportSuccessData> => {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post<ApiResponseEnvelope<ImportSuccessData>>(
    `/contact-lists/${listUuid}/import`,
    formData,
    {
      headers: {
        // Override the default JSON content type so the browser can set the multipart boundary.
        "Content-Type": undefined,
      },
      onUploadProgress: options?.onUploadProgress,
    }
  );
  return data.data;
};

export const updateContact = async (
  listUuid: string,
  contactUuid: string,
  payload: {
    email?: string;
    metadata?: Record<string, string | null>;
    subscribed?: boolean;
    status?: Contact["status"];
  },
): Promise<Contact> => {
  const { data } = await api.patch<ApiResponseEnvelope<Contact>>(
    `/contact-lists/${listUuid}/contacts/${contactUuid}`,
    payload,
  );
  return data.data;
};

export const verifyContactEmail = async (
  listUuid: string,
  contactUuid: string,
): Promise<Contact> => {
  const { data } = await api.post<ApiResponseEnvelope<Contact>>(
    `/contact-lists/${listUuid}/contacts/${contactUuid}/verify`,
  );
  return data.data;
};

export const bulkVerifyContactEmails = async (
  listUuid: string,
  contactUuids: string[],
): Promise<{ items: Contact[]; total: number }> => {
  const { data } = await api.post<
    ApiResponseEnvelope<{ items: Contact[]; total: number }>
  >(`/contact-lists/${listUuid}/contacts/verify/bulk`, {
    contact_uuids: contactUuids,
  });
  return data.data;
};

export interface ContactImportHistoryItem {
  uuid: string;
  filename: string;
  total_rows: number;
  success_count: number;
  error_count: number;
  errors: Array<{ row?: number; error?: string; message?: string }>;
  status: string;
  created_at: string;
  updated_at?: string | null;
}

export const getContactImportHistory = async (): Promise<{
  items: ContactImportHistoryItem[];
  total: number;
}> => {
  const { data } = await api.get<
    ApiResponseEnvelope<{ items: ContactImportHistoryItem[]; total: number }>
  >("/contact-lists/import-history");
  return data.data;
};

// ─── Google Sheets Import ─────────────────────────────────────────────────────

export const initGoogleSheetsOauth = async (): Promise<SheetsOAuthInitResponse> => {
  const { data } = await api.post<ApiResponseEnvelope<SheetsOAuthInitResponse>>(
    "/contact-lists/sheets/oauth/init"
  );
  return data.data;
};

export const listGoogleSheetsTabs = async (sheetUrl: string): Promise<SheetsTabsResponse> => {
  const { data } = await api.post<ApiResponseEnvelope<SheetsTabsResponse>>(
    "/contact-lists/sheets/tabs",
    { sheet_url: sheetUrl }
  );
  return data.data;
};

export const importFromGoogleSheet = async (
  listUuid: string,
  sheetUrl: string,
  tabName: string
): Promise<ImportSuccessData> => {
  const { data } = await api.post<ApiResponseEnvelope<ImportSuccessData>>(
    `/contact-lists/${listUuid}/sheets/import`,
    {
      sheet_url: sheetUrl,
      tab: tabName,
    }
  );
  return data.data;
};

// ─── Timeline / Activities ────────────────────────────────────────────────────

export const getContactTimeline = async (
  listUuid: string,
  contactUuid: string,
  limit = 50,
  offset = 0
): Promise<{ items: TimelineItem[]; total: number; limit: number; offset: number }> => {
  const { data } = await api.get<
    ApiResponseEnvelope<{ items: TimelineItem[]; total: number; limit: number; offset: number }>
  >(`/contact-lists/${listUuid}/contacts/${contactUuid}/timeline`, {
    params: { limit, offset },
  });
  return data.data;
};
