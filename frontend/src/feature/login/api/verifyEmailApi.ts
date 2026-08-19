import { api } from "../../../shared/api/axios";
import type { VerifyEmailFormData } from "../schema/VerifyEmailSchema";

// Backend verify response:
// { "success": true, "message": "Success", "data": { "message": "Email verified successfully" } }
interface VerifyEmailApiResponse {
  success: boolean;
  message: string;
  data: {
    message: string;
  };
}

export const verifyEmail = async (payload: VerifyEmailFormData) => {
  const { data: envelope } = await api.post<VerifyEmailApiResponse>(
    "/auth/email/verify",
    payload,
  );
  return envelope;
};

export const resendVerificationEmail = async (email: string) => {
  const { data: envelope } = await api.post(
    "/auth/email/resend",
    { email }
  );
  return envelope;
};
