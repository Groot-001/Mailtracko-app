import type { User } from "../../feature/login/types/user";
import type { ApiSuccessResponse } from "../types/api.types";
import { api } from "./axios";

interface CurrentUserFlags {
  two_factor_enabled?: unknown;
  is_2fa_enabled?: unknown;
  is_two_factor_enabled?: unknown;
  two_factor?: unknown;
  mfa_enabled?: unknown;
}

interface CurrentUserResponse extends CurrentUserFlags {
  success: boolean;
  message: string;
  data: CurrentUserFlags & {
    user: User;
    account_summary: {
      role: string;
      organization_name: string;
      organization_uuid: string;
      member_status: string;
      account_status: string;
      plan: string;
    };
  };
}

const parseBool = (val: unknown): boolean => {
  if (val === undefined || val === null) return false;
  if (typeof val === "boolean") return val;
  if (typeof val === "string") {
    return val.toLowerCase() === "true" || val.toLowerCase() === "enabled" || val.toLowerCase() === "1" || val.toLowerCase() === "active";
  }
  if (typeof val === "number") return val === 1;
  return !!val;
};

const getFlagValue = (source: unknown, key: keyof CurrentUserFlags): unknown => {
  if (typeof source === "object" && source !== null) {
    return (source as Record<string, unknown>)[key];
  }
  return undefined;
};

export const getCurrentUser = async () => {
  const { data } = await api.get<CurrentUserResponse>("/auth/me");

  const user = data.data?.user;
  const rawData = data.data;
  const rawEnvelope = data;

  if (user) {
    const is2FA =
      parseBool(getFlagValue(rawEnvelope, "two_factor_enabled")) ||
      parseBool(getFlagValue(rawEnvelope, "is_2fa_enabled")) ||
      parseBool(getFlagValue(rawEnvelope, "is_two_factor_enabled")) ||
      parseBool(getFlagValue(rawEnvelope, "two_factor")) ||
      parseBool(getFlagValue(rawEnvelope, "mfa_enabled")) ||
      parseBool(getFlagValue(rawData, "two_factor_enabled")) ||
      parseBool(getFlagValue(rawData, "is_2fa_enabled")) ||
      parseBool(getFlagValue(rawData, "is_two_factor_enabled")) ||
      parseBool(getFlagValue(rawData, "two_factor")) ||
      parseBool(getFlagValue(rawData, "mfa_enabled")) ||
      parseBool(user.two_factor_enabled) ||
      parseBool(user.is_2fa_enabled) ||
      parseBool(getFlagValue(user, "is_two_factor_enabled")) ||
      parseBool(getFlagValue(user, "two_factor")) ||
      parseBool(getFlagValue(user, "mfa_enabled"));

    user.is_2fa_enabled = is2FA;
    user.two_factor_enabled = is2FA;
  }

  return user;
};

export interface UpdateProfilePayload {
  full_name?: string;
  theme?: string;
  profile_image?: string;
  timezone?: string;
  phone?: string;
  country_code?: string;
  location?: string;
}

interface UpdateProfileResponse {
  success: boolean;
  message: string;
  data: User;
}

export const updateProfile = async (payload: UpdateProfilePayload) => {
  const { data } = await api.patch<UpdateProfileResponse>("/auth/profile", payload);
  return data.data;
};

type UploadImageResponse = User & { url: string };

export const uploadProfileImage = async (file: File) => {
  const formData = new FormData();
  formData.append("file", file);
  // Do not set Content-Type manually; the browser must add the multipart boundary.
  const { data } = await api.post<ApiSuccessResponse<UploadImageResponse>>(
    "/auth/profile/image",
    formData,
  );
  // Unwrap the backend success envelope consistently.
  return data.data;
};

export interface ChangePasswordPayload {
  current_password?: string;
  new_password?: string;
  confirm_password?: string;
}

interface ChangePasswordResponse {
  success: boolean;
  message: string;
}

export const changePassword = async (payload: ChangePasswordPayload) => {
  const { data } = await api.post<ChangePasswordResponse>("/auth/password/change", payload);
  return data;
};

export interface Setup2FAResponse {
  success: boolean;
  data: {
    secret: string;
    provisioning_uri: string;
    qr_code: string;
    recovery_codes: string[];
  };
}

export interface Verify2FALoginPayload {
  temp_token?: string;
  code: string;
}

export interface Verify2FALoginResponse {
  success: boolean;
  message: string;
  data: {
    session_uuid: string;
    user: User;
  };
}

export const setup2FA = async () => {
  const { data } = await api.post<Setup2FAResponse>("/auth/2fa/setup");
  return data;
};

export const verify2FA = async (code: string) => {
  const { data } = await api.post<{ success: boolean; message: string }>("/auth/2fa/verify", { code });
  return data;
};

export const disable2FA = async () => {
  const { data } = await api.post<{ success: boolean; message: string }>("/auth/2fa/disable");
  return data;
};

export const verify2FALogin = async (payload: Verify2FALoginPayload) => {
  const { data } = await api.post<Verify2FALoginResponse>("/auth/2fa/verify-login", payload);
  return data;
};

export const logoutAccount = async () => {
  const { data } = await api.post<{ success: boolean; message: string }>(
    "/auth/logout",
  );
  return data;
};

export const deleteCurrentAccount = async (): Promise<{
  message: string;
  scheduled_deletion_at: string;
}> => {
  const { data } = await api.delete<
    ApiSuccessResponse<{ message: string; scheduled_deletion_at: string }>
  >("/auth/account");
  return data.data;
};

export interface AuthSession {
  uuid: string;
  ip_address?: string | null;
  user_agent?: string | null;
  expires_at?: string | null;
  revoked_at?: string | null;
  created_at?: string | null;
}

export const listAuthSessions = async (): Promise<AuthSession[]> => {
  const { data } = await api.get<ApiSuccessResponse<AuthSession[]>>("/auth/sessions");
  return data.data;
};

export const getCurrentAuthSession = async (): Promise<AuthSession | null> => {
  const { data } = await api.get<ApiSuccessResponse<AuthSession | null>>(
    "/auth/sessions/current",
  );
  return data.data;
};

export const revokeAuthSession = async (sessionUuid: string) => {
  const { data } = await api.post<ApiSuccessResponse<{ message: string }>>(
    "/auth/sessions/revoke",
    { session_uuid: sessionUuid },
  );
  return data.data;
};

export const revokeOtherAuthSessions = async () => {
  const { data } = await api.post<ApiSuccessResponse<{ message: string }>>(
    "/auth/sessions/revoke-others",
  );
  return data.data;
};


export interface UserActivityItem {
  uuid: string;
  activity_type: string;
  description: string;
  metadata?: Record<string, unknown> | null;
  created_at: string;
}

export const listUserActivities = async (limit = 100, offset = 0) => {
  const { data } = await api.get<ApiSuccessResponse<{
    items: UserActivityItem[];
    total: number;
    limit: number;
    offset: number;
  }>>("/auth/activities", { params: { limit, offset } });
  return data.data;
};
