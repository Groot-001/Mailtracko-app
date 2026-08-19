import { api } from "../../../shared/api/axios";
import type { LoginFormData } from "../schema/LoginSchema";
import type { User } from "../types/user";

// Backend login response:
// { "success": true, "message": "...", "data": { "session_uuid": "...", "user": { uuid, full_name, email, theme } } }
interface LoginApiResponse {
  success: boolean;
  message: string;
  data: {
    session_uuid?: string;
    user?: User;
    requires_2fa?: boolean;
    requires_email_verification?: boolean;
    temp_token?: string;
  };
}

export const loginUser = async (payload: LoginFormData) => {
  const { data: envelope } = await api.post<LoginApiResponse>(
    "/auth/login",
    payload,
  );
  return envelope;
};
