import { api } from "../../../shared/api/axios";
import type { createAccountFormData } from "../schema/register";
import type { User } from "../types/user";

// Backend signup response creates the account only; authentication happens on Login.
export interface SignupApiResponse {
  success: boolean;
  message: string;
  data: {
    requires_login: true;
    user: User;
  };
}

export interface ValidateInviteResponse {
  success: boolean;
  message: string;
  data: {
    email: string;
    organization_name: string;
    role_code: string;
    expires_at: string;
  };
}

export const createAccount = async (payload: createAccountFormData) => {
  const { data: envelope } = await api.post<SignupApiResponse>(
    "/auth/signup",
    payload,
  );
  return envelope;
};

export const validateInviteToken = async (token: string) => {
  const { data: envelope } = await api.get<ValidateInviteResponse>(
    "/organizations/invitations/validate",
    {
      params: { token },
    }
  );
  return envelope.data;
};

export const acceptInvite = async (token: string) => {
  const { data: envelope } = await api.post(
    "/organizations/invitations/accept",
    { token },
  );
  return envelope;
};

export const declineInvite = async (token: string) => {
  const { data: envelope } = await api.post(
    "/organizations/invitations/public/decline",
    { token },
  );
  return envelope;
};
