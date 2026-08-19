import { acceptInvite } from "../../feature/login/api/registerApi";

const PENDING_INVITATION_TOKEN_KEY = "mailtracko_pending_invitation_token";

export const storePendingInvitationToken = (token: string) => {
  const cleanToken = token.trim();
  if (!cleanToken) return;
  window.sessionStorage.setItem(PENDING_INVITATION_TOKEN_KEY, cleanToken);
};

export const getPendingInvitationToken = () =>
  window.sessionStorage.getItem(PENDING_INVITATION_TOKEN_KEY);

export const clearPendingInvitationToken = () =>
  window.sessionStorage.removeItem(PENDING_INVITATION_TOKEN_KEY);

export const completePendingInvitation = async (): Promise<boolean> => {
  const token = getPendingInvitationToken();
  if (!token) return false;

  await acceptInvite(token);
  clearPendingInvitationToken();
  return true;
};
