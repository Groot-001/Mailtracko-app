import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listEmailAccounts,
  getEmailAccount,
  connectSMTP,
  verifySMTP,
  resendVerificationCode,
  connectOAuth,
  testConnection,
  updateEmailAccount,
  deleteEmailAccount,
} from "../api/emailAccountsApi";
import type {
  SMTPConnectPayload,
  VerifyPayload,
  OAuthConnectPayload,
  UpdateEmailAccountPayload,
} from "../types/email-accounts.types";

export const EMAIL_ACCOUNTS_KEY = ["email-accounts"] as const;

export const useEmailAccountsList = (limit = 50, offset = 0) => {
  return useQuery({
    queryKey: [...EMAIL_ACCOUNTS_KEY, "list", limit, offset],
    queryFn: () => listEmailAccounts(limit, offset),
    staleTime: 1000 * 30,
    refetchInterval: 30_000,
    refetchIntervalInBackground: false,
  });
};

export const useEmailAccountDetail = (uuid?: string) => {
  return useQuery({
    queryKey: [...EMAIL_ACCOUNTS_KEY, "detail", uuid],
    queryFn: () => getEmailAccount(uuid!),
    enabled: !!uuid,
  });
};

export const useConnectSMTP = () => {
  return useMutation({
    mutationFn: (payload: SMTPConnectPayload) => connectSMTP(payload),
  });
};

export const useVerifySMTP = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ uuid, payload }: { uuid: string; payload: VerifyPayload }) =>
      verifySMTP(uuid, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: EMAIL_ACCOUNTS_KEY });
    },
  });
};

export const useResendCode = () => {
  return useMutation({
    mutationFn: (uuid: string) => resendVerificationCode(uuid),
  });
};

export const useConnectOAuth = () => {
  return useMutation({
    mutationFn: (payload: OAuthConnectPayload) => connectOAuth(payload),
  });
};

export const useTestConnection = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (uuid: string) => testConnection(uuid),
    onSuccess: (_data, uuid) => {
      queryClient.invalidateQueries({ queryKey: [...EMAIL_ACCOUNTS_KEY, "detail", uuid] });
      queryClient.invalidateQueries({ queryKey: EMAIL_ACCOUNTS_KEY });
    },
  });
};

export const useUpdateEmailAccount = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ uuid, payload }: { uuid: string; payload: UpdateEmailAccountPayload }) =>
      updateEmailAccount(uuid, payload),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: [...EMAIL_ACCOUNTS_KEY, "detail", variables.uuid] });
      queryClient.invalidateQueries({ queryKey: EMAIL_ACCOUNTS_KEY });
    },
  });
};

export const useDeleteEmailAccount = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (uuid: string) => deleteEmailAccount(uuid),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: EMAIL_ACCOUNTS_KEY });
    },
  });
};
