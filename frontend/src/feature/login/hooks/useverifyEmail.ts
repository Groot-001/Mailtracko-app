import { useMutation } from "@tanstack/react-query";
import type { AxiosError } from "axios";
import { verifyEmail } from "../api/verifyEmailApi";

export interface ApiErrorResponse {
  message: string;
}

export function useVerifyEmail() {
  // No navigate here — let the component decide what to do on
  // success/error, since that depends on UI state (showing a
  // banner, etc.) that the hook shouldn't own.
  return useMutation({
    mutationFn: verifyEmail,
  });
}

export type VerifyEmailError = AxiosError<ApiErrorResponse>;
