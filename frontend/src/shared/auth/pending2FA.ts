const PENDING_2FA_TOKEN_KEY = "mailtracko_pending_2fa_token";

export const storePending2FAToken = (token: string) => {
  const cleanToken = token.trim();
  if (!cleanToken) return;
  window.sessionStorage.setItem(PENDING_2FA_TOKEN_KEY, cleanToken);
};

export const getPending2FAToken = () =>
  window.sessionStorage.getItem(PENDING_2FA_TOKEN_KEY);

export const clearPending2FAToken = () =>
  window.sessionStorage.removeItem(PENDING_2FA_TOKEN_KEY);
