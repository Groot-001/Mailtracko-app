import { api } from "../../../shared/api/axios";
import type {
  EmailAccount,
  SMTPConnectPayload,
  SMTPConnectResponse,
  VerifyPayload,
  OAuthConnectPayload,
  OAuthConnectResponse,
  ConnectionTestResponse,
  UpdateEmailAccountPayload,
} from "../types/email-accounts.types";

interface ApiResponseEnvelope<T> {
  success: boolean;
  message?: string;
  data: T;
}

// ─── Connect SMTP ────────────────────────────────────────────────────────────

export const connectSMTP = async (payload: SMTPConnectPayload): Promise<SMTPConnectResponse> => {
  const { data } = await api.post<ApiResponseEnvelope<SMTPConnectResponse>>(
    "/email-accounts/smtp/connect",
    payload
  );
  return data.data;
};

export const testSMTPCredentials = async (
  payload: SMTPConnectPayload,
): Promise<{ smtp: string; imap: string }> => {
  const { data } = await api.post<ApiResponseEnvelope<{ smtp: string; imap: string }>>(
    "/email-accounts/smtp/test-credentials",
    payload,
  );
  return data.data;
};

// ─── Verify Code ──────────────────────────────────────────────────────────────

export const verifySMTP = async (uuid: string, payload: VerifyPayload): Promise<EmailAccount> => {
  const { data } = await api.post<ApiResponseEnvelope<EmailAccount>>(
    `/email-accounts/${uuid}/verify`,
    payload
  );
  return data.data;
};

export const resendVerificationCode = async (
  uuid: string
): Promise<{ message: string }> => {
  const { data } = await api.post<ApiResponseEnvelope<{ message: string }>>(
    `/email-accounts/${uuid}/resend-code`
  );
  return data.data;
};

// ─── OAuth Connect ────────────────────────────────────────────────────────────

export const connectOAuth = async (payload: OAuthConnectPayload): Promise<OAuthConnectResponse> => {
  const { data } = await api.post<ApiResponseEnvelope<OAuthConnectResponse>>(
    "/email-accounts/oauth/connect",
    payload
  );
  return data.data;
};

// ─── Test Connection ──────────────────────────────────────────────────────────

export const testConnection = async (uuid: string): Promise<ConnectionTestResponse> => {
  const { data } = await api.post<ApiResponseEnvelope<ConnectionTestResponse>>(
    `/email-accounts/${uuid}/test`
  );
  return data.data;
};

// ─── List / Get / Update / Delete ─────────────────────────────────────────────

export const listEmailAccounts = async (
  limit = 50,
  offset = 0
): Promise<{ items: EmailAccount[]; total: number; limit: number; offset: number }> => {
  const { data } = await api.get<
    ApiResponseEnvelope<{ items: EmailAccount[]; total: number; limit: number; offset: number }>
  >("/email-accounts/", {
    params: { limit, offset },
  });
  return data.data;
};

export const getEmailAccount = async (uuid: string): Promise<EmailAccount> => {
  const { data } = await api.get<ApiResponseEnvelope<{ email_account: EmailAccount }>>(
    `/email-accounts/${uuid}`
  );
  return data.data.email_account;
};

export const updateEmailAccount = async (
  uuid: string,
  payload: UpdateEmailAccountPayload
): Promise<EmailAccount> => {
  const { data } = await api.patch<ApiResponseEnvelope<{ email_account: EmailAccount }>>(
    `/email-accounts/${uuid}`,
    payload
  );
  return data.data.email_account;
};

export const deleteEmailAccount = async (uuid: string): Promise<{ message: string }> => {
  const { data } = await api.delete<ApiResponseEnvelope<{ message: string }>>(
    `/email-accounts/${uuid}`
  );
  return data.data;
};
