import { api } from "../../../shared/api/axios";
import type { forgotPasswordFormData } from "../schema/forgotPasswordSchema";

export const forgotPassword = async (payload: forgotPasswordFormData) => {
  const { data } = await api.post("/auth/password/forgot", payload);
  return data;
};

export interface VerifyForgotPasswordCodePayload {
  token: string;
}

export interface ResetPasswordPayload {
  reset_challenge: string;
  new_password: string;
}

export const verifyForgotPasswordCode = async (payload: VerifyForgotPasswordCodePayload) => {
  const { data } = await api.post<{
    success: boolean;
    data: { reset_challenge: string; expires_in: number };
  }>("/auth/password/forgot/verify-code", payload);
  return data.data;
};

export const resetForgotPassword = async (payload: ResetPasswordPayload) => {
  const { data } = await api.post("/auth/password/forgot/reset", payload);
  return data;
};
