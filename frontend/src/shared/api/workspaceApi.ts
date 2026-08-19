import { api } from "./axios";
import type { ApiSuccessResponse, PaginatedResponse } from "../types/api.types";

export interface EmailAccount {
  uuid: string;
  organization_id: number;
  provider: string;
  email: string;
  sender_name: string | null;
  status: string;
  health_status: string;
  health_score: number | null;
  health_details: Record<string, unknown> | null;
  daily_sent_count: number;
  sending_limit: number;
  reply_to: string | null;
  signature: string | null;
  last_used_at: string | null;
  created_at: string | null;
}

export interface ContactList {
  uuid: string;
  name: string;
  description: string | null;
  field_definitions: string[] | null;
  created_at: string | null;
  updated_at: string | null;
}

export const listEmailAccounts = async (): Promise<PaginatedResponse<EmailAccount>> => {
  const { data } = await api.get<ApiSuccessResponse<PaginatedResponse<EmailAccount>>>(
    "/email-accounts/",
    { params: { limit: 100, offset: 0 } },
  );
  return data.data;
};

export const listContactLists = async (): Promise<PaginatedResponse<ContactList>> => {
  const { data } = await api.get<ApiSuccessResponse<PaginatedResponse<ContactList>>>(
    "/contact-lists/",
    { params: { limit: 100, offset: 0 } },
  );
  return data.data;
};

export const getContactListCount = async (listUuid: string): Promise<number> => {
  const { data } = await api.get<
    ApiSuccessResponse<PaginatedResponse<{ uuid: string; email: string }>>
  >(`/contact-lists/${listUuid}/contacts`, { params: { limit: 1, offset: 0 } });
  return data.data.total;
};
